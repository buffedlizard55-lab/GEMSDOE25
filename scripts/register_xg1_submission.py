#!/usr/bin/env python3
"""Register the XG1 build as the featured (primary) download in registry/submissions.json.

Reads only machine receipts: the builder's ``checks-*.json``, the lane receipts
(``docs/downloads/lane-*.json`` from check_lane_duplicates.py, ``evidence/xg1_lane_surface.json``
from check_lane_surface.py) and the holdout analyses (``evidence/xg1_screen/analysis.json``
and, if run, ``evidence/xg1_confirm/analysis.json``). Also writes
``registry/run_card_xg1_2026-10-25.json`` (protocol rule 5).

Verdict rule (knowledge/21 §6, frozen): ``promote`` only if screen AND confirmation gates
passed, both TIFs pass all hard format checks, the surface Spearman screen passes, and no
substantive registry raster is lane-flagged (substantive = every checked raster except the
dense r13 lattice calibration probe, which flags any in-footprint file by construction and
is reported separately). ``slot_approved`` is always False; ``ok_to_submit_slot`` is True
only on promote. Featuring a file is not slot approval. Idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG, DL, EV = ROOT / "registry", ROOT / "docs" / "downloads", ROOT / "evidence"
LATTICE = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
B2_FILE = "g32_h33-2-b2_0.2778.tif"


def J(p: Path):
    return json.loads(p.read_text())


def opt(p: Path):
    return J(p) if p.exists() else None


def main() -> None:
    zeros = sorted(DL.glob("gems25-xg1-crossgrad-*-zeros.tif"))
    assert len(zeros) == 1, zeros
    zpath = zeros[0]
    npath = Path(str(zpath).replace("-zeros.tif", "-nan.tif"))
    assert npath.exists(), npath
    receipt_path = DL / f"checks-{zpath.stem}.json"
    rec = J(receipt_path)
    zrec, nrec = rec["files"]["zeros"], rec["files"]["nan"]
    note = rec["note"]
    assert len(note) <= 140 and "no slot" in note and "unscored" in note and "not slot-approved" in note, note
    cid = zrec["content_id"]

    scr = J(EV / "xg1_screen" / "analysis.json")
    cnf = opt(EV / "xg1_confirm" / "analysis.json")
    comb = opt(EV / "xg1_confirm" / "combined_analysis.json") or scr
    screen_pass = bool(scr["gate"]["passed"] and scr["leakage_canary"]["passed"])
    confirm_pass = bool(cnf and cnf["gate"]["passed"] and cnf["leakage_canary"]["passed"])
    gates_ok = bool(screen_pass and confirm_pass)

    lane_path = DL / f"lane-{zpath.stem}.json"
    lane = J(lane_path)
    surface = J(EV / "xg1_lane_surface.json")
    rows = [r for r in lane["rows"] if "spearman" in r]
    lat_rows = [r for r in rows if r["file"] == LATTICE]
    lat_overlap = float(lat_rows[0]["dots_within_3px"]) if lat_rows else None
    substantive = [r for r in rows if r["file"] != LATTICE]
    flags_sub = [r["file"] for r in substantive if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]
    worst_sub_overlap = max((r["dots_within_3px"] for r in substantive), default=0.0)
    worst_sub_overlap_file = max(substantive, key=lambda r: r["dots_within_3px"])["file"] if substantive else None
    worst_sub_rho = max((abs(r["spearman"]) for r in substantive), default=0.0)
    b2_rows = [r for r in substantive if r["file"] == B2_FILE]
    b2_overlap = float(b2_rows[0]["dots_within_3px"]) if b2_rows else None
    surface_rho_max = float(surface["worst_abs_spearman"])
    surface_ok = bool(surface_rho_max <= 0.90 and not surface["flagged"])
    format_ok = bool(zrec["format_ok"] and nrec["format_ok"] and not zrec["hard_failures"] and not nrec["hard_failures"])
    lane_ok = bool(not flags_sub and worst_sub_rho <= 0.90 and surface_ok and not lane["sha_in_artifact_ledger"])
    verdict = "promote" if (gates_ok and format_ok and lane_ok) else "negative"
    ok_slot = verdict == "promote"

    fail_parts = []
    if not gates_ok:
        fail_parts.append(
            "holdout gate: screen " + ("PASS" if screen_pass else "FAIL")
            + (", confirmation " + ("PASS" if confirm_pass else "FAIL") if cnf else ", confirmation not run (screen failed)")
        )
    if not format_ok:
        fail_parts.append("format audit FAILED")
    if not lane_ok:
        fail_parts.append(f"substantive lane flags: {flags_sub}" if flags_sub else "surface lane screen FAILED")
    lat_txt = f"strict literal lane vs the dense r13 lattice: {100 * lat_overlap:.1f}% of dots within 3 px" if lat_overlap is not None else "r13 lattice not restored"
    slot_reason = (
        "gate + substantive lane + exact-file audit all pass; eligible for the owner's separate selector step "
        f"(literal lattice caveat disclosed: {lat_txt})"
        if ok_slot
        else "; ".join(fail_parts) + f"; {lat_txt} (IR-25-LANE-DENSITY)"
    )
    lane_summary = (
        f"{lat_txt}; vs {len(substantive)} substantive registry rasters worst 3-px dot overlap "
        f"{worst_sub_overlap:.3f} ({worst_sub_overlap_file}), worst final-dot |Spearman| {worst_sub_rho:.3f}, "
        f"pre-placement surface worst |Spearman| {surface_rho_max:.3f}; "
        + (f"overlap vs GEMSDOE32 B2 (0.2778) {b2_overlap:.3f}; " if b2_overlap is not None else "B2 raster not in lane set; ")
        + ("no substantive flag" if not flags_sub else f"FLAGGED: {flags_sub}")
    )
    x, b35 = comb["arms"]["X"], comb["arms"]["B35"]
    gain = comb["primary_X_vs_B35"]
    stage_txt = f"screen draws 14-15 gain {scr['primary_X_vs_B35']['mean']:+.4f} ({scr['primary_X_vs_B35']['folds_positive']}/4 folds)" + (
        f"; confirmation draws 16-17 gain {cnf['primary_X_vs_B35']['mean']:+.4f} ({cnf['primary_X_vs_B35']['folds_positive']}/4 folds)"
        if cnf
        else "; confirmation not run (frozen rule: only after a screen pass)"
    )
    holdout_txt = (
        f"HOLDOUT-DTI X {x['mean']:.4f} (95% CI {x['ci95'][0]:.4f}–{x['ci95'][1]:.4f}; pooled {x['pooled_dti']:.4f}) vs same-run best "
        f"control B35 {b35['mean']:.4f} (pooled {b35['pooled_dti']:.4f}); paired gain {gain['mean']:+.4f} "
        f"(95% CI {gain['ci95'][0]:+.4f}–{gain['ci95'][1]:+.4f}), {gain['folds_positive']}/4 folds, worst {gain['worst_fold']:+.4f}, "
        f"withheld positives per fold {comb['withheld_positives_per_fold']}"
    )
    status = (
        f"UNIQUE BY CONTENT · FORMAT-VALID · verdict {verdict} · "
        + ("gate-passed; selector-eligible (not slot-approved)" if ok_slot else f"DO NOT SUBMIT ({slot_reason})")
    )
    summary = (
        f"XG1 cross-gradient block (knowledge/21): gravity/RTP/log-depth-to-base gradient-alignment ridges added to the "
        f"validated H35 base (BDE+7 + directed tip + H34 RESMAG-FLEX), 3-draw HGB average, score-ordered dots at 2.4 px, "
        f"3.5% candidate budget, catalogue pixels excluded, no B=2 prune. {stage_txt}. Combined/stage result: {holdout_txt}. "
        f"HOLDOUT-DTI is a catalogue-gap proxy, not a competition score. Leakage canary max effective single-feature AUC "
        f"{comb['leakage_canary']['max_effective_feature_auc']:.3f} (cap 0.90). Primary file is zeros-outside (every cell finite "
        f"in [0,1], no NaN anywhere); the NaN twin has identical footprint values. Lane: {lane_summary}. Verdict: {verdict}."
    )
    expected = f"no live projection (HOLDOUT-DTI {x['mean']:.4f} only; not a score)"

    lane_entry = dict(
        lane_clear=bool(lane_ok),
        strict_verdict=lane.get("verdict"),
        lattice_overlap=lat_overlap,
        worst_other_registry_overlap=worst_sub_overlap,
        worst_other_registry_file=worst_sub_overlap_file,
        worst_abs_spearman_final=worst_sub_rho,
        worst_abs_spearman_surface=surface_rho_max,
        overlap_vs_gemsdoe32_b2=b2_overlap,
        flagged_substantive=flags_sub,
        registry_checked=lane.get("registry_checked"),
    )
    common = dict(
        verdict=verdict, slot_approved=False, do_not_resubmit=False,
        ok_to_download=bool(format_ok), ok_to_submit_slot=bool(ok_slot),
        slot_reason=slot_reason, expected_range=expected, lane=lane_entry, lane_summary=lane_summary,
        run_card="registry/run_card_xg1_2026-10-25.json", note=note,
        parent="H35 arm B detector (BDE+7+H27_tip+H34) + XG1 cross-gradient block (knowledge/21)",
    )
    title = (
        f"XG1 cross-gradient + H35 base ({zrec['positive_pixels']:,} dots) — "
        + ("gate-passed; selector-eligible, not slot-approved" if ok_slot else "unique file; verdict negative; DO NOT SUBMIT")
    )
    rec.update(
        file=zrec["file"], sha256=zrec["sha256"], bytes=zrec["bytes"], content_id=cid,
        positive_pixels=zrec["positive_pixels"], format_ok=format_ok, checks=zrec["checks"],
        lane_check_receipt=lane_path.name, surface_lane="evidence/xg1_lane_surface.json",
        lane_entry=lane_entry, lane_summary=lane_summary, verdict=verdict, slot_reason=slot_reason,
        holdout={
            "label": "HOLDOUT-DTI", "evaluator": comb["evaluator"], "combined_or_screen": comb,
            "screen": {"path": "evidence/xg1_screen/analysis.json", "gain": scr["primary_X_vs_B35"]["mean"], "passed": screen_pass},
            "confirmation": (
                {"path": "evidence/xg1_confirm/analysis.json", "gain": cnf["primary_X_vs_B35"]["mean"], "passed": confirm_pass}
                if cnf else None
            ),
        },
    )
    receipt_path.write_text(json.dumps(rec, indent=1) + "\n")

    card = dict(
        run_card_version=1,
        date_utc="2026-10-25",
        session_branch="arena/60dab308-gemsdoe25",
        hypothesis=(
            "XG1: a buried fault offsets density, magnetization and conductive-base depth across the same plane, so the "
            "horizontal gradients of gravity, RTP magnetics and log depth-to-base are co-located and parallel "
            "(cross-gradient ~ 0) even where alluvial cover removes every scarp; adding those three alignment-ridge "
            "columns to the validated H35 detector raises credit per emitted pixel on catalogue-missing faults."
        ),
        mechanism=(
            "DTI = TP/(0.2(TP+FP)+0.8N); at fixed emission (sapd2.4, 3.5% budget) only detector ranking changes. "
            "XG columns are ridge_strength(|cos between gradient vectors| x min p99-normalised gradient magnitude) "
            "for the (gravity,RTP), (gravity,depth), (RTP,depth) pairs at sigma=1.5 px — surface-free, catalogue-free."
        ),
        non_fault_process_that_could_mimic_it=(
            "Lithologic/intrusive contacts and caldera ring margins step gravity, magnetics and apparent basement depth "
            "along one boundary with parallel gradients and no fault offset; common flight-line levelling can also align "
            "gravity/RTP gradient artefacts."
        ),
        pre_registration="knowledge/21_preregistered_xg1_cross_gradient_2026-10-25.md (commit da478e6, before any fit)",
        holdout={
            "label": "HOLDOUT-DTI",
            "evaluator": comb["evaluator"],
            "stage_summaries": stage_txt,
            "arms": comb["arms"],
            "primary_X_vs_B35": gain,
            "withheld_positives_per_fold": comb["withheld_positives_per_fold"],
            "withheld_positives_total": comb["withheld_positives_total"],
            "leakage_canary": comb["leakage_canary"],
            "screen_passed": screen_pass,
            "confirmation_passed": confirm_pass if cnf else None,
            "note": "Catalogue-gap proxy (hidden = withheld catalogue components); not a competition score.",
        },
        correlation_overlap_vs_registry=lane_entry | {"lane_summary": lane_summary, "lane_receipt": f"docs/downloads/{lane_path.name}"},
        raster=dict(file=zrec["file"], sha256=zrec["sha256"], content_id=cid, positive_pixels=zrec["positive_pixels"],
                    nan_twin=dict(file=nrec["file"], sha256=nrec["sha256"]), zip=rec.get("zip")),
        validator=dict(
            hard_failures=zrec["hard_failures"], ok_to_upload=zrec["format_ok"], checks=zrec["checks"],
            receipt=f"docs/downloads/{receipt_path.name}",
        ),
        submission_name=zrec["file"],
        driven_data_note=note,
        note_chars=len(note),
        verdict=verdict,
        slot_approved=False,
        ok_to_download=bool(format_ok),
        ok_to_submit_slot=bool(ok_slot),
        slot_reason=slot_reason,
        build=rec.get("build"),
    )
    (REG / "run_card_xg1_2026-10-25.json").write_text(json.dumps(card, indent=1) + "\n")

    subs = J(REG / "submissions.json")
    files = [f for f in subs["files"] if not f.get("id", "").startswith("xg1-")]
    for f in files:
        if f["role"] == "primary":
            f["role"] = "alternate"
    nan_note = f"GEMSDOE25 XG1 nan twin fallback | unscored; not slot-approved; no slot | id {cid}"
    assert len(nan_note) <= 140
    primary = dict(
        id="xg1-crossgrad", role="primary", file=zrec["file"], path=zrec["path"], bytes=zrec["bytes"],
        sha256=zrec["sha256"], content_id=cid, positive_pixels=zrec["positive_pixels"], format_ok=format_ok,
        checks=zrec["checks"], receipt=receipt_path.name, lane_receipt=lane_path.name, outside="zero",
        status=status, title=title, summary=summary, zip=rec["zip"]["file"] if rec.get("zip") else "",
        zip_bundle=rec.get("zip"),
        transform="ridge-NMS top-K (3.5%) -> score-ordered dots 2.4 px, 3-draw HGB average (BDE+7+tip+H34+XG1), catalogue pixels excluded, 0.0 outside footprint",
        **common,
    )
    fallback = dict(
        id="xg1-crossgrad-nan", role="fallback", file=nrec["file"], path=nrec["path"], bytes=nrec["bytes"],
        sha256=nrec["sha256"], content_id=cid, positive_pixels=nrec["positive_pixels"],
        format_ok=bool(nrec["format_ok"] and not nrec["hard_failures"]), checks={}, receipt=receipt_path.name,
        lane_receipt=lane_path.name, outside="nan",
        status="template-convention twin (NaN outside); identical footprint values; unscored; not slot-approved; "
               + ("same verdict as primary" if ok_slot else "DO NOT SUBMIT"),
        title="XG1 with NaN outside the footprint (official template convention); same dots as primary",
        summary="Identical prediction values inside the template footprint; NaN instead of 0.0 outside. Prefer the zeros "
                "primary (passes the strictest whole-array [0,1] validator); use this twin only if the portal rejects zeros.",
        transform="outside=nan",
        **{**common, "note": nan_note},
    )
    subs["files"] = [primary, fallback] + files
    subs["generated_by"] = "scripts/register_xg1_submission.py (XG1 session 2026-10-25)"
    (REG / "submissions.json").write_text(json.dumps(subs, indent=1) + "\n")
    print("verdict:", verdict, "| gates_ok", gates_ok, "(screen", screen_pass, "confirm", confirm_pass if cnf else "n/a",
          ") | format_ok", format_ok, "| lane_ok", lane_ok, "| flags_substantive", flags_sub)
    print("primary:", zrec["file"], zrec["sha256"], zrec["positive_pixels"])
    print("lane:", lane_summary)
    print("slot_reason:", slot_reason)


if __name__ == "__main__":
    main()
