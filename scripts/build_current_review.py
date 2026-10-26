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
<span>No new candidate has cleared all required gates. Historical downloads are not new submissions.</span>
<a href="{prefix}current-review.html">Read the nine-site executive review &amp; automatic test result →</a></aside>'''


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
    budget_path = ROOT/'evidence/lane_budget_2026-10-26/budget.json'
    budget = json.loads(budget_path.read_text()) if budget_path.exists() else None
    d01_path = ROOT/'evidence/d01_density_2026-10-26/analysis.json'
    d01 = json.loads(d01_path.read_text()) if d01_path.exists() else None
    subs = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
    featured = next(s for s in subs if s["role"] == "primary")
    download = (
        f'<p><b>OK to download: YES</b> for local testing of unique content id '
        f'<code>{e(featured["content_id"])}</code>. '
        f'<b>OK to spend a weekly slot: NO — DO NOT SUBMIT.</b> '
        f'H71 HGPC-BLIND is format-valid and density-aware unique vs scored rasters; '
        f'three DIRECT screens failed vs H35. ROD/POL3 wrote no competition TIFF.</p>'
        f'<a class="btn" download href="downloads/{e(featured["file"])}">↓ Download {e(featured["file"])} — testing only</a>'
    )
    historical = 'gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif'
    rows, cards = [], []
    fname = e(featured['file'])
    rows.append(f'''<tr><th scope="row">This project</th>
<td class="submission-id"><a href="downloads/{fname}" download>{fname}</a></td>
<td>No leaderboard estimate exists. Proxy HOLDOUT-DTI is 0.13–0.15 and is <b>not</b> a score.<small>NOT A FORECAST</small></td>
<td><span class="badge b-ok">Yes — unique content id {e(featured["content_id"])}</span><small>density-aware check</small></td>
<td><span class="badge b-bad">NO — testing only</span></td></tr>''')
    for row in sorted(focus['sites'], key=lambda r: -r['owner_reported_score']):
        rows.append(f'''<tr><th scope="row"><a href="{e(row['site_url'])}">{e(row['site'])}</a></th>
<td class="submission-id">{e(row['submission'])}</td>
<td>{row['owner_reported_score']:.4f}<small>OWNER-REPORTED, historical. Not an estimate for a new file.</small></td>
<td><span class="badge b-warn">NO — earlier submission, not unique</span></td>
<td><span class="badge b-bad">DO NOT SUBMIT</span></td></tr>''')
        cards.append(f'''<article class="card"><h3>{e(row['site'])}</h3><p>{e(row['mechanism'])}</p>
<p class="small">{row['positive_pixels']:,} positive pixels · Local format checks: {'pass' if row['local_format_pass'] else 'fail'} ·
Not approved as a new submission. SHA-256: <code class="wrap-hash">{row['sha256']}</code></p>
<a href="{e(row['source_url'])}">Pinned source revision</a> · <a href="{e(row['site_url'])}">Original site</a></article>''')
    d01_rows, budget_dti, current_dti, paired, paired_ci = '', None, None, None, None
    if budget and d01:
        d01_rows = ''.join(
            f'<tr><td>{int(k):,}</td><td>{v["pooled_dti"]:.4f}</td>'
            f'<td>{v["ci95"][0]:.4f}–{v["ci95"][1]:.4f}</td><td>{v["emitted_median"]:,.0f}</td></tr>'
            for k, v in d01['arms'].items())
        lane_arm = d01['arms']['21713']
        cur_arm = d01['arms']['70524']
        budget_dti, current_dti = lane_arm['pooled_dti'], cur_arm['pooled_dti']
        paired, paired_ci = lane_arm['paired_gain_vs_current'], lane_arm['paired_ci95']
    body = f'''<section class="hero"><p class="eyebrow">RESEARCH DECISION BRIEF / 26 OCTOBER 2026</p>
