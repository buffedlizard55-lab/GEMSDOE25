"""H71-1 signed half-graben polarity concordance (DIRECT emission; catalogue-free).

Pre-registered in ``knowledge/27_preregistered_h71_hgpc_2026-10-26.md`` (commit before any fit).

Two physics columns plus a copied Family-B crest control, all finite in ``[0, 1]`` on the
footprint index vector. ``labels.tif`` / ``existing_faults.tif`` are never read.

* ``H71_blind_hgpc`` — local normal is the unit gravity gradient. A hanging-wall basin is a
  gravity low and a deeper MT basement, so basement shallows toward the gravity high:
  ``sgn(∂n g) == -sgn(∂n D_base)``. No DEM (buried / blind basin-bounding faults).
* ``H71_surf_hgpc`` — local normal is the unit elevation gradient (upslope / footwall).
  Three-field concordance ``sgn(∂n z) == sgn(∂n g) == -sgn(∂n D)``.
* ``H71_crest_ctrl`` — percentile-scaled ``B_crest`` from the pinned static cache (same
  emission machinery; not a new hypothesis).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .features import nearest_fill

H71_NAMES = ["H71_blind_hgpc", "H71_surf_hgpc", "H71_crest_ctrl"]
SMOOTH_SIGMA_PX = 2.0
EPS = 1e-12


def _gaussian_smooth(a: np.ndarray, sigma: float) -> np.ndarray:
    from scipy.ndimage import gaussian_filter

    return gaussian_filter(np.asarray(a, dtype=np.float32), float(sigma))


def _unit_grad(field: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (nx, ny, |∇|) with n = ∇ / |∇| in (x=col, y=row) convention."""
    gy, gx = np.gradient(np.asarray(field, dtype=np.float32))
    mag = np.sqrt(gx * gx + gy * gy).astype(np.float32)
    nx = (gx / (mag + EPS)).astype(np.float32)
    ny = (gy / (mag + EPS)).astype(np.float32)
    return nx, ny, mag


