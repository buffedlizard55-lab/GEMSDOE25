"""H72 — Untried multi-physics sidecars for pre-registered H72 experiments (knowledge/29).

Strictly static and label-free: neither ``labels.tif`` nor ``existing_faults.tif`` nor any
label-derived CSV column (``dist_known_fault_px`` / ``gdr_qfaults_traces.csv``) is ever read.

Block 1 (`H72_PTTG_NAMES`, Rank #1 in `knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md`):
  * ``PTTG_grav_diffcurv``      — Multi-scale (sigma = 2.0, 5.0 px = 200, 500 m) geometric
    persistence of Phillips (2007) / Roberts (2001) isotropic differential horizontal gravity
    curvature ``K_diff(g) = sqrt((g_xx - g_yy)^2 + 4 * g_xy^2)`` from ``13_iso_grav_anom``.
    Rotationally invariant across all fault strikes (0-180 deg), fixing band 18's E-W
    directional blindness (r = +0.9484 with dg/dx) to WNW-ESE / E-W transfer faults.
  * ``PTTG_grav_thdr_unit``     — Unit-consistent (mGal/km horizontal vs mGal/km vertical)
    isotropic gravity tilt horizontal derivative ``|grad_h arctan2(V_g, 10 * |grad_h g|)|``,
    capturing depth-normalized intrabasinal density-contact crests regardless of throw magnitude.
  * ``PTTG_transtension_loc``   — Dimensionless kinematic dilatation obliquity
    ``max(dil, 0) / hypot(shear, dil)`` weighted by 25 km background-demeaned strain-rate
    intensity ``[log1p(I2) - mean_25km(log1p(I2))]_+``, isolating local pull-apart / relay-ramp
    transtensional anomalies without quadrant-scale Walker Lane non-stationarity.
  * ``PTTG_concealed_transfer`` — Cover-masked basement-to-conductivity transfer index combining
    unit-consistent magnetic THDR (``nT/km``), gravity THDR (``mGal/km``), MT conductivity
    gradient ``|grad_h log1p(cond_surf)|``, and low surface slope ``1 - 0.7 * norm(det_elev_slope)``.

Block 2 (`H72_VCCD_NAMES`, Rank #2 in `knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md`):
  * ``VCCD_subcover_flex``      — Surficial volcanic-cap + closed-playa cover-opacity mask
    ``O_cover`` interacted with 1 km upward-continued gravity gradient and MT basement flexure.
  * ``VCCD_volc_clutter_veto``  — Volcanic short-wavelength RTP lava-flow edge clutter proxy
    ``O_volc * norm(|grad_h RTP|)`` allowing trees to discount non-tectonic volcanic flow margins.
  * ``RBDT_throw_dipole``       — Hanks (2000) 3DEP 1 m asymmetric scarp throw polarity
    ``|L_downface - L_upface| / (L_downface + L_upface + 0.02)`` times crest-toe curvature
    dipole ``sqrt(norm(L_lapneg) * norm(L_lappos)) * L_coh100`` (suppressing two-bank gullies).
  * ``RBDT_non_shoreline_scarp``— Pluvial Lake Lahontan / Bonneville constant-contour veto:
    ``L_step_max * L_coh100 * |s_strike . grad_hat_500m(det_elev)|``, isolating cross-contour
    tectonic scarps against wave-cut shorelines that follow horizontal elevation contours.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import (
    binary_erosion,
    distance_transform_edt,
    gaussian_filter,
    uniform_filter,
)

from .features import LIDAR_BANDS, LIDAR_QUANT, dequantize, grad_mag, load_base, nearest_fill
from .h34 import upward_continue_multi

H72_PTTG_NAMES = [
    "PTTG_grav_diffcurv",
    "PTTG_grav_thdr_unit",
    "PTTG_transtension_loc",
    "PTTG_concealed_transfer",
]

H72_VCCD_NAMES = [
    "VCCD_subcover_flex",
    "VCCD_volc_clutter_veto",
    "RBDT_throw_dipole",
    "RBDT_non_shoreline_scarp",
]


def _pct_scale_eroded(arr: np.ndarray, foot: np.ndarray, erode_px: int = 4) -> np.ndarray:
    """Scale finite footprint values to [0, 1] using 1st-99th percentiles on eroded interior."""
    foot_b = np.asarray(foot, dtype=bool)
    core = binary_erosion(foot_b, iterations=erode_px) if erode_px > 0 else foot_b
    if not core.any():
        core = foot_b
    vals = np.asarray(arr, dtype=np.float32)
    sample = vals[core & np.isfinite(vals)]
    if sample.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    lo, hi = np.percentile(sample, [1.0, 99.0])
    if not np.isfinite(hi) or hi <= lo:
        return np.zeros(arr.shape, dtype=np.float32)
    out = np.clip((vals - float(lo)) / float(hi - lo), 0.0, 1.0)
    return np.where(foot_b & np.isfinite(vals), out, 0.0).astype(np.float32)


def phillips_diff_curvature(field: np.ndarray, sigma_px: float) -> np.ndarray:
    """Isotropic 2D differential horizontal curvature sqrt((f_xx - f_yy)^2 + 4 * f_xy^2)."""
    s = gaussian_filter(np.asarray(field, dtype=np.float32), float(sigma_px))
    gy, gx = np.gradient(s)
    gyy, gyx = np.gradient(gy)
    gxy, gxx = np.gradient(gx)
    hxy = 0.5 * (gxy + gyx)
    diff = gxx - gyy
    return np.sqrt(diff * diff + 4.0 * hxy * hxy).astype(np.float32)


def unit_consistent_thdr(
    potential_field: np.ndarray,
    vertical_grad: np.ndarray,
    horiz_to_vert_scale: float,
    vert_scale: float = 1.0,
    smooth_sigma: float = 1.5,
    eps: float = 1e-3,
) -> np.ndarray:
    """Total Horizontal Derivative of unit-matched tilt angle |grad_h arctan2(V, H)|."""
    s = gaussian_filter(np.asarray(potential_field, dtype=np.float32), float(smooth_sigma))
    gy, gx = np.gradient(s)
    horiz = float(horiz_to_vert_scale) * np.hypot(gx, gy)
    vert = float(vert_scale) * gaussian_filter(np.asarray(vertical_grad, dtype=np.float32), 1.0)
    tilt = np.arctan2(vert, horiz + float(eps)).astype(np.float32)
    ty, tx = np.gradient(gaussian_filter(tilt, 1.0))
    return np.hypot(tx, ty).astype(np.float32)


def compute_pttg_grids(base: dict[str, np.ndarray], footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Compute the 4 static `H72_PTTG_NAMES` full-grid float32 arrays (0 outside footprint)."""
    foot = np.asarray(footprint, dtype=bool)
    if not foot.any():
        raise ValueError("empty footprint")

    g = nearest_fill(np.asarray(base["iso_grav_anom"], dtype=np.float32))
    gvg = nearest_fill(np.asarray(base["iso_grav_anom_vg"], dtype=np.float32))

    # 1. Multi-scale Phillips differential horizontal curvature persistence (200 m x 500 m)
    k2 = _pct_scale_eroded(phillips_diff_curvature(g, 2.0), foot)
    k5 = _pct_scale_eroded(phillips_diff_curvature(g, 5.0), foot)
    grav_diffcurv = np.sqrt(k2 * k5).astype(np.float32)
    del k2, k5

    # 2. Unit-consistent isotropic gravity THDR (10 * mGal/100m == mGal/km, matching band 11)
    thdr_g_raw = unit_consistent_thdr(g, gvg, horiz_to_vert_scale=10.0, vert_scale=1.0, smooth_sigma=1.5, eps=1e-3)
    grav_thdr = _pct_scale_eroded(thdr_g_raw, foot)
    del g, gvg, thdr_g_raw

    # 3. Local 25 km demeaned kinematic transtensional strain-partitioning anomaly
    dil = nearest_fill(np.asarray(base["geod_dilaterate"], dtype=np.float32))
    shr = np.maximum(nearest_fill(np.asarray(base["geod_shearrate"], dtype=np.float32)), 0.0)
    inv2 = np.maximum(nearest_fill(np.asarray(base["geod_2ndinv"], dtype=np.float32)), 0.0)
    obliq_ext = np.maximum(dil, 0.0) / (np.hypot(shr, dil) + 1e-6)
    log_i2 = np.log1p(inv2).astype(np.float32)
    bg_i2 = uniform_filter(log_i2, size=251)
    loc_i2 = _pct_scale_eroded(np.maximum(log_i2 - bg_i2, 0.0), foot)
    transtension_loc = np.where(foot, obliq_ext * loc_i2, 0.0).astype(np.float32)
    del dil, shr, inv2, obliq_ext, log_i2, bg_i2, loc_i2

    # 4. Cover-masked basement-to-conductivity transfer coupling (unit-consistent nT/km & mGal/km)
    tmi = nearest_fill(np.asarray(base["tmi"], dtype=np.float32))
    tvg = nearest_fill(np.asarray(base["tmi_vg"], dtype=np.float32))
    # 10 * nT/100m = nT/km; 1000 * nT/m = nT/km
    thdr_m = _pct_scale_eroded(
        unit_consistent_thdr(tmi, tvg, horiz_to_vert_scale=10.0, vert_scale=1000.0, smooth_sigma=1.5, eps=0.1),
        foot,
    )
    del tmi, tvg
    cond = np.log1p(np.maximum(nearest_fill(np.asarray(base["cond_surf"], dtype=np.float32)), 0.0))
    cond_edge = _pct_scale_eroded(grad_mag(cond, 1.5), foot)
    del cond
    slope = _pct_scale_eroded(nearest_fill(np.asarray(base["det_elev_slope"], dtype=np.float32)), foot)
    cover_flat = (1.0 - 0.70 * slope).astype(np.float32)
    concealed_transfer = np.where(
        foot,
        np.cbrt(grav_thdr * thdr_m * cond_edge) * cover_flat,
        0.0,
    ).astype(np.float32)
    del thdr_m, cond_edge, slope, cover_flat

    return {
        "PTTG_grav_diffcurv": np.nan_to_num(grav_diffcurv, nan=0.0, posinf=0.0, neginf=0.0),
        "PTTG_grav_thdr_unit": np.nan_to_num(grav_thdr, nan=0.0, posinf=0.0, neginf=0.0),
        "PTTG_transtension_loc": np.nan_to_num(transtension_loc, nan=0.0, posinf=0.0, neginf=0.0),
        "PTTG_concealed_transfer": np.nan_to_num(concealed_transfer, nan=0.0, posinf=0.0, neginf=0.0),
    }


