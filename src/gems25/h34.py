"""H34-1 RESMAG-FLEX — depth-sliced potential-field columns (pre-registered, knowledge/18).

Three static columns, computed once from the pinned competition bands and stored as a
footprint-vector sidecar so the shared harness (`gems25.experiment.Cell`) is untouched:

* ``H34_resmag_shallow_ridge`` — ridge strength of ``log1p(|grad(RTP - RTP↑400 m)|)``
* ``H34_resmag_mid_ridge``     — ridge strength of ``log1p(|grad(RTP↑400 m - RTP↑1200 m)|)``
* ``H34_baseflex_ridge``       — ridge strength of ``|grad(log1p(depth_to_base_surf))|``

Upward continuation is the exact Fourier-domain potential-field operator: a harmonic
field observed on a plane, continued upward by ``dz``, has spectrum multiplied by
``exp(-2*pi*|f|*dz)`` with ``|f|`` in cycles per metre. This is a mathematical identity
for the operator (implemented and unit-tested here on synthetics), not a data claim.

Physical target: a fault that offsets magnetic basement/volcanics or the conductive
base produces a depth-localised potential-field edge even where alluvial cover removes
every topographic scarp (the catalogue's and family B's blind spot). Named mimics:
lithologic contacts / flow margins (same magnetic edge, no fault), depositional
basin-margin pinch-out (same base gradient ridge, no fault), survey line levelling.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .features import grad_mag, nearest_fill, ridge_strength

H34_NAMES = ["H34_resmag_shallow_ridge", "H34_resmag_mid_ridge", "H34_baseflex_ridge"]
CELL_M = 100.0
DZ_SHALLOW_M = 400.0
DZ_MID_M = 1200.0
RIDGE_SIGMA = 1.5
PAD_PX = 256


def upward_continue_multi(field: np.ndarray, dzs_m: tuple[float, ...], cell_m: float = CELL_M,
                          pad: int = PAD_PX) -> list[np.ndarray]:
    """Upward-continue ``field`` by each height in ``dzs_m`` (metres). Finite input required.

    ``pad`` reflect-pads the grid before the FFT to suppress periodic wrap-around;
    ``pad=0`` is the bare periodic operator (exact for periodic test fields).
    """
    a = np.asarray(field, dtype=np.float64)
    if a.ndim != 2 or not np.isfinite(a).all():
        raise ValueError("upward continuation needs a finite 2-D field (fill nodata first)")
    if any(dz < 0 for dz in dzs_m) or cell_m <= 0 or pad < 0:
        raise ValueError("dzs must be >= 0, cell_m > 0, pad >= 0")
    p = np.pad(a, pad, mode="reflect") if pad else a
    H, W = p.shape
    spec = np.fft.rfft2(p)
    fy = np.fft.fftfreq(H, d=cell_m)[:, None]
    fx = np.fft.rfftfreq(W, d=cell_m)[None, :]
    k = np.sqrt(fx * fx + fy * fy)  # cycles per metre
    out = []
    for dz in dzs_m:
        continued = np.fft.irfft2(spec * np.exp(-2.0 * np.pi * k * float(dz)), s=(H, W))
        out.append((continued[pad:pad + a.shape[0], pad:pad + a.shape[1]] if pad else continued).astype(np.float32))
    return out


def h34_grids(rtp: np.ndarray, depth_to_base: np.ndarray) -> dict[str, np.ndarray]:
    """The three H34 grids from raw band grids (NaN nodata allowed; filled internally)."""
    rtp_f = nearest_fill(np.asarray(rtp, dtype=np.float32))
    up400, up1200 = upward_continue_multi(rtp_f, (DZ_SHALLOW_M, DZ_MID_M))
    shallow = rtp_f - up400
    mid = up400 - up1200
    depth_f = nearest_fill(np.asarray(depth_to_base, dtype=np.float32))
    log_depth = np.log1p(np.maximum(depth_f, 0.0))
    return {
        H34_NAMES[0]: ridge_strength(np.log1p(grad_mag(shallow, 1.0)), RIDGE_SIGMA),
        H34_NAMES[1]: ridge_strength(np.log1p(grad_mag(mid, 1.0)), RIDGE_SIGMA),
        H34_NAMES[2]: ridge_strength(grad_mag(log_depth, 1.0), RIDGE_SIGMA),
    }


def build_h34_sidecar(band_dir: Path, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    """Build (3, n_footprint) float32 sidecar + names JSON from ``work/bands`` grids."""
    band_dir = Path(band_dir)
    rtp = np.load(band_dir / "02_rtp.npy")
    depth = np.load(band_dir / "15_depth_to_base_surf.npy")
    grids = h34_grids(rtp, depth)
    fi = np.asarray(footprint_idx)
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32, shape=(len(H34_NAMES), fi.size))
    for j, name in enumerate(H34_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"H34 column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H34_NAMES))
    return list(H34_NAMES)


def load_h34_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load the sidecar, building it from the cached bands if absent. Returns (3, n_foot)."""
    work = Path(work)
    path = work / "h34_columns.npy"
    if not path.exists():
        build_h34_sidecar(work / "bands", footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H34_NAMES or arr.shape != (len(H34_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"H34 sidecar mismatch: names={names} shape={arr.shape}")
    return arr
