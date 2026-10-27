#!/usr/bin/env python3
"""Pre-registered H79 (CTHM-PoE & SGMC-Coulomb) 3-experiment holdout runner.

Pre-registered in ``knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md`` (committed at ``b59b129``
before feature computation or model fitting).

Experiment schedule (virgin draws 114-117; hard cap <= 3 experiments):
  exp1 (standard Holdout, draws 114, 115):
    CTRL_H35, CTRL_SUBSURF (51 cols = H74_SUBSURF), H79_SUBSURF (55 cols), H79_POE (55 crustal x 26 morpho)
  exp2 (25-km block-withheld H74-BW, draws 114, 115):
    CTRL_H35, CTRL_SUBSURF (51 cols = H74_SUBSURF), H79_SUBSURF (55 cols), H79_POE (55 crustal x 26 morpho)
  exp3 (25-km block-withheld H74-BW out-of-sample confirmation + H79-2 SGMC test, draws 116, 117):
    CTRL_H35, H79_SINGLE_HGB (81 static cols), H79_POE (55 crustal x 26 morpho), H79_POE_SGMC (56 crustal x 26 morpho)
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
from gems25.features import ADDON_NAMES, build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h74_rmps import BLOCK_PX_DEFAULT, H74_RMPS_NAMES, draw_block25km, load_h74_rmps_sidecar  # noqa: E402
from gems25.h79_cthm import (  # noqa: E402
    H79_ALL_NAMES,
    H79_CTHM_NAMES,
    H79_SGMC_NAMES,
    POE_FLOOR_CRUSTAL,
    POE_FLOOR_MORPHO,
    POE_GAMMA_CRUSTAL,
    build_h79_sidecar,
    fuse_poe_scores,
)
from gems25.paths import data_dir, work_dir  # noqa: E402
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
SINGLE_STATIC_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm", "X3_gd")

EXP_SPECS = {
    "exp1": dict(
        mode="standard",
        default_draws=[114, 115],
        default_out="evidence/h79_exp1_standard",
        arms=("CTRL_H35", "CTRL_SUBSURF", "H79_SUBSURF", "H79_POE"),
    ),
    "exp2": dict(
        mode="block25km",
        default_draws=[114, 115],
        default_out="evidence/h79_exp2_block25km",
        arms=("CTRL_H35", "CTRL_SUBSURF", "H79_SUBSURF", "H79_POE"),
    ),
    "exp3": dict(
        mode="block25km",
        default_draws=[116, 117],
        default_out="evidence/h79_exp3_confirm_bw25km",
        arms=("CTRL_H35", "H79_SINGLE_HGB", "H79_POE", "H79_POE_SGMC"),
    ),
}


def file_sha256(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def pooled_sub_dti(rows: list[dict], prefix: str) -> float:
    tp = sum(float(r[f"{prefix}_tp"]) for r in rows)
    fp = sum(float(r[f"{prefix}_fp"]) for r in rows)
    n = sum(int(r[f"{prefix}_n_truth"]) for r in rows)
    return float(tp / (0.2 * (tp + fp) + 0.8 * n + 1e-7)) if n > 0 else 0.0


def summarize_run(out: Path, arms: tuple[str, ...]) -> dict:
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
            pooled_far_gt9_dti=pooled_sub_dti(ar, "far_gt9"),
            pooled_vfar_gt20_dti=pooled_sub_dti(ar, "vfar_gt20"),
            withheld_positive_occurrences=int(sum(r["n_truth"] for r in ar)),
            far_gt9_withheld_occurrences=int(sum(r["far_gt9_n_truth"] for r in ar)),
            vfar_gt20_withheld_occurrences=int(sum(r["vfar_gt20_n_truth"] for r in ar)),
            mean_emitted_dots=float(np.mean([r["n_emitted"] for r in ar])),
            mean_emit_frac_le2=float(np.mean([r["emitted_strata"]["frac_le2"] for r in ar])),
            mean_emit_frac_2_9=float(np.mean([r["emitted_strata"]["frac_2_9"] for r in ar])),
            mean_emit_frac_9_20=float(np.mean([r["emitted_strata"]["frac_9_20"] for r in ar])),
            mean_emit_frac_gt20=float(np.mean([r["emitted_strata"]["frac_gt20"] for r in ar])),
            mean_emit_median_d_vis=float(np.mean([r["emitted_strata"]["median_d_vis"] for r in ar])),
        )

    ctrl_rows = [r for r in rows if r["arm"] == "CTRL_H35"]
    truth_profile = dict(
        mean_truth_frac_le2=float(np.mean([r["truth_strata"]["frac_truth_le2"] for r in ctrl_rows])),
        mean_truth_frac_2_9=float(np.mean([r["truth_strata"]["frac_truth_2_9"] for r in ctrl_rows])),
        mean_truth_frac_gt9=float(np.mean([r["truth_strata"]["frac_truth_gt9"] for r in ctrl_rows])),
        mean_truth_frac_gt20=float(np.mean([r["truth_strata"]["frac_truth_gt20"] for r in ctrl_rows])),
        mean_median_truth_d_vis=float(np.mean([r["truth_strata"]["median_truth_d_vis"] for r in ctrl_rows])),
    )

    contrasts = {}
    if "CTRL_SUBSURF" in arms and "H79_SUBSURF" in arms:
        contrasts["h79_subsurf_vs_ctrl_subsurf"] = pooled_summary(
            rows, candidate="H79_SUBSURF", control="CTRL_SUBSURF"
        )
        contrasts["h79_poe_vs_ctrl_subsurf"] = pooled_summary(
            rows, candidate="H79_POE", control="CTRL_SUBSURF"
        )
        contrasts["h79_poe_vs_h79_subsurf"] = pooled_summary(
            rows, candidate="H79_POE", control="H79_SUBSURF"
        )
    if "H79_POE" in arms:
        contrasts["h79_poe_vs_ctrl_h35"] = pooled_summary(
            rows, candidate="H79_POE", control="CTRL_H35"
        )
    if "H79_SINGLE_HGB" in arms:
        contrasts["h79_poe_vs_single_hgb"] = pooled_summary(
            rows, candidate="H79_POE", control="H79_SINGLE_HGB"
        )
        contrasts["single_hgb_vs_ctrl_h35"] = pooled_summary(
            rows, candidate="H79_SINGLE_HGB", control="CTRL_H35"
        )
    if "H79_POE_SGMC" in arms:
        contrasts["h79_poe_sgmc_vs_h79_poe"] = pooled_summary(
            rows, candidate="H79_POE_SGMC", control="H79_POE"
        )
        contrasts["h79_poe_sgmc_vs_ctrl_h35"] = pooled_summary(
            rows, candidate="H79_POE_SGMC", control="CTRL_H35"
        )

    worst_rec = max(canaries, key=lambda c: c["worst_canary_auc"])
    worst_h79_rec = max(canaries, key=lambda c: c["worst_h79_canary_auc"])
    summary = dict(
        label="HOLDOUT-DTI",
        experiment=design["experiment"],
        mode=design["mode"],
        evaluator=EVALUATOR,
        preregistration=design["preregistration"],
        preregistration_commit=design["preregistration_commit"],
        draws=design["draws"],
        n_cells_per_arm=len(ctrl_rows),
        truth_d_vis_profile=truth_profile,
        per_arm=per_arm,
        contrasts=contrasts,
        leakage_canary=dict(
            cap=design["leakage_auc_cap"],
            n_cells=len(canaries),
            n_columns=canaries[0]["n_columns"],
            max_canary_auc=worst_rec["worst_canary_auc"],
            max_canary_column=worst_rec["worst_column"],
            max_h79_canary_auc=worst_h79_rec["worst_h79_canary_auc"],
            max_h79_canary_column=worst_h79_rec["worst_h79_column"],
            all_passed=all(c["all_passed"] for c in canaries),
        ),
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp", choices=tuple(EXP_SPECS.keys()), required=True)
    ap.add_argument("--draws", type=int, nargs="+", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--resume", action="store_true", help="Resume incomplete cells in existing out dir")
    args = ap.parse_args()

    spec = EXP_SPECS[args.exp]
    draws = list(args.draws) if args.draws is not None else list(spec["default_draws"])
    out = Path(args.out) if args.out is not None else (ROOT / spec["default_out"])
    mode = spec["mode"]
    arms: tuple[str, ...] = spec["arms"]

    if out.exists() and not args.resume:
        raise SystemExit(f"Refusing to overwrite existing evidence directory: {out}")
    out.mkdir(parents=True, exist_ok=True)

    work = work_dir()
    d_root = data_dir()
    t_start = time.time()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; build addons.npy first")

    h34_mm = load_h34_sidecar(work, ctx.fi)
    h74_mm = load_h74_rmps_sidecar(work, ctx.fi)
    h79_mm, h79_names = build_h79_sidecar(work, d_root / "external")
    assert h79_names == H79_ALL_NAMES
    dom_full = binary_erosion(ctx.foot, iterations=DOMAIN_ERODE)
    dom_full_px = float(dom_full.sum())

    # Union matrix layout (93 columns total):
    # [0 .. 63]   static ABCD (64 cols)
    # [64 .. 70]  dynamic E (7 cols)
    # [71 .. 77]  EXTRAS (7 cols)
    # [78]        dynamic H27_tip (1 col)
    # [79 .. 81]  static H34 (3 cols)
    # [82 .. 85]  static H74_RMPS (4 cols)
    # [86 .. 87]  static S_dem_c2, S_dem_s2 from addons.npy[3:5] (2 cols)
    # [88 .. 92]  static H79_ALL (5 cols: 4 CTHM + 1 SGMC)
    s_dem_names = list(ADDON_NAMES[3:5])
    assert s_dem_names == ["S_dem_c2", "S_dem_s2"]
    union_names = (
        list(ctx.static_names)
        + list(ctx.e_names)
        + list(ctx.extra_names)
        + ["H27_tip"]
        + list(H34_NAMES)
        + list(H74_RMPS_NAMES)
        + s_dem_names
        + list(H79_ALL_NAMES)
    )
    assert len(union_names) == 93
    ucol = {n: i for i, n in enumerate(union_names)}

    bde_extra_cols = [ucol[n] for n in ([ctx.all_names[i] for i in ctx.columns("BDE")] + list(EXTRAS))]
    ctrl_h35_cols = bde_extra_cols + [ucol["H27_tip"]] + [ucol[n] for n in H34_NAMES]  # 59 cols

    acd_cols = [ucol[ctx.all_names[i]] for i in ctx.columns("ACD")]  # 40 cols
    sub_extra_cols = [ucol[n] for n in SUBSURF_EXTRAS]               # 4 cols
    h34_cols = [ucol[n] for n in H34_NAMES]                          # 3 cols
    h74_cols = [ucol[n] for n in H74_RMPS_NAMES]                     # 4 cols
    h79_cthm_cols = [ucol[n] for n in H79_CTHM_NAMES]                # 4 cols
    h79_sgmc_cols = [ucol[n] for n in H79_SGMC_NAMES]                # 1 col

    ctrl_subsurf_cols = acd_cols + sub_extra_cols + h34_cols + h74_cols                # 51 cols
    h79_subsurf_cols = ctrl_subsurf_cols + h79_cthm_cols                               # 55 cols
    h79_crustal_sgmc_cols = h79_subsurf_cols + h79_sgmc_cols                           # 56 cols
    morpho_cols = [ucol[ctx.all_names[i]] for i in ctx.columns("B")] + [ucol[n] for n in s_dem_names]  # 26 cols
    single_static_cols = (
        [ucol[ctx.all_names[i]] for i in ctx.columns("ABCD")]
        + [ucol[n] for n in SINGLE_STATIC_EXTRAS]
        + [ucol[n] for n in s_dem_names]
        + h34_cols
        + h74_cols
        + h79_cthm_cols
    )  # 64 + 5 + 2 + 3 + 4 + 4 = 82 static cols (zero E / zero X2_compat)

    assert len(ctrl_subsurf_cols) == 51
    assert len(h79_subsurf_cols) == 55
    assert len(h79_crustal_sgmc_cols) == 56
    assert len(morpho_cols) == 26

    design = dict(
        experiment=f"H79_{args.exp.upper()}_{mode.upper()}",
        exp_id=args.exp,
        mode=mode,
        preregistration="knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md",
        preregistration_commit="b59b129",
        draws=draws,
        folds=list(FOLD_IDS),
        fold_names=list(FOLDS),
        arms=list(arms),
        feature_counts=dict(
            CTRL_H35=len(ctrl_h35_cols),
            CTRL_SUBSURF=len(ctrl_subsurf_cols),
            H79_SUBSURF=len(h79_subsurf_cols),
            M_morpho=len(morpho_cols),
            M_crustal_sgmc=len(h79_crustal_sgmc_cols),
            H79_SINGLE_HGB=len(single_static_cols),
        ),
        poe_params=dict(
            gamma_crustal=POE_GAMMA_CRUSTAL,
            floor_crustal=POE_FLOOR_CRUSTAL,
            floor_morpho=POE_FLOOR_MORPHO,
        ),
        n_neg=int(N_NEG),
        hgb_params=HGB_PARAMS,
        kfrac_h35=KFRAC_H35,
        min_dist_h35=MIN_DIST_H35,
        kfrac_blind=KFRAC_BLIND,
        cat_buf_blind=CAT_BUF_BLIND,
        full_b2_budget=FULL_B2_BUDGET,
        block_px=BLOCK_PX_DEFAULT if mode == "block25km" else None,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        evaluator=EVALUATOR,
        evaluator_hashes={
            "src/gems25/metric.py": file_sha256("src/gems25/metric.py"),
            "src/gems25/holdout.py": file_sha256("src/gems25/holdout.py"),
            "src/gems25/validation.py": file_sha256("src/gems25/validation.py"),
            "src/gems25/h74_rmps.py": file_sha256("src/gems25/h74_rmps.py"),
            "src/gems25/h79_cthm.py": file_sha256("src/gems25/h79_cthm.py"),
        },
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    def build_union_matrix(E_vis: np.ndarray, tip_vis: np.ndarray, idx: np.ndarray) -> np.ndarray:
        X = np.empty((idx.size, 93), dtype=np.float32)
        gather_columns(ctx, E_vis, idx, True, out=X[:, :78])
        X[:, 78] = tip_vis[idx].astype(np.float32)
        X[:, 79:82] = np.asarray(h34_mm[:, idx], dtype=np.float32).T
        X[:, 82:86] = np.asarray(h74_mm[:, idx], dtype=np.float32).T
        X[:, 86:88] = np.asarray(ctx.addon[3:5, idx], dtype=np.float32).T
        X[:, 88:93] = np.asarray(h79_mm[:, idx], dtype=np.float32).T
        return X

    cells_path = out / "cells.jsonl"
    canaries_jsonl = out / "canaries.jsonl"
    done_cells: set[tuple[int, int]] = set()
    done_canaries: dict[tuple[int, int], dict] = {}
    if args.resume and cells_path.exists():
        existing_rows = [json.loads(ln) for ln in cells_path.read_text().splitlines() if ln.strip()]
        for fold in FOLD_IDS:
            for draw in draws:
                got_arms = {r["arm"] for r in existing_rows if r["fold"] == fold and r["draw"] == draw}
                if got_arms == set(arms):
                    done_cells.add((fold, draw))
        if canaries_jsonl.exists():
            for ln in canaries_jsonl.read_text().splitlines():
                if ln.strip():
                    cr = json.loads(ln)
                    done_canaries[(int(cr["fold"]), int(cr["draw"]))] = cr

    canary_records = []
    grid_buf = np.zeros(ctx.foot.shape, dtype=np.float32)

    with cells_path.open("a" if args.resume else "w") as sink, canaries_jsonl.open("a" if args.resume else "w") as csink:
        for fold in FOLD_IDS:
            for draw in draws:
                if (fold, draw) in done_cells and (fold, draw) in done_canaries:
                    canary_records.append(done_canaries[(fold, draw)])
                    continue
                t_cell = time.time()
                d = (
                    ctx.holdout.draw(fold, draw)
                    if mode == "standard"
                    else draw_block25km(ctx.holdout, fold, draw, block_px=BLOCK_PX_DEFAULT)
                )
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

                # Mandatory Protocol Rule 4: test EVERY column standalone + missingness
                cell_canaries = {}
                Xq_eval = Xq_u[auc_eval_idx]
                for col_i, cname in enumerate(union_names):
                    res = feature_canary(Xq_eval[:, col_i], auc_eval_y, cap=LEAKAGE_AUC_CAP)
                    cell_canaries[cname] = res
                    if not res["passed"]:
                        raise RuntimeError(
                            f"LEAKAGE CANARY FIRED in exp={args.exp} fold={fold} draw={draw} "
                            f"col={cname}: canary_auc={res['canary_auc']}"
                        )
                del Xq_eval

                worst_col = max(cell_canaries, key=lambda c: cell_canaries[c]["canary_auc"])
                worst_auc = float(cell_canaries[worst_col]["canary_auc"])
                worst_h79_col = max(H79_ALL_NAMES, key=lambda c: cell_canaries[c]["canary_auc"])
                worst_h79_auc = float(cell_canaries[worst_h79_col]["canary_auc"])
                crec = dict(
                    fold=int(fold),
                    fold_name=FOLDS[fold],
                    draw=int(draw),
                    n_columns=len(union_names),
                    worst_column=worst_col,
                    worst_canary_auc=round(worst_auc, 6),
                    worst_h79_column=worst_h79_col,
                    worst_h79_canary_auc=round(worst_h79_auc, 6),
                    h79_canaries={
                        c: round(float(cell_canaries[c]["canary_auc"]), 6) for c in H79_ALL_NAMES
                    },
                    all_passed=True,
                )
                canary_records.append(crec)
                csink.write(json.dumps(crec) + "\n")
                csink.flush()
                if (fold, draw) in done_cells:
                    del Xtr_u, Xq_u
                    gc.collect()
                    continue

                # Cache shared expert predictions within this cell so PoE reuses identical M_crustal / M_morpho
                p_crustal_55: np.ndarray | None = None
                meta_crustal_55: dict | None = None
                p_morpho_26: np.ndarray | None = None
                meta_morpho_26: dict | None = None

                for arm in arms:
                    if arm == "CTRL_H35":
                        p_q, fmeta = fit_predict(Xtr_u[:, ctrl_h35_cols], y_tr, Xq_u[:, ctrl_h35_cols], seed=draw)
                        em, emeta = emit_sapd(grid_buf, fi_q, sl, dom_c, known_c, p_q)
                    elif arm == "CTRL_SUBSURF":
                        p_q, fmeta = fit_predict(
                            Xtr_u[:, ctrl_subsurf_cols], y_tr, Xq_u[:, ctrl_subsurf_cols], seed=draw
                        )
                        em, emeta = emit_blind_submod(
                            grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px
                        )
                    elif arm == "H79_SUBSURF":
                        p_crustal_55, meta_crustal_55 = fit_predict(
                            Xtr_u[:, h79_subsurf_cols], y_tr, Xq_u[:, h79_subsurf_cols], seed=draw
                        )
                        p_q, fmeta = p_crustal_55, meta_crustal_55
                        em, emeta = emit_blind_submod(
                            grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px
                        )
                    elif arm == "H79_SINGLE_HGB":
                        p_q, fmeta = fit_predict(
                            Xtr_u[:, single_static_cols], y_tr, Xq_u[:, single_static_cols], seed=draw
                        )
                        em, emeta = emit_blind_submod(
                            grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px
                        )
                    elif arm == "H79_POE":
                        if p_crustal_55 is None:
                            p_crustal_55, meta_crustal_55 = fit_predict(
                                Xtr_u[:, h79_subsurf_cols], y_tr, Xq_u[:, h79_subsurf_cols], seed=draw
                            )
                        if p_morpho_26 is None:
                            p_morpho_26, meta_morpho_26 = fit_predict(
                                Xtr_u[:, morpho_cols], y_tr, Xq_u[:, morpho_cols], seed=draw + 1000
                            )
                        p_q = fuse_poe_scores(p_crustal_55, p_morpho_26)
                        fmeta = dict(
                            fit_s=round(meta_crustal_55["fit_s"] + meta_morpho_26["fit_s"], 3),
                            predict_s=round(meta_crustal_55["predict_s"] + meta_morpho_26["predict_s"], 3),
                            n_features=int(len(h79_subsurf_cols) + len(morpho_cols)),
                        )
                        em, emeta = emit_blind_submod(
                            grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px
                        )
                    elif arm == "H79_POE_SGMC":
                        p_cs, meta_cs = fit_predict(
                            Xtr_u[:, h79_crustal_sgmc_cols], y_tr, Xq_u[:, h79_crustal_sgmc_cols], seed=draw
                        )
                        if p_morpho_26 is None:
                            p_morpho_26, meta_morpho_26 = fit_predict(
                                Xtr_u[:, morpho_cols], y_tr, Xq_u[:, morpho_cols], seed=draw + 1000
                            )
                        p_q = fuse_poe_scores(p_cs, p_morpho_26)
                        fmeta = dict(
                            fit_s=round(meta_cs["fit_s"] + meta_morpho_26["fit_s"], 3),
                            predict_s=round(meta_cs["predict_s"] + meta_morpho_26["predict_s"], 3),
                            n_features=int(len(h79_crustal_sgmc_cols) + len(morpho_cols)),
                        )
                        em, emeta = emit_blind_submod(
                            grid_buf, fi_q, sl, dom_c, known_c, d_vis_c, p_q, dom_full_px
                        )
                        del p_cs
                    else:
                        raise ValueError(f"Unknown arm: {arm}")

                    auc_val = (
                        float(roc_auc_score(auc_eval_y, p_q[auc_eval_idx]))
                        if np.unique(p_q[auc_eval_idx]).size > 1
                        else 0.5
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
                            exp=args.exp,
                            mode=mode,
                            arm=arm,
                            fold=int(fold),
                            fold_name=FOLDS[fold],
                            draw=int(draw),
                            canary_max_auc=round(worst_auc, 6),
                            canary_h79_max_auc=round(worst_h79_auc, 6),
                            **fmeta,
                            **emeta,
                        ),
                    )
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    if arm not in ("H79_SUBSURF",):
                        del p_q
                    del em

                del p_crustal_55, p_morpho_26, Xtr_u, Xq_u
                gc.collect()
                print(
                    f"[{time.time() - t_start:6.1f}s] exp={args.exp}({mode}) fold={fold}({FOLDS[fold]}) "
                    f"draw={draw} truth={truth_strata['n_truth']:,} med_dvis={truth_strata['median_truth_d_vis']:.1f}px "
                    f"worst_canary={worst_col}:{worst_auc:.4f} h79_canary={worst_h79_col}:{worst_h79_auc:.4f} "
                    f"({time.time() - t_cell:.1f}s)",
                    flush=True,
                )

    (out / "feature_canaries.json").write_text(json.dumps(canary_records, indent=1) + "\n")
    summary = summarize_run(out, arms)
    print(f"Completed {args.exp} in {time.time() - t_start:.1f}s -> {out}")
    for arm, st in summary["per_arm"].items():
        print(
            f"  {arm:16s} pooled_DTI={st['pooled_dti']:.6f} far>9={st['pooled_far_gt9_dti']:.6f} "
            f"vfar>20={st['pooled_vfar_gt20_dti']:.6f} AUC={st['mean_auc']:.4f} "
            f"dots={st['mean_emitted_dots']:.0f} emit_gt20={st['mean_emit_frac_gt20']*100:.1f}%"
        )


if __name__ == "__main__":
    main()
