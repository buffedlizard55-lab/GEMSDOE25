#!/usr/bin/env python3
"""Evidence-driven current executive subpage; never labels an old TIF as new."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
e = html.escape


def current_banner(prefix: str) -> str:
    return f"""<aside class="current-status" aria-label="Current submission status">
<strong>26 OCT 2026 · OK TO DOWNLOAD: YES (TESTING ONLY) · OK TO SUBMIT: NO — DO NOT SUBMIT</strong>
<span>Primary unique GeoTIFF <code>88bbebfe79b4</code> (H72-3 DEM-free subsurface, 41,061 dots) passes all 15 format checks and density-aware 85-raster lane uniqueness (<code>flagged_lane = []</code>), but failed the frozen H35 holdout gate.</span>
<a href="{prefix}current-review.html">Read the nine-site executive review, 0.2778 PhD proof &amp; H72 results →</a></aside>"""


def render_body(root_page: bool = False) -> str:
    focus = json.loads((ROOT / "evidence/focus_audit_2026-10-26.json").read_text())
    path = ROOT / "evidence/rod_2026-10-26/run_card.json"
    card = json.loads(path.read_text()) if path.exists() else None
    audit = ROOT / "evidence/rod_2026-10-26/analysis.json"
    analysis = json.loads(audit.read_text()) if audit.exists() else None
    status = e(card["reason"]) if card else "Run incomplete. No submission file is authorized."

    h72_path = ROOT / "registry/run_card_h72_2026-10-26.json"
    h72 = json.loads(h72_path.read_text()) if h72_path.exists() else None

    outcome = "<p>No valid HOLDOUT-DTI result is available. This is not a score of zero.</p>"
    if analysis:
        c, b = analysis["arms"]["ROD"], analysis["arms"]["H35"]
        outcome = f"""<div class="review-metrics"><div><span>ROD · HOLDOUT-DTI</span><strong>{c['pooled_dti']:.4f}</strong>
<small>95% CI {c['ci95'][0]:.4f}–{c['ci95'][1]:.4f}</small></div>
<div><span>Same-run H35 · HOLDOUT-DTI</span><strong>{b['pooled_dti']:.4f}</strong>
<small>95% CI {b['ci95'][0]:.4f}–{b['ci95'][1]:.4f}</small></div></div>
<p>{c['withheld_positive_occurrences']:,} withheld-positive occurrences; {analysis['distinct_withheld_pixels']:,} distinct pixels.
Four buffered spatial quadrants, whole components withheld. {e(analysis['ci_method'])}.
Evaluator: <code>gems25.metric.dti_binary</code>, α=0.2, β=0.8, 300 m triangular kernel;
<a href="../evidence/rod_2026-10-26/analysis.json">version hashes and full paired results</a>.
This estimates catalogue-gap recovery, not leaderboard performance.</p>"""

    pol3_path = ROOT / "evidence/pol3_screen_2026-10-26/summary.json"
    pol3 = json.loads(pol3_path.read_text()) if pol3_path.exists() else None
    pol3_section = ""
    if pol3:
        pol3_section = f"""<section class="card"><p class="eyebrow">PRIOR PARALLEL SESSION · ONE SCREEN · PRESERVED AUDIT TRAIL</p>
