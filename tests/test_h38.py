"""Unit tests for H38-OSPC static physics columns and 300 m submodular skeleton allocation."""

from __future__ import annotations

import numpy as np
import pytest

from gems25.features import LIDAR_BANDS, LIDAR_QUANT
from gems25.h38 import (
    H38_NAMES,
    calibrate_case_control_posterior,
    compute_h38_ospc_grids,
    submodular_skeleton_dots,
)
from gems25.metric import _OFFS, dti_binary


def _quantize_u8(val: np.ndarray, name: str, valid_mask: np.ndarray) -> np.ndarray:
    xmax, how = LIDAR_QUANT[name]
    ratio = np.clip(val / xmax, 0.0, 1.0)
    t = np.sqrt(ratio) if how == "sqrt" else ratio
    q = np.clip(np.round(1.0 + 254.0 * t), 1, 255).astype(np.uint8)
    return np.where(valid_mask, q, np.uint8(0))


def test_monoclinal_polarity_rejects_symmetric_gully_and_aligns_spin2_strike():
    H, W = 64, 64
    foot = np.ones((H, W), dtype=bool)
    foot[:2, :] = False  # verify outside-footprint zeroing
    valid_lidar = np.ones((H, W), dtype=bool)
    valid_lidar[:, 50:] = False  # 3DEP coverage hole -> must not leak NaNs

    bidx = {n: i for i, n in enumerate(LIDAR_BANDS)}
    q = np.zeros((len(LIDAR_BANDS), H, W), dtype=np.uint8)
    for nm in LIDAR_BANDS:
        q[bidx[nm]] = _quantize_u8(np.zeros((H, W), dtype=np.float32), nm, valid_lidar)
    q[bidx["valid"]] = np.where(valid_lidar, np.uint8(255), np.uint8(0))

    # Row 20: E-W (strike = 0 deg) one-sided monoclinal fault scarp (downface >> upface)
    # Row 44: E-W symmetric V-shaped wash (downface == upface) -> polarity must vanish
    d_val = np.zeros((H, W), dtype=np.float32)
    u_val = np.zeros((H, W), dtype=np.float32)
    ex_val = np.zeros((H, W), dtype=np.float32)
    step_val = np.zeros((H, W), dtype=np.float32)
    coh_val = np.zeros((H, W), dtype=np.float32)
    strike_val = np.zeros((H, W), dtype=np.float32)

    d_val[19:22, 8:46] = 0.85
    u_val[19:22, 8:46] = 0.02
    ex_val[19:22, 8:46] = 0.22
    step_val[19:22, 8:46] = 0.75
    coh_val[19:22, 8:46] = 0.90
    strike_val[19:22, 8:46] = 0.0  # E-W line along column axis

    d_val[43:46, 8:46] = 0.60
    u_val[43:46, 8:46] = 0.60
    ex_val[43:46, 8:46] = 0.22
    step_val[43:46, 8:46] = 0.75
    coh_val[43:46, 8:46] = 0.90

    q[bidx["downface_max"]] = _quantize_u8(d_val, "downface_max", valid_lidar)
    q[bidx["upface_max"]] = _quantize_u8(u_val, "upface_max", valid_lidar)
    q[bidx["ex_mean"]] = _quantize_u8(ex_val, "ex_mean", valid_lidar)
    q[bidx["step_max"]] = _quantize_u8(step_val, "step_max", valid_lidar)
    q[bidx["coh100"]] = _quantize_u8(coh_val, "coh100", valid_lidar)
    q[bidx["strike"]] = _quantize_u8(strike_val, "strike", valid_lidar)

    rows = np.arange(H, dtype=np.float32)[:, None]
    cols = np.arange(W, dtype=np.float32)[None, :]
    # Parallel E-W subsurface gravity step at row 20 vs orthogonal N-S gravity step
    grav_parallel = np.tanh((rows - 20.0) / 2.0) * 15.0 + 0.0 * cols
    grav_orth = np.tanh((cols - 25.0) / 2.0) * 15.0 + 0.0 * rows
    rtp_flat = np.zeros((H, W), dtype=np.float32)
    cond = np.full((H, W), 2.0, dtype=np.float32)

    g_par = compute_h38_ospc_grids(rtp_flat, grav_parallel, cond, q, foot)
    g_ort = compute_h38_ospc_grids(rtp_flat, grav_orth, cond, q, foot)

    assert tuple(g_par.keys()) == H38_NAMES
    for nm, arr in g_par.items():
        assert arr.dtype == np.float32
        assert np.isfinite(arr).all(), f"NaN/Inf in {nm}"
        assert np.all(arr[~foot] == 0.0), f"Non-zero outside footprint in {nm}"

    # Monoclinal scarp at row 20 >> symmetric V-gully at row 44
    assert float(g_par["H38_monoclinal_polarity"][20, 25]) > 0.15
    assert float(g_par["H38_monoclinal_polarity"][44, 25]) == pytest.approx(0.0, abs=1e-6)

    # Parallel E-W subsurface gravity step gives strongly positive spin-2 alignment;
    # orthogonal N-S subsurface step flips spin-2 dot product negative.
    assert float(g_par["H38_subsurf_strike_align"][20, 25]) > 0.50
    assert float(g_ort["H38_subsurf_strike_align"][20, 25]) < -0.50


