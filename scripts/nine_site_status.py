#!/usr/bin/env python3
"""Nine-focus-site brief (GEMSDOE24/25/27/28/30/31/32/33/36), generated only from evidence receipts.

Inputs (all COMPUTED on SHA-256-pinned owner-mirror bytes, 2026-10-28):
  * evidence/nine_site_top_files_2026-10-28.json   (scripts/audit_nine_site_top_files.py)
  * evidence/portal_safety_sweep_2026-10-28.json   (scripts/audit_portal_safety.py)
  * evidence/lane_bound_r13_2026-10-28.json        (scripts/audit_r13_lane_bound.py)

Scores are OWNER-REPORTED claims from the brief. No organizer receipt exists here, and no calibrated
competition estimate exists, so every estimate column says UNKNOWN. Nothing in this module uploads,
selects a slot or clears novelty; every file is marked DO NOT SUBMIT.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
e = html.escape

# Public owner pages (from registry/top_scorer_sources.json), used only as links for manual review.
SITE_URL = {
    "GEMSDOE24": "https://buffedlizard55-lab.github.io/GEMSDOE24/",
    "GEMSDOE25": "https://buffedlizard55-lab.github.io/GEMSDOE25/",
    "GEMSDOE27": "https://buffedlizard55-lab.github.io/GEMSDOE27/",
    "GEMSDOE28": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
    "GEMSDOE30": "https://buffedlizard55-lab.github.io/GEMSDOE30/",
    "GEMSDOE31": "https://buffedlizard55-lab.github.io/GEMSDOE31/docs/",
    "GEMSDOE32": "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html",
    "GEMSDOE33": "https://buffedlizard55-lab.github.io/GEMSDOE33/",
    "GEMSDOE36": "https://buffedlizard55-lab.github.io/GEMSDOE36/docs/",
}
FOCUS = list(SITE_URL)


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())


def load() -> dict:
    top = _load("evidence/nine_site_top_files_2026-10-28.json")
    sweep = _load("evidence/portal_safety_sweep_2026-10-28.json")
    lane = _load("evidence/lane_bound_r13_2026-10-28.json")
    rows = {r["site"]: r for r in top["rows"]}
    return dict(top=top, sweep=sweep, lane=lane, rows=rows)


def _twins(rows: dict, site: str) -> list[str]:
    """Other audited rasters with an identical positive dot set (exact duplicate, not near)."""
    me = rows[site]["dot_set_sha256_16"]
    return [s for s, r in rows.items() if s != site and r["dot_set_sha256_16"] == me]


def site_table(d: dict) -> list[dict]:
    rows, top = d["rows"], d["top"]
    out = []
    for site in FOCUS:
        r = rows[site]
        twins = _twins(rows, site)
        maxj = top["max_jaccard_vs_other_focus_top"][site]
        portal_safe = r["outside_convention"] == "zeros"
        if twins:
            uniq = f"NO — exact dot-set twin of {', '.join(twins)} (same {r['positives']:,} dots)"
        elif maxj >= 0.90:
            uniq = f"NO — near-duplicate of another focus top (max Jaccard {maxj:.3f})"
        else:
            uniq = f"Distinct from the other eight focus tops (max Jaccard {maxj:.3f}); still a previous submission family"
        if portal_safe:
            fmt = "zeros outside — portal-safe format (no NaN, all cells in [0, 1])"
        else:
            fmt = "NaN outside — portal-REJECTED convention (fails whole-array [0, 1] check)"
        if portal_safe:
            ok = ("NO — already a scored submission of this site (owner-reported). Do not copy a previous submission; "
                  "learning reference only")
        else:
            ok = ("NO — NaN-outside convention (the portal rejects it); also a previous submission of this site "
                  "(owner-reported)")
        out.append(dict(site=site, slug=r["slug"], file=r["file"], score=r["owner_reported_score"],
                        positives=r["positives"], sha=r["sha256"], fmt=fmt, uniq=uniq, ok=ok,
                        portal_safe=portal_safe, url=SITE_URL[site], maxj=maxj))
    return out


def readme_block() -> str:
    d = load()
    lane = d["lane"]
    return f"""## Nine-site brief (28 October 2026) — what to download, and why nothing is OK to submit

**OK TO DOWNLOAD AND SUBMIT: NO — no file in this repository or on the nine focus sites is cleared.**
Estimated competition score: **UNKNOWN / NOT ESTIMATED** for every file (no calibrated projection exists).

