"""A renamed TIFF or zero-outside variant is not new prediction content."""
import json
from pathlib import Path

import numpy as np
import pytest

from scripts.audit_downloads import footprint_digest, audit


def test_identity_ignores_outside_and_negative_zero():
    footprint = np.array([[True, True, False]])
    assert footprint_digest(np.array([[0., 1., np.nan]]), footprint) == footprint_digest(
        np.array([[-0., 1., 0.]]), footprint)
    assert footprint_digest(np.array([[1., 1., 0.]]), footprint) != footprint_digest(
        np.array([[0., 1., 0.]]), footprint)


@pytest.mark.parametrize('value', [np.nan, np.inf, -np.inf, -.01, 1.01])
def test_invalid_inside_never_gets_identity(value):
    with pytest.raises(ValueError):
        footprint_digest(np.array([[value]]), np.ones((1, 1), bool))


def test_template_pin_is_required(tmp_path):
    template = tmp_path/'template.tif'
    template.write_bytes(b'not a template')
    with pytest.raises(ValueError, match='template hash'):
        audit(tmp_path, template, '0'*64)


def test_shipped_inventory_never_authorizes_slots():
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root/'docs/data/download_audit.json').read_text())
    assert report['okay_to_submit'] is False
    assert {r['file'] for r in report['files']} == {p.name for p in (root/'docs/downloads').glob('*.tif')}
    for row in report['files']:
        assert row['okay_to_submit'] is False
        assert row['estimated_leaderboard_score'] is None
        assert row['sha256'] == __import__('hashlib').sha256((root/'docs/downloads'/row['file']).read_bytes()).hexdigest()
        assert row['validator']['format_valid'] == row['format_valid']
        for name in row['identical_footprint_files']:
            other = next(r for r in report['files'] if r['file'] == name)
            assert row['footprint_sha256'] == other['footprint_sha256']
            assert row['file'] in other['identical_footprint_files']
