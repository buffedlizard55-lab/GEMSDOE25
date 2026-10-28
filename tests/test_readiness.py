import copy

import pytest

from gems25.readiness import FOOTPRINT_PIXELS, assess_readiness


def complete():
    sha, manifest, template, surface_sha = ('a' * 64, 'b' * 64, 'c' * 64, 'd' * 64)
    cells = [dict(fold=f, draw=d) for f in range(4) for d in (60, 61)]
    canary_cells = [dict(**cell, features={
        'geomorphology': dict(passed=True, canary_auc=.8),
        'geophysics': dict(passed=True, canary_auc=.9),
    }) for cell in cells]
    lane_shared = dict(raster_sha256=sha, registry_complete=True, max_abs_rank_correlation=.90,
                       registry_manifest_sha256=manifest, template_sha256=template,
                       rank_footprint_pixels=FOOTPRINT_PIXELS, registry_checked=117)
    return dict(raster_sha256=sha, lane='assigned-test-lane',
                format=dict(raster_sha256=sha, template_sha256=template, labels_sha256='f'*64, **dict.fromkeys(
                    ('no_nan_inside', 'values_in_range', 'whole_array_finite_in_0_1', 'crs_match', 'shape_match',
                     'transform_match', 'single_band', 'dtype_float32', 'catalogue_mask_exact'), True)),
                surface=dict(**lane_shared, scores_sha256=surface_sha),
                dots=dict(**lane_shared, surface_sha256=surface_sha, max_overlap_3px=.70, exact_duplicate=False),
                canary=dict(raster_sha256=sha, run_id='confirm-1', all_features_tested=True, max_auc=.90,
                            feature_names=['geomorphology', 'geophysics'], cells=canary_cells),
                holdout=dict(raster_sha256=sha, labels_sha256='f'*64, run_id='confirm-1', stage='confirmation', cells=cells,
                             evidence_class='HOLDOUT-DTI', evaluator_version='test-only', evaluator_sha256='e'*64,
                             withheld_positives=100, same_run_comparator=True, whole_segment_buffered=True,
                             visible_only_features=True, visible_mask_exact=True, pooled=True,
                             alpha=.2, beta=.8, kernel_m=300, kernel='triangular', paired_delta_ci95=[.001, .02],
                             dti=.2, dti_ci95=[.18, .22], comparator_dti=.19))


def test_complete_is_selector_only_never_upload_approval():
    result = assess_readiness(complete())
    assert result['selector_eligible']
    assert not result['okay_to_submit']


def test_empty_fails_closed():
    assert not assess_readiness({})['selector_eligible']
    assert not assess_readiness(None)['selector_eligible']


@pytest.mark.parametrize('section,key,value', [
    ('dots', 'max_overlap_3px', .70001), ('surface', 'max_abs_rank_correlation', .90001),
    ('surface', 'max_abs_rank_correlation', float('nan')), ('dots', 'exact_duplicate', True),
    ('canary', 'max_auc', .90001), ('canary', 'max_auc', True), ('canary', 'max_auc', .8),
    ('holdout', 'paired_delta_ci95', [0, .02]), ('holdout', 'paired_delta_ci95', [.02, .01]),
    ('holdout', 'paired_delta_ci95', [float('nan'), .02]), ('holdout', 'dti_ci95', None),
    ('holdout', 'same_run_comparator', False), ('holdout', 'visible_only_features', False),
    ('holdout', 'comparator_dti', .21), ('holdout', 'comparator_dti', None),
    ('holdout', 'kernel', 'gaussian'), ('holdout', 'stage', 'screen'),
    ('format', 'values_in_range', False), ('format', 'whole_array_finite_in_0_1', False),
    ('format', 'dtype_float32', False), ('format', 'template_sha256', 'f'*64),
    ('holdout', 'labels_sha256', 'a'*64), ('format', 'raster_sha256', 'b'*64), ('dots', 'registry_complete', False),
    ('dots', 'surface_sha256', 'f'*64), ('dots', 'registry_manifest_sha256', 'f'*64),
    ('dots', 'template_sha256', 'f'*64), ('dots', 'rank_footprint_pixels', 10),
    ('dots', 'registry_checked', 116), ('canary', 'run_id', 'other-run'),
    ('canary', 'feature_names', []), ('holdout', 'evaluator_sha256', None),
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


def test_rejects_missing_duplicate_or_failing_per_feature_canaries():
    evidence = complete()
    del evidence['canary']['cells'][0]['features']['geophysics']
    assert not assess_readiness(evidence)['selector_eligible']
    evidence = complete()
    evidence['canary']['cells'][0]['features']['geomorphology']['canary_auc'] = .91
    assert not assess_readiness(evidence)['selector_eligible']
    evidence = complete()
    evidence['canary']['cells'].append(copy.deepcopy(evidence['canary']['cells'][0]))
    assert not assess_readiness(evidence)['selector_eligible']


def test_rejects_incomplete_or_unmatched_confirmation_cells():
    evidence = complete()
    evidence['holdout']['cells'].pop()
    assert not assess_readiness(evidence)['selector_eligible']
    evidence = complete()
    evidence['canary']['cells'].pop()
    assert not assess_readiness(evidence)['selector_eligible']
    evidence = complete()
    evidence['holdout']['cells'][0]['fold'] = True
    assert not assess_readiness(evidence)['selector_eligible']


def test_arbitrarily_large_numbers_fail_closed_without_overflow():
    evidence = complete()
    evidence['holdout']['withheld_positives'] = 10**1000
    assert not assess_readiness(evidence)['selector_eligible']


def test_integer_fields_reject_bool_and_integer_valued_floats():
    for value in (True, 100.0):
        evidence = complete()
        evidence['holdout']['withheld_positives'] = value
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
