"""H38 · One-Sided Monoclinal Scarp Polarity, Meso-Scale Scarp Director Coherence &
Hydrothermal Magnetite-Destruction Trough (OSPC) crossed with Exact 300 m Submodular
Multi-Scale Skeleton Coverage (Session 8, pre-registered in ``knowledge/25_*``).

All four static feature columns are strictly catalogue-free (computed from ``02_rtp``,
``13_iso_grav_anom``, ``17_cond_surf``, and ``external/lidar_scarp_features_u8.tif``).
``submodular_skeleton_dots`` maximizes expected official 300 m triangular-kernel
``TP_w`` on the multi-scale ridge skeleton ``ridge_nms(1.0) | ridge_nms(2.0)`` via
exact Minoux (1978) lazy-greedy selection on Bayes-calibrated posteriors.
"""

from __future__ import annotations

from array import array
import heapq
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import correlate, gaussian_filter

from .features import LIDAR_BANDS, LIDAR_QUANT, dequantize, nearest_fill, ridge_strength
from .h34 import upward_continue_multi
from .metric import RADIUS_PX, _OFFS
from .thinning import ridge_nms

H38_NAMES: tuple[str, ...] = (
    "H38_monoclinal_polarity",
    "H38_meso_scarp_coh",
    "H38_subsurf_strike_align",
    "H38_mag_destruction_trough",
)

MESO_SIGMA_PX: float = 6.0
SUBSURF_GRAD_SIGMA_PX: float = 2.0
RTP_SHALLOW_DZ_M: float = 400.0
MAG_TROUGH_SIGMA_PX: float = 2.0
DEFAULT_POOL_KFRAC: float = 0.045
DEFAULT_MIN_DIST_FLOOR_PX: float = 1.5


def _pct_norm_foot(a: np.ndarray, foot: np.ndarray, lo: float = 1.0, hi: float = 99.0) -> np.ndarray:
    v = a[foot]
    v = v[np.isfinite(v)]
    if v.size == 0:
        return np.zeros_like(a, dtype=np.float32)
    p_lo, p_hi = np.percentile(v, [lo, hi])
    span = float(max(p_hi - p_lo, 1e-6))
    return np.clip((a - float(p_lo)) / span, 0.0, 1.0).astype(np.float32)


def _contour_spin2_weighted(field_filled: np.ndarray, foot: np.ndarray, sigma_px: float) -> tuple[np.ndarray, np.ndarray]:
    """Magnitude-normalized spin-2 contour-tangent director ``(c2, s2)`` in ``(x=col, y=row)`` convention."""
    sm = gaussian_filter(np.asarray(field_filled, dtype=np.float32), float(sigma_px))
    gy, gx = np.gradient(sm)
    mag2 = gx * gx + gy * gy
    mag = np.sqrt(mag2)
    fvals = mag[foot]
    p90 = float(np.percentile(fvals[np.isfinite(fvals)], 90.0)) if fvals.size else 1.0
    scale = max(p90, 1e-6)
    wt = np.clip(mag / scale, 0.0, 3.0).astype(np.float32)
    denom = mag2 + 1e-12
    # Matches src/gems25/features.py:249-250: c2 = -cos(phi2) = (gy^2 - gx^2)/(gx^2 + gy^2),
    # s2 = -sin(phi2) = -2*gx*gy/(gx^2 + gy^2).
    c2 = ((gy * gy - gx * gx) / denom).astype(np.float32)
    s2 = ((-2.0 * gx * gy) / denom).astype(np.float32)
    return (wt * c2).astype(np.float32), (wt * s2).astype(np.float32)


