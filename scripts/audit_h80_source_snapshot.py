#!/usr/bin/env python3
"""Record pinned GitHub-only nine-site metadata and downloaded extra-raster provenance.

No organizer access or score authentication. Inputs stay gitignored. This
snapshot is reproducible by reading the pinned Git blobs; never HEAD receipts.
"""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNERS = {'GEMSDOEkarage': 'karagemop466-tech', 'ApartGEMSDOE': 'apartanish22-droid',
          'GEMSDOESASS': 'sassnarep3-star', 'WBGGEMSDOE': 'wingbangboozle1-lang',
          'KANLERGEMSDOE': 'kanlerxz87-cyber'}


def api(endpoint):
    return json.loads(subprocess.run(['gh', 'api', endpoint], capture_output=True, text=True, check=True).stdout)


def main():
    local = sorted((ROOT/'data/registry_extra_20261028').glob('*.tif'))
    extras = {}
    for p in local:
        repo_name, _ = p.name.split('__', 1)
        owner = next((v for k, v in OWNERS.items() if repo_name.startswith(k)), 'buffedlizard55-lab')
        extras.setdefault(f'{owner}/{repo_name}', []).append(p)
    repos = sorted(set(extras) | {f'buffedlizard55-lab/GEMSDOE{n}' for n in (24,25,27,28,30,31,32,33,36)})
    rows = []
    for repo in repos:
        commit = api(f'repos/{repo}/commits/HEAD')
        ref = commit['sha']
        tree = api(f'repos/{repo}/git/trees/{ref}?recursive=1')
        if tree.get('truncated'):
            raise ValueError(f'truncated source tree: {repo}')
        sources = []
        for p in extras.get(repo, []):
            raw = p.read_bytes()
            blob = hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
            hits = [r for r in tree['tree'] if r.get('sha') == blob and r['type'] == 'blob']
            if not hits:
                raise ValueError(f'local bytes not present at pinned revision: {p}')
            sources.append(dict(local=p.name, sha256=hashlib.sha256(raw).hexdigest(), git_blob_sha=blob,
                                paths=[r['path'] for r in hits],
                                url=f"https://github.com/{repo}/blob/{ref}/{hits[0]['path']}"))
        rows.append(dict(repo=repo, ref=ref, commit_date=commit['commit']['committer']['date'],
                         url=f'https://github.com/{repo}/tree/{ref}',
                         raster_count=sum(r['path'].endswith('.tif') for r in tree['tree']), sources=sources))
    result = dict(utc=datetime.now(timezone.utc).isoformat(), repos=rows,
                  scope='GitHub repository snapshots and byte integrity only. Not current leaderboard evidence or exhaustive raster novelty.',
                  organizer_confirmed=False)
    (ROOT/'evidence/h80_sibling_source_snapshot.json').write_text(json.dumps(result, indent=2)+'\n')
    print(f'{len(rows)} repositories; {sum(len(r["sources"]) for r in rows)} extra raster pins')


if __name__ == '__main__':
    main()
