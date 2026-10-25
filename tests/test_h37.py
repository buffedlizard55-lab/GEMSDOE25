"""H37-SEISALIGN operator tests on synthetic fields (no competition data)."""

import numpy as np
import pytest

from gems25.h37 import H37_NAMES, h37_grids, structure_tensor_coherence


def test_coherence_high_for_aligned_ridge_low_for_isotropic_blob():
    H, W = 96, 96
    y, x = np.mgrid[0:H, 0:W]
    ridge = np.exp(-((y - H / 2) ** 2) / (2 * 2.0**2)) * np.ones((H, W))
    blob = np.exp(-(((y - H / 2) ** 2) + ((x - W / 2) ** 2)) / (2 * 8.0**2))
    c_ridge = structure_tensor_coherence(np.log1p(100 * ridge))
    c_blob = structure_tensor_coherence(np.log1p(100 * blob))
    assert c_ridge[H // 2, W // 2] > 0.8
    assert c_blob[H // 2, W // 2] < 0.3
    assert (c_ridge >= 0).all() and (c_ridge <= 1.0001).all()


def test_coherence_rejects_nonfinite():
    with pytest.raises(ValueError):
        structure_tensor_coherence(np.full((8, 8), np.nan))


def test_h37_grids_finite_and_aligned_ridge_peaks_on_ridge():
    H, W = 96, 96
    y = np.arange(H, dtype=np.float32)[:, None].repeat(W, axis=1)
    dens = (1000.0 * np.exp(-((y - H / 2) ** 2) / (2 * 2.0**2))).astype(np.float32)
    dens[0, 0] = np.nan
    grids = h37_grids(dens, dens.copy())
    for name in H37_NAMES:
        g = grids[name]
        assert g.shape == (H, W) and np.isfinite(g).all() and (g >= 0).all()
    assert grids["H37_seis_deq_alignridge"][H // 2, W // 2] >= grids["H37_seis_deq_alignridge"][8, W // 2]
