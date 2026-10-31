#!/usr/bin/env python3
"""Build the registry 3-px halo cache (packed bits) used by the lane-clean construction and E5.

For every registry raster with dots on the template grid, store the packed footprint-vector halo
(dist <= 3 px to any of its dots) and the count of dots. Cache lives in the work directory (never committed).
Also writes the per-pixel coverage count (all rasters) for diagnostics.

    python scripts/build_registry_halo_cache.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import check_lane_duplicates as lane  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402


def main() -> int:
    with rasterio.open(data_dir() / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    names, sizes, packed = [], [], []
    for p in lane.registry_rasters():
        try:
            with rasterio.open(p) as s:
                if s.shape != foot.shape:
                    continue
                a = s.read(1)
        except Exception:
            continue
        d = (np.nan_to_num(a, nan=0) > 0) & foot
        if d.sum() == 0:
            continue
        h = distance_transform_edt(~d) <= 3.0
        names.append(p.name)
        sizes.append(int(d.sum()))
        packed.append(np.packbits((h & foot)[foot]))
    out = work_dir() / "registry_halos.npz"
    np.savez(out, names=np.array(names), sizes=np.array(sizes), packed=np.stack(packed))
    meta = dict(n_rasters=len(names), footprint_px=int(foot.sum()), file=str(out))
    print(json.dumps(meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
