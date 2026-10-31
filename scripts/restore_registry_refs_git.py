#!/usr/bin/env python3
"""Restore the registry references declared in registry/top_scorer_sources.json through git (github.com), not the API.

Each file is written to data/registry_top/<basename> ONLY if its SHA-256 equals the declared pin. Mismatches are
reported and not written. Uses the same partial-clone helper as scripts/restore_data.py.

    python scripts/restore_registry_refs_git.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.paths import data_dir  # noqa: E402
from restore_data import _git_fetch_blob  # noqa: E402

OUT = data_dir() / "registry_top"


def main() -> int:
    top = json.loads((ROOT / "registry/top_scorer_sources.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    ok = bad = skipped = 0
    for r in top["rasters"]:
        repo, path, pin = r.get("repo"), r.get("path"), r.get("sha256")
        if not repo or "/" not in str(repo) or repo == "local-restore (registry/data_manifest.json scored group)":
            skipped += 1
            continue
        dest = OUT / Path(path).name
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == pin:
            ok += 1
            continue
        tmp = dest.with_suffix(".partial")
        with tmp.open("wb") as fh:
            fetched = _git_fetch_blob(repo, "main", path, fh)
        if not fetched or tmp.stat().st_size == 0:
            tmp.unlink(missing_ok=True)
            bad += 1
            print(f"NOT FOUND {repo}:{path}")
            continue
        digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
        if digest != pin:
            tmp.unlink(missing_ok=True)
            bad += 1
            print(f"PIN MISMATCH {repo}:{path} got {digest[:12]} want {pin[:12]}")
            continue
        tmp.rename(dest)
        ok += 1
        print(f"OK {digest[:12]} {repo}:{path}")
    print(f"ok={ok} bad={bad} skipped={skipped}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
