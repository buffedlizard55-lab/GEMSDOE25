#!/usr/bin/env python3
"""Render the current, evidence-led decision without upgrading archives into submissions."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
e = html.escape


def read_json(path: str):
    return json.loads((ROOT / path).read_text())


def current_banner(prefix: str) -> str:
    old = read_json("registry/run_card_h73_2026-10-26.json")["holdout_dti"]
    return f'''<!-- H73-BW-2026-10-26 --><aside class="current-status" aria-label="Current decision">
<strong>27 OCT 2026 · NO NEW TIF · H73-BW: BLOCKED BEFORE FIT · RESEARCH-ARCHIVE DOWNLOAD: YES (INSPECTION ONLY) · COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT</strong>
<span>Current preregistered lane stopped before model fitting: at least 82.70% overlap is unavoidable at its fixed budget.
The earlier H73-PM HOLDOUT-DTI {old['pm_deapron_pooled']:.5f} vs same-run H35 {old['ctrl_h35_pooled']:.5f}
(evaluator {e(old['evaluator'])}; {old['withheld_positive_occurrences']:,} withheld positive occurrences;
95% CI [{old['pm_deapron_ci95'][0]:.5f}, {old['pm_deapron_ci95'][1]:.5f}]) was a negative proxy, not an organizer score.
Its literal lane audit flags 100% of dots within 3 px of the r13 lattice. Estimated competition score: UNKNOWN (not calibrated).</span>
<a href="{prefix}current-review.html">Review decision and evidence →</a></aside>'''


def render_body(root_page: bool = False) -> str:
    card = read_json("registry/run_card_2026-10-27.json")
    focus = read_json("evidence/focus_winners_reaudit_2026-10-27.json")
    geometry = read_json("evidence/lane_preflight_2026-10-27.json")
    h78 = read_json("registry/run_card_h78_2026-10-27.json")
    h71 = read_json("registry/run_card_h71_2026-10-26.json")["holdout_dti"]
    subs = read_json("registry/submissions.json")["files"]
    archive = {s["content_id"]: s for s in subs if s["file"].endswith("-zeros.tif")}
    download = "docs/downloads/" if root_page else "downloads/"
    repo = "" if root_page else "../"
    h78_name = h78["submission"]["name"]
    descriptions = {
        "GEMSDOE24": "Different positive mask in this nine-file comparison; H19-5 D1.5 lineage.",
        "GEMSDOE25": "Exact-mask duplicate of GEMSDOE30 (D2.8).",
        "GEMSDOE27": "Different mask; D1.5 topographic gap-closure lineage.",
        "GEMSDOE28": "Rung30 winner differs from GEMSDOE31; GEMSDOE28's lower-scoring R1 is an Exact-mask duplicate of GEMSDOE31 (R1).",
        "GEMSDOE30": "Exact-mask duplicate of GEMSDOE25 (D2.8).",
        "GEMSDOE31": "R1 equals GEMSDOE28's lower-scoring R1, not its Rung30 winner.",
        "GEMSDOE32": "B2 is D2.8 after removing pixels within 200 m of the mirrored catalogue; historical, not new.",
        "GEMSDOE33": "Different mask in this nine-file comparison; not cleared against the full registry.",
        "GEMSDOE36": "Contains the B2 mask plus 1,200 additional positive pixels.",
    }
    winner_rows = []
    for row in sorted(focus["sites"], key=lambda r: -r["owner_reported_score"]):
        winner_rows.append(
            f'<tr><th><a href="{e(row["site_url"])}">{e(row["site"])}</a></th>'
            f'<td><a download href="{e(row["download_url"])}"><code>{e(row["file"])}</code></a>'
            f'<small>{row["footprint_positive_pixels"]:,} positive pixels; pinned public mirror</small></td>'
            f'<td>{row["owner_reported_score"]:.4f}<small>OWNER-REPORTED · no organizer receipt</small></td>'
            f'<td>{e(descriptions[row["site"]])}</td><td><b>NO — historical file</b></td></tr>'
        )
    archive_rows = []
    for cid, explanation in (
        ("3751606e1ce5", "H74: strict lane failed; H35 holdout gate failed."),
        ("88bbebfe79b4", "H72-3: H35 FAIL · STRICT LANE FAIL."),
        ("1d7c1e9ea55f", "H72-CF: holdout and literal lane failed."),
        ("3646faf70507", "Objective diagnostic: no slot approval."),
        ("1b7533ebb62b", "H73-PM: strict lane and H35 holdout failed."),
    ):
        item = archive[cid]
        archive_rows.append(
            f'<tr><td><a download href="{download}{e(item["file"])}"><code>{e(item["file"])}</code></a>'
            f'<small>Research identifier: {e(item["note"])}</small></td>'
            f'<td>NOT ESTIMATED</td><td>{e(explanation)}</td><td><b>NO — DO NOT SUBMIT</b></td></tr>'
        )
    bounds = "".join(f"<tr><td>{x['dots']:,}</td><td>{x['minimum_overlap']:.2%}</td><td>Impossible</td></tr>"
                     for x in geometry["cases"])
    body = f'''<section class="hero"><p class="eyebrow">RESEARCH DECISION BRIEF / 27 OCTOBER 2026</p>
<h1>Know when to stop.</h1><p class="lead">The requested unique competition-ready TIFF remains unfulfilled. A preregistered geometric stop prevents an honest candidate at the frozen density. No model or new TIFF was produced, and no weekly slot was selected.</p>
<div class="stats"><div class="stat"><b>Research-archive download: YES</b><span>Inspection/testing only.</span></div>
<div class="stat"><b>Competition-ready TIF: NO</b><span>OK TO SUBMIT: NO — DO NOT SUBMIT.</span></div>
<div class="stat"><b>Estimated competition score: UNKNOWN</b><span>No defensible leaderboard estimate is available.</span></div></div></section>
<section class="review-decision"><span class="badge b-bad">LITERAL LANE FAIL · NOT SUBMISSION-ELIGIBLE</span>
<h2>Existing H78 TIFF: format pass, not unique under the lane rule</h2>
<p><a download href="{download}{e(h78_name)}"><code>{e(h78_name)}</code></a> · <a download href="{download}{e(h78['submission']['zip'])}">matching ZIP</a> · <b>research inspection only; DO NOT SUBMIT</b>.</p>
<p>Local exact-file audit: one float32 band, EPSG:32611, 3730 × 3292, expected 100 m transform; all pixels finite in [0,1], zero outside, 43,550 positive pixels and zero positives on the mirrored catalogue. ZIP content matches. SHA-256 <code>{e(h78['validator_output']['sha256'])}</code>.</p>
<p><b>100% of its dots are within 3 px of the registered r13 lattice; threshold 70%.</b> Full-footprint Spearman against that reference is {h78['correlation_overlap_vs_registry']['spearman_full_footprint_vs_lattice']:.6f}; the registry-wide audit is incomplete. No density waiver applies. The previous H78 holdout, forecast and submit-ready statements were unsupported and are retracted.</p>
<p>The earlier portal error “Predicted values must be in range [0, 1]” is consistent with NaNs inside an earlier owner-mirrored footprint. Zero padding also passes a stricter local whole-array range check, but the official format specifies null/NaN outside the bounds; organizer acceptance of zero padding is unknown. Format does not prove novelty, performance, or approval.</p>
<p>The <a href="{repo}scripts/verify_candidate_independent.py">automated independent validator</a> checks the pinned template, labels, exact raster and ZIP without human inspection; a failed check exits nonzero. This does not replace the separate lane and scientific checks.</p>
<p><a href="{repo}evidence/h78_independent_reaudit_2026-10-27.json">Format/ZIP audit</a> · <a href="{repo}evidence/h78_literal_lane_reaudit_2026-10-27.json">Literal lane audit</a> · <a href="{repo}knowledge/38_h78_mhscf_and_phd_focus_sites_analysis_2026-10-27.md">Correction and explanation</a> · <a href="{repo}registry/run_card_2026-10-27.json">Current JSON run card</a></p></section>
<section id="lane-feasibility"><h2>Why the frozen continuation stopped</h2>
<p>The mirrored template, labels and r13 grid were hash-checked. Only <b>6,514</b> eligible pixels are outside the lattice's 3-pixel halo. At fixed budget K, at least max(0, K − 6,514) dots overlap. For 37,654 dots the minimum is <b>82.70%</b> — a strict failure, before placement or fitting.</p>
<div class="table-scroll"><table><thead><tr><th>Fixed dot budget K</th><th>Minimum overlap</th><th>70% gate</th></tr></thead><tbody>{bounds}</tbody></table></div>
<p>At most 21,713 dots are not ruled out by this <em>one necessary bound</em>; smaller budgets are not automatically feasible or competitive. This is computed geometry, not HOLDOUT-DTI. No density exception or movement into uncovered slivers was used. <a href="{repo}evidence/lane_preflight_2026-10-27.json">Fresh preflight receipt</a>.</p></section>
<section><h2>Nine historical winners: files, claims, and uniqueness</h2>
<p>Highest <em>supplied</em> result for each requested site, not an exhaustive live leaderboard. Values are OWNER-REPORTED, not ORGANIZER-CONFIRMED; none is eligible as a new submission. New-file estimated competition score: <b>Not estimated</b>.</p>
<div class="table-scroll"><table><thead><tr><th>Site</th><th>Historical file for learning only</th><th>Historical score</th><th>Positive-mask uniqueness / lineage</th><th>OK to submit?</th></tr></thead><tbody>{''.join(winner_rows)}</tbody></table></div>
<p>The pinned downloads were verified against public GitHub blob IDs. <a href="{repo}evidence/focus_winners_reaudit_2026-10-27.json">Pixel audit</a> · <a href="{repo}evidence/focus_source_links_2026-10-27.json">Source verification</a> · <a href="{repo}registry/review_passes_2026-10-27.json">Three review passes</a>. Conflicting overall-leader claims 0.3195 and 0.4413 remain unverified.</p></section>
<section><h2>Why GEMSDOE32 B2 may have done well</h2>
<p>Its 0.2778 is the strongest supplied OWNER-REPORTED result. B2 equals D2.8 with 6,436 dots within 200 m of known faults removed. Sparse dots reduce redundant mass; selective pruning might remove more false-positive mass than nearby triangular-kernel credit. This is a plausible consequence of the local scoring formula, not proof of hidden-label causation or an organizer-confirmed score. A unique method might beat it, but there is no evidence or valid forecast that this continuation does.</p></section>
<section><h2>Four ranked geological hypotheses — not newly tested</h2>
<div class="table-scroll"><table><thead><tr><th>Rank and layers</th><th>Physical signature and missing-fault rationale</th><th>Named non-fault mimic</th><th>Novelty, expected benefit and cost</th></tr></thead><tbody>
<tr><td>1. Root × scarp: magnetic/gravity gradients and H74 subsurface features × LiDAR/DEM</td><td>Separately fitted subsurface edge and scarp experts corroborate a buried fault root and subtle surface trace.</td><td>Alluvial fan margin crossing a lithologic contact; lake shoreline</td><td>Separate experts and blocked testing extend H74; related H36 PoE already exists. Benefit unknown; medium-high cost.</td></tr>
<tr><td>2. Signed paired edges: GeoDAWN magnetics and gravity</td><td>Paired edge polarity and migration at two continuation scales could mark a covered fault-bounded block.</td><td>Intrusive sheets, volcanic contacts, survey seams</td><td>Tests edge pairing, not isolated edge magnitude. Benefit unknown; high cost.</td></tr>
<tr><td>3. Drainage/provenance boundary: DEM, GeoDAWN K/Th/U</td><td>Repeated compositional transitions across adjacent divides may reveal a buried structural barrier.</td><td>Fan avulsion, source-rock contacts, drainage capture</td><td>Catchment recurrence differs from local ROD translation. Benefit unknown; high cost; drainage graph not built.</td></tr>
<tr><td>4. Temperature residuals: well/spring observations, elevation and gravity</td><td>Elevation-conditioned temperature residuals aligned with basement edges might flag a concealed fault conduit.</td><td>Meteoric groundwater circulation, sampling bias</td><td>Residual modeling differs from raw proximity; benefit unknown; medium-high cost and sparse-data risk.</td></tr></tbody></table></div>
<p>Ranking is qualitative, not a score forecast. The unspecified “single method paragraph” was not identifiable; rank 1 follows the previous H74 handoff provisionally, not an owner-confirmed lane. No blocked hide-and-recover experiment or per-feature canary was run because the preregistered stop occurred first. <a href="{repo}knowledge/39_lane_hypotheses_and_preflight_2026-10-27.md">Frozen hypotheses, implementation and sources</a>.</p></section>
<section id="h73-status"><h2>Prior research archives, not submission candidates</h2>
<p><b>OK TO DOWNLOAD: YES</b> for inspection-only research archives; <b>OK TO SUBMIT: NO — DO NOT SUBMIT.</b> OK to spend a weekly slot: NO. A different filename or outside-footprint variant is not a new prediction. The density-aware statistic is diagnostic only.</p>
<div class="table-scroll"><table><thead><tr><th>Archived file</th><th>Estimated competition score</th><th>Unique under literal lane rule?</th><th>Decision</th></tr></thead><tbody>{''.join(archive_rows)}</tbody></table></div>
<p>Archived H72-3 research artifact only: prior H71 HOLDOUT-DTI {h71['pooled_dti']:.6f}, evaluator <code>{e(h71['evaluator_version'])}</code>, {h71['withheld_positives']:,} withheld positives, 95% CI [{h71['ci_95'][0]:.6f}, {h71['ci_95'][1]:.6f}]; not an organizer score. Its lane result was 100% within 3 px of the registered r13 lattice; threshold 70%.</p>
<p><b>H73-BW BLOCKED BEFORE FIT</b>: H73-BW diagnostic candidate: <b>no file produced</b>. The earlier preflight recorded eight missing cache artifacts; after the restored/rebuilt stack, the H34 sidecar and names are still missing. No H73-BW fit or HOLDOUT-DTI exists. <a href="{repo}evidence/h73_bw_cache_rebuild_2026-10-27.json">Current cache receipt</a> · <a href="{repo}registry/run_card_h73_bw_2026-10-26.json">Historical run card</a> · <a href="{repo}knowledge/30_executive_summary_and_apfl_outcomes_2026-10-26.md">APFL piedmont-flexure completion (prior negative)</a>.</p></section>
<section id="how-to-submit"><h2>Submission checklist — only after a separate selector approves</h2>
<ol><li>Preregister a feasible lane; compare the full surface before placement and final dots to the complete declared registry. Stop for |Spearman| &gt; 0.90 or &gt;70% overlap within 3 px of any one reference.</li>
<li>Test each feature alone for leakage, hide whole buffered fault segments, derive catalogue features only from visible faults, mask visible pixels exactly, and report pooled HOLDOUT-DTI with evaluator, withheld positives and 95% CI against the same-run control. Confirm on fresh draws.</li>
<li>Independently validate the exact file's finite footprint, [0,1] values, single-band grid/CRS/transform and ZIP; decide the outside-footprint convention with organizer guidance. A separate selector must respect the weekly cap. No selector approval exists now.</li>
<li>Only if all gates and selector pass, use the official competition interface and a note of at most 140 characters. Current research note: <code>{e(card['submission_note'])}</code> (not a submission instruction).</li></ol>
<p><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official reference code</a> · <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a> · <a href="https://www.usgs.gov/3d-elevation-program/about-3dep-products-services">USGS 3DEP</a> · <a href="https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and">USGS-hosted Great Basin play-fairway report</a>. Source availability and public mirror hashes do not prove provenance or performance.</p></section>'''
    return body


def readme_status() -> str:
    return '''<!-- CURRENT-REVIEW-2026-10-27 -->
## Current decision — 2026-10-27

**Research-archive download: YES (inspection/testing only) · Competition-ready TIF: NO · OK TO SUBMIT: NO · weekly slot: NO — DO NOT SUBMIT.**

No new TIFF or model was produced. The preregistered 37,654-dot budget is geometrically forced to overlap the registered r13 lattice by at least **82.70%** within three pixels, above the allowed 70%. No density exception was used. The requested unique submission remains unfulfilled. [Preflight](evidence/lane_preflight_2026-10-27.json) · [ranked hypotheses and frozen design](knowledge/39_lane_hypotheses_and_preflight_2026-10-27.md) · [current JSON run card](registry/run_card_2026-10-27.json).

The existing [H78 zero-outside TIFF](docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif) passes a local format audit only, but **100% of its 43,550 dots overlap the r13 halo; DO NOT SUBMIT**. Prior H78 holdout, score estimate and submit-ready claims are retracted as unsupported. [Correction](knowledge/38_h78_mhscf_and_phd_focus_sites_analysis_2026-10-27.md) · [format audit](evidence/h78_independent_reaudit_2026-10-27.json) · [literal lane re-audit](evidence/h78_literal_lane_reaudit_2026-10-27.json). The reported portal error “Predicted values must be in range [0, 1]” is consistent with earlier NaNs inside the mirrored footprint; the exact organizer validation behavior and acceptance of zero outside are unverified.

GEMSDOE32's **0.2778 is OWNER-REPORTED**, not organizer-confirmed. B2 is exactly D2.8 pruned of 6,436 pixels within 200 m of the catalogue; sparsity and selective pruning could explain improved local credit/false-positive balance, but hidden-label causation and future scores are unknown. A fresh nine-site audit also finds GEMSDOE28's 0.2710 Rung30 winner differs from GEMSDOE31; only its lower-scoring R1 is identical to GEMSDOE31. [Executive summary & downloads](docs/executive-summary.html) · [pixel and source audit](evidence/focus_winners_reaudit_2026-10-27.json).

Prior archives, including [H74](docs/downloads/gems25-h74-rmps-subsurf-catfree-b2-37654-20261026-3751606e1ce5-zeros.tif) and [H72-3](docs/downloads/gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif), remain inspection-only and are not lane-cleared; [H74 prior analysis](knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md) · [H74 run card](registry/run_card_h74_2026-10-26.json). Read the standing owner brief below every session; Maximize P(Win) and Own the Outcome do not justify submitting a failed candidate.

'''


def main() -> None:
    # Reuse the single generator so all public entry points stay in sync.
    try:
        from build_site import main as build
    except ImportError:
        from scripts.build_site import main as build
    build()


if __name__ == "__main__":
    main()
