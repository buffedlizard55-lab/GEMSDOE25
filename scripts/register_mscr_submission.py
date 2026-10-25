#!/usr/bin/env python3
"""Register the MSCR build in registry/submissions.json as the featured (testing-only) download.

The MSCR zeros file becomes role "primary" and its NaN twin "fallback"; the previous primary
(KDC) is demoted to "alternate" with its labels unchanged. Featuring is NOT slot approval:
verdict negative (both of this session's pre-registered holdout gates failed; literal strict
lane stop), slot_approved stays false everywhere. Status/summary/lane text is assembled from
the build receipt, both lane receipts and the session run card. Idempotent.

    .venv/bin/python scripts/register_mscr_submission.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_CARD = "registry/run_card_session_2026-10-25_gmce_mscr.json"
TITLE = ("MSCR-1 multi-scale crest (BEST detector + 3 multi-scale crest columns) — unique content, "
         "holdout gate FAILED, strict lane stop; testing only, do not submit")
SUMMARY = ("Session candidate (knowledge/21-22): the H35-B holdout-best detector (BDE + 7 add-ons + H27_tip + 3 H34 "
           "columns) plus 3 multi-scale crest columns from det_elev (400 m crest, cross-scale persistence, 400 m trough), "
           "3-draw averaged, ridge-NMS -> top 3.5% -> score-ordered dots at 2.4 px; 48,442 dots, 0 on catalogue pixels. "
           "Pre-registered holdout screen (draws 22-23) FAILED: HOLDOUT-DTI pooled 0.161954 vs same-run BEST 0.161968, "
           "paired -0.000373 (1/4 folds); Experiment 1 (GMCE-1 gravity-magnetic coherent edge, draws 20-21) also FAILED "
           "(paired -0.001209, 1/4 folds). Leakage canaries passed (max AUC 0.654 / 0.560 <= 0.90). Surface and final-dot "
           "rank correlation <= 0.90 vs every compared raster; dots overlap <= 0.38 vs the sparse 9-site focus winners, but "
           "the literal strict lane gate fails vs dense rasters (r13 lattice 100%) and this repo's own H31/H35 lineage "
           "(0.76-0.92). HOLDOUT-DTI is a research proxy, not a competition score. Download for local testing; do not submit.")
STATUS = ("UNIQUE BY CONTENT · FORMAT-VALID · pre-registered holdout gates FAILED (GMCE -0.0012, MSCR -0.0004) · "
          "STRICT LANE FAIL (literal rule) · verdict negative · DO NOT SUBMIT")


def main() -> None:
    ck_path = sorted((ROOT / "docs/downloads").glob("checks-gems25-mscr-*.json"))[-1]
    build = json.loads(ck_path.read_text())
    card = json.loads((ROOT / RUN_CARD).read_text())
    z, nn = build["files"]["zeros"], build["files"]["nan"]
    lane_summary = card["lane"]["extended"]["reading"]
    common = dict(
        verdict="negative", slot_approved=False, do_not_resubmit=True, ok_to_download=True, ok_to_submit_slot=False,
        expected_range="no live projection computed — holdout gates FAILED (not a score)",
        lane=dict(lane_clear=False,
                  strict_verdict=card["lane"]["strict_receipt"]["verdict"],
                  lattice_overlap=card["lane"]["extended"]["lattice"][0]["cand_dots_within_3px"],
                  focus_winners=card["lane"]["extended"]["focus_site_winners_registry_top"],
                  external_sparse=card["lane"]["extended"]["external_sparse"],
                  own_lineage=card["lane"]["extended"]["own_lineage"]),
        lane_summary=lane_summary, run_card=RUN_CARD, note=build["note"], title=TITLE, summary=SUMMARY,
        parent="H35-B detector config (BDE+7+tip+H34) + MSCR-1 columns; no previous submission's dots are copied (new full-catalogue fit)")
    new = [
        dict(id="mscr-multiscale-crest", role="primary", file=z["file"], path=z["path"], bytes=z["bytes"],
             sha256=z["sha256"], content_id=z["content_id"], positive_pixels=z["positive_pixels"],
             format_ok=z["format_ok"], checks=z["checks"], receipt=ck_path.name, outside="zero",
             status=STATUS, zip=build["zip"]["file"], **common),
        dict(id="mscr-multiscale-crest-nan", role="fallback", file=nn["file"], path=nn["path"], bytes=nn["bytes"],
             sha256=nn["sha256"], content_id=nn["content_id"], positive_pixels=nn["positive_pixels"],
             format_ok=nn["format_ok"], checks=nn["checks"], receipt=ck_path.name, outside="nan",
             status="NaN-outside twin of the MSCR file (same dots); same verdict: holdout gates failed, strict lane fail; DO NOT SUBMIT",
             **{**common, "title": "MSCR-1 with NaN outside the footprint (official template convention); testing only, do not submit"}),
    ]
    reg_path = ROOT / "registry/submissions.json"
    reg = json.loads(reg_path.read_text())
    files = [f for f in reg["files"] if not f.get("id", "").startswith("mscr-")]
    for f in files:
        if f["role"] == "primary":
            f["role"] = "alternate"
    reg["files"] = new + files
    reg_path.write_text(json.dumps(reg, indent=1) + "\n")
    # fold lane + run-card pointers back into the build receipt (note untouched; tests compare it)
    build["lane_extended"] = "evidence/mscr_lane_extended.json"
    build["lane_strict"] = card["lane"]["strict_receipt"]
    build["independent_audits"] = ["evidence/mscr_independent_audit_zeros.json", "evidence/mscr_independent_audit_nan.json"]
    build["run_card"] = RUN_CARD
    ck_path.write_text(json.dumps(build, indent=1) + "\n")
    print([(f["role"], f.get("id")) for f in reg["files"]][:6], "| note:", build["note"], len(build["note"]))


if __name__ == "__main__":
    main()