def load_h72_pttg_sidecar(work: Path, fi: np.ndarray) -> np.ndarray:
    """Build or open cached ``(4, n_footprint)`` float32 memmap for `H72_PTTG_NAMES`."""
    out_path = work / "h72_pttg.npy"
    meta_path = work / "h72_pttg.names.json"
    if out_path.exists() and meta_path.exists():
        names = json.loads(meta_path.read_text())
        if names == H72_PTTG_NAMES:
            mm = np.load(out_path, mmap_mode="r")
            if mm.shape == (len(H72_PTTG_NAMES), fi.size):
                return mm

    foot = np.load(work / "bands" / "_footprint.npy")
    base = load_base(work / "bands")
    grids = compute_pttg_grids(base, foot)
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(len(H72_PTTG_NAMES), fi.size))
    for i, nm in enumerate(H72_PTTG_NAMES):
        mm[i] = grids[nm].ravel()[fi]
    mm.flush()
    meta_path.write_text(json.dumps(H72_PTTG_NAMES) + "\n")
    return np.load(out_path, mmap_mode="r")


def compute_vccd_grids(
    base: dict[str, np.ndarray],
    external_dir: Path,
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute the 4 static `H72_VCCD_NAMES` full-grid float32 arrays (0 outside footprint).

    Strictly reads only ``row`` and ``col`` from ``gdr_volcanic_vents_in_footprint.csv``;
    ``dist_known_fault_px`` is never accessed.
    """
    foot = np.asarray(footprint, dtype=bool)
    shape = foot.shape

    # Quaternary vent proximity (label-free coordinates only)
    vents_csv = external_dir / "gdr_volcanic_vents_in_footprint.csv"
    vent_mask = np.zeros(shape, dtype=bool)
    if vents_csv.exists():
        df = pd.read_csv(vents_csv, usecols=["row", "col"])
        valid_rc = (df["row"] >= 0) & (df["row"] < shape[0]) & (df["col"] >= 0) & (df["col"] < shape[1])
        vent_mask[df.loc[valid_rc, "row"].to_numpy(int), df.loc[valid_rc, "col"].to_numpy(int)] = True
    vent_prox = np.exp(-distance_transform_edt(~vent_mask) / 80.0).astype(np.float32) if vent_mask.any() else np.zeros(shape, np.float32)

    # Short-wavelength RTP volcanic texture roughness + 400 m residual
    rtp = nearest_fill(np.asarray(base["rtp"], dtype=np.float32))
    rtp_up400 = upward_continue_multi(rtp, (400.0,))[0].astype(np.float32)
    rtp_hi = rtp - rtp_up400
    mean_hi = uniform_filter(rtp_hi, size=9)
    var_hi = np.maximum(uniform_filter(rtp_hi * rtp_hi, size=9) - mean_hi * mean_hi, 0.0)
    volc_rough = _pct_scale_eroded(np.sqrt(var_hi), foot)
    o_volc = np.clip(volc_rough * (0.5 + 0.5 * vent_prox), 0.0, 1.0).astype(np.float32)
    rtp_grad = _pct_scale_eroded(grad_mag(rtp, 1.0), foot)
    volc_clutter_veto = np.where(foot, o_volc * rtp_grad, 0.0).astype(np.float32)
    del rtp, rtp_up400, rtp_hi, mean_hi, var_hi, volc_rough, vent_prox, rtp_grad

    # Closed-basin playa opacity: flat slope + negative TPI + high shallow MT conductance
    z = nearest_fill(np.asarray(base["det_elev"], dtype=np.float32))
    tpi11 = z - uniform_filter(z, size=11)
    slope_n = _pct_scale_eroded(nearest_fill(np.asarray(base["det_elev_slope"], dtype=np.float32)), foot)
    cond_n = _pct_scale_eroded(
        np.log1p(np.maximum(nearest_fill(np.asarray(base["cond_surf"], dtype=np.float32)), 0.0)),
        foot,
    )
    playa_opac = (1.0 - slope_n) * _pct_scale_eroded(np.maximum(-tpi11, 0.0), foot) * cond_n
    o_cover = np.clip(np.maximum(o_volc, playa_opac), 0.0, 1.0).astype(np.float32)
    del tpi11, slope_n, cond_n, playa_opac, o_volc

    # Deep 1 km upward-continued gravity gradient + MT basement-depth flexure gated by cover opacity
    g = nearest_fill(np.asarray(base["iso_grav_anom"], dtype=np.float32))
    g_up1000 = upward_continue_multi(g, (1000.0,))[0].astype(np.float32)
    deep_grav = _pct_scale_eroded(grad_mag(g_up1000, 1.5), foot)
    del g, g_up1000
    db = np.log1p(np.maximum(nearest_fill(np.asarray(base["depth_to_base_surf"], dtype=np.float32)), 0.0))
    db_flex = _pct_scale_eroded(grad_mag(db, 1.5), foot)
    del db
    subcover_flex = np.where(foot, o_cover * np.sqrt(deep_grav * db_flex), 0.0).astype(np.float32)
    del o_cover, deep_grav, db_flex

    # 3DEP 1 m LiDAR asymmetric scarp dipole + pluvial shoreline constant-contour veto
    with rasterio.open(external_dir / "lidar_scarp_features_u8.tif") as src:
        q = src.read()
    lid = {n: dequantize(q[i], *LIDAR_QUANT[n]) for i, n in enumerate(LIDAR_BANDS)}
    del q
    l_valid = (np.nan_to_num(lid["valid"], nan=0.0) > 0.5) & foot
    downf = np.nan_to_num(lid["downface_max"], nan=0.0)
    upf = np.nan_to_num(lid["upface_max"], nan=0.0)
    asym = np.abs(downf - upf) / (downf + upf + 0.02)
    lapn = _pct_scale_eroded(np.nan_to_num(lid["lapneg_max"], nan=0.0), l_valid, erode_px=0)
    lapp = _pct_scale_eroded(np.nan_to_num(lid["lappos_max"], nan=0.0), l_valid, erode_px=0)
    coh = np.clip(np.nan_to_num(lid["coh100"], nan=0.0), 0.0, 1.0)
    throw_dipole = np.where(l_valid, asym * np.sqrt(lapn * lapp) * coh, 0.0).astype(np.float32)

    # Strike azimuth clockwise from North: east = sin(az), north = -cos(az) (row increases south)
    strike_rad = np.deg2rad(np.nan_to_num(lid["strike"], nan=0.0))
    sx = np.sin(strike_rad).astype(np.float32)
    sy = (-np.cos(strike_rad)).astype(np.float32)
    z500 = gaussian_filter(z, 5.0)
    zy, zx = np.gradient(z500)
    zmag = np.hypot(zx, zy) + 1e-4
    # Along-strike elevation change |s . grad_hat(z500)|: ~0 on horizontal pluvial shorelines
    cross_contour = np.abs(sx * (zx / zmag) + sy * (zy / zmag))
    step_n = _pct_scale_eroded(np.nan_to_num(lid["step_max"], nan=0.0), l_valid, erode_px=0)
    non_shoreline = np.where(l_valid, step_n * coh * cross_contour, 0.0).astype(np.float32)

    return {
        "VCCD_subcover_flex": np.nan_to_num(subcover_flex, nan=0.0, posinf=0.0, neginf=0.0),
        "VCCD_volc_clutter_veto": np.nan_to_num(volc_clutter_veto, nan=0.0, posinf=0.0, neginf=0.0),
        "RBDT_throw_dipole": np.nan_to_num(throw_dipole, nan=0.0, posinf=0.0, neginf=0.0),
        "RBDT_non_shoreline_scarp": np.nan_to_num(non_shoreline, nan=0.0, posinf=0.0, neginf=0.0),
    }


def load_h72_vccd_sidecar(work: Path, ext_dir: Path, fi: np.ndarray) -> np.ndarray:
    """Build or open cached ``(4, n_footprint)`` float32 memmap for `H72_VCCD_NAMES`."""
    out_path = work / "h72_vccd.npy"
    meta_path = work / "h72_vccd.names.json"
    if out_path.exists() and meta_path.exists():
        names = json.loads(meta_path.read_text())
        if names == H72_VCCD_NAMES:
            mm = np.load(out_path, mmap_mode="r")
            if mm.shape == (len(H72_VCCD_NAMES), fi.size):
                return mm

    foot = np.load(work / "bands" / "_footprint.npy")
    base = load_base(work / "bands")
    grids = compute_vccd_grids(base, ext_dir, foot)
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(len(H72_VCCD_NAMES), fi.size))
    for i, nm in enumerate(H72_VCCD_NAMES):
        mm[i] = grids[nm].ravel()[fi]
    mm.flush()
    meta_path.write_text(json.dumps(H72_VCCD_NAMES) + "\n")
    return np.load(out_path, mmap_mode="r")
