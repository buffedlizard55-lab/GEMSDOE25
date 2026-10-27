"""End-to-end verification tests for the 2026-10-27 H75 DCHB-CG 3-experiment & LOQO B2 session."""

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
    assert subs[0]["id"] == "h75-dchb-cg"

    h75 = next(s for s in subs if s["id"] == "h75-dchb-cg")
    h75_nan = next(s for s in subs if s["id"] == "h75-dchb-cg-nan")

    assert card["schema"].startswith("run_card/v1")
    assert card["content_id"] == h75["content_id"] == h75_nan["content_id"] == "e035d75ca5d5"
    assert card["positive_pixels"] == h75["positive_pixels"] == h75_nan["positive_pixels"] == 37_654
    assert card["raster_sha256"] == h75["sha256"]
    assert card["nan_twin_sha256"] == h75_nan["sha256"]
    assert card["verdict"] == h75["verdict"] == h75_nan["verdict"] == "negative"
    assert card["slot_approved"] is False and h75["slot_approved"] is False
    assert card["ok_to_submit_slot"] is False and h75["ok_to_submit_slot"] is False
    assert card["ok_to_download_inspection"] is True and h75["ok_to_download"] is True
    assert card["organizer_confirmed_score"] is None
    assert card["estimated_leaderboard_score"] is None
    assert card["note"] == h75["note"] and len(card["note"]) <= 140
    for token in ("no slot", "not slot-approved", "DO NOT SUBMIT", "unscored", "e035d75ca5d5"):
        assert token in card["note"]


def test_h75_three_experiments_virgin_draws_canaries_and_blockholdout_g2() -> None:
    card = J("registry/run_card_h75_2026-10-27.json")
    x1 = card["holdout_dti"]["experiment_1_standard_holdout"]
    x2 = card["holdout_dti"]["experiment_2_block25km_holdout"]
    x3 = card["holdout_dti"]["experiment_3_checkerboard25km_full_block_holdout"]

    # Virgin draw separation across Exp 1-2 vs Exp 3, disjoint from all prior H72/H73/H74 draws (< 120)
    assert x1["draws"] == x2["draws"] == [120, 121]
    assert x3["draws"] == [122, 123]
    assert set(x1["draws"]).isdisjoint(x3["draws"])

    # Total experiment wall-clock <= 2 hours (7,200 s) across <= 3 experiments
    total_s = x1["elapsed_seconds"] + x2["elapsed_seconds"] + x3["elapsed_seconds"]
    assert total_s <= 7200.0

    # Every single-feature leakage canary passed across all 2,184 feature-cell checks
    for exp_dir, exp_rec in (
        ("evidence/h75_exp1_standard", x1),
        ("evidence/h75_exp2_block25km", x2),
        ("evidence/h75_exp3_checkerboard25km", x3),
    ):
        lc = exp_rec["leakage_canary"]
        assert lc["passed"] is True
        assert lc["total_feature_cell_checks"] == 91 * 8 == 728
        assert lc["max_canary_auc"] <= 0.90
        assert lc["max_h75_dchb_canary_auc"] <= 0.90
        raw_canaries = J(f"{exp_dir}/canaries.json")
        assert all(r["passed"] and r["canary_auc"] <= 0.90 for r in raw_canaries)
        design = J(f"{exp_dir}/design.json")
        assert design["preregistration_commit"] == "12931bb52bda9195495797590bd66ac073ee5589"
        for src_rel, sha in design["evaluator_hashes"].items():
            assert hashlib.sha256((ROOT / src_rel).read_bytes()).hexdigest() == sha, (exp_dir, src_rel)

    # Exp 3 (25-km full-checkerboard BlockHoldout, 95,188 withheld +) passed Gate G2 vs BOTH blind controls
    assert x3["withheld_positive_occurrences"] == 95_188
    assert x3["gates"]["gate_g2_cg_vs_both_blind_controls"] is True
    assert x3["contrasts"]["h75_cg_vs_ctrl_subsurf"]["paired_gain"] > 0.015
    assert all(g > 0 for g in x3["contrasts"]["h75_cg_vs_ctrl_subsurf"]["fold_gains"])
    assert x3["contrasts"]["h75_cg_vs_ctrl_blind_abcd"]["paired_gain"] > 0.003
    assert sum(g > 0 for g in x3["contrasts"]["h75_cg_vs_ctrl_blind_abcd"]["fold_gains"]) >= 3
    # And H75_CG_BLIND beat CTRL_H35 on the 24.66% L_valid == 0 gap in Exp 3
    assert x3["per_arm"]["H75_CG_BLIND"]["lidar_gap_dti"] > x3["per_arm"]["CTRL_H35"]["lidar_gap_dti"]

    # Pooled Slot Gate G1 vs CTRL_H35 remained False -> honest negative verdict, no weekly slot spent
    assert x1["gates"]["gate_g1_cg_vs_h35"] is False
    assert x2["gates"]["gate_g1_cg_vs_h35"] is False
    assert x3["gates"]["gate_g1_cg_vs_h35"] is False