<h2>POL3 signed half-graben screen — negative</h2>
<p><b>HOLDOUT-DTI</b>, evaluator <code>{e(pol3['evaluator'])}</code>, draws <code>{e(str(pol3['draws']))}</code>,
{pol3['withheld_positives']:,} withheld positives. Candidate pooled <code>{pol3['candidate_pooled']['dti']:.6f}</code> vs same-run H35
<code>{pol3['control_pooled']['dti']:.6f}</code>; paired four-fold mean gain <code>{pol3['paired_fold_mean_gain']:+.6f}</code>,
95% CI <code>[{pol3['paired_fold_ci95'][0]:+.6f}, {pol3['paired_fold_ci95'][1]:+.6f}]</code>,
{pol3['positive_folds']}/4 folds positive. Feature-alone maximum AUC <code>{pol3['max_canary_auc']:.4f}</code>.
The frozen screen gate failed; lane clearance is <b>NOT RUN</b>.
This is a catalogue-gap proxy, not an organizer score or blind-fault performance claim.</p>
<p><a href="../knowledge/27_ranked_hypotheses_and_review_2026-10-26.md">POL3 session review</a> ·
<a href="../knowledge/28_preregistered_pol3_signed_halfgraben_2026-10-26.md">frozen preregistration</a> ·
<a href="../registry/run_card_pol3_screen_2026-10-26.json">POL3 run card</a> ·
<a href="../evidence/pol3_screen_2026-10-26/summary.json">saved-cell result</a>.</p></section>"""

    subs = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
    featured = next(s for s in subs if s["role"] == "primary")
    alt_h72_1 = next((s for s in subs if s["id"] == "h72-1-deapron"), None)

    h72_section = ""
    h72_lane_detail = ""
    if h72:
        e1 = json.loads((ROOT / "evidence/h72_1_screen/analysis.json").read_text())
        e2 = json.loads((ROOT / "evidence/h72_2_screen/analysis.json").read_text())
        e3 = json.loads((ROOT / "evidence/h72_3_screen/analysis.json").read_text())
        lane_lit = json.loads((ROOT / featured["lane"]["receipt"]).read_text())
        h23_ov = next(r["dots_within_3px"] for r in lane_lit["rows"] if r["file"] == "h23-a-6pct.tif")
        rc = h72["correlation_overlap_vs_registry"]
        top21 = rc["focus_21_top_scorers"]
        own = rc["own_lineage"]
        w1 = len(e1["draws"]) * sum(e1["withheld_positives_per_fold"].values())
        w2 = len(e2["draws"]) * sum(e2["withheld_positives_per_fold"].values())
        w3 = len(e3["draws"]) * sum(e3["withheld_positives_per_fold"].values())
        c1_auc = max(e1["leakage_canary"]["max_effective_auc"].values())
        c2_auc = max(e2["leakage_canary"]["max_effective_auc"].values())
        c3_auc = max(e3["leakage_canary"]["max_effective_auc"].values())
        h72_lane_detail = (
            f"Density-aware lane check: <b>UNIQUE</b> (<code>flagged_lane = []</code> across all "
            f"{rc['registry_rasters_checked']} indexed rasters; <code>{100 * top21['b2_overlap']:.2f}%</code> vs GEMSDOE32 B2, "
            f"<code>{100 * top21['worst_cand_dots_within_3px']:.2f}%</code> max across {top21['n']} sibling top-scorers, "
            f"<code>{100 * own['worst_cand_dots_within_3px']:.2f}%</code> max across {own['n']} own-lineage rasters, "
            f"<code>{100 * h23_ov:.2f}%</code> vs <code>h23-a-6pct</code>, "
            f"surface <code>|Spearman| &le; {rc['surface_max_abs_spearman']:.4f}</code>). "
            f"Strict literal 70% flags only the 3 non-discriminative &ge;73.4%-halo rasters (<code>r13-lattice-s5</code>, <code>pindrop-*</code>)."
        )
        h72_section = f"""<section class="card"><p class="eyebrow">CURRENT SESSION · 3 PRE-REGISTERED EXPERIMENTS (DRAWS 80–85) · 4 RANKED HYPOTHESES</p>
<h2>H72 Unit-Consistent Tensor Gradient, Valley-Crossing Contrast &amp; DEM-Free Magnetic Depth-Splay</h2>
<p><b>Pre-registered before fitting:</b>
<a href="../knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md">4 ranked hypotheses &amp; H72-1/2 design (<code>53cb884</code>)</a> ·
<a href="../knowledge/30_preregistered_h72_3_subsurf_blind_2026-10-26.md">H72-3 DEM-free subsurface design (<code>fc60bdd</code>)</a> ·
<a href="../knowledge/31_h72_outcomes_and_portfolio_synthesis_2026-10-26.md">Full PhD synthesis &amp; 9-site audit</a> ·
<a href="../registry/run_card_h72_2026-10-26.json">JSON Run Card</a>.</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Four ranked H72 geological hypotheses">
<table><thead><tr><th>Rank</th><th>Hypothesis &amp; Cached Layers</th><th>Physical Signature &amp; Why Catalogue Misses It</th><th>Named Non-Fault Mimic</th><th>Repo Novelty, Cost &amp; Official Data</th><th>Expected ΔDTI / Status</th></tr></thead>
<tbody>
<tr><td><b>1</b></td><td><b>H72-A · PTTG-DR</b><br><small>Bands 02, 03, 09, 10, 11, 12, 16, 17</small></td><td>Unit-consistent isotropic gravity/magnetic THDR + Phillips horizontal differential curvature <code>K_diff</code> (fixes <code>r=+0.948</code> E–W directional bias of band 18 and ~40&times; TMI unit mismatch) + de-aproned OOF HGB; catches concealed pediment/playa &amp; E–W transfer faults.</td><td>Caldera ring-fracture walls, pluton aureoles, basaltic feeder dikes</td><td>First rotationally invariant gravity tensor curvature + propensity-de-aproned HGB in repo; ~16 min CPU; 100% cached GDR #1391 layers (USGS/PACES gravity &amp; NAMAG TMI verified obtainable).</td><td><code>+0.003..+0.012</code><br><b>Tested in Exp 1</b> (<code>+0.0061</code> vs Blind in 4/4 folds; FAIL vs H35)</td></tr>
<tr><td><b>2</b></td><td><b>H72-B · VCCD + RBDT</b><br><small>Bands 01, 02, 05, 06, 07, 13, 14, 15, 19</small></td><td>Anisotropic across- vs along-strike Mahalanobis step in K/Th/U + 2 m temperature + heatflow gated by 100 m LiDAR scarp coherence; catches active range-front/relay splays vs contour-parallel shorelines.</td><td>Pluvial Lake Lahontan/Bonneville shorelines, welded tuff cooling units, fan toes</td><td>Uses across/along-strike contrast ratio rather than isotropic gradient or ROD shift; ~16 min CPU; cached USGS NURE K/Th/U + 3DEP 100 m LiDAR (USGS 3DEP STAC verified free).</td><td><code>+0.002..+0.008</code><br><b>Tested in Exp 2</b> (<code>+0.0073</code> vs Blind in 4/4 folds; <code>+0.0005</code> vs H35 in 2/4 folds)</td></tr>
<tr><td><b>3</b></td><td><b>H72-C · MTHS</b><br><small>Bands 03, 09, 10, 11, 12, 17 (zero DEM/LiDAR)</small></td><td>Multi-scale upward-continued (200 m / 600 m / 1.5 km) magnetic tilt-zero lateral depth-splay + strike-coherent gravity curvature; catches blind steeply dipping intrabasinal faults beneath alluvial fans while structurally immune to DEM-scarp ribbon collisions.</td><td>Tilted ash-flow tuff sheets, buried pluton roof pendants, paleochannel basalts</td><td>First multi-altitude upward-continued magnetic tilt-locus migration in repo (zero DEM/LiDAR/Family E); ~7 min CPU; cached GDR #1391 potential fields.</td><td><code>+0.001..+0.006</code> vs Subsurf<br><b>Tested in Exp 3</b> (<code>+0.0014</code> vs Subsurf, <code>flagged_lane = []</code>; FAIL vs H35)</td></tr>
<tr><td><b>4</b></td><td><b>H72-D · BDFP</b><br><small>Bands 02, 10, 11, 12, 16, 19</small></td><td>Paired antithetic gravity inflection across narrow intrabasinal horsts/step-overs weighted by strain rate; catches buried accommodation relays.</td><td>Exhumed metamorphic core-complex domes, dense carbonate horst blocks</td><td>Pairs opposing signed second-derivative walls across 0.8–3.0 km basin horsts; ~15 min CPU; cached GDR #1391 gravity + Kreemer geodetic strain.</td><td><code>0.000..+0.005</code><br>Registered reserve (capped at 3/3 experiments)</td></tr>
</tbody></table></div>

