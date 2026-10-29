"""Regression checks for the 2026-10-29 owner-brief session (arena/30397b95-gemsdoe25).

No network, no DrivenData. Data-dependent checks skip when the owner-mirror inputs are not restored.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _readme() -> str:
    return (ROOT / "README.md").read_text()


def test_readme_has_start_here_brief_with_no_go_status():
    text = _readme()
    assert text.index("## START HERE — owner brief 2026-10-29") < text.index("## Current result — 29 October 2026")
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in text
    assert "Estimated competition score: NOT ESTIMATED" in text


def test_readme_executive_table_covers_all_nine_sites():
    text = _readme()
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                 "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert f"| {site} |" in text or f"| **{site}** |" in text, site


def test_nine_site_scores_match_owner_prompt():
    text = _readme()
    expected = {"GEMSDOE24": "0.2477", "GEMSDOE25": "0.2600", "GEMSDOE27": "0.2449", "GEMSDOE28": "0.2710",
                "GEMSDOE30": "0.2600", "GEMSDOE31": "0.2708", "GEMSDOE32": "0.2778", "GEMSDOE33": "0.2632",
                "GEMSDOE36": "0.2750"}
    rows = [line for line in text.splitlines() if line.startswith("| ")]
    for site, score in expected.items():
        row = next(r for r in rows if f"| {site} |" in r or f"| **{site}** |" in r)
        assert score in row, (site, row)


def test_knowledge_brief_states_decision_and_sources():
    text = (ROOT / "knowledge" / "51_owner_brief_session_review_2026-10-29_30397b95.md").read_text()
    assert "OK TO DOWNLOAD AND SUBMIT — NO" in text
    assert "https://www.drivendata.org/competitions/306/competition-doe-gems/" in text
    assert "evidence/b2_lineage_2026-10-29.json" in text


def test_lineage_receipt_arithmetic_and_pins():
    rec = json.loads((ROOT / "evidence" / "b2_lineage_2026-10-29.json").read_text())
    assert rec["dots"]["d28"] - rec["removed"]["from_d2-8"] == rec["dots"]["b2"] == 37654
    assert rec["dots"]["h27"] - rec["removed"]["from_h27_4"] == rec["dots"]["b2"]
    assert rec["removed"] == rec["removed_within_200m"]
    assert rec["b2_dots_within_200m"] == 0 and rec["b2_dots_on_catalogue"] == 0
    assert rec["sha256_matches_pins"] == {"b2": True, "h27": True}
    assert rec["consistent_with_pruning_rule"] is True


def test_lane_receipt_fails_literal_cap():
    rec = json.loads((ROOT / "evidence" / "b2_lane_vs_r13_2026-10-29.json").read_text())
    assert rec["b2_within_3px_of_r13"] == 37622 and rec["b2_dots"] == 37654
    assert rec["passes_literal_cap"] is False


def test_run_card_is_negative_and_not_submittable():
    card = json.loads((ROOT / "registry" / "run_card_session_30397b95_2026-10-29.json").read_text())
    assert card["ok_to_download_and_submit"] is False
    assert card["verdict"] == "negative"
    assert card["estimated_competition_score"] == "NOT ESTIMATED"


def test_build_readme_refuses_to_overwrite():
    before = _readme()
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_readme.py")],
                          capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 2
    assert "Refusing to rebuild" in proc.stderr
    assert _readme() == before


def test_b2_lineage_recomputes_from_mirror_bytes_when_present():
    mirror = ROOT / "data" / "mirror"
    files = [mirror / "gemsdoe32_b2_0.2778_zeros.tif", mirror / "gemsdoe32_d2-8_zeros.tif",
             mirror / "gemsdoe28_h27-4_r1-solo_nan.tif"]
    if not all(f.exists() for f in files) or not (ROOT / "data" / "labels.tif").exists():
        pytest.skip("owner-mirror B2 files not restored (see scripts/audit_b2_lineage.py docstring)")
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_b2_lineage.py")],
                          capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    rec = json.loads((ROOT / "evidence" / "b2_lineage_2026-10-29.json").read_text())
    assert rec["sha256"]["b2"] == hashlib.sha256(files[0].read_bytes()).hexdigest()