def _dn(field: np.ndarray, nx: np.ndarray, ny: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(np.asarray(field, dtype=np.float32))
    return (gx * nx + gy * ny).astype(np.float32)


def _pct01(mag: np.ndarray, foot: np.ndarray, p_lo: float = 1.0, p_hi: float = 99.0) -> np.ndarray:
    """Percentile-scale a non-negative magnitude on the footprint to [0, 1]."""
    foot_b = np.asarray(foot, dtype=bool)
    v = np.asarray(mag, dtype=np.float32)
    fin = foot_b & np.isfinite(v)
    out = np.zeros(foot_b.shape, dtype=np.float32)
    if not fin.any():
        return out
    sample = v[fin]
    lo = float(np.percentile(sample, p_lo))
    hi = float(np.percentile(sample, p_hi))
    if not np.isfinite(hi) or hi <= lo:
        hi = float(sample.max()) if sample.size else 1.0
        if hi <= lo:
            return out
    out[fin] = np.clip((v[fin] - lo) / (hi - lo), 0.0, 1.0)
    return out


def compute_h71_grids(
    det_elev: np.ndarray,
    iso_grav: np.ndarray,
    depth_base: np.ndarray,
    footprint: np.ndarray,
    *,
    sigma_px: float = SMOOTH_SIGMA_PX,
    crest: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Return the three H71 grids (zero outside ``footprint``, finite in [0, 1] inside)."""
    foot = np.asarray(footprint, dtype=bool)
    if det_elev.shape != foot.shape or iso_grav.shape != foot.shape or depth_base.shape != foot.shape:
        raise ValueError("det_elev, iso_grav, depth_base, footprint must share one 2-D shape")

    z = _gaussian_smooth(nearest_fill(np.asarray(det_elev, dtype=np.float32)), sigma_px)
    g = _gaussian_smooth(nearest_fill(np.asarray(iso_grav, dtype=np.float32)), sigma_px)
    d = _gaussian_smooth(nearest_fill(np.asarray(depth_base, dtype=np.float32)), sigma_px)

    # --- blind: n from gravity -------------------------------------------------
    ngx, ngy, gmag = _unit_grad(g)
    dn_g = _dn(g, ngx, ngy)  # == |∇g| ≥ 0
    dn_d_g = _dn(d, ngx, ngy)
    # Concordance: basement shallows toward the gravity high (∂n D < 0).
    blind_ok = (dn_d_g < 0.0) & (gmag > EPS)
    g01 = _pct01(np.abs(dn_g), foot)
    d01_g = _pct01(np.abs(dn_d_g), foot)
    blind = np.where(blind_ok & foot, np.sqrt(np.maximum(g01 * d01_g, 0.0)), 0.0).astype(np.float32)

    # --- surface: n from elevation (upslope / footwall) ------------------------
    nzx, nzy, zmag = _unit_grad(z)
    dn_z = _dn(z, nzx, nzy)  # == |∇z| ≥ 0
    dn_g_z = _dn(g, nzx, nzy)
    dn_d_z = _dn(d, nzx, nzy)
    surf_ok = (dn_g_z > 0.0) & (dn_d_z < 0.0) & (zmag > EPS)
    z01 = _pct01(np.abs(dn_z), foot)
    g01_z = _pct01(np.abs(dn_g_z), foot)
    d01_z = _pct01(np.abs(dn_d_z), foot)
    surf = np.where(
        surf_ok & foot,
        np.power(np.maximum(z01 * g01_z * d01_z, 0.0), 1.0 / 3.0),
        0.0,
    ).astype(np.float32)

    if crest is None:
        crest_g = np.zeros(foot.shape, dtype=np.float32)
    else:
        if np.asarray(crest).shape != foot.shape:
            raise ValueError("crest grid must match footprint shape")
        crest_g = _pct01(np.nan_to_num(np.asarray(crest, dtype=np.float32), nan=0.0), foot)

    def _clip_foot(name: str, arr: np.ndarray) -> np.ndarray:
        out = np.where(foot, np.nan_to_num(arr, nan=0.0), 0.0).astype(np.float32)
        inside = out[foot]
        if inside.size and (not np.isfinite(inside).all()):
            raise ValueError(f"{name} has non-finite values inside the footprint")
        if inside.size and (float(inside.min()) < 0.0 or float(inside.max()) > 1.0 + 1e-6):
            raise ValueError(f"{name} values escape [0, 1] on the footprint")
        return out

    return {
        H71_NAMES[0]: _clip_foot(H71_NAMES[0], blind),
        H71_NAMES[1]: _clip_foot(H71_NAMES[1], surf),
        H71_NAMES[2]: _clip_foot(H71_NAMES[2], crest_g),
    }


def build_h71_sidecar(
    band_dir: Path,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
    out_path: Path,
    *,
    static: np.ndarray | None = None,
    static_names: list[str] | None = None,
) -> list[str]:
    """Write ``(3, n_foot)`` float32 sidecar + names JSON."""
    band_dir = Path(band_dir)
    z = np.load(band_dir / "12_det_elev.npy")
    g = np.load(band_dir / "13_iso_grav_anom.npy")
    d = np.load(band_dir / "15_depth_to_base_surf.npy")
    crest = None
    if static is not None and static_names is not None and "B_crest" in static_names:
        grid = np.zeros(footprint.shape, dtype=np.float32)
        grid.ravel()[np.asarray(footprint_idx)] = np.asarray(static[static_names.index("B_crest")], dtype=np.float32)
        crest = grid
    grids = compute_h71_grids(z, g, d, footprint, crest=crest)
    fi = np.asarray(footprint_idx)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(len(H71_NAMES), fi.size))
    for j, name in enumerate(H71_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"H71 column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H71_NAMES))
    return list(H71_NAMES)


def load_h71_sidecar(
    work: Path,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
    *,
    static: np.ndarray | None = None,
    static_names: list[str] | None = None,
) -> np.ndarray:
    """Load the sidecar, building it if absent. Returns ``(3, n_foot)``."""
    work = Path(work)
    path = work / "h71_hgpc_columns.npy"
    if not path.exists():
        build_h71_sidecar(work / "bands", footprint, footprint_idx, path, static=static, static_names=static_names)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H71_NAMES or arr.shape != (len(H71_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"H71 sidecar mismatch: names={names} shape={arr.shape}")
    return arr