<div class="table-scroll" tabindex="0" role="region" aria-label="H72 3-experiment holdout results">
<table><thead><tr><th>Exp / Draws</th><th>Candidate Arm</th><th>Withheld Pos</th><th>Canary Max AUC</th><th>Candidate HOLDOUT-DTI [95% CI]</th><th>Same-Run Control(s)</th><th>Paired Contrast (Folds +)</th><th>Verdict</th></tr></thead>
<tbody>
<tr><td><b>Exp 1</b><br><code>[80, 81]</code></td><td><code>A3_PTTG_DEAPRON</code><br><small>(&amp; <code>A1_PTTG_H35</code>)</small></td><td>{w1:,}</td><td>{c1_auc:.4f} (PASS)</td><td><code>{e1['arms']['A3_PTTG_DEAPRON']['mean_dti']:.5f}</code><br><small>[{e1['arms']['A3_PTTG_DEAPRON']['ci95_dti'][0]:.4f}, {e1['arms']['A3_PTTG_DEAPRON']['ci95_dti'][1]:.4f}]</small></td><td>Blind: <code>{e1['arms']['CTRL_BLIND_BD']['mean_dti']:.5f}</code><br>H35: <code>{e1['arms']['CTRL_H35']['mean_dti']:.5f}</code></td><td><b><code>{e1['contrasts']['A3_PTTG_DEAPRON_vs_CTRL_BLIND_BD']['mean']:+.5f}</code></b> vs Blind ({e1['contrasts']['A3_PTTG_DEAPRON_vs_CTRL_BLIND_BD']['folds_positive']}/4)<br><code>{e1['contrasts']['A3_PTTG_DEAPRON_vs_CTRL_H35']['mean']:+.5f}</code> vs H35 ({e1['contrasts']['A3_PTTG_DEAPRON_vs_CTRL_H35']['folds_positive']}/4)</td><td><span class="badge b-warn">Blind PASS / H35 FAIL</span></td></tr>
<tr><td><b>Exp 2</b><br><code>[82, 83]</code></td><td><code>B3_FULL_DEAPRON</code><br><small>(&amp; <code>B1_FULL_H35</code>)</small></td><td>{w2:,}</td><td>{c2_auc:.4f} (PASS)</td><td><code>{e2['arms']['B3_FULL_DEAPRON']['mean_dti']:.5f}</code><br><small>[{e2['arms']['B3_FULL_DEAPRON']['ci95_dti'][0]:.4f}, {e2['arms']['B3_FULL_DEAPRON']['ci95_dti'][1]:.4f}]</small></td><td>Blind: <code>{e2['arms']['CTRL_BLIND_BD']['mean_dti']:.5f}</code><br>H35: <code>{e2['arms']['CTRL_H35']['mean_dti']:.5f}</code></td><td><b><code>{e2['contrasts']['B3_FULL_DEAPRON_vs_CTRL_BLIND_BD']['mean']:+.5f}</code></b> vs Blind ({e2['contrasts']['B3_FULL_DEAPRON_vs_CTRL_BLIND_BD']['folds_positive']}/4)<br><code>B1</code> vs H35: <code>{e2['contrasts']['B1_FULL_H35_vs_CTRL_H35']['mean']:+.5f}</code> ({e2['contrasts']['B1_FULL_H35_vs_CTRL_H35']['folds_positive']}/4)</td><td><span class="badge b-warn">Blind PASS / H35 FAIL</span></td></tr>
<tr><td><b>Exp 3</b><br><code>[84, 85]</code></td><td><b><code>C1_SUBSURF_PTTG_MTHS</code></b><br><small>(Featured GeoTIFF)</small></td><td>{w3:,}</td><td>{c3_auc:.4f} (PASS)</td><td><code>{e3['arms']['C1_SUBSURF_PTTG_MTHS']['mean_dti']:.5f}</code><br><small>[{e3['arms']['C1_SUBSURF_PTTG_MTHS']['ci95_dti'][0]:.4f}, {e3['arms']['C1_SUBSURF_PTTG_MTHS']['ci95_dti'][1]:.4f}]</small></td><td>Subsurf: <code>{e3['arms']['CTRL_SUBSURF_D']['mean_dti']:.5f}</code><br>H35: <code>{e3['arms']['CTRL_H35']['mean_dti']:.5f}</code></td><td><code>{e3['contrasts']['C1_SUBSURF_PTTG_MTHS_vs_CTRL_SUBSURF_D']['mean']:+.5f}</code> vs Subsurf ({e3['contrasts']['C1_SUBSURF_PTTG_MTHS_vs_CTRL_SUBSURF_D']['folds_positive']}/4)<br><code>{e3['contrasts']['C1_SUBSURF_PTTG_MTHS_vs_CTRL_H35']['mean']:+.5f}</code> vs H35 ({e3['contrasts']['C1_SUBSURF_PTTG_MTHS_vs_CTRL_H35']['folds_positive']}/4)</td><td><span class="badge b-bad">H35 FAIL · UNIQUE LANE</span></td></tr>
</tbody></table></div>
<p class="small">Evaluator: <code>gems25.metric.dti_binary</code> (α=0.2, β=0.8, 300 m triangular kernel); whole fault segments withheld with 300 m buffer across 4 spatial quadrants; visible catalogue pixels masked pixel-exactly. Stopped cleanly at the 3-experiment budget cap.</p></section>"""

    nid = "note-primary-h72"
    download = (
        f'<p><b>OK to download: YES</b> for local testing of unique content id '
        f'<code>{e(featured["content_id"])}</code> (<code>{featured["positive_pixels"]:,}</code> binary dots, '
        f'SHA-256 <code>{featured["sha256"][:16]}…</code>, EPSG:32611, <code>3730&times;3292</code>, zeros outside, '
        f'zero NaN/Inf across all <code>12,279,160</code> cells, all values in <code>[0, 1]</code>). '
        f'<b>OK to spend a weekly slot: NO — DO NOT SUBMIT.</b> {h72_lane_detail}</p>'
        f'<div class="row">'
        f'<a class="btn" download href="downloads/{e(featured["file"])}">↓ One-Click Download {e(featured["file"])} (testing only)</a> '
        f'<a class="btn alt" download href="downloads/{e(featured["zip"])}">↓ Zip ({e(featured["zip"])})</a> '
        f'<a class="btn alt" download href="../registry/run_card_h72_2026-10-26.json">↓ H72 Run Card JSON</a>'
        f'</div>'
        f'<p class="small" style="margin:8px 0 2px"><b>Research identifier note (&le;140 chars — do NOT paste into DrivenData; not slot-approved):</b> '
        f'<button class="btn alt small" data-copy="{nid}">Copy note</button></p>'
        f'<div class="note"><code id="{nid}">{e(featured["note"])}</code></div>'
    )

    historical = "gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif"
    latest_2026_notes = {
        "GEMSDOE32": "Portfolio-best historical exemplar (`0.2778` OWNER-REPORTED; 49.2% >20 px). Newer 2026-10-26 runs (`H44-1 SPCP`, `PGRN-PU`, `EXP3_H38`) are negative (`DO NOT SUBMIT`).",
        "GEMSDOE36": "`B2` union 1,200 Andersonian PINN dots (`38,854` px, `96.9%` overlap with `B2`; `0.2750` in pinned focus audit / `0.2683` in G36 ledger). Newer 2026-10-26 `MTO-36` (`0.0676`) & `WDP-36` (`0.0933`) are `DO NOT SUBMIT`.",
        "GEMSDOE28": "`h36-1-rung30-blind-r1` (`37,660` px, `0.2710`) & `R1 = D2.8 & (d_cat > 1 px)` (`40,199` px, `0.2708`). Newer 2026-10-26 `S20-NCHC` (`0.1313 vs 0.1444`) is `DO NOT SUBMIT`.",
        "GEMSDOE31": "Byte-identical positive mask to `GEMSDOE28 R1` (`40,199` px). Newer 2026-10-26 `XFCOH31` (`0.0459 vs 0.0481`) is negative (`DO NOT SUBMIT`).",
        "GEMSDOE33": "Analog tip/stepover addition (`41,865` px, `-0.0146` below `B2`, illustrating FP dilution); `CSHT` scored `0.2286`. Newer 2026-10-26 `A33-R3-LLC` & `G33-DPPS` are `DO NOT SUBMIT`.",
        "GEMSDOE25": "This repo: `D2.8` scored `0.2600` (`44,090` px); supervised `H66` scored `0.0742` (`69.6%` in 2–9 px apron). New 2026-10-26 `H72-3` (`88bbebfe79b4`, `41,061` px) is format-valid & density-aware `UNIQUE` (`flagged_lane=[]`), held `DO NOT SUBMIT`.",
        "GEMSDOE30": "Byte-identical positive mask to `GEMSDOE25 D2.8` (`44,090` px); `MSDB1` scored `0.1462`. Newer 2026-10-26 `G30-TAD` & `PTA-1` are negative (`DO NOT SUBMIT`).",
        "GEMSDOE24": "`dot_thin(H19-5, 1.5)` (`60,069` px); `GVC1` scored `0.0859`. Newer 2026-10-26 `H24-DPRF1` (`0.1638` holdout) held `DO NOT SUBMIT` under v2 lattice gate.",
        "GEMSDOE27": "`topo-gap-closure` on `D1.5` (`61,328` px, `0.2449`); non-`H19-5` dual-regime `H29-S` scored `0.2190` (`44.3% >20 px`). `H31-1` (`cf8e1bbef244`) cleared repo-narrow 27-raster gate.",
    }
    rows, cards = [], []
    for row in sorted(focus["sites"], key=lambda r: -r["owner_reported_score"]):
        sname = row["site"]
        extra = latest_2026_notes.get(sname, "")
        rows.append(
            f"""<tr><th scope="row"><a href="{e(row['site_url'])}">{e(sname)}</a></th>
