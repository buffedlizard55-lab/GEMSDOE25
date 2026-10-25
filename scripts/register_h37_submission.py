#!/usr/bin/env python3
"""Register the H37 session file (DOC arm) + write the protocol run card.

Assembled programmatically from evidence receipts (no hand-typed result numbers):
  evidence/h37_screen/analysis.json       H37-1 DOC screen (negative)
  evidence/h37_2_screen/analysis.json     H37-2 SPR screen (negative, near-miss)
  evidence/h37_build/surface_lane_doc.json surface Spearman before placement
  docs/downloads/checks-<zeros>.json      writer/checker receipt
  docs/downloads/lane-<zeros>.json        final-dot lane receipt (literal + density-aware)
  evidence/h37_b2_recheck.json            B2 chain identities (incl. fetched B2 raster)

Verdict rule (knowledge/22 section 5): promote only if holdout screen+confirmation,
canary, lane (section 4 tiers) and exact-file validator all pass. This session both
experiments failed their screens, so the verdict is negative and the file is an
alternate testing download -- DO NOT SUBMIT; the KDC primary is unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
REG, DL, EV = ROOT / "registry", ROOT / "docs" / "downloads", ROOT / "evidence"
LATTICE = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def J(p: Path):
    return json.loads(p.read_text())


def dots(path: Path, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as s:
        return (np.nan_to_num(s.read(1), nan=0.0) > 0) & foot


def main() -> None:
    zeros = sorted(DL.glob("gems25-h37-doc-dipoffset-*-zeros.tif"))
    assert len(zeros) == 1, zeros
    zpath = zeros[0]
    npath = Path(str(zpath).replace("-zeros.tif", "-nan.tif"))
    assert npath.exists(), npath
    receipt_path = DL / f"checks-{zpath.stem}.json"
    rec = J(receipt_path)
    zrec, nrec = rec["files"]["zeros"], rec["files"]["nan"]
    note = rec["note"]
    assert len(note) <= 140 and "no slot" in note and "unscored" in note, note
    cid = zrec["content_id"]
    lane_path = DL / f"lane-{zpath.stem}.json"
    lane = J(lane_path)
    e1 = J(EV / "h37_screen" / "analysis.json")
    e2 = J(EV / "h37_2_screen" / "analysis.json")
    surf = J(EV / "h37_build" / "surface_lane_doc.json")
    b2chk = J(EV / "h37_b2_recheck.json")

    scored_names = {p.name for p in (ROOT / "data" / "scored").glob("*.tif")}
    rows = [r for r in lane["rows"] if "spearman" in r]
    substantive = [r for r in rows if r["file"] in scored_names and r["file"] != LATTICE]
    lattice = next(r for r in rows if r["file"] == LATTICE)
    lineage = [r for r in rows if r["file"] not in scored_names and r["file"] != zpath.name]
    worst_sub_ov = max(r["dots_within_3px"] for r in substantive)
    worst_sub_rho = max(abs(r["spearman"]) for r in substantive)
    worst_lin_ov = max(r["dots_within_3px"] for r in lineage)
    worst_lin_file = max(lineage, key=lambda r: r["dots_within_3px"])["file"]

    # explicit comparison vs the owner-reported 0.2778 B2 raster (fetched + pinned)
    with rasterio.open(ROOT / "data" / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    cand = dots(zpath, foot)
    b2 = dots(Path(b2chk["fetched"]["B2"]["path"]), foot)
    d_b2 = distance_transform_edt(~b2)
    d_cand = distance_transform_edt(~cand)
    b2_ov = float((d_b2[cand] <= 3.0).mean())
    b2_rev = float((d_cand[b2] <= 3.0).mean())
    b2_cov = float(((d_b2 <= 3.0) & foot).sum() / int(foot.sum()))

    format_ok = bool(zrec["format_ok"] and nrec["format_ok"]
                     and not zrec["hard_failures"] and not nrec["hard_failures"])
    holdout_ok = bool(e1["gate"]["passed"] or e2["gate"]["passed"])
    lane_substantive_ok = bool(worst_sub_ov <= 0.70 and worst_sub_rho <= 0.90
                               and surf["worst_abs_spearman"] <= 0.90 and not lane["sha_in_artifact_ledger"])
    verdict = "promote" if (holdout_ok and format_ok and lane_substantive_ok
                            and worst_lin_ov <= 0.70) else "negative"

    lane_summary = (
        f"vs other-site substantive scored rasters: worst 3-px overlap {worst_sub_ov:.3f}, worst final |rho| "
        f"{worst_sub_rho:.3f}, worst pre-placement surface |rho| {surf['worst_abs_spearman']:.3f} (caps 0.70/0.90) -- clean; "
        f"vs H33-2-B2 (0.2778 file) overlap {b2_ov:.3f} (reverse {b2_rev:.3f}); "
        f"dense r13 lattice: literal overlap {lattice['dots_within_3px']:.3f} but halo coverage "
        f"{lattice['halo_coverage_3px']:.4f} (a random file scores the same; symmetric-min "
        f"{lattice['symmetric_min_overlap_3px']:.3f}); "
        f"own lineage (same detector family): worst overlap {worst_lin_ov:.3f} vs {worst_lin_file} -- "
        f"duplicate lane vs superseded H31/H35 lineage, never submit alongside them"
    )
    g1, g2 = e1["primary_A37_vs_C37"], e2["primary_A37S_vs_C37"]
    status = ("UNIQUE FILE BY CONTENT - DO NOT SUBMIT: both pre-registered holdout screens failed "
              "(H37-1 DOC paired -0.0009, 2/4 folds; H37-2 SPR +0.00094 vs +0.001 gate, 3/4 folds); "
              "lane-duplicate vs own H31/H35 lineage; unscored; not slot-approved")
    summary = (
        "Session-7 file (knowledge/22-24): H35 arm-B detector (BDE+7 + directed tip + H34 RESMAG-FLEX) "
        "plus six DOC down-dip offset concordance columns (gravity/magnetic/conductive-base ridge fields "
        "sampled 200-400 m downhill of the candidate trace), 3-draw HGB average, ridge-NMS top-K 3.5%, "
        "score-ordered dots at 2.4 px, catalogue pixels excluded. HOLDOUT-DTI screen (draws 14-15, "
        f"withheld positives per fold {e1['withheld_positives_per_fold']}): A37 {e1['arms']['A37']['mean']:.4f} "
        f"(pooled {e1['arms']['A37']['pooled_dti']:.4f}) vs same-run H35-B control {e1['arms']['C37']['mean']:.4f}; "
        f"paired gain {g1['mean']:+.4f} (95% CI {g1['ci95'][0]:+.4f} to {g1['ci95'][1]:+.4f}), {g1['folds_positive']}/4 folds "
        f"-> frozen gate FAILED; leakage canary max AUC {e1['leakage_canary']['doc_max_feature_auc']:.3f} (no leakage). "
        f"Second pre-registered experiment H37-2 (spring-line alignment ridge, draws 18-19): paired gain "
        f"{g2['mean']:+.5f} vs the +0.001 gate, {g2['folds_positive']}/4 folds, canary "
        f"{e2['leakage_canary']['spr_max_feature_auc']:.3f} -> gate FAILED (near-miss is not a pass). "
        "HOLDOUT-DTI is a catalogue-gap proxy, not a competition score; no live effect is claimed. "
        f"Lane: {lane_summary}. Zeros-outside primary has every cell finite in [0,1]; NaN twin identical in-footprint. "
        "Download for local testing only; do not spend a weekly slot."
    )
    entry = dict(id="h37-doc-dipoffset", role="alternate", verdict=verdict, file=zrec["file"],
                 path=zrec["path"], bytes=zrec["bytes"], sha256=zrec["sha256"], content_id=cid,
                 positive_pixels=zrec["positive_pixels"], format_ok=format_ok, checks=zrec["checks"],
                 receipt=receipt_path.name, lane_receipt=lane_path.name, lane_summary=lane_summary,
                 outside="zero", status=status,
                 title="H37 DOC down-dip offset dots (zeros outside) - holdout gates failed; DO NOT SUBMIT",
                 summary=summary,
                 expected_range=(f"no competition estimate (HOLDOUT-DTI only: A37 {e1['arms']['A37']['mean']:.4f}, "
                                 f"95% CI {e1['arms']['A37']['ci95'][0]:.4f}-{e1['arms']['A37']['ci95'][1]:.4f}; "
                                 f"same-run control {e1['arms']['C37']['mean']:.4f})"),
                 note=note,
                 parent="H37-1 DOC arm (knowledge/22) on H35 arm B; H37-2 SPR (knowledge/23) also negative, no SPR file built",
                 transform="ridge-NMS top-K (3.5%) -> score-ordered dots 2.4 px, 3-draw HGB average, catalogue pixels excluded, 0.0 outside footprint",
                 slot_approved=False, do_not_resubmit=False, holdout_gate_passed=False,
                 ok_to_download=True, ok_to_submit_slot=False,
                 run_card="registry/run_card_h37_2026-10-25.json",
                 lane=dict(lane_clear=False,
                           policy="knowledge/22 section 4: literal + density-aware (halo coverage + symmetric-min for coverage>=0.70 rasters)",
                           worst_overlap_substantive_scored=worst_sub_ov,
                           worst_abs_spearman_substantive_scored=worst_sub_rho,
                           worst_abs_spearman_surface=surf["worst_abs_spearman"],
                           vs_h33_2_b2=dict(overlap=b2_ov, reverse=b2_rev, halo_coverage=b2_cov),
                           lattice=dict(literal_overlap=lattice["dots_within_3px"],
                                        halo_coverage=lattice["halo_coverage_3px"],
                                        symmetric_min=lattice["symmetric_min_overlap_3px"]),
                           worst_overlap_own_lineage=worst_lin_ov, worst_lineage_file=worst_lin_file),
                 zip=rec["zip"]["file"])
    twin_note = f"GEMSDOE25 H37 DOC nan twin fallback | unscored; not slot-approved; no slot | id {cid}"
    assert len(twin_note) <= 140
    twin = dict(id="h37-doc-dipoffset-nan", role="fallback", verdict=verdict, file=nrec["file"],
                path=nrec["path"], bytes=nrec["bytes"], sha256=nrec["sha256"], content_id=cid,
                positive_pixels=nrec["positive_pixels"], format_ok=bool(nrec["format_ok"]), checks={},
                receipt=receipt_path.name, lane_receipt=lane_path.name, outside="nan",
                status="template-convention twin (NaN outside); identical footprint values; unscored; not slot-approved; DO NOT SUBMIT",
                title="NaN-outside twin of the H37 DOC file (same dots) - DO NOT SUBMIT",
                summary="Identical prediction values inside the template footprint; NaN instead of 0.0 outside, matching the template convention. Research/testing twin only: holdout gates failed, so do not upload either H37 file.",
                expected_range=entry["expected_range"], note=twin_note, parent="h37-doc-dipoffset",
                transform="outside=nan", slot_approved=False, do_not_resubmit=False,
                holdout_gate_passed=False, ok_to_download=True, ok_to_submit_slot=False,
                run_card="registry/run_card_h37_2026-10-25.json", lane_summary=lane_summary)

    subs = J(REG / "submissions.json")
    keep = [s for s in subs["files"] if s["id"] not in ("h37-doc-dipoffset", "h37-doc-dipoffset-nan")]
    subs["files"] = keep + [entry, twin]
    subs["generated_by"] = "scripts/register_h37_submission.py (session 7, 2026-10-25)"
    (REG / "submissions.json").write_text(json.dumps(subs, indent=1) + "\n")

    rec.update(file=zrec["file"], sha256=zrec["sha256"], content_id=cid, verdict=verdict,
               lane_check_receipt=lane_path.name)
    receipt_path.write_text(json.dumps(rec, indent=1) + "\n")

    # ---- protocol run card (PARALLEL-RUN PROTOCOL item 5) ----
    card = {
        "run_card_version": 1,
        "date_utc": "2026-10-25",
        "session_branch": "arena/97b7bf66-gemsdoe25",
        "hypothesis": ("H37-1 DOC: subsurface steps offset 200-400 m down-dip (downhill) of the surface "
                       "trace mark buried basin-margin faults missed by zero-lag concordance features. "
                       "H37-2 SPR: aligned hot-spring discharge (ridge/elongation of the spring KDE) "
                       "marks permeable unmapped faults."),
        "mechanism": ("Detector = H35 arm B (BDE+7+H27_tip+H34 RESMAG-FLEX HGB, sapd2.4/k3.5%) + 6 DOC "
                      "lagged-ridge columns (E1) or + 2 SPR spring-line columns (E2); same-run paired "
                      "control C37 = H35-B recomputed per cell. DTI = TP/(0.2(TP+FP)+0.8N); a better "
                      "detector raises mean credit per emitted pixel."),
        "non_fault_process_that_could_mimic_it": ("DOC: alluvial-fan wedges prograding off unfaulted bedrock "
                                                  "slopes, lava-flow/intrusion margins, Lake Lahontan shoreline benches. "
                                                  "SPR: fan-toe/lithologic-contact spring lines, valley/road sampling bias."),
        "pre_registration": ["knowledge/22_preregistered_h37_doc_down_dip_offset_2026-10-25.md (commit 7618687)",
                             "knowledge/23_preregistered_h37_2_spring_line_2026-10-25.md (commit 75696c8; amendment disclosed there)"],
        "experiments": [
            {"id": "E1 H37-1 DOC screen", "evidence": "evidence/h37_screen/", "draws": [14, 15],
             "label": "HOLDOUT-DTI", "evaluator": e1["evaluator"],
             "candidate_mean": e1["arms"]["A37"]["mean"], "candidate_ci95": e1["arms"]["A37"]["ci95"],
             "candidate_pooled": e1["arms"]["A37"]["pooled_dti"],
             "control_mean": e1["arms"]["C37"]["mean"], "control_pooled": e1["arms"]["C37"]["pooled_dti"],
             "paired_gain_mean": g1["mean"], "paired_gain_ci95": g1["ci95"],
             "per_fold_gain": g1["per_fold"], "folds_positive": g1["folds_positive"],
             "worst_fold": g1["worst_fold"], "hug_mean": g1["hug_mean"],
             "withheld_positives_per_fold": e1["withheld_positives_per_fold"],
             "leakage_canary_max": e1["leakage_canary"]["doc_max_feature_auc"],
             "gate_passed": e1["gate"]["passed"], "verdict": "FAIL (no confirmation run)"},
            {"id": "E2 H37-2 SPR screen", "evidence": "evidence/h37_2_screen/", "draws": [18, 19],
             "label": "HOLDOUT-DTI", "evaluator": e2["evaluator"],
             "candidate_mean": e2["arms"]["A37S"]["mean"], "candidate_ci95": e2["arms"]["A37S"]["ci95"],
             "candidate_pooled": e2["arms"]["A37S"]["pooled_dti"],
             "control_mean": e2["arms"]["C37"]["mean"], "control_pooled": e2["arms"]["C37"]["pooled_dti"],
             "paired_gain_mean": g2["mean"], "paired_gain_ci95": g2["ci95"],
             "per_fold_gain": g2["per_fold"], "folds_positive": g2["folds_positive"],
             "worst_fold": g2["worst_fold"], "hug_mean": g2["hug_mean"],
             "withheld_positives_per_fold": e2["withheld_positives_per_fold"],
             "leakage_canary_max": e2["leakage_canary"]["spr_max_feature_auc"],
             "gate_passed": e2["gate"]["passed"],
             "verdict": "FAIL (mean gain +0.00094 < +0.001 gate; no confirmation run)"},
        ],
        "holdout_dti": {"label": "HOLDOUT-DTI", "evaluator": e1["evaluator"],
                        "A37_mean": e1["arms"]["A37"]["mean"], "A37_ci95": e1["arms"]["A37"]["ci95"],
                        "A37_pooled": e1["arms"]["A37"]["pooled_dti"],
                        "C37_mean_draws14_15": e1["arms"]["C37"]["mean"],
                        "withheld_positives_per_fold": e1["withheld_positives_per_fold"],
                        "note": "catalogue-gap proxy; not ORGANIZER-CONFIRMED; no live score implied"},
        "b2_recheck": {"identities": b2chk["identities"], "counts": b2chk["counts"],
                       "evidence": "evidence/h37_b2_recheck.json",
                       "reading": "B2 (0.2778 OWNER) = D2.8 & d(cat)>2px pixel-exact (XOR 0); emission economics, not new geology"},
        "correlation_overlap_vs_registry": {
            "caps": {"spearman": 0.90, "overlap": 0.70, "radius_px": 3.0},
            "registry_checked": lane["registry_checked"],
            "surface_worst_abs_spearman_before_placement": surf["worst_abs_spearman"],
            "substantive_scored_worst_overlap": worst_sub_ov,
            "substantive_scored_worst_abs_spearman_final": worst_sub_rho,
            "vs_h33_2_b2": {"overlap": b2_ov, "reverse": b2_rev, "halo_coverage": b2_cov},
            "lattice": {"literal_overlap": lattice["dots_within_3px"],
                        "halo_coverage": lattice["halo_coverage_3px"],
                        "excess_over_coverage": lattice["excess_overlap_over_coverage"],
                        "symmetric_min": lattice["symmetric_min_overlap_3px"]},
            "own_lineage_worst_overlap": worst_lin_ov, "own_lineage_worst_file": worst_lin_file,
            "flagged_literal": lane["flagged_literal"], "flagged_lane_density_aware": lane["flagged_lane"],
            "sha_in_artifact_ledger": lane["sha_in_artifact_ledger"],
            "lane_verdict": ("UNIQUE BY CONTENT vs other-site substantive rasters; DUPLICATE LANE vs own "
                             "H31/H35 lineage (same detector family) -- supersession tier, never submit "
                             "alongside them; lattice literal flag is non-discriminative (coverage 0.9987)")},
        "shipped_file": {"zeros": entry["file"], "sha256": entry["sha256"], "content_id": cid,
                         "positive_pixels": entry["positive_pixels"], "bytes": entry["bytes"],
                         "nan_twin": nrec["file"], "nan_sha256": nrec["sha256"],
                         "zip": rec["zip"]["file"]},
        "raster_sha256": entry["sha256"],
        "validator_output": {"ok_to_upload_format": format_ok, "hard_failures": zrec["hard_failures"],
                             "checks_pass": {k: v["pass_"] for k, v in zrec["checks"].items()},
                             "footprint": "5,167,373 px all finite in [0,1]; EPSG:32611; 3730x3292; transform matches pinned owner-mirror template (not organizer-authenticated)"},
        "submission_name": entry["file"],
        "note": note, "note_chars": len(note),
        "ok_to_download_local_testing": True,
        "ok_to_submit_slot": False,
        "verdict": verdict,
        "verdict_reason": ("Both pre-registered screens failed their frozen gates (E1 paired -0.0009, 2/4 "
                           "folds; E2 +0.00094 vs +0.001, 3/4 folds). The file is unique by content and "
                           "format-valid, lane-clean vs other-site substantive rasters, but lane-duplicate "
                           "vs its own H31/H35 detector lineage. DO NOT SUBMIT. H33-2-B2 (OWNER 0.2778) "
                           "remains the strongest known file; no file here is shown to beat it."),
        "deviation_from_preregistration": ("knowledge/22 section 3's session stopping sentence was amended "
                                           "by knowledge/23 BEFORE any SPR computation to allow the "
                                           "pre-ranked experiment 2 (IR-25-H37-AMENDMENT). The TIF was "
                                           "built despite failed gates per the owner's highest-urgency "
                                           "unique-download requirement (knowledge/22 section 5 frozen "
                                           "policy), labelled negative everywhere."),
        "limitations": ["Registry for lane checks = restored data/scored (11) + docs/downloads (15) + fetched focus rasters for B2; newer sibling-session lanes are not pinned here (IR-25-GEMSDOE32-NEW-LANES-UNCHECKED).",
                        "Holdout truth is withheld catalogue components; it cannot reward genuinely off-catalogue faults or test catalogue-flank pruning (IR-25-HOLDOUT-DOES-NOT-TEST-PRUNING).",
                        "Leaderboard figures 0.4413/0.3195/0.3262 are OWNER claims in conflict (IR-25-LEADERBOARD-CONFLICT); template is owner-mirror, not organizer-authenticated (IR-25-PROVENANCE)."],
    }
    (REG / "run_card_h37_2026-10-25.json").write_text(json.dumps(card, indent=1) + "\n")
    print("verdict:", verdict, "| format_ok", format_ok, "| holdout_ok", holdout_ok)
    print("primary (alternate):", entry["file"], entry["sha256"], entry["positive_pixels"])
    print("lane:", lane_summary)


if __name__ == "__main__":
    main()
