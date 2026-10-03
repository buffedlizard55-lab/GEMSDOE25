#!/usr/bin/env python3
"""Validate and analyze the frozen H30-1 2² paired-relay × terrain holdout run."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.h30 import (  # noqa: E402
    H30_ARMS,
    H30_BASE_EXTRAS,
    H30_CONTROL,
    H30_HISTORICAL_H28_COMPARATOR_DTI,
    H30_HISTORICAL_TIP_SCREEN_DTI,
    factorial_2x2_effects,
    h30_promotion_gate,
)

EXPECTED_DRAWS = {"screen": [6, 7], "confirm": [8, 9]}
EXPECTED_ARMS = {"BASE_NO_TIP", *H30_ARMS}
FROZEN_DESIGN_SEED = 20261004
FROZEN_CANONICAL_MATRIX = [
    {"arm": "BASE_NO_TIP", "P": -1, "S": -1, "include_tip": False, "factorial_arm": False},
    {"arm": "T_BASE", "P": -1, "S": -1, "include_tip": True, "factorial_arm": True},
    {"arm": "T_PLUS_P", "P": 1, "S": -1, "include_tip": True, "factorial_arm": True},
    {"arm": "T_PLUS_S", "P": -1, "S": 1, "include_tip": True, "factorial_arm": True},
    {"arm": "T_PLUS_P_S", "P": 1, "S": 1, "include_tip": True, "factorial_arm": True},
]
EXPECTED_FOLDS = ["NW", "NE", "SW", "SE"]
EXPECTED_HGB_PARAMETERS = {
    "max_iter": 100,
    "learning_rate": 0.12,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 50,
    "l2_regularization": 1.0,
    "class_weight": {"0": 1, "1": 5},
    "early_stopping": False,
    "fit_seed": "draw",
    "negative_sample_count_max": 300000,
}
METRICS = ("dti", "coverage", "emitted", "hug", "auc")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_frozen_design(design: dict, stage: str) -> None:
    """Fail closed if a run's saved plan differs from the committed H30 preregistration."""
    preregistration = ROOT / "knowledge" / "11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md"
    if (design.get("preregistration") != str(preregistration.relative_to(ROOT))
            or design.get("preregistration_sha256") != sha256_file(preregistration)):
        raise SystemExit("H30 design does not identify the current, hash-pinned preregistration")
    if design.get("draws") != EXPECTED_DRAWS[stage]:
        raise SystemExit(f"design draw order differs from frozen {stage} draws {EXPECTED_DRAWS[stage]}")
    if design.get("spatial_folds") != EXPECTED_FOLDS:
        raise SystemExit("design spatial folds differ from the frozen NW,NE,SW,SE order")
    if design.get("design_seed") != FROZEN_DESIGN_SEED:
        raise SystemExit("design randomization seed differs from the frozen seed")
    if design.get("canonical_matrix") != FROZEN_CANONICAL_MATRIX:
        raise SystemExit("canonical H30 arm matrix differs from the frozen 2x2 plus no-tip control")
    expected_order = np.random.default_rng(FROZEN_DESIGN_SEED).permutation(5).tolist()
    if design.get("row_order_zero_based") != expected_order:
        raise SystemExit("saved randomized row order differs from the frozen RNG permutation")
    expected_randomized = [FROZEN_CANONICAL_MATRIX[i] for i in expected_order]
    if design.get("randomized_matrix") != expected_randomized:
        raise SystemExit("randomized H30 matrix differs from the frozen row order")
    if design.get("fixed_model_families") != "BDE" or design.get("fixed_addons") != H30_BASE_EXTRAS:
        raise SystemExit("fixed H30 base feature families/add-ons differ from the preregistration")
    if design.get("fixed_tip_control") != "H27_tip":
        raise SystemExit("H30 factorial does not use the frozen H27 tip-only control")
    if design.get("factorial_rows") != ["T_BASE", "T_PLUS_P", "T_PLUS_S", "T_PLUS_P_S"]:
        raise SystemExit("H30 factorial response arms differ from the frozen 2x2")
    if design.get("control_row") != "BASE_NO_TIP":
        raise SystemExit("H30 no-tip control differs from the frozen design")
    if design.get("paired_bridge_definition") != {
        "endpoint_source": "draw.visible only",
        "connectivity": 8,
        "distinct_visible_components": True,
        "distance_px": [2.0, 15.0],
        "minimum_tip_coherence": 0.25,
        "minimum_cos2_strike_compatibility": 0.5,
        "minimum_cross_strike_fraction": 0.35,
        "pair_weight": "exp(-distance/8) × clip((cos2-0.5)/0.5,0,1) × sqrt(coherence_1*coherence_2) × cross_strike_fraction",
        "segment_sampling_max_step_px": 0.5,
        "buffer_disk_radius_px": 2,
    }:
        raise SystemExit("H30 paired-bridge feature definition differs from the frozen design")
    if design.get("hgb_parameters") != EXPECTED_HGB_PARAMETERS:
        raise SystemExit("H30 model/sample parameters differ from the frozen design")
    if design.get("emission") != {
        "method": "Hessian ridge NMS → top-K → score-ordered Poisson-disk",
        "nms_sigma_px": 1.0,
        "k_fraction": 0.035,
        "min_distance_px": 2.4,
        "drop_visible_catalogue": True,
    }:
        raise SystemExit("H30 emission parameters differ from the frozen design")
    if design.get("terrain_feature") != (
        "clip(scale(L_step_max) * scale(L_cross_max) * scale(L_coh100), 0, 1); "
        "Context.scale 1st/99th percentiles from default_rng(1) sample of 200000 footprint pixels"
    ):
        raise SystemExit("H30 terrain feature definition differs from the frozen design")
    terrain_scale = design.get("terrain_scaling_parameters_1st_99th_percentile", {})
    if set(terrain_scale) != {"L_step_max", "L_cross_max", "L_coh100"}:
        raise SystemExit("H30 design must save all three fixed terrain percentile scales")
    for name, limits in terrain_scale.items():
        try:
            limits_arr = np.asarray(limits, dtype=float)
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"invalid frozen terrain scale for {name}: {limits}") from exc
        if limits_arr.shape != (2,) or not np.isfinite(limits_arr).all() or limits_arr[1] <= limits_arr[0]:
            raise SystemExit(f"invalid frozen terrain scale for {name}: {limits}")
    revision = design.get("code_revision")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SystemExit("H30 design is missing the frozen Git commit hash")
    if design.get("clean_worktree_before_fit") is not True:
        raise SystemExit("H30 run was not launched from a clean committed worktree")

    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    expected_manifest = {
        row["id"]: {"sha256": row["sha256"], "bytes": row["bytes"]}
        for row in manifest["files"]
    }
    if design.get("data_manifest_sha256_and_bytes") != expected_manifest:
        raise SystemExit("H30 run does not carry the current pinned source-manifest hashes")
    cache_record = json.loads((ROOT / "evidence" / "work_cache_hashes.json").read_text())
    cache_names = (
        "static_ABCD.npy",
        "static_ABCD.npy.names.json",
        "addons.npy",
        "addons.npy.names.json",
        "bands/_footprint.npy",
        "bands/_labels.npy",
    )
    expected_caches = {name: cache_record[name] for name in cache_names}
    if design.get("derived_cache_sha256_verified") != expected_caches:
        raise SystemExit("H30 run does not carry the pinned derived-cache hashes")


