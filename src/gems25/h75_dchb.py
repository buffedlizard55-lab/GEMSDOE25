"""H75-1 (DCHB-CG) static hydrogeologic/transtensional/contact sidecar & Corridor-Gated Dual-Regime coupling.

Pre-registered in ``knowledge/38_preregistered_h75_dchb_cg_2026-10-27.md`` (committed at ``12931bb``
before feature construction, holdout fitting, or raster generation).

Design invariants:
  * ``labels.tif``, ``existing_faults.tif``, ``gdr_qfaults_traces.csv``, and ``derived_sgmc_faults_100m_u8.tif``
    are NEVER opened or read anywhere in this module.
  * ``dist_known_fault_px`` in ``gdr_wellspring_in_footprint.csv`` is strictly forbidden via an explicit
    column allowlist plus runtime ``ValueError`` guard.
  * All 5 static ``H75_DCHB_NAMES`` columns are finite ``float32`` in ``[0, 1]`` over the ``5,167,373``
    footprint vector ``fi`` (``0.0`` outside ``footprint``).
  * ``combine_corridor_gated_scores`` implements the frozen ``gamma = 0.60`` subsurface-corridor x
    shoreline-deconfounded trace geometric coupling with monotone empirical quantile calibration
    (``gap_scale = 0.95``) across the ``24.66%`` ``L_valid == 0`` 3DEP LiDAR coverage gap.
"""

from __future__ import annotations

import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import binary_erosion, gaussian_filter

from .features import LIDAR_BANDS, LIDAR_QUANT, dequantize, grad_mag, nearest_fill, ridge_strength
from .h72_cf import (
    MACRO_DEM_SIGMA_PX,
    MACRO_TENSOR_SIGMA_PX,
    MICRO_DEM_SIGMA_PX,
    contour_doubled_angle,
    hessian_ridge_doubled_angle,
    lidar_strike_to_grid_doubled_angle,
)
from .paths import data_dir

H75_DCHB_NAMES: list[str] = [
    "H75_darcy_seepage_barrier",
    "H75_uth_sinter_emergence",
    "H75_oblique_piedmont_inflection",
    "H75_riedel_obliquity_shear",
    "H75_destriped_blakely_contact",
]

H75_CORRIDOR_SUBSET: list[str] = [
    "H75_darcy_seepage_barrier",
    "H75_uth_sinter_emergence",
    "H75_destriped_blakely_contact",
]

GDR_QUARTZ_ALLOWED_COLS: tuple[str, ...] = (
    "row",
    "col",
    "layer",
    "thermalclass",
    "temp_c",
    "geothermquartz_c",
)

DARCY_HEAD_SIGMA_PX: float = 30.0      # 3.0 km smoothed piezometric water-table head surface
DARCY_AQUITARD_SIGMA_PX: float = 2.0   # 200 m fault-core conductivity / basement step scale
QUARTZ_UPFLOW_SIGMA_PX: float = 12.0   # 1.2 km silica-enthalpy hydrothermal upflow halo
RIEDEL_DELTA_DEG: float = 17.0         # Byerlee (phi ~ 34 deg) R-shear angle: +-17 deg (2*delta = +-34 deg)
GRAV_CORRIDOR_SIGMA_PX: float = 15.0   # 1.5 km subsurface basement corridor scale
GRAV_CORRIDOR_TENSOR_PX: float = 6.0   # 600 m structure-tensor smoothing

CORRIDOR_GAMMA_DEFAULT: float = 0.60
LIDAR_GAP_SCALE_DEFAULT: float = 0.95


def pct_clip01(arr: np.ndarray, mask: np.ndarray, p_lo: float = 1.0, p_hi: float = 99.0) -> np.ndarray:
    """Percentile-normalize ``arr`` onto ``[0, 1]`` using finite values inside ``mask``."""
    a = np.asarray(arr, dtype=np.float32)
    m = np.asarray(mask, dtype=bool) & np.isfinite(a)
    out = np.zeros(a.shape, dtype=np.float32)
    if not m.any():
        return out
    vals = a[m]
    lo, hi = np.percentile(vals, [p_lo, p_hi])
    span = float(hi - lo)
    if not np.isfinite(span) or span <= 1e-12:
        mx = float(vals.max())
        mn = float(vals.min())
        if mx > mn + 1e-12:
            lo, span = mn, mx - mn
        else:
            return out
    fin = np.isfinite(a)
    out[fin] = np.clip((a[fin] - float(lo)) / float(span), 0.0, 1.0)
    return out


