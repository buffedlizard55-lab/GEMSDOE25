#!/usr/bin/env python3
"""Prepend the H73-PM status banner to docs/index.html and refresh the README decision block.

Idempotent; reads every number from registry/run_card_h73_2026-10-26.json. Historical page
content is preserved verbatim below the banner (tests lock several historical strings).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK = "H73-PM-2026-10-26"


def main() -> None:
    card = json.loads((ROOT / "registry" / "run_card_h73_2026-10-26.json").read_text())
    h = card["holdout_dti"]
    zfile = card["submission_name"]
    zzip = zfile.replace(".tif", ".zip")
    banner = (
        f'<!-- {MARK} --><aside class="current-status" aria-label="H73-PM status">\n'
        f"<strong>26 OCT 2026 · NEW UNIQUE RESEARCH TIF (H73-PM) · OK TO DOWNLOAD: YES (INSPECTION ONLY) · OK TO SUBMIT: NO — DO NOT SUBMIT</strong>\n"
        f"<span>Propensity-matched H35 GeoTIFF <code>{card['content_id']}</code> ({card['positive_pixels']:,} dots) is format-valid "
        f"and density-aware UNIQUE ({100 * card['correlation_overlap_vs_registry']['focus_winners']['b2_overlap']:.1f}% of dots within 3 px of GEMSDOE32 B2), "
        f"but HOLDOUT-DTI {h['pm_deapron_pooled']:.5f} failed the frozen slot gate vs same-run CTRL_H35 {h['ctrl_h35_pooled']:.5f} "
        f"(paired {h['paired_gain_vs_h35']:+.5f}). HOLDOUT-DTI is a catalogue-gap proxy, not a leaderboard estimate. "
        f'Note ({card["note_chars"]} chars, identification only): <code>{card["note"]}</code></span>\n'
        f'<a href="downloads/{zfile}" download>↓ Download {zfile} (inspection only)</a> · '
        f'<a href="downloads/{zzip}" download>↓ ZIP</a> · '
        f'<a href="data/run_card_h73_2026-10-26.json" download>↓ H73 run card JSON</a> · '
        f'<a href="../knowledge/33_h73_outcomes_and_executive_summary_2026-10-26.md">H73 outcomes &amp; nine-site executive summary →</a></aside>'
    )
    page_path = ROOT / "docs" / "index.html"
    page = page_path.read_text()
    if MARK not in page:
        anchor = '<main class="wrap">'
        assert anchor in page
        page = page.replace(anchor, anchor + banner, 1)
        page_path.write_text(page)
        print("docs/index.html banner inserted")
    else:
        print("docs/index.html banner already present")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    if MARK not in readme:
        block = (
            f"<!-- {MARK} -->\n"
            f"**H73-PM update (2026-10-26, this branch):** unique research GeoTIFF "
            f"[`{zfile}`](docs/downloads/{zfile}) (content id `{card['content_id']}`, {card['positive_pixels']:,} dots) — "
            f"**OK to download: YES (inspection) · OK to spend a weekly slot: NO — DO NOT SUBMIT.** "
            f"Propensity-matched training restored B2-like far-field geometry and beat the catalogue-free control, "
            f"but pooled HOLDOUT-DTI {h['pm_deapron_pooled']:.5f} failed the frozen slot gate vs same-run CTRL_H35 "
            f"{h['ctrl_h35_pooled']:.5f} (paired {h['paired_gain_vs_h35']:+.5f}). "
            f"[H73 outcomes & nine-site executive summary](knowledge/33_h73_outcomes_and_executive_summary_2026-10-26.md) · "
            f"[H73 run card](registry/run_card_h73_2026-10-26.json) · [pre-registration](knowledge/32_preregistered_h73_pm_2026-10-26.md). "
            f"Next required instrument: 25-km block-withheld selector (knowledge/33 §4). No weekly slot was used.\n\n"
        )
        marker = "## Current decision — 2026-10-26\n"
        assert marker in readme
        readme = readme.replace(marker, marker + "\n" + block, 1)
        readme_path.write_text(readme)
        print("README decision block updated")
    else:
        print("README already updated")


if __name__ == "__main__":
    main()
