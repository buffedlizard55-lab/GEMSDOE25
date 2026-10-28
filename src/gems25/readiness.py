"""Fail-closed receipt consistency gate; it does not compute or authenticate audits.

Receipts must be produced by the shared evaluators, linked to the exact raster,
pre-placement surface, template and declared registry, and reviewed separately.
Passing permits selector review only; it never authorizes an upload or weekly slot.
"""
from __future__ import annotations

import math
import re

# The footprint count is pinned by the local template/data manifest; this is not
# independent authentication of the organizer's original competition template.
FOOTPRINT_PIXELS = 5_167_373


def _sha(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def _finite(value) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _integer(value, minimum=0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= 2**63 - 1


def _number(section, key, predicate) -> bool:
    value = section.get(key)
    return _finite(value) and predicate(value)


def _cell_keys(rows):
    """Return unique (fold, draw) pairs or None for malformed/duplicate cells."""
    if not isinstance(rows, list) or not rows:
        return None
    keys = []
    for row in rows:
        if not isinstance(row, dict):
            return None
        fold, draw = row.get('fold'), row.get('draw')
        if not _integer(fold) or fold not in range(4) or not _integer(draw):
            return None
        keys.append((int(fold), int(draw)))
    return set(keys) if len(set(keys)) == len(keys) else None


def assess_readiness(evidence: dict) -> dict:
    """Reject missing, malformed, inconsistent, incomplete, or failing receipts."""
    failures = []

    def require(condition, reason):
        if not condition:
            failures.append(reason)

    if not isinstance(evidence, dict):
        evidence = {}
        failures.append('evidence must be an object')

    digest = evidence.get('raster_sha256')
    require(_sha(digest), 'missing or invalid raster SHA256')
    lane = evidence.get('lane')
    require(isinstance(lane, str) and bool(lane.strip()), 'missing assigned method lane')
    sections = {}
    for name in ('format', 'surface', 'dots', 'holdout', 'canary'):
        section = evidence.get(name)
        if not isinstance(section, dict):
            failures.append(f'missing {name} receipt')
            section = {}
        sections[name] = section
        require(_sha(digest) and section.get('raster_sha256') == digest, f'{name}: raster identity mismatch')

    fmt, surface, dots, holdout, canary = (sections[k] for k in ('format', 'surface', 'dots', 'holdout', 'canary'))
    for key in ('no_nan_inside', 'values_in_range', 'whole_array_finite_in_range', 'crs_match', 'shape_match',
                'transform_match', 'single_band', 'dtype_float32', 'catalogue_mask_exact'):
        require(fmt.get(key) is True, f'format: {key}')
    require(_sha(fmt.get('template_sha256')), 'format: missing template identity')
    require(_sha(fmt.get('labels_sha256')), 'format: missing labels identity')
    require(fmt.get('template_sha256') == surface.get('template_sha256'), 'format: template identity mismatch')
    require(_sha(fmt.get('labels_sha256')) and holdout.get('labels_sha256') == fmt.get('labels_sha256'),
            'holdout: label identity mismatch')

    for name, section in (('surface', surface), ('dots', dots)):
        require(section.get('registry_complete') is True, f'{name}: registry incomplete')
        require(_number(section, 'max_abs_rank_correlation', lambda v: 0 <= v <= .90), f'{name}: rank gate')
        require(_sha(section.get('registry_manifest_sha256')), f'{name}: missing registry identity')
        require(_sha(section.get('template_sha256')), f'{name}: missing template identity')
        require(section.get('rank_footprint_pixels') == FOOTPRINT_PIXELS, f'{name}: wrong footprint')
        require(_integer(section.get('registry_checked'), 1), f'{name}: no reference comparisons')
    require(_sha(surface.get('scores_sha256')) and dots.get('surface_sha256') == surface.get('scores_sha256'),
            'dots: pre-placement surface identity mismatch')
    for key in ('registry_manifest_sha256', 'template_sha256', 'registry_checked'):
        require(surface.get(key) is not None and surface.get(key) == dots.get(key), f'lane: {key} mismatch')
    require(_number(dots, 'max_overlap_3px', lambda v: 0 <= v <= .70), 'dots: overlap gate')
    require(dots.get('exact_duplicate') is False, 'dots: duplicate not ruled out')

    require(holdout.get('evidence_class') == 'HOLDOUT-DTI', 'holdout: wrong evidence class')
    version = holdout.get('evaluator_version')
    require(isinstance(version, str) and bool(version.strip()) and _sha(holdout.get('evaluator_sha256')),
            'holdout: missing evaluator version or SHA256')
    require(_integer(holdout.get('withheld_positives'), 1), 'holdout: missing positives')
    require(holdout.get('stage') == 'confirmation', 'holdout: confirmation required')
    require(holdout.get('same_run_comparator') is True, 'holdout: unpaired comparator')
    for key in ('whole_segment_buffered', 'visible_only_features', 'visible_mask_exact', 'pooled'):
        require(holdout.get(key) is True, f'holdout: {key}')
    require(holdout.get('alpha') == .2 and holdout.get('beta') == .8 and holdout.get('kernel_m') == 300
            and holdout.get('kernel') == 'triangular', 'holdout: metric mismatch')
    ci = holdout.get('paired_delta_ci95')
    valid_ci = isinstance(ci, list) and len(ci) == 2 and all(_finite(v) for v in ci)
    require(valid_ci and 0 < ci[0] <= ci[1] <= 1, 'holdout: improvement not established')
    ci = holdout.get('dti_ci95')
    valid_ci = isinstance(ci, list) and len(ci) == 2 and all(_finite(v) for v in ci)
    require(valid_ci and 0 <= ci[0] <= ci[1] <= 1, 'holdout: missing or invalid DTI CI')
    candidate, comparator = holdout.get('dti'), holdout.get('comparator_dti')
    require(_number(holdout, 'dti', lambda v: 0 <= v <= 1), 'holdout: invalid DTI')
    require(_finite(comparator) and 0 <= comparator <= 1 and _finite(candidate) and candidate > comparator,
            'holdout: candidate did not beat comparator')
    holdout_cells = _cell_keys(holdout.get('cells'))
    if holdout_cells is None:
        complete_cells = False
    else:
        draws = [{d for f, d in holdout_cells if f == fold} for fold in range(4)]
        complete_cells = len(draws[0]) >= 2 and all(d == draws[0] for d in draws)
    require(complete_cells, 'holdout: incomplete four-fold confirmation cells')

    run_id = holdout.get('run_id')
    require(isinstance(run_id, str) and bool(run_id.strip()) and canary.get('run_id') == run_id,
            'canary: holdout run identity mismatch')
    features = canary.get('feature_names')
    valid_features = (isinstance(features, list) and bool(features)
                      and all(isinstance(f, str) and bool(f.strip()) for f in features)
                      and len(set(features)) == len(features))
    require(canary.get('all_features_tested') is True and valid_features, 'canary: incomplete feature coverage')
    canary_cells = _cell_keys(canary.get('cells'))
    require(canary_cells is not None and canary_cells == holdout_cells, 'canary: cell coverage mismatch')
    observed = []
    all_passed = bool(valid_features and canary_cells is not None and canary_cells == holdout_cells)
    if all_passed:
        for cell in canary['cells']:
            values = cell.get('features')
            if not isinstance(values, dict) or set(values) != set(features):
                all_passed = False
                break
            for record in values.values():
                if (not isinstance(record, dict) or record.get('passed') is not True
                        or not _number(record, 'canary_auc', lambda v: 0 <= v <= .90)):
                    all_passed = False
                    break
                observed.append(record['canary_auc'])
    require(all_passed and bool(observed), 'canary: failed or missing per-feature AUC')
    require(_number(canary, 'max_auc', lambda v: 0 <= v <= .90) and bool(observed)
            and math.isclose(canary['max_auc'], max(observed), rel_tol=0, abs_tol=1e-12),
            'canary: maximum AUC inconsistent')

    return dict(selector_eligible=not failures, okay_to_submit=False, failures=failures,
                decision='SELECTOR_REVIEW_ONLY' if not failures else 'DO_NOT_SUBMIT',
                scope='Receipt consistency only; compute and authenticate all receipts separately. No slot authorization.')
