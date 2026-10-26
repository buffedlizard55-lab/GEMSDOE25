"""H71-3 aligned knickpoint / drainage-offset field (catalogue-free; DEM only).

Pre-registered in ``knowledge/27_preregistered_h71_hgpc_2026-10-26.md`` as Experiment 2
if H71-1 screen fails. No ``labels.tif`` is read.

Pipeline on the 100 m DEM (``12_det_elev``):
1. nearest-fill + tiny Gaussian (σ=0.6 px) to collapse single-cell pits;
2. D8 flow direction to the steepest downslope neighbour;
3. single-pass accumulation in elevation-descending order;
4. channels ``A ≥ 2 km²`` (200 pixels);
5. stream-power steepness ``k_sn = S · A^0.45`` residual vs log-area bin median;
6. residual mass is splatted **only perpendicular to flow** so aligned across-valley
   knickpoints form a line (a lithologic knickpoint that follows a contact along one
   valley does not).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from .features import nearest_fill

H71_AKF_NAMES = ["H71_akf_knick_align"]
CELL_KM = 0.1  # 100 m
CELL_AREA_KM2 = CELL_KM * CELL_KM  # 0.01
CHAN_MIN_KM2 = 2.0
M_THETA = 0.45
PERP_RADIUS_PX = 8
D8 = ((-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1))


def d8_flowdir(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Integer D8 direction 0..7 toward the steepest descent; -1 = pit / flat."""
    z = np.asarray(z, dtype=np.float32)
    h, w = z.shape
    pad = np.pad(z, 1, mode="constant", constant_values=np.float32(np.inf))
    best_slope = np.zeros((h, w), dtype=np.float32)
    best_drop = np.zeros((h, w), dtype=np.float32)
    fdir = np.full((h, w), -1, dtype=np.int8)
    for k, (dy, dx) in enumerate(D8):
        nb = pad[1 + dy : 1 + dy + h, 1 + dx : 1 + dx + w]
        drop = z - nb
        step = np.float32(np.sqrt(2.0) if (dy != 0 and dx != 0) else 1.0)
        slope = drop / step
        better = slope > best_slope
        fdir = np.where(better, np.int8(k), fdir)
        best_slope = np.where(better, slope, best_slope)
        best_drop = np.where(better, drop, best_drop)
    return fdir, best_drop


def d8_accumulation(z: np.ndarray, foot: np.ndarray, fdir: np.ndarray) -> np.ndarray:
    """Pixels draining through each cell (1 at every footprint pixel). Python loop over sorted cells."""
    z = np.asarray(z, dtype=np.float32)
    foot = np.asarray(foot, dtype=bool)
    fdir = np.asarray(fdir)
    h, w = z.shape
    acc = np.zeros(h * w, dtype=np.float64)
    acc[np.flatnonzero(foot.ravel())] = 1.0
    order = np.argsort(-z.ravel(), kind="mergesort")
    down = np.full(h * w, -1, dtype=np.int32)
    yy, xx = np.divmod(np.arange(h * w, dtype=np.int32), w)
    for k, (dy, dx) in enumerate(D8):
        sel = fdir.ravel() == k
        if not sel.any():
            continue
        ny = yy[sel] + dy
        nx = xx[sel] + dx
        ok = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        idx = np.flatnonzero(sel)
        down[idx[ok]] = ny[ok] * w + nx[ok]
    for i in order:
        j = down[i]
        if j >= 0:
            acc[j] += acc[i]
    return acc.reshape(h, w)


