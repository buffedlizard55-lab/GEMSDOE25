#!/usr/bin/env python3
"""Pre-registered H72 holdout runner (`H72-1` PTTG-DR & `H72-2` VCCD+RBDT).

Frozen specification: `knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md`.
Refuses to overwrite existing evidence directories and writes `design.json` before any model fit.

Usage:
  .venv/bin/python scripts/run_h72_experiments.py --exp h72_1 --draws 80 81 --out evidence/h72_1_screen
  .venv/bin/python scripts/run_h72_experiments.py --exp h72_2 --draws 82 83 --out evidence/h72_2_screen
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h72_pttg import (  # noqa: E402
    H72_MTHS_NAMES,
    H72_PTTG_NAMES,
    H72_SUBSURF_NAMES,
    H72_VCCD_NAMES,
    load_h72_mths_sidecar,
    load_h72_pttg_sidecar,
    load_h72_vccd_sidecar,
)
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from gems25.validation import feature_canary  # noqa: E402
from run_h28_holdout import EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
KFRAC_H35 = 0.035
MIN_DIST_H35 = 2.4
KFRAC_DEAPRON = 0.030
MIN_DIST_DEAPRON = 2.8
CAT_BUF_DEAPRON = 2.0
LEAKAGE_AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px) via gems25.experiment.Cell.evaluate"


def rank01(v: np.ndarray) -> np.ndarray:
    a = np.nan_to_num(np.asarray(v, dtype=np.float64), nan=0.0)
    if a.size <= 1:
        return np.zeros_like(a, dtype=np.float32)
    return ((rankdata(a, method="average") - 1.0) / float(a.size - 1)).astype(np.float32)


def run_canaries(cell: Cell, sidecars: list[tuple[np.ndarray, list[str]]]) -> dict[str, dict]:
    y = np.concatenate([np.ones(cell.auc_pos.size, np.int8), np.zeros(cell.auc_neg.size, np.int8)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    out: dict[str, dict] = {}
    for sc, names in sidecars:
        for j, nm in enumerate(names):
            vals = np.asarray(sc[j, cell.q], dtype=np.float64)[idx]
            res = feature_canary(vals, y, cap=LEAKAGE_AUC_CAP)
            out[nm] = res
            if not res["passed"]:
                raise RuntimeError(f"LEAKAGE CANARY TRIGGERED on {nm} in fold={cell.fold} draw={cell.seed}: {res}")
    return out


def fit_predict_sidecars(
    cell: Cell,
    cols: list[int],
    sidecars: list[np.ndarray],
    seed: int,
) -> tuple[np.ndarray, float, dict]:
    Xtr = cell.Xtr[:, cols]
    Xq = cell.Xq[:, cols]
    if sidecars:
        Xtr = np.hstack([Xtr] + [np.asarray(sc[:, cell.train_idx], dtype=np.float32).T for sc in sidecars])
        Xq = np.hstack([Xq] + [np.asarray(sc[:, cell.q], dtype=np.float32).T for sc in sidecars])
    t0 = time.time()
    model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    t0 = time.time()
    p = model.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    t_pred = time.time() - t0

    y_auc = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    p_auc = p[np.concatenate([cell.auc_pos, cell.auc_neg])]
    auc = float(roc_auc_score(y_auc, p_auc)) if np.unique(p_auc).size > 1 else 0.5
    del Xtr, Xq, model
    return p, auc, dict(fit_s=round(t_fit, 3), predict_s=round(t_pred, 3), n_features=int(len(cols) + sum(sc.shape[0] for sc in sidecars)))


def emit_buffered_dots(
    cell: Cell,
    score_q: np.ndarray,
    d_vis_c: np.ndarray,
    *,
    kfrac: float,
    min_dist: float,
    cat_buf_px: float,
) -> np.ndarray:
    g = cell._grid
    g[:] = 0.0
    g.ravel()[cell.ctx.fi[cell.q]] = np.nan_to_num(score_q, nan=0.0).astype(np.float32)
    s_crop = g[cell.sl].copy()
    g[:] = 0.0
    r = ridge_nms(s_crop, cell.dom_c, 1.0)
    excl = cell.known_c if cat_buf_px <= 0.0 else (cell.known_c | (d_vis_c <= cat_buf_px))
    s_clean = np.where(r & ~excl, s_crop, 0.0)
    k = int(round(kfrac * float(cell.dom_c.sum())))
    top = select_top_positive(s_clean, cell.dom_c, k)
    return score_ordered_dots(s_clean, top, min_dist)


def eval_arm_full(cell: Cell, em: np.ndarray, d_vis_c: np.ndarray, auc: float, meta: dict, canary: dict) -> dict:
    ev = cell.evaluate(em)
    far_mask = d_vis_c > 9.0
    far_truth = cell.truth_c & far_mask
    far_em = em & far_mask
    far_em_n = int((far_em & cell.dom_c & ~cell.known_c).sum())
    far_ev = dti_binary(far_em, far_truth, cell.dom_c, cell.known_c) if far_truth.any() else {"dti": 0.0, "n_truth": 0}

    dv = d_vis_c[em]
    if dv.size:
        strata = dict(
            frac_le2=round(float((dv <= 2.0).mean()), 5),
            frac_2_9=round(float(((dv > 2.0) & (dv <= 9.0)).mean()), 5),
            frac_9_20=round(float(((dv > 9.0) & (dv <= 20.0)).mean()), 5),
            frac_gt20=round(float((dv > 20.0).mean()), 5),
            median_d_vis=round(float(np.median(dv)), 3),
        )
    else:
        strata = dict(frac_le2=0.0, frac_2_9=0.0, frac_9_20=0.0, frac_gt20=0.0, median_d_vis=0.0)

    return dict(
        **ev,
        auc=round(auc, 6),
        far_gt9_dti=round(float(far_ev["dti"]), 6),
        far_gt9_n_truth=int(far_ev["n_truth"]),
        far_gt9_emitted=far_em_n,
        strata=strata,
        feature_auc_canary=canary,
        **meta,
    )


def run_experiment(exp: str, draws: list[int], out: Path) -> None:
    if out.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=False)

    if exp == "h72_3":
        run_h72_3_subsurf(draws, out)
        return

    use_vccd = exp == "h72_2"
    new_names = H72_PTTG_NAMES + (H72_VCCD_NAMES if use_vccd else [])
    arms = (
        ["CTRL_H35", "CTRL_BLIND_BD", "A1_PTTG_H35", "A2_PTTG_BLIND", "A3_PTTG_DEAPRON"]
        if not use_vccd
        else ["CTRL_H35", "CTRL_BLIND_BD", "B1_FULL_H35", "B2_FULL_BLIND", "B3_FULL_DEAPRON"]
    )
    design = dict(
        experiment=exp.upper(),
        preregistration="knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md",
        draws=draws,
        folds=list(FOLD_IDS),
        fold_names=list(FOLDS),
        new_columns=new_names,
        h34_columns=H34_NAMES,
        arms=arms,
        kfrac_h35=KFRAC_H35,
        min_dist_h35=MIN_DIST_H35,
        kfrac_deapron=KFRAC_DEAPRON,
        min_dist_deapron=MIN_DIST_DEAPRON,
        cat_buf_deapron=CAT_BUF_DEAPRON,
        evaluator=EVALUATOR,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010),
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    work, ext_dir = work_dir(), data_dir() / "external"
    ctx = load_context(work)
    h34_sc = load_h34_sidecar(work, ctx.fi)
    pttg_sc = load_h72_pttg_sidecar(work, ctx.fi)
    extra_scs = [pttg_sc]
    canary_pairs = [(pttg_sc, H72_PTTG_NAMES)]
    if use_vccd:
        vccd_sc = load_h72_vccd_sidecar(work, ext_dir, ctx.fi)
        extra_scs.append(vccd_sc)
        canary_pairs.append((vccd_sc, H72_VCCD_NAMES))

    bde7_tip_cols = ctx.columns("BDE") + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    bd7_cols = ctx.columns("BD") + ctx.named(EXTRAS)
    tip_bridge_cols = bd7_cols + [ctx.col["H27_tip"], ctx.col["H30_pair_bridge"]]

    t_start = time.time()
    cells_path = out / "cells.jsonl"
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in draws:
                t_cell = time.time()
                cell = Cell(ctx, fold, draw, extras=True, h27=True, h30=True)
                d_vis_c = distance_transform_edt(~cell.known_c).astype(np.float32)
                canary = run_canaries(cell, canary_pairs)

                # 1. CTRL_H35 (exact incumbent comparator)
                p_h35, auc_h35, m_h35 = fit_predict_sidecars(cell, bde7_tip_cols, [h34_sc], seed=draw)
                em_h35 = emit_buffered_dots(cell, p_h35, d_vis_c, kfrac=KFRAC_H35, min_dist=MIN_DIST_H35, cat_buf_px=0.0)

                # 2. CTRL_BLIND_BD (100% catalogue-free supervised HGB control)
                p_cbd, auc_cbd, m_cbd = fit_predict_sidecars(cell, bd7_cols, [h34_sc], seed=draw)
                em_cbd = emit_buffered_dots(cell, p_cbd, d_vis_c, kfrac=KFRAC_DEAPRON, min_dist=MIN_DIST_DEAPRON, cat_buf_px=CAT_BUF_DEAPRON)

                # 3. H35 + New Multi-Physics Sidecars
                p_a1, auc_a1, m_a1 = fit_predict_sidecars(cell, bde7_tip_cols, [h34_sc, *extra_scs], seed=draw)
                em_a1 = emit_buffered_dots(cell, p_a1, d_vis_c, kfrac=KFRAC_H35, min_dist=MIN_DIST_H35, cat_buf_px=0.0)

                # 4. Blind Supervised + New Multi-Physics Sidecars
                p_a2, auc_a2, m_a2 = fit_predict_sidecars(cell, bd7_cols, [h34_sc, *extra_scs], seed=draw)
                em_a2 = emit_buffered_dots(cell, p_a2, d_vis_c, kfrac=KFRAC_DEAPRON, min_dist=MIN_DIST_DEAPRON, cat_buf_px=CAT_BUF_DEAPRON)

                # 5. De-Aproned Dual-Regime (75% Blind Multi-Physics + 25% Strike-Tip/Bridge Multi-Physics)
                p_tip, auc_tip, m_tip = fit_predict_sidecars(cell, tip_bridge_cols, [h34_sc, *extra_scs], seed=draw + 1000)
                p_dual = (0.75 * rank01(p_a2) + 0.25 * rank01(p_tip)).astype(np.float32)
                y_auc = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
                auc_dual = float(roc_auc_score(y_auc, p_dual[np.concatenate([cell.auc_pos, cell.auc_neg])]))
                em_a3 = emit_buffered_dots(cell, p_dual, d_vis_c, kfrac=KFRAC_DEAPRON, min_dist=MIN_DIST_DEAPRON, cat_buf_px=CAT_BUF_DEAPRON)
                m_a3 = dict(
                    fit_s=round(m_a2["fit_s"] + m_tip["fit_s"], 3),
                    predict_s=round(m_a2["predict_s"] + m_tip["predict_s"], 3),
                    n_features=int(m_tip["n_features"]),
                    tip_sub_auc=round(auc_tip, 6),
                )

                arm_records = [
                    (arms[0], em_h35, auc_h35, m_h35),
                    (arms[1], em_cbd, auc_cbd, m_cbd),
                    (arms[2], em_a1, auc_a1, m_a1),
                    (arms[3], em_a2, auc_a2, m_a2),
                    (arms[4], em_a3, auc_dual, m_a3),
                ]
                for arm_name, em, auc_val, meta in arm_records:
                    rec = dict(
                        fold=fold,
                        fold_name=FOLDS[fold],
                        draw=draw,
                        arm=arm_name,
                        **eval_arm_full(cell, em, d_vis_c, auc_val, meta, canary),
                    )
                    sink.write(json.dumps(rec) + "\n")
                sink.flush()

                # Summary print for live progress audit
                evs = {nm: cell.evaluate(em)["dti"] for nm, em, _, _ in arm_records}
                print(
                    f"[{time.time() - t_start:6.1f}s] {FOLDS[fold]} d={draw} ({time.time() - t_cell:.1f}s) | "
                    + " | ".join(f"{k}={v:.5f}" for k, v in evs.items()),
                    flush=True,
                )
                del cell, d_vis_c, p_h35, p_cbd, p_a1, p_a2, p_tip, p_dual
                gc.collect()


def run_h72_3_subsurf(draws: list[int], out: Path) -> None:
    arms = ["CTRL_H35", "CTRL_SUBSURF_D", "C1_SUBSURF_PTTG_MTHS"]
    design = dict(
        experiment="H72_3",
        preregistration="knowledge/30_preregistered_h72_3_subsurf_blind_2026-10-26.md",
        draws=draws,
        folds=list(FOLD_IDS),
        fold_names=list(FOLDS),
        new_columns=H72_SUBSURF_NAMES,
        h34_columns=H34_NAMES,
        arms=arms,
        kfrac_h35=KFRAC_H35,
        min_dist_h35=MIN_DIST_H35,
        kfrac_subsurf=KFRAC_DEAPRON,
        min_dist_subsurf=3.0,
        cat_buf_subsurf=CAT_BUF_DEAPRON,
        evaluator=EVALUATOR,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010),
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    work, ext_dir = work_dir(), data_dir() / "external"
    ctx = load_context(work)
    h34_sc = load_h34_sidecar(work, ctx.fi)
    pttg_sc = load_h72_pttg_sidecar(work, ctx.fi)
    mths_sc = load_h72_mths_sidecar(work, ext_dir, ctx.fi)
    pttg_3 = pttg_sc[:3]  # strictly DEM-free trio
    canary_pairs = [(pttg_3, H72_PTTG_NAMES[:3]), (mths_sc, H72_MTHS_NAMES)]

    bde7_tip_cols = ctx.columns("BDE") + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    subsurf_cols = ctx.columns("D") + ctx.named(["X3_gm", "X3_gd"])

    t_start = time.time()
    cells_path = out / "cells.jsonl"
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in draws:
                t_cell = time.time()
                cell = Cell(ctx, fold, draw, extras=True, h27=True, h30=False)
                d_vis_c = distance_transform_edt(~cell.known_c).astype(np.float32)
                canary = run_canaries(cell, canary_pairs)

                p_h35, auc_h35, m_h35 = fit_predict_sidecars(cell, bde7_tip_cols, [h34_sc], seed=draw)
                em_h35 = emit_buffered_dots(cell, p_h35, d_vis_c, kfrac=KFRAC_H35, min_dist=MIN_DIST_H35, cat_buf_px=0.0)

                p_cd, auc_cd, m_cd = fit_predict_sidecars(cell, subsurf_cols, [h34_sc], seed=draw)
                em_cd = emit_buffered_dots(cell, p_cd, d_vis_c, kfrac=KFRAC_DEAPRON, min_dist=3.0, cat_buf_px=CAT_BUF_DEAPRON)

                p_c1, auc_c1, m_c1 = fit_predict_sidecars(cell, subsurf_cols, [h34_sc, pttg_3, mths_sc], seed=draw)
                em_c1 = emit_buffered_dots(cell, p_c1, d_vis_c, kfrac=KFRAC_DEAPRON, min_dist=3.0, cat_buf_px=CAT_BUF_DEAPRON)

                arm_records = [
                    (arms[0], em_h35, auc_h35, m_h35),
                    (arms[1], em_cd, auc_cd, m_cd),
                    (arms[2], em_c1, auc_c1, m_c1),
                ]
                for arm_name, em, auc_val, meta in arm_records:
                    rec = dict(
                        fold=fold,
                        fold_name=FOLDS[fold],
                        draw=draw,
                        arm=arm_name,
                        **eval_arm_full(cell, em, d_vis_c, auc_val, meta, canary),
                    )
                    sink.write(json.dumps(rec) + "\n")
                sink.flush()
                evs = {nm: cell.evaluate(em)["dti"] for nm, em, _, _ in arm_records}
                print(
                    f"[{time.time() - t_start:6.1f}s] {FOLDS[fold]} d={draw} ({time.time() - t_cell:.1f}s) | "
                    + " | ".join(f"{k}={v:.5f}" for k, v in evs.items()),
                    flush=True,
                )
                del cell, d_vis_c, p_h35, p_cd, p_c1
                gc.collect()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp", choices=("h72_1", "h72_2", "h72_3"), required=True)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if any(d < 80 for d in args.draws):
        raise SystemExit(f"Holdout draws < 80 are already consumed; got {args.draws}")
    run_experiment(args.exp, args.draws, Path(args.out))


if __name__ == "__main__":
    main()
