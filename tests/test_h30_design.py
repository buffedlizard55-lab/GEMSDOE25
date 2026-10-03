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
    validate_frozen_design,
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