def _log_area_residual(ksn: np.ndarray, area_km2: np.ndarray, chan: np.ndarray, n_bins: int = 8) -> np.ndarray:
    out = np.zeros(ksn.shape, dtype=np.float32)
    a = area_km2[chan]
    k = ksn[chan]
    if a.size < 50:
        return out
    lo, hi = np.percentile(np.log10(np.maximum(a, 1e-4)), [5, 95])
    if not np.isfinite(lo) or hi <= lo:
        return out
    bins = np.linspace(lo, hi, n_bins + 1)
    bid = np.clip(np.digitize(np.log10(np.maximum(a, 1e-4)), bins) - 1, 0, n_bins - 1)
    med = np.array([np.median(k[bid == b]) if np.any(bid == b) else 0.0 for b in range(n_bins)], dtype=np.float32)
    resid = np.maximum(k - med[bid], 0.0)
    tmp = np.zeros(ksn.shape, dtype=np.float32)
    tmp[chan] = resid
    out[chan] = resid
    return out


def compute_akf_grid(det_elev: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Return a [0, 1] aligned-knickpoint field, zero outside the footprint."""
    foot = np.asarray(footprint, dtype=bool)
    z = gaussian_filter(nearest_fill(np.asarray(det_elev, dtype=np.float32)), 0.6)
    fdir, drop = d8_flowdir(z)
    acc = d8_accumulation(z, foot, fdir)
    area = (acc * CELL_AREA_KM2).astype(np.float32)
    chan = foot & (area >= CHAN_MIN_KM2) & (drop > 0)
    # slope (m/m) using D8 step length
    step = np.ones(drop.shape, dtype=np.float32)
    for k, (dy, dx) in enumerate(D8):
        if dy != 0 and dx != 0:
            step = np.where(fdir == k, np.float32(np.sqrt(2.0)), step)
    slope = np.where(chan, drop / (100.0 * step), 0.0).astype(np.float32)
    ksn = (slope * np.power(np.maximum(area, CHAN_MIN_KM2), M_THETA)).astype(np.float32)
    resid = _log_area_residual(ksn, area, chan)
    # splat residual perpendicular to flow so across-valley alignments reinforce
    field = np.zeros(z.shape, dtype=np.float32)
    yy, xx = np.nonzero(chan & (resid > 0))
    h, w = z.shape
    r = PERP_RADIUS_PX
    for y, x in zip(yy.tolist(), xx.tolist()):
        k = int(fdir[y, x])
        if k < 0:
            continue
        pdy, pdx = D8[(k + 2) % 8]
        mass = float(resid[y, x])
        for t in range(-r, r + 1):
            ny, nx_ = y + t * pdy, x + t * pdx
            if 0 <= ny < h and 0 <= nx_ < w and foot[ny, nx_]:
                field[ny, nx_] += mass * (1.0 - abs(t) / float(r + 1))
    field = gaussian_filter(field, 1.0)
    field = np.where(foot, field, 0.0)
    fin = foot & np.isfinite(field) & (field > 0)
    out = np.zeros_like(field, dtype=np.float32)
    if fin.any():
        lo, hi = np.percentile(field[fin], [1, 99])
        if hi > lo:
            out[fin] = np.clip((field[fin] - lo) / (hi - lo), 0.0, 1.0)
    return out.astype(np.float32)


def build_akf_sidecar(band_dir: Path, footprint: np.ndarray, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    z = np.load(Path(band_dir) / "12_det_elev.npy")
    grid = compute_akf_grid(z, footprint)
    fi = np.asarray(footprint_idx)
    out_path = Path(out_path)
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(1, fi.size))
    v = grid.ravel()[fi]
    if not np.isfinite(v).all():
        raise ValueError("H71 AKF column has non-finite values")
    mm[0] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H71_AKF_NAMES))
    return list(H71_AKF_NAMES)


def load_akf_sidecar(work: Path, footprint: np.ndarray, footprint_idx: np.ndarray) -> np.ndarray:
    path = Path(work) / "h71_akf_columns.npy"
    if not path.exists():
        build_akf_sidecar(Path(work) / "bands", footprint, footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H71_AKF_NAMES or arr.shape != (1, np.asarray(footprint_idx).size):
        raise ValueError(f"AKF sidecar mismatch: {names} {arr.shape}")
    return arr
