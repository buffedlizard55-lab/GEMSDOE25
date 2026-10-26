"""Unit tests for the APFL reconstruction (synthetic static cache, no data needed)."""

import numpy as np
import pytest

from gems25.apfl import APFL_INPUTS, APFL_NAMES, apfl_components


def _static(n=2000, seed=3):
    rng = np.random.default_rng(seed)
    names = list(APFL_INPUTS)
    arr = rng.normal(size=(len(names), n)).astype(np.float32)
    arr[names.index("L_valid")] = (rng.random(n) > 0.25).astype(np.float32)
    return arr, names


def test_apfl_shape_range_finite():
    arr, names = _static()
    out = apfl_components(arr, names)
    assert out.shape == (len(APFL_NAMES), arr.shape[1])
    assert np.isfinite(out).all()
    assert out.min() >= 0.0 and out.max() <= 1.0


def test_apfl_product_zero_without_lidar():
    arr, names = _static()
    out = apfl_components(arr, names)
    invalid = arr[names.index("L_valid")] <= 0
    assert (out[APFL_NAMES.index("APFL_product")][invalid] == 0).all()


def test_apfl_product_monotone_in_lstep():
    arr, names = _static(n=4000)
    lo = apfl_components(arr, names)[APFL_NAMES.index("APFL_product")]
    arr2 = arr.copy()
    arr2[names.index("L_step_max")] += 3.0
    hi = apfl_components(arr2, names)[APFL_NAMES.index("APFL_product")]
    assert hi.mean() >= lo.mean()


def test_apfl_missing_input_raises():
    arr, names = _static()
    with pytest.raises(ValueError, match="missing APFL inputs"):
        apfl_components(arr[:-1], names[:-1])
