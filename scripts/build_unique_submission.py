#!/usr/bin/env python3
"""Retired lattice-gap publisher: the archived raster has no scientific gate.

The former builder assumed that avoiding the r13 lattice implied zero overlap
with every other registry raster. It created a TIFF before a documented
pre-placement surface audit, feature canaries, or a paired holdout comparison.
The original code and receipt are available in Git history for investigation,
not for publishing another candidate. See the current lattice-gap review.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "Lattice-gap publisher retired: unverified uniqueness, no canaries or "
        "paired holdout, and NaNs fail a strict whole-file range check. "
        "DO NOT SUBMIT. See knowledge/43_latticegap_review_2026-10-28.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
