#!/usr/bin/env python3
"""Restore the top-scorer registry rasters listed in ``registry/top_scorer_sources.json`` into ``data/registry_top``.

Each file comes from the owner's public GitHub repository (``gh api`` raw contents) and is verified against its SHA-256
pin; a mismatch aborts. Rows whose ``repo`` starts with ``local-restore`` are copied from ``data/scored`` (restored by
``scripts/restore_data.py --group scored``). Pins prove mirror consistency, NOT organizer authentication; scores are
owner-reported claims.

    python scripts/fetch_top_scorers.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    reg = json.loads((ROOT / "registry" / "top_scorer_sources.json").read_text())
    dest_dir = data_dir() / "registry_top"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for r in reg["rasters"]:
        dest = dest_dir / r["local"]
        if dest.exists() and sha(dest) == r["sha256"]:
            print("present ", r["local"])
            continue
        if r["repo"].startswith("local-restore"):
            src = data_dir() / r["path"]
            shutil.copyfile(src, dest)
        else:
            with dest.open("wb") as out:
                subprocess.run(["gh", "api", f"repos/{r['repo']}/contents/{r['path']}", "-H",
                                "Accept: application/vnd.github.raw"], stdout=out, check=True)
        got = sha(dest)
        if got != r["sha256"]:
            dest.unlink()
            raise SystemExit(f"HASH MISMATCH {r['local']}: {got} != {r['sha256']}")
        print("restored", r["local"], got[:12])


if __name__ == "__main__":
    main()
