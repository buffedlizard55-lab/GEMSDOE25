"""H72 — Macro-Basin Contour-Parallel Piedmont Scarp & Concealed MT–Gravity–Swarm Damage
Corridor (``MBSP-MTG``) crossed with Training-Time Catalogue-Proximity Censoring (``DEBIAS``).

Pre-registered in ``knowledge/29_h72_cf_hypotheses_and_preregistration_2026-10-26.md``
(committed at ``2750fe9`` before feature implementation or fitting).

Design invariants:
* ``labels.tif`` and ``existing_faults.tif`` are NEVER read by the static sidecar builder.
* ``H72_contour_scarp_lidar`` preserves ``NaN`` where ``L_valid == 0`` so missing 3DEP
  1 m LiDAR tiles (e.g. 45.8% of ``NE``) are routed natively by ``HistGradientBoostingClassifier``
  rather than conflated with measured zero scarps (fixing ``IR-25-H38-REGIME-SPLIT``).
* All other five ``H72`` static columns are 100% finite inside the valid footprint.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter

from .features import LIDAR_BANDS, LIDAR_QUANT, dequantize, grad_mag, nearest_fill, ridge_strength
from .greedy import greedy_dots
from .h31 import candidates_flank_shielded
from .thinning import score_ordered_dots

H72_NAMES = [
    "H72_contour_scarp_lidar",
    "H72_contour_scarp_dem",
    "H72_grav_contour_scarp",
    "H72_mt_gouge_step",
    "H72_grav_vg_zero_step",
    "H72_transtension_swarm",
]

MACRO_DEM_SIGMA_PX = 25.0     # 2.5 km macro-basin horst/graben contour scale
MACRO_TENSOR_SIGMA_PX = 10.0  # 1.0 km structure-tensor smoothing for macro contours
MICRO_DEM_SIGMA_PX = 1.5      # 150 m micro-scarp scale
GRAV_CONTOUR_SIGMA_PX = 15.0  # 1.5 km regional basement density-margin scale
GRAV_TENSOR_SIGMA_PX = 6.0    # 600 m structure-tensor smoothing for gravity margin
MT_BG_SIGMA_PX = 20.0         # 2.0 km basin conductivity background scale

CENSOR_MIN_DIST_PX = 15.0     # 1.5 km short-range catalogue-proximity censoring floor
D1_POOL_KFRAC = 0.045
D1_FLANK_RADIUS_PX = 2.5
D1_TIP_PRESERVE_THR = 0.05
D1_MIN_SEP_PX = float(2.0 * np.sqrt(2.0))  # 2.828427 px (exact B2/D2.8 lattice spacing)
D1_NHAT_FRAC = 0.002456                    # ~12,691 / 5,167,373 live-calibrated prevalence
D1_TARGET_FRAC = 37654.0 / 5167373.0       # 37,654 full-footprint dot cap


def _nscale(arr: np.ndarray, foot: np.ndarray, p_lo: float = 1.0, p_hi: float = 99.0) -> np.ndarray:
    """Percentile-clip ``arr`` onto ``[0, 1]`` using finite values inside ``foot``."""
    v = np.asarray(arr, dtype=np.float32)
    vals = v[np.asarray(foot, dtype=bool) & np.isfinite(v)]
    if vals.size == 0:
        return np.zeros_like(v, dtype=np.float32)
    lo = float(np.percentile(vals, p_lo))
    hi = float(np.percentile(vals, p_hi))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return np.zeros_like(v, dtype=np.float32)
    return np.clip((np.nan_to_num(v, nan=lo) - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def contour_doubled_angle(
    field: np.ndarray,
    sigma_grad: float,
    sigma_tensor: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Doubled-angle unit vector ``(cos 2*theta, sin 2*theta)`` of level-set contours of ``field``.

    Convention matches ``gems25.features.build_addons`` (``x = col``, ``y = row``):
    a N–S striking scarp / contour (gradient purely along columns ``gx != 0, gy == 0``)
    has contour strike ``theta = pi/2`` -> ``(cos 2*theta, sin 2*theta) = (-1, 0)``;
    an E–W striking scarp / contour (gradient along rows ``gy != 0, gx == 0``) has
    ``theta = 0`` -> ``(+1, 0)``.
    """
    f = nearest_fill(np.asarray(field, dtype=np.float32))
    s = gaussian_filter(f, float(sigma_grad))
    gy, gx = np.gradient(s)
    jxx = gaussian_filter(gx * gx, float(sigma_tensor))
    jyy = gaussian_filter(gy * gy, float(sigma_tensor))
    jxy = gaussian_filter(gx * gy, float(sigma_tensor))
    phi2 = np.arctan2(2.0 * jxy, jxx - jyy)
    return (-np.cos(phi2)).astype(np.float32), (-np.sin(phi2)).astype(np.float32)


