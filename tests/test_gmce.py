"""GMCE-1 unit tests on synthetic fields (pre-registered in knowledge/21; no data files)."""

import numpy as np
import pytest

from gems25.gmce import GMCE_NAMES, build_gmce_sidecar, gmce_grids, gradient_cosine, load_gmce_sidecar


def _step_x(shape=(41, 41), at=20, sign=1.0):
    a = np.zeros(shape, np.float32)
    a[:, at:] = sign * 10.0
    return a


def _step_y(shape=(41, 41), at=20, sign=1.0):
    a = np.zeros(shape, np.float32)
    a[at:, :] = sign * 10.0
    return a


def test_parallel_edges_give_cosine_one_and_strong_par_min():
    cos, ng, nm = gradient_cosine(_step_x(), _step_x(sign=3.0))
    band = (ng > np.percentile(ng[ng > 0], 90))  # pixels on the edge itself
    assert np.allclose(cos[band], 1.0, atol=1e-6)
    out = gmce_grids(_step_x(), _step_x(sign=3.0))
    assert out["GMCE_par_min"][20, 20] > 0.9
    assert out["GMCE_signed_min"][20, 20] > 0.9
    assert out["GMCE_ridge_par"].shape == (41, 41)
    assert (out["GMCE_ridge_par"] >= 0).all()


def test_antiparallel_edges_give_cosine_minus_one_and_signed_flips():
    cos, ng, _ = gradient_cosine(_step_x(), _step_x(sign=-2.0))
    band = (ng > np.percentile(ng[ng > 0], 90))
    assert np.allclose(cos[band], -1.0, atol=1e-6)
    out = gmce_grids(_step_x(), _step_x(sign=-2.0))
    # the coherent edge is still strong in |cos| but the signed twin is negative
    assert out["GMCE_par_min"][20, 20] > 0.9
    assert out["GMCE_signed_min"][20, 20] < -0.9


def test_perpendicular_edges_give_cosine_near_zero():
    cos, ng, nm = gradient_cosine(_step_x(), _step_y())
    both = (ng > np.percentile(ng[ng > 0], 90)) & (nm > np.percentile(nm[nm > 0], 90))
    assert both.any()
    assert np.abs(cos[both]).max() < 0.05


def test_flat_field_is_rejected_as_degenerate():
    flat = np.zeros((41, 41), np.float32)
    with pytest.raises(ValueError):
        gmce_grids(_step_x(), flat)
    with pytest.raises(ValueError):
        gmce_grids(flat, flat)


def test_weak_second_edge_yields_weak_par_min():
    rng = np.random.default_rng(0)
    noise = (0.01 * rng.standard_normal((41, 41))).astype(np.float32)
    out = gmce_grids(_step_x(), noise)
    strong = gmce_grids(_step_x(), _step_x(sign=3.0))
    assert out["GMCE_par_min"][20, 20] < 0.5 * strong["GMCE_par_min"][20, 20]


def test_ranges_and_nan_nodata_are_filled():
    g = _step_x()
    m = _step_x(sign=2.0)
    g[:5, :] = np.nan
    m[-5:, :] = np.nan
    foot = np.ones(g.shape, bool)
    foot[:3, :] = False
    out = gmce_grids(g, m, foot)
    for name in GMCE_NAMES:
        assert np.isfinite(out[name]).all(), name
    assert out["GMCE_par_min"].min() >= 0.0 and out["GMCE_par_min"].max() <= 1.0
    assert out["GMCE_signed_min"].min() >= -1.0 and out["GMCE_signed_min"].max() <= 1.0


def test_input_validation():
    good = _step_x()
    with pytest.raises(ValueError):
        gmce_grids(good, good[:10])
    with pytest.raises(ValueError):
        gmce_grids(good.ravel(), good.ravel())
    with pytest.raises(ValueError):
        gmce_grids(good, good, np.ones((3, 3), bool))
    with pytest.raises(ValueError):
        bad = good.copy()
        bad[0, 0] = np.inf
        gradient_cosine(bad, good)  # inf is not nodata-fillable input to the cosine core
    with pytest.raises(ValueError):
        gradient_cosine(good, good, sigma=-1.0)


def test_sidecar_roundtrip(tmp_path):
    bands = tmp_path / "bands"
    bands.mkdir()
    np.save(bands / "13_iso_grav_anom.npy", _step_x((21, 21), 10, 1.0))
    np.save(bands / "02_rtp.npy", _step_x((21, 21), 10, 2.0))
    fi = np.flatnonzero(np.ones((21, 21), bool).ravel())
    names = build_gmce_sidecar(bands, fi, tmp_path / "gmce_columns.npy")
    assert names == GMCE_NAMES
    arr = load_gmce_sidecar(tmp_path, fi)
    assert arr.shape == (3, fi.size)
    assert np.isfinite(np.asarray(arr)).all()
    # edge centre (row 10, col 10) must be a strong coherent edge
    centre = 10 * 21 + 10
    assert float(arr[0, centre]) > 0.5
    with pytest.raises(ValueError):
        load_gmce_sidecar(tmp_path, fi[:-1])  # shape mismatch must be caught
