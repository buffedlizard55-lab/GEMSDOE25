"""H81 (FHJ-SD + CLR + SLUTH) static structural-junction, disequilibrium, compositional & wavenumber sidecar.

Pre-registered in ``knowledge/44_preregistered_h81_fhj_sd_2026-10-28.md`` (committed at ``6c66fc0``
before writing this module, fitting any model on virgin draws 140-143, or building any GeoTIFF).

Design invariants:
  * Strictly static and Quaternary-catalogue-free: ``labels.tif``, ``existing_faults.tif``,
    ``gdr_qfaults_traces.csv``, and ``dist_known_fault_px`` are NEVER opened or read.
  * All 6 ``H81_FHJ_NAMES`` columns are finite ``float32`` in ``[0, 1]`` across all ``5,167,373``
    footprint pixels (``0.0`` outside ``footprint``).
  * Analytical unit-tested operators:
      1. ``forstner_junction_invariant``: vanishes on single planar 1-D steps, peaks on 2-D fault intersections.
      2. ``relay_tip_divergence``: peaks at lineament terminations and en-echelon relay step-overs.
      3. ``compute_cation_silica_diseq_halo``: label-free cation-chalcedony & quartz-measured disequilibrium.
      4. ``cospectral_theta_basin``: burial-depth-invariant Cooper-Cowan cos(Theta_g)*cos(Theta_m) phase bridge.
      5. ``aitchison_clr_jump``: moisture/clearance-invariant Aitchison CLR(K,Th,U) cross-contact jump.
      6. ``sluth_fault_structural_index``: 2-D FFT multi-altitude analytic-signal N~0 fault-step filter.
"""

from __future__ import annotations

import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import binary_erosion, gaussian_filter
from scipy.signal import fftconvolve

from .features import nearest_fill, ridge_strength
from .h74_rmps import CELL_M, PAD_PX, harmonic_vertical_derivative_fft
from .h75_dchb import combine_corridor_gated_scores, destripe_ew_flightlines, pct_clip01
from .paths import data_dir

H81_FHJ_NAMES: list[str] = [
    "H81_bimodal_junction_det",
    "H81_relay_tip_divergence",
    "H81_cation_silica_diseq",
    "H81_cospectral_theta_basin",
    "H81_aitchison_clr_jump",
    "H81_sluth_fault_index",
]

GDR_WS_ALLOWED_COLS: tuple[str, ...] = (
    "row",
    "col",
    "layer",
    "thermalclass",
    "temp_c",
    "geothermquartz_c",
    "geothermchalc_c",
    "geothermcat_c",
)

GDR_VENT_ALLOWED_COLS: tuple[str, ...] = (
    "row",
    "col",
)

JUNCTION_GAMMA_DEFAULT: float = 0.62
JUNCTION_GAP_SCALE_DEFAULT: float = 0.95


def forstner_junction_invariant(
    field: np.ndarray,
    sig_grad: float = 1.8,
    sig_ten: float = 5.0,
) -> np.ndarray:
    """Normalized 2-D Harris/Forstner minor-eigenvalue junction invariant ``4*det(J)/(tr(J) + eps)``.

    Vanishes on flat basins (``lambda_1 = lambda_2 = 0``) AND on single planar 1-D edges
    (``lambda_2 = 0``), peaking strictly where two distinct structural strikes intersect or
    step across an accommodation zone (``lambda_1 >= lambda_2 > 0``).
    """
    f = nearest_fill(np.asarray(field, dtype=np.float32))
    sm = gaussian_filter(f, float(sig_grad), mode="nearest")
    gy, gx = np.gradient(sm)
    jxx = gaussian_filter((gx * gx).astype(np.float32), float(sig_ten), mode="nearest")
    jyy = gaussian_filter((gy * gy).astype(np.float32), float(sig_ten), mode="nearest")
    jxy = gaussian_filter((gx * gy).astype(np.float32), float(sig_ten), mode="nearest")
    tr = np.maximum(jxx + jyy, 0.0)
    det = np.maximum(jxx * jyy - jxy * jxy, 0.0)
    eps = float(np.percentile(tr, 50.0)) * 1e-3 + 1e-12
    return (4.0 * det / (tr + eps)).astype(np.float32)


