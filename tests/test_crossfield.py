import numpy as np
import pytest

from gems25.crossfield import crossfield


def test_crossing_gradients_are_stronger_than_parallel():
    y, x = np.mgrid[:80, :80].astype(np.float32)
    foot = np.ones(x.shape, bool)
    a = crossfield(x, y, foot)
    b = crossfield(x, 2*x, foot)
    assert np.isfinite(a).all()
    assert a[10:-10, 10:-10].mean() > 0.9
    assert b[10:-10, 10:-10].max() < 1e-5


def test_rejects_wrong_shape_and_empty_footprint():
    a = np.ones((10, 10), np.float32)
    with pytest.raises(ValueError):
        crossfield(a, a[:, :5], np.ones_like(a, bool))
    with pytest.raises(ValueError):
        crossfield(a, a, np.zeros_like(a, bool))
