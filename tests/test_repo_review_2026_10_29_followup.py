"""Safety and provenance regression checks for the 29 Oct repository review."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOCUS = {f"GEMSDOE{n}" for n in (24, 25, 27, 28, 30, 31, 32, 33, 36)}


def test_followup_review_keeps_all_focus_sites_and_no_submit_status():
    review = (ROOT / "knowledge/52_repo_review_2026-10-29.md").read_text()
    for site in FOCUS:
        assert site in review
    assert "UNKNOWN / NOT ESTIMATED" in review
    assert "Do not submit any GeoTIFF" in review
    assert "exact positive-pixel set equals GEMSDOE30" in review
    assert "exact positive-pixel set equals GEMSDOE25" in review
    assert "not proof" in review


def test_run_card_does_not_claim_a_new_raster_or_valid_holdout():
    card = json.loads((ROOT / "registry/run_card_repo_review_2026-10-29.json").read_text())
    assert card["verdict"] == "negative"
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["validator_output"]["values_in_0_1"] is None
    assert "INVALID" in card["holdout_dti"]["class"]
    assert card["holdout_dti"]["withheld_positive_occurrences"] == 23923
    assert len(card["submission_note"]) <= 140


def test_restore_receipt_is_mirror_integrity_not_provenance_claim():
    receipt = json.loads((ROOT / "evidence/data_restore_audit_2026-10-29.json").read_text())
    assert receipt["verified_count"] == receipt["file_count"] == 22
    assert receipt["unverified_count"] == 0
    assert "not organizer provenance" in receipt["evidence_class"]
    assert receipt["cache_ready"] is False
    assert all(not cache["present"] for cache in receipt["shared_feature_cache"])


def test_readme_active_brief_points_to_this_review_and_warns_no_submit():
    readme = (ROOT / "README.md").read_text()
    active = readme[: readme.index("## 29 October 2026 — audit correction")]
    assert "knowledge/52_repo_review_2026-10-29.md" in active
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in active
    assert "normalized from this session" in active
