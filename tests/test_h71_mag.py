"""Synthetic residual-RTP lineament test for H71-4 (no labels)."""

from __future__ import annotations

import numpy as np

from gems25.h71_mag import compute_mag_aniso_grid


def test_mag_aniso_range_and_peaks_on_a_step():
    h, w = 48, 64
    cols = np.arange(w, dtype=np.float32)[None, :]
    rtp = np.repeat(8.0 * np.tanh((cols - 32.0) / 2.0), h, axis=0).astype(np.float32)
    foot = np.ones((h, w), dtype=bool)
    foot[:2, :] = False
    a = compute_mag_aniso_grid(rtp, foot)
    assert a.shape == rtp.shape and a.dtype == np.float32
    assert np.isfinite(a).all()
    assert float(a.min()) >= 0.0 and float(a.max()) <= 1.0 + 1e-6
    assert float(a[~foot].max()) == 0.0
    profile = a[2:, :].mean(axis=0)
    peak = int(np.argmax(profile))
    assert 28 <= peak <= 36, peak
    assert float(profile[peak]) > float(profile[8])
