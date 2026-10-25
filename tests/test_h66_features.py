"""Synthetic unit tests for H66-1 (MGD-F) and H66-2 (SGMC-REACT) builders + lane_check_extended fix."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.h66_mgd_sgmc import (  # noqa: E402
    GDR_ALLOWED_COLS,
    H66_MGD_NAMES,
    H66_SGMC_NAMES,
    compute_efimov_f_ridge,
    compute_mgd_wellspring_grids,
    compute_sgmc_reactivation_grids,
)


def test_gdr_allowed_cols_excludes_label_distance():
    assert "dist_known_fault_px" not in GDR_ALLOWED_COLS
    foot = np.ones((24, 24), dtype=bool)
    df_bad = pd.DataFrame({
        "layer": ["spring_chemistry_20220808"],
        "thermalclass": ["Warm"],
        "row": [12],
        "col": [12],
        "temp_c": [25.0],
        "geothermchalc_c": [110.0],
        "geothermcat_c": [150.0],
        "dist_known_fault_px": [1.0],
    })
    with pytest.raises(ValueError, match="dist_known_fault_px"):
        compute_mgd_wellspring_grids(df_bad, foot)


def test_mgd_wellspring_disequilibrium_peaks_at_masked_upflow_not_hot_equilibrium():
    foot = np.ones((40, 40), dtype=bool)
    foot[0, :] = False  # verify outside-footprint masking
    df = pd.DataFrame({
        "layer": ["spring_chemistry_20220808", "well_chemistry_20220808"],
        "thermalclass": ["Warm", "Cold"],
        "row": [20, 8],
        "col": [20, 8],
        "temp_c": [30.0, 22.0],
        "geothermchalc_c": [125.0, 20.0],   # +95 C excess at (20,20), 0 excess at (8,8)
        "geothermcat_c": [165.0, 21.0],     # +135 C excess at (20,20), 0 excess at (8,8)
    })
    cat_g, ch_g, up_g = compute_mgd_wellspring_grids(df, foot, outflow_sigma_px=4.0, upflow_decay_px=6.0)
    for g in (cat_g, ch_g, up_g):
        assert g.shape == foot.shape and g.dtype == np.float32
        assert np.isfinite(g).all()
        assert (g >= 0.0).all() and (g <= 1.0).all()
        assert (g[~foot] == 0.0).all()
    assert cat_g[20, 20] > 0.9 and cat_g[8, 8] < 0.05
    assert ch_g[20, 20] > 0.9 and ch_g[8, 8] < 0.05
    assert up_g[20, 20] == pytest.approx(1.0) and up_g[8, 8] < 0.15


def test_efimov_f_ridge_localizes_linear_potassic_alteration_zone():
    H, W = 48, 48
    foot = np.ones((H, W), dtype=bool)
    yy, xx = np.mgrid[0:H, 0:W]
    band = np.exp(-((yy - 24) ** 2) / (2.0 * 2.0 ** 2))
    k_u8 = np.clip(80 + 160 * band, 1, 255).astype(np.uint8)
    uth_u8 = np.clip(70 + 160 * band, 1, 255).astype(np.uint8)
    tc_u8 = np.clip(90 + 120 * (yy > 24), 1, 255).astype(np.uint8)
    ef = compute_efimov_f_ridge(k_u8, tc_u8, uth_u8, foot)
    assert ef.shape == (H, W) and ef.dtype == np.float32
    assert np.isfinite(ef).all() and (ef >= 0.0).all() and (ef <= 1.0).all()
    assert float(ef[24, 24]) > float(ef[6, 24]) + 0.5
    assert len(H66_MGD_NAMES) == 4


def test_sgmc_reactivation_suppresses_orthogonal_or_unstrained_traces():
    H, W = 48, 48
    foot = np.ones((H, W), dtype=bool)
    fi = np.flatnonzero(foot.ravel())
    sgmc = np.zeros((H, W), dtype=np.uint8)
    sgmc[14, 8:40] = 1  # horizontal bedrock trace (c2 = +1, s2 = 0)
    sgmc[34, 8:40] = 1  # second horizontal bedrock trace

    # LiDAR scarp aligns horizontally on top half (c2=+1), orthogonal vertically on bottom half (c2=-1)
    yy, xx = np.mgrid[0:H, 0:W]
    l_c2 = np.where(yy < 24, 1.0, -1.0).ravel()[fi].astype(np.float32)
    l_s2 = np.zeros(fi.size, dtype=np.float32)
    l_coh = np.full(fi.size, 0.9, dtype=np.float32)
    l_step = np.where((np.abs(yy - 14) <= 2) | (np.abs(yy - 34) <= 2), 10.0, 0.5).ravel()[fi].astype(np.float32)

    # High strain + gravity step on top trace, near-zero strain on bottom trace
    strain = np.where(yy < 24, 100.0, 0.0).astype(np.float32)
    grav = np.where(yy < 14, -20.0, 20.0).astype(np.float32)

    vecs = compute_sgmc_reactivation_grids(
        sgmc_u8=sgmc,
        foot=foot,
        l_c2_foot=l_c2,
        l_s2_foot=l_s2,
        l_coh_foot=l_coh,
        l_step_foot=l_step,
        geod_2ndinv_grid=strain,
        iso_grav_grid=grav,
        footprint_idx=fi,
    )
    assert vecs.shape == (len(H66_SGMC_NAMES), fi.size)
    assert np.isfinite(vecs).all() and (vecs >= 0.0).all() and (vecs <= 1.0).all()
    idx_active = 14 * W + 24
    idx_inactive = 34 * W + 24
    # Raw proximity is 1.0 on both traces, but reactivation columns fire ONLY on the active trace!
    assert vecs[0, idx_active] == pytest.approx(1.0)
    assert vecs[0, idx_inactive] == pytest.approx(1.0)
    assert vecs[1, idx_active] > 0.5 and vecs[1, idx_inactive] == pytest.approx(0.0, abs=1e-5)
    assert vecs[2, idx_active] > 0.3 and vecs[2, idx_inactive] == pytest.approx(0.0, abs=1e-5)


def test_lane_check_extended_excludes_only_candidate_own_stem():
    import lane_check_extended as lce

    mscr_z = ROOT / "docs/downloads/gems25-mscr-multiscale-crest-sapd2-4-k3p5-20261025-dd2bb4b09cd2-zeros.tif"
    xg1_z = ROOT / "docs/downloads/gems25-xg1-crossgrad-sapd2-4-k3p5-20261025-52e65fb521f9-zeros.tif"
    _, own_for_mscr = lce.groups(mscr_z)
    _, own_for_xg1 = lce.groups(xg1_z)
    assert not any("mscr-multiscale-crest" in p.name for _, p in own_for_mscr)
    assert any("mscr-multiscale-crest" in p.name for _, p in own_for_xg1)
    assert not any("xg1-crossgrad" in p.name for _, p in own_for_xg1)
