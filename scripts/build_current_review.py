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
<strong>26 OCT 2026 · OK TO SUBMIT: NO</strong>
<span>Latest saved ROD-1 test failed HOLDOUT-DTI and the literal lane gate; it wrote no TIFF. The H71 download is an earlier testing artifact only.</span>
<a href="{prefix}current-review.html">Read the nine-site executive review, score-estimate limits &amp; run card →</a></aside>'''


def render_body(root_page=False):
    focus = json.loads((ROOT/'evidence/focus_audit_2026-10-26.json').read_text())
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
    olic_path = ROOT/'evidence/olic_screen_2026-10-26/summary.json'
    olic = json.loads(olic_path.read_text()) if olic_path.exists() else None
    olic_section = ''
    if olic:
        olic_section = f'''<section class="card"><p class="eyebrow">PARALLEL SESSION · OLIC LANE · ONE FROZEN SCREEN · NEGATIVE</p>
<h2>OLIC oriented line-continuity screen — negative (no new TIF)</h2>
<p><b>HOLDOUT-DTI</b>, evaluator <code>{e(olic['evaluator'])}</code>, draws <code>{e(str(olic['draws']))}</code>,
{olic['withheld_positives']:,} withheld positives. Candidate (H35 + 9 oriented line-continuity features) pooled
<code>{olic['candidate_pooled']['dti']:.6f}</code> vs same-run H35 <code>{olic['control_pooled']['dti']:.6f}</code>;
paired four-fold mean gain <code>{olic['paired_fold_mean_gain']:+.6f}</code>,
95% CI <code>[{olic['paired_fold_ci95'][0]:+.6f}, {olic['paired_fold_ci95'][1]:+.6f}]</code>,
{olic['positive_folds']}/4 folds positive. Feature-alone maximum AUC <code>{olic['max_canary_auc']:.4f}</code> (leakage canary PASS).
The frozen gate (gain &gt; +0.001 and &ge;3/4 folds) failed, so no confirmation, no surface/lane placement and
<b>no OLIC GeoTIFF was written</b>; lane clearance is <b>NOT RUN</b>. <b>File to download for submission: NONE. Estimated leaderboard score: NOT ESTIMABLE</b>
(a projection is never a score). Catalogue-gap proxy only, not an organizer score.</p>
<p><a href="../knowledge/29_preregistered_olic_line_continuity_2026-10-26.md">Frozen preregistration &amp; ranked hypotheses</a> ·
<a href="../knowledge/29_olic_outcomes_2026-10-26.md">OLIC outcomes &amp; nine-site executive summary</a> ·
<a href="../registry/run_card_olic_2026-10-26.json">OLIC run card (JSON)</a> ·
<a href="../evidence/olic_screen_2026-10-26/summary.json">Screen summary</a></p></section>'''

    subs = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
    featured = next(s for s in subs if s["role"] == "primary")
    h71 = json.loads((ROOT / "registry" / "run_card_h71_2026-10-26.json").read_text())
    h71_result = h71["holdout_dti"]
    download = (
        f'<p><b>OK to download: YES</b> for local testing of content id '
        f'<code>{e(featured["content_id"])}</code>. '
        f'<b>OK to spend a weekly slot: NO — DO NOT SUBMIT.</b> '
        f'This earlier file is content-distinct from scored mirrors but FAILS the literal lane rule: '
        f'100% of final dots are within 3 px of the registered r13 lattice (70% cap). '
        f'The three DIRECT screens failed vs H35. ROD/POL3 wrote no new competition TIFF.</p>'
        f'<a class="btn" download href="downloads/{e(featured["file"])}">↓ Download {e(featured["file"])} — testing only</a>'
    )
    inventory_path = ROOT/'docs/data/download_audit.json'
    inventory_section = ''
    if inventory_path.exists():
        inventory = json.loads(inventory_path.read_text())
        inventory_rows = ''.join(
            f'<tr><td><a download href="downloads/{e(r["file"])}">{e(r["file"])}</a></td>'
            f'<td>{"PASS" if r["format_valid"] else "FAIL"} (local only)</td>'
            '<td>Unknown — no calibrated estimate</td>'
            f'<td>{len(r["identical_footprint_files"])} identical local footprint variant(s); '
            'cross-site novelty unproven</td><td>NO — testing only</td></tr>'
            for r in inventory['files'])
        inventory_section = f'''<section><h2>Exactly what can I download and submit?</h2>
