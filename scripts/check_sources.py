#!/usr/bin/env python3
"""Timestamped source-health feed -> ``docs/data/feed.json``.

Policy (see AGENTS.md rule 3): this script **never contacts drivendata.org** (DrivenData's Terms of Use prohibit
robots / automatic devices accessing the site "for any purpose, including monitoring"). DrivenData rows are
human-read snapshots stored in ``registry/live_scores.json``; here they appear only with their age.

What it checks automatically (when the network allows; the dev sandbox blocks most hosts, CI does not):
  * HTTP status / Last-Modified / Content-Length of every non-DrivenData source in ``registry/sources.json``
  * USGS ScienceBase JSON API ``lastUpdated`` for GeoDAWN, slip/dilation-tendency and Great Basin heat-flow items
  * GitHub API ``pushed_at`` of the owner's sibling GEMSDOE repositories (activity feed)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_SUFFIXES = ("drivendata.org",)
SCIENCEBASE = {
    "GeoDAWN release": "657e1d85d34e23d3533209f7",
    "Slip/dilation tendency release": "6296974dd34ec53d276bb33d",
    "Great Basin heat-flow release": "6297d2fad34ec53d276c5b28",
}
SIBLINGS = [f"{n}GEMSDOE" for n in (5, 6, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)] + [
    "GEMSDOE", "GEMSDOE2", "GEMSDOE3", "GEMSDOE4", "GEMSDOE9", "GEMSDOE10", "GEMSDOE21", "GEMSDOE22", "GEMSDOE23", "GEMSDOE24",
]


def is_blocked(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == s or host.endswith("." + s) for s in BLOCKED_SUFFIXES)


class BlockedRedirect(RuntimeError):
    """A safe source redirected to a host that this feed is forbidden to contact."""


def safe_request(session, method: str, url: str, **kwargs):
    """Send one request at a time; manually follow only safe redirects, never requests' automatic chain."""
    if "allow_redirects" in kwargs:
        raise ValueError("safe_request owns the redirect policy")
    current = url
    for _ in range(6):
        if is_blocked(current):
            raise BlockedRedirect(current)
        response = session.request(method, current, allow_redirects=False, **kwargs)
        if response.status_code not in (301, 302, 303, 307, 308):
            return response
        location = response.headers.get("Location", "")
        if not location:
            return response
        target = urljoin(current, location)
        response.close()
        if is_blocked(target):
            raise BlockedRedirect(target)
        current = target
    raise RuntimeError("redirect limit exceeded")


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
    response = None
    try:
        response = safe_request(session, "HEAD", url, timeout=20)
        if response.status_code in (405, 403):
            response.close()
            response = safe_request(session, "GET", url, timeout=20, stream=True)
        d = [f"HTTP {response.status_code}"]
        for h in ("Last-Modified", "Content-Length", "ETag"):
            if h in response.headers:
                d.append(f"{h}: {response.headers[h]}")
        return dict(status="ok" if response.status_code < 400 else f"HTTP {response.status_code}", detail="; ".join(d))
    except BlockedRedirect as e:
        return dict(status="redirect to DrivenData not followed", detail=str(e))
    except Exception as e:  # noqa: BLE001 - network failure is data, not an error
        return dict(status="unreachable", detail=type(e).__name__)
    finally:
        if response is not None:
            response.close()


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
        url = f"https://www.sciencebase.gov/catalog/item/{sid}?format=json"
        response = None
        try:
            response = safe_request(s, "GET", url, timeout=30)
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}")
            j = response.json()
            last = (j.get("provenance") or {}).get("lastUpdated") or j.get("lastUpdated") or "not provided"
            items.append(dict(kind="sciencebase", title=title, url=f"https://www.sciencebase.gov/catalog/item/{sid}", status="ok",
                              detail=f"lastUpdated {last}"))
        except BlockedRedirect as e:
            items.append(dict(kind="sciencebase", title=title, url=f"https://www.sciencebase.gov/catalog/item/{sid}",
                              status="redirect to DrivenData not followed", detail=str(e)))
        except Exception as e:  # noqa: BLE001
            items.append(dict(kind="sciencebase", title=title, url=f"https://www.sciencebase.gov/catalog/item/{sid}", status="unreachable", detail=type(e).__name__))
        finally:
            if response is not None:
                response.close()
    for name in SIBLINGS:
        url = f"https://api.github.com/repos/buffedlizard55-lab/{name}"
        response = None
        try:
            try:
                response = safe_request(gh, "GET", url, timeout=20)
                j, ok, code = response.json(), response.status_code < 400, response.status_code
            except BlockedRedirect:
                raise
            except Exception:  # noqa: BLE001 - fall back to the gh CLI
                j, ok, code = gh_api_json(f"repos/buffedlizard55-lab/{name}"), True, 200
            items.append(dict(kind="sibling-repo", title=name, url=f"https://github.com/buffedlizard55-lab/{name}", status="ok" if ok else f"HTTP {code}",
                              detail=f"pushed_at {j.get('pushed_at')}"))
        except BlockedRedirect as e:
            items.append(dict(kind="sibling-repo", title=name, url=f"https://github.com/buffedlizard55-lab/{name}",
                              status="redirect to DrivenData not followed", detail=str(e)))
        except Exception as e:  # noqa: BLE001
            items.append(dict(kind="sibling-repo", title=name, url=f"https://github.com/buffedlizard55-lab/{name}", status="unreachable", detail=type(e).__name__))
        finally:
            if response is not None:
                response.close()
    ls = json.loads((ROOT / "registry" / "live_scores.json").read_text())
    snap = ls["leaderboard_snapshot"]
    items.append(dict(kind="human-snapshot", title="DrivenData leaderboard (user-provided, unverified claim)", url=snap["source"],
                      status=f"{snap['status']} · reported {snap['reported_utc']}",
                      detail=f"claimed #1 {snap['top10'][0]['participant']} {snap['top10'][0]['best_public_dti']}; no organizer page/receipt was accessed"))
    feed = dict(generated_utc=now(), generator="scripts/check_sources.py",
                policy="Never requests drivendata.org (Terms of Use); HTTP redirects are followed manually and blocked if the target is that host or a subdomain. 'unreachable' means the network blocked the request from the machine that built the feed; it does not mean the source is down.",
                items=items)
    out = ROOT / "docs" / "data" / "feed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(feed, indent=1) + "\n")
    ok = sum(1 for i in items if i["status"] == "ok")
    print(f"feed: {len(items)} items, {ok} reachable -> {out}")


if __name__ == "__main__":
    sys.exit(main())
