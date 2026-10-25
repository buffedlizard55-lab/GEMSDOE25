"""H34-1 operator + column tests on synthetic fields (no competition data)."""

import numpy as np
import pytest

from gems25.h34 import DZ_MID_M, DZ_SHALLOW_M, H34_NAMES, h34_grids, upward_continue_multi


def test_upward_continuation_preserves_constant_field():
    a = np.full((64, 48), 7.5, dtype=np.float32)
    (up,) = upward_continue_multi(a, (400.0,))
    assert np.allclose(up, 7.5, atol=1e-4)


def test_upward_continuation_attenuates_sine_by_exact_factor():
    # periodic field with an integer number of cycles across the width: pad=0 is exact
    H, W, cycles = 40, 200, 10  # wavelength 20 px = 2000 m at 100 m cells
    x = np.arange(W, dtype=np.float64)
    a = np.tile(np.sin(2 * np.pi * cycles * x / W), (H, 1)).astype(np.float32)
    (up,) = upward_continue_multi(a, (400.0,), pad=0)
    expected_ratio = float(np.exp(-2 * np.pi * 400.0 / 2000.0))
    got_ratio = float(up.std() / a.std())
    assert got_ratio == pytest.approx(expected_ratio, rel=0.02)


def test_upward_continuation_zero_height_and_monotone_attenuation():
    rng = np.random.default_rng(3)
    a = rng.normal(size=(48, 48)).astype(np.float32)
    up0, up400, up1200 = upward_continue_multi(a, (0.0, DZ_SHALLOW_M, DZ_MID_M))
    assert np.allclose(up0, a, atol=1e-4)
    assert up1200.std() < up400.std() < a.std()


def test_upward_continuation_rejects_nonfinite():
    a = np.zeros((16, 16), dtype=np.float32)
    a[3, 3] = np.nan
    with pytest.raises(ValueError):
        upward_continue_multi(a, (400.0,))


def test_h34_grids_localise_a_step_edge_and_stay_finite():
    H, W = 96, 96
    rtp = np.where(np.arange(W)[None, :] >= W // 2, 300.0, -100.0).astype(np.float32)
    rtp = np.tile(rtp, (H, 1))
    rtp[0, 0] = np.nan  # nodata hole must be filled, not propagated
    depth = np.where(np.arange(W)[None, :] >= W // 2, 2500.0, 120.0).astype(np.float32)
    depth = np.tile(depth, (H, 1))
    grids = h34_grids(rtp, depth)
    assert list(grids) == H34_NAMES
    for g in grids.values():
        assert g.shape == (H, W) and np.isfinite(g).all() and (g >= 0).all()
    # the step at column W//2 must be the dominant ridge in all three columns
    mid_row = H // 2
    for name, g in grids.items():
        col = int(np.argmax(g[mid_row, 8:-8])) + 8
        assert abs(col - W // 2) <= 4, (name, col)