<p><a href="../knowledge/29_download_audit_and_next_hypotheses_2026-10-26.md">Latest audit, ranked future hypotheses and limitations</a>.</p>
<p><b>No file is currently approved to submit.</b> The table below audits the actual shipped files,
not their names. Format validity does not predict a high score or prove novelty.
Audit time: <code>{e(inventory['generated_utc'])}</code>.
{len(inventory['files'])} TIFFs; {len({r['footprint_sha256'] for r in inventory['files'] if r['footprint_sha256']})}
 distinct finite footprint prediction arrays. NaN-outside and zero-outside variants are not new predictions.</p>
<p><a href="data/download_audit.json" download>Download all exact-file validator receipts and identity groups (JSON)</a>.
Leaderboard estimates are unknown: a catalogue-gap HOLDOUT-DTI is not a calibrated competition prediction.
Historical scores in the nine-site table are OWNER-REPORTED, not ORGANIZER-CONFIRMED.</p>
<details><summary>Show every downloadable TIFF, estimated score and submission status</summary>
<div class="table-scroll"><table><thead><tr><th>File to download (research only)</th><th>Format</th>
<th>Estimated leaderboard score</th><th>Unique?</th><th>OK to submit?</th></tr></thead>
<tbody>{inventory_rows}</tbody></table></div></details></section>'''
    historical = 'gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif'
    rows, cards = [], []
    exact_mask_notes = {
        "GEMSDOE24": "Different mask; D1.5 thinning of the older H19-5 parent.",
        "GEMSDOE25": "Exact-mask duplicate of GEMSDOE30 (D2.8).",
        "GEMSDOE27": "Different mask; 97.95% lies in the older H19-5/D1.5 lineage.",
        "GEMSDOE28": "Exact-mask duplicate of GEMSDOE31 (R1).",
        "GEMSDOE30": "Exact-mask duplicate of GEMSDOE25 (D2.8).",
        "GEMSDOE31": "Exact-mask duplicate of GEMSDOE28 (R1).",
        "GEMSDOE32": "Different mask; nested B2 pruning of D2.8/R1.",
        "GEMSDOE33": "Different mask; R1 plus re-admitted collar/tip pixels.",
        "GEMSDOE36": "Different mask; B2 plus 1,200 additional pixels.",
    }
    for row in sorted(focus['sites'], key=lambda r: -r['owner_reported_score']):
        rows.append(f'''<tr><th scope="row"><a href="{e(row['site_url'])}">{e(row['site'])}</a></th>
<td class="submission-id">{e(row['submission'])}.tif</td>
<td>{row['owner_reported_score']:.4f}<small>OWNER-REPORTED · not an organizer receipt</small></td>
<td>Not estimated<small>No validated live-score model</small></td>
<td>{e(exact_mask_notes[row['site']])}<small>Pixel identity / lineage from local mirror audit</small></td>
<td><span class="badge b-warn">NO — historical; not slot-approved</span></td></tr>''')
        cards.append(f'''<article class="card"><h3>{e(row['site'])}</h3><p>{e(row['mechanism'])}</p>
