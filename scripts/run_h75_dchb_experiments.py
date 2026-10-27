#!/usr/bin/env python3
"""Pre-registered H75 (DCHB-CG) paired holdout runner across three spatial holdout instruments.

Pre-registered in ``knowledge/38_preregistered_h75_dchb_cg_2026-10-27.md`` (committed at ``12931bb``).

Modes:
  * ``standard``         — Shared ``gems25.holdout.Holdout`` (20% component split per quadrant; Exp 1, draws 120-121)
  * ``block25km``        — Shared ``draw_block25km`` (25-km tile-sampled block split; Exp 2, draws 120-121)
  * ``checkerboard25km`` — Shared ``gems25.block_holdout.BlockHoldout`` (25-km full checkerboard with 100%
                           component hiding in test blocks; Exp 3, virgin draws 122-123)

Arms (recomputed together in every cell — AGENTS.md Rule #5):
  1. CTRL_H35         (59 cols: BDE + EXTRAS + H27_tip + H34, sapd2.4)
  2. H75_APRON        (64 cols: CTRL_H35 + H75_DCHB, sapd2.4)
  3. CTRL_SUBSURF     (51 cols: ACD + SUBSURF_EXTRAS + H34 + H74_RMPS, B2 greedy_dots)
  4. CTRL_BLIND_ABCD  (78 cols: ABCD + EXTRAS + H34 + H74_RMPS, B2 greedy_dots)
  5. H75_CG_BLIND     (54/83/70 cols: M_corridor x M_trace/M_gap gamma=0.60, gap_scale=0.95, B2 greedy_dots)
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
from gems25.h74_rmps import BLOCK_PX_DEFAULT, H74_RMPS_NAMES, draw_block25km, load_h74_rmps_sidecar  # noqa: E402
from gems25.h75_dchb import (  # noqa: E402
    CORRIDOR_GAMMA_DEFAULT,
    H75_CORRIDOR_SUBSET,
    H75_DCHB_NAMES,
    LIDAR_GAP_SCALE_DEFAULT,
    combine_corridor_gated_scores,
    estimate_blind_n_hat,
    load_h75_dchb_sidecar,
)
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from gems25.validation import feature_canary, pooled_dti, pooled_summary  # noqa: E402
from run_h28_holdout import EXTRAS, FOLDS  # noqa: E402

PREREG_PATH = "knowledge/38_preregistered_h75_dchb_cg_2026-10-27.md"
PREREG_COMMIT = "12931bb52bda9195495797590bd66ac073ee5589"
EVALUATOR = "gems25.metric.dti_binary(alpha=0.2,beta=0.8,R=3px)"
FOLD_IDS = (0, 1, 2, 3)
LEAKAGE_AUC_CAP = 0.90
KFRAC_H35 = 0.035
MIN_DIST_H35 = 2.4
KFRAC_BLIND = 0.035
CAT_BUF_BLIND = 2.0
FULL_B2_BUDGET = 37_654
SUBSURF_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm")
ARMS = ("CTRL_H35", "H75_APRON", "CTRL_SUBSURF", "CTRL_BLIND_ABCD", "H75_CG_BLIND")


def file_sha256(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def emit_sapd(
    grid_buf: np.ndarray,
    fi_q: np.ndarray,
    sl: tuple,
    dom_c: np.ndarray,
    known_c: np.ndarray,
    score_q: np.ndarray,
) -> tuple[np.ndarray, dict]:
    t0 = time.time()
    grid_buf[:] = 0.0
    grid_buf.ravel()[fi_q] = np.nan_to_num(score_q, nan=0.0).astype(np.float32)
    s_crop = grid_buf[sl].copy()
    grid_buf[:] = 0.0
    r = ridge_nms(s_crop, dom_c, 1.0)
    s_clean = np.where(r & ~known_c, s_crop, 0.0)
    k = int(round(KFRAC_H35 * float(dom_c.sum())))
    top = select_top_positive(s_clean, dom_c, k)
    dots = score_ordered_dots(s_clean, top, MIN_DIST_H35)
    return dots, dict(emit_s=round(time.time() - t0, 3), pool_k=k, n_emitted=int(dots.sum()))


def emit_blind_submod_any(
    grid_buf: np.ndarray,
    fi_q: np.ndarray,
    sl: tuple,
    dom_c: np.ndarray,
    known_c: np.ndarray,
    d_vis_c: np.ndarray,
    score_q: np.ndarray,
    dom_full_px: float,
    *,
    visible_full: np.ndarray,
    train_region_full: np.ndarray,
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
    n_hat = estimate_blind_n_hat(
        known_c,
        dom_c,
        visible_train=visible_full,
        train_region=train_region_full,
        hide_frac=0.20,
        floor=100.0,
    )
    max_dots_q = int(round(float(FULL_B2_BUDGET) * float(dom_c.sum()) / float(dom_full_px)))
    dots, gdiag = greedy_dots(s_crop, top, dom_c, excl, n_hat, max_dots=max_dots_q)
    return dots, dict(
        emit_s=round(time.time() - t0, 3),
        pool_k=k,
        n_hat=round(float(n_hat), 2),
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
    l_valid_c: np.ndarray,
    auc: float,
    truth_strata: dict,
    meta: dict,
) -> dict:
    ev = dti_binary(em, truth_c, dom_c, known_c)
    far_mask = d_vis_c > 9.0
    far = dti_binary(em & far_mask, truth_c & far_mask, dom_c, known_c)
    vfar_mask = d_vis_c > 20.0
    vfar = dti_binary(em & vfar_mask, truth_c & vfar_mask, dom_c, known_c)
    lgap_mask = ~l_valid_c
    lgap = dti_binary(em & lgap_mask, truth_c & lgap_mask, dom_c & lgap_mask, known_c & lgap_mask)
    dv = d_vis_c[em]
    lgap_emit_share = round(float((~l_valid_c[em]).mean()), 5) if em.any() else 0.0
    strata = (
        dict(
            frac_le2=round(float((dv <= 2.0).mean()), 5),
            frac_2_9=round(float(((dv > 2.0) & (dv <= 9.0)).mean()), 5),
            frac_9_20=round(float(((dv > 9.0) & (dv <= 20.0)).mean()), 5),
            frac_gt20=round(float((dv > 20.0).mean()), 5),
            median_d_vis=round(float(np.median(dv)), 3),
            lidar_gap_emit_share=lgap_emit_share,
        )
        if dv.size
        else dict(frac_le2=0.0, frac_2_9=0.0, frac_9_20=0.0, frac_gt20=0.0, median_d_vis=0.0, lidar_gap_emit_share=0.0)
    )
    return dict(
        **ev,
        auc=round(float(auc), 6),
        far_dti=round(float(far["dti"]), 6),
        far_tp=round(float(far["tp"]), 4),
        far_fp=round(float(far["fp"]), 4),
        far_n_truth=int(far["n_truth"]),
        vfar_dti=round(float(vfar["dti"]), 6),
        vfar_tp=round(float(vfar["tp"]), 4),
        vfar_fp=round(float(vfar["fp"]), 4),
        vfar_n_truth=int(vfar["n_truth"]),
        lgap_dti=round(float(lgap["dti"]), 6),
        lgap_tp=round(float(lgap["tp"]), 4),
        lgap_fp=round(float(lgap["fp"]), 4),
        lgap_n_truth=int(lgap["n_truth"]),
        emit_strata=strata,
        truth_strata=truth_strata,
        **meta,
    )


def pooled_sub_dti(rows: list[dict], prefix: str) -> float:
    tp = sum(float(r[f"{prefix}_tp"]) for r in rows)
    fp = sum(float(r[f"{prefix}_fp"]) for r in rows)
    n = sum(int(r[f"{prefix}_n_truth"]) for r in rows)
    return float(tp / (0.2 * (tp + fp) + 0.8 * n + 1e-7)) if n > 0 else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("standard", "block25km", "checkerboard25km"), required=True)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=False)

    work = work_dir()
    t_start = time.time()
    ctx = load_context(work)
    h34_mm = load_h34_sidecar(work, ctx.fi)
    h74_mm = load_h74_rmps_sidecar(work, ctx.fi)
    h75_mm = load_h75_dchb_sidecar(work, ctx.fi)

    block_holdout = (
        BlockHoldout(ctx.foot, ctx.labels, 0.20, block_size_px=BLOCK_PX_DEFAULT)
        if args.mode == "checkerboard25km"
        else None
    )
    fold_names = list(BlockHoldout.FOLD_NAMES) if block_holdout is not None else list(FOLDS)

    dom_full = binary_erosion(ctx.foot, iterations=DOMAIN_ERODE)
    dom_full_px = float(dom_full.sum())

    l_valid_fi = np.asarray(ctx.static[ctx.static_names.index("L_valid")], dtype=np.float32) > 0.5
    l_valid_grid = np.zeros(ctx.foot.shape, dtype=bool)
    l_valid_grid.ravel()[ctx.fi] = l_valid_fi

    union_names = (
        list(ctx.static_names)
        + list(ctx.e_names)
        + list(ctx.extra_names)
        + ["H27_tip"]
        + list(H34_NAMES)
        + list(H74_RMPS_NAMES)
        + list(H75_DCHB_NAMES)
    )
    assert len(union_names) == 91, len(union_names)
    ucol = {n: i for i, n in enumerate(union_names)}

    bde_extra = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("BDE")] + list(EXTRAS))]
    acd_sub = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("ACD")] + list(SUBSURF_EXTRAS))]
    abcd_extra = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("ABCD")] + list(EXTRAS))]
    tip_idx = ucol["H27_tip"]
    h34_idxs = [ucol[n] for n in H34_NAMES]
    h74_idxs = [ucol[n] for n in H74_RMPS_NAMES]
    h75_idxs = [ucol[n] for n in H75_DCHB_NAMES]
    h75_cor_idxs = [ucol[n] for n in H75_CORRIDOR_SUBSET]
    lidar_set = {ucol[n] for n in ctx.static_names if n.startswith("L_")}
    assert len(lidar_set) == 13

    cols_ctrl_h35 = bde_extra + [tip_idx] + h34_idxs                         # 59
    cols_h75_apron = cols_ctrl_h35 + h75_idxs                                # 64
    cols_ctrl_subsurf = acd_sub + h34_idxs + h74_idxs                        # 51
    cols_ctrl_blind_abcd = abcd_extra + h34_idxs + h74_idxs                  # 78
    cols_m_corridor = cols_ctrl_subsurf + h75_cor_idxs                       # 54
    cols_m_trace = cols_ctrl_blind_abcd + h75_idxs                           # 83
    cols_m_gap = [c for c in cols_m_trace if c not in lidar_set]             # 70

    assert (
        len(cols_ctrl_h35),
        len(cols_h75_apron),
        len(cols_ctrl_subsurf),
        len(cols_ctrl_blind_abcd),
        len(cols_m_corridor),
        len(cols_m_trace),
        len(cols_m_gap),
    ) == (59, 64, 51, 78, 54, 83, 70)

    design = dict(
        experiment=f"H75_{args.mode.upper()}",
        mode=args.mode,
        preregistration=PREREG_PATH,
        preregistration_commit=PREREG_COMMIT,
        draws=list(args.draws),
        folds=list(FOLD_IDS),
        fold_names=fold_names,
        arms=list(ARMS),
        feature_counts=dict(
            CTRL_H35=len(cols_ctrl_h35),
            H75_APRON=len(cols_h75_apron),
            CTRL_SUBSURF=len(cols_ctrl_subsurf),
            CTRL_BLIND_ABCD=len(cols_ctrl_blind_abcd),
            M_corridor=len(cols_m_corridor),
            M_trace=len(cols_m_trace),
            M_gap=len(cols_m_gap),
        ),
        corridor_gamma=CORRIDOR_GAMMA_DEFAULT,
        lidar_gap_scale=LIDAR_GAP_SCALE_DEFAULT,
        n_neg=int(N_NEG),
        hgb_params=HGB_PARAMS,
        kfrac_h35=KFRAC_H35,
        min_dist_h35=MIN_DIST_H35,
        kfrac_blind=KFRAC_BLIND,
        cat_buf_blind=CAT_BUF_BLIND,
        full_b2_budget=FULL_B2_BUDGET,
        block_px=BLOCK_PX_DEFAULT,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        evaluator=EVALUATOR,
        evaluator_hashes={
            "src/gems25/metric.py": file_sha256("src/gems25/metric.py"),
            "src/gems25/holdout.py": file_sha256("src/gems25/holdout.py"),
            "src/gems25/block_holdout.py": file_sha256("src/gems25/block_holdout.py"),
            "src/gems25/validation.py": file_sha256("src/gems25/validation.py"),
            "src/gems25/h74_rmps.py": file_sha256("src/gems25/h74_rmps.py"),
            "src/gems25/h75_dchb.py": file_sha256("src/gems25/h75_dchb.py"),
        },
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    def build_union_matrix(E_vis: np.ndarray, tip_vis: np.ndarray, idx: np.ndarray) -> np.ndarray:
        X = np.empty((idx.size, 91), dtype=np.float32)
        gather_columns(ctx, E_vis, idx, True, out=X[:, :78])
        X[:, 78] = tip_vis[idx].astype(np.float32)
        X[:, 79:82] = np.asarray(h34_mm[:, idx], dtype=np.float32).T
        X[:, 82:86] = np.asarray(h74_mm[:, idx], dtype=np.float32).T
        X[:, 86:91] = np.asarray(h75_mm[:, idx], dtype=np.float32).T
        return X

    cells_path = out / "cells.jsonl"
    canary_records: list[dict] = []
    rows_all: list[dict] = []
    grid_buf = np.zeros(ctx.foot.shape, dtype=np.float32)

    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in args.draws:
                t_cell = time.time()
                if args.mode == "standard":
                    d = ctx.holdout.draw(fold, draw)
                elif args.mode == "block25km":
                    d = draw_block25km(ctx.holdout, fold, draw, block_px=BLOCK_PX_DEFAULT)
                else:
                    assert block_holdout is not None
                    d = block_holdout.draw(fold, draw)

                assert not (d.visible & d.hidden_test).any(), "visible overlaps hidden_test"
                assert not (d.visible & d.hidden_train).any(), "visible overlaps hidden_train"
                assert not (d.train_region & d.quadrant).any(), "train_region overlaps test fold"
                if args.mode == "checkerboard25km":
                    assert not (d.visible & d.quadrant).any(), "BlockHoldout must have 0 visible faults in test blocks"

                E_vis = build_catalogue_features(d.visible, ctx.fi)
                tip_vis = build_tip_continuation(d.visible, ctx.foot, ctx.fi)

                rng = np.random.default_rng(777 + 31 * fold + draw)
                pos = ctx.vec(d.hidden_train)
                near = distance_transform_edt(~d.hidden_train) <= 1.5
                cand = ctx.vec(d.train_region & ~ctx.labels & ~near)
                neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
                train_idx = np.sort(np.concatenate([pos, neg]))
                y_tr = np.isin(train_idx, pos).astype(np.int8)

                q_idx = ctx.vec(d.quadrant)
                fi_q = ctx.fi[q_idx]
                lv_q = l_valid_fi[q_idx]
                sl = d.bbox
                dom_q = binary_erosion(d.quadrant, iterations=DOMAIN_ERODE)
                dom_c = dom_q[sl]
                truth_c = (d.hidden_test & dom_q)[sl]
                known_c = d.visible[sl]
                l_valid_c = l_valid_grid[sl]
                d_vis_c = distance_transform_edt(~known_c).astype(np.float32)

                tv = d_vis_c[truth_c]
                truth_strata = dict(
                    n_truth=int(tv.size),
                    frac_truth_le2=round(float((tv <= 2.0).mean()), 5) if tv.size else 0.0,
                    frac_truth_2_9=round(float(((tv > 2.0) & (tv <= 9.0)).mean()), 5) if tv.size else 0.0,
                    frac_truth_gt9=round(float((tv > 9.0).mean()), 5) if tv.size else 0.0,
                    frac_truth_gt20=round(float((tv > 20.0).mean()), 5) if tv.size else 0.0,
                    median_truth_d_vis=round(float(np.median(tv)), 3) if tv.size else 0.0,
                    frac_truth_lidar_gap=round(float((~l_valid_c[truth_c]).mean()), 5) if tv.size else 0.0,
                )

                dq = dom_q.ravel()[ctx.fi][q_idx]
                hq = (d.hidden_test & dom_q).ravel()[ctx.fi][q_idx]
                cq = ctx.labels.ravel()[ctx.fi][q_idx]
                auc_pos = np.flatnonzero(hq)
                neg_pool = np.flatnonzero(dq & ~cq)
                auc_neg = np.random.default_rng(5).choice(
                    neg_pool, size=min(150_000, neg_pool.size), replace=False
                )
                auc_eval_idx = np.concatenate([auc_pos, auc_neg])
                y_auc = np.r_[np.ones(auc_pos.size, dtype=np.int8), np.zeros(auc_neg.size, dtype=np.int8)]

                Xtr = build_union_matrix(E_vis, tip_vis, train_idx)
                Xq = build_union_matrix(E_vis, tip_vis, q_idx)

                # Standalone single-feature leakage canary across all 91 union columns
                cell_max_canary = 0.0
                cell_worst_feat = ""
                for j, fname in enumerate(union_names):
                    res = feature_canary(Xq[auc_eval_idx, j], y_auc, cap=LEAKAGE_AUC_CAP)
                    c_auc = float(res["canary_auc"]) if res["canary_auc"] is not None else 1.0
                    if c_auc > cell_max_canary:
                        cell_max_canary = c_auc
                        cell_worst_feat = fname
                    if not res["passed"]:
                        raise RuntimeError(
                            f"LEAKAGE CANARY FAILED in mode={args.mode} fold={fold} draw={draw} "
                            f"feature={fname}: {res}"
                        )
                    if fname in H75_DCHB_NAMES:
                        canary_records.append(
                            dict(fold=fold, draw=draw, feature=fname, **{k: res[k] for k in ("auc", "canary_auc", "missingness_auc", "passed")})
                        )
                canary_records.append(
                    dict(fold=fold, draw=draw, feature="__CELL_WORST__", canary_auc=round(cell_max_canary, 6), worst_feature=cell_worst_feat, passed=True)
                )

                # Fit the 4 baseline/ablation models + 3 Corridor-Gated Dual-Regime experts on identical (Xtr, y_tr)
                p_h35, m_h35 = fit_predict(Xtr[:, cols_ctrl_h35], y_tr, Xq[:, cols_ctrl_h35], draw)
                p_apr, m_apr = fit_predict(Xtr[:, cols_h75_apron], y_tr, Xq[:, cols_h75_apron], draw)
                p_sub, m_sub = fit_predict(Xtr[:, cols_ctrl_subsurf], y_tr, Xq[:, cols_ctrl_subsurf], draw)
                p_abcd, m_abcd = fit_predict(Xtr[:, cols_ctrl_blind_abcd], y_tr, Xq[:, cols_ctrl_blind_abcd], draw)

                p_cor, m_cor = fit_predict(Xtr[:, cols_m_corridor], y_tr, Xq[:, cols_m_corridor], draw)
                p_tr, m_tr = fit_predict(Xtr[:, cols_m_trace], y_tr, Xq[:, cols_m_trace], draw)
                p_gp, m_gp = fit_predict(Xtr[:, cols_m_gap], y_tr, Xq[:, cols_m_gap], draw)
                p_cg = combine_corridor_gated_scores(
                    p_cor, p_tr, p_gp, lv_q,
                    gamma=CORRIDOR_GAMMA_DEFAULT,
                    gap_scale=LIDAR_GAP_SCALE_DEFAULT,
                )
                m_cg = dict(
                    fit_s=round(m_cor["fit_s"] + m_tr["fit_s"] + m_gp["fit_s"], 3),
                    predict_s=round(m_cor["predict_s"] + m_tr["predict_s"] + m_gp["predict_s"], 3),
                    n_features=len(cols_m_trace),
                )

                arm_preds = {
                    "CTRL_H35": (p_h35, m_h35, "sapd"),
                    "H75_APRON": (p_apr, m_apr, "sapd"),
                    "CTRL_SUBSURF": (p_sub, m_sub, "blind_submod"),
                    "CTRL_BLIND_ABCD": (p_abcd, m_abcd, "blind_submod"),
                    "H75_CG_BLIND": (p_cg, m_cg, "blind_submod"),
                }

                for arm, (pq, fmeta, em_kind) in arm_preds.items():
                    auc_val = float(roc_auc_score(y_auc, pq[auc_eval_idx]))
                    if em_kind == "sapd":
                        em, emeta = emit_sapd(grid_buf, fi_q, sl, dom_c, known_c, pq)
                    else:
                        em, emeta = emit_blind_submod_any(
                            grid_buf,
                            fi_q,
                            sl,
                            dom_c,
                            known_c,
                            d_vis_c,
                            pq,
                            dom_full_px,
                            visible_full=d.visible,
                            train_region_full=d.train_region,
                        )
                    rec = dict(
                        mode=args.mode,
                        arm=arm,
                        fold=int(fold),
                        fold_name=fold_names[fold],
                        draw=int(draw),
                        **eval_arm(
                            em,
                            truth_c,
                            dom_c,
                            known_c,
                            d_vis_c,
                            l_valid_c,
                            auc_val,
                            truth_strata,
                            dict(**fmeta, **emeta),
                        ),
                    )
                    sink.write(json.dumps(rec) + "\n")
                    sink.flush()
                    rows_all.append(rec)

                del Xtr, Xq, E_vis, tip_vis
                gc.collect()
                cell_dtis = {r["arm"]: round(r["dti"], 5) for r in rows_all[-len(ARMS):]}
                print(
                    f"[{args.mode}] fold={fold}({fold_names[fold]}) draw={draw} "
                    f"({time.time() - t_cell:.1f}s) max_canary={cell_max_canary:.4f}({cell_worst_feat}) "
                    f"DTIs={cell_dtis}",
                    flush=True,
                )

    (out / "canaries.json").write_text(json.dumps(canary_records, indent=1) + "\n")

    # Aggregate pooled summaries & paired contrasts
    per_arm = {}
    for arm in ARMS:
        ar = [r for r in rows_all if r["arm"] == arm]
        per_arm[arm] = dict(
            pooled_dti=round(pooled_dti(ar), 6),
            far_gt9_dti=round(pooled_sub_dti(ar, "far"), 6),
            vfar_gt20_dti=round(pooled_sub_dti(ar, "vfar"), 6),
            lidar_gap_dti=round(pooled_sub_dti(ar, "lgap"), 6),
            mean_auc=round(float(np.mean([r["auc"] for r in ar])), 6),
            total_emitted=int(sum(r["n_emitted"] for r in ar)),
            mean_frac_gt9=round(float(np.mean([r["emit_strata"]["frac_gt9"] if "frac_gt9" in r["emit_strata"] else (r["emit_strata"]["frac_9_20"] + r["emit_strata"]["frac_gt20"]) for r in ar])), 5),
            mean_frac_gt20=round(float(np.mean([r["emit_strata"]["frac_gt20"] for r in ar])), 5),
            mean_median_d_vis=round(float(np.mean([r["emit_strata"]["median_d_vis"] for r in ar])), 3),
            mean_lidar_gap_emit_share=round(float(np.mean([r["emit_strata"]["lidar_gap_emit_share"] for r in ar])), 5),
            withheld_positive_occurrences=int(sum(r["n_truth"] for r in ar)),
        )

    contrasts = {
        "h75_cg_vs_ctrl_subsurf": pooled_summary(
            [r for r in rows_all if r["arm"] in ("H75_CG_BLIND", "CTRL_SUBSURF")],
            candidate="H75_CG_BLIND",
            control="CTRL_SUBSURF",
        ),
        "h75_cg_vs_ctrl_blind_abcd": pooled_summary(
            [r for r in rows_all if r["arm"] in ("H75_CG_BLIND", "CTRL_BLIND_ABCD")],
            candidate="H75_CG_BLIND",
            control="CTRL_BLIND_ABCD",
        ),
        "h75_cg_vs_ctrl_h35": pooled_summary(
            [r for r in rows_all if r["arm"] in ("H75_CG_BLIND", "CTRL_H35")],
            candidate="H75_CG_BLIND",
            control="CTRL_H35",
        ),
        "h75_apron_vs_ctrl_h35": pooled_summary(
            [r for r in rows_all if r["arm"] in ("H75_APRON", "CTRL_H35")],
            candidate="H75_APRON",
            control="CTRL_H35",
        ),
    }

    worst_canary = max(
        (r for r in canary_records if r["feature"] == "__CELL_WORST__"),
        key=lambda r: r["canary_auc"],
    )
    h75_canary_max = max(
        (r["canary_auc"] for r in canary_records if r["feature"] in H75_DCHB_NAMES),
        default=0.0,
    )

    c_apr_h35 = contrasts["h75_apron_vs_ctrl_h35"]
    c_cg_h35 = contrasts["h75_cg_vs_ctrl_h35"]
    gate_g1_apron = bool(
        c_apr_h35["paired_gain"] >= 0.0020
        and c_apr_h35["paired_ci95"][0] > 0.0
        and sum(g > 0 for g in c_apr_h35["fold_gains"]) >= 3
        and min(c_apr_h35["fold_gains"]) >= -0.0080
    )
    gate_g1_cg = bool(
        c_cg_h35["paired_gain"] >= 0.0020
        and c_cg_h35["paired_ci95"][0] > 0.0
        and sum(g > 0 for g in c_cg_h35["fold_gains"]) >= 3
        and min(c_cg_h35["fold_gains"]) >= -0.0080
    )

    c_cg_sub = contrasts["h75_cg_vs_ctrl_subsurf"]
    c_cg_abcd = contrasts["h75_cg_vs_ctrl_blind_abcd"]
    gate_g2_blind = bool(
        c_cg_sub["paired_gain"] > 0.0
        and sum(g > 0 for g in c_cg_sub["fold_gains"]) >= 3
        and c_cg_abcd["paired_gain"] > 0.0
        and sum(g > 0 for g in c_cg_abcd["fold_gains"]) >= 3
        and worst_canary["canary_auc"] <= LEAKAGE_AUC_CAP
    )

    analysis = dict(
        label="HOLDOUT-DTI",
        evaluator=EVALUATOR,
        mode=args.mode,
        draws=list(args.draws),
        preregistration=PREREG_PATH,
        preregistration_commit=PREREG_COMMIT,
        elapsed_seconds=round(time.time() - t_start, 2),
        leakage_canary=dict(
            passed=True,
            cap=LEAKAGE_AUC_CAP,
            n_union_features=len(union_names),
            n_cells=len(FOLD_IDS) * len(args.draws),
            total_feature_cell_checks=len(union_names) * len(FOLD_IDS) * len(args.draws),
            max_canary_auc=worst_canary["canary_auc"],
            worst_feature=worst_canary["worst_feature"],
            max_h75_dchb_canary_auc=round(float(h75_canary_max), 6),
        ),
        per_arm=per_arm,
        contrasts=contrasts,
        gates=dict(
            gate_g1_apron_vs_h35=gate_g1_apron,
            gate_g1_cg_vs_h35=gate_g1_cg,
            gate_g2_cg_vs_both_blind_controls=gate_g2_blind,
        ),
    )
    (out / "analysis.json").write_text(json.dumps(analysis, indent=1) + "\n")
    print(f"=== {args.mode.upper()} COMPLETE in {analysis['elapsed_seconds']}s ===", flush=True)
    for arm, st in per_arm.items():
        print(
            f"  {arm:<16} DTI={st['pooled_dti']:.6f} far(>9)={st['far_gt9_dti']:.6f} "
            f"vfar(>20)={st['vfar_gt20_dti']:.6f} Lgap={st['lidar_gap_dti']:.6f} "
            f"AUC={st['mean_auc']:.4f} Lgap_emit={st['mean_lidar_gap_emit_share']*100:.1f}%",
            flush=True,
        )


if __name__ == "__main__":
    main()
