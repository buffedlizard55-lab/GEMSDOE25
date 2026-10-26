"""H74-1 (RMPS-BFP) static geophysical/geomechanical sidecar & H74-BW 25-km block-withheld selector.

Pre-registered in ``knowledge/35_preregistered_h74_rmps_bw_2026-10-26.md`` (committed at ``af10a19``
before feature computation or model fitting).

Design invariants:
* ``compute_h74_rmps_grids`` and ``load_h74_rmps_sidecar`` are strictly static and label-free:
  ``labels.tif``, ``existing_faults.tif``, ``gdr_qfaults_traces.csv``, and ``dist_known_fault_px``
  are never opened or referenced.
* All four ``H74_RMPS_NAMES`` columns are finite ``float32`` in ``[0, 1]`` across all ``5,167,373``
  footprint pixels.
* ``draw_block25km`` returns a standard :class:`gems25.holdout.Draw` so shared ``Holdout.score``,
  ``dti_binary``, ``feature_canary``, and ``pooled_summary`` run unchanged without a private fork.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import (
    binary_dilation,
    binary_erosion,
    gaussian_filter,
    gaussian_laplace,
)

from .features import load_base, nearest_fill, ridge_strength
from .holdout import COLLAR_PX, Draw, Holdout

H74_RMPS_NAMES = [
    "H74_remanent_skew_crest",
    "H74_biharmonic_plate_hinge",
    "H74_simpson_pore_crit",
    "H74_laplace_harmonic_defect",
]

CELL_M = 100.0
PAD_PX = 256
BLOCK_PX_DEFAULT = 250  # 25 km at 100 m pixel spacing


def pct_scale_eroded(arr: np.ndarray, foot: np.ndarray, erode_px: int = 4) -> np.ndarray:
    """Clip and linearly scale finite values to [0, 1] via [1, 99] percentiles on eroded interior."""
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
    scaled = np.clip((vals - float(lo)) / float(hi - lo), 0.0, 1.0)
    return np.where(foot_b & np.isfinite(vals), scaled, 0.0).astype(np.float32)


def harmonic_vertical_derivative_fft(
    field: np.ndarray,
    cell_m: float = CELL_M,
    pad: int = PAD_PX,
) -> np.ndarray:
    """Exact downward harmonic vertical derivative F^{-1}{+2*pi*|k|*F_hat(k)} in units [field]/m.

    For a harmonic potential field satisfying Laplace's equation above z=0, upward continuation
    multiplies each 2-D Fourier mode k (cycles/m) by exp(-2*pi*|k|*dz), so the downward vertical
    derivative at z=0 is +2*pi*|k|*F_hat(k). ``pad=0`` gives the exact periodic operator.
    """
    a = np.asarray(field, dtype=np.float64)
    if a.ndim != 2 or not np.isfinite(a).all():
        raise ValueError("harmonic_vertical_derivative_fft requires a finite 2-D array")
    if cell_m <= 0 or pad < 0:
        raise ValueError("cell_m must be > 0 and pad must be >= 0")
    p = np.pad(a, pad, mode="reflect") if pad else a
    h, w = p.shape
    spec = np.fft.rfft2(p)
    fy = np.fft.fftfreq(h, d=cell_m)[:, None]
    fx = np.fft.rfftfreq(w, d=cell_m)[None, :]
    k = np.sqrt(fx * fx + fy * fy)
    v_down = np.fft.irfft2(spec * (2.0 * np.pi * k), s=(h, w))
    cropped = v_down[pad : pad + a.shape[0], pad : pad + a.shape[1]] if pad else v_down
    return cropped.astype(np.float32)


def biharmonic_magnitude(field: np.ndarray, sigma_px: float) -> np.ndarray:
    """Scale-normalized 4th-order biharmonic magnitude |sigma^4 * nabla^2(nabla^2 G_sigma * field)|."""
    if sigma_px <= 0:
        raise ValueError("sigma_px must be positive")
    f = np.asarray(field, dtype=np.float64)
    # Split total smoothing variance sigma^2 across two cascaded Laplacian-of-Gaussians
    # (sigma_step = sigma / sqrt(2)) so total Gaussian smoothing has std = sigma_px.
    s_step = float(sigma_px) / np.sqrt(2.0)
    lap1 = gaussian_laplace(f, sigma=s_step, truncate=6.0)
    biharm = gaussian_laplace(lap1, sigma=s_step, truncate=6.0) * (float(sigma_px) ** 4)
    return np.abs(biharm).astype(np.float32)


def compute_h74_rmps_grids(base: dict[str, np.ndarray], footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Compute the 4 frozen static H74-1 (RMPS-BFP) grids (knowledge/35 §3)."""
    foot = np.asarray(footprint, dtype=bool)
    if not foot.any():
        raise ValueError("footprint must contain at least one valid pixel")

    # 1. H74_remanent_skew_crest: TMI vs RTP phase-skewness contrast weighted by 3-D Analytic Signal
    tmi = nearest_fill(np.asarray(base["tmi"], dtype=np.float32))
    rtp = nearest_fill(np.asarray(base["rtp"], dtype=np.float32))
    tvg = nearest_fill(np.asarray(base["tmi_vg"], dtype=np.float32))

    tmi_s = gaussian_filter(tmi, 1.5)
    rtp_s = gaussian_filter(rtp, 1.5)
    tmi_gy, tmi_gx = np.gradient(tmi_s)
    rtp_gy, rtp_gx = np.gradient(rtp_s)
    g_tmi = 10.0 * np.hypot(tmi_gx, tmi_gy)  # nT/km
    g_rtp = 10.0 * np.hypot(rtp_gx, rtp_gy)  # nT/km
    tvg_km = 1000.0 * gaussian_filter(tvg, 1.0)  # nT/km
    as_tmi = np.hypot(g_tmi, tvg_km)

    gt_n = pct_scale_eroded(g_tmi, foot)
    gr_n = pct_scale_eroded(g_rtp, foot)
    at_n = pct_scale_eroded(np.log1p(as_tmi), foot)
    s_rem = (np.abs(gt_n - gr_n) / (gt_n + gr_n + 0.05)) * at_n
    remanent_skew_crest = pct_scale_eroded(ridge_strength(s_rem.astype(np.float32), 1.5), foot)
    del rtp, rtp_s, tmi_s, tmi_gy, tmi_gx, rtp_gy, rtp_gx, g_tmi, g_rtp, tvg_km, as_tmi, gt_n, gr_n, at_n, s_rem

    # 2. H74_biharmonic_plate_hinge: multi-scale biharmonic broken-plate flexure x isostatic gravity slope
    h_base = nearest_fill(np.asarray(base["depth_to_base_surf"], dtype=np.float32))
    w_base = np.log1p(np.maximum(h_base, 0.0))
    b2 = pct_scale_eroded(biharmonic_magnitude(w_base, 2.0), foot)
    b4 = pct_scale_eroded(biharmonic_magnitude(w_base, 4.0), foot)
    b24 = np.sqrt(b2 * b4)

    g_iso = nearest_fill(np.asarray(base["iso_grav_anom"], dtype=np.float32))
    ggy, ggx = np.gradient(gaussian_filter(g_iso, 2.0))
    g_iso_grad = pct_scale_eroded(np.hypot(ggx, ggy), foot)
    biharmonic_plate_hinge = pct_scale_eroded(
        ridge_strength(np.sqrt(b24 * g_iso_grad).astype(np.float32), 1.5),
        foot,
    )
    del h_base, w_base, b2, b4, b24, ggy, ggx, g_iso_grad

    # 3. H74_simpson_pore_crit: continuum strain-rate extension regime x high-pass MT conductance x microseismicity
    dil = nearest_fill(np.asarray(base["geod_dilaterate"], dtype=np.float32))
    shr = np.maximum(nearest_fill(np.asarray(base["geod_shearrate"], dtype=np.float32)), 0.0)
    e1 = 0.5 * dil + shr
    e2 = 0.5 * dil - shr
    t_ext = 0.5 + 0.5 * np.clip((e1 + e2) / (np.abs(e1) + np.abs(e2) + 1e-3), -1.0, 1.0)

    cond = np.log1p(np.maximum(nearest_fill(np.asarray(base["cond_surf"], dtype=np.float32)), 0.0))
    c_hp = pct_scale_eroded(np.maximum(cond - gaussian_filter(cond, 15.0), 0.0), foot)

    ieq = np.log1p(np.maximum(nearest_fill(np.asarray(base["ieq_n100a15"], dtype=np.float32)), 0.0))
    q_hp = pct_scale_eroded(np.maximum(ieq - gaussian_filter(ieq, 25.0), 0.0), foot)

    simpson_pore_crit = pct_scale_eroded(
        (t_ext * np.sqrt(c_hp * (0.25 + 0.75 * q_hp))).astype(np.float32),
        foot,
    )
    del dil, shr, e1, e2, t_ext, cond, c_hp, ieq, q_hp

    # 4. H74_laplace_harmonic_defect: sign-invariant spectral vs measured vertical-derivative defect
    tmi_1 = gaussian_filter(tmi, 1.0)
    v_fft_tmi = harmonic_vertical_derivative_fft(tmi_1, cell_m=CELL_M, pad=PAD_PX)
    tvg_1 = gaussian_filter(tvg, 1.0)
    d_m = pct_scale_eroded(np.abs(np.abs(tvg_1) - np.abs(v_fft_tmi)), foot)

    g_iso_1 = gaussian_filter(g_iso, 1.0)
    v_fft_grav_km = 1000.0 * harmonic_vertical_derivative_fft(g_iso_1, cell_m=CELL_M, pad=PAD_PX)
    gvg_1 = gaussian_filter(nearest_fill(np.asarray(base["iso_grav_anom_vg"], dtype=np.float32)), 1.0)
    d_g = pct_scale_eroded(np.abs(np.abs(gvg_1) - np.abs(v_fft_grav_km)), foot)

    laplace_harmonic_defect = pct_scale_eroded(
        ridge_strength(np.sqrt(d_m * d_g).astype(np.float32), 1.5),
        foot,
    )
    del tmi, tvg, g_iso, tmi_1, v_fft_tmi, tvg_1, d_m, g_iso_1, v_fft_grav_km, gvg_1, d_g

    out = {
        "H74_remanent_skew_crest": remanent_skew_crest,
        "H74_biharmonic_plate_hinge": biharmonic_plate_hinge,
        "H74_simpson_pore_crit": simpson_pore_crit,
        "H74_laplace_harmonic_defect": laplace_harmonic_defect,
    }
    for k, v in out.items():
        clean = np.where(foot, np.clip(np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0), 0.0, 1.0), 0.0)
        out[k] = clean.astype(np.float32)
    return out


