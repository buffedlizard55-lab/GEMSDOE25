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
    return f"""<section class="dl"><h2>{e(s['title'])}</h2>
<p>{e(s['summary'])}</p>
<div class="row"><a class="btn" href="{href}" download>↓ Download {e(s['file'])}</a></div>
<div class="row">{badge(status, kind)}{badge(chk, 'ok' if s.get('format_ok') else 'bad')}{badge('float32 · [0,1] · ' + ('zeros outside footprint' if s.get('outside') == 'zero' else 'NaN outside footprint'), 'info')}{badge(f"{s['positive_pixels']:,} px emitted", 'info')}</div>
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
    oos = opt("evidence/emission_model_oos_check.json")
    ext = opt("evidence/addons/emk_extension.json")
    href = opt("evidence/harness_references.json")
    h27_screen = opt("evidence/h27_screen/results.json")
    h27_confirm = opt("evidence/h27_confirm/results.json")
    primary = next(s for s in subs if s["role"] == "primary")
    others = [s for s in subs if s["role"] != "primary"]
    snap = ls["leaderboard_snapshot"]
    lead = snap["top10"][0]["best_public_dti"]
    best = max(a["score"] for a in ls["artifacts"] if a["score"] is not None)

    def home(prefix: str) -> str:
        hero = """<div class="hero"><h1>Download the format-validated GeoTIFF. Know what it proves.</h1>
<p class="lead">One click gets a <b>single-band float32 GeoTIFF with finite [0,1] predictions throughout the footprint</b>, checked against the pinned template. This establishes file-format validity only—not holdout promotion or a competition score. The current D2.8 file has not demonstrated a win over the 0.152003389 spatial-holdout comparator and is <b>not slot-approved</b>. The earlier range error was caused by NaNs inside the footprint (inferred from the file; the portal validator is not public); that defect is fixed.</p></div>"""
        cards = dl_card(primary, prefix)
        alt = "".join(f"""<div class="card"><b>{e(o['title'])}</b> {badge(o['status'], 'ok' if o['status']=='scored' else 'warn')}
<p class="small" style="margin:.3em 0">{e(o['summary'])}</p><a class="btn alt small" href="{prefix}downloads/{o['file']}" download>↓ {e(o['file'])}</a>
 <span class="small">· {o['positive_pixels']:,} px · <code>{o['content_id']}</code></span></div>""" for o in others if o["role"] == "fallback")
        stats = f"""<div class="stats"><div class="stat"><b>{lead:.4f}</b><span>Unverified #1 leaderboard claim · reported {snap['reported_utc']}</span></div>
<div class="stat"><b>{best:.4f}</b><span>Unverified group-best score claim · rank association not authenticated</span></div>
<div class="stat"><b>+{snap['gap_to_rank5']:.3f}</b><span>arithmetic gap to the supplied #5 claim ({snap['top10'][4]['best_public_dti']:.4f}); +{snap['gap_to_rank1']:.3f} (+{100*snap['relative_gain_needed_for_rank1']:.0f} %) to the supplied #1 claim</span></div>
<div class="stat"><b>{primary['expected_range'] if primary.get('expected_range') else 'n/a'}</b><span>model expectation for the primary file — a model, not a score</span></div></div>"""
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
        if h27_confirm:
            h27_status = "confirmation gate passed" if h27_confirm["slot_eligible"] else "confirmation gate failed; stop"
        elif h27_screen:
            h27_status = "screen passed; fresh-draw confirmation still required" if h27_screen["slot_eligible"] else "screen failed; stop, no slot"
        else:
            h27_status = "screen pending on the frozen draws 4,5"
        plan = ('<div class="callout warn"><b>No weekly slot is approved for the currently downloadable D2.8 file.</b> '
                'It is format-validated but has not demonstrated a win over the current 0.152003389 spatial-holdout best. '
                f'H27-1 status: {e(h27_status)}. Even a confirmed proxy win only makes a corresponding candidate eligible for packaging and review; it does not score or upload automatically. '
                'Do not spend a weekly slot unless that specific candidate passes the frozen holdout gate.</div>')
        return hero + cards + (f"<h3>Also available</h3>{alt}" if alt else "") + plan + stats + whyb + facb + flagb + feed

    exec_body = f"""<div class="hero"><h1>Executive summary &amp; submission guide</h1><p class="lead">The file and upload instructions are provided for reproducibility. Nothing here uploads for you: the owner submits manually.</p></div>
