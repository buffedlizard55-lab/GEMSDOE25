#!/usr/bin/env python3
"""Register the newest KDC build (docs/downloads/checks-gems25-kdc-*.json) in registry/submissions.json.

Featured download: the KDC zeros file becomes role "primary" and its NaN twin "fallback". The previous primary is demoted to
"alternate" with its own labels unchanged. Why KDC is featured: it is the only unique file that keeps all 37,654 dots of the
owner-reported 0.2778 file (evidence/kdc_build/candidates_vs_b2.json). Featuring a file is NOT slot approval: under the strict
lane policy (PR #14) every file, including this one, is DO NOT SUBMIT.

--note replaces the DrivenData note. The note is not embedded in the TIF, so bytes and SHA-256 are unchanged; the original is
kept in the receipt as note_original. Idempotent.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATTICE = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
TITLE = "KDC — H33-2-B2 (all 37,654 dots) + 17,720 new model dots; unique content, strict lane stop; testing only, do not submit"
SUMMARY = ("Additive complement design (G25-K1, knowledge/17): keep every dot of the owner-reported 0.2778 H33-2-B2 file and add 17,720 "
           "score-ordered dots from this repo's full-catalogue HGB (BDE + 7 add-ons; reproduces H31-C content id 9edd6bed8268) on ridge "
           "pixels > 3 px from B2/H19-5, > 2 px from the catalogue and > 3 px from every other-site registry raster's dots. "
           "Pre-registered holdout gate FAILED (paired −0.0007 vs best same-run control, 2/4 folds; efficiency R 0.505). "
           "The strict lane gate fails only on the dense r13 lattice ({lat:.1%} of dots within 3 px; 70 % limit); against the other "
           "{n_sub} registry rasters the worst overlap is {worst:.3f}. HOLDOUT-DTI is a research proxy, not a competition score. "
           "Download for local testing; do not submit.")
STATUS = ("UNIQUE BY CONTENT · FORMAT-VALID · STRICT LANE FAIL (r13 lattice {lat:.1%}; clean vs the other {n_sub} registry rasters, "
          "worst {worst:.3f}) · pre-registered holdout gate FAILED · verdict negative · DO NOT SUBMIT")
APPEND = {
    "gem1-blind-magnetics": " | KDC E1 (2026-10-25): as a complement to the best same-run control, GEM-1 ranking was random-level "
                            "(R 0.167 vs random 0.183; IR-25-GEM1-WEAK-CONTROL).",
    "primary-gem-fuse1": " | 2026-10-25 audit: keeps only 465 of B2's 37,654 dots (1.2 %); its holdout gate used control_B_crest "
                         "(DTI 0.019–0.021), not the best same-run control (IR-25-GEM-FUSE1-WEAK-CONTROL).",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--note", default=None, help="replacement DrivenData note (<= 120 chars, repo rule)")
    a = ap.parse_args()
    ck = Path(sorted(glob.glob(str(ROOT / "docs" / "downloads" / "checks-gems25-kdc-*.json")))[-1])
    d = json.loads(ck.read_text())
    if a.note:
        need = ("no slot", "unscored", "not slot-approved", d["content_id"])
        if len(a.note) > 120 or not all(t in a.note for t in need):
            raise SystemExit(f"note must be <= 120 chars and contain {need}")
        d.setdefault("note_original", d["note"])
        d["note"], d["note_chars"] = a.note, len(a.note)
    lane = d["lane"]
    rows = lane["rows"]
    lat = next(r["overlap_within_3px"] for r in rows if r["file"] == LATTICE)
    subs_rows = [r for r in rows if r["file"] != LATTICE and not r["file"].startswith("gems25-")]
    worst = max(r["overlap_within_3px"] for r in subs_rows)
    n_sub = len({r["file"] for r in subs_rows})
    d["strict_lane"] = dict(policy="literal 70 % / 3 px, no density exception (PR #14)", lattice_file=LATTICE,
                            lattice_overlap=lat, lane_clear=lat <= 0.70 and worst <= 0.70,
                            strict_verdict="DUPLICATE LANE / STOP (r13 lattice)" if lat > 0.70 else "clear",
                            worst_other_registry_overlap=worst, other_registry_rasters=n_sub)
    ck.write_text(json.dumps(d, indent=1) + "\n")
    v = d["validator"]["primary"]
    fmt = dict(lat=lat, n_sub=n_sub, worst=worst)
    lane_entry = dict(lane_clear=d["strict_lane"]["lane_clear"], strict_verdict=d["strict_lane"]["strict_verdict"],
                      lattice_overlap=lat, worst_other_registry_overlap=worst,
                      worst_abs_spearman_final=lane["worst_abs_spearman_final"],
                      worst_abs_spearman_surface=lane["worst_abs_spearman_surface"])
    common = dict(
        verdict=d["verdict"], slot_approved=False, do_not_resubmit=True, ok_to_download=bool(v["ok_to_upload"]), ok_to_submit_slot=False,
        expected_range="0.25–0.31 (projection, not a score)", lane=lane_entry,
        lane_summary=(f"strict lane FAIL on the r13 lattice ({lat:.1%} within 3 px); vs the other {n_sub} registry rasters worst "
                      f"overlap {worst:.3f}, worst final-dot Spearman {lane['worst_abs_spearman_final']:.3f}, pre-placement surface "
                      f"Spearman ≤ {lane['worst_abs_spearman_surface']:.3f}"),
        run_card="registry/run_card_kdc_2026-10-25.json", note=d["note"], title=TITLE, summary=SUMMARY.format(**fmt),
        parent="GEMSDOE32 H33-2-B2 (all dots) + GEMSDOE25 full-catalogue HGB complement")
    nan_path = ROOT / "docs" / "downloads" / d["nan_twin"]["file"]
    new = [
        dict(id="kdc-b2-complement", role="primary", file=v["file"], path="docs/downloads/" + v["file"], bytes=v["bytes"], sha256=v["sha256"],
             content_id=d["content_id"], positive_pixels=v["positive_pixels"], format_ok=v["ok_to_upload"], checks=v["checks"],
             receipt=ck.name, outside="zero", status=STATUS.format(**fmt), zip=d["zip"]["file"], **common),
        dict(id="kdc-b2-complement-nan", role="fallback", file=d["nan_twin"]["file"], path="docs/downloads/" + d["nan_twin"]["file"],
             bytes=os.path.getsize(nan_path), sha256=d["nan_twin"]["sha256"], content_id=d["content_id"], positive_pixels=v["positive_pixels"],
             format_ok=d["nan_twin"]["ok"], checks={}, receipt=ck.name, outside="nan",
             status="NaN-outside twin of the KDC file (same dots); same verdict: strict lane fail, holdout gate failed; DO NOT SUBMIT",
             **{**common, "title": "KDC with NaN outside the footprint (official template convention); testing only, do not submit"}),
    ]
    reg_path = ROOT / "registry" / "submissions.json"
    reg = json.loads(reg_path.read_text())
    files = [f for f in reg["files"] if not f.get("id", "").startswith("kdc-")]
    for f in files:
        if f["role"] == "primary":
            f["role"] = "alternate"
            if f.get("id") == "primary":
                f["id"] = "primary-gem-fuse1"
        extra = APPEND.get(f.get("id", ""))
        if extra and extra not in f["status"]:
            f["status"] += extra
    reg["files"] = new + files
    reg_path.write_text(json.dumps(reg, indent=1) + "\n")
    card_path = ROOT / "registry" / "run_card_kdc_2026-10-25.json"
    if card_path.exists():
        card = json.loads(card_path.read_text())
        card["note"], card["note_chars"] = d["note"], len(d["note"])
        card["strict_lane"] = d["strict_lane"]
        card_path.write_text(json.dumps(card, indent=1) + "\n")
    print([(f["role"], f.get("id"), f["file"][:50]) for f in reg["files"]], "| note:", d["note"], len(d["note"]))


if __name__ == "__main__":
    main()