def load_h74_rmps_sidecar(work: Path, fi: np.ndarray) -> np.ndarray:
    """Build or load cached ``(4, n_footprint)`` float32 memmap for ``H74_RMPS_NAMES``."""
    work = Path(work)
    out_path = work / "h74_rmps.npy"
    meta_path = work / "h74_rmps.names.json"
    fi_arr = np.asarray(fi)
    if out_path.exists() and meta_path.exists():
        names = json.loads(meta_path.read_text())
        if names == H74_RMPS_NAMES:
            mm = np.load(out_path, mmap_mode="r")
            if mm.shape == (len(H74_RMPS_NAMES), fi_arr.size):
                return mm

    foot = np.load(work / "bands" / "_footprint.npy")
    base = load_base(work / "bands")
    grids = compute_h74_rmps_grids(base, foot)
    mm = np.lib.format.open_memmap(
        out_path,
        mode="w+",
        dtype=np.float32,
        shape=(len(H74_RMPS_NAMES), fi_arr.size),
    )
    for j, name in enumerate(H74_RMPS_NAMES):
        vec = grids[name].ravel()[fi_arr]
        if not np.isfinite(vec).all() or (vec < 0.0).any() or (vec > 1.0).any():
            raise ValueError(f"H74 sidecar column {name} failed [0, 1] finite check")
        mm[j] = vec
    mm.flush()
    meta_path.write_text(json.dumps(H74_RMPS_NAMES) + "\n")
    return np.load(out_path, mmap_mode="r")


