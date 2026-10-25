"""H36: Unit-consistent subsurface potential-field local-wavenumber (SPI-GM-UP150),
hydrogeochemical geothermometer disequilibrium, and Bayes-calibrated 300 m tent
submodular allocation (`knowledge/21_preregistered_h36_spigm_submodular_2026-10-25.md`).

Design invariants:
* Never touches ``labels.tif`` or ``existing_faults.tif`` inside the static sidecar builder.
* Stores a footprint-vector float32 memmap ``(7, 5_167_373)`` (~145 MB on disk) so peak RAM stays well
  below the 3.8 GiB sandbox ceiling.
* ``submod300_emit`` implements exact 1-by-1 Minoux (1978) lazy-accelerated greedy maximization of the
  official 300 m (R = 3.0 px) radial triangular tent kernel on centered dual-regime fault skeletons,
  with fold-safe tip-preserved lateral-flank shielding (strictly from ``visible`` traces).
"""

from __future__ import annotations

import array
import csv
import heapq
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter

from .features import load_base, nearest_fill
from .thinning import ridge_nms, select_top_positive

H36_NAMES = [
    "H36_grav_spi_k",
    "H36_mag_spi_k",
    "H36_up150_persist",
    "H36_gm_strike_concord",
    "H36_transtension_iq",
    "H36_chem_diseq",
    "H36_burial_regime",
]

TARGET_FULL_DOTS = 37_654
FULL_FOOTPRINT_PX = 5_167_373
MASS_FRAC_DEFAULT = TARGET_FULL_DOTS / FULL_FOOTPRINT_PX  # 0.00728687478144117
PI0_DEFAULT = 0.0024
FLANK_PX_DEFAULT = 2.0
TIP_KEEP_DEFAULT = 0.06
CAND_KFRAC_DEFAULT = 0.035
TAU_MIN_DEFAULT = 1e-6


def tent_offsets_3px() -> list[tuple[int, int, float]]:
    """Exact nonzero (dr, dc, weight) entries of the official R=3.0 px triangular tent kernel."""
    offs: list[tuple[int, int, float]] = []
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            d = math.hypot(dr, dc)
            if d < 3.0:
                offs.append((dr, dc, float(1.0 - d / 3.0)))
    return offs


TENT25 = tent_offsets_3px()


def rank_percentiles_1d(v: np.ndarray) -> np.ndarray:
    """Exact rank-percentile in [0, 1] of a finite 1-D vector."""
    x = np.nan_to_num(np.asarray(v, dtype=np.float32), nan=0.0)
    n = x.size
    if n <= 1:
        return np.zeros(n, dtype=np.float32)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(n, dtype=np.float32)
    ranks[order] = np.linspace(0.0, 1.0, n, dtype=np.float32)
    return ranks


def compute_alpha_sub(det_elev_slope_vec: np.ndarray, l_valid_vec: np.ndarray) -> np.ndarray:
    """Regime-adaptive subsurface Product-of-Experts exponent alpha_sub in [0.35, 0.85]."""
    u_flat = 1.0 - rank_percentiles_1d(det_elev_slope_vec)
    v_void = (np.nan_to_num(l_valid_vec, nan=0.0) <= 0.0).astype(np.float32)
    return np.clip(0.35 + 0.35 * u_flat + 0.15 * v_void, 0.35, 0.85).astype(np.float32)


def poe_blend(p_multi: np.ndarray, p_sub: np.ndarray, alpha_sub: np.ndarray) -> np.ndarray:
    """Regime-gated Product-of-Experts geometric pooling s = p_M^(1-a) * p_S^a."""
    pm = np.clip(np.asarray(p_multi, dtype=np.float32), 1e-6, 1.0 - 1e-6)
    ps = np.clip(np.asarray(p_sub, dtype=np.float32), 1e-6, 1.0 - 1e-6)
    a = np.clip(np.asarray(alpha_sub, dtype=np.float32), 0.0, 1.0)
    return np.exp((1.0 - a) * np.log(pm) + a * np.log(ps)).astype(np.float32)


def elkan_calibrate(s: np.ndarray, pi_train: float, pi0: float = PI0_DEFAULT) -> np.ndarray:
    """Elkan (2001) Bayes prior-shift probability recalibration from subsampled training prevalence."""
    pt = float(np.clip(pi_train, 1e-4, 1.0 - 1e-4))
    p0 = float(np.clip(pi0, 1e-6, 1.0 - 1e-6))
    r = (p0 / (1.0 - p0)) / (pt / (1.0 - pt))
    sc = np.clip(np.asarray(s, dtype=np.float32), 1e-6, 1.0 - 1e-6)
    num = r * sc
    return (num / ((1.0 - sc) + num)).astype(np.float32)


