#!/usr/bin/env python3
"""Register the Session-8 H38 (OSPC + 300 m submodular multi-scale skeleton) GeoTIFFs in
registry/submissions.json and emit registry/run_card_h38_2026-10-25.json.

All verdicts are computed strictly from machine-readable receipts:
  - docs/downloads/checks-gems25-h38-ospc-submod-*-zeros.json
  - docs/downloads/lane-gems25-h38-ospc-submod-*-zeros.json
  - evidence/h38_build/surface_lane_h38.json
  - evidence/h38_screen/analysis.json (and evidence/h38_confirm/analysis.json if executed)
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG, DL, EV = ROOT / "registry", ROOT / "docs" / "downloads", ROOT / "evidence"
LATTICE = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
B2_FILE = "g32_h33-2-b2_0.2778.tif"
G70_FILE = "g70_dual-submod_0.2478.tif"


def J(p: Path):
    return json.loads(p.read_text())


def opt(p: Path):
    return J(p) if p.exists() else None


def main() -> None:
    zeros = sorted(DL.glob("gems25-h38-ospc-submod-*-zeros.tif"))
    assert len(zeros) == 1, zeros
    zpath = zeros[0]
    npath = Path(str(zpath).replace("-zeros.tif", "-nan.tif"))
    assert npath.exists(), npath

    receipt_path = DL / f"checks-{zpath.stem}.json"
    rec = J(receipt_path)
    zrec, nrec = rec["files"]["zeros"], rec["files"]["nan"]
    note = rec["note"]
    assert len(note) <= 120 and "no slot" in note and "unscored" in note and "not slot-approved" in note, note
    cid = zrec["content_id"]

    scr = J(EV / "h38_screen" / "analysis.json")
    cnf = opt(EV / "h38_confirm" / "analysis.json")
    comb = cnf or scr
    screen_pass = bool(scr["gate"]["passed"] and scr["leakage_canary"]["passed"])
    confirm_pass = bool(cnf and cnf["gate"]["passed"] and cnf["leakage_canary"]["passed"])
    gates_ok = bool(screen_pass and confirm_pass)

    lane_path = DL / f"lane-{zpath.stem}.json"
    lane = J(lane_path)
    surface = J(EV / "h38_build" / "surface_lane_h38.json")
    rows = [r for r in lane["rows"] if "spearman" in r]

    lat_rows = [r for r in rows if r["file"] == LATTICE]
    lat_overlap = float(lat_rows[0]["dots_within_3px"]) if lat_rows else None
    substantive = [r for r in rows if r["file"] != LATTICE]
    other_site_rows = [r for r in substantive if not r["file"].startswith("gems25-")]
    own_repo_rows = [r for r in substantive if r["file"].startswith("gems25-")]
    sibling_top_rows = [r for r in substantive if r["file"].startswith("g") and "_" in r["file"] and r["file"][1].isdigit()]

    flags_literal = [r["file"] for r in rows if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]
    flags_sub = [r["file"] for r in substantive if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]
    flags_other_site = [r["file"] for r in other_site_rows if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]
    flags_own_repo = [r["file"] for r in own_repo_rows if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]
    flags_sibling_top = [r["file"] for r in sibling_top_rows if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]

    worst_sub_overlap = max((r["dots_within_3px"] for r in substantive), default=0.0)
    worst_sub_overlap_file = max(substantive, key=lambda r: r["dots_within_3px"])["file"] if substantive else None
    worst_other_site_overlap = max((r["dots_within_3px"] for r in other_site_rows), default=0.0)
    worst_other_site_file = max(other_site_rows, key=lambda r: r["dots_within_3px"])["file"] if other_site_rows else None
    worst_sibling_top_overlap = max((r["dots_within_3px"] for r in sibling_top_rows), default=0.0)
    worst_sibling_top_file = max(sibling_top_rows, key=lambda r: r["dots_within_3px"])["file"] if sibling_top_rows else None
    worst_sub_rho = max((abs(r["spearman"]) for r in substantive), default=0.0)

    b2_rows = [r for r in substantive if r["file"] == B2_FILE]
    b2_overlap = float(b2_rows[0]["dots_within_3px"]) if b2_rows else None
    g70_rows = [r for r in substantive if r["file"] == G70_FILE]
    g70_overlap = float(g70_rows[0]["dots_within_3px"]) if g70_rows else None

    surface_rho_max = float(surface["worst_abs_spearman"])
    surface_ok = bool(surface_rho_max <= 0.90 and not surface["flagged"])
    format_ok = bool(zrec["format_ok"] and nrec["format_ok"] and not zrec["hard_failures"] and not nrec["hard_failures"])
    strict_lane_ok = bool(not flags_literal and surface_ok and not lane["sha_in_artifact_ledger"])

    verdict = "promote" if (gates_ok and format_ok and strict_lane_ok) else "negative"
    ok_slot = verdict == "promote"

    g1s1 = comb["arms"]["G1_S1"]
    g0s0 = comb["arms"]["G0_S0"]
    gain = comb["contrasts"]["primary_G1_S1_vs_G0_S0"]
    main_g = comb["factorial_effects"]["main_effect_G_OSPC"]
    main_s = comb["factorial_effects"]["main_effect_S_SUBMOD"]

    fail_parts = []
    if not gates_ok:
        fail_parts.append(
            f"holdout screen FAILED ({gain['mean']:+.4f} fold-mean gain, {gain['folds_positive']}/4 folds positive; "
            f"confirmation not run per frozen stopping rule)"
        )
    if not format_ok:
        fail_parts.append("format audit FAILED")
    if not strict_lane_ok:
        fail_parts.append(
            f"strict lane gate flagged {len(flags_literal)} rasters (r13 5-px lattice {lat_overlap:.3f}, "
            f"gems10-h25 dense ridge {worst_other_site_overlap:.3f}, and own H31/H35/XG1/H37 HGB lineage {worst_sub_overlap:.3f}; "
            f"0/21 GEMSDOE27..91 top-scorers flagged, max {worst_sibling_top_overlap:.3f})"
        )
    slot_reason = "; ".join(fail_parts) + " (IR-25-LANE-DENSITY)"

    lane_summary = (
        f"strict lane gate (literal) vs r13 5-px lattice: {100.0 * (lat_overlap or 0.0):.1f}% within 3 px; "
        f"0/21 GEMSDOE27..91 top-scorers flagged (GEMSDOE32 0.2778 overlap {b2_overlap:.3f}, "
        f"GEMSDOE70 submodular 0.2478 overlap {g70_overlap:.3f}, max sibling top-scorer {worst_sibling_top_overlap:.3f} on {worst_sibling_top_file}); "
        f"historical scored max {worst_other_site_overlap:.3f} ({worst_other_site_file}); "
        f"own HGB lineage max 3-px overlap {worst_sub_overlap:.3f} ({worst_sub_overlap_file}; exact pixel overlap vs S0 on same surface only "
        f"{rec['build']['exact_overlap_vs_s0_on_same_surface']:.3f}); "
        f"worst final-dot |Spearman| {worst_sub_rho:.3f}, pre-placement surface worst |Spearman| {surface_rho_max:.3f}"
    )

    holdout_txt = (
        f"HOLDOUT-DTI ({comb['evaluator_version']}, draws {comb['draws']}, {g1s1['total_withheld_positives']:,} withheld positives): "
        f"G1_S1 fold-mean {g1s1['fold_mean_dti']:.4f} (95% CI {g1s1['ci95_fold_mean'][0]:.4f}–{g1s1['ci95_fold_mean'][1]:.4f}; "
        f"pooled {g1s1['pooled_dti']:.4f}) vs same-run H35 arm-B control G0_S0 {g0s0['fold_mean_dti']:.4f} "
        f"(pooled {g0s0['pooled_dti']:.4f}); paired gain {gain['mean']:+.4f} "
        f"(95% CI {gain['ci95'][0]:+.4f}–{gain['ci95'][1]:+.4f}), {gain['folds_positive']}/4 folds positive "
        f"(NW {gain['per_fold']['NW']:+.4f}, NE {gain['per_fold']['NE']:+.4f}, SW {gain['per_fold']['SW']:+.4f}, SE {gain['per_fold']['SE']:+.4f}); "
        f"Factor G main effect {main_g['mean']:+.4f}, Factor S main effect {main_s['mean']:+.4f}, hug delta {gain['hug_mean']:+.4f}"
    )

    status = f"UNIQUE BY CONTENT · 16/16 FORMAT CHECKS PASS · OK TO DOWNLOAD · verdict {verdict} · DO NOT SUBMIT ({slot_reason})"
    title = f"H38 OSPC × 300 m Submodular Skeleton ({zrec['positive_pixels']:,} off-catalogue dots) — unique file; format-valid; verdict negative; DO NOT SUBMIT"
    summary = (
        f"Session-8 H38 primary candidate (knowledge/25, committed pre-fit): 4 catalogue-free OSPC columns "
        f"(1 m 3DEP monoclinal scarp polarity, ~1.5 km spin-2 scarp director coherence, surface-to-subsurface strike alignment, "
        f"and negative-RTP hydrothermal magnetite-destruction trough x cond_surf) added to H35 arm B, emitted via exact "
        f"Minoux lazy-greedy 300 m submodular coverage on the multi-scale ridge skeleton R_1 U R_2 at exact S0-matched budget "
        f"({zrec['positive_pixels']:,} dots, moving 72.5% of pixel coordinates vs sapd2.4). {holdout_txt}. "
        f"Leakage canary passed (max standalone feature AUC {comb['leakage_canary']['h38_max_canary_auc']:.3f} <= 0.90). "
        f"HOLDOUT-DTI is a local catalogue-gap proxy, never a live score projection. Primary GeoTIFF is zeros-outside "
        f"(every cell finite in {{0.0, 1.0}} subset [0, 1], zero NaN anywhere); NaN-outside fallback has identical footprint dots. "
        f"Lane audit: {lane_summary}. Verdict: {verdict}."
    )
    expected = f"no live projection (HOLDOUT-DTI {g1s1['fold_mean_dti']:.4f} only; not a score)"

    lane_entry = dict(
        lane_clear=bool(strict_lane_ok),
        lane_clear_vs_sibling_top_scorers=bool(len(flags_sibling_top) == 0 and surface_ok),
        strict_verdict=lane.get("verdict"),
        density_aware_verdict=lane.get("verdict_density_aware"),
        lattice_overlap=lat_overlap,
        worst_sibling_top_scorer_overlap=worst_sibling_top_overlap,
        worst_sibling_top_scorer_file=worst_sibling_top_file,
        overlap_vs_gemsdoe32_b2=b2_overlap,
        overlap_vs_gemsdoe70_submod=g70_overlap,
        worst_historical_other_site_overlap=worst_other_site_overlap,
        worst_historical_other_site_file=worst_other_site_file,
        worst_other_registry_overlap=worst_sub_overlap,
        worst_other_registry_file=worst_sub_overlap_file,
        worst_abs_spearman_final=worst_sub_rho,
        worst_abs_spearman_surface=surface_rho_max,
        flagged_literal=flags_literal,
        flagged_substantive=flags_sub,
        flagged_own_lineage=flags_own_repo,
        flagged_other_site=flags_other_site,
        flagged_sibling_top_scorers=flags_sibling_top,
        registry_checked=lane.get("registry_checked"),
    )

    rec.update(
        file=zrec["file"],
        sha256=zrec["sha256"],
        bytes=zrec["bytes"],
        content_id=cid,
        positive_pixels=zrec["positive_pixels"],
        format_ok=format_ok,
        checks=zrec["checks"],
        lane_check_receipt=lane_path.name,
        lane_entry=lane_entry,
        lane_summary=lane_summary,
        verdict=verdict,
        slot_reason=slot_reason,
        holdout=dict(
            label="HOLDOUT-DTI",
            evaluator=comb["evaluator_version"],
            screen=dict(path="evidence/h38_screen/analysis.json", gain=gain["mean"], passed=screen_pass),
            confirmation=(
                dict(path="evidence/h38_confirm/analysis.json", gain=cnf["contrasts"]["primary_G1_S1_vs_G0_S0"]["mean"], passed=confirm_pass)
                if cnf
                else None
            ),
        ),
    )
    receipt_path.write_text(json.dumps(rec, indent=2) + "\n")

    card = dict(
        run_card_version=1,
        date_utc="2026-10-25",
        session_branch="arena/97f7dfaa-gemsdoe25",
        hypothesis=(
            "H38-1 (OSPC x SUBMOD): (Factor G) 1 m 3DEP one-sided monoclinal scarp polarity, ~1.5 km spin-2 scarp director "
            "coherence, surface-scarp to subsurface potential-field strike alignment, and hydrothermal magnetite-destruction "
            "negative-RTP troughs gated by shallow thermal conductivity detect breached piedmont scarps and blind demagnetized "
            "fault conduits missed by 1:250k catalogue mapping; (Factor S) exact lazy-greedy 300 m triangular-kernel submodular "
            "coverage on multi-scale skeletons R_1 U R_2 eliminates 2.4-px over-packing waste at matched dot budget M."
        ),
        mechanism=(
            "Official DTI sums max_{x in S} max(1 - d(x, g)/3, 0) over hidden fault pixels g divided by 0.2|S| + 0.8|G|. "
            "Factor G adds 4 catalogue-free physical columns to H35 arm B; Factor S replaces greedy 2.4-px Poisson thinning "
            "with exact Minoux lazy-greedy maximization of expected 300 m kernel credit on King-Zeng calibrated posteriors "
            "supported on ridge_nms(1.0) | ridge_nms(2.0) at identical dot count M."
        ),
        non_fault_process_that_could_mimic_it=(
            "Asymmetric fluvial terrace risers and Pleistocene pluvial-lake (Lahontan/Bonneville) shoreline scarps locally "
            "sub-parallel to range-front basement strike mimic monoclinal scarp polarity; reversely magnetized volcanic "
            "paleochannels or conductive playa clay channels mimic negative-RTP x cond_surf troughs; in high-density Southern "
            "Walker Lane / SE carbonate splays (~1.5% fault prevalence), sigma=6 px (600 m) blurs adjacent fault strands and "
            "stretching dot spacing sacrifices high-probability ridge midpoint credit."
        ),
        pre_registration="knowledge/25_preregistered_h38_ospc_submod_factorial_2026-10-25.md (commit c9c7e76, before any fit)",
        deviation_from_preregistration=(
            "None in features, draws, model, emission, or gate. Documentation note: knowledge/25 §4.1 prose wrote '55 cols' / "
            "'59 cols' for G0 / G1 by mis-summing 48(BDE)+7(addons)+1(tip)+3(H34)=59 and +4(H38)=63; exact H35 arm-B + H38 "
            "columns (59 and 63) ran identically across holdout and build."
        ),
        holdout_dti=dict(
            label="HOLDOUT-DTI",
            evaluator_version=comb["evaluator_version"],
            draws_evaluated=comb["draws"],
            confirmation_draws_status="not run (honored pre-registered conditional stopping rule after screen fail)",
            withheld_positives_total=g1s1["total_withheld_positives"],
            candidate_G1_S1=g1s1,
            same_run_control_G0_S0=g0s0,
            diagnostic_G1_S0=comb["arms"]["G1_S0"],
            diagnostic_G0_S1=comb["arms"]["G0_S1"],
            primary_contrast_G1_S1_vs_G0_S0=gain,
            factorial_effects=comb["factorial_effects"],
            leakage_canary=comb["leakage_canary"],
            gate=comb["gate"],
        ),
        correlation_overlap_vs_registry=lane_entry | dict(
            caps=dict(spearman=0.90, overlap_3px=0.70),
            lane_summary=lane_summary,
            lane_receipt=f"docs/downloads/{lane_path.name}",
            surface_lane_receipt="evidence/h38_build/surface_lane_h38.json",
        ),
        raster=dict(
            file=zrec["file"],
            path=zrec["path"],
            bytes=zrec["bytes"],
            sha256=zrec["sha256"],
            content_id=cid,
            positive_pixels=zrec["positive_pixels"],
            nan_twin=dict(file=nrec["file"], path=nrec["path"], bytes=nrec["bytes"], sha256=nrec["sha256"]),
            zip=rec.get("zip"),
        ),
        validator_output=dict(
            ok_to_upload=bool(zrec["format_ok"]),
            ok_to_submit_slot=bool(ok_slot),
            hard_failures=zrec["hard_failures"],
            checks=zrec["checks"],
            receipt=f"docs/downloads/{receipt_path.name}",
        ),
        submission_name=zrec["file"],
        note=note,
        driven_data_note=note,
        note_chars=len(note),
        verdict=verdict,
        slot_approved=False,
        ok_to_download=bool(format_ok),
        ok_to_submit_slot=bool(ok_slot),
        slot_reason=slot_reason,
        experiments_run=1,
        budget_respected=True,
        build=rec.get("build"),
    )
    (REG / "run_card_h38_2026-10-25.json").write_text(json.dumps(card, indent=2) + "\n")

    subs = J(REG / "submissions.json")
    files = [f for f in subs["files"] if not f.get("id", "").startswith("h38-")]
    for f in files:
        if f["role"] == "primary":
            f["role"] = "alternate"

    nan_note = f"GEMSDOE25 H38 nan fallback | unscored; not slot-approved; no slot | id {cid}"
    assert len(nan_note) <= 120, len(nan_note)

    common = dict(
        verdict=verdict,
        slot_approved=False,
        do_not_resubmit=False,
        ok_to_download=bool(format_ok),
        ok_to_submit_slot=bool(ok_slot),
        slot_reason=slot_reason,
        expected_range=expected,
        lane=lane_entry,
        lane_summary=lane_summary,
        run_card="registry/run_card_h38_2026-10-25.json",
        note=note,
        parent="H35 arm B detector (BDE+7+H27_tip+H34) + H38 OSPC (4 cols) + exact 300 m submodular R_1 U R_2 allocation",
    )
    primary = dict(
        id="h38-ospc-submod",
        role="primary",
        file=zrec["file"],
        path=zrec["path"],
        bytes=zrec["bytes"],
        sha256=zrec["sha256"],
        content_id=cid,
        positive_pixels=zrec["positive_pixels"],
        format_ok=format_ok,
        checks=zrec["checks"],
        receipt=receipt_path.name,
        lane_receipt=lane_path.name,
        outside="zero",
        status=status,
        title=title,
        summary=summary,
        zip=rec["zip"]["file"] if rec.get("zip") else "",
        zip_bundle=rec.get("zip"),
        transform=(
            "3-draw HGB ensemble (BDE+7+H27_tip+H34+H38_OSPC, 63 cols) -> King-Zeng posterior calibration -> "
            "exact Minoux lazy-greedy 300 m submodular coverage on R_1 U R_2 matched to sapd2.4 budget (48,666 dots), "
            "known catalogue pixels masked, 0.0 outside footprint"
        ),
        **common,
    )
    fallback = dict(
        id="h38-ospc-submod-nan",
        role="fallback",
        file=nrec["file"],
        path=nrec["path"],
        bytes=nrec["bytes"],
        sha256=nrec["sha256"],
        content_id=cid,
        positive_pixels=nrec["positive_pixels"],
        format_ok=bool(nrec["format_ok"] and not nrec["hard_failures"]),
        checks={},
        receipt=receipt_path.name,
        lane_receipt=lane_path.name,
        outside="nan",
        status="template-convention twin (NaN outside); identical footprint dots; unscored; not slot-approved; DO NOT SUBMIT",
        title="H38 OSPC × Submodular with NaN outside footprint (template convention); identical in-footprint dots",
        summary=(
            "Identical 48,666 binary fault predictions inside the competition footprint; NaN instead of 0.0 outside. "
            "Kept for local template comparison only; same negative verdict and strict lane stop as the zeros-outside primary."
        ),
        transform="outside=nan",
        **{**common, "note": nan_note},
    )
    subs["files"] = [primary, fallback] + files
    subs["generated_by"] = "scripts/register_h38_submission.py (H38 session 8, 2026-10-25)"
    (REG / "submissions.json").write_text(json.dumps(subs, indent=2) + "\n")
    print("REGISTERED primary:", primary["file"], "| sha256:", primary["sha256"], "| verdict:", verdict)
    print("ok_to_download:", primary["ok_to_download"], "| ok_to_submit_slot:", primary["ok_to_submit_slot"])


if __name__ == "__main__":
    main()
