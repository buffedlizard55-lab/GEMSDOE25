#!/usr/bin/env python3
"""Extended lane check: candidate surface + dots vs every restored competition raster.

Groups (deduplicated by positive-mask content where noted in the output):
  external  = data/scored (11 pinned) + data/artifacts (ledger mirrors) + data/registry_top
              (top-scorer mirrors incl. the 9 focus-site winners)
  own       = docs/downloads/*.tif (this repo's earlier iterations; twins deduped by stem)

For each registry raster: Spearman of the candidate's *continuous* surface (pre-placement,
from ``--scores`` footprint-vector .npy) vs the registry raster's values, and Spearman of the
final binary rasters, both on a fixed 400k footprint sample (seed 0, as in
``scripts/check_lane_duplicates.py``); candidate dots within 3 px of registry dots and the
reverse. The dense 13GEMSDOE 5-px lattice is tagged `dense_lattice` and reported separately.

    .venv/bin/python scripts/lane_check_extended.py docs/downloads/<cand>-zeros.tif \
        --scores data/work/mscr_full_scores.npy --out evidence/mscr_lane_extended.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

LATTICE = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def groups(cand: Path):
    d = data_dir()
    ext = [("scored", p) for p in sorted((d / "scored").glob("*.tif"))]
    ext += [("artifacts", p) for p in sorted((d / "artifacts").glob("*.tif"))] if (d / "artifacts").exists() else []
    ext += [("registry_top", p) for p in sorted((d / "registry_top").glob("*.tif"))] if (d / "registry_top").exists() else []
    own = []
    seen = set()
    for p in sorted((ROOT / "docs" / "downloads").glob("*.tif")):
        stem = p.stem.replace("-zeros", "").replace("-nan", "")
        if p.resolve() == cand.resolve() or stem in seen or "mscr" in p.stem:
            seen.add(stem)
            continue
        seen.add(stem)
        own.append(("own_downloads", p))
    return ext, own


def load(p: Path, foot: np.ndarray):
    with rasterio.open(p) as s:
        if s.shape != foot.shape:
            return None
        return np.nan_to_num(s.read(1), nan=0.0)


def compare(cv, surf_samp, cand_dots, dist_to_cand, samp, group, p, foot):
    rv = load(p, foot)
    if rv is None:
        return dict(group=group, file=p.name, skipped="shape differs")
    rdots = (rv > 0) & foot
    rho_s = float(spearmanr(surf_samp, rv.ravel()[samp]).correlation)
    rho_b = float(spearmanr(cv.ravel()[samp], rv.ravel()[samp]).correlation)
    d_reg = distance_transform_edt(~rdots) if rdots.any() else np.full(cv.shape, np.inf)
    return dict(group=group, file=p.name,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                registry_dots=int(rdots.sum()),
                spearman_surface=round(rho_s, 6), spearman_final=round(rho_b, 6),
                cand_dots_within_3px=float((d_reg[cand_dots] <= 3.0).mean()) if cand_dots.any() else 0.0,
                reg_dots_within_3px_of_cand=float((dist_to_cand[rdots] <= 3.0).mean()) if rdots.any() else 0.0,
                dense_lattice=bool(p.name == LATTICE))


def summarise(rows):
    ok = [r for r in rows if "spearman_surface" in r]
    if not ok:
        return dict(n=0)
    ws = max(ok, key=lambda r: abs(r["spearman_surface"]))
    wf = max(ok, key=lambda r: abs(r["spearman_final"]))
    wo = max(ok, key=lambda r: r["cand_dots_within_3px"])
    return dict(n=len(ok),
                worst_abs_spearman_surface=abs(ws["spearman_surface"]), worst_surface_file=ws["file"],
                worst_abs_spearman_final=abs(wf["spearman_final"]), worst_final_file=wf["file"],
                worst_cand_dots_within_3px=wo["cand_dots_within_3px"], worst_overlap_file=wo["file"],
                lane_pass=bool(abs(ws["spearman_surface"]) <= 0.90 and abs(wf["spearman_final"]) <= 0.90
                               and wo["cand_dots_within_3px"] <= 0.70))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("--scores", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cand = Path(a.candidate)
    with rasterio.open(data_dir() / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    fi = np.flatnonzero(foot.ravel())
    with rasterio.open(cand) as s:
        cv = np.nan_to_num(s.read(1), nan=0.0)
    cand_dots = (cv > 0) & foot
    surf = np.zeros(foot.shape, np.float32)
    surf.ravel()[fi] = np.load(a.scores)
    samp = np.sort(np.random.default_rng(0).choice(fi, 400_000, replace=False))
    dist_to_cand = distance_transform_edt(~cand_dots)
    ext_paths, own_paths = groups(cand)
    rows = [compare(cv, surf.ravel()[samp], cand_dots, dist_to_cand, samp, g, p, foot) for g, p in ext_paths + own_paths]
    ext_rows = [r for r in rows if r["group"] != "own_downloads" and not r.get("dense_lattice")]
    lat_rows = [r for r in rows if r.get("dense_lattice")]
    own_rows = [r for r in rows if r["group"] == "own_downloads"]
    rec = dict(candidate=cand.name, sha256=hashlib.sha256(cand.read_bytes()).hexdigest(),
               candidate_dots=int(cand_dots.sum()), thresholds=dict(abs_spearman_max=0.90, dots_within_3px_max=0.70),
               external_sparse=summarise(ext_rows), lattice=lat_rows, own_lineage=summarise(own_rows),
               rows=rows)
    print(json.dumps({k: rec[k] for k in ("candidate", "candidate_dots", "external_sparse", "own_lineage")}, indent=1))
    for r in lat_rows:
        print("lattice:", json.dumps(r))
    if a.out:
        Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")


if __name__ == "__main__":
    main()
