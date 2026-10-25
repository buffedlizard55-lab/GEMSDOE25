"""H66-1 (Masked Geothermometry Disequilibrium & Efimov Potassic-Metasomatism F-Ridge)
and H66-2 (Neotectonically Reactivated SGMC Bedrock Faults) static sidecars.

Pre-registered in `knowledge/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md`.
All columns in this module are strictly catalogue-free:
  * `labels.tif` / `existing_faults.tif` are NEVER read;
  * `dist_known_fault_px` in `gdr_wellspring_in_footprint.csv` is NEVER loaded (`usecols` allowlist);
  * All outputs are finite `float32` in `[0, 1]` over the footprint index vector `fi`.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter

from .features import grad_mag, nearest_fill, ridge_strength

H66_MGD_NAMES = [
    "H66_mgd_cat_excess",
    "H66_mgd_chalc_excess",
    "H66_spring_upflow_prox",
    "H66_efimov_f_ridge",
]

H66_SGMC_NAMES = [
    "H66_sgmc_prox4",
    "H66_sgmc_scarp_compat",
    "H66_sgmc_strain_react",
]

GDR_ALLOWED_COLS = [
    "layer",
    "thermalclass",
    "row",
    "col",
    "temp_c",
    "geothermchalc_c",
    "geothermcat_c",
]

OUTFLOW_SIGMA_PX = 15.0  # 1.5 km lateral outflow plume kernel
UPFLOW_DECAY_PX = 20.0   # 2.0 km fault-damage seepage scale
SGMC_DECAY_PX = 4.0      # 400 m positional uncertainty of 1:250k-1:500k SGMC compilation


def pct_scale_footprint(grid: np.ndarray, foot: np.ndarray, p_lo: float = 1.0, p_hi: float = 99.0) -> np.ndarray:
    """Scale finite positive/continuous footprint values to [0, 1] using (p_lo, p_hi) percentiles."""
    foot_b = np.asarray(foot, dtype=bool)
    vals = np.asarray(grid, dtype=np.float32)
    fin = foot_b & np.isfinite(vals)
    out = np.zeros(foot_b.shape, dtype=np.float32)
    if not fin.any():
        return out
    sample = vals[fin]
    nz = sample[sample > 0]
    ref = nz if nz.size >= 100 else sample
    lo = float(np.percentile(ref, p_lo)) if nz.size < 100 else 0.0
    hi = float(np.percentile(ref, p_hi))
    if not np.isfinite(hi) or hi <= lo:
        mx = float(sample.max())
        if mx > lo:
            hi = mx
        else:
            return out
    out[fin] = np.clip((vals[fin] - lo) / (hi - lo), 0.0, 1.0)
    return out


def _peak_normalized_gaussian(impulse_grid: np.ndarray, sigma_px: float) -> np.ndarray:
    """Gaussian-smooth sparse impulse maxima and divide by unit-impulse peak `(1 / (2*pi*sigma^2))`."""
    sm = gaussian_filter(np.asarray(impulse_grid, dtype=np.float32), float(sigma_px), mode="constant", cval=0.0)
    peak_unit = float(1.0 / (2.0 * np.pi * float(sigma_px) ** 2))
    return (sm / max(peak_unit, 1e-12)).astype(np.float32)


def compute_mgd_wellspring_grids(
    df: pd.DataFrame,
    foot: np.ndarray,
    *,
    outflow_sigma_px: float = OUTFLOW_SIGMA_PX,
    upflow_decay_px: float = UPFLOW_DECAY_PX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build `(mgd_cat_excess, mgd_chalc_excess, spring_upflow_prox)` grids in `[0, 1]` from GDR table."""
    if "dist_known_fault_px" in df.columns:
        raise ValueError("dist_known_fault_px is label-derived and must never be passed to H66 builders")
    foot_b = np.asarray(foot, dtype=bool)
    H, W = foot_b.shape
    sub = df[(df["row"] >= 0) & (df["row"] < H) & (df["col"] >= 0) & (df["col"] < W)].copy()
    if sub.empty:
        z = np.zeros((H, W), dtype=np.float32)
        return z, z.copy(), z.copy()

    rows = sub["row"].to_numpy(dtype=np.int64)
    cols = sub["col"].to_numpy(dtype=np.int64)
    layer_s = sub["layer"].fillna("").astype(str)
    is_spring = layer_s.str.startswith("spring_").to_numpy()
    w_spring = np.where(is_spring, 1.5, 1.0).astype(np.float32)

    temp = pd.to_numeric(sub["temp_c"], errors="coerce").to_numpy(dtype=np.float64)
    t_cat = pd.to_numeric(sub["geothermcat_c"], errors="coerce").to_numpy(dtype=np.float64)
    t_chalc = pd.to_numeric(sub["geothermchalc_c"], errors="coerce").to_numpy(dtype=np.float64)

    # 1. Cation (Na-K-Ca) masked reservoir disequilibrium
    ok_cat = np.isfinite(temp) & np.isfinite(t_cat)
    exc_cat = np.clip(t_cat[ok_cat] - temp[ok_cat], 0.0, 180.0).astype(np.float32) * w_spring[ok_cat]
    cat_imp = np.zeros((H, W), dtype=np.float32)
    if exc_cat.size:
        np.maximum.at(cat_imp, (rows[ok_cat], cols[ok_cat]), exc_cat)
    cat_field = np.log1p(np.maximum(_peak_normalized_gaussian(cat_imp, outflow_sigma_px), 0.0))
    cat_norm = pct_scale_footprint(cat_field, foot_b)

    # 2. Chalcedony masked reservoir disequilibrium
    ok_ch = np.isfinite(temp) & np.isfinite(t_chalc)
    exc_ch = np.clip(t_chalc[ok_ch] - temp[ok_ch], 0.0, 150.0).astype(np.float32) * w_spring[ok_ch]
    ch_imp = np.zeros((H, W), dtype=np.float32)
    if exc_ch.size:
        np.maximum.at(ch_imp, (rows[ok_ch], cols[ok_ch]), exc_ch)
    ch_field = np.log1p(np.maximum(_peak_normalized_gaussian(ch_imp, outflow_sigma_px), 0.0))
    ch_norm = pct_scale_footprint(ch_field, foot_b)

    # 3. Natural spring seepage U {Hot, Warm} upflow proximity
    tclass = sub["thermalclass"].fillna("").astype(str).str.strip()
    is_upflow = is_spring | tclass.isin(["Hot", "Warm"]).to_numpy()
    up_mask = np.zeros((H, W), dtype=bool)
    if is_upflow.any():
        up_mask[rows[is_upflow], cols[is_upflow]] = True
    up_mask &= foot_b
    if up_mask.any():
        dist_up = distance_transform_edt(~up_mask).astype(np.float32)
        up_prox = np.where(foot_b, np.exp(-dist_up / float(upflow_decay_px)), 0.0).astype(np.float32)
    else:
        up_prox = np.zeros((H, W), dtype=np.float32)

    return cat_norm, ch_norm, up_prox