<td>{row['owner_reported_score']:.4f}<small>OWNER-REPORTED</small></td>
<td class="submission-id">{e(row['submission'])}<br><small>{row['positive_pixels']:,} px · {e(extra)}</small></td>
<td><span class="badge b-warn">Historical only — do not re-submit</span></td></tr>"""
        )
        cards.append(
            f"""<article class="card"><h3>{e(sname)} — {row['owner_reported_score']:.4f} <small>(OWNER-REPORTED)</small></h3>
<p>{e(row['mechanism'])} {e(extra)}</p>
<p class="small">{row['positive_pixels']:,} positive pixels · Local format checks: {'pass' if row['local_format_pass'] else 'fail'} ·
Not approved as a new submission. SHA-256: <code class="wrap-hash">{row['sha256']}</code></p>
<a href="{e(row['source_url'])}">Pinned source revision</a> · <a href="{e(row['site_url'])}">Original site</a></article>"""
        )

    coverage = focus["lattice_coverage"]
    alt_h72_html = ""
    if alt_h72_1:
        alt_h72_html = (
            f'<p>Also built in this H72 session (Exp 1 alternate, testing-only, DO NOT SUBMIT — clears own HGB lineage '
            f'at 55.5% and sibling top-scorers at 60.4%, stopped on historical DEM-scarp ribbons <code>h23-a-6pct</code>/<code>r7-nms3</code>): '
            f'<a href="downloads/{e(alt_h72_1["file"])}" download>{e(alt_h72_1["file"])}</a> '
            f'({alt_h72_1["positive_pixels"]:,} px, id <code>{e(alt_h72_1["content_id"])}</code>, not slot-approved).</p>'
        )

    body = f"""<section class="hero"><p class="eyebrow">RESEARCH DECISION BRIEF / 26 OCTOBER 2026</p>