def _pick_block_components(
    rng: np.random.Generator,
    comp: np.ndarray,
    region_pos_mask: np.ndarray,
    allowed_comp_ids: set[int],
    target_px: float,
    block_px: int,
) -> np.ndarray:
    """Sample whole 8-connected components by drawing contiguous ``block_px x block_px`` tiles."""
    if target_px <= 0 or not allowed_comp_ids:
        return np.empty(0, dtype=np.int64)
    ys, xs = np.nonzero(region_pos_mask)
    if ys.size == 0:
        return np.empty(0, dtype=np.int64)
    tile_keys = np.unique((ys // block_px) * 100_000 + (xs // block_px))
    perm_tiles = rng.permutation(tile_keys)

    # Pre-index which allowed components touch each tile so selection is O(n_pos)
    c_vals = comp[ys, xs]
    t_vals = (ys // block_px) * 100_000 + (xs // block_px)
    order = np.argsort(t_vals, kind="mergesort")
    t_sorted = t_vals[order]
    c_sorted = c_vals[order]
    uniq_t, starts, counts = np.unique(t_sorted, return_index=True, return_counts=True)
    tile_to_comps: dict[int, np.ndarray] = {}
    allowed_arr = np.fromiter(sorted(allowed_comp_ids), dtype=comp.dtype)
    for tk, st, cnt in zip(uniq_t.tolist(), starts.tolist(), counts.tolist()):
        cs = np.unique(c_sorted[st : st + cnt])
        cs = cs[cs > 0]
        cs = cs[np.isin(cs, allowed_arr)]
        if cs.size:
            tile_to_comps[tk] = cs

    # Measure component pixel counts inside region_pos_mask so >= hide_frac is achieved in-region
    max_id = int(comp.max())
    in_region_counts = np.bincount(c_vals, minlength=max_id + 1)

    chosen: set[int] = set()
    acc_px = 0
    for tk in perm_tiles.tolist():
        cs = tile_to_comps.get(tk)
        if cs is None:
            continue
        for cid in cs.tolist():
            if cid not in chosen:
                chosen.add(cid)
                acc_px += int(in_region_counts[cid])
        if acc_px >= target_px:
            break
    return np.fromiter(sorted(chosen), dtype=np.int64)


def draw_block25km(
    holdout: Holdout,
    fold: int,
    seed: int,
    block_px: int = BLOCK_PX_DEFAULT,
) -> Draw:
    """25-km spatial-block component-withheld realisation (H74-BW, knowledge/35 §4).

    Withholds whole 8-connected components intersecting deterministically sampled ``block_px x block_px``
    tiles in both test quadrant ``fold`` and training region ``~collar``, enforcing a 15-px training
    buffer around both ``q`` and ``hidden_full`` so zero label or ``d_vis`` stub leaks across a block.
    """
    if block_px <= 0:
        raise ValueError("block_px must be positive")
    rng = np.random.default_rng(1_000_000 + int(seed) * 17 + int(fold))
    q = holdout.quad == fold
    quad_collar = holdout.collar(fold)
    ids = np.arange(1, holdout.n_comp + 1)

    in_test = set(np.unique(holdout.comp[q & holdout.labels]).tolist()) - {0}
    target_test = holdout.hide_frac * float((holdout.labels & q).sum())
    hid_test = _pick_block_components(
        rng,
        holdout.comp,
        q & holdout.labels,
        in_test,
        target_test,
        block_px,
    )
    hidden_full = np.isin(holdout.comp, hid_test)

    # Guard training region against any component that crosses from test quadrant across quad_collar
    hidden_test_collar = (
        binary_dilation(hidden_full, structure=np.ones((3, 3), dtype=bool), iterations=COLLAR_PX)
        & holdout.footprint
    )
    effective_collar = quad_collar | hidden_test_collar

    touch_eff_collar = set(np.unique(holdout.comp[effective_collar & holdout.labels]).tolist()) - {0}
    train_allowed = set(ids.tolist()) - touch_eff_collar - set(hid_test.tolist())
    train_pos_pool = (~effective_collar) & holdout.labels
    target_train = holdout.hide_frac * float(
        sum(int(holdout.comp_size[cid]) for cid in train_allowed)
    )
    hid_train = _pick_block_components(
        rng,
        holdout.comp,
        train_pos_pool,
        train_allowed,
        target_train,
        block_px,
    )
    hidden_train_full = np.isin(holdout.comp, hid_train)
    visible = holdout.labels & ~hidden_full & ~hidden_train_full

    rows = np.flatnonzero(q.any(axis=1))
    cols = np.flatnonzero(q.any(axis=0))
    bbox = (slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1))
    return Draw(
        fold=fold,
        seed=seed,
        quadrant=q,
        collar=effective_collar,
        hidden_test=hidden_full & q,
        hidden_train=hidden_train_full & ~effective_collar,
        visible=visible,
        train_region=holdout.footprint & ~effective_collar,
        bbox=bbox,
    )
