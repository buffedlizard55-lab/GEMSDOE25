"""End-to-end verification tests for the 2026-10-26 H74 RMPS-BFP & H74-BW 3-experiment session."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def test_h74_run_card_and_registry_consistency() -> None:
    card = J("registry/run_card_h74_2026-10-26.json")
    subs = J("registry/submissions.json")["files"]
    docs_subs = J("docs/data/submissions.json")["files"]
    assert subs == docs_subs

    h74 = next(s for s in subs if s["id"] == "h74-rmps-subsurf")
    h74_nan = next(s for s in subs if s["id"] == "h74-rmps-subsurf-nan")

    assert card["schema"].startswith("run_card/v1")
    assert card["content_id"] == h74["content_id"] == h74_nan["content_id"] == "3751606e1ce5"
    assert card["positive_pixels"] == h74["positive_pixels"] == h74_nan["positive_pixels"] == 37_654
    assert card["raster_sha256"] == h74["sha256"]
    assert card["nan_twin_sha256"] == h74_nan["sha256"]
    assert card["verdict"] == h74["verdict"] == h74_nan["verdict"] == "negative"
    assert card["slot_approved"] is False and h74["slot_approved"] is False
    assert card["ok_to_submit_slot"] is False and h74["ok_to_submit_slot"] is False
    assert card["ok_to_download_inspection"] is True and h74["ok_to_download"] is True
    assert card["organizer_confirmed_score"] is None
    assert card["estimated_leaderboard_score"] is None
    assert card["note"] == h74["note"] and len(card["note"]) <= 120
    for token in ("no slot", "not slot-approved", "DO NOT SUBMIT", "unscored", "3751606e1ce5"):
        assert token in card["note"]


def test_h74_three_experiments_virgin_draws_canaries_and_gates() -> None:
    card = J("registry/run_card_h74_2026-10-26.json")
    joint = J("evidence/h74_joint_analysis.json")
    exp3 = J("evidence/h74_exp3_subsurf_bw25km/analysis.json")

    x1 = card["holdout_dti"]["experiment_1_standard_holdout"]
    x2 = card["holdout_dti"]["experiment_2_block25km_holdout"]
    x3 = card["holdout_dti"]["experiment_3_subsurf_block25km_shipped_family"]

    # Virgin draw separation across Exp 1-2 vs Exp 3
    assert x1["draws"] == x2["draws"] == [110, 111]
    assert x3["draws"] == [112, 113]
    assert set(x1["draws"]).isdisjoint(x3["draws"])

    # Every single-feature leakage canary passed in all 3 experiments
    for exp_canary_rel in (
        "evidence/h74_exp1_standard/feature_canaries.json",
        "evidence/h74_exp2_block25km/feature_canaries.json",
        "evidence/h74_exp3_subsurf_bw25km/feature_canaries.json",
    ):
        recs = J(exp_canary_rel)
        assert len(recs) == 8
        assert all(r["all_passed"] and r["worst_canary_auc"] <= 0.90 for r in recs)

    # Exp 2 25-km block-withheld instrument shift & G2 gates
    assert x2["median_truth_d_vis_px"] > 60.0 and x1["median_truth_d_vis_px"] < 12.0
    assert x2["gate_g2_apron_passed"] is True
    assert x2["gate_g2_blind_passed"] is True
    shift = joint["instrument_shift_diagnostic"]
    collapse_ratio = -shift["apron_advantage_collapse_delta"] / shift["ctrl_h35_minus_ctrl_blind_standard"]
    assert collapse_ratio > 0.60  # 62.9% apron advantage collapse

    # Slot Gate G1 and Exp 3 G3_SUBSURF both remain False -> no slot authorized
    assert x1["slot_gate_g1_passed"] is False
    assert x3["gate_g3_subsurf_passed"] is False and exp3["slot_gate_passed"] is False
    assert x3["h74_subsurf_pooled"] == pytest.approx(exp3["per_arm"]["H74_SUBSURF"]["pooled_dti"])


def test_h74_geotiffs_uniqueness_and_stopped_abcd_irregularity() -> None:
    card = J("registry/run_card_h74_2026-10-26.json")
    zeros_p = ROOT / "docs" / "downloads" / card["submission_name"]
    nan_p = ROOT / "docs" / "downloads" / card["nan_twin_name"]
    zip_p = ROOT / "docs" / "downloads" / card["zip_name"]

    assert zeros_p.exists() and nan_p.exists() and zip_p.exists()
    assert hashlib.sha256(zeros_p.read_bytes()).hexdigest() == card["raster_sha256"]
    assert hashlib.sha256(nan_p.read_bytes()).hexdigest() == card["nan_twin_sha256"]
    assert hashlib.sha256(zip_p.read_bytes()).hexdigest() == card["zip_sha256"]
    with zipfile.ZipFile(zip_p) as zf:
        assert zf.namelist() == [zeros_p.name]
        assert zf.read(zeros_p.name) == zeros_p.read_bytes()

    val = card["validator_output"]
    assert val["format_valid"] is True
    assert val["hard_failures_zeros"] == [] and val["hard_failures_nan"] == []
    assert val["independent_rasterio_zeros"]["inside_in_0_1"] is True
    assert val["independent_rasterio_zeros"]["inside_nan_count"] == 0
    assert val["independent_rasterio_zeros"]["outside_all_zero"] is True
    assert val["independent_rasterio_nan"]["outside_all_nan"] is True
    assert card["d_cat_strata_full_build"]["min_d_cat_px"] > 2.0

    lane = card["correlation_overlap_vs_registry"]
    assert lane["lane_clear"] is False  # literal dense-halo rasters reported honestly
    assert lane["flagged_lane"] == []
    assert lane["registry_checked"] >= 100
    assert lane["surface_worst_abs_spearman"] <= 0.90
    assert lane["external_sparse"]["lane_pass"] is True
    assert lane["own_lineage"]["lane_pass"] is True
    assert lane["focus_winners"]["b2_overlap"] < 0.30
    assert lane["vs_prior_subsurface_h72_3"]["cand_dots_within_3px"] < 0.40

    # Halted ABCD blind staging run recorded as irregularity and never published
    assert not list((ROOT / "docs" / "downloads").glob("*h74-rmps-bfp-catfree*"))
    irr_ids = {i["id"] for i in J("registry/irregularities.json")["issues"]}
    assert "IR-25-LIDAR-BLIND-CONVERGENCE-20261026" in irr_ids


def test_h74_pages_and_readme_expose_download_table_and_do_not_submit() -> None:
    card = J("registry/run_card_h74_2026-10-26.json")
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html", "docs/current-review.html"):
        txt = (ROOT / rel).read_text()
        assert card["submission_name"] in txt, rel
        assert card["content_id"] in txt, rel
        assert card["note"] in txt, rel
        assert "DO NOT SUBMIT" in txt, rel
    readme = (ROOT / "README.md").read_text()
    assert card["submission_name"] in readme
    assert "37_h74_outcomes_and_executive_summary_2026-10-26.md" in readme
    assert "run_card_h74_2026-10-26.json" in readme
