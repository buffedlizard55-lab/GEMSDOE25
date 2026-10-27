"""Locks the 2026-10-26 H72 DEM-free subsurface session: Run Card <-> analyses <-> registry <-> GeoTIFFs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "registry" / "run_card_h72_2026-10-26.json").read_text())
SUBS = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
PRIMARY = next(s for s in SUBS if s["role"] == "primary")
NAN_TWIN = next(s for s in SUBS if s["id"] == "h72-3-subsurf-nan")
ALT_H72_1 = next(s for s in SUBS if s["id"] == "h72-1-deapron")


def test_h72_3_is_featured_primary_and_matches_run_card() -> None:
    assert PRIMARY["id"] == "h72-3-subsurf"
    assert PRIMARY["sha256"] == CARD["raster_sha256"]
    assert NAN_TWIN["sha256"] == CARD["nan_twin_sha256"]
    assert PRIMARY["content_id"] == NAN_TWIN["content_id"] == CARD["content_id"] == "88bbebfe79b4"
    assert PRIMARY["positive_pixels"] == NAN_TWIN["positive_pixels"] == 41061
    assert PRIMARY["note"] == CARD["note"]
    assert len(PRIMARY["note"]) <= 120
    assert "no slot" in PRIMARY["note"] and "unscored" in PRIMARY["note"] and "not slot-approved" in PRIMARY["note"]
    assert CARD["verdict"] == "negative"
    assert PRIMARY["verdict"] == "negative"
    assert PRIMARY["ok_to_download"] is True
    assert PRIMARY["ok_to_submit_slot"] is False
    assert PRIMARY["slot_approved"] is False
    assert "DO NOT SUBMIT" in PRIMARY["status"]
    assert "lane gate" in PRIMARY["summary"].lower() or "strict lane" in PRIMARY["summary"].lower()
    assert ALT_H72_1["content_id"] == "a07ef071c49e"
    assert ALT_H72_1["slot_approved"] is False


def test_h72_three_experiments_match_saved_analyses_and_pass_canaries() -> None:
    a1 = json.loads((ROOT / "evidence" / "h72_1_screen" / "analysis.json").read_text())
    a2 = json.loads((ROOT / "evidence" / "h72_2_screen" / "analysis.json").read_text())
    a3 = json.loads((ROOT / "evidence" / "h72_3_screen" / "analysis.json").read_text())
    for ana in (a1, a2, a3):
        assert ana["leakage_canary"]["passed"] is True
        assert max(ana["leakage_canary"]["max_effective_auc"].values()) <= 0.90
    # De-aproned models beat blind controls in 4/4 folds in Exp 1 & Exp 2, while all 3 failed vs H35
    assert a1["contrasts"]["A3_PTTG_DEAPRON_vs_CTRL_BLIND_BD"]["folds_positive"] == 4
    assert a2["contrasts"]["B3_FULL_DEAPRON_vs_CTRL_BLIND_BD"]["folds_positive"] == 4
    assert a1["contrasts"]["A3_PTTG_DEAPRON_vs_CTRL_H35"]["gate_passed"] is False
    assert a2["contrasts"]["B1_FULL_H35_vs_CTRL_H35"]["gate_passed"] is False
    assert a3["contrasts"]["C1_SUBSURF_PTTG_MTHS_vs_CTRL_H35"]["gate_passed"] is False
    assert a3["contrasts"]["C1_SUBSURF_PTTG_MTHS_vs_CTRL_SUBSURF_D"]["mean"] > 0.0


def test_h72_3_density_aware_nonflag_does_not_waive_literal_lane_stop() -> None:
    az = json.loads((ROOT / "evidence" / "h72_3_independent_audit_zeros.json").read_text())
    an = json.loads((ROOT / "evidence" / "h72_3_independent_audit_nan.json").read_text())
    lane_lit = json.loads((ROOT / PRIMARY["lane"]["receipt"]).read_text())
    rc = CARD["correlation_overlap_vs_registry"]
    r13 = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
    assert az["all_hard_checks_pass"] is True
    assert an["all_hard_checks_pass"] is True
    assert az["checks"]["whole_array_finite_in_0_1"] is True
    assert az["checks"]["zero_known_catalogue_overlap"] is True
    assert len(lane_lit["rows"]) >= 85
    assert lane_lit["flagged_lane"] == []  # density-aware filter only; not a literal-rule clearance
    assert rc["lane_clean_density_aware"] is True
    assert rc["lane_clean"] is False
    assert r13 in rc["literal_flagged"]
    assert r13 in lane_lit["flagged_literal"]
    assert PRIMARY["lane"]["lane_clear"] is False
    assert PRIMARY["lane"]["lattice_overlap"] == 1.0
    assert lane_lit["verdict"] == "DUPLICATE/LANE OVERLAP - do not package"
    r13_row = next(row for row in lane_lit["rows"] if row["file"] == r13)
    assert r13_row["dots_within_3px"] == 1.0
    assert r13_row["flag_overlap"] is True
    assert r13_row["flag_overlap_lane"] is False  # dense-reference exception is not the standing rule
    assert rc["focus_21_top_scorers"]["worst_cand_dots_within_3px"] <= 0.40
    assert rc["focus_21_top_scorers"]["b2_overlap"] < 0.26
    assert rc["own_lineage"]["worst_cand_dots_within_3px"] <= 0.50
    assert rc["surface_max_abs_spearman"] <= 0.90


def test_h72_3_tifs_revalidate_when_template_present() -> None:
    import pytest

    from gems25.paths import data_dir
    from gems25.submission import check_file

    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("competition template not restored")
    for entry in (PRIMARY, NAN_TWIN):
        res = check_file(ROOT / entry["path"], tmpl)
        assert res["ok_to_upload"] is True, res["hard_failures"]
        assert res["positive_pixels"] == 41061
        assert res["sha256"] == entry["sha256"]


def test_h72_3_site_and_readme_make_submit_status_obvious() -> None:
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html", "docs/current-review.html"):
        html = (ROOT / rel).read_text()
        assert html.index("OK TO SUBMIT: NO") < html.index(PRIMARY["file"])
        assert "RESEARCH-ARCHIVE DOWNLOAD: YES" in html.upper()
        assert "Competition-ready" in html
        assert "OK to spend a weekly slot: NO" in html
        assert "DO NOT SUBMIT" in html
        assert "88bbebfe79b4" in html
    readme = (ROOT / "README.md").read_text()
    assert PRIMARY["file"] in readme
    assert "NO NEW COMPETITION TIFF" in readme
    assert "OK TO SUBMIT: NO — DO NOT SUBMIT" in readme
    assert (ROOT / "docs" / "downloads" / PRIMARY["zip"]).exists()
