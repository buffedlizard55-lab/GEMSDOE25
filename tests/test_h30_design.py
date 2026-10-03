import hashlib
import json
from pathlib import Path

import numpy as np

from gems25.h30 import H30_BASE_EXTRAS, factorial_2x2_effects, h30_promotion_gate
from scripts.analyze_h30_relay_factorial import (
    EXPECTED_FOLDS,
    EXPECTED_HGB_PARAMETERS,
    FROZEN_CANONICAL_MATRIX,
    FROZEN_DESIGN_SEED,
    validate_cell_metrics,
    validate_frozen_design,
    verify_passing_screen,
)

ROOT = Path(__file__).resolve().parents[1]


def frozen_design_for_test():
    prereg = ROOT / "knowledge" / "11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md"
    cache_record = json.loads((ROOT / "evidence" / "work_cache_hashes.json").read_text())
    cache_names = (
        "static_ABCD.npy",
        "static_ABCD.npy.names.json",
        "addons.npy",
        "addons.npy.names.json",
        "bands/_footprint.npy",
        "bands/_labels.npy",
    )
    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    order = np.random.default_rng(FROZEN_DESIGN_SEED).permutation(5).tolist()
    return {
        "preregistration": str(prereg.relative_to(ROOT)),
        "preregistration_sha256": hashlib.sha256(prereg.read_bytes()).hexdigest(),
        "stage": "screen",
        "draws": [6, 7],
        "spatial_folds": EXPECTED_FOLDS,
        "design_seed": FROZEN_DESIGN_SEED,
        "canonical_matrix": FROZEN_CANONICAL_MATRIX,
        "row_order_zero_based": order,
        "randomized_matrix": [FROZEN_CANONICAL_MATRIX[i] for i in order],
        "fixed_model_families": "BDE",
        "fixed_addons": H30_BASE_EXTRAS,
        "fixed_tip_control": "H27_tip",
        "factorial_rows": ["T_BASE", "T_PLUS_P", "T_PLUS_S", "T_PLUS_P_S"],
        "control_row": "BASE_NO_TIP",
        "paired_bridge_definition": {
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
        },
        "hgb_parameters": EXPECTED_HGB_PARAMETERS,
        "emission": {
            "method": "Hessian ridge NMS → top-K → score-ordered Poisson-disk",
            "nms_sigma_px": 1.0,
            "k_fraction": 0.035,
            "min_distance_px": 2.4,
            "drop_visible_catalogue": True,
        },
        "terrain_feature": (
            "clip(scale(L_step_max) * scale(L_cross_max) * scale(L_coh100), 0, 1); "
            "Context.scale 1st/99th percentiles from default_rng(1) sample of 200000 footprint pixels"
        ),
        "terrain_scaling_parameters_1st_99th_percentile": {
            name: [0.0, 1.0] for name in ("L_step_max", "L_cross_max", "L_coh100")
        },
        "code_revision": "0" * 40,
        "clean_worktree_before_fit": True,
        "data_manifest_sha256_and_bytes": {
            row["id"]: {"sha256": row["sha256"], "bytes": row["bytes"]}
            for row in manifest["files"]
        },
        "derived_cache_sha256_verified": {name: cache_record[name] for name in cache_names},
    }


