"""Unit tests for the TENT/IGN3 training-sample construction (knowledge/29)."""

import numpy as np
import pytest

from gems25.objective import RING_PX, build_objective_samples, sampled_far, tent_masks, tent_targets


class _MiniCtx:
    def __init__(self, foot, labels):
        self.foot = foot
        self.labels = labels
        self.fi = np.flatnonzero(foot.ravel())

    def vec(self, mask):
        return np.flatnonzero(np.asarray(mask).ravel()[self.fi])


class _Draw:
    def __init__(self, hidden_train, train_region):
        self.hidden_train = hidden_train
        self.train_region = train_region


def _world():
    foot = np.ones((12, 12), bool)
    labels = np.zeros((12, 12), bool)
    labels[2, 2:10] = True          # visible catalogue segment
    labels[8, 2:10] = True          # pseudo-hidden training segment
    hidden_train = np.zeros((12, 12), bool)
    hidden_train[8, 2:10] = True
    train_region = foot.copy()
    return foot, labels, hidden_train, train_region


def test_tent_masks_geometry():
    _, labels, hidden_train, train_region = _world()
    dist, trace, ring, far = tent_masks(hidden_train, labels, train_region)
    assert trace.sum() == 8
    assert not (ring & labels).any() and not (far & labels).any()
    assert not (ring & trace).any() and not (far & (ring | trace)).any()
    # every ring pixel is within (0, 3] px; every far pixel beyond 3 px
    assert dist[ring].min() > 0 and dist[ring].max() <= RING_PX
    assert dist[far].min() > RING_PX
    # pixel one row above the hidden trace is ring with target 2/3
    tgt = tent_targets(dist, trace, ring)
    assert tgt[8, 5] == 1.0
    assert abs(tgt[7, 5] - 2 / 3) < 1e-6
    assert abs(tgt[6, 5] - 1 / 3) < 1e-6
    assert tgt[5, 5] == 0.0  # d = 3 -> kernel 0 at exactly R... d==3 gives max(1-1,0)=0
    # catalogue pixel adjacent to ring never receives a target
    assert tgt[2, 5] == 0.0 and not ring[3, 5] or dist[3, 5] > 3


def test_tent_masks_rejects_leak_outside_train_region():
    _, labels, hidden_train, train_region = _world()
    hidden_train[0, 0] = True
    region = train_region.copy()
    region[0, 0] = False
    with pytest.raises(ValueError):
        tent_masks(hidden_train, labels, region)


def test_build_objective_samples_shared_far_and_no_leakage():
    foot, labels, hidden_train, train_region = _world()
    ctx = _MiniCtx(foot, labels)
    out = build_objective_samples(ctx, _Draw(hidden_train, train_region), fold=1, draw_seed=90, n_neg=20)
    tent_idx, tent_y = out["tent"]
    ign_idx, ign_y = out["ign3"]
    allowed = set(ctx.vec(train_region).tolist())
    assert set(tent_idx.tolist()) <= allowed and set(ign_idx.tolist()) <= allowed
    # IGN3 positives are exactly the trace positions; TENT target 1.0 on the same set
    trace_pos = set(ctx.vec(hidden_train).tolist())
    assert set(ign_idx[ign_y == 1].tolist()) == trace_pos
    assert set(tent_idx[tent_y == 1.0].tolist()) == trace_pos
    # TENT adds ring rows with targets in (0, 1); IGN3 has no ring rows at all
    assert ((tent_y > 0) & (tent_y < 1)).any()
    ring_rows_tent = tent_idx[(tent_y > 0) & (tent_y < 1)]
    assert not np.isin(ring_rows_tent, ign_idx).any()
    # far-negative rows are shared between the arms (same pool + seed); TENT may
    # additionally carry d==3 ring-boundary rows whose target is exactly 0
    far_tent = set(tent_idx[tent_y == 0].tolist())
    far_ign = set(ign_idx[ign_y == 0].tolist())
    assert far_ign <= far_tent and len(far_ign) == 20
    dist, _, _, _ = tent_masks(hidden_train, labels, train_region)
    dist_at = dist.ravel()[ctx.fi]
    extra_zero = np.array(sorted(far_tent - far_ign))
    assert extra_zero.size == 0 or (dist_at[extra_zero] == 3.0).all()
    assert out["diag"]["n_trace"] == 8


def test_sampled_far_small_pool_returns_all():
    pool = np.array([3, 7, 9])
    assert sampled_far(pool, 20, seed=1).tolist() == [3, 7, 9]
    got = sampled_far(np.arange(100), 10, seed=42)
    assert got.size == 10 and np.unique(got).size == 10
    assert sampled_far(np.arange(100), 10, seed=42).tolist() == got.tolist()  # deterministic
