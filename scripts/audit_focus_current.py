#!/usr/bin/env python3
"""Reaudit pinned focus-site artifacts and source availability, never DrivenData.

Owner score claims are used only to identify historical exemplars. No slot selection.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems25.submission import check_file, sha256_file  # noqa: E402

FOCUS = (24, 25, 27, 28, 30, 31, 32, 33, 36)
MECHANISMS = {
    24: 'D1.5 spacing applied to the H19-5 parent. Historical baseline, not a fresh submission.',
    25: 'D2.8 thinning of the same parent; identical prediction mask to GEMSDOE30.',
    27: 'Topographic gap-closure variant of D1.5; its reported result is lower than its parent.',
    28: 'Rung30/blind variant is the highest of the four supplied historical results; small reported margin over R1.',
    30: 'Same prediction mask as GEMSDOE25 D2.8; filename does not establish a new method.',
    31: 'Same prediction mask as GEMSDOE28 R1; catalogue collar pruning, not a distinct discovery.',
    32: 'B2 equals D2.8 with predictions within 200 m of catalogue removed; highest supplied focus-site result.',
    33: 'Analog tip/stepover variant. Its reported result does not outperform B2.',
    36: 'B2 plus additional predictions; a different mask, but reported performance is below B2.',
}


def main():
    rows = json.loads((ROOT/'registry/top_scorer_sources.json').read_text())['rasters']
    template = ROOT/'data/sample_submission.tif'
    with rasterio.open(template) as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ROOT/'data/labels.tif') as ds:
        known = ds.read(1) == 1
    distance = distance_transform_edt(~known)

    def mask(row):
        path = ROOT/'data/registry_top'/row['local']
        if sha256_file(path) != row['sha256']:
            raise ValueError(f'Unpinned bytes: {path}')
        with rasterio.open(path) as ds:
            return (ds.read(1)>0) & foot

    selected, masks, checks = [], {}, {}
    for n in FOCUS:
        candidates = [r for r in rows if f'/GEMSDOE{n}/' in r['site']]
        row = max(candidates, key=lambda r: r['owner_reported_score'])
        masks[n] = mask(row)
        checks[str(n)] = check_file(ROOT/'data/registry_top'/row['local'], template)
        result = dict(site=f'GEMSDOE{n}', site_url=row['site'], submission=row['submission_name_in_brief'],
                      owner_reported_score=row['owner_reported_score'], score_class='OWNER-REPORTED; no organizer receipt',
                      sha256=row['sha256'], positive_pixels=int(masks[n].sum()),
                      mechanism=MECHANISMS[n], okay_to_submit_as_new=False,
                      local_format_pass=checks[str(n)]['ok_to_upload'],
                      highest_scope='highest supplied, pinned historical result; not a live leaderboard query')
        # Pin source revision separately from the older artifact identity. This is source freshness, not score authentication.
        repo=f'buffedlizard55-lab/GEMSDOE{n}'
        proc = subprocess.run(['gh', 'api', f'repos/{repo}/commits/HEAD', '--jq', '.sha'], capture_output=True, text=True)
        result['source_head'] = proc.stdout.strip() if proc.returncode == 0 else None
        result['source_status'] = 'GitHub revision retrieved' if proc.returncode == 0 else 'unavailable'
        result['source_url'] = f'https://github.com/{repo}/tree/{result["source_head"]}' if result['source_head'] else f'https://github.com/{repo}'
        selected.append(result)
    d28 = masks[25]
    r1_row = next(r for r in rows if r['local'].startswith('g28_h27-4'))
    r1 = mask(r1_row)
    identities = dict(
        gems25_equals_gems30_mask=bool(np.array_equal(d28, masks[30])),
        gems28_r1_equals_gems31_mask=bool(np.array_equal(r1, masks[31])),
        gems28_r1_equals_d28_distance_gt_1=bool(np.array_equal(r1, d28 & (distance>1))),
        gems32_b2_equals_d28_distance_gt_2=bool(np.array_equal(masks[32], d28 & (distance>2))),
        removed_d28_to_b2=int((d28 & ~masks[32]).sum()),
        gems36_added_to_b2=int((masks[36] & ~masks[32]).sum()),
        gems36_removed_from_b2=int((masks[32] & ~masks[36]).sum()),
    )
    lattice_path=ROOT/'data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif'
    with rasterio.open(lattice_path) as ds:
        lattice=(ds.read(1)>0)&foot
    eligible=foot & ~known
    dist=distance_transform_edt(~lattice)
    coverage=dict(sha256=sha256_file(lattice_path), eligible_pixels=int(eligible.sum()),
                  covered_pixels=int((eligible & (dist<=3)).sum()), uncovered_pixels=int((eligible & (dist>3)).sum()),
                  coverage_fraction=float((dist[eligible]<=3).mean()),
                  note='Literal registry dots including any catalogue pixels; not proof that all candidates must fail.')
    out=dict(date_utc=datetime.now(timezone.utc).isoformat(), evidence_class='COMPUTED geometry; OWNER-REPORTED scores',
             sites=selected, identities=identities, lattice_coverage=coverage,
             source_limitations='GitHub owner mirrors are not organizer receipts. Other official hosts are outside this sandbox network allowlist.')
    (ROOT/'evidence/focus_audit_2026-10-26.json').write_text(json.dumps(out,indent=2)+'\n')
    (ROOT/'evidence/focus_format_2026-10-26.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(dict(identities=identities,lattice_coverage=coverage), indent=2))


if __name__=='__main__':
    main()
