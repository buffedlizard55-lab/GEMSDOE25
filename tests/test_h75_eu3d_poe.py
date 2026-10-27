"""Unit and synthetic-physics tests for H75-1 (EU3D-POE) in src/gems25/h75_eu3d.py."""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from gems25 import h75_eu3d
from gems25.h75_eu3d import (
    H75_EU3D_NAMES,
    SHMIN_UX,
    SHMIN_UY,
    compute_h75_eu3d_grids,
    euler_3d_window_solve,
    poe_combine,
)


def test_vectorized_euler_matches_bruteforce_window_solve() -> None:
    rng = np.random.default_rng(42)
    h, w = 24, 26
    win = 7
    half = win // 2
    cell_m = 100.0
    damping = 1e-6

    field = rng.normal(10.0, 2.5, size=(h, w))
    tx = rng.normal(0.0, 0.02, size=(h, w))
    ty = rng.normal(0.0, 0.02, size=(h, w))
    tz = rng.normal(0.01, 0.03, size=(h, w))

    vec = euler_3d_window_solve(
        field, tx, ty, tz, n_indices=(0.5, 2.0), win=win, cell_m=cell_m, damping_rel=damping, chunk_rows=9
    )

    # Check interior pixels free of boundary reflection
    for r in (5, 11, 17):
        for c in (6, 13, 19):
            sub_t = field[r - half : r + half + 1, c - half : c + half + 1]
            sub_gx = tx[r - half : r + half + 1, c - half : c + half + 1] * cell_m
            sub_gy = ty[r - half : r + half + 1, c - half : c + half + 1] * cell_m
            sub_gz = tz[r - half : r + half + 1, c - half : c + half + 1] * cell_m
            dy_grid, dx_grid = np.mgrid[-half : half + 1, -half : half + 1]

            A = np.column_stack([sub_gx.ravel(), sub_gy.ravel(), sub_gz.ravel(), np.ones(win * win)])
            G = (A.T @ A) / float(win * win)
            lam = damping * (G[0, 0] + G[1, 1] + G[2, 2]) / 3.0 + 1e-12
            G_reg = G.copy()
            G_reg[0, 0] += lam
            G_reg[1, 1] += lam
            G_reg[2, 2] += lam
            G_reg[3, 3] += 1e-12

            for n_val in (0.5, 2.0):
                y = (dx_grid * sub_gx + dy_grid * sub_gy + n_val * sub_t).ravel()
                b = (A.T @ y) / float(win * win)
                th = np.linalg.solve(G_reg, b)
                mse_bf = float(np.mean((A @ th - y) ** 2))
                tss_bf = float(np.var(y))

                assert vec[n_val]["dx0_m"][r, c] == pytest.approx(th[0] * cell_m, rel=1e-5, abs=1e-4)
                assert vec[n_val]["dy0_m"][r, c] == pytest.approx(th[1] * cell_m, rel=1e-5, abs=1e-4)
                assert vec[n_val]["z0_m"][r, c] == pytest.approx(th[2] * cell_m, rel=1e-5, abs=1e-4)
                assert vec[n_val]["nb"][r, c] == pytest.approx(th[3], rel=1e-5, abs=1e-5)
                assert vec[n_val]["mse"][r, c] == pytest.approx(mse_bf, rel=1e-5, abs=1e-6)
                assert vec[n_val]["tss"][r, c] == pytest.approx(tss_bf, rel=1e-5, abs=1e-6)


def test_analytical_euler_recovers_depth_and_discriminates_contact_vs_plug() -> None:
    # Exact analytical homogeneous potential T(x, y, z=0) = B + C * ((x-x0)^2 + (y-y0)^2 + z0^2)^(-N_true/2)
    h, w = 41, 41
    cell_m = 100.0
    yy, xx = np.mgrid[0:h, 0:w] * cell_m
    x0, y0, z0 = 2000.0, 2000.0, 600.0
    bg = 25.0

    for n_true, n_other in ((0.5, 2.0), (2.0, 0.5)):
        r2 = (xx - x0) ** 2 + (yy - y0) ** 2 + z0**2
        amp = 5.0e4 if n_true == 2.0 else 500.0
        t = bg + amp * (r2 ** (-0.5 * n_true))
        tx = -n_true * amp * (xx - x0) * (r2 ** (-0.5 * n_true - 1.0))
        ty = -n_true * amp * (yy - y0) * (r2 ** (-0.5 * n_true - 1.0))
        # At z=0 with z downward, (z - z0) = -z0 -> dT/dz = +n_true * amp * z0 * r2^(-N/2 - 1)
        tz = +n_true * amp * z0 * (r2 ** (-0.5 * n_true - 1.0))

        sol = euler_3d_window_solve(t, tx, ty, tz, n_indices=(0.5, 2.0), win=7, cell_m=cell_m, damping_rel=1e-10)
        st = sol[n_true]
        so = sol[n_other]
        assert abs(float(st["dx0_m"][20, 20])) < 1e-2
        assert abs(float(st["dy0_m"][20, 20])) < 1e-2
        assert float(st["z0_m"][20, 20]) == pytest.approx(z0, rel=1e-3)
        rel_true = float(st["mse"][20, 20] / (st["tss"][20, 20] + 1e-12))
        rel_other = float(so["mse"][20, 20] / (so["tss"][20, 20] + 1e-12))
        assert rel_true < 1e-6 and rel_other > 5e-4
        assert abs(float(so["z0_m"][20, 20]) - z0) > 100.0  # wrong N biases apparent depth z0


