#!/usr/bin/env python3
"""Publish the cache-gated H73-BW stop and keep the prior H73-PM file inspection-only.

The H73-PM model remains a failed, unscored research result; this block selector is blocked before
fit because shared caches are absent. This synchronization helper never creates a model, TIFF, or score.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "H73-BW-2026-10-26"


def h73bw_banner(pm_card: dict, bw_card: dict, preflight: dict, lane_audit: dict, *, docs_page: bool = True) -> str:
    pm = pm_card["holdout_dti"]
    bw = bw_card["holdout_dti"]
    lattice = lane_audit["lattice"][0]
    file_name = pm_card["submission_name"]
    missing = [row["path"] for row in preflight["required_artifacts"] if not row["exists"]]
    links = "" if docs_page else "docs/"
    kb = "../knowledge/" if docs_page else "knowledge/"
    ev = "../evidence/" if docs_page else "evidence/"
    reg = "../registry/" if docs_page else "registry/"
    return (
        f'<!-- {MARK} --><aside class="current-status" aria-label="Current H73-BW decision">\n'
        f"<strong>26 OCT 2026 · NO NEW TIF · H73-BW: BLOCKED BEFORE FIT · "
        f"PRIOR RESEARCH ARCHIVE DOWNLOAD: YES (INSPECTION ONLY) · COMPETITION-READY TIF: NO · "
        f"OK TO SUBMIT: NO — DO NOT SUBMIT</strong>\n"
        f"<span>H73-BW is an evaluation-only diagnostic, conditionally authorized but stopped by its cache gate: "
        f"{len(missing)}/{len(preflight['required_artifacts'])} required shared-cache artifacts are absent. "
        f"No H73-BW fit, HOLDOUT-DTI, canary, candidate surface, lane audit, or raster exists ({html.escape(bw['reason'])}). Prior H73-PM "
        f"HOLDOUT-DTI {pm['pm_deapron_pooled']:.5f} vs same-run H35 {pm['ctrl_h35_pooled']:.5f} "
        f"({pm['withheld_positive_occurrences']:,} withheld-positive occurrences; 95% CI "
        f"[{pm['pm_deapron_ci95'][0]:.5f}, {pm['pm_deapron_ci95'][1]:.5f}]) is a catalogue-gap proxy, not a "
        f"leaderboard estimate. Its literal lane audit flags {100 * lattice['cand_dots_within_3px']:.0f}% of dots "
        f"within 3 px of the r13 lattice; no density-aware waiver applies. No submission is eligible. "
f"Estimated competition score: UNKNOWN (not calibrated).</span>\n"
        f'<a href="{links}downloads/{html.escape(file_name)}" download>↓ Prior H73-PM file for inspection only — DO NOT SUBMIT</a> · '
        f'<a href="{reg}run_card_h73_bw_2026-10-26.json" download>H73-BW run card (metrics null)</a> · '
        f'<a href="{ev}h73_bw_preflight_2026-10-26.json" download>cache preflight receipt</a> · '
        f'<a href="{kb}34_h73_bw_block_selector_2026-10-26.md">H73-BW decision &amp; design</a> · '
        f'<a href="{links}current-review.html#h73-status">full current review →</a></aside>'
    )


def publish_banner(page: str, banner: str) -> str:
    """Replace this review's marked banner, or insert it at the top of <main>."""
    marker = f"<!-- {MARK} -->"
    start = page.find(marker)
    if start >= 0:
        close = page.find("</aside>", start)
        if close < 0:
            raise ValueError("H73-BW marker found without its closing aside")
        return page[:start] + banner + page[close + len("</aside>"):]
    anchor = '<main class="wrap">'
    if anchor not in page:
        raise ValueError("Could not locate main wrapper to publish H73-BW decision")
    return page.replace(anchor, anchor + banner, 1)


def main() -> None:
    pm_card = json.loads((ROOT / "registry" / "run_card_h73_2026-10-26.json").read_text())
    bw_card = json.loads((ROOT / "registry" / "run_card_h73_bw_2026-10-26.json").read_text())
    preflight = json.loads((ROOT / "evidence" / "h73_bw_preflight_2026-10-26.json").read_text())
    lane_audit = json.loads((ROOT / "evidence" / "h73_lane_extended.json").read_text())

    for rel in ("docs/index.html", "index.html", "docs/current-review.html", "docs/executive-summary.html"):
        path = ROOT / rel
        page = path.read_text()
        banner = h73bw_banner(pm_card, bw_card, preflight, lane_audit, docs_page=(rel != "index.html"))
        updated = publish_banner(page, banner)
        updated = updated.replace(
            "26 OCT 2026 · RESEARCH-ARCHIVE DOWNLOAD: YES (INSPECTION ONLY) · COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT",
            "PRIOR H72-3 ARCHIVE · RESEARCH INSPECTION ONLY · COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT",
        )
        path.write_text(updated)
        print(f"{rel}: H73-BW status synchronized")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    marker = f"<!-- {MARK} -->"
    h = pm_card["holdout_dti"]
    file_name = pm_card["submission_name"]
    block = (
        f"{marker}\n"
        f"**H73-BW diagnostic: {bw_card['status'].upper()} · NO NEW TIF · OK TO SUBMIT: NO.** "
        f"The evaluation-only block selector is blocked before fit because {len(preflight['errors'])} cache-gate errors were recorded. "
        f"Prior H73-PM research GeoTIFF [{file_name}](docs/downloads/{file_name}) "
        f"(content id `{pm_card['content_id']}`, {pm_card['positive_pixels']:,} dots) is for inspection only; "
        f"the literal lane audit flags the r13 lattice, so DO NOT SUBMIT. Its HOLDOUT-DTI is {h['pm_deapron_pooled']:.5f} "
        f"vs same-run H35 {h['ctrl_h35_pooled']:.5f}, paired gain {h['paired_gain_vs_h35']:+.5f}, "
        f"95% CI [{h['paired_ci95_vs_h35'][0]:+.5f}, {h['paired_ci95_vs_h35'][1]:+.5f}], "
        f"{h['withheld_positive_occurrences']:,} withheld positives; this is not a leaderboard estimate. "
        f"No H73-BW metric or raster was produced. [H73-BW design](knowledge/34_h73_bw_block_selector_2026-10-26.md) · "
        f"[preflight](evidence/h73_bw_preflight_2026-10-26.json) · "
        f"[run card](registry/run_card_h73_bw_2026-10-26.json) · "
        f"[follow-up review](knowledge/35_h73_bw_followup_review_2026-10-26.md).\n\n"
    )
    if marker in readme:
        start = readme.index(marker)
        end = readme.find("\n\n", start)
        if end < 0:
            raise ValueError("README H73-BW marker has no paragraph terminator")
        readme = readme[:start] + block.rstrip() + readme[end:]
    else:
        heading = "## Current decision — 2026-10-26\n"
        if heading not in readme:
            raise ValueError("README current-decision heading not found")
        readme = readme.replace(heading, heading + "\n" + block, 1)
    readme_path.write_text(readme)
    print("README: H73-BW status synchronized")


if __name__ == "__main__":
    main()
