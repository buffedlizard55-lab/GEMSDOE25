"""APFL piedmont-flexure columns — reconstruction from the frozen formula (knowledge/27, knowledge/29).

The 2026-10-26 APFL GeoTIFF shipped with a run card and a frozen product formula
but no builder code in this repo (irregularity disclosed in knowledge/29). This
module re-implements that formula from the pinned static cache only. It is a
reconstruction: percentile scaling uses the full footprint (p1/p99), components
are floored at ``FLOOR`` before the power product so one zero channel does not
annihilate the geometric-mean-style product, and ``L_valid`` gates the product
(no LiDAR descriptors -> product 0). Any numerical difference from the shipped
APFL file is measured and reported by the session's lane audit, never hidden.

Formula (knowledge/27 section 3, frozen):
    S = L_valid * (L_step^0.35 * gravAS^0.30 * depthGrad^0.20 * condGrad^0.05
                   * TPI_pos^0.10) * (1 + 0.5 * crest)
with every component p1-p99 scaled to [0, 1] on the footprint. ``labels.tif`` is
never read. Named non-fault mimic: unfaulted alluvial-fan onlap wedges / axial
drainage incision (same TPI/depth gradients, no gravity step).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

APFL_INPUTS = ("L_step_max", "A_grav_as", "D_depth_base_grad", "D_cond_grad", "B_tpi11", "B_crest", "L_valid")
APFL_NAMES = ["APFL_lstep", "APFL_gravas", "APFL_depthgrad", "APFL_condgrad", "APFL_tpipos", "APFL_crest", "APFL_product"]
APFL_WEIGHTS = dict(lstep=0.35, gravas=0.30, depthgrad=0.20, condgrad=0.05, tpipos=0.10)
FLOOR = 0.01


def _pct01(v: np.ndarray) -> np.ndarray:
    """p1-p99 scale a footprint vector to [0, 1] (non-finite -> 0)."""
    v = np.asarray(v, dtype=np.float64)
    out = np.zeros(v.shape, dtype=np.float32)
    fin = np.isfinite(v)
    if not fin.any():
        return out
    lo, hi = np.percentile(v[fin], [1.0, 99.0])
    if not np.isfinite(hi) or hi <= lo:
        return out
    out[fin] = np.clip((v[fin] - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)
    return out


def apfl_components(static: np.ndarray, static_names: list[str]) -> np.ndarray:
    """Return the (7, n_footprint) APFL sidecar array from the static cache."""
    missing = [n for n in APFL_INPUTS if n not in static_names]
    if missing:
        raise ValueError(f"static cache is missing APFL inputs: {missing}")
    idx = {n: static_names.index(n) for n in APFL_INPUTS}
    n = static.shape[1]
    lstep = _pct01(np.asarray(static[idx["L_step_max"]], dtype=np.float64))
    gravas = _pct01(np.asarray(static[idx["A_grav_as"]], dtype=np.float64))
    depthg = _pct01(np.asarray(static[idx["D_depth_base_grad"]], dtype=np.float64))
    condg = _pct01(np.asarray(static[idx["D_cond_grad"]], dtype=np.float64))
    # TPI positive part: scaled TPI above its footprint median, rescaled to [0,1].
    tpi_raw = np.asarray(static[idx["B_tpi11"]], dtype=np.float64)
    tpi_scaled = _pct01(tpi_raw)
    med = float(np.nanmedian(tpi_scaled[np.isfinite(tpi_scaled)])) if n else 0.5
    tpipos = np.clip((tpi_scaled - med) / max(1.0 - med, 1e-6), 0.0, 1.0).astype(np.float32)
    crest = _pct01(np.asarray(static[idx["B_crest"]], dtype=np.float64))
    valid_raw = np.asarray(static[idx["L_valid"]], dtype=np.float64)
    valid01 = np.where(np.isfinite(valid_raw) & (valid_raw > 0), 1.0, 0.0).astype(np.float32)

    w = APFL_WEIGHTS
    log_prod = (
        w["lstep"] * np.log(np.maximum(lstep, FLOOR))
        + w["gravas"] * np.log(np.maximum(gravas, FLOOR))
        + w["depthgrad"] * np.log(np.maximum(depthg, FLOOR))
        + w["condgrad"] * np.log(np.maximum(condg, FLOOR))
        + w["tpipos"] * np.log(np.maximum(tpipos, FLOOR))
    )
    product = (valid01 * np.exp(log_prod) * (1.0 + 0.5 * crest)).astype(np.float32)
    product = np.nan_to_num(product, nan=0.0, posinf=0.0, neginf=0.0)
    # Renormalise product to [0, 1] by its p99 so DIRECT emission thresholds are stable.
    p99 = float(np.percentile(product, 99.0)) if product.size else 0.0
    if p99 > 0:
        product = np.clip(product / p99, 0.0, 1.0).astype(np.float32)
    out = np.vstack([lstep, gravas, depthg, condg, tpipos, crest, product]).astype(np.float32)
    if not np.isfinite(out).all():
        raise ValueError("APFL sidecar contains non-finite values")
    return out


def load_apfl_sidecar(work: Path, static: np.ndarray, static_names: list[str]) -> np.ndarray:
    """Load (or build and cache) the APFL sidecar in ``work``. Returns (7, n_foot)."""
    work = Path(work)
    path = work / "apfl_columns.npy"
    n_foot = int(static.shape[1])
    if path.exists():
        arr = np.load(path, mmap_mode="r")
        names = json.loads(Path(str(path) + ".names.json").read_text())
        if names == APFL_NAMES and arr.shape == (len(APFL_NAMES), n_foot):
            return arr
        raise ValueError(f"APFL sidecar mismatch: names={names} shape={arr.shape}")
    cols = apfl_components(static, static_names)
    mm = np.lib.format.open_memmap(path, mode="w+", dtype=np.float32, shape=cols.shape)
    mm[:] = cols
    mm.flush()
    del mm
    Path(str(path) + ".names.json").write_text(json.dumps(APFL_NAMES))
    return np.load(path, mmap_mode="r")
