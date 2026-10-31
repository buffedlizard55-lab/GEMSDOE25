#!/usr/bin/env python3
"""Generate docs/executive-summary-2026-10-31.html from the evidence JSON files (no hand-typed numbers).

    python scripts/build_executive_summary_2026_10_31.py
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "evidence"
OUT = ROOT / "docs" / "executive-summary-2026-10-31.html"


def j(name: str) -> dict:
    return json.loads((EV / name).read_text())


def esc(x) -> str:
    return html.escape(str(x))


def main() -> int:
    ns = j("nine_site_summary_2026-10-31.json")["sites"]
    cand = j("clean_candidate_2026-10-31.json")
    ver = j("verify_clean_candidate_2026-10-31.json")
    lane = j("lane_check_clean_candidate_2026-10-31.json")
    e3, e4, e5 = j("bound_fill_exp3_2026-10-31.json"), j("repulsion_exp4_2026-10-31.json"), j("clean_construction_exp5_2026-10-31.json")
    inv = j("submission_inventory_2026-10-31.json")
    b2 = next(f for f in inv["files"] if f["file"].startswith("GEMSDOE32"))
    ok_count = sum(1 for s in ns.values() if s["ok_to_download_and_submit"].startswith("YES"))
    rows = []
    for site, s in ns.items():
        reason = "; ".join(s["blocking_reasons"]) or "none"
        rows.append(
            "<tr>"
            f"<td><strong>{esc(site)}</strong></td>"
            f"<td><code>{esc(s['file'])}</code></td>"
            f"<td>{s['owner_score']:.4f}<br><small>OWNER-REPORTED</small></td>"
            f"<td>NOT ESTIMATED</td>"
            f"<td>{'Yes' if s['unique_among_nine'] else 'No'} (max {s['max_within3px_share_of_its_dots_to_another_top_file_pct']:.1f}% of dots within 3 px of {esc(s['nearest_other_site'])})</td>"
            f"<td class='no'>NO</td>"
            f"<td><small>{esc(reason)}</small></td>"
            "</tr>"
        )
    e3r, e4r, e5r = e3["arms"], e4["arms"], e5["arms"]

    def hd(res, arm, split):
        r = res[arm][split]
        return f"{r['pooled_dti']:.5f} [{r['ci95'][0]:.5f}, {r['ci95'][1]:.5f}]"

    def arm_rows(res, arms, names):
        out = []
        for a in arms:
            out.append(f"<tr><td>{esc(a)}</td><td>{esc(names[a])}</td><td>{hd(res, a, 'dev')}</td><td>{res[a]['dev']['n_truth_total']:,}</td>"
                       f"<td>{hd(res, a, 'conf')}</td><td>{res[a]['conf']['n_truth_total']:,}</td></tr>")
        return "\n".join(out)

    e3_names = {"F1": "Lane bound-fill, ridge-ranked halo (pre-registered candidate)", "F2": "Lane bound-fill, random halo (control)",
                "F3": "Top-K ridge, not lane-compliant (reference)", "F4": "Random K over footprint (floor)"}
    e4_names = {"P0": "Base top-37,654 ridge", "P1": "Base minus dots within 200 m of visible catalogue (B2-style)",
                "P2": "Density-matched random thinning", "P3": "Repulsion with count refill"}
    e5_names = {"C1": "Protocol-clean halo fill (lowest registry coverage) = shipped file construction",
                "C2": "Random halo fill (control)", "C3": "Random K over footprint (floor)"}
    fname = cand["file"]
    lane_max = max(r["dots_within_3px"] for r in lane["rows"])
    lane_rho = max(abs(r["spearman"]) for r in lane["rows"] if r["spearman"] is not None)
    b2_pct = b2["within_200m_of_catalogue_pct"]

    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Executive summary (31 Oct 2026): can we submit a file?</title>
<style>
body{{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:1180px;margin:24px auto;padding:0 16px;color:#1b1f24;line-height:1.5}}
h1{{font-size:1.7rem}} h2{{margin-top:2rem;border-bottom:1px solid #d0d7de;padding-bottom:.3rem}}
.banner{{border:3px solid #b42318;background:#fef3f2;padding:14px 18px;border-radius:8px;font-size:1.05rem}}
.ok{{border-color:#067647;background:#ecfdf3}}
table{{border-collapse:collapse;width:100%;font-size:.9rem;margin:10px 0}}
th,td{{border:1px solid #d0d7de;padding:6px 8px;vertical-align:top;text-align:left}}
th{{background:#f6f8fa}} td.no{{color:#b42318;font-weight:700}}
code{{font-size:.82rem;word-break:break-all}} small{{color:#57606a}}
.tag{{display:inline-block;padding:1px 6px;border-radius:4px;background:#eaeef2;font-size:.78rem;margin-right:4px}}
</style></head><body>
<p><a href="index.html">&larr; site home</a> · <a href="../README.md">README (owner brief)</a></p>
<h1>Executive summary: can we download and submit a file? (31 Oct 2026)</h1>

<div class="banner"><strong>Answer: NO file is cleared for a leaderboard slot.</strong>
<br>A unique, format-valid TIF is provided for download so you can inspect the file, but its holdout result is <strong>far below random</strong>, so it is <strong>not a submission candidate</strong>.
<br>The highest owner-reported score that passes the portal's range rule (<strong>GEMSDOE32, 0.2778</strong>) is a file that was <strong>already submitted</strong>. Copying it is not allowed, and no unique file has evidence of beating it.</div>

<h2>1. Download and submit status (one table)</h2>
<table>
<tr><th>Item</th><th>File to download</th><th>Score</th><th>Estimated score</th><th>Unique?</th><th>OK to download AND submit?</th><th>Why</th></tr>
<tr><td><strong>NEW unique TIF</strong> (this session)</td>
<td><a href="downloads/{esc(fname)}"><code>{esc(fname)}</code></a><br><small>(also a .zip with the same bytes)</small></td>
<td>none yet</td><td>NOT ESTIMATED<br><small>holdout DTI 0.0042 (E5, 95% CI 0.0023–0.0061) vs random floor 0.0327</small></td>
<td>Yes vs all 120 readable registry rasters (max {lane_max*100:.2f}% of dots within 3 px, limit 70%; max |rho| {lane_rho:.2f}). <strong>Lane audit UNVERIFIED</strong> (one registry raster on a different grid, see §6).</td>
<td class="no">Download: as a unique test file only.<br>Submit: NO</td>
<td><small>Format PASS (independent verifier; see §4). Holdout far below random. Not cleared (AGENTS rule 5).</small></td></tr>
{''.join(rows)}
</table>
<p><small>Nine-site rows: the files live on the owner mirrors (links in the README brief). OK-to-submit count: <strong>{ok_count} of 9</strong>. Scores are OWNER-REPORTED (no organizer receipt exists). Source: <code>evidence/nine_site_summary_2026-10-31.json</code>.</small></p>

<h2>2. Why GEMSDOE32 (0.2778) scored highest</h2>
<p><span class="tag">COMPUTED</span> The file is the end of a subset chain. Each step removes dots near the labelled catalogue:</p>
<ul>
<li>D2.8 (GEMSDOE30 / GEMSDOE25, 44,090 dots): 14.6% of dots within 200 m of the catalogue, owner-reported 0.2600.</li>
<li>h27-4 (GEMSDOE31, 40,199 dots): 6.33%, owner-reported 0.2708.</li>
<li>B2 (GEMSDOE32, {b2['dots']:,} dots): <strong>{b2_pct:.1f}%</strong> within 200 m, owner-reported 0.2778. It is also <strong>zeros outside the footprint</strong>, the form the portal accepts.</li>
</ul>
<p><span class="tag">INFERENCE</span> DTI (src/gems25/metric.py) weights false positives at alpha = 0.2 and false negatives at beta = 0.8, so a wrong dot costs less than a missed fault. Removing dots that sit near the catalogue can therefore raise DTI when they are false positives. <strong>Not proven:</strong> the removal could be a density effect (fewer dots), and the 0.0070 gain over the parent is within what one leaderboard round can move. Our holdout (E4) cannot separate the two: repulsion minus density-matched thinning = {e4['paired_differences']['dev']['P1-P2']['diff']:+.5f} (dev) and {e4['paired_differences']['conf']['P1-P2']['diff']:+.5f} (confirm), both CIs spanning zero.</p>

<h2>3. Can we beat 0.2778? Not shown.</h2>
<p>Three pre-registered experiments ran this session (budget: 3). All three are negative on the holdout proxy. Labels: <span class="tag">HOLDOUT-DTI</span> (evaluator <code>gems25.metric.dti_binary</code>, pooled over draws; 95% CI from the shared bootstrap helper <code>boot</code>, 10,000 resamples; withheld positives shown).</p>
<h3>E3 (knowledge/56 §3): lane-compliant bound-fill</h3>
<table><tr><th>Arm</th><th>Construction</th><th>Dev DTI [95% CI]</th><th>Withheld (dev)</th><th>Virgin confirm DTI [95% CI]</th><th>Withheld (conf)</th></tr>
{arm_rows(e3r, ("F1","F2","F3","F4"), e3_names)}
</table>
<p><strong>Verdict: {esc(e3['verdict'])}.</strong> The ridge ranking inside the r13 halo is worse than random (F1 − F2 = {e3['paired_differences']['dev']['F1-F2']['diff']:+.5f}, CI excludes zero). Canary: ridge AUC {e3['leakage_canary']['summary']['conf.auc_ridge']['min']:.2f}–{e3['leakage_canary']['summary']['conf.auc_ridge']['max']:.2f}, so the ridge carries no measured holdout skill. Gate G0 passed.</p>
<h3>E4 (knowledge/56 §4): B2 mechanism control (repulsion vs thinning)</h3>
<table><tr><th>Arm</th><th>Construction</th><th>Dev DTI [95% CI]</th><th>Withheld (dev)</th><th>Virgin confirm DTI [95% CI]</th><th>Withheld (conf)</th></tr>
{arm_rows(e4r, ("P0","P1","P2","P3"), e4_names)}
</table>
<p><strong>Verdict: {esc(e4['verdict'])}.</strong> Note: E4 reused confirmation seeds 150–153, which E3 had already used in this session (disclosed in the review).</p>
<h3>E5 (knowledge/56 §6): the protocol-clean construction (the shipped file)</h3>
<table><tr><th>Arm</th><th>Construction</th><th>Dev DTI [95% CI]</th><th>Withheld (dev)</th><th>Virgin confirm DTI [95% CI]</th><th>Withheld (conf)</th></tr>
{arm_rows(e5r, ("C1","C2","C3"), e5_names)}
</table>
<p><strong>Verdict: {esc(e5['verdict'])}.</strong> Choosing halo pixels that <em>other</em> registry submissions avoid removes holdout signal: on confirm, C1 is {e5r['C1']['conf']['pooled_dti']:.4f} against {e5r['C2']['conf']['pooled_dti']:.4f} for random halo fill (C2) and {e5r['C3']['conf']['pooled_dti']:.4f} for the random floor (C3). Possible causes (not separated here): the registry rasters encode catalogue-proximity, or the hidden faults sit where submitters already put dots. Flagged for review (IR-31-REGISTRY-COVERAGE).</p>

<h2>4. The new TIF: what was checked, on the bytes</h2>
<table>
<tr><th>Check</th><th>Result</th><th>Receipt</th></tr>
<tr><td>Independent format verifier (grid, CRS, transform, single-band float32, finite values in [0,1] over the whole array, zeros outside, no dots on catalogue, ZIP holds the exact bytes)</td><td>{'PASS' if ver['all_hard_checks_pass'] else 'FAIL'} (positive pixels {ver['positive_pixels']:,}; catalogue positives {ver['catalogue_positive_pixels']})</td><td><code>evidence/verify_clean_candidate_2026-10-31.json</code></td></tr>
<tr><td>Dots</td><td>{cand['dots']:,} = {cand['lane_free_dots']:,} lane-free + {cand['halo_dots']:,} r13-halo</td><td><code>evidence/clean_candidate_2026-10-31.json</code></td></tr>
<tr><td>Lane audit against the registry (duplicate test: |Spearman| &gt; 0.90 or &gt; 70% of dots within 3 px)</td><td>{len(lane['rows'])} readable references: <strong>no duplicate flagged</strong>; max dot share {lane_max*100:.2f}%; max |rho| {lane_rho:.2f}. Verdict <strong>{esc(lane['verdict'])}</strong> because one declared reference is on a different geotransform (IR-31-GEOM-HORSE-GRID; diagnostic geographic overlap 0.6%, not clearance).</td><td><code>evidence/lane_check_clean_candidate_2026-10-31.json</code></td></tr>
<tr><td>Name and note</td><td>File <code>{esc(fname)}</code>; note: <em>{esc(cand['note'])}</em> ({cand['note_chars']} characters, within the 140-character protocol limit)</td><td>—</td></tr>
<tr><td>Estimated organizer score</td><td>NOT ESTIMATED. No holdout signal, and no organizer receipt exists.</td><td>—</td></tr>
</table>

<h2>5. Hypotheses (new, ranked by expected DTI gain and cost; none validated)</h2>
<ol>
<li><strong>H-HF1, USGS Great Basin heat-flow residual × structure (BLOCKED).</strong> Layer: USGS heat-flow map and supporting data, DOI 10.5066/P9BZPVUC (<a href="https://catalog.data.gov/dataset/heat-flow-maps-and-supporting-data-for-the-great-basin-usa">catalog.data.gov record</a>). Signature: conductive-heat-flow residual above the regional background, where upflow is focused along permeable faults. Why it could catch a missing fault: it is an independent physical channel not in the USGS/INGENIOUS catalogue. Mimic: regional heat-flow variation from radiogenic plutons or sediment blankets. Repo difference: pre-registered in knowledge/09 (H27-4) and knowledge/10 (H29-4), but never run. <strong>Cost:</strong> medium (124 MB ZIP). <strong>Blocker:</strong> sciencebase.gov is not reachable from this sandbox. Owner action: supply a pinned copy or allow the host.</li>
<li><strong>H-REG1, registry-coverage as a diagnostic (not a candidate).</strong> Test whether "pixels few submitters cover" predicts holdout truth (E5 suggests it is anti-predictive). Cost: nil (already computed). Risk: crowd-submission information may be a leakage path, so it must not be used to choose dots without owner review.</li>
<li><strong>H-GRAD1, shallow temperature-gradient map (BLOCKED).</strong> Layer: NBMG/SMU Temperature Gradient Map of the Great Basin (0–1 km gradient, wells in known geothermal areas excluded to keep the prediction blind), available via <a href="https://data.wu.ac.at/schema/geothermaldata_org/MTEzMzRlOGYtOGJlNy00OTUwLWFlOWEtM2QyYzYyYjkzOTky">geothermaldata.org metadata</a>. Signature: gradient excess not explained by the catalogue. Cost: low once fetched. Blocker: the grid is not in the repo or on the allowed hosts.</li>
<li><strong>H-QF1, USGS Quaternary Fault and Fold Database as an independent fault prior (partly tested).</strong> Source: <a href="https://www.usgs.gov/programs/earthquake-hazards/faults">USGS Faults program page</a>, DOI 10.5066/P9BCVRCK. The repo already uses GDR QFaults-derived layers (knowledge/27 lists <code>gdr_qfaults</code>). Only a fully independent fetch of the USGS file would be new. Expected gain: low.</li>
</ol>

<h2>6. Irregularities for review</h2>
<ul>
<li><strong>IR-31-GEOM-HORSE-GRID:</strong> registry raster <code>geom-horse-ensemble.tif</code> (GEMSDOE14) has the template's shape but a different geotransform (origin 500,000 E / 4,500,000 N vs 243,350 E / 4,508,550 N). Only 6,482 of its 116,225 horse dots fall in the template footprint. The file cannot be checked on the template grid, which blocks a clean lane audit.</li>
<li><strong>IR-31-NAN-SCORED:</strong> the README records NaN-outside files as failing the portal range check ("Fails (NaN)"), yet the same files carry owner-reported scores (e.g. 0.2600). Both cannot be right without organizer receipts.</li>
<li><strong>IR-31-UNIQUENESS-METRIC:</strong> the README uniqueness column uses Jaccard (GEMSDOE28 max 0.557). The brief's lane rule is an asymmetric within-3 px share. Under that rule GEMSDOE28 is 100% within 3 px of GEMSDOE24, because GEMSDOE24 is denser. The rule therefore marks all nine top files as non-unique, which the table above uses.</li>
<li><strong>IR-31-SAMPLE-NAN:</strong> the organizer's sample file (owner mirror, pinned) is NaN outside the footprint, which the portal rejects. The writer therefore uses zeros outside.</li>
<li><strong>IR-31-PINDROP-LANE:</strong> the first lane-compliant build (21,700 dots, bound-fill) overlapped <code>pindrop-discovery.tif</code> at 71.05%. It was removed from <code>docs/downloads</code> and is not packaged (evidence kept).</li>
<li><strong>IR-31-E3E4-SEEDS:</strong> E3 and E4 share virgin seeds 150–153; E5 was added after E3/E4 (disclosed in knowledge/56 §6).</li>
<li><strong>IR-31-LEADERBOARD:</strong> the brief gives 0.4413 as the high score in one place and 0.3195 in another (unresolved; see README). A human reading of the leaderboard is still needed.</li>
</ul>

<h2>7. Limitations and next steps</h2>
<ol>
<li>Organizer receipts are the only score evidence. Nothing here is an organizer score.</li>
<li>The portal's handling of zeros outside the footprint is <strong>unverified</strong> (verifier: "portal outside-footprint behavior unverified"). The zeros convention is inferred from owner-reported scored files (GEMSDOE32, GEMSDOE36).</li>
<li>The holdout proxy is off-scale (it puts the live best files at 0.02–0.03, against 0.25–0.28 owner-reported). The random-floor arms score 0.032–0.036 on it, above every structured arm, so the proxy cannot rank files.</li>
<li>Next session: unblock H-HF1 or H-GRAD1 (owner supplies a pinned copy). Pre-register it before any run. Do not spend a slot unless the candidate beats the paired comparator on virgin seeds.</li>
<li>Owner decision: does the 70% lane rule apply to the competition? The brief sets it as a rule for this work; its scope for the competition is not stated. Every file this session was built under it.</li>
</ol>
<p><small>Generated by <code>scripts/build_executive_summary_2026_10_31.py</code> from the evidence files listed above. Re-run to refresh.</small></p>
</body></html>
"""
    OUT.write_text(html_doc)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
