"""H37-SEISALIGN — seismicity-alignment columns (pre-registered, knowledge/22).

Three static columns from the two earthquake-density bands, stored as a
footprint-vector sidecar so the shared harness is untouched:

* ``H37_seis_deq_coh``         — structure-tensor coherence of log(deq_n100a15);
* ``H37_seis_deq_alignridge``  — ridge_strength(log deq, 2.0) x that coherence;
* ``H37_seis_ieq_alignridge``  — ridge_strength(log ieq, 2.0) x ieq coherence.

Structure tensor: gradients of the sigma=2 px Gaussian-smoothed log-density,
tensor components smoothed at sigma=5 px; coherence
c = sqrt((Jxx-Jyy)^2 + (2Jxy)^2) / (Jxx+Jyy + eps) in [0, 1] measures local
gradient-orientation alignment (an elongated density ridge has c near 1).

Physical target: microseismicity aligned along a buried seismogenic fault
traces it where no Quaternary scarp exists. Named mimics: aftershock/swarm
elongation on non-fault structures, induced seismicity, location-error
smearing, and the provider density kernel's own 15-degree azimuth parameter
(knowledge/22, flagged in advance).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

from .features import nearest_fill, ridge_strength

H37_NAMES = ["H37_seis_deq_coh", "H37_seis_deq_alignridge", "H37_seis_ieq_alignridge"]
SMOOTH_SIGMA = 2.0
TENSOR_SIGMA = 5.0
RIDGE_SIGMA = 2.0
EPS = 1e-12


def structure_tensor_coherence(field: np.ndarray, smooth: float = SMOOTH_SIGMA,
                               tensor_sigma: float = TENSOR_SIGMA) -> np.ndarray:
    """Gradient-orientation coherence in [0, 1] of a finite 2-D field."""
    a = np.asarray(field, dtype=np.float64)
    if a.ndim != 2 or not np.isfinite(a).all():
        raise ValueError("coherence needs a finite 2-D field (fill nodata first)")
    s = gaussian_filter(a, smooth)
    gy, gx = np.gradient(s)
    jxx = gaussian_filter(gx * gx, tensor_sigma)
    jyy = gaussian_filter(gy * gy, tensor_sigma)
    jxy = gaussian_filter(gx * gy, tensor_sigma)
    num = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy * jxy)
    den = jxx + jyy
    return np.where(den > EPS, num / (den + EPS), 0.0).astype(np.float32)


def _align_columns(band: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    f = np.log1p(np.maximum(nearest_fill(np.asarray(band, dtype=np.float32)), 0.0)).astype(np.float64)
    coh = structure_tensor_coherence(f)
    ridge = ridge_strength(f.astype(np.float32), RIDGE_SIGMA)
    return coh, (ridge * coh).astype(np.float32)


def h37_grids(deq: np.ndarray, ieq: np.ndarray) -> dict[str, np.ndarray]:
    """The three H37 grids from the two earthquake-density grids (NaN filled internally)."""
    coh_d, align_d = _align_columns(deq)
    coh_i, align_i = _align_columns(ieq)
    out = {H37_NAMES[0]: coh_d, H37_NAMES[1]: align_d, H37_NAMES[2]: align_i,
           "_ieq_coh": coh_i}
    for name in H37_NAMES:
        g = out[name]
        if not np.isfinite(g).all():
            raise ValueError(f"H37 column {name} has non-finite values")
    return out


def build_h37_sidecar(band_dir: Path, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    band_dir = Path(band_dir)
    grids = h37_grids(np.load(band_dir / "10_deq_n100a15.npy"), np.load(band_dir / "16_ieq_n100a15.npy"))
    fi = np.asarray(footprint_idx)
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32, shape=(len(H37_NAMES), fi.size))
    for j, name in enumerate(H37_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"H37 column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H37_NAMES))
    return list(H37_NAMES)


def load_h37_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    work = Path(work)
    path = work / "h37_columns.npy"
    if not path.exists():
        build_h37_sidecar(work / "bands", footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H37_NAMES or arr.shape != (len(H37_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"H37 sidecar mismatch: names={names} shape={arr.shape}")
    return arr
