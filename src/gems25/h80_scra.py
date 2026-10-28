"""H80 diagnostic operators and cover-adaptive fusion; NEGATIVE, not a geothermal model.

Scientific interpretation is withdrawn: mirrored tc is a magnetic derivative,
deq_n100a15 is described as distance, not earthquake rate, and K/Th/U
code-space ratios are not physical concentrations. Preserve the frozen numeric
operators for replay only; see knowledge/45_h80_outcome_2026-10-28.md.

Pre-registered in ``knowledge/44_preregistered_h80_scra_poe_2026-10-28.md`` (committed at ``69e6176``
before feature computation or model fitting).

Design invariants:
* Strictly static and Quaternary-catalogue-free: ``labels.tif``, ``existing_faults.tif``,
  ``gdr_qfaults_traces.csv``, and ``dist_known_fault_px`` are NEVER opened or referenced.
* All four ``H80_NAMES`` columns and two cover-regime vectors ``(c_cover, w_regime)`` are finite
  ``float32`` in ``[0, 1]`` across all ``5,167,373`` valid footprint pixels.
* Reuses ``gems25.features`` and ``gems25.h79_cthm`` primitives without duplicating shared helpers.
"""

from __future__ import annotations

import csv
import gc
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_erosion, gaussian_filter
from scipy.signal import fftconvolve

from .features import load_base, nearest_fill, ridge_strength
from .h74_rmps import pct_scale_eroded
from .h79_cthm import (
    WELLSPRING_ALLOWED_COLS,
    _elliptical_gaussian_kernel,
    _strike_director_doubled,
    _zscore_core,
    rank01_domain,
)

H80_NAMES = [
    "H80_suballuvial_mag_continuity",
    "H80_geotherm_disequilibrium_upflow",
    "H80_conserved_tc_rad_offset",
    "H80_halfgraben_rollover_hinge",
]

# Frozen SCRA-PoE constants (knowledge/44 §2.2)
SCRA_PRIMARY_PARAMS = dict(gamma_range=0.52, gamma_basin=0.86, floor_c=0.05, floor_m=0.10)
SCRA_DEEP_PARAMS = dict(gamma_range=0.66, gamma_basin=0.92, floor_c=0.05, floor_m=0.14)

DISALLOWED_COLUMNS = frozenset({"dist_known_fault_px", "existing_faults", "label"})


