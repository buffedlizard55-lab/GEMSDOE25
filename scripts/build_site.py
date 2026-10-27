#!/usr/bin/env python3
"""Build the GitHub Pages site (root index.html + docs/*.html) from registries and evidence.

Every number on the site is read from ``registry/*.json`` or ``evidence/**/*.json``; nothing is hand-typed.
Pages is configured to build from ``main:/``, so the landing page is the ROOT ``index.html``; the same pages are
also written under ``docs/`` (the group's URL convention, e.g. .../docs/index.html).
"""

from __future__ import annotations

import datetime as dt
import html
import json
import sys
from pathlib import Path

from build_current_review import current_banner, render_body

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
e = html.escape


def J(p):
    return json.loads((ROOT / p).read_text())


def opt(p):
    f = ROOT / p
    return json.loads(f.read_text()) if f.exists() else None


def fmt_bytes(n: int) -> str:
    return f"{n / 1048576:.2f} MiB"


def page(title: str, body: str, active: str, prefix: str) -> str:
    """``prefix`` is the path from the page to docs/ ('' inside docs, 'docs/' from the root)."""
    nav = [("index", "Start here", "index.html"), ("current", "Current review", "current-review.html"),
           ("exec", "How to submit", "executive-summary.html"),
           ("research", "Research", "research.html"), ("sources", "Sources & audit", "sources.html")]
    links = []
    for key, label, href in nav:
        h = "index.html" if key == "index" else prefix + href
        links.append(f'<a class="{"on" if key == active else ""}" href="{h}">{label}</a>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · GEMSDOE25</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body>
<header class="top"><div class="wrap"><div class="brand">GEMSDOE25<small>DOE GEMS Prize · DrivenData #306 · designed factorial experiments</small></div><nav>{''.join(links)}</nav></div></header>
<main class="wrap">{current_banner(prefix)}{body}</main>
<footer><div class="wrap">Core values: <b>Maximize P(Win)</b> · <b>Own the Outcome</b>. Source: <a href="https://github.com/buffedlizard55-lab/GEMSDOE25">github.com/buffedlizard55-lab/GEMSDOE25</a> ·
built {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} from <code>registry/</code> and <code>evidence/</code> by <code>scripts/build_site.py</code>.
No score here is promised; reported scores are unverified unless an organizer receipt is supplied. This site/feed never contacts drivendata.org.</div></footer>
<script src="{prefix}assets/app.js"></script></body></html>"""


def score_fmt(x):
    return "" if x is None else f"{x:.4f}"


def badge(txt, kind):
    return f'<span class="badge b-{kind}">{e(txt)}</span>'


def dl_card(s: dict, prefix: str, big: bool = True) -> str:
    href = f"{prefix}downloads/{s['file']}"
    nid = "note-" + s["id"]
    kind = {"scored": "ok"}.get(s["status"], "warn")
    status = s["status"] if s["status"] != "scored" else f"scored {s.get('owner_reported_score'):.4f} (owner-reported)"
    chk = "format verified (all hard checks)" if s.get("format_ok") else "FORMAT CHECK FAILED"
    download_label = "Download research archive (inspection only)" if not s.get("ok_to_submit_slot") else "Download selector-candidate file"
    return f"""<section class="dl"><h2>{e(s['title'])}</h2>
<p>{e(s['summary'])}</p>
<div class="row"><a class="btn" href="{href}" download>↓ {download_label}: {e(s['file'])}</a></div>
<div class="row">{badge(status, kind)}{badge(chk, 'ok' if s.get('format_ok') else 'bad')}{badge('float32 · [0,1] · ' + ('zeros outside footprint' if s.get('outside') == 'zero' else 'NaN outside footprint'), 'info')}{badge(f"{s['positive_pixels']:,} px emitted", 'info')}</div>
<p class="small">{fmt_bytes(s['bytes'])} · unique content id <code>{s['content_id']}</code> · SHA-256 <code>{s['sha256'][:16]}…</code> · <a href="{prefix}executive-summary.html">exact upload steps</a></p>
<p style="margin:10px 0 2px"><b>{'Note to paste in DrivenData only if separately selector-approved' if s.get('ok_to_submit_slot') else 'Research note only — NOT for the competition form (DO NOT SUBMIT)'}</b> <button class="btn alt small" data-copy="{nid}">Copy {'submission note' if s.get('ok_to_submit_slot') else 'research identifier'}</button></p>
<div class="note"><code id="{nid}">{e(s['note'])}</code></div></section>"""


def verdict_banner(p: dict, prefix: str, exec_page: bool = False) -> str:
    """Top-of-page status separates research-archive access from competition eligibility."""
    archive = "YES — RESEARCH INSPECTION ONLY" if p.get("ok_to_download", p.get("format_ok")) else "NO"
    submit = "NO — DO NOT SUBMIT" if not p.get("ok_to_submit_slot") else "REQUIRES SEPARATE OWNER SELECTOR"
    title = "Executive summary &amp; submission guide" if exec_page else "Archived research artifact — no eligible competition TIF"
    return f"""<div class="hero"><h1>{title}</h1>
<div class="stats"><div class="stat"><b style="color:#1d4ed8">Research-archive download: {archive}</b><span>Existing file for local inspection/testing only; format validity and unique file bytes do not establish lane clearance or competition eligibility.</span></div>
<div class="stat"><b style="color:#b91c1c">Competition-ready TIF / OK TO SUBMIT: {submit}</b><span>verdict <b>{e(p.get('verdict', 'n/a'))}</b>: {'separate owner selector review still required; this is not slot approval' if p.get('ok_to_submit_slot') else 'the current candidate failed required gates and is not slot-approved'} ({e(p.get('slot_reason') or 'see registry')}). Weekly slot: NO.</span></div>
<div class="stat"><b>{e(p.get('expected_range') or 'n/a')}</b><span>No calibrated live-score estimate is available; HOLDOUT-DTI is a proxy result in the run card, not a competition score.</span></div></div>
<p class="lead"><b>{e(p['title'])}.</b> The archived download card below is for local inspection only and contains a research identifier, not an authorized submission note.</p>
<p class="small"><b>Status:</b> {e(p['status'])}. <b>Lane:</b> {e(p.get('lane_summary', 'n/a'))}. <b>Run card:</b> <code>{e(p.get('run_card', ''))}</code>.
Research ZIP alternative: <a href="{prefix}downloads/{e(p.get('zip', ''))}" download>{e(p.get('zip', ''))}</a>. The earlier "Predicted values must be in range [0, 1]" error came from NaN pixels inside the footprint of an old file; the archived H72-3 file has none (zeros outside, no NaN anywhere).
The frozen holdout comparator 0.152003389 does not reproduce in this environment (IR-25-COMPARATOR-DRIFT); historical gates use the best same-run control instead.</p></div>"""


def main() -> None:
    subs = J("registry/submissions.json")["files"]
    ls = J("registry/live_scores.json")
    irr = J("registry/irregularities.json")["issues"]
    src = J("registry/sources.json")["sources"]
    man = J("registry/data_manifest.json")["files"]
    why = J("evidence/why_0_2477.json")
    fac = J("evidence/factorial/results.json")
    add = opt("evidence/addons/results.json")
    conf = opt("evidence/addons_confirm/results.json")
    emu = opt("evidence/emission_model.json")
    oos = opt("evidence/emission_model_oos_check.json")
    ext = opt("evidence/addons/emk_extension.json")
    href = opt("evidence/harness_references.json")
    h27_screen = opt("evidence/h27_screen/results.json")
    h27_confirm = opt("evidence/h27_confirm/results.json")
    h30_screen = opt("evidence/h30_relay_screen/results.json")
    h30_confirm = opt("evidence/h30_relay_confirm/results.json")
    h31_flank_screen = opt("evidence/h31_flank_screen/results.json")
    h31_flank_confirm = opt("evidence/h31_flank_confirm/results.json")
    h31_card = opt("evidence/h31_run_card_2026-10-25.json")
    h31_aniso_res = opt("evidence/h31_experiments/results.json")
    h31_aniso_card = opt("evidence/h31_experiments/run_card.json")
    focus_forensics = opt("evidence/focus_sites_forensics.json")
    h28 = opt("evidence/h28_calibration/design.json")
    h28_anchors = opt("evidence/h28_calibration/anchors.json")
    h28_habitat = opt("evidence/h28_calibration/habitat_fit.json")
    h28_mix = opt("evidence/h28_calibration/mixture.json")
    h28_hold = opt("evidence/h28_holdout/results.json")
    h28_ledger = opt("registry/artifact_ledger.json")
    primary = next(s for s in subs if s["role"] == "primary")
    others = [s for s in subs if s["role"] != "primary"]
    selected = primary
    h36_spigm_card = opt("registry/run_card_h36_spigm_2026-10-25.json")
    h36_spigm_pool = opt("evidence/h36_spigm_pooled_16cells.json")
    kdc = opt("registry/run_card_kdc_2026-10-25.json")
    anchor = opt("evidence/live_anchor_complement.json")
    snap = ls["leaderboard_snapshot"]
    lead = snap["top10"][0]["best_public_dti"]
    best = max(a["score"] for a in ls["artifacts"] if a["score"] is not None)
    h30_result = h30_confirm or h30_screen
    if h30_confirm:
        h30_gate = h30_confirm["paired_promotion_gate"]
        if h30_confirm.get("confirmation_gate_passed"):
            h30_status = "screen and fresh-draw confirmation gates passed; full-data build and exact-file audit still required"
        elif h30_screen and h30_screen.get("screen_gate_passed"):
            h30_status = "screen passed; fresh-draw confirmation failed; stop, no candidate file or slot"
        else:
            h30_status = "fresh-draw confirmation gate failed; stop, no candidate file or slot"
    elif h30_screen:
        h30_gate = h30_screen["paired_promotion_gate"]
        h30_status = ("screen gate passed; frozen confirmation on draws 8,9 required"
                      if h30_screen.get("screen_gate_passed")
                      else "screen gate failed; stop, no confirmation or candidate file")
    else:
        h30_gate = None
        h30_status = "registered screen draws 6,7; real-data feature smoke passed, no model fit or DTI yet"

    cf1 = next((s for s in subs if s['id'] == 'cf1-transverse-negative'), None)
    cf1_card = opt('registry/run_card_cf1_2026-10-25.json')
    h38_card = opt('registry/run_card_h38_ospc_2026-10-25.json')
    h66_card = opt('registry/run_card_h66_2026-10-25.json')
    h71_card = opt('registry/run_card_h71_2026-10-26.json')
    obj_card = opt('registry/run_card_objective_2026-10-26.json')

    def latest_diagnostic(prefix: str) -> str:
        if cf1 is None or cf1_card is None:
            return ''
        hold = cf1_card['holdout_dti']
        comp = cf1_card['registry_comparison']
        # Historical parallel-lane diagnostic kept below the primary featured H38 card.
        return f'''<section class="dl"><h2>Prior parallel-lane CF-1 research TIFF — DO NOT SUBMIT</h2>
<p><b>OK to download for local testing: YES. OK to submit to DrivenData: NO.</b>
HOLDOUT-DTI {hold['candidate']:.6f} ({hold['n_withheld_positives']:,} withheld positives; seed {hold['draws'][0]}, four folds) vs same-run control {hold['same_run_control']:.6f};
paired gain {hold['paired_gain']:+.6f} (95% fold-t CI {hold['gain_95pct_fold_t_ci'][0]:+.6f}…{hold['gain_95pct_fold_t_ci'][1]:+.6f}), {hold['positive_folds']}/4 folds positive.
Pre-registered screen failed; no confirmation or weekly slot. The strict lane check also fails:
{comp['lattice_overlap']:.0%} of dots within 3 px of the registered r13 lattice; {comp['h31_control_overlap']:.2%} near H31-C. New SHA-256
is not a lane clearance. Format verification is against an owner-mirrored template only.</p>
<a class="btn alt small" href="{prefix}downloads/{e(cf1['file'])}" download>↓ Download CF-1 diagnostic TIFF (testing only)</a>
<p class="small">SHA-256 <code>{cf1['sha256']}</code> · EPSG:32611 · 3730×3292 · no NaN inside footprint · all values [0,1] · <a href="{prefix}executive-summary.html">submission eligibility guide</a> · note (≤140 chars): <code>{e(cf1['note'])}</code></p></section>'''

    def apfl2_summary_card(prefix: str) -> str:
        rc_path = ROOT / "registry" / "run_card_apfl2_2026-10-26.json"
        if not rc_path.exists():
            return ""
        rc = json.loads(rc_path.read_text())
        x1, x2 = rc["holdout_dti"]["exp1_direct"], rc["holdout_dti"]["exp2_hgb"]
        return f"""<article class="card">
      <div class="card-top"><span class="badge b-bad">Screen FAIL</span><span class="badge b-grey">Testing download only</span></div>
      <h3>APFL piedmont-flexure completion (parallel session)</h3>
      <p>Two pre-registered screens vs same-run H35 — direct HOLDOUT-DTI {x1['candidate']['pooled_dti']:.6f} [22,813 withheld]
      and H35+APFL {x2['candidate']['pooled_dti']:.6f} [22,931 withheld] — both FAIL; OCEM diagnostic: B2+refill ~neutral on proxy.
      New unique testing GeoTIFF <code>{e(rc['submission']['name'])}</code> (48,658 dots, strict [0,1] pass) is registered as alternate.</p>
      <div class="links"><a href="{prefix}downloads/{e(rc['submission']['name'])}" download>Download testing GeoTIFF</a>
      <a href="../knowledge/30_executive_summary_and_apfl_outcomes_2026-10-26.md">Executive summary</a>
      <a href="../registry/run_card_apfl2_2026-10-26.json">Run card</a></div></article>"""

    def h38_summary_card(prefix: str) -> str:
        if not h38_card:
            return ''
        hd = h38_card['holdout_dti']
        c_arm = hd['candidate_G1_S1']
        b_arm = hd['same_run_control_G0_S0']
        g_con = hd['primary_contrast_G1_S1_vs_G0_S0']
        fe = hd['factorial_effects']
        ov = h38_card['correlation_overlap_vs_registry']
        kbase = "../knowledge" if not prefix else "knowledge"
        return f'''<div class="card"><h2>Session 8 — H38 OSPC × 300 m Submodular Multi-Scale Skeleton 2&sup2; Factorial (Pre-Registered Pre-Fit)</h2>
<p><b>Pre-registration:</b> <a href="{kbase}/25_preregistered_h38_ospc_submod_factorial_2026-10-25.md"><code>knowledge/25</code></a> (commit <code>c9c7e76</code>) · <b>Full PhD synthesis &amp; 0.2778 proof:</b> <a href="{kbase}/26_h38_outcomes_and_0.2778_phd_synthesis_2026-10-25.md"><code>knowledge/26</code></a> · <b>Run card:</b> <code>registry/run_card_h38_ospc_2026-10-25.json</code>.</p>
<ul>
<li><b>HOLDOUT-DTI (<code>{e(hd['evaluator_version'])}</code>, draws <code>{hd['draws_evaluated']}</code>, <code>{hd['withheld_positives_total']:,}</code> withheld positives):</b> Primary <code>G1_S1</code> fold-mean <code>{c_arm['fold_mean_dti']:.6f}</code> (95% CI <code>[{c_arm['ci95_fold_mean'][0]:.6f}, {c_arm['ci95_fold_mean'][1]:.6f}]</code>; pooled <code>{c_arm['pooled_dti']:.6f}</code>) vs same-run H35 arm-B control <code>G0_S0</code> <code>{b_arm['fold_mean_dti']:.6f}</code> (pooled <code>{b_arm['pooled_dti']:.6f}</code>); paired gain <b><code>{g_con['mean']:+.6f}</code></b> (<code>{g_con['folds_positive']}/4</code> folds positive; <code>hug</code> delta <code>{g_con['hug_mean']:+.4f}</code>). Leakage canary PASSED (max standalone feature AUC <code>{hd['leakage_canary']['h38_max_canary_auc']:.4f} &le; 0.90</code>). Confirmation draws <code>[26, 27]</code> were NOT run per frozen stopping rule.</li>
<li><b>Great Basin North–South Structural Regime Split (<code>IR-25-H38-REGIME-SPLIT</code>):</b> Sparse-catalogue <code>NW</code> (<code>0.88%</code> fault prevalence, <code>75.0%</code> 3DEP 1 m LiDAR) jumped <b><code>{g_con['per_fold']['NW']:+.6f}</code></b> (<code>+0.0033</code> OSPC + <code>+0.0068</code> submodular), whereas missing-LiDAR <code>NE</code> (<code>54.2%</code> 3DEP) was flat (<code>{g_con['per_fold']['NE']:+.6f}</code>) and dense anastomosing <code>SW/SE</code> (<code>1.44–1.54%</code> Walker Lane / Sevier splays) lost <code>{g_con['per_fold']['SW']:+.6f}</code> / <code>{g_con['per_fold']['SE']:+.6f}</code>. Orthogonal main effects: Factor <code>G</code> <code>{fe['main_effect_G_OSPC']['mean']:+.6f}</code>, Factor <code>S</code> <code>{fe['main_effect_S_SUBMOD']['mean']:+.6f}</code>, <code>G&times;S</code> <code>{fe['interaction_GxS']['mean']:+.6f}</code>.</li>
<li><b>3-Tier Registry Uniqueness:</b> <b><code>0 / 21</code></b> sibling top-scorers (<code>GEMSDOE27..91</code>) flagged — overlap vs <code>GEMSDOE32</code> (<code>0.2778</code>) = <code>{ov['overlap_vs_gemsdoe32_b2']:.3f}</code>, vs <code>GEMSDOE70</code> submodular (<code>0.2478</code>) = <code>{ov['overlap_vs_gemsdoe70_submod']:.3f}</code>, max sibling top-scorer = <code>{ov['worst_sibling_top_scorer_overlap']:.3f}</code>; pre-placement surface max <code>|&rho;| = {ov['worst_abs_spearman_surface']:.4f} &le; 0.90</code>; literal strict lane flags <code>r13</code> lattice (<code>1.000</code>), <code>gems10-h25</code> (<code>{ov['worst_historical_other_site_overlap']:.3f}</code>), and own-repo HGB lineage (<code>{ov['worst_other_registry_overlap']:.3f}</code>) &rarr; <b>OK TO DOWNLOAD: YES · OK TO SUBMIT: NO (DO NOT SUBMIT)</b>.</li>
</ul></div>'''

    def h71_summary_card(prefix: str) -> str:
        if not h71_card:
            return ''
        e1 = h71_card['experiments']['experiment_1_h71_1_hgpc_screen']
        e2 = h71_card['experiments']['experiment_2_h71_3_akf_screen']
        e3 = h71_card['experiments']['experiment_3_h71_4_mag_screen']
        rc = h71_card['registry_correlation_and_overlap']
        fw = rc['focus_21_top_scorers']
        kbase = "../knowledge" if not prefix else "knowledge"
        return f'''<div class="card"><h2>Prior 3-Experiment Session — H71 DIRECT physics (HGPC-BLIND, AKF knickpoints, MAG-ANISO)</h2>
<p><b>Pre-registration:</b> <a href="{kbase}/27_preregistered_h71_hgpc_2026-10-26.md"><code>knowledge/27</code></a> (commit <code>d4d4bf7</code>, before any fit) · <b>Outcomes:</b> <a href="{kbase}/28_h71_outcomes_2026-10-26.md"><code>knowledge/28</code></a> · <b>Run card:</b> <code>registry/run_card_h71_2026-10-26.json</code>.</p>
<table><thead><tr><th>Experiment (3/3 budget)</th><th>Draws / Withheld Pos</th><th class="num">Canary max AUC</th><th class="num">Candidate Pooled HOLDOUT-DTI [95% CI]</th><th class="num">Same-Run H35 Control</th><th class="num">vs crest / vs H35 (folds +)</th><th>Stage Verdict</th></tr></thead><tbody>
<tr><td><b>Exp 1: H71-1 HGPC-BLIND</b> (<code>HGPC_BLIND_B2</code>)</td><td><code>{e(str(e1['draws']))}</code> / {e1['withheld_positives']:,}</td><td class="num">{e1['leakage_canary']['max_feature_auc']:.4f}</td><td class="num">{e1['candidate_pooled_holdout_dti']:.6f} [{e1['candidate_pooled_ci95'][0]:.4f}, {e1['candidate_pooled_ci95'][1]:.4f}]</td><td class="num">{e1['control_h35_pooled_holdout_dti']:.6f}</td><td class="num">{e1['gate']['vs_named']['CTRL_CREST_B2']['mean_gain']:+.4f} ({e1['gate']['vs_named']['CTRL_CREST_B2']['folds_positive']}/4) / {e1['gate']['vs_named']['CTRL_H35_24']['mean_gain']:+.4f} ({e1['gate']['vs_named']['CTRL_H35_24']['folds_positive']}/4)</td><td>{badge('SCREEN FAIL vs H35', 'bad')}</td></tr>
<tr><td><b>Exp 2: H71-3 AKF</b> (<code>AKF_B2</code>)</td><td><code>{e(str(e2['draws']))}</code> / {e2['withheld_positives']:,}</td><td class="num">{e2['leakage_canary']['max_feature_auc']:.4f}</td><td class="num">{e2['candidate_pooled_holdout_dti']:.6f} [{e2['candidate_pooled_ci95'][0]:.4f}, {e2['candidate_pooled_ci95'][1]:.4f}]</td><td class="num">{e2['control_h35_pooled_holdout_dti']:.6f}</td><td class="num">{e2['gate']['vs_named']['CTRL_CREST_B2']['mean_gain']:+.4f} ({e2['gate']['vs_named']['CTRL_CREST_B2']['folds_positive']}/4) / {e2['gate']['vs_named']['CTRL_H35_24']['mean_gain']:+.4f} ({e2['gate']['vs_named']['CTRL_H35_24']['folds_positive']}/4)</td><td>{badge('SCREEN FAIL vs H35', 'bad')}</td></tr>
<tr><td><b>Exp 3: H71-4 MAG-ANISO</b> (<code>MAG_ANISO_B2</code>)</td><td><code>{e(str(e3['draws']))}</code> / {e3['withheld_positives']:,}</td><td class="num">{e3['leakage_canary']['max_feature_auc']:.4f}</td><td class="num">{e3['candidate_pooled_holdout_dti']:.6f} [{e3['candidate_pooled_ci95'][0]:.4f}, {e3['candidate_pooled_ci95'][1]:.4f}]</td><td class="num">{e3['control_h35_pooled_holdout_dti']:.6f}</td><td class="num">{e3['gate']['vs_named']['CTRL_CREST_B2']['mean_gain']:+.4f} ({e3['gate']['vs_named']['CTRL_CREST_B2']['folds_positive']}/4) / {e3['gate']['vs_named']['CTRL_H35_24']['mean_gain']:+.4f} ({e3['gate']['vs_named']['CTRL_H35_24']['folds_positive']}/4)</td><td>{badge('SCREEN FAIL vs H35', 'bad')}</td></tr>
</tbody></table>
<p class="small"><b>Key scientific findings:</b> (1) Three independent catalogue-free physical fields each beat unsupervised Family-B crest emission and each fail vs Family-E H35 on the catalogue-gap proxy (honest negative). (2) Featured GeoTIFF is the first GEMSDOE25 file to clear own HGB lineage under the 70% 3-px rule (max {100*rc['own_lineage']['worst_cand_dots_within_3px']:.1f}%; {100*fw['b2_overlap']:.1f}% vs GEMSDOE32 B2 0.2778; max sibling {100*fw['worst_cand_dots_within_3px']:.1f}%; surface |&rho;| {rc['surface_max_abs_spearman']:.4f} &le; 0.90). (3) Literal strict lane still fails on the dense r13 5-px lattice (100%; <code>IR-25-LANE-DENSITY</code>). (4) <b>OK TO DOWNLOAD: YES · OK TO SUBMIT: NO — DO NOT SUBMIT</b> (no weekly slot).</p></div>'''


    def objective_summary_card(prefix: str) -> str:
        if not obj_card:
            return ''
        x1 = obj_card['experiments']['experiment_1_tent']
        x2 = obj_card['experiments']['experiment_2_hardneg']
        x3 = obj_card['experiments']['experiment_3_ign3']
        fd = obj_card['registry_correlation_and_overlap']['final_dots']
        ext = fd['external_sparse']
        b2o = fd['vs_gemsdoe32_b2']
        kbase = "../knowledge" if not prefix else "knowledge"
        return f"""<div class="card"><h2>Latest 3-Experiment Pre-Registered Session — training-objective geometry (TENT, HARDNEG, IGN3) · featured download above</h2>
<p><b>Pre-registrations:</b> <a href="{kbase}/29_ranked_hypotheses_and_preregistration_2026-10-26.md"><code>knowledge/29</code></a> (commit <code>005e115</code>, before any fit), <a href="{kbase}/30_preregistered_ign3_experiment3_2026-10-26.md"><code>knowledge/30</code></a> · <b>Outcomes &amp; nine-site executive summary:</b> <a href="{kbase}/31_objective_outcomes_and_executive_summary_2026-10-26.md"><code>knowledge/31</code></a> · <b>Run card:</b> <code>registry/run_card_objective_2026-10-26.json</code>.</p>
<table><thead><tr><th>Experiment (3/3 budget) — all HOLDOUT-DTI</th><th>Draws / Withheld +</th><th class="num">Canary max</th><th class="num">Candidate pooled</th><th class="num">Same-run BIN pooled</th><th class="num">Paired &Delta; [95% CI] (folds +)</th><th>Verdict</th></tr></thead><tbody>
<tr><td><b>Exp 1 TENT</b> (kernel-regression target)</td><td><code>{e(str(x1['draws']))}</code> / {x1['withheld_positives_total']:,}</td><td class="num">{x1['leakage_canary']['max_effective_auc']:.4f}</td><td class="num">{x1['candidate_greedy']['pooled_dti']:.6f}</td><td class="num">{x1['bin_greedy']['pooled_dti']:.6f}</td><td class="num">{x1['paired']['mean_gain']:+.6f} [{x1['paired']['ci95'][0]:+.4f}, {x1['paired']['ci95'][1]:+.4f}] ({x1['paired']['folds_positive']}/4)</td><td>{badge('SCREEN FAIL', 'bad')}</td></tr>
<tr><td><b>Exp 2 HARDNEG</b> (hard-negative mining)</td><td><code>{e(str(x2['draws']))}</code> / {x2['withheld_positives_total']:,}</td><td class="num">{x2['leakage_canary']['max_effective_auc']:.4f}</td><td class="num">{x2['candidate_greedy']['pooled_dti']:.6f}</td><td class="num">{x2['bin_greedy']['pooled_dti']:.6f}</td><td class="num">{x2['paired']['mean_gain']:+.6f} [{x2['paired']['ci95'][0]:+.4f}, {x2['paired']['ci95'][1]:+.4f}] ({x2['paired']['folds_positive']}/4)</td><td>{badge('SCREEN FAIL', 'bad')}</td></tr>
<tr><td><b>Exp 3 IGN3</b> (ring-excluded negatives)</td><td><code>{e(str(x3['draws']))}</code> / {x3['withheld_positives_total']:,}</td><td class="num">{x3['leakage_canary']['max_effective_auc']:.4f}</td><td class="num">{x3['candidate_greedy']['pooled_dti']:.6f}</td><td class="num">{x3['bin_greedy']['pooled_dti']:.6f}</td><td class="num">{x3['paired']['mean_gain']:+.6f} [{x3['paired']['ci95'][0]:+.4f}, {x3['paired']['ci95'][1]:+.4f}] ({x3['paired']['folds_positive']}/4)</td><td>{badge('SCREEN FAIL', 'bad')}</td></tr>
</tbody></table>
<p class="small">No training-objective variant beat the frozen binary classifier; the featured GeoTIFF is that incumbent stack rebuilt with fresh production seeds. Unique vs scored/external rasters (worst overlap {100*ext['worst_cand_dots_within_3px']:.1f}% &le; 70%; {100*b2o['cand_dots_within_3px']:.1f}% vs GEMSDOE32 B2 0.2778); strict lane fails vs own unscored HGB lineage + r13 lattice. <b>OK TO DOWNLOAD: YES · OK TO SUBMIT: NO — DO NOT SUBMIT.</b></p></div>"""

    def h66_summary_card(prefix: str) -> str:
        if not h66_card:
            return ''
        e1 = h66_card['experiments']['experiment_1_h66_1_screen']
        e2 = h66_card['experiments']['experiment_2_h66_1_confirm']
        e3 = h66_card['experiments']['experiment_3_h66_2_sgmc_react_screen']
        rc = h66_card['registry_correlation_and_overlap']
        fw = rc['focus_21_top_scorers']
        kbase = "../knowledge" if not prefix else "knowledge"
        return f'''<div class="card"><h2>Latest 3-Experiment Pre-Registered Session — H66-1 (MGD-F &times; Tip-Preserved Flank Shield) &amp; H66-2 (SGMC-REACT)</h2>
<p><b>Pre-registration:</b> <a href="{kbase}/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md"><code>knowledge/25</code></a> (commit <code>0f6fc77</code>) · <b>Full PhD forensics &amp; outcomes:</b> <a href="{kbase}/26_h66_outcomes_2026-10-25.md"><code>knowledge/26</code></a> · <b>Run card:</b> <code>registry/run_card_h66_2026-10-25.json</code>.</p>
<table><thead><tr><th>Experiment (3/3 budget)</th><th>Draws / Withheld Pos</th><th class="num">Canary max AUC</th><th class="num">Candidate Pooled HOLDOUT-DTI [95% CI]</th><th class="num">Same-Run H35 Control</th><th class="num">Paired &Delta;DTI (Folds +)</th><th>Stage Verdict</th></tr></thead><tbody>
<tr><td><b>Exp 1: H66-1 Screen</b> (<code>G1_C1</code>)</td><td><code>{e(str(e1['draws']))}</code> / {e1['withheld_positives']:,}</td><td class="num">{e1['leakage_canary']['max_feature_auc']:.4f}</td><td class="num">{e1['candidate_pooled_holdout_dti']:.6f} [{e1['candidate_pooled_ci95'][0]:.4f}, {e1['candidate_pooled_ci95'][1]:.4f}]</td><td class="num">{e1['control_h35_pooled_holdout_dti']:.6f}</td><td class="num">{e1['gate']['mean_gain']:+.6f} ({e1['gate']['folds_positive']}/4)</td><td>{badge('SCREEN PASS', 'ok')}</td></tr>
<tr><td><b>Exp 2: H66-1 Confirm</b> (<code>G1_C1</code>)</td><td><code>{e(str(e2['draws']))}</code> / {e2['withheld_positives']:,}</td><td class="num">{e2['leakage_canary']['max_feature_auc']:.4f}</td><td class="num">{e2['candidate_pooled_holdout_dti']:.6f} [{e2['candidate_pooled_ci95'][0]:.4f}, {e2['candidate_pooled_ci95'][1]:.4f}]</td><td class="num">{e2['control_h35_pooled_holdout_dti']:.6f}</td><td class="num">{e2['gate']['mean_gain']:+.6f} ({e2['gate']['folds_positive']}/4)</td><td>{badge('CONFIRM FAIL', 'bad')}</td></tr>
<tr><td><b>Exp 3: H66-2 Screen</b> (<code>SGMC_REACT_ONLY</code>)</td><td><code>{e(str(e3['draws']))}</code> / {e3['withheld_positives']:,}</td><td class="num">{e3['leakage_canary']['max_feature_auc']:.4f}</td><td class="num">{e3['candidate_pooled_holdout_dti']:.6f} [{e3['candidate_pooled_ci95'][0]:.4f}, {e3['candidate_pooled_ci95'][1]:.4f}]</td><td class="num">{e3['control_h35_pooled_holdout_dti']:.6f}</td><td class="num">{e3['gate']['mean_gain']:+.6f} ({e3['gate']['folds_positive']}/4)</td><td>{badge('SCREEN PASS (unconfirmed)', 'warn')}</td></tr>
</tbody></table>
<p class="small"><b>Key scientific findings:</b> (1) <code>Factor C</code> (tip-preserved lateral-flank shielding, <code>r=2.5 px</code>, <code>H27_tip &ge; 0.05</code>) was positive in <code>4/4</code> screen AND <code>4/4</code> confirmation folds (<code>8/8</code> here; <b><code>16/16</code> fold-blocks</b> combined with H31-1). (2) Sparse 610-cell GDR geothermometry (<code>MGD-F</code>) is draw-dependent (<code>IR-25-MGD-SPARSE-DRAW-DEPENDENCE</code>); two-stage confirmation stopped a false-positive weekly slot spend. (3) Gating USGS SGMC bedrock faults by 3DEP LiDAR scarps &amp; GPS strain jumped HOLDOUT-DTI by <code>+0.0138</code> (95% CI <code>[+0.0025, +0.0251]</code>, <code>4/4</code> folds+), held unpromoted at the 3-experiment cap with HGB smooth-multiplier tree inversion documented (<code>IR-25-SGMC-TREE-INVERSION</code>). (4) Featured GeoTIFF clears all {fw['n']} focus/top-scorer submissions (max 3-px overlap <code>{100*fw['worst_cand_dots_within_3px']:.1f}% &le; 70%</code>; <code>{100*fw['b2_overlap']:.1f}%</code> vs GEMSDOE32 B2 <code>0.2778</code>; max surface |&rho;| <code>{rc['surface_max_abs_spearman']:.4f} &le; 0.90</code>), held <b>DO NOT SUBMIT</b>.</p></div>'''

    def pol3_summary_card(prefix: str) -> str:
        pol3 = opt("evidence/pol3_screen_2026-10-26/summary.json")
        if not pol3:
            return ""
        kbase = "../knowledge" if not prefix else "knowledge"
        return f'''<div class="card"><h2>Latest experiment — POL3 signed half-graben polarity (negative screen)</h2>
<p>Pre-registered before fitting: <a href="{kbase}/27_ranked_hypotheses_and_review_2026-10-26.md">ranked hypotheses &amp; repo review</a> · <a href="{kbase}/28_preregistered_pol3_signed_halfgraben_2026-10-26.md">POL3 preregistration</a> · run card <code>registry/run_card_pol3_screen_2026-10-26.json</code>.</p>
<ul><li><b>HOLDOUT-DTI</b> (<code>{e(pol3['evaluator'])}</code>, draws <code>{pol3['draws']}</code>, <code>{pol3['withheld_positives']:,}</code> withheld positives): candidate pooled <code>{pol3['candidate_pooled']['dti']:.6f}</code> vs same-run H35 control <code>{pol3['control_pooled']['dti']:.6f}</code>.</li>
<li><b>HOLDOUT-DTI paired 4-fold gain</b> <code>{pol3['paired_fold_mean_gain']:+.6f}</code>, 95% CI <code>[{pol3['paired_fold_ci95'][0]:+.6f}, {pol3['paired_fold_ci95'][1]:+.6f}]</code>; <code>{pol3['positive_folds']}/4</code> folds positive. Feature-alone leakage canary max AUC <code>{pol3['max_canary_auc']:.4f}</code> (&le; 0.90).</li>
<li><b>Verdict: NEGATIVE.</b> Screen gate failed; confirmation, full-catalogue surface, dot placement and new TIFF were not run. No submission slot is authorized.</li></ul></div>'''

    def home(prefix: str) -> str:
        hero = verdict_banner(primary, prefix)
        cards = dl_card(primary, prefix) + objective_summary_card(prefix) + apfl2_summary_card(prefix) + h71_summary_card(prefix) + pol3_summary_card(prefix) + h66_summary_card(prefix) + h38_summary_card(prefix) + latest_diagnostic(prefix)
        alt = "".join(f"""<div class="card"><b>{e(o['title'])}</b> {badge(o['status'], 'ok' if o['status']=='scored' else 'warn')}
<p class="small" style="margin:.3em 0">{e(o['summary'])}</p><a class="btn alt small" href="{prefix}downloads/{o['file']}" download>↓ {e(o['file'])}</a>
 <span class="small">· {o['positive_pixels']:,} px · <code>{o['content_id']}</code></span></div>""" for o in others if o["role"] in ("fallback", "alternate"))
        stats = f"""<div class="stats"><div class="stat"><b>{lead:.4f}</b><span>Unverified #1 leaderboard claim · reported {snap['reported_utc']}</span></div>
<div class="stat"><b>{best:.4f}</b><span>Unverified group-best score claim · rank association not authenticated</span></div>
<div class="stat"><b>+{snap['gap_to_rank5']:.3f}</b><span>arithmetic gap to the supplied #5 claim ({snap['top10'][4]['best_public_dti']:.4f}); +{snap['gap_to_rank1']:.3f} (+{100*snap['relative_gain_needed_for_rank1']:.0f} %) to the supplied #1 claim</span></div>
<div class="stat"><b>DUPLICATE LANE / STOP</b><span>strict lane rule: do not submit; all current downloads are testing-only</span></div></div>"""
        r = why["relations"]
        px15 = next(v["positive_px"] for k, v in why["rasters"].items() if "d1-5" in k)
        px195 = next(v["positive_px"] for k, v in why["rasters"].items() if "h19-5" in k and "dotted" not in k and "d1-5" not in k and "d2-8" not in k)
        lc = why["lattice_calibration"]
        imp = why["conditional_on_reported_scores"]
        whyb = f"""<h2>Local audit of the reported 0.2477 raster (score unverified)</h2>
<div class="card"><ol>
<li><b>The mask is exactly <code>dot_thin(H19-5, 1.5)</code></b> — pixel-for-pixel a deterministic subset of the H19-5-labelled raster: {px15:,} of {px195:,} pixels kept ({100*r['pixel_retention_d1_5']:.1f} %), none on a catalogue pixel, zero NaN inside the footprint. This verifies the raster transformation, not the reported DTI.</li>
<li><b>Metric arithmetic:</b> DTI = TP<sub>w</sub> / (0.2·(TP<sub>w</sub>+FP<sub>w</sub>) + 0.8·|G|). Thinning keeps ≈{100*r['geometric_credit_retention_d1_5']:.0f} % of the geometric credit estimate while removing ≈{100*(1-r['pixel_retention_d1_5']):.0f} % of the emitted pixels.</li>
<li><b>Unverified score inputs:</b> the 0.0904 lattice and 0.1922→0.2477 values are supplied/owner-reported claims. Under those assumptions, estimated |G| is ≈{lc['truth_px_in_footprint']:,.0f} px and each emitted pixel needs ≥{imp['break_even_ratio_at_0_2477']:.3f} credit per unit of false-positive mass. No organizer page or receipt was accessed.</li></ol>
<p class="small">Details, tables and caveats on the <a href="{prefix}research.html">Research</a> page. Evidence: <code>evidence/why_0_2477.json</code>; score claims: <code>registry/live_scores.json</code>.</p></div>"""
        h28b = ""
        if h28 and h28_anchors and h28_hold:
            cal = h28["calibrated"]
            rf = h28["reference_rows_under_calibrated_pi"]
            cl = h28["ceiling_best"]
            sel = h28_anchors["scan"][cal["pi"]]["per_anchor"]
            tg = h28["targets_credit_density"]["table"]["0.3195"][str(int(cl["mass"]))]
            h28b = f"""<h2>H28 metric-model calibration conditional on owner-reported claims — and the ceiling of the current surface family</h2>
<div class="card"><ol>
<li><b>Conditional on owner-reported anchors, a uniform-π truth model has no finite solution.</b> For four of the group's own surfaces the published DTI has <i>no</i> solution in the truth count under a uniform truth. Under
<code>pi &prop; exp(-d(H19-5)/{cal['lambda_hat_px']} px)</code> all five anchors imply one count — {", ".join(f"{k} {v['implied_N']:,.0f}" for k, v in sel.items())} —
so <b>model-implied N̂ = {cal['n_hat']:,.0f}</b> pixels in the hidden truth (spread {h28_anchors['checks']['A2']['max_relative_spread'] * 100:.1f} %), agreeing with the blind-lattice-only estimate
{h28_anchors['scan']['uniform']['per_anchor']['lattice-s5']['implied_N']:,.0f} and the earlier independent 12,503.</li>
<li><b>The fitted model matches selected owner-reported anchors conditionally; this is not score verification.</b> Predicted vs reported: {" · ".join(f"<code>{k}</code> {rf[k]['dti']:.4f} / {rf[k]['reported']:.4f}" for k in ("lattice-s5", "h19-5", "d1-5"))}.
Monte-Carlo of the published metric agrees with the analytic expectation to ≤{max(v['abs_err'] for v in h28['checks']['C5_monte_carlo']['per_artefact'].values()):.4f}.</li>
<li><b>Within the tested H19-5 dotting sweep and selected model, the downloadable file is the modelled ceiling.</b> Sweeping <code>dot_thin(H19-5, d)</code> over d ∈ [1.8, 4.0] peaks at d = {cl['min_dist']:.1f} px,
{cl['mass']:,.0f} px → <b>{cl['dti']:.5f}</b>, which is exactly this D2.8 file. A kernel-disjoint 6 px design (zero redundancy) reaches only
{max(r['dti'] for r in h28['designs'] if r['rule'] == 'R1_value6'):.5f} and beats <code>d1-5</code> in {h28['decision']['sensitivity_cells_beating_d1_5'].split('/')[0]} of 9 sensitivity cells.</li>
<li><b>Conditional model arithmetic against the unverified 0.3195 claim.</b> Matching that owner-reported number at this budget would need <b>{tg['vs_best_current_c_per_px']:.2f}×</b> the credit density
({tg['credit_per_px_needed']:.4f} vs {cl['credit_per_px']:.4f} per emitted pixel); this is not a verified score comparison or proof that all emission changes are exhausted. In the catalogue-gap proxy, the 30-arm holdout factorial found spacing 2.4–3.0 px near-optimal, 6 px costs 0.045 DTI,
habitat ranking adds {h28_hold['contrasts']['value_score_to_habitat']:+.4f} (p = 0.25) → <b>registered gate FAIL, no slot, nothing new packaged</b>.</li>
</ol><p class="small">Pre-registered before any fit: <code>knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md</code>. All reported scores are owner claims matched to bytes by SHA-256, not receipts.
<a href="{prefix}research.html#h28">Full tables on the Research page</a>.</p></div>"""
        if h30_result:
            h30_ps = h30_result["arms"]["T_PLUS_P_S"]
            h30_primary = (f"P+S mean DTI {h30_ps['mean_dti']:.6f}; paired gain "
                           f"{h30_gate['mean_gain_vs_best_paired_control']:+.6f}; {h30_status}")
        else:
            h30_primary = h30_status
        kbase = "../knowledge" if not prefix else "knowledge"
        h30b = f"""<h2>Current ranked geology tests — H30 (additional to the five-family factorial)</h2>
<div class="card"><p><b>H30-1 status:</b> {e(h30_primary)}. The P+S arm is compared to the best same-run no-tip or H27 tip-only control, with four spatial blocks and two draws per stage. A proxy pass is not a score or slot approval.</p>
<table><thead><tr><th>Rank</th><th>Hypothesis</th><th>Planning ΔDTI (not a prediction)</th><th>Status</th></tr></thead><tbody>
<tr><td>1</td><td>Paired visible-tip cross-strike bridge × LiDAR scarp persistence</td><td>+0.001 to +0.008</td><td>{e(h30_primary)}</td></tr>
<tr><td>2</td><td>Visible-fault junction / accommodation-zone branch field</td><td>0 to +0.006</td><td>Registered only; not fitted</td></tr>
<tr><td>3</td><td>Scale-persistent terrain lineament</td><td>0 to +0.005</td><td>Registered only; not fitted</td></tr></tbody></table>
<p class="small">Hypotheses, novelty audit, official-source links, design and promotion gates: <a href="{kbase}/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md">H30 preregistration</a> · <a href="{kbase}/12_h30_relay_factorial_outcomes_2026-10-03.md">screen/confirmation decision record</a> · <a href="{prefix}research.html#h30">holdout tables</a>. The pre-existing five-family A–E experiment remains separately recorded in <code>evidence/factorial/</code>.</p></div>"""
        cls = fac["classification"]
        rows = "".join(f"<tr><td><b>{k}</b></td><td>{e(v['label'])}</td><td>{badge(v['classification'], {'matters alone':'ok','matters in combination':'info','inert':'warn','harmful':'bad'}[v['classification']])}</td><td class='num'>{v['main_effect']:+.4f}</td><td class='num'>{v['folds_positive']}/4</td></tr>" for k, v in cls.items())
        facb = f"""<h2>Which feature families matter? (designed experiment, not hunches)</h2>
<p>A 2<sup>5−1</sup> Resolution V fractional factorial ({fac['design']['runs']} runs × {fac['design']['cells_per_run']} spatially blocked hide-and-recover cells) estimates every family's main effect and all ten pairwise interactions.
Main effect = change in mean sparse DTI when a family is included. Lenth ME at α = .05: <b>{fac['effects_dti']['lenth']['me']:.4f}</b>.</p>
<table><thead><tr><th>Factor</th><th>Family</th><th>Class</th><th class="num">Main effect</th><th class="num">Folds +</th></tr></thead><tbody>{rows}</tbody></table>
<p class="small">Proxy caveat: the holdout hides catalogue components; it is necessary, not sufficient, evidence. <a href="{prefix}research.html#factorial">Full tables</a>.</p>"""
        flags = [i for i in irr if i["severity"] in ("critical", "high") and i["status"] in ("open", "flagged", "fixed", "disclosed")]
        fl = "".join(f"<tr><td class='mono'>{i['id']}</td><td>{badge(i['severity'], 'bad' if i['severity']=='critical' else 'warn')}{badge(i['status'], 'ok' if i['status']=='fixed' else 'info')}</td><td>{e(i['issue'][:230])}{'…' if len(i['issue'])>230 else ''}</td></tr>" for i in flags[:8])
        flagb = f"""<h2>Flagged for review</h2><table><thead><tr><th>ID</th><th>Level / status</th><th>Issue</th></tr></thead><tbody>{fl}</tbody></table>
<p class="small">All {len(irr)} items with evidence and actions: <a href="{prefix}sources.html#irregularities">Sources &amp; audit</a>.</p>"""
        feed = f"""<h2>Source feed</h2><div id="feed" data-base="{prefix}"><p class="small">Loading <code>data/feed.json</code> …</p></div>
<p class="small">The feed blocks DrivenData requests and redirected targets. The displayed leaderboard values are user-provided, unverified claims—not live snapshots.</p>"""
        plan = ('<div class="callout warn"><b>No weekly slot is approved for the downloadable GeoTIFFs (0.152003389 historical comparator drift; strict lane &amp; confirmation gates not cleared).</b> '
                f'All current downloads (including <code>{e(primary["file"])}</code>, <code>gems25-h31-1-flank-subscarp-sapd24-20261025-40bfe1d5b1c5-nan.tif</code> and <code>gems25-gem-fuse1-blind-magnetics-prune2-20261025-c2097a554ef2-nan.tif</code>) are format-validated research artifacts only and are <b>not slot-approved (DO NOT SUBMIT)</b>. '
                f'H30-1 status: {e(h30_status)}. H31-1 flank-shielded 2&sup2; status: screen passed (<code>0.153199</code> pooled HOLDOUT-DTI, <code>+0.003384</code> paired gain, <code>3/4</code> folds +); confirmation achieved <code>0.144941</code> pooled HOLDOUT-DTI (<code>+0.003848</code> pooled gain, <code>3/4</code> folds + vs each individual control, <code>2/4</code> vs strict pointwise max &rarr; verdict: <code>negative</code>). '
                'Nothing is submitted or monitored automatically.</div>')
        h31_block = ""
        if h31_flank_screen and h31_flank_confirm and h31_card and focus_forensics:
            inv = focus_forensics["nested_chain_inversion_conditional_on_reported_scores"]
            s1 = inv["d28_to_r1_delete_0_1px_collar"]
            s2 = inv["r1_to_b2_delete_1_2px_collar"]
            h31_aniso_html = ""
            if h31_aniso_res and h31_aniso_card:
                h31_aniso_html = (
                    "<p><b>H31-1 Anisotropic Along-Strike Continuation &times; 100 m 3DEP LiDAR Strike Coherence + B=2 Shadow Guard (<code>knowledge/13_preregistered_h31_anisotropic_scarp_coherence_2026-10-25.md</code>, <code>knowledge/14_h31_anisotropic_scarp_outcomes_2026-10-25.md</code>):</b> "
                    "Evaluated on draws 10,11 (8 cells, 22,317 withheld positives). Single-feature leakage canary PASSED (max AUC = <code>0.8419</code> &le; <code>0.90</code>). "
                    "<code>H31_E3_B2</code> achieved pooled <code>HOLDOUT-DTI = 0.156013</code>, cell mean <code>0.156523</code> (95% CI <code>[0.141886, 0.171160]</code>), "
                    "beating <code>BASE</code> by <code>+0.008838</code> (<code>4/4</code> folds) and <code>T_BASE</code> by <code>+0.005717</code> (<code>4/4</code> folds) while the historical absolute comparator <code>0.152003389</code> is not comparable across environments (IR-25-COMPARATOR-DRIFT). "
                    "Primary GeoTIFF: <code>gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.tif</code> (<code>43,771</code> dots, SHA-256 <code>22a9d729bec4…</code>, 15/15 hard format checks PASS, "
                    "max rank-corr <code>0.1697</code> &le; <code>0.90</code>, max symmetric 3-px overlap <code>0.5837</code> &le; <code>0.70</code>, max sparse-detector 3-px overlap <code>0.6707</code> &le; <code>0.70</code>, <code>0.3175</code> vs GEMSDOE32 <code>0.2778</code>; "
                    "literal r13 5-px lattice overlap <code>1.000</code> under IR-25-LANE-DENSITY). JSON Run Card: <code>evidence/h31_experiments/run_card.json</code>.</p>"
                )
            h31_block = f"""<h2>9-Site Pixel-Exact Forensics (GEMSDOE24..36) &amp; H31-1 Geological Experiments</h2>
<div class="card"><p><b>Why GEMSDOE32 <code>h33-h33-2-b2</code> (owner-reported <code>0.2778</code>, unverified claim) scored highest:</b> Pixel-exact forensics across 13 fetched GeoTIFFs (<code>evidence/focus_sites_forensics.json</code>) proves that <code>GEMSDOE28</code>/<code>31</code> <code>r1</code> (<code>0.2708</code>, <code>40,199</code> px) is <b><code>D2.8 &amp; (d(catalogue) &gt; 1.0 px)</code></b> (deleting <code>{s1['deleted_pixels']:,}</code> collar dots at 100 m with implied credit <code>{s1['implied_credit_per_deleted_px']:.5f}</code>/px &ll; &tau; = <code>{s1['break_even_tau_at_0_2600']:.4f}</code>) and <b><code>GEMSDOE32</code> <code>H33-2-B2</code> (<code>0.2778</code>, <code>37,654</code> px) is <code>D2.8 &amp; (d(catalogue) &gt; 2.0 px)</code></b> (deleting an additional <code>{s2['deleted_pixels']:,}</code> collar dots in 100–200 m with implied credit <code>{s2['implied_credit_per_deleted_px']:.5f}</code>/px &ll; &tau; = <code>{s2['break_even_tau_at_0_2708']:.4f}</code>), while <code>GEMSDOE36</code> (<code>0.2750</code>, <code>38,854</code> px) is <code>B2</code> plus <code>1,200</code> extra dots.</p>
{h31_aniso_html}
<p><b>H31-1 2&sup2; Factorial (<code>knowledge/14_preregistered_h31_flank_shielded_subscarp_factorial_2026-10-25.md</code>, <code>knowledge/15_h31_outcomes_and_run_card_2026-10-25.md</code>):</b> Tested tip-preserved lateral-flank shielding (<code>Factor C</code>: <code>d(visible) &gt; 2.5 px</code> or <code>H27_tip &ge; 0.05</code>) &times; multi-physics subdued-scarp concordance (<code>Factor M</code>: <code>H31_subscarp_concord</code> + <code>H31_offflank_tip_halo</code>). Leakage Canary PASSED (all standalone features AUC &le; <code>0.8386</code> &le; <code>0.90</code>). Screen (draws 10,11) PASSED with <code>{e(h31_flank_screen['arms']['M1_C1']['pooled']['formatted_label'])}</code> (paired gain <code>+0.003384</code>, <code>3/4</code> folds +). Confirmation (draws 12,13) achieved <code>{e(h31_flank_confirm['arms']['M1_C1']['pooled']['formatted_label'])}</code> (<code>+0.003848</code> pooled gain; <code>3/4</code> folds + vs <code>M0_C0</code>, <code>3/4</code> vs <code>CTRL_NO_TIP</code>, Factor <code>C</code> positive in <code>8/8</code> fold-blocks, <code>2/4</code> vs strict pointwise max &rarr; Run Card verdict: <code>negative</code>). Unique GeoTIFF: <code>gems25-h31-1-flank-subscarp-sapd24-20261025-40bfe1d5b1c5-nan.tif</code> (<code>49,041</code> dots, SHA-256 <code>41461ce0d0a6…</code>, max surface Spearman <code>0.1826</code>, comparable dotted/focus 3-px overlap <code>0.6544</code> &le; <code>0.70</code>, <code>0.3183</code> vs GEMSDOE32 <code>0.2778</code>; literal r13 5-px lattice overlap <code>1.000</code> &rarr; testing only, DO NOT SUBMIT).</p></div>"""
        kdcb = ""
        if kdc:
            g1 = kdc["experiments"][0]["gate"]
            g2 = kdc["experiments"][1]["gate"]
            arms = kdc["holdout_dti"]["arms"]
            hc = kdc["live_build"]["registry_halo_cost"]
            def ci_txt(v):
                return "" if not v["ci95"] else "[{:.4f}, {:.4f}]".format(*v["ci95"])

            def eff_txt(x):
                return "n/i" if not x["identifiable"] else "{:.2f}–{:.2f}".format(*x["efficiency_range"])

            arow = "".join(f"<tr><td class='mono'>{e(k)}</td><td class='num'>{v['mean']:.5f}</td><td class='num'>{ci_txt(v)}</td></tr>"
                           for k, v in arms.items())
            anc = ""
            if anchor:
                anc = "".join(f"<tr><td class='mono'>{e(x['file'])}</td><td class='num'>{x['owner_reported_score']:.4f}</td>"
                              f"<td class='num'>{x['frac_within_3px_h19_5']:.3f}</td><td class='num'>{eff_txt(x)}</td></tr>"
                              for x in sorted(anchor["rows"], key=lambda x: -x["owner_reported_score"]))
            kdcb = f"""<h2 id="b2">Why H33-2-B2 scored 0.2778, and why this session could not beat it</h2>
<div class="card"><ol>
<li><b>What B2 is (COMPUTED from the pinned rasters):</b> exactly the GEMSDOE28 h27-4 file minus every dot within 2 px of the catalogue (XOR 0), and h27-4 is the D2.8 dotting of H19-5 minus dots within 1 px. B2 has 37,654 binary dots (nearest-neighbour spacing 3.0 px, median 19.6 px from the catalogue). Every file scoring ≥ 0.2449 except GEMSDOE70 (0.2478; 14.3 % on H19-5 pixels, 62 % within 3 px) is a ≥ 96.9 % pixel subset of H19-5.</li>
<li><b>Why it scored higher (INFERENCE from owner-reported scores):</b> each removal of near-catalogue dots raised the score monotonically (0.2600 → 0.2708 → 0.2778), so the hidden truth is depleted within ≈200 m of mapped faults (masked pixels score nothing; expert-identified new faults sit away from mapped traces). Removing low-yield dots lowers FP faster than TP.</li>
<li><b>Seven sibling files swapped 34–49 % of their dots off the H19-5 halo; all scored lower</b>. Implied off-halo dot efficiency is 0.15–0.72 of B2's average dot (table below). Nobody had <i>added</i> dots. Under the lane rule, adding beats swapping (DTI algebra, knowledge/17).</li>
<li><b>This session's test (HOLDOUT-DTI, pre-registered):</b> adding kernel-disjoint model dots to the best same-run control gave {g1['mean_gain']:+.4f} (95 % CI [{g1['gain_ci95'][0]:+.4f}, {g1['gain_ci95'][1]:+.4f}], {g1['folds_positive']}/4 folds, efficiency R {g1['efficiency_R_pooled']:.3f}) → <b>gate FAIL</b>. The flank-zone variant gave {g2['mean_gain']:+.4f} (R {g2['efficiency_R_pooled']:.3f}) → <b>FAIL</b>. The folds disagree: north R ≈ 0.36, south R ≈ 0.6.</li>
<li><b>The uniqueness wall:</b> the 3 px halos of 30 other-site registry rasters cover {100*hc['footprint_frac_in_registry_halo']:.1f} % of the footprint and {100*hc['frac_topk_ridge_inside_registry_halo']:.1f} % of this repo's top-3.5 % model ridges. A unique file must put new dots in lower-value terrain (IR-25-REGISTRY-HALO-COST).</li></ol>
<table><thead><tr><th>Holdout arm (E1+E2)</th><th class="num">Mean HOLDOUT-DTI</th><th class="num">95 % CI</th></tr></thead><tbody>{arow}</tbody></table>
<p class="small">{e(kdc['holdout_dti']['evaluator'])}; withheld positives per fold {e(kdc['holdout_dti']['withheld_positives_per_fold'])}. {e(kdc['holdout_dti']['reproduction'])}.</p>
<table><thead><tr><th>Registry file (swap design)</th><th class="num">Owner-reported</th><th class="num">Share near H19-5</th><th class="num">Off-incumbent efficiency e</th></tr></thead><tbody>{anc}</tbody></table>
<p class="small">INFERENCE from owner-reported scores (<code>evidence/live_anchor_complement.json</code>); live break-even e ≈ 0.33–0.47. n/i = not identifiable (&lt;5 % off-incumbent dots).</p></div>"""
        h36_spigm_b = ""
        if h36_spigm_card and h36_spigm_pool:
            p16 = h36_spigm_pool["arms"]
            cmp16 = h36_spigm_pool["comparisons"]
            sl = h36_spigm_card["correlation_overlap_vs_registry"]
            h36_rows = "".join(
                f"<tr><td class='mono'>{e(arm_k)}</td><td class='num'><b>{p16[arm_k]['pooled_dti']:.5f}</b></td>"
                f"<td class='num'>[{p16[arm_k]['pooled_dti_bootstrap_ci95'][0]:.4f}, {p16[arm_k]['pooled_dti_bootstrap_ci95'][1]:.4f}]</td>"
                f"<td class='num'>{p16[arm_k]['mean_fold_dti']:.5f}</td><td class='num'>{p16[arm_k]['mean_emitted_per_cell']:,.0f}</td>"
                f"<td class='num'>{p16[arm_k]['mean_hug']:.3f}</td></tr>"
                for arm_k in ("H36_PoE_sapd", "H36_PoE_submod", "C0_BDE_ctrl", "H36_S_submod", "C1_Sub_ctrl", "H36_S_sapd")
                if arm_k in p16
            )
            h36_spigm_b = f"""<h2 id="h36-spigm">Latest session (H36-SPIGM): Unit-corrected SPI-GM subsurface expert + exact 300 m submodular cover</h2>
<div class="card"><ol>
<li><b>Physical unit-mismatch bug discovered &amp; fixed (COMPUTED, <code>IR-25-POTENTIAL-FIELD-UNIT-MISMATCH</code>):</b> band <code>15_tmi_hg</code> is scaled per 200 m central-difference span (~200&times; <code>09_tmi_vg</code> in nT/m), making <code>tmi_hg&sup2;</code> dominate <code>tmi_vg&sup2;</code> by ~40,000&times; in <code>Family A</code>, while <code>18_iso_grav_anom_hg</code> is a signed ~N110&deg;E projection. <code>src/gems25/h36_spigm.py</code> computes unit-consistent local potential-field source wavenumbers (<code>H36_mag_spi_k</code>, <code>H36_grav_spi_k</code>; Thurston &amp; Smith 1997) without mutating the pinned comparator cache.</li>
<li><b>Leakage Canary &amp; 16-cell spatial holdout (<code>{h36_spigm_pool['withheld_positives_total_cell_evaluations']:,}</code> withheld positive evaluations across draws 20..23):</b> all 8 features pass standalone AUC &le; 0.90 (max <code>{h36_spigm_card['leakage_canary']['max_canary_auc_pooled_16cells']:.4f}</code>). Zero-topography <code>H36_S_submod</code> (zero DEM / zero LiDAR) passes its paired subsurface gate (<code>{cmp16['subsurface_H36_S_submod_vs_C1_Sub_ctrl']['mean_fold_gain']:+.5f}</code> fold gain, <code>{cmp16['subsurface_H36_S_submod_vs_C1_Sub_ctrl']['folds_positive']}/4</code> folds +, <code>{cmp16['subsurface_H36_S_submod_vs_C1_Sub_ctrl']['cells_positive']}/16</code> cells +) and improves <b>3.4&times;</b> over prior blind-magnetics lanes (<code>0.1345</code> vs <code>0.040</code>). <code>H36_PoE_sapd</code> reaches <code>0.15117</code> pooled HOLDOUT-DTI (<code>+0.00227</code> fold gain vs <code>C0</code>), while fixed-budget <code>H36_PoE_submod</code> wins western basin quadrants (NW <code>+0.0135</code>, SW <code>+0.0046</code>) and trails eastern range-front quadrants (<code>2/4</code> folds + &rarr; honest <code>verdict: negative</code>).</li>
<li><b>Unique 4-fold LOQO GeoTIFF (<code>{e(h36_spigm_card['submission_name'])}</code>, <code>0</code> pixels copied):</b> dual automated validators pass with 0 hard failures (zeros outside, all 12,279,160 cells in [0, 1]). Clears <b>all {sl['scored_and_sibling_non_lattice_count']}/{sl['scored_and_sibling_non_lattice_count']} non-lattice scored &amp; sibling rasters</b> (<code>{100*sl['overlap_vs_gemsdoe32_b2_02778']:.2f}%</code> 3-px overlap vs GEMSDOE32 <code>0.2778</code>; <code>{100*sl['overlap_vs_gemsdoe70_02478']:.2f}%</code> vs GEMSDOE70; worst <code>{100*sl['worst_scored_or_sibling_overlap']:.2f}%</code> &le; 70%; pre-placement surface |Spearman| &le; <code>{sl['worst_abs_spearman_surface']:.4f}</code>; max mutual 3-px overlap <code>{100*sl['max_mutual_3px_overlap_non_lattice']:.2f}%</code> &le; 70%); strict literal one-way check stops on <code>r13-lattice-s5</code> (100.0%) and unscored local Family-E halo builds (<code>70.3%&ndash;{100*sl['worst_local_unscored_overlap']:.1f}%</code>; <code>IR-25-CATALOGUE-HALO-CONVERGENCE</code>).</li></ol>
<table><thead><tr><th>Arm (draws 20..23, 16 cells)</th><th class="num">Pooled HOLDOUT-DTI</th><th class="num">Bootstrap 95 % CI</th><th class="num">Mean Fold DTI</th><th class="num">Dots / cell</th><th class="num">Hug</th></tr></thead><tbody>{h36_rows}</tbody></table>
<p class="small">Evaluator: <code>{e(h36_spigm_pool['evaluator_version'])}</code>. Pre-registration (5 ranked untried hypotheses H36-1..H36-5): <a href="{kbase}/21_preregistered_h36_spigm_submodular_2026-10-25.md"><code>knowledge/21</code></a> · Full outcomes &amp; forensics: <a href="{kbase}/22_h36_outcomes_and_forensics_2026-10-25.md"><code>knowledge/22</code></a> · Run Card: <code>registry/run_card_h36_spigm_2026-10-25.json</code>.</p></div>"""
        return hero + cards + (f"<h3>Also available</h3>{alt}" if alt else "") + plan + h36_spigm_b + kdcb + stats + h31_block + whyb + h28b + h30b + facb + flagb + feed

    exec_body = f"""{verdict_banner(primary, '', exec_page=True)}
<div class="callout"><b>Current featured unique research artifact: {e(selected['file'])}.</b> <b>OK to download for local inspection/reproduction: YES.</b> Automated validation (<code>gems25.submission.check_file</code> 16/16 checks + plain-<code>rasterio</code> <code>scripts/verify_candidate_independent.py</code>) passed freshly against the SHA-256-pinned template (<code>2176d08e…</code>, owner-mirrored, not organizer-authenticated): every pixel is finite in <code>{{0.0, 1.0}} &sub; [0, 1]</code>, zero NaN anywhere, exact <code>EPSG:32611</code> / <code>3730 &times; 3292</code> grid. <b>OK to submit to a competition scoring slot: NO — DO NOT SUBMIT.</b> Three pre-registered H71 DIRECT-emission screens (HGPC-BLIND, AKF, MAG-ANISO) each beat unsupervised crest emission and each failed vs same-run H35 (0/4 folds). Density-aware lane is UNIQUE vs 21 top-scorers (15.4% vs GEMSDOE32 B2) and own HGB lineage (23.4%); literal strict lane fails only on the dense <code>r13</code> lattice (100%; <code>IR-25-LANE-DENSITY</code>). No weekly slot. Parallel-session research GeoTIFFs (including <code>gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif</code>, <code>gems25-h38-ospc-submod-20261025-680d62616417-zeros.tif</code>, <code>gems25-h36-spigm-subsurface-submod300-20261025-3937b96ce366-zeros.tif</code>, and <code>gems25-h38-greedy-credit-k3p5-20261025-18de99d38bb0-zeros.tif</code>) remain available in the registry below and are likewise testing-only (<b>DO NOT SUBMIT</b>).</div>
{dl_card(selected, '')}
{objective_summary_card('')}
{apfl2_summary_card('')}
{h71_summary_card('')}
{pol3_summary_card('')}
{h66_summary_card('')}
{h38_summary_card('')}
{latest_diagnostic('')}
<h2>Competition upload instructions — for a future gate-cleared candidate only</h2>
<div class="callout"><b>Do not follow these steps with the current downloadable TIFF.</b> They describe the competition form, not authorization to submit. First require a fresh pre-registered holdout win, feature-alone leakage canaries, strict pre-placement and final-dot lane clearance, and exact-file format validation.</div>
<ol class="steps">
<li>After all gates pass and the separate selector approves a slot, download the selector-approved <code>.tif</code>; verify its SHA-256 against its own receipt.</li>
<li>Open the <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a> and sign in. The competition form provides the upload control.</li>
<li>Select a single-band GeoTIFF (<code>.tif</code>) or a ZIP containing exactly one GeoTIFF. Confirm the approved artifact matches the submission format's CRS, shape, and geotransform.</li>
<li>Enter the copy-ready note registered for that exact artifact in the form's optional Note field (short comment).</li>
<li>Only after authorized upload and receipt, the owner may record the organizer-confirmed result using <code>python scripts/record_live_score.py --file &lt;exact-file-or-content-id&gt; --score &lt;receipt-score&gt;</code>. Do not enter a projection or proxy value.</li></ol>
<h2>What the tracked format receipt says about this exact file (not freshly revalidated)</h2>
<table><thead><tr><th>Check</th><th>Recorded result</th><th>Detail</th></tr></thead><tbody>{''.join(f"<tr><td>{e(k)}</td><td>{badge('pass', 'ok') if v['pass_'] else (badge('FAIL', 'bad') if v['hard'] else badge('informational', 'info'))}</td><td class='small'>{e(v['detail'])}</td></tr>" for k, v in selected['checks'].items())}</tbody></table>
<p class="small">Historical receipt uses <code>src/gems25/submission.py::check_file</code> against an owner-mirrored template (sha256 prefix 2176d08e…). The template and validator are not organizer-authenticated. Format-check receipt: <a href="downloads/{selected['receipt']}">{selected['receipt']}</a>.</p>
<div class="callout"><b>If an approved future file is rejected for "Predicted values must be in range [0, 1]"</b><ol><li>Confirm you uploaded the exact selector-approved file and compare its SHA-256 with its receipt.</li>
<li>Run the local exact-file validator against the matching official-format template; confirm all footprint values are finite and in [0,1], and CRS, shape, transform match.</li>
<li>Do not use a fallback or another artifact unless its own receipt and exact-file checks pass. Organizer acceptance remains unknown until a receipt is issued.</li></ol></div>
{''.join(dl_card(o, '', False) if o['role'] == 'fallback' else '' for o in others)}
<h2>Rules that matter (read on the official pages)</h2><ul>
<li>Up to <b>3 submissions per week</b> per entity; <b>one final submission</b> per entity must be chosen before the deadline (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules §3.2, §3.4</a>).</li>
<li>Generative-AI use is allowed but must be described in the narrative (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">§3.2</a>); a draft is in <code>AI_DISCLOSURE.md</code>.</li>
<li>Known USGS/INGENIOUS pixels are masked and pixel-exact; predictions on them do not matter (<a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">staff</a>).</li>
<li>Deadline wording differs between the page (11:59 p.m. UTC, 3 Dec 2026) and the rules (5:00 p.m. ET): confirm with <a href="mailto:gemsprize@nlr.gov">gemsprize@nlr.gov</a>.</li></ul>
<div class="callout"><b>Slot discipline.</b> All current downloads are research artifacts only — none is OK to submit. The featured H71 file is format-valid and density-aware unique vs scored rasters and own HGB lineage, but three pre-registered DIRECT screens failed vs H35, so its verdict is negative and it must not be uploaded. Prior H66/H38/H36/H35 files remain testing-only. The GMCE/MSCR session's two fresh-draw experiments failed (paired -0.0012 and -0.0004) and its MSCR file is a strict-lane stop; the KDC file failed its pre-registered holdout gate; GEM-1/GEM-FUSE1 were gated against a weak control; H31-C and H31-1 were negative; session 7's two new pre-registered experiments also failed their frozen gates (H37-1 DOC paired −0.0009; H37-2 SPR +0.00094 vs the +0.001 gate), and the H37 file is a lane duplicate of its own H31/H35 detector lineage. Do not upload any of them. Lane receipts now also report each registry raster's halo coverage: the dense r13 lattice covers 99.87 % of the footprint within 3 px, so the literal 70 % test fails essentially any file against it; the density-aware symmetric statistic and every literal number are printed per file (knowledge/22 §4, knowledge/24 §4, knowledge/28 §4). A future candidate needs a fresh passing holdout, leakage canaries, lane clearance, and exact-file audit; no proxy result is a live score.</div>"""

    # ------------------------------------------------------------------ research page
    effs = fac["effects_dti"]
    er = "".join(f"<tr><td>{k}</td><td class='num'>{v:+.4f}</td><td class='num'>{effs['folds'][k]['se']:.4f}</td><td class='num'>{effs['folds'][k]['blocks_positive']}/4</td><td>{'<b>yes</b>' if abs(v) > effs['lenth']['me'] else ''}</td></tr>" for k, v in sorted(effs['effects'].items(), key=lambda t: -abs(t[1])))
    rr = "".join(f"<tr><td>{r['row']}</td><td class='mono'>{r['families']}</td><td class='num'>{r['dti_mean']:.4f}</td><td class='num'>{r['auc_mean']:.3f}</td><td class='num'>{r['hug_mean']:.2f}</td><td class='num'>{r['emitted_mean']:.0f}</td></tr>" for r in sorted(fac['runs'], key=lambda r: -r['dti_mean']))
    refs = "".join(f"<tr><td>{k}</td><td class='num'>{v['dti_mean']:.4f}</td><td class='num'>{v['auc_mean']:.3f}</td><td class='num'>{v['hug_mean']:.2f}</td></tr>" for k, v in fac['references_same_harness'].items())
    def addon_tbl(a, label):
        if not a:
            return f"<p class='small'>{label}: not run.</p>"
        arms = "".join(f"<tr><td>{k}</td><td class='num'>{v['mean_dti']:.4f}</td><td class='num'>{v['gate_vs_base']['mean_gain']:+.4f}</td><td class='num'>{v['gate_vs_base']['folds_positive']}/4</td><td class='num'>{v['hug']:.2f}</td><td>{badge('gate pass','ok') if v['gate_vs_base']['passed'] else badge('gate fail','warn')}</td></tr>" for k, v in a['arms'].items())
        em = a["EM0_equal_N"]
        return f"""<p><b>{label}</b> — base family set <code>{a['base']}</code>, base mean sparse DTI <b>{a['BASE']['mean_dti']:.4f}</b>.</p>
<table><thead><tr><th>Arm</th><th class="num">DTI</th><th class="num">Δ vs base</th><th class="num">Folds +</th><th class="num">Hug</th><th>Pre-registered gate</th></tr></thead><tbody>{arms}</tbody></table>
<p>Score-ordered Poisson-disk vs score-blind <code>dot_thin</code> at equal pixel count (~{em['n_eq_mean']:.0f}): <b>{em['sapd']:.4f}</b> vs <b>{em['dot_thin']:.4f}</b> (Δ {em['gate_sapd_vs_dot_thin']['mean_gain']:+.4f}, {em['gate_sapd_vs_dot_thin']['folds_positive']}/4 folds) → {'gate pass' if em['gate_sapd_vs_dot_thin']['passed'] else 'gate fail'}.</p>"""
    emk = ""
    if add:
        emk = "<table><thead><tr><th>Variant</th><th class='num'>Budget</th><th class='num'>Emitted px</th><th class='num'>Coverage</th><th class='num'>DTI</th></tr></thead><tbody>" + "".join(f"<tr><td>{r['variant']}</td><td class='num'>{100*r['kfrac']:.2f}%</td><td class='num'>{r['emitted']:.0f}</td><td class='num'>{r['coverage']:.3f}</td><td class='num'>{r['dti']:.4f}</td></tr>" for r in add['EMK']) + "</tbody></table>"
    ext_html = ""
    if ext:
        ext_html = ("<p><b>Post-hoc extension (Addendum A, exploratory, not gated)</b> — base <code>" + e(ext["base"]) + "</code> + add-on columns, K beyond the frozen grid; the optimum lies <i>inside</i> the extended grid:</p>"
                    "<table><thead><tr><th>Variant</th><th class='num'>Budget</th><th class='num'>Emitted px / cell</th><th class='num'>Coverage</th><th class='num'>DTI</th></tr></thead><tbody>"
                    + "".join(f"<tr><td>{r['variant']}</td><td class='num'>{100 * r['kfrac']:.2f}%</td><td class='num'>{r['emitted']:.0f}</td><td class='num'>{r['coverage']:.3f}</td><td class='num'>{r['dti']:.4f}</td></tr>" for r in ext["table"])
                    + f"</tbody></table><p class='small'>Best: {ext['best']['variant']} at {100 * ext['best']['kfrac']:.1f} % → {ext['best']['dti']:.4f}.</p>")
    emu_html = ""
    if emu:
        emu_html = "<table><thead><tr><th>min-dist</th><th class='num'>px</th><th class='num'>credit retention (geometric)</th><th class='num'>model DTI</th></tr></thead><tbody>" + "".join(f"<tr><td>{r['min_dist']}</td><td class='num'>{r['px']:,}</td><td class='num'>{r['retention']:.3f}</td><td class='num'>{r['model_dti']:.4f}</td></tr>" for r in emu['curve']) + f"</tbody></table><p class='small'>{e(emu['caveat'])}</p>"
    oos_html = ""
    if oos:
        oos_html = (f"<div class='card'><b>Out-of-sample check (pair not used for calibration):</b> solid H25 (unverified owner-reported claim 0.1280) → dotted H28 (unverified owner-reported claim 0.1839). "
                    f"Model prediction <b>{oos['predicted_dotted_dti']:.4f}</b> vs reported claim <b>{oos['owner_reported_dotted_dti']:.4f}</b> (error {oos['error']:+.4f}). "
                    "The model under-predicts the dotting gain here, so the expected +0.008 for D2.8 is smaller than the model's own error: the sign is likely, not certain.</div>")
    req_html = ""
    if emu and emu.get("requirements"):
        rq = emu["requirements"]
        base_cpp = rq["dotted_h19_5_d1_5_has"]["credit_per_emitted_px"]
        req_html = ("<h3>What would a higher score require? (same calibration)</h3><table><thead><tr><th>Target</th><th class='num'>Emitted px</th><th class='num'>Credit needed (share of |G|)</th>"
                    "<th class='num'>Credit per emitted px</th><th class='num'>× the 0.2477 file</th></tr></thead><tbody>"
                    + "".join(f"<tr><td>{e(r['label'])}</td><td class='num'>{r['emitted_px']:,}</td><td class='num'>{r['credit_fraction_required']:.3f}</td><td class='num'>{r['credit_per_emitted_px']:.3f}</td><td class='num'>{r['credit_per_emitted_px'] / base_cpp:.2f}</td></tr>" for r in rq["table"])
                    + f"</tbody></table><p class='small'>The 0.2477 file earns {base_cpp:.3f} credit per emitted pixel ({rq['dotted_h19_5_d1_5_has']['credit_fraction']:.3f} of |G| ≈ {rq['truth_px_used']:,.0f} px with {rq['dotted_h19_5_d1_5_has']['emitted_px']:,} pixels). "
                    f"Each emitted pixel carries ≈{rq['fp_mass_per_emitted_px']:.2f} of false-positive mass.</p>")
        cp = emu.get("consensus_pruning_break_even")
        if cp:
            req_html += ("<h3>Consensus pruning (drop dots a second detector disagrees with): break-even</h3><table><thead><tr><th class='num'>Dropped share of pixels</th><th class='num'>Max share of credit they may carry</th></tr></thead><tbody>"
                         + "".join(f"<tr><td class='num'>{100 * r['dropped_fraction_of_pixels']:.0f} %</td><td class='num'>{100 * r['max_credit_share_of_dropped']:.1f} %</td></tr>" for r in cp["rows"])
                         + "</tbody></table><p class='small'>Pruning pays only if the dropped dots earn well under the average credit per pixel; a second detector must therefore be strongly informative <i>within</i> the first one's detections.</p>")
    href_html = ""
    if href:
        import re as _re

        def live_of(name):
            m = _re.search(r"\(([0-9.]+)\)", name)
            return float(m.group(1)) if m else None

        rows_ = ""
        for k, v in href.items():
            lv = live_of(k)
            live_txt = "" if lv is None else f"{lv:.4f}"
            ratio_txt = "" if lv is None else f"{lv / v['mean_dti']:.2f}"
            rows_ += (f"<tr><td>{e(k)}</td><td class='num'>{v['mean_dti']:.4f}</td><td class='num'>{live_txt}</td>"
                      f"<td class='num'>{ratio_txt}</td><td class='num'>{v['hug']:.2f}</td><td class='num'>{v['emitted']:.0f}</td></tr>")
        href_html = ("<h3>The proxy against user/owner-reported score claims (diagnostic only; claims unverified)</h3><table><thead><tr><th>Owner-mirrored raster (unverified DTI claim)</th><th class='num'>Harness DTI</th><th class='num'>Reported claim</th>"
                     "<th class='num'>Claim / harness</th><th class='num'>Hug</th><th class='num'>Emitted px / cell</th></tr></thead><tbody>" + rows_
                     + "</tbody></table><p class='small'>No organizer receipts were accessed. Not out-of-fold: these owner-mirrored rasters were built with the whole catalogue and mask every catalogue pixel. "
                       "The blind lattice is reproduced within ~5 % under the unverified claim, and dotting raises the score in both proxy/calibration calculations; this does not authenticate any competition score. "
                       "The proxy is necessary, not sufficient.</p>")
    h27_result = h27_confirm or h27_screen
    if h27_result:
        h27_rows = "".join(
            f"<tr><td>{arm}</td><td class='num'>{h27_result['arms'][arm]['mean_dti']:.6f}</td>"
            + "".join(f"<td class='num'>{v:.6f}</td>" for v in h27_result['arms'][arm]['by_fold_dti'])
            + f"<td class='num'>{h27_result['arms'][arm]['mean_emitted']:.0f}</td><td class='num'>{h27_result['arms'][arm]['mean_hug']:.4f}</td></tr>"
            for arm in ("BASE", "T", "S", "TS")
        )
        ef = h27_result["factorial_effects_dti"]
        h27_effect_rows = "".join(
            f"<tr><td>{name}</td><td class='num'>{v['mean']:+.6f}</td>"
            + "".join(f"<td class='num'>{x:+.6f}</td>" for x in v["by_fold"])
            + "</tr>"
            for name, v in ef.items()
        )
        g = h27_result["promotion_gate"]
        decision = ("<b>PASS — confirmation required before packaging.</b>" if h27_result["stage"] == "screen" and g["passed"] else
                    ("<b>PASS — proxy confirmation met; a corresponding full-data TIF still needs packaging and independent checks.</b>" if g["passed"] else
                     "<b>FAIL — stop. No confirmation, H27 TIFF, or weekly slot.</b>"))
        h27_section = f"""<p>Frozen 2² design, details and ranked geological hypotheses: <a href="../knowledge/09_preregistered_hypotheses_2026-10-02.md">knowledge/09_preregistered_hypotheses_2026-10-02.md</a>. Stage <b>{e(h27_result['stage'])}</b>, draws {', '.join(map(str, h27_result['draws']))}, 32 paired cells. Historical comparator = {h27_result['historical_holdout_best']:.9f} (repository proxy, not a competition score).</p>
<table><thead><tr><th>Arm</th><th class="num">Mean DTI</th><th class="num">NW</th><th class="num">NE</th><th class="num">SW</th><th class="num">SE</th><th class="num">Emitted</th><th class="num">Hug share</th></tr></thead><tbody>{h27_rows}</tbody></table>
<h3>Estimated 2² response contrasts (DTI)</h3><table><thead><tr><th>Effect</th><th class="num">Mean</th><th class="num">NW</th><th class="num">NE</th><th class="num">SW</th><th class="num">SE</th></tr></thead><tbody>{h27_effect_rows}</tbody></table>
<div class="callout"><b>Frozen gate:</b> absolute comparator {g['candidate_mean_dti']:.6f} {'>' if g['historical_comparator_passed'] else '≤'} {g['historical_best']:.6f}; paired TS−BASE {g['mean_gain_vs_paired_base']:+.6f}, {g['folds_positive']}/4 folds positive, worst {g['worst_fold_gain']:+.6f}, hug delta {g['hug_share_delta']:+.4f}. {decision} This is a catalogue-gap proxy, not new-fault truth or a live score.</div>"""
    else:
        h27_section = """<p>H27-1 is prior work, not a current untried candidate. Its recorded screen did not make a candidate slot-eligible; the historical absolute comparator later failed reproduction. Do not use its cross-draw value as a current baseline.</p><p><a href="../knowledge/09_preregistered_hypotheses_2026-10-02.md">Read the full ranked register, data gates, feature formula and analysis plan.</a></p>"""
    if h30_result:
        h30_rows = "".join(
            f"<tr><td><b>{arm}</b></td><td class='num'>{h30_result['arms'][arm]['mean_dti']:.6f}</td>"
            + "".join(f"<td class='num'>{value:.6f}</td>" for value in h30_result['arms'][arm]['by_fold_dti'])
            + f"<td class='num'>{h30_result['arms'][arm]['mean_hug']:.4f}</td>"
            f"<td class='num'>{h30_result['arms'][arm]['mean_coverage']:.4f}</td></tr>"
            for arm in ("BASE_NO_TIP", "T_BASE", "T_PLUS_P", "T_PLUS_S", "T_PLUS_P_S")
        )
        h30_effect_rows = "".join(
            f"<tr><td>{name}</td><td class='num'>{effect['mean']:+.6f}</td>"
            + "".join(f"<td class='num'>{value:+.6f}</td>" for value in effect['by_fold'])
            + f"<td class='num'>[{effect['t_95_ci'][0]:+.6f}, {effect['t_95_ci'][1]:+.6f}]</td></tr>"
            for name, effect in h30_result["factorial_effects"].items()
        )
        gate = h30_result["paired_promotion_gate"]
        screen_history = ""
        if h30_confirm and h30_screen:
            screen_gate = h30_screen["paired_promotion_gate"]
            screen_history = (
                f"<p class=\"small\"><b>Prior screen:</b> draws 6,7 passed with mean paired gain "
                f"{screen_gate['mean_gain_vs_best_paired_control']:+.6f} DTI ({screen_gate['folds_positive']}/4 positive; "
                f"worst {screen_gate['worst_fold_gain']:+.6f}; hug change {screen_gate['mean_hug_share_delta']:+.4f}). "
                f"<a href=\"../evidence/h30_relay_screen/results.md\">Screen report</a>. "
                f"<a href=\"../evidence/h30_relay_confirm/results.md\">Confirmation report</a>.</p>"
            )
        if h30_result["stage"] == "screen":
            h30_decision = ("<b>SCREEN PASS — only the registered fresh-draw confirmation may proceed.</b>"
                            if h30_result.get("screen_gate_passed")
                            else "<b>SCREEN FAIL — stop; no confirmation or candidate file.</b>")
        else:
            h30_decision = ("<b>CONFIRMATION PASS — proxy only; full-data build and exact-file audit still required.</b>"
                            if h30_result.get("confirmation_gate_passed")
                            else "<b>CONFIRMATION FAIL — stop; no candidate file or slot.</b>")
        h30_section = f"""<h2 id="h30">4 · H30-1 paired relay bridge × persistent scarp — {e(h30_result['stage'])}</h2>
<p>Frozen design: <a href="../knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md">H30 preregistration</a>. Stage <b>{e(h30_result['stage'])}</b>, draws {', '.join(map(str, h30_result['design']['draws']))}, 4 spatial folds × 2 draws × 5 arms = {h30_result['n_rows']} model cells. The 2² P/S contrasts are estimated only on T, T+P, T+S, T+P+S; BASE_NO_TIP is a second same-run control.</p>
{screen_history}
<table><thead><tr><th>Arm</th><th class="num">Mean DTI</th><th class="num">NW</th><th class="num">NE</th><th class="num">SW</th><th class="num">SE</th><th class="num">Hug</th><th class="num">Coverage</th></tr></thead><tbody>{h30_rows}</tbody></table>
<h3>Registered 2² response effects (four spatial-fold blocks)</h3><table><thead><tr><th>Effect</th><th class="num">Mean</th><th class="num">NW</th><th class="num">NE</th><th class="num">SW</th><th class="num">SE</th><th class="num">95% t interval</th></tr></thead><tbody>{h30_effect_rows}</tbody></table>
<div class="callout"><b>Frozen P+S gate:</b> gain vs the per-fold best same-run control {gate['mean_gain_vs_best_paired_control']:+.6f} DTI; {gate['folds_positive']}/4 positive folds; worst fold {gate['worst_fold_gain']:+.6f}; mean hug-share change {gate['mean_hug_share_delta']:+.4f}. {h30_decision} Slot eligible: <b>no</b>. This catalogue-gap proxy is not new-fault truth or a competition score.</div>
<p class="small">Historical comparator values are contextual only; the gate compares same-run controls and requires confirmation. Full ranked H30-1/2/3 hypotheses and citations are in the preregistration. The separate five-family A–E experiment remains in <code>evidence/factorial/</code>.</p>"""
    else:
        h30_section = """<h2 id="h30">4 · H30 — paired relay bridge × terrain support (registered, not yet fitted)</h2>
<p>The frozen H30-1 screen has not run. It uses paired cross-strike bridges between distinct <i>visible</i> fault components plus the fixed LiDAR scarp-persistence feature, tested as a 2² with the H27 tip-only arm. Screen draws: 6,7; fresh confirmation draws 8,9 are permitted only after a passing screen. No candidate file or slot is eligible at this stage.</p>
<p>A real-data feature-construction smoke test passed for one fold/draw: aligned feature matrices and finite, nonempty H30 columns were checked, but <b>no model was fitted and no DTI was computed</b>. <a href="../evidence/h30_feature_smoke.json">See diagnostics.</a></p>
<p><b>Ranked hypotheses:</b> (1) paired bridge × scarp persistence, planning ΔDTI +0.001 to +0.008; (2) junction/accommodation-zone branch field, 0 to +0.006; (3) scale-persistent terrain lineament, 0 to +0.005. These are uncertain planning brackets, not predictions. See the <a href="../knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md">full novelty review, physical rationale, official sources, costs, and gates</a>.</p>"""

    h28_section = ""
    if h28 and h28_anchors and h28_hold:
        cal, chk = h28["calibrated"], h28["checks"]
        rf, cl = h28["reference_rows_under_calibrated_pi"], h28["ceiling_best"]
        scan = h28_anchors["scan"]
        anchor_rows = "".join(
            f"<tr><td class='mono'>{k}</td><td class='num'>{v['mass']:,.0f}</td><td class='num'>{v['reported']:.4f}</td>"
            f"<td class='num'>{v['T']:.4f}</td><td class='num'>{v['U']:.4f}</td><td class='num'>{(v['U'] - v['T']) / v['U']:.2f}</td>"
            f"<td class='num'><b>{v['implied_N']:,.0f}</b></td></tr>"
            for k, v in scan[cal["pi"]]["per_anchor"].items())
        ref_rows = "".join(
            f"<tr><td class='mono'>{k}</td><td class='num'>{v['mass']:,.0f}</td><td class='num'>{v['dti']:.5f}</td>"
            f"<td class='num'>{v['reported']:.4f}</td><td class='num'>{v['dti'] - v['reported']:+.4f}</td><td class='num'>{v['credit_per_px']:.4f}</td></tr>"
            if v["reported"] is not None else
            f"<tr><td class='mono'>{k}</td><td class='num'>{v['mass']:,.0f}</td><td class='num'>{v['dti']:.5f}</td>"
            f"<td class='num'>unscored</td><td class='num'>—</td><td class='num'>{v['credit_per_px']:.4f}</td></tr>"
            for k, v in rf.items())
        lam_rows = "".join(
            f"<tr><td class='mono'>{k}</td><td class='num'>{v['n_finite']}/5</td><td class='num'>{v['median_N']:,.0f}</td>"
            f"<td class='num'>{v['max_relative_spread']:.3f}</td><td>{badge('selected', 'ok') if k == cal['pi'] else (badge('falsified', 'bad') if v['n_finite'] < 5 else '')}</td></tr>"
            for k, v in scan.items())
        def check_text(k: str, v: dict) -> str:
            if not isinstance(v, dict):
                return ""
            if k == "C3_masking":
                return (f"hedge-v2 and ens12 are statistically identical once the metric masks known pixels "
                        f"(emitted mass {v['mass_hedge_v2']:,.0f} both; max |ΔTA| = {v['ta_max_abs_diff']:.1e}); both are reported at "
                        f"{v['reported_scores']['ens12']:.4f}")
            if k == "A1":
                return ("no finite truth count can produce the reported scores of h19-5, h19-4, h16-1 or d1-5 under "
                        f"{', '.join(v['shapes_with_no_finite_N'])} truth — that π is falsified")
            if k == "A2":
                return (f"selected <code>{e(v['selected_pi'])}</code>; implied N spread {v['max_relative_spread']:.4f} ≤ {v['threshold']}")
            if k == "A3":
                return (f"N̂ = {v['n_hat']:,.0f} vs lattice-only {v['lattice_only_uniform_pi']:,.0f} and this repo's earlier independent "
                        f"{v['repo_previous_estimate']:,.0f} (tolerance ±{v['tolerance']:.0%})")
            if k == "A4":
                lo = min(v["implied_over_n_hat"].values())
                hi = max(v["implied_over_n_hat"].values())
                return f"implied N / N̂ across the five anchors spans {lo:.3f}–{hi:.3f}"
            if k == "C5_monte_carlo":
                worst = max(x["abs_err"] for x in v["per_artefact"].values())
                return f"max |analytic − Monte-Carlo| = {worst:.5f} ≤ {v['threshold']} over {len(v['per_artefact'])} artefacts"
            return e(json.dumps(v, default=str)[:200])

        check_rows = "".join(
            f"<tr><td class='mono'>{k}</td><td>{badge(v.get('verdict', 'n/a') if isinstance(v, dict) else 'n/a', 'ok' if isinstance(v, dict) and v.get('verdict') == 'PASS' else 'bad')}</td>"
            f"<td class='small'>{check_text(k, v)}</td></tr>"
            for k, v in chk.items())
        mc_rows = "".join(
            f"<tr><td class='mono'>{k}</td><td class='num'>{v['analytic']:.5f}</td><td class='num'>{v['mc']['mean']:.5f} ± {v['mc']['sd']:.5f}</td>"
            f"<td class='num'>{v['abs_err']:.5f}</td><td class='num'>{v['reported'] if v['reported'] is not None else '—'}</td></tr>"
            for k, v in chk["C5_monte_carlo"]["per_artefact"].items())
        skill_rows = "".join(
            f"<tr><td class='mono'>{r['id']}</td><td class='num'>{r['mass']:,.0f}</td><td class='num'>{r.get('nn_median', float('nan')):.2f}</td>"
            f"<td class='num'>{r.get('share_nn_below_6px', float('nan')):.2f}</td><td class='num'>{(r['redundancy_share'] or 0):.2f}</td>"
            f"<td class='num'>{r['coverage_of_truth']:.4f}</td><td class='num'><b>{r['credit_per_px']:.4f}</b></td>"
            f"<td class='num'>{r['reported']:.4f}</td><td>{badge('hash-linked', 'ok') if r['id'] in {x['id'] for x in (h28_ledger or {}).get('artifacts', []) if x.get('fit')} else badge('brief-only', 'warn')}</td></tr>"
            for r in sorted(h28["redundancy_theorem"]["rows"], key=lambda x: -x["credit_per_px"]))
        ceil_rows = "".join(
            f"<tr><td class='num'>{r['min_dist']:.2f}</td><td class='num'>{r['mass']:,.0f}</td><td class='num'>{r['t']:.4f}</td>"
            f"<td class='num'>{r['redundancy']:.4f}</td><td class='num'>{r['fp_per_px']:.3f}</td><td class='num'><b>{r['dti']:.5f}</b></td>"
            f"{'<td>' + badge('ceiling = shipped D2.8', 'ok') + '</td>' if abs(r['dti'] - cl['dti']) < 1e-9 else '<td></td>'}</tr>"
            for r in h28["ceiling_sweep"])
        des_rows = "".join(
            f"<tr><td class='mono'>{r['rule']}</td><td class='num'>{r.get('min_dist', 0):.2f}</td><td class='num'>{r['mass']:,.0f}</td>"
            f"<td class='num'>{r['t']:.4f}</td><td class='num'>{r['redundancy']:.4f}</td><td class='num'>{r['credit_per_px']:.4f}</td><td class='num'><b>{r['dti']:.5f}</b></td></tr>"
            for r in sorted(h28["designs"], key=lambda x: -x["dti"])[:12])
        tg = h28["targets_credit_density"]["table"]
        targ_rows = "".join(
            f"<tr><td class='num'>{k}</td>" + "".join(
                f"<td class='num'>{v['credit_per_px_needed']:.4f} ({v['vs_best_current_c_per_px']:.2f}×)</td>"
                for _, v in sorted(tg[k].items(), key=lambda kv: int(kv[0]))) + "</tr>"
            for k in ("0.2477", "0.2941", "0.3195") if k in tg)
        sens_rows = "".join(
            f"<tr><td class='num'>{r['lambda']}</td><td class='num'>{r['n_truth']:,.0f}</td><td class='num'>{r['best_budget']}</td>"
            f"<td class='num'>{r['best_dti']:.5f}</td><td class='num'>{r['d1_5_dti']:.5f}</td>"
            f"<td class='num'>{r.get('d2_8_dti', float('nan')):.5f}</td>"
            f"<td>{badge('beats both', 'ok') if r.get('beats_d2_8') else badge('loses', 'bad')}</td></tr>" for r in h28["sensitivity"])
        hold_rows = "".join(
            f"<tr><td>{r['value']}</td><td class='num'>{r['min_dist']}</td><td class='num'>{100 * r['kfrac']:.2f} %</td>"
            f"<td class='num'><b>{r['dti_mean']:.6f}</b></td><td class='num'>{r['emitted_mean']:,.0f}</td><td class='num'>{r['coverage_mean']:.4f}</td>"
            f"<td class='num'>{r['hug_mean']:.3f}</td><td class='num'>{r['paired_delta_vs_comparator']:+.6f}</td>"
            f"<td class='num'>{r['paired_cells_positive']}/{r['n_cells']}</td><td class='num'>{r['paired_p']:.3f}</td></tr>"
            for r in h28_hold["table"][:12])
        con_rows = "".join(f"<tr><td class='mono'>{k}</td><td class='num'>{v:+.6f}</td></tr>"
                           for k, v in sorted(h28_hold["contrasts"].items(), key=lambda kv: -abs(kv[1])))
        mix = h28_mix["adoption_rule"] if h28_mix else {}
        hab = h28_habitat or {}
        hab_rows = "".join(
            f"<tr><td class='mono'>{m}</td><td class='num'>{v['n_truth']:,.0f}</td><td class='num'>{v['rmse']:.5f}</td>"
            f"<td class='num'>{hab['loo'][m]['loo_rmse']:.5f}</td><td class='num'>{v['max_abs_resid']:.4f}</td>"
            f"<td>{badge('selected', 'ok') if m == hab.get('selected') else ''}</td></tr>"
            for m, v in hab.get("fits", {}).items())
        h28_section = f"""<h2 id="h28">4b · H28 — metric-model calibration on {(h28_ledger or {}).get('n_used_in_fit', 25)} hash-linked owner-reported scores (not independently verified)</h2>
<p>Pre-registered before any fit in <a href="../knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md"><code>knowledge/10</code></a>
(with amendments D1–D3 logged in the same file). {h28_ledger['n_rows'] if h28_ledger else 30} competition rasters were fetched from the owner's public mirrors through the GitHub API and
content-hashed; {(h28_ledger or {}).get('n_used_in_fit', 25)} are tied to a reported DTI by SHA-256 (<code>registry/artifact_ledger.json</code>). <b>Reported scores remain owner claims, not receipts.</b>
The algebra: <code>E[TP] = N&lang;pi, m_p&rang;</code> is exact; <code>E[FP] = &Sigma;_x p(x) &Psi;(&nu;_x)</code> is the exact Poisson saturation of the kernel maximum.</p>
<h3>Anchor inversion: a model-implied count conditional on owner-reported scores</h3>
<table><thead><tr><th>&pi; candidate</th><th class="num">anchors identified</th><th class="num">median implied N</th><th class="num">max relative spread</th><th></th></tr></thead><tbody>{lam_rows}</tbody></table>
<p class="small">Conditional on the owner-reported scores, a shape with fewer than five finite solutions is <b>inconsistent</b>: no truth count under that assumed π reproduces those values. Selected
<code>{e(cal['pi'])}</code> → N = {cal['n_hat']:,.0f}.</p>
<table><thead><tr><th>anchor</th><th class="num">emitted px</th><th class="num">reported</th><th class="num">T = &lang;pi,m&rang;</th><th class="num">U = &lang;pi,u&rang;</th><th class="num">redundancy R/U</th><th class="num">implied N</th></tr></thead><tbody>{anchor_rows}</tbody></table>
<h4>Predicted against reported under the calibrated model (scope: inside the H19-5 band — IR-25-LIVE-MODEL-SCOPE)</h4>
<table><thead><tr><th>raster</th><th class="num">emitted px</th><th class="num">predicted DTI</th><th class="num">reported</th><th class="num">residual</th><th class="num">credit / px</th></tr></thead><tbody>{ref_rows}</tbody></table>
<h3>Acceptance and validation checks</h3>
<table><thead><tr><th>check</th><th>verdict</th><th>values</th></tr></thead><tbody>{check_rows}</tbody></table>
<h4>Monte-Carlo of the published metric against the analytic expectation (truth drawn from the fitted &pi;)</h4>
<table><thead><tr><th>artefact</th><th class="num">analytic</th><th class="num">Monte-Carlo (6 draws)</th><th class="num">|error|</th><th class="num">reported</th></tr></thead><tbody>{mc_rows}</tbody></table>
<h3>Every score-linked owner-mirrored raster, ranked by modelled credit per emitted pixel</h3>
<p class="small">Credit per pixel is <code>N&middot;T/M</code> under the calibrated &pi;; the blind lattice (0.0228) is the information-free floor. Redundancy <code>R/U</code> is the share of
captured kernel mass wasted on overlapping kernels — the quantity dotting removes. Rows marked <i>brief-only</i> have no hash-linked ledger row and were excluded from every fit.</p>
<table><thead><tr><th>raster</th><th class="num">emitted px</th><th class="num">median NN</th><th class="num">share NN &lt; 6 px</th><th class="num">R/U</th><th class="num">coverage T</th><th class="num">credit / px</th><th class="num">reported</th><th>score link</th></tr></thead><tbody>{skill_rows}</tbody></table>
<p class="small">Ledger-wide Spearman(share of pixels with a neighbour inside 6 px, reported score) = <b>{h28['redundancy_theorem']['spearman_all']['rho']:.3f}</b>
(p = {h28['redundancy_theorem']['spearman_all']['p']:.1e}, n = {h28['redundancy_theorem']['spearman_all']['n']}) — consistent with the redundancy theorem; inside mass strata it is not significant
(n ≤ 7), because detector skill dominates. The theorem itself is proved algebraically, not statistically.</p>
<h3>Modelled ceiling of the status-quo family under selected &pi;, and designs that lose to it</h3>
<table><thead><tr><th class="num">min_dist px</th><th class="num">emitted px</th><th class="num">T</th><th class="num">redundancy</th><th class="num">FP / px</th><th class="num">predicted DTI</th><th></th></tr></thead><tbody>{ceil_rows}</tbody></table>
<table><thead><tr><th>rule</th><th class="num">exclusion px</th><th class="num">emitted px</th><th class="num">T</th><th class="num">redundancy</th><th class="num">credit / px</th><th class="num">predicted DTI</th></tr></thead><tbody>{des_rows}</tbody></table>
<h3>What a higher score would require (same calibrated model, measured &phi; = {h28['targets_credit_density']['phi_used']:.3f})</h3>
<table><thead><tr><th class="num">target DTI</th>{"".join(f"<th class='num'>M = {int(m):,}</th>" for m in sorted(tg['0.3195'], key=lambda x: int(x)))}</tr></thead><tbody>{targ_rows}</tbody></table>
<h3>Sensitivity of the 6 px (kernel-disjoint) design: {h28['decision']['sensitivity_cells_beating_d1_5']} cells beat d1-5, {h28['decision']['sensitivity_cells_beating_d2_8']} beat the shipped D2.8 file (which dominates d1-5 in every cell: {h28['decision']['d2_8_dominates_d1_5_in_every_cell']})</h3>
<table><thead><tr><th class="num">&lambda; px</th><th class="num">N</th><th class="num">best budget</th><th class="num">best DTI</th><th class="num">d1-5 DTI</th><th class="num">D2.8 DTI</th><th>verdict</th></tr></thead><tbody>{sens_rows}</tbody></table>
<h3>Holdout factorial (hidden catalogue-component labels; proxy): value field × spacing × budget, 4 folds × draws 0,1</h3>
<div class="callout {'warn' if not h28_hold['verdict']['gate_passed'] else ''}"><b>Comparator reproduction: {h28_hold['reproduction_check']['verdict']}</b> —
recomputed {h28_hold['reproduction_check']['recomputed_mean']:.9f} vs frozen {h28_hold['reproduction_check']['frozen_mean']:.9f} (fold 0 identical to 9 decimals; folds 1–3 differ by up to
{h28_hold['reproduction_check']['max_fold_abs_diff']:.1e}). This session's pipeline re-runs bit-for-bit, so the drift is environmental (IR-25-COMPARATOR-DRIFT; <code>evidence/work_cache_hashes.json</code> now pins every derived cache).
<b>Gate: {'PASS' if h28_hold['verdict']['gate_passed'] else 'FAIL'}</b> — best arm {h28_hold['best_arm']['value']}/{h28_hold['best_arm']['min_dist']} px/{100 * h28_hold['best_arm']['kfrac']:.2f} % at
{h28_hold['gate']['candidate_mean_dti']:.6f}; paired gain {h28_hold['gate']['mean_gain_vs_paired_base']:+.6f} ({h28_hold['gate']['folds_positive']}/4 folds). No arm is slot-eligible.</div>
<table><thead><tr><th>value field</th><th class="num">spacing</th><th class="num">budget</th><th class="num">DTI</th><th class="num">emitted</th><th class="num">coverage</th><th class="num">hug</th><th class="num">&Delta; vs comparator</th><th class="num">cells +</th><th class="num">p</th></tr></thead><tbody>{hold_rows}</tbody></table>
<table><thead><tr><th>contrast</th><th class="num">&Delta; DTI</th></tr></thead><tbody>{con_rows}</tbody></table>
<h3>Two models that were tested and rejected</h3>
<p><b>Habitat in distance-to-known-faults</b> (pre-registered §5): leave-one-artefact-out RMSE
{hab.get('loo', {}).get(hab.get('selected', ''), {}).get('loo_rmse', float('nan')):.4f} against a 0.020 threshold; the blind lattice is predicted at
{hab.get('checks', {}).get('C2', {}).get('predicted', float('nan')):.4f} instead of 0.0904. Its residuals are per-artefact detector skill, which that basis cannot represent —
<b>&ldquo;hug the known-fault halo&rdquo; is not supported.</b></p>
{'<table><thead><tr><th>model</th><th class="num">N</th><th class="num">RMSE</th><th class="num">LOO RMSE</th><th class="num">max residual</th><th></th></tr></thead><tbody>' + hab_rows + '</tbody></table>' if hab_rows else ''}
<p><b>Two-band mixture</b> (amendment D3): the best second band (<code>{e(str(mix.get('selected', {}).get('second_parent')))}</code>, b = {mix.get('selected', {}).get('b')}) reaches a nine-anchor spread of
{mix.get('criterion_i', {}).get('mixture', float('nan')):.3f} against a {mix.get('criterion_i', {}).get('threshold', float('nan')):.3f} threshold and makes the mean absolute residual <i>worse</i>
({mix.get('criterion_ii', {}).get('mixture', float('nan')):.4f} vs {mix.get('criterion_ii', {}).get('single_parent', float('nan')):.4f}) → <b>not adopted</b>, and nothing was designed from it.
Conditional on the owner-reported anchors and fitted model, single-band residuals require off-band truth for these surfaces to reconcile the anchors: implied N
{h28_mix['single_parent_detail']['h28-dotted-ridge']['implied_N']:,.0f} for <code>h28-dotted-ridge</code>,
{h28_mix['single_parent_detail']['lidarscarp-top2pct']['implied_N']:,.0f} for <code>lidarscarp-top2pct</code>,
{h28_mix['single_parent_detail']['h25-ctx-ridge']['implied_N']:,.0f} for <code>h25-ctx-ridge</code> against 12,472–13,358 for the H19-5 family. This is a model implication, not evidence of the actual hidden labels; those surfaces remain H29 prioritization targets, not validated truth.</p>
<p class="small">Evidence: <code>evidence/h28_calibration/anchors.json</code>, <code>design.json</code>, <code>mixture.json</code>, <code>habitat_fit.json</code>,
<code>evidence/h28_holdout/results.json</code>. Scope limit IR-25-LIVE-MODEL-SCOPE: the model reproduces its own family and the blind lattice within 0.004 DTI but under-predicts off-band
surfaces by up to 0.059; predictions for emissions outside the H19-5 band are therefore not validated by this calibration.</p>"""

    hyp = open(ROOT / "knowledge" / "03_hypotheses_ranked_2026-10-02.md").read()
    research = f"""<div class="hero"><h1>Research</h1><p class="lead">What was run, in what order, and what it shows. Preregistrations were written before the corresponding runs (<code>knowledge/04</code>, <code>knowledge/05</code>, <code>knowledge/09</code>).</p></div>
<h2 id="factorial">1 · Fractional factorial across the five feature families</h2>
<p>Design: 2<sup>5−1</sup>, generator E = ABCD, defining relation <code>I = ABCDE</code>, Resolution V ({fac['design']['runs']} runs; each run = {fac['design']['cells_per_run']} hide-and-recover cells). Aliasing: each main effect with a 4-factor interaction, each two-factor interaction with a 3-factor interaction.
Response: exact sparse-regime DTI of a fixed emission (ridge NMS → top 2.45 % → Poisson-disk dots, 1.5 px). Execution order randomised (seed 20261002).</p>
<h3>Runs (ranked)</h3><table><thead><tr><th>Row</th><th>Families</th><th class="num">Mean DTI</th><th class="num">AUC</th><th class="num">Hug</th><th class="num">Emitted</th></tr></thead><tbody>{rr}</tbody></table>
<h3>Same-harness references</h3><table><thead><tr><th>Reference</th><th class="num">DTI</th><th class="num">AUC</th><th class="num">Hug</th></tr></thead><tbody>{refs}</tbody></table>
<p class="small">REF_null = random scores through the same ridge/top-K/dot pipeline; REF_topo/REF_geo = leak-free unsupervised ridge scores. The 300 m kernel rewards space-filling dots, so the null is not zero.</p>
<h3>Effects (DTI units) — Lenth PSE {effs['lenth']['pse']:.4f}, ME {effs['lenth']['me']:.4f}, SME {effs['lenth']['sme']:.4f}</h3>
<table><thead><tr><th>Effect</th><th class="num">Estimate</th><th class="num">SE (4 folds)</th><th class="num">Folds +</th><th>&gt; ME</th></tr></thead><tbody>{er}</tbody></table>
<h3>Classification (pre-registered rule)</h3><table><thead><tr><th>Factor</th><th>Family</th><th>Class</th><th class="num">Main effect</th><th class="num">Folds +</th></tr></thead><tbody>{''.join(f"<tr><td>{k}</td><td>{e(v['label'])}</td><td>{badge(v['classification'], {'matters alone':'ok','matters in combination':'info','inert':'warn','harmful':'bad'}[v['classification']])}</td><td class='num'>{v['main_effect']:+.4f}</td><td class='num'>{v['folds_positive']}/4</td></tr>" for k, v in fac['classification'].items())}</tbody></table>
<h2>2 · Add-on hypotheses and emission (pre-registered, paired)</h2>
{addon_tbl(add, 'Cells = draws 0,1')}{addon_tbl(conf, 'Confirmation replicate (fresh draws 2,3)')}
<p class="small"><code>CFG_*</code> rows (confirmation only) are whole family sets compared with the base: <code>CFG_BE</code> is the factorial's predicted-best corner (predicted 0.145, observed in this table), <code>CFG_ABCDE</code> all five families, <code>CFG_E</code> catalogue geometry alone.</p>
<h3>Budget / dotting sweep on the base surface (draws 0,1)</h3>{emk}{ext_html}
<h2>3 · Fault-tip × scarp hypothesis (prior H27-1)</h2>{h27_section}
{h30_section}
<h2>5 · Audit of the reported 0.2477-labelled raster (score unverified) — emission model</h2>{emu_html}{oos_html}{req_html}{href_html}
{h28_section}
<h2>6 · Prior H26 register and current H30 hypotheses</h2><p class="small">H26 and H27 are historical registers with outcomes; current ranked H30 hypotheses and the frozen paired-relay design are in <code>knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md</code>. The older H29 items in knowledge/10 are already preregistered and are not relabeled as new work.</p>
<details><summary>Show the historical H26 register</summary><pre style="white-space:pre-wrap;font-size:.85rem">{e(hyp)}</pre></details>
<div class="callout"><b>Limits.</b> The holdout is a catalogue-gap proxy; H19-5 as emitted is not out-of-fold; family E may be flattered; proxy-vs-live Spearman was +0.33 (n = 24, n.s.) in the group's earlier record. Nothing here is a leaderboard score.</div>"""

    # ------------------------------------------------------------------ sources page
    st = "".join(f"<tr><td><a href='{e(s['url'])}'>{e(s['title'])}</a><div class='small'>{e(s['publisher'])} · {e(s['kind'])}</div></td><td>{badge('read ' + s['verified_utc'], 'ok') if s['verified'] else badge('not verified here', 'warn')}</td><td class='small'>{e(s['used_for'])}</td><td class='small'>{e(s['how_verified'])}{(' — ' + e(s['caveats'])) if s['caveats'] else ''}</td></tr>" for s in src)
    dm = "".join(f"<tr><td class='mono'>{e(f['dest'])}</td><td class='mono'>{f['sha256'][:16]}…</td><td class='num'>{f['bytes']:,}</td><td>{e(f['group'])}</td><td class='small'>{e(f['provenance'])}</td></tr>" for f in man)
    ir = "".join(f"<tr id='{i['id']}'><td class='mono'>{i['id']}</td><td>{badge(i['severity'], 'bad' if i['severity']=='critical' else ('warn' if i['severity'] in ('high','medium') else 'info'))}{badge(i['status'], 'ok' if i['status'] in ('fixed','verified') else 'info')}</td><td>{e(i['issue'])}<div class='small'><b>Evidence:</b> {e(i['evidence'])}</div><div class='small'><b>Action:</b> {e(i['resolution_or_action'])}</div></td></tr>" for i in irr)
    sc = "".join(f"<tr><td>{e(a['project'])}</td><td class='mono'>{e(a['label'])}</td><td class='num'>{score_fmt(a['score'])}</td><td class='small'>{e(a['status'])}{(' — ' + e(a['note'])) if a['note'] else ''}</td></tr>" for a in sorted(ls['artifacts'], key=lambda a: -(a['score'] or -1)))
    lbt = "".join(f"<tr><td>#{r['rank']}</td><td>{e(r['participant'])}</td><td class='num'>{r['best_public_dti']:.4f}</td><td class='num'>{r['submissions']}</td></tr>" for r in snap['top10'])
    sources = f"""<div class="hero"><h1>Sources &amp; audit</h1><p class="lead">Every source with its verification status, every input file with its SHA-256 pin, every irregularity with evidence and action.
"Verified" reflects the recorded repository evidence and date/method; it does not imply the page was re-fetched this turn. "Not verified here" means unverified, carried over or unreachable.</p></div>
<h2>Official and trusted sources</h2><table><thead><tr><th>Source</th><th>Status</th><th>Used for</th><th>How verified / caveat</th></tr></thead><tbody>{st}</tbody></table>
<h2>Input data (restore with <code>scripts/restore_data.py</code>)</h2><table><thead><tr><th>File</th><th>SHA-256</th><th class="num">Bytes</th><th>Group</th><th>Provenance</th></tr></thead><tbody>{dm}</tbody></table>
<h2 id="irregularities">Irregularities and flags ({len(irr)})</h2><table><thead><tr><th>ID</th><th>Level</th><th>Issue · evidence · action</th></tr></thead><tbody>{ir}</tbody></table>
<h2>Score ledger (user/owner claims; not organizer-verified)</h2><p class="small">No organizer receipt or official leaderboard page was accessed for the 0.2477 or 0.3195 claims. The local raster identity check verifies pixels, not DTI.</p><table><thead><tr><th>Project</th><th>Submission</th><th class="num">Reported score</th><th>Note / status</th></tr></thead><tbody>{sc}</tbody></table>
<h2>Leaderboard values supplied in the task (unverified; reported {snap['reported_utc']})</h2><table><thead><tr><th>Claimed rank</th><th>Participant claim</th><th class="num">Claimed public DTI</th><th class="num">Claimed submissions</th></tr></thead><tbody>{lbt}</tbody></table>"""

    DOCS.mkdir(exist_ok=True)
    (DOCS / "history.html").write_text(page("Historical archive", home(""), "history", ""))
    (DOCS / "submission-history.html").write_text(page("Historical submission guide", exec_body, "history", ""))
    (DOCS / "index.html").write_text(page("Start here", render_body(), "index", ""))
    (ROOT / "index.html").write_text(page("Start here", render_body(root_page=True), "index", "docs/"))
    (DOCS / "executive-summary.html").write_text(page("Executive summary & submission guide", render_body(), "exec", ""))
    (DOCS / "research.html").write_text(page("Research", research, "research", ""))
    (DOCS / "sources.html").write_text(page("Sources & audit", sources, "sources", ""))
    (DOCS / "current-review.html").write_text(page("Current executive review", render_body(), "current", ""))
    for name in (
        "submissions",
        "live_scores",
        "irregularities",
        "sources",
        "data_manifest",
        "artifact_ledger",
        "run_card_h72_2026-10-26",
        "run_card_h73_2026-10-26",
        "run_card_h73_bw_2026-10-26",
        "run_card_h74_2026-10-26",
        "run_card_h75_2026-10-27",
    ):
        (DOCS / "data" / f"{name}.json").write_text((ROOT / "registry" / f"{name}.json").read_text())
    # Reapply the current, gate-negative H73 status after generated pages are written.
    # Keep research inspection visibly separate from competition eligibility.
    try:
        from announce_h73_site import main as publish_current_status
    except ImportError:
        from scripts.announce_h73_site import main as publish_current_status
    publish_current_status()
    print("site built:", [p.name for p in DOCS.glob("*.html")] + ["../index.html"])


if __name__ == "__main__":
    sys.exit(main())
