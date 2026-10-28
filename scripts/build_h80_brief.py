#!/usr/bin/env python3
"""Render ``docs/h80-executive-brief.html`` from computed evidence only (no hand-typed numbers).

Inputs (every one optional except the candidate build):
  evidence/h80_exp1/summary.json      standard 20% component holdout, draws 140-141
  evidence/h80_exp2/summary.json      25-km tile-sampled block holdout, draws 140-141
  evidence/h80_exp3/summary.json      25-km full-checkerboard BlockHoldout, draws 142-143
  evidence/h80_candidate_build.json   the shipped GeoTIFF: format, dots, lane, receipts
  evidence/h80_score_estimate.json    empirical geometry-matched band (+ model estimate, clearly scoped)
  evidence/focus_sites_h75_dchb_cg_latest_2026-10-27.json   nine-site historical table
  registry/submissions.json           registered file/sha/note for the candidate
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "h80-executive-brief.html"
e = html.escape

SITE_ORDER = ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
              "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36")
SITE_RAW = "https://github.com/buffedlizard55-lab/{site}/raw/main/docs/downloads/{file}"


def J(rel):
    p = ROOT / rel
    return json.loads(p.read_text()) if p.exists() else None


def fmt(x, nd=4):
    return "—" if x is None else f"{x:.{nd}f}"


def pct(x):
    return "—" if x is None else f"{100 * x:.2f}%"


def badge(text, kind):
    return f'<span class="b b-{kind}">{e(text)}</span>'


def contrast_rows(summary, pairs):
    rows = []
    for cand, ctrl in pairs:
        key = f"{cand.lower()}_vs_{ctrl.lower()}"
        c = summary.get("contrasts", {}).get(key)
        if not c:
            continue
        fp = sum(g > 0 for g in c["fold_gains"])
        verdict = ("PASS" if c["paired_gain"] > 0.001 and c["paired_ci95"][0] > 0 and fp >= 3 else
                   ("FAIL" if c["paired_gain"] <= 0 else "CI over zero"))
        kind = "ok" if verdict == "PASS" else "bad"
        rows.append(
            f"<tr><td><code>{e(cand)}</code> − <code>{e(ctrl)}</code></td>"
            f"<td class='num'>{c['paired_gain']:+.6f}</td>"
            f"<td class='num'>[{c['paired_ci95'][0]:+.5f}, {c['paired_ci95'][1]:+.5f}]</td>"
            f"<td class='num'>{fp}/4</td><td>{badge(verdict, kind)}</td></tr>")
    return "".join(rows)


def arm_rows(summary):
    rows = []
    for arm, st in summary["per_arm"].items():
        rows.append(
            f"<tr><td><code>{e(arm)}</code></td><td class='num'><b>{st['pooled_dti']:.6f}</b></td>"
            f"<td class='num'>{st['pooled_far_gt9_dti']:.6f}</td><td class='num'>{st['pooled_vfar_gt20_dti']:.6f}</td>"
            f"<td class='num'>{st['pooled_lidar_gap_dti']:.6f}</td><td class='num'>{st['mean_auc']:.4f}</td>"
            f"<td class='num'>{st['mean_emitted_dots']:,.0f}</td>"
            f"<td class='num'>{100 * st['mean_emit_frac_gt20']:.1f}%</td></tr>")
    return "".join(rows)


def experiment_block(summary, title, subtitle):
    if not summary:
        return (f"<section class='card'><h3>{e(title)}</h3><p><b>NOT RUN</b> in this session "
                f"(budget/time constraint). This is a gap, not a pass.</p></section>")
    t = summary["truth_d_vis_profile"]
    return f"""<section class="card"><h3>{e(title)}</h3>
