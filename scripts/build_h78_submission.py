#!/usr/bin/env python3
"""Retired H78 experiment builder.

The preserved H78 raster is format-valid but fails the repository's literal lane
rule: its saved lane receipt reports 100% of candidate dots within 3 px of the
r13 registry raster (the stop threshold is 70%). The former builder also emitted
a hard-coded leaderboard projection unsupported by an organizer receipt or a
traceable H78-specific holdout result. It is intentionally disabled; do not
rebuild, rename, or submit this lane.

See ``knowledge/39_h78_fail_closed_review_2026-10-27.md`` and the exact-file
receipts under ``docs/downloads/`` for the evidence and correction.
"""


def main() -> None:
    raise SystemExit(
        "H78 builder retired: strict lane duplicate (100% dot overlap with r13 within 3 px); "
        "no verified H78 HOLDOUT-DTI or calibrated score estimate; do not submit."
    )


if __name__ == "__main__":
    main()
