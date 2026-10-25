#!/usr/bin/env python3
"""Pre-registered H66 holdout runner (`H66-1` MGD-F x Flank-Shield 2x2 & `H66-2` SGMC-REACT).

Frozen specification: `knowledge/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md`.
Refuses to overwrite existing evidence directories and writes `design.json` before any model fit.

Usage:
  .venv/bin/python scripts/run_h66_experiments.py --exp h66_1 --draws 50 51 --out evidence/h66_1_screen
  .venv/bin/python scripts/run_h66_experiments.py --exp h66_1 --draws 52 53 --out evidence/h66_1_confirm  # ONLY if screen passes
  .venv/bin/python scripts/run_h66_experiments.py --exp h66_2 --draws 54 55 --out evidence/h66_2_screen
"""

from __future__ import annotations

import argparse
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
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h66_mgd_sgmc import (  # noqa: E402
    H66_MGD_NAMES,
    H66_SGMC_NAMES,
    load_h66_mgd_sidecar,
    load_h66_sgmc_sidecar,
)
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
KFRAC = 0.035
MIN_DIST_PRIMARY = 3.0
MIN_DIST_H35_CTRL = 2.4
FLANK_RADIUS_PX = 2.5
TIP_PRESERVE_THR = 0.05
LEAKAGE_AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px) via gems25.experiment.Cell.evaluate"


def canary_sidecar(cell: Cell, sidecar: np.ndarray, names: list[str]) -> dict[str, dict[str, float]]:
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    out: dict[str, dict[str, float]] = {}
    for j, nm in enumerate(names):
        v = np.nan_to_num(np.asarray(sidecar[j, cell.q], dtype=np.float64)[idx], nan=0.0)
        raw = float(roc_auc_score(y, v)) if np.unique(v).size > 1 else 0.5
        out[nm] = {"raw_auc": raw, "canary_auc": float(max(raw, 1.0 - raw))}
    return out


def fit_predict_custom(cell: Cell, cols: list[int], extra_sidecars: list[np.ndarray], seed: int):
    Xtr = cell.Xtr[:, cols]
    Xq = cell.Xq[:, cols]
    if extra_sidecars:
        Xtr = np.hstack([Xtr] + [np.asarray(sc[:, cell.train_idx], dtype=np.float32).T for sc in extra_sidecars])
        Xq = np.hstack([Xq] + [np.asarray(sc[:, cell.q], dtype=np.float32).T for sc in extra_sidecars])
    t0 = time.time()
    m = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    t0 = time.time()
    p = m.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=round(t_fit, 3), predict_s=round(time.time() - t0, 3), n_features=int(Xtr.shape[1]))


def emit_dots(cell: Cell, p: np.ndarray, *, shielded: bool, min_dist: float) -> tuple[np.ndarray, dict]:
    k = int(round(KFRAC * cell.dom_c.sum()))
    if shielded:
        s_crop, top, diag = cell.candidates_flank_shielded(
            p, k, flank_radius_px=FLANK_RADIUS_PX, tip_preserve_threshold=TIP_PRESERVE_THR
        )
    else:
        s_crop, top = cell.candidates(p, k)
        diag = {"selected_top_k": int(np.count_nonzero(top))}
    return score_ordered_dots(s_crop, top, min_dist), diag


