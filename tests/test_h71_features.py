"""Synthetic-graben tests for H71 signed half-graben polarity (no labels, no fit)."""

from __future__ import annotations

import numpy as np

from gems25.h71 import H71_NAMES, compute_h71_grids


def _graben(H: int = 80, W: int = 80, col: float = 40.0, width: float = 3.0):
    """Vertical normal fault: left = hanging-wall basin, right = footwall range."""
    cols = np.arange(W, dtype=np.float32)[None, :]
    step = np.tanh((cols - col) / width)  # -1 left, +1 right
    # Broadcast to 2-D
    step = np.repeat(step, H, axis=0)
    z = 200.0 * step  # low basin, high range
    g = 12.0 * step  # gravity low in basin, high on range
    d = 1.8 - 1.2 * step  # deep basement in basin, shallow on range
    foot = np.ones((H, W), dtype=bool)
    foot[:2, :] = False
    return z, g, d, foot


def test_names_and_range():
    z, g, d, foot = _graben()
    grids = compute_h71_grids(z, g, d, foot)
    assert tuple(grids) == tuple(H71_NAMES)
    for name, arr in grids.items():
        assert arr.shape == foot.shape
        assert arr.dtype == np.float32
        assert np.isfinite(arr).all()
        assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0 + 1e-6
        assert float(arr[~foot].max()) == 0.0


def test_blind_peaks_at_graben_edge_not_basin_floor():
    z, g, d, foot = _graben()
    blind = compute_h71_grids(z, g, d, foot)["H71_blind_hgpc"]
    profile = blind[2:, :].mean(axis=0)
    peak = int(np.argmax(profile))
    assert 36 <= peak <= 44, peak
    assert float(profile[peak]) > float(profile[8]) * 3.0
    assert float(profile[peak]) > float(profile[72]) * 3.0


def test_blind_vanishes_when_basement_thickens_toward_gravity_high():
    z, g, d, foot = _graben()
    # Invert basement: now deep on the range (anti-graben) — polarity must collapse.
    d_bad = (d.max() + d.min()) - d
    blind_ok = compute_h71_grids(z, g, d, foot)["H71_blind_hgpc"]
    blind_bad = compute_h71_grids(z, g, d_bad, foot)["H71_blind_hgpc"]
    assert float(blind_ok[foot].mean()) > 5.0 * float(blind_bad[foot].mean() + 1e-8)


def test_surf_requires_elevation_concordance():
    z, g, d, foot = _graben()
    surf_ok = compute_h71_grids(z, g, d, foot)["H71_surf_hgpc"]
    z_flip = -z  # high basin, low range — not a half-graben
    surf_bad = compute_h71_grids(z_flip, g, d, foot)["H71_surf_hgpc"]
    assert float(surf_ok[foot].mean()) > 5.0 * float(surf_bad[foot].mean() + 1e-8)


def test_crest_passthrough_is_percentile_scaled_not_a_copy_of_blind():
    z, g, d, foot = _graben()
    crest = np.zeros_like(z)
    crest[:, 10:12] = 5.0
    grids = compute_h71_grids(z, g, d, foot, crest=crest)
    assert float(grids["H71_crest_ctrl"][:, 10:12].mean()) > 0.5
    assert float(grids["H71_crest_ctrl"][:, 40].mean()) < 0.05
    # Blind still peaks at the fault, not at the injected crest stripe.
    assert int(np.argmax(grids["H71_blind_hgpc"].mean(axis=0))) != 11
