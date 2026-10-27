#!/usr/bin/env python3
"""Synchronize the latest, fail-closed current decision across the static site and README.

The file name is retained for historical build compatibility. This helper does not contact the
competition service, create a model, write a candidate TIFF, or authorize an upload.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "CURRENT-REVIEW-2026-10-27"


def current_banner(*, docs_page: bool = True) -> str:
    if docs_page:
        archive = "downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif"
        fmt = "../evidence/h78_format_recheck_2026-10-27.json"
        lane = "../evidence/h78_lane_recheck_2026-10-27.json"
        review = "current-executive-review.html"
        run = "../registry/run_card_current_review_2026-10-27.json"
    else:
        archive = "docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif"
        fmt = "evidence/h78_format_recheck_2026-10-27.json"
        lane = "evidence/h78_lane_recheck_2026-10-27.json"
        review = "docs/current-executive-review.html"
        run = "registry/run_card_current_review_2026-10-27.json"
    return (
        f'<!-- {MARK} --><aside class="current-status" aria-label="Current competition decision">\n'
        "<strong>27 OCT 2026 · NO ELIGIBLE COMPETITION TIFF · CBEC HOLDOUT SCREEN: NEGATIVE · "
        "H78 ARCHIVE: INSPECTION ONLY · RESEARCH-ARCHIVE DOWNLOAD: YES (INSPECTION ONLY) · "
        "COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT</strong>\n"
        "<span>The preregistered CBEC 2×2 spatial-block screen failed against same-run H35. No new raster was generated. "
        "Existing H78 passes local format/range checks but fails the strict lane rule: 100% of its final dots are within 3 px of the r13 lattice. "
        "Its stored 0.2785 leaderboard estimate was hard-coded and is withdrawn. Leaderboard estimate: NOT ESTIMATED.</span>\n"
        f'<a href="{archive}" download>↓ H78 research archive — inspection only, DO NOT SUBMIT</a> · '
        f'<a href="{fmt}" download>format recheck</a> · <a href="{lane}" download>lane recheck</a> · '
        f'<a href="{run}" download>current JSON run card</a> · <a href="{review}">full current review →</a></aside>'
    )


def publish_banner(page: str, banner: str) -> str:
    marker = f"<!-- {MARK} -->"
    start = page.find(marker)
    if start >= 0:
        close = page.find("</aside>", start)
        if close < 0:
            raise ValueError("current-review marker found without its closing aside")
        return page[:start] + banner + page[close + len("</aside>"):]
    anchor = '<main class="wrap">'
    if anchor not in page:
        raise ValueError("Could not locate main wrapper to publish current decision")
    return page.replace(anchor, anchor + banner, 1)


def main() -> None:
    for rel in ("docs/index.html", "index.html", "docs/current-review.html", "docs/executive-summary.html"):
        path = ROOT / rel
        page = path.read_text()
        updated = publish_banner(page, current_banner(docs_page=(rel != "index.html")))
        path.write_text(updated)
        print(f"{rel}: current fail-closed status synchronized")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    required = (
        "## Current Decision — 2026-10-27",
        "NO NEW COMPETITION TIFF",
        "knowledge/39_current_review_2026-10-27.md",
        "registry/run_card_current_review_2026-10-27.json",
    )
    missing = [text for text in required if text not in readme]
    if missing:
        raise ValueError(f"README current-decision content missing: {missing}")
    print("README: current fail-closed decision verified")


if __name__ == "__main__":
    main()
