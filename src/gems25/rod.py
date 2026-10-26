"""ROD-1: catalogue-free radiometric offset registration (knowledge/27).

Inputs are quantized radiometric channels, not calibrated elemental concentrations.
An improved offset match is a hypothesis about displacement, NOT evidence of a fault.
"""
from __future__ import annotations

import numpy as np


def shifted(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Sample a[y+dy,x+dx], with NaN padding; never wrap the far edge."""
    a = np.asarray(a, dtype=np.float32)
    if a.ndim != 2:
        raise ValueError("expected a 2-D grid")
    h, w = a.shape
    out = np.full(a.shape, np.nan, dtype=np.float32)
    y0, y1, x0, x1 = max(0, -dy), min(h, h-dy), max(0, -dx), min(w, w-dx)
    if y1 > y0 and x1 > x0:
        out[y0:y1, x0:x1] = a[y0+dy:y1+dy, x0+dx:x1+dx]
    return out


def scale_channel(a: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float32)
    sel = footprint & np.isfinite(a)
    if not sel.any():
        raise ValueError("no finite feature values in footprint")
    lo, hi = np.percentile(a[sel], [1, 99])
    if hi <= lo:
        return np.where(sel, 0.0, np.nan).astype(np.float32)
    return np.where(sel, np.clip((a-lo)/(hi-lo), 0, 1), np.nan).astype(np.float32)


def offset_evidence(channels: list[np.ndarray]) -> np.ndarray:
    """Positive cross-line matching improvement after tangential shifts.

    All three elemental channels must be observed at every stencil location.
    No Gaussian fill across unmapped data, catalogue inputs or raster resampling.
    """
    if len(channels) != 3 or any(a.ndim != 2 or a.shape != channels[0].shape for a in channels):
        raise ValueError("three equal-shaped 2-D normalized channels required")
    out = np.zeros(channels[0].shape, dtype=np.float32)
    for ny, nx in ((1, 0), (0, 1), (1, 1), (1, -1)):
        ty, tx = -nx, ny
        d0 = np.zeros_like(out)
        dm, dp = np.zeros_like(out), np.zeros_like(out)
        for a in channels:
            left = shifted(a, 2*ny, 2*nx)
            d0 += (left - shifted(a, -2*ny, -2*nx))**2
            dm += (left - shifted(a, -2*ny-2*ty, -2*nx-2*tx))**2
            dp += (left - shifted(a, -2*ny+2*ty, -2*nx+2*tx))**2
        ds = np.minimum(dm, dp)
        value = np.maximum(0, (d0-ds)/(d0+ds+0.01)) * np.sqrt(d0/3)
        out = np.maximum(out, np.nan_to_num(value, nan=0.0))
    return out


def build_rod(static, names, footprint):
    """Read the shared static cache and return footprint-vector feature columns."""
    fi = np.flatnonzero(footprint)
    channels = []
    inputs = {}
    for name in ("D_K", "D_Th", "D_U", "L_step_max", "L_coh100"):
        raw = np.asarray(static[names.index(name)], dtype=np.float32)
        inputs[name] = raw
        if name.startswith("D_"):
            grid = np.full(footprint.shape, np.nan, dtype=np.float32)
            grid.ravel()[fi] = raw
            channels.append(scale_channel(grid, footprint))
    offset = offset_evidence(channels).ravel()[fi]
    step = scale_channel(inputs["L_step_max"], np.ones(fi.size, bool))
    support = np.sqrt(np.nan_to_num(step, nan=0) * np.clip(np.nan_to_num(inputs["L_coh100"], nan=0), 0, 1))
    primary = np.sqrt(offset * support)
    inputs.update(ROD_offset=offset, ROD_scarp=support, ROD_primary=primary)
    return inputs