def compute_cover_regime_grids(
    base: dict[str, np.ndarray],
    footprint: np.ndarray,
    external_dir: Path,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Sedimentary-Basin Cover Index ``c(x)`` in ``[0, 1]`` and ``w_regime(x)`` in ``[0.65, 1.0]``."""
    foot = np.asarray(footprint, dtype=bool)
    z_base = nearest_fill(np.asarray(base["depth_to_base_surf"], dtype=np.float32))
    slope_deg = np.maximum(nearest_fill(np.asarray(base["det_elev_slope"], dtype=np.float32)), 0.0)

    lidar_tif = external_dir / "lidar_scarp_features_u8.tif"
    if lidar_tif.is_file():
        with rasterio.open(lidar_tif) as lsrc:
            l_valid = (lsrc.read(12) > 0).astype(np.float32)
    else:
        l_valid = np.ones(foot.shape, dtype=np.float32)

    c_depth = np.clip((z_base - 100.0) / 900.0, 0.0, 1.0).astype(np.float32)
    c_flat = np.exp(-slope_deg / 3.5).astype(np.float32)
    c_cover = np.clip(0.55 * c_depth + 0.35 * c_flat + 0.10 * (1.0 - l_valid), 0.0, 1.0).astype(np.float32)

    steep_cliff = np.clip((slope_deg - 8.0) / 12.0, 0.0, 1.0).astype(np.float32)
    w_regime = np.clip(1.0 - 0.35 * (1.0 - c_depth) * steep_cliff, 0.65, 1.0).astype(np.float32)

    c_cover = np.where(foot, c_cover, 0.0).astype(np.float32)
    w_regime = np.where(foot, w_regime, 1.0).astype(np.float32)
    return c_cover, w_regime


def fuse_scra_poe_scores(
    p_crustal: np.ndarray,
    p_morpho: np.ndarray,
    c_cover: np.ndarray,
    w_regime: np.ndarray,
    gamma_range: float = 0.52,
    gamma_basin: float = 0.86,
    floor_c: float = 0.05,
    floor_m: float = 0.10,
) -> np.ndarray:
    """Frozen Sedimentary-Cover Regime-Adaptive Product-of-Experts score in ``(0, 1]`` (knowledge/44 §2.2)."""
    arrays = [np.asarray(v) for v in (p_crustal, p_morpho, c_cover, w_regime)]
    if any(a.ndim != 1 or a.shape != arrays[0].shape for a in arrays):
        raise ValueError("fusion inputs must have identical 1-D shapes")
    if any(not np.isfinite(a).all() for a in arrays):
        raise ValueError("fusion inputs must be finite")
    params = (gamma_range, gamma_basin, floor_c, floor_m)
    if any(isinstance(v, bool) or not np.isfinite(v) or not 0 <= v <= 1 for v in params):
        raise ValueError("fusion parameters must be finite in [0,1]")
    rc = rank01_domain(p_crustal)
    rm = rank01_domain(p_morpho)
    cc = np.clip(np.asarray(c_cover, dtype=np.float32), 0.0, 1.0)
    wr = np.clip(np.asarray(w_regime, dtype=np.float32), 0.65, 1.0)
    if not (rc.shape == rm.shape == cc.shape == wr.shape):
        raise ValueError("p_crustal, p_morpho, c_cover, and w_regime must have identical 1-D shapes")

    gamma_x = float(gamma_range) + (float(gamma_basin) - float(gamma_range)) * cc
    tc = np.clip(float(floor_c) + (1.0 - float(floor_c)) * rc, 1e-6, 1.0)
    tm = np.clip(float(floor_m) + (1.0 - float(floor_m)) * rm, 1e-6, 1.0)
    out = wr * (tc ** gamma_x) * (tm ** (1.0 - gamma_x))
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def _load_disequilibrium_impulses(external_dir: Path, shape: tuple[int, int]) -> np.ndarray:
    """Historical supplied-channel contrasts; geothermcat interpretation is unverified. Label distance is ignored."""
    h, w = shape
    imp = np.zeros((h, w), dtype=np.float32)
    ws_csv = external_dir / "gdr_wellspring_in_footprint.csv"
    if not ws_csv.is_file():
        return imp

    allowed = frozenset({"row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"})
    assert allowed.issubset(WELLSPRING_ALLOWED_COLS)
    assert allowed.isdisjoint(DISALLOWED_COLUMNS)

    def _fval(row: dict[str, str], key: str) -> float:
        assert key in allowed
        raw = row.get(key, "")
        if not raw:
            return float("nan")
        try:
            v = float(raw)
            return v if np.isfinite(v) else float("nan")
        except ValueError:
            return float("nan")

    with ws_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r_f = _fval(row, "row")
            c_f = _fval(row, "col")
            if not (np.isfinite(r_f) and np.isfinite(c_f)):
                continue
            r, c = int(r_f), int(c_f)
            if not (0 <= r < h and 0 <= c < w):
                continue

            t_spr = _fval(row, "temp_c")
            t_qtz = _fval(row, "geothermquartz_c")
            t_cha = _fval(row, "geothermchalc_c")
            t_cat = _fval(row, "geothermcat_c")

            dt_cc = 0.0
            if np.isfinite(t_cat) and np.isfinite(t_cha):
                dt_cc = max(t_cat - t_cha, 0.0)

            t_res = max([v for v in (t_cat, t_qtz) if np.isfinite(v)], default=float("nan"))
            dt_up = 0.0
            if np.isfinite(t_res) and np.isfinite(t_spr):
                dt_up = max(t_res - t_spr, 0.0)
            elif np.isfinite(t_res) and t_res > 90.0:
                dt_up = max(t_res - 90.0, 0.0)

            w_imp = float(np.clip(dt_cc / 35.0, 0.0, 3.0) + 0.7 * np.clip(dt_up / 45.0, 0.0, 3.0))
            if w_imp > 0.0:
                imp[r, c] += w_imp

    return np.log1p(imp).astype(np.float32)


def compute_h80_grids(
    base: dict[str, np.ndarray],
    footprint: np.ndarray,
    external_dir: Path,
) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    """Compute the 4 frozen static H80 grids + ``(c_cover, w_regime)`` (knowledge/44 §2)."""
    foot = np.asarray(footprint, dtype=bool)
    if not foot.any():
        raise ValueError("footprint must contain at least one valid pixel")
    core = binary_erosion(foot, iterations=4)
    if not core.any():
        core = foot

    c_cover, w_regime = compute_cover_regime_grids(base, foot, external_dir)
    out: dict[str, np.ndarray] = {}

    # 1. H80_suballuvial_mag_continuity: shallow continuation residual ridge propagated across cover
    tmi = nearest_fill(np.asarray(base["tmi"], dtype=np.float32))
    tmi_hg = nearest_fill(np.asarray(base["tmi_hg"], dtype=np.float32))
    ext_tif = external_dir / "geodawn_extensions_u8.tif"
    if ext_tif.is_file():
        with rasterio.open(ext_tif) as esrc:
            up150_raw = esrc.read(4)
        up150_ok = up150_raw > 0
        up150_f = nearest_fill(np.where(up150_ok, up150_raw.astype(np.float32), np.nan))
        del up150_raw
        dz_shal = np.where(up150_ok, _zscore_core(tmi, core & up150_ok) - _zscore_core(up150_f, core & up150_ok), 0.0)
        del up150_f, up150_ok
    else:
        dz_shal = _zscore_core(tmi, core) - gaussian_filter(_zscore_core(tmi, core), 4.0)
    del tmi

    dz_sm = gaussian_filter(dz_shal.astype(np.float32), 1.2)
    gy_m, gx_m = np.gradient(dz_sm)
    grad_shal = np.hypot(gx_m, gy_m).astype(np.float32)
    del gy_m, gx_m, dz_sm

    hg_norm = pct_scale_eroded(np.log1p(np.maximum(tmi_hg, 0.0)), foot)
    del tmi_hg
    r_mag = pct_scale_eroded(ridge_strength(pct_scale_eroded(grad_shal, foot) + 0.5 * hg_norm, 1.5), foot)
    del grad_shal, hg_norm

    c2_m, s2_m, coh_m = _strike_director_doubled(dz_shal, sig_grad=1.5, sig_ten=3.0)
    del dz_shal
    p_num = np.zeros(foot.shape, dtype=np.float32)
    p_den = np.zeros(foot.shape, dtype=np.float32)
    for alpha_cw in (0.0, 45.0, 90.0, 135.0):
        a_rad = np.deg2rad(alpha_cw)
        tx, ty = np.sin(a_rad), -np.cos(a_rad)
        c2_k = float(tx * tx - ty * ty)
        s2_k = float(2.0 * tx * ty)
        kern = _elliptical_gaussian_kernel(14.0, 1.8, alpha_cw, truncate=3.0)
        resp = np.maximum(fftconvolve(r_mag, kern, mode="same").astype(np.float32), 0.0)
        align = np.maximum(0.0, 0.5 * (1.0 + c2_m * c2_k + s2_m * s2_k))
        wk = ((0.25 + 0.75 * coh_m) * (align * align) + 0.02).astype(np.float32)
        p_num += wk * resp
        p_den += wk
    p_axial = p_num / np.maximum(p_den, 1e-6)
    out["H80_suballuvial_mag_continuity"] = pct_scale_eroded(
        p_axial * (0.35 + 0.65 * c_cover),
        foot,
    )
    del r_mag, c2_m, s2_m, coh_m, p_num, p_den, p_axial
    gc.collect()

    # 2. Historical operator: undocumented geothermcat channel difference x log seismic-distance proxy x cond/tc.
    # NOT verified microseismicity, heatflow or geothermal upflow; values preserved for negative-screen replay.
    q_dis = _load_disequilibrium_impulses(external_dir, foot.shape)
    g_iso = nearest_fill(np.asarray(base["iso_grav_anom"], dtype=np.float32))
    z_base_f = nearest_fill(np.asarray(base["depth_to_base_surf"], dtype=np.float32))
    c2_g, s2_g, k_g = _strike_director_doubled(g_iso)
    c2_b, s2_b, k_b = _strike_director_doubled(z_base_f)
    del g_iso
    wt_gb = 0.55 * k_g + 0.45 * k_b + 1e-6
    c2_gb = ((0.55 * k_g * c2_g + 0.45 * k_b * c2_b) / wt_gb).astype(np.float32)
    s2_gb = ((0.55 * k_g * s2_g + 0.45 * k_b * s2_b) / wt_gb).astype(np.float32)
    n_gb = np.hypot(c2_gb, s2_gb) + 1e-6
    c2_gb /= n_gb
    s2_gb /= n_gb
    del c2_g, s2_g, k_g, c2_b, s2_b, k_b, wt_gb, n_gb

    d_num = np.zeros(foot.shape, dtype=np.float32)
    d_den = np.zeros(foot.shape, dtype=np.float32)
    for alpha_cw in (0.0, 45.0, 90.0, 135.0):
        a_rad = np.deg2rad(alpha_cw)
        tx, ty = np.sin(a_rad), -np.cos(a_rad)
        c2_k = float(tx * tx - ty * ty)
        s2_k = float(2.0 * tx * ty)
        kern = _elliptical_gaussian_kernel(16.0, 2.5, alpha_cw, truncate=3.0)
        resp = np.maximum(fftconvolve(q_dis, kern, mode="same").astype(np.float32), 0.0)
        align = np.maximum(0.0, 0.5 * (1.0 + c2_gb * c2_k + s2_gb * s2_k))
        wk = (align * align + 0.03).astype(np.float32)
        d_num += wk * resp
        d_den += wk
    plume_dis = pct_scale_eroded(np.log1p(12.0 * (d_num / np.maximum(d_den, 1e-6))), foot)
    del q_dis, c2_gb, s2_gb, d_num, d_den

    deq = np.log1p(np.maximum(nearest_fill(np.asarray(base["deq_n100a15"], dtype=np.float32)), 0.0))
    ieq = np.log1p(np.maximum(nearest_fill(np.asarray(base["ieq_n100a15"], dtype=np.float32)), 0.0))
    s_eq = pct_scale_eroded(deq + 0.5 * ieq, foot)
    del deq, ieq

    cond_p = pct_scale_eroded(
        np.log1p(np.maximum(nearest_fill(np.asarray(base["cond_surf"], dtype=np.float32)), 0.0)),
        foot,
    )
    tc_p = pct_scale_eroded(nearest_fill(np.asarray(base["tc"], dtype=np.float32)), foot)
    mt_tc = np.sqrt((0.25 + 0.75 * cond_p) * (0.25 + 0.75 * tc_p)).astype(np.float32)
    del cond_p, tc_p

    out["H80_geotherm_disequilibrium_upflow"] = pct_scale_eroded(
        (0.20 + 0.80 * plume_dis) * (0.30 + 0.70 * s_eq) * mt_tc,
        foot,
    )
    del plume_dis, s_eq, mt_tc
    gc.collect()

    # 3. H80_conserved_tc_rad_offset: TC-invariance-gated cross-edge ln(K/Th) & ln(U/Th) juxtaposition
    rad_tif = external_dir / "geodawn_rad_u8.tif"
    if rad_tif.is_file():
        with rasterio.open(rad_tif) as rsrc:
            k_u8 = rsrc.read(1)
            th_u8 = rsrc.read(2)
            u_u8 = rsrc.read(3)
            tc_u8 = rsrc.read(4)
        rad_ok = (k_u8 > 0) & (th_u8 > 0) & (tc_u8 > 0)
        k_f = nearest_fill(np.where(rad_ok, k_u8.astype(np.float32), np.nan))
        th_f = nearest_fill(np.where(rad_ok, th_u8.astype(np.float32), np.nan))
        u_f = nearest_fill(np.where(rad_ok, np.maximum(u_u8, 1).astype(np.float32), np.nan))
        tc_rad_f = nearest_fill(np.where(rad_ok, tc_u8.astype(np.float32), np.nan))
        del k_u8, th_u8, u_u8, tc_u8

        l_kth = gaussian_filter(np.log((k_f + 1.0) / (th_f + 1.0)).astype(np.float32), 1.5)
        l_uth = gaussian_filter(np.log((u_f + 1.0) / (th_f + 1.0)).astype(np.float32), 1.5)
        z_tc = gaussian_filter(_zscore_core(tc_rad_f, core & rad_ok), 1.5)
        del k_f, th_f, u_f, tc_rad_f

        gy1, gx1 = np.gradient(l_kth)
        gy2, gx2 = np.gradient(l_uth)
        gyt, gxt = np.gradient(z_tc)
        g_comp = np.sqrt(gx1 * gx1 + gy1 * gy1 + gx2 * gx2 + gy2 * gy2).astype(np.float32)
        g_tc = np.hypot(gxt, gyt).astype(np.float32)
        del l_kth, l_uth, z_tc, gy1, gx1, gy2, gx2, gyt, gxt

        valid_core_tc = g_tc[core & rad_ok]
        sig_tc = float(np.percentile(valid_core_tc, 65.0)) if valid_core_tc.size else 1.0
        sig_tc = max(sig_tc, 1e-4)
        w_tc = np.exp(-g_tc / sig_tc).astype(np.float32)
        rad_edge = np.where(rad_ok, ridge_strength((g_comp * w_tc).astype(np.float32), 1.5), 0.0)
        out["H80_conserved_tc_rad_offset"] = pct_scale_eroded(rad_edge, foot)
        del rad_ok, g_comp, g_tc, w_tc, rad_edge
    else:
        out["H80_conserved_tc_rad_offset"] = np.zeros(foot.shape, dtype=np.float32)
    gc.collect()

    # 4. H80_halfgraben_rollover_hinge: hanging-wall basement rollover curvature x master gravity flank x dilation
    zb_sm = gaussian_filter(z_base_f, 3.0)
    pos_curv = ridge_strength((-zb_sm).astype(np.float32), sigma=2.0)
    kappa_plus = np.where(zb_sm > 120.0, pos_curv, 0.0).astype(np.float32)
    del z_base_f, zb_sm, pos_curv

    ghg = pct_scale_eroded(nearest_fill(np.asarray(base["iso_grav_anom_hg"], dtype=np.float32)), foot)
    h_master = pct_scale_eroded(gaussian_filter(ghg, 25.0).astype(np.float32), foot)
    del ghg

    dil = nearest_fill(np.asarray(base["geod_dilaterate"], dtype=np.float32))
    d_plus = pct_scale_eroded(np.maximum(dil, 0.0), foot)
    del dil

    out["H80_halfgraben_rollover_hinge"] = pct_scale_eroded(
        pct_scale_eroded(kappa_plus, foot) * (0.25 + 0.75 * h_master) * (0.30 + 0.70 * d_plus),
        foot,
    )
    del kappa_plus, h_master, d_plus
    gc.collect()

    for nm in H80_NAMES:
        arr = out[nm]
        arr = np.where(foot, np.nan_to_num(arr, nan=0.0, posinf=1.0, neginf=0.0), 0.0).astype(np.float32)
        out[nm] = np.clip(arr, 0.0, 1.0)

    return out, c_cover, w_regime


def build_h80_sidecar(
    work: Path,
    external_dir: Path,
    force: bool = False,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build or load ``(4, N_foot)`` H80 sidecar and ``(2, N_foot)`` cover-regime sidecar."""
    feat_npy = work / "h80_scra_sidecar.npy"
    cov_npy = work / "h80_scra_cover.npy"
    meta_json = work / "h80_scra_sidecar.json"

    foot = np.load(work / "bands" / "_footprint.npy")
    fi = np.flatnonzero(foot.ravel())
    n_foot = int(fi.size)

    if not force and feat_npy.is_file() and cov_npy.is_file() and meta_json.is_file():
        meta = json.loads(meta_json.read_text())
        if meta.get("names") == H80_NAMES and meta.get("n_foot") == n_foot:
            feat_mm = np.load(feat_npy, mmap_mode="r")
            cov_mm = np.load(cov_npy, mmap_mode="r")
            if feat_mm.shape == (len(H80_NAMES), n_foot) and cov_mm.shape == (2, n_foot):
                return feat_mm, cov_mm, list(H80_NAMES)

    base = load_base(work / "bands")
    grids, c_cover, w_regime = compute_h80_grids(base, foot, external_dir)
    del base
    gc.collect()

    feat_mat = np.empty((len(H80_NAMES), n_foot), dtype=np.float32)
    for idx, nm in enumerate(H80_NAMES):
        feat_mat[idx] = grids[nm].ravel()[fi]
    cov_mat = np.empty((2, n_foot), dtype=np.float32)
    cov_mat[0] = c_cover.ravel()[fi]
    cov_mat[1] = w_regime.ravel()[fi]
    del grids, c_cover, w_regime
    gc.collect()

    np.save(feat_npy, feat_mat)
    np.save(cov_npy, cov_mat)
    meta_json.write_text(
        json.dumps(
            dict(
                names=H80_NAMES,
                cover_names=["c_cover", "w_regime"],
                n_foot=n_foot,
                scra_primary_params=SCRA_PRIMARY_PARAMS,
                scra_deep_params=SCRA_DEEP_PARAMS,
            ),
            indent=2,
        )
        + "\n"
    )
    return np.load(feat_npy, mmap_mode="r"), np.load(cov_npy, mmap_mode="r"), list(H80_NAMES)
