"""H31: Anisotropic Along-Strike Structural Continuation, Cross-Scale 3DEP LiDAR-DEM-Catalogue
Rotational Strike Coherence, and B=2 Digitization-Shadow Flank Guard.

Method lane (single family):
- Experiment 1 (E1 / +ANISO4): Decomposes the Euclidean vector from the nearest visible fault trace
  into its rotational strike alignment ``H31_a_along = cos(2*(phi_disp - theta_strike))``,
  along-strike coordinate ``H31_d_par``, cross-strike normal offset ``H31_d_perp``, and elliptical
  along-strike continuation kernel ``H31_k_aniso``.
- Experiment 2 (E2 / +ANISO4+LIDAR2): Adds explicit rotational inner products between 1 m 3DEP LiDAR
  scarp strike, 100 m DEM lineament strike, and regional visible-catalogue fault strike weighted by
  1 m LiDAR scarp coherence (``H31_lidar_dem_compat``, ``H31_lidar_cat_compat``).
- Experiment 3 (E3 / E2+B2): Applies post-thinning digitization-shadow flank exclusion at
  ``d_vis > 2.0 px`` (200 m, B=2) to shed cartographic flank-shadow false positives on already-mapped
  faults without backfilling low-probability tail candidates.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

H31_ANISO_NAMES = (
    "H31_a_along",
    "H31_d_par",
    "H31_d_perp",
    "H31_k_aniso",
)
H31_COH_NAMES = (
    "H31_lidar_dem_compat",
    "H31_lidar_cat_compat",
)
H31_FEATURE_NAMES = H31_ANISO_NAMES + H31_COH_NAMES

H31_ARMS = (
    "BASE",
    "T_BASE",
    "H31_E1_ANISO",
    "H31_E2_COH",
    "H31_E3_B2",
)


def build_static_lidar_dem_coherence(
    static: np.ndarray,
    static_names: list[str],
    addon: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(l_c2, l_s2, l_coh, lidar_dem_compat)`` over the footprint index vector ``fi``."""
    idx_c2 = static_names.index("L_strike_c2")
    idx_s2 = static_names.index("L_strike_s2")
    idx_coh = static_names.index("L_coh100")

    l_c2 = np.nan_to_num(np.asarray(static[idx_c2], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    l_s2 = np.nan_to_num(np.asarray(static[idx_s2], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    l_coh = np.clip(
        np.nan_to_num(np.asarray(static[idx_coh], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0),
        0.0,
        1.0,
    )
    dem_c2 = np.nan_to_num(np.asarray(addon[3], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    dem_s2 = np.nan_to_num(np.asarray(addon[4], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)

    lidar_dem_compat = np.clip((l_c2 * dem_c2 + l_s2 * dem_s2) * l_coh, -1.0, 1.0).astype(np.float32)
    return l_c2, l_s2, l_coh, lidar_dem_compat


def build_h31_features(
    visible: np.ndarray,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
    l_c2: np.ndarray,
    l_s2: np.ndarray,
    l_coh: np.ndarray,
    lidar_dem_compat: np.ndarray,
    chunk_size: int = 500_000,
) -> np.ndarray:
    """Compute the 6 H31 columns ``(6, n_footprint)`` strictly from the visible fault mask and static caches.

    Columns:
      0: ``H31_a_along``          — cos(2*(phi_disp - theta_strike)) in [-1, 1]
      1: ``H31_d_par``            — log1p(min(d_parallel, 60.0))
      2: ``H31_d_perp``           — log1p(min(d_perpendicular, 60.0))
      3: ``H31_k_aniso``          — exp(-d_par_raw/12 - d_perp_raw/3) * max(0, a_along)
      4: ``H31_lidar_dem_compat`` — cos(2*(theta_LiDAR - theta_DEM)) * L_coh100
      5: ``H31_lidar_cat_compat`` — cos(2*(theta_LiDAR - theta_cat)) * L_coh100
    """
    v = np.asarray(visible, dtype=bool) & np.asarray(footprint, dtype=bool)
    fi = np.asarray(footprint_idx, dtype=np.int64)
    H, W = v.shape
    out = np.zeros((6, fi.size), dtype=np.float32)
    out[4] = lidar_dem_compat
    if not v.any() or fi.size == 0:
        return out

    dist, (iy, ix) = distance_transform_edt(~v, return_indices=True)
    s = gaussian_filter(v.astype(np.float32), 2.0)
    gy, gx = np.gradient(s)
    jxx = gaussian_filter(gx * gx, 2.0)
    jyy = gaussian_filter(gy * gy, 2.0)
    jxy = gaussian_filter(gx * gy, 2.0)
    th_grad2 = np.arctan2(2.0 * jxy, jxx - jyy)
    c2 = (-np.cos(th_grad2)).astype(np.float32)
    s2 = (-np.sin(th_grad2)).astype(np.float32)
    del s, gy, gx, jxx, jyy, jxy, th_grad2

    dist_flat = dist.ravel()
    iy_flat = iy.ravel()
    ix_flat = ix.ravel()
    c2_flat = c2.ravel()
    s2_flat = s2.ravel()

    for start in range(0, fi.size, chunk_size):
        stop = min(fi.size, start + chunk_size)
        ids = fi[start:stop]
        rr = (ids // W).astype(np.float32)
        cc = (ids % W).astype(np.float32)
        nr = iy_flat[ids].astype(np.float32)
        nc = ix_flat[ids].astype(np.float32)
        near_flat = iy_flat[ids].astype(np.int64) * W + ix_flat[ids].astype(np.int64)

        dr = rr - nr
        dc = cc - nc
        d_fi = dist_flat[ids].astype(np.float32)
        d2 = np.maximum(dr * dr + dc * dc, 1e-12)
        disp_c2 = (dc * dc - dr * dr) / d2
        disp_s2 = (2.0 * dc * dr) / d2

        nc2 = c2_flat[near_flat]
        ns2 = s2_flat[near_flat]
        a_along = np.clip(nc2 * disp_c2 + ns2 * disp_s2, -1.0, 1.0)

        d_par_raw = d_fi * np.sqrt(np.maximum(0.0, 0.5 * (1.0 + a_along)))
        d_perp_raw = d_fi * np.sqrt(np.maximum(0.0, 0.5 * (1.0 - a_along)))

        out[0, start:stop] = a_along.astype(np.float32)
        out[1, start:stop] = np.log1p(np.minimum(d_par_raw, 60.0)).astype(np.float32)
        out[2, start:stop] = np.log1p(np.minimum(d_perp_raw, 60.0)).astype(np.float32)
        out[3, start:stop] = (
            np.exp(-d_par_raw / 12.0 - d_perp_raw / 3.0) * np.maximum(0.0, a_along)
        ).astype(np.float32)
        out[5, start:stop] = np.clip(
            (l_c2[start:stop] * nc2 + l_s2[start:stop] * ns2) * l_coh[start:stop],
            -1.0,
            1.0,
        ).astype(np.float32)

    return out


def apply_digitization_shadow_guard(
    emitted: np.ndarray,
    known_faults: np.ndarray,
    buffer_px: float = 2.0,
) -> np.ndarray:
    """Suppress emitted dots within ``buffer_px`` (default B=2.0 px = 200 m) of known/visible fault traces."""
    em = np.asarray(emitted, dtype=bool)
    kn = np.asarray(known_faults, dtype=bool)
    if em.shape != kn.shape:
        raise ValueError("emitted and known_faults must have identical 2-D shapes")
    if buffer_px <= 0.0 or not kn.any():
        return em & ~kn
    dist_known = distance_transform_edt(~kn)
    return em & (dist_known > float(buffer_px))
