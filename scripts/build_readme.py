#!/usr/bin/env python3
"""Render README.md: status and result tables come from registry/ + evidence/, the owner brief from knowledge/owner_brief_verbatim.txt."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(p):
    return json.loads((ROOT / p).read_text())


def opt(p):
    f = ROOT / p
    return json.loads(f.read_text()) if f.exists() else None


def main() -> None:
    subs = J("registry/submissions.json")["files"]
    primary = next(s for s in subs if s["role"] == "primary")
    others = [s for s in subs if s["role"] != "primary"]
    ls = J("registry/live_scores.json")
    snap = ls["leaderboard_snapshot"]
    fac = J("evidence/factorial/results.json")
    why = J("evidence/why_0_2477.json")
    emu = J("evidence/emission_model.json")
    add = opt("evidence/addons/results.json")
    conf = opt("evidence/addons_confirm/results.json")
    h27_screen = opt("evidence/h27_screen/results.json")
    h28 = opt("evidence/h28_calibration/design.json")
    h28_anchors = opt("evidence/h28_calibration/anchors.json")
    h28_habitat = opt("evidence/h28_calibration/habitat_fit.json")
    h28_mix = opt("evidence/h28_calibration/mixture.json")
    h28_hold = opt("evidence/h28_holdout/results.json")
    h28_ledger = opt("registry/artifact_ledger.json")
    h27_confirm = opt("evidence/h27_confirm/results.json")
    irr = J("registry/irregularities.json")["issues"]
    best = max(a["score"] for a in ls["artifacts"] if a["score"] is not None)
    brief = (ROOT / "knowledge" / "owner_brief_verbatim.txt").read_text().rstrip()
    L = []
    A = L.append
    A("# GEMSDOE25 — designed-factorial fault discovery for the DOE GEMS Prize\n")
    A("> **Maximize P(Win)** · **Own the Outcome** — the Arena core values are the decision rule for every change in this repository.\n")
    A("**Competition:** [DOE GEMS Prize, DrivenData #306](https://www.drivendata.org/competitions/306/competition-doe-gems/) · "
      "**Live site:** <https://buffedlizard55-lab.github.io/GEMSDOE25/> · **Weekly limit:** 3 submissions · "
      "**Ends:** 3 Dec 2026 (page: 11:59 p.m. UTC; rules: 5:00 p.m. ET — see IR-25-DEADLINE)\n")
    A("## ⬇ Download the format-validated GeoTIFF (not slot-approved)\n")
    A(f"**[↓ `{primary['file']}`](docs/downloads/{primary['file']})** — {primary['summary']}\n")
    A(f"* Format: single-band float32 GeoTIFF, EPSG:32611, 3730 × 3292, 100 m, values in [0, 1] at **all 5,167,373 footprint pixels**, NaN outside "
      f"(verified against the pinned owner-mirror template, not organizer-authenticated; independent check receipt: `docs/downloads/{primary['receipt']}`).")
    A(f"* Unique content id `{primary['content_id']}` · SHA-256 `{primary['sha256']}` · {primary['positive_pixels']:,} emitted pixels · status: **{primary['status']}**.")
    A(f"* **Note to paste** in DrivenData's *Note (optional)* field: `{primary['note']}`")
    for o in others:
        if o["role"] == "fallback":
            A(f"* Format fallback (format troubleshooting only; not slot-approved): [`{o['file']}`](docs/downloads/{o['file']}) — {o['title']} ({o['status']}; {o['positive_pixels']:,} px).")
    A("* Step-by-step upload guide: [`docs/executive-summary.html`](https://buffedlizard55-lab.github.io/GEMSDOE25/docs/executive-summary.html).\n")
    A("## Where things stand\n")
    A(f"* **Unverified leaderboard claims** (reported {snap['reported_utc']}; no organizer page or receipt was accessed): #1 {snap['top10'][0]['participant']} {snap['top10'][0]['best_public_dti']:.4f}; reported rank #5 {snap['top10'][4]['best_public_dti']:.4f}. "
      f"The group-best claim is **{best:.4f}**; the previously reported rank #16/account association is not authenticated. These are not independently verified scores; apparent gaps to ranks #5/#1 are arithmetic on supplied claims only.")
    A("* **Root cause of the reported portal error** (`Predicted values must be in range [0, 1]`): the previous GEMSDOE25 file used an invented footprint — "
      "2,344,929 of the 5,167,373 owner-mirror template-footprint pixels were NaN (NaN fails every range test) and it emitted 1,249,834 positive pixels. Fixed and tested "
      "(`evidence/old_gems25_tif_forensics.json`, `src/gems25/submission.py`). The cause is inferred from the data; the portal validator is not public.")
    r = why["relations"]
    A(f"* **Local audit of the reported 0.2477 raster (score unverified):** it is *exactly* `dot_thin(H19-5, 1.5)` — a pixel-identical deterministic subset ({r['pixel_retention_d1_5'] * 100:.1f} % of H19-5's pixels, none on a catalogue pixel). "
      f"This verifies the raster transformation, not the claimed competition DTI. No organizer receipt/page was accessed; the claimed 0.2477 and 0.3195 remain unverified.")
    d28 = emu["d2_8"]
    A(f"* **Model-only calibration:** if the supplied 0.2477 score claim is correct, the emission model predicts **{d28['model_dti']:.4f}** (band {d28['model_dti_low']:.4f}–{d28['model_dti_high']:.4f}) for `dot_thin(H19-5, 2.4)` "
      "(44,090 px). This is an extrapolation on owner/user-provided score anchors, not independent evidence or a score; no comparison to the unverified 0.3195 claim is established.")
    if h28 and h28_anchors and h28_hold:
        cal = h28["calibrated"]
        refs = h28["reference_rows_under_calibrated_pi"]
        ceil = h28["ceiling_best"]
        anch = h28_anchors["scan"]
        sel = anch[cal["pi"]]["per_anchor"]
        led_n = h28_ledger["n_rows"] if h28_ledger else 30
        fit_n = h28_ledger["n_used_in_fit"] if h28_ledger else 25
        hold_best = h28_hold["best_arm"]
        hold_gate = h28_hold["gate"]
        repro = h28_hold["reproduction_check"]
        A("## H28 — the live metric, calibrated on the group's own 25 hash-verified scores\n")
        A(f"Pre-registered before any fit in [`knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md`](knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md). "
          f"{led_n} competition rasters were fetched from the owner's public GitHub mirrors and content-hashed; **{fit_n} are tied to a reported DTI by SHA-256** "
          "(`registry/artifact_ledger.json`, `scripts/restore_artifacts.py`). Every DTI below labelled *reported* is a user/owner-reported claim, not a receipt; every value labelled *predicted* is conditional on the fitted model.\n")
        A(f"* **The hidden truth cannot be uniform.** For `h19-5`, `h19-4`, `h16-1` and `d1-5` the closed-form inversion of the published DTI has **no solution** under a uniform truth: "
          "no truth count whatever reproduces their reported scores. Under "
          f"`pi ∝ exp(-d(H19-5)/{cal['lambda_hat_px']} px)` all five anchors imply one truth count — "
          + ", ".join(f"{k} {v['implied_N']:,.0f}" for k, v in sel.items())
          + f" → **N = {cal['n_hat']:,.0f}** hidden truth pixels (max spread {h28_anchors['checks']['A2']['max_relative_spread'] * 100:.1f} %), "
          f"which agrees with the blind-lattice-only estimate {anch['uniform']['per_anchor']['lattice-s5']['implied_N']:,.0f} and with this repo's earlier independent 12,503.")
        A("* **The forward model reproduces live scores.** predicted vs reported: "
          + "; ".join(f"`{k}` {refs[k]['dti']:.4f} vs {refs[k]['reported']:.4f}" for k in ("lattice-s5", "h19-5", "d1-5") if k in refs)
          + f". A Monte-Carlo run of the *published* metric on truth drawn from the fitted `pi` agrees with the analytic expectation to "
          f"{max(v['abs_err'] for v in h28['checks']['C5_monte_carlo']['per_artefact'].values()):.4f} DTI (check C5).")
        A(f"* **Why the reported 0.2477 won — arithmetic, not narrative.** Dotting the solid `h19-5` surface threw away "
          f"{100 * (1 - refs['d1-5']['mass'] / refs['h19-5']['mass']):.0f} % of its pixels but only "
          f"{100 * (1 - refs['d1-5']['t'] / refs['h19-5']['t']):.0f} % of the credit it captured, and it cut redundant (overlapping-kernel) mass from "
          f"{refs['h19-5']['redundancy'] / refs['h19-5']['u'] * 100:.0f} % to {refs['d1-5']['redundancy'] / refs['d1-5']['u'] * 100:.0f} % of captured kernel mass. "
          f"Credit per emitted pixel rose {refs['h19-5']['credit_per_px']:.4f} → {refs['d1-5']['credit_per_px']:.4f}; predicted DTI {refs['h19-5']['dti']:.4f} → {refs['d1-5']['dti']:.4f}. "
          "The detector did not change at all: the 0.2477 file is a *geometry* win.")
        A(f"* **The ceiling of that geometry is the file already shipped here.** Sweeping `dot_thin(H19-5, d)` over d ∈ [1.8, 4.0] peaks at "
          f"**d = {ceil['min_dist']:.1f} px, {ceil['mass']:,.0f} px, predicted DTI {ceil['dti']:.5f}** — which *is* the D2.8 download. "
          f"Value-ranked alternatives are worse: greedy-by-`pi*k` at 3 px peaks at {max(r['dti'] for r in h28['designs'] if r['rule'] == 'R3_value3'):.5f}, "
          f"and at 6 px (kernel-disjoint, zero redundancy) at {max(r['dti'] for r in h28['designs'] if r['rule'] == 'R1_value6'):.5f}. "
          f"The 6 px design beats `d1-5` in **{h28['decision']['sensitivity_cells_beating_d1_5'].split('/')[0]} of 9** cells of the (λ, N) sensitivity grid and the shipped D2.8 file in "
          f"**{h28['decision']['sensitivity_cells_beating_d2_8'].split('/')[0]} of 9** (D2.8 dominates d1-5 in every cell: {h28['decision']['d2_8_dominates_d1_5_in_every_cell']}): "
          "the redundancy theorem is true and irrelevant here, because for line-like truth the gaps between disjoint dots cost more credit than the overlap they save.")
        A(f"* **The holdout agrees, with real hidden truth.** A 30-arm factorial (value field × spacing × budget, 4 spatial folds × draws 0,1, one shared fit per cell — "
          "`evidence/h28_holdout/`): spacing 1.5→2.4 px **+0.0074**, 2.4→3.0 −0.0003, 3.0→4.0 −0.0112, 4.0→6.0 **−0.0350**; habitat-ranked dots add "
          f"{h28_hold['contrasts']['value_score_to_habitat']:+.4f} and habitat×score {h28_hold['contrasts']['value_score_to_both']:+.4f} (best arm paired gain "
          f"{hold_gate['mean_gain_vs_paired_base']:+.6f}, p = 0.248). **Gate: FAIL on both criteria** ({hold_best['dti_mean']:.6f} ≤ 0.152003389; gain ≤ 0.001) → no arm is slot-eligible and nothing new was packaged.")
        A(f"* **The remaining gap to 0.3195 is detection, not emission.** At the measured 0.900 false-positive mass per emitted pixel, reaching 0.3195 at this file's budget needs "
          f"**{h28['targets_credit_density']['table']['0.3195'][str(int(ceil['mass']))]['vs_best_current_c_per_px']:.2f}×** its credit density "
          f"({h28['targets_credit_density']['table']['0.3195'][str(int(ceil['mass']))]['credit_per_px_needed']:.4f} vs {ceil['credit_per_px']:.4f}); reaching the reported #5 (0.2941) needs "
          f"{h28['targets_credit_density']['table']['0.2941'][str(int(ceil['mass']))]['vs_best_current_c_per_px']:.2f}×. Emission geometry is exhausted — the whole gap is *which pixels the detector calls faults*.")
        A(f"* **Where the truth is not.** A habitat model in distance-to-known-faults alone cannot explain the 25 live scores "
          f"(leave-one-artefact-out RMSE {min(v['loo_rmse'] for v in h28_habitat['loo'].values()) if h28_habitat else 0.0705:.4f} against a pre-registered 0.020 threshold; the blind lattice is predicted at "
          f"{h28_habitat['checks']['C2']['predicted']:.4f} instead of 0.0904) — its residuals are per-artefact detector skill. **\"Hug the known-fault halo\" is not a supported strategy.** "
          f"A two-band mixture is not identified either (nine-anchor spread {h28_mix['adoption_rule']['criterion_i']['mixture']:.3f} vs a {h28_mix['adoption_rule']['criterion_i']['threshold']:.3f} threshold), so it was **not adopted** and nothing was designed from it.")
        A("* **Where the truth is.** Implied truth count per surface measures off-band truth: "
          f"`h28-dotted-ridge` {h28_mix['single_parent_detail']['h28-dotted-ridge']['implied_N']:,.0f}, "
          f"`lidarscarp-top2pct` {h28_mix['single_parent_detail']['lidarscarp-top2pct']['implied_N']:,.0f}, "
          f"`h25-ctx-ridge` {h28_mix['single_parent_detail']['h25-ctx-ridge']['implied_N']:,.0f} against 12,472–13,358 for the H19-5 family. "
          "Three surfaces sit on truth the H19-5 band does not contain — the GEMSDOE10 context ridge and the 7GEMSDOE LiDAR-scarp top-2 % emission. That is H29's first target.")
        A(f"* **Reproducibility flag (IR-25-COMPARATOR-DRIFT).** The frozen comparator arm recomputes to {repro['recomputed_mean']:.9f} here against the frozen {repro['frozen_mean']:.9f} "
          f"(fold 0 identical to 9 decimals; folds 1–3 differ by up to {repro['max_fold_abs_diff']:.1e}); this session's pipeline re-runs bit-for-bit, so the drift is environmental "
          "(`data/work` is a gitignored derived cache that was never hashed). `evidence/work_cache_hashes.json` now pins every derived cache and the library versions. "
          "**Absolute comparators do not transfer between environments; only same-run paired contrasts do.**")
        A("")
    A("")
    A("## Designed factorial experiment (replaces one-factor-at-a-time)\n")
    A(f"2^(5−1), Resolution V, generator E = ABCD → {fac['design']['runs']} runs × {fac['design']['cells_per_run']} spatially blocked hide-and-recover cells; response = exact sparse-regime DTI. "
      f"Lenth ME = {fac['effects_dti']['lenth']['me']:.4f}. Pre-registered before the run (`knowledge/04_preregistered_factorial_2026-10-02.md`).\n")
    A("| Factor | Family | Class | Main effect (DTI) | Folds + |")
    A("|---|---|---|---|---|")
    for k, v in fac["classification"].items():
        A(f"| {k} | {v['label']} | **{v['classification']}** | {v['main_effect']:+.4f} | {v['folds_positive']}/4 |")
    A("")
    A("Top interactions: " + ", ".join(f"`{k}` {v:+.4f}" for k, v in fac["ranked_interactions"][:4]) + ". Full tables: [`evidence/factorial/results.md`](evidence/factorial/results.md).\n")
    if add:
        A("## Add-on hypotheses (pre-registered gate, paired)\n")
        A("| Arm | mean DTI | Δ vs base | folds + | gate |")
        A("|---|---|---|---|---|")
        A(f"| BASE `{add['base']}` | {add['BASE']['mean_dti']:.4f} | — | — | — |")
        for k, v in add["arms"].items():
            g = v["gate_vs_base"]
            A(f"| {k} | {v['mean_dti']:.4f} | {g['mean_gain']:+.4f} | {g['folds_positive']}/4 | {'pass' if g['passed'] else 'fail'} |")
        em = add["EM0_equal_N"]
        A(f"| EM-0 score-ordered dots vs `dot_thin` (equal N≈{em['n_eq_mean']:.0f}) | {em['sapd']:.4f} vs {em['dot_thin']:.4f} | {em['gate_sapd_vs_dot_thin']['mean_gain']:+.4f} | {em['gate_sapd_vs_dot_thin']['folds_positive']}/4 | {'pass' if em['gate_sapd_vs_dot_thin']['passed'] else 'fail'} |")
        A("")
    if conf:
        A("## Confirmation replicate (fresh draws 2,3; pre-registered)\n")
        A("| Arm | mean DTI | Δ vs BDE | folds + | gate |")
        A("|---|---|---|---|---|")
        A(f"| BASE `{conf['base']}` | {conf['BASE']['mean_dti']:.4f} | — | — | — |")
        for k, v in conf["arms"].items():
            g = v["gate_vs_base"]
            A(f"| {k} | {v['mean_dti']:.4f} | {g['mean_gain']:+.4f} | {g['folds_positive']}/4 | {'pass' if g['passed'] else 'fail'} |")
        em = conf["EM0_equal_N"]
        A(f"| EM-0 score-ordered dots vs `dot_thin` | {em['sapd']:.4f} vs {em['dot_thin']:.4f} | {em['gate_sapd_vs_dot_thin']['mean_gain']:+.4f} | {em['gate_sapd_vs_dot_thin']['folds_positive']}/4 | {'pass' if em['gate_sapd_vs_dot_thin']['passed'] else 'fail'} |")
        A("\n`CFG_*` rows are whole family sets (e.g. `CFG_BE` = the factorial's predicted-best corner, which did not replicate its predicted 0.145).\n")
    A("## Score ledger — user/owner-reported claims (not organizer-verified; full ledger in `registry/live_scores.json`)\n")
    A("| Project | Submission | Score | Note |")
    A("|---|---|---|---|")
    for a_ in sorted((x for x in ls["artifacts"] if x["score"] is not None), key=lambda x: -x["score"])[:10]:
        A(f"| {a_['project']} | `{a_['label']}` | {a_['score']:.4f} | {a_['note']} |")
    A("")
    A("## Prior H26 register — outcomes (ranked before its runs; not a list of untried work)\n")
    A("| Rank | ID | Idea | Recorded outcome |")
    A("|---|---|---|---|")
    A("| 1 | H26-0 | score-aware Poisson-disk dotting + marginal-ratio budget | **passes** (+0.0037 vs score-blind dotting at equal N, 4/4 folds, replicated +0.0034) |")
    A("| 2 | H26-2 | strike-compatibility prior (DEM line orientation × visible-catalogue strike) | alone: fail on draws 0,1 (+0.0015, 2/4), small pass on fresh draws 2,3 (+0.0033, 3/4); jointly passes both |")
    A("| 3 | H26-1 | oriented cross-scarp radiometric contrast (K, Th/K, U/K × DEM normal) | alone: fail on draws 0,1 (+0.0006, 2/4), small pass on draws 2,3 (+0.0026, 4/4); jointly passes both |")
    A("| 4 | H26-3 | concealed joint step (gravity ∧ magnetic ridge, basement-depth step) | alone: fail on draws 0,1 (+0.0003, 2/4), small pass on draws 2,3 (+0.0032, 4/4); jointly passes both |")
    A("| 5 | H26-4 | dilation-tendency-weighted orientation prior (USGS 10.5066/P9YL58W6) | page-listed shapefile; direct access failed, bytes/licence not verified |")
    A("")
    if h27_confirm:
        h27_status = "confirmation passed" if h27_confirm["slot_eligible"] else "confirmation failed; do not promote"
        h27_metrics = h27_confirm["arms"]["TS"]["mean_dti"]
    elif h27_screen:
        h27_status = "screen passed; confirmation draws 6,7 required" if h27_screen["slot_eligible"] else "screen failed; stop, no slot"
        h27_metrics = h27_screen["arms"]["TS"]["mean_dti"]
    else:
        h27_status, h27_metrics = "pre-registered for draws 4,5; not yet scored", None
    A("## Current ranked geological candidates (H27; full layers, signatures, costs and preregistration in `knowledge/09_preregistered_hypotheses_2026-10-02.md`)\n")
    A("| Rank | ID | Idea | Expected proxy ΔDTI (planning bracket) | Status |")
    A("|---|---|---|---|---|")
    h27_result = f"TS DTI {h27_metrics:.6f}; {h27_status}" if h27_metrics is not None else h27_status
    A(f"| 1 | H27-1 | directed visible-fault-tip continuation × multi-scale DEM/LiDAR scarp | +0.001 to +0.010 | {h27_result} |")
    A("| 2 | H27-2 | residualized GDR 2 m temperature probes | 0 to +0.010 | blocked: binary/schema/coverage not fetched |")
    A("| 3 | H27-3 | paleo-geothermal deposits away from visible traces | 0 to +0.005 | blocked: binary/schema/coverage not fetched |")
    A("| 4 | H27-4 | USGS heat-flow residual × structural/scarp support | 0 to +0.005 | blocked: binary, residual definition and licence not verified |")
    A("\nThese ΔDTI ranges are planning judgments, not estimates. No weekly slot is eligible unless the tested candidate beats the 0.152003389 holdout comparator and also passes paired confirmation; the site never uploads automatically.\n")
    A("## Flagged for review (full list with evidence: [`registry/irregularities.json`](registry/irregularities.json))\n")
    for i in irr:
        if i["severity"] in ("critical", "high"):
            A(f"* **{i['id']}** ({i['severity']}, {i['status']}) — {i['issue'][:260]}{'…' if len(i['issue']) > 260 else ''}")
    A("")
    A("## Limitations and what is needed\n")
    A("1. **No competition credentials or organizer receipts.** Every competition raster is an owner mirror (hash-pinned, not organizer-authenticated). The 0.2477 result and 0.3195 leader are user-provided, unverified claims; no competition/leaderboard page was accessed. Do not automate or monitor DrivenData.")
    A("2. **External binaries are blocked here:** GDR 1391 lists the 2 m probe and paleo-geothermal files under CC BY 4.0, but direct downloads failed; the USGS heat-flow ZIP is page-listed, but its bytes and licence were not verified. H27-2/3/4 require a networked runner and source/coverage checks before use.")
    A("3. **Compute:** 2 CPUs / 4 GB RAM, no GPU → boosted trees, not the reference U-Net; no raw 1 m DEM processing. The H27 screen ran in about 14 minutes after the feature cache was built.")
    A("4. **The proxy is not the truth:** the hide-and-recover holdout hides catalogue components; proxy-vs-live correlation in the group's prior record was weak (Spearman +0.33, n = 24, n.s.). Holdout wins are necessary, not sufficient.")
    A("5. **Hidden labels, public/private split, source authenticity, score claims and the portal validator remain undisclosed/unverified.**")
    A("6. **The live-anchored model has a scope limit (IR-25-LIVE-MODEL-SCOPE):** it reproduces the H19-5 family and the blind lattice within 0.004 DTI but under-predicts surfaces outside that band by up to 0.059, so it cannot score an emission that leaves the band.")
    A("7. **The frozen holdout comparator is environment-specific (IR-25-COMPARATOR-DRIFT):** 0.152003389 recomputes to 0.149668 here. Any future gate must recompute its comparator in the same run.\n")
    A("## Next work (order matters)\n")
    if h27_confirm:
        if h27_confirm["slot_eligible"]:
            A("1. H27-1 passed the preregistered confirmation proxy gates. Package a full-data candidate from the confirmed model, validate its exact GeoTIFF and hash, and review it before any manual slot use. The existing D2.8 download is not that candidate.")
        else:
            A("1. H27-1 failed fresh-draw confirmation. Stop; do not use a weekly slot. Any new idea requires a new preregistration.")
    elif h27_screen:
        if h27_screen["slot_eligible"]:
            A("1. H27-1 screen passed; run the frozen confirmation on draws 6,7 before packaging. No weekly slot is eligible until that fresh-draw confirmation passes.")
        else:
            A("1. H27-1 failed the absolute holdout-comparator gate on draws 4,5. Stop per preregistration; do not run confirmation or spend a slot. A T-only follow-up is unconfirmed and would need its own preregistration and fresh holdout validation.")
    else:
        A("1. Run the frozen H27-1 screen on draws 4,5 (`python scripts/run_h27.py --stage screen && python scripts/analyze_h27.py --dir evidence/h27_screen`); do not skip or alter the absolute comparator gate.")
    A("2. Full ranked register with layers, signatures, why-they-find-missing-faults, differences from what exists, obtainability and cost: `knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md` §13 (H29-1 … H29-5).")
    A("3. **H29-1 (ranked first by the live evidence): multi-surface parent.** Build the emission from the union of `h19-5`, `h28-dotted-ridge`/`h25-ctx-ridge` and `lidarscarp-top2pct`, dotted at 2.4-3.0 px with the marginal-rule budget. Those three are the surfaces whose implied truth count exceeds N-hat, i.e. they hold off-band truth; all three rasters are already on disk and hash-verified. It needs either a >=3-band `pi` with more anchors or holdout-only validation, and it must beat a same-run comparator before any slot.")
    A("4. **H29-2/H29-3: skill-weighted consensus pruning, then tip continuation (family T) on that union parent** - the only positive factor in the H27 screen (+0.008120, 4/4 folds), which failed solely on the environment-specific absolute comparator.")
    A("5. On a networked runner, retrieve the official GDR geodetics/seismicity and probe/paleo files (H29-5) and the USGS heat-flow ZIP (H29-4); verify checksums, schema, coverage, residual definitions and licence before preregistering any new test.")
    A("6. Keep the D2.8 file format-validated but unscored/not slot-approved. Only package and consider a specific candidate after it beats a **same-run** paired comparator on the spatially blocked holdout (the frozen 0.152003389 record does not reproduce in this environment — IR-25-COMPARATOR-DRIFT) and, where a pre-registration specifies it, fresh-draw confirmation.")
    A("7. If organizer verification of 0.2477/0.3195 is needed, use an independently supplied non-sensitive receipt; this repository will not fetch or monitor DrivenData.")
    A("8. Owner decisions remain in IR-25-SCORE-IDENTITY, IR-25-TOU, IR-25-PUBLIC-DATA, IR-25-DEADLINE, and IR-27-EXTERNAL-DATA-ACCESS.\n")
    A("## Standing session charter\n")
    A("Read this README **and the verbatim brief below** at the start of every session, then `AGENTS.md`. First commands: `git fetch origin`, compare with the session branch, `gh pr list --state open`. Pre-register before running. No weekly slot unless that specific candidate beats the current holdout best and passes the exact-file audit; no exception is authorized here. Never automate drivendata.org. Review in three passes. Unknown stays unknown.\n")
    A("## Reproduce\n")
    A("```bash\npython -m venv .venv && .venv/bin/pip install -r requirements.txt\n"
      ".venv/bin/python scripts/restore_data.py --group all          # SHA-256-pinned inputs from the owner's public repos -> data/ (ignored by Git); same as: bash scripts/download_competition_data.sh\n"
      ".venv/bin/python scripts/build_features.py && .venv/bin/python scripts/build_addons.py\n"
      "# pre-registered experiments (knowledge/04, 05)\n"
      ".venv/bin/python scripts/run_factorial.py && .venv/bin/python scripts/analyze_factorial.py            # ~30 min on 2 CPUs\n"
      ".venv/bin/python scripts/run_addons.py && .venv/bin/python scripts/analyze_addons.py                  # draws 0,1\n"
      ".venv/bin/python scripts/run_addons.py --out evidence/addons_confirm --draws 2 3 --extra-configs ABCDE BE E && .venv/bin/python scripts/analyze_addons.py --dir evidence/addons_confirm\n"
      ".venv/bin/python scripts/run_emk_extension.py --base BDE --extras X1_K X1_ThK X1_UK X2_compat X2_compat_coh X3_gm X3_gd   # post hoc (Addendum A)\n"
      "# H27-1 frozen 2x2 screen (knowledge/09); confirmation is permitted only if screen gate passes\n"
      ".venv/bin/python scripts/run_h27.py --stage screen && .venv/bin/python scripts/analyze_h27.py --dir evidence/h27_screen\n"
      "# if and only if the screen's absolute + paired gates pass:\n"
      ".venv/bin/python scripts/run_h27.py --stage confirm && .venv/bin/python scripts/analyze_h27.py --dir evidence/h27_confirm\n"
      "# H28: live-anchored calibration, inverse design, holdout factorial (knowledge/10)\n"
      ".venv/bin/python scripts/restore_artifacts.py                # fetch + hash the 30 owner-mirrored competition rasters -> registry/artifact_ledger.json\n"
      ".venv/bin/python scripts/run_h28.py                        # anchors, checks, ceiling sweep, designs, sensitivity (~7 min)\n"
      ".venv/bin/python scripts/run_h28.py --habitat-only          # the section 5 misspecification diagnostic (~10 min)\n"
      ".venv/bin/python scripts/run_h28_mixture.py                 # two-band mixture test (D3)\n"
      ".venv/bin/python scripts/run_h28_holdout.py && .venv/bin/python scripts/analyze_h28_holdout.py   # 30 arms x 8 cells (~6 min)\n"
      "# forensics and emission model\n"
      ".venv/bin/python scripts/analyze_scored_rasters.py && .venv/bin/python scripts/emission_model.py && .venv/bin/python scripts/validate_emission_model.py && .venv/bin/python scripts/harness_references.py\n"
      "# files, site, README\n"
      ".venv/bin/python scripts/build_candidate.py --help            # train on the full catalogue, emit, verify (exploratory surface)\n"
      ".venv/bin/python scripts/package_submissions.py --exploratory-receipt docs/downloads/checks-<file>.json\n"
      ".venv/bin/python scripts/build_data_dictionary.py && .venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py\n"
      ".venv/bin/python -m pytest -q && .venv/bin/python -m ruff check src scripts tests\n```\n")
    A("Set `GEMS_DATA_DIR` / `GEMS_WORK_DIR` to keep the 419 MB raster and the ~1.5 GB feature cache outside the checkout.\n")
    A("## Repository map\n")
    A("| Path | Role |\n|---|---|\n| `src/gems25/` | metric (official DTI + brute-force twin), hide-and-recover holdout, thinning/NMS, families & features, factorial engine, experiment cells, strict submission writer/checker |\n| `scripts/` | restore, build, run, analyse, package, site, README, feed, score recorder |\n| `registry/` | sources (with verification status), irregularities, score ledger, data pins, shipped submissions |\n| `evidence/` | machine-readable results and forensics |\n| `knowledge/` | pre-registrations, ranked hypotheses, verified research digest, the brief |\n| `docs/`, `index.html` | GitHub Pages site (root `index.html` is the landing page; Pages builds from `main:/`) |\n| `tests/` | unit, parity, integrity and reproduction tests |\n")
    A("## Owner brief (verbatim) — read every session\n")
    A("<details><summary><strong>Full text of the owner's brief for this session</strong> (copied from the task message of 2026-10-02; link markup and whitespace as pasted)</summary>\n")
    A("```text\n" + brief + "\n```\n")
    A("</details>\n")
    (ROOT / "README.md").write_text("\n".join(L))
    print("README.md written,", len("\n".join(L)), "chars")


if __name__ == "__main__":
    main()
