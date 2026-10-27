#!/usr/bin/env python3
"""Independent exact-file raster/ZIP audit; success is format-only, never slot approval.

The pinned owner-mirror template and labels are checked by SHA-256 and grid.
The TIFF must match their CRS/shape/transform, be single-band float32, contain
finite [0,1] values in the footprint and no positive catalogue pixels. A ZIP,
if present or required, must contain exactly the audited TIFF bytes. Organizer
acceptance, novelty and performance are separate questions.
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
from gems25.paths import data_dir  # noqa: E402

EXPECTED = dict(epsg=32611, shape=(3730, 3292),
                transform=(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
                footprint_pixels=5_167_373)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pins() -> dict[str, str]:
    rows = json.loads((ROOT / "registry/data_manifest.json").read_text())["files"]
    result = {}
    for name in ("sample_submission", "labels"):
        matches = [r.get("sha256") for r in rows if r.get("id") == name]
        if len(matches) != 1 or not isinstance(matches[0], str) or len(matches[0]) != 64:
            raise ValueError(f"missing or ambiguous {name} pin")
        result[name] = matches[0]
    return result


def audit(cand: Path, tmpl: Path, labels: Path, *, expected: dict, template_pin: str,
          labels_pin: str, require_zip: bool = False) -> dict:
    with rasterio.open(tmpl) as t:
        tarr, tcrs, ttr, tshape, tcount = t.read(1), t.crs, t.transform, t.shape, t.count
    foot = np.isfinite(tarr)
    with rasterio.open(labels) as lab_src:
        lab = lab_src.read(1) == 1
        lab_grid = (lab_src.shape, lab_src.crs, lab_src.transform, lab_src.count)
    with rasterio.open(cand) as src:
        arr = src.read(1)
        nd = src.nodata
        meta = dict(count=src.count, dtypes=list(src.dtypes), crs=str(src.crs),
                    epsg=src.crs.to_epsg() if src.crs else None, shape=list(src.shape),
                    transform=list(tuple(src.transform)[:6]),
                    nodata=("nan" if isinstance(nd, float) and nd != nd else nd))
    shape_match = tuple(meta["shape"]) == tuple(tshape)
    labels_match = lab_grid == (tshape, tcrs, ttr, 1)
    template_ok = (tcount == 1 and tcrs is not None and tcrs.to_epsg() == expected["epsg"]
                   and tshape == expected["shape"] and tuple(ttr)[:6] == expected["transform"])
    inside = arr[foot] if shape_match else np.array([], dtype=np.float32)
    outside = arr[~foot] if shape_match else np.array([], dtype=np.float32)
    inside_finite = bool(inside.size and np.isfinite(inside).all())
    outside_zero = bool(shape_match and np.all(outside == 0))
    outside_nan = bool(shape_match and outside.size and np.isnan(outside).all())
    checks = {
        "template_sha256_matches_pin": sha(tmpl) == template_pin,
        "labels_sha256_matches_pin": sha(labels) == labels_pin,
        "template_crs_shape_transform_matches_expected": bool(template_ok),
        "template_footprint_px_is_expected": int(foot.sum()) == expected["footprint_pixels"],
        "labels_grid_matches_template": bool(labels_match),
        "single_band": meta["count"] == 1,
        "dtype_float32": tuple(meta["dtypes"]) == ("float32",),
        "crs_epsg_matches_template": meta["epsg"] == expected["epsg"] and meta["crs"] == str(tcrs),
        "shape_equals_template": shape_match,
        "transform_equals_template": tuple(meta["transform"]) == tuple(ttr)[:6],
        "footprint_all_finite": inside_finite,
        "footprint_values_in_0_1": bool(inside_finite and inside.min() >= 0 and inside.max() <= 1),
        "outside_all_zero": outside_zero,
        "outside_all_nan": outside_nan,
        "strict_whole_array_0_le_x_le_1": bool(((arr >= 0) & (arr <= 1)).all()),
        "no_emission_on_catalogue": bool(shape_match and labels_match and not ((arr > 0) & lab & foot).any()),
    }
    outside_conv = "zeros" if outside_zero else ("nan" if outside_nan else "MIXED/INVALID")
    hard_keys = ("template_sha256_matches_pin", "labels_sha256_matches_pin",
                 "template_crs_shape_transform_matches_expected", "template_footprint_px_is_expected",
                 "labels_grid_matches_template", "single_band", "dtype_float32", "crs_epsg_matches_template",
                 "shape_equals_template", "transform_equals_template", "footprint_all_finite",
                 "footprint_values_in_0_1", "no_emission_on_catalogue")
    hard_ok = all(checks[k] for k in hard_keys) and outside_conv in ("zeros", "nan")
    if outside_conv == "zeros":
        hard_ok = hard_ok and checks["strict_whole_array_0_le_x_le_1"]
    zip_path = cand.with_suffix(".zip")
    zrec = None
    if zip_path.exists():
        try:
            with zipfile.ZipFile(zip_path) as z:
                names = z.namelist()
                ok = names == [cand.name] and z.read(cand.name) == cand.read_bytes()
            zrec = dict(file=zip_path.name, sha256=sha(zip_path), members=names,
                        contains_exactly_candidate_bytes=bool(ok))
        except (OSError, KeyError, RuntimeError, zipfile.BadZipFile) as exc:
            zrec = dict(file=zip_path.name, contains_exactly_candidate_bytes=False, error=str(exc))
        hard_ok = hard_ok and zrec["contains_exactly_candidate_bytes"]
    elif require_zip:
        zrec = dict(file=zip_path.name, contains_exactly_candidate_bytes=False, error="required ZIP missing")
        hard_ok = False
    return dict(file=cand.name, bytes=cand.stat().st_size, sha256=sha(cand), meta=meta,
                template_sha256=sha(tmpl), labels_sha256=sha(labels), footprint_px=int(foot.sum()),
                positive_pixels=int((inside > 0).sum()),
                distinct_values=[float(v) for v in np.unique(inside[np.isfinite(inside)])[:10]],
                outside_convention=outside_conv, checks=checks, all_hard_checks_pass=bool(hard_ok),
                zip=zrec, scope="local exact-file format and catalogue-mask checks only; no organizer or slot approval")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--require-zip", action="store_true")
    args = ap.parse_args()
    try:
        expected_pins = pins()
        rec = audit(args.candidate, data_dir() / "sample_submission.tif", data_dir() / "labels.tif",
                    expected=EXPECTED, template_pin=expected_pins["sample_submission"],
                    labels_pin=expected_pins["labels"], require_zip=args.require_zip)
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioError) as exc:
        rec = dict(file=str(args.candidate), all_hard_checks_pass=False,
                   scope="local format audit failed; no organizer or slot approval", error=str(exc))
    text = json.dumps(rec, indent=1, allow_nan=False) + "\n"
    print(text, end="")
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    return 0 if rec["all_hard_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
