#!/usr/bin/env python3
"""H36 holdout runner (`knowledge/21_preregistered_h36_spigm_submodular_2026-10-25.md`).

Executes one paired holdout stage (screen `--draws 20 21` or untouched confirmation
`--draws 22 23`) across the 4 spatial quadrants (NW, NE, SW, SE) of `gems25.experiment.Cell`:
  * Leakage Canary on all 7 H36 columns + H27_tip (aborts if max(AUC, 1-AUC) > 0.90)
  * C0_BDE_ctrl    : Same-run BDE+7 incumbent + sapd2.4 (kfrac=0.035, d=2.4)
  * C1_Sub_ctrl    : Same-run zero-topography ACDE + H27_tip baseline + sapd2.4
  * H36_S_submod   : Zero-topography Head S (ACDE + H27_tip + 7 H36 cols) + submod300_emit
  * H36_PoE_submod : PRIMARY regime-gated Product-of-Experts (Head M x Head S) + submod300_emit
  * H36_PoE_sapd   : Diagnostic emission ablation (s_PoE + sapd2.4)
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.h36_spigm import (  # noqa: E402
    CAND_KFRAC_DEFAULT,
    FLANK_PX_DEFAULT,
    H36_NAMES,
    MASS_FRAC_DEFAULT,
    PI0_DEFAULT,
    TAU_MIN_DEFAULT,
    TIP_KEEP_DEFAULT,
    compute_alpha_sub,
    load_h36_sidecar,
    poe_blend,
    submod300_emit,
)
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
SAPD_MIN_DIST = 2.4
SAPD_KFRAC = 0.035
LEAKAGE_CAP = 0.90
EVALUATOR_VERSION = (
    "gems25.holdout.Holdout(v1,4-quadrant,collar=15px,hide_frac=0.20,erode=12)"
    "+gems25.metric.dti_binary(alpha=0.2,beta=0.8,R=3.0px)"
)


def _to_crop(cell: Cell, vec_q: np.ndarray) -> np.ndarray:
    g = cell._grid
    g[:] = 0.0
    g.ravel()[cell.ctx.fi[cell.q]] = np.nan_to_num(vec_q, nan=0.0).astype(np.float32)
    out = g[cell.sl].copy()
    g[:] = 0.0
    return out


def _emit_sapd24(cell: Cell, p_q: np.ndarray) -> np.ndarray:
    k = int(round(SAPD_KFRAC * int(cell.dom_c.sum())))
    s_crop, top = cell.candidates(p_q, k)
    return score_ordered_dots(s_crop, top, SAPD_MIN_DIST)


def _eval_full(cell: Cell, emitted_c: np.ndarray) -> dict:
    r = dti_binary(emitted_c, cell.truth_c, valid=cell.dom_c, known=cell.known_c)
    n = int(emitted_c.sum())
    hug = float((emitted_c & cell.near_vis).sum() / max(n, 1))
    return dict(
        dti=float(r["dti"]),
        coverage=float(r["coverage"]),
        tp=float(r["tp"]),
        fp=float(r["fp"]),
        fn=float(r["fn"]),
        n_truth=int(r["n_truth"]),
        emitted=n,
        hug=hug,
    )


def _fit_predict_with_sidecar(
    cell: Cell,
    cols: list[int],
    sidecar: np.ndarray | None,
    seed: int,
) -> tuple[np.ndarray, dict[str, float]]:
    if sidecar is None:
        Xtr = np.ascontiguousarray(cell.Xtr[:, cols])
        Xq = np.ascontiguousarray(cell.Xq[:, cols])
    else:
        Xtr = np.hstack([cell.Xtr[:, cols], np.asarray(sidecar[:, cell.train_idx], dtype=np.float32).T])
        Xq = np.hstack([cell.Xq[:, cols], np.asarray(sidecar[:, cell.q], dtype=np.float32).T])
    t0 = time.time()
    model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    del Xtr
    t0 = time.time()
    p = model.predict_proba(Xq)[:, 1].astype(np.float32)
    t_pred = time.time() - t0
    del Xq, model
    return p, dict(fit_s=round(t_fit, 3), predict_s=round(t_pred, 3))


def _canary_aucs(cell: Cell, sidecar: np.ndarray, tip_col: int) -> dict[str, dict[str, float]]:
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    out: dict[str, dict[str, float]] = {}
    for j, name in enumerate(H36_NAMES):
        v = np.nan_to_num(np.asarray(sidecar[j, cell.q], dtype=np.float64)[idx], nan=0.0)
        raw = float(roc_auc_score(y, v)) if np.unique(v).size > 1 else 0.5
        sym = float(max(raw, 1.0 - raw))
        out[name] = dict(raw_auc=round(raw, 6), canary_auc=round(sym, 6))
    vt = np.nan_to_num(np.asarray(cell.Xq[:, tip_col], dtype=np.float64)[idx], nan=0.0)
    raw_t = float(roc_auc_score(y, vt)) if np.unique(vt).size > 1 else 0.5
    out["H27_tip"] = dict(raw_auc=round(raw_t, 6), canary_auc=round(max(raw_t, 1.0 - raw_t), 6))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-ablation", action="store_true", help="omit diagnostic H36_PoE_sapd in confirmation")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cells_path = out / "cells.jsonl"
    design_path = out / "design.json"
    if cells_path.exists() or design_path.exists():
        raise SystemExit(f"Refusing to overwrite existing holdout outputs in {out}")

    work, ddir = work_dir(), data_dir()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("Add-on cache missing; run scripts/build_addons.py first")
    sidecar = load_h36_sidecar(work, ddir / "external", ctx.foot)

    alpha_sub_full = compute_alpha_sub(
        np.asarray(ctx.static[ctx.col["det_elev_slope"]], dtype=np.float32),
        np.asarray(ctx.static[ctx.col["L_valid"]], dtype=np.float32),
    )

    c0_cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    tip_col = ctx.col["H27_tip"]
    c1_cols = ctx.columns("ACDE") + [tip_col]
    head_s_base_cols = list(c1_cols)
    head_m_base_cols = ctx.columns("ABCDE") + ctx.named(EXTRAS) + [tip_col]

    design = dict(
        hypothesis="H36-1: Unit-consistent subsurface SPI-GM-UP150 + hydrogeochemical disequilibrium PoE + Bayes 300m submodular allocation",
        preregistration="knowledge/21_preregistered_h36_spigm_submodular_2026-10-25.md",
        evaluator_version=EVALUATOR_VERSION,
        draws=list(a.draws),
        folds=list(FOLD_IDS),
        leakage_auc_cap=LEAKAGE_CAP,
        h36_columns=list(H36_NAMES),
        submod_params=dict(
            pi0=PI0_DEFAULT,
            flank_px=FLANK_PX_DEFAULT,
            tip_keep=TIP_KEEP_DEFAULT,
            cand_kfrac=CAND_KFRAC_DEFAULT,
            mass_frac=MASS_FRAC_DEFAULT,
            tau_min=TAU_MIN_DEFAULT,
        ),
        sapd_params=dict(kfrac=SAPD_KFRAC, min_dist=SAPD_MIN_DIST),
        gate=dict(
            primary_comparison="H36_PoE_submod vs C0_BDE_ctrl",
            subsurface_comparison="H36_S_submod vs C1_Sub_ctrl",
            mean_gain_gt=0.001,
            folds_positive_min=3,
            worst_fold_min=-0.010,
        ),
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    t_start = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = _canary_aucs(cell, sidecar, tip_col)
                worst_feat, worst_info = max(canary.items(), key=lambda kv: kv[1]["canary_auc"])
                if worst_info["canary_auc"] > LEAKAGE_CAP:
                    raise SystemExit(
                        f"LEAKAGE CANARY FIRED in fold={fold} draw={draw}: "
                        f"{worst_feat} canary_auc={worst_info['canary_auc']:.4f} > {LEAKAGE_CAP}"
                    )

                pi_train = float(cell.y.mean())
                alpha_q = alpha_sub_full[cell.q]

                # 1. C0_BDE_ctrl
                p_c0, t_c0 = _fit_predict_with_sidecar(cell, c0_cols, None, seed=draw)
                t0 = time.time()
                em_c0 = _emit_sapd24(cell, p_c0)
                ev_c0 = _eval_full(cell, em_c0)
                auc_c0 = cell.auc(p_c0)
                emit_s_c0 = round(time.time() - t0, 3)
                del p_c0, em_c0

                # 2. C1_Sub_ctrl (zero topography/LiDAR baseline)
                p_c1, t_c1 = _fit_predict_with_sidecar(cell, c1_cols, None, seed=draw)
                t0 = time.time()
                em_c1 = _emit_sapd24(cell, p_c1)
                ev_c1 = _eval_full(cell, em_c1)
                auc_c1 = cell.auc(p_c1)
                emit_s_c1 = round(time.time() - t0, 3)
                del p_c1, em_c1

                # 3. Head S (zero topography/LiDAR + 7 H36 physics invariants)
                p_s, t_s = _fit_predict_with_sidecar(cell, head_s_base_cols, sidecar, seed=draw)
                auc_s = cell.auc(p_s)
                s_sub_crop = _to_crop(cell, p_s)
                t0 = time.time()
                em_s = submod300_emit(
                    s_sub_crop, None, cell.dom_c, cell.known_c, cell.tip_c, pi_train=pi_train
                )
                ev_s = _eval_full(cell, em_s)
                emit_s_sub = round(time.time() - t0, 3)
                del em_s

                # 4. Head M + Regime-Gated PoE
                p_m, t_m = _fit_predict_with_sidecar(cell, head_m_base_cols, sidecar, seed=draw)
                s_poe_q = poe_blend(p_m, p_s, alpha_q)
                auc_poe = cell.auc(s_poe_q)
                del p_m, p_s
                s_poe_crop = _to_crop(cell, s_poe_q)
                t0 = time.time()
                em_poe = submod300_emit(
                    s_poe_crop, s_sub_crop, cell.dom_c, cell.known_c, cell.tip_c, pi_train=pi_train
                )
                ev_poe = _eval_full(cell, em_poe)
                emit_s_poe = round(time.time() - t0, 3)
                del em_poe, s_poe_crop, s_sub_crop

                arm_records = [
                    ("C0_BDE_ctrl", auc_c0, ev_c0, t_c0, emit_s_c0),
                    ("C1_Sub_ctrl", auc_c1, ev_c1, t_c1, emit_s_c1),
                    ("H36_S_submod", auc_s, ev_s, t_s, emit_s_sub),
                    (
                        "H36_PoE_submod",
                        auc_poe,
                        ev_poe,
                        dict(fit_s=round(t_s["fit_s"] + t_m["fit_s"], 3), predict_s=round(t_s["predict_s"] + t_m["predict_s"], 3)),
                        emit_s_poe,
                    ),
                ]

                if not a.skip_ablation:
                    t0 = time.time()
                    em_sapd = _emit_sapd24(cell, s_poe_q)
                    ev_sapd = _eval_full(cell, em_sapd)
                    emit_s_sapd = round(time.time() - t0, 3)
                    del em_sapd
                    arm_records.append(
                        (
                            "H36_PoE_sapd",
                            auc_poe,
                            ev_sapd,
                            dict(fit_s=round(t_s["fit_s"] + t_m["fit_s"], 3), predict_s=round(t_s["predict_s"] + t_m["predict_s"], 3)),
                            emit_s_sapd,
                        )
                    )
                del s_poe_q

                for arm_name, auc_val, ev, timing, emit_sec in arm_records:
                    rec = dict(
                        fold=fold,
                        fold_name=FOLDS[fold],
                        draw=draw,
                        arm=arm_name,
                        pi_train=round(pi_train, 6),
                        auc=round(float(auc_val), 6),
                        emit_s=emit_sec,
                        canary_worst_feature=worst_feat,
                        canary_worst_auc=worst_info["canary_auc"],
                        feature_auc_canary=canary if arm_name == "C0_BDE_ctrl" else None,
                        **ev,
                        **timing,
                    )
                    sink.write(json.dumps(rec) + "\n")
                    sink.flush()
                    print(
                        f"[{time.time() - t_start:5.0f}s] {FOLDS[fold]} d={draw} {arm_name:15s}: "
                        f"HOLDOUT-DTI={ev['dti']:.6f} emit={ev['emitted']:5d} truth={ev['n_truth']:4d} "
                        f"hug={ev['hug']:.3f} auc={auc_val:.4f} canary_max={worst_info['canary_auc']:.3f}",
                        flush=True,
                    )

                del cell
                gc.collect()

    print(f"DONE {cells_path} in {time.time() - t_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
