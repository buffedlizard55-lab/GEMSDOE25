#!/usr/bin/env python3
"""Pre-registered Experiment 3 (3/3): Topography-free subsurface H74_SUBSURF on virgin draws 112, 113.

Pre-registered in ``knowledge/36_preregistered_h74_exp3_subsurface_2026-10-26.md`` (committed at ``32897de``).

Evaluated on 25-km spatial-block component-withheld selector (H74-BW, draw_block25km, block_px=250):
  CTRL_H35      BDE + EXTRAS + H27_tip + H34 (59 cols), uniform negatives, sapd2.4 emission
  CTRL_SUBSURF  ACD + [X1_K, X1_ThK, X1_UK, X3_gm] + H34 (47 static subsurface cols), B2 greedy_dots
  H74_SUBSURF   CTRL_SUBSURF + H74_RMPS (51 static subsurface cols), B2 greedy_dots
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
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h74_rmps import BLOCK_PX_DEFAULT, H74_RMPS_NAMES, draw_block25km, load_h74_rmps_sidecar  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.validation import feature_canary, pooled_dti, pooled_summary  # noqa: E402
from run_h28_holdout import EXTRAS, FOLDS  # noqa: E402
from run_h74_experiments import (  # noqa: E402
    CAT_BUF_BLIND,
    EVALUATOR,
    FOLD_IDS,
    FULL_B2_BUDGET,
    KFRAC_BLIND,
    KFRAC_H35,
    LEAKAGE_AUC_CAP,
    MIN_DIST_H35,
    emit_blind_submod,
    emit_sapd,
    eval_arm,
    fit_predict,
)

SUBSURF_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm")
ARMS = ("CTRL_H35", "CTRL_SUBSURF", "H74_SUBSURF")


def file_sha256(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def pooled_sub_dti(rows: list[dict], prefix: str) -> float:
    tp = sum(float(r[f"{prefix}_tp"]) for r in rows)
    fp = sum(float(r[f"{prefix}_fp"]) for r in rows)
    n = sum(int(r[f"{prefix}_n_truth"]) for r in rows)
    return float(tp / (0.2 * (tp + fp) + 0.8 * n + 1e-7)) if n > 0 else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, nargs="+", default=[112, 113])
    ap.add_argument("--out", default=str(ROOT / "evidence" / "h74_exp3_subsurf_bw25km"))
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
    dom_full = binary_erosion(ctx.foot, iterations=DOMAIN_ERODE)
    dom_full_px = float(dom_full.sum())

    union_names = (
        list(ctx.static_names)
        + list(ctx.e_names)
        + list(ctx.extra_names)
        + ["H27_tip"]
        + list(H34_NAMES)
        + list(H74_RMPS_NAMES)
    )
    assert len(union_names) == 86
    ucol = {n: i for i, n in enumerate(union_names)}

    bde_extra_cols = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("BDE")] + list(EXTRAS))]
    acd_sub_cols = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("ACD")] + list(SUBSURF_EXTRAS))]
    tip_idx = ucol["H27_tip"]
    h34_idxs = [ucol[n] for n in H34_NAMES]
    h74_idxs = [ucol[n] for n in H74_RMPS_NAMES]

    arm_cols = {
        "CTRL_H35": bde_extra_cols + [tip_idx] + h34_idxs,  # 59 cols
        "CTRL_SUBSURF": acd_sub_cols + h34_idxs,            # 47 static topography-free cols
        "H74_SUBSURF": acd_sub_cols + h34_idxs + h74_idxs,  # 51 static topography-free cols
    }
    assert (len(arm_cols["CTRL_H35"]), len(arm_cols["CTRL_SUBSURF"]), len(arm_cols["H74_SUBSURF"])) == (59, 47, 51)

    design = dict(
        experiment="H74_EXP3_SUBSURF_BW25KM",
        mode="block25km",
        preregistration="knowledge/36_preregistered_h74_exp3_subsurface_2026-10-26.md",
        preregistration_commit="32897de",
        draws=list(args.draws),
        folds=list(FOLD_IDS),
        fold_names=list(FOLDS),
        arms=list(ARMS),
        arm_feature_counts={k: len(v) for k, v in arm_cols.items()},
        subsurf_columns=[union_names[i] for i in arm_cols["H74_SUBSURF"]],
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
            "src/gems25/validation.py": file_sha256("src/gems25/validation.py"),
            "src/gems25/h74_rmps.py": file_sha256("src/gems25/h74_rmps.py"),
        },
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    def build_union_matrix(E_vis: np.ndarray, tip_vis: np.ndarray, idx: np.ndarray) -> np.ndarray:
        X = np.empty((idx.size, 86), dtype=np.float32)
        gather_columns(ctx, E_vis, idx, True, out=X[:, :78])
        X[:, 78] = tip_vis[idx].astype(np.float32)
        X[:, 79:82] = np.asarray(h34_mm[:, idx], dtype=np.float32).T
        X[:, 82:86] = np.asarray(h74_mm[:, idx], dtype=np.float32).T
        return X

    cells_path = out / "cells.jsonl"
    canary_records = []
    rows_all = []
    grid_buf = np.zeros(ctx.foot.shape, dtype=np.float32)

    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in args.draws:
                t_cell = time.time()
                d = draw_block25km(ctx.holdout, fold, draw, block_px=BLOCK_PX_DEFAULT)
                assert not (d.visible & d.hidden_test).any()
                assert not (d.visible & d.hidden_train).any()
                assert not (d.train_region & d.quadrant).any()

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
                sl = d.bbox
                dom_q = binary_erosion(d.quadrant, iterations=DOMAIN_ERODE)
                dom_c = dom_q[sl]
                truth_c = (d.hidden_test & dom_q)[sl]
                known_c = d.visible[sl]
                d_vis_c = distance_transform_edt(~known_c).astype(np.float32)

                tv = d_vis_c[truth_c]
                truth_strata = dict(
                    n_truth=int(tv.size),
                    frac_truth_le2=round(float((tv <= 2.0).mean()), 5) if tv.size else 0.0,
                    frac_truth_2_9=round(float(((tv > 2.0) & (tv <= 9.0)).mean()), 5) if tv.size else 0.0,
                    frac_truth_gt9=round(float((tv > 9.0).mean()), 5) if tv.size else 0.0,
                    frac_truth_gt20=round(float((tv > 20.0).mean()), 5) if tv.size else 0.0,
                    median_truth_d_vis=round(float(np.median(tv)), 3) if tv.size else 0.0,
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
                auc_eval_y = np.concatenate(
                    [np.ones(auc_pos.size, dtype=np.int8), np.zeros(auc_neg.size, dtype=np.int8)]
                )

                Xtr_u = build_union_matrix(E_vis, tip_vis, train_idx)
                Xq_u = build_union_matrix(E_vis, tip_vis, q_idx)
                del E_vis, tip_vis

                cell_canaries = {}
                Xq_eval = Xq_u[auc_eval_idx]
                for col_i, cname in enumerate(union_names):
                    res = feature_canary(Xq_eval[:, col_i], auc_eval_y, cap=LEAKAGE_AUC_CAP)
                    cell_canaries[cname] = res
                    if not res["passed"]:
                        raise RuntimeError(f"LEAKAGE CANARY FIRED: {cname} {res['canary_auc']}")
                del Xq_eval
                worst_col = max(cell_canaries, key=lambda c: cell_canaries[c]["canary_auc"])
                worst_auc = float(cell_canaries[worst_col]["canary_auc"])
                worst_h74_col = max(H74_RMPS_NAMES, key=lambda c: cell_canaries[c]["canary_auc"])
                worst_h74_auc = float(cell_canaries[worst_h74_col]["canary_auc"])
                canary_records.append(
                    dict(
                        fold=int(fold),
                        fold_name=FOLDS[fold],
                        draw=int(draw),
                        n_columns=len(union_names),
                        worst_column=worst_col,
                        worst_canary_auc=round(worst_auc, 6),
                        worst_h74_column=worst_h74_col,
                        worst_h74_canary_auc=round(worst_h74_auc, 6),
                        all_passed=True,
                    )
                )

                for arm in ARMS:
                    cols = arm_cols[arm]
                    p_q, fmeta = fit_predict(Xtr_u[:, cols], y_tr, Xq_u[:, cols], seed=draw)
                    auc_val = (
                        float(roc_auc_score(auc_eval_y, p_q[auc_eval_idx]))
                        if np.unique(p_q[auc_eval_idx]).size > 1
                        else 0.5
                    )
                    if arm == "CTRL_H35":
                        em, emeta = emit_sapd(grid_buf, fi_q, sl, dom_c, known_c, p_q)
                    else:
                        em, emeta = emit_blind_submod(
                            grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px
                        )
                    row = eval_arm(
                        em,
                        truth_c,
                        dom_c,
                        known_c,
                        d_vis_c,
                        auc_val,
                        truth_strata,
                        dict(
                            mode="block25km",
                            arm=arm,
                            fold=int(fold),
                            fold_name=FOLDS[fold],
                            draw=int(draw),
                            canary_max_auc=round(worst_auc, 6),
                            canary_h74_max_auc=round(worst_h74_auc, 6),
                            **fmeta,
                            **emeta,
                        ),
                    )
                    rows_all.append(row)
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    del p_q, em

                del Xtr_u, Xq_u
                gc.collect()
                print(
                    f"[{time.time() - t_start:6.1f}s] exp3 fold={fold}({FOLDS[fold]}) draw={draw} "
                    f"truth={truth_strata['n_truth']:,} med_dvis={truth_strata['median_truth_d_vis']:.1f}px "
                    f"canary={worst_col}:{worst_auc:.4f} ({time.time() - t_cell:.1f}s)",
                    flush=True,
                )

    (out / "feature_canaries.json").write_text(json.dumps(canary_records, indent=1) + "\n")

    per_arm = {}
    for arm in ARMS:
        ar = [r for r in rows_all if r["arm"] == arm]
        per_arm[arm] = dict(
            pooled_dti=pooled_dti(ar),
            mean_cell_dti=float(np.mean([r["dti"] for r in ar])),
            mean_auc=float(np.mean([r["auc"] for r in ar])),
            pooled_far_gt9_dti=pooled_sub_dti(ar, "far_gt9"),
            pooled_vfar_gt20_dti=pooled_sub_dti(ar, "vfar_gt20"),
            withheld_positive_occurrences=int(sum(r["n_truth"] for r in ar)),
            mean_emitted_dots=float(np.mean([r["n_emitted"] for r in ar])),
            mean_emit_frac_2_9=float(np.mean([r["emitted_strata"]["frac_2_9"] for r in ar])),
            mean_emit_frac_gt20=float(np.mean([r["emitted_strata"]["frac_gt20"] for r in ar])),
            mean_emit_median_d_vis=float(np.mean([r["emitted_strata"]["median_d_vis"] for r in ar])),
        )

    sub_vs_ctrl_sub = pooled_summary(rows_all, candidate="H74_SUBSURF", control="CTRL_SUBSURF")
    sub_vs_ctrl_h35 = pooled_summary(rows_all, candidate="H74_SUBSURF", control="CTRL_H35")
    fg = sub_vs_ctrl_sub["fold_gains"]
    g3_subsurf = dict(
        paired_gain=sub_vs_ctrl_sub["paired_gain"],
        paired_ci95=sub_vs_ctrl_sub["paired_ci95"],
        fold_gains=fg,
        folds_positive=int(sum(g > 0.0 for g in fg)),
        passed=bool(sub_vs_ctrl_sub["paired_gain"] > 0.0 and sum(g > 0.0 for g in fg) >= 3),
    )
    worst_rec = max(canary_records, key=lambda c: c["worst_canary_auc"])
    summary = dict(
        label="HOLDOUT-DTI",
        experiment="H74_EXP3_SUBSURF_BW25KM",
        preregistration="knowledge/36_preregistered_h74_exp3_subsurface_2026-10-26.md",
        evaluator=EVALUATOR,
        draws=list(args.draws),
        n_cells_per_arm=8,
        per_arm=per_arm,
        contrasts=dict(
            h74_subsurf_vs_ctrl_subsurf=sub_vs_ctrl_sub,
            h74_subsurf_vs_ctrl_h35=sub_vs_ctrl_h35,
        ),
        gate_g3_subsurf=g3_subsurf,
        slot_gate_passed=False,
        canary=dict(
            cap=LEAKAGE_AUC_CAP,
            max_canary_auc=worst_rec["worst_canary_auc"],
            max_canary_column=worst_rec["worst_column"],
            max_h74_canary_auc=max(c["worst_h74_canary_auc"] for c in canary_records),
            all_passed=True,
        ),
    )
    (out / "analysis.json").write_text(json.dumps(summary, indent=1) + "\n")
    print("Exp3 per_arm:", {k: round(v["pooled_dti"], 6) for k, v in per_arm.items()})
    print("Exp3 G3_SUBSURF:", g3_subsurf)


if __name__ == "__main__":
    main()
