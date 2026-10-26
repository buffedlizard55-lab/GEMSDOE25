"""Unit tests for the H73-PM propensity-matched sampler (synthetic data only)."""

import numpy as np
import pytest

from gems25.h73_pm import BIN_EDGES_PX, bin_ids, matched_quotas, propensity_matched_negatives


def test_bin_edges():
    d = np.array([0.0, 2.0, 2.1, 5.0, 9.0, 15.0, 25.0, 40.0, 80.0, 500.0])
    assert bin_ids(d).tolist() == [0, 0, 1, 1, 2, 3, 4, 5, 6, 7]
    assert len(BIN_EDGES_PX) - 1 == 8
    with pytest.raises(ValueError):
        bin_ids(np.array([np.nan]))
    with pytest.raises(ValueError):
        bin_ids(np.array([-1.0]))


def test_quotas_match_positive_shares_when_pool_is_deep():
    rng = np.random.default_rng(0)
    pos_bins = rng.choice(8, size=10_000, p=[0.4, 0.3, 0.1, 0.05, 0.05, 0.04, 0.03, 0.03])
    pool_bins = rng.integers(0, 8, size=2_000_000)
    q = matched_quotas(pos_bins, pool_bins, 100_000)
    assert q.sum() == 100_000
    share = q / q.sum()
    target = np.bincount(pos_bins, minlength=8) / pos_bins.size
    assert np.max(np.abs(share - target)) < 0.005


def test_quotas_respect_caps_and_redistribute():
    pos_bins = np.zeros(1000, dtype=int)  # all positives in bin 0
    pool_bins = np.concatenate([np.zeros(10, dtype=int), np.ones(5000, dtype=int)])
    q = matched_quotas(pos_bins, pool_bins, 1000)
    assert q[0] == 10  # capped at pool size
    assert q.sum() == 1000  # shortfall redistributed
    assert q[1] == 990


def test_matched_negatives_disjoint_deterministic_matched():
    rng = np.random.default_rng(1)
    n = 400_000
    d_vis = rng.gamma(shape=2.0, scale=12.0, size=n)
    pos = np.arange(0, 5000)
    pool = np.arange(5000, n)
    neg1, diag = propensity_matched_negatives(d_vis, pos, pool, 50_000, seed=42)
    neg2, _ = propensity_matched_negatives(d_vis, pos, pool, 50_000, seed=42)
    assert np.array_equal(neg1, neg2)
    assert np.intersect1d(neg1, pos).size == 0
    assert diag["n_neg"] == 50_000
    assert np.max(np.abs(np.array(diag["neg_bin_shares"]) - np.array(diag["pos_bin_shares"]))) < 0.01
    with pytest.raises(ValueError):
        propensity_matched_negatives(d_vis, pos, np.arange(0, 6000), 10, seed=0)
