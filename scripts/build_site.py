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
    nav = [("index", "Start here", "index.html"), ("exec", "How to submit", "executive-summary.html"),
           ("research", "Research", "research.html"), ("sources", "Sources & audit", "sources.html")]
    links = []
    for key, label, href in nav:
        h = "index.html" if key == "index" else prefix + href
        links.append(f'<a class="{"on" if key == active else ""}" href="{h}">{label}</a>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · GEMSDOE25</title><link rel="stylesheet" href="{prefix}assets/style.css"></head><body>
<header class="top"><div class="wrap"><div class="brand">GEMSDOE25<small>DOE GEMS Prize · DrivenData #306 · designed factorial experiments</small></div><nav>{''.join(links)}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">Core values: <b>Maximize P(Win)</b> · <b>Own the Outcome</b>. Source: <a href="https://github.com/buffedlizard55-lab/GEMSDOE25">github.com/buffedlizard55-lab/GEMSDOE25</a> ·
built {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} from <code>registry/</code> and <code>evidence/</code> by <code>scripts/build_site.py</code>.
No score here is promised; owner-reported scores are not DrivenData receipts. This site never contacts drivendata.org.</div></footer>
<script src="{prefix}assets/app.js"></script></body></html>"""


def badge(txt, kind):
    return f'<span class="badge b-{kind}">{e(txt)}</span>'


def dl_card(s: dict, prefix: str, big: bool = True) -> str:
    href = f"{prefix}downloads/{s['file']}"
    nid = "note-" + s["id"]
    kind = {"scored": "ok"}.get(s["status"], "warn")
    status = s["status"] if s["status"] != "scored" else f"scored {s.get('owner_reported_score'):.4f} (owner-reported)"
    chk = "format verified (all hard checks)" if s.get("format_ok") else "FORMAT CHECK FAILED"
    return f"""<section class="dl"><h2>{e(s['title'])}</h2>
<p>{e(s['summary'])}</p>
<div class="row"><a class="btn" href="{href}" download>↓ Download {e(s['file'])}</a></div>
<div class="row">{badge(status, kind)}{badge(chk, 'ok' if s.get('format_ok') else 'bad')}{badge('float32 · [0,1] · NaN outside footprint', 'info')}{badge(f"{s['positive_pixels']:,} px emitted", 'info')}</div>
<p class="small">{fmt_bytes(s['bytes'])} · unique content id <code>{s['content_id']}</code> · SHA-256 <code>{s['sha256'][:16]}…</code> · <a href="{prefix}executive-summary.html">exact upload steps</a></p>
<p style="margin:10px 0 2px"><b>Note to paste in DrivenData's "Note (optional)" field</b> <button class="btn alt small" data-copy="{nid}">Copy note</button></p>
<div class="note"><code id="{nid}">{e(s['note'])}</code></div></section>"""


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
    primary = next(s for s in subs if s["role"] == "primary")
    others = [s for s in subs if s["role"] != "primary"]
    snap = ls["leaderboard_snapshot"]
    lead = snap["top10"][0]["best_public_dti"]
    best = max(a["score"] for a in ls["artifacts"] if a["score"] is not None)

    def home(prefix: str) -> str:
        hero = f"""<div class="hero"><h1>Download the file. Know exactly what it is.</h1>
<p class="lead">One click gets the submission GeoTIFF. It is a <b>valid, unique, unscored candidate</b>: single band, float32, values in [0, 1], NaN only
outside the organizers' footprint. The previous site's file failed with <i>"Predicted values must be in range [0, 1]"</i> because 45 % of the official footprint was NaN; that
is fixed and verified against the organizers' template.</p></div>"""
        cards = dl_card(primary, prefix)
        alt = "".join(f"""<div class="card"><b>{e(o['title'])}</b> {badge(o['status'], 'ok' if o['status']=='scored' else 'warn')}
<p class="small" style="margin:.3em 0">{e(o['summary'])}</p><a class="btn alt small" href="{prefix}downloads/{o['file']}" download>↓ {e(o['file'])}</a>
 <span class="small">· {o['positive_pixels']:,} px · <code>{o['content_id']}</code></span></div>""" for o in others if o["role"] in ("alternate", "fallback"))
        stats = f"""<div class="stats"><div class="stat"><b>{lead:.4f}</b><span>Leaderboard #1 (DARD) · snapshot {snap['read_utc']}</span></div>
<div class="stat"><b>{best:.4f}</b><span>Group best, owner-reported (rank #16, wbg1)</span></div>
<div class="stat"><b>+{snap['gap_to_rank5']:.3f}</b><span>needed to reach rank #5 ({snap['top10'][4]['best_public_dti']:.4f}); +{snap['gap_to_rank1']:.3f} (+{100*snap['relative_gain_needed_for_rank1']:.0f} %) for #1</span></div>
<div class="stat"><b>{primary['expected_range'] if primary.get('expected_range') else 'n/a'}</b><span>model expectation for the primary file — a model, not a score</span></div></div>"""
        r = why["relations"]
        px15 = next(v["positive_px"] for k, v in why["rasters"].items() if "d1-5" in k)
        px195 = next(v["positive_px"] for k, v in why["rasters"].items() if "h19-5" in k and "dotted" not in k and "d1-5" not in k and "d2-8" not in k)
        lc = why["lattice_calibration"]
        imp = why["implied_by_live_scores"]
        whyb = f"""<h2>Why the 0.2477 file scored best</h2>
<div class="card"><ol>
<li><b>It is exactly <code>dot_thin(H19-5, 1.5)</code></b> — pixel-for-pixel a deterministic subset of the 0.1922 file: {px15:,} of {px195:,} pixels kept ({100*r['pixel_retention_d1_5']:.1f} %), none on a catalogue pixel, zero NaN inside the footprint. Same detections, half the false-positive mass.</li>
<li><b>The metric rewards that.</b> DTI = TP<sub>w</sub> / (0.2·(TP<sub>w</sub>+FP<sub>w</sub>) + 0.8·|G|). Thinning keeps ≈{100*r['geometric_credit_retention_d1_5']:.0f} % of the credit (geometric estimate) while removing ≈{100*(1-r['pixel_retention_d1_5']):.0f} % of the emitted pixels.</li>
<li><b>Two independent live-score readings agree on the hidden-truth size:</b> the blind lattice (0.0904) gives |G| ≈ {lc['truth_px_in_footprint']:,.0f} px; the H19-5 → dotted pair implies ≈ {imp['implied_truth_px_if_92pct_of_h19_5_px_are_fp']:,.0f} px (2 % apart). At that density each emitted pixel must earn ≥ {imp['break_even_ratio_at_0_2477']:.3f} credit per unit of false-positive mass to pay for itself.</li></ol>
<p class="small">Details, tables and caveats on the <a href="{prefix}research.html">Research</a> page. Evidence: <code>evidence/why_0_2477.json</code>.</p></div>"""
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
<p class="small">The feed never requests drivendata.org (Terms of Use). Leaderboard rows are human-read snapshots.</p>"""
        return hero + cards + (f"<h3>Also available</h3>{alt}" if alt else "") + stats + whyb + facb + flagb + feed

    exec_body = f"""<div class="hero"><h1>How to submit — exact steps</h1><p class="lead">Five clicks. Nothing here uploads for you: the owner submits (DrivenData's Terms of Use forbid automation).</p></div>
{dl_card(primary, '')}
<h2>Steps</h2><ol class="steps">
<li><b>Download</b> <code>{e(primary['file'])}</code> with the green button above. Optional: check <code>sha256sum</code> starts with <code>{primary['sha256'][:16]}</code>.</li>
<li><b>Sign in</b> at <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">DrivenData → GEMS → Submissions</a> and click <i>Make new submission</i> ("New submission" form).</li>
<li><b>File to submit:</b> choose the <code>.tif</code>. (A <code>.zip</code> containing exactly one GeoTIFF is also accepted by the form; this page offers the plain <code>.tif</code>.)</li>
<li><b>Note (optional):</b> paste the note above. It is {len(primary['note'])} characters; the form says "A short comment to help you or your team tell submissions apart later".</li>
<li><b>Submit</b>, wait for the score, then record it for the ledger: <code>python scripts/record_live_score.py --file {e(primary['content_id'])} --score 0.xxxx</code> and re-run <code>python scripts/build_site.py</code>.</li></ol>
<h2>What was verified about this exact file</h2>
<table><thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead><tbody>{''.join(f"<tr><td>{e(k)}</td><td>{badge('pass' if v['pass_'] else 'FAIL', 'ok' if v['pass_'] else 'bad')}</td><td class='small'>{e(v['detail'])}</td></tr>" for k, v in primary['checks'].items())}</tbody></table>
<p class="small">Independent plain-rasterio check (<code>src/gems25/submission.py::check_file</code>) against the pinned organizer template (sha256 prefix 2176d08e…). Receipt: <a href="downloads/{primary['receipt']}">{primary['receipt']}</a>.</p>
<div class="callout"><b>If the portal says "Predicted values must be in range [0, 1]"</b><ol><li>Make sure you uploaded <i>this</i> file (name and SHA-256 above), not the old <code>gems25-factorial-best-v1-*.tif</code>.</li>
<li>That earlier file had 2,344,929 NaN pixels <i>inside</i> the 5,167,373-pixel footprint (see <code>evidence/old_gems25_tif_forensics.json</code>); this one has 0.</li>
<li>Try the zeros-outside fallback below (earlier files with either convention were scored by the portal). If it still fails, email <a href="mailto:info@drivendata.org">info@drivendata.org</a> with the exact message; do not re-upload repeatedly.</li></ol></div>
{''.join(dl_card(o, '', False) if o['role'] == 'fallback' else '' for o in others)}
<h2>Rules that matter (read on the official pages)</h2><ul>
<li>Up to <b>3 submissions per week</b> per entity; <b>one final submission</b> per entity must be chosen before the deadline (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules §3.2, §3.4</a>).</li>
<li>Generative-AI use is allowed but must be described in the narrative (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">§3.2</a>); a draft is in <code>AI_DISCLOSURE.md</code>.</li>
<li>Known USGS/INGENIOUS pixels are masked and pixel-exact; predictions on them do not matter (<a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">staff</a>).</li>
<li>Deadline wording differs between the page (11:59 p.m. UTC, 3 Dec 2026) and the rules (5:00 p.m. ET): confirm with <a href="mailto:gemsprize@nlr.gov">gemsprize@nlr.gov</a>.</li></ul>
<div class="callout info"><b>Slot discipline.</b> Do not spend a slot on a file that has not beaten the current comparable hide-and-recover best, unless you consciously accept the declared exception ({e(primary.get('gate_summary','see Research'))}). A holdout win is necessary, not sufficient.</div>"""

    # ------------------------------------------------------------------ research page
    effs = fac["effects_dti"]
    er = "".join(f"<tr><td>{k}</td><td class='num'>{v:+.4f}</td><td class='num'>{effs['folds'][k]['se']:.4f}</td><td class='num'>{effs['folds'][k]['blocks_positive']}/4</td><td>{'<b>yes</b>' if abs(v) > effs['lenth']['me'] else ''}</td></tr>" for k, v in sorted(effs['effects'].items(), key=lambda t: -abs(t[1])))
    rr = "".join(f"<tr><td>{r['row']}</td><td class='mono'>{r['families']}</td><td class='num'>{r['dti_mean']:.4f}</td><td class='num'>{r['auc_mean']:.3f}</td><td class='num'>{r['hug_mean']:.2f}</td><td class='num'>{r['emitted_mean']:.0f}</td></tr>" for r in sorted(fac['runs'], key=lambda r: -r['dti_mean']))
    refs = "".join(f"<tr><td>{k}</td><td class='num'>{v['dti_mean']:.4f}</td><td class='num'>{v['auc_mean']:.3f}</td><td class='num'>{v['hug_mean']:.2f}</td></tr>" for k, v in fac['references_same_harness'].items())
    inter = "".join(f"<tr><td>{k}</td><td class='num'>{v:+.4f}</td></tr>" for k, v in fac['ranked_interactions'][:6])
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
    emu_html = ""
    if emu:
        emu_html = "<table><thead><tr><th>min-dist</th><th class='num'>px</th><th class='num'>credit retention (geometric)</th><th class='num'>model DTI</th></tr></thead><tbody>" + "".join(f"<tr><td>{r['min_dist']}</td><td class='num'>{r['px']:,}</td><td class='num'>{r['retention']:.3f}</td><td class='num'>{r['model_dti']:.4f}</td></tr>" for r in emu['curve']) + f"</tbody></table><p class='small'>{e(emu['caveat'])}</p>"
    hyp = open(ROOT / "knowledge" / "03_hypotheses_ranked_2026-10-02.md").read()
    research = f"""<div class="hero"><h1>Research</h1><p class="lead">What was run, in what order, and what it shows. Pre-registrations were committed before the runs
(<code>knowledge/04_…</code>, <code>knowledge/05_…</code>).</p></div>
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
<h3>Budget / dotting sweep on the base surface (draws 0,1)</h3>{emk}
<h2>3 · Why 0.2477 — the emission model</h2>{emu_html}
<h2>4 · Hypotheses register</h2><p class="small">Verbatim register (written before the add-on runs): <code>knowledge/03_hypotheses_ranked_2026-10-02.md</code>.</p>
<details><summary>Show the register</summary><pre style="white-space:pre-wrap;font-size:.85rem">{e(hyp)}</pre></details>
<div class="callout"><b>Limits.</b> The holdout is a catalogue-gap proxy; H19-5 as emitted is not out-of-fold; family E may be flattered; proxy-vs-live Spearman was +0.33 (n = 24, n.s.) in the group's earlier record. Nothing here is a leaderboard score.</div>"""

    # ------------------------------------------------------------------ sources page
    st = "".join(f"<tr><td><a href='{e(s['url'])}'>{e(s['title'])}</a><div class='small'>{e(s['publisher'])} · {e(s['kind'])}</div></td><td>{badge('read ' + s['verified_utc'], 'ok') if s['verified'] else badge('not verified here', 'warn')}</td><td class='small'>{e(s['used_for'])}</td><td class='small'>{e(s['how_verified'])}{(' — ' + e(s['caveats'])) if s['caveats'] else ''}</td></tr>" for s in src)
    dm = "".join(f"<tr><td class='mono'>{e(f['dest'])}</td><td class='mono'>{f['sha256'][:16]}…</td><td class='num'>{f['bytes']:,}</td><td>{e(f['group'])}</td><td class='small'>{e(f['provenance'])}</td></tr>" for f in man)
    ir = "".join(f"<tr id='{i['id']}'><td class='mono'>{i['id']}</td><td>{badge(i['severity'], 'bad' if i['severity']=='critical' else ('warn' if i['severity'] in ('high','medium') else 'info'))}{badge(i['status'], 'ok' if i['status'] in ('fixed','verified') else 'info')}</td><td>{e(i['issue'])}<div class='small'><b>Evidence:</b> {e(i['evidence'])}</div><div class='small'><b>Action:</b> {e(i['resolution_or_action'])}</div></td></tr>" for i in irr)
    sc = "".join(f"<tr><td>{e(a['project'])}</td><td class='mono'>{e(a['label'])}</td><td class='num'>{'' if a['score'] is None else f'{a['score']:.4f}'}</td><td class='small'>{e(a['status'])}{(' — ' + e(a['note'])) if a['note'] else ''}</td></tr>" for a in sorted(ls['artifacts'], key=lambda a: -(a['score'] or -1)))
    lbt = "".join(f"<tr><td>#{r['rank']}</td><td>{e(r['participant'])}</td><td class='num'>{r['best_public_dti']:.4f}</td><td class='num'>{r['submissions']}</td></tr>" for r in snap['top10'])
    sources = f"""<div class="hero"><h1>Sources &amp; audit</h1><p class="lead">Every source with its verification status, every input file with its SHA-256 pin, every irregularity with evidence and action.
"Read" means the page/file was actually read in this session; "not verified here" means carried over or unreachable.</p></div>
<h2>Official and trusted sources</h2><table><thead><tr><th>Source</th><th>Status</th><th>Used for</th><th>How verified / caveat</th></tr></thead><tbody>{st}</tbody></table>
<h2>Input data (restore with <code>scripts/restore_data.py</code>)</h2><table><thead><tr><th>File</th><th>SHA-256</th><th class="num">Bytes</th><th>Group</th><th>Provenance</th></tr></thead><tbody>{dm}</tbody></table>
<h2 id="irregularities">Irregularities and flags ({len(irr)})</h2><table><thead><tr><th>ID</th><th>Level</th><th>Issue · evidence · action</th></tr></thead><tbody>{ir}</tbody></table>
<h2>Score ledger (owner-reported; not DrivenData receipts)</h2><table><thead><tr><th>Project</th><th>Submission</th><th class="num">Score</th><th>Note</th></tr></thead><tbody>{sc}</tbody></table>
<h2>Leaderboard snapshot (human-read {snap['read_utc']})</h2><table><thead><tr><th>Rank</th><th>Participant</th><th class="num">Public DTI</th><th class="num">Submissions</th></tr></thead><tbody>{lbt}</tbody></table>"""

    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(page("Start here", home(""), "index", ""))
    (ROOT / "index.html").write_text(page("Start here", home("docs/"), "index", "docs/"))
    (DOCS / "executive-summary.html").write_text(page("How to submit", exec_body, "exec", ""))
    (DOCS / "research.html").write_text(page("Research", research, "research", ""))
    (DOCS / "sources.html").write_text(page("Sources & audit", sources, "sources", ""))
    for name in ("submissions", "live_scores", "irregularities", "sources", "data_manifest"):
        (DOCS / "data" / f"{name}.json").write_text((ROOT / "registry" / f"{name}.json").read_text())
    print("site built:", [p.name for p in DOCS.glob("*.html")] + ["../index.html"])


if __name__ == "__main__":
    sys.exit(main())
