#!/usr/bin/env python3
"""Restore the top-scorer registry rasters listed in ``registry/top_scorer_sources.json`` into ``data/registry_top``.

Each file is verified against its SHA-256 pin. Pins prove mirror consistency, NOT organizer
authentication; scores are owner-reported claims.

Primary fetch is a shallow git blob read of the public repo (avoids GitHub Contents API JSON
error bodies being written as 538-byte fake GeoTIFFs). ``gh api`` is a last-resort fallback
and is never retried in a loop after a 403/rate-limit.

    python scripts/fetch_top_scorers.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

MIN_RASTER_BYTES = 10_000


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_checked(dest: Path, blob: bytes, expected: str, label: str) -> None:
    if len(blob) < MIN_RASTER_BYTES:
        raise SystemExit(
            f"REFUSED undersized payload for {label}: {len(blob)} bytes "
            f"(likely an API error body, not a GeoTIFF)"
        )
    got = hashlib.sha256(blob).hexdigest()
    if got != expected:
        raise SystemExit(f"HASH MISMATCH {label}: {got} != {expected}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    tmp.write_bytes(blob)
    tmp.replace(dest)


def fetch_via_git(repo: str, path: str) -> bytes:
    tmp = Path(tempfile.mkdtemp(prefix="gems25-git-"))
    try:
        subprocess.run(["git", "init", "--bare", "-q"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(
            [
                "git",
                "fetch",
                "--depth=1",
                "--filter=blob:none",
                f"https://github.com/{repo}.git",
                "HEAD",
            ],
            cwd=tmp,
            check=True,
            capture_output=True,
        )
        blob = subprocess.run(
            ["git", "show", f"FETCH_HEAD:{path}"],
            cwd=tmp,
            check=True,
            capture_output=True,
        )
        return blob.stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fetch_via_gh_api(repo: str, path: str) -> bytes:
    proc = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}", "-H", "Accept: application/vnd.github.raw"],
        check=True,
        capture_output=True,
    )
    return proc.stdout


def main() -> None:
    reg = json.loads((ROOT / "registry" / "top_scorer_sources.json").read_text())
    dest_dir = data_dir() / "registry_top"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for r in reg["rasters"]:
        dest = dest_dir / r["local"]
        if dest.exists() and dest.stat().st_size >= MIN_RASTER_BYTES and sha(dest) == r["sha256"]:
            print("present ", r["local"])
            continue
        if dest.exists() and dest.stat().st_size < MIN_RASTER_BYTES:
            dest.unlink()
        if r["repo"].startswith("local-restore"):
            src = data_dir() / r["path"]
            blob = src.read_bytes()
            _write_checked(dest, blob, r["sha256"], r["local"])
            print("restored", r["local"], sha(dest)[:12], "(local)")
            continue
        try:
            blob = fetch_via_git(r["repo"], r["path"])
            _write_checked(dest, blob, r["sha256"], r["local"])
            print("restored", r["local"], sha(dest)[:12], "(git)")
            continue
        except (subprocess.CalledProcessError, SystemExit) as err:
            print(f"git-blob failed for {r['local']}: {err}", file=sys.stderr)
        try:
            blob = fetch_via_gh_api(r["repo"], r["path"])
            _write_checked(dest, blob, r["sha256"], r["local"])
            print("restored", r["local"], sha(dest)[:12], "(gh-api)")
        except (subprocess.CalledProcessError, SystemExit) as err:
            raise SystemExit(
                f"could not restore {r['local']} from {r['repo']}:{r['path']}: {err}"
            ) from err


if __name__ == "__main__":
    main()
