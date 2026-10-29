"""Regression checks for the 2026-10-29 review artefacts (no network, no DrivenData)."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECHECK = ROOT / "evidence" / "portal_file_recheck_2026-10-29.json"


def _load():
    return json.loads(RECHECK.read_text())["files"]


def test_recheck_pairs_nan_fails_zeros_passes():
    rows = _load()
    assert rows, "recheck file has no rows"
    for r in rows:
        if r["file"].endswith("-nan.tif"):
            assert r["nan_cells"] > 0
            assert r["portal_range_pass"] is False
        elif r["file"].endswith("-zeros.tif"):
            assert r["nan_cells"] == 0
            assert r["portal_range_pass"] is True
            assert 0.0 <= r["finite_min"] and r["finite_max"] <= 1.0
        assert r["epsg"] == 32611
        assert r["shape"] == [3730, 3292]
        assert r["dtype"] == "float32"
        assert len(r["sha256"]) == 64


def test_recheck_matches_files_on_disk():
    import hashlib

    for r in _load():
        path = ROOT / "docs" / "downloads" / r["file"]
        if not path.exists():
            pytest.skip("download not present")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == r["sha256"]


def test_ir29_entries_present_and_open():
    d = json.loads((ROOT / "registry" / "irregularities.json").read_text())
    by_id = {i["id"]: i for i in d["issues"]}
    for key in [
        "IR-29-LEADERBOARD-CONFLICT",
        "IR-29-NAN-DEFAULT-DOWNLOAD",
        "IR-29-NINE-SITE-SCORES-OWNER-ONLY",
        "IR-29-LANE-RULE-UNSATISFIABLE-AT-BUDGET",
        "IR-29-ZEROS-NOT-ORGANIZER-CONFIRMED",
    ]:
        assert key in by_id, key
        assert by_id[key]["status"] == "open"


def test_readme_states_no_submission_cleared():
    text = (ROOT / "README.md").read_text()
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in text
    assert "knowledge/48_session_review_2026-10-29.md" in text
