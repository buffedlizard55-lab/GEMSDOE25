"""Byte-level reproduction of the 0.2477 file from its H19-5 parent (needs the restored scored rasters)."""

from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems25.paths import data_dir
from gems25.thinning import dot_thin

SCORED = data_dir() / "scored"
H195 = SCORED / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"
D15 = SCORED / "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif"
D28 = SCORED / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"

pytestmark = pytest.mark.skipif(not (H195.exists() and D15.exists() and D28.exists()),
                                reason="run scripts/restore_data.py --group scored first")


def mask(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return np.nan_to_num(s.read(1), nan=0.0) > 0


def test_scored_file_is_exactly_dot_thin_of_h19_5():
    h, d = mask(H195), mask(D15)
    assert h.sum() == 121_131 and d.sum() == 60_069
    assert (d & ~h).sum() == 0
    assert np.array_equal(dot_thin(h, 1.5), d)


def test_alternate_is_dot_thin_2_4_and_integer_lattice_makes_2_4_equal_2_8():
    h, a = mask(H195), mask(D28)
    assert a.sum() == 44_090
    assert np.array_equal(dot_thin(h, 2.4), a) and np.array_equal(dot_thin(h, 2.8), a)
