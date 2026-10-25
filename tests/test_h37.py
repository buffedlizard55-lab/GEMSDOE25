"""H37-1 DOC columns: synthetic checks on the frozen definitions (knowledge/22)."""

import numpy as np
import pytest

from gems25.h37 import H37_NAMES, doc_pair, downhill_unit, h37_grids, lag_sample


def _plane_downhill_rows(shape=(101, 41)):
    rows = np.arange(shape[0], dtype=np.float64)[:, None]
    return np.repeat(-rows, shape[1], axis=1)  # elevation decreases with row -> downhill = +row


def test_downhill_unit_points_downhill_and_is_unit():
    u_r, u_c = downhill_unit(_plane_downhill_rows())
    mid_r, mid_c = u_r[50, 20], u_c[50, 20]
    assert float(mid_r) == pytest.approx(1.0, abs=1e-5)
    assert float(mid_c) == pytest.approx(0.0, abs=1e-5)


def test_downhill_unit_flat_is_zero_and_rejects_nan():
    u_r, u_c = downhill_unit(np.zeros((21, 21)))
    assert np.all(u_r == 0) and np.all(u_c == 0)
    bad = np.zeros((5, 5)); bad[2, 2] = np.nan
    with pytest.raises(ValueError):
        downhill_unit(bad)


def test_doc_pair_finds_ridge_offset_downhill_not_uphill():
    z = _plane_downhill_rows()
    u_r, u_c = downhill_unit(z)
    rows = np.arange(z.shape[0], dtype=np.float64)
    prof = 3.0 * np.exp(-0.5 * ((rows - 53.0) / 1.0) ** 2)  # smooth ridge centred 3 px downhill
    field = np.repeat(prof[:, None].astype(np.float32), z.shape[1], axis=1)
    down, asym = doc_pair(field, u_r, u_c)
    # lag samples at +2/+4 read the flanks of the smooth ridge centred at +3
    # (real ridge-strength fields are Gaussian-smoothed the same way), while the
    # uphill samples read ~0.
    assert down[50, 20] > 0.0
    assert asym[50, 20] > 0.0
    # an uphill ridge gives the opposite sign (delta at exactly the -4 lag)
    field2 = np.zeros(z.shape, np.float32)
    field2[46, :] = 3.0
    down2, asym2 = doc_pair(field2, u_r, u_c)
    assert asym2[50, 20] < 0.0
    # exact-lag alignment: ridge at exactly +4 is fully captured downhill
    field3 = np.zeros(z.shape, np.float32)
    field3[54, :] = 3.0
    down3, _ = doc_pair(field3, u_r, u_c)
    assert down3[50, 20] == pytest.approx(3.0)


def test_doc_pair_constant_field_and_flat_dem_give_zero_asym():
    u_r, u_c = downhill_unit(_plane_downhill_rows())
    _, asym = doc_pair(np.ones((101, 41), np.float32), u_r, u_c)
    assert np.allclose(asym[5:-5, 2:-2], 0.0)
    u0_r, u0_c = downhill_unit(np.zeros((101, 41)))
    f = np.random.default_rng(0).normal(size=(101, 41)).astype(np.float32)
    down0, asym0 = doc_pair(f, u0_r, u0_c)
    assert np.allclose(asym0, 0.0) and np.allclose(down0, f)


def test_lag_sample_zero_lag_is_identity_and_shape_guard():
    f = np.arange(100, dtype=np.float32).reshape(10, 10)
    z = np.zeros((10, 10), np.float32)
    assert np.allclose(lag_sample(f, z, z, 2.0), f)
    with pytest.raises(ValueError):
        lag_sample(f, np.zeros((3, 3), np.float32), z, 1.0)


def test_h37_grids_names_finite_and_nan_input_filled():
    rng = np.random.default_rng(1)
    shape = (61, 53)
    elev = np.repeat(-np.arange(shape[0])[:, None].astype(np.float32), shape[1], axis=1)
    elev[0, 0] = np.nan
    grav = np.abs(rng.normal(size=shape)).astype(np.float32); grav[3, 3] = np.nan
    tmi = np.abs(rng.normal(size=shape)).astype(np.float32) + 0.1
    depth = (100 + 50 * rng.random(shape)).astype(np.float32); depth[5, 5] = np.nan
    out = h37_grids(elev, grav, tmi, depth)
    assert list(out) == H37_NAMES
    for v in out.values():
        assert v.shape == shape and np.isfinite(v).all()
