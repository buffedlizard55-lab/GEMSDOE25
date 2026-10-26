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
<strong>26 OCT 2026 · RESEARCH-ARCHIVE DOWNLOAD: YES (INSPECTION ONLY) · COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT</strong>
<span>Latest H74-SUBSURF research GeoTIFF <code>3751606e1ce5</code> (37,654 dots; density-aware unique across all 101 rasters, <code>flagged_lane = []</code>, 23.63% vs B2) and archived H72-3 <code>88bbebfe79b4</code> are available for local inspection only — both failed the same-run H35 slot gate and the literal 99.87%-lattice rule; no weekly slot is approved.</span>
<a href="{prefix}executive-summary.html">Open Executive Summary, downloads, 9-site table, 0.2778 PhD proof &amp; H74 run card →</a></aside>'''


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
    h72_path = ROOT / "registry" / "run_card_h72_2026-10-26.json"
    h72 = json.loads(h72_path.read_text()) if h72_path.exists() else None
    h72_section = ""
    h72_table_row = ""
    if h72:
        e1 = json.loads((ROOT / "evidence/h72_1_screen/analysis.json").read_text())
        e2 = json.loads((ROOT / "evidence/h72_2_screen/analysis.json").read_text())
        e3 = json.loads((ROOT / "evidence/h72_3_screen/analysis.json").read_text())
        lane_lit = json.loads((ROOT / featured["lane"]["receipt"]).read_text())
        h23_ov = next(r["dots_within_3px"] for r in lane_lit["rows"] if r["file"] == "h23-a-6pct.tif")
        rc72 = h72["correlation_overlap_vs_registry"]
        top21 = rc72["focus_21_top_scorers"]
        own72 = rc72["own_lineage"]
        w1 = len(e1["draws"]) * sum(e1["withheld_positives_per_fold"].values())
        w2 = len(e2["draws"]) * sum(e2["withheld_positives_per_fold"].values())
        w3 = len(e3["draws"]) * sum(e3["withheld_positives_per_fold"].values())
        c1_auc = max(e1["leakage_canary"]["max_effective_auc"].values())
        c2_auc = max(e2["leakage_canary"]["max_effective_auc"].values())
        c3_auc = max(e3["leakage_canary"]["max_effective_auc"].values())
        hd72 = h72["holdout_dti"]
        lane_extended = json.loads((ROOT/'evidence/h72_3_lane_extended.json').read_text())
        r13_overlap = lane_extended['lattice'][0]['cand_dots_within_3px']
        sparse_overlap = lane_extended['external_sparse']['worst_cand_dots_within_3px']
        sparse_overlap_file = lane_extended['external_sparse']['worst_overlap_file']
        h72_table_row = f"""<tr><td class="submission-id">{e(featured['file'])}</td>
<td>NOT ESTIMATED — no calibrated leaderboard projection</td>
<td>HOLDOUT-DTI {hd72['pooled_dti']:.6f}; evaluator {e(hd72['evaluator_version'])}; {hd72['withheld_positive_occurrences']:,} withheld positives; 95% CI [{hd72['ci95'][0]:.6f}, {hd72['ci95'][1]:.6f}]</td>
<td><b>NO.</b> Literal 70% / 3-px uniqueness fails: {100*r13_overlap:.2f}% of final dots are within 3 px of the registered r13 lattice; the sparse-registry maximum is {100*sparse_overlap:.2f}% vs <code>{e(sparse_overlap_file)}</code>. No density-aware exception applies.</td>
<td><b>DO NOT SUBMIT.</b> Holdout failed vs H35; archived research artifact only.</td></tr>"""
        h72_section = f'''<section class="card"><p class="eyebrow">PRIOR SESSION · 3 PRE-REGISTERED EXPERIMENTS (DRAWS 80–85) · ARCHIVED RESEARCH ARTIFACT, NOT ELIGIBLE</p>
