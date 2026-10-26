import numpy as np
import pytest

from gems25.rod import offset_evidence, scale_channel, shifted
from gems25.validation import feature_canary, pooled_dti, pooled_summary


def test_shift_does_not_wrap():
    a = np.arange(12).reshape(3, 4)
    b = shifted(a, 1, -1)
    assert np.isnan(b[:, 0]).all()
    assert np.isnan(b[-1]).all()
    assert b[0, 1] == a[1, 0]
    assert np.isnan(shifted(a, 10, 10)).all()


def test_constant_and_missing_channels_have_no_offset():
    assert not offset_evidence([np.ones((12, 12)) for _ in range(3)]).any()
    assert not offset_evidence([np.full((12, 12), np.nan) for _ in range(3)]).any()


def test_translated_texture_produces_offset():
    # Across the horizontal boundary the pattern is translated by two columns.
    y, x = np.indices((40, 40))
    a = ((x + 2*(y > 20)) % 7)/7
    v = offset_evidence([a.astype(np.float32)]*3)
    assert v[19:22, 8:-8].max() > 0
    assert np.isfinite(v).all() and v.min() >= 0 and v.max() <= 1


def test_scale_handles_constant_and_missing():
    a = np.array([2., 2., np.nan])
    s = scale_channel(a, np.ones(3, bool))
    assert np.array_equal(s[:2], [0, 0])
    assert np.isnan(s[-1])
    with pytest.raises(ValueError):
        scale_channel(a, np.zeros(3, bool))


def test_canary_inverted_leakage():
    y = np.array([0, 0, 1, 1])
    r = feature_canary(1-y, y)
    assert r['auc'] == 0 and r['canary_auc'] == 1 and not r['passed']


def test_canary_missingness_and_missing_class():
    y = np.r_[np.zeros(10), np.ones(10)]
    x = np.zeros(20)
    x[:9] = np.nan
    r = feature_canary(x, y)
    assert r['missingness_auc'] < .1 and not r['passed']
    assert not feature_canary(np.full(20, np.nan), y)['passed']
    assert not feature_canary(np.zeros(10), np.zeros(10))['passed']
    assert feature_canary(np.ones(20), y)['passed']


def test_pooled_is_not_mean_dti_and_pairing_enforced():
    rows = [dict(fold=f, draw=0, arm=a, tp=1+f, fp=2, n_truth=10+50*f)
            for f in range(4) for a in ('H35', 'ROD')]
    r = pooled_summary(rows)
    assert r['paired_gain'] == 0 and r['paired_ci95'] == [0, 0]
    assert not r['screen_passed']
    assert r['arms']['ROD']['pooled_dti'] == pooled_dti([x for x in rows if x['arm'] == 'ROD'])
    with pytest.raises(ValueError):
        pooled_summary(rows[:-1])
    with pytest.raises(ValueError):
        pooled_summary(rows + [rows[0]])
    rows[0]['n_truth'] += 1
    with pytest.raises(ValueError):
        pooled_summary(rows)
