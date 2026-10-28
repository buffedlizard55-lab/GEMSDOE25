"""Regression checks for the 2026-10-28 audit, score retraction and submit-safety copy."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str):
    return json.loads((ROOT / path).read_text())


def test_nine_site_table_covers_all_requested_sites_and_never_promotes_archive():
    audit = read_json("evidence/h80_focus_winners_reaudit_2026-10-28.json")
    assert {row["site"] for row in audit["sites"]} == {
        f"GEMSDOE{n}" for n in (24, 25, 27, 28, 30, 31, 32, 33, 36)
    }
    assert max(audit["sites"], key=lambda r: r["owner_reported_score"])["site"] == "GEMSDOE32"
    assert max(audit["sites"], key=lambda r: r["owner_reported_score"])["owner_reported_score"] == 0.2778
    page = (ROOT / "docs/executive-summary.html").read_text()
    for site in (24, 25, 27, 28, 30, 31, 32, 33, 36):
        assert f"GEMSDOE{site}" in page
    assert "Estimated new-submission score" in page
    assert "UNKNOWN — no calibrated estimate" in page
    assert "OWNER-REPORTED · no organizer receipt" in page
    assert "NO — historical file" in page
    assert "exact positive-mask duplicate of GEMSDOE30 (D2.8)" in page
    assert "exact positive-mask duplicate of GEMSDOE25 (D2.8)" in page


def test_h81_public_score_band_is_retracted_and_score_is_not_estimated():
    page = (ROOT / "docs/h81-executive-brief.html").read_text()
    assert "NEW-SUBMISSION SCORE: NOT ESTIMATED" in page
    assert "0.2250–0.2250" not in page
    assert "0.2708–0.2778" not in page
    gated = read_json("evidence/h81_score_estimate_gated.json")
    assert gated["empirical_band"]["n_matched"] == 0
    card = read_json("registry/run_card_h81_2026-10-28.json")
    assert card["estimated_competition_score"] is None
    assert card["submission"]["ok_to_submit_slot"] is False


def test_review_run_card_is_negative_and_has_required_provenance_labels():
    path = ROOT / "knowledge/47_repo_review_2026-10-28.md"
    text = path.read_text()
    assert text.endswith("```\n")
    assert "Three review passes completed" in text
    assert "not fetched in this sandbox" in text
    block = re.findall(r"```json\n(.*?)\n```", text, flags=re.S)
    assert len(block) == 1
    card = json.loads(block[0])
    assert card == read_json("registry/run_card_repo_review_2026-10-28.json")
    passes = read_json("registry/review_passes_repo_review_2026-10-28.json")
    assert len(passes["passes"]) == 3 and passes["verdict"].startswith("negative")
    assert card["verdict"] == "negative"
    assert card["holdout_dti"]["label"] == "HOLDOUT-DTI"
    assert card["holdout_dti"]["withheld_positive_occurrences"] == 95188
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["validator_output"]["values_in_0_1"] is None
    assert len(card["submission_note"]) <= 140


def test_no_outdated_score_promotion_or_live_score_claim_in_start_pages():
    for rel in ("index.html", "docs/index.html", "docs/current-review.html", "docs/executive-summary.html", "docs/h81-executive-brief.html"):
        text = (ROOT / rel).read_text()
        assert "0.2250–0.2250" not in text
        assert "0.2708–0.2778" not in text
        assert "OK TO SUBMIT: YES" not in text
    readme = (ROOT / "README.md").read_text()
    assert "are **retracted**" in readme and "New-submission score: NOT ESTIMATED" in readme
    assert "OK TO SUBMIT: YES" not in readme
    for rel in ("docs/index.html", "docs/current-review.html", "docs/executive-summary.html", "docs/history.html", "docs/research.html", "docs/sources.html", "docs/submission-guide.html", "docs/submission-history.html"):
        text = (ROOT / rel).read_text()
        assert ("New-submission score: NOT ESTIMATED" in text
                or "New-submission score: <b>UNKNOWN / NOT ESTIMATED</b>" in text
                or "Estimated competition score: <b>UNKNOWN / NOT ESTIMATED</b>" in text
                or "no new-submission score is estimated" in text)


def test_review_file_links_resolve():
    html = (ROOT / "docs/h81-executive-brief.html").read_text()
    for href in re.findall(r'(?:href|src)="([^"#?]+)', html):
        parts = urlsplit(href)
        if parts.scheme or parts.netloc:
            continue
        assert (ROOT / "docs" / parts.path).resolve().exists(), href
