#!/usr/bin/env python3
"""Recheck shipped TIFF bytes with the shared writer's independent validator.

Never infers novelty from a filename, format validity, or a different file hash.
This is a local download inventory, NOT the cross-site surface/dot lane gate.
No network access and no competition submission are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import check_file, sha256_file  # noqa: E402


def footprint_digest(values, footprint):
    """Full SHA-256 of footprint float32 values, independent of compression/outside.

    Not a scored-content id: known catalogue pixels are deliberately included.
    Invalid values cannot receive an identity/uniqueness assertion.
    """
    values = np.asarray(values)
    footprint = np.asarray(footprint, bool)
    if values.shape != footprint.shape:
        raise ValueError('shape mismatch')
    v = np.asarray(values[footprint], dtype='<f4').copy()
    if not v.size or not np.isfinite(v).all() or (v < 0).any() or (v > 1).any():
        raise ValueError('empty, nonfinite or out-of-range footprint')
    v[v == 0] = 0  # normalize negative zero
    return hashlib.sha256(v.tobytes()).hexdigest()


def audit(downloads, template, expected_template_sha):
    if sha256_file(template) != expected_template_sha:
        raise ValueError('template hash does not match pinned manifest')
    with rasterio.open(template) as ds:
        footprint = np.isfinite(ds.read(1))
    rows = []
    for path in sorted(Path(downloads).glob('*.tif')):
        row = dict(file=path.name, sha256=sha256_file(path), footprint_sha256=None,
                   format_valid=False, strict_whole_array_valid=False,
                   download_eligibility='RESEARCH ONLY', okay_to_submit=False, estimated_leaderboard_score=None,
                   novelty='UNPROVEN: full registry surface and final-dot checks required')
        try:
            receipt = check_file(path, template)
            # Do not republish the misleading legacy upload/official field names in the public inventory.
            receipt['legacy_format_only_result'] = receipt.pop('ok_to_upload')
            receipt['outside_nan_legacy_alias'] = receipt.pop('official_nan_outside')
            checks = receipt['checks']
            if 'outside_footprint_is_nan_official' in checks:
                checks['outside_nan_legacy_alias'] = checks.pop('outside_footprint_is_nan_official')
            row.update(format_valid=receipt['format_valid'], strict_whole_array_valid=receipt['strict_whole_array_valid'],
                       validator=receipt)
            if receipt['format_valid']:
                with rasterio.open(path) as ds:
                    row['footprint_sha256'] = footprint_digest(ds.read(1), footprint)
        except (ValueError, rasterio.errors.RasterioError) as exc:
            row['error'] = str(exc)
        rows.append(row)
    # Add the independent H79 findings only when they match the exact audited bytes.
    # This is a recorded cross-check, not a fresh lane/catalogue audit by this tool.
    mask_path = ROOT / 'evidence/h79_independent_reaudit_2026-10-27.json'
    lane_path = ROOT / 'evidence/h79_literal_lane_reaudit_2026-10-27.json'
    if mask_path.exists() and lane_path.exists():
        mask = json.loads(mask_path.read_text())
        lane = json.loads(lane_path.read_text())
        for row in rows:
            if row['file'] == mask.get('file') and row['sha256'] == mask.get('sha256') == lane.get('sha256'):
                row['novelty'] = f"Recorded one-reference lane audit: {lane.get('verdict', 'UNVERIFIED')}"
                row['recorded_catalogue_positive_pixels'] = mask.get('catalogue_positive_pixels')
                row['recorded_reaudits'] = [str(mask_path.relative_to(ROOT)), str(lane_path.relative_to(ROOT))]
    # This archived lattice-gap TIFF was independently rechecked; no surface audit exists.
    mask_path = ROOT / 'evidence/latticegap_format_b0b734ae.json'
    lane_path = ROOT / 'evidence/latticegap_final_lane_b0b734ae.json'
    pair_path = ROOT / 'evidence/latticegap_r13_pair_audit_b0b734ae.json'
    if mask_path.exists() and lane_path.exists():
        mask = json.loads(mask_path.read_text())
        lane = json.loads(lane_path.read_text())
        for row in rows:
            if row['file'] == mask.get('file') and row['sha256'] == mask.get('sha256') == lane.get('sha256'):
                row['novelty'] = (f"UNVERIFIED: final audit stopped after {lane.get('registry_checked', 0)} references; "
                                  "an invalid registry grid and the missing pre-placement surface block clearance")
                row['recorded_catalogue_positive_pixels'] = mask.get('catalogue_positive_pixels')
                row['recorded_reaudits'] = [str(mask_path.relative_to(ROOT)), str(lane_path.relative_to(ROOT))]
                if pair_path.exists():
                    row['recorded_reaudits'].append(str(pair_path.relative_to(ROOT)))
    for row in rows:
        digest = row['footprint_sha256']
        row['identical_footprint_files'] = [r['file'] for r in rows
            if digest is not None and r['footprint_sha256'] == digest and r['file'] != row['file']]
    return dict(schema_version=1, generated_utc=datetime.now(timezone.utc).isoformat(),
                evidence_class='COMPUTED local format and footprint identity only',
                template_sha256=expected_template_sha, files=rows,
                okay_to_submit=False,
                limitations=['No new geological experiment or TIFF generated by this audit.',
                             'format_valid is a legacy footprint-format check, not upload readiness; strict_whole_array_valid is separate.',
                             'Outside-footprint NaNs fail the strict whole-array check; portal padding behavior is unverified.',
                             'All downloadable files are research-only; no download is approved for submission.',
                             'Identical footprint means identical local predictions, not cross-site novelty.',
                             'Catalogue masking is not tested by this format inventory; recorded re-audits are linked separately.',
                             'No candidate has acquired holdout, lane or selector approval from this audit.',
                             'No calibrated leaderboard score estimator or organizer receipt is available.',
                             'Template is a pinned owner mirror, not organizer-authenticated.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'docs/data/download_audit.json')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'registry/data_manifest.json').read_text())
    template = next(r for r in manifest['files'] if r['id'] == 'sample_submission')
    result = audit(ROOT/'docs/downloads', data_dir()/template['dest'], template['sha256'])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(files=len(result['files']), format_valid=sum(r['format_valid'] for r in result['files']),
                          okay_to_submit=False, receipt=str(args.out))))
    return 0 if result['files'] and all(r['format_valid'] for r in result['files']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
