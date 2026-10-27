"""Independent format audit fails closed, including optional ZIP packaging."""
from __future__ import annotations

import zipfile

import numpy as np
import rasterio
from affine import Affine

from scripts import verify_candidate_independent as verifier

TR = Affine(100, 0, 0, 0, -100, 800)


def raster(path, array, transform=TR):
    with rasterio.open(path, "w", driver="GTiff", count=1, dtype="float32", height=array.shape[0],
                       width=array.shape[1], crs="EPSG:32611", transform=transform) as ds:
        ds.write(np.asarray(array, np.float32), 1)
    return path


def inputs(tmp_path):
    grid = np.ones((8, 8), np.float32)
    grid[0, 0] = np.nan
    template = raster(tmp_path / "template.tif", grid)
    labels = np.zeros((8, 8), np.float32)
    labels[3, 3] = 1
    labels_path = raster(tmp_path / "labels.tif", labels)
    data = np.zeros((8, 8), np.float32)
    data[4, 4] = 1
    cand = raster(tmp_path / "candidate.tif", data)
    expected = dict(epsg=32611, shape=(8, 8), transform=tuple(TR)[:6], footprint_pixels=63)
    return cand, template, labels_path, expected


def run(paths, *, require_zip=False):
    cand, template, labels, expected = paths
    return verifier.audit(cand, template, labels, expected=expected,
                          template_pin=verifier.sha(template), labels_pin=verifier.sha(labels),
                          require_zip=require_zip)


def test_valid_tiff_and_exact_zip_pass_format_only(tmp_path):
    paths = inputs(tmp_path)
    cand = paths[0]
    with zipfile.ZipFile(cand.with_suffix(".zip"), "w") as archive:
        archive.writestr(cand.name, cand.read_bytes())
    rec = run(paths, require_zip=True)
    assert rec["all_hard_checks_pass"] is True
    assert rec["zip"]["contains_exactly_candidate_bytes"] is True
    assert "no organizer or slot approval" in rec["scope"]


def test_missing_wrong_member_and_bad_zip_all_fail(tmp_path):
    paths = inputs(tmp_path)
    cand = paths[0]
    assert not run(paths, require_zip=True)["all_hard_checks_pass"]
    with zipfile.ZipFile(cand.with_suffix(".zip"), "w") as archive:
        archive.writestr("wrong.tif", cand.read_bytes())
    rec = run(paths)
    assert not rec["all_hard_checks_pass"] and not rec["zip"]["contains_exactly_candidate_bytes"]
    cand.with_suffix(".zip").write_bytes(b"not a zip")
    rec = run(paths)
    assert not rec["all_hard_checks_pass"] and not rec["zip"]["contains_exactly_candidate_bytes"]


def test_bad_shape_nonfinite_and_label_overlap_return_negative_receipts(tmp_path):
    paths = inputs(tmp_path)
    cand = paths[0]
    raster(cand, np.zeros((7, 8), np.float32))
    rec = run(paths)
    assert not rec["checks"]["shape_equals_template"] and not rec["all_hard_checks_pass"]
    bad = np.zeros((8, 8), np.float32)
    bad[4, 4] = np.nan
    raster(cand, bad)
    assert not run(paths)["checks"]["footprint_all_finite"]
    bad[4, 4], bad[3, 3] = 0, 1
    raster(cand, bad)
    assert not run(paths)["checks"]["no_emission_on_catalogue"]
    bad[3, 3], bad[4, 4] = 0, 1.1
    raster(cand, bad)
    assert not run(paths)["checks"]["footprint_values_in_0_1"]


def test_misaligned_labels_and_wrong_template_pin_are_rejected(tmp_path):
    paths = inputs(tmp_path)
    cand, template, labels, expected = paths
    raster(labels, np.zeros((8, 8), np.float32), transform=Affine(100, 0, 1, 0, -100, 800))
    rec = run(paths)
    assert not rec["checks"]["labels_grid_matches_template"] and not rec["all_hard_checks_pass"]
    rec = verifier.audit(cand, template, labels, expected=expected, template_pin="0" * 64,
                         labels_pin=verifier.sha(labels))
    assert not rec["checks"]["template_sha256_matches_pin"] and not rec["all_hard_checks_pass"]