<p class="small">{row['positive_pixels']:,} positive pixels · Local format checks: {'pass' if row['local_format_pass'] else 'fail'} ·
Not approved as a new submission. SHA-256: <code class="wrap-hash">{row['sha256']}</code></p>
<a href="{e(row['source_url'])}">Pinned source revision</a> · <a href="{e(row['site_url'])}">Original site</a></article>''')
    feasibility = json.loads((ROOT/'evidence/lane_feasibility_2026-10-26.json').read_text())
    geometry = feasibility['geometry']
    bounds = ''.join(f"<tr><td>{r['dots']:,}</td><td>{r['minimum_overlap']:.2%}</td><td>Impossible at this density</td></tr>"
                     for r in feasibility['cases'])
    coverage = focus['lattice_coverage']
    body = f'''<section class="hero"><p class="eyebrow">RESEARCH DECISION BRIEF / 26 OCTOBER 2026</p>
<h1>Know what to submit.<br>Know when to stop.</h1>
<p class="lead">Nine focus sites, one auditable comparison, and a new geological test. No renamed reference files. No predicted leaderboard scores.</p></section>
<section class="review-decision"><span class="badge b-bad">OK TO SUBMIT: NO</span><h2>Content-distinct H71 testing GeoTIFF only — no new ROD/POL3 file was written; strict lane and performance gates failed</h2>
<p>{e(featured['title'])}. {e(featured['summary'])}</p>
<p>ROD stop: {status}</p>{download}
<div class="row"><a class="btn" href="../evidence/rod_2026-10-26/run_card.json" download>Download decision receipt</a>
<a class="btn alt" href="#how-to-submit">Submission checklist</a>
<a class="btn alt" href="../knowledge/29_current_checkout_review_2026-10-26.md">Current-checkout review and ranked next hypotheses</a></div></section>
{inventory_section}
<section><h2>Current downloadable file: estimate and uniqueness decision</h2>
<div class="table-scroll"><table><thead><tr><th>File</th><th>Estimated competition score</th><th>Saved HOLDOUT-DTI (proxy)</th><th>Unique under literal lane rule?</th><th>Decision</th></tr></thead><tbody>
<tr><td class="submission-id">{e(featured['file'])}</td>
<td>NOT ESTIMATED — no calibrated leaderboard projection</td>
<td>HOLDOUT-DTI {h71_result['pooled_dti']:.6f}; evaluator {e(h71_result['evaluator_version'])}; {h71_result['withheld_positives']:,} withheld positives; 95% CI [{h71_result['ci_95'][0]:.6f}, {h71_result['ci_95'][1]:.6f}]</td>
<td><b>NO.</b> 100% within 3 px of the registered r13 lattice; threshold 70%.</td>
<td><b>DO NOT SUBMIT.</b> Holdout failed vs H35; testing only.</td></tr></tbody></table></div>
<p>Saved H71 evidence, not rerun in this review. HOLDOUT-DTI is a catalogue-gap proxy, not an organizer score or leaderboard forecast.</p></section>
<section id="lane-feasibility"><h2>Strict-overlap feasibility audit</h2>
<p>Freshly restored SHA-pinned template, labels and registry lattice match CRS, shape and transform.
Only <b>{geometry['uncovered_pixels']:,}</b> eligible pixels lie outside that lattice's 3-pixel halo.
For K distinct dots, at least max(0, K − {geometry['uncovered_pixels']:,}) must overlap.
These are <b>COMPUTED GEOMETRY diagnostics, not performance scores</b>.</p>
<table><thead><tr><th>Candidate dot budget K</th><th>Minimum unavoidable overlap</th><th>Literal 70% gate</th></tr></thead><tbody>{bounds}</tbody></table>
<p>At most <b>21,713 dots</b> are not ruled out by this one necessary condition. Smaller budgets are not automatically feasible,
unique, high-scoring or approved. No candidate was placed; no geological model was fitted in this audit.
We did not exclude the dense reference or substitute a density-aware waiver.</p>
<p><a href="../evidence/lane_feasibility_2026-10-26.json">Download the reproducible geometry receipt</a> ·
<a href="../knowledge/29_lane_feasibility_plan_2026-10-26.md">Preregistered proof and three deferred geological hypotheses</a></p>
<p><b>No new TIFF generated:</b> the preregistered budgets cannot pass the required gate. The existing research download above remains DO NOT SUBMIT.</p></section>
<section><h2>What is the strongest historical evidence?</h2>
<p><b>GEMSDOE32 B2 — 0.2778, OWNER-REPORTED.</b> It is the highest supplied historical result among these focus sites.
It is already an earlier submission, so it is <b>not</b> eligible as a new unique artifact. No organizer receipt has been supplied.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Nine focus-site files, reported results, estimates, and eligibility"><table><thead><tr><th>Site</th><th>Historical file</th><th>Historical score</th><th>Estimated score for a new file</th><th>Focus-mask uniqueness</th><th>New submission eligible?</th></tr></thead>
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
<section><h2>New test: radiometric offset discontinuity</h2>
<p>Does a compositional pattern match better after sliding one side of a scarp along strike? The preregistered ROD test uses cached K/Th/U and LiDAR step/coherence,
not a copied prediction mask. Volcanic flow lobes, sediment sorting and survey seams can mimic this signature.</p>
{outcome}<p><a href="../knowledge/27_preregistered_rod_2026-10-26.md">Four ranked hypotheses &amp; frozen design</a> ·
<a href="../evidence/rod_2026-10-26/feature_canaries.json">Every-feature leakage canaries</a> ·
<a href="../evidence/rod_2026-10-26/surface_lane.json">Pre-placement surface audit</a></p></section>
{pol3_section}
{olic_section}
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
<p><a href="../knowledge/29_repository_review_2026-10-26.md">This repository review and limitations</a> ·
<a href="../registry/run_card_repo_review_2026-10-26_session.json">This review's run card</a> ·
<a href="history.html">Historical experiment/download archive</a></p></section>'''
    if root_page:
        body = body.replace('href="../', 'href="').replace('href="downloads/', 'href="docs/downloads/')
        body = body.replace('href="history.html"', 'href="docs/history.html"')
        body = body.replace('href="data/', 'href="docs/data/')
    return body


def readme_status():
    brief = (ROOT/'knowledge/current_project_brief_2026-10-26.md').read_text()
    return ("<!-- CURRENT-REVIEW-2026-10-26 -->\n"
            "## Current decision — 2026-10-26\n\n"
            "**OK to download: YES for local testing only · OK to spend a weekly slot: NO — DO NOT SUBMIT.** "
            "Featured content-distinct H71 testing GeoTIFF [`gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif`](docs/downloads/gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif) "
            "(content id `9eb0c31e5149`; HOLDOUT-DTI FAIL vs H35; strict lane FAIL: 100% within 3 px of r13 lattice). The requested new submission TIF is **not produced**. "
            "[Nine-site executive review, non-estimable new-file score, and automated ROD result](docs/current-review.html) · "
            "[Current-checkout review](knowledge/29_current_checkout_review_2026-10-26.md) · "
            "[Repository review](knowledge/29_repository_review_2026-10-26.md) · "
            "[Current-checkout run card](registry/run_card_repo_review_2026-10-26_current.json) · "
            "[Repository-review run card](registry/run_card_repo_review_2026-10-26_session.json) · "
            "[Exact-download audit](knowledge/29_download_audit_and_next_hypotheses_2026-10-26.md) · "
            "[Strict-lane feasibility proof and hypothesis slate](knowledge/29_lane_feasibility_plan_2026-10-26.md) · "
            "[H71 outcomes](knowledge/28_h71_outcomes_2026-10-26.md) · "
            "[ROD run card](evidence/rod_2026-10-26/run_card.json) · "
            "[This review's machine-readable run card](registry/run_card_repo_review_2026-10-26_current.json). "
            "A separate merged parallel OLIC screen (draws 82–83) failed its frozen gate (+0.000849, 2/4 folds); no OLIC TIF was written. "
            "GEMSDOE32 B2 is the strongest supplied historical exemplar (**OWNER-REPORTED 0.2778**), not a new submission. "
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
