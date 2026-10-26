import numpy as np

from gems25.pol3 import POL3_NAMES, compute_pol3_grids


def _planes(gravity_sign=-1):
    h, w = 64, 64
    y, x = np.mgrid[:h, :w]
    elev = y.astype(np.float32)
    grav = (gravity_sign * y).astype(np.float32)
    depth = y.astype(np.float32)
    foot = np.ones((h, w), bool)
    c2 = np.ones((h, w), np.float32)
    s2 = np.zeros((h, w), np.float32)
    valid = np.ones((h, w), np.float32)
    return elev, grav, depth, c2, s2, valid, foot


def test_pol3_signed_agreement_detects_frozen_three_field_polarity():
    grids = compute_pol3_grids(*_planes())
    assert len(POL3_NAMES) == 4
    assert all(np.isfinite(g).all() and g.min() >= 0 and g.max() <= 1 for g in grids)
    assert grids[3][20:44, 20:44].mean() > 0.9


def test_pol3_rejects_wrong_gravity_sign_and_invalid_lidar_coverage():
    wrong_sign = compute_pol3_grids(*_planes(gravity_sign=1))
    assert not wrong_sign[3].any()

    inputs = list(_planes())
    inputs[5][:] = 0.0
    invalid = compute_pol3_grids(*inputs)
    assert not invalid[3].any()
    assert all(np.isfinite(g).all() for g in invalid)
