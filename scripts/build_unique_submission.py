#!/usr/bin/env python3
"""Retired lattice-gap publisher (PR #70); historical source remains in Git.

Excluding r13's halo does not imply exclusion of every other reference's halo.
The old builder selected arbitrary lattice gaps, read only the first radiometric
and LiDAR bands, silently packaged before a complete registry/canary/holdout
check, and labeled those locations geothermal anomalies without verification.
Do not reproduce that unsupported publication pathway.
"""
from __future__ import annotations

import sys


def main() -> int:
    print('Lattice-gap publisher retired: no valid hide-and-recover evidence or complete two-stage lane clearance. '
          'Historical aa0104874adb remains research only. DO NOT SUBMIT.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
