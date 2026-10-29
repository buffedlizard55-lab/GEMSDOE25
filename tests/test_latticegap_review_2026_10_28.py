"""Regressions for the archived lattice-gap file and the current negative decision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts import build_unique_submission

ROOT = Path(__file__).resolve().parents[1]
NAME = 'gems25-gems25-unique-latticegap-geothermal-20261028-20261028-aa0104874adb-nan.tif'
SHA = '79597e464fcf1d5f884f01c017597bd7facf13ca7def2b98dd5a72241bc69a82'


def read(path):
    return json.loads((ROOT / path).read_text())


def test_archived_bytes_and_independent_format_result():
    tif = ROOT / 'docs/downloads' / NAME
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == SHA
    audit = read('evidence/latticegap_format_b0b734ae.json')
    assert audit['sha256'] == SHA and audit['positive_pixels'] == 6430
    assert audit['catalogue_positive_pixels'] == 0
    assert audit['checks']['footprint_all_finite'] and audit['checks']['footprint_values_in_0_1']
    assert not audit['checks']['strict_whole_array_0_le_x_le_1']
    assert not audit['all_hard_checks_pass'] and not audit['okay_to_submit']
    assert audit['zip']['error'] == 'required ZIP missing'
    assert not tif.with_suffix('.zip').exists()


def test_complete_inventory_does_not_imply_complete_comparisons():
    restore = read('evidence/registry_restore_b0b734ae.json')
    lane = read('evidence/latticegap_final_lane_b0b734ae.json')
    assert restore['after']['complete'] and restore['after']['declared_hashes'] == 117
    assert lane['registry_inventory']['complete'] and lane['registry_checked'] == 15
    assert not lane['registry_complete'] and not lane['lane_clear']
    assert lane['errors'][0]['file'] == 'geom-horse-ensemble.tif'
    assert 'transform mismatch' in lane['errors'][0]['error']
    assert lane['rows'][0]['dots_within_3px'] == 0
    assert not lane['flagged']  # no flag among these 15 is not full-registry clearance


def test_superseded_claims_and_builder_stay_negative(capsys):
    card = read('registry/run_card_unique_latticegap_2026-10-28.json')
    rec = read('docs/downloads/checks-' + NAME.removesuffix('.tif') + '.json')
    assert card['verdict'] == 'negative' and not card['submission']['ok_to_submit']
    assert card['submission']['zip'] is None and card['holdout_dti'] is None
    assert len(card['submission']['note']) <= 140
    assert len(card['original_receipt']['sha256']) == 64 and '13c1f021' in card['original_receipt']['url']
    assert not rec['okay_to_submit'] and not rec['strict_whole_array_valid']
    before = set((ROOT / 'docs/downloads').glob('*.tif'))
    assert build_unique_submission.main() == 2
    assert set((ROOT / 'docs/downloads').glob('*.tif')) == before
    assert 'DO NOT SUBMIT' in capsys.readouterr().err


def test_inventory_and_public_guide_separate_research_from_submission():
    report = read('docs/data/download_audit.json')
    row = next(r for r in report['files'] if r['file'] == NAME)
    # Whole-array [0,1] is now a hard portal-format check; old receipt's
    # footprint-only `format_valid=True` is intentionally superseded.
    assert not row['format_valid'] and not row['strict_whole_array_valid']
    assert 'portal_all_cells_finite_in_0_1' in row['validator']['hard_failures']
    assert row['download_eligibility'] == 'RESEARCH ONLY' and not row['okay_to_submit']
    assert 'ok_to_upload' not in row['validator'] and 'UNVERIFIED' in row['novelty']
    for page in ('index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/current-review.html'):
        text = (ROOT / page).read_text()
        assert NAME in text and 'DO NOT SUBMIT' in text
        assert 'previously advertised ZIP and zero twin are absent' in text
        assert NAME.removesuffix('.tif') + '.zip' not in text
    guide = (ROOT / 'docs/submission-guide.html').read_text()
    assert 'NO competition-ready TIFF exists' in guide
    assert 'selector review only' in guide and 'portal' in guide.lower()
    assert 'DO NOT SUBMIT' in guide


def test_current_run_card_and_cache_are_honest():
    card = read('registry/run_card_b0b734ae_2026-10-28.json')
    assert card['verdict'] == 'negative' and not card['okay_to_submit']
    assert card['experiments'] == card['new_tiffs'] == card['weekly_slots_used'] == 0
    assert card['raster_sha256'] is card['holdout_dti'] is card['submission_name'] is None
    assert len(card['note']) <= 140
    cache = read('evidence/cache_rebuild_b0b734ae.json')['files']
    assert len(cache) == 6 and all(r['matches_prior'] for r in cache.values())
