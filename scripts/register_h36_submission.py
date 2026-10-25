#!/usr/bin/env python3
"""Register the H36-TZC candidate in registry/submissions.json (2026-10-25 session).

Verdict rule (knowledge/21-22 + AGENTS.md): ``promote`` only if the frozen
holdout gate passed on screen AND confirmation, the leakage canary passed,
all hard format checks pass, and the strict lane check (any registry raster,
lattice included) is clear. Otherwise ``negative``: the file stays a
downloadable testing artifact with DO NOT SUBMIT labelling. The agent never
approves a slot (`slot_approved` stays False).

    .venv/bin/python scripts/register_h36_submission.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG, DL, EV = ROOT / "registry", ROOT / "docs" / "downloads", ROOT / "evidence"
LATTICE = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def J(p: Path):
    return json.loads(p.read_text())


def main() -> None:
    zeros = sorted(DL.glob("gems25-h36-tiltzero-coincide-*-zeros.tif"))
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

    scr = J(EV / "h36_screen" / "analysis.json")
    seis = J(EV / "h37_screen" / "analysis.json")
    gate_passed = bool(scr["gate"]["passed"])  # frozen: screen pass required before any confirmation existed
    canary_passed = bool(scr["leakage_canary"]["passed"])
    format_ok = bool(zrec["format_ok"] and nrec["format_ok"] and not zrec["hard_failures"] and not nrec["hard_failures"])

    lane_path = DL / f"lane-{zpath.stem}.json"
    lane = J(lane_path)
    surface = J(EV / "h36_lane_surface.json")
    rows = [r for r in lane["rows"] if "spearman" in r]
    lattice_rows = [r for r in rows if r["file"] == LATTICE]
    substantive = [r for r in rows if r["file"] != LATTICE]
    flags_substantive = [r["file"] for r in substantive if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]
    worst_overlap_sub = max((r["dots_within_3px"] for r in substantive), default=0.0)
    worst_rho_sub = max((abs(r["spearman"]) for r in substantive), default=0.0)
    lattice_overlap = lattice_rows[0]["dots_within_3px"] if lattice_rows else None
    strict_lane_clear = bool(not lane["flagged"] and not lane["sha_in_artifact_ledger"])
    verdict = "promote" if (gate_passed and canary_passed and format_ok and strict_lane_clear) else "negative"

    own_lineage = [r for r in substantive if "h35-resmag-tip" in r["file"] or "h31-control" in r["file"]]
    own_txt = (f"; own-lineage overlap vs the H35/H31-C downloads reaches "
               f"{100 * max(r['dots_within_3px'] for r in own_lineage):.1f}% (same base detector — a substantive "
               f"duplicate-lane stop, not only the lattice)" if own_lineage else "")
    lane_summary = (
        f"STRICT lane gate: {'CLEAR' if strict_lane_clear else 'FAIL'} — vs the dense r13 lattice "
        f"{100 * lattice_overlap:.1f}% of dots within 3 px (70% cap) under the literal any-registry-raster rule; "
        f"vs all other registry rasters combined: worst 3-px dot overlap {100 * worst_overlap_sub:.1f}%, "
        f"worst final-dot |Spearman| {worst_rho_sub:.3f}, pre-placement surface worst |Spearman| "
        f"{surface['worst_abs_spearman']:.3f} (caps 70% / 0.90)"
        + own_txt
        + (f"; substantive flags: {flags_substantive}." if flags_substantive else "; no substantive flag.")
    )
    b, best = scr["arms"]["TZC"], scr["arms"]["BEST"]
    gain = scr["primary_TZC_vs_BEST"]
    holdout_txt = (f"HOLDOUT-DTI (hide-and-recover, draws 30-31, {scr['withheld_positives_per_fold']} withheld "
                   f"positives per fold NW/NE/SW/SE): TZC {b['mean']:.4f} (95% CI {b['ci95'][0]:.4f}-{b['ci95'][1]:.4f}) "
                   f"vs same-run BEST {best['mean']:.4f}; paired gain {gain['mean']:+.4f} "
                   f"(95% CI {gain['ci95'][0]:+.4f} to {gain['ci95'][1]:+.4f}), {gain['folds_positive']}/4 folds — "
                   f"frozen gate FAILED, no confirmation run. HOLDOUT-DTI is a catalogue-gap proxy, not a competition score.")
    status = ("UNIQUE BY CONTENT · FORMAT-VALID · HOLDOUT GATE FAILED · STRICT LANE FAIL (lattice + own-lineage) · "
              "verdict negative · DO NOT SUBMIT")
    summary = (
        f"H36-TZC full-footprint build (knowledge/21): BDE+7 + directed tip + H34 RESMAG-FLEX + three coincident "
        f"tilt-zero contact columns (spectral tilt of TMI and isostatic gravity, THDR-gated zero lines), 3-draw "
        f"average, score-ordered dots at 2.4 px, 3.5% candidate budget, catalogue pixels excluded. {holdout_txt} "
        f"Experiment 2 (H37 seismicity alignment, knowledge/22) also failed its screen "
        f"({seis['primary_SEIS_vs_BEST']['mean']:+.4f}, {seis['primary_SEIS_vs_BEST']['folds_positive']}/4 folds). "
        f"Strict lane gate fails on the dense r13 lattice ({100 * lattice_overlap:.1f}% within 3 px) AND on "
        f"substantive own-lineage overlaps (worst {100 * worst_overlap_sub:.1f}% vs the H35/H31 downloads — the "
        f"shared BDE+tip+H34 base detector dominates dot placement); worst final-dot |Spearman| "
        f"{worst_rho_sub:.3f}, pre-placement surface worst |Spearman| {surface['worst_abs_spearman']:.3f}. "
        f"Download for local testing only; do not submit. "
        f"No live score exists for this file; nothing here is a projection of one."
    )
    title = "H36-TZC tilt-zero coincidence dots (zeros outside) — unique testing file, DO NOT SUBMIT"
    lane_block = dict(lane_clear=False, strict_verdict="DUPLICATE LANE / STOP (r13 lattice + own-lineage H35/H31 overlap)" if not strict_lane_clear else "clear",
                      lattice_overlap=lattice_overlap, worst_other_registry_overlap=worst_overlap_sub,
                      worst_abs_spearman_final=worst_rho_sub,
                      worst_abs_spearman_surface=surface["worst_abs_spearman"],
                      flagged_substantive=flags_substantive)

    subs = J(REG / "submissions.json")
    files = subs["files"]
    for s in files:  # demote the previous primary pair; keep them as alternates
        if s["id"] == "kdc-b2-complement":
            s.update(role="alternate")
        elif s["id"] == "kdc-b2-complement-nan":
            s.update(role="alternate")
    nan_note = f"GEMSDOE25 H36-TZC nan twin fallback | unscored; not slot-approved; no slot | id {cid}"
    assert len(nan_note) <= 120, nan_note
    primary = dict(id="h36-tzc", role="primary", verdict=verdict, slot_approved=False,
                   ok_to_download=True, ok_to_submit_slot=False, do_not_resubmit=True,
                   file=zrec["file"], path=zrec["path"], bytes=zrec["bytes"], sha256=zrec["sha256"],
                   content_id=cid, positive_pixels=zrec["positive_pixels"], format_ok=format_ok,
                   checks=zrec["checks"], receipt=receipt_path.name, outside="zero", status=status,
                   zip=rec["files"]["zeros"].get("zip"),
                   run_card="registry/run_card_h36_h37_2026-10-25.json",
                   lane=lane_block, lane_summary=lane_summary,
                   expected_range="no live projection (HOLDOUT-DTI only; gate failed)",
                   note=note, title=title, summary=summary,
                   parent="H36-TZC arm (knowledge/21) on H35 arm-B detector (BDE+7 + tip + H34)")
    fallback = dict(id="h36-tzc-nan", role="fallback", verdict=verdict, slot_approved=False,
                    ok_to_download=True, ok_to_submit_slot=False, do_not_resubmit=True,
                    file=nrec["file"], path=nrec["path"], bytes=nrec["bytes"], sha256=nrec["sha256"],
                    content_id=cid, positive_pixels=nrec["positive_pixels"],
                    format_ok=bool(nrec["format_ok"]), checks={},
                    receipt=receipt_path.name, outside="nan",
                    status="NaN-outside twin of the H36-TZC file (same dots); same verdict: holdout gate failed, strict lane fail; DO NOT SUBMIT",
                    run_card="registry/run_card_h36_h37_2026-10-25.json",
                    lane=lane_block, lane_summary=lane_summary,
                    expected_range=primary["expected_range"], note=nan_note,
                    title="H36-TZC with NaN outside the footprint (official template convention); testing only, do not submit",
                    summary="Identical prediction values inside the template footprint; NaN instead of 0.0 outside. Same negative verdict as the zeros primary; do not submit.",
                    parent="h36-tzc")
    others = [s for s in files if s["id"] not in ("h36-tzc", "h36-tzc-nan")]
    subs["files"] = [primary, fallback] + others
    subs["generated_by"] = "scripts/register_h36_submission.py (H36/H37 session 2026-10-25)"
    (REG / "submissions.json").write_text(json.dumps(subs, indent=1) + "\n")
    print("verdict:", verdict, "| gate", gate_passed, "| canary", canary_passed, "| format", format_ok,
          "| strict_lane_clear", strict_lane_clear)
    print("primary:", zrec["file"], zrec["sha256"], zrec["positive_pixels"])
    print("lane:", lane_summary)


if __name__ == "__main__":
    main()