def run_h66_1(draws: list[int], out: Path) -> None:
    cells_path, design_path = out / "cells.jsonl", out / "design.json"
    design = dict(
        experiment="H66-1",
        hypothesis="2x2 factorial: Factor G (MGD cation/chalcedony disequilibrium + natural spring upflow + Efimov F-ridge) x Factor C (tip-preserved flank shielding r=2.5px, tip>=0.05) on H35 detector at min_dist=3.0px",
        preregistration="knowledge/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md",
        draws=draws,
        folds=list(FOLD_IDS),
        kfrac=KFRAC,
        min_dist_primary=MIN_DIST_PRIMARY,
        min_dist_h35_control=MIN_DIST_H35_CTRL,
        flank_radius_px=FLANK_RADIUS_PX,
        tip_preserve_threshold=TIP_PRESERVE_THR,
        mgd_columns=H66_MGD_NAMES,
        h34_columns=H34_NAMES,
        arms=["CTRL_BDE7", "CTRL_H35_24", "G0_C0", "G1_C0", "G0_C1", "G1_C1"],
        primary_arm="G1_C1",
        controls=["CTRL_BDE7", "CTRL_H35_24", "G0_C0"],
        evaluator=EVALUATOR,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010, mean_hug_increase_max=0.10),
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    work, ext_dir = work_dir(), data_dir() / "external"
    ctx = load_context(work)
    h34_sc = load_h34_sidecar(work, ctx.fi)
    mgd_sc = load_h66_mgd_sidecar(work, ext_dir, ctx.foot, ctx.fi)
    bde7_cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    bde7_tip_cols = bde7_cols + [ctx.col["H27_tip"]]

    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = canary_sidecar(cell, mgd_sc, H66_MGD_NAMES)
                max_can = max(v["canary_auc"] for v in canary.values())
                if max_can > LEAKAGE_AUC_CAP:
                    raise RuntimeError(f"LEAKAGE CANARY TRIGGERED in H66-1 fold={fold} draw={draw}: {canary}")

                # Fit 1: CTRL_BDE7
                p_bde7, t_bde7 = fit_predict_custom(cell, bde7_cols, [], seed=draw)
                em_bde7, _ = emit_dots(cell, p_bde7, shielded=False, min_dist=MIN_DIST_PRIMARY)
                ev_bde7 = cell.evaluate(em_bde7)
                row_bde7 = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm="CTRL_BDE7",
                                auc=cell.auc(p_bde7), feature_auc_canary=canary, **ev_bde7, **t_bde7)
                sink.write(json.dumps(row_bde7) + "\n")
                del p_bde7

                # Fit 2: H35 (shared across CTRL_H35_24, G0_C0, G0_C1!)
                p_g0, t_g0 = fit_predict_custom(cell, bde7_tip_cols, [h34_sc], seed=draw)
                auc_g0 = cell.auc(p_g0)
                for arm_nm, sh, md in (
                    ("CTRL_H35_24", False, MIN_DIST_H35_CTRL),
                    ("G0_C0", False, MIN_DIST_PRIMARY),
                    ("G0_C1", True, MIN_DIST_PRIMARY),
                ):
                    em, diag = emit_dots(cell, p_g0, shielded=sh, min_dist=md)
                    ev = cell.evaluate(em)
                    row = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm_nm,
                               auc=auc_g0, shield_diag=diag, feature_auc_canary=canary, **ev, **t_g0)
                    sink.write(json.dumps(row) + "\n")
                del p_g0

                # Fit 3: H35 + MGD-F (shared across G1_C0 and G1_C1!)
                p_g1, t_g1 = fit_predict_custom(cell, bde7_tip_cols, [h34_sc, mgd_sc], seed=draw)
                auc_g1 = cell.auc(p_g1)
                for arm_nm, sh in (("G1_C0", False), ("G1_C1", True)):
                    em, diag = emit_dots(cell, p_g1, shielded=sh, min_dist=MIN_DIST_PRIMARY)
                    ev = cell.evaluate(em)
                    row = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm_nm,
                               auc=auc_g1, shield_diag=diag, feature_auc_canary=canary, **ev, **t_g1)
                    sink.write(json.dumps(row) + "\n")
                    print(f"[{time.time()-t_all:.0f}s] H66-1 f={fold}({FOLDS[fold]}) d={draw} {arm_nm}: "
                          f"DTI={ev['dti']:.6f} emit={ev['emitted']} hug={ev['hug']:.3f} max_canary={max_can:.3f}",
                          flush=True)
                sink.flush()
                del p_g1, cell
    print(f"DONE H66-1 -> {cells_path} in {time.time()-t_all:.1f}s", flush=True)


