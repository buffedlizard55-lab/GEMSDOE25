"""Current review/evidence consistency; negative results must stay negative."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from gems25.validation import pooled_summary

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'evidence/rod_2026-10-26'


def test_pooled_result_recomputed_from_cells_and_card_agrees():
    rows = [json.loads(s) for s in (RUN/'cells.jsonl').read_text().splitlines()]
    computed = pooled_summary(rows)
    stored = json.loads((RUN/'analysis.json').read_text())
    card = json.loads((RUN/'run_card.json').read_text())
    for k, value in computed.items():
        assert value == stored[k], k
    assert stored['screen_passed'] is False
    assert card['holdout_dti'] == computed['arms']['ROD']['pooled_dti']
    assert card['ci95'] == computed['arms']['ROD']['ci95']
    assert card['withheld_positives']['occurrences'] == computed['arms']['ROD']['withheld_positive_occurrences']
    for path, digest in card['evaluator'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == digest


def test_negative_lane_stops_writer_no_fabricated_receipt():
    card = json.loads((RUN/'run_card.json').read_text())
    lane = json.loads((RUN/'final_lane.json').read_text())
    assert card['verdict'] == 'negative' and card['okay_to_submit'] is False
    assert len(card['note']) <= 140
    assert all(card[k] is None for k in ('raster_sha256', 'validator_output', 'submission_name'))
    assert not list((ROOT/'docs/downloads').glob('*rod1*.tif'))
    assert card['correlation_overlap_vs_registry']['final_dots']['max_overlap'] == max(r['overlap_within_3px'] for r in lane)
    assert any(r['duplicate'] for r in lane)
    assert not (RUN/'validator.json').exists()


def test_every_feature_has_canary_on_every_cell():
    cells = json.loads((RUN/'feature_canaries.json').read_text())
    assert {(r['fold'], r['draw']) for r in cells} == {(f, d) for f in range(4) for d in (60, 61)}
    for r in cells:
        assert len(r['features']) == 67
        assert {'D_K', 'D_Th', 'D_U', 'L_step_max', 'L_coh100', 'ROD_primary'} <= set(r['features'])
        assert all(v['passed'] and v['canary_auc'] <= .90 for v in r['features'].values())


def test_focus_claims_are_not_organizer_receipts():
    report = json.loads((ROOT/'evidence/focus_audit_2026-10-26.json').read_text())
    assert {r['site'] for r in report['sites']} == {f'GEMSDOE{n}' for n in (24,25,27,28,30,31,32,33,36)}
    assert all('OWNER-REPORTED' in r['score_class'] and r['okay_to_submit_as_new'] is False for r in report['sites'])
    assert max(report['sites'], key=lambda r:r['owner_reported_score'])['site'] == 'GEMSDOE32'
    assert report['identities']['gems32_b2_equals_d28_distance_gt_2'] is True


def test_executive_summary_separates_holdout_from_score_and_strict_novelty():
    page = (ROOT/'docs/executive-summary.html').read_text()
    assert 'Estimated competition score' in page
    assert 'NOT ESTIMATED' in page
    assert 'HOLDOUT-DTI 0.050577' in page
    assert '21,835 withheld positives' in page
    assert 'Unique under literal lane rule?' in page
    assert '100% within 3 px of the registered r13 lattice; threshold 70%' in page
    assert 'DO NOT SUBMIT' in page
    assert 'dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif' in page
    assert 'Exact-mask duplicate of GEMSDOE30 (D2.8)' in page
    assert 'Exact-mask duplicate of GEMSDOE31 (R1)' in page


def test_current_review_run_card_is_complete_and_honest():
    card = json.loads((ROOT/'registry/run_card_repo_review_2026-10-26_session.json').read_text())
    assert card['verdict'].startswith('negative')
    assert card['holdout_dti']['label'] == 'HOLDOUT-DTI'
    assert card['holdout_dti']['source'].startswith('saved prior-session')
    assert card['holdout_dti']['withheld_positive_count'] == 21835
    assert card['correlation_overlap_vs_registry']['strict_final_dot_overlap']['candidate_dots_within_3px_fraction'] == 1.0
    assert card['raster']['generated_in_this_review'] is False
    assert card['validator_output']['all_pixels_finite'] is True
    assert card['validator_output']['grid_matches_live_template'] is None
    assert card['submission_note_characters'] == len(card['submission_note']) <= 140
    assert card['score_projection'] is None


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(v for k,v in attrs if k in ('href', 'src') and v)


@pytest.mark.parametrize('rel', ['index.html', 'docs/index.html', 'docs/executive-summary.html',
                                'docs/current-review.html', 'docs/history.html', 'docs/submission-history.html',
                                'docs/research.html', 'docs/sources.html'])
def test_all_static_local_paths_resolve(rel):
    path = ROOT/rel
    parser = Links()
    parser.feed(path.read_text())
    for href in parser.links:
        parts = urlsplit(href)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        target = (path.parent/unquote(parts.path)).resolve()
        assert target.is_relative_to(ROOT) and target.exists(), (rel, href)
