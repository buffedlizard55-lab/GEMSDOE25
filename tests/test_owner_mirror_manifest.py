"""Regression guard for the pinned owner-mirror group used by the GEMSDOE32 B2 lineage check.

Runs without any restored data: it only reads registry/data_manifest.json and scripts/restore_data.py.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
OWNER = [e for e in MANIFEST["files"] if e.get("group") == "owner_mirror"]


def test_owner_mirror_entries_pinned_to_commits_and_hashes() -> None:
    ids = {e["id"] for e in OWNER}
    assert ids == {"owner_gemsdoe32_h33_b2_zeros", "owner_gemsdoe28_h27_4_nan"}
    for e in OWNER:
        assert re.fullmatch(r"[0-9a-f]{40}", e["ref"]), e["id"]
        assert re.fullmatch(r"[0-9a-f]{64}", e["sha256"]), e["id"]
        assert e["dest"].startswith("owner_mirrors/"), e["id"]
        assert e["repo"].startswith("buffedlizard55-lab/"), e["id"]
        assert e["path"].startswith("docs/downloads/") and e["path"].endswith(".tif"), e["id"]
        assert "NOT organizer-authenticated" in e["provenance"], e["id"]


def test_restore_script_accepts_owner_mirror_group() -> None:
    src = (ROOT / "scripts" / "restore_data.py").read_text()
    assert '"owner_mirror"' in src
