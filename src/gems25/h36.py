"""H36-TZC — coincident tilt-zero contact columns (pre-registered, knowledge/21).

Three static columns, computed once from the pinned competition field bands and
stored as a footprint-vector sidecar so the shared harness (`gems25.experiment.Cell`)
is untouched:

* ``H36_tzc_mag_prox``  — exp(-d_mag^2 / (2*2^2)), d_mag = distance (px) to the
  nearest magnetic tilt-zero-crossing pixel;
* ``H36_tzc_grav_prox`` — same for the gravity tilt-zero line;
* ``H36_tzc_coincide``  — exp(-d_mag * d_grav / 9), high only where *both* contact
  lines are near (a cross-physics coincidence, not an amplitude product).

Tilt operator (knowledge/21 Amendment 1, frozen before any fit): the provider
derivative bands are scale-mismatched for a direct tilt (``tmi_hg`` is a per-km
horizontal-gradient magnitude, Spearman 0.991 with the spatial derivative of
``tmi`` but ~7x its per-pixel scale, while ``tmi_vg`` is ~300x smaller than a
comparable vertical derivative), so tilt is computed from each field itself
(``tmi`` band 14, ``iso_grav_anom`` band 13) by the spectral derivative theorem
at a 200 m upward-continued level: VDR spectrum = 2*pi*|k| * exp(-2*pi*|k|*dz) *
F spectrum, THDR from spatial gradients of the continued field. Both derivatives
then share units and the tilt spans (-pi/2, pi/2). A tilt-zero crossing is a
pixel with a 4-neighbour of opposite sign, gated to at/above-median THDR (Amendment 3).

Physical target (Miller & Singh 1994 tilt concept): a buried fault that juxtaposes
magnetically and gravitationally different basement blocks under alluvial cover
produces coincident tilt-zero contact lines with no Quaternary scarp for the
USGS/INGENIOUS catalogue to record. Named mimics: lithologic contacts / volcanic
flow margins (same contact lines, no fault), basin-margin facies pinch-outs,
survey line-levelling artefacts.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

from .features import nearest_fill

H36_NAMES = ["H36_tzc_mag_prox", "H36_tzc_grav_prox", "H36_tzc_coincide"]
PROX_SIGMA_PX = 2.0
COINCIDE_SCALE_PX2 = 9.0
CELL_M = 100.0
DZ_M = 200.0
PAD_PX = 256


def spectral_tilt(field: np.ndarray, dz_m: float = DZ_M, cell_m: float = CELL_M,
                  pad: int = PAD_PX) -> np.ndarray:
    """Tilt angle atan2(VDR, THDR) of ``field`` at an upward-continued level.

    Finite input required. ``pad`` reflect-pads before the FFT to suppress
    periodic wrap-around; ``pad=0`` is the bare periodic operator (exact for
    periodic test fields, where THDR comes from the same spectrum).
    """
    a = np.asarray(field, dtype=np.float64)
    if a.ndim != 2 or not np.isfinite(a).all():
        raise ValueError("spectral_tilt needs a finite 2-D field (fill nodata first)")
    if dz_m < 0 or cell_m <= 0 or pad < 0:
        raise ValueError("dz_m must be >= 0, cell_m > 0, pad >= 0")
    p = np.pad(a, pad, mode="reflect") if pad else a
    H, W = p.shape
    spec = np.fft.rfft2(p)
    fy = np.fft.fftfreq(H, d=cell_m)[:, None]
    fx = np.fft.rfftfreq(W, d=cell_m)[None, :]
    k = np.sqrt(fx * fx + fy * fy)  # cycles per metre
    att = np.exp(-2.0 * np.pi * k * float(dz_m))
    cont = np.fft.irfft2(spec * att, s=(H, W))
    vdr = np.fft.irfft2(spec * att * (2.0 * np.pi * k), s=(H, W))
    gy, gx = np.gradient(cont, cell_m)
    thdr = np.sqrt(gx * gx + gy * gy)
    theta = np.arctan2(vdr, thdr)
    if pad:
        sl = (slice(pad, pad + a.shape[0]), slice(pad, pad + a.shape[1]))
        return theta[sl].astype(np.float32), thdr[sl].astype(np.float32)
    return theta.astype(np.float32), thdr.astype(np.float32)


def zero_crossing_mask(theta: np.ndarray) -> np.ndarray:
    """Pixels on a tilt-zero line: a 4-neighbour has the opposite sign (knowledge/21 Amd.2).

    Both sides of the contour are marked (a 1-2 px line); a pixel whose theta
    is exactly 0 also counts. NaN theta counts as no crossing.
    """
    t = np.asarray(theta, dtype=np.float64)
    if t.ndim != 2:
        raise ValueError("theta must be 2-D")
    exact = np.isfinite(t) & (t == 0.0)
    pos = np.isfinite(t) & (t > 0)
    neg = np.isfinite(t) & (t < 0)

    def shift(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
        out = np.zeros_like(a)
        ys = slice(max(dy, 0), a.shape[0] + min(dy, 0))
        xs = slice(max(dx, 0), a.shape[1] + min(dx, 0))
        yt = slice(max(-dy, 0), a.shape[0] + min(-dy, 0))
        xt = slice(max(-dx, 0), a.shape[1] + min(-dx, 0))
        out[ys, xs] = a[yt, xt]
        return out

    crosses = np.zeros_like(exact)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        crosses |= (pos & shift(neg, dy, dx)) | (neg & shift(pos, dy, dx))
    return crosses | exact


def proximity(distance_px: np.ndarray, sigma: float = PROX_SIGMA_PX) -> np.ndarray:
    d = np.asarray(distance_px, dtype=np.float64)
    return np.exp(-(d * d) / (2.0 * float(sigma) ** 2)).astype(np.float32)


def h36_grids(tmi: np.ndarray, grav: np.ndarray) -> dict[str, np.ndarray]:
    """The three H36 grids from the two field grids (NaN nodata filled internally)."""
    th_mag, thdr_mag = spectral_tilt(nearest_fill(np.asarray(tmi, dtype=np.float32)))
    th_grav, thdr_grav = spectral_tilt(nearest_fill(np.asarray(grav, dtype=np.float32)))
    # Amendment 3: keep only crossings with at/above-median gradient strength.
    z_mag = zero_crossing_mask(th_mag) & (thdr_mag >= np.median(thdr_mag))
    z_grav = zero_crossing_mask(th_grav) & (thdr_grav >= np.median(thdr_grav))
    if not z_mag.any() or not z_grav.any():
        raise ValueError(f"empty tilt-zero line: mag={int(z_mag.sum())} grav={int(z_grav.sum())}")
    d_mag = distance_transform_edt(~z_mag)
    d_grav = distance_transform_edt(~z_grav)
    return {
        H36_NAMES[0]: proximity(d_mag),
        H36_NAMES[1]: proximity(d_grav),
        H36_NAMES[2]: np.exp(-d_mag * d_grav / COINCIDE_SCALE_PX2).astype(np.float32),
        "_zero_mag_px": z_mag,
        "_zero_grav_px": z_grav,
        "_theta_mag": th_mag,
        "_theta_grav": th_grav,
    }


def build_h36_sidecar(band_dir: Path, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    """Build (3, n_footprint) float32 sidecar + names JSON from ``work/bands`` grids."""
    band_dir = Path(band_dir)
    grids = h36_grids(np.load(band_dir / "14_tmi.npy"), np.load(band_dir / "13_iso_grav_anom.npy"))
    diag = {k: int(grids[k].sum()) for k in ("_zero_mag_px", "_zero_grav_px")}
    fi = np.asarray(footprint_idx)
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32, shape=(len(H36_NAMES), fi.size))
    for j, name in enumerate(H36_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"H36 column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H36_NAMES))
    Path(str(out_path) + ".diag.json").write_text(json.dumps(diag))
    return list(H36_NAMES)


def load_h36_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load the sidecar, building it from the cached bands if absent. Returns (3, n_foot)."""
    work = Path(work)
    path = work / "h36_columns.npy"
    if not path.exists():
        build_h36_sidecar(work / "bands", footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H36_NAMES or arr.shape != (len(H36_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"H36 sidecar mismatch: names={names} shape={arr.shape}")
    return arr