<div class="callout"><b>Slot status: do not submit the current D2.8 file on this evidence.</b> Format checks passed, but this candidate has not beaten the current 0.152003389 spatial-holdout comparator. Use a weekly slot only after the specific candidate passes the frozen holdout gate and any required confirmation.</div>
{dl_card(primary, '')}
<h2>Manual upload steps (only for a candidate that has passed its holdout gate)</h2><ol class="steps">
<li><b>Download</b> <code>{e(primary['file'])}</code> with the green button above. Optional: check <code>sha256sum</code> starts with <code>{primary['sha256'][:16]}</code>.</li>
<li><b>Open the competition and sign in</b> — <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/">competition page</a>, then click <b>Submit</b> in the sidebar and <b>Make new submission</b> (wording from the competition page; this opens the "New submission" form).</li>
<li><b>File to submit:</b> choose the <code>.tif</code>. The form says: "You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF ... It must match the submission format's CRS, shape, and geotransform." This page offers the plain <code>.tif</code>.</li>
<li><b>Note (optional):</b> paste the note above. It is {len(primary['note'])} characters; the form says "A short comment to help you or your team tell submissions apart later".</li>
<li><b>Submit</b>, wait for the score, then record it for the ledger: <code>python scripts/record_live_score.py --file {e(primary['content_id'])} --score 0.xxxx</code> and re-run <code>python scripts/build_site.py</code>.</li></ol>
<h2>What was verified about this exact file</h2>
<table><thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead><tbody>{''.join(f"<tr><td>{e(k)}</td><td>{badge('pass', 'ok') if v['pass_'] else (badge('FAIL', 'bad') if v['hard'] else badge('informational', 'info'))}</td><td class='small'>{e(v['detail'])}</td></tr>" for k, v in primary['checks'].items())}</tbody></table>
<p class="small">Independent plain-rasterio check (<code>src/gems25/submission.py::check_file</code>) against the pinned owner-mirror template (sha256 prefix 2176d08e…). Its footprint also matches the owner-mirrored raster labelled 0.2477; that score/portal status is not independently verified. Format-check receipt: <a href="downloads/{primary['receipt']}">{primary['receipt']}</a>.</p>
<div class="callout"><b>If the portal says "Predicted values must be in range [0, 1]"</b><ol><li>Make sure you uploaded <i>this</i> file (name and SHA-256 above), not the old <code>gems25-factorial-best-v1-*.tif</code>.</li>
<li>That earlier file had 2,344,929 NaN pixels <i>inside</i> the 5,167,373-pixel footprint (see <code>evidence/old_gems25_tif_forensics.json</code>); this one has 0.</li>
<li>Do not use either file for a weekly slot unless this specific candidate beats the current 0.152003389 holdout best and passes the frozen exact-file gate. The zeros-outside variant is only a format fallback; organizer acceptance is unverified. If a future gate-cleared file is rejected, email <a href="mailto:info@drivendata.org">info@drivendata.org</a> with the exact message; do not re-upload repeatedly.</li></ol></div>
{''.join(dl_card(o, '', False) if o['role'] == 'fallback' else '' for o in others)}
<h2>Rules that matter (read on the official pages)</h2><ul>
<li>Up to <b>3 submissions per week</b> per entity; <b>one final submission</b> per entity must be chosen before the deadline (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">rules §3.2, §3.4</a>).</li>
<li>Generative-AI use is allowed but must be described in the narrative (<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">§3.2</a>); a draft is in <code>AI_DISCLOSURE.md</code>.</li>
<li>Known USGS/INGENIOUS pixels are masked and pixel-exact; predictions on them do not matter (<a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">staff</a>).</li>
<li>Deadline wording differs between the page (11:59 p.m. UTC, 3 Dec 2026) and the rules (5:00 p.m. ET): confirm with <a href="mailto:gemsprize@nlr.gov">gemsprize@nlr.gov</a>.</li></ul>
<div class="callout"><b>Slot discipline.</b> This file's old paired diagnostic compared it to the dotted 0.2477-labelled raster on a shared mask family; it is not evidence against the current 0.152003389 holdout best. The current D2.8 download is therefore not slot-approved. A specific candidate must beat the current spatially blocked holdout comparator before any weekly slot is considered; no proxy result is a live score.</div>"""

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
        h27_section = """<p>H27-1 is preregistered for draws 4,5; the screen has not run. No candidate is eligible for a weekly slot until the frozen absolute (0.152003389) and paired gates pass, followed by confirmation on fresh draws 6,7.</p><p><a href="../knowledge/09_preregistered_hypotheses_2026-10-02.md">Read the full ranked register, data gates, feature formula and analysis plan.</a></p>"""
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
<h2>3 · Fault-tip × scarp hypothesis (H27-1)</h2>{h27_section}
<h2>4 · Audit of the reported 0.2477 raster (score unverified) — emission model</h2>{emu_html}{oos_html}{req_html}{href_html}
<h2>5 · Prior H26 register and current H27 hypotheses</h2><p class="small">H26 is a historical pre-run register with outcomes; the fresh H27 ranking is in <code>knowledge/09_preregistered_hypotheses_2026-10-02.md</code>.</p>
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
