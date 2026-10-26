import numpy as np

from gems25.olic import OLIC_NAMES, compute_olic_grids, line_means


def test_line_means_constant_field():
    g = np.full((31, 31), 0.5, np.float32)
    lm = line_means(g, 5)
    assert lm.shape == (4, 31, 31)
    assert np.allclose(lm[:, 15, 15], 0.5)  # interior: no zero-padding dilution


def test_olic_prefers_line_over_isolated_dot():
    foot = np.ones((31, 31), bool)
    line = np.zeros((31, 31), np.float32)
    line[15, 5:26] = 1.0
    dot = np.zeros((31, 31), np.float32)
    dot[15, 15] = 1.0
    fl = compute_olic_grids([line], foot)[0]
    fd = compute_olic_grids([dot], foot)[0]
    assert fl[15, 15] > fd[15, 15]
    assert len(OLIC_NAMES) == 9


def test_olic_zero_outside_and_finite():
    foot = np.zeros((15, 15), bool)
    foot[3:12, 3:12] = True
    rng = np.random.default_rng(0)
    feats = compute_olic_grids([rng.random((15, 15), dtype=np.float32)], foot)
    for f in feats:
        assert np.isfinite(f).all() and f[~foot].max() == 0.0 and f.min() >= 0.0 and f.max() <= 1.0
