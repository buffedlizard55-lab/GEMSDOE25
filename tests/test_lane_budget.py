import numpy as np
import pytest

from gems25.lane_budget import halo_budget, rule_can_pass


def test_formula_matches_bruteforce_small_grid():
    # A 20x20 domain, one reference dot: the halo covers a 7x7 block (radius 3).
    domain = np.ones((20, 20), bool)
    reference = np.zeros((20, 20), bool)
    reference[10, 10] = True
    b = halo_budget(domain, reference)

    rows, cols = np.mgrid[0:20, 0:20]
    halo = (rows - 10) ** 2 + (cols - 10) ** 2 <= 9
    assert b["covered_domain_pixels"] == int(halo.sum()) == 29
    assert b["uncovered_pixels"] == 371
    assert b["max_feasible_unique_dots"] == 400  # every dot can sit outside a tiny halo
    assert rule_can_pass(400, 371)


def test_empty_reference_allows_every_dot():
    b = halo_budget(np.ones((5, 5), bool), np.zeros((5, 5), bool))
    assert b["uncovered_pixels"] == 25 and b["max_feasible_unique_dots"] == 25


def test_total_coverage_permits_only_arithmetically_small_sets():
    # Halo covers 8 of 10 eligible pixels, leaving 2 outside. K dots can place
    # at most 2 outside, so 10*max(0,K-2) <= 7K holds only for K <= 6.
    domain = np.ones((2, 5), bool)
    reference = np.zeros((2, 5), bool)
    reference[:, 0:4] = True
    b = halo_budget(domain, reference, radius_px=0.0)
    assert b["uncovered_pixels"] == 2
    assert b["max_feasible_unique_dots"] == 6
    assert rule_can_pass(6, 2)
    assert rule_can_pass(2, 2)
    assert not rule_can_pass(7, 2)
    assert not rule_can_pass(10, 2)


def test_threshold_is_exact_not_rounded():
    assert rule_can_pass(10, 3)          # 70% exactly
    assert not rule_can_pass(11, 3)      # 72.7%


def test_empty_domain_and_bad_shapes_reject():
    with pytest.raises(ValueError, match="empty domain"):
        halo_budget(np.zeros((4, 4), bool), np.zeros((4, 4), bool))
    with pytest.raises(ValueError, match="differ"):
        halo_budget(np.ones((4, 4), bool), np.ones((3, 4), bool))
    with pytest.raises(ValueError, match="boolean"):
        halo_budget(np.ones((4, 4)), np.zeros((4, 4), bool))
    with pytest.raises(ValueError, match="non-negative"):
        halo_budget(np.ones((4, 4), bool), np.zeros((4, 4), bool), radius_px=-1)
    with pytest.raises(ValueError, match="cap"):
        halo_budget(np.ones((4, 4), bool), np.zeros((4, 4), bool), cap=1.0)
    with pytest.raises(ValueError):
        rule_can_pass(-1, 3)


def test_radius_grows_coverage():
    domain = np.ones((30, 30), bool)
    reference = np.zeros((30, 30), bool)
    reference[15, 15] = True
    small = halo_budget(domain, reference, radius_px=1.0)["covered_domain_pixels"]
    big = halo_budget(domain, reference, radius_px=4.0)["covered_domain_pixels"]
    assert small < big
