"""Synthetic drainage-offset tests for H71-3 AKF (no labels)."""

from __future__ import annotations

import numpy as np

from gems25.h71_akf import compute_akf_grid, d8_accumulation, d8_flowdir


def test_d8_flows_down_a_ramp():
    z = np.tile(np.arange(32, dtype=np.float32)[None, :], (24, 1))  # increases to the right
    # flow should go left (decreasing x) -> D8 index of (0, -1) is 6
    fdir, drop = d8_flowdir(z)
    assert (fdir[:, 1:-1] == 6).mean() > 0.9
    assert float(drop[:, 5].mean()) > 0.5


def test_accumulation_grows_downslope():
    z = np.tile(np.arange(20, dtype=np.float32)[None, :], (12, 1))
    foot = np.ones(z.shape, dtype=bool)
    fdir, _ = d8_flowdir(z)
    acc = d8_accumulation(z, foot, fdir)
    # leftmost column is the outlet
    assert float(acc[:, 0].mean()) > float(acc[:, -1].mean()) * 5.0


def test_akf_range_and_footprint_zero():
    rng = np.random.default_rng(0)
    z = rng.normal(0, 5, size=(40, 40)).astype(np.float32)
    z += np.linspace(30, 0, 40, dtype=np.float32)[None, :]
    foot = np.ones(z.shape, dtype=bool)
    foot[:2, :] = False
    a = compute_akf_grid(z, foot)
    assert a.shape == z.shape and a.dtype == np.float32
    assert np.isfinite(a).all()
    assert float(a.min()) >= 0.0 and float(a.max()) <= 1.0 + 1e-6
    assert float(a[~foot].max()) == 0.0
