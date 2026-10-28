"""Locks the APFL2 session (knowledge/29-30): run card <-> analyses <-> registry <-> GeoTIFFs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "registry" / "run_card_apfl2_2026-10-26.json").read_text())
SUBS = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
# Merge note: featured rotated to obj-bin-greedy by PR #48 (merged first); APFL2 is alternate.
PRIMARY = next(s for s in SUBS if s["id"] == "apfl2-h35plus-apfl-b2-zeros")
NAN_TWIN = next(s for s in SUBS if s["id"] == "apfl2-h35plus-apfl-b2-nan")


def test_apfl2_is_featured_primary_and_matches_run_card() -> None:
    assert PRIMARY["id"] == "apfl2-h35plus-apfl-b2-zeros"
    assert PRIMARY["role"] == "alternate"
    assert PRIMARY["sha256"] == CARD["raster_sha256"]
    assert PRIMARY["content_id"] == NAN_TWIN["content_id"] == CARD["submission"]["content_id"] == "2e9e4189f554"
    assert PRIMARY["positive_pixels"] == NAN_TWIN["positive_pixels"] == 48658
    assert PRIMARY["note"] == CARD["submission"]["note"]
    assert len(PRIMARY["note"]) <= 140
    assert "no slot" in PRIMARY["note"] and "unscored" in PRIMARY["note"] and "not slot-approved" in PRIMARY["note"]
    assert "negative" in CARD["verdict"]
    assert PRIMARY["verdict"] == "negative"
    assert PRIMARY["ok_to_download"] is True
    assert PRIMARY["ok_to_submit_slot"] is False
    assert PRIMARY["slot_approved"] is False
    assert "DO NOT SUBMIT" in PRIMARY["status"]
    for entry in (PRIMARY, NAN_TWIN):
        p = ROOT / entry["path"]
        assert hashlib.sha256(p.read_bytes()).hexdigest() == entry["sha256"]
    assert (ROOT / "docs" / "downloads" / PRIMARY["zip"]).exists()


def test_apfl2_both_screens_fail_vs_h35_canary_clean() -> None:
    for name in ("apfl_direct_screen", "apfl_hgb_screen"):
        ana = json.loads((ROOT / "evidence" / name / "analysis.json").read_text())
        assert ana["gate"]["passed"] is False
        assert ana["leakage_canary"]["passed"] is True
        assert ana["leakage_canary"]["max_feature_auc"] <= 0.90
        assert (ROOT / "evidence" / name / "design.json").exists()
    direct = json.loads((ROOT / "evidence/apfl_direct_screen/analysis.json").read_text())
    assert direct["gate"]["vs_named"]["CTRL_CREST_B2"]["passed"] is True  # beats unsupervised floor
    assert direct["gate"]["vs_named"]["CTRL_H35_24"]["passed"] is False


def test_apfl2_lane_unique_vs_focus_sites_not_own_lineage() -> None:
    lane = CARD["correlation_overlap_vs_registry"]["final_dots"]
    assert all(v["dots_within_3px"] <= 0.70 for v in lane["vs_focus_sites"].values())
    assert lane["vs_focus_sites"]["GEMSDOE32"]["dots_within_3px"] < 0.35
    assert lane["worst_external_scored"]["dots_within_3px"] <= 0.70
    assert lane["worst_own_lineage"]["dots_within_3px"] > 0.70  # disclosed, not hidden
    surf = CARD["correlation_overlap_vs_registry"]["surface_before_placement"]
    assert surf["worst_abs_spearman"] <= 0.90


def test_apfl2_tifs_revalidate_when_template_present() -> None:
    import pytest

    from gems25.paths import data_dir
    from gems25.submission import check_file

    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("competition template not restored")
    for entry in (PRIMARY, NAN_TWIN):
        res = check_file(ROOT / entry["path"], tmpl)
        assert res["positive_pixels"] == 48658
        assert res["sha256"] == entry["sha256"]
        if entry is NAN_TWIN:
            # 2026-10-28 portal-safe gate: NaN-outside fails ONLY the portal [0, 1] range check
            assert res["hard_failures"] == ["portal_all_cells_finite_in_0_1"], res["hard_failures"]
            assert res["ok_to_upload"] is False
        else:
            assert res["ok_to_upload"] is True, res["hard_failures"]
    res0 = check_file(ROOT / PRIMARY["path"], tmpl)
    assert res0["checks"]["variant_strict_whole_array_no_nan"]["pass_"] is True


def test_apfl2_site_and_readme_make_submit_status_obvious() -> None:
    # Current pages feature the newer obj-bin file; APFL2 stays on history + section.
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html"):
        html = (ROOT / rel).read_text()
        assert "OK TO SUBMIT: NO" in html or "DO NOT SUBMIT" in html
        assert "0.148880" in html or "APFL piedmont-flexure completion" in html
    history = (ROOT / "docs/history.html").read_text()
    assert PRIMARY["file"] in history
    assert "2e9e4189f554" in history
    readme = (ROOT / "README.md").read_text()
    assert PRIMARY["file"] in readme
    assert "DO NOT SUBMIT" in readme
