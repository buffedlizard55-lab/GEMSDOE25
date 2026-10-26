import json

from scripts import record_live_score


def test_score_claim_cannot_remove_negative_submission_status(tmp_path, monkeypatch):
    registry = tmp_path/'registry'
    registry.mkdir()
    item = dict(file='candidate.tif', content_id='abcd', sha256='f'*64,
                status='DO NOT SUBMIT: negative lane', note='historical unscored note',
                verdict='negative', slot_approved=False, ok_to_submit_slot=False)
    (registry/'submissions.json').write_text(json.dumps({'files':[item]}))
    (registry/'live_scores.json').write_text(json.dumps({'artifacts':[]}))
    monkeypatch.setattr(record_live_score,'ROOT',tmp_path)
    monkeypatch.setattr('sys.argv',['record_live_score','--file','candidate.tif','--score','0.0742'])
    record_live_score.main()
    result=json.loads((registry/'submissions.json').read_text())['files'][0]
    assert all(result[k] == v for k,v in item.items())
    assert result['owner_reported_score'] == .0742
    assert 'OWNER-REPORTED' in result['score_evidence_class']