<h1>Know what to submit.<br>Know when to stop.</h1>
<p class="lead">Nine focus sites, one auditable comparison, and a new geological test. No renamed reference files. No predicted leaderboard scores.</p></section>
<section class="review-decision"><span class="badge b-bad">OK TO SUBMIT: NO</span><h2>Unique research GeoTIFF is downloadable — not slot-cleared</h2>
<p>{e(featured['title'])}. {e(featured['summary'])}</p>
<p>ROD stop: {status}</p>{download}
<div class="row"><a class="btn" href="../evidence/rod_2026-10-26/run_card.json" download>Download decision receipt</a>
<a class="btn alt" href="#how-to-submit">Submission checklist</a></div></section>
<section><h2>What is the strongest historical evidence?</h2>
<p><b>GEMSDOE32 B2 — 0.2778, OWNER-REPORTED.</b> It is the highest supplied historical result among these focus sites.
It is already an earlier submission, so it is <b>not</b> eligible as a new unique artifact. No organizer receipt has been supplied.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Download, estimate, uniqueness and submit decision"><table><thead><tr><th>Source</th><th>File to download</th><th>Estimated leaderboard score</th><th>Unique as a new submission?</th><th>Submit?</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="small">No calibration maps any proxy number to this leaderboard: the private labels are unavailable and no organizer receipt exists, so an <b>estimate is stated as unavailable</b> rather than invented. Owner-reported historical scores are context, not predictions. Not a live leaderboard query and not a slot selection. The conflicting overall-leader claims 0.3195 and 0.4413 remain unverified.</p></section>
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
<section><h2>The novelty rule and the scoring objective are in direct conflict</h2>
<p>The literal rule is: more than 70% of a candidate's unique dots within 3 px of any one registry raster is a duplicate-lane stop.
An exact arithmetic audit of the restored registry (<a href="../evidence/lane_budget_2026-10-26/budget.json">budget.json</a>) finds the binding raster is
<code>{budget['binding_raster']['file']}</code>: its three-pixel halo covers <b>{budget['binding_raster']['coverage_fraction']*100:.4f}%</b> of the
{budget['eligible_domain_pixels']:,} eligible pixels, leaving only <b>{budget['binding_raster']['uncovered_pixels']:,}</b> outside.
With K unique dots at most U can lie outside, so the rule requires <code>10·max(0,K−U) ≤ 7·K</code>, i.e. <b>K ≤ {budget['binding_raster']['max_feasible_unique_dots']:,}</b>,
and that maximum is reachable only by placing a dot on <i>every</i> uncovered pixel. Anything larger cannot pass, whatever its geology or rank correlation.</p>
<p>The same-run density diagnostic (D01) then measures what that cap costs. <b>HOLDOUT-DTI</b>, shared evaluator α=0.2, β=0.8, 300 m kernel, four buffered
quadrants, draws 60/61; one fit per cell shared by every density, spacing 2.4 px:</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Density diagnostic"><table><thead><tr><th>Requested cap (full-footprint dots)</th><th>HOLDOUT-DTI</th><th>95% CI</th><th>Median emitted per quadrant</th></tr></thead><tbody>
{d01_rows}</tbody></table></div>
<p>The lane-compatible cap gives <b>{budget_dti:.4f}</b> versus <b>{current_dti:.4f}</b> at the current request — paired difference
<b>{paired:+.4f}</b>, 95% CI [{paired_ci[0]:+.4f}, {paired_ci[1]:+.4f}], worse in every quadrant and both draws.
Uniform thinning is therefore <b>not</b> a route to a higher score; the earlier B2 result is better explained by selective near-catalogue collar pruning than by uniform density reduction,
and even that remains a conditional explanation without the private labels. Requested caps saturate at available ridge candidates, so this orders density regimes rather than simulating one exact file.</p>
<p>No density exception was applied and no dots were moved to evade the registry. <b>This is a policy decision for the owner</b>: either exclude the synthetic sibling lattice from the lane
registry (reporting it separately), or replace the literal rule with a symmetric density-aware statistic. Until one is chosen, no competitive candidate can be both lane-clean and high-scoring,
so no new TIF is asserted as submittable.</p></section>
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
            "**OK to download: YES · OK to spend a weekly slot: NO — DO NOT SUBMIT.** "
            "Featured unique GeoTIFF [`gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif`](docs/downloads/gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif) "
            "(content id `9eb0c31e5149`; HOLDOUT-DTI FAIL vs H35; 0 NaN in footprint, values in [0,1]). "
            "[Executive review with the download/estimate/uniqueness table](docs/current-review.html) · "
            "[D01 lane-budget and density outcome](knowledge/31_d01_outcome_2026-10-26.md) · "
            "[lane budget receipt](evidence/lane_budget_2026-10-26/budget.json) · "
            "[D01 run card](evidence/d01_density_2026-10-26/run_card.json). "
            "The literal 70%/3 px lane rule caps any candidate at 21,713 unique dots against the restored lattice, "
            "and the density diagnostic puts that cap at HOLDOUT-DTI 0.0859 vs 0.1321 at the current request, so no "
            "competitive file can be both lane-clean and high-scoring until the owner chooses a registry policy. "
            "No leaderboard estimate is available: the private labels and organizer receipts are absent. "
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
