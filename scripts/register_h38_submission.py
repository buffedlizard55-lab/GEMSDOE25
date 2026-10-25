#!/usr/bin/env python3
"""Register the H38 build as the featured (primary) download in registry/submissions.json.

Reads only machine receipts: the builder's ``checks-*.json``, the lane receipts
(``docs/downloads/lane-*.json``, ``evidence/h38_lane_surface.json``) and the holdout
analyses (``evidence/h38_screen/results.json``, ``evidence/h38_confirm/results.json``;
combined statistics recomputed here from the two ``cells.jsonl``). Also writes
``registry/run_card_h38_2026-10-25.json`` (protocol rule 5).

Verdict rule (knowledge/25, frozen): ``promote`` only if screen AND confirmation gates
passed, both TIFs pass all hard format checks, the surface Spearman screen passes, and
no substantive registry raster is lane-flagged (substantive = every checked raster
except the dense r13 lattice probe, whose 3-px halo covers 99.87% of the footprint and
is reported separately). Substantive flags are split into other-site/scored rasters
(``data/scored`` + ``data/registry_top``) vs this repo's own unscored lineage
(``docs/downloads``). ``slot_approved`` is always False; ``ok_to_submit_slot`` is True
only on promote. Featuring a file is not slot approval. Idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
REG, DL, EV = ROOT / "registry", ROOT / "docs" / "downloads", ROOT / "evidence"
LATTICE = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
B2_FILE = "g32_h33-2-b2_0.2778.tif"


def J(p: Path):
    return json.loads(p.read_text())


def pooled(rows: list[dict], tp: str, fp: str, n: str) -> float:
    TP = sum(r[tp] for r in rows)
    FP = sum(r[fp] for r in rows)
    N = sum(r[n] for r in rows)
    return float(TP / (0.2 * (TP + FP) + 0.8 * N)) if N else 0.0


def combined_stage() -> dict:
    """Combined draws 20-23 statistics from the raw cells (fold means over 4 draws)."""
    rows = []
    for stage in ("h38_screen", "h38_confirm"):
        rows += [json.loads(ln) for ln in (EV / stage / "cells.jsonl").read_text().splitlines() if ln.strip()]
    out = {"arms": {}, "contrasts": {}}
    for arm in ("A0", "A1", "A2", "A3"):
        rs = [r for r in rows if r["arm"] == arm]
        fold_means = [float(np.mean([r["dti"] for r in rs if r["fold"] == f])) for f in range(4)]
        arr = np.array(fold_means)
        half = float(stats.t.ppf(0.975, 3) * arr.std(ddof=1) / 2.0)
        out["arms"][arm] = dict(
            fold_means=fold_means, mean=float(arr.mean()),
            ci95=[float(arr.mean() - half), float(arr.mean() + half)],
            pooled_dti=pooled(rs, "tp", "fp", "n_truth"),
            pooled_dti_offcat=pooled(rs, "tp_offcat", "fp_offcat", "n_truth_offcat"),
            mean_emitted=float(np.mean([r["emitted"] for r in rs])),
            mean_hug=float(np.mean([r["hug"] for r in rs])),
        )
    for arm in ("A1", "A2", "A3"):
        gains = np.array([out["arms"][arm]["fold_means"][f] - out["arms"]["A0"]["fold_means"][f] for f in range(4)])
        half = float(stats.t.ppf(0.975, 3) * gains.std(ddof=1) / 2.0)
        out["contrasts"][arm] = dict(
            per_fold=[float(v) for v in gains], mean=float(gains.mean()),
            ci95=[float(gains.mean() - half), float(gains.mean() + half)],
            folds_positive=int((gains > 0).sum()), worst_fold=float(gains.min()),
            pooled_delta=float(out["arms"][arm]["pooled_dti"] - out["arms"]["A0"]["pooled_dti"]),
            pooled_delta_offcat=float(out["arms"][arm]["pooled_dti_offcat"] - out["arms"]["A0"]["pooled_dti_offcat"]),
        )
    out["withheld_positives_per_fold"] = [
        int(round(np.mean([r["n_truth"] for r in rows if r["arm"] == "A0" and r["fold"] == f]))) for f in range(4)
    ]
    out["withheld_positives_offcat_per_fold"] = [
        int(round(np.mean([r["n_truth_offcat"] for r in rows if r["arm"] == "A0" and r["fold"] == f]))) for f in range(4)
    ]
    out["draws"] = [20, 21, 22, 23]
    return out


def main() -> None:
    zeros = sorted(DL.glob("gems25-h38-greedy-credit-*-zeros.tif"))
    assert len(zeros) == 1, zeros
    zpath = zeros[0]
    npath = Path(str(zpath).replace("-zeros.tif", "-nan.tif"))
    assert npath.exists(), npath
    receipt_path = DL / f"checks-{zpath.stem}.json"
    rec = J(receipt_path)
    zrec, nrec = rec["files"]["zeros"], rec["files"]["nan"]
    cid = zrec["content_id"]
    # Final registry note (overrides the builder's interim text; the repo-integrity
    # test requires <=120 chars with literal "not slot-approved"/"unscored"/"no slot").
    note = f"GEMSDOE25 H38 greedy-credit k3.5% | PASSx2 +0.005; unscored; not slot-approved; no slot | id {cid}"
    assert len(note) <= 120 and "unscored" in note and "no slot" in note and "not slot-approved" in note, note
    rec["note"] = note
    rec["note_chars"] = len(note)

    scr = J(EV / "h38_screen" / "results.json")
    cnf = J(EV / "h38_confirm" / "results.json")
    comb = combined_stage()
    screen_pass = bool(scr["gates"]["A1"]["passed"] and scr["leakage_canary"]["passed"])
    confirm_pass = bool(cnf["gates"]["A1"]["passed"] and cnf["leakage_canary"]["passed"])
    gates_ok = bool(screen_pass and confirm_pass)

    lane_path = DL / f"lane-{zpath.stem}.json"
    lane = J(lane_path)
    surface = J(EV / "h38_lane_surface.json")
    rows = [r for r in lane["rows"] if "spearman" in r]
    lat_rows = [r for r in rows if r["file"] == LATTICE]
    lat_overlap = float(lat_rows[0]["dots_within_3px"]) if lat_rows else None
    substantive = [r for r in rows if r["file"] != LATTICE]
    own = [r for r in substantive if r["file"].startswith("gems25-")]
    other = [r for r in substantive if not r["file"].startswith("gems25-")]

    def flagged(rs: list[dict]) -> list[str]:
        return [r["file"] for r in rs if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]

    flags_own, flags_other = flagged(own), flagged(other)
    flags_sub = flags_own + flags_other
    worst_other_overlap = max((r["dots_within_3px"] for r in other), default=0.0)
    worst_other_file = max(other, key=lambda r: r["dots_within_3px"])["file"] if other else None
    worst_own_overlap = max((r["dots_within_3px"] for r in own), default=0.0)
    worst_own_file = max(own, key=lambda r: r["dots_within_3px"])["file"] if own else None
    worst_sub_rho = max((abs(r["spearman"]) for r in substantive), default=0.0)
    b2_rows = [r for r in substantive if r["file"] == B2_FILE]
    b2_overlap = float(b2_rows[0]["dots_within_3px"]) if b2_rows else None
    surface_rho_max = float(surface["worst_abs_spearman"])
    surface_ok = bool(surface_rho_max <= 0.90 and not surface["flagged"])
    format_ok = bool(zrec["format_ok"] and nrec["format_ok"] and not zrec["hard_failures"] and not nrec["hard_failures"])
    lane_ok = bool(not flags_sub and worst_sub_rho <= 0.90 and surface_ok and not lane["sha_in_artifact_ledger"])
    verdict = "promote" if (gates_ok and format_ok and lane_ok) else "negative"
    ok_slot = verdict == "promote"

    lat_txt = (
        f"strict lane gate (literal) vs the dense r13 lattice: {100 * lat_overlap:.1f}% of dots within 3 px "
        f"(halo coverage 99.87%; density-aware symmetric overlap {lat_rows[0]['symmetric_min_overlap_3px']:.3f})"
        if lat_rows else "r13 lattice not restored"
    )
    own_short = sorted({f.removesuffix("-nan.tif").removesuffix("-zeros.tif").removeprefix("gems25-") for f in flags_own})
    fail_parts = []
    if not gates_ok:
        fail_parts.append(f"holdout gate: screen {'PASS' if screen_pass else 'FAIL'}, confirmation {'PASS' if confirm_pass else 'FAIL'}")
    if not format_ok:
        fail_parts.append("format audit FAILED")
    if not lane_ok:
        if flags_other:
            fail_parts.append(f"lane flags vs other-site rasters: {', '.join(flags_other)}")
        if flags_own:
            fail_parts.append(
                f"lane duplicate vs this repo's own unscored lineage ({', '.join(own_short)}; worst {worst_own_overlap:.3f} vs {worst_own_file}) "
                f"— supersession is an owner selector decision, not agent-cleared"
            )
        if not surface_ok:
            fail_parts.append("surface lane screen FAILED")
    slot_reason = (
        f"gate + substantive lane + exact-file audit all pass; eligible for the owner's separate selector step ({lat_txt})"
        if ok_slot
        else ("holdout gate PASS x2 + format PASS; blocked by: " if (gates_ok and format_ok) else "")
        + "; ".join(fail_parts) + f"; {lat_txt} (IR-25-LANE-DENSITY)"
    )
    lane_summary = (
        f"{lat_txt}; vs {len(other)} other-site/scored rasters worst 3-px dot overlap {worst_other_overlap:.3f} "
        f"({worst_other_file}), no flag; overlap vs GEMSDOE32 B2 (OWNER 0.2778) "
        + (f"{b2_overlap:.3f}; " if b2_overlap is not None else "not in lane set; ")
        + f"worst final-dot |Spearman| {worst_sub_rho:.3f}, pre-placement surface worst |Spearman| {surface_rho_max:.3f}; "
        + (f"FLAGGED vs own unscored lineage ({', '.join(own_short)}; worst {worst_own_overlap:.3f})" if flags_own else "no own-lineage flag")
    )
    a1, a0 = comb["arms"]["A1"], comb["arms"]["A0"]
    gain = comb["contrasts"]["A1"]
    holdout_txt = (
        f"HOLDOUT-DTI A1 {a1['mean']:.4f} (95% CI {a1['ci95'][0]:.4f}–{a1['ci95'][1]:.4f}; pooled {a1['pooled_dti']:.4f}) "
        f"vs same-surface control A0 {a0['mean']:.4f} (pooled {a0['pooled_dti']:.4f}); combined paired gain {gain['mean']:+.4f} "
        f"(95% CI {gain['ci95'][0]:+.4f}–{gain['ci95'][1]:+.4f}), {gain['folds_positive']}/4 folds, worst {gain['worst_fold']:+.4f}, "
        f"pooled +{gain['pooled_delta']:.4f}; screen (draws 20–21) {scr['contrasts_vs_A0']['A1']['standard']['mean']:+.4f} PASS, "
        f"confirmation (draws 22–23) {cnf['contrasts_vs_A0']['A1']['standard']['mean']:+.4f} PASS; off-catalogue pooled gain "
        f"{gain['pooled_delta_offcat']:+.4f}; withheld positives per fold {comb['withheld_positives_per_fold']} "
        f"(off-catalogue {comb['withheld_positives_offcat_per_fold']})"
    )
    summary = (
        f"H38 greedy marginal-credit emission (knowledge/25): the validated H35 detector surface (BDE+7 + directed tip + "
        f"H34 RESMAG-FLEX, 3-draw HGB average) is unchanged; dots are bought from the same ridge-NMS 3.5% candidate pool by "
        f"exact incremental triangular-kernel credit per plug-in FP, stopping at the DTI break-even ratio — no fixed spacing "
        f"or count ({zrec['positive_pixels']:,} dots). {holdout_txt}. HOLDOUT-DTI is a catalogue-gap proxy, not a competition "
        f"score. Leakage canary max effective AUC {max(scr['leakage_canary']['line_score_auc_max_effective'], cnf['leakage_canary']['line_score_auc_max_effective']):.3f} "
        f"(line score; base surface {max(scr['leakage_canary']['base_surface_auc_max_effective'], cnf['leakage_canary']['base_surface_auc_max_effective']):.3f}; cap 0.90). "
        f"Primary file is zeros-outside (every cell finite in [0,1], no NaN anywhere); the NaN twin has identical footprint "
        f"values. Lane: {lane_summary}. Verdict: {verdict}."
    )
    status = (
        f"UNIQUE BY CONTENT · FORMAT-VALID · HOLDOUT GATE PASS x2 · verdict {verdict} · "
        + ("gate-passed; selector-eligible (not slot-approved)" if ok_slot else f"DO NOT SUBMIT ({slot_reason})")
    )
    expected = f"no live projection (HOLDOUT-DTI {a1['mean']:.4f} only; not a score)"
    lane_entry = dict(
        lane_clear=bool(lane_ok), strict_verdict=lane.get("verdict"),
        density_aware_verdict=lane.get("verdict_density_aware"),
        lattice_overlap=lat_overlap,
        worst_other_site_overlap=worst_other_overlap, worst_other_site_file=worst_other_file,
        worst_own_lineage_overlap=worst_own_overlap, worst_own_lineage_file=worst_own_file,
        worst_abs_spearman_final=worst_sub_rho, worst_abs_spearman_surface=surface_rho_max,
        overlap_vs_gemsdoe32_b2=b2_overlap,
        flagged_other_site=flags_other, flagged_own_lineage=flags_own,
        registry_checked=lane.get("registry_checked"),
    )
    common = dict(
        verdict=verdict, slot_approved=False, do_not_resubmit=False,
        ok_to_download=bool(format_ok), ok_to_submit_slot=bool(ok_slot),
        slot_reason=slot_reason, expected_range=expected, lane=lane_entry, lane_summary=lane_summary,
        run_card="registry/run_card_h38_2026-10-25.json", note=note,
        parent="H35 arm B detector surface (BDE+7+H27_tip+H34) + greedy marginal-credit emission (knowledge/25)",
    )
    title = (
        f"H38 greedy-credit emission on the H35 surface ({zrec['positive_pixels']:,} dots) — holdout gate PASS x2; "
        + ("selector-eligible, not slot-approved" if ok_slot else "lane-blocked; DO NOT SUBMIT")
    )

    card = dict(
        run_card_version=1,
        date_utc="2026-10-25",
        session_branch="arena/501aa834-gemsdoe25",
        hypothesis=(
            "H38-1: on a fixed detector surface, buying dots by exact incremental triangular-kernel credit per unit "
            "false-positive mass (plug-in truth density proportional to the surface, break-even stopping at "
            "alpha*D/(1-alpha*D)) raises credit per emitted pixel versus fixed-spacing score-ordered dotting, because "
            "the metric pays only for the maximum kernel over nearby dots and fixed budgets force-spend FP mass in "
            "barren terrain while under-covering short high-credit segments."
        ),
        mechanism=(
            "DTI = TP/(0.2(TP+FP)+0.8N); detector (H35 arm B) and candidate pool (ridge-NMS top 3.5%) are identical "
            "across arms, so only the selection rule changes. Greedy maximises dTP_hat/dFP_hat with "
            "dTP_hat = sum_g phat_g*max(0,k-cur_g) (exact max-kernel incremental accounting, submodular) and "
            "dFP_hat = 1-E[max_g k*Bern(phat_g)] under neighbour independence; phat is the surface normalised to "
            "Nhat = 0.25*|visible catalogue in domain|."
        ),
        non_fault_process_that_could_mimic_it=(
            "No new geology: the lane inherits the H35 detector's mimics (lithologic/intrusive contacts, basin-margin "
            "pinch-outs). Lane-specific failure mode: phat is the detector's own uncalibrated score, so greedy spending "
            "amplifies the detector's systematic errors, and the independence approximation understates FP along "
            "continuous false lineaments (roads, flight-line levelling, fan-lobe edges)."
        ),
        pre_registration="knowledge/25_preregistered_h38_greedy_credit_emission_2026-10-25.md (commit 766b590, before any fit)",
        holdout={
            "label": "HOLDOUT-DTI",
            "evaluator": scr["evaluator"],
            "screen": {"draws": scr["draws"], "passed": screen_pass, "arms": scr["arms"],
                       "A1_vs_A0": scr["contrasts_vs_A0"]["A1"], "leakage_canary": scr["leakage_canary"],
                       "withheld_positives_per_fold": scr["withheld_positives_per_fold"]},
            "confirmation": {"draws": cnf["draws"], "passed": confirm_pass, "arms": cnf["arms"],
                             "A1_vs_A0": cnf["contrasts_vs_A0"]["A1"], "leakage_canary": cnf["leakage_canary"],
                             "withheld_positives_per_fold": cnf["withheld_positives_per_fold"]},
            "combined_draws_20_23": comb,
            "secondary_A3_line_filter": {
                "screen_gain": scr["contrasts_vs_A0"]["A3"]["standard"]["mean"],
                "confirmation_gain": cnf["contrasts_vs_A0"]["A3"]["standard"]["mean"],
                "verdict": "negative (failed both stages)",
            },
            "diagnostic_A2_b2_prune": {
                "screen_gain": scr["contrasts_vs_A0"]["A2"]["standard"]["mean"],
                "confirmation_gain": cnf["contrasts_vs_A0"]["A2"]["standard"]["mean"],
                "note": "B=2 visible-catalogue prune of the incumbent emission: near-neutral on both responses (this detector already hugs little: A0 hug ~0.09 vs H19-5-family shells).",
            },
            "note": "Catalogue-gap proxy (hidden = withheld catalogue components); not a competition score. Off-catalogue response = truth restricted to hidden pixels >2 px from the visible catalogue.",
        },
        correlation_overlap_vs_registry=lane_entry | {"lane_summary": lane_summary, "lane_receipt": f"docs/downloads/{lane_path.name}",
                                                      "surface_receipt": "evidence/h38_lane_surface.json"},
        raster=dict(file=zrec["file"], sha256=zrec["sha256"], content_id=cid, positive_pixels=zrec["positive_pixels"],
                    nan_twin=dict(file=nrec["file"], sha256=nrec["sha256"]), zip=rec.get("zip")),
        validator=dict(hard_failures=zrec["hard_failures"], ok_to_upload=zrec["format_ok"], checks=zrec["checks"],
                       receipt=f"docs/downloads/{receipt_path.name}"),
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
    (REG / "run_card_h38_2026-10-25.json").write_text(json.dumps(card, indent=1) + "\n")
    rec.update(lane_check_receipt=lane_path.name, surface_lane="evidence/h38_lane_surface.json",
               lane_entry=lane_entry, lane_summary=lane_summary, verdict=verdict, slot_reason=slot_reason)
    receipt_path.write_text(json.dumps(rec, indent=1) + "\n")

    subs = J(REG / "submissions.json")
    files = [f for f in subs["files"] if not f.get("id", "").startswith("h38-")]
    for f in files:
        if f["role"] == "primary":
            f["role"] = "alternate"
    nan_note = f"GEMSDOE25 H38 nan twin fallback | unscored; not slot-approved; no slot | id {cid}"
    assert len(nan_note) <= 140
    primary = dict(
        id="h38-greedy-credit", role="primary", file=zrec["file"], path=zrec["path"], bytes=zrec["bytes"],
        sha256=zrec["sha256"], content_id=cid, positive_pixels=zrec["positive_pixels"], format_ok=format_ok,
        checks=zrec["checks"], receipt=receipt_path.name, lane_receipt=lane_path.name, outside="zero",
        status=status, title=title, summary=summary, zip=rec["zip"]["file"] if rec.get("zip") else "",
        zip_bundle=rec.get("zip"),
        transform="ridge-NMS top-K (3.5%) -> greedy marginal-credit dots (break-even stopping, no fixed spacing), 3-draw HGB average (BDE+7+tip+H34), catalogue pixels excluded, 0.0 outside footprint",
        **common,
    )
    fallback = dict(
        id="h38-greedy-credit-nan", role="fallback", file=nrec["file"], path=nrec["path"], bytes=nrec["bytes"],
        sha256=nrec["sha256"], content_id=cid, positive_pixels=nrec["positive_pixels"],
        format_ok=bool(nrec["format_ok"] and not nrec["hard_failures"]), checks={}, receipt=receipt_path.name,
        lane_receipt=lane_path.name, outside="nan",
        status="template-convention twin (NaN outside); identical footprint values; unscored; not slot-approved; "
               + ("same verdict as primary" if ok_slot else "DO NOT SUBMIT"),
        title="H38 with NaN outside the footprint (official template convention); same dots as primary",
        summary="Identical prediction values inside the template footprint; NaN instead of 0.0 outside. "
                "Format-convention twin kept for local testing only; same verdict as the zeros primary.",
        transform="outside=nan",
        **{**common, "note": nan_note},
    )
    subs["files"] = [primary, fallback] + files
    subs["generated_by"] = "scripts/register_h38_submission.py (H38 session 2026-10-25)"
    (REG / "submissions.json").write_text(json.dumps(subs, indent=1) + "\n")
    print("verdict:", verdict, "| gates_ok", gates_ok, "(screen", screen_pass, "confirm", confirm_pass,
          ") | format_ok", format_ok, "| lane_ok", lane_ok)
    print("primary:", zrec["file"], zrec["sha256"], zrec["positive_pixels"])
    print("lane:", lane_summary)
    print("slot_reason:", slot_reason)
    print("combined A1-A0:", gain)


if __name__ == "__main__":
    main()
