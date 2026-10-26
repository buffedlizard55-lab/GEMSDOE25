import numpy as np

from gems25.features import build_catalogue_features, dequantize, nearest_fill, ridge_strength
from gems25.families import FAMILIES, family_columns
from gems25.block_holdout import BlockHoldout
from gems25.holdout import COLLAR_PX, Holdout, quadrant_ids
from gems25.metric import dti_binary


def test_dequantize_inverts_the_documented_quantisation():
    xmax = 1.5
    x = np.array([0.0, 0.01, 0.3, 0.9, 1.5], np.float32)
    q = (1 + np.round(254 * np.sqrt(np.clip(x / xmax, 0, 1)))).astype(np.uint8)
    back = dequantize(q, xmax, "sqrt")
    assert np.allclose(back, x, atol=xmax * 0.01)
    assert np.isnan(dequantize(np.array([0], np.uint8), xmax, "sqrt")).all()  # 0 = no lidar -> NaN


def test_nearest_fill_removes_nans_without_touching_valid_pixels():
    a = np.arange(25, dtype=np.float32).reshape(5, 5)
    a[2, 2] = np.nan
    f = nearest_fill(a)
    assert np.isfinite(f).all() and f[0, 0] == 0 and f[4, 4] == 24


def test_ridge_strength_peaks_on_a_crest():
    yy, xx = np.mgrid[0:40, 0:40]
    z = np.exp(-((yy - 20) ** 2) / 6.0).astype(np.float32)
    r = ridge_strength(z, 1.5)
    assert r[20, 20] > 5 * r[5, 20] and (r >= 0).all()


def test_catalogue_features_orientation_conventions_and_distance():
    H = W = 120
    foot_idx = np.arange(H * W)
    horiz = np.zeros((H, W), bool)
    horiz[60, 10:110] = True  # line along x (columns): strike 0 deg -> cos2 = +1
    E = build_catalogue_features(horiz, foot_idx).reshape(7, H, W)
    assert E[0][60, 50] == 0.0  # log1p(0)
    assert E[1][58, 50] > 0.9 and abs(E[2][58, 50]) < 0.2
    vert = np.zeros((H, W), bool)
    vert[10:110, 60] = True  # strike 90 deg -> cos2 = -1
    E2 = build_catalogue_features(vert, foot_idx).reshape(7, H, W)
    assert E2[1][50, 58] < -0.9
    far = E[0][5, 5]
    assert far > E[0][58, 50] and far <= np.log1p(60.0) + 1e-6  # distance is capped at 60 px
    assert 0 <= E[6].min() and E[6].max() <= 1.0  # coherence


def test_family_registry_is_a_partition_of_the_column_set():
    cols = [c for L in FAMILIES for c in family_columns(L)]
    assert len(cols) == len(set(cols))
    assert sum(len(family_columns(L)) for L in "ABCD") == 64 and len(family_columns("E")) == 7


def _toy_holdout(seed=0):
    rng = np.random.default_rng(seed)
    H, W = 400, 460
    foot = np.zeros((H, W), bool)
    foot[10:390, 15:445] = True
    lab = np.zeros((H, W), bool)
    for _ in range(260):  # short random segments
        y, x = rng.integers(20, 380), rng.integers(25, 420)
        L = rng.integers(4, 30)
        if rng.random() < 0.5:
            lab[y, x : x + L] = True
        else:
            lab[y : y + L, x] = True
    return foot, lab & foot


def test_quadrants_partition_the_footprint():
    foot, _ = _toy_holdout()
    q = quadrant_ids(foot)
    assert (q[foot] >= 0).all() and (q[~foot] == -1).all() and set(np.unique(q[foot])) == {0, 1, 2, 3}


def test_draw_hides_about_twenty_percent_and_never_leaks_across_the_collar():
    foot, lab = _toy_holdout()
    H = Holdout(foot, lab, 0.20)
    for fold in range(4):
        d = H.draw(fold, 0)
        in_q = lab & d.quadrant
        share = d.hidden_test.sum() / max(in_q.sum(), 1)
        assert 0.1 < share < 0.45, share  # whole components are hidden, so the share is approximate
        assert not (d.hidden_test & d.visible).any() and not (d.hidden_train & d.visible).any()
        assert not (d.hidden_train & d.collar).any()  # no training positives inside the test collar
        assert (d.visible <= lab).all()
        assert not (d.hidden_train & d.hidden_test).any()
        # determinism
        d2 = H.draw(fold, 0)
        assert np.array_equal(d.hidden_test, d2.hidden_test) and np.array_equal(d.hidden_train, d2.hidden_train)
        d3 = H.draw(fold, 1)
        assert not np.array_equal(d.hidden_test, d3.hidden_test)
    assert COLLAR_PX == 15