def write_screen_fixture(directory: Path, candidate_dti: float = 0.13) -> Path:
    directory.mkdir()
    design = frozen_design_for_test()
    design_path = directory / "design.json"
    cells_path = directory / "cells.jsonl"
    design_path.write_text(json.dumps(design, indent=1) + "\n")
    means = {
        "BASE_NO_TIP": 0.10,
        "T_BASE": 0.11,
        "T_PLUS_P": 0.12,
        "T_PLUS_S": 0.11,
        "T_PLUS_P_S": candidate_dti,
    }
    hugs = {
        "BASE_NO_TIP": 0.10,
        "T_BASE": 0.15,
        "T_PLUS_P": 0.16,
        "T_PLUS_S": 0.16,
        "T_PLUS_P_S": 0.20,
    }
    rows = []
    for fold, fold_name in enumerate(EXPECTED_FOLDS):
        for draw in (6, 7):
            for run_order, cfg in enumerate(design["randomized_matrix"], start=1):
                rows.append({
                    "stage": "screen",
                    "fold": fold,
                    "fold_name": fold_name,
                    "draw": draw,
                    "run_order": run_order,
                    "arm": cfg["arm"],
                    "P": cfg["P"],
                    "S": cfg["S"],
                    "include_tip": cfg["include_tip"],
                    "factorial_arm": cfg["factorial_arm"],
                    "design_seed": FROZEN_DESIGN_SEED,
                    "k_fraction": 0.035,
                    "min_distance_px": 2.4,
                    "dti": means[cfg["arm"]],
                    "coverage": 0.5,
                    "tp": 1,
                    "fp": 1,
                    "n_truth": 2,
                    "emitted": 2,
                    "hug": hugs[cfg["arm"]],
                    "auc": 0.5,
                })
    cells_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    gate = h30_promotion_gate(
        [candidate_dti] * 4,
        {"BASE_NO_TIP": [means["BASE_NO_TIP"]] * 4, "T_BASE": [means["T_BASE"]] * 4},
        [hugs["T_PLUS_P_S"]] * 4,
        {"BASE_NO_TIP": [hugs["BASE_NO_TIP"]] * 4, "T_BASE": [hugs["T_BASE"]] * 4},
    )
    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    results = {
        "stage": "screen",
        "n_rows": len(rows),
        "design": design,
        "evidence_sha256": {"design.json": digest(design_path), "cells.jsonl": digest(cells_path)},
        "paired_promotion_gate": gate,
        "screen_gate_passed": gate["paired_gate_passed"],
        "slot_eligible": False,
    }
    (directory / "results.json").write_text(json.dumps(results, indent=1) + "\n")
    return directory


def test_h30_2x2_effects_return_coded_main_effects_and_difference_in_differences():
    effects = factorial_2x2_effects(
        {"T_BASE": 0.10, "T_PLUS_P": 0.12, "T_PLUS_S": 0.11, "T_PLUS_P_S": 0.16}
    )
    assert np.isclose(effects["P"], 0.035)
    assert np.isclose(effects["S"], 0.025)
    assert np.isclose(effects["P_x_S"], 0.015)
    assert np.isclose(effects["P_x_S_difference_in_differences"], 0.03)


def test_h30_gate_uses_best_paired_control_per_fold_and_all_frozen_conditions():
    gate = h30_promotion_gate(
        candidate_by_fold=[0.16, 0.15, 0.15, 0.14],
        controls_by_fold={
            "BASE_NO_TIP": [0.14, 0.14, 0.14, 0.14],
            "T_BASE": [0.15, 0.145, 0.145, 0.13],
        },
        candidate_hug_by_fold=[0.10, 0.10, 0.10, 0.10],
        controls_hug_by_fold={
            "BASE_NO_TIP": [0.08, 0.08, 0.08, 0.08],
            "T_BASE": [0.09, 0.09, 0.09, 0.09],
        },
    )
    assert gate["reference_arm_by_fold"] == ["T_BASE", "T_BASE", "T_BASE", "BASE_NO_TIP"]
    assert np.allclose(gate["per_fold_gain"], [0.01, 0.005, 0.005, 0.0])
    assert gate["paired_gate_passed"]


def test_h30_gate_fails_if_candidate_loses_too_many_folds_or_hug_limit():
    gate = h30_promotion_gate(
        candidate_by_fold=[0.16, 0.16, 0.12, 0.12],
        controls_by_fold={"BASE_NO_TIP": [0.14] * 4, "T_BASE": [0.15] * 4},
        candidate_hug_by_fold=[0.25] * 4,
        controls_hug_by_fold={"BASE_NO_TIP": [0.08] * 4, "T_BASE": [0.09] * 4},
    )
    assert not gate["paired_gate_passed"]
    assert gate["folds_positive"] == 2
    assert gate["mean_hug_share_delta"] > 0.10


