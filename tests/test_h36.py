"""Unit and mathematical-equivalence tests for H36 (`src/gems25/h36.py`)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

from gems25.h36 import (
    H36_NAMES,
    TENT25,
    compute_alpha_sub,
    elkan_calibrate,
    load_h36_sidecar,
    poe_blend,
    rank_percentiles_1d,
    submod300_emit,
)
from gems25.paths import data_dir, work_dir
from gems25.thinning import ridge_nms, select_top_positive


def _bruteforce_submod(
    w_grid: np.ndarray,
    cand_mask: np.ndarray,
    budget: int,
    tau_min: float,
) -> np.ndarray:
    """Reference 1-by-1 naive submodular greedy solver on small grids for exact verification."""
    rs, cs = np.nonzero(cand_mask)
    h, w = w_grid.shape
    cov = np.zeros((h, w), dtype=np.float64)
    chosen = np.zeros((h, w), dtype=bool)
    used = np.zeros(rs.size, dtype=bool)
    for _ in range(budget):
        best_gain = -1.0
        best_i = -1
        for i in range(rs.size):
            if used[i]:
                continue
            r0, c0 = int(rs[i]), int(cs[i])
            g = 0.0
            for dr, dc, kv in TENT25:
                rr, cc = r0 + dr, c0 + dc
                if 0 <= rr < h and 0 <= cc < w and kv > cov[rr, cc]:
                    g += float(w_grid[rr, cc]) * (kv - cov[rr, cc])
            # Match IEEE-754 float32 cov / w_arr storage in submod300_emit within 1e-6 tie margin
            if g > best_gain + 1e-11:
                best_gain = g
                best_i = i
        if best_i < 0 or best_gain < tau_min:
            break
        used[best_i] = True
        r0, c0 = int(rs[best_i]), int(cs[best_i])
        chosen[r0, c0] = True
        for dr, dc, kv in TENT25:
            rr, cc = r0 + dr, c0 + dc
            if 0 <= rr < h and 0 <= cc < w and kv > cov[rr, cc]:
                cov[rr, cc] = float(np.float32(kv))
    return chosen


def test_tent25_kernel_matches_3px_support():
    assert len(TENT25) == 25
    center = [kv for dr, dc, kv in TENT25 if dr == 0 and dc == 0]
    assert center == [1.0]
    assert all(0.0 < kv <= 1.0 for _, _, kv in TENT25)


def test_elkan_and_poe_monotonicity_and_bounds():
    s = np.linspace(0.01, 0.99, 99, dtype=np.float32)
    cal = elkan_calibrate(s, pi_train=0.14, pi0=0.0024)
    assert cal.dtype == np.float32
    assert np.all((cal > 0.0) & (cal < 1.0))
    assert np.all(np.diff(cal) > 0.0)
    # Background p=0.10 must be strongly suppressed relative to p=0.90
    assert float(cal[9]) < 0.003
    assert float(cal[89] / cal[9]) > 50.0

    alpha = compute_alpha_sub(np.array([0.0, 5.0, 30.0], np.float32), np.array([0.0, 1.0, 1.0], np.float32))
    assert np.all((alpha >= 0.35) & (alpha <= 0.85))
    assert alpha[0] > alpha[1] > alpha[2]

    b = poe_blend(np.array([0.8, 0.8], np.float32), np.array([0.05, 0.6], np.float32), np.array([0.5, 0.5], np.float32))
    assert b[1] > 2.5 * b[0]
    assert np.allclose(rank_percentiles_1d(np.array([10.0, 20.0, 30.0])), [0.0, 0.5, 1.0])


def test_submod300_matches_bruteforce_sequential_greedy():
    rng = np.random.default_rng(123)
    shape = (44, 48)
    dom = np.ones(shape, dtype=bool)
    dom[:2, :] = False
    vis = np.zeros(shape, dtype=bool)
    vis[20, 10:30] = True
    score = rng.uniform(0.05, 0.95, size=shape).astype(np.float32)
    sub = rng.uniform(0.05, 0.90, size=shape).astype(np.float32)
    tip = np.zeros(shape, dtype=np.float32)
    tip[20, 30:34] = 0.25

    got = submod300_emit(
        score, sub, dom, vis, tip, pi_train=0.15,
        flank_px=2.0, tip_keep=0.06, cand_kfrac=0.15, max_dots=28, tau_min=1e-5,
    )

    # Reconstruct exact candidate set & weight grid for reference brute-force check
    d_vis = distance_transform_edt(~vis)
    shield = (d_vis <= 2.0) & (tip < 0.06)
    allow = dom & ~vis & ~shield
    w_grid = np.zeros(shape, dtype=np.float32)
    w_grid[allow] = elkan_calibrate(score[allow], pi_train=0.15)
    skel = ridge_nms(score, dom, 1.0) | ridge_nms(sub, dom, 1.2)
    k_cand = max(28, int(round(0.15 * int(dom.sum()))))
    cand_mask = select_top_positive(np.where(skel & allow, score, 0.0), dom, k_cand) & allow

    ref = _bruteforce_submod(w_grid, cand_mask, budget=28, tau_min=1e-5)
    assert int(got.sum()) == 28
    assert np.array_equal(got, ref)
    assert not (got & vis).any()
    assert not (got & shield).any()


def test_submod300_preserves_tip_zone_while_shielding_lateral_flanks():
    shape = (30, 30)
    dom = np.ones(shape, dtype=bool)
    vis = np.zeros(shape, dtype=bool)
    vis[15, 5:15] = True  # mapped trace ending at col 14
    score = np.full(shape, 0.01, dtype=np.float32)
    # Lateral flank ridge parallel at row 13 (2 px away, tip=0) -> must be shielded
    score[13, 6:14] = 0.95
    # Along-strike tip continuation at row 15, cols 15..16 (1-2 px from tip, tip=0.30) -> must be allowed
    score[15, 15:22] = 0.90
    tip = np.zeros(shape, dtype=np.float32)
    tip[14:17, 15:20] = 0.30

    em = submod300_emit(
        score, None, dom, vis, tip, pi_train=0.14,
        flank_px=2.0, tip_keep=0.06, cand_kfrac=0.20, max_dots=4, tau_min=1e-6,
    )
    assert not em[13, 6:14].any(), "non-tip lateral flank within 2 px must be shielded"
    assert em[15, 15:17].any(), "along-strike tip continuation within 2 px must be preserved"
    assert not (em & vis).any()


def test_real_h36_sidecar_if_bands_restored():
    w, d = work_dir(), data_dir()
    foot_path = w / "bands" / "_footprint.npy"
    if not foot_path.exists() or not (d / "external" / "geodawn_extensions_u8.tif").exists():
        pytest.skip("bands/external rasters not restored")
    foot = np.load(foot_path)
    arr = load_h36_sidecar(w, d / "external", foot)
    assert arr.shape == (len(H36_NAMES), int(foot.sum()))
    assert arr.dtype == np.float32
    for j in range(len(H36_NAMES)):
        col = np.asarray(arr[j])
        assert np.isfinite(col).all(), H36_NAMES[j]
        assert float(np.std(col)) > 0.0, H36_NAMES[j]