<h2>H72 Unit-Consistent Tensor Gradient, Valley-Crossing Contrast &amp; DEM-Free Magnetic Depth-Splay</h2>
<p><b>Pre-registered before fitting:</b>
<a href="../knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md">4 ranked hypotheses &amp; H72-1/2 design (<code>53cb884</code>)</a> ·
<a href="../knowledge/30_preregistered_h72_3_subsurf_blind_2026-10-26.md">H72-3 DEM-free subsurface design (<code>fc60bdd</code>)</a> ·
<a href="../knowledge/31_h72_outcomes_and_portfolio_synthesis_2026-10-26.md">Full PhD 0.2778 proof, how to beat 0.2778 &amp; 9-site synthesis</a> ·
<a href="../registry/run_card_h72_2026-10-26.json">H72 JSON Run Card</a> ·
<a href="../registry/review_passes_h72_2026-10-26.json">3-pass review receipt</a>.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Four ranked H72 geological hypotheses">
<table><thead><tr><th>Rank</th><th>Hypothesis &amp; Cached Layers</th><th>Physical Signature &amp; Why Catalogue Misses It</th><th>Named Non-Fault Mimic</th><th>Repo Novelty, Cost &amp; Official Data</th><th>Expected ΔDTI / Status</th></tr></thead>
<tbody>
<tr><td><b>1</b></td><td><b>H72-A · PTTG-DR</b><br><small>Bands 02, 03, 09, 10, 11, 12, 16, 17</small></td><td>Unit-consistent isotropic gravity/magnetic THDR + Phillips horizontal differential curvature <code>K_diff</code> (fixes <code>r=+0.948</code> E–W directional bias of band 18 and ~40&times; TMI unit mismatch) + de-aproned OOF HGB; catches concealed pediment/playa &amp; E–W transfer faults.</td><td>Caldera ring-fracture walls, pluton aureoles, basaltic feeder dikes</td><td>First rotationally invariant gravity tensor curvature + propensity-de-aproned HGB; ~16 min CPU; cached GDR #1391 potential fields.</td><td><code>+0.003..+0.012</code><br><b>Exp 1:</b> <code>+0.0061</code> vs Blind (4/4); FAIL vs H35</td></tr>
<tr><td><b>2</b></td><td><b>H72-B · VCCD + RBDT</b><br><small>Bands 01, 02, 05, 06, 07, 13, 14, 15, 19</small></td><td>Anisotropic across- vs along-strike Mahalanobis step in K/Th/U + 2 m temperature + heatflow gated by 100 m LiDAR scarp coherence; catches active range-front/relay splays vs contour-parallel shorelines.</td><td>Pluvial Lake Lahontan/Bonneville shorelines, welded tuff cooling units, fan toes</td><td>Across/along-strike contrast ratio rather than isotropic gradient or ROD shift; ~16 min CPU; cached USGS NURE + 3DEP 100 m LiDAR.</td><td><code>+0.002..+0.008</code><br><b>Exp 2:</b> <code>+0.0073</code> vs Blind (4/4); <code>+0.0005</code> vs H35 (2/4)</td></tr>
<tr><td><b>3</b></td><td><b>H72-C · MTHS</b><br><small>Bands 03, 09, 10, 11, 12, 17 (zero DEM/LiDAR)</small></td><td>Multi-scale upward-continued (200 m / 600 m / 1.5 km) magnetic tilt-zero lateral depth-splay + strike-coherent gravity curvature; catches blind steeply dipping intrabasinal faults beneath alluvial fans while structurally immune to DEM-scarp ribbon collisions.</td><td>Tilted ash-flow tuff sheets, buried pluton roof pendants, paleochannel basalts</td><td>First multi-altitude upward-continued magnetic tilt-locus migration (zero DEM/LiDAR/Family E); ~7 min CPU; cached GDR #1391 potential fields.</td><td><code>+0.001..+0.006</code> vs Subsurf<br><b>Exp 3:</b> <code>+0.0014</code> vs Subsurf, <code>flagged_lane=[]</code>; FAIL vs H35</td></tr>
<tr><td><b>4</b></td><td><b>H72-D · BDFP</b><br><small>Bands 02, 10, 11, 12, 16, 19</small></td><td>Paired antithetic gravity inflection across narrow intrabasinal horsts/step-overs weighted by strain rate; catches buried accommodation relays.</td><td>Exhumed metamorphic core-complex domes, dense carbonate horst blocks</td><td>Pairs opposing signed second-derivative walls across 0.8–3.0 km basin horsts; ~15 min CPU; cached GDR #1391 gravity + Kreemer strain.</td><td><code>0.000..+0.005</code><br>Reserve (3/3 budget cap)</td></tr>
</tbody></table></div>
<div class="table-scroll" tabindex="0" role="region" aria-label="H72 3-experiment holdout results">
<table><thead><tr><th>Exp / Draws</th><th>Candidate Arm</th><th>Withheld +</th><th>Canary Max</th><th>Candidate HOLDOUT-DTI [95% CI]</th><th>Same-Run Control(s)</th><th>Paired Contrast (Folds +)</th><th>Verdict</th></tr></thead>
<tbody>
<tr><td><b>Exp 1</b> <code>[80, 81]</code></td><td><code>A3_PTTG_DEAPRON</code></td><td>{w1:,}</td><td>{c1_auc:.4f}</td><td><code>{e1['arms']['A3_PTTG_DEAPRON']['mean_dti']:.5f}</code> [{e1['arms']['A3_PTTG_DEAPRON']['ci95_dti'][0]:.4f}, {e1['arms']['A3_PTTG_DEAPRON']['ci95_dti'][1]:.4f}]</td><td>Blind: <code>{e1['arms']['CTRL_BLIND_BD']['mean_dti']:.5f}</code><br>H35: <code>{e1['arms']['CTRL_H35']['mean_dti']:.5f}</code></td><td><b><code>{e1['contrasts']['A3_PTTG_DEAPRON_vs_CTRL_BLIND_BD']['mean']:+.5f}</code></b> vs Blind ({e1['contrasts']['A3_PTTG_DEAPRON_vs_CTRL_BLIND_BD']['folds_positive']}/4)<br><code>{e1['contrasts']['A3_PTTG_DEAPRON_vs_CTRL_H35']['mean']:+.5f}</code> vs H35 ({e1['contrasts']['A3_PTTG_DEAPRON_vs_CTRL_H35']['folds_positive']}/4)</td><td><span class="badge b-warn">Blind PASS / H35 FAIL</span></td></tr>
<tr><td><b>Exp 2</b> <code>[82, 83]</code></td><td><code>B3_FULL_DEAPRON</code></td><td>{w2:,}</td><td>{c2_auc:.4f}</td><td><code>{e2['arms']['B3_FULL_DEAPRON']['mean_dti']:.5f}</code> [{e2['arms']['B3_FULL_DEAPRON']['ci95_dti'][0]:.4f}, {e2['arms']['B3_FULL_DEAPRON']['ci95_dti'][1]:.4f}]</td><td>Blind: <code>{e2['arms']['CTRL_BLIND_BD']['mean_dti']:.5f}</code><br>H35: <code>{e2['arms']['CTRL_H35']['mean_dti']:.5f}</code></td><td><b><code>{e2['contrasts']['B3_FULL_DEAPRON_vs_CTRL_BLIND_BD']['mean']:+.5f}</code></b> vs Blind ({e2['contrasts']['B3_FULL_DEAPRON_vs_CTRL_BLIND_BD']['folds_positive']}/4)<br><code>B1</code> vs H35: <code>{e2['contrasts']['B1_FULL_H35_vs_CTRL_H35']['mean']:+.5f}</code> ({e2['contrasts']['B1_FULL_H35_vs_CTRL_H35']['folds_positive']}/4)</td><td><span class="badge b-warn">Blind PASS / H35 FAIL</span></td></tr>
<tr><td><b>Exp 3</b> <code>[84, 85]</code></td><td><b><code>C1_SUBSURF_PTTG_MTHS</code></b></td><td>{w3:,}</td><td>{c3_auc:.4f}</td><td><code>{e3['arms']['C1_SUBSURF_PTTG_MTHS']['mean_dti']:.5f}</code> [{e3['arms']['C1_SUBSURF_PTTG_MTHS']['ci95_dti'][0]:.4f}, {e3['arms']['C1_SUBSURF_PTTG_MTHS']['ci95_dti'][1]:.4f}]</td><td>Subsurf: <code>{e3['arms']['CTRL_SUBSURF_D']['mean_dti']:.5f}</code><br>H35: <code>{e3['arms']['CTRL_H35']['mean_dti']:.5f}</code></td><td><code>{e3['contrasts']['C1_SUBSURF_PTTG_MTHS_vs_CTRL_SUBSURF_D']['mean']:+.5f}</code> vs Subsurf ({e3['contrasts']['C1_SUBSURF_PTTG_MTHS_vs_CTRL_SUBSURF_D']['folds_positive']}/4)<br><code>{e3['contrasts']['C1_SUBSURF_PTTG_MTHS_vs_CTRL_H35']['mean']:+.5f}</code> vs H35 ({e3['contrasts']['C1_SUBSURF_PTTG_MTHS_vs_CTRL_H35']['folds_positive']}/4)</td><td><span class="badge b-bad">H35 FAIL · STRICT LANE FAIL</span></td></tr>
</tbody></table></div>
<p class="small"><b>Literal global lane outcome: FAIL.</b> Surface/final rank-correlation maxima are {rc72['surface_max_abs_spearman']:.5f} / {rc72['final_max_abs_spearman']:.5f} (below 0.90), but final-dot overlap exceeds 70%: {100*sparse_overlap:.2f}% vs <code>{e(sparse_overlap_file)}</code> and {100*r13_overlap:.2f}% vs the r13 lattice. The separate density-aware subset comparison ({100*top21['b2_overlap']:.2f}% vs B2; {100*top21['worst_cand_dots_within_3px']:.2f}% max across {top21['n']} sibling top-scorers; {100*own72['worst_cand_dots_within_3px']:.2f}% max across {own72['n']} own-lineage rasters; {100*h23_ov:.2f}% vs <code>h23-a-6pct</code>) does not waive this strict stop.</p></section>'''
    h72_cf_path = ROOT / "registry" / "run_card_h72_cf_2026-10-26.json"
    h72_cf = json.loads(h72_cf_path.read_text()) if h72_cf_path.exists() else None
    h72_cf_section = ""
    if h72_cf:
        hm = h72_cf["holdout_dti"]["screen_and_confirm_H72_with_H35"]
        cf = h72_cf["holdout_dti"]["shipped_catfree_detector_family"]
        fl = h72_cf["correlation_overlap_vs_registry"]["final_dots"]
        h72_cf_section = f'''<section class="card"><p class="eyebrow">PARALLEL H72-CF LANE · 3/3 PRE-REGISTERED EXPERIMENTS · UNIQUE NEGATIVE ALTERNATE</p>
