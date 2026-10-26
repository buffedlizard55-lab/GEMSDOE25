#!/usr/bin/env python3
"""Record a score *the owner read on the DrivenData submissions page* (never automated; Terms of Use).

    python scripts/record_live_score.py --file <file-name | sha256-prefix | content-id> --score 0.2xxx [--note "..."]

Records an OWNER-REPORTED claim in registry/submissions.json and registry/live_scores.json,
without changing any submission status, lane verdict, approval, or signed historical note.
A score claim is not an organizer receipt or permission to resubmit. Re-run ``python scripts/build_site.py``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--score", type=float, required=True)
    ap.add_argument("--note", default="")
    a = ap.parse_args()
    if not 0.0 <= a.score <= 1.0:
        raise SystemExit("score must be in [0, 1]")
    sp, lp = ROOT / "registry" / "submissions.json", ROOT / "registry" / "live_scores.json"
    subs, ls = json.loads(sp.read_text()), json.loads(lp.read_text())
    hits = [s for s in subs["files"] if a.file in (s["file"], s["content_id"]) or s["sha256"].startswith(a.file)]
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} matches for {a.file!r}; give the exact file name, content id or a longer sha256 prefix")
    s = hits[0]
    # Never replace a DO NOT SUBMIT status with a green 'scored' badge.
    # A reported result does not waive a failed lane or performance gate.
    s["score_evidence_class"] = "OWNER-REPORTED; no organizer receipt supplied"
    s["owner_reported_score"] = a.score
    s["score_recorded_utc"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ls["artifacts"].append(dict(project="GEMSDOE25", label=s["file"], score=a.score, status="owner-reported", note=a.note))
    sp.write_text(json.dumps(subs, indent=1) + "\n")
    lp.write_text(json.dumps(ls, indent=1) + "\n")
    print(f"recorded {a.score:.4f} for {s['file']}")


if __name__ == "__main__":
    main()
