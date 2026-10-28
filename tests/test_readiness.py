import copy

import pytest

from gems25.readiness import assess_readiness


def complete():
    sha = 'a' * 64
    return dict(raster_sha256=sha, lane='assigned-test-lane',
                format=dict(raster_sha256=sha, **dict.fromkeys(
                    ('no_nan_inside', 'values_in_range', 'crs_match', 'shape_match', 'transform_match',
                     'single_band', 'catalogue_mask_exact', 'whole_array_finite_in_0_1'), True)),
                surface=dict(raster_sha256=sha, registry_complete=True, max_abs_rank_correlation=.90),
                dots=dict(raster_sha256=sha, registry_complete=True, max_abs_rank_correlation=.90,
                          max_overlap_3px=.70, exact_duplicate=False),
                canary=dict(raster_sha256=sha, all_features_tested=True, max_auc=.90),
                holdout=dict(raster_sha256=sha, evidence_class='HOLDOUT-DTI', evaluator_version='test-only',
                             withheld_positives=100, same_run_comparator=True, whole_segment_buffered=True,
                             visible_only_features=True, visible_mask_exact=True, pooled=True,
                             alpha=.2, beta=.8, kernel_m=300, kernel='triangular', paired_delta_ci95=[.001, .02], dti=.2, dti_ci95=[.18, .22], comparator_dti=.19))


def test_complete_is_selector_only_never_upload_approval():
    result = assess_readiness(complete())
    assert result['selector_eligible']
    assert not result['okay_to_submit']


def test_empty_fails_closed():
    assert not assess_readiness({})['selector_eligible']


@pytest.mark.parametrize('section,key,value', [
    ('dots', 'max_overlap_3px', .70001), ('surface', 'max_abs_rank_correlation', .90001),
    ('surface', 'max_abs_rank_correlation', float('nan')), ('dots', 'exact_duplicate', True),
    ('canary', 'max_auc', .90001), ('canary', 'max_auc', True),
    ('holdout', 'paired_delta_ci95', [0, .02]), ('holdout', 'paired_delta_ci95', [.02, .01]),
    ('holdout', 'paired_delta_ci95', [float('nan'), .02]),
    ('holdout', 'same_run_comparator', False), ('holdout', 'visible_only_features', False),
    ('holdout', 'comparator_dti', .21), ('holdout', 'comparator_dti', None),
    ('holdout', 'kernel', 'gaussian'), ('format', 'values_in_range', False),
    ('format', 'raster_sha256', 'b'*64), ('dots', 'registry_complete', False),
])
def test_rejects_failed_gate(section, key, value):
    evidence = copy.deepcopy(complete())
    evidence[section][key] = value
    assert not assess_readiness(evidence)['selector_eligible']


@pytest.mark.parametrize('section', ['format', 'surface', 'dots', 'holdout', 'canary'])
def test_missing_receipt(section):
    evidence = complete()
    del evidence[section]
    assert not assess_readiness(evidence)['selector_eligible']


@pytest.mark.parametrize('value', [None, [], True, [0.2], [0.3, 0.1],
                                  [float('nan'), .3], [-.1, .3], [.1, 1.1], [False, .3]])
def test_absolute_ci_required(value):
    evidence = complete()
    evidence['holdout']['dti_ci95'] = value
    assert not assess_readiness(evidence)['selector_eligible']


def test_legacy_receipts_do_not_silently_grandfather_nan_archives():
    evidence = complete()
    del evidence['format']['whole_array_finite_in_0_1']
    assert not assess_readiness(evidence)['selector_eligible']


@pytest.mark.parametrize('value', [None, [], 1, 'receipt'])
def test_malformed_top_level_fails_closed(value):
    assert assess_readiness(value)['decision'] == 'DO_NOT_SUBMIT'
