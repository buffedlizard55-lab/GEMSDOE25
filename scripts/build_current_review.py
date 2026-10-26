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
    subs = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
    featured = next(s for s in subs if s["role"] == "primary")
    download = (
        f'<p><b>OK to download: YES</b> for local testing of unique content id '
        f'<code>{e(featured["content_id"])}</code>. '
        f'<b>OK to spend a weekly slot: NO — DO NOT SUBMIT.</b> '
        f'The objective-lane BIN greedy candidate is format-valid and unique vs scored/external rasters; '
        f'three training-objective screens failed vs the same-run BIN comparator, so it is not slot-cleared.</p>'
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
<p class="lead">Nine focus sites, one auditable comparison, and a new geological test. No renamed reference files. No predicted leaderboard scores.</p></section>
<section class="review-decision"><span class="badge b-bad">OK TO SUBMIT: NO</span><h2>Unique research GeoTIFF is downloadable — not slot-cleared</h2>
<p>{e(featured['title'])}. {e(featured['summary'])}</p>
<p>Prior-session ROD stop: {status}</p>{download}
<div class="row"><a class="btn" href="../evidence/rod_2026-10-26/run_card.json" download>Download decision receipt</a>
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
<section><h2>New test: radiometric offset discontinuity</h2>
<p>Does a compositional pattern match better after sliding one side of a scarp along strike? The preregistered ROD test uses cached K/Th/U and LiDAR step/coherence,
not a copied prediction mask. Volcanic flow lobes, sediment sorting and survey seams can mimic this signature.</p>
{outcome}<p><a href="../knowledge/27_preregistered_rod_2026-10-26.md">Four ranked hypotheses &amp; frozen design</a> ·
<a href="../evidence/rod_2026-10-26/feature_canaries.json">Every-feature leakage canaries</a> ·
<a href="../evidence/rod_2026-10-26/surface_lane.json">Pre-placement surface audit</a></p></section>
{pol3_section}
{obj_section}
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
            "Featured unique GeoTIFF [`gems25-obj-bin-greedy-k3p5-20261026-3646faf70507-zeros.tif`](docs/downloads/gems25-obj-bin-greedy-k3p5-20261026-3646faf70507-zeros.tif) "
            "(content id `3646faf70507`; frozen H35/H38 stack, fresh production seeds). Three pre-registered training-objective screens all failed vs the same-run BIN comparator "
            "(TENT -0.0003, HARDNEG -0.0427, IGN3 -0.0009 paired fold-mean HOLDOUT-DTI; leakage canaries <= 0.63 PASS). "
            "The file is unique vs every scored/external registry raster (worst 3-px overlap 69.2% <= 70%; 32.0% vs GEMSDOE32 B2); the strict lane still fails vs this repo's own unscored H38 greedy file (87.2%) and the dense r13 lattice (100%, `IR-25-LANE-DENSITY`). "
            "[Nine-site executive review](docs/current-review.html) · "
            "[Objective-session outcomes + executive summary](knowledge/31_objective_outcomes_and_executive_summary_2026-10-26.md) · "
            "[Run card](registry/run_card_objective_2026-10-26.json). "
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
