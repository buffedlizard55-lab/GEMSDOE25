"""Regression tests for literal, full-footprint, complete-registry lane gates."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine

from scripts import check_lane_duplicates as final
from scripts import check_lane_surface as surface

ROOT = Path(__file__).resolve().parents[1]


def write_raster(path, values, *, transform=None, crs="EPSG:32611", nodata=None):
    values = np.asarray(values, dtype=np.float32)
    with rasterio.open(path, "w", driver="GTiff", height=values.shape[0], width=values.shape[1],
                       count=1, dtype="float32", crs=crs,
                       transform=transform or Affine(100, 0, 0, 0, -100, 2000), nodata=nodata) as ds:
        ds.write(values, 1)
    return path


@pytest.fixture
def pair(tmp_path, monkeypatch):
    # Exercise array/registry logic on small grids without pretending those
    # test templates are eligible for the production CLI.
    monkeypatch.setattr(final, "validate_template", lambda path: final.sha256(path))
    template = write_raster(tmp_path / "template.tif", np.ones((20, 20)))
    a = np.zeros((20, 20), np.float32)
    b = np.zeros_like(a)
    a[1, 1] = a[1, 3] = a[3, 1] = a[3, 3] = 1
    b[16, 16] = b[16, 18] = b[18, 16] = b[18, 18] = 1
    candidate = write_raster(tmp_path / "candidate.tif", a)
    ref = write_raster(tmp_path / "reference.tif", b)
    return template, candidate, ref


def test_full_registry_can_clear_only_when_every_pin_is_present(pair):
    template, candidate, ref = pair
    expected = {final.sha256(ref)}
    result = final.audit(candidate, template, [ref], expected)
    assert result["registry_complete"] and result["lane_clear"]
    assert result["rank_footprint_pixels"] == 400
    assert result["rows"][0]["dots_within_3px"] == 0
    missing = final.audit(candidate, template, [ref], expected | {"f" * 64})
    assert not missing["registry_complete"] and not missing["lane_clear"]
    assert "f" * 64 in missing["registry_inventory"]["missing_sha256"]
    assert not final.audit(candidate, template, [ref], set())["lane_clear"]
    assert not final.audit(candidate, template, [ref], expected, selected_only=True)["lane_clear"]


def test_wrong_transform_wrong_crs_and_nonfinite_reference_never_clear(pair, tmp_path):
    template, candidate, _ = pair
    b = np.zeros((20, 20), np.float32)
    b[17, 17] = 1
    for path in (write_raster(tmp_path / "shift.tif", b, transform=Affine(100, 0, 10, 0, -100, 2000)),
                 write_raster(tmp_path / "wrong_crs.tif", b, crs="EPSG:4326")):
        # A reference on a different grid/CRS is not comparable on the template
        # grid: it is skipped and recorded, never treated as evidence, and it
        # can never produce clearance.
        result = final.audit(candidate, template, [path], {final.sha256(path)})
        assert not result["lane_clear"]
        assert result["skipped"]
        assert not result["errors"]
    b[5, 5] = np.nan
    nonfinite = write_raster(tmp_path / "nonfinite.tif", b)
    result = final.audit(candidate, template, [nonfinite], {final.sha256(nonfinite)})
    assert not result["lane_clear"] and "nonfinite" in result["errors"][0]["error"]


def test_same_stem_or_same_mask_siblings_are_not_excluded(pair, tmp_path):
    template, candidate, _ = pair
    with rasterio.open(candidate) as ds:
        values = ds.read(1)
    # Different bytes, same footprint mask: old same-stem logic used to omit this sibling.
    sibling = write_raster(tmp_path / "candidate-nan.tif", values, nodata=-9999)
    assert final.sha256(candidate) != final.sha256(sibling)
    result = final.audit(candidate, template, [sibling], {final.sha256(sibling)})
    assert result["rows"][0]["dots_within_3px"] == 1
    assert result["rows"][0]["duplicate"] and not result["lane_clear"]


def test_undefined_rank_and_empty_candidates_fail_closed(pair, tmp_path):
    template, candidate, _ = pair
    constant = write_raster(tmp_path / "constant.tif", np.ones((20, 20)))
    result = final.audit(candidate, template, [constant], {final.sha256(constant)})
    assert result["rows"][0]["rank_undefined"] and not result["lane_clear"]
    empty = write_raster(tmp_path / "empty.tif", np.zeros((20, 20)))
    empty_result = final.audit(empty, template, [constant], {final.sha256(constant)})
    assert not empty_result["lane_clear"] and "empty candidate" in empty_result["errors"][0]["error"]
    assert surface.surface_rank(np.zeros(5), np.arange(5))["flag_rank"]


def test_dense_reference_overlap_cannot_be_waived():
    foot = np.ones((60, 60), dtype=bool)
    lattice = np.zeros(foot.shape, np.float32)
    lattice[::5, ::5] = 1
    candidate = np.zeros(foot.shape, np.float32)
    candidate[2::5, 2::5] = 1
    row = final.compare_arrays(candidate, lattice, foot)
    assert row["halo_coverage_3px"] >= 0.70
    assert row["dots_within_3px"] == 1.0
    assert row["flag_overlap"] and row["duplicate"]


def test_exact_threshold_is_allowed_only_when_not_exceeded():
    # Put exactly seven of ten separated candidate dots on the reference.
    foot = np.ones((80, 80), bool)
    candidate, ref = np.zeros(foot.shape), np.zeros(foot.shape)
    for i in range(10):
        candidate[5 + 7 * i, 5] = 1
        if i < 7:
            ref[5 + 7 * i, 5] = 1
    row = final.compare_arrays(candidate, ref, foot)
    assert row["dots_within_3px"] == pytest.approx(0.7)
    assert not row["flag_overlap"]
    ref[5 + 7 * 7, 5] = 1
    assert final.compare_arrays(candidate, ref, foot)["flag_overlap"]


def test_rank_uses_all_pixels_not_legacy_400k_sample(monkeypatch):
    shape = (700, 700)
    foot = np.ones(shape, bool)
    a, b = np.zeros(shape), np.zeros(shape)
    a[1::30, 1::30] = 1
    b[15::30, 15::30] = 1
    seen = []
    original = final.spearmanr

    def record(x, y):
        seen.append((len(x), len(y)))
        return original(x, y)

    monkeypatch.setattr(final, "spearmanr", record)
    final.compare_arrays(a, b, foot)
    assert seen == [(490_000, 490_000)]


def test_surface_audit_requires_complete_inventory_and_full_grid(pair):
    template, _, ref = pair
    with rasterio.open(template) as ds:
        profile = (ds.shape, ds.crs, ds.transform)
    foot = np.ones((20, 20), bool)
    scores = np.random.default_rng(11).random(foot.sum())
    good = surface.audit_surface(scores, foot, profile, [ref], {final.sha256(ref)})
    assert good["surface_clear"] and good["rank_footprint_pixels"] == 400
    assert not surface.audit_surface(scores, foot, profile, [ref], {"f" * 64})["surface_clear"]
    assert not surface.audit_surface(scores, foot, profile, [ref], {final.sha256(ref)}, excluded=True)["surface_clear"]
    with pytest.raises(ValueError, match="nonfinite"):
        surface.audit_surface(np.full(foot.sum(), np.nan), foot, profile, [ref], {final.sha256(ref)})


def test_diagnostic_reference_cli_never_issues_clearance(pair, tmp_path):
    template, candidate, ref = pair
    out = tmp_path / "result.json"
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_lane_duplicates.py"), str(candidate),
                             "--template", str(template), "--reference", str(ref), "--out", str(out)],
                            text=True, capture_output=True, check=False)
    assert result.returncode == 2
    audit = json.loads(out.read_text())
    assert not audit["lane_clear"] and "template" in audit["error"].lower()


def test_inventory_pins_every_registered_file_and_h78_twins():
    pins = final.declared_hashes()
    submissions = json.loads((ROOT / "registry/submissions.json").read_text())["files"]
    extra = json.loads((ROOT / "registry/lane_reference_pins.json").read_text())["rasters"]
    assert {x["sha256"] for x in submissions + extra} <= pins


def test_unpinned_custom_template_is_not_a_clearance(tmp_path):
    template = write_raster(tmp_path / "fake-template.tif", np.ones((20, 20)))
    with pytest.raises(ValueError, match="template SHA-256"):
        final.validate_template(template)