def compute_h38_ospc_grids(
    rtp_raw: np.ndarray,
    grav_raw: np.ndarray,
    cond_raw: np.ndarray,
    lidar_u8: np.ndarray,
    footprint: np.ndarray,
    *,
    cell_m: float = 100.0,
) -> dict[str, np.ndarray]:
    """Compute the 4 pre-registered H38-OSPC 2-D float32 feature grids (zero outside ``footprint``)."""
    foot = np.asarray(footprint, dtype=bool)
    if rtp_raw.shape != foot.shape or grav_raw.shape != foot.shape or cond_raw.shape != foot.shape:
        raise ValueError("rtp_raw, grav_raw, cond_raw, and footprint must share one 2-D shape")
    if lidar_u8.ndim != 3 or lidar_u8.shape[0] != len(LIDAR_BANDS) or lidar_u8.shape[1:] != foot.shape:
        raise ValueError(f"lidar_u8 must have shape ({len(LIDAR_BANDS)}, H, W)")

    bidx = {n: i for i, n in enumerate(LIDAR_BANDS)}
    v_mask = (lidar_u8[bidx["valid"]] > 0) & foot
    v_f = v_mask.astype(np.float32)

    def _lid(name: str) -> np.ndarray:
        raw = dequantize(lidar_u8[bidx[name]], *LIDAR_QUANT[name])
        return np.where(v_mask & np.isfinite(raw), raw, 0.0).astype(np.float32)

    d_face = _lid("downface_max")
    u_face = _lid("upface_max")
    ex_mean = _lid("ex_mean")
    step_max = _lid("step_max")
    coh100 = _lid("coh100")
    strike_deg = _lid("strike")

    # 1. H38_monoclinal_polarity: one-sided scarp asymmetry (monoclinal fault step vs V-shaped wash).
    p_mono = (np.abs(d_face - u_face) / (d_face + u_face + 1e-4) * ex_mean * coh100 * v_f).astype(np.float32)
    p_mono = np.where(foot, p_mono, 0.0).astype(np.float32)

    # 2. H38_meso_scarp_coh: ~1.5 km (sigma=6 px) spin-2 LiDAR scarp director resultant coherence.
    th2 = np.deg2rad(strike_deg) * 2.0
    c2_l = (np.cos(th2) * v_f).astype(np.float32)
    s2_l = (np.sin(th2) * v_f).astype(np.float32)
    w_l = (step_max * coh100 * v_f).astype(np.float32)
    del d_face, u_face, ex_mean, step_max, coh100, strike_deg, th2, v_f

    m_c = gaussian_filter(w_l * c2_l, MESO_SIGMA_PX).astype(np.float32)
    m_s = gaussian_filter(w_l * s2_l, MESO_SIGMA_PX).astype(np.float32)
    m_0 = gaussian_filter(w_l, MESO_SIGMA_PX).astype(np.float32)
    del w_l, c2_l, s2_l

    m_norm = np.sqrt(m_c * m_c + m_s * m_s).astype(np.float32)
    c_meso = np.clip(m_norm / (m_0 + 1e-6), 0.0, 1.0).astype(np.float32)
    c_meso = np.where(m_0 > 1e-5, c_meso, 0.0).astype(np.float32)
    meso_coh = (gaussian_filter(p_mono, MESO_SIGMA_PX) * c_meso).astype(np.float32)
    meso_coh = np.where(foot, meso_coh, 0.0).astype(np.float32)

    surf_c2 = (m_c / (m_norm + 1e-12)).astype(np.float32)
    surf_s2 = (m_s / (m_norm + 1e-12)).astype(np.float32)
    del m_c, m_s, m_0, m_norm

    # 3. H38_subsurf_strike_align & 4. H38_mag_destruction_trough
    rtp_f = nearest_fill(np.asarray(rtp_raw, dtype=np.float32))
    rtp_up400 = upward_continue_multi(rtp_f, [RTP_SHALLOW_DZ_M], cell_m=cell_m)[0]
    rtp_shallow = (rtp_f - rtp_up400).astype(np.float32)
    del rtp_f, rtp_up400

    grav_f = nearest_fill(np.asarray(grav_raw, dtype=np.float32))
    gc2, gs2 = _contour_spin2_weighted(grav_f, foot, SUBSURF_GRAD_SIGMA_PX)
    del grav_f
    mc2, ms2 = _contour_spin2_weighted(rtp_shallow, foot, SUBSURF_GRAD_SIGMA_PX)

    uc = gc2 + mc2
    us = gs2 + ms2
    del gc2, gs2, mc2, ms2
    unorm = np.sqrt(uc * uc + us * us) + 1e-12
    sub_c2 = (uc / unorm).astype(np.float32)
    sub_s2 = (us / unorm).astype(np.float32)
    del uc, us, unorm

    subsurf_align = ((surf_c2 * sub_c2 + surf_s2 * sub_s2) * c_meso).astype(np.float32)
    subsurf_align = np.where(foot, np.clip(subsurf_align, -1.0, 1.0), 0.0).astype(np.float32)
    del surf_c2, surf_s2, sub_c2, sub_s2, c_meso

    # Hydrothermal magnetite-destruction trough: crest of (-RTP_shallow) gated by shallow thermal conductivity.
    neg_rtp_trough = ridge_strength(-rtp_shallow, MAG_TROUGH_SIGMA_PX)
    del rtp_shallow
    cond_f = nearest_fill(np.asarray(cond_raw, dtype=np.float32))
    cond_gate = _pct_norm_foot(np.log1p(np.maximum(cond_f, 0.0)), foot)
    del cond_f
    mag_trough = np.where(foot, neg_rtp_trough * cond_gate, 0.0).astype(np.float32)

    return {
        "H38_monoclinal_polarity": p_mono,
        "H38_meso_scarp_coh": meso_coh,
        "H38_subsurf_strike_align": subsurf_align,
        "H38_mag_destruction_trough": mag_trough,
    }