def relay_tip_divergence(
    field: np.ndarray,
    sig_grad: float = 1.8,
    sig_disp: float = 8.0,
) -> np.ndarray:
    """Along-strike lineament termination rate ``|t . grad(A)|`` x 800-m strike dispersion ``1 - R_8``."""
    f = nearest_fill(np.asarray(field, dtype=np.float32))
    sm = gaussian_filter(f, float(sig_grad), mode="nearest")
    gy, gx = np.gradient(sm)
    amp = np.hypot(gx, gy).astype(np.float32)
    denom = amp + 1e-6
    # Strike tangent t is perpendicular to gradient (gx, gy): tx = -gy/|g|, ty = gx/|g|
    tx = -gy / denom
    ty = gx / denom
    gay, gax = np.gradient(gaussian_filter(amp, 1.2, mode="nearest"))
    along_term = np.abs(tx * gax + ty * gay).astype(np.float32)

    # Doubled-strike director n2 = (tx^2 - ty^2, 2*tx*ty) weighted by amplitude
    c2 = (tx * tx - ty * ty).astype(np.float32)
    s2 = (2.0 * tx * ty).astype(np.float32)
    w_sm = gaussian_filter(amp, float(sig_disp), mode="nearest") + 1e-6
    c2_bar = gaussian_filter(amp * c2, float(sig_disp), mode="nearest") / w_sm
    s2_bar = gaussian_filter(amp * s2, float(sig_disp), mode="nearest") / w_sm
    r_coh = np.clip(np.hypot(c2_bar, s2_bar), 0.0, 1.0)
    dispersion = 1.0 - r_coh
    return (along_term * (0.20 + 0.80 * dispersion)).astype(np.float32)


def _aniso_gaussian_kernel(
    sigma_along: float,
    sigma_across: float,
    azimuth_cw_deg: float,
    truncate: float = 3.0,
) -> np.ndarray:
    rad = int(np.ceil(max(sigma_along, sigma_across) * truncate))
    yy, xx = np.mgrid[-rad : rad + 1, -rad : rad + 1].astype(np.float64)
    a = np.deg2rad(float(azimuth_cw_deg))
    tx, ty = np.sin(a), -np.cos(a)
    nx, ny = -ty, tx
    u_par = xx * tx + yy * ty
    u_perp = xx * nx + yy * ny
    k = np.exp(-0.5 * ((u_par / sigma_along) ** 2 + (u_perp / sigma_across) ** 2))
    k /= max(float(k.sum()), 1e-12)
    return k.astype(np.float32)


