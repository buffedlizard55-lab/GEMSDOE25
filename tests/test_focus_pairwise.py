"""Pins the focus-site novelty decision to reproducible hash-backed geometry evidence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = json.loads((ROOT / "evidence" / "focus_pairwise_overlap_2026-10-26.json").read_text())


def test_all_nine_focus_winners_fail_the_literal_pairwise_overlap_gate() -> None:
    expected = {f"GEMSDOE{n}" for n in (24, 25, 27, 28, 30, 31, 32, 33, 36)}
    assert set(AUDIT["focus_winners"]) == expected
    for site, row in AUDIT["focus_winners"].items():
        assert row["owner_reported_dti"] is not None
        assert row["max_cross_site_candidate_dot_share_within_3px"] > 0.70, site
        assert row["strict_lane_unique_vs_all_other_focus_winners"] is False
        assert row["sha256"] and len(row["sha256"]) == 64


def test_exact_duplicate_and_near_duplicate_are_distinguished() -> None:
    pairs = {
        frozenset((row["site_a"], row["site_b"]))
        for row in AUDIT["exact_prediction_mask_duplicate_pairs"]
    }
    assert pairs == {frozenset(("GEMSDOE25", "GEMSDOE30"))}
    assert AUDIT["focus_winners"]["GEMSDOE32"]["exact_mask_match_sites"] == []
    assert AUDIT["focus_winners"]["GEMSDOE32"]["max_cross_site_candidate_dot_share_within_3px"] > 0.70


def test_h71_is_unique_within_focus_list_but_fails_global_literal_lane() -> None:
    candidate = AUDIT["h71_candidate"]
    assert candidate["unique_vs_all_nine_focus_winners_under_70pct_rule"] is True
    assert candidate["max_focus_site_dot_share_within_3px"] <= 0.70
    assert candidate["surface_max_abs_spearman_vs_available_registry"] <= 0.90
    assert candidate["strict_global_registry_lane_clear"] is False
    assert candidate["strict_global_registry_lane_stop"]["candidate_dots_within_3px_of_registry_dots"] == 1.0
    assert candidate["holdout_dti"]["evaluator_version"] == "gems25.holdout.v1.2-buffered-4quad-pooled-dti"
    assert candidate["holdout_dti"]["withheld_positives"] == 21835
    assert candidate["verdict"].endswith("DO NOT SUBMIT")


def test_focus_pairwise_report_does_not_relabel_scores() -> None:
    assert "does not verify any competition score" in (ROOT / "scripts" / "audit_focus_pairwise.py").read_text()
    assert "OWNER-REPORTED" in AUDIT["score_caveat"]
    assert all(row["owner_reported_dti"] is not None for row in AUDIT["focus_winners"].values())


def test_current_review_has_no_eligible_tif_and_table_preserves_provenance() -> None:
    page = (ROOT / "docs" / "current-review.html").read_text()
    assert "Executive comparison — strongest supplied artifact for each focus site" in page
    assert "Competition-download deliverable: NOT AVAILABLE" in page
    assert "OK TO SUBMIT: NO" in page and "DO NOT SUBMIT" in page
    assert "HOLDOUT-DTI" in page
    assert "No current live score or score projection is available" in page
    assert AUDIT["h71_candidate"]["file"] in page
    assert "OWNER-REPORTED DTI" in page
    assert "GEMSDOE32" in page and "GEMSDOE36" in page
    assert f'href="downloads/{AUDIT["h71_candidate"]["file"]}"' not in page