def test_h75_geotiffs_uniqueness_across_108_rasters_and_deconfounding_irregularity() -> None:
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
    assert val["independent_rasterio_zeros"]["crs"] == "EPSG:32611"
    assert val["independent_rasterio_zeros"]["shape"] == [3730, 3292]
    assert val["independent_rasterio_zeros"]["inside_in_0_1"] is True
    assert val["independent_rasterio_zeros"]["inside_nan_count"] == 0
    assert val["independent_rasterio_zeros"]["inside_inf_count"] == 0
    assert val["independent_rasterio_zeros"]["outside_all_zero"] is True
    assert val["independent_rasterio_nan"]["outside_all_nan"] is True
    assert card["d_cat_strata_full_build"]["min_d_cat_px"] > 2.0

    lane = card["correlation_overlap_vs_registry"]
    assert lane["lane_clear"] is False  # literal >73%-halo rasters reported honestly
    assert lane["flagged_lane"] == []
    assert lane["registry_checked"] >= 108
    assert lane["surface_worst_abs_spearman"] <= 0.90
    assert lane["external_sparse"]["lane_pass"] is True
    assert lane["own_lineage"]["lane_pass"] is True
    # Corridor-Gated gamma=0.60 resolved Family-B LiDAR scarp convergence (<= 70% vs h23-a-6pct and H72-CF)
    assert lane["vs_h23_a_6pct"]["cand_dots_within_3px"] <= 0.70
    assert lane["vs_h72_catfree"]["cand_dots_within_3px"] <= 0.70
    assert lane["focus_winners"]["n"] == 32
    assert lane["focus_winners"]["b2_overlap"] < 0.40

    irr_ids = {i["id"] for i in J("registry/irregularities.json")["issues"]}
    assert "IR-25-CORRIDOR-GATED-DECONFOUNDING-20261027" in irr_ids


def test_h75_pages_readme_and_20261027_live_scores() -> None:
    card = J("registry/run_card_h75_2026-10-27.json")
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html", "docs/current-review.html"):
        txt = (ROOT / rel).read_text()
        assert card["submission_name"] in txt, rel
        assert card["content_id"] in txt, rel
        assert card["note"] in txt, rel
        assert "OK TO DOWNLOAD" in txt and "DO NOT SUBMIT" in txt, rel
        # Prominent above H74 download box
        assert txt.index(card["submission_name"]) < txt.index("3751606e1ce5"), rel

    readme = (ROOT / "README.md").read_text()
    assert card["submission_name"] in readme
    assert "39_h75_outcomes_and_executive_summary_2026-10-27.md" in readme
    assert "run_card_h75_2026-10-27.json" in readme
    assert "owner_brief_2026-10-27_verbatim.txt" in readme
    assert "Maximize P(Win)" in readme and "Own the Outcome" in readme

    # Verify all 8 new 2026-10-27 OWNER-REPORTED scores are recorded as owner_reported (never organizer_confirmed)
    ls = J("registry/live_scores.json")["artifacts"]
    by_score = {round(a["score"], 4) for a in ls if a["score"] is not None}
    for s in (0.2250, 0.1647, 0.0963, 0.0742, 0.0298, 0.0254, 0.0206, 0.0053):
        assert s in by_score
    assert all(a["status"] != "organizer_confirmed" for a in ls)

    # Verify 9 focus sites + extended sibling groups in 2026-10-27 executive summary artifact
    foc = J("evidence/focus_sites_h75_latest_2026-10-27.json")
    assert {r["site"] for r in foc["sites"]} == {f"GEMSDOE{n}" for n in (24, 25, 27, 28, 30, 31, 32, 33, 36)}
    assert len(foc["extended_sibling_sites"]) >= 15
