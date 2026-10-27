#!/usr/bin/env python3
"""Retired H78 artifact builder; intentionally fails closed.

H78's displayed leaderboard estimate was hard-coded, its exact raster fails the strict literal
registry lane rule, and its stored HOLDOUT-DTI record cannot be reproduced from saved cells in this
checkout. The historical implementation is retained in repository history; this entry point must
never recreate, relabel, or authorize the H78 TIFF.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "H78 is quarantined: its leaderboard estimate was hard-coded, its HOLDOUT-DTI evidence "
        "is not reproducible here, and its exact raster fails the strict registry lane gate. "
        "No H78 TIFF may be generated or submitted. See "
        "knowledge/39_current_review_2026-10-27.md."
    )


if __name__ == "__main__":
    main()
