"""GMCE-1 — Gravity-Magnetic Coherent Edge columns (pre-registered, knowledge/21).

Three static columns, computed once from the pinned competition bands and stored as a
footprint-vector sidecar so the shared harness (`gems25.experiment.Cell`) is untouched:

* ``GMCE_par_min``    — ``min(e_G, e_M) * |cos(delta)|`` in [0, 1]
* ``GMCE_signed_min`` — ``min(e_G, e_M) * cos(delta)`` in [-1, 1]
* ``GMCE_ridge_par``  — Hessian ridge strength of ``GMCE_par_min`` (sigma 1.5), >= 0

where ``G``/``M`` are the isostatic gravity anomaly (band 13) and RTP magnetic anomaly
(band 2) grids, nodata-filled and Gaussian-smoothed at sigma = 2 px; ``delta`` is the
angle between their gradient *vectors* ``grad(G)`` and ``grad(M)``; and ``e_G``/``e_M``
are the log1p gradient magnitudes percentile-scaled (1st-99th, footprint only) to [0, 1].

Physical target: a fault offsetting basement juxtaposes blocks differing in both density
and magnetization across the same plane, so both potential fields step across one line and
their gradient vectors are (anti)parallel there — including under cover with no scarp for
the catalogue to record. Named mimics: lithologic contacts (intrusion margins,
stratigraphic pinch-outs) with joint density+magnetization contrast but no fault, and
survey-levelling lineaments shared by both grids. No label is read by this module.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from .features import nearest_fill, ridge_strength

GMCE_NAMES = ["GMCE_par_min", "GMCE_signed_min", "GMCE_ridge_par"]
SMOOTH_SIGMA = 2.0
RIDGE_SIGMA = 1.5
EPS = 1e-12


def _pct_scale(v: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Clip-scale ``v`` to [0, 1] using the 1st/99th percentiles of ``ref`` (finite only)."""
    r = np.asarray(ref, dtype=np.float64).ravel()
    r = r[np.isfinite(r)]
    if r.size == 0:
        raise ValueError("percentile reference has no finite values")
    lo, hi = np.percentile(r, (1.0, 99.0))
    if not hi > lo:
        raise ValueError("percentile reference is degenerate (p99 <= p1)")
    return np.clip((np.asarray(v, dtype=np.float64) - lo) / (hi - lo), 0.0, 1.0)


def gradient_cosine(grav: np.ndarray, mag: np.ndarray, sigma: float = SMOOTH_SIGMA):
    """Return ``(cos_delta, |grad G|, |grad M|)`` for two finite, same-shaped 2-D fields.

    ``cos_delta`` is 0 wherever either gradient is exactly zero (direction undefined);
    the caller multiplies by the (zero) minimum edge there, so the choice is inert.
    """
    g = np.asarray(grav, dtype=np.float64)
    m = np.asarray(mag, dtype=np.float64)
    if g.ndim != 2 or g.shape != m.shape or not np.isfinite(g).all() or not np.isfinite(m).all():
        raise ValueError("gradient_cosine needs two finite, equal-shaped 2-D fields (fill nodata first)")
    if sigma < 0:
        raise ValueError("sigma must be >= 0")
    if sigma > 0:
        g = gaussian_filter(g, sigma)
        m = gaussian_filter(m, sigma)
    gy, gx = np.gradient(g)
    my, mx = np.gradient(m)
    ng = np.hypot(gx, gy)
    nm = np.hypot(mx, my)
    cos = np.where((ng > 0) & (nm > 0), (gx * mx + gy * my) / (ng * nm + EPS), 0.0)
    return np.clip(cos, -1.0, 1.0), ng, nm


def gmce_grids(grav: np.ndarray, mag: np.ndarray, footprint: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """The three GMCE grids from raw band grids (NaN nodata allowed; filled internally).

    Percentile scaling of the log gradient magnitudes uses ``footprint`` pixels only when
    given, else every finite pixel of the filled grids.
    """
    grav = np.asarray(grav)
    mag = np.asarray(mag)
    if grav.ndim != 2 or grav.shape != mag.shape:
        raise ValueError("grav and mag must be equal-shaped 2-D grids")
    if footprint is not None and np.asarray(footprint).shape != grav.shape:
        raise ValueError("footprint must match the band grids")
    g_f = nearest_fill(grav.astype(np.float32))
    m_f = nearest_fill(mag.astype(np.float32))
    cos, ng, nm = gradient_cosine(g_f, m_f, SMOOTH_SIGMA)
    lg, lm = np.log1p(ng), np.log1p(nm)
    sel = np.ones(grav.shape, bool) if footprint is None else np.asarray(footprint, bool)
    e_g = _pct_scale(lg, lg[sel])
    e_m = _pct_scale(lm, lm[sel])
    e_min = np.minimum(e_g, e_m)
    par = (e_min * np.abs(cos)).astype(np.float32)
    signed = (e_min * cos).astype(np.float32)
    return {
        GMCE_NAMES[0]: par,
        GMCE_NAMES[1]: signed,
        GMCE_NAMES[2]: ridge_strength(par, RIDGE_SIGMA),
    }


def build_gmce_sidecar(band_dir: Path, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    """Build (3, n_footprint) float32 sidecar + names JSON from ``work/bands`` grids."""
    band_dir = Path(band_dir)
    grav = np.load(band_dir / "13_iso_grav_anom.npy")
    mag = np.load(band_dir / "02_rtp.npy")
    fi = np.asarray(footprint_idx)
    footprint = np.zeros(grav.shape, bool)
    footprint.ravel()[fi] = True
    grids = gmce_grids(grav, mag, footprint)
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32, shape=(len(GMCE_NAMES), fi.size))
    for j, name in enumerate(GMCE_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"GMCE column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(GMCE_NAMES))
    return list(GMCE_NAMES)


def load_gmce_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load the sidecar, building it from the cached bands if absent. Returns (3, n_foot)."""
    work = Path(work)
    path = work / "gmce_columns.npy"
    if not path.exists():
        build_gmce_sidecar(work / "bands", footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != GMCE_NAMES or arr.shape != (len(GMCE_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"GMCE sidecar mismatch: names={names} shape={arr.shape}")
    return arr
