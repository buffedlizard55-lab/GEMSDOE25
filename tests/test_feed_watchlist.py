from __future__ import annotations

import json
import sys
from urllib.parse import urlparse

from scripts import check_sources as sources


def test_feed_watchlist_includes_all_remote_focus_sites_and_pinned_scorers() -> None:
    names = set(sources.sibling_repositories())
    assert set(sources.FOCUS_SIBLINGS) <= names
    assert "GEMSDOE25" not in names  # current project is not mislabeled as a sibling
    pins = json.loads((sources.ROOT / "registry" / "top_scorer_sources.json").read_text())
    expected = {
        row["repo"].removeprefix("buffedlizard55-lab/")
        for row in pins["rasters"]
        if row.get("repo", "").startswith("buffedlizard55-lab/")
    }
    assert expected <= names


def test_repository_only_refresh_never_probes_non_github_hosts(tmp_path, monkeypatch, capsys) -> None:
    registry = tmp_path / "registry"
    feed_dir = tmp_path / "docs" / "data"
    registry.mkdir()
    feed_dir.mkdir(parents=True)
    (registry / "top_scorer_sources.json").write_text(
        json.dumps({"rasters": [{"repo": "buffedlizard55-lab/GEMSDOE91"}]})
    )
    (registry / "live_scores.json").write_text(
        json.dumps(
            {
                "leaderboard_snapshot": {
                    "source": "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
                    "status": "user-provided snapshot, unverified",
                    "reported_utc": "2026-10-03",
                    "top10": [{"participant": "unverified", "best_public_dti": 0.3195}],
                }
            }
        )
    )
    (feed_dir / "feed.json").write_text(
        json.dumps(
            {
                "generated_utc": "2026-10-25T00:00:00Z",
                "items": [
                    {"kind": "source", "title": "cached official source", "url": "https://example.gov/", "status": "ok"},
                    {"kind": "sciencebase", "title": "cached ScienceBase", "url": "https://www.sciencebase.gov/", "status": "ok"},
                ],
            }
        )
    )
    monkeypatch.setattr(sources, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_sources.py", "--repositories-only"])
    monkeypatch.setattr(sources, "now", lambda: "2026-10-26T17:00:00Z")
    hosts: list[str] = []

    class Response:
        status_code = 200
        headers: dict[str, str] = {}

        @staticmethod
        def json():
            return {"pushed_at": "2026-10-26T16:00:00Z"}

        @staticmethod
        def close():
            return None

    def fake_safe_request(_session, method, url, **_kwargs):
        assert method == "GET"
        hosts.append(urlparse(url).hostname or "")
        return Response()

    monkeypatch.setattr(sources, "safe_request", fake_safe_request)
    sources.main()
    assert hosts and set(hosts) == {"api.github.com"}
    output = json.loads((feed_dir / "feed.json").read_text())
    assert "GitHub repository activity checked" in output["refresh_scope"]
    assert "GEMSDOE24" in {item["title"] for item in output["items"] if item["kind"] == "sibling-repo"}
    assert "GEMSDOE91" in {item["title"] for item in output["items"] if item["kind"] == "sibling-repo"}
    stale = [item for item in output["items"] if item["kind"] in ("source", "sciencebase")]
    assert len(stale) == 2
    assert all("not rechecked" in item["freshness"] for item in stale)
    snapshot = next(item for item in output["items"] if item["kind"] == "human-snapshot")
    assert snapshot["checked_utc"] is None
    assert "not contacted" in snapshot["freshness"]
    assert "Never requests drivendata.org" in output["policy"]
    assert "feed: " in capsys.readouterr().out


def test_refreshed_feed_keeps_non_github_rows_explicitly_stale() -> None:
    feed = json.loads((sources.ROOT / "docs" / "data" / "feed.json").read_text())
    assert "GitHub repository activity checked" in feed["refresh_scope"]
    repos = [item for item in feed["items"] if item["kind"] == "sibling-repo"]
    assert set(sources.FOCUS_SIBLINGS) <= {item["title"] for item in repos}
    assert repos and all(item.get("checked_utc") == feed["generated_utc"] for item in repos)
    non_github = [item for item in feed["items"] if item["kind"] in ("source", "sciencebase")]
    assert non_github and all("not rechecked" in item["freshness"] for item in non_github)
    assert any("not fetched (Terms of Use)" == item["status"] for item in feed["items"])
    snapshot = next(item for item in feed["items"] if item["kind"] == "human-snapshot")
    assert snapshot["checked_utc"] is None and "not contacted" in snapshot["freshness"]
