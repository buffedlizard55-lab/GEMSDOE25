#!/usr/bin/env python3
"""Publish the latest H73-PM decision consistently across the static site and README.

The GeoTIFF is research-only: the paired HOLDOUT-DTI gate failed and the literal lane
check fails on the dense r13 registry raster. This script must never describe it as
slot-approved. It is idempotent and reads all numeric H73 results from its run card.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "H73-PM-2026-10-26"


def h73_banner(card: dict, lane_audit: dict, *, docs_page: bool = True) -> str:
    h = card["holdout_dti"]
    lane = card["correlation_overlap_vs_registry"]
    lattice = lane_audit["lattice"][0]
    file_name = card["submission_name"]
    # The candidate's lane_clear is false because the literal rule flags the dense r13 lattice.
    prefix = "" if docs_page else "docs/"
    return (
        f'<!-- {MARK} --><aside class="current-status" aria-label="Current H73-PM decision">\n'
        f"<strong>26 OCT 2026 · RESEARCH ARCHIVE ONLY · OK TO DOWNLOAD: YES (INSPECTION) · "
        f"COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT</strong>\n"
        f"<span>H73-PM <code>{html.escape(card['content_id'])}</code>: "
        f"HOLDOUT-DTI {h['pm_deapron_pooled']:.5f} vs same-run CTRL_H35 {h['ctrl_h35_pooled']:.5f}; "
        f"paired gain {h['paired_gain_vs_h35']:+.5f}, 95% CI "
        f"[{h['paired_ci95_vs_h35'][0]:+.5f}, {h['paired_ci95_vs_h35'][1]:+.5f}] "
        f"({h['withheld_positive_occurrences']:,} withheld-positive occurrences). "
        f"This is a catalogue-gap proxy, not a leaderboard estimate. Hard format checks pass against the "
        f"pinned owner-mirror template, but the literal uniqueness gate fails: "
        f"{100 * lattice['cand_dots_within_3px']:.0f}% of candidate dots are within 3 px of "
        f"{html.escape(lattice['file'])}; no density-aware exception applies. "
        f"Surface max |Spearman|={lane['surface_worst_abs_spearman']:.3f} is below 0.90. "
        f"Estimated competition score: UNKNOWN (not calibrated).</span>\n"
        f'<a href="{prefix}downloads/{html.escape(file_name)}" download>↓ Download for research inspection only — DO NOT SUBMIT</a> · '
        f'<a href="{prefix}data/run_card_h73_2026-10-26.json" download>H73 run card JSON</a> · '
        f'<a href="{prefix}../knowledge/34_current_session_review_2026-10-26.md">Current review &amp; nine-site table →</a></aside>'
    )


def publish_banner(page: str, banner: str) -> str:
    """Replace this review's marked banner, or insert it at the top of <main>."""
    marker = f"<!-- {MARK} -->"
    start = page.find(marker)
    if start >= 0:
        close = page.find("</aside>", start)
        if close < 0:
            raise ValueError("H73 marker found without its closing aside")
        return page[:start] + banner + page[close + len("</aside>"):]
    anchor = '<main class="wrap">'
    if anchor not in page:
        raise ValueError("Could not locate main wrapper to publish H73 decision")
    return page.replace(anchor, anchor + banner, 1)


def main() -> None:
    card = json.loads((ROOT / "registry" / "run_card_h73_2026-10-26.json").read_text())
    lane_audit = json.loads((ROOT / "evidence" / "h73_lane_extended.json").read_text())
    h = card["holdout_dti"]
    zfile = card["submission_name"]

    # docs/index already had an H73 strip; refresh it from the authoritative run card.
    # Keep the root index in sync as well as the two pages users visit to decide/submission.
    for rel in ("docs/index.html", "index.html", "docs/current-review.html", "docs/executive-summary.html"):
        path = ROOT / rel
        page = path.read_text()
        banner = h73_banner(card, lane_audit, docs_page=(rel != "index.html"))
        updated = publish_banner(page, banner)
        # Existing H72 status strips are retained as history, but must not appear current.
        updated = updated.replace(
            "26 OCT 2026 · RESEARCH-ARCHIVE DOWNLOAD: YES (INSPECTION ONLY) · COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT",
            "PRIOR H72-3 ARCHIVE · RESEARCH INSPECTION ONLY · COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT",
        )
        path.write_text(updated)
        print(f"{rel}: H73 decision synchronized")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    marker = f"<!-- {MARK} -->"
    block = (
        f"{marker}\n"
        f"**H73-PM decision (2026-10-26):** research GeoTIFF [{zfile}](docs/downloads/{zfile}) "
        f"(content id `{card['content_id']}`, {card['positive_pixels']:,} dots). "
        f"**OK to download: YES (inspection only) · competition-ready: NO · OK TO SUBMIT: NO — DO NOT SUBMIT.** "
        f"HOLDOUT-DTI {h['pm_deapron_pooled']:.5f} vs same-run CTRL_H35 {h['ctrl_h35_pooled']:.5f}; "
        f"paired gain {h['paired_gain_vs_h35']:+.5f}, 95% CI "
        f"[{h['paired_ci95_vs_h35'][0]:+.5f}, {h['paired_ci95_vs_h35'][1]:+.5f}], "
        f"{h['withheld_positive_occurrences']:,} withheld-positive occurrences. This is not a leaderboard estimate. "
        f"It also fails the literal lane gate on the r13 lattice (no density-aware waiver). "
        f"[Current nine-site review](knowledge/34_current_session_review_2026-10-26.md) · "
        f"[H73 outcomes](knowledge/33_h73_outcomes_and_executive_summary_2026-10-26.md) · "
        f"[Run card](registry/run_card_h73_2026-10-26.json). No weekly slot was used.\n\n"
    )
    if marker in readme:
        start = readme.index(marker)
        # The marked paragraph ends at the first blank line after its content.
        end = readme.find("\n\n", start)
        if end < 0:
            raise ValueError("README H73 marker has no paragraph terminator")
        readme = readme[:start] + block.rstrip() + readme[end:]
    else:
        heading = "## Current decision — 2026-10-26\n"
        if heading not in readme:
            raise ValueError("README current-decision heading not found")
        readme = readme.replace(heading, heading + "\n" + block, 1)
    readme_path.write_text(readme)
    print("README: H73 decision synchronized")


if __name__ == "__main__":
    main()