def _chem_diseq_grid(csv_path: Path, shape: tuple[int, int]) -> np.ndarray:
    """Build 2.5 km smoothed hydrogeochemical geothermometer disequilibrium log1p(DeltaT)."""
    grid = np.zeros(shape, dtype=np.float32)
    if not csv_path.exists():
        return grid
    h, w = shape
    with csv_path.open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, TypeError, ValueError):
                continue
            if not (0 <= r < h and 0 <= c < w):
                continue
            t_chems: list[float] = []
            for key in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                raw = (row.get(key) or "").strip()
                if not raw:
                    continue
                try:
                    val = float(raw)
                    if math.isfinite(val) and -50.0 < val < 400.0:
                        t_chems.append(val)
                except ValueError:
                    continue
            if not t_chems:
                continue
            t_meas = 15.0
            raw_t = (row.get("temp_c") or "").strip()
            if raw_t:
                try:
                    vt = float(raw_t)
                    if math.isfinite(vt) and 0.0 <= vt < 350.0:
                        t_meas = max(vt, 15.0)
                except ValueError:
                    pass
            dt = float(np.clip(max(t_chems) - t_meas, 0.0, 250.0))
            if dt > grid[r, c]:
                grid[r, c] = dt
    smoothed = gaussian_filter(grid, sigma=25.0, mode="nearest", truncate=3.0).astype(np.float32)
    return np.log1p(np.maximum(smoothed, 0.0)).astype(np.float32)