<h1>Know what to submit.<br>Know when to stop.</h1>
<p class="lead">Nine focus sites + sibling context through GEMSDOE92, PhD deconstruction of GEMSDOE32 B2 (0.2778 OWNER-REPORTED), and the 3-experiment H72 DEM-free subsurface GeoTIFF. Zero copied masks. Zero projected scores.</p></section>
<section class="review-decision"><span class="badge b-bad">OK TO SUBMIT: NO</span><h2>Unique H72-3 GeoTIFF is ready to download — DO NOT SUBMIT to a weekly slot</h2>
<p><b>{e(featured['title'])}.</b> {e(featured['summary'])}</p>
{download}
<p class="small">Prior same-day ROD audit status: {status} (<a href="../evidence/rod_2026-10-26/run_card.json" download>ROD decision receipt</a> · <a href="#how-to-submit">How-to-submit checklist</a>).</p></section>

<section><h2>Executive summary across all 9 focus sites (+ GEMSDOE19..92 context)</h2>
<p><b>Highest historical focus-site submission: GEMSDOE32 B2 (<code>h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif</code>) — 0.2778, OWNER-REPORTED.</b>
All 9 focus sites currently recommend <b>0 live weekly slot spends today</b>: historical top files are already scored (not eligible as new submissions), and every 2026-10-26 candidate across <code>GEMSDOE24..36</code> failed either its same-run holdout gate or literal lattice/ribbon overlap gate.
Among non-<code>H19-5</code> sibling architectures across <code>GEMSDOE19..92</code>, the strongest reported live results are <b><code>GEMSDOE70 P8-OOF38k</code> (0.2478, OWNER-REPORTED</b>; 37,654 dots, 4-fold OOF dual-population HGB + 300 m submodular cover, 45.5% &gt;2 km), <code>GEMSDOE49</code> (0.2376), <code>GEMSDOE76</code> (0.2343), <code>GEMSDOE63</code> (0.2303), <code>GEMSDOE48</code> (0.2296), and <code>GEMSDOE27 H29-S</code> (0.2190).</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="Nine historical exemplars"><table><thead><tr><th>Site</th><th>Reported result</th><th>Highest supplied historical submission &amp; 2026-10-26 site status</th><th>Eligibility</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="small">Every score above is an unverified user/owner claim (<code>OWNER-REPORTED</code>); no organizer receipt is stored here. The discrepant overall leaderboard figures supplied in task prompts (<code>0.3195</code> from 2026-10-02 DARD, misattributed in prompt prose to GEMSDOE87, vs <code>0.4413</code> / <code>0.4437</code> for <code>xiaofanhu</code>) also remain unverified (<code>IR-25-G87-STALE-PROMPT-CLAIM</code>).</p></section>

