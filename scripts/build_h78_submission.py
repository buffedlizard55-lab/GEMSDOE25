#!/usr/bin/env python3
"""Retired H78 publisher: the archived H78 raster failed the strict lane rule.

The original builder wrote a purported leaderboard estimate and holdout result
as constants and promoted a density-aware result over a literal lane failure.
The old source is preserved in Git history for study, not for candidate creation.
A new build must start from a preregistered hypothesis, the shared evaluator and
writer, and independent, fail-closed surface, final-dot and holdout gates.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "H78 publisher retired: its literal lane audit failed and its score/holdout "
        "claims were not supported by an experiment. DO NOT SUBMIT. "
        "See knowledge/38_h78_mhscf_and_phd_focus_sites_analysis_2026-10-27.md.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
