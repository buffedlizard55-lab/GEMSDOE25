#!/usr/bin/env python3
"""Pre-registered H74 (RMPS-BFP) & H74-BW (25-km block-withheld) holdout runner.

Pre-registered in ``knowledge/35_preregistered_h74_rmps_bw_2026-10-26.md`` (committed at ``af10a19``).

Paired 2 x 2 arms per (fold, draw) cell, all evaluated on the identical split:
  CTRL_H35    BDE + EXTRAS + H27_tip + H34 (59 cols), uniform negatives, sapd2.4 emission
  H74_APRON   CTRL_H35 + H74_RMPS (63 cols), uniform negatives, sapd2.4 emission
  CTRL_BLIND  ABCD + EXTRAS + H34 (74 static cols, zero E/tip), B2 (d_vis > 2 px) greedy_dots
  H74_BLIND   CTRL_BLIND + H74_RMPS (78 static cols, zero E/tip), B2 (d_vis > 2 px) greedy_dots

Modes:
  --mode standard   shared ``ctx.holdout.draw(fold, draw)`` (Experiment 1)
  --mode block25km  ``draw_block25km(ctx.holdout, fold, draw, block_px=250)`` (Experiment 2)
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

from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.greedy import greedy_dots  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h74_rmps import BLOCK_PX_DEFAULT, H74_RMPS_NAMES, draw_block25km, load_h74_rmps_sidecar  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from gems25.validation import feature_canary  # noqa: E402
from run_h28_holdout import EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
KFRAC_H35, MIN_DIST_H35 = 0.035, 2.4
KFRAC_BLIND, CAT_BUF_BLIND, FULL_B2_BUDGET = 0.035, 2.0, 37_654
LEAKAGE_AUC_CAP = 0.90
ARMS = ("CTRL_H35", "H74_APRON", "CTRL_BLIND", "H74_BLIND")
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px)"


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
    ap.add_argument("--mode", choices=("standard", "block25km"), required=True)
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
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")

    h34_mm = load_h34_sidecar(work, ctx.fi)
    h74_mm = load_h74_rmps_sidecar(work, ctx.fi)
    dom_full = binary_erosion(ctx.foot, iterations=DOMAIN_ERODE)
    dom_full_px = float(dom_full.sum())

    # Column index specification inside the 86-column union matrix:
    # [0 .. 63]   static ABCD (64 cols)
    # [64 .. 70]  dynamic E (7 cols)
    # [71 .. 77]  EXTRAS (7 cols)
    # [78]        dynamic H27_tip (1 col)
    # [79 .. 81]  static H34 (3 cols)
    # [82 .. 85]  static H74_RMPS (4 cols)
    ns = ctx.static.shape[0]
    ne = len(ctx.e_names)
    nx = len(ctx.extra_names)
    assert (ns, ne, nx) == (64, 7, 7)

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

    bde_extra_cols = [ucol[n] for n in (
        [ctx.all_names[i] for i in ctx.columns("BDE")] + list(EXTRAS)
    )]
    abcd_extra_cols = [ucol[n] for n in (
        [ctx.all_names[i] for i in ctx.columns("ABCD")] + list(EXTRAS)
    )]
    tip_idx = ucol["H27_tip"]
    h34_idxs = [ucol[n] for n in H34_NAMES]
    h74_idxs = [ucol[n] for n in H74_RMPS_NAMES]

    arm_cols = {
        "CTRL_H35": bde_extra_cols + [tip_idx] + h34_idxs,       # 59 cols
        "H74_APRON": bde_extra_cols + [tip_idx] + h34_idxs + h74_idxs,  # 63 cols
        "CTRL_BLIND": abcd_extra_cols + h34_idxs,                # 74 cols
        "H74_BLIND": abcd_extra_cols + h34_idxs + h74_idxs,      # 78 cols
    }

    design = dict(
        experiment=f"H74_{args.mode.upper()}",
        mode=args.mode,
        preregistration="knowledge/35_preregistered_h74_rmps_bw_2026-10-26.md",
        preregistration_commit="af10a19",
        draws=list(args.draws),
        folds=list(FOLD_IDS),
        fold_names=list(FOLDS),
        arms=list(ARMS),
        arm_feature_counts={k: len(v) for k, v in arm_cols.items()},
        n_neg=int(N_NEG),
        hgb_params=HGB_PARAMS,
        kfrac_h35=KFRAC_H35,
        min_dist_h35=MIN_DIST_H35,
        kfrac_blind=KFRAC_BLIND,
        cat_buf_blind=CAT_BUF_BLIND,
        full_b2_budget=FULL_B2_BUDGET,
        block_px=BLOCK_PX_DEFAULT if args.mode == "block25km" else None,
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
    grid_buf = np.zeros(ctx.foot.shape, dtype=np.float32)

    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in args.draws:
                t_cell = time.time()
                d = (
                    ctx.holdout.draw(fold, draw)
                    if args.mode == "standard"
                    else draw_block25km(ctx.holdout, fold, draw, block_px=BLOCK_PX_DEFAULT)
                )
                # Explicit runtime leakage assertions on every realisation
                assert not (d.visible & d.hidden_test).any(), "visible leaks hidden_test"
                assert not (d.visible & d.hidden_train).any(), "visible leaks hidden_train"
                assert not (d.train_region & d.quadrant).any(), "train_region intersects test quadrant"

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

                # Single-feature leakage canary across ALL 86 columns on test-quadrant target
                cell_canaries = {}
                Xq_eval = Xq_u[auc_eval_idx]
                for col_i, cname in enumerate(union_names):
                    res = feature_canary(Xq_eval[:, col_i], auc_eval_y, cap=LEAKAGE_AUC_CAP)
                    cell_canaries[cname] = res
                    if not res["passed"]:
                        raise RuntimeError(
                            f"LEAKAGE CANARY FIRED in mode={args.mode} fold={fold} draw={draw} "
                            f"col={cname}: canary_auc={res['canary_auc']}"
                        )
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
                        h74_canaries={
                            c: round(float(cell_canaries[c]["canary_auc"]), 6) for c in H74_RMPS_NAMES
                        },
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
                    if arm in ("CTRL_H35", "H74_APRON"):
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
                            mode=args.mode,
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
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    del p_q, em

                del Xtr_u, Xq_u
                gc.collect()
                print(
                    f"[{time.time() - t_start:6.1f}s] mode={args.mode} fold={fold}({FOLDS[fold]}) "
                    f"draw={draw} truth={truth_strata['n_truth']:,} med_dvis={truth_strata['median_truth_d_vis']:.1f}px "
                    f"worst_canary={worst_col}:{worst_auc:.4f} h74_canary={worst_h74_col}:{worst_h74_auc:.4f} "
                    f"({time.time() - t_cell:.1f}s)",
                    flush=True,
                )

    (out / "feature_canaries.json").write_text(json.dumps(canary_records, indent=1) + "\n")
    print(f"Completed mode={args.mode} in {time.time() - t_start:.1f}s -> {out}", flush=True)


if __name__ == "__main__":
    main()
