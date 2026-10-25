"""Locks the 2026-10-25 H66 MGD-F + SGMC-REACT session: Run Card <-> analyses <-> registry <-> GeoTIFFs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "registry" / "run_card_h66_2026-10-25.json").read_text())
SUBS = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
PRIMARY = next(s for s in SUBS if s["role"] == "primary")
NAN_TWIN = next(s for s in SUBS if s["id"] == "h66-mgd-flank-nan")


def test_h66_primary_and_run_card_invariants() -> None:
    assert PRIMARY["id"] == "h66-mgd-flank"
    assert PRIMARY["sha256"] == CARD["tif"]["sha256"]
    assert NAN_TWIN["sha256"] == CARD["tif"]["nan_twin_sha256"]
    assert PRIMARY["content_id"] == NAN_TWIN["content_id"] == CARD["tif"]["content_id"] == "da617550a0e9"
    assert PRIMARY["positive_pixels"] == NAN_TWIN["positive_pixels"] == 44832
    assert PRIMARY["note"] == CARD["tif"]["note"]
    assert len(PRIMARY["note"]) <= 120
    assert CARD["verdict"] == "negative"
    assert PRIMARY["verdict"] == "negative"
    assert PRIMARY["ok_to_download"] is True
    assert PRIMARY["ok_to_submit_slot"] is False
    assert PRIMARY["slot_approved"] is False
    assert "DO NOT SUBMIT" in PRIMARY["status"]


def test_h66_three_experiments_match_analyses() -> None:
    s1 = json.loads((ROOT / "evidence" / "h66_1_screen" / "analysis.json").read_text())
    c1 = json.loads((ROOT / "evidence" / "h66_1_confirm" / "analysis.json").read_text())
    s2 = json.loads((ROOT / "evidence" / "h66_2_screen" / "analysis.json").read_text())
    e1 = CARD["experiments"]["experiment_1_h66_1_screen"]
    e2 = CARD["experiments"]["experiment_2_h66_1_confirm"]
    e3 = CARD["experiments"]["experiment_3_h66_2_sgmc_react_screen"]

    assert e1["gate"]["passed"] is True and s1["gate"]["passed"] is True
    assert e2["gate"]["passed"] is False and c1["gate"]["passed"] is False
    assert e3["gate"]["passed"] is True and s2["gate"]["passed"] is True

    for exp, ana in ((e1, s1), (e2, c1), (e3, s2)):
        assert exp["leakage_canary"]["passed"] is True
        assert exp["leakage_canary"]["max_feature_auc"] <= 0.90
        assert abs(exp["gate"]["mean_gain"] - ana["gate"]["mean_gain"]) < 1e-12

    # Factor C (tip-preserved flank shielding) was positive in 4/4 screen AND 4/4 confirmation fold-blocks (8/8 total)
    assert s1["factorial_2x2"]["C_main"]["folds_positive"] == 4
    assert c1["factorial_2x2"]["C_main"]["folds_positive"] == 4


def test_h66_independent_audit_and_lane_checks() -> None:
    az = json.loads((ROOT / "evidence" / "h66_independent_audit_zeros.json").read_text())
    an = json.loads((ROOT / "evidence" / "h66_independent_audit_nan.json").read_text())
    lane = json.loads((ROOT / "evidence" / "h66_lane_extended.json").read_text())
    f9 = json.loads((ROOT / "evidence" / "h66_focus_sites_forensics.json").read_text())

    assert az["all_hard_checks_pass"] is True and an["all_hard_checks_pass"] is True
    assert az["checks"]["strict_whole_array_0_le_x_le_1"] is True
    assert az["checks"]["footprint_values_in_0_1"] is True
    assert az["checks"]["footprint_all_finite"] is True
    assert az["checks"]["no_emission_on_catalogue"] is True
    assert az["zip"]["contains_exactly_candidate_bytes"] is True

    assert lane["sha256"] == PRIMARY["sha256"]
    assert CARD["registry_correlation_and_overlap"]["surface_max_abs_spearman"] <= 0.90
    assert CARD["registry_correlation_and_overlap"]["focus_21_top_scorers"]["worst_cand_dots_within_3px"] <= 0.70
    assert lane["lattice"][0]["cand_dots_within_3px"] > 0.70

    assert all(
        f9["identities"][k] is True
        for k in (
            "d28_g25_equals_d28_g30",
            "r1_g28_equals_r1_g31",
            "r1_is_exact_d28_gt_1px",
            "b2_is_exact_r1_gt_2px",
            "g36_is_exact_superset_of_b2_plus_1200",
        )
    )


def test_h66_tifs_revalidate_live_when_template_present() -> None:
    import pytest

    from gems25.paths import data_dir
    from gems25.submission import check_file

    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("competition template not restored")
    for entry in (PRIMARY, NAN_TWIN):
        res = check_file(ROOT / entry["path"], tmpl)
        assert res["ok_to_upload"] is True, res["hard_failures"]
        assert res["positive_pixels"] == 44832
        assert res["sha256"] == entry["sha256"]

