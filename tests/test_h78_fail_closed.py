from __future__ import annotations

import pytest

from scripts.build_h78_submission import main


def test_h78_builder_fails_closed_after_lane_and_score_audit(capsys: pytest.CaptureFixture[str]) -> None:
    assert main() == 2
    assert "H78 publisher retired" in capsys.readouterr().err


def test_h78_archive_is_not_marked_as_slot_approved() -> None:
    import json
    from pathlib import Path

    card = json.loads(Path("registry/run_card_h78_2026-10-27.json").read_text())
    assert card["estimated_competition_score"] is None
    assert card["submission"]["ok_to_submit"] is False
    assert card["submission"]["verdict"].startswith("negative")
    lane = card["correlation_overlap_vs_registry"]
    assert lane["candidate_dots_within_3px"] > 0.70
    assert "FAIL" in lane["status"]