def test_scoring_masks_visible_faults_and_scores_only_hidden_truth():
    foot, lab = _toy_holdout()
    H = Holdout(foot, lab, 0.20)
    d = H.draw(0, 0)
    perfect = d.hidden_test.copy()
    r = H.score(d, perfect)
    assert r["dti"] > 0.99 and r["n_truth"] == int(d.hidden_test[d.bbox].sum())
    with_known = perfect | (d.visible & d.quadrant)  # emitting on masked known pixels must not matter
    assert abs(H.score(d, with_known)["dti"] - r["dti"]) < 1e-12
    assert H.score(d, np.zeros_like(perfect))["dti"] == 0.0
    # the generic scorer agrees
    assert abs(dti_binary(perfect[d.bbox], d.hidden_test[d.bbox], valid=d.quadrant[d.bbox], known=d.visible[d.bbox])["dti"] - r["dti"]) < 1e-12


def test_block_component_picker_hides_no_training_components_at_zero_target():
    foot = np.ones((100, 100), bool)
    labels = np.zeros((100, 100), bool)
    labels[50, 50] = True
    holdout = BlockHoldout(foot, labels, block_size_px=40)
    selected = holdout._pick(np.random.default_rng(0), np.array([1]), 0.0)
    assert selected.size == 0


def test_block_holdout_uses_25km_checkerboard_and_hides_all_test_components():
    foot, labels = _toy_holdout(seed=5)
    holdout = BlockHoldout(foot, labels, hide_frac=0.20)
    assert holdout.block_size_px == 250
    assert holdout.block_grid_shape == (2, 2)
    assert holdout.FOLD_NAMES == ("block_parity_00", "block_parity_01", "block_parity_10", "block_parity_11")
    assert (holdout.quad[foot] >= 0).all() and (holdout.quad[~foot] == -1).all()
    # Each 25-km block uses one checkerboard colour, independent of the footprint mask.
    for br in range(holdout.block_grid_shape[0]):
        for bc in range(holdout.block_grid_shape[1]):
            r0, c0 = br * holdout.block_size_px, bc * holdout.block_size_px
            r1, c1 = min(r0 + holdout.block_size_px, foot.shape[0]), min(c0 + holdout.block_size_px, foot.shape[1])
            local_foot = foot[r0:r1, c0:c1]
            block = holdout.quad[r0:r1, c0:c1]
            values = np.unique(block[local_foot])
            assert values.size == 1 and values[0] == 2 * (br % 2) + (bc % 2)
    for fold in range(4):
        draw = holdout.draw(fold, seed=94)
        q_labels = labels & draw.quadrant
        assert np.array_equal(draw.hidden_test, q_labels)  # all labelled pixels in every test block are truth
        assert not (draw.visible & draw.quadrant).any()
        test_components = np.unique(holdout.comp[q_labels])
        test_components = test_components[test_components > 0]
        if test_components.size:
            assert not np.isin(holdout.comp, test_components)[draw.visible].any()
        assert not (draw.hidden_train & draw.collar).any()
        assert (draw.hidden_train <= draw.train_region).all()
        assert not (draw.hidden_train & draw.hidden_test).any()
        assert np.array_equal(draw.hidden_test, holdout.draw(fold, 94).hidden_test)
        assert np.array_equal(draw.hidden_train, holdout.draw(fold, 94).hidden_train)
        assert not np.array_equal(draw.hidden_train, holdout.draw(fold, 95).hidden_train)


def test_block_holdout_rejects_degenerate_blocks_and_fold_ids():
    foot = np.ones((100, 100), bool)
    labels = np.zeros_like(foot)
    with np.testing.assert_raises(ValueError):
        BlockHoldout(foot, labels, block_size_px=2 * COLLAR_PX)
    holdout = BlockHoldout(foot, labels, block_size_px=40)
    with np.testing.assert_raises(ValueError):
        holdout.draw(4, 0)
