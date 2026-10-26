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
    obj_path = ROOT/'registry/run_card_objective_2026-10-26.json'
    objc = json.loads(obj_path.read_text()) if obj_path.exists() else None
    obj_section = ''
    if objc:
        ex = objc['experiments']
        obj_rows = []
        for key, label in (('experiment_1_tent', '<b>Exp 1 TENT</b> (kernel-regression target)'),
                           ('experiment_2_hardneg', '<b>Exp 2 HARDNEG</b> (hard-negative mining)'),
                           ('experiment_3_ign3', '<b>Exp 3 IGN3</b> (ring-excluded negatives)')):
            x = ex[key]
            obj_rows.append(f"""<tr><td>{label}</td><td><code>{e(str(x['draws']))}</code> / {x['withheld_positives_total']:,}</td>
<td>{x['leakage_canary']['max_effective_auc']:.4f}</td>
<td>{x['candidate_greedy']['pooled_dti']:.6f}</td><td>{x['bin_greedy']['pooled_dti']:.6f}</td>
<td>{x['paired']['mean_gain']:+.6f} [{x['paired']['ci95'][0]:+.4f}, {x['paired']['ci95'][1]:+.4f}] ({x['paired']['folds_positive']}/4)</td>
<td><span class="badge b-bad">SCREEN FAIL</span></td></tr>""")
        fd = objc['registry_correlation_and_overlap']['final_dots']
        ext, b2o = fd['external_sparse'], fd['vs_gemsdoe32_b2']
        obj_section = f"""<section class="card"><p class="eyebrow">SEPARATE BRANCH SESSION · THREE SCREENS · 3/3 EXPERIMENT BUDGET</p>
<h2>Training-objective geometry (TENT / HARDNEG / IGN3) — three negatives</h2>
<p><b>HOLDOUT-DTI</b>, evaluator <code>{e(ex['experiment_1_tent']['evaluator_version'])}</code>.
Hypothesis (pre-registered before any fit): the binary classifier labels genuine scarp-crest pixels
1.5&ndash;3&nbsp;px off the cartographic catalogue trace as negatives although the metric pays inside 300&nbsp;m.
TENT prices the credit ring with the metric's own triangular kernel; HARDNEG mines fault-like non-fault
lineaments (roads, shoreline benches, contacts, survey seams); IGN3 excludes the ring from supervision.
Detector columns and greedy emission are frozen; every comparator is recomputed in the same run.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Objective session experiments"><table><thead><tr>
<th>Experiment</th><th>Draws / withheld +</th><th>Canary max</th><th>Candidate pooled</th>
<th>Same-run BIN pooled</th><th>Paired fold-mean gain [95% CI] (folds +)</th><th>Verdict</th></tr></thead>
<tbody>{''.join(obj_rows)}</tbody></table></div>
<p>No variant beat the incumbent, so no confirmation draws ran (92&ndash;93 / 96&ndash;97 / 102&ndash;103 permanently unused),
no objective-scheme TIF was built, and no slot is supported. The featured download is the incumbent stack
rebuilt with fresh production seeds. It is unique vs scored/external rasters (worst 3-px overlap
{100*ext['worst_cand_dots_within_3px']:.1f}% &le; 70%; {100*b2o['cand_dots_within_3px']:.1f}% vs GEMSDOE32 B2) but the strict lane
fails vs this repo's own unscored HGB lineage and the dense lattice. This is a catalogue-gap proxy, not a competition score.</p>
<p><a href="../knowledge/29_ranked_hypotheses_and_preregistration_2026-10-26.md">Frozen preregistration</a> ·
<a href="../knowledge/31_objective_outcomes_and_executive_summary_2026-10-26.md">Outcomes &amp; nine-site executive summary</a> ·
<a href="../registry/run_card_objective_2026-10-26.json">Run card</a> ·
<a href="../evidence/focus_audit_local_2026-10-26.json">This session's nine-site raster audit</a>.</p></section>
"""
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
        f'The objective-lane BIN greedy candidate is format-valid and unique vs scored/external rasters; '
        f'three training-objective screens failed vs the same-run BIN comparator, so it is not slot-cleared.'
        f' ROD/POL3/OLIC/D01 wrote no new competition TIFF.</p>'
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

    apfl2_path = ROOT/'registry/run_card_apfl2_2026-10-26.json'
    apfl2 = json.loads(apfl2_path.read_text()) if apfl2_path.exists() else None
    apfl2_section = ''
    if apfl2:
        x1 = apfl2['holdout_dti']['exp1_direct']
        x2 = apfl2['holdout_dti']['exp2_hgb']
        cnd, ctl = x2['candidate'], x2['control_h35']
        apfl2_section = f'''<section class="card"><p class="eyebrow">PARALLEL SESSION · APFL LANE · TWO FROZEN SCREENS + OCEM DIAGNOSTIC · NEGATIVE</p>
<h2>APFL piedmont-flexure completion — both screens negative</h2>
<p><b>Exp 1 (DIRECT, draws 60–61):</b> HOLDOUT-DTI <code>{x1['candidate']['pooled_dti']:.6f}</code> vs same-run H35 <code>{x1['control_h35']['pooled_dti']:.6f}</code> (gain {x1['gate']['mean_gain']:+.4f}, {x1['gate']['folds_positive']}/4 folds) — FAIL.
<b>Exp 2 (H35+APFL columns, draws 62–63):</b> HOLDOUT-DTI <code>{cnd['pooled_dti']:.6f}</code> [{cnd['ci_95'][0]:.4f}, {cnd['ci_95'][1]:.4f}], {cnd['withheld_positives']:,} withheld positives, vs H35 <code>{ctl['pooled_dti']:.6f}</code> (gain {x2['gate']['mean_gain']:+.4f}, {x2['gate']['folds_positive']}/4 folds) — FAIL.
Canary max AUC {x1['canary']['max_feature_auc']:.3f} / {x2['canary']['max_feature_auc']:.3f} (≤0.90). Evaluator <code>gems25.holdout.v1.2-buffered-4quad-pooled-dti</code>. Catalogue-gap proxy only — not a leaderboard score or estimate.</p>
<p><b>Exp 3 (OCEM diagnostic):</b> B=2 collar with budget refill is ~neutral on this proxy; the live B2 effect was deletion without refill. A ≥200 m off-catalogue truth restriction is vacuous here.</p>
<p><a href="../knowledge/29_preregistered_apfl_completion_2026-10-26.md">Pre-registration</a> ·
<a href="../knowledge/30_executive_summary_and_apfl_outcomes_2026-10-26.md">Executive summary &amp; outcomes (knowledge/30)</a> ·
<a href="../registry/run_card_apfl2_2026-10-26.json">Run card</a> ·
<a href="../evidence/focus_audit_session_2026-10-26.json">Fresh nine-site pixel audit</a>.</p></section>'''
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
    d01_path = ROOT/'evidence/d01_density_2026-10-26/analysis.json'
    d01_section = ''
    if d01_path.exists():
        d01 = json.loads(d01_path.read_text())
        d01_rows = ''.join(
            f'<tr><td>{int(k):,}</td><td>{v["pooled_dti"]:.4f}</td>'
            f'<td>{v["ci95"][0]:.4f}–{v["ci95"][1]:.4f}</td><td>{v["emitted_median"]:,.0f}</td></tr>'
            for k, v in d01['arms'].items())
        lane_arm, cur_arm = d01['arms']['21713'], d01['arms']['70524']
        d01_section = f'''<section id="d01-density"><h2>New test: what the lane budget costs in proxy performance</h2>
<p>The strict gate alone does not say whether a lane-clean file could be competitive, so the preregistered D01 diagnostic measured the incumbent H35 surface at seven fixed emission caps.
One fit per buffered quadrant, draws 60/61, spacing 2.4 px, every feature canary passed (maximum AUC 0.8025). <b>HOLDOUT-DTI</b>, α=0.2, β=0.8, 300 m kernel:</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="D01 density response"><table><thead><tr><th>Requested cap (full-footprint dots)</th><th>HOLDOUT-DTI</th><th>95% CI</th><th>Median emitted per quadrant</th></tr></thead><tbody>{d01_rows}</tbody></table></div>
<p>The lane-compatible cap gives <b>{lane_arm['pooled_dti']:.4f}</b> versus <b>{cur_arm['pooled_dti']:.4f}</b> at the current request: paired difference
<b>{lane_arm['paired_gain_vs_current']:+.4f}</b>, 95% CI [{lane_arm['paired_ci95'][0]:+.4f}, {lane_arm['paired_ci95'][1]:+.4f}], worse in every quadrant and both draws.
Uniform thinning is therefore <b>not</b> a route to a higher score; the reported B2 gain is better explained by selective near-catalogue collar pruning than by uniform density reduction.
Requested caps saturate at available ridge candidates, so this orders density regimes rather than simulating one exact file (recorded as IR-26-REQUESTED-CAP-SATURATION).</p>
<p><a href="../knowledge/31_d01_outcome_2026-10-26.md">Scientific write-up and the policy decision required</a> ·
<a href="../evidence/d01_density_2026-10-26/run_card.json">D01 run card</a> ·
<a href="../evidence/d01_density_2026-10-26/analysis.json">Full paired results and evaluator hashes</a></p></section>'''
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
<p>Prior-session ROD stop: {status}</p>{download}
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
{d01_section}
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
{obj_section}
{olic_section}
{apfl2_section}
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
<li><a href="../evidence/focus_audit_local_2026-10-26.json">This branch's independent nine-site raster re-audit</a> — computed geometry from SHA-pinned local mirrors; scores remain OWNER-REPORTED.</li>
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
            "**OK to download: YES · OK to spend a weekly slot: NO — DO NOT SUBMIT.** "
            "Featured unique GeoTIFF [`gems25-obj-bin-greedy-k3p5-20261026-3646faf70507-zeros.tif`](docs/downloads/gems25-obj-bin-greedy-k3p5-20261026-3646faf70507-zeros.tif) "
            "(content id `3646faf70507`; frozen H35/H38 stack, fresh production seeds). Three pre-registered training-objective screens all failed vs the same-run BIN comparator "
            "(TENT -0.0003, HARDNEG -0.0427, IGN3 -0.0009 paired fold-mean HOLDOUT-DTI; leakage canaries <= 0.63 PASS). "
            "The file is unique vs every scored/external registry raster (worst 3-px overlap 69.2% <= 70%; 32.0% vs GEMSDOE32 B2); the strict lane still fails vs this repo's own unscored H38 greedy file (87.2%) and the dense r13 lattice (100%, `IR-25-LANE-DENSITY`). "
            "[Nine-site executive review](docs/current-review.html) · "
            "[Objective-session outcomes + executive summary](knowledge/31_objective_outcomes_and_executive_summary_2026-10-26.md) · "
            "[Run card](registry/run_card_objective_2026-10-26.json). "
            "[Current-checkout review](knowledge/29_current_checkout_review_2026-10-26.md) · "
            "[Repository review](knowledge/29_repository_review_2026-10-26.md) · "
            "[Exact-download audit](knowledge/29_download_audit_and_next_hypotheses_2026-10-26.md) · "
            "[Strict-lane feasibility proof](knowledge/29_lane_feasibility_plan_2026-10-26.md) · "
            "[D01 density outcome](knowledge/31_d01_outcome_2026-10-26.md) · "
            "[H71 outcomes](knowledge/28_h71_outcomes_2026-10-26.md). "
            "Parallel merged sessions: OLIC screen (draws 82–83) failed its frozen gate (+0.000849, 2/4 folds) and D01 density diagnostic was negative; neither wrote a TIF. "
            "Parallel APFL session: two screens failed (0.045617 / 0.148880 HOLDOUT-DTI); its unique testing TIF `2e9e4189f554` is registered alternate — [executive summary](knowledge/30_executive_summary_and_apfl_outcomes_2026-10-26.md) · [run card](registry/run_card_apfl2_2026-10-26.json). "
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
