"""Regression tests for the feed's no-DrivenData host policy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_sources as cs  # noqa: E402


@pytest.mark.parametrize(
    "url",
    [
        "https://drivendata.org/",
        "https://drivendata.org./",
        "https://WWW.DRIVENDATA.ORG./leaderboard/",
        "https://www.drivendata.org../leaderboard/",
        "https://community.drivendata.org./t/example",
        "https://www.drivendata。org/leaderboard/",
        "https://www.drivendata．org/leaderboard/",
        "https://www.drivendata｡org/leaderboard/",
    ],
)
def test_dns_equivalent_drivendata_hosts_are_blocked(url: str) -> None:
    assert cs.is_blocked(url)


def test_non_drivendata_hosts_and_lookalikes_are_not_false_positives() -> None:
    assert not cs.is_blocked("https://gdr.openei.org/submissions/1391")
    assert not cs.is_blocked("https://drivendata.org.example.test/redirect")


def test_malformed_host_fails_closed() -> None:
    assert cs.is_blocked("https://[")
    assert cs.is_blocked("https://")
    assert cs.is_blocked("https://bad..example.test/")


def test_redirect_to_trailing_dot_drivendata_is_rejected_before_second_request() -> None:
    class Response:
        status_code = 302
        headers = {"Location": "https://www.drivendata.org./competitions/306/"}
        closed = False

        def close(self) -> None:
            self.closed = True

    class Session:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def request(self, method: str, url: str, **kwargs) -> Response:
            assert kwargs["allow_redirects"] is False
            self.calls.append((method, url))
            return Response()

    session = Session()
    original = "https://public.example.test/file"
    with pytest.raises(cs.BlockedRedirect):
        cs.safe_request(session, "GET", original)

    assert session.calls == [("GET", original)]
