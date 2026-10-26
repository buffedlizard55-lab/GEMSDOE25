"""H71-4 multi-scale structure-tensor lineaments of shallow residual RTP (DIRECT, catalogue-free).

``rtp - upward_continue(rtp, 400 m)`` then structure-tensor anisotropy × |∇| at σ=1 and σ=2;
persistence is the geometric mean. Distinct from H34 (Hessian ridge of the same residual as an HGB column).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from .features import nearest_fill
from .h34 import DZ_SHALLOW_M, upward_continue_multi

H71_MAG_NAMES = ["H71_mag_aniso_persist"]
EPS = 1e-12


def structure_tensor_ridge(field: np.ndarray, sigma: float) -> np.ndarray:
    s = gaussian_filter(np.asarray(field, dtype=np.float32), float(sigma))
    gy, gx = np.gradient(s)
    jxx = gaussian_filter(gx * gx, sigma)
    jyy = gaussian_filter(gy * gy, sigma)
    jxy = gaussian_filter(gx * gy, sigma)
    tmp = np.sqrt(((jxx - jyy) * 0.5) ** 2 + jxy * jxy)
    l1 = 0.5 * (jxx + jyy) + tmp
    l2 = 0.5 * (jxx + jyy) - tmp
    aniso = (l1 - l2) / (l1 + l2 + EPS)
    mag = np.sqrt(gx * gx + gy * gy)
    return (np.clip(aniso, 0.0, 1.0) * mag).astype(np.float32)


def compute_mag_aniso_grid(rtp: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    foot = np.asarray(footprint, dtype=bool)
    rtp_f = nearest_fill(np.asarray(rtp, dtype=np.float32))
    up400 = upward_continue_multi(rtp_f, (DZ_SHALLOW_M,))[0]
    residual = rtp_f - up400
    r1 = structure_tensor_ridge(residual, 1.0)
    r2 = structure_tensor_ridge(residual, 2.0)
    pers = np.sqrt(np.maximum(r1, 0.0) * np.maximum(r2, 0.0))
    out = np.zeros(foot.shape, dtype=np.float32)
    fin = foot & np.isfinite(pers)
    if fin.any():
        lo, hi = np.percentile(pers[fin], [1, 99])
        if hi > lo:
            out[fin] = np.clip((pers[fin] - lo) / (hi - lo), 0.0, 1.0)
    return np.where(foot, out, 0.0).astype(np.float32)


def build_mag_sidecar(band_dir: Path, footprint: np.ndarray, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    rtp = np.load(Path(band_dir) / "02_rtp.npy")
    grid = compute_mag_aniso_grid(rtp, footprint)
    fi = np.asarray(footprint_idx)
    out_path = Path(out_path)
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(1, fi.size))
    v = grid.ravel()[fi]
    if not np.isfinite(v).all():
        raise ValueError("H71 MAG column has non-finite values")
    mm[0] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H71_MAG_NAMES))
    return list(H71_MAG_NAMES)


def load_mag_sidecar(work: Path, footprint: np.ndarray, footprint_idx: np.ndarray) -> np.ndarray:
    path = Path(work) / "h71_mag_columns.npy"
    if not path.exists():
        build_mag_sidecar(Path(work) / "bands", footprint, footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H71_MAG_NAMES or arr.shape != (1, np.asarray(footprint_idx).size):
        raise ValueError(f"MAG sidecar mismatch: {names} {arr.shape}")
    return arr
