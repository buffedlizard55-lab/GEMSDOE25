"""Locks the 2026-10-26 H71 HGPC-BLIND session: run card <-> analyses <-> registry <-> GeoTIFFs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "registry" / "run_card_h71_2026-10-26.json").read_text())
SUBS = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
PRIMARY = next(s for s in SUBS if s["role"] == "primary")
NAN_TWIN = next(s for s in SUBS if s["id"] == "h71-hgpc-blind-nan")


def test_h71_is_featured_primary_and_matches_run_card() -> None:
    assert PRIMARY["id"] == "h71-hgpc-blind"
    assert PRIMARY["sha256"] == CARD["tif"]["sha256"]
    assert NAN_TWIN["sha256"] == CARD["tif"]["nan_twin_sha256"]
    assert PRIMARY["content_id"] == NAN_TWIN["content_id"] == CARD["tif"]["content_id"] == "9eb0c31e5149"
    assert PRIMARY["positive_pixels"] == NAN_TWIN["positive_pixels"] == 59472
    assert PRIMARY["note"] == CARD["tif"]["note"]
    assert len(PRIMARY["note"]) <= 120
    assert "no slot" in PRIMARY["note"] and "unscored" in PRIMARY["note"] and "not slot-approved" in PRIMARY["note"]
    assert CARD["verdict"] == "negative"
    assert PRIMARY["verdict"] == "negative"
    assert PRIMARY["ok_to_download"] is True
    assert PRIMARY["ok_to_submit_slot"] is False
    assert PRIMARY["slot_approved"] is False
    assert "DO NOT SUBMIT" in PRIMARY["status"]
    assert "strict lane" in PRIMARY["summary"].lower()


def test_h71_three_experiments_all_fail_vs_h35_and_beat_crest() -> None:
    s1 = json.loads((ROOT / "evidence" / "h71_1_screen" / "analysis.json").read_text())
    s2 = json.loads((ROOT / "evidence" / "h71_2_akf_screen" / "analysis.json").read_text())
    s3 = json.loads((ROOT / "evidence" / "h71_3_mag_screen" / "analysis.json").read_text())
    e1 = CARD["experiments"]["experiment_1_h71_1_hgpc_screen"]
    e2 = CARD["experiments"]["experiment_2_h71_3_akf_screen"]
    e3 = CARD["experiments"]["experiment_3_h71_4_mag_screen"]
    for exp, ana in ((e1, s1), (e2, s2), (e3, s3)):
        assert exp["leakage_canary"]["passed"] is True
        assert exp["leakage_canary"]["max_feature_auc"] <= 0.90
        assert exp["gate"]["passed"] is False
        assert ana["gate"]["passed"] is False
        assert ana["gate"]["vs_named"]["CTRL_CREST_B2"]["mean_gain"] > 0.0
        assert ana["gate"]["vs_named"]["CTRL_H35_24"]["mean_gain"] < 0.0


def test_h71_lane_unique_vs_top_scorers_and_own_lineage() -> None:
    az = json.loads((ROOT / "evidence" / "h71_independent_audit_zeros.json").read_text())
    lane = json.loads((ROOT / "evidence" / "h71_lane_extended.json").read_text())
    assert az["all_hard_checks_pass"] is True
    assert az["checks"]["strict_whole_array_0_le_x_le_1"] is True
    assert az["checks"]["no_emission_on_catalogue"] is True
    assert lane["external_sparse"]["lane_pass"] is True
    assert lane["own_lineage"]["lane_pass"] is True
    assert lane["external_sparse"]["worst_cand_dots_within_3px"] <= 0.70
    assert CARD["registry_correlation_and_overlap"]["focus_21_top_scorers"]["b2_overlap"] < 0.20
    assert lane["lattice"][0]["cand_dots_within_3px"] > 0.70
    assert CARD["registry_correlation_and_overlap"]["surface_max_abs_spearman"] <= 0.90


def test_h71_tifs_revalidate_when_template_present() -> None:
    import pytest

    from gems25.paths import data_dir
    from gems25.submission import check_file

    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("competition template not restored")
    for entry in (PRIMARY, NAN_TWIN):
        res = check_file(ROOT / entry["path"], tmpl)
        assert res["ok_to_upload"] is True, res["hard_failures"]
        assert res["positive_pixels"] == 59472
        assert res["sha256"] == entry["sha256"]


def test_h71_site_and_readme_make_no_eligible_download_obvious() -> None:
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html"):
        html = (ROOT / rel).read_text()
        assert PRIMARY["file"] in html
        assert "Competition-ready download: NO" in html
        assert "OK to spend a weekly slot: NO" in html
        assert "DO NOT SUBMIT" in html
        assert "9eb0c31e5149" in html
        assert f'href="downloads/{PRIMARY["file"]}"' not in html
    readme = (ROOT / "README.md").read_text()
    assert PRIMARY["file"] in readme
    assert "Research-archive downloads: YES for inspection only · Competition-ready download: NO · OK TO SUBMIT: NO — DO NOT SUBMIT" in readme
    assert (ROOT / "docs" / "downloads" / PRIMARY["zip"]).exists()
