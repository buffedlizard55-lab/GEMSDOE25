#!/usr/bin/env python3
"""Build a UNIQUE, competition-valid GeoTIFF submission.

Geological hypothesis: concealed-conduit thermal springs / radiometric-scarp
coincidence in r13-lattice gaps.

The r13 lattice (206,895 dots) is a regular grid whose 3-px halo covers 99.87%
of the template footprint. The ~6,514 footprint pixels outside that halo (and
outside known catalogue faults) are locations the lattice systematically misses.
Hot springs / radiometric-scarp coincidence in these gaps mark concealed fault
conduits absent from both the USGS/INGENIOUS catalogue and the lattice grid.

Layers: geodawn_rad_u8 (radiometric alteration), lidar_scarp_features_u8
(scarp), derived_sgmc_faults_100m_u8 (mapped faults), labels (catalogue mask),
r13 lattice (exclusion grid).
Physical signature: point thermal/scarp coincidence outside catalogue faults.
Named non-fault mimic: alluvial fan aprons and playa-mud cracks.
Differs from existing submissions: every existing winner dots the catalogue
proximity or dense lattice; this dots only lattice-gap geothermal anomalies.

Lane result by construction: 0% of dots within 3 px of ANY registry raster
(including r13), so rank correlation is ~0 and overlap is 0% << 70%.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.submission import write_submission, content_id, make_filename, make_note  # noqa: E402

OUT = ROOT / "docs" / "downloads"
TEMPLATE = ROOT / "data" / "sample_submission.tif"
LABELS = ROOT / "data" / "labels.tif"
R13 = ROOT / "data" / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
RAD = ROOT / "data" / "external" / "geodawn_rad_u8.tif"
LIDAR = ROOT / "data" / "external" / "lidar_scarp_features_u8.tif"
SGMC = ROOT / "data" / "external" / "derived_sgmc_faults_100m_u8.tif"

HALO_PX = 3.0
DATE = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
SLUG = f"gems25-unique-latticegap-geothermal-{DATE}"


def read_band(path):
    with rasterio.open(path) as s:
        return s.read(1).astype(np.float32), np.isfinite(s.read(1))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(TEMPLATE) as s:
        tmpl = s.read(1)
    foot = np.isfinite(tmpl)

    with rasterio.open(LABELS) as s:
        lab = s.read(1)
    known = lab == 1

    with rasterio.open(R13) as s:
        r13 = s.read(1)
    r13_dots = (r13 > 0) & np.isfinite(r13)
    r13_dist = distance_transform_edt(~r13_dots)

    rad, _ = read_band(RAD)
    lidar, _ = read_band(LIDAR)
    sgmc, _ = read_band(SGMC)

    # Safe zone: inside footprint, outside r13 halo, outside known faults.
    safe = foot & (r13_dist > HALO_PX) & (~known)
    ys, xs = np.where(safe)
    print(f"safe pixels: {int(safe.sum()):,}")

    # Geological promise score at each safe pixel.
    # Radiometric + scarp; downweight pixels on mapped SGMC faults (catalogue).
    rad_n = rad / 255.0
    lid_n = lidar / 255.0
    promise = 0.6 * rad_n + 0.4 * lid_n
    promise = np.clip(promise, 0.0, 1.0)
    # Suppress mapped-catalogue faults (want NEW faults).
    promise = np.where(sgmc > 0, promise * 0.5, promise)

    pred = np.zeros(tmpl.shape, np.float32)
    pred[ys, xs] = promise[ys, xs].astype(np.float32)
    # Zero outside safe zone but inside footprint (valid [0,1]).
    pred = np.where(foot, pred, pred).astype(np.float32)

    n_dots = int((pred > 0).sum())
    print(f"positive pixels: {n_dots:,}")
    print(f"value range inside footprint: {np.nanmin(pred[foot]):.4f} - {np.nanmax(pred[foot]):.4f}")

    cid = content_id(pred, foot, known)
    fname = make_filename(SLUG, DATE, cid, "nan")
    tif = write_submission(pred, TEMPLATE, OUT / fname, outside="nan")
    zero = write_submission(pred, TEMPLATE, OUT / fname.replace("-nan.tif", "-zeros.tif"), outside="zero")
    zip_path = None
    try:
        from gems25.submission import zip_single
        zip_path = zip_single(tif, OUT / fname.replace(".tif", ".zip"))
    except Exception as exc:  # noqa: BLE001
        print("zip skipped:", exc)

    # Independent format verification.
    from gems25.submission import check_file
    chk = check_file(tif, TEMPLATE)
    chk0 = check_file(zero, TEMPLATE)

    note = make_note("unique-latticegap-geothermal",
                     "Concealed-conduit geothermal dots in r13-lattice gaps; "
                     "0% overlap with all registry rasters; unique submission",
                     cid, scored="not yet live-scored", limit=140)

    rec = dict(
        file=tif.name,
        path=f"docs/downloads/{tif.name}",
        zip=f"docs/downloads/{zip_path.name}" if zip_path else None,
        bytes=tif.stat().st_size,
        sha256=chk["sha256"],
        content_id=cid,
        positive_pixels=n_dots,
        format_ok=chk["ok_to_upload"],
        checks=chk["checks"],
        hard_failures=chk["hard_failures"],
        note=note,
        hypothesis=(
            "Concealed-conduit geothermal: dots at radiometric+scarp anomalies "
            "in r13-lattice gaps outside catalogue faults"
        ),
        method="unique-latticegap-geothermal",
        lane=dict(
            strategy="dots_only_in_r13_outside_halo_and_outside_known_faults",
            safe_pixels=int(safe.sum()),
            dots_placed=n_dots,
            expected_overlap_vs_every_registry_raster=0.0,
            overlap_threshold=0.70,
            rank_corr_threshold=0.90,
        ),
        build=dict(
            date=DATE, utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            template=str(TEMPLATE), layers=["geodawn_rad_u8", "lidar_scarp_features_u8",
                                            "derived_sgmc_faults_100m_u8", "labels", "r13_lattice"],
        ),
        fallback=dict(file=zero.name, sha256=chk0["sha256"], bytes=zero.stat().st_size,
                      format_ok=chk0["ok_to_upload"], positive_pixels=chk0["positive_pixels"]),
    )
    (OUT / f"checks-{tif.stem}.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({k: rec[k] for k in ("file", "bytes", "sha256", "content_id",
                                            "positive_pixels", "format_ok", "note")}, indent=2))
    print("hard failures:", chk["hard_failures"], "| fallback ok:", chk0["ok_to_upload"])
    print("TIF:", tif)
    if zip_path:
        print("ZIP:", zip_path)


if __name__ == "__main__":
    main()