<h2>MBSP-MTG macro-basin scarp + concealed MT/gravity/swarm damage</h2>
<p>The six H72-CF columns replicated as an add-on to H35: <b>HOLDOUT-DTI</b> <code>{hm['candidate_pooled']:.6f}</code>
[<code>{hm['candidate_ci95'][0]:.4f}, {hm['candidate_ci95'][1]:.4f}</code>] vs same-run H35 <code>{hm['same_run_h35_pooled']:.6f}</code>;
paired <code>{hm['paired_gain']:+.6f}</code> [<code>{hm['paired_gain_ci95'][0]:+.4f}, {hm['paired_gain_ci95'][1]:+.4f}</code>],
{hm['withheld_positive_occurrences']:,} withheld-positive occurrences. But the downloadable 100% CatFree detector family is
<code>{cf['candidate_pooled']:.6f}</code> vs H35 <code>{cf['same_run_h35_pooled']:.6f}</code>
(paired <code>{cf['paired_gain_vs_H35']:+.6f}</code>, 0/4 folds): performance gate FAIL.</p>
<p><b>Alternate testing file:</b> <a download href="downloads/{e(h72_cf['submission_name'])}"><code>{e(h72_cf['submission_name'])}</code></a>
(content <code>{e(h72_cf['raster']['content_id'])}</code>, SHA-256 <code>{e(h72_cf['raster']['sha256'])}</code>).
No defensible leaderboard estimate exists. Content is unique vs prior registry; final dots clear 27 focus/top rasters (max
{100*fl['focus_and_top_scorers_27']['max_candidate_dots_within_3px']:.1f}%) and own lineage ({100*fl['own_lineage']['max_candidate_dots_within_3px']:.1f}%),
but strict lane fails the lattice and four broad historical artifact halos. <b>OK TO DOWNLOAD: YES (testing) · OK TO SUBMIT: NO — DO NOT SUBMIT.</b></p>
<p><a href="../knowledge/29_h72_cf_hypotheses_and_preregistration_2026-10-26.md">Five ranked hypotheses &amp; preregistration</a> ·
<a href="../knowledge/30_h72_cf_outcomes_and_executive_decision_2026-10-26.md">Outcomes and nine-site decision</a> ·
<a href="../registry/run_card_h72_cf_2026-10-26.json">H72-CF run card</a>.</p></section>'''

    h74_path = ROOT / "registry" / "run_card_h74_2026-10-26.json"
    h74 = json.loads(h74_path.read_text()) if h74_path.exists() else None
    h74_download_box = ""
    h74_table_row = ""
    h74_section = ""
    if h74:
        hd74 = h74["holdout_dti"]
        x1_74 = hd74["experiment_1_standard_holdout"]
        x2_74 = hd74["experiment_2_block25km_holdout"]
        x3_74 = hd74["experiment_3_subsurf_block25km_shipped_family"]
        ln74 = h74["correlation_overlap_vs_registry"]
        fw74 = ln74["focus_winners"]
        ext74 = ln74["external_sparse"]
        own74 = ln74["own_lineage"]
        sh74 = x2_74["apron_advantage_collapse"]
        nid74 = "note-research-h74"
        h74_download_box = (
            f'<div class="card" style="border-left:4px solid #b91c1c;margin-bottom:14px">'
            f'<p class="eyebrow">LATEST SESSION DELIVERABLE · H74 RMPS-BFP SUBSURFACE LOQO B2 (3/3 BUDGET COMPLETE)</p>'
            f'<h3>New Unique Research GeoTIFF: <code>{e(h74["submission_name"])}</code> — OK TO DOWNLOAD (TESTING): YES · OK TO SUBMIT: NO — DO NOT SUBMIT</h3>'
            f'<p>Content id <code>{e(h74["content_id"])}</code> · <code>{h74["positive_pixels"]:,}</code> binary dots · '
            f'SHA-256 <code>{e(h74["raster_sha256"][:16])}…</code> · EPSG:32611 · <code>3730&times;3292</code> · '
            f'0 NaN/Inf inside 5,167,373-px footprint · all values in <code>[0, 1]</code> · '
            f'51 static topography-free &amp; catalogue-free subsurface columns (zero Family B DEM/LiDAR, zero Family E catalogue). '
            f'<b>Density-aware unique across all {ln74["registry_checked"]} rasters</b> (<code>flagged_lane = []</code>; '
            f'surface |&rho;| &le; {ln74["surface_worst_abs_spearman"]:.4f}; {100*fw74["b2_overlap"]:.2f}% vs GEMSDOE32 B2; '
            f'{100*ln74["vs_prior_subsurface_h72_3"]["cand_dots_within_3px"]:.2f}% vs H72-3-subsurf; '
            f'{100*own74["worst_cand_dots_within_3px"]:.2f}% max own-lineage; {100*ext74["worst_cand_dots_within_3px"]:.2f}% max sparse external), '
            f'while literal 70% flags the 3 &gt;73%-halo rasters (r13 lattice 100%, pindrop 76.2%). '
            f'<b>Verdict: <code>{e(h74["verdict"])}</code> · OK to spend a weekly slot: NO — DO NOT SUBMIT.</b></p>'
            f'<div class="row">'
            f'<a class="btn" download href="downloads/{e(h74["submission_name"])}">↓ Download H74 unique research TIF (zeros outside) — DO NOT SUBMIT</a> '
            f'<a class="btn alt" download href="downloads/{e(h74["nan_twin_name"])}">↓ NaN-outside twin ({e(h74["nan_twin_name"])})</a> '
            f'<a class="btn alt" download href="downloads/{e(h74["zip_name"])}">↓ Single-TIFF ZIP ({e(h74["zip_name"])})</a> '
            f'<a class="btn alt" download href="../registry/run_card_h74_2026-10-26.json">↓ H74 JSON Run Card</a> '
            f'<a class="btn alt" href="../knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md">Full H74 report &amp; 0.2778 PhD proof</a>'
            f'</div>'
            f'<p class="small" style="margin:8px 0 2px"><b>DrivenData-format research identifier ({h74["note_chars"]} chars &le; 120 — DO NOT SUBMIT):</b> '
            f'<button class="btn alt small" data-copy="{nid74}">Copy H74 research note</button></p>'
            f'<div class="note"><code id="{nid74}">{e(h74["note"])}</code></div></div>'
        )
        h74_table_row = (
            f'<tr><td class="submission-id">{e(h74["submission_name"])}</td>'
            f'<td>NOT ESTIMATED — no calibrated leaderboard projection</td>'
            f'<td>HOLDOUT-DTI {x3_74["h74_subsurf_pooled"]:.6f} (Exp 3 25-km block-withheld; evaluator {e(hd74["evaluator"])}; '
            f'{x3_74["withheld_positive_occurrences"]:,} withheld positives; 95% CI [{x3_74["h74_subsurf_ci95"][0]:.6f}, {x3_74["h74_subsurf_ci95"][1]:.6f}]); '
            f'Exp 2 H74_BLIND {x2_74["h74_blind_pooled"]:.6f} (+{x2_74["blind_h74_vs_ctrl_blind"]["paired_gain"]:.5f} vs blind, 3/4 folds PASS)</td>'
            f'<td><b>LITERAL: NO / DENSITY-AWARE: YES.</b> <code>flagged_lane = []</code> across all {ln74["registry_checked"]} rasters '
            f'({100*fw74["b2_overlap"]:.2f}% vs B2, {100*ext74["worst_cand_dots_within_3px"]:.2f}% max sparse vs <code>{e(ext74["worst_overlap_file"])}</code>, '
            f'{100*own74["worst_cand_dots_within_3px"]:.2f}% max own-lineage); literal 70% fails vs r13 lattice (100.00%) &amp; pindrop (76.19%).</td>'
            f'<td><b>DO NOT SUBMIT.</b> Exp 2 G2 passed, but Slot Gate G1 &amp; Exp 3 failed vs H35; research/inspection only.</td></tr>'
        )
        foc_latest = json.loads((ROOT / "evidence" / "focus_sites_h74_latest_2026-10-26.json").read_text())["sites"]
        foc_latest_rows = "".join(
            f'<tr><th scope="row"><a href="{e(s["repo_url"])}">{e(s["site"])}</a></th>'
            f'<td class="submission-id">{e(s["latest_20261026_file"])}</td>'
            f'<td>{e(s["latest_metric_label"])}<br><small>Historical best: {s["historical_score_owner_reported"]:.4f} OWNER-REPORTED ({e(s["historical_file"])})</small></td>'
            f'<td>{e(s["estimated_leaderboard_score"])}</td>'
            f'<td>{e(s["uniqueness_audit"])}</td>'
            f'<td><b>{e(s["ok_to_submit"])}</b></td></tr>'
            for s in foc_latest
        )
        h74_section = f'''<section class="card" id="h74-session"><p class="eyebrow">LATEST SESSION (26 OCT 2026) · 3/3 PRE-REGISTERED EXPERIMENTS (DRAWS 110–113) · UNIQUE SUBSURFACE RESEARCH GEOTIFF</p>