def compute_efimov_f_ridge(
    k_u8: np.ndarray,
    tc_u8: np.ndarray,
    uth_u8: np.ndarray,
    foot: np.ndarray,
) -> np.ndarray:
    """Efimov (1978) potassic-metasomatism F-parameter across-strike ridge modulated by |grad(TC)|."""
    foot_b = np.asarray(foot, dtype=bool)
    k_f = nearest_fill(np.where(np.asarray(k_u8) > 0, np.asarray(k_u8, dtype=np.float32) / 255.0, np.nan))
    uth_f = nearest_fill(np.where(np.asarray(uth_u8) > 0, np.asarray(uth_u8, dtype=np.float32) / 255.0, np.nan))
    tc_f = nearest_fill(np.where(np.asarray(tc_u8) > 0, np.asarray(tc_u8, dtype=np.float32) / 255.0, np.nan))

    f_idx = (k_f * uth_f).astype(np.float32)
    f_ridge = ridge_strength(f_idx, 2.0)
    tc_grad_norm = pct_scale_footprint(grad_mag(tc_f, 1.5), foot_b)
    raw = f_ridge * (0.5 + 0.5 * tc_grad_norm)
    return pct_scale_footprint(raw, foot_b)


def build_h66_mgd_sidecar(external_dir: Path, foot: np.ndarray, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    """Build `(4, n_footprint)` float32 sidecar for H66-1 (`MGD-F`)."""
    external_dir = Path(external_dir)
    foot_b = np.asarray(foot, dtype=bool)
    fi = np.asarray(footprint_idx, dtype=np.int64)

    df = pd.read_csv(external_dir / "gdr_wellspring_in_footprint.csv", usecols=GDR_ALLOWED_COLS)
    cat_g, ch_g, up_g = compute_mgd_wellspring_grids(df, foot_b)
    del df

    with rasterio.open(external_dir / "geodawn_rad_u8.tif") as s:
        k_u8 = s.read(1)
        tc_u8 = s.read(4)
    with rasterio.open(external_dir / "geodawn_extensions_u8.tif") as s:
        uth_u8 = s.read(3)
    ef_g = compute_efimov_f_ridge(k_u8, tc_u8, uth_u8, foot_b)
    del k_u8, tc_u8, uth_u8

    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32, shape=(len(H66_MGD_NAMES), fi.size))
    for j, (name, g) in enumerate(zip(H66_MGD_NAMES, (cat_g, ch_g, up_g, ef_g), strict=True)):
        v = np.asarray(g, dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all() or (v < 0.0).any() or (v > 1.0).any():
            raise ValueError(f"{name} has invalid values outside finite [0, 1]")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H66_MGD_NAMES))
    return list(H66_MGD_NAMES)