def test_magnetite_destruction_trough_detects_negative_rtp_with_conductivity():
    H, W = 64, 64
    foot = np.ones((H, W), dtype=bool)
    q = np.zeros((len(LIDAR_BANDS), H, W), dtype=np.uint8)
    rows = np.arange(H, dtype=np.float32)[:, None]
    cols = np.arange(W, dtype=np.float32)[None, :]
    # Negative shallow magnetic trough along row 20 vs positive dike crest along row 44
    rtp = -80.0 * np.exp(-0.5 * ((rows - 20.0) / 1.8) ** 2) + 80.0 * np.exp(-0.5 * ((rows - 44.0) / 1.8) ** 2) + 0.0 * cols
    grav = np.zeros((H, W), dtype=np.float32)
    cond = np.where(rows < 32, 3.0, 3.0).astype(np.float32) + 0.01 * cols  # non-degenerate span

    grids = compute_h38_ospc_grids(rtp, grav, cond, q, foot)
    trough = grids["H38_mag_destruction_trough"]
    assert float(trough[20, 32]) > 5.0 * max(float(trough[44, 32]), 1e-4)


def test_case_control_calibration_monotone_and_exact_at_identity():
    p = np.array([0.0, 0.05, 0.25, 0.50, 0.90], dtype=np.float32)
    same = calibrate_case_control_posterior(p, pi_true=0.10, r_train=0.10)
    assert np.allclose(same, p, atol=1e-6)

    cal = calibrate_case_control_posterior(p, pi_true=0.012, r_train=0.105)
    assert np.all(np.diff(cal) > 0.0)
    # Rare-event calibration steepens high-vs-low posterior contrast relative to raw p
    assert float(cal[3] / cal[1]) > float(p[3] / p[1]) * 1.4


