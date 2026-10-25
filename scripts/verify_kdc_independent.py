#!/usr/bin/env python3
"""Independent re-verification of the shipped KDC files, sharing no code with scripts/build_kdc_submission.py.

Checks: B2 is a subset of the file; complement count and minimum distances; the NaN twin equals the zeros file inside the footprint;
the zip holds exactly the zeros TIF; and lane overlap is recomputed from scratch against every registry raster.
Output: evidence/kdc_build/independent_verification.json; exits 1 on any failure.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]


def read(p: Path) -> np.ndarray:
    with rasterio.open(p) as f:
        return f.read(1)


def main() -> None:
    subs = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
    prim = next(s for s in subs if s["role"] == "primary")
    fb = next(s for s in subs if s["role"] == "fallback")
    z = read(ROOT / prim["path"])
    n = read(ROOT / fb["path"])
    tmpl = read(ROOT / "data" / "sample_submission.tif")
    foot = np.isfinite(tmpl)
    lab = read(ROOT / "data" / "labels.tif") > 0
    pos = foot & (z > 0)
    b2 = read(ROOT / "data" / "registry_top" / "g32_h33-2-b2_0.2778.tif")
    b2 = np.isfinite(b2) & (b2 > 0)
    h19 = read(ROOT / "data" / "registry_top" / "g19_h19-5_0.1922.tif")
    h19 = np.isfinite(h19) & (h19 > 0)
    comp = pos & ~b2
    d_b2, d_h19, d_cat = (distance_transform_edt(~m) for m in (b2, h19, lab))
    res = {
        "zeros_finite_everywhere": bool(np.isfinite(z).all()),
        "zeros_values_binary_0_1": bool(np.isin(np.unique(z), [0.0, 1.0]).all()),
        "zeros_outside_footprint_all_zero": bool((z[~foot] == 0).all()),
        "nan_twin_equal_inside_footprint": bool(np.array_equal(z[foot], n[foot])),
        "nan_twin_nan_outside": bool(np.isnan(n[~foot]).all()),
        "b2_subset_of_file": bool((b2 & ~pos).sum() == 0),
        "b2_dots": int(b2.sum()), "file_dots": int(pos.sum()), "complement_dots": int(comp.sum()),
        "complement_min_dist_b2_px": float(d_b2[comp].min()), "complement_min_dist_h19_5_px": float(d_h19[comp].min()),
        "complement_min_dist_catalogue_px": float(d_cat[comp].min()),
        "dots_on_catalogue_pixels": int((pos & lab).sum()),
    }
    with zipfile.ZipFile(ROOT / "docs" / "downloads" / prim["zip"]) as zf:
        names = zf.namelist()
        res["zip_members"] = names
        res["zip_member_sha256_matches"] = len(names) == 1 and hashlib.sha256(zf.read(names[0])).hexdigest() == prim["sha256"]
    lane = []
    for p in sorted((ROOT / "data" / "registry_top").glob("*.tif")) + sorted((ROOT / "data" / "scored").glob("*.tif")):
        a = read(p)
        if a.shape != z.shape:
            continue
        rp = np.isfinite(a) & (a > 0)
        if not rp.any():
            continue
        ov = float((distance_transform_edt(~rp)[pos] <= 3).mean())
        same = hashlib.sha256(p.read_bytes()).hexdigest() in (prim["sha256"], fb["sha256"])
        lane.append({"file": p.name, "overlap_within_3px": round(ov, 4), "byte_identical": same})
    res["lane_recomputed"] = sorted(lane, key=lambda r: -r["overlap_within_3px"])[:8]
    worst = max((r for r in lane if "lattice" not in r["file"]), key=lambda r: r["overlap_within_3px"])
    res["worst_non_degenerate_overlap"] = worst
    ok = (res["zeros_finite_everywhere"] and res["zeros_values_binary_0_1"] and res["zeros_outside_footprint_all_zero"]
          and res["nan_twin_equal_inside_footprint"] and res["nan_twin_nan_outside"] and res["b2_subset_of_file"]
          and res["complement_dots"] == 17_720 and res["b2_dots"] == 37_654 and res["complement_min_dist_b2_px"] > 3
          and res["complement_min_dist_catalogue_px"] > 2 and res["dots_on_catalogue_pixels"] == 0
          and res["zip_member_sha256_matches"] and worst["overlap_within_3px"] <= 0.70
          and not any(r["byte_identical"] for r in lane))
    res["all_ok"] = bool(ok)
    out = ROOT / "evidence" / "kdc_build" / "independent_verification.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k != "lane_recomputed"}, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
