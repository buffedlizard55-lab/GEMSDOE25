"""Current review: source identities, strict stop, retractions, and public status."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.build_current_review import readme_status, render_body

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text())


def test_current_run_card_is_one_honest_negative_result():
    card = read("registry/run_card_2026-10-27.json")
    assert card["verdict"] == "negative" and card["experiments_fitted"] == 0
    assert card["new_raster_created"] is False and card["slot_selected_or_used"] is False
    assert card["submission_name"] is None and card["raster_sha256"] is None
    assert card["holdout_dti"]["pooled_dti"] is None
    assert card["holdout_dti"]["confidence_interval_95"] is None
    assert card["holdout_dti"]["withheld_positive_occurrences"] is None
    assert card["estimated_organizer_score"] is None
    assert len(card["submission_note"]) <= 140
    assert card["previous_h78_reaudit"]["okay_to_submit"] is False


def test_frozen_preflight_reproduces_pigeonhole_bound():
    card = read("registry/run_card_2026-10-27.json")
    pre = read("evidence/lane_preflight_2026-10-27.json")
    assert pre["preregistration_commit"] == card["preregistration_commit"]
    g = card["correlation_overlap_vs_registry"]["geometric_preflight"]
    assert g["minimum_forced_overlap_pixels"] == g["preregistered_dot_budget"] - g["eligible_pixels_outside_3px_halo"]
    assert g["minimum_forced_overlap_fraction"] == g["minimum_forced_overlap_pixels"] / g["preregistered_dot_budget"]
    assert g["minimum_forced_overlap_fraction"] > 0.7
    assert pre["experiments"] == 0 and pre["new_tiff_generated"] is False and pre["okay_to_submit"] is False


def test_nine_winners_use_correct_highest_supplied_raster_and_source():
    audit = read("evidence/focus_winners_reaudit_2026-10-27.json")
    winners = {s["site"]: s for s in audit["sites"]}
    assert set(winners) == {f"GEMSDOE{x}" for x in (24, 25, 27, 28, 30, 31, 32, 33, 36)}
    assert max(winners.values(), key=lambda x: x["owner_reported_score"])["site"] == "GEMSDOE32"
    assert winners["GEMSDOE32"]["owner_reported_score"] == 0.2778
    assert winners["GEMSDOE28"]["owner_reported_score"] == 0.2710
    assert "rung30" in winners["GEMSDOE28"]["file"]
    assert audit["identities"]["gems28_winner_equals_gems31"] is False
    assert audit["identities"]["gems28_lower_scoring_r1_equals_gems31"] is True
    assert audit["identities"]["b2_equals_d28_pruned_distance_le_2"] is True
    assert audit["identities"]["d28_pixels_removed_b2"] == 6436
    assert all(s["score_class"].startswith("OWNER-REPORTED") and s["slot_approved"] is False for s in winners.values())
    links = read("evidence/focus_source_links_2026-10-27.json")
    assert len(links["results"]) == 9 and all(r["matches"] for r in links["results"])
    assert links["organizer_authenticity_verified"] is False


def test_generator_and_published_pages_do_not_repromote_h78():
    for text in (readme_status(), render_body(), render_body(root_page=True)):
        assert "DO NOT SUBMIT" in text and "82.70%" in text
        assert "0.2785" not in text and "OK TO SUBMIT: YES" not in text
    for path in ("README.md", "index.html", "docs/index.html", "docs/current-review.html", "docs/executive-summary.html"):
        text = (ROOT / path).read_text()
        assert "DO NOT SUBMIT" in text and "82.70%" in text
        assert "0.2785" not in text and "OK TO SUBMIT: YES" not in text
    receipt = read("docs/downloads/checks-gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.json")
    assert receipt["ok_to_submit"] is False and receipt["estimated_competition_score"] is None
    assert receipt["flagged_duplicates"]


def test_original_prompt_preserved_and_latest_archive_not_claimed_verbatim():
    text = (ROOT / "README.md").read_text()
    brief = (ROOT / "knowledge/owner_brief_verbatim.txt").read_text().strip()
    assert brief in text
    assert "Current 2026-10-27 session scope — condensed, not verbatim" in text
