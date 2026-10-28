"""Conservative evidence gate, not a substitute for computing exact-file audits.

Receipts must be produced by the shared evaluators and bound to the same raster
SHA256. Passing permits selector review only; it never spends a weekly slot.
"""
from __future__ import annotations

import math
import re


def assess_readiness(evidence: dict) -> dict:
    """Missing, malformed, stale, or failing evidence blocks selector eligibility."""
    failures = []

    def require(condition, reason):
        if not condition:
            failures.append(reason)

    def finite(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

    def number(section, key, predicate):
        value = section.get(key)
        return finite(value) and predicate(value)

    digest = evidence.get('raster_sha256')
    require(isinstance(digest, str) and re.fullmatch(r'[0-9a-f]{64}', digest) is not None,
            'missing or invalid raster SHA256')
    require(isinstance(evidence.get('lane'), str) and bool(evidence['lane'].strip()), 'missing assigned method lane')
    for name in ('format', 'surface', 'dots', 'holdout', 'canary'):
        section = evidence.get(name)
        if not isinstance(section, dict):
            failures.append(f'missing {name} receipt')
            continue
        require(section.get('raster_sha256') == digest and digest is not None, f'{name}: raster identity mismatch')
        if name == 'format':
            for key in ('no_nan_inside', 'values_in_range', 'crs_match', 'shape_match', 'transform_match',
                        'single_band', 'catalogue_mask_exact'):
                require(section.get(key) is True, f'format: {key}')
        elif name in ('surface', 'dots'):
            require(section.get('registry_complete') is True, f'{name}: registry incomplete')
            require(number(section, 'max_abs_rank_correlation', lambda v: 0 <= v <= .90), f'{name}: rank gate')
            if name == 'dots':
                require(number(section, 'max_overlap_3px', lambda v: 0 <= v <= .70), 'dots: overlap gate')
                require(section.get('exact_duplicate') is False, 'dots: duplicate not ruled out')
        elif name == 'canary':
            require(section.get('all_features_tested') is True, 'canary: incomplete feature coverage')
            require(number(section, 'max_auc', lambda v: 0 <= v <= .90), 'canary: leakage or missing AUC')
        else:
            require(section.get('evidence_class') == 'HOLDOUT-DTI', 'holdout: wrong evidence class')
            require(bool(section.get('evaluator_version')), 'holdout: missing evaluator version')
            require(number(section, 'withheld_positives', lambda v: v > 0 and int(v) == v), 'holdout: missing positives')
            require(section.get('same_run_comparator') is True, 'holdout: unpaired comparator')
            for key in ('whole_segment_buffered', 'visible_only_features', 'visible_mask_exact', 'pooled'):
                require(section.get(key) is True, f'holdout: {key}')
            require(section.get('alpha') == .2 and section.get('beta') == .8
                    and section.get('kernel_m') == 300 and section.get('kernel') == 'triangular', 'holdout: metric mismatch')
            ci = section.get('paired_delta_ci95')
            valid_ci = isinstance(ci, list) and len(ci) == 2 and all(finite(v) for v in ci)
            require(valid_ci and 0 < ci[0] <= ci[1] <= 1, 'holdout: improvement not established')
            require(number(section, 'dti', lambda v: 0 <= v <= 1), 'holdout: invalid DTI')
            comparator = section.get('comparator_dti')
            candidate = section.get('dti')
            require(finite(comparator) and 0 <= comparator <= 1 and finite(candidate)
                    and candidate > comparator, 'holdout: candidate did not beat comparator')
    return dict(selector_eligible=not failures, okay_to_submit=False, failures=failures,
                decision='SELECTOR_REVIEW_ONLY' if not failures else 'DO_NOT_SUBMIT',
                scope='Receipt consistency only; caller must compute and authenticate all receipts. No slot authorization.')
