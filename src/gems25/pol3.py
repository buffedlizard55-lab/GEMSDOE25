"""Catalogue-free signed half-graben polarity features for the pre-registered POL3 screen."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from .features import nearest_fill

POL3_NAMES = ["POL3_elevation_normal_gradient", "POL3_gravity_normal_gradient",
              "POL3_basement_normal_gradient", "POL3_signed_concordance"]
SIGMA_PX = 1.5


def _scale_abs(values: np.ndarray, valid: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    sample = np.asarray(values[footprint & valid & np.isfinite(values)], dtype=np.float32)
    out = np.zeros(values.shape, dtype=np.float32)
    if sample.size == 0:
        return out
    lo, hi = np.percentile(sample, [1.0, 99.0])
    if not np.isfinite(hi) or hi <= lo:
        return out
    out[footprint & valid] = np.clip((np.abs(values[footprint & valid]) - lo) / (hi - lo), 0.0, 1.0)
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def compute_pol3_grids(elevation: np.ndarray, gravity: np.ndarray, basement_depth: np.ndarray,
                       strike_c2: np.ndarray, strike_s2: np.ndarray, lidar_valid: np.ndarray,
                       footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return three normalized gradient magnitudes and the signed 3-field composite.

    All arguments are static inputs. No catalogue or label raster is accepted. The joint sign test is invariant
    to the arbitrary 180-degree direction of the undirected strike-normal vector.
    """
    foot = np.asarray(footprint, dtype=bool)
    valid = foot & np.isfinite(lidar_valid) & (np.asarray(lidar_valid) >= 0.5)
    c2 = np.asarray(strike_c2, dtype=np.float32)
    s2 = np.asarray(strike_s2, dtype=np.float32)
    if any(np.asarray(a).shape != foot.shape for a in
           (elevation, gravity, basement_depth, strike_c2, strike_s2, lidar_valid)):
        raise ValueError("POL3 inputs must all match the footprint grid")

    theta = 0.5 * np.arctan2(s2, c2)
    nx, ny = -np.sin(theta), np.cos(theta)
    derivs = []
    for field in (elevation, gravity, basement_depth):
        z = gaussian_filter(nearest_fill(np.where(foot, np.asarray(field, dtype=np.float32), np.nan)), SIGMA_PX)
        gy, gx = np.gradient(z)
        derivs.append((gx * nx + gy * ny).astype(np.float32))
    gz, gg, gd = derivs
    z01, g01, d01 = (_scale_abs(v, valid, foot) for v in derivs)
    signs = (np.sign(gz) == np.sign(gd)) & (np.sign(gg) == -np.sign(gz))
    concordance = np.where(valid & signs, np.sqrt(np.maximum(z01 * g01 * d01, 0.0)), 0.0).astype(np.float32)
    return tuple(np.where(foot, a, 0.0).astype(np.float32) for a in (z01, g01, d01, concordance))


def build_pol3_sidecar(static: np.ndarray, static_names: list[str], footprint: np.ndarray,
                       footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    """Build a finite [0,1] ``(4, n_footprint)`` array from the cached static stack."""
    required = ("det_elev", "iso_grav_anom", "depth_to_base_surf", "L_strike_c2", "L_strike_s2", "L_valid")
    missing = [n for n in required if n not in static_names]
    if missing:
        raise ValueError(f"POL3 missing cached inputs: {missing}")
    idx = {n: static_names.index(n) for n in required}
    shape = np.asarray(footprint).shape
    grids = {n: np.zeros(shape, np.float32) for n in required}
    fi = np.asarray(footprint_idx, dtype=np.int64)
    for n in required:
        grids[n].ravel()[fi] = np.asarray(static[idx[n]], dtype=np.float32)
    arrays = compute_pol3_grids(*(grids[n] for n in required), footprint)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(len(POL3_NAMES), fi.size))
    for i, a in enumerate(arrays):
        v = a.ravel()[fi]
        if not np.isfinite(v).all() or (v < 0.0).any() or (v > 1.0).any():
            raise ValueError(f"{POL3_NAMES[i]} is not finite in [0,1]")
        mm[i] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(POL3_NAMES) + "\n")
    return list(POL3_NAMES)


def load_pol3_sidecar(work: Path, static: np.ndarray, static_names: list[str],
                      footprint: np.ndarray, footprint_idx: np.ndarray) -> np.ndarray:
    path = Path(work) / "pol3_columns.npy"
    if not path.exists():
        build_pol3_sidecar(static, static_names, footprint, footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != POL3_NAMES or arr.shape != (len(POL3_NAMES), len(footprint_idx)):
        raise ValueError(f"POL3 sidecar mismatch: {names=} {arr.shape=}")
    return arr
