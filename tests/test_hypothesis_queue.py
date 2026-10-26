from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = json.loads((ROOT / "registry" / "hypothesis_queue_2026-10-26.json").read_text())


def test_queue_is_a_ranked_planning_slate_not_experiment_results() -> None:
    generated = dt.datetime.fromisoformat(QUEUE["generated_utc"].replace("Z", "+00:00"))
    assert generated.tzinfo is not None
    assert QUEUE["schema"] == "planning_hypothesis_queue/v1"
    assert "no new hypothesis was fit" in QUEUE["evidence_class"]
    assert "No experiment" in QUEUE["experiment_budget_effect"]
    rows = QUEUE["hypotheses"]
    assert 3 <= len(rows) <= 5
    assert [row["rank"] for row in rows] == list(range(1, len(rows) + 1))
    required = {
        "id", "name", "layers", "signature_and_transform", "blind_fault_rationale",
        "repo_distinction", "non_fault_mimics", "planning_expected_holdout_delta_dti",
        "implementation_cost", "data_availability", "official_manual_review_sources", "status",
    }
    for row in rows:
        assert required <= row.keys()
        assert row["layers"] and row["non_fault_mimics"] and row["official_manual_review_sources"]
        assert row["repo_distinction"]
        expected = row["planning_expected_holdout_delta_dti"]
        assert expected["low"] <= expected["high"]
        assert "planning judgment" in expected["label"]
        assert all(source["url"].startswith("https://") for source in row["official_manual_review_sources"])


def test_review_page_renders_hypotheses_as_planning_judgments_only() -> None:
    page = (ROOT / "docs" / "current-review.html").read_text()
    assert "Ranked blind-fault research hypotheses — planning only, no fit" in page
    assert "Planning judgment:" in page
    assert "Conductive alteration-front / radiometric edge co-orientation" in page
    assert "no new test was run in this review" in page
