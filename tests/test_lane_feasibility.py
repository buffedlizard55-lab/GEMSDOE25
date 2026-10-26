"""Capacity proof checked against exhaustive toy placements and strict boundaries."""
import itertools
import json
from pathlib import Path

import numpy as np
import pytest

from gems25.lane_feasibility import capacity_bound, halo_capacity


def test_pigeonhole_bound_matches_exhaustive_placements():
    for n in range(1, 9):
        for u in range(n+1):
            for k in range(1, n+1):
                bound = capacity_bound(n, u, k)
                actual = min(sum(i >= u for i in subset)/k for subset in itertools.combinations(range(n), k))
                assert bound['minimum_overlap'] == actual
                assert bound['impossible'] == (actual > .7)


def test_strict_cap_boundary_uses_rational_arithmetic():
    assert not capacity_bound(100, 3, 10)['impossible']  # exactly 70%
    assert capacity_bound(100, 3, 11)['impossible']
    assert capacity_bound(100, 3, 10)['max_dots_not_ruled_out'] == 10
    assert capacity_bound(100, 0, 1)['impossible']
    assert not capacity_bound(100, 100, 100)['impossible']


@pytest.mark.parametrize('args', [(10,11,1), (10,-1,1), (10,1,0), (10,1,11), (10,1,2.5), (True,0,1)])
def test_invalid_counts_fail_closed(args):
    with pytest.raises(ValueError):
        capacity_bound(*args)


def test_halo_keeps_catalogue_reference_dots_and_includes_radius_boundary():
    foot = np.ones((9,9), bool)
    known = np.zeros_like(foot)
    known[4,4] = True
    ref = np.zeros(foot.shape)
    ref[4,4] = 1
    result = halo_capacity(foot, known, ref, 3)
    assert result['eligible_pixels'] == 80
    assert result['covered_pixels'] == 28  # integer circle: 29 pixels minus known center
    assert result['reference_dots'] == 1
    ref[:] = np.nan
    assert halo_capacity(foot, known, ref)['covered_pixels'] == 0
    ref[4,4] = np.inf
    assert halo_capacity(foot, known, ref)['reference_dots'] == 0


def test_evidence_bound_recomputes_without_raw_data():
    root = Path(__file__).resolve().parents[1]
    evidence = json.loads((root/'evidence/lane_feasibility_2026-10-26.json').read_text())
    g = evidence['geometry']
    for case in evidence['cases']:
        assert case == capacity_bound(g['eligible_pixels'], g['uncovered_pixels'], case['dots'])
    assert evidence['okay_to_submit'] is False
    assert evidence['experiments'] == 0