<section><h2>PhD analysis: why GEMSDOE32 B2 achieved 0.2778 — and how a unique model can beat 0.2778</h2>
<p><b>1. Exact deterministic pixel chain (zero new fault detections from 0.1922 to 0.2778):</b> Byte-exact raster audits prove the 5-step climb
<code>19GEMSDOE H19-5</code> (121,131 px, <code>0.1922</code>) &rarr; <code>GEMSDOE24 D1.5</code> (60,069 px, <code>0.2477</code>) &rarr;
<code>GEMSDOE25/30 D2.8</code> (44,090 px, <code>0.2600</code>) &rarr; <code>GEMSDOE28/31 R1</code> (40,199 px, <code>0.2708</code>) &rarr;
<b><code>GEMSDOE32 B2</code> (37,654 px, <code>0.2778</code>)</b> added <b>zero</b> detections. Under exact Distance-Weighted Tversky
<code>S = T / (0.2(T + F) + 0.8|G|)</code> (α=0.2, β=0.8, 300 m triangular kernel), <code>TP_w</code> takes a <b>maximum</b> over predictions within 3 px of hidden truth whereas <code>FP_w</code> takes an <b>additive sum</b> over off-fault dots:
(a) Poisson-disk thinning <code>dot_thin(H19-5, 2.4)</code> removed 77,041 kernel-redundant ridge pixels (−63.6% mass) while retaining ~91% of 300 m tube coverage (+0.0678 DTI);
(b) Catalogue-collar pruning <code>B2 = D2.8 &amp; (d_cat &gt; 2 px)</code> deleted 6,436 parallel scarp-halo dots within 200 m of already-mapped USGS/INGENIOUS faults whose marginal truth-to-mass ratio satisfied <code>&Delta;T / &Delta;(T+F) &ll; 0.2S / (1 &minus; 0.2S) &approx; 0.055</code> (+0.0178 DTI). Conversely, <code>GEMSDOE33</code> (41,865 px &rarr; 0.2632) and <code>GEMSDOE36</code> (B2 + 1,200 dots, 38,854 px &rarr; 0.2750 / 0.2683) fell below B2 because low-precision additions violated that marginal threshold. <i>(Because hidden test labels are unavailable, this proves mathematical consistency with the OWNER-REPORTED scores, not causal authentication of hidden truth.)</i></p>
<p><b>2. Why supervised Family-E HGB models collapsed live (H66 = 0.0742) and how to exceed 0.2778:</b> Every live scorer &ge;0.219 places <b>40.9%–49.2%</b> of its ~38k dots at <code>&gt;2 km</code> from known faults (<code>B2</code>: 0% &le;2 px, 27.4% 2–9 px, 49.2% &gt;20 px). Component-withholding holdouts place 47.6% of withheld positives in <code>2–9 px</code> vs 17.1% of background (~8.0&times; prior tilt), tricking Family-E HGB into dumping 69.6% of dots into the 2–9 px apron (only 3.0% &gt;20 px). Surpassing <code>0.2778</code> without copying <code>H19-5</code> requires:
(i) <b>propensity-matched negative sampling in <code>d_vis</code> strata + whole-basin holdout evaluation</b> so training and selection reward blind basin discovery;
(ii) <b>2D spatial receptive fields (multi-scale U-Net / ConvNeXt on 6.4–12.8 km tiles)</b> that separate 15 km linear en-echelon fault scarps from sinuous pluvial Lake Lahontan/Bonneville shorelines and volcanic rims (where B2 wastes &gt;65% of its 37,654 dots); and
(iii) <b>300 m submodular facility-location emission with <code>d_cat &gt; 2 px</code> collar pruning</b> (~35k–38k binary dots, 45–50% at <code>&gt;2 km</code>), extending the non-<code>H19-5</code> <code>GEMSDOE70</code> 0.2478 architecture.</p>
<a href="../knowledge/31_h72_outcomes_and_portfolio_synthesis_2026-10-26.md">Read the full PhD derivation, H72 synthesis &amp; caveats</a> ·
<a href="../knowledge/28_focus_review_2026-10-26.md">Prior focus review</a></section>

{h72_section}

<section class="card"><p class="eyebrow">PRIOR SAME-DAY EXPERIMENT · PRESERVED AUDIT TRAIL</p>
<h2>Prior test: radiometric offset discontinuity (ROD)</h2>
<p>Does a compositional pattern match better after sliding one side of a scarp along strike? The preregistered ROD test uses cached K/Th/U and LiDAR step/coherence,
not a copied prediction mask. Volcanic flow lobes, sediment sorting and survey seams can mimic this signature.</p>
{outcome}<p><a href="../knowledge/27_preregistered_rod_2026-10-26.md">ROD hypotheses &amp; frozen design</a> ·
<a href="../evidence/rod_2026-10-26/feature_canaries.json">ROD feature canaries</a> ·
<a href="../evidence/rod_2026-10-26/surface_lane.json">ROD surface audit</a></p></section>
{pol3_section}

