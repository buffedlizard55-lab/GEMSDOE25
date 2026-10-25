"""H38 greedy-emission unit tests (knowledge/25): formula checks before any holdout fit."""
import numpy as np

from gems25.greedy import (
    _KVALS,
    _OFFS,
    expected_fp,
    greedy_dots,
    greedy_dots_bruteforce,
    line_max_mean,
    plug_in_density,
)
from gems25.metric import kernel


def test_kernel_offsets_sorted_descending_and_complete():
    ks = [k for _, _, k in _OFFS]
    assert ks == sorted(ks, reverse=True)
    assert np.allclose(_KVALS, ks)
    # every offset with positive kernel value is present exactly once
    expect = {(dy, dx) for dy in range(-3, 4) for dx in range(-3, 4) if kernel(np.hypot(dy, dx)) > 0}
    assert {(dy, dx) for dy, dx, _ in _OFFS} == expect
    assert len(_OFFS) == len(expect)


def test_plug_in_density_sums_and_excludes_known():
    rng = np.random.default_rng(0)
    score = rng.random((20, 20))
    dom = np.ones((20, 20), bool)
    known = np.zeros((20, 20), bool)
    known[5, 5] = True
    phat = plug_in_density(score, dom, known, 10.0)
    assert phat[5, 5] == 0.0
    assert abs(phat.sum() - 10.0) < 0.5  # clipping at 1 can only shave a little here
    assert (phat >= 0).all() and (phat <= 1).all()


def test_expected_fp_matches_monte_carlo():
    rng = np.random.default_rng(1)
    phat = np.clip(rng.random((15, 15)) * 0.4, 0, 1)
    cand = np.array([7 * 15 + 7, 3 * 15 + 10, 12 * 15 + 4])
    exact = expected_fp(phat, cand)
    # Monte Carlo: draw Bernoulli truth fields, FP = 1 - max_g k(d) over drawn truths
    n_mc = 40_000
    acc = np.zeros(cand.size)
    nbrs = []
    for c in cand:
        y, x = divmod(int(c), 15)
        idx = [(y + dy, x + dx, k) for dy, dx, k in _OFFS if 0 <= y + dy < 15 and 0 <= x + dx < 15]
        nbrs.append(idx)
    for _ in range(200):  # 200 blocks x 200 draws
        draws = rng.random((200, 15, 15)) < phat[None, :, :]
        for ci, idx in enumerate(nbrs):
            mx = np.zeros(200)
            for yy, xx, k in idx:
                mx = np.maximum(mx, np.where(draws[:, yy, xx], k, 0.0))
            acc[ci] += (1.0 - mx).sum()
    mc = acc / (200 * 200)
    assert n_mc == 200 * 200
    assert np.allclose(exact, mc, atol=0.01), (exact, mc)


def test_expected_fp_edge_cases():
    phat = np.zeros((11, 11))
    assert np.allclose(expected_fp(phat, np.array([60])), 1.0)  # no truth anywhere -> FP 1
    phat[5, 5] = 1.0
    assert np.allclose(expected_fp(phat, np.array([60])), 0.0)  # dot on certain truth -> FP 0


def test_lazy_greedy_equals_bruteforce():
    for seed in range(6):
        rng = np.random.default_rng(seed)
        H, W = 26, 24
        # ridge-like score: a couple of blurred lines + noise
        score = rng.random((H, W)) * 0.05
        score[5:20, 8] += 0.9
        score[10, 4:22] += 0.7
        dom = np.ones((H, W), bool)
        known = np.zeros((H, W), bool)
        known[3, 3] = True
        cand = score > np.percentile(score, 70)
        a, da = greedy_dots(score, cand, dom, known, n_hat=25.0)
        b, db = greedy_dots_bruteforce(score, cand, dom, known, n_hat=25.0)
        assert (a == b).all(), seed
        assert da["n_selected"] == db["n_selected"]
        assert np.isclose(da["plugin_tp"], db["plugin_tp"], atol=1e-9)
        assert not (a & known).any()
        assert (a <= cand).all()


def test_greedy_concentrates_on_the_line_and_stops():
    H, W = 30, 30
    score = np.full((H, W), 0.001)
    score[5:25, 15] = 1.0
    dom = np.ones((H, W), bool)
    known = np.zeros((H, W), bool)
    cand = score > 0.01
    # near-certain plug-in density (phat ~0.96/line px): buying every line pixel is
    # correct, because a dot on near-certain truth costs ~0 FP.
    sel, diag = greedy_dots(score, cand, dom, known, n_hat=20.0)
    ys, xs = np.nonzero(sel)
    assert diag["n_selected"] >= 3
    assert (xs == 15).all()  # every bought dot sits on the high-density line
    assert diag["plugin_dti"] > 0.3
    # uncertain density (phat ~0.1/line px): FP is real, so kernel-geometry
    # spacing must emerge and the rule must stop before buying the whole pool.
    sel2, diag2 = greedy_dots(score, cand, dom, known, n_hat=2.0)
    ys2, xs2 = np.nonzero(sel2)
    assert (xs2 == 15).all()
    assert 2 <= diag2["n_selected"] < diag["n_selected"]
    assert np.all(np.diff(np.sort(ys2)) >= 2)


def test_greedy_empty_pool_and_cap():
    score = np.zeros((10, 10))
    score[5, 5] = 1.0
    dom = np.ones((10, 10), bool)
    known = np.zeros((10, 10), bool)
    sel, diag = greedy_dots(score, np.zeros((10, 10), bool), dom, known, n_hat=5.0)
    assert not sel.any() and diag["stop_reason"] == "empty_candidate_pool"
    cand = np.ones((10, 10), bool)
    sel, diag = greedy_dots(score, cand, dom, known, n_hat=5.0, max_dots=2)
    assert sel.sum() <= 2


def test_line_max_mean_finds_both_orientations():
    s = np.zeros((31, 31), np.float64)
    s[15, 5:26] = 1.0  # horizontal
    valid = np.ones_like(s, bool)
    f = line_max_mean(s, valid, length=15)
    assert f[15, 15] > 0.99
    assert f[15, 8] > 0.5
    assert f[5, 5] < 0.2
    s2 = np.zeros((31, 31))
    s2[5:26, 15] = 1.0  # vertical
    f2 = line_max_mean(s2, valid, length=15)
    assert f2[15, 15] > 0.99
    # faint-but-long beats bright-but-short at the centre pixel of each
    s3 = np.zeros((31, 31))
    s3[8, 3:28] = 0.4
    s3[22, 14:17] = 1.0
    f3 = line_max_mean(s3, valid, length=15)
    assert f3[8, 15] > f3[22, 15]