def run_h66_2(draws: list[int], out: Path) -> None:
    cells_path, design_path = out / "cells.jsonl", out / "design.json"
    design = dict(
        experiment="H66-2",
        hypothesis="Neotectonically reactivated SGMC bedrock faults (SGMC x 3DEP LiDAR strike/step + SGMC x geodetic strain/gravity) vs ungated SGMC and same-run H35 controls",
        preregistration="knowledge/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md",
        caveat="IR-25-SGMC-PROXY-CONTAMINATION: compilation-overlap risk disclosed alongside physics-gated vs ungated ablation",
        draws=draws,
        folds=list(FOLD_IDS),
        kfrac=KFRAC,
        min_dist_primary=MIN_DIST_PRIMARY,
        min_dist_h35_control=MIN_DIST_H35_CTRL,
        sgmc_columns=H66_SGMC_NAMES,
        arms=["CTRL_H35_24", "CTRL_H35_C1", "SGMC_REACT_ONLY", "SGMC_ALL3"],
        primary_arm="SGMC_REACT_ONLY",
        controls=["CTRL_H35_24", "CTRL_H35_C1"],
        evaluator=EVALUATOR,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010, mean_hug_increase_max=0.10),
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    work, ext_dir = work_dir(), data_dir() / "external"
    ctx = load_context(work)
    h34_sc = load_h34_sidecar(work, ctx.fi)
    sgmc_sc = load_h66_sgmc_sidecar(work, ext_dir, ctx.static, ctx.static_names, ctx.foot, ctx.fi)
    sgmc_react_sc = sgmc_sc[1:3]  # ONLY [H66_sgmc_scarp_compat, H66_sgmc_strain_react]
    bde7_tip_cols = ctx.columns(BASE) + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]

    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = canary_sidecar(cell, sgmc_sc, H66_SGMC_NAMES)
                max_can = max(v["canary_auc"] for v in canary.values())
                if max_can > LEAKAGE_AUC_CAP:
                    raise RuntimeError(f"LEAKAGE CANARY TRIGGERED in H66-2 fold={fold} draw={draw}: {canary}")

                # Controls from H35
                p_ctrl, t_ctrl = fit_predict_custom(cell, bde7_tip_cols, [h34_sc], seed=draw)
                auc_ctrl = cell.auc(p_ctrl)
                for arm_nm, sh, md in (("CTRL_H35_24", False, MIN_DIST_H35_CTRL), ("CTRL_H35_C1", True, MIN_DIST_PRIMARY)):
                    em, diag = emit_dots(cell, p_ctrl, shielded=sh, min_dist=md)
                    ev = cell.evaluate(em)
                    sink.write(json.dumps(dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm_nm,
                                               auc=auc_ctrl, shield_diag=diag, feature_auc_canary=canary,
                                               **ev, **t_ctrl)) + "\n")
                del p_ctrl

                # Primary arm: SGMC_REACT_ONLY (excludes ungated H66_sgmc_prox4)
                p_react, t_react = fit_predict_custom(cell, bde7_tip_cols, [h34_sc, sgmc_react_sc], seed=draw)
                em_react, diag_react = emit_dots(cell, p_react, shielded=True, min_dist=MIN_DIST_PRIMARY)
                ev_react = cell.evaluate(em_react)
                sink.write(json.dumps(dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm="SGMC_REACT_ONLY",
                                           auc=cell.auc(p_react), shield_diag=diag_react, feature_auc_canary=canary,
                                           **ev_react, **t_react)) + "\n")
                del p_react

                # Diagnostic arm: SGMC_ALL3 (includes ungated H66_sgmc_prox4)
                p_all, t_all3 = fit_predict_custom(cell, bde7_tip_cols, [h34_sc, sgmc_sc], seed=draw)
                em_all, diag_all = emit_dots(cell, p_all, shielded=True, min_dist=MIN_DIST_PRIMARY)
                ev_all = cell.evaluate(em_all)
                sink.write(json.dumps(dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm="SGMC_ALL3",
                                           auc=cell.auc(p_all), shield_diag=diag_all, feature_auc_canary=canary,
                                           **ev_all, **t_all3)) + "\n")
                sink.flush()
                print(f"[{time.time()-t_all:.0f}s] H66-2 f={fold}({FOLDS[fold]}) d={draw}: "
                      f"REACT={ev_react['dti']:.6f} ALL3={ev_all['dti']:.6f} max_canary={max_can:.3f}", flush=True)
                del p_all, cell
    print(f"DONE H66-2 -> {cells_path} in {time.time()-t_all:.1f}s", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp", choices=("h66_1", "h66_2"), required=True)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "cells.jsonl").exists() or (out / "design.json").exists():
        raise SystemExit(f"Refusing to overwrite existing evidence directory {out}")
    if args.exp == "h66_1":
        run_h66_1(list(args.draws), out)
    else:
        run_h66_2(list(args.draws), out)


if __name__ == "__main__":
    main()