def compute_cation_silica_diseq_halo(
    ws_df: pd.DataFrame,
    vent_df: pd.DataFrame,
    cond_surf: np.ndarray,
    footprint: np.ndarray,
    norm_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Anisotropic hydrothermal cation-chalcedony & quartz-measured disequilibrium x MT clay-cap gradient."""
    if "dist_known_fault_px" in ws_df.columns or "dist_known_fault_px" in vent_df.columns:
        raise ValueError("dist_known_fault_px is label-derived and strictly forbidden in H81 builders")
    foot = np.asarray(footprint, dtype=bool)
    nmask = foot if norm_mask is None else np.asarray(norm_mask, dtype=bool)
    h, w = foot.shape
    imp = np.zeros((h, w), dtype=np.float32)

    if not ws_df.empty:
        sub = ws_df[(ws_df["row"] >= 0) & (ws_df["row"] < h) & (ws_df["col"] >= 0) & (ws_df["col"] < w)]
        if not sub.empty:
            rows = sub["row"].to_numpy(dtype=np.int64)
            cols = sub["col"].to_numpy(dtype=np.int64)
            is_spring = sub["layer"].fillna("").astype(str).str.startswith("spring_").to_numpy()
            w_spr = np.where(is_spring, 1.4, 1.0).astype(np.float32)

            t_meas = pd.to_numeric(sub["temp_c"], errors="coerce").to_numpy(dtype=np.float64)
            t_qtz = pd.to_numeric(sub["geothermquartz_c"], errors="coerce").to_numpy(dtype=np.float64)
            t_chalc = pd.to_numeric(sub["geothermchalc_c"], errors="coerce").to_numpy(dtype=np.float64)
            t_cat = pd.to_numeric(sub["geothermcat_c"], errors="coerce").to_numpy(dtype=np.float64)

            dt_qm = np.where(np.isfinite(t_qtz) & np.isfinite(t_meas), np.maximum(0.0, t_qtz - t_meas), 0.0)
            dt_qm_solo = np.where(np.isfinite(t_qtz) & ~np.isfinite(t_meas), np.maximum(0.0, t_qtz - 25.0) * 0.5, 0.0)
            dt_cc = np.where(np.isfinite(t_cat) & np.isfinite(t_chalc), np.maximum(0.0, t_cat - t_chalc), 0.0)
            dt_m = np.where(np.isfinite(t_meas), np.maximum(0.0, t_meas - 20.0), 0.0)

            diseq = np.clip(dt_qm + dt_qm_solo + 0.70 * dt_cc + 0.50 * dt_m, 0.0, 260.0).astype(np.float32) * w_spr
            pos = diseq > 0.0
            if pos.any():
                np.maximum.at(imp, (rows[pos], cols[pos]), diseq[pos])

    if not vent_df.empty:
        vsub = vent_df[(vent_df["row"] >= 0) & (vent_df["row"] < h) & (vent_df["col"] >= 0) & (vent_df["col"] < w)]
        if not vsub.empty:
            vr = vsub["row"].to_numpy(dtype=np.int64)
            vc = vsub["col"].to_numpy(dtype=np.int64)
            np.maximum.at(imp, (vr, vc), 25.0)

    log_imp = np.log1p(imp).astype(np.float32)
    k_br = _aniso_gaussian_kernel(14.0, 3.5, 15.0)   # N15E Basin & Range normal extension strike
    k_wl = _aniso_gaussian_kernel(14.0, 3.5, 145.0)  # N35W Walker Lane transtensional strike
    plume = (
        0.60 * np.maximum(fftconvolve(log_imp, k_br, mode="same").astype(np.float32), 0.0)
        + 0.40 * np.maximum(fftconvolve(log_imp, k_wl, mode="same").astype(np.float32), 0.0)
    )
    plume_n = pct_clip01(np.log1p(50.0 * plume), nmask)

    cond_log = np.log1p(np.maximum(nearest_fill(np.asarray(cond_surf, dtype=np.float32)), 0.0))
    cgy, cgx = np.gradient(gaussian_filter(cond_log, 2.0, mode="nearest"))
    mt_flank = pct_clip01(np.hypot(cgx, cgy).astype(np.float32), nmask)
    coupled = plume_n * (0.25 + 0.75 * mt_flank)
    return np.where(foot, pct_clip01(coupled, nmask), 0.0).astype(np.float32)


def cospectral_theta_basin(
    iso_grav: np.ndarray,
    iso_grav_vg: np.ndarray,
    rtp_ds: np.ndarray,
    depth_to_base: np.ndarray,
    footprint: np.ndarray,
    norm_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Burial-depth-invariant Cooper-Cowan ``cos(Theta_grav) * cos(Theta_mag) * cos^2(phi_g - phi_m)``."""
    foot = np.asarray(footprint, dtype=bool)
    nmask = foot if norm_mask is None else np.asarray(norm_mask, dtype=bool)

    g = gaussian_filter(nearest_fill(np.asarray(iso_grav, dtype=np.float32)), 1.5, mode="nearest")
    ggy, ggx = np.gradient(g)
    gh_km = 10.0 * np.hypot(ggx, ggy).astype(np.float32)  # mGal / km on 100-m grid
    gz_km = gaussian_filter(nearest_fill(np.asarray(iso_grav_vg, dtype=np.float32)), 1.5, mode="nearest")
    eps_g = float(np.percentile(gh_km[nmask], 20.0)) * 0.25 + 1e-6
    cos_theta_g = gh_km / np.sqrt(gh_km * gh_km + gz_km * gz_km + eps_g * eps_g)

    m = gaussian_filter(nearest_fill(np.asarray(rtp_ds, dtype=np.float32)), 1.5, mode="nearest")
    mgy, mgx = np.gradient(m)
    mh_m = (np.hypot(mgx, mgy) / float(CELL_M)).astype(np.float32)  # nT / m
    mz_m = harmonic_vertical_derivative_fft(m, cell_m=CELL_M, pad=min(PAD_PX, max(m.shape) // 2))
    eps_m = float(np.percentile(mh_m[nmask], 20.0)) * 0.25 + 1e-6
    cos_theta_m = mh_m / np.sqrt(mh_m * mh_m + mz_m * mz_m + eps_m * eps_m)

    dot = ggx * mgx + ggy * mgy
    cos2_dphi = (dot * dot) / ((ggx * ggx + ggy * ggy + 1e-12) * (mgx * mgx + mgy * mgy + 1e-12))

    base_log = np.log1p(np.maximum(nearest_fill(np.asarray(depth_to_base, dtype=np.float32)), 0.0))
    w_basin = 0.25 + 0.75 * pct_clip01(base_log, nmask)
    bridge = (cos_theta_g * cos_theta_m * cos2_dphi).astype(np.float32)
    crest = ridge_strength(bridge, 1.2) * w_basin
    return np.where(foot, pct_clip01(crest, nmask), 0.0).astype(np.float32)


def aitchison_clr_raw_jump(
    k_pos: np.ndarray,
    th_pos: np.ndarray,
    u_pos: np.ndarray,
    nx: np.ndarray,
    ny: np.ndarray,
    sigma: float = 1.8,
) -> np.ndarray:
    """Moisture/altitude-invariant Aitchison ``||n . grad CLR(K, Th, U)||_2`` across normal ``(nx, ny)``.

    Exact invariance: scaling ``(K, Th, U) -> m(x,y) * (K, Th, U)`` for ANY positive field ``m(x,y) > 0``
    adds ``ln m(x,y)`` identically to ``ln K, ln Th, ln U`` and their mean, leaving ``CLR`` unchanged.
    """
    lk = np.log(np.maximum(np.asarray(k_pos, dtype=np.float64), 1e-12))
    lth = np.log(np.maximum(np.asarray(th_pos, dtype=np.float64), 1e-12))
    lu = np.log(np.maximum(np.asarray(u_pos, dtype=np.float64), 1e-12))
    lbar = (lk + lth + lu) / 3.0
    c1 = (lk - lbar).astype(np.float32)
    c2 = (lth - lbar).astype(np.float32)
    c3 = (lu - lbar).astype(np.float32)

    nx_f = np.asarray(nx, dtype=np.float32)
    ny_f = np.asarray(ny, dtype=np.float32)
    acc = np.zeros(c1.shape, dtype=np.float32)
    for comp in (c1, c2, c3):
        gy, gx = np.gradient(gaussian_filter(comp, float(sigma), mode="nearest"))
        proj = nx_f * gx + ny_f * gy
        acc += proj * proj
    return np.sqrt(acc).astype(np.float32)


def compute_aitchison_clr_jump(
    k_u8: np.ndarray,
    th_u8: np.ndarray,
    u_u8: np.ndarray,
    tc_u8: np.ndarray,
    iso_grav: np.ndarray,
    rtp_ds: np.ndarray,
    footprint: np.ndarray,
    norm_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Deconfounded Aitchison CLR(K,Th,U) cross-strike compositional jump on valid GeoDAWN pixels."""
    foot = np.asarray(footprint, dtype=bool)
    nmask = foot if norm_mask is None else np.asarray(norm_mask, dtype=bool)
    rad_ok = foot & (k_u8 > 0) & (th_u8 > 0) & (u_u8 > 0) & (tc_u8 > 0)
    if not rad_ok.any():
        return np.zeros(foot.shape, dtype=np.float32)

    k_f = nearest_fill(np.where(rad_ok, k_u8.astype(np.float32), np.nan))
    th_f = nearest_fill(np.where(rad_ok, th_u8.astype(np.float32), np.nan))
    u_f = nearest_fill(np.where(rad_ok, u_u8.astype(np.float32), np.nan))
    tc_f = nearest_fill(np.where(rad_ok, tc_u8.astype(np.float32), np.nan))

    # Composite potential-field normal vector (nx, ny)
    ggy, ggx = np.gradient(gaussian_filter(nearest_fill(np.asarray(iso_grav, dtype=np.float32)), 2.0, mode="nearest"))
    mgy, mgx = np.gradient(gaussian_filter(nearest_fill(np.asarray(rtp_ds, dtype=np.float32)), 2.0, mode="nearest"))
    gn = np.hypot(ggx, ggy) + 1e-6
    mn = np.hypot(mgx, mgy) + 1e-6
    # Align magnetic gradient sign with gravity gradient so antiparallel contacts reinforce rather than cancel
    sgn = np.where((ggx * mgx + ggy * mgy) >= 0.0, 1.0, -1.0).astype(np.float32)
    vx = (ggx / gn) + sgn * (mgx / mn)
    vy = (ggy / gn) + sgn * (mgy / mn)
    vn = np.hypot(vx, vy) + 1e-6
    nx, ny = vx / vn, vy / vn

    clr_j = aitchison_clr_raw_jump(k_f, th_f, u_f, nx, ny, sigma=1.8)
    ltc = np.log(np.maximum(tc_f, 1.0))
    tcy, tcx = np.gradient(gaussian_filter(ltc, 1.8, mode="nearest"))
    tc_proj = np.abs(nx * tcx + ny * tcy)
    rad_core = nmask & rad_ok
    msk = rad_core if rad_core.any() else rad_ok
    tau_tc = max(float(np.percentile(tc_proj[msk], 75.0)), 1e-4)
    deconf = clr_j * np.exp(-tc_proj / tau_tc)
    eroded_rad = binary_erosion(rad_ok, iterations=2)
    use_rad = eroded_rad if eroded_rad.any() else rad_ok
    raw = np.where(use_rad, ridge_strength(deconf.astype(np.float32), 1.2), 0.0)
    return np.where(use_rad, pct_clip01(raw, use_rad & nmask), 0.0).astype(np.float32)


def upward_analytic_signal_fft(
    field: np.ndarray,
    altitudes_m: tuple[float, float] = (150.0, 400.0),
    cell_m: float = CELL_M,
    pad: int = 128,
) -> tuple[np.ndarray, np.ndarray]:
    """Exact 2-D FFT upward-continued analytic-signal amplitudes ``(A_z1, A_z2)`` in ``[field]/m``."""
    a = nearest_fill(np.asarray(field, dtype=np.float32)).astype(np.float64)
    h, w = a.shape
    p = min(int(pad), max(h, w) // 2)
    ap = np.pad(a, ((p, p), (p, p)), mode="reflect") if p > 0 else a
    hp, wp = ap.shape
    ky = np.fft.fftfreq(hp, d=float(cell_m))[:, None]
    kx = np.fft.rfftfreq(wp, d=float(cell_m))[None, :]
    kr = np.hypot(kx, ky)
    fhat = np.fft.rfft2(ap)

    amps: list[np.ndarray] = []
    for z in altitudes_m:
        att = np.exp(-2.0 * np.pi * kr * float(z))
        fx = np.fft.irfft2(fhat * (2j * np.pi * kx) * att, s=(hp, wp))
        fy = np.fft.irfft2(fhat * (2j * np.pi * ky) * att, s=(hp, wp))
        fz = np.fft.irfft2(fhat * (2.0 * np.pi * kr) * att, s=(hp, wp))
        if p > 0:
            fx = fx[p : p + h, p : p + w]
            fy = fy[p : p + h, p : p + w]
            fz = fz[p : p + h, p : p + w]
        amps.append(np.sqrt(fx * fx + fy * fy + fz * fz).astype(np.float32))
    return amps[0], amps[1]


def sluth_local_exponent(
    field: np.ndarray,
    z1_m: float = 150.0,
    z2_m: float = 400.0,
    z_ref_m: float = 150.0,
    cell_m: float = CELL_M,
    pad: int = 128,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(eta_local, A_z1)`` where ``eta_local ~ N + 1`` (``~1`` for ``N=0`` fault step, ``>=3`` for dipole)."""
    a1, a2 = upward_analytic_signal_fft(field, altitudes_m=(z1_m, z2_m), cell_m=cell_m, pad=pad)
    eps = float(np.percentile(a2, 25.0)) * 0.10 + 1e-9
    denom = float(np.log((z2_m + z_ref_m) / (z1_m + z_ref_m)))
    eta = np.log((a1 + eps) / (a2 + eps)) / max(denom, 1e-9)
    return eta.astype(np.float32), a1


def compute_sluth_fault_index(
    rtp_ds: np.ndarray,
    footprint: np.ndarray,
    norm_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Multi-altitude harmonic upward-continuation structural-index ``N~0`` fault-step filter."""
    foot = np.asarray(footprint, dtype=bool)
    nmask = foot if norm_mask is None else np.asarray(norm_mask, dtype=bool)
    eta, a150 = sluth_local_exponent(rtp_ds, z1_m=150.0, z2_m=400.0, z_ref_m=150.0, cell_m=CELL_M, pad=128)
    w_step = np.exp(-0.5 * ((eta - 1.0) / 0.55) ** 2).astype(np.float32)
    amp_ridge = pct_clip01(ridge_strength(np.log1p(np.maximum(a150, 0.0)), 1.2), nmask)
    return np.where(foot, pct_clip01(w_step * amp_ridge, nmask), 0.0).astype(np.float32)


def compute_h81_fhj_grids(
    *,
    rtp: np.ndarray,
    iso_grav: np.ndarray,
    iso_grav_vg: np.ndarray,
    depth_to_base: np.ndarray,
    cond_surf: np.ndarray,
    geod_shear: np.ndarray,
    geod_dilate: np.ndarray,
    deq_seis: np.ndarray,
    ieq_seis: np.ndarray,
    rad_k_u8: np.ndarray,
    rad_th_u8: np.ndarray,
    rad_u_u8: np.ndarray,
    rad_tc_u8: np.ndarray,
    wellspring_df: pd.DataFrame,
    vent_df: pd.DataFrame,
    footprint: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute all 6 strictly static, Quaternary-catalogue-free ``H81_FHJ_NAMES`` grids in ``[0, 1]``."""
    foot = np.asarray(footprint, dtype=bool)
    core = binary_erosion(foot, iterations=4)
    nmask = core if core.any() else foot

    rtp_ds = destripe_ew_flightlines(rtp, sigma_ns=2.0, sigma_ew=14.0)
    base_log = np.log1p(np.maximum(nearest_fill(np.asarray(depth_to_base, dtype=np.float32)), 0.0))

    # 1. H81_bimodal_junction_det: Faulds-Hinz 2-D Forstner bimodal junction invariant x transtensional strain
    jg = pct_clip01(forstner_junction_invariant(iso_grav, sig_grad=1.8, sig_ten=5.0), nmask)
    jm = pct_clip01(forstner_junction_invariant(rtp_ds, sig_grad=1.8, sig_ten=5.0), nmask)
    jb = pct_clip01(forstner_junction_invariant(base_log, sig_grad=1.8, sig_ten=5.0), nmask)
    shear_pos = np.maximum(nearest_fill(np.asarray(geod_shear, dtype=np.float32)), 0.0)
    dil_pos = np.maximum(nearest_fill(np.asarray(geod_dilate, dtype=np.float32)), 0.0)
    strain_gate = 0.30 + 0.70 * pct_clip01(pct_clip01(shear_pos, nmask) + 0.80 * pct_clip01(dil_pos, nmask), nmask)
    j_comb = (0.40 * jg + 0.35 * jm + 0.25 * jb) * strain_gate
    h81_junc = np.where(foot, pct_clip01(j_comb, nmask), 0.0).astype(np.float32)
    del jg, jm, jb, shear_pos, dil_pos, strain_gate, j_comb

    # 2. H81_relay_tip_divergence: Along-strike contact termination x 800-m strike dispersion x microseismicity
    tg = pct_clip01(relay_tip_divergence(iso_grav, sig_grad=1.8, sig_disp=8.0), nmask)
    tm = pct_clip01(relay_tip_divergence(rtp_ds, sig_grad=1.8, sig_disp=8.0), nmask)
    s_deq = np.log1p(np.maximum(nearest_fill(np.asarray(deq_seis, dtype=np.float32)), 0.0))
    s_ieq = np.log1p(np.maximum(nearest_fill(np.asarray(ieq_seis, dtype=np.float32)), 0.0))
    seis_gate = 0.30 + 0.70 * pct_clip01(pct_clip01(s_deq, nmask) + pct_clip01(s_ieq, nmask), nmask)
    h81_relay = np.where(foot, pct_clip01((0.55 * tg + 0.45 * tm) * seis_gate, nmask), 0.0).astype(np.float32)
    del tg, tm, s_deq, s_ieq, seis_gate

    # 3. H81_cation_silica_diseq: Anisotropic multi-geothermometer boiling disequilibrium x MT clay-cap flank
    h81_diseq = compute_cation_silica_diseq_halo(wellspring_df, vent_df, cond_surf, foot, norm_mask=nmask)

    # 4. H81_cospectral_theta_basin: Burial-depth-invariant Cooper-Cowan cos(Theta_g)*cos(Theta_m) phase bridge
    h81_theta = cospectral_theta_basin(iso_grav, iso_grav_vg, rtp_ds, depth_to_base, foot, norm_mask=nmask)

    # 5. H81_aitchison_clr_jump: Moisture-invariant Aitchison CLR(K,Th,U) cross-contact compositional jump
    h81_clr = compute_aitchison_clr_jump(
        rad_k_u8, rad_th_u8, rad_u_u8, rad_tc_u8, iso_grav, rtp_ds, foot, norm_mask=nmask
    )

    # 6. H81_sluth_fault_index: Multi-altitude FFT upward-continuation N~0 fault-step structural-index filter
    h81_sluth = compute_sluth_fault_index(rtp_ds, foot, norm_mask=nmask)

    out = {
        "H81_bimodal_junction_det": h81_junc,
        "H81_relay_tip_divergence": h81_relay,
        "H81_cation_silica_diseq": h81_diseq,
        "H81_cospectral_theta_basin": h81_theta,
        "H81_aitchison_clr_jump": h81_clr,
        "H81_sluth_fault_index": h81_sluth,
    }
    for name, arr in out.items():
        if not np.isfinite(arr).all():
            raise ValueError(f"{name} contains non-finite values")
        if (arr[foot] < 0.0).any() or (arr[foot] > 1.0).any():
            raise ValueError(f"{name} values outside [0, 1] inside footprint")
        if (arr[~foot] != 0.0).any():
            raise ValueError(f"{name} non-zero outside footprint")
    return out


def build_h81_fhj_sidecar(
    band_dir: Path,
    external_dir: Path,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
    out_path: Path,
) -> list[str]:
    """Build ``(6, n_footprint)`` float32 memmap + ``.names.json`` without touching any label file."""
    band_dir, external_dir, out_path = Path(band_dir), Path(external_dir), Path(out_path)
    foot = np.asarray(footprint, dtype=bool)
    fi = np.asarray(footprint_idx, dtype=np.int64)

    with rasterio.open(external_dir / "geodawn_rad_u8.tif") as ds:
        rad_k_u8 = ds.read(1)
        rad_th_u8 = ds.read(2)
        rad_u_u8 = ds.read(3)
        rad_tc_u8 = ds.read(4)

    ws_df = pd.read_csv(
        external_dir / "gdr_wellspring_in_footprint.csv",
        usecols=list(GDR_WS_ALLOWED_COLS),
    )
    vent_df = pd.read_csv(
        external_dir / "gdr_volcanic_vents_in_footprint.csv",
        usecols=list(GDR_VENT_ALLOWED_COLS),
    )

    grids = compute_h81_fhj_grids(
        rtp=np.load(band_dir / "02_rtp.npy", mmap_mode="r"),
        iso_grav=np.load(band_dir / "13_iso_grav_anom.npy", mmap_mode="r"),
        iso_grav_vg=np.load(band_dir / "11_iso_grav_anom_vg.npy", mmap_mode="r"),
        depth_to_base=np.load(band_dir / "15_depth_to_base_surf.npy", mmap_mode="r"),
        cond_surf=np.load(band_dir / "17_cond_surf.npy", mmap_mode="r"),
        geod_shear=np.load(band_dir / "07_geod_shearrate.npy", mmap_mode="r"),
        geod_dilate=np.load(band_dir / "08_geod_dilaterate.npy", mmap_mode="r"),
        deq_seis=np.load(band_dir / "10_deq_n100a15.npy", mmap_mode="r"),
        ieq_seis=np.load(band_dir / "16_ieq_n100a15.npy", mmap_mode="r"),
        rad_k_u8=rad_k_u8,
        rad_th_u8=rad_th_u8,
        rad_u_u8=rad_u_u8,
        rad_tc_u8=rad_tc_u8,
        wellspring_df=ws_df,
        vent_df=vent_df,
        footprint=foot,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(
        out_path, mode="w+", dtype=np.float32, shape=(len(H81_FHJ_NAMES), fi.size)
    )
    for j, name in enumerate(H81_FHJ_NAMES):
        mm[j] = grids[name].ravel()[fi]
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H81_FHJ_NAMES) + "\n")
    del grids, mm
    gc.collect()
    return list(H81_FHJ_NAMES)


def load_h81_fhj_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load or build ``h81_fhj_columns.npy`` inside ``work`` without altering pinned caches."""
    work = Path(work)
    path = work / "h81_fhj_columns.npy"
    names_path = Path(str(path) + ".names.json")
    if not path.exists() or not names_path.exists():
        foot = np.load(work / "bands" / "_footprint.npy")
        build_h81_fhj_sidecar(work / "bands", data_dir() / "external", foot, footprint_idx, path)
    names = json.loads(names_path.read_text())
    arr = np.load(path, mmap_mode="r")
    if names != H81_FHJ_NAMES or arr.shape != (len(H81_FHJ_NAMES), len(footprint_idx)):
        raise ValueError(f"H81 FHJ sidecar mismatch: {names=} {arr.shape=}")
    return arr


def combine_junction_corridor_scores(
    p_subsurf: np.ndarray,
    p_trace: np.ndarray,
    p_gap: np.ndarray,
    lidar_valid: np.ndarray,
    *,
    gamma: float = JUNCTION_GAMMA_DEFAULT,
    gap_scale: float = JUNCTION_GAP_SCALE_DEFAULT,
) -> np.ndarray:
    """Frozen H81 Junction-Corridor Dual-Regime coupling across ``L_valid == 1`` and ``L_valid == 0``."""
    return combine_corridor_gated_scores(
        p_subsurf,
        p_trace,
        p_gap,
        lidar_valid,
        gamma=gamma,
        gap_scale=gap_scale,
    )
