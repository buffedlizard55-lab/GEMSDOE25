"""Local pixel-identity checks for owner-mirrored rasters carrying user/owner-reported score labels."""

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


def test_reported_0_2477_mask_is_exactly_dot_thin_of_h19_5():
    h, d = mask(H195), mask(D15)
    assert h.sum() == 121_131 and d.sum() == 60_069
    assert (d & ~h).sum() == 0
    assert np.array_equal(dot_thin(h, 1.5), d)


def test_alternate_is_dot_thin_2_4_and_integer_lattice_makes_2_4_equal_2_8():
    h, a = mask(H195), mask(D28)
    assert a.sum() == 44_090
    assert np.array_equal(dot_thin(h, 2.4), a) and np.array_equal(dot_thin(h, 2.8), a)


def test_writer_reproduces_the_owner_mirror_profile_and_pixels(tmp_path):
    """The writer reproduces the local 0.2477-labelled raster's pixels/profile; no portal status is inferred."""
    from gems25.submission import check_file, write_submission

    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("template not restored")
    with rasterio.open(D15) as s:
        ref, prof_ref = s.read(1), s.profile
    pred = np.nan_to_num(ref, nan=0.0)
    out = write_submission(pred, tmpl, tmp_path / "re.tif", outside="nan")
    with rasterio.open(out) as s:
        got, prof = s.read(1), s.profile
    assert np.array_equal(np.isnan(got), np.isnan(ref)) and np.array_equal(np.nan_to_num(got), np.nan_to_num(ref))
    for k in ("driver", "dtype", "width", "height", "count", "crs", "transform", "compress", "blockxsize", "blockysize", "tiled", "interleave"):
        assert prof[k] == prof_ref[k], (k, prof[k], prof_ref[k])
    assert np.isnan(prof["nodata"]) and np.isnan(prof_ref["nodata"])
    assert check_file(out, tmpl)["ok_to_upload"] and check_file(D15, tmpl)["ok_to_upload"]
