"""Training-objective / sampling variants for the 2026-10-26 session (pre-registered, knowledge/29).

Exp 1 changes *only* how training pixels/targets are drawn around the pseudo-hidden
trace of a hide-and-recover draw:

* BIN  (repo status quo, lives in ``gems25.experiment.Cell``): exact trace pixels positive,
  uniform negatives excluding catalogue pixels and d<=1.5 px to the trace.
* TENT (primary): regression target = triangular kernel credit ``k(d)=max(1-d/3,0)`` to
  ``hidden_train`` — trace 1.0, ring ``0<d<=3`` (non-catalogue) ``1-d/3``, far pixels 0.0.
* IGN3 (diagnostic): classifier as BIN but negatives exclude ``d<=3`` px to the trace.

Everything is derived from ``hidden_train`` and ``train_region`` of one
``gems25.holdout.Draw``; the held-out test-quadrant truth is never read here.
All returned sample indices are positions in the footprint vector (``Context.fi``),
matching ``Cell.train_idx`` conventions.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

from .metric import kernel

N_NEG_OBJECTIVE = 300_000
RING_PX = 3.0  # the metric kernel radius, in pixels (300 m at 100 m/px)


def tent_masks(hidden_train, labels, train_region):
    """Return ``(dist, trace, ring, far)`` boolean grids for one draw.

    ``labels`` is the full catalogue (visible + hidden + hidden-test): ring/far pixels
    never sit on any catalogue pixel, mirroring ``Cell``'s negative-pool construction.
    """
    hidden_train = np.asarray(hidden_train, bool)
    labels = np.asarray(labels, bool)
    train_region = np.asarray(train_region, bool)
    if not (hidden_train.shape == labels.shape == train_region.shape):
        raise ValueError("aligned 2-D grids required")
    if (hidden_train & ~train_region).any():
        raise ValueError("hidden_train leaks outside train_region")
    dist = distance_transform_edt(~hidden_train)
    trace = hidden_train & train_region
    ring = train_region & ~labels & (dist > 0.0) & (dist <= RING_PX)
    far = train_region & ~labels & (dist > RING_PX)
    return dist, trace, ring, far


def tent_targets(dist, trace, ring):
    """Target value at every grid pixel for the tent strata (0 outside trace/ring)."""
    out = np.zeros(np.asarray(dist).shape, np.float32)
    out[np.asarray(ring, bool)] = kernel(np.asarray(dist)[np.asarray(ring, bool)]).astype(np.float32)
    out[np.asarray(trace, bool)] = 1.0
    return out


def sampled_far(far_positions, n_max: int, seed: int) -> np.ndarray:
    """Uniform choice without replacement from ascending far positions (Cell's RNG convention)."""
    far_positions = np.asarray(far_positions)
    if far_positions.size <= n_max:
        return far_positions.copy()
    rng = np.random.default_rng(seed)
    return rng.choice(far_positions, size=int(n_max), replace=False)


def assert_within(positions, allowed_positions) -> None:
    """Fail loudly if any sample position lies outside the allowed (train-region) positions."""
    positions = np.asarray(positions)
    allowed = np.asarray(allowed_positions)
    if positions.size == 0:
        raise ValueError("empty training sample")
    inside = np.isin(positions, allowed, assume_unique=True) if np.unique(allowed).size == allowed.size \
        else np.isin(positions, allowed)
    if not bool(inside.all()):
        raise ValueError(f"{int((~inside).sum())} training positions outside the allowed region")


def build_objective_samples(ctx, draw, fold: int, draw_seed: int, n_neg: int = N_NEG_OBJECTIVE) -> dict:
    """Footprint-vector training sets for TENT and IGN3 for one cell.

    Returns dict with ``tent=(idx, target)``, ``ign3=(idx, y)`` and ``diag`` counts.
    The far-negative draw is shared between TENT and IGN3 (same pool, same seed
    formula ``777 + 31*fold + draw`` as ``Cell``), so the two arms differ only in
    what they do with the trace/ring zone.
    """
    dist, trace, ring, far = tent_masks(draw.hidden_train, ctx.labels, draw.train_region)
    target_grid = tent_targets(dist, trace, ring)
    flat_target = target_grid.ravel()[ctx.fi]

    trace_pos = ctx.vec(trace)
    ring_pos = ctx.vec(ring)
    far_pos = sampled_far(ctx.vec(far), n_neg, 777 + 31 * int(fold) + int(draw_seed))
    allowed = ctx.vec(draw.train_region)

    tent_idx = np.sort(np.concatenate([trace_pos, ring_pos, far_pos]))
    tent_y = flat_target[tent_idx].astype(np.float32)
    assert_within(tent_idx, allowed)
    if not (np.isfinite(tent_y).all() and (tent_y >= 0).all() and (tent_y <= 1).all()):
        raise ValueError("tent targets must lie in [0, 1]")

    ign_idx = np.sort(np.concatenate([trace_pos, far_pos]))
    ign_y = np.isin(ign_idx, trace_pos).astype(np.int8)
    assert_within(ign_idx, allowed)

    return dict(
        tent=(tent_idx, tent_y),
        ign3=(ign_idx, ign_y),
        diag=dict(
            n_trace=int(trace_pos.size), n_ring=int(ring_pos.size), n_far_sampled=int(far_pos.size),
            tent_target_mass=float(tent_y.sum()), tent_rows=int(tent_idx.size), ign3_rows=int(ign_idx.size),
        ),
    )