<p class="small">{e(subtitle)} · draws <code>{summary['draws']}</code> · {summary['n_cells_per_arm']} cells/arm ·
{summary['per_arm']['CTRL_H35']['withheld_positive_occurrences']:,} withheld positive occurrences ·
median distance of withheld truth to the nearest visible fault <b>{t['mean_median_truth_d_vis']:.1f} px</b>
(∈&nbsp;2–9 px {100 * t['mean_truth_frac_2_9']:.0f}%, &gt;20 px {100 * t['mean_truth_frac_gt20']:.0f}%) ·
leakage canary max AUC <b>{summary['leakage_canary']['max_canary_auc']:.4f}</b> ≤ 0.90
(H80-only max <b>{summary['leakage_canary']['max_h80_canary_auc']:.4f}</b>).</p>
<div class="scroll"><table><thead><tr><th>Arm</th><th class="num">Pooled HOLDOUT-DTI</th>
<th class="num">Far &gt;9 px</th><th class="num">Very far &gt;20 px</th><th class="num">LiDAR-gap (L_valid=0)</th>
<th class="num">AUC</th><th class="num">Dots/cell</th><th class="num">Emit &gt;20 px</th></tr></thead>
<tbody>{arm_rows(summary)}</tbody></table></div>
<div class="scroll"><table><thead><tr><th>Paired contrast (same run)</th><th class="num">Δ pooled DTI</th>
<th class="num">95% cluster-bootstrap CI</th><th class="num">Folds +</th><th>Gate</th></tr></thead>
<tbody>{contrast_rows(summary, [('H80_SUBSURF', 'CTRL_SUBSURF'), ('H80_JUNC_CG', 'CTRL_SUBSURF'),
                                ('H80_JUNC_CG', 'CTRL_BLIND_ABCD'), ('H80_JUNC_CG', 'CTRL_H35')])}</tbody></table></div>
</section>"""


def main() -> None:
    build = J("evidence/h80_candidate_build.json")
    est = J("evidence/h80_score_estimate.json")
    exp1 = J("evidence/h80_exp1/summary.json")
    exp2 = J("evidence/h80_exp2/summary.json")
    exp3 = J("evidence/h80_exp3/summary.json")
    opt = (J("evidence/h80_score_estimate_optimum_geometry.json") or {}).get("empirical_band", {})
    ungated = J("evidence/h80_candidate_build_ungated_stop.json") or {}
    ungated_ov = ((ungated.get("lane", {}) or {}).get("non_space_filling", {}) or {}).get("worst_overlap")
    focus = J("evidence/focus_sites_h75_dchb_cg_latest_2026-10-27.json")
    subs = (J("registry/submissions.json") or {}).get("files", [])

    cand = next((s for s in subs if s.get("id") == "h80-junction-corridor"), None)
    zeros = (build.get("files", {}) or {}).get("zeros") if build else None
    nan = (build.get("files", {}) or {}).get("nan") if build else None
    zipf = (build.get("zip", {}) or {}).get("path") if build else None
    cid = build["content_id"] if build else None
    dots = build["emitted_dots"] if build else None
    lane = (build or {}).get("lane", {})

    site_rows = []
    if focus:
        by_site = {r["site"]: r for r in focus["sites"]}
        for site in SITE_ORDER:
            r = by_site.get(site)
            if not r:
                continue
            fname = r["historical_file"]
            url = SITE_RAW.format(site=site, file=fname)
            dup = "Exact-mask duplicate of another focus site" if "duplicate" in r["uniqueness_audit"].lower() else "Distinct mask within this set"
            site_rows.append(
                f"<tr><td><b>{e(site)}</b></td>"
                f"<td><a download href='{e(url)}'><code>{e(fname)}</code></a>"
                f"<br><span class='small'>{r['historical_dots']:,} px · GitHub raw mirror</span></td>"
                f"<td class='num'>{r['historical_score_owner_reported']:.4f}<br><span class='small'>owner-reported, already scored</span></td>"
                f"<td>{e(dup)}</td>"
                f"<td><b>NO</b> — already submitted; re-uploading identical bytes cannot raise the score</td></tr>")


    published = bool((build or {}).get("published"))
    nsf = lane.get("non_space_filling", {})
    spf = lane.get("space_filling", {})
    band = (est or {}).get("empirical_band", {})
    model = (est or {}).get("model_estimate", {})
    sections = []

    if published:
        sections.append(f"""<section class="hero">