def build_h36_sidecar(
    band_dir: Path,
    external_dir: Path,
    footprint: np.ndarray,
    out_path: Path,
) -> list[str]:
    """Compute all 7 static H36 columns and stream them into a (7, n_foot) float32 memmap."""
    band_dir = Path(band_dir)
    external_dir = Path(external_dir)
    foot = np.asarray(footprint, dtype=bool)
    fi = np.flatnonzero(foot.ravel())
    shape = foot.shape
    base = load_base(band_dir)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(len(H36_NAMES), fi.size))

    # 1. Unit-consistent Gravity SPI local wavenumber (mGal/km matched)
    g = gaussian_filter(nearest_fill(np.asarray(base["iso_grav_anom"], dtype=np.float32)), sigma=1.0, mode="nearest")
    gz = gaussian_filter(nearest_fill(np.asarray(base["iso_grav_anom_vg"], dtype=np.float32)), sigma=1.0, mode="nearest")
    gy, gx = np.gradient(g, 0.1)
    del g
    hg = np.hypot(gx, gy).astype(np.float32)
    theta_g = np.arctan2(gz, hg + 0.05).astype(np.float32)
    del gz, hg
    tgy, tgx = np.gradient(theta_g, 0.1)
    del theta_g
    kappa_g = np.log1p(np.hypot(tgx, tgy)).astype(np.float32)
    del tgx, tgy
    mm[0] = kappa_g.ravel()[fi]

    # 2. Unit-consistent Magnetic SPI local wavenumber (1000 * tmi_vg matched to ||grad(tmi)|| in nT/km)
    tmi = gaussian_filter(nearest_fill(np.asarray(base["tmi"], dtype=np.float32)), sigma=1.0, mode="nearest")
    tz = gaussian_filter(1000.0 * nearest_fill(np.asarray(base["tmi_vg"], dtype=np.float32)), sigma=1.0, mode="nearest")
    ty, tx = np.gradient(tmi, 0.1)
    del tmi
    ht = np.hypot(tx, ty).astype(np.float32)
    del tx, ty
    theta_m = np.arctan2(tz, ht + 2.0).astype(np.float32)
    del tz
    tmy, tmx = np.gradient(theta_m, 0.1)
    del theta_m
    kappa_m = np.log1p(np.hypot(tmx, tmy)).astype(np.float32)
    del tmx, tmy
    mm[1] = kappa_m.ravel()[fi]

    # 3. GeoDAWN TMI_up150 upward-continuation persistence ratio
    ext_tif = external_dir / "geodawn_extensions_u8.tif"
    with rasterio.open(ext_tif) as ds:
        q_up = ds.read(4)
    u_up = np.where(q_up > 0, (q_up.astype(np.float32) - 1.0) / 254.0, np.nan).astype(np.float32)
    del q_up
    u_up = gaussian_filter(nearest_fill(u_up), sigma=1.0, mode="nearest")
    uy, ux = np.gradient(u_up, 0.1)
    del u_up
    g_up = np.hypot(ux, uy).astype(np.float32)
    del ux, uy
    g_up_foot = g_up.ravel()[fi]
    p25, p75 = np.percentile(g_up_foot[::8], [25.0, 75.0])
    iqr_up = float(max(p75 - p25, 1e-6))
    med_ht = float(max(np.median(ht.ravel()[fi][::8]), 1e-6))
    persist = (np.log1p(g_up / iqr_up) - 0.5 * np.log1p(ht / med_ht)).astype(np.float32)
    del g_up, ht
    mm[2] = persist.ravel()[fi]
    del persist

    # 4. Vector strike-locked gravity-magnetic phase concordance
    rtp = gaussian_filter(nearest_fill(np.asarray(base["rtp"], dtype=np.float32)), sigma=1.5, mode="nearest")
    ry, rx = np.gradient(rtp, 0.1)
    del rtp
    dot = gx * rx + gy * ry
    cross = gx * ry - gy * rx
    denom = (gx * gx + gy * gy) * (rx * rx + ry * ry) + 1e-9
    del gx, gy, rx, ry
    cos2_dphi = np.maximum(0.0, (dot * dot - cross * cross) / denom).astype(np.float32)
    del dot, cross, denom
    gm_joint = np.sqrt(np.maximum(kappa_g * kappa_m, 0.0)).astype(np.float32)
    del kappa_g, kappa_m
    concord = (gm_joint * cos2_dphi).astype(np.float32)
    del cos2_dphi
    mm[3] = concord.ravel()[fi]
    del concord

    # 5. Andersonian transtensional strain x seismic intensity coupling
    dil = nearest_fill(np.asarray(base["geod_dilaterate"], dtype=np.float32))
    inv2 = nearest_fill(np.asarray(base["geod_2ndinv"], dtype=np.float32))
    ieq = np.maximum(nearest_fill(np.asarray(base["ieq_n100a15"], dtype=np.float32)), 0.0)
    deq = np.maximum(nearest_fill(np.asarray(base["deq_n100a15"], dtype=np.float32)), 0.0)
    transt = ((dil / (np.maximum(inv2, 0.0) + 1.0)) * np.log1p(ieq / (deq + 100.0))).astype(np.float32)
    del dil, inv2, ieq, deq
    mm[4] = transt.ravel()[fi]
    del transt

    # 6. GDR hydrogeochemical geothermometer disequilibrium
    chem = _chem_diseq_grid(external_dir / "gdr_wellspring_in_footprint.csv", shape)
    mm[5] = chem.ravel()[fi]
    del chem

    # 7. Sedimentary burial & 3DEP LiDAR-void subsurface exposure regime
    slope_foot = nearest_fill(np.asarray(base["det_elev_slope"], dtype=np.float32)).ravel()[fi]
    u_flat = 1.0 - rank_percentiles_1d(slope_foot)
    del slope_foot
    lidar_tif = external_dir / "lidar_scarp_features_u8.tif"
    with rasterio.open(lidar_tif) as ds:
        l_valid_foot = (ds.read(12).ravel()[fi] == 0).astype(np.float32)
    burial = ((0.65 * u_flat + 0.35 * l_valid_foot) * gm_joint.ravel()[fi]).astype(np.float32)
    del gm_joint, u_flat, l_valid_foot
    mm[6] = burial
    del burial

    for j, name in enumerate(H36_NAMES):
        if not np.isfinite(mm[j]).all():
            raise ValueError(f"H36 column {name} contains non-finite values inside footprint")
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H36_NAMES))
    return list(H36_NAMES)