def hessian_ridge_doubled_angle(
    field: np.ndarray,
    sigma: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Tilt-invariant doubled-angle unit vector ``(cos 2*theta, sin 2*theta)`` of Hessian ridge axes.

    Unlike first-derivative ``grad(z)``, the second-derivative Hessian annihilates any background
    planar range-front slope ``a*x + b*y + c``, isolating the true strike of micro-scarps and
    canyon spurs on steep hillsides.
    """
    f = nearest_fill(np.asarray(field, dtype=np.float32))
    s = gaussian_filter(f, float(sigma))
    gy, gx = np.gradient(s)
    hyy, hyx = np.gradient(gy)
    hxy, hxx = np.gradient(gx)
    hxy = 0.5 * (hxy + hyx)
    psi2 = np.arctan2(-2.0 * hxy, (-hxx) - (-hyy))
    return (-np.cos(psi2)).astype(np.float32), (-np.sin(psi2)).astype(np.float32)


def lidar_strike_to_grid_doubled_angle(strike_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert 3DEP LiDAR ``strike`` (degrees in the grid ``(+col, +row)`` frame, identical to
    ``gems25.features.build_static`` ``L_strike_c2 = cos(2*th), L_strike_s2 = sin(2*th)``) into
    ``(cos 2*theta, sin 2*theta)``.

    Verified empirically against ``S_dem_c2, S_dem_s2`` across 336,523 coherent scarps
    (``mean(L_c2*D_c2 + L_s2*D_s2) = +0.3782``).
    """
    th2 = np.deg2rad(2.0 * np.asarray(strike_deg, dtype=np.float32))
    return np.cos(th2).astype(np.float32), np.sin(th2).astype(np.float32)


def compute_h72_grids(
    *,
    det_elev: np.ndarray,
    iso_grav: np.ndarray,
    iso_grav_slope: np.ndarray,
    iso_grav_vg: np.ndarray,
    cond_surf: np.ndarray,
    depth_to_base: np.ndarray,
    geod_shear: np.ndarray,
    geod_dilat: np.ndarray,
    deq: np.ndarray,
    ieq: np.ndarray,
    lidar_step_max: np.ndarray,
    lidar_coh100: np.ndarray,
    lidar_strike_deg: np.ndarray,
    lidar_valid: np.ndarray,
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute the 6 strictly catalogue-free ``H72`` feature grids."""
    foot = np.asarray(footprint, dtype=bool)
    z = nearest_fill(np.asarray(det_elev, dtype=np.float32))

    # 1-2. Macro-basin contour parallelism (2.5 km range-front contour vs 1m LiDAR & 100m DEM scarps)
    c_macro, s_macro = contour_doubled_angle(z, MACRO_DEM_SIGMA_PX, MACRO_TENSOR_SIGMA_PX)
    c_dem, s_dem = hessian_ridge_doubled_angle(z, MICRO_DEM_SIGMA_PX)
    dem_crest = _nscale(ridge_strength(z, MICRO_DEM_SIGMA_PX), foot)

    l_ok = np.isfinite(lidar_valid) & (lidar_valid > 0.5) & np.isfinite(lidar_strike_deg)
    c_lid, s_lid = lidar_strike_to_grid_doubled_angle(np.nan_to_num(lidar_strike_deg, nan=0.0))
    w_lid_raw = np.sqrt(np.clip(np.nan_to_num(lidar_step_max, nan=0.0), 0.0, None)) * np.clip(
        np.nan_to_num(lidar_coh100, nan=0.0), 0.0, 1.0
    )
    w_lid = _nscale(np.where(l_ok, w_lid_raw, np.nan), foot)
    cos2_lid_macro = np.clip(c_lid * c_macro + s_lid * s_macro, -1.0, 1.0)
    h72_lidar = np.where(l_ok, w_lid * cos2_lid_macro, np.nan).astype(np.float32)

    cos2_dem_macro = np.clip(c_dem * c_macro + s_dem * s_macro, -1.0, 1.0)
    h72_dem = (dem_crest * cos2_dem_macro).astype(np.float32)

    # 3. Subsurface 1.5 km isostatic-gravity margin strike concordance
    c_grav, s_grav = contour_doubled_angle(iso_grav, GRAV_CONTOUR_SIGMA_PX, GRAV_TENSOR_SIGMA_PX)
    grav_sl = _nscale(nearest_fill(iso_grav_slope), foot)
    use_lid = l_ok & (np.nan_to_num(lidar_coh100, nan=0.0) >= 0.25)
    c_mic = np.where(use_lid, c_lid, c_dem)
    s_mic = np.where(use_lid, s_lid, s_dem)
    scarp_amp = np.where(use_lid, w_lid, dem_crest)
    cos2_grav = np.clip(c_mic * c_grav + s_mic * s_grav, -1.0, 1.0)
    h72_grav_scarp = (grav_sl * scarp_amp * cos2_grav).astype(np.float32)

    # 4. Magnetotelluric smectite clay-gouge anomaly x conductive-base shoaling step
    cs = nearest_fill(np.asarray(cond_surf, dtype=np.float32))
    cond_hp = np.maximum(0.0, cs - gaussian_filter(cs, MT_BG_SIGMA_PX))
    db = nearest_fill(np.asarray(depth_to_base, dtype=np.float32))
    db_grad = grad_mag(np.log1p(np.maximum(db, 0.0)), 1.5)
    h72_mt_gouge = (_nscale(cond_hp, foot) * _nscale(db_grad, foot)).astype(np.float32)

    # 5. Vertical-gravity-gradient zero-crossing sharpness x gravity slope
    vg = gaussian_filter(nearest_fill(np.asarray(iso_grav_vg, dtype=np.float32)), 1.5)
    vg_vals = vg[foot]
    mad_vg = float(np.median(np.abs(vg_vals - np.median(vg_vals)))) if vg_vals.size else 1.0
    vg_sharp = grad_mag(vg, 1.0) / (np.abs(vg) + max(mad_vg, 1e-3))
    h72_vg_zero = (_nscale(vg_sharp, foot) * grav_sl).astype(np.float32)

    # 6. Kreemer & Young (2022) fluid-driven swarm excess x transtensional dilatational shear
    deq_f = np.maximum(nearest_fill(np.asarray(deq, dtype=np.float32)), 0.0)
    ieq_f = np.maximum(nearest_fill(np.asarray(ieq, dtype=np.float32)), 0.0)
    swarm_excess = np.maximum(0.0, np.log1p(deq_f) - np.log1p(ieq_f))
    sh_f = np.maximum(nearest_fill(np.asarray(geod_shear, dtype=np.float32)), 0.0)
    di_f = np.maximum(nearest_fill(np.asarray(geod_dilat, dtype=np.float32)), 0.0)
    transtens = np.sqrt(sh_f * di_f)
    h72_swarm = (_nscale(swarm_excess, foot) * _nscale(transtens, foot)).astype(np.float32)

    return {
        "H72_contour_scarp_lidar": h72_lidar,
        "H72_contour_scarp_dem": h72_dem,
        "H72_grav_contour_scarp": h72_grav_scarp,
        "H72_mt_gouge_step": h72_mt_gouge,
        "H72_grav_vg_zero_step": h72_vg_zero,
        "H72_transtension_swarm": h72_swarm,
    }


def build_h72_sidecar(
    band_dir: Path,
    external_dir: Path,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
    out_path: Path,
) -> list[str]:
    """Build ``(6, n_footprint)`` float32 sidecar + ``.names.json`` without reading any labels."""
    band_dir, external_dir, out_path = Path(band_dir), Path(external_dir), Path(out_path)
    foot = np.asarray(footprint, dtype=bool)
    fi = np.asarray(footprint_idx)

    with rasterio.open(external_dir / "lidar_scarp_features_u8.tif") as src:
        q = src.read()
    lid = {n: dequantize(q[i], *LIDAR_QUANT[n]) for i, n in enumerate(LIDAR_BANDS)}

    grids = compute_h72_grids(
        det_elev=np.load(band_dir / "12_det_elev.npy", mmap_mode="r"),
        iso_grav=np.load(band_dir / "13_iso_grav_anom.npy", mmap_mode="r"),
        iso_grav_slope=np.load(band_dir / "05_iso_grav_anom_slope.npy", mmap_mode="r"),
        iso_grav_vg=np.load(band_dir / "11_iso_grav_anom_vg.npy", mmap_mode="r"),
        cond_surf=np.load(band_dir / "17_cond_surf.npy", mmap_mode="r"),
        depth_to_base=np.load(band_dir / "15_depth_to_base_surf.npy", mmap_mode="r"),
        geod_shear=np.load(band_dir / "07_geod_shearrate.npy", mmap_mode="r"),
        geod_dilat=np.load(band_dir / "08_geod_dilaterate.npy", mmap_mode="r"),
        deq=np.load(band_dir / "10_deq_n100a15.npy", mmap_mode="r"),
        ieq=np.load(band_dir / "16_ieq_n100a15.npy", mmap_mode="r"),
        lidar_step_max=lid["step_max"],
        lidar_coh100=lid["coh100"],
        lidar_strike_deg=lid["strike"],
        lidar_valid=lid["valid"],
        footprint=foot,
    )
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(len(H72_NAMES), fi.size))
    for j, name in enumerate(H72_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if name != "H72_contour_scarp_lidar" and not np.isfinite(v).all():
            raise ValueError(f"H72 column {name} must be finite everywhere inside the footprint")
        if np.isinf(v).any():
            raise ValueError(f"H72 column {name} contains Inf")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H72_NAMES))
    return list(H72_NAMES)


def load_h72_sidecar(
    work: Path,
    external_dir: Path,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
) -> np.ndarray:
    """Load or build the cached ``work/h72_cf_sidecar.npy`` memmap."""
    work = Path(work)
    out = work / "h72_cf_sidecar.npy"
    names_file = Path(str(out) + ".names.json")
    fi = np.asarray(footprint_idx)
    if not out.exists() or not names_file.exists():
        build_h72_sidecar(work / "bands", external_dir, footprint, fi, out)
    names = json.loads(names_file.read_text())
    arr = np.load(out, mmap_mode="r")
    if names != H72_NAMES or arr.shape != (len(H72_NAMES), fi.size):
        build_h72_sidecar(work / "bands", external_dir, footprint, fi, out)
        arr = np.load(out, mmap_mode="r")
    return arr


def censor_catalogue_proximity(E: np.ndarray, min_dist_px: float = CENSOR_MIN_DIST_PX) -> np.ndarray:
    """Return a copy of ``Family E`` ``(7, N)`` with short-range proximity censored:
    * ``E[0]`` = ``log1p(max(expm1(E[0]), min_dist_px))`` (constant below ``min_dist_px``);
    * ``E[3]`` (``E_dens5``, 500 m fault density) = ``0.0``;
    * regional strike ``E[1:3]`` and meso/macro density & coherence ``E[4:7]`` preserved.
    """
    if E.ndim != 2 or E.shape[0] != 7:
        raise ValueError(f"Expected (7, N) Family E array, got {E.shape}")
    out = np.array(E, dtype=np.float32, copy=True)
    floor_val = float(np.log1p(float(min_dist_px)))
    out[0] = np.maximum(out[0], floor_val)
    out[3] = 0.0
    return out


def emit_debiased_b2_greedy(
    score_grid: np.ndarray,
    domain: np.ndarray,
    known: np.ndarray,
    tip_grid: np.ndarray,
    *,
    pool_kfrac: float = D1_POOL_KFRAC,
    flank_radius_px: float = D1_FLANK_RADIUS_PX,
    tip_preserve_threshold: float = D1_TIP_PRESERVE_THR,
    min_sep_px: float = D1_MIN_SEP_PX,
    n_hat_frac: float = D1_NHAT_FRAC,
    target_frac: float = D1_TARGET_FRAC,
) -> tuple[np.ndarray, dict]:
    """Frozen ``Factor D = +1`` emission (``knowledge/29`` §3.1):
    tip-preserved ``B2.5`` flank shield -> ``min_sep_px = 2*sqrt(2)`` spacing ->
    ``300 m`` lazy-greedy tent-credit selection capped at ``round(target_frac * |domain|)``.
    """
    dom = np.asarray(domain, dtype=bool)
    kn = np.asarray(known, dtype=bool)
    n_dom = int(dom.sum())
    k_pool = max(1, int(round(float(pool_kfrac) * n_dom)))
    max_dots = max(1, int(round(float(target_frac) * n_dom)))
    n_hat = max(1.0, float(n_hat_frac) * float(n_dom))

    s_clean, top_pool, shield_diag = candidates_flank_shielded(
        score_grid,
        dom,
        kn,
        tip_grid,
        k_pool,
        flank_radius_px=float(flank_radius_px),
        tip_preserve_threshold=float(tip_preserve_threshold),
    )
    spaced_pool = score_ordered_dots(s_clean, top_pool, float(min_sep_px))
    if not spaced_pool.any():
        return spaced_pool, dict(shield=shield_diag, spaced_pool=0, greedy=dict(n_selected=0))
    emitted, greedy_diag = greedy_dots(
        s_clean,
        spaced_pool,
        dom,
        kn,
        n_hat,
        max_dots=max_dots,
    )
    return emitted, dict(
        shield=shield_diag,
        spaced_pool=int(spaced_pool.sum()),
        max_dots=max_dots,
        greedy=greedy_diag,
    )
