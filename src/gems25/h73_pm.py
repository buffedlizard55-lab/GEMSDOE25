"""H73-PM — propensity-matched negative sampling in ``d_vis`` bins (pre-registered, knowledge/32).

The hide-and-recover sampler in :mod:`gems25.experiment` draws training negatives uniformly over the
training region. Because withheld positives are catalogue components, their distance-to-visible-fault
(``d_vis``) distribution is far more concentrated near the catalogue than the uniform background
(measured ~8x prior tilt in the 2-9 px band, knowledge/31 §2.2). A global HGB can then separate the
classes largely from catalogue-proximity columns alone, emitting apron-hugging dots that win the
component-split holdout and collapse live (H66: 69.6 % of dots at 2-9 px, OWNER-REPORTED live 0.0742).

H73-PM removes that shortcut at the *sampler*: negatives are drawn so that their ``d_vis`` histogram
matches the positives' histogram bin-for-bin. ``d_vis`` is computed from the draw's *visible*
catalogue only (never from hidden components), so the corresponding family-E features carry no
class-prior information after matching; separation must come from geophysical evidence.

Named non-fault mimic: pluvial Lake Lahontan shoreline scarps and fan channel levees far from mapped
faults, which a de-biased model may over-fire on. This module changes only *which* background pixels
are shown during training — no feature, label, evaluator or writer is altered.
"""

from __future__ import annotations

import numpy as np

BIN_EDGES_PX = (0.0, 2.0, 5.0, 9.0, 15.0, 25.0, 40.0, 80.0, np.inf)


def bin_ids(d_vis: np.ndarray, edges: tuple[float, ...] = BIN_EDGES_PX) -> np.ndarray:
    """Bin index per pixel: bin 0 is ``edges[0] <= d <= edges[1]``, bin k is ``edges[k] < d <= edges[k+1]``."""
    d = np.asarray(d_vis, dtype=np.float64)
    if not np.isfinite(d).all() or (d < 0).any():
        raise ValueError("d_vis must be finite and non-negative")
    inner = np.asarray(edges[1:-1], dtype=np.float64)
    return np.searchsorted(inner, d, side="left").astype(np.int32)


def matched_quotas(pos_bins: np.ndarray, pool_bins: np.ndarray, total: int) -> np.ndarray:
    """Per-bin negative quotas proportional to positive bin shares, capped at pool bin sizes.

    Shortfall from capped bins is redistributed proportionally among uncapped bins (iterated).
    Deterministic; quotas sum to ``min(total, pool size)``.
    """
    pos_bins = np.asarray(pos_bins)
    pool_bins = np.asarray(pool_bins)
    if pos_bins.size == 0 or total < 0:
        raise ValueError("need at least one positive and a non-negative total")
    n_bins = int(max(pos_bins.max(initial=0), pool_bins.max(initial=0))) + 1
    pos_counts = np.bincount(pos_bins, minlength=n_bins).astype(np.float64)
    pool_counts = np.bincount(pool_bins, minlength=n_bins)
    target = int(min(total, pool_counts.sum()))
    quotas = np.zeros(n_bins, dtype=np.int64)
    remaining = target
    active = pool_counts > 0
    while remaining > 0 and active.any():
        share = pos_counts.copy()
        # bins with no positives still absorb redistributed shortfall in proportion to pool mass
        share[share == 0] = 0.0
        w = np.where(active, share, 0.0)
        if w.sum() <= 0:
            w = np.where(active, pool_counts, 0).astype(np.float64)
        raw = remaining * w / w.sum()
        take = np.minimum(np.floor(raw).astype(np.int64), pool_counts - quotas)
        # largest-remainder top-up so uncapped bins can still advance by one each round
        order = np.argsort(-(raw - np.floor(raw)))
        for b in order:
            if take.sum() >= remaining:
                break
            if active[b] and quotas[b] + take[b] < pool_counts[b]:
                take[b] += 1
        if take.sum() == 0:
            break
        quotas += take
        remaining = target - int(quotas.sum())
        active = quotas < pool_counts
    return quotas


def propensity_matched_negatives(
    d_vis: np.ndarray,
    pos_idx: np.ndarray,
    pool_idx: np.ndarray,
    total: int,
    seed: int,
) -> tuple[np.ndarray, dict]:
    """Draw ``total`` negatives from ``pool_idx`` with a ``d_vis`` histogram matched to ``pos_idx``.

    ``d_vis`` is indexed by the same footprint-vector positions as ``pos_idx`` / ``pool_idx``.
    Returns (sorted negative indices, diagnostics). Raises on overlap between positives and pool.
    """
    d_vis = np.asarray(d_vis)
    pos_idx = np.asarray(pos_idx, dtype=np.int64)
    pool_idx = np.asarray(pool_idx, dtype=np.int64)
    if pos_idx.size == 0 or pool_idx.size == 0:
        raise ValueError("positives and negative pool must both be non-empty")
    if np.intersect1d(pos_idx, pool_idx, assume_unique=False).size:
        raise ValueError("negative pool overlaps positives")
    pb = bin_ids(d_vis[pos_idx])
    qb = bin_ids(d_vis[pool_idx])
    quotas = matched_quotas(pb, qb, int(total))
    rng = np.random.default_rng(int(seed))
    chosen: list[np.ndarray] = []
    for b, q in enumerate(quotas):
        if q <= 0:
            continue
        members = pool_idx[qb == b]
        chosen.append(rng.choice(members, size=int(q), replace=False))
    neg = np.sort(np.concatenate(chosen)) if chosen else np.empty(0, dtype=np.int64)
    n_bins = len(BIN_EDGES_PX) - 1
    diag = dict(
        n_pos=int(pos_idx.size),
        n_neg=int(neg.size),
        quotas=[int(x) for x in quotas],
        pos_bin_shares=[round(float(x), 5) for x in np.bincount(pb, minlength=n_bins) / pb.size],
        neg_bin_shares=[round(float(x), 5) for x in np.bincount(bin_ids(d_vis[neg]), minlength=n_bins) / max(neg.size, 1)],
        pool_bin_shares=[round(float(x), 5) for x in np.bincount(qb, minlength=n_bins) / qb.size],
    )
    return neg, diag