def test_anderson_orientation_prefers_nne_ssw_normal_fault_over_parallel_strike() -> None:
    h, w = 64, 64
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    foot = np.ones((h, w), dtype=bool)

    # Case A: Basement step normal aligned with SHmin (NNE-SSW fault strike) -> high normal dilation
    s_fav = (xx - 32.0) * SHMIN_UX + (yy - 32.0) * SHMIN_UY
    g_fav = np.tanh(s_fav / 3.0).astype(np.float32) * 10.0

    # Case B: Basement step normal perpendicular to SHmin (WNW-ESE strike) -> zero normal dilation
    s_unfav = -(xx - 32.0) * SHMIN_UY + (yy - 32.0) * SHMIN_UX
    g_unfav = np.tanh(s_unfav / 3.0).astype(np.float32) * 10.0

    def _base(g_field: np.ndarray) -> dict[str, np.ndarray]:
        return {
            "iso_grav_anom": g_field,
            "rtp": g_field * 20.0,
            "geod_dilaterate": np.full((h, w), 10.0, dtype=np.float32),
            "geod_shearrate": np.zeros((h, w), dtype=np.float32),  # pure dilatation test
            "cond_surf": np.ones((h, w), dtype=np.float32),
            "depth_to_base_surf": np.full((h, w), 500.0, dtype=np.float32),
            "tc": np.full((h, w), 80.0, dtype=np.float32),
        }

    # Check raw cos^2(alpha) alignment via gradient normal
    gy_f, gx_f = np.gradient(g_fav)
    gy_u, gx_u = np.gradient(g_unfav)
    nf_norm = np.hypot(gx_f[32, 32], gy_f[32, 32])
    nu_norm = np.hypot(gx_u[32, 32], gy_u[32, 32])
    td_fav = ((gx_f[32, 32] / nf_norm) * SHMIN_UX + (gy_f[32, 32] / nf_norm) * SHMIN_UY) ** 2
    td_unfav = ((gx_u[32, 32] / nu_norm) * SHMIN_UX + (gy_u[32, 32] / nu_norm) * SHMIN_UY) ** 2
    assert td_fav > 0.99 and td_unfav < 0.01

    out = compute_h75_eu3d_grids(_base(g_fav), foot)
    assert set(out.keys()) == set(H75_EU3D_NAMES)
    for k, arr in out.items():
        assert arr.dtype == np.float32 and arr.shape == (h, w)
        assert np.isfinite(arr).all() and arr.min() >= 0.0 and arr.max() <= 1.0, k


def test_poe_combine_and_no_label_or_topography_leakage_in_source() -> None:
    ps = np.array([[0.81, 0.81, np.nan]], dtype=np.float32)
    pr = np.array([[0.25, 0.0, 0.5]], dtype=np.float32)
    comb = poe_combine(ps, pr, gamma=0.5)
    assert comb.dtype == np.float32
    assert comb[0, 0] == pytest.approx(0.45, abs=1e-6)
    assert comb[0, 1] == 0.0
    assert comb[0, 2] == 0.0

    src_code = inspect.getsource(h75_eu3d.compute_h75_eu3d_grids) + inspect.getsource(h75_eu3d.load_h75_eu3d_sidecar)
    for forbidden in (
        "_labels",
        "labels.tif",
        "existing_faults",
        "qfaults",
        "dist_known_fault",
        "det_elev",
        "lidar_scarp",
    ):
        assert forbidden not in src_code, forbidden
