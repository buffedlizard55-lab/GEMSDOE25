#!/usr/bin/env python3
"""Run the preregistered H31 single-lane 3-experiment suite on fresh hide-and-recover draws 10, 11.

Preregistration: ``knowledge/13_preregistered_h31_anisotropic_scarp_coherence_2026-10-25.md``.
Executes:
  - Single-feature leakage canary across all base, add-on, tip, and H31 columns (gate: max(AUC, 1-AUC) <= 0.90)
  - Control 0: BASE (BDE + X1 + X2 + X3)
  - Control 1: T_BASE (BASE + H27_tip)
  - Experiment 1: H31_E1_ANISO (T_BASE + 4 anisotropic structural continuation columns)
  - Experiment 2: H31_E2_COH (H31_E1_ANISO + 2 cross-scale 3DEP LiDAR rotational strike coherence columns)
  - Experiment 3: H31_E3_B2 (H31_E2_COH + post-thinning B=2.0 px = 200 m digitization-shadow flank exclusion)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.h31 import (  # noqa: E402
    H31_ANISO_NAMES,
    H31_ARMS,
    H31_COH_NAMES,
    H31_FEATURE_NAMES,
    apply_digitization_shadow_guard,
    build_h31_features,
    build_static_lidar_dem_coherence,
)
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402

EVALUATOR_VERSION = "HOLDOUT-DTI-v1 (alpha=0.2, beta=0.8, R=300m triangular kernel, 20km blocks, 2km guard, 3px visible-collar, 12px domain erosion)"
FOLDS = ["NW", "NE", "SW", "SE"]
DEFAULT_DRAWS = [10, 11]
DESIGN_SEED = 20261025
KFRAC = 0.035
MIN_DIST_PX = 2.4
B2_BUFFER_PX = 2.0
BASE_FAMILIES = "BDE"
BASE_EXTRAS = ["X1_K", "X1_ThK", "X1_UK", "X2_compat", "X2_compat_coh", "X3_gm", "X3_gd"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ci95(values: list[float] | np.ndarray) -> tuple[float, float, float]:
    """Return ``(mean, ci_low, ci_high)`` using two-sided 95% Student-t interval."""
    arr = np.asarray(values, dtype=float)
    mean = float(np.mean(arr))
    if arr.size < 2:
        return mean, mean, mean
    sd = float(np.std(arr, ddof=1))
    se = sd / np.sqrt(arr.size)
    crit = float(student_t.ppf(0.975, df=arr.size - 1))
    half = crit * se
    return mean, mean - half, mean + half


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, nargs="+", default=DEFAULT_DRAWS)
    ap.add_argument("--out", default=str(ROOT / "evidence" / "h31_experiments"))
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    prereg_path = ROOT / "knowledge" / "13_preregistered_h31_anisotropic_scarp_coherence_2026-10-25.md"

    ctx = load_context(work_dir())
    l_c2, l_s2, l_coh, lidar_dem_compat = build_static_lidar_dem_coherence(
        ctx.static, ctx.static_names, ctx.addon
    )

    base_cols = ctx.columns(BASE_FAMILIES) + ctx.named(BASE_EXTRAS)
    t_cols = base_cols + ctx.named(["H27_tip"])

    fitted_arms = ["BASE", "T_BASE", "H31_E1_ANISO", "H31_E2_COH"]
    rng = np.random.default_rng(DESIGN_SEED)
    order = rng.permutation(len(fitted_arms)).tolist()
    randomized_fitted = [fitted_arms[i] for i in order]

    design = {
        "schema_version": 1,
        "hypothesis": "H31-1",
        "method_lane": "Anisotropic Along-Strike Structural Continuation + Cross-Scale 3DEP LiDAR Rotational Strike Coherence + B=2 Digitization-Shadow Guard",
        "evaluator_version": EVALUATOR_VERSION,
        "preregistration": str(prereg_path.relative_to(ROOT)),
        "preregistration_sha256": sha256_file(prereg_path) if prereg_path.exists() else None,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "draws": list(args.draws),
        "spatial_folds": FOLDS,
        "design_seed": DESIGN_SEED,
        "fitted_arms_canonical": fitted_arms,
        "fitted_arms_randomized_order": randomized_fitted,
        "all_arms": list(H31_ARMS),
        "base_families": BASE_FAMILIES,
        "base_extras": BASE_EXTRAS,
        "h31_aniso_features": list(H31_ANISO_NAMES),
        "h31_coherence_features": list(H31_COH_NAMES),
        "hgb_params": HGB_PARAMS,
        "emission": {
            "kfrac": KFRAC,
            "min_dist_px": MIN_DIST_PX,
            "e3_post_thinning_flank_guard_px": B2_BUFFER_PX,
        },
    }
    (out_dir / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    cells_path = out_dir / "cells.jsonl"
    existing_cells: dict[tuple[int, int], list[dict]] = {}
    if cells_path.exists():
        for line in cells_path.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            existing_cells.setdefault((int(r["fold"]), int(r["draw"])), []).append(r)

    cells_rows: list[dict] = []
    canary_by_feature: dict[str, list[float]] = {}
    withheld_positives_by_cell: list[dict] = []

    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in range(4):
            for draw in args.draws:
                t_cell = time.time()
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                h31_mat = build_h31_features(
                    cell.draw.visible,
                    ctx.foot,
                    ctx.fi,
                    l_c2,
                    l_s2,
                    l_coh,
                    lidar_dem_compat,
                )
                n_orig = cell.Xtr.shape[1]
                cell.Xtr = np.hstack([cell.Xtr, h31_mat[:, cell.train_idx].T])
                cell.Xq = np.hstack([cell.Xq, h31_mat[:, cell.q].T])

                aniso_cols = list(range(n_orig, n_orig + 4))
                coh_cols = list(range(n_orig + 4, n_orig + 6))
                arm_cols = {
                    "BASE": base_cols,
                    "T_BASE": t_cols,
                    "H31_E1_ANISO": t_cols + aniso_cols,
                    "H31_E2_COH": t_cols + aniso_cols + coh_cols,
                }

                # 1. Single-feature leakage canary on every candidate column in this cell
                for col_idx in t_cols:
                    fname = ctx.all_names[col_idx]
                    raw_auc = cell.auc(cell.Xq[:, col_idx])
                    canary_by_feature.setdefault(fname, []).append(float(raw_auc))
                for offset, fname in enumerate(H31_FEATURE_NAMES):
                    col_idx = n_orig + offset
                    raw_auc = cell.auc(cell.Xq[:, col_idx])
                    canary_by_feature.setdefault(fname, []).append(float(raw_auc))

                n_withheld = int(cell.truth_c.sum())
                withheld_positives_by_cell.append(
                    {
                        "fold": fold,
                        "fold_name": FOLDS[fold],
                        "draw": draw,
                        "n_withheld_positives": n_withheld,
                        "domain_pixels": int(cell.dom_c.sum()),
                    }
                )

                cached = existing_cells.get((fold, draw), [])
                if len(cached) == len(H31_ARMS):
                    by_arm = {r["arm"]: r for r in cached}
                    for arm in H31_ARMS:
                        row = by_arm[arm]
                        cells_rows.append(row)
                        sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(
                        f"[fold {fold} ({FOLDS[fold]}) draw {draw} | CACHED | {time.time()-t_cell:.1f}s] "
                        + " | ".join(f"{a}={by_arm[a]['dti']:.6f}" for a in H31_ARMS),
                        flush=True,
                    )
                    del cell
                    continue

                # 2. Fit and evaluate the 4 fitted arms in randomized order, plus E3 (post-thinning B=2 guard on E2)
                k = int(round(KFRAC * cell.dom_c.sum()))
                cell_results: dict[str, dict] = {}
                e2_emitted = None
                e2_auc = None
                e2_timing = None

                for run_order, arm in enumerate(randomized_fitted, start=1):
                    p, timing = cell.fit_predict(arm_cols[arm], seed=draw)
                    score_crop, candidates = cell.candidates(p, k)
                    emitted = score_ordered_dots(score_crop, candidates, MIN_DIST_PX)
                    ev = cell.evaluate(emitted)
                    auc_val = cell.auc(p)
                    row = {
                        "fold": fold,
                        "fold_name": FOLDS[fold],
                        "draw": draw,
                        "run_order": run_order,
                        "arm": arm,
                        "kfrac": KFRAC,
                        "min_dist_px": MIN_DIST_PX,
                        "flank_guard_px": 0.0,
                        "auc": auc_val,
                        **ev,
                        **timing,
                    }
                    cell_results[arm] = row
                    if arm == "H31_E2_COH":
                        e2_emitted = emitted
                        e2_auc = auc_val
                        e2_timing = timing

                # Experiment 3: Post-thinning B=2.0 px digitization-shadow flank exclusion on H31_E2_COH
                t_b2 = time.time()
                emitted_b2 = apply_digitization_shadow_guard(e2_emitted, cell.known_c, B2_BUFFER_PX)
                b2_s = time.time() - t_b2
                ev_b2 = cell.evaluate(emitted_b2)
                cell_results["H31_E3_B2"] = {
                    "fold": fold,
                    "fold_name": FOLDS[fold],
                    "draw": draw,
                    "run_order": 5,
                    "arm": "H31_E3_B2",
                    "kfrac": KFRAC,
                    "min_dist_px": MIN_DIST_PX,
                    "flank_guard_px": B2_BUFFER_PX,
                    "auc": e2_auc,
                    **ev_b2,
                    "fit_s": e2_timing["fit_s"],
                    "predict_s": e2_timing["predict_s"] + b2_s,
                }

                for arm in H31_ARMS:
                    row = cell_results[arm]
                    cells_rows.append(row)
                    sink.write(json.dumps(row) + "\n")
                sink.flush()

                print(
                    f"[fold {fold} ({FOLDS[fold]}) draw {draw} | n_pos={n_withheld} | {time.time()-t_cell:.1f}s] "
                    + " | ".join(f"{a}={cell_results[a]['dti']:.6f}" for a in H31_ARMS),
                    flush=True,
                )
                del cell

    # Summarize leakage canary
    canary_summary = []
    canary_all_pass = True
    for fname, vals in canary_by_feature.items():
        arr = np.asarray(vals, dtype=float)
        sym = np.maximum(arr, 1.0 - arr)
        max_sym = float(np.max(sym))
        mean_raw = float(np.mean(arr))
        mean_sym = float(np.mean(sym))
        passed = bool(max_sym <= 0.90)
        if not passed:
            canary_all_pass = False
        canary_summary.append(
            {
                "feature": fname,
                "mean_auc": round(mean_raw, 6),
                "mean_symmetric_auc": round(mean_sym, 6),
                "max_symmetric_auc": round(max_sym, 6),
                "threshold": 0.90,
                "pass": passed,
            }
        )
    canary_summary.sort(key=lambda r: r["max_symmetric_auc"], reverse=True)
    canary_payload = {
        "schema_version": 1,
        "evaluator_version": EVALUATOR_VERSION,
        "threshold_max_symmetric_auc": 0.90,
        "n_features_checked": len(canary_summary),
        "all_features_pass": canary_all_pass,
        "max_observed_symmetric_auc": canary_summary[0]["max_symmetric_auc"] if canary_summary else 0.0,
        "max_observed_feature": canary_summary[0]["feature"] if canary_summary else None,
        "features": canary_summary,
    }
    (out_dir / "leakage_canary.json").write_text(json.dumps(canary_payload, indent=1) + "\n")

    # Summarize arm metrics (both cell-mean with 8-cell 95% CI, 4-fold block mean with 4-fold 95% CI, and pooled DTI)
    arm_summaries: dict[str, dict] = {}
    for arm in H31_ARMS:
        rows = [r for r in cells_rows if r["arm"] == arm]
        cell_dtis = [r["dti"] for r in rows]
        mean_cell, lo_cell, hi_cell = ci95(cell_dtis)

        fold_means = []
        fold_dict = {}
        for fold in range(4):
            f_rows = [r["dti"] for r in rows if r["fold"] == fold]
            fm = float(np.mean(f_rows))
            fold_means.append(fm)
            fold_dict[FOLDS[fold]] = round(fm, 6)
        mean_fold, lo_fold, hi_fold = ci95(fold_means)

        tot_tp = float(sum(r["tp"] for r in rows))
        tot_fp = float(sum(r["fp"] for r in rows))
        tot_truth = int(sum(r["n_truth"] for r in rows))
        tot_emitted = int(sum(r["emitted"] for r in rows))
        fn = max(float(tot_truth) - tot_tp, 0.0)
        pooled_dti = float(tot_tp / (tot_tp + 0.2 * tot_fp + 0.8 * fn))

        arm_summaries[arm] = {
            "arm": arm,
            "n_cells": len(rows),
            "total_withheld_positives": tot_truth,
            "mean_withheld_positives_per_cell": round(tot_truth / max(len(rows), 1), 1),
            "pooled_holdout_dti": round(pooled_dti, 6),
            "cell_mean_holdout_dti": round(mean_cell, 6),
            "cell_ci95": [round(lo_cell, 6), round(hi_cell, 6)],
            "fold_mean_holdout_dti": round(mean_fold, 6),
            "fold_ci95": [round(lo_fold, 6), round(hi_fold, 6)],
            "per_fold_dti": fold_dict,
            "mean_coverage": round(float(np.mean([r["coverage"] for r in rows])), 6),
            "mean_auc": round(float(np.mean([r["auc"] for r in rows])), 6),
            "mean_emitted_per_cell": round(float(np.mean([r["emitted"] for r in rows])), 1),
            "total_emitted": tot_emitted,
            "mean_hug_share": round(float(np.mean([r["hug"] for r in rows])), 6),
        }

    # Paired contrasts
    def paired_contrast(cand_arm: str, ref_arm: str) -> dict:
        c_rows = {(r["fold"], r["draw"]): r for r in cells_rows if r["arm"] == cand_arm}
        b_rows = {(r["fold"], r["draw"]): r for r in cells_rows if r["arm"] == ref_arm}
        keys = sorted(c_rows.keys())
        diffs_cell = [c_rows[k]["dti"] - b_rows[k]["dti"] for k in keys]
        m_c, lo_c, hi_c = ci95(diffs_cell)

        fold_diffs = []
        fold_diff_map = {}
        for fold in range(4):
            fd = float(np.mean([c_rows[(fold, d)]["dti"] - b_rows[(fold, d)]["dti"] for d in args.draws]))
            fold_diffs.append(fd)
            fold_diff_map[FOLDS[fold]] = round(fd, 6)
        m_f, lo_f, hi_f = ci95(fold_diffs)
        hug_diff = float(np.mean([c_rows[k]["hug"] - b_rows[k]["hug"] for k in keys]))
        pooled_diff = arm_summaries[cand_arm]["pooled_holdout_dti"] - arm_summaries[ref_arm]["pooled_holdout_dti"]
        return {
            "candidate": cand_arm,
            "reference": ref_arm,
            "pooled_dti_delta": round(pooled_diff, 6),
            "mean_dti_delta": round(m_c, 6),
            "cell_delta_ci95": [round(lo_c, 6), round(hi_c, 6)],
            "fold_delta_ci95": [round(lo_f, 6), round(hi_f, 6)],
            "per_fold_delta": fold_diff_map,
            "folds_positive": int(sum(1 for d in fold_diffs if d > 0.0)),
            "worst_fold_delta": round(float(min(fold_diffs)), 6),
            "mean_hug_delta": round(hug_diff, 6),
        }

    contrasts = {
        "E1_vs_BASE": paired_contrast("H31_E1_ANISO", "BASE"),
        "E1_vs_T_BASE": paired_contrast("H31_E1_ANISO", "T_BASE"),
        "E2_vs_BASE": paired_contrast("H31_E2_COH", "BASE"),
        "E2_vs_T_BASE": paired_contrast("H31_E2_COH", "T_BASE"),
        "E2_vs_E1": paired_contrast("H31_E2_COH", "H31_E1_ANISO"),
        "E3_vs_BASE": paired_contrast("H31_E3_B2", "BASE"),
        "E3_vs_T_BASE": paired_contrast("H31_E3_B2", "T_BASE"),
        "E3_vs_E2": paired_contrast("H31_E3_B2", "H31_E2_COH"),
    }

    c_vs_base = contrasts["E3_vs_BASE"]
    c_vs_t = contrasts["E3_vs_T_BASE"]
    c_vs_e2 = contrasts["E3_vs_E2"]
    promote_gate = {
        "leakage_canary_pass": canary_all_pass,
        "beats_base_outside_noise_ci95_gt_0": bool(c_vs_base["cell_delta_ci95"][0] > 0.0 and c_vs_base["mean_dti_delta"] > 0.005),
        "beats_t_base_outside_noise_ci95_gt_0": bool(c_vs_t["cell_delta_ci95"][0] > 0.0 and c_vs_t["mean_dti_delta"] > 0.001),
        "exceeds_historical_holdout_best_0_152003": bool(arm_summaries["H31_E3_B2"]["cell_mean_holdout_dti"] > 0.152003389),
        "positive_in_at_least_3_of_4_folds_vs_base": bool(c_vs_base["folds_positive"] >= 3),
        "positive_in_at_least_3_of_4_folds_vs_t_base": bool(c_vs_t["folds_positive"] >= 3),
        "worst_fold_gt_minus_0_010": bool(c_vs_t["worst_fold_delta"] > -0.010),
        "reduces_hug_share_vs_t_base_and_e2": bool(
            c_vs_t["mean_hug_delta"] < 0.0 and c_vs_e2["mean_hug_delta"] < 0.0 and abs(c_vs_base["mean_hug_delta"]) <= 0.05
        ),
    }
    promote_gate["all_passed"] = bool(all(promote_gate.values()))

    results = {
        "schema_version": 1,
        "hypothesis": "H31-1",
        "evaluator_version": EVALUATOR_VERSION,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "elapsed_seconds": round(time.time() - t_all, 1),
        "draws": list(args.draws),
        "spatial_folds": FOLDS,
        "withheld_positives_by_cell": withheld_positives_by_cell,
        "total_withheld_positives_across_cells": int(sum(c["n_withheld_positives"] for c in withheld_positives_by_cell)),
        "leakage_canary": {
            "all_features_pass": canary_all_pass,
            "max_observed_symmetric_auc": canary_payload["max_observed_symmetric_auc"],
            "max_observed_feature": canary_payload["max_observed_feature"],
            "top_10_features": canary_summary[:10],
        },
        "arms": arm_summaries,
        "paired_contrasts": contrasts,
        "promotion_gate": promote_gate,
        "verdict": "promote" if promote_gate["all_passed"] else "negative",
    }
    (out_dir / "results.json").write_text(json.dumps(results, indent=1) + "\n")

    # Write human-readable Markdown summary
    md = [
        "# H31 Single-Lane 3-Experiment Holdout Results (Draws 10, 11)",
        "",
        f"- **Evaluator:** `{EVALUATOR_VERSION}`",
        f"- **Draws:** `{args.draws}` across 4 spatial folds (`NW`, `NE`, `SW`, `SE`, 8 cells total)",
        f"- **Total withheld positive fault pixels across 8 cells:** `{results['total_withheld_positives_across_cells']:,}`",
        f"- **Leakage canary (`max(AUC, 1-AUC) <= 0.90`):** `PASS={canary_all_pass}` (highest single-feature symmetric AUC: `{canary_payload['max_observed_Feature'] if 'max_observed_Feature' in canary_payload else canary_payload['max_observed_feature']}` = `{canary_payload['max_observed_symmetric_auc']:.4f}`)",
        f"- **Verdict:** **`{results['verdict'].upper()}`**",
        "",
        "## Arm Summary (`HOLDOUT-DTI`)",
        "",
        "| Arm | Pooled `HOLDOUT-DTI` | Cell Mean `HOLDOUT-DTI` | 95% CI (8 cells) | 95% CI (4 folds) | `NW` | `NE` | `SW` | `SE` | Mean Emitted | Hug Share |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in H31_ARMS:
        s = arm_summaries[arm]
        pf = s["per_fold_dti"]
        md.append(
            f"| `{arm}` | **{s['pooled_holdout_dti']:.6f}** | **{s['cell_mean_holdout_dti']:.6f}** | "
            f"`[{s['cell_ci95'][0]:.6f}, {s['cell_ci95'][1]:.6f}]` | `[{s['fold_ci95'][0]:.6f}, {s['fold_ci95'][1]:.6f}]` | "
            f"{pf['NW']:.6f} | {pf['NE']:.6f} | {pf['SW']:.6f} | {pf['SE']:.6f} | "
            f"{s['mean_emitted_per_cell']:.1f} | {s['mean_hug_share']:.4f} |"
        )
    md += [
        "",
        "## Paired Contrasts",
        "",
        "| Contrast | Pooled $\\Delta$DTI | Mean $\\Delta$DTI | 95% CI (8 cells) | Folds $+$ | Worst Fold $\\Delta$ | $\\Delta$ Hug Share |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    for cname, c in contrasts.items():
        md.append(
            f"| `{cname}` | `{c['pooled_dti_delta']:+.6f}` | **`{c['mean_dti_delta']:+.6f}`** | "
            f"`[{c['cell_delta_ci95'][0]:+.6f}, {c['cell_delta_ci95'][1]:+.6f}]` | "
            f"`{c['folds_positive']}/4` | `{c['worst_fold_delta']:+.6f}` | `{c['mean_hug_delta']:+.4f}` |"
        )
    (out_dir / "results.md").write_text("\n".join(md) + "\n")
    print(f"\nDONE in {results['elapsed_seconds']}s -> {out_dir / 'results.json'} (verdict={results['verdict']})", flush=True)


if __name__ == "__main__":
    main()
