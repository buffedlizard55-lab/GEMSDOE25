#!/usr/bin/env python3
"""Timestamped source-health feed -> ``docs/data/feed.json``.

Policy (see AGENTS.md rule 3): this script **never contacts drivendata.org** (DrivenData's Terms of Use prohibit
robots / automatic devices accessing the site "for any purpose, including monitoring"). DrivenData rows are
human-read snapshots stored in ``registry/live_scores.json``; here they appear only with their age.

What it checks automatically (when the network allows; the dev sandbox blocks most hosts, CI does not):
  * HTTP status / Last-Modified / Content-Length of every non-DrivenData source in ``registry/sources.json``
  * USGS ScienceBase JSON API ``lastUpdated`` for the GeoDAWN and slip/dilation-tendency items
  * GitHub API ``pushed_at`` of the owner's sibling GEMSDOE repositories (activity feed)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_SUFFIXES = ("drivendata.org",)
SCIENCEBASE = {
    "GeoDAWN release": "657e1d85d34e23d3533209f7",
    "Slip/dilation tendency release": "6296974dd34ec53d276bb33d",
}
SIBLINGS = [f"{n}GEMSDOE" for n in (5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)] + [
    "GEMSDOE", "GEMSDOE2", "GEMSDOE3", "GEMSDOE4", "GEMSDOE9", "GEMSDOE10", "GEMSDOE21", "GEMSDOE22", "GEMSDOE23", "GEMSDOE24",
]


def is_blocked(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == s or host.endswith("." + s) for s in BLOCKED_SUFFIXES)


def gh_api_json(path: str):
    """GitHub API via the authenticated ``gh`` CLI when available (works where plain HTTPS to api.github.com is blocked)."""
    import shutil
    import subprocess

    if not shutil.which("gh"):
        raise RuntimeError("gh CLI not available")
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[:120])
    return json.loads(out.stdout)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def probe(session, url: str) -> dict:
    if is_blocked(url):
        return dict(status="not fetched (Terms of Use)", detail="DrivenData host: human-read snapshot only")
    try:
        r = session.head(url, timeout=20, allow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get("Location", "")
            if is_blocked(loc):
                return dict(status="redirect to DrivenData not followed", detail=loc)
            r = session.head(loc, timeout=20, allow_redirects=False) if loc.startswith("http") else r
        if r.status_code in (405, 403):
            r = session.get(url, timeout=20, stream=True)
            r.close()
        d = [f"HTTP {r.status_code}"]
        for h in ("Last-Modified", "Content-Length", "ETag"):
            if h in r.headers:
                d.append(f"{h}: {r.headers[h]}")
        return dict(status="ok" if r.status_code < 400 else f"HTTP {r.status_code}", detail="; ".join(d))
    except Exception as e:  # noqa: BLE001 - network failure is data, not an error
        return dict(status="unreachable", detail=type(e).__name__)


def main() -> None:
    import requests

    s = requests.Session()
    s.headers["User-Agent"] = "GEMSDOE25-source-feed (+https://github.com/buffedlizard55-lab/GEMSDOE25)"
    tok = os.environ.get("GITHUB_TOKEN")
    gh = requests.Session()
    gh.headers.update({"Accept": "application/vnd.github+json", "User-Agent": s.headers["User-Agent"]})
    if tok:
        gh.headers["Authorization"] = f"Bearer {tok}"
    items = []
    for src in json.loads((ROOT / "registry" / "sources.json").read_text())["sources"]:
        p = probe(s, src["url"])
        items.append(dict(kind="source", title=src["title"], url=src["url"], verified_in_repo=src["verified"], **p))
    for title, sid in SCIENCEBASE.items():
        url = f"https://www.sciencebase.gov/catalog/item/{sid}?format=json&fields=title,lastUpdated,dateCreated"
        try:
            j = s.get(url, timeout=20).json()
            items.append(dict(kind="sciencebase", title=title, url=f"https://www.sciencebase.gov/catalog/item/{sid}", status="ok",
                              detail=f"lastUpdated {j.get('lastUpdated')}"))
        except Exception as e:  # noqa: BLE001
            items.append(dict(kind="sciencebase", title=title, url=f"https://www.sciencebase.gov/catalog/item/{sid}", status="unreachable", detail=type(e).__name__))
    for name in SIBLINGS:
        url = f"https://api.github.com/repos/buffedlizard55-lab/{name}"
        try:
            try:
                r = gh.get(url, timeout=20)
                j, ok, code = r.json(), r.ok, r.status_code
            except Exception:  # noqa: BLE001 - fall back to the gh CLI
                j, ok, code = gh_api_json(f"repos/buffedlizard55-lab/{name}"), True, 200
            items.append(dict(kind="sibling-repo", title=name, url=f"https://github.com/buffedlizard55-lab/{name}", status="ok" if ok else f"HTTP {code}",
                              detail=f"pushed_at {j.get('pushed_at')}"))
        except Exception as e:  # noqa: BLE001
            items.append(dict(kind="sibling-repo", title=name, url=f"https://github.com/buffedlizard55-lab/{name}", status="unreachable", detail=type(e).__name__))
    ls = json.loads((ROOT / "registry" / "live_scores.json").read_text())
    snap = ls["leaderboard_snapshot"]
    age = (dt.datetime.now(dt.timezone.utc).date() - dt.date.fromisoformat(snap["read_utc"])).days
    items.append(dict(kind="human-snapshot", title="DrivenData leaderboard (human-read snapshot)", url=snap["source"], status=f"snapshot {snap['read_utc']} ({age} d old)",
                      detail=f"#1 {snap['top10'][0]['participant']} {snap['top10'][0]['best_public_dti']}; update with scripts/record_live_score.py after reading it yourself"))
    feed = dict(generated_utc=now(), generator="scripts/check_sources.py",
                policy="Never requests drivendata.org (Terms of Use). 'unreachable' means the network blocked the request from the machine that built the feed; it does not mean the source is down.",
                items=items)
    out = ROOT / "docs" / "data" / "feed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feed, indent=1) + "\n")
    ok = sum(1 for i in items if i["status"] == "ok")
    print(f"feed: {len(items)} items, {ok} reachable -> {out}")


if __name__ == "__main__":
    sys.exit(main())
