#!/usr/bin/env python3
"""Reproducible hash-pinned audit; no model, candidate placement or upload."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from gems25.lane_feasibility import capacity_bound, halo_capacity  # noqa: E402
from gems25.submission import sha256_file  # noqa: E402
from restore_data import restore  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore', action='store_true', help='Use existing hash-pinned mirror restorer')
    parser.add_argument('--output', type=Path, default=ROOT/'evidence/lane_feasibility_2026-10-26.json')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'registry/data_manifest.json').read_text())['files']
    suffix = '13gems_20261001_r13-lattice-s5_v2_nan-outside.tif'
    entries = [next(e for e in manifest if e['id'] == name) for name in ('sample_submission', 'labels')]
    entries.append(next(e for e in manifest if e['dest'] == 'scored/'+suffix))
    arrays, profiles, pins = [], [], []
    for entry in entries:
        if args.restore:
            restore(entry, ROOT/'data')
        path = ROOT/'data'/entry['dest']
        digest = sha256_file(path)
        if digest != entry['sha256']:
            raise ValueError(f'Hash mismatch: {path}')
        with rasterio.open(path) as ds:
            if ds.count != 1:
                raise ValueError('Single band required')
            arrays.append(ds.read(1))
            profiles.append((ds.shape, ds.crs, ds.transform))
        pins.append(dict(path=entry['dest'], sha256=digest,
                         source=f"https://github.com/{entry['repo']}/blob/{entry['ref']}/{entry['path']}"))
    if any(p != profiles[0] for p in profiles) or profiles[0][1] is None:
        raise ValueError('CRS/shape/transform mismatch or missing CRS')
    geometry = halo_capacity(np.isfinite(arrays[0]), arrays[1] == 1, arrays[2])
    cases = [capacity_bound(geometry['eligible_pixels'], geometry['uncovered_pixels'], k)
             for k in (37654, 38854, 40199, 44090, 70524)]
    output = dict(evidence_class='COMPUTED GEOMETRY; not HOLDOUT-DTI or an organizer score',
                  preregistration_commit='06612d8', inputs=pins, grid_match=True, geometry=geometry,
                  cases=cases, proof='At most U distinct candidate pixels can avoid the halo; at least max(0,K-U) must overlap.',
                  scope='Necessary condition against one registry raster. Not a full registry uniqueness check.',
                  decision='STOP: all preregistered target densities impossible' if all(c['impossible'] for c in cases)
                  else 'Some densities not ruled out; no candidate approved',
                  experiments=0, new_tiff_generated=False, okay_to_submit=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False)+'\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