def build_h38_ospc_columns(
    work_dir: Path,
    external_dir: Path,
    out_path: Path | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Build or load ``(4, n_foot)`` float32 sidecar ``work/h38_ospc_columns.npy``."""
    work_dir = Path(work_dir)
    external_dir = Path(external_dir)
    target = out_path if out_path is not None else (work_dir / "h38_ospc_columns.npy")
    names_path = Path(str(target) + ".names.json")
    if target.exists() and names_path.exists():
        names = json.loads(names_path.read_text())
        if tuple(names) == H38_NAMES:
            return np.load(target, mmap_mode="r"), list(names)

    band_dir = work_dir / "bands"
    foot = np.load(band_dir / "_footprint.npy")
    fi = np.flatnonzero(foot.ravel())
    rtp_raw = np.load(band_dir / "02_rtp.npy")
    grav_raw = np.load(band_dir / "13_iso_grav_anom.npy")
    cond_raw = np.load(band_dir / "17_cond_surf.npy")
    with rasterio.open(external_dir / "lidar_scarp_features_u8.tif") as src:
        lidar_u8 = src.read()

    grids = compute_h38_ospc_grids(rtp_raw, grav_raw, cond_raw, lidar_u8, foot)
    del rtp_raw, grav_raw, cond_raw, lidar_u8

    target.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(target, mode="w+", dtype=np.float32, shape=(len(H38_NAMES), fi.size))
    for i, nm in enumerate(H38_NAMES):
        vec = np.asarray(grids[nm], dtype=np.float32).ravel()[fi]
        if not np.isfinite(vec).all():
            raise RuntimeError(f"Non-finite values encountered in {nm}")
        mm[i] = vec
    mm.flush()
    names_path.write_text(json.dumps(list(H38_NAMES), indent=2))
    return np.load(target, mmap_mode="r"), list(H38_NAMES)


def calibrate_case_control_posterior(prob: np.ndarray, pi_true: float, r_train: float) -> np.ndarray:
    """Exact King & Zeng (2001) prior-odds Bayes calibration from subsampled training prevalence."""
    if not (0.0 < pi_true < 1.0) or not (0.0 < r_train < 1.0):
        raise ValueError(f"pi_true ({pi_true}) and r_train ({r_train}) must lie strictly in (0, 1)")
    tau = (pi_true / (1.0 - pi_true)) / (r_train / (1.0 - r_train))
    p = np.clip(np.asarray(prob, dtype=np.float32), 0.0, 1.0 - 1e-6)
    num = tau * p
    return (num / ((1.0 - p) + num)).astype(np.float32)


def _kernel_grid_5x5() -> np.ndarray:
    rad = int(math.ceil(RADIUS_PX)) - 1  # 2 for R=3.0 (k(3.0) == 0)
    kgrid = np.zeros((2 * rad + 1, 2 * rad + 1), dtype=np.float32)
    for dy, dx, w in _OFFS:
        kgrid[dy + rad, dx + rad] = float(w)
    return kgrid


def submodular_skeleton_dots(
    score: np.ndarray,
    valid: np.ndarray,
    known: np.ndarray,
    n_dots: int,
    *,
    pi_true: float,
    r_train: float,
    pool_kfrac: float = DEFAULT_POOL_KFRAC,
    min_dist_floor: float = DEFAULT_MIN_DIST_FLOOR_PX,
) -> np.ndarray:
    """Exact lazy-greedy maximization of 300 m triangular-kernel expected ``TP_w`` on ``R_1 | R_2``.

    Parameters
    ----------
    score:
        2-D predicted fault probability array ``(H, W)`` from ``HGB.predict_proba``.
    valid:
        Boolean evaluation domain mask (``dom_c`` in holdout, ``footprint`` in full build).
    known:
        Boolean visible-catalogue mask to exclude pixel-exact before placement.
    n_dots:
        Exact target number of binary dots ``M`` to emit (matched to ``S0`` in factorial cells).
    pi_true, r_train:
        Observed visible-catalogue prevalence on the training domain and sampled positive rate in ``y_train``
        (parameter-free case-control Bayes calibration).
    """
    val = np.asarray(valid, dtype=bool)
    kn = np.asarray(known, dtype=bool)
    sc = np.asarray(score, dtype=np.float32)
    if sc.shape != val.shape or kn.shape != val.shape or sc.ndim != 2:
        raise ValueError("score, valid, and known must be aligned 2-D arrays")
    target = int(n_dots)
    out = np.zeros(val.shape, dtype=bool)
    if target <= 0 or not val.any():
        return out

    eligible = val & (~kn) & np.isfinite(sc) & (sc > 0.0)
    if not eligible.any():
        return out

    # Multi-scale curvilinear ridge skeleton R_1 | R_2 on the continuous surface.
    r1 = ridge_nms(sc, val, sigma=1.0)
    r2 = ridge_nms(sc, val, sigma=2.0)
    skel = (r1 | r2) & eligible

    k_pool = max(target, int(round(float(pool_kfrac) * int(val.sum()))))
    skel_idx = np.flatnonzero(skel.ravel())
    sc_flat = sc.ravel()
    if skel_idx.size > k_pool:
        part = np.argpartition(-sc_flat[skel_idx], k_pool - 1)[:k_pool]
        pool_idx = skel_idx[part]
    else:
        pool_idx = skel_idx

    # Calibrated posterior skeleton mass w(g).
    pi_cal = calibrate_case_control_posterior(sc, pi_true=pi_true, r_train=r_train)
    w_grid = np.zeros(val.shape, dtype=np.float32)
    w_grid.ravel()[pool_idx] = pi_cal.ravel()[pool_idx]

    H, W = val.shape
    pad = max(2, int(math.ceil(max(min_dist_floor, RADIUS_PX))))
    Wp = W + 2 * pad
    Hp = H + 2 * pad

    w_pad = np.zeros((Hp, Wp), dtype=np.float32)
    w_pad[pad : pad + H, pad : pad + W] = w_grid

    # Fast exact initial gains on the unoccluded skeleton via 5x5 float64 correlation (+1e-12 strict UB).
    k5 = _kernel_grid_5x5().astype(np.float64)
    init_gain_grid = correlate(w_grid.astype(np.float64), k5, mode="constant", cval=0.0) + 1e-12

    # Low-overhead C-array buffers for Minoux (1978) lazy-greedy updates.
    w_buf = array("f", w_pad.ravel().tolist())
    c_buf = array("f", [0.0]) * (Hp * Wp)
    sup_buf = bytearray(Hp * Wp)
    del w_pad

    kern_offs: list[tuple[int, float]] = [(dy * Wp + dx, float(kw)) for dy, dx, kw in _OFFS]
    r_sup = int(math.ceil(float(min_dist_floor)))
    sup_offs: list[int] = [
        dy * Wp + dx
        for dy in range(-r_sup, r_sup + 1)
        for dx in range(-r_sup, r_sup + 1)
        if float(min_dist_floor) > 0.0 and math.hypot(dy, dx) < float(min_dist_floor)
    ]
    if not sup_offs:
        sup_offs = [0]

    def _run_stage(cand_flat: np.ndarray, remaining: int, gain_grid: np.ndarray, stage_w_buf: array) -> list[int]:
        if remaining <= 0 or cand_flat.size == 0:
            return []
        cr, cc = np.divmod(cand_flat, W)
        p_idx = ((cr + pad) * Wp + (cc + pad)).tolist()
        g0 = gain_grid.ravel()[cand_flat].tolist()
        s0 = sc_flat[cand_flat].tolist()
        fl = cand_flat.tolist()
        heap: list[tuple[float, float, int, int]] = [
            (-float(g), -float(sv), int(fi_i), int(pi_i))
            for g, sv, fi_i, pi_i in zip(g0, s0, fl, p_idx)
            if not sup_buf[pi_i]
        ]
        heapq.heapify(heap)
        picked: list[int] = []
        while heap and len(picked) < remaining:
            neg_ub, neg_sv, fi_i, p = heapq.heappop(heap)
            if sup_buf[p]:
                continue
            # Recompute exact current marginal gain against coverage state c_buf.
            cur = 0.0
            for off, kw in kern_offs:
                wi = stage_w_buf[p + off]
                if wi > 0.0:
                    rem = kw - c_buf[p + off]
                    if rem > 0.0:
                        cur += wi * rem
            cand_key = (-cur, neg_sv, fi_i)
            if not heap or cand_key <= heap[0][:3]:
                picked.append(fi_i)
                for off, kw in kern_offs:
                    idx2 = p + off
                    if kw > c_buf[idx2]:
                        c_buf[idx2] = kw
                for soff in sup_offs:
                    sup_buf[p + soff] = 1
            else:
                heapq.heappush(heap, (-cur, neg_sv, fi_i, p))
        return picked

    chosen = _run_stage(pool_idx, target, init_gain_grid, w_buf)

    # Fallback only if pool exhausted before target (e.g., tiny synthetic grids): extend to remaining skeleton/eligible.
    if len(chosen) < target:
        extra_mask = eligible.copy()
        extra_mask.ravel()[pool_idx] = False
        extra_idx = np.flatnonzero(extra_mask.ravel())
        if extra_idx.size:
            w_extra = np.where(eligible, pi_cal, 0.0).astype(np.float32)
            w_pad2 = np.zeros((Hp, Wp), dtype=np.float32)
            w_pad2[pad : pad + H, pad : pad + W] = w_extra
            w_buf2 = array("f", w_pad2.ravel().tolist())
            gain2 = correlate(w_extra, k5, mode="constant", cval=0.0)
            # Prioritize remaining skeleton pixels before off-skeleton eligible pixels.
            skel_rem = np.flatnonzero((skel & extra_mask).ravel())
            if skel_rem.size:
                chosen.extend(_run_stage(skel_rem, target - len(chosen), gain2, w_buf2))
            if len(chosen) < target:
                chosen.extend(_run_stage(extra_idx, target - len(chosen), gain2, w_buf2))

    if chosen:
        out.ravel()[np.asarray(chosen, dtype=np.int64)] = True
    return out
