#!/usr/bin/env python3
"""Inventory every restored submission raster: dot sets, portal format, pairwise overlap (COMPUTED).

Dots = pixels with value > 0 inside the template footprint (a binary raster is assumed; the script records
any non-binary values). Overlap metrics:
  * jaccard            |A & B| / |A | B| on dot pixels
  * within3_of_B_pct   share of A's dots within 3 px (Chebyshev-free Euclidean, EDT) of any B dot  (lane protocol metric)
Catalogue distance: share of dots within 200 m (2 px) of a labelled catalogue pixel.

    python scripts/inventory_submissions.py --out evidence/submission_inventory_2026-10-31.json
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

SKIP = {"training_features.tif", "derived_sgmc_faults_100m_u8.tif", "geodawn_extensions_u8.tif",
        "geodawn_rad_u8.tif", "lidar_scarp_features_u8.tif"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_dots(path: Path, foot: np.ndarray):
    with rasterio.open(path) as s:
        a = s.read(1)
        nodata = s.nodata
    inside = a[foot]
    outside = a[~foot]
    fin = np.isfinite(inside)
    vals = np.unique(inside[fin])
    dots = np.zeros(foot.shape, bool)
    dots[foot] = np.where(fin, inside, 0) > 0
    fmt = dict(
        nan_inside=int((~fin).sum()),
        outside=("nan" if np.isnan(outside).all() else "zero" if (outside == 0).all() else "mixed"),
        values_inside=[float(v) for v in vals[:6]],
        binary=bool(np.isin(vals, (0, 1)).all()),
        nodata=("nan" if isinstance(nodata, float) and nodata != nodata else nodata),
    )
    fmt["portal_pass_hypothesis"] = bool(fmt["nan_inside"] == 0 and fmt["outside"] == "zero" and
                                         (np.nanmin(inside) >= 0) and (np.nanmax(inside) <= 1))
    return dots, fmt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    d = data_dir()
    with rasterio.open(d / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(d / "labels.tif") as t:
        cat = (t.read(1) == 1) & foot
    dt_cat = distance_transform_edt(~cat)
    files = sorted(p for p in glob.glob(str(d / "**" / "*.tif"), recursive=True) if Path(p).name not in SKIP)
    recs, dots_by = [], {}
    for p in files:
        p = Path(p)
        if p.name in ("labels.tif", "existing_faults.tif", "sample_submission.tif"):
            continue
        dots, fmt = load_dots(p, foot)
        n = int(dots.sum())
        if n == 0:
            continue
        dots_by[p.name] = dots
        recs.append(dict(file=p.name, sha256=sha256(p), dots=n, format=fmt,
                         within_200m_of_catalogue_pct=round(100 * float((dt_cat[dots] <= 2.0).mean()), 2)))
    names = list(dots_by)
    edt = {k: distance_transform_edt(~v) for k, v in dots_by.items()}
    pairs = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            A, B = dots_by[a], dots_by[b]
            inter = int((A & B).sum())
            union = int((A | B).sum())
            jac = inter / union
            w3_ab = float((edt[b][A] <= 3.0).mean())
            w3_ba = float((edt[a][B] <= 3.0).mean())
            if jac > 0.2 or max(w3_ab, w3_ba) > 0.5:
                pairs.append(dict(a=a, b=b, jaccard=round(jac, 4), a_within3_of_b_pct=round(100 * w3_ab, 2),
                                  b_within3_of_a_pct=round(100 * w3_ba, 2)))
    out = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/inventory_submissions.py",
        evidence_class="COMPUTED (restored owner-mirror / registry rasters; pins in registry/data_manifest.json)",
        template_footprint_px=int(foot.sum()),
        catalogue_px=int(cat.sum()),
        n_files=len(recs),
        files=recs,
        pairs_jaccard_gt_0_2_or_within3_gt_50pct=pairs,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1) + "\n")
    print(f"files={len(recs)} pairs_flagged={len(pairs)} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
