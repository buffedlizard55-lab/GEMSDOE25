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
<strong>26 OCT 2026 · OK TO DOWNLOAD: YES (TESTING) · OK TO SUBMIT: NO</strong>
<span>New H72-CF GeoTIFF is content-unique and format-valid, but its holdout family and strict final-dot lane gates fail. DO NOT SUBMIT.</span>
<a href="{prefix}current-review.html">Read the nine-site executive review &amp; H72 automatic decision →</a></aside>'''


def render_body(root_page=False):
    focus = json.loads((ROOT/'evidence/focus_audit_2026-10-26.json').read_text())
    h72_path = ROOT/'registry/run_card_h72_cf_2026-10-26.json'
    card = json.loads(h72_path.read_text()) if h72_path.exists() else None
    status = e(card['verdict_reason']) if card else 'Run incomplete. No submission file is authorized.'
    outcome = '<p>No valid HOLDOUT-DTI result is available. This is not a score of zero.</p>'
    if card:
        main = card['holdout_dti']['screen_and_confirm_H72_with_H35']
        cf = card['holdout_dti']['shipped_catfree_detector_family']
        outcome = f'''<div class="review-metrics"><div><span>H72 add-on · HOLDOUT-DTI</span><strong>{main['candidate_pooled']:.4f}</strong>
<small>95% CI {main['candidate_ci95'][0]:.4f}–{main['candidate_ci95'][1]:.4f}; paired +{main['paired_gain']:.4f} vs H35</small></div>
<div><span>Shipped CatFree family · HOLDOUT-DTI</span><strong>{cf['candidate_pooled']:.4f}</strong>
<small>95% CI {cf['candidate_ci95'][0]:.4f}–{cf['candidate_ci95'][1]:.4f}; paired {cf['paired_gain_vs_H35']:+.4f} vs H35</small></div></div>
<p>H72 add-on used {main['withheld_positive_occurrences']:,} withheld-positive occurrences across Screen + Confirmation; shipped CatFree diagnostic used {cf['withheld_positive_occurrences']:,}.
Four buffered spatial quadrants; whole components withheld; quadrant-cluster bootstrap 95% CIs.
Evaluator: <code>{e(card['holdout_dti']['evaluator_version'])}</code>.
The additive block replicated, but the downloadable CatFree lineage did not beat same-run H35; neither number is a leaderboard score.</p>'''
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
    download = (
        f'<p><b>OK to download: YES</b> for local testing of unique content id '
        f'<code>{e(featured["content_id"])}</code>. '
        f'<b>OK to spend a weekly slot: NO — DO NOT SUBMIT.</b> '
        f'H72-CF is content-unique and format-valid; it clears 27 focus/top rasters and own lineage, '
        f'but its detector family loses to same-run H35 and final dots fail strict overlap against the lattice and four broad historical artifacts.</p>'
        f'<a class="btn" download href="downloads/{e(featured["file"])}">↓ Download {e(featured["file"])} — testing only</a>'
    )
    historical = 'gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif'
    rows, cards = [], []
    for row in sorted(focus['sites'], key=lambda r: -r['owner_reported_score']):
        rows.append(f'''<tr><th scope="row"><a href="{e(row['site_url'])}">{e(row['site'])}</a></th>
<td>{row['owner_reported_score']:.4f}<small>OWNER-REPORTED</small></td>
<td class="submission-id">{e(row['submission'])}</td><td><span class="badge b-warn">Historical only</span></td></tr>''')
        cards.append(f'''<article class="card"><h3>{e(row['site'])}</h3><p>{e(row['mechanism'])}</p>
<p class="small">{row['positive_pixels']:,} positive pixels · Local format checks: {'pass' if row['local_format_pass'] else 'fail'} ·
Not approved as a new submission. SHA-256: <code class="wrap-hash">{row['sha256']}</code></p>
<a href="{e(row['source_url'])}">Pinned source revision</a> · <a href="{e(row['site_url'])}">Original site</a></article>''')
    coverage = focus['lattice_coverage']
    body = f'''<section class="hero"><p class="eyebrow">RESEARCH DECISION BRIEF / 26 OCTOBER 2026</p>
