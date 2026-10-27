"""End-to-end verification tests for the 2026-10-27 H79 CTHM-PoE + SGMC 3-experiment session & GeoTIFF."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def test_h79_run_card_and_registry_consistency() -> None:
    card = J("registry/run_card_h79_2026-10-27.json")
    docs_card = J("docs/data/run_card_h79_2026-10-27.json")
    assert card == docs_card

    subs = J("registry/submissions.json")["files"]
    docs_subs = J("docs/data/submissions.json")["files"]
    assert subs == docs_subs

    h79 = next(s for s in subs if s["id"] == "h79-cthm-crustal-sgmc")
    h79_nan = next(s for s in subs if s["id"] == "h79-cthm-crustal-sgmc-nan")

    assert card["schema"].startswith("run_card/v1")
    assert card["content_id"] == h79["content_id"] == h79_nan["content_id"] == "e7ad8a4bf3ed"
    assert card["positive_pixels"] == h79["positive_pixels"] == h79_nan["positive_pixels"] == 37_654
    assert card["raster_sha256"] == h79["sha256"]
    assert card["nan_twin_sha256"] == h79_nan["sha256"]
    assert card["verdict"] == h79["verdict"] == h79_nan["verdict"] == "negative"
    assert card["slot_approved"] is False and h79["slot_approved"] is False
    assert card["ok_to_submit_slot"] is False and h79["ok_to_submit_slot"] is False
    assert card["ok_to_download_inspection"] is True and h79["ok_to_download"] is True
    assert card["organizer_confirmed_score"] is None
    assert card["estimated_leaderboard_score"] is None
    assert card["note"] == h79["note"] and len(card["note"]) <= 120
    for token in ("no slot", "not slot-approved", "DO NOT SUBMIT", "unscored", "e7ad8a4bf3ed"):
        assert token in card["note"]


def test_h79_three_experiments_virgin_draws_canaries_and_discoveries() -> None:
    card = J("registry/run_card_h79_2026-10-27.json")
    joint = J("evidence/h79_joint_analysis.json")
    hd = card["holdout_dti"]
    x1 = hd["experiment_1_standard_holdout"]
    x2 = hd["experiment_2_block25km_holdout"]
    x3 = hd["experiment_3_confirm_block25km"]
    c56 = hd["shipped_crustal_sgmc_56col_readout"]

    # Virgin draw separation across Exp 1-2 vs Exp 3, and disjoint from all prior draws <= 113
    assert x1["draws"] == x2["draws"] == [114, 115]
    assert x3["draws"] == c56["draws"] == [116, 117]
    assert set(x1["draws"]).isdisjoint(x3["draws"])
    assert min(x1["draws"] + x3["draws"]) >= 114

    # All 2,232 single-feature leakage canary evaluations passed (AUC <= 0.90)
    assert joint["canary_summary"]["total_feature_cell_evaluations"] == 2232
    assert joint["canary_summary"]["all_passed"] is True
    assert joint["canary_summary"]["max_canary_auc"] <= 0.90
    for cf in (
        "evidence/h79_exp1_standard/feature_canaries.json",
        "evidence/h79_exp2_block25km/feature_canaries.json",
        "evidence/h79_exp3_confirm_bw25km/feature_canaries.json",
    ):
        recs = J(cf)
        assert len(recs) == 8
        assert all(r["all_passed"] and r["worst_canary_auc"] <= 0.90 for r in recs)

    # 25-km block holdout shifts truth into deep blind basins (median d_vis > 60 px vs < 10 px standard)
    assert x1["median_truth_d_vis_px"] < 10.0
    assert x2["median_truth_d_vis_px"] > 60.0 and x3["median_truth_d_vis_px"] > 60.0

    # Key scientific discoveries: PoE > CTRL_SUBSURF (4/4 folds), PoE > SINGLE_HGB (95% CI > 0), +SGMC (4/4 folds, 95% CI > 0)
    assert all(g > 0.0 for g in x1["poe_vs_ctrl_subsurf"]["fold_gains"])
    assert all(g > 0.0 for g in x2["poe_vs_ctrl_subsurf"]["fold_gains"])
    assert x3["poe_vs_single_hgb"]["paired_ci95"][0] > 0.0
    assert all(g > 0.0 for g in x3["poe_sgmc_vs_poe"]["fold_gains"])
    assert x3["poe_sgmc_vs_poe"]["paired_ci95"][0] > 0.0

    # Shipped 56-col crustal+SGMC readout improves on prior H74_SUBSURF (0.03906) while slot gate remains False
    assert c56["pooled_dti"] > 0.050
    assert x1["slot_gate_g1_passed"] is False and x3["slot_gate_passed"] is False


def test_h79_geotiffs_portal_range_safety_uniqueness_and_staging_stops() -> None:
    card = J("registry/run_card_h79_2026-10-27.json")
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

    # Exact DrivenData portal [0, 1] check across all 12,279,160 raster cells
    with rasterio.open(zeros_p) as ds:
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert ds.crs.to_epsg() == 32611
        assert ds.shape == (3730, 3292)
        arr = ds.read(1)
        assert np.all(np.isfinite(arr))
        assert bool(((arr >= 0.0) & (arr <= 1.0)).all()) is True
        assert int((arr > 0.0).sum()) == 37_654

    lane = card["correlation_overlap_vs_registry"]
    assert lane["lane_clear"] is False  # literal dense-halo rasters reported honestly
    assert lane["flagged_lane"] == []
    assert lane["registry_checked"] >= 103
    assert lane["surface_worst_abs_spearman"] <= 0.90
    assert lane["external_sparse"]["lane_pass"] is True
    assert lane["own_lineage"]["lane_pass"] is True
    assert lane["focus_winners"]["b2_overlap"] == pytest.approx(0.23538, abs=1e-4)
    assert lane["own_lineage"]["worst_cand_dots_within_3px"] < 0.50

    # Halted staging runs (poe_sgmc & 55-col subsurf) never published to docs/downloads
    assert not list((ROOT / "docs" / "downloads").glob("*h79-cthm-poe-sgmc*"))
    assert not list((ROOT / "docs" / "downloads").glob("*h79-cthm-subsurf*"))

    irr_ids = {i["id"] for i in J("registry/irregularities.json")["issues"]}
    assert "IR-25-H78-FABRICATED-HOLDOUT-AND-CI-FAILURE-20261027" in irr_ids
    assert "IR-25-POE-RIBBON-VS-SUBSURF-LINEAGE-20261027" in irr_ids


def test_focus_9_audit_and_ui_surface_h79_prominently() -> None:
    foc = J("evidence/focus_sites_2026_10_27_audit.json")
    assert {s["site"] for s in foc["sites"]} == {
        f"GEMSDOE{n}" for n in (24, 25, 27, 28, 30, 31, 32, 33, 36)
    }
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html", "docs/current-review.html", "README.md"):
        txt = (ROOT / rel).read_text()
        assert "gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed-zeros.tif" in txt, rel
        assert "e7ad8a4bf3ed" in txt, rel
        assert "DO NOT SUBMIT" in txt, rel
        assert "OK TO SUBMIT: YES" not in txt, rel