<h2>H74 Remanent-Magnetic Phase Skewness &amp; Biharmonic Broken-Plate Flexure (RMPS-BFP) &times; 25-km Block-Withheld Holdout (H74-BW)</h2>
<p><b>Pre-registered before fitting:</b>
<a href="../knowledge/35_preregistered_h74_rmps_bw_2026-10-26.md">4 ranked hypotheses &amp; 25-km block holdout design (<code>af10a19</code>)</a> ·
<a href="../knowledge/36_preregistered_h74_exp3_subsurface_2026-10-26.md">Exp 3 topography-free subsurface addendum (<code>32897de</code>)</a> ·
<a href="../knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md">Executive summary, 0.2778 PhD proof &amp; H74 outcomes</a> ·
<a href="../registry/run_card_h74_2026-10-26.json">H74 JSON Run Card</a> ·
<a href="../registry/review_passes_h74_2026-10-26.json">3-pass review receipt</a> ·
<a href="../evidence/h74_joint_analysis.json">Exp 1–2 joint analysis</a> ·
<a href="../evidence/h74_exp3_subsurf_bw25km/analysis.json">Exp 3 subsurface analysis</a>.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Four ranked H74 geological hypotheses">
<table><thead><tr><th>Rank</th><th>Hypothesis &amp; Layers</th><th>Physical Signature &amp; Why Catalogue Misses It</th><th>Named Non-Fault Mimic</th><th>Repo Novelty, Cost &amp; Official Data</th><th>Expected &Delta;DTI / Status</th></tr></thead>
<tbody>
<tr><td><b>1</b></td><td><b>H74-1 · RMPS-BFP</b><br><small><code>mag_tmi</code>, <code>mag_rtp</code>, <code>mag_tilt</code>, <code>mag_up2km</code>, <code>mag_up4km</code>, <code>grav_bouguer_up2km</code>, <code>geod_dilaterate</code>, <code>geod_maxshear</code>, <code>temp_2m</code>, <code>deq_n100a15</code></small></td><td>Standardized TMI-vs-RTP remanent phase-skewness crest + normalized biharmonic broken-plate hinge &nabla;<sup>4</sup>h<sub>b</sub> (<code>truncate=6.0</code>) + Simpson pore-fluid dilation criticality + harmonic Laplace defect; catches reversed-polarity volcanic &amp; playa-concealed basement faults.</td><td>Unfaulted caldera ring-dike margins, basaltic feeder vents, buried granitoid pluton contacts, evaporite diapir edges</td><td>First remanent TMI-vs-RTP phase-skewness + biharmonic &nabla;<sup>4</sup>h<sub>b</sub> + harmonic defect in GEMSDOE portfolio; ~38 min CPU total across 3 exps; cached GDR #1391 / USGS potential fields.</td><td>Planning: <code>+0.002..+0.008</code><br><b>Exp 2 G2 PASS</b> (<code>+0.0024</code> blind, <code>+0.0004</code> apron); Slot Gate G1 &amp; Exp 3 FAIL</td></tr>
<tr><td><b>2</b></td><td><b>H74-2 · MS-EU3D</b><br><small>Cached Bouguer + TMI + upward continuations</small></td><td>Multi-scale Thompson/Reid Euler structural-index deconvolution separating SI&approx;0.5–1.0 steep fault contacts from SI&approx;2–3 equant pluton/caldera bodies beneath cover.</td><td>Tabular Mesozoic sills, dipping stratigraphic basalt pinch-outs</td><td>Estimates depth z<sub>0</sub> &amp; structural index N directly rather than gradient magnitude; ~15 min CPU; cached GDR #1391 grids.</td><td>Planning: <code>+0.001..+0.005</code><br>Deferred (3/3 budget cap)</td></tr>
<tr><td><b>3</b></td><td><b>H74-3 · MT-BTD</b><br><small>USArray/EarthScope 3D MT resistivity + <code>heatflow</code></small></td><td>Caldwell–Bibby–Brown magnetotelluric phase-tensor skew &beta;<sub>MT</sub> &amp; 5–15 km brittle-ductile sub-vertical conductor roots of deep fluid-bearing faults beneath conductive playas.</td><td>Graphitic Paleozoic black-shale belts (Roberts Mountains thrust), closed-basin lithium brines</td><td>True 3D crustal electrical tensor vs scalar 1D cached MT slices; ~25 min CPU + fetch; free CC0 USGS ScienceBase release.</td><td>Planning: <code>+0.002..+0.009</code><br>Deferred (external fetch + 3/3 cap)</td></tr>
<tr><td><b>4</b></td><td><b>H74-4 · RTHS</b><br><small>USGS GeoDAWN / NURE <code>K</code>, <code>eTh</code>, <code>eU</code> + <code>temp_2m</code></small></td><td>Regression-residual hydrothermal potassium metasomatism excess K<sub>excess</sub> = K &minus; (a&middot;eTh + b) coupled with 2-m thermal upflow along blind argillic/adularia fault zones.</td><td>Potassic rhyolite domes, evaporitic playa-margin K-feldspar deflation lags</td><td>Thorium-normalized geochemical alteration excess rather than spatial K/Th/U step; ~12 min CPU; cached GDR #1391 + CC0 USGS GeoDAWN.</td><td>Planning: <code>+0.001..+0.004</code><br>Deferred (3/3 budget cap)</td></tr>
</tbody></table></div>
<div class="table-scroll" tabindex="0" role="region" aria-label="H74 3-experiment paired holdout results">
<table><thead><tr><th>Experiment &amp; Virgin Draws</th><th>Withheld + (median d_vis)</th><th>Canary Max</th><th>Control HOLDOUT-DTI [95% CI]</th><th>Candidate HOLDOUT-DTI [95% CI]</th><th>Paired Gain [95% CI] (Folds +)</th><th>Gate Outcome</th></tr></thead>
<tbody>
<tr><td><b>Exp 1 · Standard 20%-Component Holdout</b><br><code>draws [110, 111]</code></td><td>{x1_74['withheld_positive_occurrences']:,}<br><small>({x1_74['median_truth_d_vis_px']:.2f} px; {100*x1_74['frac_truth_gt20_px']:.1f}% &gt;20 px)</small></td><td>{x1_74['leakage_canary']['max_canary_auc']:.4f}</td><td>H35: <code>{x1_74['ctrl_h35_pooled']:.5f}</code> [{x1_74['ctrl_h35_ci95'][0]:.4f}, {x1_74['ctrl_h35_ci95'][1]:.4f}]<br>Blind: <code>{x1_74['ctrl_blind_pooled']:.5f}</code></td><td>Apron: <code>{x1_74['h74_apron_pooled']:.5f}</code><br>Blind: <code>{x1_74['h74_blind_pooled']:.5f}</code></td><td>Apron vs H35: <code>{x1_74['apron_vs_ctrl_h35']['paired_gain']:+.5f}</code> (2/4)<br><b>Blind vs Blind: <code>{x1_74['blind_h74_vs_ctrl_blind']['paired_gain']:+.5f}</code></b> (NE <code>+0.0190</code>)</td><td><span class="badge b-bad">Slot Gate G1 FAIL</span></td></tr>
<tr><td><b>Exp 2 · 25-km Block-Withheld H74-BW</b><br><code>draws [110, 111]</code></td><td>{x2_74['withheld_positive_occurrences']:,}<br><small>(<b>{x2_74['median_truth_d_vis_px']:.2f} px</b>; <b>{100*x2_74['frac_truth_gt20_px']:.1f}% &gt;20 px</b>)</small></td><td>{x2_74['leakage_canary']['max_canary_auc']:.4f}</td><td>H35: <code>{x2_74['ctrl_h35_pooled']:.5f}</code> [{x2_74['ctrl_h35_ci95'][0]:.4f}, {x2_74['ctrl_h35_ci95'][1]:.4f}]<br>Blind: <code>{x2_74['ctrl_blind_pooled']:.5f}</code></td><td>Apron: <code>{x2_74['h74_apron_pooled']:.5f}</code><br>Blind: <code>{x2_74['h74_blind_pooled']:.5f}</code></td><td><b>Apron vs H35: <code>{x2_74['apron_vs_ctrl_h35']['paired_gain']:+.5f}</code> (3/4)</b><br><b>Blind vs Blind: <code>{x2_74['blind_h74_vs_ctrl_blind']['paired_gain']:+.5f}</code> (3/4; SE <code>+0.0234</code> vs H35)</b></td><td><span class="badge b-ok">Gate G2 PASS (both)</span><br><small>Apron lead &minus;62.9%</small></td></tr>
<tr><td><b>Exp 3 · 25-km Block-Withheld H74_SUBSURF</b><br><code>draws [112, 113]</code> (51 ACD cols, zero DEM/LiDAR)</td><td>{x3_74['withheld_positive_occurrences']:,}<br><small>(~72.3 px; ~88% &gt;20 px)</small></td><td>{x3_74['leakage_canary']['max_canary_auc']:.4f}</td><td>Subsurf: <code>{x3_74['ctrl_subsurf_pooled']:.5f}</code><br>H35: <code>{x3_74['ctrl_h35_pooled']:.5f}</code></td><td><b><code>{x3_74['h74_subsurf_pooled']:.5f}</code></b> [{x3_74['h74_subsurf_ci95'][0]:.4f}, {x3_74['h74_subsurf_ci95'][1]:.4f}]</td><td>vs Subsurf: <code>{x3_74['paired_gain_vs_ctrl_subsurf']:+.5f}</code> (2/4; SW/SE +)<br>vs H35: <code>{x3_74['paired_gain_vs_ctrl_h35']:+.5f}</code></td><td><span class="badge b-bad">G3 FAIL · DO NOT SUBMIT</span></td></tr>
</tbody></table></div>
<p class="small"><b>Key scientific findings:</b> (1) Switching from 20% component split to 25-km block withholding collapsed <code>CTRL_H35 &minus; CTRL_BLIND</code> by <b>62.9%</b> (<code>+{sh74['ctrl_h35_minus_ctrl_blind_standard']:.5f}</code> &rarr; <code>+{sh74['ctrl_h35_minus_ctrl_blind_block25km']:.5f}</code>), explaining why Family-E apron models win standard holdout yet score 0.0742 live. (2) Pre-publish staging caught <code>IR-25-LIDAR-BLIND-CONVERGENCE-20261026</code> on ABCD <code>H74_BLIND</code> (76.88% vs <code>h23-a-6pct.tif</code>, 74.52% vs <code>H72-CF</code>) and halted before writing to <code>docs/downloads/</code>; removing Family B in <code>H74_SUBSURF</code> cleared all 101 rasters density-aware (<code>flagged_lane = []</code>).</p>
<h3>Nine Focus Sites (GEMSDOE24–36): Latest 2026-10-26 Candidate Audit, Scores/Estimates, Uniqueness &amp; Readiness</h3>
<div class="table-scroll" tabindex="0" role="region" aria-label="Nine focus sites latest 2026-10-26 candidate audit">
<table><thead><tr><th>Focus Site</th><th>Latest 2026-10-26 File (and Historical Reference)</th><th>Score / Holdout Proxy (Properly Labeled)</th><th>Estimated Leaderboard Score</th><th>Uniqueness vs GEMSDOE Portfolio</th><th>OK to Submit?</th></tr></thead>
<tbody>{foc_latest_rows}</tbody></table></div></section>'''

    nid = "note-primary-h72"
    download = (
        f'<p><b>Research-archive download: YES (local inspection/testing only). Competition-ready download: NO.</b> '
        f'The already-existing artifact has content id <code>{e(featured["content_id"])}</code> '
        f'(<code>{featured["positive_pixels"]:,}</code> binary dots, EPSG:32611, <code>3730&times;3292</code>, '
        f'zeros outside, zero NaN/Inf, all values in <code>[0, 1]</code>). No new TIF was generated in this review. '
        f'<b>OK TO SUBMIT: NO · OK to spend a weekly slot: NO — DO NOT SUBMIT.</b> '
        f'H72-3 passed the format validator but fails the strict literal registry lane despite its density-aware comparison; '
        f'it also failed the same-run H35 holdout gate. ROD/POL3/OLIC/D01 wrote no new competition TIFF.</p>'
        f'<div class="row">'
        f'<a class="btn" download href="downloads/{e(featured["file"])}">↓ Download research archive for inspection — DO NOT SUBMIT</a> '
        f'<a class="btn alt" download href="downloads/{e(featured["zip"])}">↓ Research ZIP ({e(featured["zip"])})</a> '
        f'<a class="btn alt" download href="../registry/run_card_h72_2026-10-26.json">↓ H72 research run card JSON</a>'
        f'</div>'
        f'<p class="small" style="margin:8px 0 2px"><b>Research identifier note (&le;140 chars — NOT for DrivenData):</b> '
        f'<button class="btn alt small" data-copy="{nid}">Copy research identifier</button></p>'
        f'<div class="note"><code id="{nid}">{e(featured["note"])}</code></div>'
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
<p class="lead">Nine focus sites, one auditable comparison, and a clear stop. No new experiment or TIF in this review. No predicted leaderboard scores.</p></section>
<section class="review-decision"><span class="badge b-bad">NO ELIGIBLE COMPETITION TIF · OK TO SUBMIT: NO</span><h2>Latest H74-SUBSURF &amp; archived H72-3 research artifacts only — no competition-ready download (DO NOT SUBMIT)</h2>
{h74_download_box}
<p>{e(featured['title'])}. {e(featured['summary'])}</p>
<p>Prior-session ROD stop: {status}</p>{download}
<div class="row"><a class="btn" href="../evidence/rod_2026-10-26/run_card.json" download>Download ROD decision receipt</a>
<a class="btn alt" href="#how-to-submit">Submission checklist</a>
<a class="btn alt" href="../knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md">H74 outcomes, 0.2778 PhD proof &amp; 9-site table</a>
<a class="btn alt" href="../registry/run_card_h74_2026-10-26.json">H74 run card</a>
<a class="btn alt" href="../knowledge/31_h72_outcomes_and_portfolio_synthesis_2026-10-26.md">H72 outcomes, 0.2778 PhD proof &amp; 9-site synthesis</a>
<a class="btn alt" href="../knowledge/32_repo_review_2026-10-26_61f81983.md">This review</a>
<a class="btn alt" href="../registry/run_card_review_61f81983_2026-10-26.json">Review run card</a>
<a class="btn alt" href="../evidence/download_audit_61f81983_2026-10-26.json">Exact-file audit</a>
<a class="btn alt" href="../knowledge/29_current_checkout_review_2026-10-26.md">Current-checkout review</a></div></section>
{inventory_section}
<section><h2>Current H74-SUBSURF &amp; existing H72-3 research archives: validation and eligibility decision</h2>
<div class="table-scroll"><table><thead><tr><th>File</th><th>Estimated competition score</th><th>Saved HOLDOUT-DTI (proxy)</th><th>Unique under literal lane rule?</th><th>Decision</th></tr></thead><tbody>
{h74_table_row}
{h72_table_row}
<tr><td class="submission-id">gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif</td>
<td>NOT ESTIMATED — no calibrated leaderboard projection</td>
<td>HOLDOUT-DTI {h71_result['pooled_dti']:.6f}; evaluator {e(h71_result['evaluator_version'])}; {h71_result['withheld_positives']:,} withheld positives; 95% CI [{h71_result['ci_95'][0]:.6f}, {h71_result['ci_95'][1]:.6f}]</td>
<td><b>NO.</b> 100% within 3 px of the registered r13 lattice; threshold 70%.</td>
<td><b>DO NOT SUBMIT.</b> Holdout failed vs H35; testing only.</td></tr></tbody></table></div>
<p>HOLDOUT-DTI is a catalogue-gap proxy, not an organizer score or leaderboard forecast.</p></section>
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
{h74_section}
{h72_section}
{h72_cf_section}
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
            "**Research-archive download: YES (inspection/testing only) · Competition-ready TIF: NO · OK TO SUBMIT: NO · weekly slot: NO — DO NOT SUBMIT.** "
            "New unique H74-SUBSURF research GeoTIFF generated this session: [`gems25-h74-rmps-subsurf-catfree-b2-37654-20261026-3751606e1ce5-zeros.tif`](docs/downloads/gems25-h74-rmps-subsurf-catfree-b2-37654-20261026-3751606e1ce5-zeros.tif) "
            "(content id `3751606e1ce5`, `37,654` binary dots, SHA-256 `9e0200dc3b1597c7…`, 51 static topography-free & catalogue-free subsurface `ACD + H34 + H74_RMPS` columns; density-aware unique across all 101 rasters with `flagged_lane = []`, `23.63%` vs `GEMSDOE32 B2`, `33.13%` vs `H72-3-subsurf`; literal 70% fails only the 3 >73%-halo rasters `r13` lattice + `pindrop`; DrivenData research note `GEMSDOE25 H74-SUBSURF | no slot, not slot-approved; DO NOT SUBMIT | id 3751606e1ce5 | unscored`; **DO NOT SUBMIT**). "
            "In 3/3 pre-registered H74 experiments (draws 110–113, all 688 leakage canaries <= 0.8259), switching to 25-km spatial-block withholding (`H74-BW`) collapsed `CTRL_H35 - CTRL_BLIND` by **62.9%** (`+0.06353 -> +0.02356`) and both `H74_APRON` (`+0.00038`, 3/4 folds) and `H74_BLIND` (`+0.00237`, 3/4 folds; SE `+0.02343` above `CTRL_H35`) passed Gate G2, while Slot Gate G1 (`-0.00086`) and Exp 3 `H74_SUBSURF` (`0.03906` vs `0.12821` `CTRL_H35`) did not pass. "
            "Existing H72-3 research artifact: [`gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif`](docs/downloads/gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif) "
            "(content id `88bbebfe79b4`, `41,061` binary dots; DEM-free 4-fold OOF PTTG + MTHS subsurface stack). "
            "Three pre-registered H72 screens (draws 80–85) passed standalone leakage canaries (max AUC <= 0.655): de-aproned `H72-1` (+0.0061) and `H72-2` (+0.0073) beat blind controls in 4/4 folds, and `H72-3` (+0.0014) beat its subsurface control, while all three failed vs same-run Family-E `H35`. "
            "The existing `H72-3` file is content-distinct and passes format checks, but it is **not lane-unique under the literal rule**: 74.64% of final dots overlap `pindrop-discovery.tif` within 3 px and 100% overlap the r13 lattice; the surface/final rank-correlation limits pass. No density-aware exception is authorized. It also failed the same-run H35 holdout gate. "
            "[Executive summary & downloads](docs/executive-summary.html) · "
            "[H74 outcomes, 0.2778 PhD proof & 9-site table](knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md) · "
            "[H74 run card](registry/run_card_h74_2026-10-26.json) · "
            "[H74 pre-registrations](knowledge/35_preregistered_h74_rmps_bw_2026-10-26.md) ([Exp 3 addendum](knowledge/36_preregistered_h74_exp3_subsurface_2026-10-26.md)) · "
            "[Nine-site executive review](docs/current-review.html) · "
            "[H72 outcomes, 0.2778 PhD proof & 9-site synthesis](knowledge/31_h72_outcomes_and_portfolio_synthesis_2026-10-26.md) · "
            "[H72 run card](registry/run_card_h72_2026-10-26.json) · "
            "[Objective-session outcomes](knowledge/31_objective_outcomes_and_executive_summary_2026-10-26.md) (`3646faf70507`, alternate) · "
            "[Current session review](knowledge/32_repo_review_2026-10-26_61f81983.md) · "
            "[This review's JSON run card](registry/run_card_review_61f81983_2026-10-26.json) · "
            "[Exact-file audit receipt](evidence/download_audit_61f81983_2026-10-26.json) · "
            "[Current-checkout review](knowledge/29_current_checkout_review_2026-10-26.md) · "
            "[Repository review](knowledge/29_repository_review_2026-10-26.md) · "
            "[Exact-download audit](knowledge/29_download_audit_and_next_hypotheses_2026-10-26.md) · "
            "[Strict-lane feasibility proof](knowledge/29_lane_feasibility_plan_2026-10-26.md) · "
            "[D01 density outcome](knowledge/31_d01_outcome_2026-10-26.md) · "
            "[APFL2 outcomes](knowledge/30_executive_summary_and_apfl_outcomes_2026-10-26.md) (`2e9e4189f554`, alternate) · "
            "[H71 outcomes](knowledge/28_h71_outcomes_2026-10-26.md) (`9eb0c31e5149`, alternate). "
            "GEMSDOE32 B2 is the strongest supplied historical exemplar (**OWNER-REPORTED 0.2778**), not a new submission; sibling `GEMSDOE70 P8-OOF38k` (**OWNER-REPORTED 0.2478**) is the strongest non-`H19-5` architecture. "
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