def destripe_ew_flightlines(field: np.ndarray, sigma_ns: float = 2.0, sigma_ew: float = 14.0) -> np.ndarray:
    """Suppress 200-400 m E-W (090 deg) aeromagnetic tie-line corrugation (Glen & Earney, 2024)."""
    f = nearest_fill(np.asarray(field, dtype=np.float32))
    ns_high = f - gaussian_filter(f, sigma=(float(sigma_ns), 0.0), mode="nearest")
    ew_stripes = gaussian_filter(ns_high, sigma=(0.0, float(sigma_ew)), mode="nearest")
    return (f - ew_stripes).astype(np.float32)


def compute_quartz_upflow_halo(df: pd.DataFrame, footprint: np.ndarray) -> np.ndarray:
    """Compute 1.2 km hydrothermal quartz-enthalpy excess grid from GDR 1391 without label columns."""
    if "dist_known_fault_px" in df.columns:
        raise ValueError("dist_known_fault_px is label-derived and forbidden in H75 builders")
    foot = np.asarray(footprint, dtype=bool)
    H, W = foot.shape
    if df.empty:
        return np.zeros((H, W), dtype=np.float32)
    sub = df[(df["row"] >= 0) & (df["row"] < H) & (df["col"] >= 0) & (df["col"] < W)].copy()
    if sub.empty:
        return np.zeros((H, W), dtype=np.float32)

    rows = sub["row"].to_numpy(dtype=np.int64)
    cols = sub["col"].to_numpy(dtype=np.int64)
    layer_s = sub["layer"].fillna("").astype(str)
    is_spring = layer_s.str.startswith("spring_").to_numpy()
    w_spring = np.where(is_spring, 1.5, 1.0).astype(np.float32)

    t_meas = pd.to_numeric(sub["temp_c"], errors="coerce").to_numpy(dtype=np.float64)
    t_qtz = pd.to_numeric(sub["geothermquartz_c"], errors="coerce").to_numpy(dtype=np.float64)
    t_best = np.fmax(t_qtz, t_meas)
    ok = np.isfinite(t_best)
    if not ok.any():
        return np.zeros((H, W), dtype=np.float32)

    dt = np.clip(t_best[ok] - 15.0, 0.0, 220.0).astype(np.float32) * w_spring[ok]
    imp = np.zeros((H, W), dtype=np.float32)
    np.maximum.at(imp, (rows[ok], cols[ok]), dt)
    sm = gaussian_filter(imp, float(QUARTZ_UPFLOW_SIGMA_PX), mode="constant", cval=0.0)
    peak_unit = float(1.0 / (2.0 * np.pi * float(QUARTZ_UPFLOW_SIGMA_PX) ** 2))
    halo = np.log1p(np.maximum(sm / max(peak_unit, 1e-12), 0.0)).astype(np.float32)
    return np.where(foot, halo, 0.0).astype(np.float32)


