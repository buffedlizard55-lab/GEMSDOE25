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
