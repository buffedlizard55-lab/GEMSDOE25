from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "registry/run_card_review_61f81983_2026-10-26.json").read_text())
AUDIT = json.loads((ROOT / "evidence/download_audit_61f81983_2026-10-26.json").read_text())
FOCUS = json.loads((ROOT / "evidence/focus_audit_local_2026-10-26.json").read_text())


def test_review_run_card_is_explicitly_negative_and_does_not_invent_a_new_result() -> None:
    assert CARD["experiments"]["run_this_session"] == 0
    assert CARD["experiments"]["weekly_slot_used"] is False
    assert CARD["hypothesis"] is None
    assert CARD["holdout_dti"] is None
    assert CARD["new_raster"]["created"] is False
    assert CARD["new_raster"]["file"] is None
    assert CARD["new_raster"]["sha256"] is None
    assert CARD["new_raster"]["submission_note"] is None
    assert CARD["new_raster"]["promotion"] is False


def test_prior_h72_file_is_format_valid_but_fails_performance_and_literal_lane() -> None:
    ref = CARD["prior_candidate_reference"]
    assert ref["format_validator"]["format_valid"] is True
    assert ref["format_validator"]["okay_to_submit"] is False
    assert ref["prior_holdout_dti"]["label"] == "HOLDOUT-DTI"
    assert ref["prior_holdout_dti"]["withheld_positive_occurrences"] == 22334
    assert ref["prior_holdout_dti"]["pooled_dti"] < ref["prior_holdout_dti"]["same_run_h35_pooled_dti"]
    lane = ref["prior_lane_audit"]
    assert lane["surface_rank_gate_pass"] and lane["final_rank_gate_pass"]
    assert lane["max_final_dots_within_3px_sparse_registry"] > lane["strict_overlap_limit"]
    assert lane["final_dots_within_3px_r13_lattice"] == 1.0
    assert lane["strict_literal_lane_pass"] is False


def test_focus_winner_overlap_and_exact_mask_facts_remain_distinct() -> None:
    expected = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}
    assert set(FOCUS["pairwise_3px_forward_overlap"]) == expected
    for site, row in FOCUS["pairwise_3px_forward_overlap"].items():
        shares = [value for peer, value in row.items() if peer != site]
        assert max(shares) > 0.70, site
    identities = FOCUS["identities"]
    assert identities["g25_d28_mask_equals_g30"] is True
    assert identities["g28_r1_mask_equals_g31"] is True
    assert identities["b2_equals_d28_and_distcat_gt_2"] is True
    assert identities["g36_extra_over_b2"] == 1200


def test_download_audit_keeps_format_separate_from_authorization() -> None:
    assert AUDIT["summary"]["tif_files_audited"] == 46
    assert AUDIT["summary"]["format_valid"] == 46
    assert AUDIT["summary"]["okay_to_submit"] is False
    artifact = AUDIT["target_existing_artifact"]
    assert artifact["format_valid"] is True
    assert artifact["okay_to_submit"] is False
    assert artifact["positive_pixels"] == 41061
    assert artifact["in_footprint_min_max"] == [0.0, 1.0]


def test_current_pages_separate_research_download_from_competition_eligibility() -> None:
    for rel in ("index.html", "docs/index.html", "docs/current-review.html", "docs/executive-summary.html"):
        page = (ROOT / rel).read_text()
        assert "Research-archive download" in page, rel
        assert "Competition-ready" in page, rel
        assert "DO NOT SUBMIT" in page, rel
        assert "H35 FAIL · STRICT LANE FAIL" in page, rel
        assert "H35 FAIL · UNIQUE LANE" not in page, rel
    readme = (ROOT / "README.md").read_text()
    assert "Research-archive download: YES (inspection/testing only)" in readme
    assert "NO NEW COMPETITION TIFF" in readme
    assert "Competition-ready TIF: NO" in readme
    report = (ROOT / "knowledge/32_repo_review_2026-10-26_61f81983.md").read_text()
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert site in report
    assert "0.4413" in report and "0.3195" in report
