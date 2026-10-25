#!/usr/bin/env python3
"""HISTORICAL (pre-merge state of PR #18): do not re-run on the merged tree.

This registered H35 as primary under this session's substantive-lane reading. The
merged origin/main strict literal lane policy superseded that registration; the
merged registry/submissions.json was then hand-reconciled (H35 = alternate,
DO NOT SUBMIT; see registry/run_card_h35_2026-10-25.json post_merge_addendum).

Register the H35 candidate in registry/submissions.json from evidence + lane receipts.

Verdict rule (knowledge/18-19): ``promote`` (eligible for the owner's separate selector
step; ``slot_approved`` stays False — this agent never approves/uploads a slot) only if
H35 screen+confirmation gates passed, both TIFs pass all hard format checks, the surface
Spearman screen passes, and no *substantive scored* registry raster is lane-flagged.
The dense 13GEMSDOE lattice and this repo's own unscored predecessor (H31-C, same lineage)
are disclosed as caveats in the lane summary; they are not silently treated as clean.
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
    zeros = sorted(DL.glob("gems25-h35-resmag-tip-*-zeros.tif"))
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

    scr = J(EV / "h35_screen" / "analysis.json")
    cnf = J(EV / "h35_confirm" / "analysis.json")
    comb = J(EV / "h35_confirm" / "combined_analysis.json")
    gates_ok = bool(scr["gate"]["passed"] and cnf["gate"]["passed"]
                    and scr["leakage_canary"]["passed"] and cnf["leakage_canary"]["passed"])
    lane_path = DL / f"lane-{zpath.stem}.json"
    lane = J(lane_path)
    surface = J(EV / "h35_lane_surface.json")
    scored_names = {p.name for p in (ROOT / "data" / "scored").glob("*.tif")}
    scored_rows = [r for r in lane["rows"] if r.get("file") in scored_names and "spearman" in r]
    downloads_rows = [r for r in lane["rows"] if r.get("file") not in scored_names and "spearman" in r]
    substantive = [r for r in scored_rows if r["file"] != LATTICE]
    flags_substantive = [r["file"] for r in substantive if r["flag_rank"] or r["flag_overlap"] or r["byte_identical"]]
    worst_scored_overlap = max((r["dots_within_3px"] for r in substantive), default=0.0)
    worst_scored_rho = max((abs(r["spearman"]) for r in scored_rows), default=0.0)
    h31_rows = [r for r in downloads_rows if "h31-control" in r["file"]]
    h31_overlap = max((r["dots_within_3px"] for r in h31_rows), default=0.0)
    surface_ok = bool(surface["worst_abs_spearman"] <= 0.90 and not surface["flagged"])
    format_ok = bool(zrec["format_ok"] and nrec["format_ok"] and not zrec["hard_failures"] and not nrec["hard_failures"])
    lane_ok = bool(not flags_substantive and worst_scored_rho <= 0.90 and surface_ok
                   and not lane["sha_in_artifact_ledger"])
    verdict = "promote" if (gates_ok and format_ok and lane_ok) else "negative"

    lane_summary = (
        f"vs substantive scored registry rasters: worst |Spearman| (final TIF) {worst_scored_rho:.3f}, "
        f"worst surface |Spearman| {surface['worst_abs_spearman']:.3f}, worst 3-px dot overlap "
        f"{100 * worst_scored_overlap:.1f}% (caps 0.90 / 70%)"
        + ("; no substantive flag." if not flags_substantive else f"; FLAGGED: {flags_substantive}.")
        + f" Caveats disclosed, not cleared: the dense 13GEMSDOE lattice flags any emission (IR-25-LANE-DENSITY), "
          f"and overlap vs this repo's own unscored predecessor H31-C is {100 * h31_overlap:.1f}% "
          f"(same-detector lineage; H31-C is superseded below — never submit both)."
    )
    b, c = comb["arms"]["B"], comb["arms"]["C"]
    gain = comb["primary_B_vs_C"]
    holdout_txt = (f"HOLDOUT-DTI B {b['mean']:.4f} (95% CI {b['ci95'][0]:.4f}–{b['ci95'][1]:.4f}) vs same-run control "
                   f"{c['mean']:.4f}; paired gain {gain['mean']:+.4f} (95% CI {gain['ci95'][0]:+.4f}–{gain['ci95'][1]:+.4f}), "
                   f"{gain['folds_positive']}/4 folds, withheld positives per fold {comb['withheld_positives_per_fold']}")
    status = ("GATE-PASSED unique file — eligible for the manual selector step WITH lane caveats disclosed below; "
              "unscored; not slot-approved by this agent"
              if verdict == "promote" else
              "UNIQUE FILE - NOT CLEARED: a required gate/lane/audit did not pass; do not spend a slot")
    summary = (
        f"H35 arm B full-footprint build: incumbent BDE+7 plus directed tip continuation (visible catalogue only) plus the "
        f"H34 RESMAG-FLEX block (depth-sliced RTP residual ridges + conductive-base flexure), 3-draw average, score-ordered "
        f"dots at 2.4 px, 3.5% candidate budget, catalogue pixels excluded. It beat the comparable same-run holdout best "
        f"(its paired control) under the frozen gate in screen (draws 10-11, +{scr['primary_B_vs_C']['mean']:.4f}) and "
        f"confirmation (draws 12-13, +{cnf['primary_B_vs_C']['mean']:.4f}); combined {holdout_txt}. "
        f"This is HOLDOUT-DTI (catalogue-gap proxy), not a competition score, and the paired-gain CI includes zero — "
        f"the SE fold was negative in both stages. Primary file is zeros-outside (every cell finite in [0,1]); "
        f"the NaN twin has identical footprint values. Lane: passes vs substantive scored registry rasters "
        f"(worst 3-px overlap {100 * worst_scored_overlap:.1f}%, worst surface |rho| {surface['worst_abs_spearman']:.3f}); "
        f"disclosed flags remain vs the dense lattice probe and vs this repo's own unscored H31-C predecessor "
        f"({100 * h31_overlap:.1f}% — same-detector lineage, superseded, never submit both). Verdict: {verdict} "
        f"(selector-eligible; the separate selector step owns the final slot decision)."
    )
    rec.update(file=zrec["file"], sha256=zrec["sha256"], bytes=zrec["bytes"], content_id=cid,
               positive_pixels=zrec["positive_pixels"], format_ok=format_ok, checks=zrec["checks"],
               lane_check_receipt=lane_path.name, surface_lane="evidence/h35_lane_surface.json",
               slot_eligible=False, verdict=verdict,
               holdout={"label": "HOLDOUT-DTI", "evaluator": comb["evaluator"], "combined": comb,
                        "screen": {"path": "evidence/h35_screen/analysis.json", "gain": scr["primary_B_vs_C"]["mean"]},
                        "confirmation": {"path": "evidence/h35_confirm/analysis.json", "gain": cnf["primary_B_vs_C"]["mean"]},
                        "h34_negative": "evidence/h34_screen/analysis.json"})
    receipt_path.write_text(json.dumps(rec, indent=1) + "\n")

    subs = J(REG / "submissions.json")
    files = subs["files"]
    for s in files:  # demote the H31-C primary pair in place (same lineage, superseded); idempotent
        if s["id"] == "primary" and "h31-control" in s["file"]:
            s.update(id="h31-control", role="alternate", slot_approved=False, verdict="negative",
                     status="superseded by the H35 file in the same lineage; unscored; not slot-approved; never submit both")
        elif s["id"] == "primary-zeros" and "h31-control" in s["file"]:
            s.update(id="h31-control-zeros", role="alternate", slot_approved=False, verdict="negative",
                     status="superseded zeros twin of H31-C; unscored; not slot-approved")
    nan_note = f"GEMSDOE25 H35 R+T nan twin fallback | unscored; not slot-approved; no slot | id {cid}"
    assert len(nan_note) <= 120 and "fallback" in nan_note
    primary = dict(id="primary", role="primary", verdict=verdict, file=zrec["file"], path=zrec["path"],
                   bytes=zrec["bytes"], sha256=zrec["sha256"], content_id=cid,
                   positive_pixels=zrec["positive_pixels"], format_ok=format_ok, checks=zrec["checks"],
                   receipt=receipt_path.name, lane_receipt=lane_path.name, lane_summary=lane_summary,
                   outside="zero", status=status,
                   title=f"{'Gate-passed' if verdict == 'promote' else 'Not cleared'}: H35 RESMAG+tip dots (zeros outside)",
                   summary=summary,
                   expected_range=f"no competition estimate (HOLDOUT-DTI only: {b['mean']:.4f}, 95% CI {b['ci95'][0]:.4f}–{b['ci95'][1]:.4f})",
                   note=note,
                   parent="H35 arm B (knowledge/19); detector BDE+7+H27_tip+H34 block; H34-1 alone was negative (evidence/h34_screen)",
                   transform="ridge-NMS top-K (3.5%) -> score-ordered dots 2.4 px, 3-draw HGB average, catalogue pixels excluded, 0.0 outside footprint",
                   slot_approved=False, do_not_resubmit=False)
    fallback = dict(id="primary-nan", role="fallback", verdict=verdict, file=nrec["file"], path=nrec["path"],
                    bytes=nrec["bytes"], sha256=nrec["sha256"], content_id=cid,
                    positive_pixels=nrec["positive_pixels"], format_ok=bool(nrec["format_ok"]), checks={},
                    receipt=receipt_path.name, lane_receipt=lane_path.name, outside="nan",
                    status="template-convention twin (NaN outside); identical footprint values; unscored; not slot-approved",
                    title="NaN-outside twin of the H35 primary (same dots)",
                    summary="Identical prediction values inside the template footprint; NaN instead of 0.0 outside, matching the template convention. Upload the zeros primary first (strictest [0,1] validator); use this twin only if the portal rejects zeros.",
                    expected_range=primary["expected_range"], note=nan_note, parent="primary",
                    transform="outside=nan", slot_approved=False, do_not_resubmit=False)
    others = [s for s in files if s["id"] not in ("primary", "primary-nan", "primary-zeros")]
    subs["files"] = [primary, fallback] + others
    subs["generated_by"] = "scripts/register_h35_submission.py (H34/H35 session 2026-10-25)"
    (REG / "submissions.json").write_text(json.dumps(subs, indent=1) + "\n")
    print("verdict:", verdict, "| gates_ok", gates_ok, "| format_ok", format_ok, "| lane_ok", lane_ok,
          "| flags_substantive", flags_substantive)
    print("primary:", zrec["file"], zrec["sha256"], zrec["positive_pixels"])
    print("lane:", lane_summary)


if __name__ == "__main__":
    main()
