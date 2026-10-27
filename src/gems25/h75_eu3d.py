"""H75-1 (EU3D-POE) static 3-D Euler homogeneity, basement-strike criticality & MT-thermal sidecar.

Pre-registered in ``knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md`` (committed at
``3053f69`` before writing this module or fitting any model).

Design invariants:
* Strictly static, label-free, and topography-free: ``labels.tif``, ``existing_faults.tif``,
  ``gdr_qfaults_traces.csv``, ``dist_known_fault_px``, ``det_elev``, ``det_elev_slope``, and
  ``lidar_scarp_features_u8.tif`` are NEVER opened or referenced by ``compute_h75_eu3d_grids`` or
  ``load_h75_eu3d_sidecar``.
* All four ``H75_EU3D_NAMES`` columns are finite ``float32`` in ``[0, 1]`` across all ``5,167,373``
  footprint pixels.
* Sliding-window 3-D Euler deconvolution uses exact separable window moments (verified to ``<1e-10``
  against brute-force per-window ``np.linalg.lstsq``) with harmonic FFT downward vertical derivatives
  matching horizontal derivative units (``[field]/m``).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import correlate1d, gaussian_filter, uniform_filter1d

from .features import load_base, nearest_fill, ridge_strength
from .h74_rmps import CELL_M, PAD_PX, harmonic_vertical_derivative_fft, pct_scale_eroded

H75_EU3D_NAMES = [
    "H75_euler_grav_contact",
    "H75_euler_mag_contact",
    "H75_anderson_slip_dilation",
    "H75_mt_thermal_conduit",
]

# Great Basin WNW-ESE regional minimum horizontal stress (N65W-S65E, azimuth 115 deg clockwise from North).
# In EPSG:32611 raster coordinates (+x = +col = East, +y = +row = South):
#   North = (0, -1), East = (+1, 0) -> u_x = sin(115 deg), u_y = -cos(115 deg).
SHMIN_AZIMUTH_DEG = 115.0
SHMIN_UX = float(np.sin(np.deg2rad(SHMIN_AZIMUTH_DEG)))   # +0.906307787
SHMIN_UY = float(-np.cos(np.deg2rad(SHMIN_AZIMUTH_DEG)))  # +0.422618262


def _sep_mean(arr: np.ndarray, win: int) -> np.ndarray:
    """Exact unweighted W x W window mean using reflect boundary conditions."""
    tmp = uniform_filter1d(arr, size=win, axis=0, mode="reflect")
    return uniform_filter1d(tmp, size=win, axis=1, mode="reflect")


def _sep_corr_dx(arr: np.ndarray, k_vec: np.ndarray, win: int) -> np.ndarray:
    """Window mean of ``delta_x * arr`` where ``delta_x = (col - col_c)`` in pixel units."""
    tmp = uniform_filter1d(arr, size=win, axis=0, mode="reflect")
    return correlate1d(tmp, weights=k_vec / float(win), axis=1, mode="reflect")


def _sep_corr_dy(arr: np.ndarray, k_vec: np.ndarray, win: int) -> np.ndarray:
    """Window mean of ``delta_y * arr`` where ``delta_y = (row - row_c)`` in pixel units."""
    tmp = correlate1d(arr, weights=k_vec / float(win), axis=0, mode="reflect")
    return uniform_filter1d(tmp, size=win, axis=1, mode="reflect")


def _sep_corr_dx2(arr: np.ndarray, k2_vec: np.ndarray, win: int) -> np.ndarray:
    """Window mean of ``delta_x^2 * arr``."""
    tmp = uniform_filter1d(arr, size=win, axis=0, mode="reflect")
    return correlate1d(tmp, weights=k2_vec / float(win), axis=1, mode="reflect")


def _sep_corr_dy2(arr: np.ndarray, k2_vec: np.ndarray, win: int) -> np.ndarray:
    """Window mean of ``delta_y^2 * arr``."""
    tmp = correlate1d(arr, weights=k2_vec / float(win), axis=0, mode="reflect")
    return uniform_filter1d(tmp, size=win, axis=1, mode="reflect")


def _sep_corr_dxdy(arr: np.ndarray, k_vec: np.ndarray) -> np.ndarray:
    """Window mean of ``delta_x * delta_y * arr``."""
    win = int(k_vec.size)
    tmp = correlate1d(arr, weights=k_vec / float(win), axis=0, mode="reflect")
    return correlate1d(tmp, weights=k_vec / float(win), axis=1, mode="reflect")


def euler_3d_window_solve(
    field: np.ndarray,
    tx_m: np.ndarray,
    ty_m: np.ndarray,
    tz_m: np.ndarray,
    n_indices: tuple[float, ...] = (0.5, 2.0),
    win: int = 7,
    cell_m: float = CELL_M,
    damping_rel: float = 1e-6,
    chunk_rows: int = 256,
) -> dict[float, dict[str, np.ndarray]]:
    """Vectorized sliding-window 3-D Euler homogeneity least-squares solver.

    Solves at every pixel center ``(x_c, y_c)`` over a ``win x win`` window:
        ``dx0 * T_x + dy0 * T_y + z0 * T_z + (N * B) * 1 = dx * T_x + dy * T_y + N * T``
    where ``dx = x - x_c``, ``dy = y - y_c``, ``(dx0, dy0) = (x0 - x_c, y0 - y_c)`` in meters,
    and ``z0 > 0`` is source depth below ``z = 0`` in meters (``T_z`` positive downward).

    Returns per structural index ``N`` a dict with ``dx0_m``, ``dy0_m``, ``z0_m``, ``nb``,
    ``mse``, and ``tss`` (all ``float32`` arrays of shape ``field.shape``).
    """
    if win < 3 or win % 2 != 1:
        raise ValueError("win must be an odd integer >= 3")
    if cell_m <= 0:
        raise ValueError("cell_m must be > 0")
    t = np.asarray(field, dtype=np.float64)
    # Work in dimensionless pixel coordinates u = dx / cell_m, gx = cell_m * T_x
    gx = np.asarray(tx_m, dtype=np.float64) * float(cell_m)
    gy = np.asarray(ty_m, dtype=np.float64) * float(cell_m)
    gz = np.asarray(tz_m, dtype=np.float64) * float(cell_m)
    if not (t.shape == gx.shape == gy.shape == gz.shape and t.ndim == 2):
        raise ValueError("field and derivatives must be aligned 2-D arrays")

    half = win // 2
    k_vec = np.arange(-half, half + 1, dtype=np.float64)
    k2_vec = k_vec * k_vec

    h, w = t.shape
    results: dict[float, dict[str, np.ndarray]] = {
        float(n): {
            "dx0_m": np.empty((h, w), dtype=np.float32),
            "dy0_m": np.empty((h, w), dtype=np.float32),
            "z0_m": np.empty((h, w), dtype=np.float32),
            "nb": np.empty((h, w), dtype=np.float32),
            "mse": np.empty((h, w), dtype=np.float32),
            "tss": np.empty((h, w), dtype=np.float32),
        }
        for n in n_indices
    }

    # Reflect-pad along rows once by `half` pixels so strip-wise separable filtering is exact
    t_pad = np.pad(t, ((half, half), (0, 0)), mode="reflect")
    gx_pad = np.pad(gx, ((half, half), (0, 0)), mode="reflect")
    gy_pad = np.pad(gy, ((half, half), (0, 0)), mode="reflect")
    gz_pad = np.pad(gz, ((half, half), (0, 0)), mode="reflect")
    del t, gx, gy, gz

    for r0 in range(0, h, chunk_rows):
        r1 = min(r0 + chunk_rows, h)
        ch = r1 - r0
        psl = slice(r0, r1 + 2 * half)
        inner = slice(half, half + ch)
        out_sl = slice(r0, r1)

        ts = t_pad[psl]
        gxs = gx_pad[psl]
        gys = gy_pad[psl]
        gzs = gz_pad[psl]

        g00 = _sep_mean(gxs * gxs, win)[inner]
        g01 = _sep_mean(gxs * gys, win)[inner]
        g02 = _sep_mean(gxs * gzs, win)[inner]
        g03 = _sep_mean(gxs, win)[inner]
        g11 = _sep_mean(gys * gys, win)[inner]
        g12 = _sep_mean(gys * gzs, win)[inner]
        g13 = _sep_mean(gys, win)[inner]
        g22 = _sep_mean(gzs * gzs, win)[inner]
        g23 = _sep_mean(gzs, win)[inner]

        q0 = (_sep_corr_dx(gxs * gxs, k_vec, win) + _sep_corr_dy(gxs * gys, k_vec, win))[inner]
        q1 = (_sep_corr_dx(gys * gxs, k_vec, win) + _sep_corr_dy(gys * gys, k_vec, win))[inner]
        q2 = (_sep_corr_dx(gzs * gxs, k_vec, win) + _sep_corr_dy(gzs * gys, k_vec, win))[inner]
        q3 = (_sep_corr_dx(gxs, k_vec, win) + _sep_corr_dy(gys, k_vec, win))[inner]

        at0 = _sep_mean(gxs * ts, win)[inner]
        at1 = _sep_mean(gys * ts, win)[inner]
        at2 = _sep_mean(gzs * ts, win)[inner]
        at3 = _sep_mean(ts, win)[inner]

        s2_mean = (
            _sep_corr_dx2(gxs * gxs, k2_vec, win)
            + _sep_corr_dy2(gys * gys, k2_vec, win)
            + 2.0 * _sep_corr_dxdy(gxs * gys, k_vec)
        )[inner]
        st_mean = (_sep_corr_dx(ts * gxs, k_vec, win) + _sep_corr_dy(ts * gys, k_vec, win))[inner]
        t2_mean = _sep_mean(ts * ts, win)[inner]

        G = np.empty((ch, w, 4, 4), dtype=np.float64)
        G[:, :, 0, 0] = g00
        G[:, :, 0, 1] = G[:, :, 1, 0] = g01
        G[:, :, 0, 2] = G[:, :, 2, 0] = g02
        G[:, :, 0, 3] = G[:, :, 3, 0] = g03
        G[:, :, 1, 1] = g11
        G[:, :, 1, 2] = G[:, :, 2, 1] = g12
        G[:, :, 1, 3] = G[:, :, 3, 1] = g13
        G[:, :, 2, 2] = g22
        G[:, :, 2, 3] = G[:, :, 3, 2] = g23
        G[:, :, 3, 3] = 1.0

        G_raw = G.copy()
        tr3 = (G[:, :, 0, 0] + G[:, :, 1, 1] + G[:, :, 2, 2]) / 3.0
        lam = float(damping_rel) * tr3 + 1e-12
        G[:, :, 0, 0] += lam
        G[:, :, 1, 1] += lam
        G[:, :, 2, 2] += lam
        G[:, :, 3, 3] += 1e-12

        k_n = len(n_indices)
        B_rhs = np.empty((ch, w, 4, k_n), dtype=np.float64)
        for j, n_val in enumerate(n_indices):
            nf = float(n_val)
            B_rhs[:, :, 0, j] = q0 + nf * at0
            B_rhs[:, :, 1, j] = q1 + nf * at1
            B_rhs[:, :, 2, j] = q2 + nf * at2
            B_rhs[:, :, 3, j] = q3 + nf * at3

        theta = np.linalg.solve(G, B_rhs)  # (ch, w, 4, k_n)

        for j, n_val in enumerate(n_indices):
            nf = float(n_val)
            th = theta[:, :, :, j]
            b_vec = B_rhs[:, :, :, j]
            y2 = s2_mean + 2.0 * nf * st_mean + (nf * nf) * t2_mean
            y_mean = q3 + nf * at3
            tss = np.maximum(y2 - y_mean * y_mean, 0.0)
            g_th = np.einsum("...ij,...j->...i", G_raw, th)
            mse = np.maximum(
                np.einsum("...i,...i->...", th, g_th) - 2.0 * np.einsum("...i,...i->...", th, b_vec) + y2,
                0.0,
            )

            out = results[nf]
            out["dx0_m"][out_sl] = (th[:, :, 0] * float(cell_m)).astype(np.float32)
            out["dy0_m"][out_sl] = (th[:, :, 1] * float(cell_m)).astype(np.float32)
            out["z0_m"][out_sl] = (th[:, :, 2] * float(cell_m)).astype(np.float32)
            out["nb"][out_sl] = th[:, :, 3].astype(np.float32)
            out["mse"][out_sl] = mse.astype(np.float32)
            out["tss"][out_sl] = tss.astype(np.float32)

    return results


def euler_contact_discrimination_score(
    field: np.ndarray,
    foot: np.ndarray,
    *,
    n_contact: float = 0.5,
    n_plug: float = 2.0,
    smooth_sigma: float = 1.5,
    win: int = 7,
    cell_m: float = CELL_M,
    pad: int = PAD_PX,
) -> np.ndarray:
    """Compute the frozen [0, 1] Euler steep-contact vs equant-plug score (knowledge/38 §3)."""
    f = nearest_fill(np.asarray(field, dtype=np.float32))
    fs = gaussian_filter(f, float(smooth_sigma)) if smooth_sigma > 0 else f
    ty_m_64, tx_m_64 = np.gradient(fs.astype(np.float64), float(cell_m))
    tx_m = tx_m_64.astype(np.float32)
    ty_m = ty_m_64.astype(np.float32)
    del tx_m_64, ty_m_64
    tz_m = harmonic_vertical_derivative_fft(fs, cell_m=cell_m, pad=pad)

    sol = euler_3d_window_solve(
        fs,
        tx_m,
        ty_m,
        tz_m,
        n_indices=(float(n_contact), float(n_plug)),
        win=win,
        cell_m=cell_m,
    )
    del fs, tz_m
    sc = sol[float(n_contact)]
    sp = sol[float(n_plug)]

    r0 = np.hypot(sc["dx0_m"], sc["dy0_m"])
    z0 = sc["z0_m"]
    rel_err_c = sc["mse"] / (sc["tss"] + 1e-6)
    rel_err_p = sp["mse"] / (sp["tss"] + 1e-6)
    r2_c = np.clip(1.0 - rel_err_c, 0.0, 1.0)
    plug_reject = np.clip(
        0.5 + 2.0 * (rel_err_p - rel_err_c) / (rel_err_p + rel_err_c + 1e-4),
        0.0,
        1.0,
    )
    apex_prox = np.exp(-0.5 * (r0 / 250.0) ** 2)
    z_ok = (z0 >= 50.0) & (z0 <= 3500.0)
    z_safe = np.where(z_ok, np.maximum(z0, 50.0), 600.0)
    depth_win = np.where(z_ok, np.exp(-((np.log(z_safe / 600.0) / 1.25) ** 2)), 0.0)

    # Weight by mild horizontal gradient amplitude so flat zero-anomaly interiors do not fire
    grad_amp = pct_scale_eroded(np.hypot(tx_m, ty_m).astype(np.float32), foot)
    raw = (r2_c * plug_reject * apex_prox * depth_win * np.sqrt(grad_amp)).astype(np.float32)
    s_base = pct_scale_eroded(raw, foot)
    s_ridge = pct_scale_eroded(ridge_strength(raw, 1.5), foot)
    return pct_scale_eroded(0.5 * s_base + 0.5 * s_ridge, foot)


def compute_h75_eu3d_grids(
    base: dict[str, np.ndarray],
    footprint: np.ndarray,
    d_gdr_tmax5km: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Compute the 4 frozen static H75_EU3D grids (knowledge/38 §3)."""
    foot = np.asarray(footprint, dtype=bool)
    if not foot.any():
        raise ValueError("footprint must contain at least one valid pixel")

    # 1. H75_euler_grav_contact: N_c=0.5 basement step vs N_p=2.0 plug on isostatic gravity
    g_iso = nearest_fill(np.asarray(base["iso_grav_anom"], dtype=np.float32))
    euler_grav = euler_contact_discrimination_score(
        g_iso, foot, n_contact=0.5, n_plug=2.0, smooth_sigma=1.5, win=7
    )

    # 2. H75_euler_mag_contact: N_c=0.5 faulted volcanic/dike contact vs N_p=2.5 plug on RTP
    rtp = nearest_fill(np.asarray(base["rtp"], dtype=np.float32))
    euler_mag = euler_contact_discrimination_score(
        rtp, foot, n_contact=0.5, n_plug=2.5, smooth_sigma=1.5, win=7
    )
    del rtp

    # 3. H75_anderson_slip_dilation: Morris (1996) resolved dilation & shear tendency on basement strike
    gs2 = gaussian_filter(g_iso, 2.0)
    gy, gx = np.gradient(gs2)  # +x = East, +y = South
    jxx = gaussian_filter(gx * gx, 4.0)
    jyy = gaussian_filter(gy * gy, 4.0)
    jxy = gaussian_filter(gx * gy, 4.0)
    # Principal gradient eigenvector angle phi in (+x East, +y South)
    phi = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy)
    nx = np.cos(phi)
    ny = np.sin(phi)
    cos2_alpha = (nx * SHMIN_UX + ny * SHMIN_UY) ** 2
    t_dil = cos2_alpha  # peaks (=1) on NNE-SSW normal faults perpendicular to N65W-S65E SHmin
    t_shr = 4.0 * cos2_alpha * (1.0 - cos2_alpha)  # peaks (=1) on +/-45 deg Walker Lane / ENE relays

    dil_n = pct_scale_eroded(
        np.maximum(nearest_fill(np.asarray(base["geod_dilaterate"], dtype=np.float32)), 0.0), foot
    )
    shr_n = pct_scale_eroded(
        np.maximum(nearest_fill(np.asarray(base["geod_shearrate"], dtype=np.float32)), 0.0), foot
    )
    g_grad_n = pct_scale_eroded(np.hypot(gx, gy).astype(np.float32), foot)
    anderson_crit = pct_scale_eroded(
        (g_grad_n * (0.65 * t_dil * dil_n + 0.35 * t_shr * shr_n)).astype(np.float32),
        foot,
    )
    del gs2, gy, gx, jxx, jyy, jxy, phi, nx, ny, cos2_alpha, t_dil, t_shr, dil_n, shr_n, g_grad_n, g_iso

    # 4. H75_mt_thermal_conduit: basin-thickness-normalized MT conductance x heat-flow & Euler root
    cond_raw = np.maximum(nearest_fill(np.asarray(base["cond_surf"], dtype=np.float32)), 0.0)
    log_c = np.log1p(cond_raw)
    dc_hp = np.maximum(log_c - gaussian_filter(log_c, 25.0), 0.0)
    h_base = np.maximum(nearest_fill(np.asarray(base["depth_to_base_surf"], dtype=np.float32)), 0.0)
    cond_norm_basin = pct_scale_eroded(
        (dc_hp / (1.0 + 0.5 * np.log1p(h_base / 500.0))).astype(np.float32),
        foot,
    )

    tc = nearest_fill(np.asarray(base["tc"], dtype=np.float32))
    tc_hp = pct_scale_eroded(np.maximum(tc - gaussian_filter(tc, 30.0), 0.0), foot)
    if d_gdr_tmax5km is not None:
        gdr_t = pct_scale_eroded(
            np.maximum(nearest_fill(np.asarray(d_gdr_tmax5km, dtype=np.float32)), 0.0), foot
        )
        therm = np.clip(tc_hp + 0.30 * gdr_t, 0.0, 1.0)
    else:
        therm = tc_hp

    euler_root = np.maximum(euler_grav, euler_mag)
    mt_thermal_conduit = pct_scale_eroded(
        (cond_norm_basin * np.sqrt(therm * (0.15 + 0.85 * euler_root))).astype(np.float32),
        foot,
    )

    out = {
        "H75_euler_grav_contact": euler_grav,
        "H75_euler_mag_contact": euler_mag,
        "H75_anderson_slip_dilation": anderson_crit,
        "H75_mt_thermal_conduit": mt_thermal_conduit,
    }
    for k, v in out.items():
        clean = np.where(foot, np.clip(np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0), 0.0, 1.0), 0.0)
        out[k] = clean.astype(np.float32)
    return out


