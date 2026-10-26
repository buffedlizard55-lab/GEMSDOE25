#!/usr/bin/env python3
"""Surface-stage lane check (PARALLEL-RUN PROTOCOL item 1: check before placement AND on final dots).

Spearman rank correlation between a continuous footprint-vector score surface (``.npy``,
as saved by the candidate builders) and every registry raster, on the same 400k
footprint sample (seed 0) as ``scripts/check_lane_duplicates.py``. Dot-overlap is the
final-TIF checker's job; this script is the pre-placement surface half.

    .venv/bin/python scripts/check_lane_surface.py data/work/h35_full_scores.npy --out evidence/h35_lane_surface.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir, work_dir  # noqa: E402

SAMPLE = 400_000
RHO_MAX = 0.90


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scores", help="footprint-vector .npy of continuous scores")
    ap.add_argument("--out", default=None)
    ap.add_argument("--exclude-stem", default=None, help="skip registry TIFs whose stem contains this (the candidate itself)")
    a = ap.parse_args()
    work = work_dir()
    foot = np.load(work / "bands" / "_footprint.npy")
    fi = np.flatnonzero(foot.ravel())
    scores = np.load(a.scores)
    if scores.size != fi.size:
        raise SystemExit(f"scores size {scores.size} != footprint {fi.size}")
    rng = np.random.default_rng(0)
    samp_vec = np.sort(rng.choice(fi.size, min(SAMPLE, fi.size), replace=False))
    samp_flat = fi[samp_vec]
    svals = np.asarray(scores, dtype=np.float64)[samp_vec]
    import hashlib

    raw_paths = []
    for d in (
        data_dir() / "scored",
        data_dir() / "calibration",
        data_dir() / "research",
        data_dir() / "artifacts",
        data_dir() / "registry_top",
        ROOT / "docs" / "downloads",
    ):
        if d.exists():
            raw_paths.extend(sorted(d.glob("*.tif")))
    paths = []
    seen_sha = set()
    for p in raw_paths:
        if a.exclude_stem and a.exclude_stem in p.stem:
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest in seen_sha:
            continue
        seen_sha.add(digest)
        paths.append(p)
    rows = []
    for p in paths:
        with rasterio.open(p) as r:
            if r.shape != foot.shape:
                rows.append(dict(file=p.name, spearman_surface=None, flag_rank=True, skipped="shape differs"))
                continue
            rv = np.nan_to_num(r.read(1), nan=0.0).ravel()[samp_flat]
        finite = np.isfinite(svals) & np.isfinite(rv)
        if finite.sum() >= 1000 and svals[finite].min() != svals[finite].max() and rv[finite].min() != rv[finite].max():
            rho = float(spearmanr(svals[finite], rv[finite]).statistic)
        else:
            rho = float("nan")
        flag = bool(not np.isfinite(rho) or abs(rho) > RHO_MAX)
        rows.append(dict(file=p.name, spearman_surface=round(rho, 6) if np.isfinite(rho) else None, flag_rank=flag))
        print(f"{p.name[:70]:70s} rho={rho:+.4f}" if np.isfinite(rho) else f"{p.name[:70]:70s} rho=nan (FLAGGED)")
    worst = max((abs(r["spearman_surface"]) for r in rows if r["spearman_surface"] is not None), default=float("nan"))
    rec = dict(scores=str(a.scores), sample=int(samp_vec.size), rho_max=RHO_MAX,
               worst_abs_spearman=worst, flagged=[r["file"] for r in rows if r["flag_rank"]], rows=rows,
               note="Registry rasters are binary/near-binary, so Spearman has heavy ties; this is the protocol's rank screen, not a Pearson correlation.")
    print(json.dumps({k: rec[k] for k in ("worst_abs_spearman", "flagged")}, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")


if __name__ == "__main__":
    main()
