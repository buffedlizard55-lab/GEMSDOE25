from __future__ import annotations

import numpy as np
import pytest

from gems25.h72 import (
    CENSOR_MIN_DIST_PX,
    H72_NAMES,
    censor_catalogue_proximity,
    compute_h72_grids,
    contour_doubled_angle,
    emit_debiased_b2_greedy,
    hessian_ridge_doubled_angle,
    lidar_strike_to_grid_doubled_angle,
)


def test_contour_parallel_scarp_positive_and_downslope_canyon_negative():
    """A N-S piedmont scarp on an eastward-sloping range front must score positive on
    ``H72_contour_scarp_dem`` and ``H72_contour_scarp_lidar``, whereas an E-W canyon crest
    draining down the eastward macro-slope must score negative."""
    h, w = 180, 180
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Eastward-sloping range flank: elevation decreases with col (xx) -> N-S contours (theta = 90 deg)
    macro = 500.0 - 4.0 * xx
    # Add a sharp N-S piedmont fault ridge at col=60 (contour-parallel) and an E-W canyon spur at row=120
    ns_scarp = 25.0 * np.exp(-0.5 * ((xx - 60.0) / 1.5) ** 2) * (yy < 90)
    ew_spur = 25.0 * np.exp(-0.5 * ((yy - 135.0) / 1.5) ** 2) * (xx > 95)
    z = macro + ns_scarp + ew_spur

    foot = np.ones((h, w), dtype=bool)
    c_m, s_m = contour_doubled_angle(macro, 15.0, 6.0)
    # N-S contour -> theta_grid = 90 deg -> cos(180) = -1, sin(180) = 0
    assert float(c_m[90, 90]) == pytest.approx(-1.0, abs=1e-3)
    assert float(s_m[90, 90]) == pytest.approx(0.0, abs=1e-3)

    lid_strike = np.full((h, w), 90.0, dtype=np.float32)  # N-S in grid frame
    lid_strike[120:, :] = 0.0                             # E-W in lower strip
    lid_valid = np.ones((h, w), dtype=np.float32)
    lid_valid[:20, :] = np.nan                            # missing 3DEP strip -> must stay NaN

    c_l, s_l = lidar_strike_to_grid_doubled_angle(np.array([90.0, 0.0], dtype=np.float32))
    assert c_l[0] == pytest.approx(-1.0, abs=1e-5)
    assert c_l[1] == pytest.approx(+1.0, abs=1e-5)

    # Diagonal NW-SE ridge along xx == yy on tilted plane: theta = +45 deg -> (cos 90, sin 90) = (0, +1)
    nwse = macro + 25.0 * np.exp(-0.5 * ((xx - yy) / 2.0) ** 2)
    cd_diag, sd_diag = hessian_ridge_doubled_angle(nwse, 1.5)
    assert float(cd_diag[90, 90]) == pytest.approx(0.0, abs=1e-2)
    assert float(sd_diag[90, 90]) == pytest.approx(+1.0, abs=1e-2)

    ones = np.ones((h, w), dtype=np.float32)
    grids = compute_h72_grids(
        det_elev=z,
        iso_grav=-macro,
        iso_grav_slope=ones,
        iso_grav_vg=(xx - 60.0),
        cond_surf=np.exp(-0.5 * ((xx - 60.0) / 3.0) ** 2),
        depth_to_base=100.0 + 10.0 * np.maximum(xx - 58.0, 0.0),
        geod_shear=ones * 10.0,
        geod_dilat=ones * 5.0,
        deq=ones * 200.0,
        ieq=ones * 50.0,
        lidar_step_max=0.05 + 0.8 * ((ns_scarp > 1.0) | (ew_spur > 1.0)).astype(np.float32),
        lidar_coh100=ones * 0.8,
        lidar_strike_deg=lid_strike,
        lidar_valid=lid_valid,
        footprint=foot,
    )
    assert list(grids.keys()) == H72_NAMES
    # Missing 3DEP tiles stay NaN on H72_contour_scarp_lidar, while all other 5 columns are finite
    assert np.isnan(grids["H72_contour_scarp_lidar"][:20, :]).all()
    for nm in H72_NAMES[1:]:
        assert np.isfinite(grids[nm]).all(), nm

    # Contour-parallel N-S fault ridge at (50, 60) > 0; down-slope E-W canyon spur at (135, 130) < 0
    assert float(grids["H72_contour_scarp_dem"][50, 60]) > 0.20
    assert float(grids["H72_contour_scarp_dem"][135, 130]) < -0.20
    assert float(grids["H72_contour_scarp_lidar"][50, 60]) > 0.20
    assert float(grids["H72_contour_scarp_lidar"][135, 130]) < -0.20


def test_censor_catalogue_proximity_clamps_dist_and_zeros_dens5():
    e = np.zeros((7, 5), dtype=np.float32)
    e[0] = np.log1p(np.array([0.0, 2.0, 8.0, 15.0, 35.0], dtype=np.float32))
    e[1] = 0.5
    e[3] = np.array([0.4, 0.3, 0.2, 0.1, 0.0], dtype=np.float32)
    e[5] = 0.02

    c = censor_catalogue_proximity(e)
    assert np.allclose(c[0, :4], np.log1p(CENSOR_MIN_DIST_PX))
    assert c[0, 4] == pytest.approx(np.log1p(35.0))
    assert np.all(c[3] == 0.0)
    assert np.allclose(c[1], 0.5)
    assert np.allclose(c[5], 0.02)
    # Original array untouched
    assert e[3, 0] == pytest.approx(0.4)


def test_emit_debiased_b2_greedy_respects_flank_shield_and_preserves_tip():
    h, w = 80, 80
    dom = np.ones((h, w), dtype=bool)
    known = np.zeros((h, w), dtype=bool)
    known[20:50, 30] = True  # vertical known fault segment from row 20..49 at col 30

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # Ridge 1: lateral parallel halo at col 32 (2 px from known fault, tip=0) -> MUST be shielded
    halo_ridge = 0.8 * np.exp(-0.5 * ((xx - 32.0) / 0.8) ** 2) * ((yy >= 22) & (yy <= 47))
    # Ridge 2: genuine on-strike tip continuation at rows 51..62, col 30 (tip=0.4) -> preserved
    tip_ridge = 0.85 * np.exp(-0.5 * ((xx - 30.0) / 0.8) ** 2) * ((yy >= 51) & (yy <= 62))
    # Ridge 3: off-flank blind ridge at col 60
    blind_ridge = 0.9 * np.exp(-0.5 * ((xx - 60.0) / 0.8) ** 2) * ((yy >= 15) & (yy <= 65))
    score = (halo_ridge + tip_ridge + blind_ridge).astype(np.float32)

    tip = np.zeros((h, w), dtype=np.float32)
    tip[50:60, 29:32] = 0.4

    em, diag = emit_debiased_b2_greedy(
        score, dom, known, tip,
        pool_kfrac=0.10, target_frac=0.02, n_hat_frac=0.01,
    )
    assert not (em & known).any()
    # Lateral flank ridge at col 32 (rows 25..45) is completely suppressed
    assert int(em[25:45, 31:34].sum()) == 0
    # Tip extension (rows 51..60, col 30) and blind ridge (col 60) emit dots
    assert int(em[51:60, 29:32].sum()) >= 1
    assert int(em[15:65, 59:62].sum()) >= 3
    assert diag["greedy"]["n_selected"] == int(em.sum())
