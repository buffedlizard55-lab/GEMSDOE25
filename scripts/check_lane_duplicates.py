#!/usr/bin/env python3
"""Lane / duplicate check for a candidate raster against every registry raster available in this repo.

PARALLEL-RUN PROTOCOL, items 1 and 5:
* duplicate if Spearman rank-correlation with any registry raster > 0.90;
* duplicate if more than 70 % of the candidate's dots lie within 3 px of one registry raster's dots;
* byte duplicate if SHA-256 matches any registry raster or any ledger entry.

Registry rasters = every restored file under data/scored, data/calibration, plus docs/downloads/*.tif and the SHA-256s
pinned in registry/artifact_ledger.json. Writes a JSON receipt when --out is given.

    python scripts/check_lane_duplicates.py docs/downloads/<candidate>.tif --out docs/downloads/lane-<candidate>.json
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

RHO_MAX, OVERLAP_MAX, OVERLAP_DIST = 0.90, 0.70, 3.0
SAMPLE = 400_000


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def registry_rasters() -> list[Path]:
    paths = []
    for sub in ("scored", "calibration"):
        paths += sorted((data_dir() / sub).glob("*.tif")) if (data_dir() / sub).exists() else []
    paths += sorted((ROOT / "docs" / "downloads").glob("*.tif"))
    return paths


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("--template", default=str(data_dir() / "sample_submission.tif"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cand = Path(a.candidate)
    cand_sha = sha256(cand)
    ledger = json.loads((ROOT / "registry" / "artifact_ledger.json").read_text())
    rows_ledger = ledger.get("artifacts", []) if isinstance(ledger, dict) else ledger
    ledger_sha = {row.get("sha256") for row in rows_ledger if isinstance(row, dict)}
    with rasterio.open(a.template) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(cand) as s:
        cv = np.nan_to_num(s.read(1), nan=0.0)
    cand_dots = (cv > 0) & foot
    rng = np.random.default_rng(0)
    fidx = np.flatnonzero(foot.ravel())
    samp = np.sort(rng.choice(fidx, min(SAMPLE, fidx.size), replace=False))
    cvals = cv.ravel()[samp]
    rows = []
    for p in registry_rasters():
        if p.resolve() == cand.resolve():
            continue
        if p.stem.replace("-zeros", "-nan") == cand.stem.replace("-zeros", "-nan"):
            continue  # same predictions, other outside-convention sibling (not an independent registry raster)
        with rasterio.open(p) as r:
            if r.shape != cv.shape:
                rows.append(dict(file=p.name, skipped="shape differs"))
                continue
            rv = np.nan_to_num(r.read(1), nan=0.0)
        rho = float(spearmanr(cvals, rv.ravel()[samp]).correlation)
        rdots = (rv > 0) & foot
        dist_to_reg = distance_transform_edt(~rdots) if rdots.any() else np.full(cv.shape, np.inf)
        ov = float((dist_to_reg[cand_dots] <= OVERLAP_DIST).mean()) if cand_dots.any() else 0.0
        dist_to_cand = distance_transform_edt(~cand_dots) if cand_dots.any() else np.full(cv.shape, np.inf)
        ov_rev = float((dist_to_cand[rdots] <= OVERLAP_DIST).mean()) if rdots.any() else 0.0
        # Density-aware companion (pre-registered knowledge/22 section 4): halo
        # coverage = footprint fraction within 3 px of the registry dots = the
        # overlap a uniformly random candidate would score. At coverage >= 0.70 the
        # literal candidate-side test cannot discriminate; the symmetric statistic
        # decides for those rasters. The literal flag is kept and always reported.
        coverage = float(((dist_to_reg <= OVERLAP_DIST) & foot).sum() / max(int(foot.sum()), 1)) if rdots.any() else 0.0
        dense_nondiscriminative = bool(coverage >= OVERLAP_MAX)
        sym_min = float(min(ov, ov_rev))
        lane_overlap_flag = bool(sym_min > OVERLAP_MAX) if dense_nondiscriminative else bool(ov > OVERLAP_MAX)
        rows.append(dict(file=p.name, sha256=sha256(p), byte_identical=sha256(p) == cand_sha,
                         spearman=round(rho, 6), dots_within_3px=round(ov, 6), registry_dots_within_3px_of_candidate=round(ov_rev, 6),
                         registry_dots=int(rdots.sum()),
                         flag_rank=bool(abs(rho) > RHO_MAX), flag_overlap=bool(ov > OVERLAP_MAX),
                         halo_coverage_3px=round(coverage, 6),
                         excess_overlap_over_coverage=round(ov - coverage, 6),
                         symmetric_min_overlap_3px=round(sym_min, 6),
                         non_discriminative_dense=dense_nondiscriminative,
                         flag_overlap_lane=lane_overlap_flag,
                         density_caveat=("registry raster halo covers >= 70% of the footprint; candidate-side overlap is not discriminative, symmetric statistic used"
                                         if dense_nondiscriminative else "")))
    flagged = [r for r in rows if r.get("flag_rank") or r.get("flag_overlap") or r.get("byte_identical")]
    flagged_lane = [r for r in rows if r.get("flag_rank") or r.get("flag_overlap_lane") or r.get("byte_identical")]
    in_ledger = cand_sha in ledger_sha
    registry_complete = bool(rows)
    rec = dict(candidate=cand.name, sha256=cand_sha, candidate_dots=int(cand_dots.sum()),
               thresholds=dict(spearman_max=RHO_MAX, dots_within_3px_max=OVERLAP_MAX, dist_px=OVERLAP_DIST),
               sha_in_artifact_ledger=in_ledger, registry_checked=len(rows), registry_complete=registry_complete,
               flagged=[r["file"] for r in flagged],
               flagged_literal=[r["file"] for r in flagged],
               flagged_lane=[r["file"] for r in flagged_lane],
               verdict=("UNVERIFIED - empty registry; fail closed" if not registry_complete
                        else ("DUPLICATE/LANE OVERLAP - do not package" if (flagged or in_ledger)
                              else "UNIQUE vs available registry")),
               verdict_density_aware=("UNVERIFIED - empty registry; fail closed" if not registry_complete
                                      else ("DUPLICATE/LANE OVERLAP (density-aware) - do not package" if (flagged_lane or in_ledger)
                                            else "UNIQUE vs available registry (density-aware; literal flags, if any, listed in flagged_literal)")),
               rows=rows,
               note=("Spearman is computed on a 400k random footprint sample of raw values; binary rasters have heavy "
                     "ties, so rho is a conservative rank summary, not a continuous rank correlation."))
    print(json.dumps({k: rec[k] for k in ("candidate", "sha256", "candidate_dots", "sha_in_artifact_ledger",
                                          "registry_checked", "flagged", "verdict", "flagged_lane",
                                          "verdict_density_aware")}, indent=1))
    for r in rows:
        if "spearman" in r:
            print(f"  {r['file'][:70]:70s} rho={r['spearman']:+.3f} within3px={r['dots_within_3px']:.3f} "
                  f"rev={r['registry_dots_within_3px_of_candidate']:.3f} identical={r['byte_identical']}")
    if a.out:
        Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")


if __name__ == "__main__":
    main()
