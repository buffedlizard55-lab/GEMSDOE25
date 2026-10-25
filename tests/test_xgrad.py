"""Unit tests for the XG1 cross-gradient block on synthetic fields (knowledge/21).

These use no competition data and fit no model: they pin the *definition* —
parallel co-located edges score high, perpendicular or single-field edges score low,
constant fields give exactly zero, and every output is finite float32.
"""

from __future__ import annotations

import numpy as np
import pytest

from gems25.xgrad import XG_NAMES, _pair_column, _gradients, xg_grids

N = 96


def _step(axis: int) -> np.ndarray:
    a = np.zeros((N, N), np.float32)
    if axis == 1:  # step across columns -> gradient along x
        a[:, N // 2 :] = 10.0
    else:  # step across rows -> gradient along y
        a[N // 2 :, :] = 10.0
    return a


def _centre(v: np.ndarray) -> float:
    return float(v[N // 2 - 8 : N // 2 + 8, N // 2 - 8 : N // 2 + 8].max())


def test_parallel_edges_score_higher_than_perpendicular():
    gx_field = _gradients(_step(1))  # gradients point along +x near the step
    gy_field = _gradients(_step(0))  # gradients point along +y near the step
    parallel = _pair_column(gx_field, gx_field)
    perpendicular = _pair_column(gx_field, gy_field)
    assert np.isfinite(parallel).all() and np.isfinite(perpendicular).all()
    assert _centre(parallel) > 0
    assert _centre(perpendicular) < 0.25 * _centre(parallel)


def test_single_field_edge_scores_low():
    edge = _gradients(_step(1))
    flat = _gradients(np.ones((N, N), np.float32))
    out = _pair_column(edge, flat)
    assert float(out.max()) == 0.0  # joint strength is min(...) -> exactly zero


def test_constant_fields_give_zero_finite_grids():
    grids = xg_grids(np.ones((N, N), np.float32), np.zeros((N, N), np.float32), np.full((N, N), 5.0, np.float32))
    assert list(grids) == XG_NAMES
    for v in grids.values():
        assert v.shape == (N, N) and v.dtype == np.float32
        assert np.isfinite(v).all()
        assert float(v.max()) == 0.0


def test_nan_nodata_is_filled_not_propagated():
    grav = _step(1)
    grav[:5, :5] = np.nan
    grids = xg_grids(grav, _step(1), np.exp(_step(1)) - 1.0)
    for v in grids.values():
        assert np.isfinite(v).all()
    assert _centre(grids["XG_gm_align_ridge"]) > 0


def test_nonfinite_or_wrong_shape_rejected_by_gradients():
    with pytest.raises(ValueError):
        _gradients(np.array([[np.inf]], np.float32))
    with pytest.raises(ValueError):
        _gradients(np.zeros((3,), np.float32))
