"""H79 (CTHM-PoE & SGMC-Coulomb) static multi-physics sidecar & Domain-Decoupled PoE fusion.

Pre-registered in ``knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md`` (committed at ``b59b129``
before feature computation or model fitting).

Design invariants:
* Strictly static and Quaternary-catalogue-free: ``labels.tif``, ``existing_faults.tif``,
  ``gdr_qfaults_traces.csv``, and ``dist_known_fault_px`` are NEVER opened or referenced.
* All five ``H79_ALL_NAMES`` columns are finite ``float32`` in ``[0, 1]`` across all ``5,167,373``
  valid footprint pixels (``0.0`` outside ``footprint``).
* Peak RAM stays low (one 2-D float32 grid at a time, streamed into a ``(5, N_foot)`` float32 memmap).
"""

from __future__ import annotations

import csv
import gc
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import (
    binary_erosion,
    distance_transform_edt,
    gaussian_filter,
)
from scipy.signal import fftconvolve
from scipy.stats import rankdata

from .features import load_base, nearest_fill, ridge_strength
from .h74_rmps import pct_scale_eroded

H79_CTHM_NAMES = [
    "H79_aniso_conduit_plume",
    "H79_demag_argillic_crest",
    "H79_euler_contact_index",
    "H79_grav_mt_gouge_juxtapose",
]

H79_SGMC_NAMES = [
    "H79_sgmc_coulomb_react",
]

H79_ALL_NAMES = H79_CTHM_NAMES + H79_SGMC_NAMES

# Frozen Domain-Decoupled PoE constants (knowledge/39 §4)
POE_GAMMA_CRUSTAL = 0.55
POE_FLOOR_CRUSTAL = 0.10
POE_FLOOR_MORPHO = 0.22

WELLSPRING_ALLOWED_COLS = frozenset({
    "row",
    "col",
    "thermalclass",
    "temp_c",
    "geothermquartz_c",
    "geothermchalc_c",
    "geothermcat_c",
})

VENT_ALLOWED_COLS = frozenset({"row", "col"})


def rank01_domain(values: np.ndarray) -> np.ndarray:
    """Tie-averaged empirical quantile rank in (0, 1] on a 1-D finite float vector."""
    v = np.asarray(values, dtype=np.float64)
    if v.ndim != 1:
        raise ValueError("rank01_domain expects a 1-D array")
    n = v.size
    if n == 0:
        return np.empty(0, dtype=np.float32)
    if not np.isfinite(v).all():
        v = np.nan_to_num(v, nan=0.0, posinf=1.0, neginf=0.0)
    if np.ptp(v) == 0.0:
        return np.full(n, 0.5, dtype=np.float32)
    return (rankdata(v, method="average") / float(n)).astype(np.float32)


def fuse_poe_scores(
    p_crustal: np.ndarray,
    p_morpho: np.ndarray,
    gamma: float = POE_GAMMA_CRUSTAL,
    floor_c: float = POE_FLOOR_CRUSTAL,
    floor_m: float = POE_FLOOR_MORPHO,
) -> np.ndarray:
    """Frozen floor-protected Domain-Decoupled Product-of-Experts score in (0, 1] (knowledge/39 §4).

    ``S_PoE(x) = (floor_c + (1 - floor_c) * R_c(x))^gamma * (floor_m + (1 - floor_m) * R_m(x))^(1 - gamma)``
    """
    rc = rank01_domain(p_crustal)
    rm = rank01_domain(p_morpho)
    tc = np.clip(floor_c + (1.0 - floor_c) * rc, 1e-6, 1.0)
    tm = np.clip(floor_m + (1.0 - floor_m) * rm, 1e-6, 1.0)
    out = (tc ** float(gamma)) * (tm ** float(1.0 - gamma))
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def _elliptical_gaussian_kernel(
    sigma_along: float,
    sigma_across: float,
    strike_deg_cw_from_north: float,
    truncate: float = 3.0,
) -> np.ndarray:
    """Normalized 2-D elliptical Gaussian kernel oriented at ``strike_deg_cw_from_north``."""
    rad = int(np.ceil(max(sigma_along, sigma_across) * truncate))
    yy, xx = np.mgrid[-rad : rad + 1, -rad : rad + 1].astype(np.float64)
    # Convert clockwise-from-North strike angle alpha to (dx=col=East, dy=row=South) unit tangent:
    # North = (dx=0, dy=-1), East = (dx=+1, dy=0) => tangent t = (sin(alpha), -cos(alpha))
    alpha = np.deg2rad(strike_deg_cw_from_north)
    tx, ty = np.sin(alpha), -np.cos(alpha)
    nx, ny = -ty, tx
    u_along = xx * tx + yy * ty
    u_across = xx * nx + yy * ny
    k = np.exp(-0.5 * ((u_along / sigma_along) ** 2 + (u_across / sigma_across) ** 2))
    k /= max(float(k.sum()), 1e-12)
    return k.astype(np.float32)


