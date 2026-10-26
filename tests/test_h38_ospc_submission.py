"""Automated end-to-end gates for the Session-8 H38 deliverable, Run Card, and top-of-site verdict."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_h38_is_featured_primary_and_files_match_registry():
    subs = J("registry/submissions.json")["files"]
    primary = next(s for s in subs if s["id"] == "h38-ospc-submod")
    fallback = next(s for s in subs if s["id"] == "h38-ospc-submod-nan")
    assert primary["id"] == "h38-ospc-submod"
    assert fallback["id"] == "h38-ospc-submod-nan"
    assert primary["content_id"] == fallback["content_id"] == "680d62616417"
    assert primary["positive_pixels"] == fallback["positive_pixels"] == 48666
    for s in (primary, fallback):
        p = ROOT / s["path"]
        assert p.exists() and sha256(p) == s["sha256"] and p.stat().st_size == s["bytes"]
    assert (ROOT / "docs" / "downloads" / primary["zip"]).exists()


def test_h38_run_card_and_note_follow_parallel_run_protocol():
    primary = next(s for s in J("registry/submissions.json")["files"] if s["id"] == "h38-ospc-submod")
    card = J("registry/run_card_h38_ospc_2026-10-25.json")
    receipt = J(f"docs/downloads/{primary['receipt']}")

    required = (
        "hypothesis",
        "mechanism",
        "non_fault_process_that_could_mimic_it",
        "pre_registration",
        "holdout_dti",
        "correlation_overlap_vs_registry",
        "raster",
        "validator_output",
        "submission_name",
        "note",
        "verdict",
        "deviation_from_preregistration",
    )
    for k in required:
        assert k in card, k

    assert len(primary["note"]) <= 120
    assert all(tok in primary["note"] for tok in ("no slot", "unscored", "not slot-approved", primary["content_id"]))
    assert card["note"] == receipt["note"] == primary["note"]
    assert card["raster"]["sha256"] == primary["sha256"]
    assert card["holdout_dti"]["label"] == "HOLDOUT-DTI"
    assert card["experiments_run"] == 1 and card["budget_respected"] is True
    assert primary["ok_to_download"] is True
    assert primary["ok_to_submit_slot"] is False and primary["slot_approved"] is False
    assert primary["verdict"] == card["verdict"] == "negative"
    assert "DO NOT SUBMIT" in primary["status"]


def test_h38_holdout_screen_and_three_tier_lane_audit():
    scr = J("evidence/h38_ospc_screen/analysis.json")
    assert scr["leakage_canary"]["passed"] is True
    assert scr["leakage_canary"]["h38_max_canary_auc"] <= 0.90
    assert scr["gate"]["passed"] is False
    assert scr["contrasts"]["primary_G1_S1_vs_G0_S0"]["folds_positive"] == 1
    assert scr["contrasts"]["primary_G1_S1_vs_G0_S0"]["per_fold"]["NW"] > 0.005
    assert not (ROOT / "evidence" / "h38_ospc_confirm").exists(), "Confirmation must not run after screen failure"

    primary = next(s for s in J("registry/submissions.json")["files"] if s["id"] == "h38-ospc-submod")
    lane = primary["lane"]
    assert lane["lane_clear"] is False
    assert lane["lane_clear_vs_sibling_top_scorers"] is True
    assert lane["flagged_sibling_top_scorers"] == []
    assert lane["overlap_vs_gemsdoe32_b2"] <= 0.70
    assert lane["overlap_vs_gemsdoe70_submod"] <= 0.70
    assert lane["worst_abs_spearman_surface"] <= 0.90
    assert lane["worst_abs_spearman_final"] <= 0.90
    assert lane["lattice_overlap"] > 0.70


def test_h38_revalidates_independently_against_template():
    from gems25.paths import data_dir
    from gems25.submission import check_file

    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("competition template not restored")
    primary = next(s for s in J("registry/submissions.json")["files"] if s["id"] == "h38-ospc-submod")
    r = check_file(ROOT / primary["path"], tmpl)
    assert r["ok_to_upload"] and not r["hard_failures"], r["hard_failures"]
    assert r["positive_pixels"] == 48666


def test_site_and_readme_surface_h38_verdict_at_top():
    primary = next(s for s in J("registry/submissions.json")["files"] if s["role"] == "primary")
    for rel in ("docs/history.html", "docs/submission-history.html"):
        html = (ROOT / rel).read_text()
        assert "OK to download: YES" in html
        assert "OK to spend a weekly slot: NO" in html
        assert primary["file"] in html
        assert html.index("OK to download: YES") < html.index("Prior parallel-lane CF-1 research TIFF")
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html"):
        html = (ROOT / rel).read_text()
        assert "OK TO SUBMIT: NO" in html
        assert "New TIF download: unavailable" in html
    readme = (ROOT / "README.md").read_text()
    assert primary["file"] in readme
    assert "OK to download (local testing): YES · OK to spend a weekly slot: NO — DO NOT SUBMIT" in readme
