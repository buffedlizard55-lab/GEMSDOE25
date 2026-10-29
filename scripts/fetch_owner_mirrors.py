#!/usr/bin/env python3
"""Fetch the owner-mirror rasters used by the nine-site audit into ``data/owner_mirrors``.

Source of truth: ``evidence/nine_site_top_files_2026-10-28.json``. Every row whose file name carries an owner
prefix (``GEMSDOEnn__<name>.tif``) is looked up in the PUBLIC repository ``buffedlizard55-lab/GEMSDOEnn`` by
listing its git tree through the GitHub API (api.github.com) and matching the basename case-insensitively.
Each downloaded file must match the SHA-256 pinned in that evidence row; on any mismatch the file is
discarded and the script exits non-zero (fail closed).

Scope: only owner-mirror rasters. DrivenData is never contacted. A matching SHA-256 proves the mirror is
unchanged; it does NOT authenticate the bytes as organizer files, and the scores are OWNER-REPORTED.

    python scripts/fetch_owner_mirrors.py
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "nine_site_top_files_2026-10-28.json"
DEST_DIR = ROOT / "data" / "owner_mirrors"
OWNER_ORG = "buffedlizard55-lab"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def owner_targets() -> list[tuple[str, str, str]]:
    """(local file name, owner repo, pinned sha256) for every owner-prefixed row in the evidence."""
    out: dict[str, tuple[str, str, str]] = {}
    for row in json.loads(EVIDENCE.read_text())["rows"]:
        name = row["file"]
        if "__" not in name:
            continue  # local scored files are restored by scripts/restore_data.py --group scored
        prefix = name.split("__", 1)[0]
        out[name] = (name, f"{OWNER_ORG}/{prefix}", row["sha256"])
    return list(out.values())


def find_in_repo(repo: str, basename: str) -> str | None:
    """Return the repo path of the .tif whose basename matches (case-insensitive), or None."""
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/git/trees/HEAD?recursive=1", "--jq", '.tree[] | select(.type=="blob") | .path'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if r.returncode != 0:
        return None
    wanted = basename.split("__", 1)[1].lower()
    hits = [p for p in r.stdout.splitlines() if p.lower().endswith(".tif") and Path(p).name.lower() == wanted]
    return hits[0] if hits else None


def main() -> int:
    if shutil.which("gh") is None:
        print("gh CLI not found; cannot fetch owner mirrors", file=sys.stderr)
        return 2
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    failures = 0
    for name, repo, expected in owner_targets():
        dest = DEST_DIR / name
        if dest.exists() and sha256(dest) == expected:
            print(f"ok (present, sha matches) {name}")
            continue
        path = find_in_repo(repo, name)
        if path is None:
            print(f"NOT FOUND in {repo}: {name}", file=sys.stderr)
            failures += 1
            continue
        tmp = dest.with_suffix(dest.suffix + ".partial")
        with tmp.open("wb") as out:
            r = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{path}", "-H", "Accept: application/vnd.github.raw"],
                stdout=out,
                stderr=subprocess.PIPE,
            )
        if r.returncode != 0 or tmp.stat().st_size == 0:
            tmp.unlink(missing_ok=True)
            print(f"FAILED to fetch {repo}:{path}: {r.stderr.decode(errors='replace')[:200]}", file=sys.stderr)
            failures += 1
            continue
        got = sha256(tmp)
        if got != expected:
            tmp.unlink(missing_ok=True)
            print(f"SHA MISMATCH {name}: got {got}, pinned {expected}; discarded", file=sys.stderr)
            failures += 1
            continue
        tmp.replace(dest)
        print(f"restored {name} sha256={got[:12]} from {repo}:{path} (pin verified)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
