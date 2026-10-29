"""Regression guards for the 2026-10-29 verified review (session branch arena/87a0b9a8-gemsdoe25).

These tests do not contact the network. Data-dependent checks skip when the restored inputs are absent.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def J(p: str):
    return json.loads((ROOT / p).read_text())


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


NEW_IDS = {
    "IR-29-LABELS-EQUALS-CATALOGUE",
    "IR-29-B2-LINEAGE-REPRODUCED",
    "IR-29-GEMSDOE25-FILE-LABEL",
    "IR-29-FRONTPAGE-DOWNLOAD-OF-INVALID-DIAGNOSTIC",
    "IR-29-REVIEW-STALE-FACTS",
    "IR-29-OWNER-MIRROR-RESTORE-GAP",
}


def test_session_irregularities_are_registered_with_expected_status() -> None:
    issues = {i["id"]: i for i in J("registry/irregularities.json")["issues"]}
    assert NEW_IDS <= set(issues)
    # The labels/catalogue identity is a human-decision item: it must stay open until the organizer page is read.
    assert issues["IR-29-LABELS-EQUALS-CATALOGUE"]["status"] == "open"
    assert issues["IR-29-LABELS-EQUALS-CATALOGUE"]["severity"] == "critical"


def test_nine_site_owner_files_are_pinned_in_manifest() -> None:
    """All 8 owner-prefixed nine-site rasters are restored by scripts/restore_data.py from pinned commits."""
    man = J("registry/data_manifest.json")["files"]
    groups = [f for f in man if f.get("group") in ("owner_mirror", "owner_mirror_nine_site")]
    dests = {f["dest"] for f in groups}
    rows = J("evidence/nine_site_top_files_2026-10-28.json")["rows"]
    owner_rows = [r for r in rows if "__" in r["file"]]
    assert len(owner_rows) == 8
    assert {f"owner_mirrors/{r['file']}" for r in owner_rows} <= dests
    by_dest = {f["dest"]: f for f in groups}
    for r in owner_rows:
        entry = by_dest[f"owner_mirrors/{r['file']}"]
        assert entry["sha256"] == r["sha256"], r["file"]
        assert re.fullmatch(r"[0-9a-f]{40}", entry["ref"]), r["file"]
        assert entry["repo"].startswith("buffedlizard55-lab/GEMSDOE"), r["file"]
        assert "NOT organizer-authenticated" in entry["provenance"], r["file"]
    restore_src = (ROOT / "scripts" / "restore_data.py").read_text()
    assert '"owner_mirror_nine_site"' in restore_src


def test_nine_site_evidence_lineage_is_internally_consistent() -> None:
    ev = J("evidence/nine_site_top_files_2026-10-28.json")
    lin = ev["lineage_steps"]
    assert lin["d2_8_dots"] - lin["d2_8_to_h27_4_removed"] == lin["h27_4_dots"] == 40199
    assert lin["h27_4_dots"] - lin["h27_4_to_b2_removed"] == lin["b2_dots"] == 37654
    assert ev["b2_lineage"]["b2_subset_of_h27_4"] is True
    assert ev["b2_lineage"]["dots_in_h27_4_not_in_b2"] == lin["h27_4_to_b2_removed"] == 2545
    assert lin["b2_dots_within_2px_catalogue"] == 0
    assert ev["estimated_competition_score"].startswith("UNKNOWN")


def test_label_identity_receipt_matches_restored_bytes() -> None:
    receipt_path = ROOT / "evidence" / "label_identity_audit_2026-10-29.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["issue"] == "IR-29-LABELS-EQUALS-CATALOGUE"
    assert receipt["checks"]["labels_bytes_identical_to_existing_faults"] is True
    assert receipt["checks"]["sample_ones_equal_labels_ones"] is True
    assert receipt["checks"]["labels_positive_count"] == 60988
    labels = ROOT / "data" / "labels.tif"
    catalogue = ROOT / "data" / "existing_faults.tif"
    if not (labels.exists() and catalogue.exists()):
        pytest.skip("core inputs not restored (scripts/restore_data.py --group core)")
    assert _sha256(labels) == receipt["inputs"]["labels"]["sha256"]
    assert _sha256(catalogue) == receipt["inputs"]["existing_faults"]["sha256"]


def test_front_pages_and_readme_surface_the_label_alert() -> None:
    for page in ("index.html", "docs/index.html", "README.md"):
        text = (ROOT / page).read_text(encoding="utf8")
        assert "IR-29-LABELS-EQUALS-CATALOGUE" in text, page
        assert "NOTHING ON THIS SITE IS CLEARED" in text or "Nothing in this repository is cleared" in text, page


def test_no_drivendata_host_in_new_scripts() -> None:
    for name in ("scripts/audit_label_identity.py",):
        assert "drivendata.org" not in (ROOT / name).read_text(encoding="utf8").replace(
            "https://www.drivendata.org/competitions/306/competition-doe-gems/data/", ""
        ), name
