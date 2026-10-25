#!/usr/bin/env python3
"""Register the newest KDC build (docs/downloads/checks-gems25-kdc-*.json) in registry/submissions.json.

The build becomes the primary download, with its NaN twin as fallback; H31-C and GEM-1 are marked superseded. Idempotent.
--note replaces the DrivenData note (it is not embedded in the TIF, so file bytes and SHA-256 are unchanged). The
original note is kept in the receipt as note_original.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS = "UNIQUE · FORMAT-VALID · LANE-CLEAN · NOT SLOT-CLEARED (pre-registered holdout gate failed; verdict negative)"
TITLE = "New unique file: H33-2-B2 (37,654 dots) + 17,720 new model dots placed away from every registry raster"
SUMMARY = ("Additive complement design (G25-K1, knowledge/17): keep every dot of the 0.2778 H33-2-B2 file and add 17,720 score-ordered "
           "dots from this repo's full-catalogue HGB surface (BDE + 7 add-ons; reproduces H31-C content id 9edd6bed8268) on ridge pixels "
           "> 3 px from B2/H19-5, > 2 px from the catalogue and > 3 px from every other-site registry raster's dots (lane rule). "
           "B2 share 68 %. Holdout analogue failed its frozen gate (paired −0.0007 vs best same-run control, 2/4 folds; R 0.505). "
           "Format and lane checks pass. Format validity is not a competition score, and this file has not beaten the comparable "
           "same-run holdout best.")
GEM1 = ("SUPERSEDED / NOT RECOMMENDED: its PR #12 holdout comparison used a weak control (B_crest, 0.02); as a complement to the "
        "0.15 control it was random-level (E1 K_gem1 R 0.167 vs K_rand 0.183; IR-25-GEM1-WEAK-CONTROL)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--note", default=None, help="replacement DrivenData note (<= 140 chars)")
    a = ap.parse_args()
    ck = Path(sorted(glob.glob(str(ROOT / "docs" / "downloads" / "checks-gems25-kdc-*.json")))[-1])
    d = json.loads(ck.read_text())
    if a.note:
        if len(a.note) > 120 or d["content_id"] not in a.note:
            raise SystemExit("note must be <= 120 chars (repo rule; DrivenData limit used: 140) and contain the content id")
        d.setdefault("note_original", d["note"])
        d["note"], d["note_chars"] = a.note, len(a.note)
        ck.write_text(json.dumps(d, indent=1) + "\n")
    v, lane = d["validator"]["primary"], d["lane"]
    common = dict(
        verdict=d["verdict"], slot_approved=False, ok_to_download=bool(v["ok_to_upload"] and lane["lane_clean"]),
        ok_to_submit_slot=False, expected_range="0.25–0.31 (projection, not a score)",
        lane_summary=(f"worst dot overlap {lane['worst_overlap']:.3f} (cap 0.70) vs {lane['worst_overlap_file']}; worst final-dot Spearman "
                      f"{lane['worst_abs_spearman_final']:.3f}; pre-placement surface Spearman ≤ {lane['worst_abs_spearman_surface']:.3f} "
                      f"(cap 0.90); {lane['n_registry']} registry rasters; 13GEMSDOE lattice treated as degenerate (IR-25-LANE-DENSITY)"),
        run_card="registry/run_card_kdc_2026-10-25.json", note=d["note"])
    nan_path = ROOT / "docs" / "downloads" / d["nan_twin"]["file"]
    new = [
        dict(id="kdc-b2-complement", role="primary", file=v["file"], path="docs/downloads/" + v["file"], bytes=v["bytes"], sha256=v["sha256"],
             content_id=d["content_id"], positive_pixels=v["positive_pixels"], format_ok=v["ok_to_upload"], checks=v["checks"],
             receipt=ck.name, outside="zero", status=STATUS, title=TITLE, summary=SUMMARY, zip=d["zip"]["file"], **common),
        dict(id="kdc-b2-complement-nan", role="fallback", file=d["nan_twin"]["file"], path="docs/downloads/" + d["nan_twin"]["file"],
             bytes=os.path.getsize(nan_path), sha256=d["nan_twin"]["sha256"], content_id=d["content_id"], positive_pixels=v["positive_pixels"],
             format_ok=d["nan_twin"]["ok"], checks={}, receipt=ck.name, outside="nan",
             status="NaN-outside twin of the primary (same dots, official NaN convention); same verdict: NOT slot-cleared",
             title="Same file with NaN outside the footprint (official template convention)",
             summary="Identical predictions inside the footprint; use only if the zeros file is rejected.", **common),
    ]
    reg_path = ROOT / "registry" / "submissions.json"
    reg = json.loads(reg_path.read_text())
    files = [f for f in reg["files"] if not f.get("id", "").startswith("kdc-")]
    for f in files:
        if f.get("content_id") == "9edd6bed8268":
            f["role"] = "superseded"
            f["status"] = ("SUPERSEDED 2026-10-25 by the KDC file; unique and format-valid but parity with its holdout control; "
                           "NOT slot-cleared")
        if f.get("id") == "gem1-blind-magnetics":
            f["role"], f["slot_approved"], f["status"] = "superseded", False, GEM1
    reg["files"] = new + files
    reg_path.write_text(json.dumps(reg, indent=1) + "\n")
    card_path = ROOT / "registry" / "run_card_kdc_2026-10-25.json"
    if card_path.exists():
        card = json.loads(card_path.read_text())
        card["note"], card["note_chars"] = d["note"], len(d["note"])
        card_path.write_text(json.dumps(card, indent=1) + "\n")
    print([(f["role"], f["file"][:64]) for f in reg["files"]], "| note:", d["note"], len(d["note"]))


if __name__ == "__main__":
    main()
