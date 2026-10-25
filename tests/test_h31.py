import numpy as np
import pytest

from gems25.h31 import (
    H31_SUB_INPUTS,
    H31_SURF_INPUTS,
    build_offflank_tip_halo,
    build_subscarp_concordance,
    candidates_flank_shielded,
    check_duplicate_lane_against_registry,
    factorial_2x2_effects,
    h31_promotion_gate,
    pooled_dti_summary,
)


def test_build_subscarp_concordance_geometric_mean_and_nonfinite_handling():
    names = list(H31_SURF_INPUTS) + list(H31_SUB_INPUTS)
    mat = np.zeros((len(names), 4), np.float32)
    mat[:, 1] = 0.5
    mat[:, 2] = 1.0
    mat[:3, 3] = 1.0
    mat[3:, 3] = np.nan
    scales = {n: (0.0, 1.0) for n in names}

    out, diag = build_subscarp_concordance(mat, names, scales)

    assert np.allclose(out, [0.0, 0.5, 1.0, 0.0], atol=1e-6)
    assert np.isfinite(out).all() and out.min() >= 0.0 and out.max() <= 1.0
    assert diag["n_footprint_pixels"] == 4
    assert diag["source_nonfinite_counts"]["A_grav_hg_ridge"] == 1


def test_build_offflank_tip_halo_suppresses_non_tip_flank_and_preserves_tips():
    h = w = 30
    foot = np.ones((h, w), bool)
    vis = np.zeros((h, w), bool)
    vis[15, 5:18] = True
    fi = np.arange(h * w, dtype=np.int64)
    tip = np.zeros(fi.size, np.float32)
    tip[15 * w + 19] = 0.8  # 1-px beyond right tip

    out, diag = build_offflank_tip_halo(vis, tip, foot, fi)
    grid = out.reshape(h, w)

    assert grid[14, 10] == 0.0  # 1-px lateral flank with no tip -> suppressed to 0
    assert grid[13, 10] == 0.0  # 2-px lateral flank with no tip -> suppressed to 0
    assert grid[11, 10] > 0.5   # 4-px piedmont corridor -> active
    assert np.isclose(grid[15, 19], 0.8)  # 1-px tip continuation -> preserved
    assert np.isfinite(out).all() and out.min() >= 0.0 and out.max() <= 1.0
    assert diag["flank_suppressed_fraction"] > 0.0


def test_candidates_flank_shielded_removes_lateral_flank_and_keeps_tip_cones():
    h = w = 40
    dom = np.ones((h, w), bool)
    known = np.zeros((h, w), bool)
    known[20, 8:28] = True
    score = np.zeros((h, w), np.float32)
    # Lateral side-lobe ridge 2 px away from known trace (row 18)
    score[18, 10:26] = 0.9
    score[17, 10:26] = 0.4
    score[19, 10:26] = 0.4
    # Off-flank ridge 8 px away (row 10)
    score[10, 10:26] = 0.6
    score[9, 10:26] = 0.2
    score[11, 10:26] = 0.2
    tip = np.zeros((h, w), np.float32)
    tip[18, 25] = 0.5  # mark one pixel in tip cone

    _, top, diag = candidates_flank_shielded(
        score, dom, known, tip, k=20, nms_sigma=0.5, flank_radius_px=2.5, tip_preserve_threshold=0.05
    )

    assert not top[18, 15]  # non-tip lateral flank removed
    assert top[18, 25]      # tip-cone pixel preserved
    assert top[10, 15]      # off-flank ridge kept
    assert diag["flank_removed_ridges"] > 0
    assert diag["tip_preserved_in_flank"] >= 1


def test_factorial_2x2_effects_and_pooled_dti_and_gate():
    eff = factorial_2x2_effects({"M0_C0": 0.140, "M1_C0": 0.142, "M0_C1": 0.144, "M1_C1": 0.148})
    assert np.isclose(eff["M"], 0.003)
    assert np.isclose(eff["C"], 0.005)
    assert np.isclose(eff["M_x_C"], 0.001)

    rows = [
        {"fold": 0, "tp": 400.0, "fp": 7000.0, "n_truth": 2000},
        {"fold": 1, "tp": 420.0, "fp": 7100.0, "n_truth": 2100},
        {"fold": 2, "tp": 450.0, "fp": 7200.0, "n_truth": 2200},
        {"fold": 3, "tp": 430.0, "fp": 7050.0, "n_truth": 2150},
    ]
    ps = pooled_dti_summary(rows)
    assert ps["withheld_positives"] == 8450
    assert 0.10 < ps["pooled_dti"] < 0.25
    assert "HOLDOUT-DTI" in ps["formatted_label"]

    gate = h31_promotion_gate(
        [0.151, 0.152, 0.153, 0.154],
        {"CTRL_NO_TIP": [0.148, 0.149, 0.150, 0.151], "M0_C0": [0.149, 0.150, 0.151, 0.152]},
        [0.05, 0.05, 0.05, 0.05],
        {"CTRL_NO_TIP": [0.09, 0.09, 0.09, 0.09], "M0_C0": [0.08, 0.08, 0.08, 0.08]},
    )
    assert gate["paired_gate_passed"] is True
    assert gate["folds_positive"] == 4


def test_duplicate_lane_check_catches_high_overlap_and_passes_independent():
    foot = np.ones((30, 30), bool)
    em = np.zeros((30, 30), bool)
    em[5, 5:15] = True
    surf = np.linspace(0.0, 1.0, 900, dtype=np.float32)

    reg_dup = em.astype(np.float32)
    res_dup = check_duplicate_lane_against_registry(surf, em, foot, {"dup": reg_dup})
    assert res_dup["passed"] is False

    reg_ind = np.zeros((30, 30), np.float32)
    reg_ind[25, 5:15] = 1.0
    res_ind = check_duplicate_lane_against_registry(surf, em, foot, {"ind": reg_ind})
    assert res_ind["passed"] is True
    with pytest.raises(ValueError):
        check_duplicate_lane_against_registry(surf, np.zeros_like(em), foot, {"ind": reg_ind})
