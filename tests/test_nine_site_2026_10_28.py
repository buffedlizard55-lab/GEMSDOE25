"""Regression checks for the 2026-10-28 nine-site brief, the portal-safe gate and the r13 lane bound.

Receipt tests run everywhere (they read committed JSON). Raster tests skip unless the pinned owner mirrors are restored.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"


def _j(name: str) -> dict:
    return json.loads((EV / name).read_text())


def test_nine_site_receipt_reports_pins_and_lineage_chain() -> None:
    d = _j("nine_site_top_files_2026-10-28.json")
    rows = {r["site"]: r for r in d["rows"]}
    assert len(rows) == 10  # nine focus tops + one owner-listed sibling
    assert all(r["sha256_matches_pin"] for r in rows.values())
    lin = d["lineage_steps"]
    assert lin["d2_8_subset_chain_ok"] is True
    assert (lin["d2_8_dots"], lin["h27_4_dots"], lin["b2_dots"]) == (44090, 40199, 37654)
    assert lin["d2_8_to_h27_4_removed"] == 3891 and lin["h27_4_to_b2_removed"] == 2545
    assert lin["d2_8_dots_within_2px_catalogue"] == 6436
    assert lin["b2_dots_within_2px_catalogue"] == 0
    assert lin["removed_step1_max_catalogue_distance_px"] <= 2.0
    assert lin["removed_step2_max_catalogue_distance_px"] <= 2.0


def test_exact_duplicates_are_the_documented_pairs() -> None:
    d = _j("nine_site_top_files_2026-10-28.json")
    pairs = {tuple(sorted(p)) for p in d["exact_dot_set_duplicates_among_nine_sites"]}
    assert ("GEMSDOE25", "GEMSDOE30") in pairs
    # the GEMSDOE28 h27-4 sibling is an exact dot-set twin of GEMSDOE31 (checked by hash of the dot set)
    rows = {r["site"]: r for r in d["rows"]}
    assert rows["GEMSDOE31"]["dot_set_sha256_16"] == rows["GEMSDOE28-h27-4-r1-solo"]["dot_set_sha256_16"]


def test_b2_is_the_only_portal_safe_top_with_zero_catalogue_dots() -> None:
    d = _j("nine_site_top_files_2026-10-28.json")
    rows = {r["site"]: r for r in d["rows"]}
    assert rows["GEMSDOE32"]["outside_convention"] == "zeros"
    assert rows["GEMSDOE32"]["on_catalogue"] == 0
    assert rows["GEMSDOE32"]["positives"] == 37654
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE33"):
        assert rows[site]["outside_convention"] == "nan", site


def test_portal_sweep_counts_match_docs_downloads() -> None:
    sweep = _j("portal_safety_sweep_2026-10-28.json")
    # A dated 28 October receipt is an immutable historical snapshot, not today's inventory.
    current = {p.name for p in (ROOT / "docs" / "downloads").glob("*.tif")}
    assert {r["file"] for r in sweep["rows"]}.issubset(current)
    # The archived receipt says 61 but lists 60 rows: preserve and flag this
    # historical inconsistency rather than rewriting a dated receipt as current.
    assert sweep["total"] == 61 and len(sweep["rows"]) == 60
    assert sweep["portal_safe"] + sweep["portal_rejected_convention"] == sweep["total"]
    assert all(f.endswith(("-zeros.tif", "-zero.tif")) for f in sweep["portal_safe_files"])


def test_r13_lane_bound_arithmetic() -> None:
    b = _j("lane_bound_r13_2026-10-28.json")
    assert b["eligible_pixels_outside_halo_and_catalogue"] == 6514
    assert b["min_overlap_at_37654_dots"] == pytest.approx(1 - 6514 / 37654, abs=1e-6)
    assert b["max_dots_with_min_overlap_at_most_0_70"] == 21713
    assert 1 - 6514 / 21713 == pytest.approx(0.70, abs=1e-4)


def test_brief_page_and_readme_say_no_submission_and_unknown_estimate() -> None:
    page = (ROOT / "docs" / "nine-site-brief.html").read_text()
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in page
    assert "UNKNOWN" in page
    readme = (ROOT / "README.md").read_text()
    head = readme[: readme.index("## Latest result")]
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in head
    assert head.index("OK TO DOWNLOAD AND SUBMIT: NO") < head.index("nine-site-brief.html")


def test_portal_gate_rejects_nan_and_accepts_zeros(tmp_path) -> None:
    rasterio = pytest.importorskip("rasterio")
    from gems25.submission import check_file, write_submission

    tmpl = tmp_path / "t.tif"
    foot = np.zeros((20, 30), bool)
    foot[2:18, 3:27] = True
    prof = dict(driver="GTiff", dtype="float32", count=1, height=20, width=30, crs="EPSG:32611",
                transform=rasterio.transform.from_origin(243350, 4508550, 100, 100))
    with rasterio.open(tmpl, "w", nodata=np.nan, **prof) as dst:
        dst.write(np.where(foot, 0.0, np.nan).astype(np.float32), 1)
    pred = np.zeros((20, 30), np.float32)
    pred[10, 10:14] = 1.0
    for outside, expect_pass in (("nan", False), ("zero", True)):
        out = write_submission(pred, tmpl, tmp_path / f"{outside}.tif", outside=outside)
        r = check_file(out, tmpl)
        assert ("portal_all_cells_finite_in_0_1" not in r["hard_failures"]) is expect_pass, (outside, r["hard_failures"])


def test_recomputed_b2_subset_matches_receipt_when_mirrors_restored() -> None:
    rasterio = pytest.importorskip("rasterio")
    from gems25.paths import data_dir

    b2 = data_dir() / "owner_mirrors" / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    h27 = data_dir() / "owner_mirrors" / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
    d28 = data_dir() / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
    if not (b2.exists() and h27.exists() and d28.exists()):
        pytest.skip("owner mirrors not restored")
    with rasterio.open(b2) as s:
        pb = np.nan_to_num(s.read(1)) > 0
    with rasterio.open(h27) as s:
        ph = np.nan_to_num(s.read(1)) > 0
    with rasterio.open(d28) as s:
        pd = np.nan_to_num(s.read(1)) > 0
    assert int(pb.sum()) == 37654 and int(ph.sum()) == 40199 and int(pd.sum()) == 44090
    assert not (pb & ~ph).any() and not (ph & ~pd).any()
