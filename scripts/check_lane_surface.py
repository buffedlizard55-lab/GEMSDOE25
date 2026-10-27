#!/usr/bin/env python3
"""Fail-closed surface-stage rank audit before any full-footprint placement.

A clear result covers only the declared, locally restored registry and is not
approval to submit. A later independent final-dot audit is mandatory. Missing
hash-pinned references, missing/unaligned grids and undefined ranks stop the run.
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
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from gems25.paths import data_dir, work_dir  # noqa: E402
from scripts.check_lane_duplicates import (  # noqa: E402
    RHO_MAX,
    _read_aligned,
    declared_hashes,
    registry_inventory,
    registry_rasters,
    sha256,
    validate_template,
)


def surface_rank(values: np.ndarray, reference_values: np.ndarray) -> dict:
    a, b = np.asarray(values), np.asarray(reference_values)
    if a.ndim != 1 or a.shape != b.shape or not a.size:
        raise ValueError("rank inputs must be nonempty, aligned vectors")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("nonfinite value in rank input")
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return dict(spearman_surface=None, flag_rank=True, reason="undefined constant input")
    rho = float(spearmanr(a, b).statistic)
    if not np.isfinite(rho):
        return dict(spearman_surface=None, flag_rank=True, reason="undefined rank")
    return dict(spearman_surface=rho, flag_rank=abs(rho) > RHO_MAX,
                reason="duplicate" if abs(rho) > RHO_MAX else "clear")


def audit_surface(scores: np.ndarray, footprint: np.ndarray, profile: tuple, paths: list[Path],
                  expected: set[str], *, excluded: bool = False) -> dict:
    foot = np.asarray(footprint, dtype=bool)
    fi = np.flatnonzero(foot.ravel())
    scores = np.asarray(scores)
    if foot.ndim != 2 or scores.ndim != 1 or scores.size != fi.size or not fi.size:
        raise ValueError("surface must be one finite value per footprint pixel")
    if not np.isfinite(scores).all():
        raise ValueError("surface contains nonfinite values inside the footprint")
    # Use every footprint pixel; a sample is not an authorized clearance.
    inventory = registry_inventory(paths, expected)
    rows, errors = [], []
    for p in paths:
        try:
            ref = _read_aligned(p, profile, foot)
            row = surface_rank(scores, ref.ravel()[fi])
            row["file"] = p.name
            rows.append(row)
        except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
            errors.append(dict(file=p.name, error=str(exc)))
            break
        if row["flag_rank"]:
            break
    flagged = [r["file"] for r in rows if r["flag_rank"]]
    complete = bool(paths and inventory["complete"] and not excluded and not errors
                    and len(rows) == len(paths) and not flagged)
    return dict(rank_footprint_pixels=int(fi.size), rho_max=RHO_MAX, registry_inventory=inventory,
                registry_manifest_sha256=inventory["registry_manifest_sha256"],
                registry_checked=len(rows), registry_complete=complete, errors=errors,
                flagged=flagged, rows=rows, surface_clear=complete,
                verdict=("DUPLICATE OR UNDEFINED RANK - stop" if flagged
                         else "SURFACE CLEAR vs declared registry; final dots and other gates required" if complete
                         else "UNVERIFIED - incomplete or invalid registry; stop"),
                note="Full-footprint ranks can have ties; constant ranks cannot prove uniqueness. This does not check final dots.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scores", type=Path, help="one-dimensional footprint-vector .npy")
    ap.add_argument("--template", type=Path, default=data_dir() / "sample_submission.tif")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--exclude-stem", help="diagnostic only: exclusions make clearance impossible")
    args = ap.parse_args()
    try:
        template_sha = validate_template(args.template)
        foot = np.load(work_dir() / "bands" / "_footprint.npy")
        with rasterio.open(args.template) as t:
            if t.count != 1 or t.crs is None or not np.array_equal(foot, np.isfinite(t.read(1))):
                raise ValueError("cached footprint does not match the single-band template")
            profile = (t.shape, t.crs, t.transform)
        paths = registry_rasters()
        if args.exclude_stem:
            paths = [p for p in paths if args.exclude_stem not in p.stem]
        result = audit_surface(np.load(args.scores), foot, profile, paths, declared_hashes(),
                               excluded=args.exclude_stem is not None)
        result["scores"] = str(args.scores)
        result["scores_sha256"] = sha256(args.scores)
        result["template_sha256"] = template_sha
    except (OSError, ValueError, KeyError, json.JSONDecodeError, rasterio.errors.RasterioError) as exc:
        result = dict(scores=str(args.scores), surface_clear=False, verdict="UNVERIFIED - audit error; stop", error=str(exc))
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["surface_clear"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
