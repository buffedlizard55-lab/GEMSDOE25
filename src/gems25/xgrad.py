"""XG1 — surface-free cross-gradient alignment block (pre-registered in knowledge/21).

Three static columns built only from potential-field / basement grids already in the
cached band stack (``02_rtp``, ``13_iso_grav_anom``, ``15_depth_to_base_surf``): for each
pair of fields, the ridge strength of ``alignment x joint strength`` of their horizontal
gradient vectors, where alignment is the absolute cosine between the two gradient
directions (1 = parallel edges, cross-gradient ~ 0 in the Gallardo & Meju sense) and
joint strength is the minimum of the two p99-normalised gradient magnitudes.

Physical target: a fault that offsets magnetic basement, density and the conductive base
across the same plane under alluvial cover — no topographic scarp (the catalogue's and
family B's blind spot), but co-oriented edges in three independent fields. Named mimics:
lithologic/intrusive contacts and caldera ring margins (same aligned edges, no fault),
common flight-line levelling artefacts in the gravity and magnetic grids.

No catalogue or label array is read anywhere in this module, so the columns cannot leak
holdout truth through construction; the per-feature AUC canary in the runner is still
applied before any result is trusted.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from .features import nearest_fill, ridge_strength

XG_NAMES = ["XG_gm_align_ridge", "XG_gd_align_ridge", "XG_md_align_ridge"]
SMOOTH_SIGMA = 1.5
RIDGE_SIGMA = 1.5
SCALE_SAMPLE = 200_000
SCALE_SEED = 1
SCALE_PCT = 99.0


def _gradients(field: np.ndarray, sigma: float = SMOOTH_SIGMA) -> tuple[np.ndarray, np.ndarray]:
    """(gy, gx) of the Gaussian-smoothed field. Finite 2-D input required."""
    a = np.asarray(field, dtype=np.float64)
    if a.ndim != 2 or not np.isfinite(a).all():
        raise ValueError("cross-gradient needs a finite 2-D field (fill nodata first)")
    s = gaussian_filter(a, sigma) if sigma > 0 else a
    gy, gx = np.gradient(s)
    return gy.astype(np.float32), gx.astype(np.float32)


def _p99_scale(mag: np.ndarray, sample: int = SCALE_SAMPLE, seed: int = SCALE_SEED) -> float:
    """99th percentile of a gradient magnitude on a fixed random sample (Context-style)."""
    flat = np.asarray(mag, dtype=np.float32).ravel()
    fin = flat[np.isfinite(flat)]
    if fin.size == 0:
        return 1.0
    if fin.size > sample:
        idx = np.random.default_rng(seed).choice(fin.size, size=sample, replace=False)
        fin = fin[np.sort(idx)]
    hi = float(np.percentile(fin, SCALE_PCT))
    return hi if hi > 0 else 1.0


def _pair_column(g1, g2) -> np.ndarray:
    """ridge_strength(|cos| * min normalised magnitude) for two gradient fields."""
    gy1, gx1 = g1
    gy2, gx2 = g2
    m1 = np.sqrt(gx1.astype(np.float64) ** 2 + gy1.astype(np.float64) ** 2)
    m2 = np.sqrt(gx2.astype(np.float64) ** 2 + gy2.astype(np.float64) ** 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        cos = np.abs(gx1 * gx2 + gy1 * gy2) / (m1 * m2)
    cos = np.where((m1 > 0) & (m2 > 0), np.clip(cos, 0.0, 1.0), 0.0)
    joint = np.minimum(m1 / _p99_scale(m1), m2 / _p99_scale(m2))
    joint = np.clip(joint, 0.0, 1.0)
    out = ridge_strength((cos * joint).astype(np.float32), RIDGE_SIGMA)
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)


def xg_grids(gravity: np.ndarray, rtp: np.ndarray, depth_to_base: np.ndarray) -> dict[str, np.ndarray]:
    """The three XG1 grids from raw band grids (NaN nodata allowed; filled internally)."""
    g_grav = _gradients(nearest_fill(np.asarray(gravity, dtype=np.float32)))
    g_mag = _gradients(nearest_fill(np.asarray(rtp, dtype=np.float32)))
    depth_f = nearest_fill(np.asarray(depth_to_base, dtype=np.float32))
    g_dep = _gradients(np.log1p(np.maximum(depth_f, 0.0)))
    return {
        XG_NAMES[0]: _pair_column(g_grav, g_mag),
        XG_NAMES[1]: _pair_column(g_grav, g_dep),
        XG_NAMES[2]: _pair_column(g_mag, g_dep),
    }


def build_xg_sidecar(band_dir: Path, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    """Build (3, n_footprint) float32 sidecar + names JSON from ``work/bands`` grids."""
    band_dir = Path(band_dir)
    gravity = np.load(band_dir / "13_iso_grav_anom.npy")
    rtp = np.load(band_dir / "02_rtp.npy")
    depth = np.load(band_dir / "15_depth_to_base_surf.npy")
    grids = xg_grids(gravity, rtp, depth)
    fi = np.asarray(footprint_idx)
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32, shape=(len(XG_NAMES), fi.size))
    for j, name in enumerate(XG_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"XG column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(XG_NAMES))
    return list(XG_NAMES)


def load_xg_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load the sidecar, building it from the cached bands if absent. Returns (3, n_foot)."""
    work = Path(work)
    path = work / "xgrad_columns.npy"
    if not path.exists():
        build_xg_sidecar(work / "bands", footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != XG_NAMES or arr.shape != (len(XG_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"XG sidecar mismatch: names={names} shape={arr.shape}")
    return arr
