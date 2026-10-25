"""MSCR-1 — Multi-scale crest persistence columns (pre-registered, knowledge/22).

Three static columns from the pinned detrended-elevation band (band 12), stored as a
footprint-vector sidecar so the shared harness (`gems25.experiment.Cell`) is untouched:

* ``MSCR_crest_s4``      — ``ridge_strength(z, 4.0)`` (400 m-scale crest), >= 0
* ``MSCR_crest_persist`` — ``sqrt(c1 * c4)`` in [0, 1], where ``c1``/``c4`` are the
  percentile-scaled (1st-99th, footprint) ridge strengths at sigma 1 and 4 px
* ``MSCR_trough_s4``     — ``ridge_strength(-z, 4.0)`` (400 m-scale trough), >= 0

Physical target: fault-controlled range fronts / graben margins are topographic lines at
400 m+ wavelength that the incumbent single-scale (sigma 1.5) crest/trough and the
within-cell LiDAR descriptors cannot separate from gully-scale noise. Named mimics:
lithologic strike ridges/valleys (hogbacks, soft-unit strike valleys) and fluvial terrace
edges, which also persist across these scales without any fault. No label is read here.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .features import nearest_fill, ridge_strength
from .gmce import _pct_scale

MSCR_NAMES = ["MSCR_crest_s4", "MSCR_crest_persist", "MSCR_trough_s4"]
SIGMA_NARROW = 1.0
SIGMA_BROAD = 4.0


def mscr_grids(det_elev: np.ndarray, footprint: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """The three MSCR grids from a raw ``det_elev`` grid (NaN nodata allowed; filled inside)."""
    a = np.asarray(det_elev)
    if a.ndim != 2:
        raise ValueError("det_elev must be a 2-D grid")
    if footprint is not None and np.asarray(footprint).shape != a.shape:
        raise ValueError("footprint must match det_elev")
    z = nearest_fill(a.astype(np.float32))
    if float(z.max()) == float(z.min()):
        raise ValueError("det_elev is constant after filling; ridge fields would be degenerate")
    crest4 = ridge_strength(z, SIGMA_BROAD)
    trough4 = ridge_strength(-z, SIGMA_BROAD)
    crest1 = ridge_strength(z, SIGMA_NARROW)
    sel = np.ones(a.shape, bool) if footprint is None else np.asarray(footprint, bool)
    c1 = _pct_scale(crest1.astype(np.float64), crest1[sel])
    c4 = _pct_scale(crest4.astype(np.float64), crest4[sel])
    return {
        MSCR_NAMES[0]: crest4,
        MSCR_NAMES[1]: np.sqrt(c1 * c4).astype(np.float32),
        MSCR_NAMES[2]: trough4,
    }


def build_mscr_sidecar(band_dir: Path, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    """Build (3, n_footprint) float32 sidecar + names JSON from ``work/bands`` grids."""
    band_dir = Path(band_dir)
    z = np.load(band_dir / "12_det_elev.npy")
    fi = np.asarray(footprint_idx)
    footprint = np.zeros(z.shape, bool)
    footprint.ravel()[fi] = True
    grids = mscr_grids(z, footprint)
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32, shape=(len(MSCR_NAMES), fi.size))
    for j, name in enumerate(MSCR_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"MSCR column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(MSCR_NAMES))
    return list(MSCR_NAMES)


def load_mscr_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load the sidecar, building it from the cached bands if absent. Returns (3, n_foot)."""
    work = Path(work)
    path = work / "mscr_columns.npy"
    if not path.exists():
        build_mscr_sidecar(work / "bands", footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != MSCR_NAMES or arr.shape != (len(MSCR_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"MSCR sidecar mismatch: names={names} shape={arr.shape}")
    return arr
