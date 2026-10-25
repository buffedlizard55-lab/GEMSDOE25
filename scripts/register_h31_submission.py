#!/usr/bin/env python3
"""Register the H31-C download in registry/submissions.json and demote the duplicate primary.

Idempotent: re-running reads the current receipt and rewrites the same records.
The new file is UNSCORED and NOT slot-cleared (lane flag open; holdout gate not passed). Nothing here uploads anything.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG, DL = ROOT / "registry", ROOT / "docs" / "downloads"
P = "gems25-h31-control-sapd2-4-k3p5-bde7-20261025-9edd6bed8268-nan.tif"
Z = P.replace("-nan.tif", "-zeros.tif")
CID = "9edd6bed8268"
NOTE = "GEMSDOE25 H31-C | sapd2.4, 3.5%, BDE+7 | unscored; not slot-approved; no slot | id 9edd6bed8268"
NOTE_Z = "GEMSDOE25 H31-C zeros | fallback, zeros outside | unscored; not slot-approved; no slot | id 9edd6bed8268"
DUP_SHA = "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    assert len(NOTE) <= 140 and len(NOTE_Z) <= 140
    receipt_path = DL / f"checks-{P[:-4]}.json"
    ck = json.loads(receipt_path.read_text())
    ck.pop("lane_check", None)
    ck["note"] = NOTE
    ck["note_limit_chars"] = 140
    ck["lane_check_receipt"] = f"lane-{P[:-4]}.json"
    ck["holdout"] = {
        "label": "HOLDOUT-DTI (evaluator gems25.metric.dti_binary, same-run control C of H31)",
        "value": 0.149668,
        "ci95_fold_t": [0.133069, 0.166266],
        "withheld_positives_per_fold": [1879, 2408, 3798, 3207],
        "evidence": "evidence/h31_screen/analysis.json",
    }
    ck["slot_eligible"] = False
    receipt_path.write_text(json.dumps(ck, indent=1) + "\n")

    subs = json.loads((REG / "submissions.json").read_text())
    files = subs["files"]
    old = next(s for s in files if s["sha256"] == DUP_SHA)
    assert old["sha256"] == DUP_SHA, "expected the duplicate primary"
    old.update(
        id="withdrawn-d28-duplicate",
        role="duplicate",
        status="DUPLICATE - byte-identical to a listed submission; do not submit",
        do_not_resubmit=True,
        title="Withdrawn primary: dotted H19-5 D2.8 (duplicate of a listed file)",
        withdrawal=("WITHDRAWN 2026-10-25: byte-identical to a raster the group lists as GEMSDOE24 (artifact ledger) "
                    "and GEMSDOE30 (91eae1ca); do not submit as new (IR-25-DUPLICATE-DOWNLOAD)."),
        note="WITHDRAWN duplicate (IR-25-DUPLICATE-DOWNLOAD); do not submit",
    )
    new_primary = dict(
        id="primary", role="primary", file=P, path=f"docs/downloads/{P}", bytes=(DL / P).stat().st_size,
        sha256=sha(DL / P), content_id=CID, positive_pixels=ck["positive_pixels"], format_ok=ck["format_ok"],
        checks=ck["checks"], receipt=receipt_path.name, outside="nan",
        status="UNIQUE FILE - NOT CLEARED: lane flag open, holdout gate not passed, do not spend a slot",
        title="New unique file: H31-C score-ordered dots at 2.4 px (3.5% budget)",
        summary=("Full-footprint emission of the H28 comparator configuration: raw-score ridge candidates, score-ordered dots "
                 "at 2.4 px, 3.5% budget, base BDE plus seven add-on columns (builder: scripts/build_candidate.py). "
                 "Format checks pass. On the spatial holdout it is at parity with its own same-run control and has not beaten the "
                 "comparable same-run holdout best; the tested alternative (A1, H31) was negative. The lane-overlap check is FLAGGED "
                 "against the dense 13GEMSDOE lattice - a density artefact under review, not cleared. Holdout-DTI 0.1497 "
                 "(95% CI 0.1331-0.1663). This is not a competition score and is not slot-approved."),
        expected_range="no competition estimate (holdout-DTI only: 0.1497, 95% CI 0.1331-0.1663)",
        note=NOTE, parent="H28 comparator arm (sapd2.4, kfrac 0.035, BDE+7), rebuilt full-footprint",
        transform="score-ordered dots (ridge NMS top-K, 2.4 px), 3-draw HGB average, catalogue pixels excluded",
        slot_approved=False, do_not_resubmit=False,
    )
    zero = dict(
        id="primary-zeros", role="fallback", file=Z, path=f"docs/downloads/{Z}", bytes=(DL / Z).stat().st_size,
        sha256=sha(DL / Z), content_id=CID, positive_pixels=new_primary["positive_pixels"], format_ok=True,
        checks={}, receipt=receipt_path.name, outside="zero",
        status="format fallback; unscored; not slot-approved", title="Format fallback: same H31-C dots, zeros outside the footprint",
        summary="Identical prediction values inside the template footprint; 0.0 instead of NaN outside. Format troubleshooting only.",
        expected_range="same as primary", note=NOTE_Z, parent="primary", transform="outside=zero",
        slot_approved=False, do_not_resubmit=False,
    )
    OLD_Z = "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif"
    old_z = dict(
        id="withdrawn-d28-zeros-duplicate", role="duplicate", file=OLD_Z, path=f"docs/downloads/{OLD_Z}",
        bytes=(DL / OLD_Z).stat().st_size, sha256=sha(DL / OLD_Z), content_id="e56ea318af89",
        positive_pixels=44090, format_ok=True, checks={}, receipt=None, outside="zero",
        status="DUPLICATE - zeros twin of the withdrawn D2.8 file; do not submit", title="Withdrawn zeros twin of the D2.8 duplicate",
        withdrawal="WITHDRAWN 2026-10-25 with its NaN twin (IR-25-DUPLICATE-DOWNLOAD).",
        note="WITHDRAWN duplicate (zeros twin); do not submit", slot_approved=False, do_not_resubmit=True,
    )
    others = [s for s in files if s is not old and s["role"] not in ("primary", "fallback", "duplicate")
              and s["id"] not in ("primary-zeros", "withdrawn-d28-zeros-duplicate")]
    subs["files"] = [new_primary, zero] + others + [old, old_z]
    (REG / "submissions.json").write_text(json.dumps(subs, indent=1) + "\n")
    print("primary:", new_primary["file"], new_primary["sha256"])
    print("fallback:", zero["file"], zero["sha256"])
    print("withdrawn:", old["file"])


if __name__ == "__main__":
    main()