def test_h30_gate_rejects_out_of_range_metrics_and_invalid_thresholds():
    args = (
        [0.16] * 4,
        {"BASE_NO_TIP": [0.14] * 4, "T_BASE": [0.15] * 4},
        [0.10] * 4,
        {"BASE_NO_TIP": [0.08] * 4, "T_BASE": [0.09] * 4},
    )
    with np.testing.assert_raises(ValueError):
        h30_promotion_gate([1.1] * 4, *args[1:])
    with np.testing.assert_raises(ValueError):
        h30_promotion_gate(args[0], *args[1:], min_gain=np.nan)


def test_h30_design_helpers_reject_incomplete_or_nonfinite_responses():
    with np.testing.assert_raises(ValueError):
        factorial_2x2_effects({"T_BASE": 0.1})
    with np.testing.assert_raises(ValueError):
        factorial_2x2_effects({"T_BASE": 0.1, "T_PLUS_P": 0.2, "T_PLUS_S": 0.1, "T_PLUS_P_S": np.nan})
    with np.testing.assert_raises(ValueError):
        h30_promotion_gate([0.1] * 3, {}, [0.0] * 4, {})


def test_analyzer_accepts_fractional_dti_credits_but_requires_integer_truth_count():
    row = {
        "dti": 0.10,
        "coverage": 0.25,
        "emitted": 5,
        "hug": 0.20,
        "auc": 0.60,
        "tp": 0.50,
        "fp": 2.25,
        "n_truth": 2,
    }
    validate_cell_metrics(row)

    bad_truth = dict(row, n_truth=2.5)
    with np.testing.assert_raises(SystemExit):
        validate_cell_metrics(bad_truth)

    bad_credit = dict(row, tp=2.5)
    with np.testing.assert_raises(SystemExit):
        validate_cell_metrics(bad_credit)


def test_frozen_h30_design_validator_accepts_exact_registered_plan():
    validate_frozen_design(frozen_design_for_test(), "screen")


def test_frozen_h30_design_validator_rejects_changed_draws_or_matrix():
    design = frozen_design_for_test()
    design["draws"] = [5, 6]
    with np.testing.assert_raises(SystemExit):
        validate_frozen_design(design, "screen")

    design = frozen_design_for_test()
    design["canonical_matrix"] = list(reversed(design["canonical_matrix"]))
    with np.testing.assert_raises(SystemExit):
        validate_frozen_design(design, "screen")


def test_confirmation_guard_recomputes_a_hash_bound_passing_screen(tmp_path):
    screen_dir = write_screen_fixture(tmp_path / "passing")
    verified = verify_passing_screen(screen_dir)
    assert verified["screen_gate_passed"] is True

    failed_dir = write_screen_fixture(tmp_path / "failed", candidate_dti=0.11)
    with np.testing.assert_raises(SystemExit):
        verify_passing_screen(failed_dir)


def test_confirmation_guard_rejects_summary_tampering_and_changed_raw_cells(tmp_path):
    screen_dir = write_screen_fixture(tmp_path / "tampered-summary")
    results_path = screen_dir / "results.json"
    results = json.loads(results_path.read_text())
    results["paired_promotion_gate"]["mean_gain_vs_best_paired_control"] = 99.0
    results_path.write_text(json.dumps(results, indent=1) + "\n")
    with np.testing.assert_raises(SystemExit):
        verify_passing_screen(screen_dir)

    changed_dir = write_screen_fixture(tmp_path / "changed-cells")
    with (changed_dir / "cells.jsonl").open("a") as sink:
        sink.write("\n")
    with np.testing.assert_raises(SystemExit):
        verify_passing_screen(changed_dir)
