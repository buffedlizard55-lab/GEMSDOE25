#!/usr/bin/env python3
"""Prepare the competition data: build the static feature arrays from the restored rasters.

This script is the second step after running `bash scripts/download_competition_data.sh`.
It converts the restored GeoTIFF rasters into fast numpy arrays for the feature pipeline.

    bash scripts/download_competition_data.sh  # Step 1: restore data/
    python scripts/prepare_data.py            # Step 2: build work/ arrays

After this, the full train→inference→validate pipeline is ready to run.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.prepare import prepare_inputs  # noqa: E402


def main() -> None:
    d, w = data_dir(), work_dir()
    w.mkdir(parents=True, exist_ok=True)
    
    t0 = time.time()
    print("Preparing inputs from restored data...")
    stats = prepare_inputs(d, w)
    print(f"Prepared: {stats}")
    print(f"Done in {time.time() - t0:.1f}s")
    print("\nNext steps:")
    print("  python scripts/build_features.py")
    print("  python scripts/build_addons.py")


if __name__ == "__main__":
    main()
