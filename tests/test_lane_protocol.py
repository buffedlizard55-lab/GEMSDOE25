"""The parallel-run lane gate is literal and fails closed."""

from types import SimpleNamespace

import numpy as np
import pytest

from scripts.validate_gem_candidate import lane_check, lane_is_clear


def test_dense_five_pixel_lattice_triggers_the_literal_three_pixel_overlap_gate():
    shape = (40, 40)
    foot = np.ones(shape, dtype=bool)
    fi = np.flatnonzero(foot)
    rng = np.random.default_rng(42)
    surface = rng.normal(size=shape).astype(np.float32)
    registry = np.zeros(shape, dtype=np.float32)
    registry[::5, ::5] = 1
    # A grid offset by (2, 2) is within sqrt(8) < 3 px of the 5-px lattice.
    emitted = np.zeros(shape, dtype=bool)
    emitted[2::5, 2::5] = True

    result = lane_check(SimpleNamespace(foot=foot, fi=fi), emitted, surface,
                        [{"file": "dense-lattice.tif", "arr": registry}])

    assert result[0]["overlap_within_3px"] == 1.0
    assert result[0]["flag_overlap"] is True
    assert result[0]["duplicate"] is True
    assert lane_is_clear(result) is False


def test_lane_gate_fails_closed_for_empty_registry_and_rejects_cropped_arrays():
    shape = (20, 20)
    foot = np.ones(shape, dtype=bool)
    ctx = SimpleNamespace(foot=foot, fi=np.flatnonzero(foot))
    assert lane_is_clear([]) is False

    with pytest.raises(ValueError, match="full-grid"):
        lane_check(ctx, np.zeros((10, 10), bool), np.zeros(shape), [])


def test_saved_gem1_decision_does_not_override_the_literal_lane_failure():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / "evidence/gem_validation/results.json").read_text())
    submissions = json.loads((root / "registry/submissions.json").read_text())["files"]
    gem1 = next(s for s in submissions if s.get("id") == "gem1-blind-magnetics")

    assert report["decision"]["package_tif"] is False
    assert report["decision"]["lane_ok"] is False
    assert "DUPLICATE LANE / STOP" in report["strict_lane_review"]["strict_verdict"]
    assert gem1["lane"]["lane_clear"] is False
    assert "do not submit" in gem1["status"].lower()


def test_negative_rank_correlation_is_checked_by_absolute_magnitude():
    shape = (40, 40)
    foot = np.ones(shape, dtype=bool)
    fi = np.flatnonzero(foot)
    values = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
    surface = values.copy()
    registry = -values
    emitted = np.zeros(shape, dtype=bool)
    emitted[::10, ::10] = True

    result = lane_check(SimpleNamespace(foot=foot, fi=fi), emitted, surface,
                        [{"file": "inverse.tif", "arr": registry}])

    assert result[0]["spearman"] == pytest.approx(-1.0)
    assert result[0]["duplicate"] is True


def test_density_diagnostics_never_override_the_literal_gate():
    """A symmetric density diagnostic is informational; the literal rule decides."""
    from scripts.validate_gem_candidate import lane_is_clear_density_aware

    shape = (60, 60)
    foot = np.ones(shape, dtype=bool)
    fi = np.flatnonzero(foot)
    rng = np.random.default_rng(7)
    surface = rng.normal(size=shape).astype(np.float32)
    lattice = np.zeros(shape, dtype=np.float32)
    lattice[::5, ::5] = 1

    sparse = np.zeros(shape, dtype=bool)
    sparse[10, 10] = sparse[30, 40] = sparse[50, 15] = sparse[5, 55] = True
    row = lane_check(SimpleNamespace(foot=foot, fi=fi), sparse, surface,
                     [{"file": "dense-lattice.tif", "arr": lattice}])[0]
    assert row["halo_coverage_3px"] >= 0.70
    assert row["non_discriminative_dense"] is True
    assert row["flag_overlap"] is True            # literal flag still reported
    assert row["duplicate"] is True               # literal verdict unchanged
    assert row["reverse_overlap_within_3px"] < 0.70
    assert row["duplicate_lane"] is False         # density-aware verdict differs
    assert lane_is_clear([row]) is False
    assert lane_is_clear_density_aware([row]) is False
    assert lane_is_clear_density_aware([row], registry_complete=True) is False
    assert lane_is_clear_density_aware([]) is False  # fails closed

    # A candidate that really does sit on the lattice stays a duplicate either way.
    on_lattice = np.zeros(shape, dtype=bool)
    on_lattice[::5, ::5] = True
    row2 = lane_check(SimpleNamespace(foot=foot, fi=fi), on_lattice, surface,
                      [{"file": "dense-lattice.tif", "arr": lattice}])[0]
    assert row2["symmetric_min_overlap_3px"] == 1.0
    assert row2["duplicate_lane"] is True
    assert lane_is_clear_density_aware([row2]) is False
