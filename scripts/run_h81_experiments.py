#!/usr/bin/env python3
"""Pre-registered H81 (FHJ-SD + CLR + SLUTH) 3-experiment holdout runner.

Pre-registered in ``knowledge/44_preregistered_h81_fhj_sd_2026-10-28.md`` (committed at ``6c66fc0``
before this module, any fit on the virgin draws, or any GeoTIFF).

Modes / virgin draws (disjoint from every prior session, which used draws <= 133):
  * ``standard``         — shared ``gems25.holdout.Holdout`` 20% component split; Exp 1, draws 140-141
  * ``block25km``        — shared ``gems25.h74_rmps.draw_block25km``; Exp 2, draws 140-141
  * ``checkerboard25km`` — shared ``gems25.block_holdout.BlockHoldout`` (100% block hiding); Exp 3, draws 142-143

Arms, all recomputed in the same cell (AGENTS.md Rule 5):
  1. CTRL_H35         (59 cols: BDE + EXTRAS + H27_tip + H34, sapd 2.4 px)
  2. CTRL_SUBSURF     (51 cols: ACD + SUBSURF_EXTRAS + H34 + H74_RMPS, B2 greedy_dots)
  3. CTRL_BLIND_ABCD  (78 cols: ABCD + EXTRAS + H34 + H74_RMPS, B2 greedy_dots)  [Exp 3 only]
  4. H81_SUBSURF      (57 cols: CTRL_SUBSURF + 6 H81, B2 greedy_dots)
  5. H81_JUNC_CG      (60/89/76-col junction-corridor dual-regime coupling, gamma=0.62, gap_scale=0.95)
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
    H75_CORRIDOR_SUBSET,
    H75_DCHB_NAMES,
    estimate_blind_n_hat,
    load_h75_dchb_sidecar,
)
from gems25.h81_fhj import (  # noqa: E402
    H81_FHJ_NAMES,
    JUNCTION_GAMMA_DEFAULT,
    JUNCTION_GAP_SCALE_DEFAULT,
    combine_junction_corridor_scores,
    load_h81_fhj_sidecar,
)
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from gems25.validation import feature_canary, pooled_dti, pooled_summary  # noqa: E402
from run_h28_holdout import EXTRAS, FOLDS  # noqa: E402

PREREG_PATH = "knowledge/44_preregistered_h81_fhj_sd_2026-10-28.md"
PREREG_COMMIT = "6c66fc0b925f5b57bde3e811cad696b22b793e61"
EVALUATOR = "gems25.metric.dti_binary(alpha=0.2,beta=0.8,R=3px)"
FOLD_IDS = (0, 1, 2, 3)
LEAKAGE_AUC_CAP = 0.90
KFRAC_H35 = 0.035
MIN_DIST_H35 = 2.4
KFRAC_BLIND = 0.035
CAT_BUF_BLIND = 2.0
FULL_B2_BUDGET = 37_654
SUBSURF_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm")

EXP_SPECS = {
    "exp1": dict(mode="standard", draws=[140, 141], arms=("CTRL_H35", "CTRL_SUBSURF", "H81_SUBSURF", "H81_JUNC_CG")),
    "exp2": dict(mode="block25km", draws=[140, 141], arms=("CTRL_H35", "CTRL_SUBSURF", "H81_SUBSURF", "H81_JUNC_CG")),
    "exp3": dict(
        mode="checkerboard25km",
        draws=[142, 143],
        arms=("CTRL_H35", "CTRL_SUBSURF", "CTRL_BLIND_ABCD", "H81_SUBSURF", "H81_JUNC_CG"),
    ),
}


def file_sha256(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def emit_sapd(grid_buf, fi_q, sl, dom_c, known_c, score_q):
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


def emit_blind_submod(grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, score_q, dom_full_px, *,
                      visible_full, train_region_full):
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
    n_hat = estimate_blind_n_hat(known_c, dom_c, visible_train=visible_full,
                                 train_region=train_region_full, hide_frac=0.20, floor=100.0)
    max_dots_q = int(round(float(FULL_B2_BUDGET) * float(dom_c.sum()) / float(dom_full_px)))
    dots, gdiag = greedy_dots(s_crop, top, dom_c, excl, n_hat, max_dots=max_dots_q)
    return dots, dict(emit_s=round(time.time() - t0, 3), pool_k=k, n_hat=round(float(n_hat), 2),
                      max_dots_q=max_dots_q, n_emitted=int(dots.sum()),
                      stop_reason=gdiag["stop_reason"], plugin_dti=round(float(gdiag["plugin_dti"]), 6))


def fit_predict(Xtr, y, Xq, seed):
    t0 = time.time()
    clf = HistGradientBoostingClassifier(random_state=int(seed), **HGB_PARAMS).fit(Xtr, y)
    fit_s = time.time() - t0
    t0 = time.time()
    p = clf.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=round(fit_s, 3), predict_s=round(time.time() - t0, 3), n_features=int(Xtr.shape[1]))


def eval_arm(em, truth_c, dom_c, known_c, d_vis_c, l_valid_c, auc, truth_strata, meta):
    ev = dti_binary(em, truth_c, dom_c, known_c)
    far_mask = d_vis_c > 9.0
    far = dti_binary(em & far_mask, truth_c & far_mask, dom_c, known_c)
    vfar_mask = d_vis_c > 20.0
    vfar = dti_binary(em & vfar_mask, truth_c & vfar_mask, dom_c, known_c)
    lgap_mask = ~l_valid_c
    lgap = dti_binary(em & lgap_mask, truth_c & lgap_mask, dom_c & lgap_mask, known_c & lgap_mask)
    dv = d_vis_c[em]
    strata = (
        dict(frac_le2=round(float((dv <= 2.0).mean()), 5),
             frac_2_9=round(float(((dv > 2.0) & (dv <= 9.0)).mean()), 5),
             frac_9_20=round(float(((dv > 9.0) & (dv <= 20.0)).mean()), 5),
             frac_gt20=round(float((dv > 20.0).mean()), 5),
             median_d_vis=round(float(np.median(dv)), 3),
             lidar_gap_emit_share=round(float((~l_valid_c[em]).mean()), 5) if em.any() else 0.0)
        if dv.size else dict(frac_le2=0.0, frac_2_9=0.0, frac_9_20=0.0, frac_gt20=0.0,
                             median_d_vis=0.0, lidar_gap_emit_share=0.0)
    )
    return dict(**ev, auc=round(float(auc), 6),
                far_dti=round(float(far["dti"]), 6), far_tp=round(float(far["tp"]), 4),
                far_fp=round(float(far["fp"]), 4), far_n_truth=int(far["n_truth"]),
                vfar_dti=round(float(vfar["dti"]), 6), vfar_tp=round(float(vfar["tp"]), 4),
                vfar_fp=round(float(vfar["fp"]), 4), vfar_n_truth=int(vfar["n_truth"]),
                lgap_dti=round(float(lgap["dti"]), 6), lgap_tp=round(float(lgap["tp"]), 4),
                lgap_fp=round(float(lgap["fp"]), 4), lgap_n_truth=int(lgap["n_truth"]),
                emit_strata=strata, truth_strata=truth_strata, **meta)


def pooled_sub_dti(rows, prefix):
    tp = sum(float(r[f"{prefix}_tp"]) for r in rows)
    fp = sum(float(r[f"{prefix}_fp"]) for r in rows)
    n = sum(int(r[f"{prefix}_n_truth"]) for r in rows)
    return float(tp / (0.2 * (tp + fp) + 0.8 * n + 1e-7)) if n > 0 else 0.0


def summarize_run(out: Path, arms, exp_id: str, mode: str, draws) -> dict:
    design = json.loads((out / "design.json").read_text())
    rows = [json.loads(ln) for ln in (out / "cells.jsonl").read_text().splitlines() if ln.strip()]
    canaries = json.loads((out / "feature_canaries.json").read_text())
    per_arm = {}
    for arm in arms:
        ar = [r for r in rows if r["arm"] == arm]
        per_arm[arm] = dict(
            pooled_dti=pooled_dti(ar),
            mean_cell_dti=float(np.mean([r["dti"] for r in ar])),
            mean_auc=float(np.mean([r["auc"] for r in ar])),
            pooled_far_gt9_dti=pooled_sub_dti(ar, "far"),
            pooled_vfar_gt20_dti=pooled_sub_dti(ar, "vfar"),
            pooled_lidar_gap_dti=pooled_sub_dti(ar, "lgap"),
            withheld_positive_occurrences=int(sum(r["n_truth"] for r in ar)),
            lidar_gap_withheld_occurrences=int(sum(r["lgap_n_truth"] for r in ar)),
            mean_emitted_dots=float(np.mean([r["n_emitted"] for r in ar])),
            mean_emit_frac_2_9=float(np.mean([r["emit_strata"]["frac_2_9"] for r in ar])),
            mean_emit_frac_gt20=float(np.mean([r["emit_strata"]["frac_gt20"] for r in ar])),
            mean_emit_median_d_vis=float(np.mean([r["emit_strata"]["median_d_vis"] for r in ar])),
            mean_lidar_gap_emit_share=float(np.mean([r["emit_strata"]["lidar_gap_emit_share"] for r in ar])),
        )
    ctrl_rows = [r for r in rows if r["arm"] == "CTRL_H35"]
    truth_profile = dict(
        mean_truth_frac_le2=float(np.mean([r["truth_strata"]["frac_truth_le2"] for r in ctrl_rows])),
        mean_truth_frac_2_9=float(np.mean([r["truth_strata"]["frac_truth_2_9"] for r in ctrl_rows])),
        mean_truth_frac_gt9=float(np.mean([r["truth_strata"]["frac_truth_gt9"] for r in ctrl_rows])),
        mean_truth_frac_gt20=float(np.mean([r["truth_strata"]["frac_truth_gt20"] for r in ctrl_rows])),
        mean_median_truth_d_vis=float(np.mean([r["truth_strata"]["median_truth_d_vis"] for r in ctrl_rows])),
        mean_truth_lidar_gap_frac=float(np.mean([r["truth_strata"]["frac_truth_lidar_gap"] for r in ctrl_rows])),
    )
    contrasts = {}
    for cand in ("H81_SUBSURF", "H81_JUNC_CG"):
        if cand in arms:
            for ctrl in ("CTRL_SUBSURF", "CTRL_BLIND_ABCD", "CTRL_H35"):
                if ctrl in arms:
                    contrasts[f"{cand.lower()}_vs_{ctrl.lower()}"] = pooled_summary(
                        rows, candidate=cand, control=ctrl
                    )
    worst = max(canaries, key=lambda c: c["worst_canary_auc"])
    worst_h81 = max(canaries, key=lambda c: c["worst_h81_canary_auc"])
    summary = dict(
        label="HOLDOUT-DTI", experiment=f"H81_{exp_id.upper()}_{mode.upper()}", exp_id=exp_id, mode=mode,
        evaluator=EVALUATOR, preregistration=design["preregistration"],
        preregistration_commit=design["preregistration_commit"], draws=list(draws),
        n_cells_per_arm=len(ctrl_rows), truth_d_vis_profile=truth_profile,
        per_arm=per_arm, contrasts=contrasts,
        leakage_canary=dict(cap=design["leakage_auc_cap"], n_cells=len(canaries),
                            n_columns=canaries[0]["n_columns"],
                            max_canary_auc=worst["worst_canary_auc"], max_canary_column=worst["worst_column"],
                            max_h81_canary_auc=worst_h81["worst_h81_canary_auc"],
                            max_h81_canary_column=worst_h81["worst_h81_column"],
                            all_passed=all(c["all_passed"] for c in canaries)),
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def run_experiment(exp_id: str) -> dict:
    spec = EXP_SPECS[exp_id]
    mode, draws, arms = spec["mode"], list(spec["draws"]), spec["arms"]
    out = ROOT / "evidence" / f"h81_{exp_id}"
    if out.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=False)

    work = work_dir()
    t_start = time.time()
    ctx = load_context(work)
    h34_mm = load_h34_sidecar(work, ctx.fi)
    h74_mm = load_h74_rmps_sidecar(work, ctx.fi)
    h75_mm = load_h75_dchb_sidecar(work, ctx.fi)
    h81_mm = load_h81_fhj_sidecar(work, ctx.fi)

    block_holdout = (
        BlockHoldout(ctx.foot, ctx.labels, 0.20, block_size_px=BLOCK_PX_DEFAULT)
        if mode == "checkerboard25km" else None
    )
    fold_names = list(BlockHoldout.FOLD_NAMES) if block_holdout is not None else list(FOLDS)

    dom_full = binary_erosion(ctx.foot, iterations=DOMAIN_ERODE)
    dom_full_px = float(dom_full.sum())
    l_valid_fi = np.asarray(ctx.static[ctx.static_names.index("L_valid")], dtype=np.float32) > 0.5
    l_valid_grid = np.zeros(ctx.foot.shape, dtype=bool)
    l_valid_grid.ravel()[ctx.fi] = l_valid_fi

    union_names = (
        list(ctx.static_names) + list(ctx.e_names) + list(ctx.extra_names) + ["H27_tip"]
        + list(H34_NAMES) + list(H74_RMPS_NAMES) + list(H75_DCHB_NAMES) + list(H81_FHJ_NAMES)
    )
    assert len(union_names) == 97, len(union_names)
    ucol = {n: i for i, n in enumerate(union_names)}

    bde_extra = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("BDE")] + list(EXTRAS))]
    acd_sub = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("ACD")] + list(SUBSURF_EXTRAS))]
    abcd_extra = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("ABCD")] + list(EXTRAS))]
    tip_idx = ucol["H27_tip"]
    h34_idxs = [ucol[n] for n in H34_NAMES]
    h74_idxs = [ucol[n] for n in H74_RMPS_NAMES]
    h75_idxs = [ucol[n] for n in H75_DCHB_NAMES]
    h75_cor_idxs = [ucol[n] for n in H75_CORRIDOR_SUBSET]
    h81_idxs = [ucol[n] for n in H81_FHJ_NAMES]
    lidar_set = {ucol[n] for n in ctx.static_names if n.startswith("L_")}
    assert len(lidar_set) == 13

    cols_ctrl_h35 = bde_extra + [tip_idx] + h34_idxs                       # 59
    cols_ctrl_subsurf = acd_sub + h34_idxs + h74_idxs                      # 51
    cols_ctrl_blind_abcd = abcd_extra + h34_idxs + h74_idxs                # 78
    cols_h81_subsurf = cols_ctrl_subsurf + h81_idxs                        # 57
    cols_m_corridor = cols_ctrl_subsurf + h75_cor_idxs + h81_idxs          # 60
    cols_m_trace = cols_ctrl_blind_abcd + h75_idxs + h81_idxs              # 89
    cols_m_gap = [c for c in cols_m_trace if c not in lidar_set]           # 76
    assert (len(cols_ctrl_h35), len(cols_ctrl_subsurf), len(cols_ctrl_blind_abcd), len(cols_h81_subsurf),
            len(cols_m_corridor), len(cols_m_trace), len(cols_m_gap)) == (59, 51, 78, 57, 60, 89, 76)

    design = dict(
        experiment=f"H81_{exp_id.upper()}_{mode.upper()}", exp_id=exp_id, mode=mode,
        preregistration=PREREG_PATH, preregistration_commit=PREREG_COMMIT,
        draws=list(draws), folds=list(FOLD_IDS), fold_names=fold_names, arms=list(arms),
        feature_counts=dict(CTRL_H35=len(cols_ctrl_h35), CTRL_SUBSURF=len(cols_ctrl_subsurf),
                            CTRL_BLIND_ABCD=len(cols_ctrl_blind_abcd), H81_SUBSURF=len(cols_h81_subsurf),
                            M_corridor=len(cols_m_corridor), M_trace=len(cols_m_trace), M_gap=len(cols_m_gap)),
        junction_gamma=JUNCTION_GAMMA_DEFAULT, junction_gap_scale=JUNCTION_GAP_SCALE_DEFAULT,
        n_neg=int(N_NEG), hgb_params=HGB_PARAMS, kfrac_h35=KFRAC_H35, min_dist_h35=MIN_DIST_H35,
        kfrac_blind=KFRAC_BLIND, cat_buf_blind=CAT_BUF_BLIND, full_b2_budget=FULL_B2_BUDGET,
        block_px=BLOCK_PX_DEFAULT, leakage_auc_cap=LEAKAGE_AUC_CAP, evaluator=EVALUATOR,
        evaluator_hashes={
            "src/gems25/metric.py": file_sha256("src/gems25/metric.py"),
            "src/gems25/holdout.py": file_sha256("src/gems25/holdout.py"),
            "src/gems25/block_holdout.py": file_sha256("src/gems25/block_holdout.py"),
            "src/gems25/validation.py": file_sha256("src/gems25/validation.py"),
            "src/gems25/h74_rmps.py": file_sha256("src/gems25/h74_rmps.py"),
            "src/gems25/h75_dchb.py": file_sha256("src/gems25/h75_dchb.py"),
            "src/gems25/h81_fhj.py": file_sha256("src/gems25/h81_fhj.py"),
        },
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    def build_union_matrix(E_vis, tip_vis, idx):
        X = np.empty((idx.size, 97), dtype=np.float32)
        gather_columns(ctx, E_vis, idx, True, out=X[:, :78])
        X[:, 78] = tip_vis[idx].astype(np.float32)
        X[:, 79:82] = np.asarray(h34_mm[:, idx], dtype=np.float32).T
        X[:, 82:86] = np.asarray(h74_mm[:, idx], dtype=np.float32).T
        X[:, 86:91] = np.asarray(h75_mm[:, idx], dtype=np.float32).T
        X[:, 91:97] = np.asarray(h81_mm[:, idx], dtype=np.float32).T
        return X

    cells_path = out / "cells.jsonl"
    canary_records: list[dict] = []
    grid_buf = np.zeros(ctx.foot.shape, dtype=np.float32)

    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in draws:
                t_cell = time.time()
                if mode == "standard":
                    d = ctx.holdout.draw(fold, draw)
                elif mode == "block25km":
                    d = draw_block25km(ctx.holdout, fold, draw, block_px=BLOCK_PX_DEFAULT)
                else:
                    assert block_holdout is not None
                    d = block_holdout.draw(fold, draw)

                assert not (d.visible & d.hidden_test).any(), "visible overlaps hidden_test"
                assert not (d.visible & d.hidden_train).any(), "visible overlaps hidden_train"
                assert not (d.train_region & d.quadrant).any(), "train_region overlaps test fold"
                if mode == "checkerboard25km":
                    assert not (d.visible & d.quadrant).any(), "BlockHoldout must hide all test-block faults"

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
                auc_neg = np.random.default_rng(5).choice(neg_pool, size=min(150_000, neg_pool.size), replace=False)
                auc_eval_idx = np.concatenate([auc_pos, auc_neg])
                auc_eval_y = np.concatenate([np.ones(auc_pos.size, dtype=np.int8),
                                             np.zeros(auc_neg.size, dtype=np.int8)])

                Xtr_u = build_union_matrix(E_vis, tip_vis, train_idx)
                Xq_u = build_union_matrix(E_vis, tip_vis, q_idx)
                del E_vis, tip_vis

                # Protocol Rule 4: every column standalone, failing closed on AUC > cap
                cell_canaries = {}
                Xq_eval = Xq_u[auc_eval_idx]
                for col_i, cname in enumerate(union_names):
                    res = feature_canary(Xq_eval[:, col_i], auc_eval_y, cap=LEAKAGE_AUC_CAP)
                    cell_canaries[cname] = res
                    if not res["passed"]:
                        raise RuntimeError(
                            f"LEAKAGE CANARY FIRED exp={exp_id} fold={fold} draw={draw} "
                            f"col={cname} canary_auc={res['canary_auc']}"
                        )
                del Xq_eval
                worst_col = max(cell_canaries, key=lambda c: cell_canaries[c]["canary_auc"])
                worst_auc = float(cell_canaries[worst_col]["canary_auc"])
                worst_h81_col = max(H81_FHJ_NAMES, key=lambda c: cell_canaries[c]["canary_auc"])
                worst_h81_auc = float(cell_canaries[worst_h81_col]["canary_auc"])
                crec = dict(fold=int(fold), fold_name=fold_names[fold], draw=int(draw), n_columns=len(union_names),
                            worst_column=worst_col, worst_canary_auc=round(worst_auc, 6),
                            worst_h81_column=worst_h81_col, worst_h81_canary_auc=round(worst_h81_auc, 6),
                            h81_canaries={c: round(float(cell_canaries[c]["canary_auc"]), 6) for c in H81_FHJ_NAMES},
                            all_passed=True)
                canary_records.append(crec)

                p_subsurf = p_h81_subsurf = p_corridor = p_trace = p_gap = None
                for arm in arms:
                    if arm == "CTRL_H35":
                        p_q, fmeta = fit_predict(Xtr_u[:, cols_ctrl_h35], y_tr, Xq_u[:, cols_ctrl_h35], seed=draw)
                        em, emeta = emit_sapd(grid_buf, fi_q, sl, dom_c, known_c, p_q)
                    elif arm == "CTRL_SUBSURF":
                        p_subsurf, fmeta = fit_predict(Xtr_u[:, cols_ctrl_subsurf], y_tr,
                                                       Xq_u[:, cols_ctrl_subsurf], seed=draw)
                        p_q = p_subsurf
                        em, emeta = emit_blind_submod(grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px,
                                                      visible_full=d.visible, train_region_full=d.train_region)
                    elif arm == "CTRL_BLIND_ABCD":
                        p_q, fmeta = fit_predict(Xtr_u[:, cols_ctrl_blind_abcd], y_tr,
                                                 Xq_u[:, cols_ctrl_blind_abcd], seed=draw)
                        em, emeta = emit_blind_submod(grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px,
                                                      visible_full=d.visible, train_region_full=d.train_region)
                    elif arm == "H81_SUBSURF":
                        p_h81_subsurf, fmeta = fit_predict(Xtr_u[:, cols_h81_subsurf], y_tr,
                                                           Xq_u[:, cols_h81_subsurf], seed=draw)
                        p_q = p_h81_subsurf
                        em, emeta = emit_blind_submod(grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px,
                                                      visible_full=d.visible, train_region_full=d.train_region)
                    elif arm == "H81_JUNC_CG":
                        p_corridor, meta_cor = fit_predict(Xtr_u[:, cols_m_corridor], y_tr,
                                                           Xq_u[:, cols_m_corridor], seed=draw)
                        p_trace, meta_tr = fit_predict(Xtr_u[:, cols_m_trace], y_tr,
                                                       Xq_u[:, cols_m_trace], seed=draw + 1000)
                        p_gap, meta_gp = fit_predict(Xtr_u[:, cols_m_gap], y_tr,
                                                     Xq_u[:, cols_m_gap], seed=draw + 2000)
                        p_q = combine_junction_corridor_scores(p_corridor, p_trace, p_gap, lv_q)
                        fmeta = dict(fit_s=round(meta_cor["fit_s"] + meta_tr["fit_s"] + meta_gp["fit_s"], 3),
                                     predict_s=round(meta_cor["predict_s"] + meta_tr["predict_s"] + meta_gp["predict_s"], 3),
                                     n_features=int(len(cols_m_corridor) + len(cols_m_trace) + len(cols_m_gap)))
                        em, emeta = emit_blind_submod(grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px,
                                                      visible_full=d.visible, train_region_full=d.train_region)
                        del p_corridor, p_trace, p_gap
                    else:
                        raise ValueError(f"Unknown arm: {arm}")

                    auc_val = (float(roc_auc_score(auc_eval_y, p_q[auc_eval_idx]))
                               if np.unique(p_q[auc_eval_idx]).size > 1 else 0.5)
                    row = eval_arm(em, truth_c, dom_c, known_c, d_vis_c, l_valid_c, auc_val, truth_strata,
                                   dict(exp=exp_id, mode=mode, arm=arm, fold=int(fold),
                                        fold_name=fold_names[fold], draw=int(draw),
                                        canary_max_auc=round(worst_auc, 6),
                                        canary_h81_max_auc=round(worst_h81_auc, 6), **fmeta, **emeta))
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    del p_q, em

                del p_subsurf, p_h81_subsurf, Xtr_u, Xq_u
                gc.collect()
                print(f"[{time.time() - t_start:6.1f}s] {exp_id}({mode}) fold={fold}({fold_names[fold]}) "
                      f"draw={draw} truth={truth_strata['n_truth']:,} "
                      f"med_dvis={truth_strata['median_truth_d_vis']:.1f}px "
                      f"worst_canary={worst_col}:{worst_auc:.4f} h81={worst_h81_col}:{worst_h81_auc:.4f} "
                      f"({time.time() - t_cell:.1f}s)", flush=True)

    (out / "feature_canaries.json").write_text(json.dumps(canary_records, indent=1) + "\n")
    summary = summarize_run(out, arms, exp_id, mode, draws)
    summary["elapsed_seconds"] = round(time.time() - t_start, 2)
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"Completed {exp_id} in {time.time() - t_start:.1f}s -> {out}")
    for arm, st in summary["per_arm"].items():
        print(f"  {arm:16s} pooled_DTI={st['pooled_dti']:.6f} far>9={st['pooled_far_gt9_dti']:.6f} "
              f"vfar>20={st['pooled_vfar_gt20_dti']:.6f} lgap={st['pooled_lidar_gap_dti']:.6f} "
              f"AUC={st['mean_auc']:.4f} dots={st['mean_emitted_dots']:.0f}")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp", choices=tuple(EXP_SPECS.keys()) + ("all",), required=True)
    args = ap.parse_args()
    exps = list(EXP_SPECS.keys()) if args.exp == "all" else [args.exp]
    t0 = time.time()
    for exp_id in exps:
        run_experiment(exp_id)
    if args.exp == "all":
        print(f"All three H81 experiments completed in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