def load_h66_mgd_sidecar(work: Path, external_dir: Path, foot: np.ndarray, footprint_idx: np.ndarray) -> np.ndarray:
    """Load `(4, n_footprint)` H66-1 sidecar from `work_dir()`, building once if absent."""
    work = Path(work)
    path = work / "h66_mgd_columns.npy"
    if not path.exists():
        build_h66_mgd_sidecar(external_dir, foot, footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H66_MGD_NAMES or arr.shape != (len(H66_MGD_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"H66 MGD sidecar mismatch: names={names} shape={arr.shape}")
    return arr


def compute_sgmc_reactivation_grids(
    sgmc_u8: np.ndarray,
    foot: np.ndarray,
    l_c2_foot: np.ndarray,
    l_s2_foot: np.ndarray,
    l_coh_foot: np.ndarray,
    l_step_foot: np.ndarray,
    geod_2ndinv_grid: np.ndarray,
    iso_grav_grid: np.ndarray,
    footprint_idx: np.ndarray,
    *,
    decay_px: float = SGMC_DECAY_PX,
) -> np.ndarray:
    """Compute `(3, n_footprint)` float32 SGMC reactivation vectors strictly without label inputs."""
    foot_b = np.asarray(foot, dtype=bool)
    fi = np.asarray(footprint_idx, dtype=np.int64)
    sgmc_b = (np.asarray(sgmc_u8) > 0) & foot_b
    out = np.zeros((3, fi.size), dtype=np.float32)
    if not sgmc_b.any() or fi.size == 0:
        return out

    dist, (iy, ix) = distance_transform_edt(~sgmc_b, return_indices=True)
    prox_fi = np.exp(-dist.ravel()[fi].astype(np.float32) / float(decay_px)).astype(np.float32)
    out[0] = np.clip(prox_fi, 0.0, 1.0)
    del dist

    # Doubled-angle tangent orientation of SGMC bedrock traces (same convention as family E / L_strike)
    sm = gaussian_filter(sgmc_b.astype(np.float32), 2.0)
    gy, gx = np.gradient(sm)
    jxx = gaussian_filter(gx * gx, 2.0)
    jyy = gaussian_filter(gy * gy, 2.0)
    jxy = gaussian_filter(gx * gy, 2.0)
    phi2 = np.arctan2(2.0 * jxy, jxx - jyy)
    sgmc_c2 = (-np.cos(phi2)).astype(np.float32)
    sgmc_s2 = (-np.sin(phi2)).astype(np.float32)
    del sm, gy, gx, jxx, jyy, jxy, phi2

    H, W = foot_b.shape
    near_flat = iy.ravel()[fi].astype(np.int64) * W + ix.ravel()[fi].astype(np.int64)
    del iy, ix
    near_c2 = sgmc_c2.ravel()[near_flat]
    near_s2 = sgmc_s2.ravel()[near_flat]
    del sgmc_c2, sgmc_s2, near_flat

    lc2 = np.nan_to_num(np.asarray(l_c2_foot, dtype=np.float32), nan=0.0)
    ls2 = np.nan_to_num(np.asarray(l_s2_foot, dtype=np.float32), nan=0.0)
    lcoh = np.clip(np.nan_to_num(np.asarray(l_coh_foot, dtype=np.float32), nan=0.0), 0.0, 1.0)
    lstep_raw = np.nan_to_num(np.asarray(l_step_foot, dtype=np.float32), nan=0.0)
    s_lo, s_hi = float(np.percentile(lstep_raw, 1.0)), float(np.percentile(lstep_raw, 99.0))
    lstep_norm = np.clip((lstep_raw - max(s_lo, 0.0)) / max(s_hi - max(s_lo, 0.0), 1e-6), 0.0, 1.0).astype(np.float32)

    strike_align = np.maximum(0.0, np.clip(near_c2 * lc2 + near_s2 * ls2, -1.0, 1.0)).astype(np.float32)
    out[1] = np.clip(prox_fi * strike_align * lcoh * lstep_norm, 0.0, 1.0)

    strain_norm = pct_scale_footprint(nearest_fill(np.asarray(geod_2ndinv_grid, dtype=np.float32)), foot_b).ravel()[fi]
    grav_grad_norm = pct_scale_footprint(
        grad_mag(nearest_fill(np.asarray(iso_grav_grid, dtype=np.float32)), 1.5), foot_b
    ).ravel()[fi]
    out[2] = np.clip(prox_fi * np.sqrt(np.maximum(strain_norm * grav_grad_norm, 0.0)), 0.0, 1.0).astype(np.float32)
    return out


def build_h66_sgmc_sidecar(
    work: Path,
    external_dir: Path,
    static: np.ndarray,
    static_names: list[str],
    foot: np.ndarray,
    footprint_idx: np.ndarray,
    out_path: Path,
) -> list[str]:
    """Build `(3, n_footprint)` float32 sidecar for H66-2 (`SGMC-REACT`)."""
    work = Path(work)
    external_dir = Path(external_dir)
    fi = np.asarray(footprint_idx, dtype=np.int64)
    with rasterio.open(external_dir / "derived_sgmc_faults_100m_u8.tif") as s:
        sgmc_u8 = s.read(1)

    geod_2nd = np.load(work / "bands" / "10_geod_2ndinv.npy")
    iso_grav = np.load(work / "bands" / "13_iso_grav_anom.npy")
    vecs = compute_sgmc_reactivation_grids(
        sgmc_u8=sgmc_u8,
        foot=foot,
        l_c2_foot=np.asarray(static[static_names.index("L_strike_c2")]),
        l_s2_foot=np.asarray(static[static_names.index("L_strike_s2")]),
        l_coh_foot=np.asarray(static[static_names.index("L_coh100")]),
        l_step_foot=np.asarray(static[static_names.index("L_step_max")]),
        geod_2ndinv_grid=geod_2nd,
        iso_grav_grid=iso_grav,
        footprint_idx=fi,
    )
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32, shape=(len(H66_SGMC_NAMES), fi.size))
    for j, name in enumerate(H66_SGMC_NAMES):
        v = vecs[j]
        if not np.isfinite(v).all() or (v < 0.0).any() or (v > 1.0).any():
            raise ValueError(f"{name} has invalid values outside finite [0, 1]")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H66_SGMC_NAMES))
    return list(H66_SGMC_NAMES)


def load_h66_sgmc_sidecar(
    work: Path,
    external_dir: Path,
    static: np.ndarray,
    static_names: list[str],
    foot: np.ndarray,
    footprint_idx: np.ndarray,
) -> np.ndarray:
    """Load `(3, n_footprint)` H66-2 sidecar from `work_dir()`, building once if absent."""
    work = Path(work)
    path = work / "h66_sgmc_columns.npy"
    if not path.exists():
        build_h66_sgmc_sidecar(work, external_dir, static, static_names, foot, footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H66_SGMC_NAMES or arr.shape != (len(H66_SGMC_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"H66 SGMC sidecar mismatch: names={names} shape={arr.shape}")
    return arr
