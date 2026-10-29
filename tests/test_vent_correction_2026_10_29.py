"""Guard against restoring the corrected public vent-probe claims."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_vent_probe_verdict_and_comparator():
    card = json.loads((ROOT / 'registry/run_card_gems25-vent-blind-fault-probe-20261028-407834b1710a-zero.json').read_text())
    assert card['holdout_dti'] > card['same_run_control_spread_only']['holdout_dti']
    assert card['holdout_dti'] < card['ctrl_h35_holdout_dti']
    assert card['lane_geometry']['dots_on_known_fault'] > 0
    assert not card['registry_lane_audit']['lane_clear']
    assert not card['okay_to_submit']


def test_public_entry_points_do_not_restore_wrong_verdict():
    for name in ('index.html', 'docs/index.html', 'docs/executive-summary.html', 'docs/submission-guide.html'):
        text = (ROOT / name).read_text().lower()
        assert 'do not submit' in text
        assert 'below the same-run spread control' not in text
        assert 'unique lane-clear tif: yes' not in text
        assert 'vent-probe-correction.html' in text