* **Portal error explained (verified):** a NaN-outside GeoTIFF fails the portal's whole-array range check
  (`NaN` fails every `0 <= x <= 1` test). The reference solution writes finite values only
  (`unet-mc-cv-reference-solution.ipynb` at pinned commit `aebe92f`; `evidence/official_reference_2026-10-26.json`). The validator now enforces this (`portal_all_cells_finite_in_0_1`).
  Of 60 GeoTIFFs in `docs/downloads/`, {d['sweep']['portal_safe']} are portal-safe (zeros outside) and {d['sweep']['portal_rejected_convention']} are NaN-outside.
* **The 0.2778 file (GEMSDOE32 B2) is a pruned copy of the 0.2708 h27-4 raster:** its 37,654 dots are a strict subset of
  the 40,199 dots in `gemsdoe28-h27-4-r1-solo` (2,545 removed; Jaccard {d['top']['b2_lineage']['jaccard']:.4f}).
  It is portal-safe, has zero dots on the labelled catalogue, and is a previous submission, so it may not be copied.
* **Lane bound (r13, verified):** at 37,654 dots at least **{lane['min_overlap_at_37654_dots']*100:.2f}%** of dots must sit within 3 px of r13.
  The literal 70% cap is reachable only at or below **{lane['max_dots_with_min_overlap_at_most_0_70']:,}** dots. This is an owner decision.
* Full table, per-file links and receipts: [docs/nine-site-brief.html](docs/nine-site-brief.html) ·
  [nine-site receipt](evidence/nine_site_top_files_2026-10-28.json) · [portal sweep](evidence/portal_safety_sweep_2026-10-28.json) ·
  [r13 bound](evidence/lane_bound_r13_2026-10-28.json).

"""


def banner(prefix: str) -> str:
    """Homepage / executive banner (HTML). Never raises: a missing receipt must not break the build."""
    try:
        d = load()
    except Exception:  # pragma: no cover - build must survive a missing receipt
        return ""
    lane = d["lane"]
    return f"""<aside class="current-status" aria-label="Nine-site brief" style="border-color:#b45309">
<strong>NINE-SITE BRIEF · 28 OCT 2026 · OK TO DOWNLOAD AND SUBMIT: NO</strong>
<span>No file on the nine focus sites is cleared. Estimated competition score: UNKNOWN. NaN-outside files fail the portal's [0, 1] check;
the 0.2778 GEMSDOE32 file is a pruned copy of a 0.2708 raster and is a previous submission. At 37,654 dots, at least
{lane['min_overlap_at_37654_dots']*100:.2f}% must sit within 3 px of the r13 lattice (literal cap 70%).</span>
<a href="{prefix}nine-site-brief.html">Nine-site table, per-file status and receipts →</a></aside>"""


def page_body(d: dict | None = None) -> str:
    d = d or load()
    top = d["top"]
    tbl = []
    for r in site_table(d):
        tbl.append(
            "<tr>"
            f"<td><strong>{e(r['site'])}</strong></td>"
            f"<td><code>{e(r['file'])}</code><br><span class='small'>sha256 <code>{e(r['sha'][:16])}…</code> · "
            f"<a href='{e(r['url'])}'>owner page</a></span></td>"
            f"<td class='num'>{r['score']:.4f}<br><span class='small'>OWNER-REPORTED</span></td>"
            f"<td>{e(r['fmt'])}</td>"
            f"<td>{e(r['uniq'])}</td>"
            "<td class='num'>UNKNOWN</td>"
            f"<td><strong>{e(r['ok'])}</strong></td>"
            "</tr>"
        )
    b2 = top["b2_lineage"]
    lin = top["lineage_steps"]
    top = dict(top, d2_8_to_h27_removed=lin["d2_8_to_h27_4_removed"], d2_8_dots_within_2px_catalogue=lin["d2_8_dots_within_2px_catalogue"])
    return f"""<div class="hero"><h1>Nine-site brief · GEMSDOE24/25/27/28/30/31/32/33/36</h1>
