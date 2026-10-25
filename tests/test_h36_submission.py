"""Automated gates for the 2026-10-25 H36/H37 deliverable: download/slot labels follow evidence files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUBS = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
# H36 artifact by id (featured primary on its session branch; an alternate after the main merge featured XG1)
PRIMARY = next(s for s in SUBS if s["id"] == "h36-tzc")
CARD = json.loads((ROOT / "registry" / "run_card_h36_h37_2026-10-25.json").read_text())
RECEIPT = json.loads((ROOT / "docs" / "downloads" / PRIMARY["receipt"]).read_text())


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_primary_is_h36_and_files_match_registry():
    assert PRIMARY["id"] == "h36-tzc" and PRIMARY["content_id"] in PRIMARY["file"]
    for s in SUBS:
        if s["role"] in ("primary", "fallback"):
            p = ROOT / s["path"]
            assert p.exists() and sha256(p) == s["sha256"] and p.stat().st_size == s["bytes"]
    assert (ROOT / "docs" / "downloads" / PRIMARY["zip"]).exists()


def test_note_and_labels_say_no_slot():
    assert len(PRIMARY["note"]) <= 120
    assert all(t in PRIMARY["note"] for t in ("no slot", "unscored", "not slot-approved"))
    assert RECEIPT["note"] == PRIMARY["note"]
    assert CARD["note"] == PRIMARY["note"] and CARD["raster"]["sha256"] == PRIMARY["sha256"]
    assert PRIMARY["ok_to_download"] is True and PRIMARY["ok_to_submit_slot"] is False
    assert PRIMARY["slot_approved"] is False and PRIMARY["verdict"] == CARD["verdict"] == "negative"
    assert "DO NOT SUBMIT" in PRIMARY["status"]


def test_holdout_gates_recompute_negative():
    for exp, key in ((CARD["experiments"][0], "primary_TZC_vs_BEST"),):
        assert exp["gate_passed"] is False
    scr = json.loads((ROOT / "evidence/h36_screen/analysis.json").read_text())
    seis = json.loads((ROOT / "evidence/h37_screen/analysis.json").read_text())
    assert scr["gate"]["passed"] is False and scr["primary_TZC_vs_BEST"]["folds_positive"] == 2
    assert seis["gate"]["passed"] is False and seis["primary_SEIS_vs_BEST"]["folds_positive"] == 1
    assert scr["leakage_canary"]["passed"] and seis["leakage_canary"]["passed"]
    assert CARD["holdout_dti"]["label"] == "HOLDOUT-DTI"


def test_strict_lane_is_recorded_as_duplicate_stop():
    lane = json.loads((ROOT / "docs/downloads" / f"lane-{Path(PRIMARY['file']).stem}.json").read_text())
    assert lane["verdict"].startswith("DUPLICATE")
    assert PRIMARY["lane"]["lane_clear"] is False
    assert PRIMARY["lane"]["lattice_overlap"] > 0.70
    assert PRIMARY["lane"]["worst_other_registry_overlap"] > 0.70  # own-lineage H35/H31 overlap


def test_primary_revalidates_independently():
    from gems25.paths import data_dir

    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("competition template not restored (run scripts/restore_data.py)")
    from gems25.submission import check_file

    r = check_file(ROOT / PRIMARY["path"], tmpl)
    assert r["ok_to_upload"], r["hard_failures"]
    assert r["positive_pixels"] == PRIMARY["positive_pixels"] == 48634
