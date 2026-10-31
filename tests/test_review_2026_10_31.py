"""Regression guards for the 31 Oct 2026 current review."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_latest_review_says_no_submission_is_cleared():
    page = (ROOT / "docs" / "review-2026-10-31.html").read_text(encoding="utf-8")
    index = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in page
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in index
    assert "NOT ESTIMATED" in page
    assert "review-2026-10-31.html" in index
    assert "docs/review-2026-10-31.html" in readme


def test_run_card_is_negative_and_has_no_unverified_score():
    card = json.loads((ROOT / "registry" / "run_card_session_2026-10-31.json").read_text(encoding="utf-8"))
    assert card["verdict"] == "negative"
    assert card["holdout_dti"]["pooled_value"] is None
    assert card["raster_sha256"] is None
    assert card["submission"]["name"] is None
    assert card["score_context"]["new_candidate_score_estimate"] == "NOT ESTIMATED"


def test_focus_site_rows_are_not_misrepresented_as_new_candidates():
    page = (ROOT / "docs" / "review-2026-10-31.html").read_text(encoding="utf-8")
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert site in page
    assert "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif" in page
    assert "gems24-h25-1-dotted-h19-5-d2-8-…-nan.tif" not in page
    assert "NO — previous" in page