def verify_passing_screen(run: Path) -> dict:
    """Recompute the saved screen gate from hash-bound raw cells before permitting confirmation.

    A passing flag in ``results.json`` is not trusted on its own: the confirmation path verifies the frozen
    design, ties the summary to the exact raw files, validates all 40 registered cells, and recalculates the gate.
    """
    run = Path(run)
    design_path, cells_path, results_path = run / "design.json", run / "cells.jsonl", run / "results.json"
    if not all(path.is_file() for path in (design_path, cells_path, results_path)):
        raise SystemExit(f"confirmation requires complete screen design/cells/results in {run}")
    try:
        design = json.loads(design_path.read_text())
        results = json.loads(results_path.read_text())
        rows = [json.loads(line) for line in cells_path.read_text().splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read complete H30 screen evidence in {run}: {exc}") from exc
    validate_frozen_design(design, "screen")
    if (design.get("stage") != "screen" or results.get("stage") != "screen"
            or results.get("design") != design or results.get("n_rows") != 40):
        raise SystemExit("saved H30 screen summary does not match its registered design and expected 40 cells")
    expected_hashes = {
        "design.json": sha256_file(design_path),
        "cells.jsonl": sha256_file(cells_path),
    }
    if results.get("evidence_sha256") != expected_hashes:
        raise SystemExit("saved H30 screen summary does not bind the exact design and raw-cell files")

    draws = EXPECTED_DRAWS["screen"]
    if any(not isinstance(row, dict) for row in rows):
        raise SystemExit("saved H30 screen cells must each be a JSON object")
    expected_keys = {(fold, draw, arm) for fold in range(4) for draw in draws for arm in EXPECTED_ARMS}
    actual_keys = [(row.get("fold"), row.get("draw"), row.get("arm")) for row in rows]
    if len(rows) != 40 or len(set(actual_keys)) != 40 or set(actual_keys) != expected_keys:
        raise SystemExit("saved H30 screen cells are incomplete, duplicated, or outside the frozen design")
    config_by_arm = {row["arm"]: row for row in design["randomized_matrix"]}
    order_by_arm = {row["arm"]: i + 1 for i, row in enumerate(design["randomized_matrix"])}
    lookup: dict[tuple[int, int, str], dict] = {}
    for row in rows:
        fold, draw, arm = row["fold"], row["draw"], row["arm"]
        if (type(fold) is not int or type(draw) is not int or arm not in EXPECTED_ARMS
                or row.get("stage") != "screen" or row.get("fold_name") != EXPECTED_FOLDS[fold]
                or row.get("run_order") != order_by_arm[arm]
                or row.get("P") != config_by_arm[arm]["P"] or row.get("S") != config_by_arm[arm]["S"]
                or row.get("include_tip") != config_by_arm[arm]["include_tip"]
                or row.get("factorial_arm") != config_by_arm[arm]["factorial_arm"]
                or row.get("design_seed") != design["design_seed"]
                or row.get("k_fraction") != design["emission"]["k_fraction"]
                or row.get("min_distance_px") != design["emission"]["min_distance_px"]):
            raise SystemExit(f"saved H30 screen cell metadata disagrees with its frozen design: {row}")
        try:
            dti_value, hug_value = float(row["dti"]), float(row["hug"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"saved H30 screen cell lacks finite DTI/hug metrics: {row}") from exc
        if not np.isfinite([dti_value, hug_value]).all() or not (0.0 <= dti_value <= 1.0 and 0.0 <= hug_value <= 1.0):
            raise SystemExit(f"saved H30 screen cell has out-of-range DTI/hug metrics: {row}")
        lookup[(fold, draw, arm)] = row

    dti_by_fold: dict[str, list[float]] = {}
    hug_by_fold: dict[str, list[float]] = {}
    for arm in EXPECTED_ARMS:
        dti_by_fold[arm] = [
            float(np.mean([lookup[(fold, draw, arm)]["dti"] for draw in draws]))
            for fold in range(4)
        ]
        hug_by_fold[arm] = [
            float(np.mean([lookup[(fold, draw, arm)]["hug"] for draw in draws]))
            for fold in range(4)
        ]
    gate = h30_promotion_gate(
        dti_by_fold["T_PLUS_P_S"],
        {H30_CONTROL: dti_by_fold[H30_CONTROL], "T_BASE": dti_by_fold["T_BASE"]},
        hug_by_fold["T_PLUS_P_S"],
        {H30_CONTROL: hug_by_fold[H30_CONTROL], "T_BASE": hug_by_fold["T_BASE"]},
    )
    if results.get("paired_promotion_gate") != gate or results.get("screen_gate_passed") is not gate["paired_gate_passed"]:
        raise SystemExit("saved H30 screen summary gate does not reproduce from its hash-bound raw cells")
    if results.get("slot_eligible") is not False:
        raise SystemExit("an H30 screen result can never mark a candidate slot-eligible")
    if not gate["paired_gate_passed"]:
        raise SystemExit("H30 screen gate failed; confirmation is prohibited")
    return results


def validate_cell_metrics(row: dict) -> None:
    """Check DTI diagnostics without assuming distance-weighted TP/FP credits are integers."""
    try:
        metric_values = np.asarray([row[name] for name in METRICS], dtype=float)
        tp, fp, n_truth = np.asarray([row[name] for name in ("tp", "fp", "n_truth")], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"missing/malformed metric or credit count in cell row: {row}") from exc
    if not np.isfinite(metric_values).all() or not np.isfinite([tp, fp, n_truth]).all():
        raise SystemExit(f"nonfinite primary/diagnostic result in row: {row}")
    if any(not 0.0 <= row[name] <= 1.0 for name in ("dti", "coverage", "hug", "auc")):
        raise SystemExit(f"unit-range metric outside [0,1] in cell row: {row}")
    emitted = metric_values[2]
    if (emitted < 0 or int(emitted) != emitted or min(tp, fp, n_truth) < 0
            or not np.isclose(n_truth, round(n_truth), rtol=0.0, atol=1e-9)):
        raise SystemExit(f"invalid emitted/truth/credit counts in cell row: {row}")
    if tp > n_truth + 1e-8 or fp > emitted + 1e-8:
        raise SystemExit(f"distance-weighted credit exceeds its possible count in cell row: {row}")
    expected_coverage = tp / n_truth if n_truth else 0.0
    if not np.isclose(metric_values[1], expected_coverage, rtol=1e-10, atol=1e-12):
        raise SystemExit(f"coverage does not agree with weighted TP and truth count in cell row: {row}")


def summarize_effect(values: np.ndarray) -> dict:
    arr = np.asarray(values, dtype=float)
    mean = float(arr.mean())
    se = float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else 0.0
    critical = float(t.ppf(0.975, arr.size - 1)) if arr.size > 1 else 0.0
    return {
        "mean": mean,
        "se_across_four_spatial_folds": se,
        "t_95_ci": [mean - critical * se, mean + critical * se],
        "folds_positive": int(np.count_nonzero(arr > 0.0)),
        "by_fold": [float(x) for x in arr],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=None, help="run directory; defaults to evidence/h30_relay_<stage>")
    args = ap.parse_args()
    run = Path(args.dir) if args.dir else None
    if run is None:
        candidates = [ROOT / "evidence" / f"h30_relay_{stage}" for stage in EXPECTED_DRAWS]
        run = next((p for p in candidates if (p / "cells.jsonl").exists()), candidates[0])
    design_path, cells_path = run / "design.json", run / "cells.jsonl"
    if not design_path.exists() or not cells_path.exists():
        raise SystemExit(f"missing H30 design or raw cell file in {run}")
    design = json.loads(design_path.read_text())
    stage = design.get("stage")
    if stage not in EXPECTED_DRAWS:
        raise SystemExit(f"unknown H30 stage {stage!r}")
    validate_frozen_design(design, stage)
    screen = None
    if stage == "confirm":
        screen = verify_passing_screen(ROOT / "evidence" / "h30_relay_screen")

    canonical = design["canonical_matrix"]
    order = design["row_order_zero_based"]
    expected_randomized = [canonical[i] for i in order]
    cfg_by_arm = {row["arm"]: row for row in expected_randomized}
    run_order_by_arm = {row["arm"]: i + 1 for i, row in enumerate(expected_randomized)}
    if set(cfg_by_arm) != EXPECTED_ARMS:
        raise SystemExit(f"design arm set differs from frozen arms: {sorted(cfg_by_arm)}")

    rows = [json.loads(line) for line in cells_path.read_text().splitlines() if line.strip()]
    expected_keys = {(fold, draw, arm) for fold in range(4) for draw in EXPECTED_DRAWS[stage] for arm in EXPECTED_ARMS}
    actual_keys = [(row.get("fold"), row.get("draw"), row.get("arm")) for row in rows]
    if len(actual_keys) != len(set(actual_keys)):
        raise SystemExit("duplicate fold/draw/arm rows in cells.jsonl")
    if set(actual_keys) != expected_keys:
        missing = sorted(expected_keys - set(actual_keys))
        extra = sorted(set(actual_keys) - expected_keys)
        raise SystemExit(f"incomplete/unregistered H30 design; missing={missing}, extra={extra}")

    for row in rows:
        cfg = cfg_by_arm[row["arm"]]
        if (row.get("stage") != stage or row.get("design_seed") != design.get("design_seed")
                or row.get("fold") not in range(4)
                or row.get("fold_name") != EXPECTED_FOLDS[row["fold"]]
                or row.get("run_order") != run_order_by_arm[row["arm"]]
                or row.get("P") != cfg["P"] or row.get("S") != cfg["S"]
                or row.get("include_tip") != cfg["include_tip"]
                or row.get("factorial_arm") != cfg["factorial_arm"]
                or row.get("k_fraction") != design["emission"]["k_fraction"]
                or row.get("min_distance_px") != design["emission"]["min_distance_px"]):
            raise SystemExit(f"cell metadata disagrees with frozen design: {row}")
        validate_cell_metrics(row)

    cell_keys = ((fold, draw) for fold in range(4) for draw in EXPECTED_DRAWS[stage])
    for fold, draw in cell_keys:
        group = [row for row in rows if row.get("fold") == fold and row.get("draw") == draw]
        diag_payloads = {json.dumps(row.get("pair_diagnostics"), sort_keys=True) for row in group}
        if len(diag_payloads) != 1:
            raise SystemExit(f"visible-tip diagnostics differ across arms for fold={fold}, draw={draw}")
        diag = group[0].get("pair_diagnostics")
        if not isinstance(diag, dict) or set(diag) != {
            "visible_tip_count", "nearby_pair_count", "accepted_pair_count", "seed_pixel_count", "nonzero_fraction", "max_value"
        }:
            raise SystemExit(f"malformed visible-tip diagnostics for fold={fold}, draw={draw}")
        counts = np.asarray([diag[key] for key in ("visible_tip_count", "nearby_pair_count", "accepted_pair_count", "seed_pixel_count")], dtype=float)
        bounded = np.asarray([diag[key] for key in ("nonzero_fraction", "max_value")], dtype=float)
        if (not np.isfinite(counts).all() or (counts < 0).any() or not np.equal(counts, np.floor(counts)).all()
                or not np.isfinite(bounded).all() or ((bounded < 0.0) | (bounded > 1.0)).any()):
            raise SystemExit(f"invalid visible-tip diagnostic values for fold={fold}, draw={draw}")

    evidence_hashes = {
        "design.json": sha256_file(design_path),
        "cells.jsonl": sha256_file(cells_path),
    }
    lookup = {(row["fold"], row["draw"], row["arm"]): row for row in rows}
    by_arm: dict[str, dict] = {}
    fold_arm: dict[int, dict[str, dict[str, float]]] = {}
    for arm in sorted(EXPECTED_ARMS):
        arm_rows = [row for row in rows if row["arm"] == arm]
        by_arm[arm] = {
            "n_cells": len(arm_rows),
            "mean_dti": float(np.mean([row["dti"] for row in arm_rows])),
            "sd_dti_cells": float(np.std([row["dti"] for row in arm_rows], ddof=1)),
            "mean_coverage": float(np.mean([row["coverage"] for row in arm_rows])),
            "mean_emitted": float(np.mean([row["emitted"] for row in arm_rows])),
            "mean_hug": float(np.mean([row["hug"] for row in arm_rows])),
            "mean_auc": float(np.mean([row["auc"] for row in arm_rows])),
            "by_fold_dti": [
                float(np.mean([lookup[(fold, draw, arm)]["dti"] for draw in sorted(EXPECTED_DRAWS[stage])]))
                for fold in range(4)
            ],
            "by_fold_hug": [
                float(np.mean([lookup[(fold, draw, arm)]["hug"] for draw in sorted(EXPECTED_DRAWS[stage])]))
                for fold in range(4)
            ],
        }
    for fold in range(4):
        fold_arm[fold] = {}
        for arm in EXPECTED_ARMS:
            fold_arm[fold][arm] = {
                metric: float(np.mean([lookup[(fold, draw, arm)][metric] for draw in sorted(EXPECTED_DRAWS[stage])]))
                for metric in METRICS
            }

    factorial_fold_effects = []
    for fold in range(4):
        response = {
            arm: fold_arm[fold][arm]["dti"]
            for arm in H30_ARMS
        }
        factorial_fold_effects.append(factorial_2x2_effects(response))
    effect_names = tuple(factorial_fold_effects[0])
    effects = {
        name: summarize_effect(np.array([entry[name] for entry in factorial_fold_effects], dtype=float))
        for name in effect_names
    }

    gate = h30_promotion_gate(
        by_arm["T_PLUS_P_S"]["by_fold_dti"],
        {
            H30_CONTROL: by_arm[H30_CONTROL]["by_fold_dti"],
            "T_BASE": by_arm["T_BASE"]["by_fold_dti"],
        },
        by_arm["T_PLUS_P_S"]["by_fold_hug"],
        {
            H30_CONTROL: by_arm[H30_CONTROL]["by_fold_hug"],
            "T_BASE": by_arm["T_BASE"]["by_fold_hug"],
        },
    )
    prior_screen_passed = bool(screen["screen_gate_passed"]) if screen is not None else True
    screen_gate_passed = bool(gate["paired_gate_passed"])
    confirmation_gate_passed = bool(gate["paired_gate_passed"] and prior_screen_passed) if stage == "confirm" else None

    # One pair diagnostic per fold/draw; it is duplicated across model arms by construction.
    pair_diags = {}
    for fold in range(4):
        for draw in sorted(EXPECTED_DRAWS[stage]):
            row = lookup[(fold, draw, "BASE_NO_TIP")]
            pair_diags[f"{row['fold_name']}_draw{draw}"] = row["pair_diagnostics"]
    means = {arm: by_arm[arm]["mean_dti"] for arm in by_arm}
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_directory": str(run),
        "n_rows": len(rows),
        "stage": stage,
        "evidence_sha256": evidence_hashes,
        "design": design,
        "arms": by_arm,
        "factorial_effects_by_fold": factorial_fold_effects,
        "factorial_effects": effects,
        "paired_promotion_gate": gate,
        "screen_gate_passed": screen_gate_passed if stage == "screen" else prior_screen_passed,
        "confirmation_gate_passed": confirmation_gate_passed,
        "proxy_holdout_passed": confirmation_gate_passed if stage == "confirm" else False,
        "slot_eligible": False,
        "slot_decision": (
            "not eligible: screen only; fresh confirmation required"
            if stage == "screen" and screen_gate_passed
            else "screen gate failed; stop; no candidate file"
            if stage == "screen"
            else "proxy gate passed; full-data build and exact-file audit still required; never upload automatically"
            if confirmation_gate_passed
            else "confirmation gate failed; no candidate file or weekly slot"
        ),
        "paired_relay_diagnostics_by_cell": pair_diags,
        "historical_context_not_used_as_cross_draw_gate": {
            "H27_tip_only_screen_mean_dti_draws_4_5": H30_HISTORICAL_TIP_SCREEN_DTI,
            "H27_tip_only_status": "unconfirmed proxy screen; not slot-eligible",
            "H28_frozen_comparator_dti": H30_HISTORICAL_H28_COMPARATOR_DTI,
            "H28_reproduction_verdict": "FAIL (0.1496675088 recomputed vs 0.1520033891 frozen)",
        },
        "mean_dti_by_arm": means,
        "proxy_warning": "Catalogue hide-and-recover proxy only; neither a pass nor the owner-reported 0.2477/0.3195 claims is a competition score verification.",
    }
    (run / "results.json").write_text(json.dumps(out, indent=1) + "\n")

    lines = [
        f"# H30-1 paired relay × terrain factorial — {stage} results",
        "",
        f"Rows: {len(rows)}; draws: {sorted(EXPECTED_DRAWS[stage])}; folds: four spatial blocks.",
        "",
        "| Arm | Mean DTI | NW | NE | SW | SE | Mean hug | Mean coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ("BASE_NO_TIP", "T_BASE", "T_PLUS_P", "T_PLUS_S", "T_PLUS_P_S"):
        item = by_arm[arm]
        folds = " | ".join(f"{value:.6f}" for value in item["by_fold_dti"])
        lines.append(
            f"| {arm} | {item['mean_dti']:.6f} | {folds} | {item['mean_hug']:.4f} | {item['mean_coverage']:.4f} |"
        )
    lines += ["", "## Factorial effects (four fold blocks; 95% t intervals are descriptive)", ""]
    for name, item in effects.items():
        lines.append(
            f"- `{name}`: {item['mean']:+.6f} DTI; SE {item['se_across_four_spatial_folds']:.6f}; "
            f"95% t interval [{item['t_95_ci'][0]:+.6f}, {item['t_95_ci'][1]:+.6f}]; "
            f"positive in {item['folds_positive']}/4 folds."
        )
    lines += [
        "",
        "## Paired gate for the pre-registered P+S candidate",
        "",
        f"- Mean gain vs the best same-run control: {gate['mean_gain_vs_best_paired_control']:+.6f} DTI.",
        f"- Positive folds: {gate['folds_positive']}/4; worst fold: {gate['worst_fold_gain']:+.6f}; "
        f"hug-share change: {gate['mean_hug_share_delta']:+.4f}.",
        f"- **Stage gate: {'PASS' if gate['paired_gate_passed'] else 'FAIL'}**.",
        f"- Slot eligible: **no** — {out['slot_decision']}.",
        "",
        "Historical DTI values are proxy outputs from different hide draws and are not used as absolute promotion thresholds. "
        "The frozen H28 comparator did not reproduce; see the registered paired rule. A fresh confirmation is required after a screen pass.",
        "",
    ]
    (run / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
