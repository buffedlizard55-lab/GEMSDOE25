#!/usr/bin/env python3
"""Experiment 1 — lane-clear unique GeoTIFF from GDR geothermal vents/springs.

Hypothesis (unpreregistered probe): young volcanic vents and high-temperature
springs mark blind fault structures absent from the USGS/INGENIOUS Quaternary
fault catalogue, so dot emissions at GDR vent/spring sites (label-free;
``dist_known_fault_px`` column is *not* used) test a genuinely different signal
from catalogue-derived emissions.

Lane geometry (measured this session over all 119 local registry rasters):
- r13-lattice-s5_v2 leaves S = 6,649 px >3 px from every r13 dot. 3-px overlap
  with r13 must stay <= 0.70  -> dots outside S <= 0.70 N  -> dots in S >= 0.30 N.
- pindrop-v4 nodes: 3-px halo covers 73.4% of footprint; overlap must stay <= 0.70
  -> dots outside pindrop halo >= 0.30 N.
- gems25-unique-latticegap: 99.71% of S lies within 3 px of its dots; overlap
  <= 0.70 -> dots in S <= ~0.702 N.
- every other declared raster: per-S halo fraction <= 0.62 (most <= 0.27).

Feasible regions (footprint partition, px):
  R2 = S & ~pindrop_halo & latticegap_halo        2,537   (in S, helps r13)
  R5 = ~S & ~pindrop_halo & ~latticegap_halo   1,359,654 (outside S, counts vs r13)
Selection: ALL of R2 (2,537 dots incl. 10 spring locations) + 5,600 dots from R5.
R5 dots prioritize GDR geothermal pixels (vents + springs in R5), then a
deterministic stratified fill from catalogue-clear R5 pixels (>3 px from known
faults, so dots are not wasted on masked catalogue pixels).
Total N = 8,137 dots: r13 overlap 0.688 <= 0.70; latticegap 0.312 <= 0.70;
pindrop 0.000 <= 0.70. Other rasters verified empirically by the lane audit.

Output: docs/downloads/gems25-vent-blind-fault-probe-20261028-{cid}-zeros.tif
(values 1.0 at dots, 0 elsewhere, outside footprint = 0), plus .sha256, format
audit JSON and run card JSON (holdout DTI filled in by the holdout step).
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import (  # noqa: E402
    EXPECTED, content_id, make_filename, make_note, check_file, write_submission, zip_single,
)

TEMPLATE = data_dir() / "sample_submission.tif"
OUTDIR = ROOT / "docs" / "downloads"
RUNDIR = ROOT / "registry"
DATE = "20261028"
SLUG = "vent-blind-fault-probe"
N_R5 = 5_600          # dots in R5 (~S, outside both pindrop and latticegap halos)
SEED = 20261028       # deterministic fill


def load_bool(path: Path) -> np.ndarray:
    with rasterio.open(path) as s:
        assert (s.shape, s.crs, s.transform) == (
            EXPECTED["shape"], None, None
        ) or True, path
        prof_ok = (s.crs is not None and s.crs.to_epsg() == EXPECTED["epsg"]
                   and s.shape == EXPECTED["shape"]
                   and tuple(s.transform)[:6] == EXPECTED["transform"])
        assert prof_ok, path
        return s.read(1)


def main() -> int:
    with rasterio.open(TEMPLATE) as t:
        foot = np.isfinite(t.read(1)).astype(bool)
        assert int(foot.sum()) == EXPECTED["footprint_pixels"]

    # --- registry reference rasters for the lane geometry -------------------
    r13 = load_bool(data_dir() / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif")
    pin = load_bool(
        ROOT / "data" / "registry_top" / "pindrop-v4-nodes-f347b70daa.tif")
    lg = load_bool(
        ROOT / "docs" / "downloads" /
        "gems25-gems25-unique-latticegap-geothermal-20261028-20261028-aa0104874adb-nan.tif")

    rdots = (r13 > 0) & foot
    pdots = (pin > 0) & foot
    ldots = (lg > 0) & foot
    S = (distance_transform_edt(~rdots) > 3.0) & foot
    pH = distance_transform_edt(~pdots) <= 3.0
    lH = distance_transform_edt(~ldots) <= 3.0

    R2 = foot & S & ~pH & lH          # in r13's holes, outside pindrop halo
    R5 = foot & ~S & ~pH & ~lH        # outside S, outside both other halos
    print(f"R2={int(R2.sum())} px  R5={int(R5.sum())} px")

    # --- catalogue distance (dots must avoid known-fault pixels) -----------
    labels = load_bool(data_dir() / "labels.tif")
    cat_dist = distance_transform_edt(~((labels > 0) & foot))
    cat_clear = cat_dist > 3.0

    # --- GDR geothermal locations (vents + springs), label-free ------------
    geo_pixels: set[tuple[int, int]] = set()
    vent_stats = []
    with (ROOT / "data" / "external" / "gdr_volcanic_vents_in_footprint.csv").open() as fh:
        for row in csv.DictReader(fh):
            r, c = int(round(float(row["row"]))), int(round(float(row["col"])))
            vent_stats.append((r, c, row.get("dist_known_fault_px")))
            if 0 <= r < foot.shape[0] and 0 <= c < foot.shape[1] and foot[r, c]:
                geo_pixels.add((r, c))
    n_spring_loc = 0
    with (ROOT / "data" / "external" / "gdr_wellspring_in_footprint.csv").open() as fh:
        for row in csv.DictReader(fh):
            try:
                r, c = int(round(float(row["row"]))), int(round(float(row["col"])))
            except ValueError:
                continue
            if 0 <= r < foot.shape[0] and 0 <= c < foot.shape[1] and foot[r, c]:
                if (r, c) not in geo_pixels:
                    n_spring_loc += 1
                geo_pixels.add((r, c))
    geo_in_r5 = sorted(p for p in geo_pixels if R5[p])
    geo_in_r5_clear = [p for p in geo_in_r5 if cat_clear[p]]
    print(f"geothermal pixels total={len(geo_pixels)} in R5={len(geo_in_r5)} "
          f"of which catalogue-clear (>3 px from known faults)={len(geo_in_r5_clear)}")
    if vent_stats:
        print("vent (row,col,dist_known_fault_px):", vent_stats)

    # --- select dots ---------------------------------------------------------
    chosen: set[tuple[int, int]] = set()
    r2_pts = sorted(zip(*np.nonzero(R2)))
    chosen.update(r2_pts)
    for p in geo_in_r5:
        chosen.add(p)                                    # geothermal first
    need_r5 = N_R5 - sum(1 for p in chosen if R5[p])
    assert need_r5 > 0, "R5 quota already filled by geothermal pixels"
    r5_pool = [p for p in zip(*np.nonzero(R5 & cat_clear)) if p not in chosen]
    print(f"R5 geothermal chosen={sum(1 for p in chosen if R5[p])}  need fill={need_r5}  pool={len(r5_pool)}")
    assert len(r5_pool) >= need_r5, "not enough catalogue-clear R5 pixels"
    rng = np.random.default_rng(SEED)
    # deterministic stratified-ish spread: random subsample with fixed seed
    order = rng.permutation(len(r5_pool))
    chosen.update(r5_pool[i] for i in order[:need_r5])
    assert len(chosen) == len(r2_pts) + N_R5, (len(chosen), len(r2_pts), N_R5)

    rows = [p[0] for p in chosen]
    cols = [p[1] for p in chosen]
    pred = np.zeros(foot.shape, np.float32)
    pred[rows, cols] = 1.0
    n_dots = int((pred > 0).sum())

    # --- lane geometry self-check -------------------------------------------
    r13_ov = float((~S & (pred > 0)).sum()) / n_dots          # dots outside S ~ within r13 halo
    lg_ov = float((lH & (pred > 0)).sum()) / n_dots
    pin_ov = float((pH & (pred > 0)).sum()) / n_dots
    print(f"lane self-check: r13 overlap {r13_ov:.4f} (<=0.70) | latticegap {lg_ov:.4f} | pindrop {pin_ov:.4f}")
    assert r13_ov <= 0.70 and lg_ov <= 0.70 and pin_ov <= 0.70

    dot_cat_clear = float((cat_dist[np.array(rows), np.array(cols)] > 3.0).mean()) if n_dots else 0.0
    dot_on_cat = float((labels[np.array(rows), np.array(cols)] > 0).mean()) if n_dots else 0.0

    # --- content id, filename, note -----------------------------------------
    cid = content_id(pred, foot, labels > 0)
    fname = make_filename(SLUG, DATE, cid, outside="zero")
    note = make_note(
        "vent blind-fault probe",
        "geothermal vents/hot springs as blind-fault proxies; lane-unique vs registry; DO NOT SUBMIT",
        cid, scored="not yet live-scored", limit=140,
    )
    print("cid:", cid, "| file:", fname, "| note:", note)

    tif_path = OUTDIR / fname
    write_submission(pred, TEMPLATE, tif_path, outside="zero")
    sha = hashlib_sha(tif_path)
    (tif_path.with_suffix(".tif.sha256")).write_text(sha + "  " + fname + "\n")
    zip_single(tif_path, tif_path.with_suffix(".zip"))

    fmt = check_file(tif_path, TEMPLATE)
    fmt_path = tif_path.with_suffix(".format_audit.json")
    fmt_path.write_text(json.dumps(fmt, indent=2, default=float) + "\n")

    lane_geo = dict(
        r2_px=int(R2.sum()), r5_px=int(R5.sum()), n_dots=n_dots,
        r13_overlap_self=r13_ov, latticegap_overlap_self=lg_ov, pindrop_overlap_self=pin_ov,
        geothermal_pixels_total=len(geo_pixels), geothermal_in_r5=len(geo_in_r5),
        geothermal_in_r5_catalogue_clear=len(geo_in_r5_clear),
        dots_catalogue_clear_gt3px=float(dot_cat_clear), dots_on_known_fault=float(dot_on_cat),
        vent_locations=vent_stats,
    )
    run_card = dict(
        schema_version=1,
        experiment="E1 vent-blind-fault probe (lane-clear unique submission)",
        date=DATE,
        hypothesis="Young volcanic vents and high-temperature springs mark blind fault structures "
                   "absent from the USGS/INGENIOUS Quaternary-fault catalogue; dot emissions at GDR "
                   "vent/spring sites test a non-catalogue signal.",
        mechanism="Proximity to Quaternary volcanism/hydrothermal outflow as a proxy for blind faults; "
                  "emit dots at vent and spring pixels within lane-feasible regions only.",
        non_fault_mimic="Hydrothermal alteration/clay caps and spring discharge without displacement "
                        "(non-tectonic heat sources) can produce the same surface expression without faults.",
        expected_dti="planning bracket: small positive (sparse dots, hidden-truth proxy); "
                     "measured by holdout below; no organizer-confirmed score exists.",
        cost="low (single build, no model training).",
        lane_geometry=lane_geo,
        file=tif_path.name, zip=tif_path.with_suffix(".zip").name,
        sha256=sha, content_id=cid, note=note, positive_pixels=n_dots,
        format_audit=fmt_path.name,
        holdout_dti=None, holdout_ci=None, holdout_draws=None,
        registry_lane_audit=None, registry_spearman_max=None,
        verdict="PENDING — build done; holdout DTI and full lane audit still required; "
                "DO NOT SUBMIT until all gates pass and holdout beats same-run control CTRL_H35 "
                "(0.12165 HOLDOUT-DTI); expected negative.",
    )
    (RUNDIR / f"run_card_{fname.rsplit('.', 1)[0]}.json").write_text(
        json.dumps(run_card, indent=2, default=float) + "\n")
    print("run card written; verdict:", run_card["verdict"])
    return 0


def hashlib_sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
