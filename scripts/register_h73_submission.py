#!/usr/bin/env python3
"""Emit registry/run_card_h73_2026-10-26.json and register the H73-PM GeoTIFFs.

Every number is read from saved receipts (evidence/h73_pm_screen/analysis.json,
evidence/h73_build/build_receipt.json, lane JSONs, checks JSONs) — nothing is recomputed
or invented here. Verdict is negative: both pre-registered gates failed (knowledge/32).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEM_Z = "gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros"
STEM_N = STEM_Z.replace("-zeros", "-nan")


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def main() -> None:
    raise SystemExit("Historical registration retired: density-aware wording cannot override literal lane failure. Do not re-register these files.")
    ana = J("evidence/h73_pm_screen/analysis.json")
    build = J("evidence/h73_build/build_receipt.json")
    chk_z = J(f"docs/downloads/checks-{STEM_Z}.json")
    chk_n = J(f"docs/downloads/checks-{STEM_N}.json")
    lane_lit = J(f"docs/downloads/lane-{STEM_Z}.json")
    lane_ext = J("evidence/h73_lane_extended.json")
    lane_surf = J("evidence/h73_lane_surface.json")
    ind_z = J("evidence/h73_independent_audit_zeros.json")

    pa = ana["per_arm"]
    slot = ana["slot_gate"]
    far = ana["far_field_screen"]
    rt = [r for r in lane_ext["rows"] if r["group"] == "registry_top"]
    b2 = next(r for r in rt if r["file"] == "g32_h33-2-b2_0.2778.tif")
    note = build["note"]
    assert len(note) <= 140 and "DO NOT SUBMIT" in note and "unscored" in note
    assert build["verdict"] == "negative" and build["slot_approved"] is False
    assert slot["passed"] is False and far["passed"] is False

    lane_block = dict(
        lane_clear=False,
        strict_verdict=lane_lit["verdict"],
        density_aware_verdict=lane_lit["verdict_density_aware"],
        flagged_lane=lane_lit["flagged_lane"],
        flagged_literal=lane_lit["flagged_literal"],
        registry_checked=lane_lit["registry_checked"],
        surface_worst_abs_spearman=lane_surf["worst_abs_spearman"],
        focus_winners=dict(
            n=len(rt),
            worst_cand_dots_within_3px=max(r["cand_dots_within_3px"] for r in rt),
            worst_overlap_file=max(rt, key=lambda r: r["cand_dots_within_3px"])["file"],
            b2_overlap=b2["cand_dots_within_3px"],
            b2_reverse_overlap=b2["reg_dots_within_3px_of_cand"],
            b2_spearman_surface=b2["spearman_surface"],
            b2_spearman_final=b2["spearman_final"],
        ),
        external_sparse=lane_ext["external_sparse"],
        own_lineage=lane_ext["own_lineage"],
        receipt=f"docs/downloads/lane-{STEM_Z}.json",
        extended_receipt="evidence/h73_lane_extended.json",
        surface_receipt="evidence/h73_lane_surface.json",
    )
    lane_summary = (
        "DENSITY-AWARE UNIQUE (flagged_lane = [] across 80 literal-checker rasters; surface |Spearman| "
        f"{lane_surf['worst_abs_spearman']:.3f} <= 0.90). Literal 70% flags only the dense r13 lattice "
        "(206,895 dots, ~100% 3-px halo — geometrically unavoidable at this budget, "
        "knowledge/29_lane_feasibility_plan). Final-dot overlap: "
        f"{100 * b2['cand_dots_within_3px']:.1f}% vs GEMSDOE32 B2 (0.2778 OWNER-REPORTED), worst "
        f"{100 * max(r['cand_dots_within_3px'] for r in rt):.1f}% across {len(rt)} registry_top rasters, "
        f"worst {100 * lane_ext['own_lineage']['worst_cand_dots_within_3px']:.1f}% own-lineage."
    )
    status = (
        "UNIQUE BY CONTENT (density-aware) · FORMAT-VALID · HOLDOUT FAIL vs CTRL_H35 (slot gate FAIL, "
        "far-field screen FAIL) · verdict negative · DO NOT SUBMIT"
    )
    slot_reason = (
        f"Pre-registered Experiment 1 (draws 90-91, {ana['n_cells_per_arm']} cells/arm) failed the slot gate: "
        f"PM_DEAPRON pooled HOLDOUT-DTI {pa['PM_DEAPRON']['pooled_dti']:.5f} vs same-run CTRL_H35 "
        f"{pa['CTRL_H35']['pooled_dti']:.5f} (paired {slot['paired_gain']:+.5f}, cluster 95% CI "
        f"[{slot['paired_ci95'][0]:+.5f}, {slot['paired_ci95'][1]:+.5f}]); far-field screen also failed "
        f"(pooled far DTI {pa['PM_DEAPRON']['pooled_far_dti']:.5f} vs CTRL_H35 {pa['CTRL_H35']['pooled_far_dti']:.5f}, "
        f"although +{far['pooled_far_gain_vs_blind']:.5f} vs CTRL_BLIND_BD in {far['folds_positive_vs_blind']}/4 folds). "
        "Experiments 2-3 not run per frozen rule. Not slot-approved."
    )
    summary = (
        f"Unique 2026-10-26 GeoTIFF ({build['positive_pixels']:,} binary dots, min_dist=2.8 px, d_cat > 2.0 px; "
        f"d_cat strata 2-9px {100 * build['d_cat_strata']['frac_2_9']:.1f}%, >20px {100 * build['d_cat_strata']['frac_gt20']:.1f}%) "
        "from pre-registered H73-PM: H35 feature stack retrained with propensity-matched negatives in d_vis bins "
        "(sampler removes the catalogue-apron prior tilt; no new feature). Strict lane gate flags only the dense "
        "r13 lattice; density-aware unique. HOLDOUT-DTI (PM_DEAPRON arm) "
        f"{pa['PM_DEAPRON']['pooled_dti']:.5f} on {pa['PM_DEAPRON']['withheld_positive_occurrences']:,} withheld-positive "
        "occurrences — a catalogue-gap proxy, not a live score. Finite [0,1] in footprint — DO NOT SUBMIT."
    )

    def entry(stem: str, chk: dict, outside: str, id_: str, role: str):
        return dict(
            id=id_, role=role, file=f"{stem}.tif", path=f"docs/downloads/{stem}.tif",
            bytes=chk["bytes"], sha256=chk["sha256"], content_id=build["content_id"],
            positive_pixels=chk["positive_pixels"], format_ok=bool(chk["format_valid"]),
            checks=chk["checks"], receipt=f"checks-{stem}.json", outside=outside, status=status,
            zip=f"{STEM_Z}.zip" if outside == "zero" else None,
            verdict="negative", slot_approved=False, do_not_resubmit=True,
            ok_to_download=True, ok_to_submit_slot=False,
            expected_range="no live projection computed — H73-PM Exp 1 FAIL vs CTRL_H35 (not a score)",
            lane=lane_block, lane_summary=lane_summary, slot_reason=slot_reason,
            run_card="registry/run_card_h73_2026-10-26.json",
            title=f"H73-PM propensity-matched H35 de-aproned HGB (sapd2.8, {outside} outside) — TESTING ONLY · DO NOT SUBMIT",
            summary=summary, note=note,
        )

    for reg_path in ("registry/submissions.json", "docs/data/submissions.json"):
        reg = J(reg_path)
        reg["files"] = [f for f in reg["files"] if f["id"] not in ("h73-pm-deapron", "h73-pm-deapron-nan")]
        reg["files"] = [
            entry(STEM_Z, chk_z, "zero", "h73-pm-deapron", "research-h73"),
            entry(STEM_N, chk_n, "nan", "h73-pm-deapron-nan", "research-h73-nan"),
        ] + reg["files"]
        reg["generated_by"] = "scripts/register_h73_submission.py (2026-10-26, H73-PM session); prior: " + str(reg.get("generated_by", ""))
        (ROOT / reg_path).write_text(json.dumps(reg, indent=1) + "\n")

    card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-26 H73-PM propensity-matched H35 (arena/11c66d52-gemsdoe25)",
        experiments_used="1 of 3 budget (Exp 1 draws 90-91; Exp 2 confirmation and Exp 3 slot-build not run — frozen gate rule, knowledge/32 §2; research build logged as IR-25-H73-BUILD-AFTER-GATE-FAIL)",
        hypothesis="H73-PM: matching the training-negative d_vis histogram to the positives' removes the catalogue-apron prior tilt, forcing the H35 HGB to use scarp/potential-field evidence and emit B2-like far-field geometry with higher live credit density.",
        mechanism="Negatives resampled per d_vis bin ([0,2],(2,5],(5,9],(9,15],(15,25],(25,40],(40,80],>80 px) proportional to positive bin shares (gems25.h73_pm.propensity_matched_negatives); H35 columns, HGB params and de-apron emission unchanged.",
        named_non_fault_mimic="Pluvial Lake Lahontan shoreline scarps and alluvial-fan channel levees far from mapped faults (linear DEM breaks a de-biased model may over-fire on).",
        holdout_dti=dict(
            label="HOLDOUT-DTI",
            evaluator=ana["evaluator"],
            cells_per_arm=ana["n_cells_per_arm"],
            withheld_positive_occurrences=pa["PM_DEAPRON"]["withheld_positive_occurrences"],
            far_withheld_positive_occurrences=pa["PM_DEAPRON"]["far_withheld_positive_occurrences"],
            pm_deapron_pooled=pa["PM_DEAPRON"]["pooled_dti"],
            pm_deapron_ci95=ana["overall_pm_deapron_vs_h35"]["arms"]["PM_DEAPRON"]["ci95"],
            ctrl_h35_pooled=pa["CTRL_H35"]["pooled_dti"],
            ctrl_blind_pooled=pa["CTRL_BLIND_BD"]["pooled_dti"],
            pm_h35_pooled=pa["PM_H35"]["pooled_dti"],
            paired_gain_vs_h35=slot["paired_gain"],
            paired_ci95_vs_h35=slot["paired_ci95"],
            fold_gains_vs_h35=slot["fold_gains"],
            pooled_far_dti=dict(pm_deapron=pa["PM_DEAPRON"]["pooled_far_dti"], ctrl_h35=pa["CTRL_H35"]["pooled_far_dti"], ctrl_blind=pa["CTRL_BLIND_BD"]["pooled_far_dti"]),
            far_gain_vs_blind=far["pooled_far_gain_vs_blind"],
            far_folds_positive_vs_blind=far["folds_positive_vs_blind"],
            slot_gate_passed=False,
            far_field_screen_passed=False,
            leakage_canary=dict(cap=0.90, max_fitted_column_auc=ana["canary"]["max_canary_auc"], neg_dvis_auc=ana["canary"]["max_neg_dvis_canary_auc"], passed=True),
        ),
        organizer_confirmed_score=None,
        correlation_overlap_vs_registry=lane_block,
        raster_sha256=chk_z["sha256"],
        nan_twin_sha256=chk_n["sha256"],
        content_id=build["content_id"],
        positive_pixels=build["positive_pixels"],
        d_cat_strata_full_build=build["d_cat_strata"],
        validator_output=dict(
            format_valid=bool(chk_z["format_valid"] and chk_n["format_valid"]),
            hard_failures_zeros=chk_z["hard_failures"],
            hard_failures_nan=chk_n["hard_failures"],
            independent_audit_all_hard_pass=bool(ind_z["all_hard_checks_pass"]),
            footprint_pixels=chk_z["footprint_pixels"],
            checks_receipts=[f"docs/downloads/checks-{STEM_Z}.json", f"docs/downloads/checks-{STEM_N}.json"],
        ),
        submission_name=f"{STEM_Z}.tif",
        note=note,
        note_chars=len(note),
        verdict="negative",
        slot_approved=False,
        ok_to_download_inspection=True,
        ok_to_submit_slot=False,
    )
    (ROOT / "registry" / "run_card_h73_2026-10-26.json").write_text(json.dumps(card, indent=1) + "\n")
    (ROOT / "docs" / "data" / "run_card_h73_2026-10-26.json").write_text(json.dumps(card, indent=1) + "\n")
    print(f"registered h73-pm-deapron ({build['content_id']}, {build['positive_pixels']} dots); run card written; verdict negative")


if __name__ == "__main__":
    main()