<section><h2>85-raster lane audit &amp; the dense-lattice / ribbon ceiling</h2>
<p>We repaired all four shared lane validators (<code>validate_gem_candidate.py</code>, <code>check_lane_surface.py</code>, <code>check_lane_duplicates.py</code>, <code>lane_check_extended.py</code>; <code>IR-25-LANE-VALIDATOR-DIR-PARITY-AND-RIBBON-SATURATION</code>) so every check audits all <b>85</b> available rasters across <code>scored</code>, <code>calibration</code>, <code>top_scorers</code>, <code>artifacts</code>, <code>research</code>, and <code>docs/downloads</code>.</p>
<ul>
<li><b>H72-3 DEM-free subsurface (<code>88bbebfe79b4</code>) clears every discriminative lane check:</b> <code>flagged_lane = []</code> (<code>UNIQUE vs available registry</code>), max surface <code>|Spearman| = 0.2857 &le; 0.90</code>, max 3-px overlap <code>39.55%</code> across all 21 sibling top-scorers (<code>24.86%</code> vs <code>GEMSDOE32 B2</code>), max <code>48.96%</code> across all 20 <code>GEMSDOE25</code> own-lineage rasters, and <code>62.25% / 60.45% &le; 70%</code> against the un-thinned historical DEM-scarp ribbons (<code>h23-a-6pct.tif</code> with 335,879 px and <code>r7-nms3-dem10-scarp.tif</code> with 103,347 px) that collided with DEM-bearing <code>H72-1</code> (81.96%).</li>
<li><b>Non-discriminative literal lattice ceiling:</b> The registered 5-px lattice's three-pixel halo covers <b>{coverage['coverage_fraction']*100:.4f}%</b> of eligible footprint pixels (only {coverage['uncovered_pixels']:,} pixels lie outside it). Any candidate above 21,713 unique dots automatically exceeds 70% one-way proximity to <code>r13-lattice-s5</code> (17.0% reverse coverage). No density exception was used to promote a slot; <code>H72-3</code> remains <b>DO NOT SUBMIT</b>.</li>
</ul></section>

<section><h2>Site-by-site executive findings (all 9 focus sites)</h2>{''.join(cards)}</section>

<section id="how-to-submit"><h2>Executive guide: how a submission becomes eligible (and why today is DO NOT SUBMIT)</h2>
<ol class="steps"><li><b>Research gate.</b> Beat the same-run best comparable buffered holdout; report pooled HOLDOUT-DTI, evaluator version, withheld-positive count and 95% CI. Confirm on fresh draws.</li>
<li><b>Novelty gate.</b> Check both the pre-placement continuous surface and exact final dots against all 85 registry rasters. Stop for rank correlation above 0.90 or more than 70% within 3 px on discriminative rasters. Renaming, changing compression or filling outside NaNs is never a new prediction.</li>
<li><b>File gate (prevents <code>"Predicted values must be in range [0, 1]"</code>).</b> Single-band <code>float32</code> GeoTIFF, <code>EPSG:32611</code>, <code>3730&times;3292</code>, exact 100 m geotransform, finite predictions in <code>[0, 1]</code> throughout all 5,167,373 footprint pixels (zeros outside in <code>-zeros.tif</code> so zero NaNs exist anywhere in the raster), verified automatically by two independent validators without human intervention.</li>
<li><b>Selector gate.</b> Separate owner authorization and a verified remaining weekly slot (cap: 3/week) are required. Format pass never implies submission approval.</li>
<li><b>Only when a future candidate passes all 4 gates:</b> click download on the approved hash-linked <code>-zeros.tif</code>, open DrivenData #306's submission page manually in a browser, select the <code>.tif</code> file, paste its &le;140-character note, submit, and record the organizer receipt in <code>registry/live_scores.json</code>. Automated access to <code>drivendata.org</code> is strictly prohibited.</li></ol>
<p><b>Today's action: DO NOT SUBMIT.</b> Download <code>{e(featured['file'])}</code> only for local inspection, pipeline benchmarking, or ensembling research; spend <b>0</b> weekly slots.</p>
<details><summary>Historical file for learning only — never submit as a new file</summary>
{alt_h72_html}
<p>Prior H71 DIRECT-physics research TIF (id <code>9eb0c31e5149</code>, testing-only, DO NOT SUBMIT) — <a href="downloads/gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif" download>gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif</a> (59,472 px, not slot-approved).</p>
<p>Historical H66 artifact (scored 0.0742 OWNER-REPORTED; DO NOT SUBMIT) — <a href="downloads/{historical}" download>Download historical H66 TIF — DO NOT SUBMIT</a>.</p>
<p>Archived APFL piedmont-flexure research TIF (testing-only, DO NOT SUBMIT) — <a href="downloads/gems25-apfl-piedmont-flexure-s3p0-k3p5-20261026-8aebdab87158-zeros.tif" download>gems25-apfl-piedmont-flexure-s3p0-k3p5-20261026-8aebdab87158-zeros.tif</a> (43,798 px, not slot-approved).</p>
</details></section>

