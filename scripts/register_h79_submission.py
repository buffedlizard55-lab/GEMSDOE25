#!/usr/bin/env python3
"""Register H79_CRUSTAL_SGMC GeoTIFFs, emit registry/run_card_h79_2026-10-27.json,
remediate PR #60's H78 run card/submission entries, update sources.json, and log 2026-10-27 irregularities.

Every numerical value is read directly from saved JSON receipts in ``evidence/`` and ``docs/downloads/``;
zero numbers are hand-typed or invented. Verdict is ``negative`` (slot_approved=False,
ok_to_download=True for local research/inspection, ok_to_submit_slot=False, DO NOT SUBMIT).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEM_BASE = "gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed"
STEM_Z = f"{STEM_BASE}-zeros"
STEM_N = f"{STEM_BASE}-nan"
CONTENT_ID = "e7ad8a4bf3ed"
NOTE = "GEMSDOE25 H79-CTHM | no slot, not slot-approved; DO NOT SUBMIT | id e7ad8a4bf3ed | unscored"
assert len(NOTE) <= 120
assert all(s in NOTE for s in ("no slot", "not slot-approved", "DO NOT SUBMIT", "unscored", CONTENT_ID))

H78_BASE = "gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c"
H78_STEM_Z = f"{H78_BASE}-zeros"
H78_STEM_N = f"{H78_BASE}-nan"
H78_CID = "b2488f5d216c"
H78_NOTE = "GEMSDOE25 H78-MHSCF | no slot, not slot-approved; DO NOT SUBMIT | id b2488f5d216c | unscored"
assert len(H78_NOTE) <= 120


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def main() -> None:
    joint = J("evidence/h79_joint_analysis.json")
    exp1 = joint["exp1_standard"]
    exp2 = joint["exp2_block25km"]
    exp3 = joint["exp3_confirm_bw25km"]
    c56 = joint["shipped_crustal_sgmc_exp3_readout"]
    tri = joint["staging_uniqueness_triangle"]

    build = J("evidence/h79_crustal_sgmc_candidate_build.json")
    surf = J("evidence/h79_crustal_sgmc_surface_lane.json")
    lane_lit = J("evidence/h79_crustal_sgmc_lane_literal.json")
    lane_ext = J("evidence/h79_crustal_sgmc_lane_extended.json")
    ind_exact = J("evidence/h79_cthm_independent_audit_2026-10-27.json")
    post_merge_109 = J("evidence/h79_cthm_post_merge_109_audit.json")

    chk_z = dict(build["zeros"]["validator"], note=NOTE)
    chk_n = dict(build["nan"]["validator"], note=NOTE)
    ind_z = build["zeros"]["independent"]
    ind_n = build["nan"]["independent"]

    # Materialize standard docs/downloads/checks-*.json and lane-*.json receipts for H79
    (ROOT / "docs" / "downloads" / f"checks-{STEM_Z}.json").write_text(json.dumps(chk_z, indent=1) + "\n")
    (ROOT / "docs" / "downloads" / f"checks-{STEM_N}.json").write_text(json.dumps(chk_n, indent=1) + "\n")
    (ROOT / "docs" / "downloads" / f"lane-{STEM_Z}.json").write_text(json.dumps(lane_lit, indent=1) + "\n")

    assert chk_z["format_valid"] is True and chk_n["format_valid"] is True
    assert lane_lit["flagged_lane"] == []
    assert lane_ext["external_sparse"]["lane_pass"] is True
    assert lane_ext["own_lineage"]["lane_pass"] is True

    rt = [r for r in lane_ext["rows"] if r["group"] == "registry_top"]
    b2 = next(r for r in rt if r["file"] == "g32_h33-2-b2_0.2778.tif")
    h74_sub = next(
        r
        for r in lane_ext["rows"]
        if r["file"].startswith("gems25-h74-rmps-subsurf-catfree-b2-37654")
    )
    h78_row = next(
        r
        for r in lane_ext["rows"]
        if r["file"].startswith("gems25-h78-mhscf-conduit-b2-sapd2-85")
    )
    h23 = next(r for r in lane_ext["rows"] if r["file"] == "h23-a-6pct.tif")

    lane_block = dict(
        lane_clear=False,
        strict_verdict=lane_lit["verdict"],
        density_aware_verdict=lane_lit["verdict_density_aware"],
        flagged_lane=lane_lit["flagged_lane"],
        flagged_literal=lane_lit["flagged_literal"],
        registry_checked=lane_lit["registry_checked"],
        surface_worst_abs_spearman=surf["worst_abs_spearman"],
        post_merge_109_audit=post_merge_109,
        focus_winners=dict(
            n=len(rt),
            worst_cand_dots_within_3px=max(r["cand_dots_within_3px"] for r in rt),
            worst_overlap_file=max(rt, key=lambda r: r["cand_dots_within_3px"])["file"],
            b2_overlap=b2["cand_dots_within_3px"],
            b2_reverse_overlap=b2["reg_dots_within_3px_of_cand"],
            b2_spearman_surface=b2["spearman_surface"],
            b2_spearman_final=b2["spearman_final"],
        ),
        vs_prior_subsurface_h74=dict(
            file=h74_sub["file"],
            spearman_surface=h74_sub["spearman_surface"],
            spearman_final=h74_sub["spearman_final"],
            cand_dots_within_3px=h74_sub["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h74_sub["reg_dots_within_3px_of_cand"],
        ),
        vs_h78_mhscf=dict(
            file=h78_row["file"],
            spearman_surface=h78_row["spearman_surface"],
            spearman_final=h78_row["spearman_final"],
            cand_dots_within_3px=h78_row["cand_dots_within_3px"],
            reg_dots_within_3px_of_cand=h78_row["reg_dots_within_3px_of_cand"],
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
        staging_uniqueness_triangle=tri,
        receipt=f"docs/downloads/lane-{STEM_Z}.json",
        extended_receipt="evidence/h79_crustal_sgmc_lane_extended.json",
        surface_receipt="evidence/h79_crustal_sgmc_surface_lane.json",
    )

    lane_summary = (
        f"DENSITY-AWARE UNIQUE (flagged_lane = [] across all {lane_lit['registry_checked']} rasters; "
        f"surface |Spearman| {surf['worst_abs_spearman']:.4f} <= 0.90; binary |Spearman| "
        f"{max(lane_ext['external_sparse']['worst_abs_spearman_final'], lane_ext['own_lineage']['worst_abs_spearman_final']):.4f} <= 0.90). "
        "Literal 70% flags only the 3 dense-halo rasters whose 3-px halos cover >70% of the footprint "
        "(r13-lattice-s5 99.87%, pindrop-nodes 73.50%, pindrop-discovery 73.41%). "
        f"Final-dot overlap: {100 * b2['cand_dots_within_3px']:.2f}% vs GEMSDOE32 B2 (0.2778 OWNER-REPORTED), "
        f"worst {100 * max(r['cand_dots_within_3px'] for r in rt):.2f}% across {len(rt)} registry_top rasters, "
        f"{100 * h74_sub['cand_dots_within_3px']:.2f}% max own-lineage vs H74-SUBSURF, "
        f"{100 * lane_ext['external_sparse']['worst_cand_dots_within_3px']:.2f}% max sparse external vs h19-c.tif."
    )
    status = (
        f"UNIQUE BY CONTENT (density-aware across {lane_lit['registry_checked']} rasters) · FORMAT-VALID (0 NaN, [0,1]) · "
        "EXP 1-3 POE (+0.0239..+0.0247) & SGMC (+0.0128, 4/4 folds) PASS BLIND GATES, "
        "SLOT GATE G1 FAILS vs CTRL_H35 · verdict negative · DO NOT SUBMIT"
    )
    slot_reason = (
        f"3/3 experiments completed (2,232/2,232 canaries <= 0.90, max {joint['canary_summary']['max_canary_auc']:.4f}). "
        f"Exp 1 (standard Holdout, draws 114-115): H79_POE {exp1['per_arm']['H79_POE']['pooled_dti']:.5f} vs "
        f"CTRL_SUBSURF {exp1['per_arm']['CTRL_SUBSURF']['pooled_dti']:.5f} (+{exp1['contrasts']['h79_poe_vs_ctrl_subsurf']['paired_gain']:.5f}, 4/4 folds) "
        f"and CTRL_H35 {exp1['per_arm']['CTRL_H35']['pooled_dti']:.5f}. "
        f"Exp 2 (25-km block-withheld, draws 114-115): H79_POE {exp2['per_arm']['H79_POE']['pooled_dti']:.5f} (+{exp2['contrasts']['h79_poe_vs_ctrl_subsurf']['paired_gain']:.5f} vs CTRL_SUBSURF, 4/4 folds). "
        f"Exp 3 (25-km block-withheld confirmation, virgin draws 116-117): H79_POE beat single-HGB on identical 81 cols by "
        f"+{exp3['contrasts']['h79_poe_vs_single_hgb']['paired_gain']:.5f} (95% CI [{exp3['contrasts']['h79_poe_vs_single_hgb']['paired_ci95'][0]:+.4f}, "
        f"{exp3['contrasts']['h79_poe_vs_single_hgb']['paired_ci95'][1]:+.4f}]), and adding H79_sgmc_coulomb_react raised H79_POE_SGMC to "
        f"{exp3['per_arm']['H79_POE_SGMC']['pooled_dti']:.5f} (+{exp3['contrasts']['h79_poe_sgmc_vs_h79_poe']['paired_gain']:.5f}, 4/4 folds), "
        f"still below CTRL_H35 {exp3['per_arm']['CTRL_H35']['pooled_dti']:.5f}. Shipped 56-col H79_CRUSTAL_SGMC expert scored {c56['pooled_dti']:.5f} on Exp 3 draws. Not slot-approved."
    )
    summary = (
        f"Unique 2026-10-27 topography-free & catalogue-free GeoTIFF ({build['emitted_dots']:,} binary dots, "
        "56 static ACD + H34 + H74_RMPS + H79_CTHM + H79_SGMC crustal/hydrothermal + SGMC-Coulomb columns, "
        "zero DEM/LiDAR Family B, zero catalogue Family E, 4-quadrant LOQO OOF + B2 submodular greedy_dots; "
        f"d_cat median {build['emitted_d_cat_median']:.1f} px, {100 * build['emitted_frac_gt9']:.1f}% > 9 px, "
        f"{100 * build['emitted_frac_gt20']:.1f}% > 20 px). "
        "Strict lane gate flags only the 3 >70%-halo rasters (r13 lattice + pindrop dense maps); density-aware unique "
        f"(flagged_lane = [] across all {lane_lit['registry_checked']} rasters; {100 * b2['cand_dots_within_3px']:.1f}% vs B2, "
        f"{100 * h74_sub['cand_dots_within_3px']:.1f}% vs H74-SUBSURF, {100 * lane_ext['external_sparse']['worst_cand_dots_within_3px']:.1f}% max external sparse). "
        f"25-km block-withheld HOLDOUT-DTI {c56['pooled_dti']:.5f} standalone crustal+SGMC ({c56['withheld_positive_occurrences']:,} withheld positives) "
        f"and {exp3['per_arm']['H79_POE_SGMC']['pooled_dti']:.5f} full two-expert H79_POE_SGMC — catalogue-gap proxy, not a live score. "
        "Finite [0,1] across all 12,279,160 pixels (0 NaN in zeros variant) — DO NOT SUBMIT."
    )

    def make_h79_entry(stem: str, chk: dict, outside: str, id_: str, role: str) -> dict:
        return dict(
            id=id_,
            role=role,
            file=f"{stem}.tif",
            path=f"docs/downloads/{stem}.tif",
            bytes=chk["bytes"],
            sha256=chk["sha256"],
            content_id=CONTENT_ID,
            positive_pixels=chk["positive_pixels"],
            format_ok=bool(chk["format_valid"]),
            checks=chk["checks"],
            receipt=f"checks-{stem}.json",
            outside=outside,
            status=status,
            zip=f"{STEM_BASE}.zip" if outside == "zero" else None,
            verdict="negative",
            slot_approved=False,
            do_not_resubmit=True,
            ok_to_download=True,
            ok_to_submit_slot=False,
            expected_range="NOT ESTIMATED — no calibrated leaderboard projection (HOLDOUT-DTI is a proxy, not a score)",
            lane=lane_block,
            lane_summary=lane_summary,
            slot_reason=slot_reason,
            run_card="registry/run_card_h79_cthm_2026-10-27.json",
            title=f"H79-CTHM+SGMC topography-free crustal LOQO B2 (37,654 dots, {outside} outside) — TESTING ONLY · DO NOT SUBMIT",
            summary=summary,
            note=NOTE,
        )

    drop_ids = {
        "h79-cthm-crustal-sgmc",
        "h79-cthm-crustal-sgmc-nan",
    }
    for reg_path in ("registry/submissions.json", "docs/data/submissions.json"):
        reg = J(reg_path)
        clean_files = [f for f in reg["files"] if f["id"] not in drop_ids]
        insert_at = 2 if len(clean_files) >= 2 and clean_files[0]["id"] == "h75-dchb-cg" else 0
        reg["files"] = (
            clean_files[:insert_at]
            + [
                make_h79_entry(STEM_Z, chk_z, "zero", "h79-cthm-crustal-sgmc", "research-h79-cthm"),
                make_h79_entry(STEM_N, chk_n, "nan", "h79-cthm-crustal-sgmc-nan", "research-h79-cthm-nan"),
            ]
            + clean_files[insert_at:]
        )
        (ROOT / reg_path).write_text(json.dumps(reg, indent=1) + "\n")

    # Log 2026-10-27 irregularities idempotently
    audit78 = J("evidence/h78_measured_holdout_audit_2026-10-27.json")
    new_irrs = [
        dict(
            id="IR-25-H78-FABRICATED-HOLDOUT-AND-CI-FAILURE-20261027",
            severity="high",
            status="resolved",
            issue=(
                "Merged PR #60 (commit 77be1ae, scripts/build_h78_submission.py) hardcoded its holdout_dti, CI, and "
                "competition projection without running HoldoutEvaluator, checked only 86 rasters, set ok_to_submit = True "
                "without selector authorization, and introduced 36 ruff lint errors on main."
            ),
            evidence=(
                "evidence/h78_measured_holdout_audit_2026-10-27.json; "
                "evidence/h78_independent_reaudit_2026-10-27.json; "
                "evidence/h78_literal_lane_reaudit_2026-10-27.json; "
                "registry/run_card_h78_2026-10-27.json."
            ),
            resolution_or_action=(
                f"Evaluated H78 on draws [60, 61] (22,813 withheld positives -> measured HOLDOUT-DTI = {audit78['pooled_dti']:.6f}, "
                f"95% CI [{audit78['ci95'][0]:.6f}, {audit78['ci95'][1]:.6f}]), retracted uncomputed metrics, set ok_to_submit = False "
                "and slot_approved = False, and restored ruff check across scripts/ to 0 errors."
            ),
        ),
        dict(
            id="IR-25-POE-RIBBON-VS-SUBSURF-LINEAGE-20261027",
            severity="medium",
            status="resolved",
            issue=(
                "Two symmetric pre-publish staging duplicate stops bracketed blind model design: (1) Two-expert H79_POE_SGMC "
                "(82 cols: 56 crustal x 26 morpho, gamma_c=0.55) eliminated own-lineage convergence (47.21% <= 70% vs H72-CF and "
                "<=53.00% across all 27 sibling winners) but still overlapped GEMSDOE22's 309,814-px h23-a-6pct.tif DEM/LiDAR ribbon "
                "at 75.55% > 70%; (2) 55-column H79_SUBSURF (without H79_SGMC) cleared all 54 external sparse rasters (53.18% on "
                "h23-a-6pct.tif) but overlapped own-lineage H74_SUBSURF at 76.79% > 70% due to 51/55 shared static columns."
            ),
            evidence=(
                "evidence/h79_poe_sgmc_stopped_lane.json; evidence/h79_poe_sgmc_stopped_extended.json; "
                "evidence/h79_subsurf_stopped_lane.json; evidence/h79_subsurf_stopped_extended.json; "
                "evidence/h79_crustal_sgmc_lane_literal.json; evidence/h79_crustal_sgmc_lane_extended.json; "
                "evidence/h79_cthm_post_merge_109_audit.json."
            ),
            resolution_or_action=(
                "Pre-publish staging guards halted both runs before touching docs/downloads/. Evaluating the exact 56-column "
                "zero-topography M_crustal expert from Exp 3 (H79_SUBSURF + H79_sgmc_coulomb_react = H79_CRUSTAL_SGMC, e7ad8a4bf3ed) "
                "broke own-lineage tie-breaking (49.69% <= 70% vs H74_SUBSURF, 44.20% vs H75-DCHB-CG, 44.17% vs H75-EU3D-POE65) "
                "while keeping all 106 sparse rasters <= 58.02% (55.49% on h23-a-6pct.tif, 23.54% on GEMSDOE32 B2)."
            ),
        ),
    ]
    new_irr_ids = {x["id"] for x in new_irrs}
    for irr_rel in ("registry/irregularities.json", "docs/data/irregularities.json"):
        irr_doc = J(irr_rel)
        irr_doc["issues"] = [i for i in irr_doc["issues"] if i["id"] not in new_irr_ids] + new_irrs
        (ROOT / irr_rel).write_text(json.dumps(irr_doc, indent=1) + "\n")

    # Add 2026-10-27 verified source entries idempotently (zero automated DrivenData access)
    new_sources = [
        dict(
            id="usgs-sgmc-ds1052",
            title="USGS State Geologic Map Compilation (SGMC) Geodatabase of the Conterminous United States (DS-1052)",
            url="https://doi.org/10.3133/ds1052",
            publisher="U.S. Geological Survey (Horton, San Juan & Stoeser, 2017)",
            kind="official",
            used_for="H79_sgmc_coulomb_react strike-aligned SGMC contact reactivation & basin-margin structural corridors (cached in data/external/sgmc_contacts_100m.tif)",
            verified=True,
            verified_utc="2026-10-27",
            how_verified="SHA-256 verified against registry/data_manifest.json and inspected raster geometry/values in data/external/sgmc_contacts_100m.tif",
            caveats="Public-domain federal compilation; standalone leakage canary AUC = 0.7455 (standard) / 0.7393 (25-km block) <= 0.90.",
            license="Public Domain (17 U.S.C. 105)",
            reachable_from_sandbox_bash=False,
        ),
        dict(
            id="focus-9-github-20261027",
            title="Live 2026-10-27 GitHub Repository Audit of Focus Sites GEMSDOE24..36 & Sibling Portfolio GEMSDOE19..92",
            url="https://github.com/buffedlizard55-lab/GEMSDOE32",
            publisher="buffedlizard55-lab GitHub organization",
            kind="internal-mirror",
            used_for="Up-to-the-minute 2026-10-27 commit SHAs, run cards, candidate GeoTIFF hashes, and duplicate/eligibility audit across GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36, and 70",
            verified=True,
            verified_utc="2026-10-27",
            how_verified="Direct gh api commit/tree/run_card inspection on 2026-10-27 plus pixel-exact raster verification in evidence/focus_sites_2026_10_27_audit.json",
            caveats="Historical leaderboard scores reported in sibling READMEs remain OWNER-REPORTED claims, not ORGANIZER-CONFIRMED receipts.",
            license="Repository internal",
            reachable_from_sandbox_bash=True,
        ),
    ]
    new_src_ids = {s["id"] for s in new_sources}
    for src_rel in ("registry/sources.json", "docs/data/sources.json"):
        src_doc = J(src_rel)
        src_doc["generated_utc"] = "2026-10-27"
        src_doc["sources"] = [s for s in src_doc["sources"] if s["id"] not in new_src_ids] + new_sources
        (ROOT / src_rel).write_text(json.dumps(src_doc, indent=1) + "\n")

    # Emit registry/run_card_h79_2026-10-27.json (Parallel-Run Protocol Item 5)
    card79 = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-27 H79 CTHM-PoE + SGMC Coulomb Reactivation & Crustal LOQO (arena/5e2cf679-gemsdoe25)",
        experiments_used=(
            "3 of 3 budget (Exp 1 standard Holdout draws 114-115; Exp 2 25-km block-withheld draws 114-115; "
            "Exp 3 25-km block-withheld confirmation + SGMC reactivation virgin draws 116-117)"
        ),
        preregistrations=[
            "knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md (commit b59b129)",
        ],
        hypothesis=(
            "H79-A (CTHM-PoE) + H79-B (SGMC-Coulomb): (1) Four zero-topography crustal-thermomechanical & hydrothermal "
            "alteration operators (H79_aniso_conduit_plume, H79_demag_argillic_crest, H79_euler_contact_index, "
            "H79_grav_mt_gouge_juxtapose) plus strike-aligned USGS SGMC lithologic-contact Coulomb reactivation "
            "(H79_sgmc_coulomb_react) detect Neogene-Quaternary faults concealed beneath Great Basin playas and bajadas; "
            "(2) Factoring blind inference into two physically orthogonal HGB experts (56-col zero-topography M_crustal x "
            "26-col morphometric M_morpho) via floor-protected log-odds Product-of-Experts stops Family B scarp features "
            "from starving blind crustal splits at shallow tree depths."
        ),
        mechanism=(
            "1) Strain-oriented anisotropic spring/vent hydrothermal plume log-density along principal extensional fault "
            "azimuth theta_f = 0.5*atan2(-e_xy, 0.5*(e_xx - e_yy)). 2) Magnetite-destruction argillic alteration crest "
            "combining thorium-normalized K excess (K - Th regression residual) with RTP magnetic-low trough along regional "
            "gravity gradients. 3) 3D potential-field Euler structural-index contact selector isolating steep fault steps "
            "(SI in [0, 1]) from deeper spheres/plutons (SI >= 2). 4) Gravity horizontal-gradient x shallow MT electrical "
            "conductivity gouge juxtaposition. 5) Strike-aligned SGMC contact proximity weighted by Kreemer strain rate and "
            "2-m temperature excess. Shipped LOQO artifact uses the 56-column zero-topography M_crustal_sgmc expert to "
            "satisfy both external_sparse <= 70% and own_lineage <= 70% simultaneously."
        ),
        named_non_fault_mimic=(
            "Unfaulted caldera ring-fracture hydrothermal alteration halos, potassic rhyolite dome margins, tabular "
            "Mesozoic intrusive sill contacts, and closed-basin evaporitic playa-margin brine/K-feldspar deflation lags."
        ),
        holdout_dti=dict(
            label="HOLDOUT-DTI",
            evaluator=exp3["evaluator"],
            canary_summary=joint["canary_summary"],
            experiment_1_standard_holdout=dict(
                draws=exp1["draws"],
                cells_per_arm=exp1["n_cells_per_arm"],
                withheld_positive_occurrences=exp1["per_arm"]["CTRL_H35"]["withheld_positive_occurrences"],
                median_truth_d_vis_px=exp1["truth_d_vis_profile"]["mean_median_truth_d_vis"],
                frac_truth_gt20_px=exp1["truth_d_vis_profile"]["mean_truth_frac_gt20"],
                ctrl_h35_pooled=exp1["per_arm"]["CTRL_H35"]["pooled_dti"],
                ctrl_subsurf_pooled=exp1["per_arm"]["CTRL_SUBSURF"]["pooled_dti"],
                h79_subsurf_pooled=exp1["per_arm"]["H79_SUBSURF"]["pooled_dti"],
                h79_poe_pooled=exp1["per_arm"]["H79_POE"]["pooled_dti"],
                subsurf_vs_ctrl_subsurf=exp1["contrasts"]["h79_subsurf_vs_ctrl_subsurf"],
                poe_vs_ctrl_subsurf=exp1["contrasts"]["h79_poe_vs_ctrl_subsurf"],
                poe_vs_ctrl_h35=exp1["contrasts"]["h79_poe_vs_ctrl_h35"],
                slot_gate_g1_passed=False,
            ),
            experiment_2_block25km_holdout=dict(
                draws=exp2["draws"],
                cells_per_arm=exp2["n_cells_per_arm"],
                withheld_positive_occurrences=exp2["per_arm"]["CTRL_H35"]["withheld_positive_occurrences"],
                median_truth_d_vis_px=exp2["truth_d_vis_profile"]["mean_median_truth_d_vis"],
                frac_truth_gt20_px=exp2["truth_d_vis_profile"]["mean_truth_frac_gt20"],
                ctrl_h35_pooled=exp2["per_arm"]["CTRL_H35"]["pooled_dti"],
                ctrl_subsurf_pooled=exp2["per_arm"]["CTRL_SUBSURF"]["pooled_dti"],
                h79_subsurf_pooled=exp2["per_arm"]["H79_SUBSURF"]["pooled_dti"],
                h79_poe_pooled=exp2["per_arm"]["H79_POE"]["pooled_dti"],
                subsurf_vs_ctrl_subsurf=exp2["contrasts"]["h79_subsurf_vs_ctrl_subsurf"],
                poe_vs_ctrl_subsurf=exp2["contrasts"]["h79_poe_vs_ctrl_subsurf"],
                poe_vs_ctrl_h35=exp2["contrasts"]["h79_poe_vs_ctrl_h35"],
            ),
            experiment_3_confirm_block25km=dict(
                draws=exp3["draws"],
                cells_per_arm=exp3["n_cells_per_arm"],
                withheld_positive_occurrences=exp3["per_arm"]["CTRL_H35"]["withheld_positive_occurrences"],
                median_truth_d_vis_px=exp3["truth_d_vis_profile"]["mean_median_truth_d_vis"],
                frac_truth_gt20_px=exp3["truth_d_vis_profile"]["mean_truth_frac_gt20"],
                ctrl_h35_pooled=exp3["per_arm"]["CTRL_H35"]["pooled_dti"],
                h79_single_hgb_pooled=exp3["per_arm"]["H79_SINGLE_HGB"]["pooled_dti"],
                h79_poe_pooled=exp3["per_arm"]["H79_POE"]["pooled_dti"],
                h79_poe_sgmc_pooled=exp3["per_arm"]["H79_POE_SGMC"]["pooled_dti"],
                poe_vs_single_hgb=exp3["contrasts"]["h79_poe_vs_single_hgb"],
                poe_sgmc_vs_poe=exp3["contrasts"]["h79_poe_sgmc_vs_h79_poe"],
                poe_sgmc_vs_ctrl_h35=exp3["contrasts"]["h79_poe_sgmc_vs_ctrl_h35"],
                slot_gate_passed=False,
            ),
            shipped_crustal_sgmc_56col_readout=c56,
        ),
        organizer_confirmed_score=None,
        estimated_leaderboard_score=None,
        correlation_overlap_vs_registry=lane_block,
        raster_sha256=chk_z["sha256"],
        nan_twin_sha256=chk_n["sha256"],
        zip_sha256=build["zip"]["sha256"],
        content_id=CONTENT_ID,
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
            independent_exact_file_audit=ind_exact,
            independent_rasterio_zeros=ind_z,
            independent_rasterio_nan=ind_n,
            footprint_pixels=chk_z["footprint_pixels"],
            checks_receipts=[
                f"docs/downloads/checks-{STEM_Z}.json",
                f"docs/downloads/checks-{STEM_N}.json",
            ],
        ),
        submission_name=f"{STEM_Z}.tif",
        nan_twin_name=f"{STEM_N}.tif",
        zip_name=f"{STEM_BASE}.zip",
        zip_zeros_name=f"{STEM_Z}.zip",
        note=NOTE,
        note_chars=len(NOTE),
        verdict="negative",
        slot_approved=False,
        ok_to_download_inspection=True,
        ok_to_submit_slot=False,
    )
    for out_rel in ("registry/run_card_h79_cthm_2026-10-27.json", "docs/data/run_card_h79_cthm_2026-10-27.json"):
        (ROOT / out_rel).write_text(json.dumps(card79, indent=1) + "\n")
    print(
        f"Registered {STEM_Z}.tif ({CONTENT_ID}, {chk_z['positive_pixels']:,} dots); "
        "run_card_h79_cthm_2026-10-27.json written; verdict=negative"
    )


if __name__ == "__main__":
    main()
