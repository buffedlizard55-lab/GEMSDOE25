"""MSCR-1 unit tests on synthetic fields (pre-registered in knowledge/22; no data files)."""

import numpy as np
import pytest

from gems25.mscr import MSCR_NAMES, build_mscr_sidecar, load_mscr_sidecar, mscr_grids


def _ridge(shape=(81, 81), at=40, width=2.0, height=100.0):
    x = np.arange(shape[1], dtype=np.float32)
    prof = height * np.exp(-((x - at) ** 2) / (2 * width**2))
    return np.tile(prof, (shape[0], 1)).astype(np.float32)


def _valley(**kw):
    return -_ridge(**kw)


def test_broad_ridge_scores_high_on_crest_and_persistence():
    out = mscr_grids(_ridge(width=6.0))
    assert out["MSCR_crest_s4"][40, 40] > out["MSCR_crest_s4"][40, 5]
    assert out["MSCR_crest_persist"][40, 40] > 0.5
    # a pure crest is not a trough at its centre
    assert out["MSCR_trough_s4"][40, 40] <= out["MSCR_trough_s4"].max() * 0.5


def test_broad_valley_scores_high_on_trough():
    out = mscr_grids(_valley(width=6.0))
    assert out["MSCR_trough_s4"][40, 40] > out["MSCR_trough_s4"][40, 5]
    assert out["MSCR_crest_s4"][40, 40] <= out["MSCR_crest_s4"].max() * 0.5


def test_narrow_noise_line_has_low_persistence_vs_broad_line():
    rng = np.random.default_rng(1)
    noisy = _ridge(width=6.0) + (rng.standard_normal((81, 81)) * 30).astype(np.float32)
    out = mscr_grids(noisy)
    # the true broad line centre should out-persist a far off-line pixel on average
    centre = out["MSCR_crest_persist"][:, 40].mean()
    off = out["MSCR_crest_persist"][:, 8].mean()
    assert centre > off


def test_ranges_finite_and_nan_filled():
    z = _ridge(width=5.0)
    z[:6, :] = np.nan
    foot = np.ones(z.shape, bool)
    foot[:2, :] = False
    out = mscr_grids(z, foot)
    for n in MSCR_NAMES:
        assert np.isfinite(out[n]).all(), n
        assert (out[n] >= 0).all(), n
    assert out["MSCR_crest_persist"].max() <= 1.0


def test_validation():
    with pytest.raises(ValueError):
        mscr_grids(np.zeros((5, 5), np.float32))  # constant field
    with pytest.raises(ValueError):
        mscr_grids(np.zeros(10, np.float32))  # not 2-D
    with pytest.raises(ValueError):
        mscr_grids(_ridge(), np.ones((3, 3), bool))  # footprint mismatch


def test_sidecar_roundtrip(tmp_path):
    bands = tmp_path / "bands"
    bands.mkdir()
    np.save(bands / "12_det_elev.npy", _ridge((41, 41), 20, 5.0))
    fi = np.flatnonzero(np.ones((41, 41), bool).ravel())
    assert build_mscr_sidecar(bands, fi, tmp_path / "mscr_columns.npy") == MSCR_NAMES
    arr = load_mscr_sidecar(tmp_path, fi)
    assert arr.shape == (3, fi.size) and np.isfinite(np.asarray(arr)).all()
    assert float(arr[1, 20 * 41 + 20]) > 0.3  # persistence at the ridge centre
    with pytest.raises(ValueError):
        load_mscr_sidecar(tmp_path, fi[:-2])
