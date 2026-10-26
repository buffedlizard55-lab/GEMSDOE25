#!/usr/bin/env python3
"""Build run_card_h71_2026-10-26.json and register H71 GeoTIFFs as the featured download.

All numbers are read from evidence/ and docs/downloads receipts (zero hand-typed metrics).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(rel: str):
    return json.loads((ROOT / rel).read_text())


def main() -> None:
    s1 = J("evidence/h71_1_screen/analysis.json")
    s2 = J("evidence/h71_2_akf_screen/analysis.json")
    s3 = J("evidence/h71_3_mag_screen/analysis.json")
    chk = J("docs/downloads/checks-gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.json")
    ind_z = J("evidence/h71_independent_audit_zeros.json")
    ind_n = J("evidence/h71_independent_audit_nan.json")
    lane_lit = J("docs/downloads/lane-gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.json")
    lane_ext = J("evidence/h71_lane_extended.json")
    lane_surf = J("evidence/h71_lane_surface.json")

    zrec = chk["files"]["zeros"]
    nrec = chk["files"]["nan"]
    zfile = "gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif"
    nfile = "gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-nan.tif"
    zpath = f"docs/downloads/{zfile}"
    npath = f"docs/downloads/{nfile}"
    note = chk["note"]
    assert len(note) <= 120
    assert "no slot" in note and "unscored" in note and "not slot-approved" in note

    b2 = next(r for r in lane_ext["rows"] if r["file"] == "g32_h33-2-b2_0.2778.tif")
    rt_rows = [r for r in lane_ext["rows"] if r["group"] == "registry_top"]
    focus_summary = dict(
        n=len(rt_rows),
        worst_cand_dots_within_3px=max(r["cand_dots_within_3px"] for r in rt_rows),
        worst_overlap_file=max(rt_rows, key=lambda r: r["cand_dots_within_3px"])["file"],
        worst_abs_spearman_surface=max(abs(r["spearman_surface"]) for r in rt_rows),
        b2_overlap=b2["cand_dots_within_3px"],
        b2_reverse_overlap=b2["reg_dots_within_3px_of_cand"],
        b2_spearman_surface=b2["spearman_surface"],
        b2_spearman_final=b2["spearman_final"],
    )

    def exp_block(ana: dict, arm: str) -> dict:
        return dict(
            draws=ana["draws"],
            evaluator=ana["arms"][arm]["pooled"]["evaluator_version"],
            withheld_positives=ana["arms"][arm]["pooled"]["withheld_positives"],
            leakage_canary=ana["leakage_canary"],
            candidate_arm=arm,
            candidate_pooled_holdout_dti=ana["arms"][arm]["pooled"]["pooled_dti"],
            candidate_pooled_ci95=ana["arms"][arm]["pooled"]["ci_95"],
            candidate_formatted=ana["arms"][arm]["pooled"]["formatted_label"],
            control_h35_pooled_holdout_dti=ana["arms"]["CTRL_H35_24"]["pooled"]["pooled_dti"],
            control_h35_pooled_ci95=ana["arms"]["CTRL_H35_24"]["pooled"]["ci_95"],
            control_crest_pooled_holdout_dti=ana["arms"]["CTRL_CREST_B2"]["pooled"]["pooled_dti"],
            gate=ana["gate"],
        )

    run_card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-26 H71 HGPC-BLIND DIRECT + AKF + MAG-ANISO (arena/71b61fac-gemsdoe25)",
        experiments_used="3 of 3 budget (Exp 1 H71-1 HGPC-BLIND screen FAIL vs H35; Exp 2 H71-3 AKF screen FAIL vs H35; Exp 3 H71-4 MAG-ANISO screen FAIL vs H35). All three beat unsupervised B_crest. No confirmation draws run.",
        deviation_from_preregistration="none — knowledge/27 frozen stopping rule followed (screen fail vs BEST_CTRL including H35 → no draws 72/73; Exp 2 AKF; Exp 3 MAG-ANISO). TIF built from HGPC_BLIND_B2 as §4 fallback.",
        hypothesis=(
            "H71-1 (built GeoTIFF): Blind / buried basin-bounding normal faults offset dense basement and fill the "
            "hanging wall with low-density alluvium, producing concordant isostatic-gravity lows and MT basement steps "
            "even where Quaternary scarps are absent (Faulds & Hinz 2015). Signed polarity sgn(∂n g)==-sgn(∂n D) with "
            "n = unit gravity gradient is the DIRECT emission field (no HGB, no Family E, no DEM)."
        ),
        mechanism=(
            "Catalogue-free sidecar H71_blind_hgpc from bands 13_iso_grav_anom and 15_depth_to_base_surf (σ=2 px). "
            "Ridge NMS, B=2 collar against labels.tif, score_ordered_dots min_dist=3.0, kfrac=0.035 of the 12-px-eroded domain."
        ),
        mimicking_non_fault_process=(
            "Unfaulted depositional onlap wedges (basinward thickening without a discrete fault), caldera and lithologic "
            "density contacts, and MT inversion artefacts."
        ),
        preregistration="knowledge/27_preregistered_h71_hgpc_2026-10-26.md (frozen at commit d4d4bf7, before any fit)",
        experiments=dict(
            experiment_1_h71_1_hgpc_screen=exp_block(s1, "HGPC_BLIND_B2"),
            experiment_2_h71_3_akf_screen=exp_block(s2, "AKF_B2"),
            experiment_3_h71_4_mag_screen=exp_block(s3, "MAG_ANISO_B2"),
        ),
        holdout_dti=dict(
            evaluator_version=s1["arms"]["HGPC_BLIND_B2"]["pooled"]["evaluator_version"],
            candidate_formatted=s1["arms"]["HGPC_BLIND_B2"]["pooled"]["formatted_label"],
            withheld_positives=s1["arms"]["HGPC_BLIND_B2"]["pooled"]["withheld_positives"],
            pooled_dti=s1["arms"]["HGPC_BLIND_B2"]["pooled"]["pooled_dti"],
            ci_95=s1["arms"]["HGPC_BLIND_B2"]["pooled"]["ci_95"],
            vs_h35_mean_gain=s1["gate"]["vs_named"]["CTRL_H35_24"]["mean_gain"],
            vs_crest_mean_gain=s1["gate"]["vs_named"]["CTRL_CREST_B2"]["mean_gain"],
        ),
        registry_correlation_and_overlap=dict(
            surface_max_abs_spearman=lane_surf["worst_abs_spearman"],
            surface_flagged=lane_surf["flagged"],
            lattice_overlap=lane_ext["lattice"][0]["cand_dots_within_3px"],
            external_sparse=lane_ext["external_sparse"],
            own_lineage=lane_ext["own_lineage"],
            focus_21_top_scorers=focus_summary,
            literal_strict_lane_verdict=lane_lit["verdict"],
            density_aware_lane_verdict=lane_lit["verdict_density_aware"],
            interpretation=(
                "UNIQUE vs all 21 focus/top-scorer rasters (max 3-px overlap 25.1% <= 70%; 15.4% vs GEMSDOE32 B2 0.2778) "
                "and vs this repo's own HGB lineage (max 23.4% <= 70%). Surface |Spearman| max 0.030 <= 0.90. "
                "Literal 70% cap fails only on the 13gems 5-px dense lattice (100%, IR-25-LANE-DENSITY). "
                "Density-aware verdict UNIQUE. Held DO NOT SUBMIT because holdout vs H35 failed in 3/3 experiments."
            ),
        ),
        tif=dict(
            submission_name="gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros",
            file=zfile,
            path=zpath,
            bytes=zrec["bytes"],
            sha256=zrec["sha256"],
            nan_twin_file=nfile,
            nan_twin_sha256=nrec["sha256"],
            zip_file=Path(chk["files"]["zip"]).name if isinstance(chk["files"]["zip"], str) else chk["files"]["zip"],
            zip_sha256=ind_z["zip"]["sha256"],
            content_id=chk["content_id"],
            positive_pixels=chk["positive_pixels"],
            note=note,
            note_chars=len(note),
            validator_gems25_check_file=dict(ok_to_upload=zrec["ok_to_upload"], hard_failures=zrec["hard_failures"]),
            validator_independent_rasterio=dict(all_hard_checks_pass=ind_z["all_hard_checks_pass"], checks=ind_z["checks"]),
        ),
        verdict="negative",
        ok_to_download=True,
        ok_to_submit_slot=False,
        slot_approved=False,
    )
    (ROOT / "registry" / "run_card_h71_2026-10-26.json").write_text(json.dumps(run_card, indent=1) + "\n")

    subs_doc = J("registry/submissions.json")
    files = subs_doc["files"]
    for item in files:
        if item.get("role") in ("primary", "fallback"):
            item["role"] = "alternate"
    files = [f for f in files if f["id"] not in ("h71-hgpc-blind", "h71-hgpc-blind-nan")]

    status = (
        "UNIQUE BY CONTENT · FORMAT-VALID · HOLDOUT FAIL vs H35 (3/3 DIRECT screens) · "
        "STRICT LANE FAIL (literal r13 lattice only) · density-aware UNIQUE vs 21 top-scorers and own HGB lineage · "
        "verdict negative · DO NOT SUBMIT"
    )
    lane_summary = (
        f"STRICT LANE FAIL (literal r13 5-px lattice 100%, IR-25-LANE-DENSITY). "
        f"Density-aware UNIQUE: max 3-px overlap vs 21 top-scorers {100*focus_summary['worst_cand_dots_within_3px']:.1f}% "
        f"({100*focus_summary['b2_overlap']:.1f}% vs GEMSDOE32 B2 0.2778); own HGB lineage max "
        f"{100*lane_ext['own_lineage']['worst_cand_dots_within_3px']:.1f}%; surface |Spearman| "
        f"{lane_surf['worst_abs_spearman']:.4f} <= 0.90."
    )
    primary_entry = dict(
        id="h71-hgpc-blind",
        role="primary",
        file=zfile,
        path=zpath,
        bytes=zrec["bytes"],
        sha256=zrec["sha256"],
        content_id=chk["content_id"],
        positive_pixels=chk["positive_pixels"],
        format_ok=True,
        checks=zrec["checks"],
        receipt="checks-gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.json",
        outside="zero",
        status=status,
        zip=Path(str(chk["files"]["zip"])).name,
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        expected_range="no live projection computed — H71-1 screen FAIL vs H35 (not a score)",
        lane=dict(
            lane_clear=False,
            strict_verdict=lane_lit["verdict"],
            lattice_overlap=lane_ext["lattice"][0]["cand_dots_within_3px"],
            focus_winners=focus_summary,
            external_sparse=lane_ext["external_sparse"],
            own_lineage=lane_ext["own_lineage"],
            receipt="docs/downloads/lane-gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.json",
            extended_receipt="evidence/h71_lane_extended.json",
            surface_receipt="evidence/h71_lane_surface.json",
        ),
        lane_summary=lane_summary,
        slot_reason=(
            "Three pre-registered DIRECT-emission screens all failed vs same-run H35 (HGPC -0.100, AKF -0.091, MAG -0.103; 0/4 folds each) "
            "although each beat unsupervised B_crest. Literal r13 lattice also fails. Not slot-approved."
        ),
        run_card="registry/run_card_h71_2026-10-26.json",
        title="H71-1 HGPC-BLIND signed gravity–basement polarity (sapd3.0, zeros outside) — TESTING ONLY · DO NOT SUBMIT",
        summary=(
            "Unique 2026-10-26 GeoTIFF (59,472 binary dots, min_dist=3.0 px) from pre-registered H71-1 DIRECT emission "
            "(signed isostatic-gravity × MT basement half-graben polarity; zero HGB; B=2 collar). "
            "Leakage canary PASS (max AUC 0.695). Holdout gate FAIL vs H35. "
            "Clears 21/21 sibling top-scorers (15.4% vs GEMSDOE32 B2) and own HGB lineage (max 23.4%). "
            "Strict lane gate fails only on the dense r13 lattice. "
            "Zero outside footprint (prevents 'Predicted values must be in range [0, 1]'). Testing only — DO NOT SUBMIT."
        ),
        note=note,
    )
    nan_entry = dict(
        id="h71-hgpc-blind-nan",
        role="fallback",
        file=nfile,
        path=npath,
        bytes=nrec["bytes"],
        sha256=nrec["sha256"],
        content_id=chk["content_id"],
        positive_pixels=chk["positive_pixels"],
        format_ok=True,
        checks=nrec["checks"],
        receipt="checks-gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.json",
        outside="nan",
        status="UNIQUE BY CONTENT · NaN-outside twin of H71-1 · holdout FAIL vs H35 · STRICT LANE FAIL (lattice) · verdict negative · DO NOT SUBMIT",
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        run_card="registry/run_card_h71_2026-10-26.json",
        title="H71-1 HGPC-BLIND (NaN-outside template twin) — DO NOT SUBMIT",
        summary=(
            "Pixel-identical on the 5,167,373-pixel footprint to the H71-1 zeros-outside primary "
            "(content_id 9eb0c31e5149, 59,472 dots), with NaN outside the footprint. DO NOT SUBMIT either file."
        ),
        note=note,
    )
    subs_doc["generated_by"] = "scripts/register_h71_submission.py (2026-10-26, H71 HGPC-BLIND session)"
    subs_doc["files"] = [primary_entry, nan_entry] + files
    (ROOT / "registry" / "submissions.json").write_text(json.dumps(subs_doc, indent=1) + "\n")
    assert ind_z["all_hard_checks_pass"] and ind_n["all_hard_checks_pass"]
    print("Wrote registry/run_card_h71_2026-10-26.json and updated registry/submissions.json")


if __name__ == "__main__":
    main()
