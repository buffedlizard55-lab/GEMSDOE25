#!/usr/bin/env python3
"""Pre-registered H73-PM holdout runner (knowledge/32_preregistered_h73_pm_2026-10-26.md).

Arms per (fold, draw) cell, all paired on the shared hide-and-recover draw:
  CTRL_H35     exact incumbent (BDE+EXTRAS+H27_tip+H34, uniform negatives, H35 emission)
  CTRL_BLIND_BD catalogue-free control (BD+EXTRAS+H34, uniform negatives, de-apron emission)
  PM_H35       CTRL_H35 columns + propensity-matched negatives, H35 emission
  PM_DEAPRON   same PM surface, de-apron emission

Refuses to overwrite existing evidence; writes design.json before any fit.

    .venv/bin/python scripts/run_h73_pm.py --draws 90 91 --out evidence/h73_pm_screen
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
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import HGB_PARAMS, N_NEG, Cell, gather_columns, load_context  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h73_pm import propensity_matched_negatives  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from gems25.validation import feature_canary  # noqa: E402
from run_h28_holdout import EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
KFRAC_H35, MIN_DIST_H35 = 0.035, 2.4
KFRAC_DEAPRON, MIN_DIST_DEAPRON, CAT_BUF_DEAPRON = 0.030, 2.8, 2.0
LEAKAGE_AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px) via gems25.experiment.Cell.evaluate"
ARMS = ["CTRL_H35", "CTRL_BLIND_BD", "PM_H35", "PM_DEAPRON"]


def emit(cell: Cell, score_q: np.ndarray, d_vis_c: np.ndarray, *, kfrac: float, min_dist: float, cat_buf_px: float) -> np.ndarray:
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


def eval_full(cell: Cell, em: np.ndarray, d_vis_c: np.ndarray, auc: float, meta: dict) -> dict:
    ev = cell.evaluate(em)
    far_mask = d_vis_c > 9.0
    far = dti_binary(em & far_mask, cell.truth_c & far_mask, cell.dom_c, cell.known_c)
    dv = d_vis_c[em]
    strata = (
        dict(
            frac_le2=round(float((dv <= 2.0).mean()), 5),
            frac_2_9=round(float(((dv > 2.0) & (dv <= 9.0)).mean()), 5),
            frac_9_20=round(float(((dv > 9.0) & (dv <= 20.0)).mean()), 5),
            frac_gt20=round(float((dv > 20.0).mean()), 5),
            median_d_vis=round(float(np.median(dv)), 3),
        )
        if dv.size
        else dict(frac_le2=0.0, frac_2_9=0.0, frac_9_20=0.0, frac_gt20=0.0, median_d_vis=0.0)
    )
    return dict(
        **ev,
        auc=round(float(auc), 6),
        far_gt9_dti=round(float(far["dti"]), 6),
        far_gt9_tp=float(far["tp"]),
        far_gt9_fp=float(far["fp"]),
        far_gt9_n_truth=int(far["n_truth"]),
        strata=strata,
        **meta,
    )


def fit_predict(Xtr: np.ndarray, y: np.ndarray, Xq: np.ndarray, seed: int) -> tuple[np.ndarray, dict]:
    t0 = time.time()
    m = HistGradientBoostingClassifier(random_state=int(seed), **HGB_PARAMS).fit(Xtr, y)
    fit_s = time.time() - t0
    t0 = time.time()
    p = m.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=round(fit_s, 3), predict_s=round(time.time() - t0, 3), n_features=int(Xtr.shape[1]))


def auc_of(cell: Cell, p: np.ndarray) -> float:
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    return float(roc_auc_score(y, p[idx])) if np.unique(p[idx]).size > 1 else 0.5


def gather_like_cell(cell: Cell, idx: np.ndarray) -> np.ndarray:
    """Rebuild Cell._gather rows for arbitrary footprint-vector indices (verified vs cell.Xtr)."""
    ctx = cell.ctx
    ns, ne = ctx.static.shape[0], cell.E.shape[0]
    X = np.empty((idx.size, ns + ne + 7 + 3 + 2), np.float32)
    gather_columns(ctx, cell.E, idx, True, out=X)
    j = ns + ne + 7
    tip = cell.tip[idx]
    scarp = ctx.h27_scarp[idx]
    X[:, j] = tip
    X[:, j + 1] = scarp
    X[:, j + 2] = tip * scarp
    X[:, j + 3] = cell.bridge[idx]
    X[:, j + 4] = ctx.h30_scarp[idx]
    return X


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    design = dict(
        experiment="H73_PM",
        preregistration="knowledge/32_preregistered_h73_pm_2026-10-26.md",
        draws=list(args.draws),
        folds=list(FOLD_IDS),
        fold_names=list(FOLDS),
        arms=ARMS,
        kfrac_h35=KFRAC_H35,
        min_dist_h35=MIN_DIST_H35,
        kfrac_deapron=KFRAC_DEAPRON,
        min_dist_deapron=MIN_DIST_DEAPRON,
        cat_buf_deapron=CAT_BUF_DEAPRON,
        n_neg=N_NEG,
        pm_seed_rule="777 + 31*fold + draw + 5000",
        evaluator=EVALUATOR,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        slot_gate=dict(mean_gain_gt=0.001, paired_ci_lo_gt=0.0, folds_positive_min=3, worst_fold_min=-0.010),
        far_field_screen=dict(pooled_far_dti_gt=["CTRL_H35", "CTRL_BLIND_BD"], folds_positive_vs_blind_min=3, frac_gt20_min=0.35),
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    work = work_dir()
    ctx = load_context(work)
    h34 = load_h34_sidecar(work, ctx.fi)
    h35_cols = ctx.columns("BDE") + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    bd_cols = ctx.columns("BD") + ctx.named(EXTRAS)
    h35_names = [ctx.all_names[i] for i in h35_cols] + list(H34_NAMES)
    verified_gather = False
    t_start = time.time()
    with (out / "cells.jsonl").open("w") as sink:
        for fold in FOLD_IDS:
            for draw in args.draws:
                t_cell = time.time()
                cell = Cell(ctx, fold, draw, extras=True, h27=True, h30=True)
                d = cell.draw
                d_vis_grid = distance_transform_edt(~d.visible)
                d_vis_c = d_vis_grid[cell.sl].astype(np.float32)
                d_vis_vec = d_vis_grid.ravel()[ctx.fi]

                # ---- propensity-matched training sample (frozen rule, knowledge/32 §2) ----
                pos = ctx.vec(d.hidden_train)
                near = distance_transform_edt(~d.hidden_train) <= 1.5
                pool = ctx.vec(d.train_region & ~ctx.labels & ~near)
                neg_pm, pm_diag = propensity_matched_negatives(
                    d_vis_vec, pos, pool, min(N_NEG, int(pool.size)), seed=777 + 31 * fold + draw + 5000
                )
                tr_pm = np.sort(np.concatenate([pos, neg_pm]))
                y_pm = np.isin(tr_pm, pos).astype(np.int8)

                # ---- leakage canaries: every fitted H35 column + (-d_vis), before trusting DTI ----
                auc_idx = np.concatenate([cell.auc_pos, cell.auc_neg])
                y_auc = np.concatenate([np.ones(cell.auc_pos.size, np.int8), np.zeros(cell.auc_neg.size, np.int8)])
                canaries: dict[str, dict] = {}
                for ci, nm in zip(h35_cols, h35_names[: len(h35_cols)]):
                    canaries[nm] = feature_canary(np.asarray(cell.Xq[auc_idx, ci], dtype=np.float64), y_auc, cap=LEAKAGE_AUC_CAP)
                for j, nm in enumerate(H34_NAMES):
                    canaries[nm] = feature_canary(np.asarray(h34[j, cell.q], dtype=np.float64)[auc_idx], y_auc, cap=LEAKAGE_AUC_CAP)
                canaries["NEG_D_VIS"] = feature_canary(-d_vis_vec[cell.q][auc_idx].astype(np.float64), y_auc, cap=LEAKAGE_AUC_CAP)
                bad = {k: v for k, v in canaries.items() if not v["passed"]}
                if bad:
                    raise RuntimeError(f"LEAKAGE CANARY TRIGGERED fold={fold} draw={draw}: {bad}")
                canary_max = max(float(v["canary_auc"]) for v in canaries.values())
                dvis_canary = float(canaries["NEG_D_VIS"]["canary_auc"])

                # ---- fits ----
                Xq_h35 = np.hstack([cell.Xq[:, h35_cols], np.asarray(h34[:, cell.q], dtype=np.float32).T])
                Xtr_h35 = np.hstack([cell.Xtr[:, h35_cols], np.asarray(h34[:, cell.train_idx], dtype=np.float32).T])
                p_h35, m_h35 = fit_predict(Xtr_h35, cell.y, Xq_h35, seed=draw)
                del Xtr_h35

                Xq_bd = np.hstack([cell.Xq[:, bd_cols], np.asarray(h34[:, cell.q], dtype=np.float32).T])
                Xtr_bd = np.hstack([cell.Xtr[:, bd_cols], np.asarray(h34[:, cell.train_idx], dtype=np.float32).T])
                p_bd, m_bd = fit_predict(Xtr_bd, cell.y, Xq_bd, seed=draw)
                del Xtr_bd, Xq_bd

                X_pm_full = gather_like_cell(cell, tr_pm)
                if not verified_gather:
                    pos_in_cell = np.flatnonzero(np.isin(cell.train_idx, tr_pm[:200]))
                    rows = np.searchsorted(tr_pm, cell.train_idx[pos_in_cell])
                    assert np.array_equal(np.nan_to_num(X_pm_full[rows]), np.nan_to_num(cell.Xtr[pos_in_cell])), (
                        "gather_like_cell does not reproduce cell.Xtr"
                    )
                    verified_gather = True
                Xtr_pm = np.hstack([X_pm_full[:, h35_cols], np.asarray(h34[:, tr_pm], dtype=np.float32).T])
                del X_pm_full
                p_pm, m_pm = fit_predict(Xtr_pm, y_pm, Xq_h35, seed=draw)
                del Xtr_pm, Xq_h35

                em_h35 = emit(cell, p_h35, d_vis_c, kfrac=KFRAC_H35, min_dist=MIN_DIST_H35, cat_buf_px=0.0)
                em_bd = emit(cell, p_bd, d_vis_c, kfrac=KFRAC_DEAPRON, min_dist=MIN_DIST_DEAPRON, cat_buf_px=CAT_BUF_DEAPRON)
                em_pm = emit(cell, p_pm, d_vis_c, kfrac=KFRAC_H35, min_dist=MIN_DIST_H35, cat_buf_px=0.0)
                em_pmd = emit(cell, p_pm, d_vis_c, kfrac=KFRAC_DEAPRON, min_dist=MIN_DIST_DEAPRON, cat_buf_px=CAT_BUF_DEAPRON)

                shared = dict(canary_max_auc=round(canary_max, 5), neg_dvis_canary_auc=round(dvis_canary, 5), pm_sampler=pm_diag)
                records = [
                    ("CTRL_H35", em_h35, auc_of(cell, p_h35), m_h35),
                    ("CTRL_BLIND_BD", em_bd, auc_of(cell, p_bd), m_bd),
                    ("PM_H35", em_pm, auc_of(cell, p_pm), m_pm),
                    ("PM_DEAPRON", em_pmd, auc_of(cell, p_pm), m_pm),
                ]
                evs = {}
                for arm, em, aucv, meta in records:
                    rec = dict(fold=fold, fold_name=FOLDS[fold], draw=int(draw), arm=arm,
                               **eval_full(cell, em, d_vis_c, aucv, meta), **shared)
                    sink.write(json.dumps(rec) + "\n")
                    evs[arm] = rec["dti"]
                sink.flush()
                print(
                    f"[{time.time() - t_start:6.1f}s] {FOLDS[fold]} d={draw} ({time.time() - t_cell:.1f}s) | "
                    + " | ".join(f"{k}={v:.5f}" for k, v in evs.items())
                    + f" | canary_max={canary_max:.3f} -dvis={dvis_canary:.3f}",
                    flush=True,
                )
                del cell, d_vis_grid, d_vis_c, d_vis_vec, p_h35, p_bd, p_pm
                gc.collect()
    print(f"DONE in {time.time() - t_start:.1f}s -> {out}")


if __name__ == "__main__":
    main()
