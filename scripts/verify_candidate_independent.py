#!/usr/bin/env python3
"""Independent exact-file audit of a candidate GeoTIFF (plain rasterio; no gems25 writer code).

Checks, against the pinned owner-mirror template (``data/sample_submission.tif``):
single band, float32, CRS EPSG:32611 equal to template, shape/transform equal to template,
footprint (finite-template pixels = 5,167,373) all finite and within [0, 1], outside
convention (all-zero XOR all-NaN), the strict whole-array ``0 <= x <= 1`` test, distinct
value set, positive-pixel count, zero emitted pixels on the catalogue, SHA-256, and — when a
sibling ``.zip`` exists — that it contains exactly this one TIF byte-for-byte.

    .venv/bin/python scripts/verify_candidate_independent.py docs/downloads/<file>-zeros.tif
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402  (path resolution only, not writer/checker logic)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cand = Path(a.candidate)
    tmpl, labels = data_dir() / "sample_submission.tif", data_dir() / "labels.tif"
    with rasterio.open(tmpl) as t:
        tarr, tcrs, ttr, tshape = t.read(1), t.crs, t.transform, t.shape
    foot = np.isfinite(tarr)
    with rasterio.open(labels) as s:
        lab = s.read(1) == 1
    with rasterio.open(cand) as s:
        arr = s.read(1)
        nd = s.nodata
        meta = dict(count=s.count, dtypes=list(s.dtypes), crs=str(s.crs), epsg=s.crs.to_epsg() if s.crs else None,
                    shape=list(s.shape), transform=list(tuple(s.transform)[:6]),
                    nodata=("nan" if isinstance(nd, float) and nd != nd else nd))
    inside, outside = arr[foot], arr[~foot]
    checks = {
        "template_footprint_px_is_5167373": int(foot.sum()) == 5_167_373,
        "single_band": meta["count"] == 1,
        "dtype_float32": tuple(meta["dtypes"]) == ("float32",),
        "crs_epsg_32611_and_equals_template": meta["epsg"] == 32611 and meta["crs"] == str(tcrs),
        "shape_equals_template": tuple(meta["shape"]) == tuple(tshape),
        "transform_equals_template": tuple(meta["transform"]) == tuple(ttr)[:6],
        "transform_is_100m_243350_4508550": tuple(meta["transform"]) == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
        "footprint_all_finite": bool(np.isfinite(inside).all()),
        "footprint_values_in_0_1": bool(inside.min() >= 0.0 and inside.max() <= 1.0),
        "outside_all_zero": bool((outside == 0).all()),
        "outside_all_nan": bool(np.isnan(outside).all()),
        "strict_whole_array_0_le_x_le_1": bool(((arr >= 0) & (arr <= 1)).all()),
        "no_emission_on_catalogue": int(((arr > 0) & lab & foot).sum()) == 0,
    }
    outside_conv = "zeros" if checks["outside_all_zero"] else ("nan" if checks["outside_all_nan"] else "MIXED/INVALID")
    hard_ok = all(checks[k] for k in (
        "template_footprint_px_is_5167373", "single_band", "dtype_float32",
        "crs_epsg_32611_and_equals_template", "shape_equals_template", "transform_equals_template",
        "transform_is_100m_243350_4508550", "footprint_all_finite", "footprint_values_in_0_1",
        "no_emission_on_catalogue")) and outside_conv in ("zeros", "nan")
    if outside_conv == "zeros":
        hard_ok = hard_ok and checks["strict_whole_array_0_le_x_le_1"]  # zeros file must pass the strictest portal-style test
    zrec = None
    zp = cand.with_suffix(".zip")
    if zp.exists():
        with zipfile.ZipFile(zp) as z:
            names = z.namelist()
            ok = names == [cand.name] and z.read(cand.name) == cand.read_bytes()
        zrec = dict(file=zp.name, sha256=sha(zp), members=names, contains_exactly_candidate_bytes=bool(ok))
    rec = dict(file=cand.name, bytes=cand.stat().st_size, sha256=sha(cand), meta=meta,
               footprint_px=int(foot.sum()), positive_pixels=int((inside > 0).sum()),
               distinct_values=[float(v) for v in np.unique(inside)[:10]],
               outside_convention=outside_conv, checks=checks, all_hard_checks_pass=bool(hard_ok), zip=zrec)
    print(json.dumps(rec, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    if not hard_ok:
        raise SystemExit("INDEPENDENT AUDIT FAILED")


if __name__ == "__main__":
    main()