def load_h36_sidecar(work: Path, external_dir: Path, footprint: np.ndarray) -> np.ndarray:
    """Load (or build once) the (7, n_foot) float32 H36 memmap sidecar."""
    work = Path(work)
    path = work / "h36_spigm_columns.npy"
    names_path = Path(str(path) + ".names.json")
    n_foot = int(np.asarray(footprint, dtype=bool).sum())
    if not path.exists() or not names_path.exists():
        build_h36_sidecar(work / "bands", external_dir, footprint, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(names_path.read_text())
    if names != H36_NAMES or arr.shape != (len(H36_NAMES), n_foot):
        raise ValueError(f"H36 sidecar mismatch: names={names} shape={arr.shape}")
    return arr


def submod300_emit(
    score_2d: np.ndarray,
    sub_2d: np.ndarray | None,
    domain: np.ndarray,
    visible: np.ndarray,
    tip_2d: np.ndarray | None,
    pi_train: float,
    *,
    pi0: float = PI0_DEFAULT,
    flank_px: float = FLANK_PX_DEFAULT,
    tip_keep: float = TIP_KEEP_DEFAULT,
    cand_kfrac: float = CAND_KFRAC_DEFAULT,
    mass_frac: float = MASS_FRAC_DEFAULT,
    max_dots: int | None = None,
    tau_min: float = TAU_MIN_DEFAULT,
) -> np.ndarray:
    """Exact Minoux (1978) lazy-accelerated greedy maximization of 300 m tent coverage.

    Selects binary dot centers from centered dual-regime skeletons outside non-tip visible
    lateral flanks (strictly derived from ``visible``, never hidden truth), maximizing
    F(X) = sum_{y} w(y) * max_{x in X} K_3.0(x, y) where w(y) is the Elkan-calibrated
    hidden-fault probability.
    """
    dom = np.asarray(domain, dtype=bool)
    vis = np.asarray(visible, dtype=bool)
    if score_2d.shape != dom.shape or vis.shape != dom.shape:
        raise ValueError("score_2d, domain, and visible must have identical 2-D shapes")

    n_dom = int(dom.sum())
    if n_dom == 0:
        return np.zeros(dom.shape, dtype=bool)

    budget = int(round(mass_frac * n_dom)) if max_dots is None else int(max_dots)
    if budget <= 0:
        return np.zeros(dom.shape, dtype=bool)

    # Fold-safe tip-preserved lateral-flank shield around VISIBLE traces only
    if vis.any() and flank_px > 0.0:
        d_vis = distance_transform_edt(~vis)
        if tip_2d is not None:
            shield = (d_vis <= flank_px) & (np.nan_to_num(tip_2d, nan=0.0) < tip_keep)
        else:
            shield = d_vis <= flank_px
    else:
        shield = np.zeros(dom.shape, dtype=bool)

    allow = dom & ~vis & ~shield
    if not allow.any():
        return np.zeros(dom.shape, dtype=bool)

    # Elkan prior-shift calibrated pixel weight grid w(y)
    s_clean = np.nan_to_num(np.asarray(score_2d, dtype=np.float32), nan=0.0)
    w_grid = np.zeros(dom.shape, dtype=np.float32)
    w_grid[allow] = elkan_calibrate(s_clean[allow], pi_train=pi_train, pi0=pi0)

    # Centered dual-regime skeleton candidates
    skel = ridge_nms(s_clean, dom, 1.0)
    if sub_2d is not None:
        sub_clean = np.nan_to_num(np.asarray(sub_2d, dtype=np.float32), nan=0.0)
        skel = skel | ridge_nms(sub_clean, dom, 1.2)
    cand_scores = np.where(skel & allow, s_clean, 0.0)
    k_cand = max(budget, int(round(cand_kfrac * n_dom)))
    cand_mask = select_top_positive(cand_scores, dom, k_cand) & allow
    rs, cs = np.nonzero(cand_mask)
    if rs.size == 0:
        return np.zeros(dom.shape, dtype=bool)

    h, w = dom.shape
    pad = 2
    hp, wp = h + 2 * pad, w + 2 * pad
    w_pad = np.zeros((hp, wp), dtype=np.float32)
    w_pad[pad : pad + h, pad : pad + w] = w_grid
    del w_grid

    rp = rs + pad
    cp = cs + pad
    g0 = np.zeros(rs.size, dtype=np.float64)
    for dr, dc, kv in TENT25:
        g0 += w_pad[rp + dr, cp + dc] * kv

    keep = g0 >= tau_min
    if not keep.any():
        return np.zeros(dom.shape, dtype=bool)
    rs, cs, rp, cp, g0 = rs[keep], cs[keep], rp[keep], cp[keep], g0[keep]

    w_arr = array.array("f", w_pad.ravel().tobytes())
    del w_pad
    cov_arr = array.array("f", b"\x00\x00\x00\x00" * (hp * wp))
    base_idx = (rp * wp + cp).tolist()
    off_kv = [(dr * wp + dc, kv) for dr, dc, kv in TENT25]

    # Deterministic tie-break by candidate coordinate index i in tuple (-gain, i)
    heap: list[tuple[float, int]] = [(-float(g0[i]), i) for i in range(rs.size)]
    heapq.heapify(heap)

    emitted = np.zeros(dom.shape, dtype=bool)
    n_picked = 0
    while n_picked < budget and heap:
        neg_ub, i = heapq.heappop(heap)
        if -neg_ub < tau_min:
            break
        b = base_idx[i]
        gain = 0.0
        for d_idx, kv in off_kv:
            idx = b + d_idx
            c_cur = cov_arr[idx]
            if kv > c_cur:
                gain += w_arr[idx] * (kv - c_cur)
        if gain < tau_min:
            continue
        if not heap or (-gain, i) <= heap[0]:
            emitted[rs[i], cs[i]] = True
            n_picked += 1
            for d_idx, kv in off_kv:
                idx = b + d_idx
                if kv > cov_arr[idx]:
                    cov_arr[idx] = kv
        else:
            heapq.heappush(heap, (-gain, i))

    return emitted
