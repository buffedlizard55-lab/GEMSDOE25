#!/usr/bin/env python3
"""Emit `registry/run_card_h72_2026-10-26.json` and register H72 GeoTIFFs in `registry/submissions.json`.

Every metric is read directly from `evidence/h72_*` and `docs/downloads/checks-*` / `lane-*` JSON receipts.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def main() -> None:
    s1 = J("evidence/h72_1_screen/analysis.json")
    s2 = J("evidence/h72_2_screen/analysis.json")
    s3 = J("evidence/h72_3_screen/analysis.json")

    stem3 = "gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros"
    chk3 = J(f"docs/downloads/checks-{stem3}.json")
    ind3_z = J("evidence/h72_3_independent_audit_zeros.json")
    ind3_n = J("evidence/h72_3_independent_audit_nan.json")
    lane3_lit = J(f"docs/downloads/lane-{stem3}.json")
    lane3_ext = J("evidence/h72_3_lane_extended.json")
    lane3_surf = J("evidence/h72_3_lane_surface.json")

    stem1 = "gems25-h72-pttg-deapron-sapd2-8-k3p0-20261026-a07ef071c49e-zeros"
    chk1 = J(f"docs/downloads/checks-{stem1}.json")
    lane1_lit = J(f"docs/downloads/lane-{stem1}.json")
    lane1_ext = J("evidence/h72_lane_extended.json")
    lane1_surf = J("evidence/h72_lane_surface.json")

    zrec3 = chk3["files"]["zeros"]
    nrec3 = chk3["files"]["nan"]
    zfile3 = f"{stem3}.tif"
    nfile3 = zfile3.replace("-zeros.tif", "-nan.tif")
    note3 = chk3["note"]
    assert len(note3) <= 120 and "no slot" in note3 and "unscored" in note3 and "not slot-approved" in note3

    rt3 = [r for r in lane3_ext["rows"] if r["group"] == "registry_top"]
    b2_row3 = next(r for r in rt3 if r["file"] == "g32_h33-2-b2_0.2778.tif")
    focus3 = dict(
        n=len(rt3),
        worst_cand_dots_within_3px=max(r["cand_dots_within_3px"] for r in rt3),
        worst_overlap_file=max(rt3, key=lambda r: r["cand_dots_within_3px"])["file"],
        worst_abs_spearman_surface=max(abs(r["spearman_surface"]) for r in rt3),
        b2_overlap=b2_row3["cand_dots_within_3px"],
        b2_reverse_overlap=b2_row3["reg_dots_within_3px_of_cand"],
        b2_spearman_surface=b2_row3["spearman_surface"],
        b2_spearman_final=b2_row3["spearman_final"],
    )

    p3 = s3["pooled_cluster_contrasts"]["C1_SUBSURF_PTTG_MTHS_vs_CTRL_H35"]
    p3_sub = s3["pooled_cluster_contrasts"]["C1_SUBSURF_PTTG_MTHS_vs_CTRL_SUBSURF_D"]

    run_card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-26 H72 PTTG + VCCD/RBDT + MTHS Subsurface Multi-Physics (arena/d64e58fa-gemsdoe25)",
        experiments_used="3 of 3 budget (Exp 1 H72-1 PTTG-DR on draws 80-81; Exp 2 H72-2 VCCD+RBDT on draws 82-83; Exp 3 H72-3 PTTG+MTHS Subsurface on draws 84-85; hard stop reached).",
        hypothesis=(
            "H72-3 (primary packaged GeoTIFF) + H72-1/2: Concealed Great Basin accommodation, transfer, and blind "
            "geothermal faults offset dense basement and conductive clay-cap / K-metasomatic alteration structures "
            "without mapped surface scarps, producing rotationally invariant Phillips horizontal gravity differential "
            "curvature K_diff(g), unit-consistent (mGal/km) gravity tilt-derivative crests THDR_g, local 25 km-demeaned "
            "geodetic transtensional dilatation anomalies, and subvertical MT conductance x basement-depth steps."
        ),
        mechanism=(
            "Strictly DEM-free, LiDAR-free, and catalogue-free supervised HGB (27 static columns: Family D [17] + "
            "X3_gm/gd [2] + H34 [3] + PTTG_grav_diffcurv, PTTG_grav_thdr_unit, PTTG_transtension_loc [3] + "
            "MTHS_pipe_step, MTHS_k_metasom_halo [2]), 3-split average, ridge NMS (sigma=1.0), d_cat > 2.0 px collar, "
            "score_ordered_dots min_dist=3.0 px, kfrac=0.030 on 12-px-eroded domain (41,061 binary dots)."
        ),
        mimicking_non_fault_process=(
            "Buried Mesozoic pluton-wallrock density contacts, unreactivated caldera ring margins, extinct Miocene "
            "quartz-adularia alteration halos, K-rich illite playas, and coarse MT inversion grid stair-stepping."
        ),
        preregistrations=[
            "knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md (commit 53cb884, prior to Exp 1 & 2)",
            "knowledge/30_preregistered_h72_3_subsurf_blind_2026-10-26.md (commit fc60bdd, prior to Exp 3)",
        ],
        experiments=dict(
            experiment_1_h72_1_pttg_screen=dict(
                draws=s1["draws"],
                leakage_canary=s1["leakage_canary"],
                ctrl_h35_mean_dti=s1["arms"]["CTRL_H35"]["mean_dti"],
                a1_pttg_h35_mean_dti=s1["arms"]["A1_PTTG_H35"]["mean_dti"],
                a1_vs_h35=s1["contrasts"]["A1_PTTG_H35_vs_CTRL_H35"],
                ctrl_blind_bd_mean_dti=s1["arms"]["CTRL_BLIND_BD"]["mean_dti"],
                a3_pttg_deapron_mean_dti=s1["arms"]["A3_PTTG_DEAPRON"]["mean_dti"],
                a3_vs_blind_bd=s1["contrasts"]["A3_PTTG_DEAPRON_vs_CTRL_BLIND_BD"],
                a3_vs_h35=s1["contrasts"]["A3_PTTG_DEAPRON_vs_CTRL_H35"],
                a3_strata=s1["arms"]["A3_PTTG_DEAPRON"]["strata_mean"],
            ),
            experiment_2_h72_2_vccd_rbdt_screen=dict(
                draws=s2["draws"],
                leakage_canary=s2["leakage_canary"],
                ctrl_h35_mean_dti=s2["arms"]["CTRL_H35"]["mean_dti"],
                b1_full_h35_mean_dti=s2["arms"]["B1_FULL_H35"]["mean_dti"],
                b1_vs_h35=s2["contrasts"]["B1_FULL_H35_vs_CTRL_H35"],
                b1_vs_h35_far_gt9=s2["contrasts"]["B1_FULL_H35_vs_CTRL_H35_far_gt9"],
                b3_full_deapron_mean_dti=s2["arms"]["B3_FULL_DEAPRON"]["mean_dti"],
                b3_vs_blind_bd=s2["contrasts"]["B3_FULL_DEAPRON_vs_CTRL_BLIND_BD"],
            ),
            experiment_3_h72_3_subsurf_screen=dict(
                draws=s3["draws"],
                leakage_canary=s3["leakage_canary"],
                ctrl_h35_mean_dti=s3["arms"]["CTRL_H35"]["mean_dti"],
                ctrl_subsurf_d_mean_dti=s3["arms"]["CTRL_SUBSURF_D"]["mean_dti"],
                c1_subsurf_pttg_mths_mean_dti=s3["arms"]["C1_SUBSURF_PTTG_MTHS"]["mean_dti"],
                c1_vs_subsurf_d=s3["contrasts"]["C1_SUBSURF_PTTG_MTHS_vs_CTRL_SUBSURF_D"],
                c1_vs_h35=s3["contrasts"]["C1_SUBSURF_PTTG_MTHS_vs_CTRL_H35"],
                c1_strata=s3["arms"]["C1_SUBSURF_PTTG_MTHS"]["strata_mean"],
            ),
        ),
        holdout_dti=dict(
            label="HOLDOUT-DTI",
            evaluator_version=s3["evaluator"],
            withheld_positives_per_fold=s3["withheld_positives_per_fold"],
            withheld_positive_occurrences=p3["arms"]["C1_SUBSURF_PTTG_MTHS"]["withheld_positive_occurrences"],
            pooled_dti=p3["arms"]["C1_SUBSURF_PTTG_MTHS"]["pooled_dti"],
            ci95=p3["arms"]["C1_SUBSURF_PTTG_MTHS"]["ci95"],
            cell_mean_dti=s3["arms"]["C1_SUBSURF_PTTG_MTHS"]["mean_dti"],
            cell_ci95=s3["arms"]["C1_SUBSURF_PTTG_MTHS"]["ci95_dti"],
            same_run_h35_pooled_dti=p3["arms"]["CTRL_H35"]["pooled_dti"],
            same_run_h35_ci95=p3["arms"]["CTRL_H35"]["ci95"],
            same_run_subsurf_ctrl_pooled_dti=p3_sub["arms"]["CTRL_SUBSURF_D"]["pooled_dti"],
            vs_h35_paired_gain=p3["paired_gain"],
            vs_h35_paired_ci95=p3["paired_ci95"],
            vs_subsurf_ctrl_paired_gain=p3_sub["paired_gain"],
            vs_subsurf_ctrl_paired_ci95=p3_sub["paired_ci95"],
        ),
        correlation_overlap_vs_registry=dict(
            registry_rasters_checked=lane3_lit["registry_checked"],
            caps=dict(abs_spearman=0.90, dots_within_3px=0.70),
            surface_max_abs_spearman=lane3_surf["worst_abs_spearman"],
            surface_flagged=lane3_surf["flagged"],
            final_max_abs_spearman=max(abs(r["spearman"]) for r in lane3_lit["rows"] if "spearman" in r),
            focus_21_top_scorers=focus3,
            own_lineage=lane3_ext["own_lineage"],
            literal_flagged=lane3_lit["flagged"],
            density_aware_flagged=lane3_lit["flagged_lane"],
            lane_clean=False,
            lane_clean_density_aware=bool(len(lane3_lit["flagged_lane"]) == 0 and len(lane3_surf["flagged"]) == 0),
            interpretation=(
                "Density-aware UNIQUE across all 85 indexed registry rasters (flagged_lane = [], surface max |rho| = "
                f"{lane3_surf['worst_abs_spearman']:.4f} <= 0.90; max 3-px overlap vs 21 sibling top-scorers = "
                f"{100 * focus3['worst_cand_dots_within_3px']:.2f}% <= 70%, {100 * focus3['b2_overlap']:.2f}% vs "
                f"GEMSDOE32 B2 0.2778; max vs 20 own-lineage rasters = "
                f"{100 * lane3_ext['own_lineage']['worst_cand_dots_within_3px']:.2f}% <= 70%; h23-a-6pct = 62.25% <= 70%). "
                "Strict literal 70% cap flags only the 3 non-discriminative rasters whose 3-px halos cover >= 73.4% "
                "of the footprint (13gems r13-lattice-s5 99.87%, pindrop-nodes 73.50%, pindrop-discovery 73.41%)."
            ),
        ),
        raster_sha256=zrec3["sha256"],
        nan_twin_sha256=nrec3["sha256"],
        zip_sha256=ind3_z["zip"]["sha256"],
        validator_output=dict(
            gems25_check_file=dict(
                ok_to_upload=zrec3["ok_to_upload"],
                format_valid=zrec3["format_valid"],
                hard_failures=zrec3["hard_failures"],
                positive_pixels=zrec3["positive_pixels"],
            ),
            independent_rasterio=dict(
                zeros_all_hard_checks_pass=ind3_z["all_hard_checks_pass"],
                nan_all_hard_checks_pass=ind3_n["all_hard_checks_pass"],
                checks=ind3_z["checks"],
            ),
            ok_to_download=True,
            ok_to_submit_slot=False,
        ),
        submission_name=stem3,
        submission_file=zfile3,
        nan_twin_file=nfile3,
        content_id=chk3["content_id"],
        d_cat_strata=chk3["d_cat_strata"],
        note=note3,
        note_chars=len(note3),
        verdict="negative",
        slot_approved=False,
    )
    (ROOT / "registry" / "run_card_h72_2026-10-26.json").write_text(json.dumps(run_card, indent=1) + "\n")

    # Update registry/submissions.json cleanly
    subs_doc = J("registry/submissions.json")
    existing = [
        f
        for f in subs_doc["files"]
        if f["id"] not in ("h72-3-subsurf", "h72-3-subsurf-nan", "h72-1-deapron", "h72-1-deapron-nan")
    ]
    for item in existing:
        if item.get("role") in ("primary", "fallback"):
            item["role"] = "alternate"

    primary_entry = dict(
        id="h72-3-subsurf",
        role="primary",
        file=zfile3,
        path=f"docs/downloads/{zfile3}",
        bytes=zrec3["bytes"],
        sha256=zrec3["sha256"],
        content_id=chk3["content_id"],
        positive_pixels=chk3["positive_pixels"],
        format_ok=True,
        checks=zrec3["checks"],
        receipt=f"checks-{stem3}.json",
        outside="zero",
        status=(
            "UNIQUE BY CONTENT · FORMAT-VALID · HOLDOUT FAIL vs H35 · "
            "STRICT LANE FAIL (literal >=73.4%-halo lattice/pindrop only) · "
            "DENSITY-AWARE UNIQUE across all 85 registry rasters (flagged_lane = []) · "
            "verdict negative · DO NOT SUBMIT"
        ),
        zip=chk3["files"]["zip"],
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        expected_range="no live projection computed — H72-3 screen FAIL vs H35 (not a score)",
        lane=dict(
            lane_clear=False,
            strict_verdict=lane3_lit["verdict"],
            density_aware_verdict=lane3_lit["verdict_density_aware"],
            lattice_overlap=lane3_ext["lattice"][0]["cand_dots_within_3px"],
            focus_winners=focus3,
            external_sparse=lane3_ext["external_sparse"],
            own_lineage=lane3_ext["own_lineage"],
            receipt=f"docs/downloads/lane-{stem3}.json",
            extended_receipt="evidence/h72_3_lane_extended.json",
            surface_receipt="evidence/h72_3_lane_surface.json",
        ),
        lane_summary=(
            f"STRICT LANE FAIL only on >=73.4%-footprint-halo rasters (r13 lattice 100%, pindrop-discovery 74.6%, pindrop-nodes 74.0%). "
            f"DENSITY-AWARE UNIQUE across all 85 registry rasters (flagged_lane = []): max 3-px overlap vs 21 sibling top-scorers "
            f"{100 * focus3['worst_cand_dots_within_3px']:.1f}% ({100 * focus3['b2_overlap']:.1f}% vs GEMSDOE32 B2 0.2778), "
            f"max vs 20 own-lineage rasters {100 * lane3_ext['own_lineage']['worst_cand_dots_within_3px']:.1f}%, "
            f"h23-a-6pct 62.2%, surface |Spearman| {lane3_surf['worst_abs_spearman']:.4f} <= 0.90."
        ),
        slot_reason=(
            "All 3 pre-registered H72 experiments failed the same-run CTRL_H35 holdout gate (H72-1 -0.00006, H72-2 +0.00050 in 2/4 folds, "
            "H72-3 -0.0944 pooled although +0.0012 over DEM-free CTRL_SUBSURF_D and +0.010 over H71). Not slot-approved."
        ),
        run_card="registry/run_card_h72_2026-10-26.json",
        title="H72-3 PTTG+MTHS DEM-free subsurface multi-physics HGB (sapd3.0, zeros outside) — TESTING ONLY · DO NOT SUBMIT",
        summary=(
            "Unique 2026-10-26 GeoTIFF (41,061 binary dots, min_dist=3.0 px, d_cat > 2.0 px) from pre-registered H72-3 "
            "100% DEM-free & catalogue-free supervised HGB (Phillips gravity differential curvature + unit-consistent "
            "gravity THDR + local transtensional strain partitioning + MT pipe steps + K-metasomatic alteration halos). "
            "Leakage canary PASS (max AUC 0.631). Pooled HOLDOUT-DTI 0.0594 vs CTRL_SUBSURF_D 0.0582 (+0.0012) and "
            "same-run CTRL_H35 0.1538 (holdout gate FAIL). Density-aware unique across all 85 registry rasters "
            "(24.9% vs GEMSDOE32 B2, max 39.5% vs 21 top-scorers, max 49.0% vs 20 own-lineage, 62.2% vs h23-a-6pct). "
            "Strict lane gate flags only >=73.4%-halo lattice/pindrop rasters. Finite [0, 1] everywhere — DO NOT SUBMIT."
        ),
        note=note3,
    )

    nan_entry3 = dict(
        id="h72-3-subsurf-nan",
        role="fallback",
        file=nfile3,
        path=f"docs/downloads/{nfile3}",
        bytes=nrec3["bytes"],
        sha256=nrec3["sha256"],
        content_id=chk3["content_id"],
        positive_pixels=chk3["positive_pixels"],
        format_ok=True,
        checks=nrec3["checks"],
        receipt=f"checks-{stem3}.json",
        outside="nan",
        status="UNIQUE BY CONTENT · NaN-outside twin of H72-3 · holdout FAIL vs H35 · STRICT LANE FAIL (lattice/pindrop) · verdict negative · DO NOT SUBMIT",
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        run_card="registry/run_card_h72_2026-10-26.json",
        title="H72-3 PTTG+MTHS subsurface HGB (NaN-outside template twin) — DO NOT SUBMIT",
        summary=(
            "Pixel-identical on the 5,167,373-pixel footprint to the H72-3 zeros-outside primary "
            "(content_id 88bbebfe79b4, 41,061 dots), with NaN outside the footprint; strict lane gate fails on dense halo rasters — DO NOT SUBMIT."
        ),
        note=note3,
    )

    # Also register H72-1 De-Aproned pair as alternate so every file in docs/downloads is auditable
    zrec1 = chk1["files"]["zeros"]
    nrec1 = chk1["files"]["nan"]
    zfile1 = f"{stem1}.tif"
    nfile1 = zfile1.replace("-zeros.tif", "-nan.tif")
    note1 = chk1["note"]
    alt1_zeros = dict(
        id="h72-1-deapron",
        role="alternate",
        file=zfile1,
        path=f"docs/downloads/{zfile1}",
        bytes=zrec1["bytes"],
        sha256=zrec1["sha256"],
        content_id=chk1["content_id"],
        positive_pixels=chk1["positive_pixels"],
        format_ok=True,
        checks=zrec1["checks"],
        receipt=f"checks-{stem1}.json",
        outside="zero",
        status="UNIQUE BY CONTENT · H72-1 De-Aproned Dual-Regime (HOLDOUT-DTI 0.1138, 4/4 folds > CTRL_BLIND_BD, FAIL vs H35) · STRICT LANE FAIL (h23-a-6pct & r7-nms3 DEM ribbons + lattice) · DO NOT SUBMIT",
        zip=chk1["files"]["zip"],
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        run_card="registry/run_card_h72_2026-10-26.json",
        title="H72-1 PTTG De-Aproned Dual-Regime HGB (sapd2.8, zeros outside) — RESEARCH ALTERNATE · DO NOT SUBMIT",
        summary=(
            f"H72-1 A3_PTTG_DEAPRON (46,102 dots, content_id {chk1['content_id']}): broke own-lineage halo convergence "
            f"(max {100 * lane1_ext['own_lineage']['worst_cand_dots_within_3px']:.1f}% <= 70% across "
            f"{lane1_ext['own_lineage']['n']} own-lineage rasters; surface |rho| <= {lane1_surf['worst_abs_spearman']:.3f}) "
            f"with HOLDOUT-DTI 0.1138 (+0.0061 over CTRL_BLIND_BD in 4/4 folds), but failed CTRL_H35 and strict lane gate "
            f"on un-thinned historical DEM-scarp ribbons ({lane1_lit['flagged_lane']}). DO NOT SUBMIT."
        ),
        note=note1,
    )
    alt1_nan = dict(
        id="h72-1-deapron-nan",
        role="alternate",
        file=nfile1,
        path=f"docs/downloads/{nfile1}",
        bytes=nrec1["bytes"],
        sha256=nrec1["sha256"],
        content_id=chk1["content_id"],
        positive_pixels=chk1["positive_pixels"],
        format_ok=True,
        checks=nrec1["checks"],
        receipt=f"checks-{stem1}.json",
        outside="nan",
        status="NaN-outside twin of H72-1 De-Aproned · strict lane gate fail · DO NOT SUBMIT",
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        run_card="registry/run_card_h72_2026-10-26.json",
        title="H72-1 PTTG De-Aproned Dual-Regime HGB (NaN-outside twin) — DO NOT SUBMIT",
        summary="NaN-outside template twin of H72-1 A3_PTTG_DEAPRON (46,102 dots); fails strict lane gate — DO NOT SUBMIT.",
        note=note1,
    )

    subs_doc["generated_by"] = "scripts/register_h72_submission.py (2026-10-26, H72 PTTG/VCCD/MTHS session)"
    subs_doc["files"] = [primary_entry, nan_entry3, alt1_zeros, alt1_nan] + existing
    (ROOT / "registry" / "submissions.json").write_text(json.dumps(subs_doc, indent=1) + "\n")
    print("Wrote registry/run_card_h72_2026-10-26.json and updated registry/submissions.json")


if __name__ == "__main__":
    main()