def test_submodular_skeleton_matches_bruteforce_and_beats_packed_spacing_on_secondary_fault():
    H, W = 48, 48
    valid = np.ones((H, W), dtype=bool)
    known = np.zeros((H, W), dtype=bool)
    known[5, :] = True  # visible fault must never receive dots

    rows = np.arange(H, dtype=np.float32)[:, None]
    cols = np.arange(W, dtype=np.float32)[None, :]
    # Fault A (row 16): strong ridge (p ~ 0.55); Fault B (row 30): blind secondary fault ridge (p ~ 0.38)
    taper = (1.0 - 0.02 * np.abs(cols - 24.0) / 24.0).astype(np.float32)
    score = (
        0.55 * np.exp(-0.5 * ((rows - 16.0) / 1.0) ** 2) * taper
        + 0.38 * np.exp(-0.5 * ((rows - 30.0) / 1.8) ** 2) * taper
    ).astype(np.float32)

    m_dots = 11  # Rigid 2.4-px top-score greedy spends ALL 11 dots on Fault A alone!
    dots_sub = submodular_skeleton_dots(
        score, valid, known, n_dots=m_dots, pi_true=0.012, r_train=0.10, pool_kfrac=0.20, min_dist_floor=1.5
    )
    assert int(dots_sub.sum()) == m_dots
    assert not (dots_sub & known).any()

    # Check hard micro-collision guard d >= 1.5 px
    rr, cc = np.nonzero(dots_sub)
    for i in range(len(rr)):
        for j in range(i + 1, len(rr)):
            assert np.hypot(rr[i] - rr[j], cc[i] - cc[j]) >= 1.5 - 1e-6

    # Hidden truth consists of BOTH Fault A and Fault B: submodular must cover BOTH faults
    truth = np.zeros((H, W), dtype=bool)
    truth[16, 12:36] = True
    truth[30, 12:36] = True

    from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive

    r_s0 = ridge_nms(score, valid, sigma=1.0)
    cand_s0 = select_top_positive(score, r_s0 & (~known), int(round(0.20 * valid.sum())))
    dots_s0 = score_ordered_dots(score, cand_s0, min_dist=2.4, max_keep=m_dots)

    assert int(dots_sub[28:33, :].sum()) >= 3, "Submodular must allocate dots to blind secondary Fault B"
    assert dti_binary(dots_sub, truth, valid, known)["dti"] > dti_binary(dots_s0, truth, valid, known)["dti"] + 0.10


def test_lazy_greedy_matches_naive_stepwise_greedy_exactly():
    rng = np.random.default_rng(7)
    H, W = 40, 40
    valid = np.ones((H, W), dtype=bool)
    known = np.zeros((H, W), dtype=bool)
    # Smooth random multi-ridge field with full interior halo support for sigma=1.0 and sigma=2.0
    from scipy.ndimage import gaussian_filter

    raw = gaussian_filter(rng.random((H, W), dtype=np.float32), 1.4)
    score = np.clip(raw, 0.01, 0.95).astype(np.float32)
    n_dots = 8
    lazy = submodular_skeleton_dots(
        score, valid, known, n_dots=n_dots, pi_true=0.02, r_train=0.10, pool_kfrac=1.0, min_dist_floor=1.5
    )

    # Brute-force stepwise greedy on exact same skeleton pool
    from gems25.thinning import ridge_nms

    skel = (ridge_nms(score, valid, 1.0) | ridge_nms(score, valid, 2.0)) & valid & (~known)
    assert int(skel.sum()) >= 25
    w = np.where(skel, calibrate_case_control_posterior(score, 0.02, 0.10), 0.0).astype(np.float32)
    cands = [int(i) for i in np.flatnonzero(skel.ravel())]
    cov = np.zeros((H, W), dtype=np.float32)
    picked_naive: list[int] = []
    for _ in range(n_dots):
        best_key = None
        best_fi = -1
        for fi in cands:
            r, c = divmod(fi, W)
            if any(np.hypot(r - divmod(p, W)[0], c - divmod(p, W)[1]) < 1.5 for p in picked_naive):
                continue
            gain = 0.0
            for dy, dx, kw in _OFFS:
                rr, cc = r + dy, c + dx
                if 0 <= rr < H and 0 <= cc < W and w[rr, cc] > 0:
                    rem = float(kw) - float(np.float32(cov[rr, cc]))
                    if rem > 0.0:
                        gain += float(w[rr, cc]) * rem
            key = (gain, float(score[r, c]), -fi)
            if best_key is None or key > best_key:
                best_key = key
                best_fi = fi
        picked_naive.append(best_fi)
        br, bc = divmod(best_fi, W)
        for dy, dx, kw in _OFFS:
            rr, cc = br + dy, bc + dx
            if 0 <= rr < H and 0 <= cc < W:
                cov[rr, cc] = np.float32(max(float(cov[rr, cc]), float(kw)))

    naive = np.zeros((H, W), dtype=bool)
    naive.ravel()[picked_naive] = True
    assert np.array_equal(lazy, naive)
