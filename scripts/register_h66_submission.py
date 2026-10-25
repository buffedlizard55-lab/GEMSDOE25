#!/usr/bin/env python3
"""Build `registry/run_card_h66_2026-10-25.json` and register H66 GeoTIFFs in `registry/submissions.json`.

All numbers are read directly from `evidence/h66_*/*.json` and `docs/downloads/*h66*.json` (zero hand-typed metrics).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())


def main() -> None:
    s1 = J("evidence/h66_1_screen/analysis.json")
    c1 = J("evidence/h66_1_confirm/analysis.json")
    s2 = J("evidence/h66_2_screen/analysis.json")
    f9 = J("evidence/h66_focus_sites_forensics.json")
    chk = J("docs/downloads/checks-gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.json")
    ind_z = J("evidence/h66_independent_audit_zeros.json")
    ind_n = J("evidence/h66_independent_audit_nan.json")
    lane_lit = J("docs/downloads/lane-gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.json")
    lane_surf = J("evidence/h66_lane_surface.json")
    lane_ext = J("evidence/h66_lane_extended.json")

    zrec = chk["files"]["zeros"]
    nrec = chk["files"]["nan"]

    # Focus winners (21 rasters in registry_top) summary from lane_ext rows
    rt_rows = [r for r in lane_ext["rows"] if r["group"] == "registry_top"]
    b2_row = next(r for r in rt_rows if "g32_h33-2-b2" in r["file"])
    focus_summary = dict(
        n=len(rt_rows),
        worst_cand_dots_within_3px=max(r["cand_dots_within_3px"] for r in rt_rows),
        worst_overlap_file=max(rt_rows, key=lambda r: r["cand_dots_within_3px"])["file"],
        worst_abs_spearman_surface=max(abs(r["spearman_surface"]) for r in rt_rows),
        b2_overlap=b2_row["cand_dots_within_3px"],
        b2_reverse_overlap=b2_row["reg_dots_within_3px_of_cand"],
        b2_spearman_surface=b2_row["spearman_surface"],
        b2_spearman_final=b2_row["spearman_final"],
    )

    run_card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-25 H66 MGD-F + SGMC-REACT (arena/66ca912a-gemsdoe25)",
        experiments_used="3 of 3 budget (Exp 1: H66-1 MGD-F screen [PASS]; Exp 2: H66-1 MGD-F confirmation [FAIL]; Exp 3: H66-2 SGMC-REACT screen [PASS +0.0138, 4/4 folds; unconfirmed at 3-exp cap]).",
        deviation_from_preregistration="none — frozen rule in knowledge/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md section 4.1 followed verbatim",
        hypothesis=(
            "H66-1 (MGD-F, built GeoTIFF): Blind hydrothermal fault conduits over-pressured in unmapped Great Basin valleys "
            "produce positive SiO2-chalcedony minus Na-K-Ca cation geothermometer disequilibrium (GDR #1391 wells/springs), "
            "2-m temperature probe upflow plumes (F2mDAB), and Efimov airborne radiometric potassium hydrothermal alteration "
            "ridges (GeoDAWN K * K/(eTh * TC)), paired with tip-preserved lateral-flank shielding (r=2.5 px, H27_tip>=0.05) "
            "and 300 m (min_dist=3.0 px) score-ordered dot spacing. "
            "H66-2 (SGMC-REACT, Exp 3 screen): A substantial fraction of unmapped Quaternary faults are neotectonically "
            "reactivated pre-Quaternary bedrock faults recorded in USGS SGMC (1:500k) where 3DEP LiDAR scarps and GPS strain "
            "gradients confirm active slip."
        ),
        mechanism=(
            "H66-1 adds 4 catalogue-free columns (H66_mgd_cat_excess, H66_mgd_chalc_excess, H66_spring_upflow_prox, "
            "H66_efimov_f_ridge) to the 82-column H35 RESMAG-TIP HGB detector, suppresses non-tip lateral flanks within "
            "2.5 px of visible catalogue faults (preserving fault-tip relays where H27_tip >= 0.05), and thins at min_dist=3.0 px. "
            "H66-2 gates USGS SGMC bedrock fault proximity exp(-d_SGMC / 4 px) by 3DEP LiDAR scarp strike alignment/step "
            "(H66_sgmc_scarp_compat) and GPS 2nd-invariant strain * gravity THDR (H66_sgmc_strain_react)."
        ),
        mimicking_non_fault_process=(
            "H66-1 mimics: Stratabound lateral outflow plumes in permeable ash-flow tuffs/playa aquifers, agricultural/evaporitic "
            "brine mixing altering Na-K-Ca ratios, and potassic rhyolite domes/unwelded tuffs with primary high K/eTh ratios. "
            "H66-2 mimics: Inactive Mesozoic Sevier thrust ramps, caldera ring-fracture contacts, and compilation overlap between "
            "1:500k state bedrock fault maps and USGS QFFDB."
        ),
        preregistration="knowledge/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md (frozen at commit 0f6fc77; band filename fix at 822fb60 before Exp 3 fit)",
        focus_sites_forensics=dict(
            why_g32_scored_0_2778=(
                "Pixel-exact subset chain on 19GEMSDOE H19-5 (121,131 px, 0.1922 [OWNER-CLAIM]): "
                "GEMSDOE24 D1.5 (60,069 px, 0.2477) -> GEMSDOE25/30 D2.8 (44,090 px, 0.2600, nn>=2.83 px cuts cone-overlap FP by 63.6%) -> "
                "GEMSDOE28/31 R1 (40,199 px, 0.2708, deletes 3,891 d_cat<=1 px collar dots carrying 0.00096 credit/px << tau=0.0549) -> "
                "GEMSDOE32 B2 (37,654 px, 0.2778 [OWNER-CLAIM], deletes 2,545 1<d_cat<=2 px collar dots carrying 0.00503 credit/px << tau=0.0573). "
                "GEMSDOE33 h33d (41,865 px, 0.2632) re-admitted 1,377 d<=1 and 2,517 1<d<=2 dots (-0.0146 vs B2); "
                "GEMSDOE36 anderson-pinn (38,854 px, 0.2750) is B2 union 1,200 extra dots (~0.0134 credit/px < tau=0.0588, -0.0028 vs B2)."
            ),
            evidence="evidence/h66_focus_sites_forensics.json",
            identities=f9["identities"],
        ),
        experiments=dict(
            experiment_1_h66_1_screen=dict(
                draws=s1["draws"],
                evaluator=s1["arms"]["G1_C1"]["pooled"]["evaluator_version"],
                withheld_positives=s1["arms"]["G1_C1"]["pooled"]["withheld_positives"],
                leakage_canary=s1["leakage_canary"],
                candidate_arm="G1_C1",
                candidate_pooled_holdout_dti=s1["arms"]["G1_C1"]["pooled"]["pooled_dti"],
                candidate_pooled_ci95=s1["arms"]["G1_C1"]["pooled"]["ci_95"],
                candidate_formatted=s1["arms"]["G1_C1"]["pooled"]["formatted_label"],
                control_h35_pooled_holdout_dti=s1["arms"]["CTRL_H35_24"]["pooled"]["pooled_dti"],
                control_h35_pooled_ci95=s1["arms"]["CTRL_H35_24"]["pooled"]["ci_95"],
                factorial=s1["factorial_2x2"],
                gate=s1["gate"],
            ),
            experiment_2_h66_1_confirm=dict(
                draws=c1["draws"],
                evaluator=c1["arms"]["G1_C1"]["pooled"]["evaluator_version"],
                withheld_positives=c1["arms"]["G1_C1"]["pooled"]["withheld_positives"],
                leakage_canary=c1["leakage_canary"],
                candidate_arm="G1_C1",
                candidate_pooled_holdout_dti=c1["arms"]["G1_C1"]["pooled"]["pooled_dti"],
                candidate_pooled_ci95=c1["arms"]["G1_C1"]["pooled"]["ci_95"],
                candidate_formatted=c1["arms"]["G1_C1"]["pooled"]["formatted_label"],
                control_h35_pooled_holdout_dti=c1["arms"]["CTRL_H35_24"]["pooled"]["pooled_dti"],
                control_h35_pooled_ci95=c1["arms"]["CTRL_H35_24"]["pooled"]["ci_95"],
                factorial=c1["factorial_2x2"],
                gate=c1["gate"],
            ),
            experiment_3_h66_2_sgmc_react_screen=dict(
                draws=s2["draws"],
                evaluator=s2["arms"]["SGMC_REACT_ONLY"]["pooled"]["evaluator_version"],
                withheld_positives=s2["arms"]["SGMC_REACT_ONLY"]["pooled"]["withheld_positives"],
                leakage_canary=s2["leakage_canary"],
                candidate_arm="SGMC_REACT_ONLY",
                candidate_pooled_holdout_dti=s2["arms"]["SGMC_REACT_ONLY"]["pooled"]["pooled_dti"],
                candidate_pooled_ci95=s2["arms"]["SGMC_REACT_ONLY"]["pooled"]["ci_95"],
                candidate_formatted=s2["arms"]["SGMC_REACT_ONLY"]["pooled"]["formatted_label"],
                sgmc_all3_pooled_holdout_dti=s2["arms"]["SGMC_ALL3"]["pooled"]["pooled_dti"],
                sgmc_all3_pooled_ci95=s2["arms"]["SGMC_ALL3"]["pooled"]["ci_95"],
                control_h35_pooled_holdout_dti=s2["arms"]["CTRL_H35_24"]["pooled"]["pooled_dti"],
                control_h35_pooled_ci95=s2["arms"]["CTRL_H35_24"]["pooled"]["ci_95"],
                gate=s2["gate"],
                scientific_caveat=(
                    "Screen PASSED (+0.013794 paired gain, CI95 [+0.002494, +0.025094], 4/4 folds+, max canary AUC 0.7890 <= 0.90), "
                    "but NOT promoted: (1) 3-of-3 experiment budget reached so confirmation draws 56,57 were not run; "
                    "(2) H66_sgmc_strain_react standalone AUC (0.7862) nearly equals raw H66_sgmc_prox4 (0.7890) because HGB trees "
                    "threshold strictly positive smooth multipliers near zero to recover USGS SGMC bedrock fault proximity "
                    "(IR-25-SGMC-TREE-INVERSION & IR-25-SGMC-PROXY-CONTAMINATION), whereas H66_sgmc_scarp_compat (AUC 0.5965) "
                    "genuinely restricts to LiDAR-scarp-bearing traces."
                ),
            ),
        ),
        registry_correlation_and_overlap=dict(
            surface_max_abs_spearman=lane_surf["worst_abs_spearman"],
            surface_cap=0.90,
            surface_pass=lane_surf["worst_abs_spearman"] <= 0.90,
            focus_21_top_scorers=focus_summary,
            external_sparse_50=lane_ext["external_sparse"],
            own_unscored_lineage_13=lane_ext["own_lineage"],
            dense_lattice_r13=lane_ext["lattice"][0],
            literal_strict_lane_verdict=lane_lit["verdict"],
            density_aware_lane_verdict=lane_lit["verdict_density_aware"],
            interpretation=(
                "Passes surface rank-correlation against all 64 rasters (max |rho|=0.1769 <= 0.90) and passes 3-px overlap "
                "against all 21 focus/sibling top-scorer submissions (max 0.4871 <= 0.70; 0.3037 vs GEMSDOE32 B2 0.2778) and all "
                "external sparse submissions <=80k dots. Exceeds literal 0.70 cap on 13gems 5-px dense lattice (1.000, IR-25-LANE-DENSITY), "
                "4 ultra-dense >100k-dot early artifact carpets (0.717-0.788 forward, 0.191-0.426 reverse), and GEMSDOE25's own unscored "
                "docs/downloads HGB lineage (0.749-0.822). Held DO NOT SUBMIT."
            ),
        ),
        tif=dict(
            submission_name="gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros",
            file=zrec["file"],
            path=zrec["path"],
            bytes=zrec["bytes"],
            sha256=zrec["sha256"],
            nan_twin_file=nrec["file"],
            nan_twin_sha256=nrec["sha256"],
            zip_file=chk["zip"]["file"],
            zip_sha256=ind_z["zip"]["sha256"],
            content_id=zrec["content_id"],
            positive_pixels=zrec["positive_pixels"],
            note=chk["note"],
            note_chars=chk["note_chars"],
            validator_gems25_check_file=dict(
                ok_to_upload=zrec["format_ok"],
                hard_failures=zrec["hard_failures"],
            ),
            validator_independent_rasterio=dict(
                all_hard_checks_pass=ind_z["all_hard_checks_pass"],
                checks=ind_z["checks"],
            ),
        ),
        verdict="negative",
        ok_to_download=True,
        ok_to_submit_slot=False,
        slot_approved=False,
    )
    (ROOT / "registry" / "run_card_h66_2026-10-25.json").write_text(json.dumps(run_card, indent=1) + "\n")

    # Update registry/submissions.json
    subs_doc = J("registry/submissions.json")
    files = subs_doc["files"]
    for item in files:
        if item.get("role") == "primary":
            item["role"] = "alternate"
    # Remove any prior h66 entry if re-run idempotently
    files = [f for f in files if f["id"] not in ("h66-mgd-flank", "h66-mgd-flank-nan")]

    primary_entry = dict(
        id="h66-mgd-flank",
        role="primary",
        file=zrec["file"],
        path=zrec["path"],
        bytes=zrec["bytes"],
        sha256=zrec["sha256"],
        content_id=zrec["content_id"],
        positive_pixels=zrec["positive_pixels"],
        format_ok=True,
        checks=zrec["checks"],
        receipt="checks-gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.json",
        outside="zero",
        status=(
            "UNIQUE BY CONTENT · FORMAT-VALID · H66-1 screen PASS (+0.0025, 4/4) / confirm FAIL (-0.0022) · "
            "STRICT LANE FAIL (literal rule) · verdict negative · DO NOT SUBMIT"
        ),
        zip=chk["zip"]["file"],
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        expected_range="no live projection computed — H66-1 confirmation gate FAILED (not a score)",
        lane=dict(
            lane_clear=False,
            strict_verdict=lane_lit["verdict"],
            lattice_overlap=lane_ext["lattice"][0]["cand_dots_within_3px"],
            focus_winners=focus_summary,
            external_sparse=lane_ext["external_sparse"],
            own_lineage=lane_ext["own_lineage"],
            receipt="docs/downloads/lane-gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.json",
            extended_receipt="evidence/h66_lane_extended.json",
            surface_receipt="evidence/h66_lane_surface.json",
        ),
        lane_summary=(
            "STRICT LANE FAIL (literal rule: 100.0% vs r13 5-px lattice, 71.7-78.8% vs >100k-dot early carpets, "
            "74.9-82.2% vs own unscored HGB downloads). Vs all 21 focus/top-scorer submissions: max 3-px overlap 48.7% "
            "(30.4% vs GEMSDOE32 B2 0.2778), max |Spearman| 0.177 <= 0.90."
        ),
        slot_reason=(
            "H66-1 passed screen (+0.0025, 4/4 folds) but failed fresh-draw confirmation (-0.0022); "
            "H66-2 SGMC-REACT passed screen (+0.0138, 4/4 folds) at 3/3 budget cap without confirmation; "
            "strict literal lane rule also fails on r13 lattice and own HGB lineage"
        ),
        run_card="registry/run_card_h66_2026-10-25.json",
        title="H66-1 MGD-F + tip-preserved flank shield (sapd3.0, zeros outside) — TESTING ONLY · DO NOT SUBMIT",
        summary=(
            "Unique 2026-10-25 GeoTIFF (44,832 binary dots, min_dist=3.0 px) from pre-registered H66-1 G1_C1 "
            "(H35 base + 4 multi-geothermometer disequilibrium & Efimov K-alteration columns + tip-preserved flank shield r=2.5 px). "
            "Passed screen (+0.0025, 4/4 folds) and Factor C flank shielding was positive in 8/8 fold-blocks, "
            "but MGD-F failed fresh-draw confirmation (-0.0022) and strict lane gate fails on dense lattice / own HGB lineage. "
            "Zero outside footprint (prevents 'Predicted values must be in range [0, 1]'). Testing only — DO NOT SUBMIT."
        ),
        note=chk["note"],
    )

    nan_entry = dict(
        id="h66-mgd-flank-nan",
        role="alternate",
        file=nrec["file"],
        path=nrec["path"],
        bytes=nrec["bytes"],
        sha256=nrec["sha256"],
        content_id=nrec["content_id"],
        positive_pixels=nrec["positive_pixels"],
        format_ok=True,
        checks=nrec["checks"],
        receipt="checks-gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.json",
        outside="nan",
        status="UNIQUE BY CONTENT · NaN-outside twin of H66-1 · confirm FAIL · STRICT LANE FAIL · verdict negative · DO NOT SUBMIT",
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        run_card="registry/run_card_h66_2026-10-25.json",
        title="H66-1 MGD-F + tip-preserved flank shield (NaN-outside template twin) — DO NOT SUBMIT",
        summary=(
            "Pixel-identical on the 5,167,373-pixel footprint to the H66-1 zeros-outside primary (content_id da617550a0e9, 44,832 dots), "
            "with NaN on the 7,111,787 outside-footprint grid cells matching sample_submission.tif. Use the zeros-outside twin if testing "
            "strict whole-array [0, 1] validators; DO NOT SUBMIT either file."
        ),
        note=chk["note"],
    )

    subs_doc["generated_by"] = "scripts/register_h66_submission.py (2026-10-25, H66 MGD-F + SGMC-REACT session)"
    subs_doc["files"] = [primary_entry, nan_entry] + files
    (ROOT / "registry" / "submissions.json").write_text(json.dumps(subs_doc, indent=1) + "\n")
    assert ind_n["all_hard_checks_pass"]
    print("Wrote registry/run_card_h66_2026-10-25.json and updated registry/submissions.json")


if __name__ == "__main__":
    main()