def compute_h75_dchb_grids(
    *,
    det_elev: np.ndarray,
    cond_surf: np.ndarray,
    depth_to_base: np.ndarray,
    rtp: np.ndarray,
    iso_grav: np.ndarray,
    geod_shear: np.ndarray,
    rad_th_u8: np.ndarray,
    ext_uth_u8: np.ndarray,
    ext_up150_u8: np.ndarray,
    lidar_step_max: np.ndarray,
    lidar_coh100: np.ndarray,
    lidar_strike_deg: np.ndarray,
    lidar_valid: np.ndarray,
    wellspring_df: pd.DataFrame,
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute the 5 strictly catalogue-free ``H75_DCHB`` static grids in ``[0, 1]``."""
    foot = np.asarray(footprint, dtype=bool)
    core = binary_erosion(foot, iterations=4)
    norm_mask = core if core.any() else foot

    z = nearest_fill(np.asarray(det_elev, dtype=np.float32))
    cond_log = np.log1p(np.maximum(nearest_fill(np.asarray(cond_surf, dtype=np.float32)), 0.0))
    base_log = np.log1p(np.maximum(nearest_fill(np.asarray(depth_to_base, dtype=np.float32)), 0.0))

    # 1. H75_darcy_seepage_barrier: directed 3 km Darcy flow impinging on smectite gouge / basement step
    hw = gaussian_filter(z, DARCY_HEAD_SIGMA_PX)
    ghw_y, ghw_x = np.gradient(hw)
    ghw_mag = np.hypot(ghw_x, ghw_y)
    uw_y = -ghw_y / (ghw_mag + 1e-5)
    uw_x = -ghw_x / (ghw_mag + 1e-5)
    gw_n = pct_clip01(ghw_mag, norm_mask)

    cs_sm = gaussian_filter(cond_log, DARCY_AQUITARD_SIGMA_PX)
    gc_y, gc_x = np.gradient(cs_sm)
    gc_mag = np.hypot(gc_x, gc_y)

    bs_sm = gaussian_filter(base_log, DARCY_AQUITARD_SIGMA_PX)
    gb_y, gb_x = np.gradient(bs_sm)
    gb_mag = np.hypot(gb_x, gb_y)

    impinge_c = np.maximum(0.0, uw_x * gc_x + uw_y * gc_y)
    impinge_b = np.abs(uw_x * gb_x + uw_y * gb_y)
    impinge_n = pct_clip01(impinge_c + 0.5 * impinge_b, norm_mask)
    step_pair = np.sqrt(pct_clip01(gc_mag, norm_mask) * pct_clip01(gb_mag, norm_mask) + 1e-4)
    darcy_raw = (gw_n * impinge_n * step_pair).astype(np.float32)
    h75_darcy = np.where(foot, pct_clip01(ridge_strength(darcy_raw, 1.5), norm_mask), 0.0).astype(np.float32)
    del hw, ghw_y, ghw_x, ghw_mag, uw_y, uw_x, cs_sm, gc_y, gc_x, bs_sm, gb_y, gb_x, darcy_raw

    # 2. H75_uth_sinter_emergence: authigenic carbonate/sinter U/Th ridge x quartz-enthalpy upflow
    uth_f = nearest_fill(np.where(ext_uth_u8 > 0, ext_uth_u8.astype(np.float32), np.nan))
    th_f = nearest_fill(np.where(rad_th_u8 > 0, rad_th_u8.astype(np.float32), np.nan))
    auth_uth = pct_clip01(uth_f, norm_mask) * (1.0 - 0.5 * pct_clip01(th_f, norm_mask))
    r_uth = pct_clip01(ridge_strength(auth_uth.astype(np.float32), 1.5), norm_mask)
    q_up = pct_clip01(compute_quartz_upflow_halo(wellspring_df, foot), norm_mask)
    hydro_gate = 0.30 + 0.70 * np.sqrt(np.clip(pct_clip01(q_up + 0.5 * h75_darcy, norm_mask), 0.0, 1.0))
    h75_uth = np.where(foot, pct_clip01(r_uth * hydro_gate, norm_mask), 0.0).astype(np.float32)
    del uth_f, th_f, auth_uth, r_uth, q_up, hydro_gate

    # 3. H75_oblique_piedmont_inflection: cross-contour sin^2(theta_mic - theta_mac) shoreline deconfounder
    c_mac, s_mac = contour_doubled_angle(z, MACRO_DEM_SIGMA_PX, MACRO_TENSOR_SIGMA_PX)
    c_dem, s_dem = hessian_ridge_doubled_angle(z, MICRO_DEM_SIGMA_PX)
    w_dem = pct_clip01(ridge_strength(z, MICRO_DEM_SIGMA_PX), norm_mask)

    l_ok = np.isfinite(lidar_valid) & (lidar_valid > 0.5) & np.isfinite(lidar_strike_deg)
    c_lid, s_lid = lidar_strike_to_grid_doubled_angle(np.nan_to_num(lidar_strike_deg, nan=0.0))
    w_lid_raw = np.sqrt(np.clip(np.nan_to_num(lidar_step_max, nan=0.0), 0.0, None)) * np.clip(
        np.nan_to_num(lidar_coh100, nan=0.0), 0.0, 1.0
    )
    w_lid = pct_clip01(np.where(l_ok, w_lid_raw, np.nan), norm_mask)
    use_lid = l_ok & (np.nan_to_num(lidar_coh100, nan=0.0) >= 0.20)
    c_mic = np.where(use_lid, c_lid, c_dem).astype(np.float32)
    s_mic = np.where(use_lid, s_lid, s_dem).astype(np.float32)
    w_mic = np.where(l_ok, 0.65 * w_lid + 0.35 * w_dem, w_dem).astype(np.float32)

    cos_2delta_mac = np.clip(c_mic * c_mac + s_mic * s_mac, -1.0, 1.0)
    sin2_oblique = 0.5 * (1.0 - cos_2delta_mac)
    w_pied = 0.25 + 0.75 * pct_clip01(base_log, norm_mask)
    h75_oblique = np.where(foot, pct_clip01(w_mic * sin2_oblique * w_pied, norm_mask), 0.0).astype(np.float32)
    del c_mac, s_mac, c_dem, s_dem, c_lid, s_lid, cos_2delta_mac, sin2_oblique, w_pied

    # 4. H75_riedel_obliquity_shear: +-17 deg Byerlee Riedel R-shear resonance along basement corridors
    g_iso = nearest_fill(np.asarray(iso_grav, dtype=np.float32))
    c_cor, s_cor = contour_doubled_angle(g_iso, GRAV_CORRIDOR_SIGMA_PX, GRAV_CORRIDOR_TENSOR_PX)
    ang2 = float(np.deg2rad(2.0 * RIEDEL_DELTA_DEG))
    ca, sa = float(np.cos(ang2)), float(np.sin(ang2))
    c_plus = c_cor * ca - s_cor * sa
    s_plus = s_cor * ca + c_cor * sa
    c_minus = c_cor * ca + s_cor * sa
    s_minus = s_cor * ca - c_cor * sa
    res_plus = 0.5 * (1.0 + np.clip(c_mic * c_plus + s_mic * s_plus, -1.0, 1.0))
    res_minus = 0.5 * (1.0 + np.clip(c_mic * c_minus + s_mic * s_minus, -1.0, 1.0))
    r_17 = np.maximum(res_plus, res_minus)
    sh_n = pct_clip01(np.maximum(nearest_fill(np.asarray(geod_shear, dtype=np.float32)), 0.0), norm_mask)
    h75_riedel = np.where(foot, pct_clip01(w_mic * r_17 * (0.20 + 0.80 * sh_n), norm_mask), 0.0).astype(np.float32)
    del c_cor, s_cor, c_plus, s_plus, c_minus, s_minus, res_plus, res_minus, r_17, sh_n, c_mic, s_mic, w_mic

    # 5. H75_destriped_blakely_contact: E-W flight-line-destriped Blakely-Simpson contact spine
    rtp_ds = destripe_ew_flightlines(rtp, sigma_ns=2.0, sigma_ew=14.0)
    up150_raw = np.where(ext_up150_u8 > 0, ext_up150_u8.astype(np.float32), np.nan)
    up150_ds = destripe_ew_flightlines(up150_raw, sigma_ns=2.0, sigma_ew=14.0)

    c_mag = pct_clip01(ridge_strength(grad_mag(rtp_ds, 1.5), 1.2), norm_mask)
    c_up = pct_clip01(ridge_strength(grad_mag(up150_ds, 2.0), 1.2), norm_mask)
    c_grav = pct_clip01(ridge_strength(grad_mag(g_iso, 2.0), 1.5), norm_mask)
    blakely_raw = np.sqrt(c_mag * c_up) * (0.35 + 0.65 * c_grav)
    h75_blakely = np.where(foot, pct_clip01(blakely_raw, norm_mask), 0.0).astype(np.float32)

    out = {
        "H75_darcy_seepage_barrier": h75_darcy,
        "H75_uth_sinter_emergence": h75_uth,
        "H75_oblique_piedmont_inflection": h75_oblique,
        "H75_riedel_obliquity_shear": h75_riedel,
        "H75_destriped_blakely_contact": h75_blakely,
    }
    for name, arr in out.items():
        if not np.isfinite(arr).all():
            raise ValueError(f"{name} contains non-finite values")
        if (arr[foot] < 0.0).any() or (arr[foot] > 1.0).any():
            raise ValueError(f"{name} values outside [0, 1] inside footprint")
    return out


def build_h75_dchb_sidecar(
    band_dir: Path,
    external_dir: Path,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
    out_path: Path,
) -> list[str]:
    """Build ``(5, n_footprint)`` float32 memmap + ``.names.json`` without touching any label file."""
    band_dir, external_dir, out_path = Path(band_dir), Path(external_dir), Path(out_path)
    foot = np.asarray(footprint, dtype=bool)
    fi = np.asarray(footprint_idx, dtype=np.int64)

    with rasterio.open(external_dir / "lidar_scarp_features_u8.tif") as ds:
        lid_q = ds.read()
    bidx = {n: i for i, n in enumerate(LIDAR_BANDS)}
    lid_step = dequantize(lid_q[bidx["step_max"]], *LIDAR_QUANT["step_max"])
    lid_coh = dequantize(lid_q[bidx["coh100"]], *LIDAR_QUANT["coh100"])
    lid_strike = dequantize(lid_q[bidx["strike"]], *LIDAR_QUANT["strike"])
    lid_valid = dequantize(lid_q[bidx["valid"]], *LIDAR_QUANT["valid"])
    del lid_q

    with rasterio.open(external_dir / "geodawn_rad_u8.tif") as ds:
        rad_th_u8 = ds.read(2)  # ('K', 'Th', 'U', 'TC')
    with rasterio.open(external_dir / "geodawn_extensions_u8.tif") as ds:
        ext_uth_u8 = ds.read(3)    # ('ThK', 'UK', 'UTh', 'TMI_up150')
        ext_up150_u8 = ds.read(4)

    ws_df = pd.read_csv(
        external_dir / "gdr_wellspring_in_footprint.csv",
        usecols=list(GDR_QUARTZ_ALLOWED_COLS),
    )

    grids = compute_h75_dchb_grids(
        det_elev=np.load(band_dir / "12_det_elev.npy", mmap_mode="r"),
        cond_surf=np.load(band_dir / "17_cond_surf.npy", mmap_mode="r"),
        depth_to_base=np.load(band_dir / "15_depth_to_base_surf.npy", mmap_mode="r"),
        rtp=np.load(band_dir / "02_rtp.npy", mmap_mode="r"),
        iso_grav=np.load(band_dir / "13_iso_grav_anom.npy", mmap_mode="r"),
        geod_shear=np.load(band_dir / "07_geod_shearrate.npy", mmap_mode="r"),
        rad_th_u8=rad_th_u8,
        ext_uth_u8=ext_uth_u8,
        ext_up150_u8=ext_up150_u8,
        lidar_step_max=lid_step,
        lidar_coh100=lid_coh,
        lidar_strike_deg=lid_strike,
        lidar_valid=lid_valid,
        wellspring_df=ws_df,
        footprint=foot,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(
        out_path, mode="w+", dtype=np.float32, shape=(len(H75_DCHB_NAMES), fi.size)
    )
    for j, name in enumerate(H75_DCHB_NAMES):
        mm[j] = grids[name].ravel()[fi]
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H75_DCHB_NAMES) + "\n")
    del grids
    gc.collect()
    return list(H75_DCHB_NAMES)


def load_h75_dchb_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load or build ``h75_dchb_columns.npy`` inside ``work`` without altering pinned caches."""
    work = Path(work)
    path = work / "h75_dchb_columns.npy"
    names_path = Path(str(path) + ".names.json")
    if not path.exists() or not names_path.exists():
        foot = np.load(work / "bands" / "_footprint.npy")
        build_h75_dchb_sidecar(work / "bands", data_dir() / "external", foot, footprint_idx, path)
    names = json.loads(names_path.read_text())
    arr = np.load(path, mmap_mode="r")
    if names != H75_DCHB_NAMES or arr.shape != (len(H75_DCHB_NAMES), len(footprint_idx)):
        raise ValueError(f"H75 DCHB sidecar mismatch: {names=} {arr.shape=}")
    return arr


def combine_corridor_gated_scores(
    p_corridor: np.ndarray,
    p_trace: np.ndarray,
    p_gap: np.ndarray,
    lidar_valid: np.ndarray,
    *,
    gamma: float = CORRIDOR_GAMMA_DEFAULT,
    gap_scale: float = LIDAR_GAP_SCALE_DEFAULT,
) -> np.ndarray:
    """Frozen Corridor-Gated Dual-Regime coupling across ``L_valid == 1`` and ``L_valid == 0``.

    * On ``L_valid == 1``: ``U_1(x) = p_corridor(x)^gamma * p_trace(x)^(1 - gamma)``.
    * On ``L_valid == 0``: ``U_0(x) = p_corridor(x)^gamma * p_gap(x)^(1 - gamma)``, mapped
      monotonically via empirical quantile matching onto ``gap_scale * Q_{U_1}(rank(U_0(x)))``.
    """
    p_cor = np.clip(np.nan_to_num(np.asarray(p_corridor, dtype=np.float64), nan=0.0), 0.0, 1.0)
    p_tr = np.clip(np.nan_to_num(np.asarray(p_trace, dtype=np.float64), nan=0.0), 0.0, 1.0)
    p_gp = np.clip(np.nan_to_num(np.asarray(p_gap, dtype=np.float64), nan=0.0), 0.0, 1.0)
    lv = np.asarray(lidar_valid, dtype=bool)
    if not (p_cor.shape == p_tr.shape == p_gp.shape == lv.shape) or p_cor.ndim != 1:
        raise ValueError("p_corridor, p_trace, p_gap, and lidar_valid must be aligned 1-D vectors")
    if not (0.0 <= gamma <= 1.0) or not (0.0 < gap_scale <= 1.0):
        raise ValueError("gamma must lie in [0, 1] and gap_scale in (0, 1]")

    u1 = np.power(p_cor, gamma) * np.power(p_tr, 1.0 - gamma)
    u0 = np.power(p_cor, gamma) * np.power(p_gp, 1.0 - gamma)

    out = np.empty(p_cor.shape, dtype=np.float32)
    if lv.all() or not (~lv).any():
        return np.clip(u1, 0.0, 1.0).astype(np.float32)
    if not lv.any():
        return np.clip(gap_scale * u0, 0.0, 1.0).astype(np.float32)

    out[lv] = np.clip(u1[lv], 0.0, 1.0).astype(np.float32)
    ref_sorted = np.sort(u1[lv])
    u0_gap = u0[~lv]
    n_gap = u0_gap.size
    order = np.argsort(u0_gap, kind="mergesort")
    ranks = np.empty(n_gap, dtype=np.float64)
    denom = max(n_gap - 1, 1)
    ranks[order] = np.arange(n_gap, dtype=np.float64) / float(denom)
    q_idx = ranks * float(ref_sorted.size - 1)
    lo_idx = np.floor(q_idx).astype(np.int64)
    hi_idx = np.minimum(lo_idx + 1, ref_sorted.size - 1)
    frac = q_idx - lo_idx
    mapped = gap_scale * ((1.0 - frac) * ref_sorted[lo_idx] + frac * ref_sorted[hi_idx])
    out[~lv] = np.clip(mapped, 0.0, 1.0).astype(np.float32)
    return out


def estimate_blind_n_hat(
    known_c: np.ndarray,
    dom_c: np.ndarray,
    *,
    visible_train: np.ndarray | None = None,
    train_region: np.ndarray | None = None,
    hide_frac: float = 0.20,
    floor: float = 100.0,
) -> float:
    """Leakage-free truth-mass estimate ``n_hat`` for ``greedy_dots`` across holdout geometries.

    * Component/tile-sampled splits (``Holdout``, ``draw_block25km``): ``(known_c & dom_c).sum() > 0``,
      so ``(hide_frac / (1 - hide_frac)) * |(known_c & dom_c)|`` estimates the ``hide_frac`` hidden mass.
    * Full-block-hidden splits (``BlockHoldout``): ``100%`` of catalogue faults in ``dom_c`` are hidden
      (``|(known_c & dom_c)| == 0``), so we estimate total catalogue prevalence strictly from
      ``visible_train`` inside ``train_region`` (where ``1 - hide_frac`` of faults remain visible)
      and multiply by ``|dom_c|``—zero access to ``hidden_test`` or ``hidden_train``.
    """
    kc = np.asarray(known_c, dtype=bool)
    dc = np.asarray(dom_c, dtype=bool)
    n_vis_dom = int((kc & dc).sum())
    if n_vis_dom > 0:
        ratio = float(hide_frac) / max(1.0 - float(hide_frac), 1e-6)
        return float(max(ratio * float(n_vis_dom), floor))
    if visible_train is not None and train_region is not None:
        vt = np.asarray(visible_train, dtype=bool)
        tr = np.asarray(train_region, dtype=bool)
        denom = max((1.0 - float(hide_frac)) * float(tr.sum()), 1.0)
        rho_cat = float((vt & tr).sum()) / denom
        return float(max(rho_cat * float(dc.sum()), floor))
    return float(floor)
