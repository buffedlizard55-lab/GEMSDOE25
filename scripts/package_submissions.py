#!/usr/bin/env python3
"""Retired legacy packager for the D2.8 H19-5 research artifact.

The old implementation could recreate and register a TIFF already identified as
byte-identical to a sibling submission. It is intentionally disabled. It must
not be used to package a competition candidate. Future packaging must consume a
new, exact-file receipt whose candidate beats a comparable same-run control,
passes feature-leakage and strict lane gates, and passes the template validator.
"""

from __future__ import annotations

import math


def promotion_receipt_valid(receipt: dict) -> bool:
    """Validate the essential promotion fields for one exact file.

    This validator is retained for unit tests and future packaging code. The
    retired D2.8 CLI does not call it or create artifacts.
    """
    if not isinstance(receipt, dict) or receipt.get("format_ok") is not True or receipt.get("slot_eligible") is not True:
        return False
    gate = receipt.get("promotion_gate")
    checks = receipt.get("checks")
    lane = receipt.get("lane_check")
    canaries = receipt.get("feature_canaries")
    if not all(isinstance(value, dict) for value in (gate, checks, lane, canaries)):
        return False
    # The format checker has informational checks, but these specific predicates
    # are mandatory here, including the whole-array range test for zero padding.
    required_checks = ("template_matches_expected_grid_and_footprint", "single_band", "dtype_float32", "crs_epsg_32611", "shape_matches_template",
                       "geotransform_matches_template", "footprint_all_finite", "footprint_values_in_0_1",
                       "variant_strict_whole_array_no_nan")
    if any(not isinstance(checks.get(name), dict) or checks[name].get("pass_") is not True for name in required_checks):
        return False
    hard_checks = [item for item in checks.values() if isinstance(item, dict) and item.get("hard") is True]
    if not hard_checks or any(item.get("pass_") is not True for item in hard_checks):
        return False
    surface, final = lane.get("surface"), lane.get("final")
    if not isinstance(surface, dict) or not isinstance(final, dict):
        return False
    manifest = surface.get("registry_manifest_sha256")

    def valid_hash(value):
        return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    if not (surface.get("surface_clear") is True and surface.get("registry_complete") is True
            and surface.get("flagged") == [] and valid_hash(manifest)
            and valid_hash(surface.get("scores_sha256")) and valid_hash(surface.get("template_sha256"))
            and final.get("template_sha256") == surface.get("template_sha256")
            and surface.get("rank_footprint_pixels") == final.get("rank_footprint_pixels") == 5_167_373
            and final.get("surface_sha256") == surface.get("scores_sha256")
            and final.get("lane_clear") is True and final.get("registry_complete") is True
            and final.get("flagged_literal") == [] and final.get("registry_manifest_sha256") == manifest
            and valid_hash(receipt.get("sha256")) and final.get("sha256") == receipt.get("sha256")):
        return False
    # Every declared input must have a standalone AUC/missingness canary in
    # each evaluation cell. An empty/incomplete canary set is not a pass.
    features, cells = canaries.get("features"), canaries.get("cells")
    if (not isinstance(features, list) or not features
            or any(not isinstance(name, str) or not name for name in features)
            or len(features) != len(set(features)) or not isinstance(cells, list) or not cells):
        return False
    seen_cells = set()
    for cell in cells:
        if not isinstance(cell, dict) or not isinstance(cell.get("fold"), int) or isinstance(cell["fold"], bool):
            return False
        draw, values = cell.get("draw"), cell.get("features")
        if not isinstance(draw, int) or isinstance(draw, bool) or not isinstance(values, dict) or set(values) != set(features):
            return False
        key = (cell["fold"], draw)
        if key in seen_cells:
            return False
        seen_cells.add(key)
        for item in values.values():
            if not isinstance(item, dict) or item.get("passed") is not True:
                return False
            auc = item.get("canary_auc")
            if isinstance(auc, bool) or not isinstance(auc, (int, float)) or not math.isfinite(auc) or not 0.5 <= auc <= 0.90:
                return False
    if {f for f, _ in seen_cells} != {0, 1, 2, 3} or canaries.get("run_id") != gate.get("run_id"):
        return False
    draws = {d for _, d in seen_cells}
    if seen_cells != {(f, d) for f in range(4) for d in draws}:
        return False
    gate_cells = gate.get("cells")
    if (not isinstance(gate_cells, list)
            or any(not isinstance(x, list) or len(x) != 2 or any(isinstance(v, bool) or not isinstance(v, int) for v in x)
                   for x in gate_cells)
            or {tuple(x) for x in gate_cells} != seen_cells or len(gate_cells) != len(seen_cells)):
        return False
    try:
        control_raw = gate["same_run_best_dti"]
        candidate_raw = gate["candidate_mean_dti"]
        gain_raw = gate["paired_mean_gain"]
        folds_positive = gate["folds_positive"]
        worst_fold_raw = gate["worst_fold_gain"]
        ci = gate["paired_ci95"]
        withheld = gate["withheld_positives"]
        evaluator_sha = gate["evaluator_sha256"]
        if (gate.get("metric_label") != "HOLDOUT-DTI" or not isinstance(gate.get("evaluator"), str)
                or not gate["evaluator"].strip() or not valid_hash(evaluator_sha)
                or not isinstance(withheld, int) or isinstance(withheld, bool) or withheld <= 0
                or not isinstance(ci, list) or len(ci) != 2
                or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in ci)
                or not 0 < ci[0] <= ci[1] <= 1):
            return False
        if any(isinstance(value, bool) for value in (control_raw, candidate_raw, gain_raw, folds_positive, worst_fold_raw)):
            return False
        if not isinstance(folds_positive, int):
            return False
        control = float(control_raw)
        candidate = float(candidate_raw)
        gain = float(gain_raw)
        worst_fold = float(worst_fold_raw)
        run_id = gate.get("run_id")
        control_id = gate.get("same_run_best_control_id")
        candidate_sha = gate.get("candidate_sha256")
        file_sha = receipt.get("sha256")
        valid_sha = isinstance(candidate_sha, str) and len(candidate_sha) == 64 and all(c in "0123456789abcdef" for c in candidate_sha)
        numeric = (control, candidate, gain, worst_fold)
        return bool(
            gate.get("stage") == "confirmation"
            and gate.get("passed") is True
            and gate.get("paired_gate_passed") is True
            and isinstance(run_id, str) and bool(run_id.strip())
            and isinstance(control_id, str) and bool(control_id.strip())
            and all(math.isfinite(value) for value in numeric)
            and 0.0 <= control <= 1.0 and 0.0 <= candidate <= 1.0
            and candidate > control
            and math.isclose(gain, candidate - control, rel_tol=0.0, abs_tol=1e-6)
            and gain > 0.001
            and 3 <= folds_positive <= 4
            and worst_fold >= -0.010
            and valid_sha
            and candidate_sha == file_sha
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def main() -> None:
    raise SystemExit(
        "disabled: this legacy script rebuilds the known duplicate D2.8 artifact "
        "(content id e56ea318af89; SHA-256 91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8). "
        "It cannot package a unique candidate. Do not use it for a submission."
    )


if __name__ == "__main__":
    main()
