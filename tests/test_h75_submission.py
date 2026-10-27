"""End-to-end verification tests for the 2026-10-27 H75 EU3D-POE & BlockHoldout session."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def test_h75_run_card_and_registry_consistency() -> None:
    card = J("registry/run_card_h75_2026-10-27.json")
    docs_card = J("docs/data/run_card_h75_2026-10-27.json")
    assert card == docs_card

    subs = J("registry/submissions.json")["files"]
    docs_subs = J("docs/data/submissions.json")["files"]
    assert subs == docs_subs

    h75 = next(s for s in subs if s["id"] == "h75-eu3d-poe65")
    h75_nan = next(s for s in subs if s["id"] == "h75-eu3d-poe65-nan")

    assert card["schema"].startswith("run_card/v1")
    assert card["content_id"] == h75["content_id"] == h75_nan["content_id"] == "0a97fd71c3f3"
    assert card["positive_pixels"] == h75["positive_pixels"] == h75_nan["positive_pixels"] == 37_654
    assert card["raster_sha256"] == h75["sha256"]
    assert card["nan_twin_sha256"] == h75_nan["sha256"]
    assert card["verdict"] == h75["verdict"] == h75_nan["verdict"] == "negative"
    assert card["slot_approved"] is False and h75["slot_approved"] is False
    assert card["ok_to_submit_slot"] is False and h75["ok_to_submit_slot"] is False
    assert card["ok_to_download_inspection"] is True and h75["ok_to_download"] is True
    assert card["organizer_confirmed_score"] is None
    assert card["estimated_leaderboard_score"] is None
    assert card["note"] == h75["note"] and len(card["note"]) <= 120
    for token in ("no slot", "not slot-approved", "DO NOT SUBMIT", "unscored", "0a97fd71c3f3"):
        assert token in card["note"]


def test_h75_virgin_draws_canaries_apron_pass_and_blockholdout_shift() -> None:
    card = J("registry/run_card_h75_2026-10-27.json")
    joint = J("evidence/h75_joint_analysis.json")
    x1 = card["holdout_dti"]["experiment_1_block25km_checkerboard"]
    x2 = card["holdout_dti"]["experiment_2_standard_holdout"]

    assert x1["draws"] == [130, 131]
    assert x2["draws"] == [132, 133]
    assert set(x1["draws"]).isdisjoint(x2["draws"])

    for exp_canary_rel in (
        "evidence/h75_exp1_block25km/feature_canaries.json",
        "evidence/h75_exp2_standard/feature_canaries.json",
    ):
        recs = J(exp_canary_rel)
        assert len(recs) == 8
        assert all(r["all_passed"] and r["worst_canary_auc"] <= 0.90 for r in recs)

    # Exp 1: 25-km checkerboard BlockHoldout instrument shift reverses PM_DEAPRON penalty
    assert x1["median_truth_d_vis_px"] > 55.0 and x2["median_truth_d_vis_px"] < 12.0
    shift = joint["checkerboard_instrument_shift"]
    assert shift["pm_minus_h35_standard"] < -0.020
    assert shift["pm_minus_h35_block25km"] > 0.001
    assert shift["pm_far_gt9_minus_h35_block25km"] > 0.002

    # Exp 2: H75_APRON passes standard holdout screen in 4/4 folds with positive 95% CI
    apr_gate = x2["h75_apron_screen_gate"]
    assert apr_gate["passed"] is True
    assert apr_gate["folds_positive"] == 4
    assert apr_gate["paired_gain_vs_ctrl_h35"] > 0.001
    assert apr_gate["paired_ci95_vs_ctrl_h35"][0] > 0.0

    # Shipped CatFree POE65 beats ROOT_H75 in 4/4 folds in both experiments, while G1_SLOT stays False
    assert sum(g > 0 for g in x1["poe65_vs_root_h75"]["fold_gains"]) == 4
    assert sum(g > 0 for g in x2["poe65_vs_root_h75"]["fold_gains"]) == 4
    assert x2["g1_slot_poe_passed"] is False


def test_h75_geotiffs_uniqueness_and_irregularities() -> None:
    card = J("registry/run_card_h75_2026-10-27.json")
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
    assert lane["lane_clear"] is False
    assert lane["flagged_lane"] == []
    assert lane["registry_checked"] >= 105
    assert lane["surface_worst_abs_spearman"] <= 0.90
    assert lane["external_sparse"]["lane_pass"] is True
    assert lane["external_sparse"]["worst_cand_dots_within_3px"] <= 0.70
    assert lane["own_lineage"]["lane_pass"] is True
    assert lane["focus_winners"]["b2_overlap"] < 0.40

    # POE50 staging stop was recorded cleanly and never published to docs/downloads/
    assert not list((ROOT / "docs" / "downloads").glob("*h75-eu3d-poe50*"))
    irr_ids = {i["id"] for i in J("registry/irregularities.json")["issues"]}
    assert "IR-25-H78-FABRICATED-METRICS-20261027" in irr_ids
    assert "IR-25-H74-EXP3-PREREG-TRUNCATED-20261027" in irr_ids
    assert "IR-25-H75-DRAFT-ABORTED-20261027" in irr_ids
    assert (ROOT / "knowledge" / "36_preregistered_h74_exp3_subsurface_2026-10-26.md").stat().st_size > 6000


def test_h75_pages_and_readme_expose_download_table_and_do_not_submit() -> None:
    card = J("registry/run_card_h75_2026-10-27.json")
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html", "docs/current-review.html"):
        txt = (ROOT / rel).read_text()
        assert card["submission_name"] in txt, rel
        assert card["content_id"] in txt, rel
        assert card["note"] in txt, rel
        assert "DO NOT SUBMIT" in txt, rel
        assert "OK TO SUBMIT: YES" not in txt, rel
    readme = (ROOT / "README.md").read_text()
    assert card["submission_name"] in readme
    assert "39_h75_outcomes_and_executive_summary_2026-10-27.md" in readme
    assert "run_card_h75_2026-10-27.json" in readme
    assert "OK TO DOWNLOAD &amp; SUBMIT: YES" not in readme