<h1>Know what to submit.<br>Know when to stop.</h1>
<p class="lead">Nine focus sites, three preregistered H72 experiments, one unique GeoTIFF, and an automatic stop. No renamed reference files. No invented leaderboard estimate.</p></section>
<section class="review-decision"><span class="badge b-bad">OK TO SUBMIT: NO</span><h2>Unique research GeoTIFF is downloadable — not slot-cleared</h2>
<p>{e(featured['title'])}. {e(featured['summary'])}</p>
<p>H72 decision: {status}</p>{download}
<div class="table-scroll"><table><thead><tr><th>File to download</th><th>Estimated leaderboard score</th><th>Unique?</th><th>Submit?</th></tr></thead><tbody><tr>
<td><code>{e(featured['file'])}</code></td>
<td><b>NO DEFENSIBLE LEADERBOARD ESTIMATE</b><small>CatFree HOLDOUT-DTI 0.0948 [0.0823, 0.1073] is a proxy, not a score.</small></td>
<td><b>Content: YES</b><small>0 prior content matches; focus/top + own lineage pass.</small><br><b>Strict lane: NO</b><small>lattice + four broad artifact halos fail.</small></td>
<td><span class="badge b-bad">NO — DO NOT SUBMIT</span></td></tr></tbody></table></div>
<div class="row"><a class="btn" href="../registry/run_card_h72_cf_2026-10-26.json" download>Download H72 decision receipt</a>
<a class="btn alt" href="#how-to-submit">Submission checklist</a></div></section>
<section><h2>What is the strongest historical evidence?</h2>
<p><b>GEMSDOE32 B2 — 0.2778, OWNER-REPORTED.</b> It is the highest supplied historical result among these focus sites.
It is already an earlier submission, so it is <b>not</b> eligible as a new unique artifact. No organizer receipt has been supplied.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Nine historical exemplars"><table><thead><tr><th>Site</th><th>Reported result</th><th>Highest supplied historical submission</th><th>Use</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="small">Not a live leaderboard query and not a slot selection. The conflicting overall-leader claims 0.3195 and 0.4413 remain unverified.</p></section>
<section><h2>Why B2 can work — and what it does not prove</h2>
<p>Fresh pixel checks show B2 is exactly D2.8 with 6,436 predictions within 200 m of the supplied catalogue removed.
GEMSDOE36 is B2 plus 1,200 predictions. GEMSDOE25 and 30 have identical masks; GEMSDOE28 R1 and 31 have identical masks.</p>
<p>DTI rewards the strongest nearby prediction for each truth pixel while charging false-positive mass.
Thinning can preserve coverage while removing redundant predictions. Collar pruning may reduce low-value emissions.
<b>The hidden labels are unavailable, so this is a conditional explanation—not proof of the cause of the reported score.</b></p>
<p>Formula: <code>S = T / (0.2(T + F) + 0.8N)</code>. Removing credit <i>t</i> and false-positive mass <i>f</i> helps only when
<code>t/f &lt; 0.2S/(1−0.2S)</code>. No amount of filename novelty establishes that condition.</p>
<a href="../knowledge/28_focus_review_2026-10-26.md">Read the scientific reasoning and limitations</a></section>
<section><h2>New test: H72 macro-basin contour scarps + concealed MT/gravity/swarm damage</h2>
<p>H72 targets a fault scarp that follows the macro-basin contour rather than down-slope drainage, plus concealed density contacts, conductive clay-gouge/base shoaling and transtensional earthquake-swarm excess. Lake shoreline benches, stratigraphic contacts and volcanic fronts are named mimics.</p>
{outcome}<p><b>Decision:</b> the six H72 columns replicated as an add-on to H35, but the genuinely catalogue-free downloadable lineage did not beat H35. Surface rank passes; final-dot overlap fails the strict registry rule. Negative result, no slot.</p>
<p><a href="../knowledge/29_h72_cf_hypotheses_and_preregistration_2026-10-26.md">Five ranked hypotheses &amp; frozen design</a> ·
<a href="../knowledge/30_h72_cf_outcomes_and_executive_decision_2026-10-26.md">Complete outcomes and nine-site decision</a> ·
<a href="../registry/run_card_h72_cf_2026-10-26.json">H72 run card</a> ·
<a href="../evidence/h72_cf_lane_surface.json">Pre-placement surface audit</a></p></section>
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
<li><a href="../evidence/h72_cf_pooled_summary.json">H72 pooled HOLDOUT-DTI + CIs</a> · <a href="../evidence/h72_cf_content_uniqueness.json">exact scored-content uniqueness</a> · <a href="../evidence/h72_cf_independent_audit.json">independent exact-file audit</a>.</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem and format</a> ·
<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Rules PDF</a> ·
<a href="https://gdr.openei.org/submissions/1391">GDR 1391</a> ·
<a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a> — manual-review links, not freshly fetched here.</li></ul>
<p>Next: stop H72 at its 3/3 budget; resolve the dense-lattice/broad-artifact policy before another high-budget run; then preregister the independent 2D spatial-context ResUNet on a GPU runner. Preserve all failed results and authenticate any new external-source bytes before use.
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
            "**OK to download: YES · OK to spend a weekly slot: NO — DO NOT SUBMIT.** "
            "Featured unique GeoTIFF [`gems25-h72-mbsp-mtg-catfree-b2-37654-20261026-1d7c1e9ea55f-zeros.tif`](docs/downloads/gems25-h72-mbsp-mtg-catfree-b2-37654-20261026-1d7c1e9ea55f-zeros.tif) "
            "(content id `1d7c1e9ea55f`; format PASS; shipped CatFree HOLDOUT-DTI FAIL vs H35; strict lane FAIL). "
            "[Nine-site executive review and automated H72 decision](docs/current-review.html) · "
            "[H72 outcomes](knowledge/30_h72_cf_outcomes_and_executive_decision_2026-10-26.md) · "
            "[H72 run card](registry/run_card_h72_cf_2026-10-26.json). "
            "GEMSDOE32 B2 is the strongest supplied historical exemplar (**OWNER-REPORTED 0.2778**), not a new submission. "
            "Do not reinterpret historical downloads or format-only receipts as authorization. "
            "No weekly slot was used.\n\n"
            "Read the current owner brief below every session, then the preserved historical prompts. "
            "**Maximize P(Win)** and **Own the Outcome**: a negative scientific result is not an excuse to submit a rejected file.\n\n"
            "<details><summary>Current owner prompt — normalized standing brief (not verbatim)</summary>\n\n"
            + brief + "\n</details>\n\n<!-- END-CURRENT-REVIEW-2026-10-26 -->\n")


def main():
    from build_site import page
    (ROOT/'docs/current-review.html').write_text(page('Current executive review', render_body(), 'current', ''))


if __name__ == '__main__':
    main()