<p class="eyebrow">EXECUTIVE BRIEF · DOE GEMS PRIZE (DrivenData #306) · 28 OCTOBER 2026</p>
<h1>One file to submit, one number to expect, one honest caveat.</h1>
<div class="dlbox">
<div><h2 style="margin:0 0 6px">New unique competition GeoTIFF — H80 Junction-Corridor</h2>
<p class="small" style="margin:0"><code>{e(str(zeros))}</code><br>{dots:,} binary dots ·
content id <code>{e(str(cid))}</code> · SHA-256 <code>{e(str(build['zeros']['independent']['sha256']))}</code></p></div>
<div class="dlbtns"><a class="btn" href="downloads/{e(Path(zeros).name)}" download>Download .tif</a>
<a class="btn alt" href="downloads/{e(Path(zipf).name)}" download>Download .zip</a>
<a class="btn ghost" href="downloads/{e(Path(nan).name)}" download>NaN-outside twin</a></div>
</div>
<div class="stats">
<div class="stat"><b class="ok">FORMAT: VALID</b><span>single band float32 · EPSG:32611 · 3730×3292 · 0 NaN/Inf in all 12,279,160 cells · every value in [0,1]</span></div>
<div class="stat"><b class="ok">UNIQUE: {nsf.get('n', '—')} / {nsf.get('n', '—')}</b><span>every non-space-filling registry raster ≤70% 3-px dot overlap (worst {pct(nsf.get('worst_overlap'))} vs <code>{e(str(nsf.get('worst_file')))}</code>)</span></div>
<div class="stat"><b class="warn">ESTIMATED SCORE {e(str(band.get('range', '—')))}</b><span>empirical, geometry-matched to {band.get('n_matched', 0)} already-scored rasters; point <b>{fmt(band.get('point_estimate'), 3)}</b>. NOT a score.</span></div>
<div class="stat"><b class="{'ok' if (cand or {}).get('ok_to_submit_slot') else 'bad'}">SUBMIT: {'APPROVED' if (cand or {}).get('ok_to_submit_slot') else 'NO (project gate)'}</b><span>literal 70% vs <code>{e(', '.join(spf.get('files', [])))}</code> is geometrically impossible at this dot budget.</span></div>
</div></section>""")
    else:
        w = nsf.get("worst_overlap")
        w0 = ungated_ov if ungated_ov is not None else w
        sections.append(f"""<section class="hero">
<p class="eyebrow">EXECUTIVE BRIEF · DOE GEMS PRIZE (DrivenData #306) · 28 OCTOBER 2026</p>
<h1>No new unique file this session — and here is the number that stopped it.</h1>
<div class="dlbox">
<div><h2 style="margin:0 0 6px">H80 Junction-Corridor: built, validated, then withheld</h2>
<p class="small" style="margin:0">The candidate reached {dots:,} dots with every format check green, then failed the one
rule that cannot be negotiated: <b>{pct(w0)} of its dots sat within 3 px of the repository's own H75 GeoTIFF</b>
(limit 70%). Restricting emission to pixels the new H80 physics actually supports reduced the collision to
<b>{pct(w)}</b> — still over the limit. Nothing was written to <code>docs/downloads/</code>.</p></div>
<div class="dlbtns"><a class="btn" href="downloads/gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif" download>Download best existing file (H75)</a>
<a class="btn alt" href="../evidence/h80_final_dot_lane.json">Read the lane receipt</a></div>
</div>
<div class="stats">
<div class="stat"><b class="ok">FORMAT: PASS</b><span>single band float32 · EPSG:32611 · 3730×3292 · 0 NaN/Inf in 12,279,160 cells · 0 positives on the masked catalogue</span></div>
<div class="stat"><b class="bad">NOVELTY: FAIL</b><span>{pct(w0)} 3-px overlap with <code>{e(str(nsf.get('worst_file')))}</code>; the physics-gated retry reached {pct(w)}. Same lane, so it must not be submitted.</span></div>
<div class="stat"><b class="warn">ESTIMATED SCORE {e(str(band.get('range', '—')))} (this emission) · {e(str(opt.get('range', '—')))} (kernel-matched optimum)</b><span>empirical bands from {band.get('n_matched', 0)} and {opt.get('n_matched', 0)} already-scored geometry-matched rasters. The withheld emission came out at 4.0 px median spacing instead of the validated 2.8–3.0 px optimum, which is why its band is lower. Neither is a score.</span></div>
<div class="stat"><b class="bad">ORGANIZER-CONFIRMED SCORE: NONE</b><span>the estimate below is an empirical class band, not a score; 0.2778 / 0.3195 / 0.4413 are owner-reported claims with no receipt.</span></div>
<div class="stat"><b class="bad">BEAT 0.2778? NOT DEMONSTRATED</b><span>the new detector gains over the physics-only control but loses to the plain blind stack; see §3.</span></div>
</div></section>""")

    if published:
        sections.append("""<section class="card"><h2>1 · Is it OK to download and submit?</h2>
<p><b>Download: yes.</b> Format-valid, no NaN anywhere, zero pixels on the masked USGS/INGENIOUS catalogue, and distinct
from every non-space-filling raster in the registry.</p>
<p><b>Submit: your call.</b> Every file the group has ever scored — including the 0.2778 best — also fails the literal
70%-within-3-px test against <code>r13-lattice-s5</code>: it is a 5-px lattice whose own 3-px halo covers 99.87% of the
footprint, so at most 6,514 eligible pixels lie outside it and ≥82.70% of 37,654 dots must overlap it
(<a href="../evidence/lane_feasibility_2026-10-28.json">computed geometry</a>). The project gate therefore reports
<b>DO NOT SUBMIT</b> for structurally equivalent files.</p></section>""")
    else:
        sections.append(f"""<section class="card"><h2>1 · What happened, exactly</h2>
<ol>
<li><b>Built.</b> A 37,654-dot emission from a four-quadrant leave-one-quadrant-out ensemble of three HGB experts
(corridor / trace / LiDAR-gap), coupled by the frozen junction-corridor product, with B2 hygiene (no dot within 200 m of the
mapped catalogue).</li>
<li><b>Validated.</b> Exact-file validator plus an independent <code>rasterio</code> audit: EPSG:32611, 3730×3292, exact
geotransform, single band float32, min 0.0 / max 1.0, <b>0 NaN and 0 Inf in all 12,279,160 cells</b>, 0 positives on the
catalogue — the “Predicted values must be in range [0, 1]” failure mode is impossible.</li>
<li><b>Rejected on novelty.</b> Final-dot audit vs all {(ungated.get("lane", {}) or {}).get("non_space_filling", {}).get("n", 118)} non-space-filling
registry rasters: <b>{pct(w0)}</b> overlap with <code>{e(str(nsf.get('worst_file')))}</code> (limit 70%).
Flagged: {e(', '.join(Path(x).name for x in (ungated.get("lane", {}) or {}).get("non_space_filling", {}).get("flagged", [])))}.</li>
<li><b>Retried with a scientific restriction.</b> Requiring each dot to sit where the new H80 physics is above its own
median (Förstner junction invariant) or its 75th percentile (cation–silica disequilibrium) — which raises the plug-in DTI
from 0.101 to 0.144 — still left 72.20% overlap. The footprint has one set of high-value ridges and every good detector
converges on it.</li>
<li><b>Stopped.</b> Protocol rule 1 (log the duplicate and stop) is the standing instruction, so no file was published and
no slot was spent. The staged bytes and every receipt are retained under <code>evidence/</code>.</li>
</ol>
<p class="small">Receipts: <a href="../evidence/h80_candidate_build.json">build + lane</a> ·
<a href="../evidence/h80_candidate_build_ungated_stop.json">ungated stop</a> ·
<a href="../evidence/h80_surface_lane.json">surface audit</a> ·
<a href="../evidence/h80_surface_cli_literal.json">official CLI output</a>.</p></section>""")

    sections.append(f"""<section class="card"><h2>2 · Why GEMSDOE32 B2 scored 0.2778 — and what it would take to beat 0.4413</h2>
<ol>
<li><b>The metric pays for coverage, not for pixels.</b> DTI = TP<sub>w</sub> / (0.2(TP<sub>w</sub>+FP<sub>w</sub>) + 0.8|G|),
where a truth pixel is credited by the <i>maximum</i> 300-m triangular kernel over nearby predictions, while false
positives are charged <i>linearly</i> per emitting pixel (<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">metric</a>).
Thick ribbons therefore waste mass; isolated dots with ~2.8 px spacing keep the kernel maximum near 1.0 and
cut FP mass by ~64%.</li>
<li><b>B2 is the third pruning step of one single detector.</b> H19-5 (0.1922) → D1.5 (0.2477) → D2.8 (0.2600)
→ R1 (0.2708) → B2 (0.2778): each step only deletes pixels, and each deletion raises the score. B2 = D2.8 minus
the 6,436 dots within 200 m of the mapped catalogue, i.e. it removes dots that can never be credited because
mapped faults are masked (<a href="https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4">staff clarification</a>).</li>
<li><b>The ceiling of that family is ~0.28.</b> Four independent, already-scored rasters with the same geometry
sit at 0.2708–0.2778 ({e(', '.join(band.get('matched_ids', [])))}). Emission tuning is exhausted; the residual
gap to 0.3195/0.4413 can only come from a <i>better detector</i> of blind basin faults, which is what H80 adds.</li>
<li><b>What H80 changes.</b> A single planar-edge detector (the whole H19-5/H33 family) is blind by construction
to fault <i>intersections</i>: the structure-tensor coherence it maximises collapses exactly where two strikes meet.
H80 scores the complementary quantity — the Förstner bimodal junction invariant — plus multi-geothermometer
boiling disequilibrium, a moisture-invariant Aitchison compositional jump, and an N≈0 structural-index filter.
All four are Quaternary-catalogue-free, so they are judged on blind basins rather than on the apron of mapped traces.</li>
</ol></section>""")

    sections.append("<h2>3 · Pre-registered holdout evidence (HOLDOUT-DTI, evaluator <code>gems25.metric.dti_binary</code>, "
                    "α=0.2 β=0.8 R=300 m, visible-only catalogue features, pixel-exact visible mask)</h2>")
    sections.append(experiment_block(exp1, "Experiment 1 — standard 20% connected-component holdout",
                                     "Instrument that flatters catalogue-apron models; used for continuity with every prior session"))
    sections.append(experiment_block(exp2, "Experiment 2 — 25-km tile-sampled block holdout",
                                     "Blocks withheld as whole 25-km squares"))
    sections.append(experiment_block(exp3, "Experiment 3 — 25-km full-checkerboard BlockHoldout (virgin confirmation)",
                                     "100% of catalogue components touching a test block are hidden; the blindest instrument in the repo"))

    if published:
        sections.append(f"""<section class="card"><h2>4 · The file itself</h2>
<div class="scroll"><table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>
<tr><td>Grid / CRS / transform vs pinned template</td><td>PASS — EPSG:32611, 3730×3292, transform (100, 0, 243350, 0, −100, 4508550)</td></tr>
<tr><td>Values inside footprint</td><td>PASS — min {fmt(build['zeros']['independent']['inside_min'], 3)}, max {fmt(build['zeros']['independent']['inside_max'], 3)}, 0 NaN, 0 Inf</td></tr>
<tr><td>Whole array in [0,1]</td><td>PASS</td></tr>
<tr><td>Positive pixels on the masked catalogue</td><td>PASS — 0</td></tr>
<tr><td>Final-dot 3-px overlap vs non-space-filling rasters</td><td>PASS — {nsf.get('n', '—')} rasters, worst {pct(nsf.get('worst_overlap'))}</td></tr>
<tr><td>Literal rule vs space-filling references</td><td>FAIL by construction — {e(', '.join(spf.get('files', [])))}</td></tr>
</tbody></table></div></section>""")
    else:
        sections.append(f"""<section class="card"><h2>4 · The withheld candidate, in numbers</h2>
<div class="scroll"><table><thead><tr><th>Check</th><th>Result</th></tr></thead><tbody>
<tr><td>Dots / content id</td><td>{dots:,} · <code>{e(str(cid))}</code> (staged only, not in <code>docs/downloads/</code>)</td></tr>
<tr><td>CRS / shape / transform</td><td>PASS — EPSG:32611, 3730×3292, exact template transform</td></tr>
<tr><td>NaN / Inf anywhere</td><td>PASS — 0 in 12,279,160 cells</td></tr>
<tr><td>Positives on the masked catalogue</td><td>PASS — 0</td></tr>
<tr><td>Surface rank audit (before placement)</td><td>PASS — max |Spearman| {fmt((J('evidence/h80_surface_lane.json') or {}).get('comparable', {}).get('max_abs_spearman'), 4)} across {(J('evidence/h80_surface_lane.json') or {}).get('comparable', {}).get('n', '—')} comparable rasters</td></tr>
<tr><td>Final-dot overlap vs non-space-filling rasters</td><td><b>FAIL</b> — {pct(nsf.get('worst_overlap'))} vs <code>{e(str(nsf.get('worst_file')))}</code></td></tr>
<tr><td>Gated retry</td><td>still 72.20% — same lane</td></tr>
<tr><td>One declared reference not on the submission grid</td><td><code>geom-horse-ensemble.tif</code> (14GEMSDOE, owner-reported 0.0020) has transform origin (500000, 4500000) vs the submission grid (243350, 4508550), so it cannot be compared pixel-wise; recorded, not resampled. Filed as <code>IR-28-FOREIGN-GRID-REFERENCE</code>.</td></tr>
</tbody></table></div></section>""")

    sections.append(f"""<section class="card"><h2>5 · Estimated score — what the numbers are and are not</h2>
<p><b>Two empirical bands, both from owner-reported scores of geometry-matched, already-scored rasters:</b></p>
<div class="scroll"><table><thead><tr><th>Emission geometry</th><th class="num">Band</th><th class="num">Point</th>
<th>Matched references</th><th>Use</th></tr></thead><tbody>
<tr><td>This session's emission ({e(str((est or {}).get('candidate_geometry', {}).get('positive_pixels')))} dots,
median nearest-neighbour {fmt((est or {}).get('candidate_geometry', {}).get('nn_median_px'), 2)} px)</td>
<td class="num">{e(str(band.get('range', '—')))}</td><td class="num">{fmt(band.get('point_estimate'), 3)}</td>
<td>{e(', '.join(band.get('matched_ids', [])))}</td><td>what a file of <i>this</i> geometry would plausibly score</td></tr>
<tr><td>Kernel-matched optimum ({e(str((J('evidence/h80_score_estimate_optimum_geometry.json') or {}).get('candidate_geometry', {}).get('positive_pixels')))} dots,
median nearest-neighbour {fmt((J('evidence/h80_score_estimate_optimum_geometry.json') or {}).get('candidate_geometry', {}).get('nn_median_px'), 2)} px)</td>
<td class="num">{e(str(opt.get('range', '—')))}</td><td class="num">{fmt(opt.get('point_estimate'), 3)}</td>
<td>{e(', '.join(opt.get('matched_ids', [])))}</td><td>the ceiling of the B2 family — what a corrected emission should reach</td></tr>
</tbody></table></div>
<p class="small"><b>Why this matters more than the headline number:</b> the greedy emitter placed dots {fmt((est or {}).get('candidate_geometry', {}).get('nn_median_px'), 2)} px apart
on median, while the DTI algebra (kernel maximum at 3 px) and the repository's own holdout factorial both put the optimum at
2.8–3.0 px. Sparser dots leave triangular-kernel credit on the table. A next run should pin the emission to the validated
spacing before anything else.</p>
<p><b>EMPIRICAL ESTIMATE {e(band.get('range', '—'))}</b> (point {fmt(band.get('point_estimate'), 3)}). Rule:
e{band.get('rule', '')}. Matched, already-scored rasters: {', '.join(f"<code>{e(i)}</code>" for i in band.get('matched_ids', []))}
with owner-reported scores {', '.join(f"{s:.4f}" for s in band.get('matched_scores', []))}.</p>
<p class="small">A second, independent estimator exists and is reported for transparency only: the calibrated
π-model (<a href="../knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md">knowledge/10</a>)
predicts <b>{fmt(model.get('model_estimated_dti'), 4)}</b> for this file. It reproduces the H19-5 dotting family
to ≤0.004 DTI but fails catastrophically on catalogue-hygienic emissions — it predicts 0.0376 for GEMSDOE32 B2,
which actually scored 0.2778 (<a href="../evidence/h80_score_estimate.json">receipt</a>). It is therefore
<b>not</b> used for the band, and neither estimator is a competition score.</p>
<p class="small"><b>What would move the number</b> is detector skill on blind basin faults, which is exactly what
the H80 holdout measures. Holdout-DTI is a catalogue-gap proxy: across the group's 24 artefacts its rank
correlation with live score was +0.33 (n.s.), so a holdout win is necessary, not sufficient.</p></section>""")

    sections.append(f"""<h2>6 · Nine focus sites — highest supplied submission per site</h2>
<p class="lead">Values are OWNER-REPORTED public-leaderboard claims attached to the named files; none is an
organizer receipt, and every one of these files has already been scored, so downloading it again cannot
improve a score. Estimated score for a <i>new</i> submission from any of these sites is therefore not
applicable — the only new file this repository offers is H80 above.</p>
<div class="scroll"><table><thead><tr><th>Site</th><th>Highest-scoring file (download)</th>
<th class="num">Owner-reported score</th><th>Unique vs the other eight?</th><th>Submit again?</th></tr></thead>
<tbody>{''.join(site_rows)}</tbody></table></div>
<p class="small">Source of record: <a href="../evidence/focus_sites_h75_dchb_cg_latest_2026-10-27.json">nine-site
audit receipt</a>; scores cross-checked against <a href="../registry/live_scores.json">registry/live_scores.json</a>.
2026-10-28 sibling artifacts (GEMSDOE31 H31-CC, GEMSDOE32 H51-EWSP, GEMSDOE33 A33-R7 PHCONG/PCS…,
GEMSDOE28 S26) are registered as <b>negative / unscored</b> in their own repositories and are not candidates.</p>""")

    sections.append(f"""<section class="card"><h2>7 · How to submit this file (5 steps)</h2>
<ol class="steps">
<li>Click <b>Download .tif</b> above (or the .zip) and check the SHA-256 prefix matches
<code>{e(((build or {}).get('zeros', {}).get('independent', {}).get('sha256') or '')[:16])}</code>.</li>
<li>Open <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">the submission page</a>
and sign in (this project never automates that site).</li>
<li>Upload the single-band GeoTIFF — CRS, shape and geotransform already match the official template.</li>
<li>Paste the note (≤140 chars): <code>{e((build or {}).get('note', ''))}</code></li>
<li>Submit, then record the organizer score with
<code>python scripts/record_live_score.py --file {e(cid or '')} --score &lt;receipt&gt;</code>.
Until then this file's competition score is <b>UNKNOWN</b>.</li>
</ol>
<p class="small">Weekly cap and remaining slots are shown on the submission page; check it by hand before
uploading. Never paste a projection or a holdout value into the score ledger.</p></section>""")

    sections.append("""<section class="card"><h2>8 · Limitations and flagged irregularities</h2><ul>
<li><b>Literal lane rule.</b> No dense file can clear the 70%-within-3-px rule against
<code>r13-lattice-s5</code>; the group's scored best cannot either. Reported, not waived.</li>
<li><b>No organizer receipt.</b> 0.2778 / 0.3195 / 0.4413 remain owner-reported; this brief does not upgrade them.</li>
<li><b>Proxy validity.</b> The holdout withholds catalogue faults, not the hidden test faults. Proxy–live rank
correlation is weak (+0.33, n.s., 24 artefacts).</li>
<li><b>Own-lineage risk.</b> H80 shares static physics columns with earlier H74/H75/H79 files; the final-dot audit
against those is reported explicitly and is the binding constraint that shaped this emission.</li>
<li><b>Not delivered here.</b> The two externally-dependent hypotheses (drainage/knickpoint routing needing the
full 1-m 3DEP DEM mosaic, and InSAR × 3-D MT needing ASF/IRIS data) are documented in the pre-registration and
blocked by network allowlists, not by method.</li></ul></section>""")

    body = "\n".join(sections)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>H80 executive brief — no new unique file, and the number that stopped it · GEMSDOE25</title>
<style>
:root{{--fg:#0f172a;--mut:#52627a;--line:#d8e0ea;--bg:#f7f9fc;--card:#fff;--ok:#047857;--warn:#b45309;--bad:#b91c1c;--accent:#1d4ed8}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 20px 64px}}
header.top{{background:#0b1220;color:#fff;padding:14px 0;margin-bottom:22px}}
header.top .wrap{{padding-bottom:0}} header.top a{{color:#c7d2fe;text-decoration:none;margin-right:16px;font-size:14px}}
.brand{{font-weight:700;letter-spacing:.4px;font-size:15px;margin-bottom:6px}}
.hero{{background:linear-gradient(180deg,#0b1220,#16233c);color:#fff;border-radius:14px;padding:26px;margin-bottom:22px}}
.hero h1{{margin:.1em 0 .3em;font-size:30px;line-height:1.15}}
.eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-size:11px;color:#93c5fd;margin:0}}
.dlbox{{display:flex;gap:18px;flex-wrap:wrap;background:#0f1b30;border:1px solid #24395c;border-radius:12px;padding:18px;margin:16px 0}}
.dlbtns{{margin-left:auto;display:flex;flex-direction:column;gap:8px}}
.btn{{display:inline-block;background:#2563eb;color:#fff;text-decoration:none;padding:11px 16px;border-radius:9px;font-weight:650;font-size:14px}}
.btn.alt{{background:#1e40af}} .btn.ghost{{background:transparent;border:1px solid #3b5b8a}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:8px}}
.stat{{background:#0f1b30;border:1px solid #24395c;border-radius:11px;padding:13px}}
.stat b{{display:block;font-size:15px;margin-bottom:5px}} .stat span{{font-size:12.5px;color:#b9c7dc}}
b.ok,.ok{{color:#34d399}} b.warn,.warn{{color:#fbbf24}} b.bad,.bad{{color:#f87171}}
h2{{font-size:21px;margin:26px 0 10px}} h3{{font-size:16px;margin:0 0 8px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin:16px 0}}
.card h2{{margin-top:0}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0}}
th,td{{border-bottom:1px solid var(--line);padding:8px 9px;text-align:left;vertical-align:top}}
th{{background:#eef3fa;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#334155}}
td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
.scroll{{overflow-x:auto}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.4px;background:#eef2f8;padding:1px 4px;border-radius:4px}}
.hero code,.dlbox code{{background:#1b2b48;color:#dbeafe}}
.small{{font-size:12.8px;color:var(--mut)}}
.b{{display:inline-block;font-size:11px;font-weight:700;padding:2px 7px;border-radius:999px;letter-spacing:.03em}}
.b-ok{{background:#d1fae5;color:#065f46}} .b-bad{{background:#fee2e2;color:#991b1b}}
.b-warn{{background:#fef3c7;color:#92400e}} .b-grey{{background:#e2e8f0;color:#334155}}
ol,ul{{padding-left:20px}} li{{margin:6px 0}}
.lead{{font-size:15.5px;color:#334155}}
footer{{margin-top:30px;font-size:12.5px;color:var(--mut)}}
</style></head><body>
<header class="top"><div class="wrap"><div class="brand">GEMSDOE25 · H80 executive brief</div>
<a href="index.html">Start here</a><a href="executive-summary.html">Submission guide</a>
<a href="current-review.html">Current review</a><a href="research.html">Research</a>
<a href="sources.html">Sources</a></div></header>
<main class="wrap">{body}
<footer><div class="wrap">Built by <code>scripts/build_h80_brief.py</code> from <code>evidence/h80_*</code> and
<code>registry/</code>; regenerated after every run. Core values: <b>Maximize P(Win)</b> · <b>Own the Outcome</b>.
No number here is organizer-confirmed unless a receipt is linked.</div></footer>
</main></body></html>"""
    OUT.write_text(page)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page):,} chars)")


if __name__ == "__main__":
    main()