<section><h2>Verified official sources, live GitHub activity feed &amp; remaining work</h2>
<ul><li><a href="sources.html">Full auditable table of official sources, SHA-256 input manifest &amp; {len(json.loads((ROOT / 'registry/irregularities.json').read_text())['issues'])} tracked irregularities</a> (every claim verified line-by-line or explicitly flagged).</li>
<li><a href="../registry/run_card_h72_2026-10-26.json">H72 JSON Run Card</a> · <a href="../registry/review_passes_h72_2026-10-26.json">3-pass cumulative self-review receipt</a> · <a href="../evidence/h72_3_lane_extended.json">85-raster lane audit</a> · <a href="../evidence/h72_3_independent_audit_zeros.json">Independent format audit</a> · <a href="../evidence/focus_audit_2026-10-26.json">Nine-site hash &amp; mask audit</a> · <a href="../evidence/official_reference_2026-10-26.json">Official reference repo audit</a>.</li>
<li><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Official problem and format</a> ·
<a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">Rules PDF (NREL/DOE)</a> ·
<a href="https://gdr.openei.org/submissions/1391">INGENIOUS GDR 1391</a> ·
<a href="https://pubs.usgs.gov/ds/1052/">USGS SGMC DS-1052</a> ·
<a href="https://www.usgs.gov/3d-elevation-program">USGS 3DEP</a> — manual-review links (DrivenData never queried automatically).</li></ul>
<h3>Live GitHub &amp; official-source feed (all 9 focus sites + official repositories)</h3>
<div id="feed" data-base=""><p class="small">Loading <code>data/feed.json</code> …</p></div>
<p class="small"><b>Remaining work &amp; limitations:</b> (1) Component-withholding holdouts have an 8.0&times; 2–9 px apron bias; build a whole-basin / 25 km-block holdout before the next promotion attempt. (2) Train a 2D multi-scale U-Net / ConvNeXt spatial backbone with propensity-matched negative sampling to separate fault scarps from pluvial shorelines without copying H19-5. (3) Reconcile quarantined SGMC Faults provenance and dense-lattice selector rules across the portfolio. <a href="history.html">Historical experiment/download archive</a>.</p></section>"""
    if root_page:
        body = body.replace('href="../', 'href="').replace('href="downloads/', 'href="docs/downloads/')
        body = body.replace('href="history.html"', 'href="docs/history.html"')
        body = body.replace('href="sources.html"', 'href="docs/sources.html"')
        body = body.replace('id="feed" data-base=""', 'id="feed" data-base="docs/"')
    return body


def readme_status() -> str:
    brief = (ROOT / "knowledge/current_project_brief_2026-10-26.md").read_text()
    subs = json.loads((ROOT / "registry/submissions.json").read_text())["files"]
    p = next(s for s in subs if s["role"] == "primary")
    return (
        "<!-- CURRENT-REVIEW-2026-10-26 -->\n"
        "## Current decision — 2026-10-26 (H72 DEM-free subsurface lane)\n\n"
        "**OK to download: YES (local testing only) · OK to spend a weekly slot: NO — DO NOT SUBMIT.** "
        f"Featured unique GeoTIFF [`{p['file']}`](docs/downloads/{p['file']}) "
        f"(content id `{p['content_id']}`, `{p['positive_pixels']:,}` binary dots, SHA-256 `{p['sha256']}`; "
        "all 15 hard format checks PASS, zero NaN/Inf, values in `[0, 1]`; "
        "**density-aware lane verdict: `UNIQUE` (`flagged_lane = []` across all 85 indexed rasters; `24.86%` vs `GEMSDOE32 B2`, `48.96%` max own-lineage)**; "
        "`HOLDOUT-DTI = 0.0594` vs same-run `H35 = 0.1538` -> **GATE FAIL, DO NOT SUBMIT**). "
        "[Nine-site executive review, 0.2778 PhD proof & H72 outcomes](docs/current-review.html) · "
        "[H72 synthesis (`knowledge/31`)](knowledge/31_h72_outcomes_and_portfolio_synthesis_2026-10-26.md) · "
        "[H72 Run Card (`registry/run_card_h72_2026-10-26.json`)](registry/run_card_h72_2026-10-26.json) · "
        "[Prior ROD run card](evidence/rod_2026-10-26/run_card.json). "
        "Across all 9 focus sites (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`), **`GEMSDOE32 B2` (`0.2778` `OWNER-REPORTED`)** remains the highest historical exemplar (not eligible as a new submission), and **0 weekly slots** are recommended today.\n\n"
        "Read the current owner brief below every session, then the preserved historical prompts. "
        "**Maximize P(Win)** and **Own the Outcome**: a negative scientific result is a first-class deliverable, never an excuse to submit an unvalidated or duplicate file.\n\n"
        "<details><summary>Current owner prompt — normalized standing brief (not verbatim)</summary>\n\n"
        + brief
        + "\n</details>\n\n<!-- END-CURRENT-REVIEW-2026-10-26 -->\n"
    )


def main() -> None:
    from build_site import page

    (ROOT / "docs/current-review.html").write_text(page("Current executive review", render_body(), "current", ""))


if __name__ == "__main__":
    main()
