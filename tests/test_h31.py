"""Unit and integration tests for H31 anisotropic continuation, cross-scale strike coherence, B=2 guard, and RUN CARD."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from gems25.h31 import (
    H31_FEATURE_NAMES,
    apply_digitization_shadow_guard,
    build_h31_features,
    build_static_lidar_dem_coherence,
)

ROOT = Path(__file__).resolve().parents[1]


def test_build_h31_features_distinguishes_along_strike_from_cross_strike_flank():
    # Horizontal fault segment along row 15, cols 10..20
    foot = np.ones((32, 32), dtype=bool)
    visible = np.zeros((32, 32), dtype=bool)
    visible[15, 10:21] = True
    fi = np.flatnonzero(foot.ravel())

    # Synthetic static cache: LiDAR strike also horizontal (theta=0 => cos(2*theta)=1, sin(2*theta)=0)
    static_names = ["L_strike_c2", "L_strike_s2", "L_coh100"]
    static = np.zeros((3, fi.size), dtype=np.float32)
    static[0] = 1.0  # L_strike_c2
    static[1] = 0.0  # L_strike_s2
    static[2] = 0.8  # L_coh100
    addon = np.zeros((5, fi.size), dtype=np.float32)
    addon[3] = 1.0  # S_dem_c2
    addon[4] = 0.0  # S_dem_s2

    l_c2, l_s2, l_coh, lidar_dem = build_static_lidar_dem_coherence(static, static_names, addon)
    assert np.allclose(lidar_dem, 0.8)

    out = build_h31_features(visible, foot, fi, l_c2, l_s2, l_coh, lidar_dem)
    assert out.shape == (len(H31_FEATURE_NAMES), fi.size)
    assert np.isfinite(out).all()

    # Point along-strike at (row 15, col 24) vs point cross-strike at (row 11, col 15)
    idx_along = 15 * 32 + 24
    idx_flank = 11 * 32 + 15
    assert out[0, idx_along] > 0.8, f"Expected positive a_along along strike, got {out[0, idx_along]}"
    assert out[0, idx_flank] < -0.8, f"Expected negative a_along on cross-strike flank, got {out[0, idx_flank]}"
    assert out[3, idx_along] > 0.3, "Expected positive k_aniso along strike"
    assert out[3, idx_flank] == 0.0, "Expected zero k_aniso on perpendicular flank"
    assert out[5, idx_along] > 0.7, "Expected positive LiDAR-catalogue strike compatibility"


def test_apply_digitization_shadow_guard_removes_2px_flank_and_keeps_far_dots():
    known = np.zeros((20, 20), dtype=bool)
    known[10, 10] = True
    emitted = np.zeros((20, 20), dtype=bool)
    emitted[10, 10] = True  # d = 0.0
    emitted[10, 11] = True  # d = 1.0
    emitted[11, 11] = True  # d = sqrt(2) ~ 1.41
    emitted[10, 12] = True  # d = 2.0
    emitted[11, 12] = True  # d = sqrt(5) ~ 2.24
    emitted[10, 13] = True  # d = 3.0

    guarded = apply_digitization_shadow_guard(emitted, known, buffer_px=2.0)
    assert not guarded[10, 10]
    assert not guarded[10, 11]
    assert not guarded[11, 11]
    assert not guarded[10, 12]
    assert guarded[11, 12]
    assert guarded[10, 13]


def test_h31_experiment_artifacts_and_run_card_integrity():
    exp_dir = ROOT / "evidence" / "h31_experiments"
    res = json.loads((exp_dir / "results.json").read_text())
    canary = json.loads((exp_dir / "leakage_canary.json").read_text())
    uniq = json.loads((exp_dir / "uniqueness_audit.json").read_text())
    card = json.loads((exp_dir / "run_card.json").read_text())

    assert canary["all_features_pass"] is True
    assert canary["max_observed_symmetric_auc"] <= 0.90
    assert res["verdict"] == "promote"
    assert res["promotion_gate"]["all_passed"] is True
    assert res["arms"]["H31_E3_B2"]["cell_mean_holdout_dti"] > 0.152003389
    assert res["paired_contrasts"]["E3_vs_BASE"]["cell_delta_ci95"][0] > 0.0
    assert res["paired_contrasts"]["E3_vs_T_BASE"]["cell_delta_ci95"][0] > 0.0

    assert uniq["rank_correlation_pass"] is True
    assert uniq["max_rank_correlation"] <= 0.90
    assert uniq["dot_overlap_pass"] is True
    assert uniq["max_symmetric_3px_dot_overlap"] <= 0.70

    required_card_keys = {
        "hypothesis",
        "mechanism",
        "mimic",
        "holdout_dti",
        "registry_correlation_overlap",
        "raster_sha256",
        "validator_output",
        "submission_name",
        "note",
        "verdict",
    }
    assert required_card_keys.issubset(card.keys())
    assert card["verdict"] == "promote"
    assert len(card["note"]) <= 140
    assert card["validator_output"]["ok_to_upload"] is True
    assert card["validator_output"]["no_nan_inside_footprint"] is True
    assert card["validator_output"]["values_in_0_1"] is True
    assert card["validator_output"]["crs_matches_template"] is True
    assert card["validator_output"]["shape_matches_template"] is True
    assert card["validator_output"]["transform_matches_template"] is True
