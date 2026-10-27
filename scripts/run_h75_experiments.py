#!/usr/bin/env python3
"""Pre-registered H75 (EU3D-POE) & 25-km Checkerboard BlockHoldout runner.

Pre-registered in ``knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md``
(committed at ``3053f69`` before writing ``src/gems25/h75_eu3d.py`` or fitting any model).

Modes:
  --mode block25km  ``BlockHoldout(..., block_size_px=250)`` on virgin draws 130, 131 (Experiment 1)
  --mode standard   shared ``Holdout(..., hide_frac=0.20)`` on virgin draws 132, 133 (Experiment 2)
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.block_holdout import BlockHoldout  # noqa: E402
from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.greedy import greedy_dots  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h72_pttg import H72_VCCD_NAMES, load_h72_vccd_sidecar  # noqa: E402
from gems25.h73_pm import propensity_matched_negatives  # noqa: E402
from gems25.h74_rmps import H74_RMPS_NAMES, load_h74_rmps_sidecar  # noqa: E402
from gems25.h75_eu3d import H75_EU3D_NAMES, load_h75_eu3d_sidecar, poe_combine  # noqa: E402
from gems25.holdout import FOLD_NAMES  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from gems25.validation import feature_canary  # noqa: E402
from run_h28_holdout import EXTRAS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
KFRAC_H35, MIN_DIST_H35 = 0.035, 2.4
KFRAC_PM, MIN_DIST_PM, CAT_BUF_PM = 0.030, 2.8, 2.0
KFRAC_BLIND, CAT_BUF_BLIND, FULL_B2_BUDGET = 0.035, 2.0, 37_654
SUBSURF_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm")
SCARP_VCCD_COLS = ("RBDT_throw_dipole", "RBDT_non_shoreline_scarp")
LEAKAGE_AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px)"


def file_sha256(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def emit_sapd(
    grid_buf: np.ndarray,
    fi_q: np.ndarray,
    sl: tuple,
    dom_c: np.ndarray,
    known_c: np.ndarray,
    d_vis_c: np.ndarray,
    score_q: np.ndarray,
    *,
    kfrac: float,
    min_dist: float,
    cat_buf_px: float = 0.0,
) -> tuple[np.ndarray, dict]:
    t0 = time.time()
    grid_buf[:] = 0.0
    grid_buf.ravel()[fi_q] = np.nan_to_num(score_q, nan=0.0).astype(np.float32)
    s_crop = grid_buf[sl].copy()
    grid_buf[:] = 0.0
    r = ridge_nms(s_crop, dom_c, 1.0)
    excl = known_c if cat_buf_px <= 0.0 else (known_c | (d_vis_c <= cat_buf_px))
    s_clean = np.where(r & ~excl, s_crop, 0.0)
    k = int(round(kfrac * float(dom_c.sum())))
    top = select_top_positive(s_clean, dom_c, k)
    dots = score_ordered_dots(s_clean, top, min_dist)
    return dots, dict(emit_s=round(time.time() - t0, 3), pool_k=k, n_emitted=int(dots.sum()))


def emit_blind_submod(
    grid_buf: np.ndarray,
    fi_q: np.ndarray,
    sl: tuple,
    dom_c: np.ndarray,
    known_c: np.ndarray,
    d_vis_c: np.ndarray,
    score_q: np.ndarray,
    dom_full_px: float,
) -> tuple[np.ndarray, dict]:
    t0 = time.time()
    grid_buf[:] = 0.0
    grid_buf.ravel()[fi_q] = np.nan_to_num(score_q, nan=0.0).astype(np.float32)
    s_crop = grid_buf[sl].copy()
    grid_buf[:] = 0.0
    excl = known_c | (d_vis_c <= CAT_BUF_BLIND)
    r = ridge_nms(s_crop, dom_c, 1.0)
    s_clean = np.where(r & ~excl, s_crop, 0.0)
    k = int(round(KFRAC_BLIND * float(dom_c.sum())))
    top = select_top_positive(s_clean, dom_c, k)
    n_vis_dom = int((known_c & dom_c).sum())
    n_hat = max(0.25 * float(n_vis_dom), 100.0)
    max_dots_q = int(round(float(FULL_B2_BUDGET) * float(dom_c.sum()) / float(dom_full_px)))
    dots, gdiag = greedy_dots(s_crop, top, dom_c, excl, n_hat, max_dots=max_dots_q)
    return dots, dict(
        emit_s=round(time.time() - t0, 3),
        pool_k=k,
        max_dots_q=max_dots_q,
        n_emitted=int(dots.sum()),
        stop_reason=gdiag["stop_reason"],
        plugin_dti=round(float(gdiag["plugin_dti"]), 6),
    )


def fit_predict(Xtr: np.ndarray, y: np.ndarray, Xq: np.ndarray, seed: int) -> tuple[np.ndarray, dict]:
    t0 = time.time()
    clf = HistGradientBoostingClassifier(random_state=int(seed), **HGB_PARAMS).fit(Xtr, y)
    fit_s = time.time() - t0
    t0 = time.time()
    p = clf.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=round(fit_s, 3), predict_s=round(time.time() - t0, 3), n_features=int(Xtr.shape[1]))


def eval_arm(
    em: np.ndarray,
    truth_c: np.ndarray,
    dom_c: np.ndarray,
    known_c: np.ndarray,
    d_vis_c: np.ndarray,
    auc: float,
    truth_strata: dict,
    meta: dict,
) -> dict:
    ev = dti_binary(em, truth_c, dom_c, known_c)
    far_mask = d_vis_c > 9.0
    far = dti_binary(em & far_mask, truth_c & far_mask, dom_c, known_c)
    vfar_mask = d_vis_c > 20.0
    vfar = dti_binary(em & vfar_mask, truth_c & vfar_mask, dom_c, known_c)
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
        vfar_gt20_dti=round(float(vfar["dti"]), 6),
        vfar_gt20_tp=float(vfar["tp"]),
        vfar_gt20_fp=float(vfar["fp"]),
        vfar_gt20_n_truth=int(vfar["n_truth"]),
        emitted_strata=strata,
        truth_strata=truth_strata,
        **meta,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("block25km", "standard"), required=True)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--resume", action="store_true", help="Resume an interrupted run without refitting completed (fold, draw) cells")
    args = ap.parse_args()

    out = Path(args.out)
    completed_cells: set[tuple[int, int]] = set()
    if out.exists():
        if not args.resume:
            raise SystemExit(f"Refusing to overwrite existing evidence directory: {out}")
        cells_file = out / "cells.jsonl"
        if cells_file.exists():
            existing_rows = [json.loads(line) for line in cells_file.read_text().splitlines() if line.strip()]
            from collections import Counter
            counts = Counter((int(r["fold"]), int(r["draw"])) for r in existing_rows)
            expected_arms = 6 if args.mode == "block25km" else 7
            completed_cells = {k for k, cnt in counts.items() if cnt == expected_arms}
            # Keep only complete cells if a partial cell was interrupted mid-write
            clean_rows = [r for r in existing_rows if (int(r["fold"]), int(r["draw"])) in completed_cells]
            cells_file.write_text("".join(json.dumps(r) + "\n" for r in clean_rows))
            print(f"Resuming {out}: {len(completed_cells)} complete cells preserved {sorted(completed_cells)}", flush=True)
    else:
        out.mkdir(parents=True, exist_ok=False)

    work = work_dir()
    data = data_dir()
    t_start = time.time()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")

    h34_mm = load_h34_sidecar(work, ctx.fi)
    vccd_mm = load_h72_vccd_sidecar(work, data / "external", ctx.fi)
    h74_mm = load_h74_rmps_sidecar(work, ctx.fi)
    h75_mm = load_h75_eu3d_sidecar(work, ctx.fi)

    if args.mode == "block25km":
        holdout = BlockHoldout(ctx.foot, ctx.labels, hide_frac=0.20, block_size_px=250)
        fold_names = list(BlockHoldout.FOLD_NAMES)
        arms = ("CTRL_H35", "PM_DEAPRON", "SCARP_ONLY", "ROOT_H75", "H75_POE50", "H75_POE65")
    else:
        holdout = ctx.holdout
        fold_names = list(FOLD_NAMES)
        arms = ("CTRL_H35", "PM_DEAPRON", "SCARP_ONLY", "ROOT_H75", "H75_POE50", "H75_POE65", "H75_APRON")

    dom_full = binary_erosion(ctx.foot, iterations=DOMAIN_ERODE)
    dom_full_px = float(dom_full.sum())

    # Union matrix columns:
    # [0 .. 63]   static ABCD (64)
    # [64 .. 70]  dynamic E (7)
    # [71 .. 77]  EXTRAS (7)
    # [78]        dynamic H27_tip (1)
    # [79 .. 80]  static S_dem_c2, S_dem_s2 from ctx.addon[3:5] (2)
    # [81 .. 82]  static RBDT_throw_dipole, RBDT_non_shoreline_scarp from vccd_mm[2:4] (2)
    # [83 .. 85]  static H34 (3)
    # [86 .. 89]  static H74_RMPS (4)
    # [90 .. 93]  static H75_EU3D (4)
    rbdt_idxs_in_vccd = [H72_VCCD_NAMES.index(n) for n in SCARP_VCCD_COLS]
    union_names = (
        list(ctx.static_names)
        + list(ctx.e_names)
        + list(ctx.extra_names)
        + ["H27_tip", "S_dem_c2", "S_dem_s2"]
        + list(SCARP_VCCD_COLS)
        + list(H34_NAMES)
        + list(H74_RMPS_NAMES)
        + list(H75_EU3D_NAMES)
    )
    assert len(union_names) == 94
    ucol = {n: i for i, n in enumerate(union_names)}

    bde_extra_cols = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("BDE")] + list(EXTRAS))]
    b_only_cols = [ucol[n] for n in [ctx.all_names[i] for i in ctx.columns("B")]]
    acd_sub_cols = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("ACD")] + list(SUBSURF_EXTRAS))]
    tip_idx = ucol["H27_tip"]
    sdem_idxs = [ucol["S_dem_c2"], ucol["S_dem_s2"]]
    rbdt_idxs = [ucol[n] for n in SCARP_VCCD_COLS]
    h34_idxs = [ucol[n] for n in H34_NAMES]
    h74_idxs = [ucol[n] for n in H74_RMPS_NAMES]
    h75_idxs = [ucol[n] for n in H75_EU3D_NAMES]

    arm_cols = {
        "CTRL_H35": bde_extra_cols + [tip_idx] + h34_idxs,                      # 59 cols
        "PM_DEAPRON": bde_extra_cols + [tip_idx] + h34_idxs,                    # 59 cols (PM sampler)
        "SCARP_ONLY": b_only_cols + sdem_idxs + rbdt_idxs,                      # 28 cols (pure scarp)
        "ROOT_H75": acd_sub_cols + h34_idxs + h74_idxs + h75_idxs,              # 55 cols (pure subsurface)
        "H75_APRON": bde_extra_cols + [tip_idx] + h34_idxs + h75_idxs,          # 63 cols
    }
    assert len(arm_cols["SCARP_ONLY"]) == 28
    assert len(arm_cols["ROOT_H75"]) == 55
    assert not any(union_names[i].startswith(("A_", "C_", "D_", "E_")) for i in arm_cols["SCARP_ONLY"])
    assert not any(union_names[i].startswith(("B_", "L_", "E_")) for i in arm_cols["ROOT_H75"])

    design = dict(
        experiment=f"H75_{args.mode.upper()}",
        mode=args.mode,
        preregistration="knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md",
        preregistration_commit="3053f69",
        draws=list(args.draws),
        folds=list(FOLD_IDS),
        fold_names=fold_names,
        arms=list(arms),
        arm_feature_counts={
            k: len(arm_cols[k]) if k in arm_cols else "PoE(28 scarp x 55 root)"
            for k in arms
        },
        n_neg=int(N_NEG),
        hgb_params=HGB_PARAMS,
        kfrac_h35=KFRAC_H35,
        min_dist_h35=MIN_DIST_H35,
        kfrac_pm=KFRAC_PM,
        min_dist_pm=MIN_DIST_PM,
        cat_buf_pm=CAT_BUF_PM,
        kfrac_blind=KFRAC_BLIND,
        cat_buf_blind=CAT_BUF_BLIND,
        full_b2_budget=FULL_B2_BUDGET,
        block_size_px=250 if args.mode == "block25km" else None,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        evaluator=EVALUATOR,
        evaluator_hashes={
            "src/gems25/holdout.py": file_sha256("src/gems25/holdout.py"),
            "src/gems25/block_holdout.py": file_sha256("src/gems25/block_holdout.py"),
            "src/gems25/metric.py": file_sha256("src/gems25/metric.py"),
            "src/gems25/validation.py": file_sha256("src/gems25/validation.py"),
            "src/gems25/h75_eu3d.py": file_sha256("src/gems25/h75_eu3d.py"),
        },
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    def build_union_matrix(e_mat: np.ndarray, tip_vec: np.ndarray, idx: np.ndarray) -> np.ndarray:
        X = np.empty((idx.size, 94), dtype=np.float32)
        gather_columns(ctx, e_mat, idx, True, out=X)
        X[:, 78] = tip_vec[idx]
        X[:, 79:81] = np.asarray(ctx.addon[3:5, idx], dtype=np.float32).T
        X[:, 81:83] = np.asarray(vccd_mm[rbdt_idxs_in_vccd][:, idx], dtype=np.float32).T
        X[:, 83:86] = np.asarray(h34_mm[:, idx], dtype=np.float32).T
        X[:, 86:90] = np.asarray(h74_mm[:, idx], dtype=np.float32).T
        X[:, 90:94] = np.asarray(h75_mm[:, idx], dtype=np.float32).T
        return X

    grid_buf = np.zeros(ctx.foot.shape, dtype=np.float32)
    canary_records = []

    open_mode = "a" if args.resume else "w"
    with (out / "cells.jsonl").open(open_mode) as sink:
        for fold in FOLD_IDS:
            for draw_id in args.draws:
                t_cell = time.time()
                cell_already_done = (fold, draw_id) in completed_cells
                d = holdout.draw(fold, draw_id)
                sl = d.bbox
                dom_c = dom_full[sl] & d.quadrant[sl]
                known_c = d.visible[sl] & d.quadrant[sl]
                truth_c = d.hidden_test[sl] & dom_c & ~known_c

                d_vis_grid = distance_transform_edt(~d.visible)
                d_vis_c = d_vis_grid[sl].astype(np.float32)
                d_vis_vec = d_vis_grid.ravel()[ctx.fi]
                del d_vis_grid

                tv = d_vis_c[truth_c]
                truth_strata = dict(
                    n_truth=int(truth_c.sum()),
                    frac_le2=round(float((tv <= 2.0).mean()), 5) if tv.size else 0.0,
                    frac_2_9=round(float(((tv > 2.0) & (tv <= 9.0)).mean()), 5) if tv.size else 0.0,
                    frac_9_20=round(float(((tv > 9.0) & (tv <= 20.0)).mean()), 5) if tv.size else 0.0,
                    frac_gt20=round(float((tv > 20.0).mean()), 5) if tv.size else 0.0,
                    median_d_vis=round(float(np.median(tv)), 3) if tv.size else 0.0,
                )

                e_mat = build_catalogue_features(d.visible, ctx.fi)
                tip_vec = build_tip_continuation(d.visible, ctx.foot, ctx.fi)

                # Uniform training sample (identical rule to gems25.experiment.Cell)
                rng = np.random.default_rng(777 + 31 * fold + draw_id)
                pos = ctx.vec(d.hidden_train)
                near = distance_transform_edt(~d.hidden_train) <= 1.5
                cand = ctx.vec(d.train_region & ~ctx.labels & ~near)
                neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
                train_idx = np.sort(np.concatenate([pos, neg]))
                y_tr = np.isin(train_idx, pos).astype(np.int8)

                # Propensity-matched training sample (frozen H73-PM / H73-BW rule)
                neg_pm, pm_diag = propensity_matched_negatives(
                    d_vis_vec, pos, cand, min(N_NEG, int(cand.size)), seed=777 + 31 * fold + draw_id + 5000
                )
                tr_pm = np.sort(np.concatenate([pos, neg_pm]))
                y_pm = np.isin(tr_pm, pos).astype(np.int8)

                q_idx = ctx.vec(d.quadrant)
                fi_q = ctx.fi[q_idx]

                # Scored test-domain sample for AUC & standalone feature leakage canaries
                q_truth_mask = np.zeros(ctx.foot.shape, dtype=bool)
                q_truth_mask[sl] = truth_c
                q_bg_mask = np.zeros(ctx.foot.shape, dtype=bool)
                q_bg_mask[sl] = dom_c & ~known_c & ~truth_c
                pos_q_full = ctx.vec(q_truth_mask)
                bg_q_full = ctx.vec(q_bg_mask)
                auc_pos = np.searchsorted(q_idx, pos_q_full)
                auc_neg = np.searchsorted(
                    q_idx,
                    rng.choice(bg_q_full, size=min(100_000, bg_q_full.size), replace=False),
                )
                auc_idx = np.concatenate([auc_pos, auc_neg])
                y_auc = np.concatenate([np.ones(auc_pos.size, np.int8), np.zeros(auc_neg.size, np.int8)])

                Xq_u = build_union_matrix(e_mat, tip_vec, q_idx)

                # Standalone leakage canary on EVERY column + (-d_vis)
                feat_can = {}
                for ci, nm in enumerate(union_names):
                    fc = feature_canary(np.asarray(Xq_u[auc_idx, ci], dtype=np.float64), y_auc, cap=LEAKAGE_AUC_CAP)
                    feat_can[nm] = fc
                    if not fc["passed"]:
                        raise RuntimeError(f"LEAKAGE CANARY FAILED fold={fold} draw={draw_id} col={nm}: {fc}")
                fc_dvis = feature_canary(-d_vis_vec[q_idx][auc_idx].astype(np.float64), y_auc, cap=LEAKAGE_AUC_CAP)
                feat_can["NEG_D_VIS"] = fc_dvis
                if not fc_dvis["passed"]:
                    raise RuntimeError(f"LEAKAGE CANARY FAILED fold={fold} draw={draw_id} NEG_D_VIS: {fc_dvis}")

                worst_col = max(feat_can, key=lambda k: feat_can[k]["canary_auc"])
                worst_h75_col = max(H75_EU3D_NAMES, key=lambda k: feat_can[k]["canary_auc"])
                canary_records.append(
                    dict(
                        fold=fold,
                        fold_name=fold_names[fold],
                        draw=draw_id,
                        n_columns_checked=len(feat_can),
                        all_passed=True,
                        worst_column=worst_col,
                        worst_canary_auc=round(float(feat_can[worst_col]["canary_auc"]), 6),
                        worst_h75_column=worst_h75_col,
                        worst_h75_canary_auc=round(float(feat_can[worst_h75_col]["canary_auc"]), 6),
                        h75_canaries={k: round(float(feat_can[k]["canary_auc"]), 6) for k in H75_EU3D_NAMES},
                        neg_d_vis_canary_auc=round(float(fc_dvis["canary_auc"]), 6),
                    )
                )
                if cell_already_done:
                    del e_mat, tip_vec, Xq_u
                    gc.collect()
                    print(f"[{args.mode} f={fold} d={draw_id}] canary verified (max={feat_can[worst_col]['canary_auc']:.4f}); cell already fitted", flush=True)
                    continue

                Xtr_u = build_union_matrix(e_mat, tip_vec, train_idx)
                Xpm_u = build_union_matrix(e_mat, tip_vec, tr_pm)
                del e_mat, tip_vec

                def _auc(prob_q: np.ndarray) -> float:
                    vals = prob_q[auc_idx]
                    return float(roc_auc_score(y_auc, vals)) if np.unique(vals).size > 1 else 0.5

                # 1. CTRL_H35
                c_h35 = arm_cols["CTRL_H35"]
                p_h35, m_h35 = fit_predict(Xtr_u[:, c_h35], y_tr, Xq_u[:, c_h35], seed=draw_id)
                em_h35, ed_h35 = emit_sapd(
                    grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_h35, kfrac=KFRAC_H35, min_dist=MIN_DIST_H35
                )

                # 2. PM_DEAPRON (completes H73-BW on BlockHoldout!)
                p_pm, m_pm = fit_predict(Xpm_u[:, c_h35], y_pm, Xq_u[:, c_h35], seed=draw_id)
                em_pm, ed_pm = emit_sapd(
                    grid_buf,
                    fi_q,
                    sl,
                    dom_c,
                    known_c,
                    d_vis_c,
                    p_pm,
                    kfrac=KFRAC_PM,
                    min_dist=MIN_DIST_PM,
                    cat_buf_px=CAT_BUF_PM,
                )
                del Xpm_u

                # 3. SCARP_ONLY
                c_scarp = arm_cols["SCARP_ONLY"]
                p_scarp, m_scarp = fit_predict(Xtr_u[:, c_scarp], y_tr, Xq_u[:, c_scarp], seed=draw_id)
                em_scarp, ed_scarp = emit_blind_submod(
                    grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_scarp, dom_full_px
                )

                # 4. ROOT_H75
                c_root = arm_cols["ROOT_H75"]
                p_root, m_root = fit_predict(Xtr_u[:, c_root], y_tr, Xq_u[:, c_root], seed=draw_id)
                em_root, ed_root = emit_blind_submod(
                    grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_root, dom_full_px
                )

                # 5 & 6. Two-stage multiplicative Product-of-Experts (PoE)
                p_poe50 = poe_combine(p_scarp, p_root, gamma=0.50)
                em_poe50, ed_poe50 = emit_blind_submod(
                    grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_poe50, dom_full_px
                )

                p_poe65 = poe_combine(p_scarp, p_root, gamma=0.65)
                em_poe65, ed_poe65 = emit_blind_submod(
                    grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_poe65, dom_full_px
                )

                arm_payloads = [
                    ("CTRL_H35", em_h35, _auc(p_h35), {**m_h35, **ed_h35}),
                    ("PM_DEAPRON", em_pm, _auc(p_pm), {**m_pm, **ed_pm, "pm_n_neg": pm_diag["n_neg"]}),
                    ("SCARP_ONLY", em_scarp, _auc(p_scarp), {**m_scarp, **ed_scarp}),
                    ("ROOT_H75", em_root, _auc(p_root), {**m_root, **ed_root}),
                    ("H75_POE50", em_poe50, _auc(p_poe50), {"gamma": 0.50, **ed_poe50}),
                    ("H75_POE65", em_poe65, _auc(p_poe65), {"gamma": 0.65, **ed_poe65}),
                ]

                if "H75_APRON" in arms:
                    c_apr = arm_cols["H75_APRON"]
                    p_apr, m_apr = fit_predict(Xtr_u[:, c_apr], y_tr, Xq_u[:, c_apr], seed=draw_id)
                    em_apr, ed_apr = emit_sapd(
                        grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_apr, kfrac=KFRAC_H35, min_dist=MIN_DIST_H35
                    )
                    arm_payloads.append(("H75_APRON", em_apr, _auc(p_apr), {**m_apr, **ed_apr}))

                del Xtr_u, Xq_u
                gc.collect()

                base_meta = dict(
                    mode=args.mode,
                    fold=fold,
                    fold_name=fold_names[fold],
                    draw=draw_id,
                    canary_worst_auc=round(float(feat_can[worst_col]["canary_auc"]), 6),
                    canary_worst_h75_auc=round(float(feat_can[worst_h75_col]["canary_auc"]), 6),
                )
                summary_parts = []
                for arm_name, em_mask, auc_val, extra_meta in arm_payloads:
                    row = eval_arm(
                        em_mask,
                        truth_c,
                        dom_c,
                        known_c,
                        d_vis_c,
                        auc_val,
                        truth_strata,
                        {**base_meta, "arm": arm_name, **extra_meta},
                    )
                    sink.write(json.dumps(row) + "\n")
                    summary_parts.append(f"{arm_name}={row['dti']:.4f}")
                sink.flush()
                print(
                    f"[{args.mode} f={fold}({fold_names[fold]}) d={draw_id}] truth={truth_c.sum():,} "
                    f"(med_d={truth_strata['median_d_vis']:.1f}px) "
                    + " ".join(summary_parts)
                    + f" ({time.time() - t_cell:.1f}s)",
                    flush=True,
                )

    (out / "feature_canaries.json").write_text(json.dumps(canary_records, indent=1) + "\n")
    print(f"Completed {args.mode} draws={args.draws} in {time.time() - t_start:.1f}s -> {out}")


if __name__ == "__main__":
    main()
