"""Guards for the 30 Oct 2026 owner brief: the NO decision stays visible and the lane-duplicate TIF is not packaged."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_decision_is_visible_in_readme_index_and_summary():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    summary = (ROOT / "docs" / "owner-brief-2026-10-30.html").read_text(encoding="utf-8")
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "owner brief 2026-10-30" in readme
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in readme
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in summary
    assert "owner-brief-2026-10-30.html" in index


def test_lane_duplicate_candidate_is_not_packaged():
    downloads = ROOT / "docs" / "downloads"
    leftovers = [p.name for p in downloads.glob("*nosubmit-hsp1*")]
    assert leftovers == [], f"lane-duplicate candidate must not be packaged: {leftovers}"


def test_irregularities_and_run_cards_are_recorded():
    issues = json.loads((ROOT / "registry" / "irregularities.json").read_text(encoding="utf-8"))["issues"]
    ids = {i["id"] for i in issues}
    for needed in ("IR-30-SOFT-PRIOR-NOT-NEW", "IR-30-TIF-LANE-DUPLICATE", "IR-30-LANE-BOUND-CAP",
                   "IR-30-HOLDOUT-SCALE-MISMATCH", "IR-30-CANARY-NEAR-THRESHOLD",
                   "IR-30-LEADERBOARD-THREE-VALUES", "IR-30-PROMPT-NORMALIZED"):
        assert needed in ids
    cards = json.loads((ROOT / "registry" / "run_card_2026-10-30.json").read_text(encoding="utf-8"))
    assert [c["verdict"] for c in cards] == ["negative", "negative"]


def test_lane_bound_arithmetic_matches_receipt():
    rec = json.loads((ROOT / "evidence" / "lane_bound_r13_2026-10-28.json").read_text(encoding="utf-8"))
    eligible = rec["eligible_pixels_outside_halo_and_catalogue"]
    assert rec["max_dots_with_min_overlap_at_most_0_70"] == int(eligible / 0.3)
