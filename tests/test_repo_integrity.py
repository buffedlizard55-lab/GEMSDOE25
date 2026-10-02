"""Repository integrity: registries, shipped downloads, site links, DrivenData-automation guard, README brief."""

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def J(p):
    return json.loads((ROOT / p).read_text())


def test_registries_parse_and_ids_are_unique():
    for name in ("sources", "irregularities", "live_scores", "data_manifest"):
        J(f"registry/{name}.json")
    ids = [i["id"] for i in J("registry/irregularities.json")["issues"]]
    assert len(ids) == len(set(ids))
    for i in J("registry/irregularities.json")["issues"]:
        assert i["evidence"] and i["resolution_or_action"] and i["severity"] in ("critical", "high", "medium", "low", "info")
    for s in J("registry/sources.json")["sources"]:
        assert s["url"].startswith("https://") and isinstance(s["verified"], bool)
        assert (s["verified_utc"] is not None) == s["verified"]


def test_data_manifest_hashes_look_like_sha256_and_pins_are_unique_files():
    man = J("registry/data_manifest.json")["files"]
    assert len({m["dest"] for m in man}) == len(man)
    for m in man:
        assert re.fullmatch(r"[0-9a-f]{64}", m["sha256"])
    assert any(m["id"] == "training_features" and m["sha256"].startswith("4371c82e") for m in man)


def test_shipped_downloads_match_registry_hashes_and_are_small():
    subs = J("registry/submissions.json")["files"]
    assert any(s["role"] == "primary" for s in subs)
    assert not any(s.get("slot_approved", False) for s in subs)
    primary = next(s for s in subs if s["role"] == "primary")
    fallback = next(s for s in subs if s["role"] == "fallback")
    for item in (primary, fallback):
        assert "not holdout-promoted vs 0.152003389" in item["note"] and "no slot" in item["note"]
        assert len(item["note"]) <= 120
    registered_tifs = {s["file"] for s in subs}
    shipped_tifs = {p.name for p in (ROOT / "docs" / "downloads").glob("*.tif")}
    assert shipped_tifs == registered_tifs, "unregistered GeoTIFF in docs/downloads can be downloaded directly"
    for s in subs:
        f = ROOT / s["path"]
        assert f.exists(), s["path"]
        assert hashlib.sha256(f.read_bytes()).hexdigest() == s["sha256"], s["file"]
        assert f.stat().st_size < 6_000_000
        assert s["format_ok"] is True
        assert len(s["note"]) <= 120 and s["content_id"] in s["file"] or s["role"] in ("fallback", "zip")


def test_no_large_or_forbidden_files_are_tracked():
    import subprocess

    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    for f in files:
        p = ROOT / f
        if p.exists() and p.stat().st_size > 6_000_000:
            pytest.fail(f"large tracked file {f}")
        assert not f.startswith("data/") or f == "data/.gitkeep", f


def test_feed_script_can_never_request_drivendata():
    import check_sources as cs

    assert cs.is_blocked("https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/")
    assert cs.is_blocked("https://community.drivendata.org/t/x")
    assert not cs.is_blocked("https://gdr.openei.org/submissions/1391")

    class Boom:
        def request(self, *a, **k):
            raise AssertionError("network call made to a blocked host")

    r = cs.probe(Boom(), "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/")
    assert "not fetched" in r["status"]


def test_feed_manually_blocks_redirects_for_every_request_method():
    import check_sources as cs

    class Response:
        def __init__(self, status, headers=None):
            self.status_code = status
            self.headers = headers or {}
            self.closed = False

        def close(self):
            self.closed = True

    class RedirectSession:
        def __init__(self, responses):
            self.responses = list(responses)
            self.calls = []

        def request(self, method, url, **kwargs):
            assert kwargs["allow_redirects"] is False
            self.calls.append((method, url))
            return self.responses.pop(0)

    original = "https://official.example.test/data"
    blocked = "https://api.drivendata.org/anything"

    # HEAD redirect: the forbidden host is never requested.
    response = Response(302, {"Location": blocked})
    session = RedirectSession([response])
    got = cs.probe(session, original)
    assert got["status"] == "redirect to DrivenData not followed"
    assert session.calls == [("HEAD", original)] and response.closed

    # A 405 HEAD followed by GET must also keep redirects disabled (the old GET fallback did not).
    head, get = Response(405), Response(302, {"Location": blocked})
    session = RedirectSession([head, get])
    got = cs.probe(session, original)
    assert got["status"] == "redirect to DrivenData not followed"
    assert session.calls == [("HEAD", original), ("GET", original)]
    assert head.closed and get.closed

    # ScienceBase and GitHub paths share this same safe primitive.
    response = Response(301, {"Location": blocked})
    session = RedirectSession([response])
    with pytest.raises(cs.BlockedRedirect):
        cs.safe_request(session, "GET", original)
    assert session.calls == [("GET", original)] and response.closed


def test_readme_carries_the_brief_and_core_values():
    t = (ROOT / "README.md").read_text()
    assert "Maximize P(Win)" in t and "Own the Outcome" in t
    assert "Predicted values must be in range [0, 1]" in t
    brief = (ROOT / "knowledge" / "owner_brief_verbatim.txt").read_text()
    assert brief.strip()[:200] in t and brief.strip()[-200:] in t


LINK = re.compile(r'(?:href|src)="([^"#?]+)"')


@pytest.mark.parametrize("page", ["index.html", "docs/index.html", "docs/executive-summary.html", "docs/research.html", "docs/sources.html"])
def test_site_local_links_resolve(page):
    f = ROOT / page
    assert f.exists(), page
    for ref in LINK.findall(f.read_text()):
        if ref.startswith(("http://", "https://", "mailto:", "data:")):
            continue
        assert (f.parent / ref).resolve().exists(), f"{page}: broken local link {ref}"


def test_first_screen_of_home_has_the_download_before_anything_else():
    t = (ROOT / "index.html").read_text()
    primary = next(s for s in J("registry/submissions.json")["files"] if s["role"] == "primary")
    assert t.index(primary["file"]) < t.index("Local audit of the reported 0.2477 raster (score unverified)")
    assert "not slot-approved" in t and "0.152003389" in t
    assert "executive-summary.html" in t


def test_the_invented_footprint_files_are_not_shipped_or_linked():
    bad = ("gems25-factorial-best-v1-nan.tif", "gems25-factorial-best-v1-allfinite.tif")
    for name in bad:
        assert not (ROOT / "docs" / "downloads" / name).exists()
    for page in ("README.md", "index.html", "docs/index.html", "docs/executive-summary.html", "docs/research.html", "docs/sources.html"):
        text = (ROOT / page).read_text()
        for name in bad:
            # mentions are allowed only as warnings ("not this file"), never as a link target
            assert f'href="docs/downloads/{name}"' not in text and f'href="downloads/{name}"' not in text and f"(docs/downloads/{name})" not in text


def test_shipped_files_are_not_duplicates_of_already_scored_files():
    # content ids of rasters that already have an owner-reported score (re-uploading them gives no information)
    already_scored = {"989f59505db1": "dotted H19-5 d1.5 (0.2477)", "80d47e1ab2ee": "H19-5 (0.1922)"}
    for s in J("registry/submissions.json")["files"]:
        assert s["content_id"] not in already_scored, (s["file"], already_scored.get(s["content_id"]))
