"""Unit and zero-leakage tests for H74-1 (RMPS-BFP) and H74-BW (25-km block-withheld selector)."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

from gems25.h74_rmps import (
    H74_RMPS_NAMES,
    biharmonic_magnitude,
    compute_h74_rmps_grids,
    draw_block25km,
    harmonic_vertical_derivative_fft,
)
from gems25.holdout import COLLAR_PX, Holdout


def test_harmonic_vertical_derivative_fft_matches_exact_plane_wave() -> None:
    ny, nx = 64, 64
    cell_m = 100.0
    yy, xx = np.meshgrid(np.arange(ny) * cell_m, np.arange(nx) * cell_m, indexing="ij")
    ky = 2.0 / (ny * cell_m)  # 2 cycles across grid
    kx = 3.0 / (nx * cell_m)  # 3 cycles across grid
    k_mag = np.hypot(kx, ky)
    field = np.cos(2.0 * np.pi * (kx * xx + ky * yy))
    expected_vdown = 2.0 * np.pi * k_mag * field
    got = harmonic_vertical_derivative_fft(field, cell_m=cell_m, pad=0)
    np.testing.assert_allclose(got, expected_vdown, rtol=1e-4, atol=1e-5)


def test_biharmonic_vanishes_on_quadratic_basin_and_spikes_on_broken_hinge() -> None:
    yy, xx = np.mgrid[-40:41, -40:41].astype(np.float64)
    # Smooth quadratic sag: nabla^2 w = const -> nabla^4 w == 0 everywhere in interior
    quad_sag = 0.02 * xx * xx - 0.015 * xx * yy + 0.03 * yy * yy + 0.5 * xx - 0.2 * yy + 10.0
    b_quad = biharmonic_magnitude(quad_sag, sigma_px=2.0)
    assert float(b_quad[15:-15, 15:-15].max()) < 1e-6

    # Broken-plate fault hinge at x = 0: w = max(x, 0) * exp(-x / 12)
    hinge = np.where(xx > 0.0, xx * np.exp(-xx / 12.0), 0.0)
    b_hinge = biharmonic_magnitude(hinge, sigma_px=2.0)
    center_band = float(b_hinge[20:-20, 38:43].max())
    far_flank = float(b_hinge[20:-20, 10:20].max())
    assert center_band > 5.0 * far_flank


def test_compute_h74_rmps_grids_bounds_nan_safety_and_remanence_identity() -> None:
    h, w = 80, 90
    foot = np.zeros((h, w), dtype=bool)
    foot[6:-6, 6:-6] = True
    yy, xx = np.mgrid[:h, :w].astype(np.float32)

    # Identical TMI and RTP -> remanent skewness must identically vanish
    step = np.tanh((xx - 45.0) / 2.5).astype(np.float32) * 120.0
    base_equal = {
        "tmi": np.where(foot, step, np.nan),
        "rtp": np.where(foot, step, np.nan),
        "tmi_vg": np.where(foot, 0.25 * np.exp(-((xx - 45.0) / 3.0) ** 2), np.nan),
        "depth_to_base_surf": np.where(foot, 300.0 + 400.0 * (xx > 45.0).astype(np.float32), np.nan),
        "iso_grav_anom": np.where(foot, -15.0 * (xx > 45.0).astype(np.float32), np.nan),
        "iso_grav_anom_vg": np.where(foot, -2.0 * np.exp(-((xx - 45.0) / 2.0) ** 2), np.nan),
        "geod_dilaterate": np.where(foot, 8.0 + 4.0 * np.sin(yy / 10.0), np.nan),
        "geod_shearrate": np.where(foot, 10.0 + 2.0 * np.cos(xx / 12.0), np.nan),
        "cond_surf": np.where(foot, 2.0 + 2.5 * np.exp(-((xx - 45.0) / 2.0) ** 2), np.nan),
        "ieq_n100a15": np.where(foot, 400.0 + 900.0 * np.exp(-((xx - 45.0) / 4.0) ** 2), np.nan),
    }
    g_eq = compute_h74_rmps_grids(base_equal, foot)
    assert list(g_eq.keys()) == H74_RMPS_NAMES
    assert float(g_eq["H74_remanent_skew_crest"].max()) == 0.0
    for name in H74_RMPS_NAMES:
        arr = g_eq[name]
        assert arr.dtype == np.float32 and arr.shape == (h, w)
        assert np.isfinite(arr).all()
        assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
        assert float(np.abs(arr[~foot]).max()) == 0.0

    # Reversed/dipolar TMI vs symmetric step RTP -> remanent skewness fires on the contact
    base_skew = dict(base_equal)
    base_skew["tmi"] = np.where(
        foot,
        120.0 * (xx - 45.0) / (4.0 + (xx - 45.0) ** 2),
        np.nan,
    ).astype(np.float32)
    g_sk = compute_h74_rmps_grids(base_skew, foot)
    assert float(g_sk["H74_remanent_skew_crest"][foot].max()) > 0.5


def test_draw_block25km_zero_leakage_and_increases_withheld_dvis() -> None:
    h, w = 240, 240
    foot = np.ones((h, w), dtype=bool)
    labels = np.zeros((h, w), dtype=bool)
    # Create multi-strand clustered fault zones in 40x40 blocks across all 4 quadrants
    rng = np.random.default_rng(42)
    for by in range(15, h - 20, 45):
        for bx in range(15, w - 20, 45):
            # 3 parallel sister strands 4 px apart inside each fault zone
            for offset in (-4, 0, 4):
                r0 = by + int(rng.integers(-3, 4))
                c0 = bx + offset
                labels[r0 : r0 + 14, c0] = True

    holdout = Holdout(foot, labels, hide_frac=0.20)
    std_medians, bw_medians = [], []
    for fold in range(4):
        d_std = holdout.draw(fold, seed=110)
        d_bw = draw_block25km(holdout, fold=fold, seed=110, block_px=45)

        # Zero-leakage invariants on H74-BW
        assert not (d_bw.visible & d_bw.hidden_test).any()
        assert not (d_bw.visible & d_bw.hidden_train).any()
        assert not (d_bw.train_region & d_bw.quadrant).any()
        assert not (d_bw.hidden_train & d_bw.quadrant).any()

        # Every 8-connected component must be either 100% visible or 100% hidden (zero partial stubs!)
        for cid in range(1, holdout.n_comp + 1):
            cmask = holdout.comp == cid
            vis_n = int((d_bw.visible & cmask).sum())
            assert vis_n in (0, int(cmask.sum())), f"component {cid} split between visible and hidden"

        # Training region must remain strictly > COLLAR_PX away from hidden_test
        if d_bw.hidden_test.any() and d_bw.train_region.any():
            min_dist_to_test_truth = float(distance_transform_edt(~d_bw.hidden_test)[d_bw.train_region].min())
            assert min_dist_to_test_truth > float(COLLAR_PX)

        dvis_std = distance_transform_edt(~d_std.visible)[d_std.hidden_test]
        dvis_bw = distance_transform_edt(~d_bw.visible)[d_bw.hidden_test]
        std_medians.append(float(np.median(dvis_std)))
        bw_medians.append(float(np.median(dvis_bw)))

    # Standard component split leaves sister strands at ~4 px; block withholding removes entire sister clusters
    assert float(np.mean(bw_medians)) > 3.0 * float(np.mean(std_medians))
