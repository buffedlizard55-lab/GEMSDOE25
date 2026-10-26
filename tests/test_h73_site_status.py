from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = ROOT / "registry/run_card_h73_2026-10-26.json"
RUN_CARD = json.loads(CARD_PATH.read_text())


def test_h73_is_prominent_but_explicitly_not_submission_eligible() -> None:
    for rel in ("index.html", "docs/index.html", "docs/current-review.html", "docs/executive-summary.html"):
        page = (ROOT / rel).read_text()
        assert "OK TO SUBMIT: NO — DO NOT SUBMIT" in page, rel
        assert "COMPETITION-READY TIF: NO" in page, rel
        assert "HOLDOUT-DTI 0.11343 vs same-run CTRL_H35 0.15239" in page, rel
        assert "literal uniqueness gate fails" in page, rel
        assert "Estimated competition score: UNKNOWN (not calibrated)" in page, rel
        assert page.index("H73-PM-2026-10-26") < page.index("PRIOR H72-3 ARCHIVE"), rel


def test_h73_status_matches_saved_run_card_and_strict_lane_receipt() -> None:
    holdout = RUN_CARD["holdout_dti"]
    assert RUN_CARD["verdict"] == "negative"
    assert RUN_CARD["ok_to_submit_slot"] is False
    assert RUN_CARD["organizer_confirmed_score"] is None
    assert holdout["slot_gate_passed"] is False
    lane = json.loads((ROOT / "evidence/h73_lane_extended.json").read_text())
    lattice = lane["lattice"][0]
    assert lattice["cand_dots_within_3px"] == 1.0
    assert lane["thresholds"]["dots_within_3px_max"] == 0.70
    assert lattice["file"] in RUN_CARD["correlation_overlap_vs_registry"]["flagged_literal"]


def test_h73_existing_tif_is_content_hashed_and_note_is_short() -> None:
    artifact = ROOT / "docs/downloads" / RUN_CARD["submission_name"]
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == RUN_CARD["raster_sha256"]
    assert len(RUN_CARD["note"]) <= 140
    assert RUN_CARD["ok_to_submit_slot"] is False


def test_review_run_card_is_negative_preflight_not_a_zero_score() -> None:
    card = json.loads((ROOT / "registry/run_card_current_session_2026-10-26.json").read_text())
    assert card["verdict"] == "negative"
    assert card["experiments_used"] == 0
    assert card["new_raster_created"] is False
    assert card["cache_status"]["scientific_python_dependencies_present"] is True
    assert card["cache_status"]["required_cached_feature_stack_present"] is False
    assert card["holdout_dti"] is None
    assert card["estimated_leaderboard_score"] is None
    assert card["prior_artifact_holdout_dti"]["label"] == "HOLDOUT-DTI"
    assert card["prior_artifact_holdout_dti"]["gate_passed"] is False
    assert card["correlation_overlap_vs_registry"]["strict_lane_clear"] is False


def test_review_table_covers_all_focus_sites_and_reports_unknown_estimates() -> None:
    report = (ROOT / "knowledge/34_current_session_review_2026-10-26.md").read_text()
    for site in (24, 25, 27, 28, 30, 31, 32, 33, 36):
        assert f"GEMSDOE{site}" in report
    assert "Estimated leaderboard score for a genuinely new file" in report
    assert "NOT ESTIMABLE" in report
    assert "Unique under strict literal lane?" in report
    assert "OK to download / submit?" in report
    assert "USGS 3DEP" in report and "blocked, not viable yet" in report