<p class="lead">Which file to download, its score status, and whether it is unique. <strong>OK TO DOWNLOAD AND SUBMIT: NO.</strong>
No file is cleared. Every score below is an owner-reported claim, not an organizer receipt, and no competition estimate exists.</p></div>
<section><h2>Summary table</h2>
<table><thead><tr><th>Site</th><th>Top file (owner mirror)</th><th class='num'>Score</th><th>Portal format</th>
<th>Unique vs the other focus tops?</th><th class='num'>Estimated competition score</th><th>OK to download and submit?</th></tr></thead>
<tbody>{''.join(tbl)}</tbody></table>
<p class="small">Each raster was re-hashed against its pin ({sum(r['sha256_matches_pin'] for r in top['rows'])} of {len(top['rows'])} match: the nine tops plus one owner-listed sibling). Format and dot statistics are computed by
<code>scripts/audit_nine_site_top_files.py</code>; the portal sweep is <code>scripts/audit_portal_safety.py</code>.
Uniqueness is only among these nine tops and their owner-listed siblings; the repository's wider lane audit is a separate receipt.</p></section>
<section><h2>Why the portal said "Predicted values must be in range [0, 1]"</h2>
<ul>
<li>NaN fails every <code>0 &lt;= x &lt;= 1</code> test. A NaN-outside GeoTIFF therefore fails a whole-array range check.</li>
<li>The official reference solution writes its output as a finite float raster with no NaN and no nodata tag (verified in
<a href="https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb">unet-mc-cv-reference-solution.ipynb</a> at pinned commit aebe92f).</li>
<li>The owner-mirror <code>sample_submission.tif</code> uses NaN outside its 5,167,373-pixel footprint, which conflicts with the portal's rejection of NaN.
This is <strong>flagged for owner review</strong>; it is not resolved by any organizer receipt.</li>
<li>The fix in this repository: the validator now requires every cell to be finite and in [0, 1]
(<code>portal_all_cells_finite_in_0_1</code>). Use the <code>-zeros.tif</code> file if a file is ever cleared.</li>
</ul></section>
<section><h2>How GEMSDOE32 reached 0.2778 (verified receipts; mechanism is an inference)</h2>
<ul>
<li>The file is binary: {d['rows']['GEMSDOE32']['positives']:,} dots at value 1.0; zeros elsewhere; 0 dots on the labelled catalogue.</li>
<li><strong>Nested lineage (set inclusion verified on the pinned rasters):</strong>
GEMSDOE32 B2 (37,654 dots, 0.2778) ⊂ GEMSDOE28 h27-4-r1-solo (40,199, 0.2708) ⊂ GEMSDOE25 d2-8 (44,090, 0.2600).
Only dots were deleted at each step: {top['d2_8_to_h27_removed']:,} dots, then {b2['dots_in_h27_4_not_in_b2']:,} dots.</li>
<li><strong>What was deleted:</strong> all {top['d2_8_to_h27_removed'] + b2['dots_in_h27_4_not_in_b2']:,} removed dots lie 1 to 2 pixels (about 100–200 m) from a labelled catalogue pixel.
B2 keeps zero dots within 2 px of the catalogue; d2-8 had {top['d2_8_dots_within_2px_catalogue']:,} such dots.
The owner-reported score rose 0.2600 → 0.2708 → 0.2778 across these two deletions.</li>
<li><strong>Mechanism is contested, not settled.</strong> The repository's record of the staff clarification (<code>knowledge/03</code>; not re-fetched here,
because AGENTS.md rule 3 bars automated access to drivendata.org forums) says near-known wrong pixels are fully penalised. That favours deletion.
The same record says test labels include corrections or modifications within 300 m of known traces. That favours keeping them.
The catalogue-gap holdout cannot test this (<code>IR-25-HOLDOUT-DOES-NOT-TEST-PRUNING</code>, <code>knowledge/17</code> §2), so the question is open.</li>
<li><strong>B2 is already widely submitted (owner-reported):</strong> two re-hosts carry the same SHA prefix <code>c55bafc4</code> and score 0.2778 (GEMSDOE50, GEMSDOE58),
and 15 B2 micro-variants score 0.2720–0.2775 (<code>evidence/b2_microvariants.json</code>, all below B2).
A copy of B2 is therefore a previous submission on several sites.</li>
<li><strong>Lane consequence (arithmetic):</strong> B2 is a registry reference in the H75 lane receipt (<code>docs/downloads/lane-gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.json</code>, entry <code>g32_h33-2-b2_0.2778.tif</code>).
Any subset of B2 has 100% of its dots within 3 px of B2 itself, so further pruning of B2 is a literal lane duplicate.
Escaping the lane needs dots moved away from the B2 family, which is a different (untested) science question.</li>
<li><strong>Within-family similarity:</strong> the nine focus tops are near-duplicates of one another (max Jaccard in the table).
The leaderboard-level differences are differences within one dot family, not a new geological discovery.</li>
</ul></section>
<section><h2>Flags for owner review</h2>
<ul>
<li>The brief lists leaderboard values of <strong>0.4413</strong> and <strong>0.3195</strong> as the current top. Neither is ORGANIZER-CONFIRMED here.</li>
<li>The 0.2778 value is OWNER-REPORTED. Its portal acceptance is unconfirmed.</li>
<li>The r13 lattice sets a literal lower bound on overlap that exceeds the 70% cap at 37,654 dots. Any change to the lane rule is an owner decision and must be recorded there.</li>
</ul></section>"""
