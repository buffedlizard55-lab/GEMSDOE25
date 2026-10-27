#!/usr/bin/env python3
"""Retired historical lane summary; it cannot establish a compliant clearance.

The old summary sampled ranks, excluded same-stem siblings and split dense
references from its ``lane_pass`` statistic. That statistic could be mistaken
for a literal pass. Use check_lane_surface.py before placement and
check_lane_duplicates.py on the final raster instead. Their outputs fail closed
on missing pins, invalid grids, undefined ranks and literal duplicates. The old
source and saved historical receipts remain in Git history.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402


def groups(candidate: Path):
    """Enumerate diagnostics without omitting same-stem or byte-identical twins."""
    d = data_dir()
    external = [(group, path) for group in ("scored", "calibration", "research", "artifacts", "registry_top")
                for path in sorted((d / group).glob("*.tif")) if path.resolve() != candidate.resolve()]
    own = [("own_downloads", path) for path in sorted((ROOT / "docs/downloads").glob("*.tif"))
           if path.resolve() != candidate.resolve()]
    return external, own


def main() -> int:
    print("Extended lane summary retired: use the full-footprint surface and final-dot checks; "
          "this command cannot authorize a candidate.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
