#!/usr/bin/env python3
"""LANE check for GEM-1's surface and final dots vs all registry rasters.

Fails (duplicate -> stop) if Spearman(|surface| vs registry) > 0.90 or if
>70% of emitted dots fall within 3 px of one registry raster's dots.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25.experiment import load_context  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import dot_thin, ridge_nms, select_top_positive  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from validate_gem_candidate import surface_gem1, KFRAC, DOT_MIN_DIST, NMS_SIGMA  # noqa: E402

_DEFAULT_REGISTRY_DIR = ROOT / "data" / "scored"
REGISTRY_DIR = _DEFAULT_REGISTRY_DIR


def load_registry():
    import rasterio
    scored_dir = data_dir() / "scored" if REGISTRY_DIR == _DEFAULT_REGISTRY_DIR else REGISTRY_DIR
    out = []
    for p in sorted(scored_dir.glob("*.tif")):
        with rasterio.open(p) as s:
            out.append(dict(file=p.name, arr=np.nan_to_num(s.read(1), nan=0.0).astype(np.float32)))
    return out


def main() -> None:
    work = work_dir()
    ctx = load_context(work)
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    surface = surface_gem1(foot, work / "bands")
    registry = load_registry()
    print(f"GEM-1 surface vs {len(registry)} registry rasters:")
    worst_corr = 0.0
    for reg in registry:
        reg_flat = np.where(foot, reg["arr"], np.nan).ravel()[fi]
        s_flat = np.where(foot, surface, np.nan).ravel()[fi]
        finite = ~(np.isnan(s_flat) | np.isnan(reg_flat))
        corr = float(spearmanr(s_flat[finite], reg_flat[finite]).statistic) if finite.sum() >= 1000 else float("nan")
        worst_corr = max(worst_corr, abs(corr))
        print(f"  {reg['file']}: spearman {corr:+.4f}")
    print(f"worst |spearman| {worst_corr:.4f} (cap 0.90) -> {'OK' if worst_corr <= 0.90 else 'DUPLICATE'}")

    # dots: full-footprint emission of GEM-1
    H, W = foot.shape
    k = int(round(KFRAC * int(foot.sum())))
    # full-footprint domain (no quadrant restriction); known catalogue masked
    g = np.where(foot & np.isfinite(surface), surface, 0.0).astype(np.float32)
    r = ridge_nms(g, foot, NMS_SIGMA)
    sc = np.where(r & ~lab, g, 0.0)
    top = select_top_positive(sc, foot, k)
    dots = dot_thin(top, DOT_MIN_DIST)
    print(f"emitted dots: {int(dots.sum())}")

    worst_overlap = 0.0
    for reg in registry:
        reg_dots = np.flatnonzero((reg["arr"] > 0) & foot)
        my = np.flatnonzero(dots.ravel())
        overlap = 0.0
        if my.size and reg_dots.size:
            my_rc = np.column_stack([my // W, my % W])
            reg_rc = np.column_stack([reg_dots // W, reg_dots % W])
            dist = cKDTree(reg_rc).query(my_rc, k=1)[0]
            overlap = float((dist <= 3.0).mean())
        worst_overlap = max(worst_overlap, overlap)
        print(f"  dots vs {reg['file']}: overlap within 3px {overlap:.4f}")
    print(f"worst overlap {worst_overlap:.4f} (cap 0.70) -> {'OK' if worst_overlap <= 0.70 else 'DUPLICATE'}")
    ok = worst_corr <= 0.90 and worst_overlap <= 0.70
    print("LANE GEM-1:", "CLEAN" if ok else "DUPLICATE - STOP")
    Path("evidence/gem_validation").mkdir(parents=True, exist_ok=True)
    Path("evidence/gem_validation/lane_gem1.json").write_text(
        json.dumps({"worst_spearman_abs": worst_corr, "worst_overlap": worst_overlap, "lane_clean": ok}, indent=1) + "\n")


if __name__ == "__main__":
    main()
