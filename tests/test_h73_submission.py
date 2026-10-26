"""Locks the 2026-10-26 H73-PM session: run card <-> analysis <-> registry <-> GeoTIFFs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "registry" / "run_card_h73_2026-10-26.json").read_text())
SUBS = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
H73 = next(s for s in SUBS if s["id"] == "h73-pm-deapron")
H73_NAN = next(s for s in SUBS if s["id"] == "h73-pm-deapron-nan")
ANA = json.loads((ROOT / "evidence" / "h73_pm_screen" / "analysis.json").read_text())


def test_h73_registry_matches_run_card_and_is_negative() -> None:
    assert H73["sha256"] == CARD["raster_sha256"]
    assert H73_NAN["sha256"] == CARD["nan_twin_sha256"]
    assert H73["content_id"] == H73_NAN["content_id"] == CARD["content_id"] == "1b7533ebb62b"
    assert H73["positive_pixels"] == H73_NAN["positive_pixels"] == CARD["positive_pixels"] == 42997
    assert H73["note"] == CARD["note"] and len(H73["note"]) <= 140
    assert "DO NOT SUBMIT" in H73["note"] and "unscored" in H73["note"]
    assert CARD["verdict"] == H73["verdict"] == "negative"
    assert H73["ok_to_download"] is True
    assert H73["ok_to_submit_slot"] is False and H73["slot_approved"] is False
    assert "DO NOT SUBMIT" in H73["status"]
    assert CARD["organizer_confirmed_score"] is None


def test_h73_gates_failed_and_canaries_passed() -> None:
    assert ANA["slot_gate"]["passed"] is False
    assert ANA["far_field_screen"]["passed"] is False
    assert ANA["slot_gate"]["paired_gain"] < 0 and ANA["slot_gate"]["paired_ci95"][1] < 0
    # PM still beats the catalogue-free control far-field (the recorded positive sub-result)
    assert ANA["far_field_screen"]["pooled_far_gain_vs_blind"] > 0
    assert ANA["far_field_screen"]["folds_positive_vs_blind"] >= 3
    assert ANA["canary"]["max_canary_auc"] <= 0.90
    h = CARD["holdout_dti"]
    assert h["label"] == "HOLDOUT-DTI" and h["withheld_positive_occurrences"] == 22290
    assert h["slot_gate_passed"] is False and h["far_field_screen_passed"] is False
    # de-biased geometry is B2-like, unlike the H35 control's apron profile
    assert ANA["per_arm"]["PM_DEAPRON"]["mean_frac_gt20"] >= 0.35
    assert ANA["per_arm"]["CTRL_H35"]["mean_frac_2_9"] > 0.5


def test_h73_format_and_lane_receipts() -> None:
    az = json.loads((ROOT / "evidence" / "h73_independent_audit_zeros.json").read_text())
    an = json.loads((ROOT / "evidence" / "h73_independent_audit_nan.json").read_text())
    assert az["all_hard_checks_pass"] is True and an["all_hard_checks_pass"] is True
    assert az["checks"]["footprint_no_nan_or_inf"] is True
    assert az["checks"]["footprint_in_0_1"] is True
    assert az["checks"]["zero_known_catalogue_overlap"] is True
    lane = CARD["correlation_overlap_vs_registry"]
    assert lane["flagged_lane"] == []  # density-aware unique
    assert lane["flagged_literal"] == ["13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"]
    assert lane["surface_worst_abs_spearman"] <= 0.90
    assert lane["focus_winners"]["b2_overlap"] <= 0.70
    assert lane["focus_winners"]["worst_cand_dots_within_3px"] <= 0.70
    assert lane["own_lineage"]["worst_cand_dots_within_3px"] <= 0.70
