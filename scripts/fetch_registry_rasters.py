#!/usr/bin/env python3
"""Fetch sibling-site registry rasters referenced by registry/ but not yet on disk.

Sources:
* registry/top_scorer_sources.json  (repo + path, ref = main)
* registry/artifact_mirrors.json    (repo + ref + path)

Writes into data/registry_top/ and prints a sha256 manifest so the lane audit
inventory can be completed. DrivenData is never contacted; only public GitHub
mirrors via gh api / raw.githubusercontent.com.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

OUT = data_dir() / "registry_top"
OUT.mkdir(parents=True, exist_ok=True)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gh_raw(repo: str, ref: str, path: str) -> bytes | None:
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "-H",
         "Accept: application/vnd.github.raw"],
        capture_output=True,
    )
    if r.returncode != 0:
        return None
    return r.stdout


def main() -> int:
    top = json.loads((ROOT / "registry/top_scorer_sources.json").read_text())
    mirrors = json.loads((ROOT / "registry/artifact_mirrors.json").read_text())

    jobs = []
    for r in top["rasters"]:
        repo = r.get("repo")
        if repo and isinstance(repo, str) and "/" in repo:
            jobs.append((repo, "main", r["path"], r.get("site", "")))
    for r in mirrors["mirrors"]:
        jobs.append((r["repo"], r.get("ref", "main"), r["path"], r.get("owner_label", "")))

    seen = set()
    fetched = skipped = failed = 0
    manifest = []
    for repo, ref, path, label in jobs:
        key = (repo, ref, path)
        if key in seen:
            continue
        seen.add(key)
        dest = OUT / Path(path).name
        if dest.exists():
            skipped += 1
            manifest.append(dict(id=label, repo=repo, ref=ref, path=path,
                                 local=str(dest), sha256=sha256_file(dest), status="present"))
            continue
        data = gh_raw(repo, ref, path)
        if data is None or len(data) == 0:
            failed += 1
            print(f"FAILED  {repo}@{ref} {path} ({label})", file=sys.stderr)
            manifest.append(dict(id=label, repo=repo, ref=ref, path=path,
                                 local=None, sha256=None, status="failed"))
            continue
        dest.write_bytes(data)
        fetched += 1
        digest = sha256_file(dest)
        manifest.append(dict(id=label, repo=repo, ref=ref, path=path,
                             local=str(dest), sha256=digest, status="fetched"))
        print(f"FETCHED {digest[:12]}  {repo}@{ref} {path} ({len(data):,} bytes)")

    (OUT / "fetch_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"\nfetched={fetched} skipped={skipped} failed={failed} total={len(manifest)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
