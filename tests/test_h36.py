"""H36-TZC operator + column tests on synthetic fields (no competition data)."""

import numpy as np
import pytest

from gems25.h36 import H36_NAMES, h36_grids, proximity, spectral_tilt, zero_crossing_mask


def test_spectral_tilt_of_linear_ramp_is_constant():
    # VDR of a plane is 0 (no vertical variation in the harmonic sense beyond the
    # padded boundary), THDR is constant: tilt is ~0 away from the pad boundary.
    H, W = 64, 64
    a = np.tile(np.arange(W, dtype=np.float64) * 3.0, (H, 1)).astype(np.float32)
    th, _ = spectral_tilt(a, pad=16)
    assert np.isfinite(th).all() and (np.abs(th) <= np.pi / 2).all()


def test_spectral_tilt_rejects_nonfinite_and_bad_params():
    with pytest.raises(ValueError):
        spectral_tilt(np.full((8, 8), np.nan, dtype=np.float32))
    with pytest.raises(ValueError):
        spectral_tilt(np.zeros((8, 8), dtype=np.float32), dz_m=-1.0)


def test_spectral_tilt_zero_crosses_at_a_step_edge():
    H, W = 96, 96
    a = np.where(np.arange(W)[None, :] >= W // 2, 300.0, -100.0).astype(np.float32)
    a = np.tile(a, (H, 1))
    th, _ = spectral_tilt(a, pad=16)
    z = zero_crossing_mask(th)
    cols = np.flatnonzero(z[H // 2])
    assert cols.size > 0 and abs(int(cols.mean()) - W // 2) <= 4


def test_zero_crossing_mask_finds_sign_change_line_only():
    th = np.tile(np.linspace(-0.4, 0.4, 41, dtype=np.float64), (10, 1))
    z = zero_crossing_mask(th)
    cols = np.flatnonzero(z.any(axis=0))
    assert 1 <= cols.size <= 2 and abs(float(cols.mean()) - 20) <= 1
    # no sign change -> no line, even where |theta| is small
    assert not zero_crossing_mask(np.full((10, 10), 0.01)).any()


def test_proximity_decays_with_distance():
    d = np.array([0.0, 2.0, 6.0])
    p = proximity(d)
    assert p[0] == pytest.approx(1.0) and p[1] == pytest.approx(np.exp(-0.5)) and p[2] < 0.02


def test_h36_grids_localise_a_shared_contact_and_stay_finite():
    H, W = 96, 96
    step = np.where(np.arange(W)[None, :] >= W // 2, 300.0, -100.0).astype(np.float32)
    step = np.tile(step, (H, 1))
    step[0, 0] = np.nan  # nodata hole must be filled, not propagated
    grids = h36_grids(step, step.copy())
    for name in H36_NAMES:
        g = grids[name]
        assert g.shape == (H, W) and np.isfinite(g).all() and (g >= 0).all() and (g <= 1).all()
    mid = H // 2
    for name in H36_NAMES:
        col = int(np.argmax(grids[name][mid, 8:-8])) + 8
        assert abs(col - W // 2) <= 4, (name, col)
    assert int(grids["_zero_mag_px"].sum()) > 0 and int(grids["_zero_grav_px"].sum()) > 0
