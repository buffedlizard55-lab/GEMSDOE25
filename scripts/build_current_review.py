#!/usr/bin/env python3
"""Evidence-driven current executive subpage; never labels an old TIF as new."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
e = html.escape


def current_banner(prefix):
    return f'''<aside class="current-status" aria-label="Current submission status">
<strong>26 OCT 2026 · NO GATE-CLEARED COMPETITION TIFF</strong>
<span>The existing H71 file is a research artifact only: HOLDOUT-DTI failed and the literal registry lane stops on the r13 lattice. DO NOT SUBMIT.</span>
<a href="{prefix}current-review.html">Read the nine-site executive review and exact-file audit →</a></aside>'''


def render_body(root_page=False):
    focus = json.loads((ROOT/'evidence/focus_audit_2026-10-26.json').read_text())
    pairwise = json.loads((ROOT/'evidence/focus_pairwise_overlap_2026-10-26.json').read_text())
    path = ROOT/'evidence/rod_2026-10-26/run_card.json'
    card = json.loads(path.read_text()) if path.exists() else None
    audit = ROOT/'evidence/rod_2026-10-26/analysis.json'
    analysis = json.loads(audit.read_text()) if audit.exists() else None
    status = e(card['reason']) if card else 'Run incomplete. No submission file is authorized.'
    outcome = '<p>No valid HOLDOUT-DTI result is available. This is not a score of zero.</p>'
    if analysis:
        c, b = analysis['arms']['ROD'], analysis['arms']['H35']
        outcome = f'''<div class="review-metrics"><div><span>ROD · HOLDOUT-DTI</span><strong>{c['pooled_dti']:.4f}</strong>
<small>95% CI {c['ci95'][0]:.4f}–{c['ci95'][1]:.4f}</small></div>
<div><span>Same-run H35 · HOLDOUT-DTI</span><strong>{b['pooled_dti']:.4f}</strong>
<small>95% CI {b['ci95'][0]:.4f}–{b['ci95'][1]:.4f}</small></div></div>
<p>{c['withheld_positive_occurrences']:,} withheld-positive occurrences; {analysis['distinct_withheld_pixels']:,} distinct pixels.
Four buffered spatial quadrants, whole components withheld. {e(analysis['ci_method'])}.
Evaluator: <code>gems25.metric.dti_binary</code>, α=0.2, β=0.8, 300 m triangular kernel;
<a href="../evidence/rod_2026-10-26/analysis.json">version hashes and full paired results</a>.
This estimates catalogue-gap recovery, not leaderboard performance.</p>'''
    pol3_path = ROOT/'evidence/pol3_screen_2026-10-26/summary.json'
    pol3 = json.loads(pol3_path.read_text()) if pol3_path.exists() else None
    pol3_section = ''
    if pol3:
        pol3_section = f'''<section class="card"><p class="eyebrow">SEPARATE BRANCH SESSION · ONE SCREEN · NOT COMBINED WITH ROD BUDGET</p>
<h2>POL3 signed half-graben screen — negative</h2>
<p><b>HOLDOUT-DTI</b>, evaluator <code>{e(pol3['evaluator'])}</code>, draws <code>{e(str(pol3['draws']))}</code>,
{pol3['withheld_positives']:,} withheld positives. Candidate pooled <code>{pol3['candidate_pooled']['dti']:.6f}</code> vs same-run H35
<code>{pol3['control_pooled']['dti']:.6f}</code>; paired four-fold mean gain <code>{pol3['paired_fold_mean_gain']:+.6f}</code>,
95% CI <code>[{pol3['paired_fold_ci95'][0]:+.6f}, {pol3['paired_fold_ci95'][1]:+.6f}]</code>,
{pol3['positive_folds']}/4 folds positive. Feature-alone maximum AUC <code>{pol3['max_canary_auc']:.4f}</code>.
The frozen screen gate failed. No confirmation, catalogue surface, placement or POL3 raster was run; lane clearance is <b>NOT RUN</b>.
This is a catalogue-gap proxy, not an organizer score or blind-fault performance claim.</p>
<p><a href="../knowledge/27_ranked_hypotheses_and_review_2026-10-26.md">POL3 session review</a> ·
<a href="../knowledge/28_preregistered_pol3_signed_halfgraben_2026-10-26.md">frozen preregistration</a> ·
<a href="../registry/run_card_pol3_screen_2026-10-26.json">POL3 run card</a> ·
<a href="../evidence/pol3_screen_2026-10-26/summary.json">saved-cell result</a>.</p></section>'''
    subs = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
    featured = next(s for s in subs if s["role"] == "primary")
    h71 = pairwise["h71_candidate"]
    h71_holdout = h71["holdout_dti"]
    download = (
        f'<p><b>Competition-download deliverable: NOT AVAILABLE.</b> The requested gate-cleared TIF was not produced. '
        f'The existing file <code>{e(featured["file"])}</code> is retained only as a research record '
        f'(content id <code>{e(featured["content_id"])}</code>); it is not offered here as an eligible competition download.</p>'
        f'<p><b>Research artifact only — DO NOT SUBMIT.</b> HOLDOUT-DTI '
        f'<code>{h71_holdout["pooled_dti"]:.6f}</code> '
        f'(evaluator <code>{e(h71_holdout["evaluator_version"])}</code>, '
        f'withheld positives {h71_holdout["withheld_positives"]:,}, 95% CI '
        f'<code>[{h71_holdout["ci_95"][0]:.6f}, {h71_holdout["ci_95"][1]:.6f}]</code>) failed vs same-run H35. '
        f'Its surface/focus-site comparisons are below threshold, but 100% of final dots fall within 3 px of the registered r13 lattice; '
        f'the literal global lane rule stops it. This is not a score or a live-score estimate.</p>'
        f'<p><a href="../registry/run_card_h71_2026-10-26.json">Run card</a> · '
        f'<a href="../evidence/focus_pairwise_overlap_2026-10-26.json">Reproducible pairwise audit</a> · '
        f'<a href="downloads/{e(featured["receipt"])}">Format-only receipt</a>. Format validity is not scientific or lane approval.</p>'
    )
    historical = 'gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif'
    rows, cards = [], []
    for row in sorted(focus['sites'], key=lambda r: -r['owner_reported_score']):
        geometry = pairwise['focus_winners'][row['site']]
        exact = ', '.join(geometry['exact_mask_match_sites']) or 'none among the nine selected winners'
        overlap = geometry['max_cross_site_candidate_dot_share_within_3px']
        peer = geometry['most_similar_focus_site']
        rows.append(f'''<tr><th scope="row"><a href="{e(row['site_url'])}">{e(row['site'])}</a></th>
<td class="submission-id"><code>{e(geometry['file'])}</code></td>
<td><b>OWNER-REPORTED DTI {row['owner_reported_score']:.4f}</b><small>Unverified by organizer receipt; no holdout/live-score projection for this historical file.</small></td>
<td><b>FAILS literal 70% / 3-px uniqueness</b><small>{overlap:.1%} of its dots within 3 px of {e(peer)}.</small></td>
<td><small>Exact prediction-mask match: {e(exact)}.</small></td></tr>''')
        cards.append(f'''<article class="card"><h3>{e(row['site'])}</h3><p>{e(row['mechanism'])}</p>
<p class="small">{geometry['emitted_pixels']:,} positive pixels · Selected file SHA-256: <code class="wrap-hash">{geometry['sha256']}</code> ·
Maximum directed 3-px neighbor share {overlap:.1%} vs {e(peer)}. Historical-only; not eligible as a new submission.</p>
<a href="{e(row['source_url'])}">Pinned source revision</a> · <a href="{e(row['site_url'])}">Owner project page (manual review)</a></article>''')
    h71_row = f'''<tr><th scope="row">GEMSDOE25 — H71 research candidate</th>
<td class="submission-id"><code>{e(h71['file'])}</code></td>
<td><b>HOLDOUT-DTI {h71_holdout['pooled_dti']:.6f}</b><small>evaluator {e(h71_holdout['evaluator_version'])}; withheld positives {h71_holdout['withheld_positives']:,}; 95% CI [{h71_holdout['ci_95'][0]:.6f}, {h71_holdout['ci_95'][1]:.6f}]; paired mean gain vs same-run H35 {h71_holdout['vs_h35_mean_gain']:+.6f}. Not a competition score; no projection.</small></td>
<td><b>Unique vs these nine only</b><small>{h71['max_focus_site_dot_share_within_3px']:.1%} max vs {e(h71['most_similar_focus_site'])}; global strict lane FAIL: 100% within 3 px of r13 lattice.</small></td>
<td><b>HOLDOUT-DTI FAIL vs H35; DO NOT SUBMIT.</b><small>Research artifact only; not an eligible competition TIF.</small></td></tr>'''
    coverage = focus['lattice_coverage']
    hypothesis_queue = json.loads((ROOT/'registry/hypothesis_queue_2026-10-26.json').read_text())
    hypothesis_rows_list = []
    for item in hypothesis_queue['hypotheses']:
        source_links = ' · '.join(
            f'<a href="{e(source["url"])}" rel="noopener noreferrer">{e(source["title"])}</a>'
            for source in item['official_manual_review_sources']
        )
        hypothesis_rows_list.append(
            f'''<tr><th scope="row">{item['rank']}. {e(item['name'])}<small>{e(item['id'])}</small></th>
<td>{e('; '.join(item['layers']))}<small>{e(item['signature_and_transform'])}</small></td>
<td>{e(item['blind_fault_rationale'])}<small>Non-fault mimics: {e('; '.join(item['non_fault_mimics']))}</small></td>
<td>Planning judgment: {item['planning_expected_holdout_delta_dti']['low']:+.3f} to {item['planning_expected_holdout_delta_dti']['high']:+.3f} HOLDOUT-DTI units<small>{e(item['implementation_cost'])} {e(item['status'])}</small></td>
<td>{e(item['data_availability'])}<small>Manual-review links: {source_links}</small></td></tr>'''
        )
    hypothesis_rows = ''.join(hypothesis_rows_list)
    body = f'''<section class="hero"><p class="eyebrow">RESEARCH DECISION BRIEF / 26 OCTOBER 2026</p>
<h1>Know what is known.<br>Know when to stop.</h1>
<p class="lead">Nine hash-pinned owner-mirror exemplars, a reproducible pairwise audit, and no cleared competition TIF. No renamed reference files. No predicted leaderboard scores.</p></section>
<section class="review-decision"><span class="badge b-bad">COMPETITION TIFF: NONE CLEARED</span><h2>The requested download-ready submission requirement is unmet</h2>
<p>No new GeoTIFF passed the scientific holdout and strict global lane gates. The existing H71 file remains a research artifact only; it is not offered as an eligible competition download.</p>
<p><b>Competition-ready download: NO · OK TO SUBMIT: NO · OK to spend a weekly slot: NO — DO NOT SUBMIT.</b></p>
<p>ROD stop: {status}</p>{download}
<div class="row"><a class="btn" href="../registry/run_card_h71_2026-10-26.json">H71 decision card</a>
<a class="btn alt" href="#how-to-submit">Submission checklist (future gate-cleared file only)</a></div></section>
<section><h2>Executive comparison — strongest supplied artifact for each focus site</h2>
<p>Scores below are <b>OWNER-REPORTED DTI claims</b> copied from the pinned local audit, not organizer-confirmed receipts. No current live score or score projection is available.
The uniqueness column applies the literal directed rule: stop if more than 70% of a candidate's dots lie within 3 px of any registry raster.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Nine historical exemplars and the H71 research candidate"><table><thead><tr><th>Site</th><th>Strongest supplied artifact</th><th>Score class / estimate</th><th>Geometric uniqueness</th><th>Eligibility / exact-mask note</th></tr></thead>
<tbody>{''.join(rows)}{h71_row}</tbody></table></div>
<p class="small">The conflicting overall-leader claims 0.3195 and 0.4413 remain unverified. The table is not a live leaderboard query and not a slot selection.</p>
</section>
<section><h2>Pairwise identity: exact duplicates versus near-duplicate lane failures</h2>
<p>All nine selected historical winners exceed the 70% directed 3-px overlap limit against at least one other selected focus winner. That establishes a lane overlap among these owner-mirrored masks, not that their filenames or scores were organizer-verified.</p>
<p><b>Exact mask match:</b> GEMSDOE25 and GEMSDOE30. The selected GEMSDOE28 winner (0.2710) and GEMSDOE31 winner (0.2708) are <b>not</b> exact, despite 99.76% / 99.56% reciprocal 3-px neighborhood coverage. A separate GEMSDOE28 R1 artifact (0.2708) is pixel-identical to GEMSDOE31 R1 (0.2708). GEMSDOE32 B2 is a strict subset of GEMSDOE36 and all B2 dots are within 3 px of the GEMSDOE36 mask.</p>
<p><a href="../evidence/focus_pairwise_overlap_2026-10-26.json">Machine-readable 90-direction pairwise audit (SHA-256 verified)</a> · <a href="../knowledge/29_focus_review_2026-10-26.md">Full review, scoring caveats, ranked research hypotheses</a>.</p></section>
<section><h2>Why B2 can work — conditional explanation, not a verified score cause</h2>
<p>Pixel forensics show B2 is exactly the D2.8 mask after 6,436 predictions within 200 m of the supplied catalogue are removed. The owner-reported claim increases 0.2600 → 0.2708 → 0.2778 through catalogue collars of 100 m then 200 m; removing 1,200 extra dots to make GEMSDOE36 accompanies a lower owner-reported 0.2750.</p>
<p>Under the repo's DTI form, a prediction receives credit within a 300 m triangular kernel while false-positive mass is charged. Pruning can improve the ratio if the removed collar dots carry less marginal credit than their false-positive cost; the hidden labels are unavailable, so the mechanism is an inference conditional on reported scores—not a proof of the true holdout mechanism.</p>
<p>Under the local inverse calculation's assumed hidden-positive count (12,691 pixels) and conditional score claims, D2.8→R1 deletes 3,891 dots with an implied mean credit loss of 0.000961 per deleted pixel, and R1→B2 deletes another 2,545 dots at 0.005029 per deleted pixel. Both are below the algebraic break-even thresholds in that assumed model. These are conditional model quantities, not HOLDOUT-DTI or organizer scores.</p>
</section>
<section><h2>Ranked blind-fault research hypotheses — planning only, no fit</h2>
<p>Expected changes below are explicitly planning judgments, not estimates or scores. Only H72-1 uses inputs already restored here, and its cache/provenance gates remain open. Official release/product pages were reviewed, but none establishes AOI-specific usable scenes for H72-2 through H72-4; those hypotheses remain blocked, not viable.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Ranked untried geological hypotheses"><table><thead><tr><th>Rank / hypothesis</th><th>Layers / signature</th><th>Blind-fault rationale / mimics</th><th>Planning Δ / cost / status</th><th>Data availability / manual sources</th></tr></thead><tbody>{hypothesis_rows}</tbody></table></div>
<p><a href="../knowledge/29_focus_review_2026-10-26.md">Full novelty boundary, source availability, physical reasoning and implementation gates</a>. Cross-sibling code novelty is not established.</p></section>
<section><h2>Prior ROD screen: negative; no new test was run in this review</h2>
<p>The earlier preregistered radiometric offset-discontinuity screen used cached K/Th/U and LiDAR step/coherence. Its saved result is negative and is not a competition score. Volcanic flow lobes, sediment sorting and survey seams can mimic the signature.</p>
{outcome}<p><a href="../knowledge/27_preregistered_rod_2026-10-26.md">Four ranked hypotheses &amp; frozen design</a> ·
<a href="../evidence/rod_2026-10-26/feature_canaries.json">Every-feature leakage canaries</a> ·
<a href="../evidence/rod_2026-10-26/surface_lane.json">Pre-placement surface audit</a></p></section>
{pol3_section}
<section><h2>The novelty constraint needs attention</h2>
<p>The registered lattice's three-pixel halo covers <b>{coverage['coverage_fraction']*100:.4f}%</b> of eligible pixels.
Only {coverage['uncovered_pixels']:,} pixels lie outside it. Under the literal overlap rule, a candidate above 21,713 unique dots cannot pass against that lattice,
even before spacing constraints. This does <b>not</b> establish that every smaller candidate passes.</p>
<p>No density exception was applied. No dots were moved merely to evade the registry.</p></section>
<section><h2>Site-by-site executive findings</h2>{''.join(cards)}</section>
<section id="how-to-submit"><h2>How a submission becomes eligible</h2>
<ol class="steps"><li><b>Research gate.</b> Beat the same-run best comparable buffered holdout; report pooled HOLDOUT-DTI, evaluator version, withheld-positive count and 95% CI. Confirm on fresh draws.</li>
<li><b>Novelty gate.</b> Check the surface before placement and exact final dots against the registry. Stop for rank correlation above 0.90 or more than 70% within 3 px. Renaming, changing compression or filling outside NaNs is not a new prediction.</li>
<li><b>File gate.</b> One float32 GeoTIFF band, finite predictions in [0,1] throughout the template footprint, identical CRS, shape and geotransform. Use the shared writer; reject invalid data instead of silently clipping it.</li>
<li><b>Selector gate.</b> Separate authorization and a verified remaining weekly slot are required. The software must not infer either from a format-pass receipt.</li>
<li><b>Only after all gates pass:</b> download the exact approved hash-linked TIF, open the competition submission form, select that TIF (not this report or JSON), paste its ≤140-character note and save the organizer receipt. This project does not automate upload.</li></ol>
<p><b>Today: stop at the failed gates.</b> No new competition file is approved. The weekly cap/remaining allowance was not freshly verified.</p>
<details><summary>Historical file for learning only — never submit as a new file</summary>
<p>This is the already-existing H66 artifact, not a new deliverable. Its newer user-reported result is 0.0742 (OWNER-REPORTED).</p>
<a href="downloads/{historical}" download>Download historical H66 TIF — DO NOT SUBMIT</a>
<p>Also archived for learning: APFL piedmont-flexure unique research TIF (testing-only, DO NOT SUBMIT) — <a href="downloads/gems25-apfl-piedmont-flexure-s3p0-k3p5-20261026-8aebdab87158-zeros.tif" download>gems25-apfl-piedmont-flexure-s3p0-k3p5-20261026-8aebdab87158-zeros.tif</a> (43,798 px, not slot-approved)</p>
</details></section>
<section><h2>Sources, freshness and next work</h2>
<ul><li><a href="../evidence/focus_audit_2026-10-26.json">Fresh mirror hashes, mask identities and nine source revisions</a> — owner mirrors, not organizer authentication.</li>
<li><a href="../evidence/focus_format_2026-10-26.json">Automated exact-template format receipts</a> — format only, not performance approval.</li>
<li><a href="../evidence/official_reference_2026-10-26.json">Fresh official reference-repository evidence</a> — CPU training is supported; its training loss is not an independent distance-weighted scorer.</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem and format</a> ·
<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Rules PDF</a> ·
<a href="https://gdr.openei.org/submissions/1391">GDR 1391</a> ·
<a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a> — manual-review links, not freshly fetched here.</li></ul>
<p>Next: resolve the dense-lattice policy before another high-budget run; address SGMC proxy contamination before confirmation; authenticate external source bytes and preserve all failed results.
Automatic source availability is not automatic scientific verification or a live leaderboard feed.</p>
<p><a href="history.html">Historical experiment/download archive</a></p></section>'''
    if root_page:
        body = body.replace('href="../', 'href="').replace('href="downloads/', 'href="docs/downloads/')
        body = body.replace('href="history.html"', 'href="docs/history.html"')
    return body


def readme_status():
    brief = (ROOT/'knowledge/current_project_brief_2026-10-26.md').read_text()
    return ("<!-- CURRENT-REVIEW-2026-10-26 -->\n"
            "## Current decision — 2026-10-26\n\n"
            "**Research-archive downloads: YES for inspection only · Competition-ready download: NO · OK TO SUBMIT: NO — DO NOT SUBMIT.** The requested gate-cleared new competition GeoTIFF was not produced; that deliverable remains unmet. "
            "The already-archived H71 file is format-valid for research inspection only, but failed HOLDOUT-DTI vs same-run H35 and the literal global lane check (100% within 3 px of the r13 lattice); it is not offered here as an eligible submission. "
            "H71 HOLDOUT-DTI is `0.050577` (evaluator `gems25.holdout.v1.2-buffered-4quad-pooled-dti`, 21,835 withheld positives, 95% CI `[0.037264, 0.063890]`), not a competition score. "
            "No new experiment, TIF, cache rebuild, promotion/selection step, or weekly slot was used in this review. "
            "[Nine-site executive table and eligibility decision](docs/current-review.html) · "
            "[Reproducible pairwise overlap audit](evidence/focus_pairwise_overlap_2026-10-26.json) · "
            "[B2 analysis and ranked planning hypotheses](knowledge/29_focus_review_2026-10-26.md) · "
            "[Owner-mirror restore/prepare receipt](evidence/data_restore_prepare_2026-10-26.json). "
            "GEMSDOE32 B2 remains the strongest supplied historical exemplar (**OWNER-REPORTED DTI 0.2778**); no organizer receipt or current score estimate is available.\n\n"
            "Read the current owner brief below every session, then the preserved historical prompts. "
            "**Maximize P(Win)** and **Own the Outcome**: a negative scientific result is not an excuse to submit a rejected file.\n\n"
            "<details><summary>Current owner prompt — normalized standing brief (not verbatim)</summary>\n\n"
            + brief + "\n</details>\n\n<!-- END-CURRENT-REVIEW-2026-10-26 -->\n")


def main():
    from build_site import page
    (ROOT/'docs/current-review.html').write_text(page('Current executive review', render_body(), 'current', ''))


if __name__ == '__main__':
    main()
