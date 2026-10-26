#!/usr/bin/env python3
"""Build registry/run_card_objective_2026-10-26.json and register the session candidate as primary download.

All metrics are read from evidence/ analyzer JSONs and docs/downloads receipts (no hand-typed numbers
except the frozen text fields). Session verdict is NEGATIVE: none of the three pre-registered
experiments beat the same-run BIN comparator, so the candidate (BIN protocol, fresh production
seeds) is downloadable for testing only and is NOT slot-approved.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "gems25-obj-bin-greedy-k3p5-20261026-3646faf70507"


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def exp_block(res: dict, primary_key: str, label: str) -> dict:
    c = res["contrasts"][primary_key]
    bin_arm = res["arms"]["BIN-greedy"]
    cand_arm = res["arms"][primary_key.split("_vs_")[0]]
    return dict(
        label=label, draws=res["draws"], evaluator=res["evaluator"], evaluator_version=res["evaluator_version"],
        withheld_positives_total=res["withheld_positives_total"],
        withheld_positives_per_fold=res["withheld_positives_per_fold"],
        bin_greedy=dict(fold_mean_dti=bin_arm["dti"]["mean"], fold_mean_ci95=bin_arm["dti"]["ci95"],
                        pooled_dti=bin_arm["pooled_dti"]),
        candidate_greedy=dict(fold_mean_dti=cand_arm["dti"]["mean"], fold_mean_ci95=cand_arm["dti"]["ci95"],
                               pooled_dti=cand_arm["pooled_dti"]),
        paired=dict(mean_gain=c["standard"]["mean"], ci95=c["standard"]["ci95"],
                    folds_positive=c["standard"]["folds_positive"], worst_fold=c["standard"]["worst_fold"],
                    pooled_delta=c["standard"]["pooled_delta"],
                    pooled_delta_boot_ci95=c["pooled_delta_boot_ci95"],
                    offcat_pooled_delta=c["offcat"]["pooled_delta"], hug_delta=c["hug_delta"]),
        leakage_canary=res["leakage_canary"], gate=res["gate"], verdict=res["verdict"],
    )


def main() -> None:
    e1 = J("evidence/tent_screen_2026-10-26/results.json")
    e2 = J("evidence/hardneg_screen_2026-10-26/results.json")
    e3 = J("evidence/ign3_screen_2026-10-26/results.json")
    chk = J(f"docs/downloads/checks-{BASE}-zeros.json")
    ind_z = J("evidence/objective_independent_audit_zeros.json")
    ind_n = J("evidence/objective_independent_audit_nan.json")
    lane_ext = J("evidence/objective_lane_extended.json")
    lane_lit = J(f"docs/downloads/lane-{BASE}-zeros.json")
    focus = J("evidence/focus_audit_local_2026-10-26.json")

    zrec, nrec = chk["files"]["zeros"], chk["files"]["nan"]
    note = chk["note"]
    assert len(note) <= 140 and "DO NOT SUBMIT" in note and chk["note_chars"] == len(note)
    assert ind_z["all_hard_checks_pass"] and ind_n["all_hard_checks_pass"] and zrec["format_ok"] and not zrec["hard_failures"]
    assert e1["gate"]["passed"] is False and e2["gate"]["passed"] is False and e3["gate"]["passed"] is False

    b2 = next(r for r in lane_ext["rows"] if r["file"] == "g32_h33-2-b2_0.2778.tif")
    ext = lane_ext["external_sparse"]
    own = lane_ext["own_lineage"]
    bin_e1 = e1["arms"]["BIN-greedy"]

    run_card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-26 training-objective lane (arena/f1967d4f-gemsdoe25)",
        preregistrations=[
            "knowledge/29_ranked_hypotheses_and_preregistration_2026-10-26.md (commit 005e115, before any fit)",
            "knowledge/30_preregistered_ign3_experiment3_2026-10-26.md (commit 7806b5c, before Exp-3 fit; draws 90-91 burned for IGN3)",
        ],
        experiments_used="3 of 3 (Exp1 TENT screen draws 90-91 FAIL; Exp2 HARDNEG screen draws 94-95 FAIL; Exp3 IGN3 screen draws 100-101 FAIL; no confirmations run because no screen passed)",
        hypothesis=("Training-objective geometry around the pseudo-hidden trace is the unused lever: (1) price the 300 m "
                    "credit ring with the metric's own triangular kernel (TENT regression), (2) mine hard negatives among "
                    "fault-like non-fault lineaments (HARDNEG), or (3) exclude the 1.5-3 px ring from supervision entirely "
                    "(IGN3). Detector columns and greedy emission frozen at the validated H35/H38 stack."),
        mechanism=("USGS/INGENIOUS traces are cartographic polylines offset from the physical scarp; binary training labels "
                   "scarp-crest pixels 1.5-3 px off-trace as negatives although the official metric still pays credit there. "
                   "TENT/IGN3 repair that label geometry; HARDNEG targets the false lineaments that decide the emission head."),
        mimicking_non_fault_process=("Roads/graded tracks, pluvial shoreline benches, lithologic contacts and survey seams are "
                                     "the fault-like non-fault lineaments all three arms must not promote; for TENT the failure "
                                     "mode is blurred localisation + catalogue hugging (observed: hug 0.044->0.093)."),
        experiments=dict(
            experiment_1_tent=exp_block(e1, "TENT-greedy_vs_BIN-greedy", "HOLDOUT-DTI"),
            experiment_2_hardneg=exp_block(e2, "HNEG-greedy_vs_BIN-greedy", "HOLDOUT-DTI"),
            experiment_3_ign3=exp_block(e3, "IGN3-greedy_vs_BIN-greedy", "HOLDOUT-DTI"),
            diagnostic_ign3_in_exp1=dict(
                paired_mean_gain=e1["contrasts"]["IGN3-greedy_vs_BIN-greedy"]["standard"]["mean"],
                pooled_delta=e1["contrasts"]["IGN3-greedy_vs_BIN-greedy"]["standard"]["pooled_delta"],
                note="Hypothesis-generating only; tested as primary in Exp 3 on fresh draws, where it did not replicate.",
            ),
        ),
        holdout_dti_candidate_stack=dict(
            label="HOLDOUT-DTI",
            evaluator=e1["evaluator"], evaluator_version=e1["evaluator_version"],
            reference_screen="Exp1 draws 90-91, BIN-greedy (the candidate's training/emission protocol)",
            fold_mean_dti=bin_e1["dti"]["mean"], fold_mean_ci95=bin_e1["dti"]["ci95"],
            pooled_dti=bin_e1["pooled_dti"], withheld_positives_total=e1["withheld_positives_total"],
            note="Catalogue-gap proxy, not a competition score and not a live projection.",
        ),
        registry_correlation_and_overlap=dict(
            surface_pre_placement=dict(
                worst_abs_spearman_external_sparse=ext["worst_abs_spearman_surface"],
                worst_file=ext["worst_surface_file"],
                worst_abs_spearman_own_lineage=own["worst_abs_spearman_surface"],
                cap=0.90, receipt="evidence/objective_lane_extended.json",
            ),
            final_dots=dict(
                external_sparse=ext, own_lineage=own, lattice=lane_ext["lattice"],
                vs_gemsdoe32_b2=dict(cand_dots_within_3px=b2["cand_dots_within_3px"],
                                     reg_dots_within_3px_of_cand=b2["reg_dots_within_3px_of_cand"],
                                     spearman_surface=b2["spearman_surface"], spearman_final=b2["spearman_final"]),
                strict_verdict=lane_lit["verdict"], density_aware_verdict=lane_lit["verdict_density_aware"],
                cap_overlap=0.70,
            ),
            interpretation=("Unique vs every scored/external sparse registry raster (worst 3-px overlap 0.692 <= 0.70; "
                            "0.320 vs GEMSDOE32 B2; surface |rho| <= 0.108). NOT a new lane vs this repo's own unscored "
                            "HGB lineage (0.872 vs the H38 greedy file — same frozen stack, fresh production seeds) and "
                            "literal lattice overlap is 1.0 (IR-25-LANE-DENSITY). Held DO NOT SUBMIT because no "
                            "experiment beat the same-run comparator and the strict lane policy is not cleared."),
        ),
        focus_sites_audit=dict(
            receipt="evidence/focus_audit_local_2026-10-26.json",
            ranking_by_owner_reported_score=focus["ranking_by_owner_reported_score"],
            identities=focus["identities"],
            evidence_class=focus["evidence_class"],
        ),
        tif=dict(
            submission_name=f"{BASE}-zeros", file=zrec["file"], path=zrec["path"], bytes=zrec["bytes"],
            sha256=zrec["sha256"], content_id=chk["files"]["zeros"]["content_id"],
            positive_pixels=zrec["positive_pixels"],
            nan_twin_file=nrec["file"], nan_twin_sha256=nrec["sha256"],
            zip_file=chk["zip"]["file"], zip_sha256=ind_z["zip"]["sha256"], zip_bytes=chk["zip"]["bytes"],
            note=note, note_chars=len(note),
            scheme=chk["build"]["scheme"], draw_seeds=chk["build"]["draw_seeds"], greedy_diag=chk["build"]["greedy_diag"],
            validator_gems25_check_file=dict(format_ok=zrec["format_ok"], hard_failures=zrec["hard_failures"]),
            validator_independent_rasterio=dict(all_hard_checks_pass=ind_z["all_hard_checks_pass"], checks=ind_z["checks"],
                                                strict_whole_array_0_le_x_le_1=ind_z["checks"]["strict_whole_array_0_le_x_le_1"]),
        ),
        verdict="negative", ok_to_download=True, ok_to_submit_slot=False, slot_approved=False,
        slot_reason=("No pre-registered experiment beat the same-run BIN comparator (TENT -0.0003, HARDNEG -0.0427, "
                     "IGN3 -0.0009 paired fold-mean HOLDOUT-DTI). Candidate is the previously validated BIN/H38 protocol "
                     "with fresh seeds; strict lane fails vs own unscored lineage + literal lattice. Selector must not "
                     "spend a weekly slot on this evidence."),
    )
    (ROOT / "registry" / "run_card_objective_2026-10-26.json").write_text(json.dumps(run_card, indent=1) + "\n")

    subs_doc = J("registry/submissions.json")
    files = [f for f in subs_doc["files"] if f["id"] not in ("obj-bin-greedy", "obj-bin-greedy-nan")]
    for item in files:
        if item.get("role") in ("primary", "fallback"):
            item["role"] = "alternate"
    status = ("UNIQUE BY CONTENT vs scored rasters · FORMAT-VALID · HOLDOUT: 3/3 objective experiments FAIL vs same-run BIN · "
              "STRICT LANE FAIL (own unscored HGB lineage 87.2% + literal lattice) · verdict negative · DO NOT SUBMIT")
    primary = dict(
        id="obj-bin-greedy", role="primary", file=zrec["file"], path=zrec["path"], bytes=zrec["bytes"],
        sha256=zrec["sha256"], content_id=zrec["content_id"], positive_pixels=zrec["positive_pixels"],
        format_ok=True, checks=zrec["checks"], receipt=f"checks-{BASE}-zeros.json", outside="zero",
        status=status, zip=chk["zip"]["file"], verdict="negative", slot_approved=False, do_not_resubmit=True,
        ok_to_download=True, ok_to_submit_slot=False,
        expected_range="no live projection computed — holdout experiments negative vs BIN (not a score)",
        lane=dict(lane_clear=False, strict_verdict=lane_lit["verdict"],
                  density_aware_verdict=lane_lit["verdict_density_aware"],
                  lattice_overlap=lane_ext["lattice"][0]["cand_dots_within_3px"],
                  external_sparse=ext, own_lineage=own,
                  vs_gemsdoe32_b2=run_card["registry_correlation_and_overlap"]["final_dots"]["vs_gemsdoe32_b2"],
                  receipt=f"docs/downloads/lane-{BASE}-zeros.json",
                  extended_receipt="evidence/objective_lane_extended.json"),
        lane_summary=("STRICT LANE FAIL: 87.2% of dots within 3 px of this repo's own unscored H38 greedy file (same frozen "
                      "stack, fresh production seeds) and 100% vs the dense r13 lattice. Unique vs scored/external sparse "
                      f"rasters (worst {100*ext['worst_cand_dots_within_3px']:.1f}% <= 70%; "
                      f"{100*b2['cand_dots_within_3px']:.1f}% vs GEMSDOE32 B2); surface |Spearman| <= "
                      f"{ext['worst_abs_spearman_surface']:.3f} external."),
        slot_reason=run_card["slot_reason"],
        run_card="registry/run_card_objective_2026-10-26.json",
        title="Objective-lane BIN greedy candidate (fresh seeds, zeros outside) — TESTING ONLY · DO NOT SUBMIT",
        summary=(f"Unique-by-content 2026-10-26 GeoTIFF ({zrec['positive_pixels']:,} binary dots) from the frozen H35/H38 "
                 "protocol (BDE+7+tip+H34 HGB, greedy marginal-credit emission) rebuilt with fresh production seeds after "
                 "three pre-registered training-objective experiments (TENT/HARDNEG/IGN3) all failed to beat it on the "
                 "spatially blocked holdout. Format-valid incl. strict whole-array [0,1] (zeros outside prevents the "
                 "'Predicted values must be in range [0, 1]' portal error). Leakage canaries PASS (max 0.63). "
                 "Strict lane fails vs own unscored HGB lineage (87.2%) + dense lattice. Testing only — DO NOT SUBMIT."),
        note=note,
    )
    nan_entry = dict(
        id="obj-bin-greedy-nan", role="fallback", file=nrec["file"], path=nrec["path"], bytes=nrec["bytes"],
        sha256=nrec["sha256"], content_id=nrec["content_id"], positive_pixels=nrec["positive_pixels"],
        format_ok=True, checks=nrec["checks"], receipt=f"checks-{BASE}-zeros.json", outside="nan",
        status="NaN-outside twin of obj-bin-greedy · holdout experiments negative · STRICT LANE FAIL · DO NOT SUBMIT",
        verdict="negative", slot_approved=False, do_not_resubmit=True, ok_to_download=True, ok_to_submit_slot=False,
        run_card="registry/run_card_objective_2026-10-26.json",
        title="Objective-lane BIN greedy (NaN-outside template twin) — DO NOT SUBMIT",
        summary=(f"Pixel-identical on the footprint to the zeros-outside primary (content id {zrec['content_id']}), "
                 "NaN outside. DO NOT SUBMIT either file."),
        note=note,
    )
    subs_doc["generated_by"] = "scripts/register_objective_submission.py (2026-10-26 training-objective session)"
    subs_doc["files"] = [primary, nan_entry] + files
    (ROOT / "registry" / "submissions.json").write_text(json.dumps(subs_doc, indent=1) + "\n")
    print("Wrote registry/run_card_objective_2026-10-26.json; primary ->", primary["file"],
          f"({primary['positive_pixels']} dots, sha {primary['sha256'][:12]}…)")


if __name__ == "__main__":
    main()
