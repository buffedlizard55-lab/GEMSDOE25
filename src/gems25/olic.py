"""OLIC: catalogue-free multi-scale oriented line-continuity features (knowledge/29).

For each edge channel, line means along 4 strike directions at half-lengths 5 and 10 px;
features are the max-direction line mean at each scale and the directional anisotropy.
No labels or catalogue geometry are inputs.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

OLIC_CHANNELS = ("L_step_max", "A_mag_hg_ridge", "D_ThK_edge")
OLIC_NAMES = [f"OLIC_{c}_{s}" for c in OLIC_CHANNELS for s in ("L11", "L21", "ANISO")]
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))
HALF_LENGTHS = (5, 10)


def _shifted(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """a[y+dy, x+dx] with zero padding (never wraps)."""
    h, w = a.shape
    out = np.zeros_like(a)
    y0, y1, x0, x1 = max(0, -dy), min(h, h - dy), max(0, -dx), min(w, w - dx)
    if y1 > y0 and x1 > x0:
        out[y0:y1, x0:x1] = a[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
    return out


def line_means(grid: np.ndarray, half: int) -> np.ndarray:
    """(4, H, W) mean of `grid` along each direction over t in [-half, half]."""
    acc = []
    for dy, dx in DIRECTIONS:
        s = np.zeros_like(grid)
        for t in range(-half, half + 1):
            s += _shifted(grid, t * dy, t * dx)
        acc.append(s / (2 * half + 1))
    return np.stack(acc)


def compute_olic_grids(channels: list[np.ndarray], footprint: np.ndarray) -> list[np.ndarray]:
    """9 finite [0,1] grids: per channel [max-dir L11, max-dir L21, anisotropy L11]."""
    foot = np.asarray(footprint, bool)
    out: list[np.ndarray] = []
    for grid in channels:
        g = np.where(foot, np.asarray(grid, np.float32), 0.0)
        l5 = line_means(g, HALF_LENGTHS[0])
        l10 = line_means(g, HALF_LENGTHS[1])
        feats = (l5.max(axis=0), l10.max(axis=0), l5.max(axis=0) - l5.mean(axis=0))
        for f in feats:
            f = np.where(footprint, np.clip(f, 0.0, 1.0), 0.0).astype(np.float32)
            if not np.isfinite(f[foot]).all():
                raise ValueError("OLIC feature non-finite inside footprint")
            out.append(f)
    return out


def _scale01(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    v = np.asarray(values, np.float32)
    sel = footprint & np.isfinite(v)
    lo, hi = np.percentile(v[sel], [1, 99])
    if hi <= lo:
        return np.where(footprint, 0.0, 0.0).astype(np.float32)
    return np.nan_to_num(np.where(footprint, np.clip((v - lo) / (hi - lo), 0, 1), 0.0), nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)


def build_olic_sidecar(static, static_names, footprint, footprint_idx, out_path) -> list[str]:
    missing = [n for n in OLIC_CHANNELS if n not in static_names]
    if missing:
        raise ValueError(f"OLIC missing cached inputs: {missing}")
    foot = np.asarray(footprint, bool)
    fi = np.asarray(footprint_idx, np.int64)
    channels = []
    for n in OLIC_CHANNELS:
        grid = np.zeros(foot.shape, np.float32)
        grid.ravel()[fi] = np.asarray(static[static_names.index(n)], np.float32)
        channels.append(_scale01(grid, foot))
    arrays = compute_olic_grids(channels, foot)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(len(OLIC_NAMES), fi.size))
    for i, a in enumerate(arrays):
        mm[i] = a.ravel()[fi]
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(OLIC_NAMES) + "\n")
    return list(OLIC_NAMES)


def load_olic_sidecar(work, static, static_names, footprint, footprint_idx) -> np.ndarray:
    path = Path(work) / "olic_columns.npy"
    if not path.exists():
        build_olic_sidecar(static, static_names, footprint, footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != OLIC_NAMES or arr.shape != (len(OLIC_NAMES), len(footprint_idx)):
        raise ValueError(f"OLIC sidecar mismatch: {names=} {arr.shape=}")
    return arr
