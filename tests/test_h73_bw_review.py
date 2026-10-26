import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_h73_bw_run_card_fails_closed_with_unknown_metrics_null():
    card = json.loads((ROOT / "registry/run_card_h73_bw_2026-10-26.json").read_text())
    metrics = card["holdout_dti"]
    assert card["status"] == "blocked_before_fit"
    assert card["conditional_decision"]["decision"] == "go_for_one_evaluation_only_diagnostic"
    assert card["conditional_decision"]["condition_met"] is True
    assert card["conditional_decision"]["basis"]["stronger_h73_pm_screen_passed"] is False
    assert metrics["label"] == "HOLDOUT-DTI"
    assert metrics["withheld_positive_occurrences"] is None
    assert metrics["pooled_candidate_dti"] is None
    assert metrics["candidate_ci95"] is None
    assert metrics["selector_gate_passed"] is None
    assert card["organizer_confirmed_score"] is None and card["score_projection"] is None
    assert card["raster_sha256"] is None and card["submission_name"] is None
    assert card["slot_approved"] is False and card["ok_to_submit_slot"] is False
    assert card["model_fit_performed"] is False


def test_h73_bw_preflight_and_site_report_all_eight_missing_caches():
    receipt = json.loads((ROOT / "evidence/h73_bw_preflight_2026-10-26.json").read_text())
    page = (ROOT / "docs/current-review.html").read_text()
    pm_card = json.loads((ROOT / "registry/run_card_h73_2026-10-26.json").read_text())
    assert receipt["status"] == "blocked_before_fit"
    assert len(receipt["errors"]) == 8
    assert all(error.startswith("missing:") for error in receipt["errors"])
    assert receipt["auto_restore_performed"] is False
    assert receipt["feature_build_performed"] is False
    assert receipt["h34_loader_called"] is False
    assert receipt["model_fit_performed"] is False
    assert "H73-BW BLOCKED BEFORE FIT" in page
    assert "H73-BW diagnostic candidate: <b>no file produced</b>" in page
    assert "NO — DO NOT SUBMIT" in page
    assert "NOT ESTIMATED" in page
    assert pm_card["submission_name"] in page
    assert "inspection-only" in page