def _strike_director_doubled(field: np.ndarray, sig_grad: float = 2.0, sig_ten: float = 3.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return doubled-strike unit vector (c2, s2) in math (col=x, row=y) coords and coherence kappa."""
    sm = gaussian_filter(np.asarray(field, dtype=np.float32), sig_grad)
    gy, gx = np.gradient(sm)
    jxx = gaussian_filter((gx * gx).astype(np.float32), sig_ten)
    jyy = gaussian_filter((gy * gy).astype(np.float32), sig_ten)
    jxy = gaussian_filter((gx * gy).astype(np.float32), sig_ten)
    phi2 = np.arctan2(2.0 * jxy, jxx - jyy)
    # Strike is perpendicular to gradient normal -> negate doubled-angle cosine/sine
    c2 = (-np.cos(phi2)).astype(np.float32)
    s2 = (-np.sin(phi2)).astype(np.float32)
    coh = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0)) / (jxx + jyy + 1e-12)
    return c2, s2, coh.astype(np.float32)


def _load_label_free_conduit_impulses(external_dir: Path, shape: tuple[int, int]) -> np.ndarray:
    """Build impulse grid I_src strictly from allowlisted chemistry/vent coordinates (never dist_known_fault_px)."""
    h, w = shape
    imp = np.zeros((h, w), dtype=np.float32)
    ws_csv = external_dir / "gdr_wellspring_in_footprint.csv"
    if ws_csv.is_file():
        with ws_csv.open(newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    r = int(float(row["row"]))
                    c = int(float(row["col"]))
                except (KeyError, ValueError):
                    continue
                if not (0 <= r < h and 0 <= c < w):
                    continue
                strength = 0.0
                for col_nm, thr in (
                    ("temp_c", 25.0),
                    ("geothermquartz_c", 80.0),
                    ("geothermchalc_c", 70.0),
                    ("geothermcat_c", 90.0),
                ):
                    assert col_nm in WELLSPRING_ALLOWED_COLS
                    raw = row.get(col_nm, "")
                    if raw:
                        try:
                            val = float(raw)
                            if np.isfinite(val) and val >= thr:
                                strength = max(strength, 1.0 + min((val - thr) / 50.0, 2.0))
                        except ValueError:
                            pass
                tcls = (row.get("thermalclass") or "").lower()
                if any(tok in tcls for tok in ("hot", "warm", "therm")):
                    strength = max(strength, 1.0)
                if strength > 0.0:
                    imp[r, c] += float(strength)

    vv_csv = external_dir / "gdr_volcanic_vents_in_footprint.csv"
    if vv_csv.is_file():
        with vv_csv.open(newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    r = int(float(row["row"]))
                    c = int(float(row["col"]))
                except (KeyError, ValueError):
                    continue
                if 0 <= r < h and 0 <= c < w:
                    imp[r, c] += 2.5
    return np.log1p(imp).astype(np.float32)


def _zscore_core(arr: np.ndarray, core: np.ndarray) -> np.ndarray:
    vals = arr[core & np.isfinite(arr)]
    if vals.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)
    mu = float(np.mean(vals))
    sd = float(np.std(vals))
    if not np.isfinite(sd) or sd <= 1e-8:
        return np.zeros(arr.shape, dtype=np.float32)
    return ((arr - mu) / sd).astype(np.float32)


def compute_h79_grids(
    base: dict[str, np.ndarray],
    footprint: np.ndarray,
    external_dir: Path,
) -> dict[str, np.ndarray]:
    """Compute the 5 frozen static H79 grids (knowledge/39 §3)."""
    foot = np.asarray(footprint, dtype=bool)
    if not foot.any():
        raise ValueError("footprint must contain at least one valid pixel")
    core = binary_erosion(foot, iterations=4)
    if not core.any():
        core = foot
    out: dict[str, np.ndarray] = {}

    # 1. H79_aniso_conduit_plume: 4-basis strike-steered hydrothermal & Quaternary-vent diffusion
    q0 = _load_label_free_conduit_impulses(external_dir, foot.shape)
    g_iso = nearest_fill(np.asarray(base["iso_grav_anom"], dtype=np.float32))
    h_base = nearest_fill(np.asarray(base["depth_to_base_surf"], dtype=np.float32))
    z_elev = nearest_fill(np.asarray(base["det_elev"], dtype=np.float32))

    c2_g, s2_g, k_g = _strike_director_doubled(g_iso)
    c2_b, s2_b, k_b = _strike_director_doubled(h_base)
    c2_e, s2_e, k_e = _strike_director_doubled(z_elev)
    del h_base, z_elev

    wt = 0.45 * k_g + 0.35 * k_b + 0.20 * k_e + 1e-6
    c2_bar = (0.45 * k_g * c2_g + 0.35 * k_b * c2_b + 0.20 * k_e * c2_e) / wt
    s2_bar = (0.45 * k_g * s2_g + 0.35 * k_b * s2_b + 0.20 * k_e * s2_e) / wt
    norm_cs = np.hypot(c2_bar, s2_bar) + 1e-6
    c2_bar = (c2_bar / norm_cs).astype(np.float32)
    s2_bar = (s2_bar / norm_cs).astype(np.float32)
    del c2_g, s2_g, k_g, c2_b, s2_b, k_b, c2_e, s2_e, k_e, wt, norm_cs

    p_num = np.zeros(foot.shape, dtype=np.float32)
    p_den = np.zeros(foot.shape, dtype=np.float32)
    for alpha_cw in (0.0, 45.0, 90.0, 135.0):
        # Convert clockwise-from-North strike alpha_cw to math angle beta = atan2(ty, tx) = atan2(-cos(a), sin(a))
        a_rad = np.deg2rad(alpha_cw)
        tx, ty = np.sin(a_rad), -np.cos(a_rad)
        c2_k = float(tx * tx - ty * ty)
        s2_k = float(2.0 * tx * ty)
        kern = _elliptical_gaussian_kernel(12.0, 2.0, alpha_cw, truncate=3.0)
        resp = np.maximum(fftconvolve(q0, kern, mode="same").astype(np.float32), 0.0)
        align = np.maximum(0.0, 0.5 * (1.0 + c2_bar * c2_k + s2_bar * s2_k))
        wk = (align * align + 0.02).astype(np.float32)
        p_num += wk * resp
        p_den += wk
    p_aniso = p_num / np.maximum(p_den, 1e-6)
    out["H79_aniso_conduit_plume"] = pct_scale_eroded(np.log1p(10.0 * p_aniso), foot)
    del q0, c2_bar, s2_bar, p_num, p_den, p_aniso
    gc.collect()

    # 2. H79_demag_argillic_crest: shallow magnetite-oxidation deficit x high-pass MT clay x K-Th alteration
    rtp = nearest_fill(np.asarray(base["rtp"], dtype=np.float32))
    cond = np.log1p(np.maximum(nearest_fill(np.asarray(base["cond_surf"], dtype=np.float32)), 0.0))

    with rasterio.open(external_dir / "geodawn_extensions_u8.tif") as esrc:
        up150_raw = esrc.read(4)
    up150_ok = up150_raw > 0
    up150_f = nearest_fill(np.where(up150_ok, up150_raw.astype(np.float32), np.nan))
    del up150_raw

    z_rtp = _zscore_core(rtp, core)
    z_up150 = _zscore_core(up150_f, core & up150_ok)
    demag_raw = np.where(up150_ok, np.maximum(gaussian_filter(z_up150 - z_rtp, 1.5), 0.0), 0.0)
    d_mag = pct_scale_eroded(demag_raw, foot)
    del up150_f, up150_ok, z_rtp, z_up150, demag_raw

    c_clay = pct_scale_eroded(np.maximum(cond - gaussian_filter(cond, 12.0), 0.0), foot)

    with rasterio.open(external_dir / "geodawn_rad_u8.tif") as rsrc:
        k_u8 = rsrc.read(1)
        th_u8 = rsrc.read(2)
    rad_ok = (k_u8 > 0) & (th_u8 > 0)
    k_f = nearest_fill(np.where(rad_ok, k_u8.astype(np.float32), np.nan))
    th_f = nearest_fill(np.where(rad_ok, th_u8.astype(np.float32), np.nan))
    del k_u8, th_u8
    zk = _zscore_core(k_f, core & rad_ok)
    zth = _zscore_core(th_f, core & rad_ok)
    k_alt_raw = np.where(rad_ok, np.maximum(gaussian_filter(zk - 0.7 * zth, 1.5), 0.0), 0.0)
    k_alt = pct_scale_eroded(k_alt_raw, foot)
    del rad_ok, k_f, th_f, zk, zth, k_alt_raw

    out["H79_demag_argillic_crest"] = pct_scale_eroded(
        d_mag * np.sqrt((0.20 + 0.80 * c_clay) * (0.20 + 0.80 * k_alt)),
        foot,
    )
    del d_mag, c_clay, k_alt
    gc.collect()

    # 3. H79_euler_contact_index: unit-consistent N=0 fault-contact Euler shallow-subcrop ridge
    gvg = gaussian_filter(nearest_fill(np.asarray(base["iso_grav_anom_vg"], dtype=np.float32)), 1.0)
    tvg_km = 1000.0 * gaussian_filter(nearest_fill(np.asarray(base["tmi_vg"], dtype=np.float32)), 1.0)

    def _euler_contact_prox(field_arr: np.ndarray, vz_km: np.ndarray) -> np.ndarray:
        f_hp = gaussian_filter(field_arr, 1.0) - gaussian_filter(field_arr, 15.0)
        gy, gx = np.gradient(gaussian_filter(field_arr, 1.5))
        hf = 10.0 * np.hypot(gx, gy)  # field_units / km on 100 m grid
        as_f = np.hypot(hf, vz_km)
        eps = float(np.percentile(as_f[core], 25.0))
        z_eul = np.abs(f_hp) / (as_f + max(eps, 1e-6))
        prox = (1.0 / (1.0 + z_eul / 0.40)) * pct_scale_eroded(np.log1p(as_f), foot)
        return prox.astype(np.float32)

    e_grav = _euler_contact_prox(g_iso, gvg)
    e_mag = _euler_contact_prox(rtp, tvg_km)
    del rtp, gvg, tvg_km
    out["H79_euler_contact_index"] = pct_scale_eroded(
        ridge_strength(np.sqrt(e_grav * e_mag).astype(np.float32), 1.5),
        foot,
    )
    del e_grav, e_mag
    gc.collect()

    # 4. H79_grav_mt_gouge_juxtapose: antiparallel gravity-vs-MT gouge cross-gradient coupling
    ggy, ggx = np.gradient(gaussian_filter(g_iso, 2.0))
    mgy, mgx = np.gradient(gaussian_filter(cond, 2.0))
    del g_iso, cond
    mg = np.hypot(ggx, ggy)
    mm = np.hypot(mgx, mgy)
    cos_t = (ggx * mgx + ggy * mgy) / (mg * mm + 1e-12)
    amp = np.sqrt(pct_scale_eroded(np.log1p(mg), foot) * pct_scale_eroded(np.log1p(mm), foot))
    j_gm = (np.maximum(0.0, -cos_t) + 0.35 * np.abs(cos_t)) * amp
    out["H79_grav_mt_gouge_juxtapose"] = pct_scale_eroded(
        ridge_strength(j_gm.astype(np.float32), 1.5),
        foot,
    )
    del ggy, ggx, mgy, mgx, mg, mm, cos_t, amp, j_gm
    gc.collect()

    # 5. H79_sgmc_coulomb_react: directional Coulomb reactivation of pre-Quaternary SGMC bedrock faults
    with rasterio.open(external_dir / "derived_sgmc_faults_100m_u8.tif") as ssrc:
        sgmc_b = ssrc.read(1) > 0
    if sgmc_b.any():
        d_sgmc = distance_transform_edt(~sgmc_b).astype(np.float32)
        c2_s, s2_s, _ = _strike_director_doubled(sgmc_b.astype(np.float32), sig_grad=2.0, sig_ten=2.5)
        # Convert math doubled-strike angle beta = 0.5*atan2(s2_s, c2_s) in (-pi/2, pi/2] to cw-from-North [0, 180)
        beta = 0.5 * np.arctan2(s2_s, c2_s)
        strike_cw = (np.rad2deg(np.arctan2(np.cos(beta), -np.sin(beta))) + 360.0) % 180.0
        d_norm = np.minimum(np.abs(strike_cw - 15.0), 180.0 - np.abs(strike_cw - 15.0))
        d_walk = np.minimum(np.abs(strike_cw - 145.0), 180.0 - np.abs(strike_cw - 145.0))
        f_az = np.maximum(np.cos(np.deg2rad(d_norm)) ** 2, 0.85 * (np.cos(np.deg2rad(d_walk)) ** 2))
        e2nd = pct_scale_eroded(nearest_fill(np.asarray(base["geod_2ndinv"], dtype=np.float32)), foot)
        ieq = pct_scale_eroded(
            np.log1p(np.maximum(nearest_fill(np.asarray(base["ieq_n100a15"], dtype=np.float32)), 0.0)),
            foot,
        )
        sgmc_raw = np.exp(-d_sgmc / 4.0) * f_az * (0.30 + 0.45 * e2nd + 0.25 * ieq)
        out["H79_sgmc_coulomb_react"] = pct_scale_eroded(sgmc_raw.astype(np.float32), foot)
        del d_sgmc, c2_s, s2_s, beta, strike_cw, d_norm, d_walk, f_az, e2nd, ieq, sgmc_raw
    else:
        out["H79_sgmc_coulomb_react"] = np.zeros(foot.shape, dtype=np.float32)
    del sgmc_b
    gc.collect()

    return out


def build_h79_sidecar(
    work: Path,
    external_dir: Path,
    out_path: Path | None = None,
    force: bool = False,
) -> tuple[np.ndarray, list[str]]:
    """Build or open ``(5, N_foot)`` float32 memmap sidecar for ``H79_ALL_NAMES``."""
    out_p = Path(out_path) if out_path is not None else (Path(work) / "h79_cthm_sidecar.npy")
    meta_p = Path(str(out_p) + ".names.json")
    if out_p.exists() and meta_p.exists() and not force:
        names = json.loads(meta_p.read_text())
        if names == H79_ALL_NAMES:
            return np.load(out_p, mmap_mode="r"), names

    foot = np.load(Path(work) / "bands" / "_footprint.npy")
    fi = np.flatnonzero(foot.ravel())
    base = load_base(Path(work) / "bands")
    grids = compute_h79_grids(base, foot, Path(external_dir))
    del base
    out_p.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(out_p, mode="w+", dtype=np.float32, shape=(len(H79_ALL_NAMES), fi.size))
    for i, nm in enumerate(H79_ALL_NAMES):
        vec = grids[nm].ravel()[fi].astype(np.float32)
        if not np.isfinite(vec).all() or float(vec.min()) < 0.0 or float(vec.max()) > 1.0:
            raise AssertionError(f"{nm} violated [0, 1] finite invariant")
        mm[i] = vec
    mm.flush()
    del mm, grids
    gc.collect()
    meta_p.write_text(json.dumps(H79_ALL_NAMES))
    return np.load(out_p, mmap_mode="r"), list(H79_ALL_NAMES)
