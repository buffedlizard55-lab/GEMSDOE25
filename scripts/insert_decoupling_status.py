#!/usr/bin/env python3
"""Idempotently put the current negative research result first on generated pages."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "registry/run_card_decoupling_2026-10-29.json"
START, END = "<!-- DECPL-STATUS-START -->", "<!-- DECPL-STATUS-END -->"


def apply() -> None:
    card = json.loads(CARD.read_text())
    tif = ROOT / card["file"]
    if hashlib.sha256(tif.read_bytes()).hexdigest() != card["sha256"]:
        raise ValueError("research download does not match run-card hash")
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html",
                "docs/submission-guide.html", "docs/nine-site-brief.html"):
        path = ROOT / rel
        html = path.read_text()
        if START in html:
            before, rest = html.split(START, 1)
            if END not in rest:
                raise ValueError(f"unterminated status block in {path}")
            html = before + rest.split(END, 1)[1]
        prefix = "docs/" if rel == "index.html" else ""
        evidence = "" if rel == "index.html" else "../"
        banner = f'''{START}<aside class="current-status" aria-label="29 October decision">
<strong>29 OCT 2026 · NEW RESEARCH GEOTIFF · DOWNLOAD FOR INSPECTION: YES · SUBMIT: NO — DO NOT SUBMIT</strong>
<p><a download href="{prefix}downloads/{tif.name}">Download new mag/TC-decoupling GeoTIFF (research only) →</a>
File: <code>{tif.name}</code> · SHA-256 <code>{card['sha256']}</code>.</p>
<p>Local format check: one float32 band, EPSG:32611, 3730×3292, template transform, all 12,279,160 values finite in [0,1] (zero outside). 8,137 positive dots. Distinct by SHA and below the strict dot/rank duplicate limits across 151 aligned pinned references (max 3-px overlap 69.89% vs r13; surface |Spearman| max 0.139); <b>one pinned historical file is off-grid and remains uncomparable</b>. Global novelty is NOT certified.</p>
<p><b>Estimated organizer score: UNKNOWN — no calibrated projection or organizer receipt.</b> Invalid HOLDOUT-DTI diagnostic: 0.00000 (95% CI [0,0], 23,923 withheld-positive occurrences; evaluator gems25.metric.dti_binary α=.2, β=.8, 300 m triangular); archived H35 raster evaluated on the same draws: 0.01946 (95% CI [0.01601,0.02235]). <b>This is NOT a valid holdout:</b> the full catalogue was used for dot placement, including withheld pixels. The candidate failed validation for selector review. Do not use a weekly slot.</p>
<p>Geological mechanism (unconfirmed): buried magnetic contact beneath apparently uniform TC cover; a lithologic/intrusive contact can mimic a fault. Band-6 TC metadata disagrees with previous numeric identification as radiometric total count; physical semantics require confirmation. <a href="{evidence}registry/run_card_decoupling_2026-10-29.json">Run card</a> · <a href="{evidence}knowledge/50_preregistered_decoupling_feasible_allocation_2026-10-29.md">Method and correction</a> · <a href="{prefix}submission-guide.html">Submission checklist</a>. Suggested distinguishing note (do not enter until cleared): <code>{card['note']}</code>.</p>
</aside>{END}'''
        marker = '<main class="wrap">'
        if marker not in html:
            raise ValueError(f"missing main in {path}")
        html = html.replace(marker, marker + banner, 1)
        path.write_text(html)


if __name__ == "__main__":
    apply()
