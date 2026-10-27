#!/usr/bin/env python3
"""Publish the cache-gated H73-BW stop and keep the prior H73-PM file inspection-only.

The H73-PM model remains a failed, unscored research result; this block selector is blocked before
fit because shared caches are absent. This synchronization helper never creates a model, TIFF, or score.
"""
from __future__ import annotations

import html

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
    """Retired: the old 2026-10-26 banner must not overwrite current status."""
    print("Historical H73 banner publisher retired; use scripts/build_site.py for current status.")


if __name__ == "__main__":
    main()
