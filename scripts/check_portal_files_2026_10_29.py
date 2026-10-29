#!/usr/bin/env python3
"""Re-read a fixed set of downloaded GeoTIFFs and record portal-relevant facts as JSON.

Read-only: no DrivenData access, no upload. Verifies: NaN count, finite min/max, positive-dot count,
[0,1] range over finite values, CRS EPSG, shape, dtype, nodata tag, and SHA-256 of the file bytes.
Usage: python scripts/check_portal_files_2026_10_29.py  (writes evidence/portal_file_recheck_2026-10-29.json)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / "docs" / "downloads"
OUT = ROOT / "evidence" / "portal_file_recheck_2026-10-29.json"
FILES = [
    "gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-nan.tif",
    "gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif",
    "gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed-nan.tif",
    "gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed-zeros.tif",
    "gems25-h36-spigm-subsurface-submod300-20261025-3937b96ce366-nan.tif",
    "gems25-h36-spigm-subsurface-submod300-20261025-3937b96ce366-zeros.tif",
]


def check(path: Path) -> dict:
    with rasterio.open(path) as ds:
        arr = ds.read(1)
        epsg = ds.crs.to_epsg() if ds.crs else None
        out = {
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "epsg": epsg,
            "shape": list(arr.shape),
            "dtype": ds.dtypes[0],
            "count": ds.count,
            "nodata_tag": ds.nodata,
            "nan_cells": int(np.isnan(arr).sum()) if arr.dtype.kind == "f" else 0,
        }
        fin = arr[np.isfinite(arr)]
        out["finite_min"] = float(fin.min())
        out["finite_max"] = float(fin.max())
        out["positive_cells"] = int((fin > 0).sum())
        out["all_finite_in_0_1"] = bool(out["nan_cells"] == 0 and ((fin >= 0) & (fin <= 1)).all())
        out["portal_range_pass"] = out["all_finite_in_0_1"]
        return out


def main() -> None:
    rows = [check(DL / f) for f in FILES]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"checked_utc_date": "2026-10-29", "files": rows}, indent=2) + "\n")
    for r in rows:
        print(r["file"][:60], "NaN=", r["nan_cells"], "portal_range_pass=", r["portal_range_pass"])


if __name__ == "__main__":
    main()
