"""Independently replay the negative screen from raw per-cell and per-feature evidence."""
import hashlib
import json
import subprocess
from pathlib import Path

from gems25.validation import pooled_summary

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return json.loads((ROOT/rel).read_text())


def test_h80_raw_cells_recompute_all_pooled_and_paired_results():
    rows = [json.loads(s) for s in (ROOT/'evidence/h80_exp1/cells.jsonl').read_text().splitlines()]
    stored = read('evidence/h80_exp1/summary.json')
    assert len(rows) == 56
    for arm in ('CTRL_CRUSTAL56', 'F0_G0', 'F1_G0', 'F0_G1', 'F1_G1', 'H80_CRUSTAL60'):
        assert pooled_summary(rows, candidate=arm, control='CTRL_H35') == stored[arm]
    assert pooled_summary(rows, candidate='F1_G1', control='CTRL_CRUSTAL56') == stored['vs_crustal56']
    card = read('registry/run_card_h80_2026-10-28.json')
    arm = stored['F1_G1']['arms']['F1_G1']
    assert card['holdout_dti']['dti'] == arm['pooled_dti']
    assert card['holdout_dti']['ci95'] == arm['ci95']
    assert card['holdout_dti']['paired_ci95'][1] < 0
    assert card['holdout_dti']['withheld_positive_occurrences'] == 26367
    assert card['verdict'] == 'negative' and not card['okay_to_submit']
    assert card['raster_sha256'] is None and card['submission_name'] is None
    assert card['estimated_competition_score'] is None and not card['new_raster_created']
    assert len(card['submission_note']) <= 140
    assert card['budget']['experiments_completed'] == 1
    assert not list((ROOT/'docs/downloads').glob('*h80*'))


def test_h80_every_feature_and_regime_canary_saved():
    records = [json.loads(s) for s in (ROOT/'evidence/h80_exp1/canaries.jsonl').read_text().splitlines()]
    assert {(r['fold'], r['draw']) for r in records} == {(f,d) for f in range(4) for d in (140,141)}
    assert sum(len(r['features']) for r in records) == 792
    assert all(len(r['features']) == 99 and r['all_passed'] for r in records)
    assert all(v['passed'] and v['canary_auc'] <= .9 and v['missingness_auc'] is not None
               for r in records for v in r['features'].values())


def test_h80_frozen_code_is_recoverable_at_recorded_commit():
    card = read('registry/run_card_h80_2026-10-28.json')
    commit = card['frozen_execution_source_commit']
    # A shallow CI checkout may not contain historical Git objects. Always
    # check receipt shape; verify exact source bytes when the object is local.
    present = subprocess.run(['git','cat-file','-e',commit], cwd=ROOT, capture_output=True).returncode == 0
    for path, digest in read('evidence/h80_exp1/design.json')['hashes'].items():
        assert len(digest) == 64
        if present:
            raw = subprocess.run(['git','show',f'{commit}:{path}'], cwd=ROOT, capture_output=True, check=True).stdout
            assert hashlib.sha256(raw).hexdigest() == digest


def test_h80_pages_do_not_offer_an_unvalidated_submission():
    for name in ('index.html','docs/index.html','docs/current-review.html','docs/executive-summary.html'):
        text = (ROOT/name).read_text()
        assert 'H80 tested' in text and '0.08744' in text and '26,367' in text
        assert text.index('OK TO SUBMIT: NO') < text.index('H80 tested')
        assert 'not heatflow' in text and 'UNKNOWN' in text
        assert 'ready-to-submit candidate you may choose' not in text
    assert 'DO_NOT_SUBMIT' == read('evidence/h80_readiness.json')['decision']
