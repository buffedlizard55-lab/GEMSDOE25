"""Regression checks for the 2026-10-29 owner-brief session (arena/30397b95-gemsdoe25).

No network, no DrivenData. Data-dependent checks skip when the owner-mirror inputs are not restored.
"""

import json
import subprocess
import sys
from pathlib import Path


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
    assert "evidence/b2_lineage_recheck_2026-10-29.json" in text


def test_lineage_receipt_arithmetic_and_pins():
    rec = json.loads((ROOT / "evidence" / "b2_lineage_recheck_2026-10-29.json").read_text())
    assert rec["b2_dots"] == 37654 and rec["parent_dots"] == 40199
    assert rec["parent_dots"] - rec["dots_removed_from_parent"] == rec["b2_dots"]
    assert rec["removed_dots_within_2px_catalogue"] == rec["dots_removed_from_parent"] == 2545
    assert rec["b2_dots_within_2px_catalogue"] == 0 and rec["b2_dots_on_catalogue_pixels"] == 0
    assert rec["b2_subset_of_parent"] is True and rec["dots_added_by_b2"] == 0
    d28 = rec["d2_8_parent"]
    assert d28["dots"] == 44090 and d28["dots"] - d28["dots_removed_from_d2_8"] >= rec["b2_dots"]
    assert d28["dots_removed_from_d2_8"] == 6436 == d28["removed_within_2px_catalogue"]
    assert d28["b2_subset_of_d2_8"] is True and d28["h27_4_subset_of_d2_8"] is True
    assert d28["sha256"] == "3e78737f0da8dd2ca66cc6caac0ce8eeefcd6715707f8d1bd3091845cd9bcc30"


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