def poe_combine(p_scarp: np.ndarray, p_root: np.ndarray, gamma: float = 0.50) -> np.ndarray:
    """Two-stage multiplicative Product-of-Experts ``p_scarp^(1 - gamma) * p_root^gamma`` in [0, 1]."""
    if not (0.0 <= float(gamma) <= 1.0):
        raise ValueError("gamma must lie in [0, 1]")
    ps = np.clip(np.nan_to_num(np.asarray(p_scarp, dtype=np.float64), nan=0.0), 0.0, 1.0)
    pr = np.clip(np.nan_to_num(np.asarray(p_root, dtype=np.float64), nan=0.0), 0.0, 1.0)
    if ps.shape != pr.shape:
        raise ValueError("p_scarp and p_root must have identical shapes")
    g = float(gamma)
    out = np.power(ps, 1.0 - g) * np.power(pr, g)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def load_h75_eu3d_sidecar(work: Path, fi: np.ndarray) -> np.ndarray:
    """Build or load cached ``(4, n_footprint)`` float32 memmap for ``H75_EU3D_NAMES``."""
    work = Path(work)
    out_path = work / "h75_eu3d.npy"
    meta_path = work / "h75_eu3d.names.json"
    fi_arr = np.asarray(fi)
    if out_path.exists() and meta_path.exists():
        names = json.loads(meta_path.read_text())
        if names == H75_EU3D_NAMES:
            mm = np.load(out_path, mmap_mode="r")
            if mm.shape == (len(H75_EU3D_NAMES), fi_arr.size):
                return mm

    foot = np.load(work / "bands" / "_footprint.npy")
    base = load_base(work / "bands")

    # Optionally pull D_gdr_tmax5km from static_ABCD.npy (label-free, static GDR spring/well Tmax)
    gdr_grid = None
    static_path = work / "static_ABCD.npy"
    static_names_path = work / "static_ABCD.npy.names.json"
    if static_path.exists() and static_names_path.exists():
        s_names = json.loads(static_names_path.read_text())
        if "D_gdr_tmax5km" in s_names:
            s_mm = np.load(static_path, mmap_mode="r")
            gdr_grid = np.zeros(foot.shape, dtype=np.float32)
            gdr_grid.ravel()[fi_arr] = np.asarray(s_mm[s_names.index("D_gdr_tmax5km")], dtype=np.float32)

    grids = compute_h75_eu3d_grids(base, foot, d_gdr_tmax5km=gdr_grid)
    mm = np.lib.format.open_memmap(
        out_path,
        mode="w+",
        dtype=np.float32,
        shape=(len(H75_EU3D_NAMES), fi_arr.size),
    )
    for j, name in enumerate(H75_EU3D_NAMES):
        vec = grids[name].ravel()[fi_arr]
        if not np.isfinite(vec).all() or (vec < 0.0).any() or (vec > 1.0).any():
            raise ValueError(f"H75 sidecar column {name} failed [0, 1] finite check")
        mm[j] = vec
    mm.flush()
    meta_path.write_text(json.dumps(H75_EU3D_NAMES) + "\n")
    return np.load(out_path, mmap_mode="r")
