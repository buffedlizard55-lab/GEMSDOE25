#!/usr/bin/env python3
"""Retired H74 research-artifact publisher.

The archived H74 raster failed its preregistered literal final-dot lane gate.
The old publisher allowed a density-aware exception and could write a new
raster after that failure. This command is intentionally disabled; its previous
source remains available in Git history. A valid future experiment must use a
new preregistration and the shared fail-closed surface and final-dot checks.
"""
from __future__ import annotations

import sys


def main() -> int:
    print("H74 publisher retired: strict literal lane failed. DO NOT SUBMIT; no new raster written.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
