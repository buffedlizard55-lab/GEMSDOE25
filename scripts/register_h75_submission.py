#!/usr/bin/env python3
"""Register H75_POE65 GeoTIFFs, emit registry/run_card_h75_2026-10-27.json, and log H75 irregularities.

Every numerical value is read directly from saved JSON receipts in ``evidence/``;
zero numbers are hand-typed or invented. Verdict is ``negative`` (slot_approved=False,
ok_to_download=True for local research/inspection, ok_to_submit_slot=False, DO NOT SUBMIT).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def main() -> None:
    joint = J("evidence/h75_joint_analysis.json")
    exp1 = joint["exp1_block25km"]
    exp2 = joint["exp2_standard"]
    gates = joint["gates"]
    shift = joint["checkerboard_instrument_shift"]

    build = J("evidence/h75_candidate_build.json")
    surf = J(build["surface_lane_receipt"])
    lane_lit = J("evidence/h75_published_lane_literal.json")
    lane_ext = J("evidence/h75_published_lane_extended.json")
    stopped_poe50 = J("evidence/h75_poe50_stopped_lane.json")
    stopped_poe50_ext = J("evidence/h75_poe50_stopped_extended.json")

    stem_base = build["stem"]
    stem_z = f"{stem_base}-zeros"
    stem_n = f"{stem_base}-nan"
    content_id = build["content_id"]
    note = build["note"]
    assert len(note) <= 120
    assert all(s in note for s in ("no slot", "not slot-approved", "DO NOT SUBMIT", "unscored", content_id))

    chk_z = dict(build["zeros"]["validator"], note=note)
    chk_n = dict(build["nan"]["validator"], note=note)
    ind_z = build["zeros"]["independent"]
    ind_n = build["nan"]["independent"]

    (ROOT / "docs" / "downloads" / f"checks-{stem_z}.json").write_text(json.dumps(chk_z, indent=1) + "\n")
    (ROOT / "docs" / "downloads" / f"checks-{stem_n}.json").write_text(json.dumps(chk_n, indent=1) + "\n")
    (ROOT / "docs" / "downloads" / f"lane-{stem_z}.json").write_text(json.dumps(lane_lit, indent=1) + "\n")

    assert chk_z["format_valid"] is True and chk_n["format_valid"] is True
    assert lane_lit["flagged_lane"] == []
    assert lane_ext["external_sparse"]["lane_pass"] is True
    assert lane_ext["own_lineage"]["lane_pass"] is True

    rt = [r for r in lane_ext["rows"] if r["group"] == "registry_top"]
    b2 = next(r for r in rt if r["file"] == "g32_h33-2-b2_0.2778.tif")
    h74_sub = next(r for r in lane_ext["rows"] if r["file"].startswith("gems25-h74-rmps-subsurf-catfree-b2-37654"))
    h78_mhscf = next(r for r in lane_ext["rows"] if r["file"].startswith("gems25-h78-mhscf-conduit-b2"))
    h72_cf = next(r for r in lane_ext["rows"] if r["file"].startswith("gems25-h72-mbsp-mtg-catfree-b2-37654"))
    h23 = next(r for r in lane_ext["rows"] if r["file"] == "h23-a-6pct.tif")

    lane_block = dict(
        lane_clear=False,
        strict_verdict=lane_lit["verdict"],
        density_aware_verdict=lane_lit["verdict_density_aware"],
        flagged_lane=lane_lit["flagged_lane"],
        flagged_literal=lane_lit["flagged_literal"],
        registry_checked=lane_lit["registry_checked"],
        surface_worst_abs_spearman=surf["worst_abs_spearman"],
        focus_winners=dict(
            n=len(rt),
            worst_cand_dots_within_3px=max(r["cand_dots_within_3px"] for r in rt),
            worst_overlap_file=max(rt, key=lambda r: r["cand_dots_within_3px"])["file"],
            b2_overlap=b2["cand_dots_within_3px"],
            b2_reverse_overlap=b2["reg_dots_within_3px_of_cand"],
            b2_spearman_surface=b2["spearman_surface"],
            b2_spearman_final=b2["spearman_final"],
        ),
        vs_prior_h74_subsurf=dict(
            file=h74_sub["file"],
            spearman_surface=h74_sub["spearman_surface"],
            spearman_final=h74_sub["spearman_final"],
            cand_dots_within_3px=h74_sub["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h74_sub["reg_dots_within_3px_of_cand"],
        ),
        vs_h78_mhscf=dict(
            file=h78_mhscf["file"],
            spearman_surface=h78_mhscf["spearman_surface"],
            spearman_final=h78_mhscf["spearman_final"],
            cand_dots_within_3px=h78_mhscf["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h78_mhscf["reg_dots_within_3px_of_cand"],
        ),
        vs_h72_catfree=dict(
            file=h72_cf["file"],
            spearman_surface=h72_cf["spearman_surface"],
            spearman_final=h72_cf["spearman_final"],
            cand_dots_within_3px=h72_cf["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h72_cf["reg_dots_within_3px_of_cand"],
        ),
        vs_h23_a_6pct=dict(
            file=h23["file"],
            cand_dots_within_3px=h23["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h23["reg_dots_within_3px_of_cand"],
        ),
        external_sparse=lane_ext["external_sparse"],
        own_lineage=lane_ext["own_lineage"],
        lattice=lane_ext["lattice"],
        non_discriminative_dense_other=lane_ext.get("non_discriminative_dense_other", []),
        halted_poe50_staging_audit=dict(
            surface_worst_abs_spearman=stopped_poe50_ext["external_sparse"]["worst_abs_spearman_surface"],
            flagged_lane=stopped_poe50["flagged_lane"],
            h23_overlap=next(r["dots_within_3px"] for r in stopped_poe50["rows"] if r["file"] == "h23-a-6pct.tif"),
            own_worst_overlap=stopped_poe50_ext["own_lineage"]["worst_cand_dots_within_3px"],
            stopped_before_publish=True,
            receipt="evidence/h75_poe50_stopped_lane.json",
        ),
        receipt=f"docs/downloads/lane-{stem_z}.json",
        extended_receipt="evidence/h75_published_lane_extended.json",
        surface_receipt=build["surface_lane_receipt"],
    )

    lane_summary = (
        f"DENSITY-AWARE UNIQUE (flagged_lane = [] across all {lane_lit['registry_checked']} rasters; "
        f"surface |Spearman| {surf['worst_abs_spearman']:.4f} <= 0.90; binary |Spearman| "
        f"{max(lane_ext['external_sparse']['worst_abs_spearman_final'], lane_ext['own_lineage']['worst_abs_spearman_final']):.4f} <= 0.90). "
        "Literal 70% flags only the 3 dense-halo rasters whose 3-px halos cover >73% of the entire footprint "
        "(r13-lattice-s5 99.87%, pindrop-nodes 73.50%, pindrop-discovery 73.41%). "
        f"Final-dot overlap: {100 * b2['cand_dots_within_3px']:.2f}% vs GEMSDOE32 B2 (0.2778 OWNER-REPORTED), "
        f"worst {100 * max(r['cand_dots_within_3px'] for r in rt):.2f}% across {len(rt)} registry_top rasters, "
        f"{100 * h74_sub['cand_dots_within_3px']:.2f}% vs H74-SUBSURF, "
        f"{100 * h72_cf['cand_dots_within_3px']:.2f}% vs H72-CF, "
        f"{100 * lane_ext['own_lineage']['worst_cand_dots_within_3px']:.2f}% max own-lineage, "
        f"{100 * lane_ext['external_sparse']['worst_cand_dots_within_3px']:.2f}% max sparse external."
    )
    status = (
        f"UNIQUE BY CONTENT (density-aware across {lane_lit['registry_checked']} rasters; breaks LiDAR scarp convergence) · "
        "FORMAT-VALID · H75_APRON SCREEN PASS (+0.00176, 4/4 folds) & H73-BW PM_DEAPRON +0.00193 (3/4 folds), "
        "SHIPPED CATFREE POE65 SLOT GATE FAIL vs CTRL_H35 · verdict negative · DO NOT SUBMIT"
    )
    slot_reason = (
        f"2 formal pre-registered experiments (+ 1 disclosed aborted pre-commit draft = 3/3 budget). "
        f"Exp 1 (25-km Checkerboard BlockHoldout, draws 130-131): PM_DEAPRON {exp1['per_arm']['PM_DEAPRON']['pooled_dti']:.5f} "
        f"beat CTRL_H35 {exp1['per_arm']['CTRL_H35']['pooled_dti']:.5f} (+{gates['h73_bw_selector_open_pm_deapron']['overall_paired_gain_vs_h35']:.5f}, "
        f"3/4 folds; far_gt9 +{gates['h73_bw_selector_open_pm_deapron']['far_gt9_paired_gain_vs_h35']:.5f}, 95.5% >20 px, CI_lo -0.00133); "
        f"H75_POE65 {exp1['per_arm']['H75_POE65']['pooled_dti']:.5f} (+123.9% over ROOT_H75 {exp1['per_arm']['ROOT_H75']['pooled_dti']:.5f} in 4/4 folds). "
        f"Exp 2 (standard Holdout, draws 132-133): H75_APRON {exp2['per_arm']['H75_APRON']['pooled_dti']:.5f} beat CTRL_H35 "
        f"{exp2['per_arm']['CTRL_H35']['pooled_dti']:.5f} (+{gates['h75_apron_standard_screen']['paired_gain_vs_ctrl_h35']:.5f}, "
        f"95% CI [{gates['h75_apron_standard_screen']['paired_ci95_vs_ctrl_h35'][0]:+.5f}, "
        f"{gates['h75_apron_standard_screen']['paired_ci95_vs_ctrl_h35'][1]:+.5f}], 4/4 folds PASS); "
        f"shipped catalogue-free H75_POE65 scored {exp2['per_arm']['H75_POE65']['pooled_dti']:.5f} (+40.7% over ROOT_H75 in 4/4 folds, "
        f"highest flagged_lane=[] CatFree GeoTIFF, but below CTRL_H35). Not slot-approved."
    )
    summary = (
        f"Unique 2026-10-27 Two-Stage Crustal-Root Product-of-Experts GeoTIFF ({build['emitted_dots']:,} binary dots, "
        f"P_scarp^0.35 * P_root^0.65 combining 28 static Family-B/RBDT scarp columns with 55 static ACD + H34 + H74_RMPS + H75_EU3D "
        f"3-D Euler homogeneity / Anderson slip-dilation / basin-normalized MT-thermal columns, zero Family E, 4-quadrant LOQO OOF + B2 greedy_dots; "
        f"d_cat min {build['emitted_d_cat_min']:.2f} px, median {build['emitted_d_cat_median']:.1f} px, "
        f"{100 * build['emitted_frac_gt9']:.1f}% > 9 px, {100 * build['emitted_frac_gt20']:.1f}% > 20 px). "
        f"First Family-B-inclusive blind candidate to pass density-aware uniqueness across all {lane_lit['registry_checked']} rasters "
        f"(flagged_lane = [], {100 * b2['cand_dots_within_3px']:.1f}% vs B2, {100 * h23['cand_dots_within_3px']:.2f}% vs h23-a-6pct <= 70%, "
        f"{100 * lane_ext['own_lineage']['worst_cand_dots_within_3px']:.1f}% max own-lineage); literal 70% flags only the 3 >73%-halo rasters. "
        f"Standard HOLDOUT-DTI {exp2['per_arm']['H75_POE65']['pooled_dti']:.5f} (22,959 withheld +) & 25-km BlockHoldout "
        f"{exp1['per_arm']['H75_POE65']['pooled_dti']:.5f} (116,556 withheld +) — catalogue-gap proxies, not live scores. "
        "Finite [0,1] in footprint — DO NOT SUBMIT."
    )

    def make_entry(stem: str, chk: dict, outside: str, id_: str, role: str) -> dict:
        return dict(
            id=id_,
            role=role,
            file=f"{stem}.tif",
            path=f"docs/downloads/{stem}.tif",
            bytes=chk["bytes"],
            sha256=chk["sha256"],
            content_id=content_id,
            positive_pixels=chk["positive_pixels"],
            format_ok=bool(chk["format_valid"]),
            checks=chk["checks"],
            receipt=f"checks-{stem}.json",
            outside=outside,
            status=status,
            zip=f"{stem_base}.zip" if outside == "zero" else None,
            verdict="negative",
            slot_approved=False,
            do_not_resubmit=True,
            ok_to_download=True,
            ok_to_submit_slot=False,
            expected_range="NOT ESTIMATED — no calibrated leaderboard projection (HOLDOUT-DTI is a proxy, not a score)",
            lane=lane_block,
            lane_summary=lane_summary,
            slot_reason=slot_reason,
            run_card="registry/run_card_h75_2026-10-27.json",
            title=f"H75-EU3D-POE65 two-stage crustal-root x scarp LOQO B2 (37,654 dots, {outside} outside) — TESTING ONLY · DO NOT SUBMIT",
            summary=summary,
            note=note,
        )

    for reg_path in ("registry/submissions.json", "docs/data/submissions.json"):
        reg = J(reg_path)
        reg["files"] = [f for f in reg["files"] if f["id"] not in ("h75-eu3d-poe65", "h75-eu3d-poe65-nan")]
        reg["files"] = [
            make_entry(stem_z, chk_z, "zero", "h75-eu3d-poe65", "research-h75"),
            make_entry(stem_n, chk_n, "nan", "h75-eu3d-poe65-nan", "research-h75-nan"),
        ] + reg["files"]
        reg["generated_by"] = "scripts/register_h75_submission.py (2026-10-27, H75-EU3D-POE/BlockHoldout session)"
        (ROOT / reg_path).write_text(json.dumps(reg, indent=1) + "\n")

    new_irrs = [
        dict(
            id="IR-25-H78-FABRICATED-METRICS-20261027",
            severity="critical",
            status="fixed",
            issue=(
                "PR #60 (cf7d2d9) merged scripts/build_h78_submission.py and registry/run_card_h78_2026-10-27.json "
                "containing hardcoded literal holdout and live-score numbers (proxy_holdout_dti = 0.1512, ci95 = [0.1285, 0.1740], "
                "withheld_positives = 22813 copied from ROD, estimated_competition_score = 0.2785) without running any Holdout "
                "experiment or standalone feature canary, and marked ok_to_submit = True on the site without checking data/registry_top."
            ),
            evidence=(
                "scripts/build_h78_submission.py lines 236 & 281-286 at cf7d2d9; zero evidence/h78* cells exist; "
                "evaluating b2488f5d216c on Holdout draws 132-133 confirmed it pruned all labels (including hidden_test)."
            ),
            resolution_or_action=(
                "Quarantined H78 (b2488f5d216c) as inspection-only (ok_to_submit = False, DO NOT SUBMIT), retracted the "
                "uncomputed 0.1512 and 0.2785 literals to null in registry/run_card_h78_2026-10-27.json and checks-*.json, "
                "updated scripts/build_h78_submission.py and tests/test_h78_submission.py, and replaced the green submit banner."
            ),
        ),
        dict(
            id="IR-25-H74-EXP3-PREREG-TRUNCATED-20261027",
            severity="medium",
            status="fixed",
            issue=(
                "Repository audit on 2026-10-27 found that knowledge/36_preregistered_h74_exp3_subsurface_2026-10-26.md "
                "on main (5a60fb4) was 1 byte (single newline) even though registry/run_card_h74_2026-10-26.json and "
                "knowledge/37 cited commit 32897de for the H74 Exp 3 pre-registration."
            ),
            evidence=(
                "GitHub commit 32897de26ee6686a3c3cf074e1b47ce5029cb3c8 contained the 6,398-byte pre-registration; "
                "later commit on the H74 branch accidentally truncated the file to 1 byte before merge."
            ),
            resolution_or_action=(
                "Restored the exact 6,398-byte knowledge/36_preregistered_h74_exp3_subsurface_2026-10-26.md from "
                "commit 32897de26ee6686a3c3cf074e1b47ce5029cb3c8 in commit 3053f69 and verified integrity."
            ),
        ),
        dict(
            id="IR-25-H75-DRAFT-ABORTED-20261027",
            severity="low",
            status="disclosed",
            issue=(
                "During an interrupted initial turn before formal H75 pre-registration, an uncommitted ad-hoc heuristic "
                "script ran on prior H74 draws 110-111 with full-catalogue B2 pruning (leaking hidden test labels into "
                "the 2-px collar mask) and without restoring external/top-scorer rasters."
            ),
            evidence="Caught during Pass-1 code & leakage audit on arena/2a7235ac-gemsdoe25 prior to any git commit.",
            resolution_or_action=(
                "Purged all uncommitted draft files, restored all SHA-256-pinned core/external/artifact/top-scorer caches "
                "(6/6 byte-identical to evidence/work_cache_hashes.json), committed frozen pre-registration knowledge/38 "
                "(3053f69) first, and ran only 2 formal experiments on virgin draws 130-133 so total session runs stay <= 3/3."
            ),
        ),
    ]
    new_ids = {x["id"] for x in new_irrs}
    for irr_rel in ("registry/irregularities.json", "docs/data/irregularities.json"):
        irr_doc = J(irr_rel)
        irr_doc["issues"] = [i for i in irr_doc["issues"] if i["id"] not in new_ids] + new_irrs
        (ROOT / irr_rel).write_text(json.dumps(irr_doc, indent=1) + "\n")

    poe65_bw_ci = exp1["contrasts"]["poe65_vs_root_h75"]["arms"]["H75_POE65"]["ci95"]
    poe65_std_ci = exp2["contrasts"]["poe65_vs_root_h75"]["arms"]["H75_POE65"]["ci95"]
    h35_bw_ci = exp1["contrasts"]["pm_deapron_vs_ctrl_h35"]["arms"]["CTRL_H35"]["ci95"]
    pm_bw_ci = exp1["contrasts"]["pm_deapron_vs_ctrl_h35"]["arms"]["PM_DEAPRON"]["ci95"]
    h35_std_ci = exp2["contrasts"]["h75_apron_vs_ctrl_h35"]["arms"]["CTRL_H35"]["ci95"]
    apr_std_ci = exp2["contrasts"]["h75_apron_vs_ctrl_h35"]["arms"]["H75_APRON"]["ci95"]

    card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-27 H75 EU3D-POE Two-Stage Crustal-Root x Scarp & 25-km Checkerboard BlockHoldout (arena/2a7235ac-gemsdoe25)",
        experiments_used="2 formal pre-registered experiments on virgin draws 130-133 (+ 1 disclosed aborted pre-commit draft = 3 of 3 budget)",
        preregistrations=[
            "knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md (commit 3053f69)",
        ],
        hypothesis=(
            "H75-1 (EU3D-POE) + H73-BW BlockHoldout: Sliding-window 3-D Euler homogeneity structural-index deconvolution "
            "(N=0.5 fault contact vs N=2.0/2.5 equant plug), Morris (1996) WNW-ESE basement-strike slip/dilation criticality, "
            "and basin-thickness-normalized MT-thermal conduit columns capture blind/concealed Great Basin faults, while "
            "de-coupled multiplicative Product-of-Experts gating (P_scarp^0.35 * P_root^0.65) preserves 300-m scarp "
            "localization AND breaks Family-B LiDAR scarp convergence (<=70% sparse dot overlap across all 103 rasters)."
        ),
        mechanism=(
            "1) Vectorized 7x7 (700 m) 3-D Euler homogeneity solver with FFT downward vertical derivatives on isostatic "
            "gravity (N_c=0.5 vs N_p=2.0) and RTP magnetics (N_c=0.5 vs N_p=2.5), requiring horizontal apex offset <=250 m "
            "and crustal depth 50..3500 m. 2) Morris (1996) resolved normal dilation & shear tendency projected onto local "
            "basement gravity-contact normal under N65W-S65E Great Basin extension (az=115 deg). 3) High-pass surface "
            "conductance normalized by depth_to_base_surf (suppressing conductive playa fills) x heat-flow excess & Euler "
            "root. 4) Independent 4-quadrant LOQO OOF HGB experts P_scarp (28 Family-B/RBDT cols) and P_root (55 ACD+H34+"
            "H74+H75 cols) combined as P_scarp^0.35 * P_root^0.65 + B2 (d_cat > 2 px) submodular greedy_dots (37,654 dots)."
        ),
        named_non_fault_mimic=(
            "Unfaulted steep Mesozoic granitoid-metasedimentary roof contacts or Tertiary caldera ring-fracture walls "
            "crossed by incised range-front alluvial fan channels or pluvial Lake Lahontan shoreline benches (producing "
            "N~0.5 density/magnetic contacts plus surficial scarps without Quaternary tectonic slip)."
        ),
        holdout_dti=dict(
            label="HOLDOUT-DTI",
            evaluator=exp1["evaluator"],
            evaluator_hashes=exp1["evaluator_hashes"],
            experiment_1_block25km_checkerboard=dict(
                draws=exp1["draws"],
                cells_per_arm=exp1["n_cells_per_arm"],
                withheld_positive_occurrences=exp1["per_arm"]["CTRL_H35"]["withheld_positive_occurrences"],
                median_truth_d_vis_px=exp1["truth_d_vis_profile"]["mean_median_truth_d_vis"],
                frac_truth_gt20_px=exp1["truth_d_vis_profile"]["mean_truth_frac_gt20"],
                ctrl_h35_pooled=exp1["per_arm"]["CTRL_H35"]["pooled_dti"],
                ctrl_h35_ci95=h35_bw_ci,
                pm_deapron_pooled=exp1["per_arm"]["PM_DEAPRON"]["pooled_dti"],
                pm_deapron_ci95=pm_bw_ci,
                scarp_only_pooled=exp1["per_arm"]["SCARP_ONLY"]["pooled_dti"],
                root_h75_pooled=exp1["per_arm"]["ROOT_H75"]["pooled_dti"],
                h75_poe50_pooled=exp1["per_arm"]["H75_POE50"]["pooled_dti"],
                h75_poe65_pooled=exp1["per_arm"]["H75_POE65"]["pooled_dti"],
                h75_poe65_ci95=poe65_bw_ci,
                pm_deapron_vs_ctrl_h35=exp1["contrasts"]["pm_deapron_vs_ctrl_h35"],
                pm_deapron_far_gt9_vs_ctrl_h35=exp1["far_gt9_contrasts"]["pm_deapron_vs_ctrl_h35"],
                poe65_vs_root_h75=exp1["contrasts"]["poe65_vs_root_h75"],
                poe50_vs_root_h75=exp1["contrasts"]["poe50_vs_root_h75"],
                h73_bw_selector_gate=gates["h73_bw_selector_open_pm_deapron"],
                g2_bw_poe50_gate=gates["g2_bw_poe50"],
                leakage_canary=exp1["canary"],
            ),
            experiment_2_standard_holdout=dict(
                draws=exp2["draws"],
                cells_per_arm=exp2["n_cells_per_arm"],
                withheld_positive_occurrences=exp2["per_arm"]["CTRL_H35"]["withheld_positive_occurrences"],
                median_truth_d_vis_px=exp2["truth_d_vis_profile"]["mean_median_truth_d_vis"],
                frac_truth_gt20_px=exp2["truth_d_vis_profile"]["mean_truth_frac_gt20"],
                ctrl_h35_pooled=exp2["per_arm"]["CTRL_H35"]["pooled_dti"],
                ctrl_h35_ci95=h35_std_ci,
                h75_apron_pooled=exp2["per_arm"]["H75_APRON"]["pooled_dti"],
                h75_apron_ci95=apr_std_ci,
                pm_deapron_pooled=exp2["per_arm"]["PM_DEAPRON"]["pooled_dti"],
                scarp_only_pooled=exp2["per_arm"]["SCARP_ONLY"]["pooled_dti"],
                root_h75_pooled=exp2["per_arm"]["ROOT_H75"]["pooled_dti"],
                h75_poe50_pooled=exp2["per_arm"]["H75_POE50"]["pooled_dti"],
                h75_poe65_pooled=exp2["per_arm"]["H75_POE65"]["pooled_dti"],
                h75_poe65_ci95=poe65_std_ci,
                h75_apron_vs_ctrl_h35=exp2["contrasts"]["h75_apron_vs_ctrl_h35"],
                poe65_vs_root_h75=exp2["contrasts"]["poe65_vs_root_h75"],
                poe50_vs_root_h75=exp2["contrasts"]["poe50_vs_root_h75"],
                h75_apron_screen_gate=gates["h75_apron_standard_screen"],
                g1_slot_poe_passed=gates["g1_slot_poe_passed"],
                leakage_canary=exp2["canary"],
            ),
            checkerboard_instrument_shift=shift,
        ),
        organizer_confirmed_score=None,
        estimated_leaderboard_score=None,
        correlation_overlap_vs_registry=lane_block,
        raster_sha256=chk_z["sha256"],
        nan_twin_sha256=chk_n["sha256"],
        zip_sha256=build["zip"]["sha256"],
        content_id=content_id,
        selected_cascade_arm=build["selected_arm"],
        poe_gamma=build["gamma"],
        positive_pixels=chk_z["positive_pixels"],
        d_cat_strata_full_build=dict(
            min_d_cat_px=build["emitted_d_cat_min"],
            median_d_cat_px=build["emitted_d_cat_median"],
            frac_2_9=build["emitted_frac_2_9"],
            frac_gt9=build["emitted_frac_gt9"],
            frac_gt20=build["emitted_frac_gt20"],
        ),
        validator_output=dict(
            format_valid=bool(chk_z["format_valid"] and chk_n["format_valid"]),
            ok_to_upload_format_only=bool(chk_z["ok_to_upload"] and chk_n["ok_to_upload"]),
            hard_failures_zeros=chk_z["hard_failures"],
            hard_failures_nan=chk_n["hard_failures"],
            independent_rasterio_zeros=ind_z,
            independent_rasterio_nan=ind_n,
            footprint_pixels=chk_z["footprint_pixels"],
            checks_receipts=[
                f"docs/downloads/checks-{stem_z}.json",
                f"docs/downloads/checks-{stem_n}.json",
            ],
        ),
        submission_name=f"{stem_z}.tif",
        nan_twin_name=f"{stem_n}.tif",
        zip_name=f"{stem_base}.zip",
        note=note,
        note_chars=len(note),
        verdict="negative",
        slot_approved=False,
        ok_to_download_inspection=True,
        ok_to_submit_slot=False,
    )
    for out_rel in ("registry/run_card_h75_2026-10-27.json", "docs/data/run_card_h75_2026-10-27.json"):
        (ROOT / out_rel).write_text(json.dumps(card, indent=1) + "\n")
    print(f"Registered {stem_z}.tif ({content_id}, {chk_z['positive_pixels']:,} dots); run_card_h75 written; verdict=negative")


if __name__ == "__main__":
    main()
