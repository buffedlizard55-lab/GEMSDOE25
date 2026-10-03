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
    h30_screen = opt("evidence/h30_relay_screen/results.json")
    h30_confirm = opt("evidence/h30_relay_confirm/results.json")
    irr = J("registry/irregularities.json")["issues"]
    best = max(a["score"] for a in ls["artifacts"] if a["score"] is not None)
    brief = (ROOT / "knowledge" / "owner_brief_verbatim.txt").read_text().rstrip()
    active_brief = (ROOT / "knowledge" / "current_project_brief_2026-10-03.md").read_text().rstrip()
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
      "(44,090 px). This is an extrapolation conditional on owner/user-provided score anchors, not independent evidence or a score; any arithmetic against the unverified 0.3195 claim is conditional on both the claim and the selected model.")
    if h28 and h28_anchors and h28_hold:
        cal = h28["calibrated"]
        refs = h28["reference_rows_under_calibrated_pi"]
        ceil = h28["ceiling_best"]
        anch = h28_anchors["scan"]
        sel = anch[cal["pi"]]["per_anchor"]
        led_n = h28_ledger["n_rows"] if h28_ledger else 30
        fit_n = h28_ledger["n_used_in_fit"] if h28_ledger else 25
        hold_gate = h28_hold["gate"]
        repro = h28_hold["reproduction_check"]
        A("## H28 — metric-model calibration on 25 hash-linked owner-reported scores (claims not independently verified)\n")
        A(f"Pre-registered before any fit in [`knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md`](knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md). "
          f"{led_n} competition rasters were fetched from the owner's public GitHub mirrors and content-hashed; **{fit_n} are tied to a reported DTI by SHA-256** "
          "(`registry/artifact_ledger.json`, `scripts/restore_artifacts.py`). Every DTI below labelled *reported* is a user/owner-reported claim, not a receipt; every value labelled *predicted* is conditional on the fitted model.\n")
        A(f"* **Conditional on the owner-reported anchors, a uniform-π truth model has no finite solution.** For `h19-5`, `h19-4`, `h16-1` and `d1-5` the closed-form inversion of the published DTI has **no solution** under a uniform truth: "
          "no truth count whatever reproduces their reported scores. Under "
          f"`pi ∝ exp(-d(H19-5)/{cal['lambda_hat_px']} px)` all five anchors imply one truth count — "
          + ", ".join(f"{k} {v['implied_N']:,.0f}" for k, v in sel.items())
          + f" → **model-implied N̂ = {cal['n_hat']:,.0f}** pixels in the hidden truth (max spread {h28_anchors['checks']['A2']['max_relative_spread'] * 100:.1f} %), "
          f"which agrees with the blind-lattice-only estimate {anch['uniform']['per_anchor']['lattice-s5']['implied_N']:,.0f} and with this repo's earlier independent 12,503.")
        A("* **The fitted model matches selected owner-reported anchors conditionally; this is not score verification.** predicted vs reported: "
          + "; ".join(f"`{k}` {refs[k]['dti']:.4f} vs {refs[k]['reported']:.4f}" for k in ("lattice-s5", "h19-5", "d1-5") if k in refs)
          + f". A Monte-Carlo run of the *published* metric on truth drawn from the fitted `pi` agrees with the analytic expectation to "
          f"{max(v['abs_err'] for v in h28['checks']['C5_monte_carlo']['per_artefact'].values()):.4f} DTI (check C5).")
        A(f"* **What the 0.2477-labelled file changes locally (the score claim is unverified).** Dotting the solid `h19-5` surface throws away "
          f"{100 * (1 - refs['d1-5']['mass'] / refs['h19-5']['mass']):.0f} % of its pixels but only "
          f"{100 * (1 - refs['d1-5']['t'] / refs['h19-5']['t']):.0f} % of the credit it captured, and it cut redundant (overlapping-kernel) mass from "
          f"{refs['h19-5']['redundancy'] / refs['h19-5']['u'] * 100:.0f} % to {refs['d1-5']['redundancy'] / refs['d1-5']['u'] * 100:.0f} % of captured kernel mass. "
          f"Credit per emitted pixel rose {refs['h19-5']['credit_per_px']:.4f} → {refs['d1-5']['credit_per_px']:.4f}; predicted DTI {refs['h19-5']['dti']:.4f} → {refs['d1-5']['dti']:.4f}. "
          "The detected pixels did not change: the 0.2477-labelled mirror is a geometry-only transform of H19-5; the score-to-file claim remains unverified.")
        A(f"* **Modelled ceiling of that geometry: the file already shipped here.** Under the fitted π, sweeping `dot_thin(H19-5, d)` over d ∈ [1.8, 4.0] peaks at "
          f"**d = {ceil['min_dist']:.1f} px, {ceil['mass']:,.0f} px, predicted DTI {ceil['dti']:.5f}** — which *is* the D2.8 download. "
          f"Value-ranked alternatives are worse: greedy-by-`pi*k` at 3 px peaks at {max(r['dti'] for r in h28['designs'] if r['rule'] == 'R3_value3'):.5f}, "
          f"and at 6 px (kernel-disjoint, zero redundancy) at {max(r['dti'] for r in h28['designs'] if r['rule'] == 'R1_value6'):.5f}. "
          f"The 6 px design beats `d1-5` in **{h28['decision']['sensitivity_cells_beating_d1_5'].split('/')[0]} of 9** cells of the (λ, N) sensitivity grid and the shipped D2.8 file in "
          f"**{h28['decision']['sensitivity_cells_beating_d2_8'].split('/')[0]} of 9** (D2.8 dominates d1-5 in every cell: {h28['decision']['d2_8_dominates_d1_5_in_every_cell']}): "
          "the redundancy theorem is true and irrelevant here, because for line-like truth the gaps between disjoint dots cost more credit than the overlap they save.")
        A(f"* **The hide-and-recover proxy agrees on held-out catalogue components.** A 30-arm factorial (value field × spacing × budget, 4 spatial folds × draws 0,1, one shared fit per cell — "
          "`evidence/h28_holdout/`): spacing 1.5→2.4 px **+0.0074**, 2.4→3.0 −0.0003, 3.0→4.0 −0.0112, 4.0→6.0 **−0.0350**; habitat-ranked dots add "
          f"{h28_hold['contrasts']['value_score_to_habitat']:+.4f} and habitat×score {h28_hold['contrasts']['value_score_to_both']:+.4f} (best arm paired gain "
          f"{hold_gate['mean_gain_vs_paired_base']:+.6f}, p = 0.248). **H28 gate: FAIL on paired gain** ({hold_gate['mean_gain_vs_paired_base']:+.6f} ≤ +0.001); the historical absolute comparator did not reproduce (IR-25-COMPARATOR-DRIFT), so it is not a cross-draw baseline. No arm is slot-eligible and nothing new was packaged.")
        A(f"* **Conditional model calculation against the unverified 0.3195 claim.** At the selected model's 0.900 false-positive mass per emitted pixel, matching that claimed target at this file's budget would need "
          f"**{h28['targets_credit_density']['table']['0.3195'][str(int(ceil['mass']))]['vs_best_current_c_per_px']:.2f}×** its credit density "
          f"({h28['targets_credit_density']['table']['0.3195'][str(int(ceil['mass']))]['credit_per_px_needed']:.4f} vs {ceil['credit_per_px']:.4f}); reaching the reported #5 (0.2941) needs "
          f"{h28['targets_credit_density']['table']['0.2941'][str(int(ceil['mass']))]['vs_best_current_c_per_px']:.2f}×. This is model-based sensitivity arithmetic, not a verified score comparison or proof that all emission changes are exhausted.")
        A(f"* **What the fitted model does not explain among owner-reported anchors.** A habitat model in distance-to-known-faults alone cannot explain the 25 reported score anchors "
          f"(leave-one-artefact-out RMSE {min(v['loo_rmse'] for v in h28_habitat['loo'].values()) if h28_habitat else 0.0705:.4f} against a pre-registered 0.020 threshold; the blind lattice is predicted at "
          f"{h28_habitat['checks']['C2']['predicted']:.4f} instead of 0.0904) — its residuals are per-artefact detector skill. **\"Hug the known-fault halo\" is not a supported strategy.** "
          f"A two-band mixture is not identified either (nine-anchor spread {h28_mix['adoption_rule']['criterion_i']['mixture']:.3f} vs a {h28_mix['adoption_rule']['criterion_i']['threshold']:.3f} threshold), so it was **not adopted** and nothing was designed from it.")
        A("* **Conditional model implication outside the calibration band.** If the owner-reported anchors and fitted model are correct, implied N suggests off-band truth on these surfaces: "
          f"`h28-dotted-ridge` {h28_mix['single_parent_detail']['h28-dotted-ridge']['implied_N']:,.0f}, "
          f"`lidarscarp-top2pct` {h28_mix['single_parent_detail']['lidarscarp-top2pct']['implied_N']:,.0f}, "
          f"`h25-ctx-ridge` {h28_mix['single_parent_detail']['h25-ctx-ridge']['implied_N']:,.0f} against 12,472–13,358 for the H19-5 family. "
          "Under this selected model, those three owner-mirrored surfaces require off-band truth to reconcile the reported anchors; that is a model implication, not evidence of the actual hidden labels. The GEMSDOE10 context ridge and the 7GEMSDOE LiDAR-scarp top-2 % emission remain H29 prioritization targets, not validated truth surfaces.")
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
    A("## Prior registered geological screen (H27; not a current untried candidate; full design in `knowledge/09_preregistered_hypotheses_2026-10-02.md`)\n")
    A("| Rank | ID | Idea | Expected proxy ΔDTI (planning bracket) | Status |")
    A("|---|---|---|---|---|")
    h27_result = f"TS DTI {h27_metrics:.6f}; {h27_status}" if h27_metrics is not None else h27_status
    A(f"| 1 | H27-1 | directed visible-fault-tip continuation × multi-scale DEM/LiDAR scarp | +0.001 to +0.010 | {h27_result} |")
    A("| 2 | H27-2 | residualized GDR 2 m temperature probes | 0 to +0.010 | blocked: binary/schema/coverage not fetched |")
    A("| 3 | H27-3 | paleo-geothermal deposits away from visible traces | 0 to +0.005 | blocked: binary/schema/coverage not fetched |")
    A("| 4 | H27-4 | USGS heat-flow residual × structural/scarp support | 0 to +0.005 | blocked: binary, residual definition and licence not verified |")
    A("\nThese ΔDTI ranges are planning judgments, not estimates. H27-1 failed its registered historical gate; the numbers are not a current cross-draw threshold.\n")
    if h30_confirm:
        h30_result = h30_confirm
        h30_gate = h30_confirm["paired_promotion_gate"]
        if h30_confirm.get("confirmation_gate_passed"):
            h30_status = "fresh-draw confirmation passed; full-data build and exact-file audit still required; no slot approval"
        else:
            h30_status = "fresh-draw confirmation failed; stop; no candidate file or slot"
    elif h30_screen:
        h30_result = h30_screen
        h30_gate = h30_screen["paired_promotion_gate"]
        h30_status = ("screen passed; confirmation draws 8,9 required" if h30_screen.get("screen_gate_passed")
                      else "screen failed; stop; confirmation and candidate file not allowed")
    else:
        h30_result, h30_gate = None, None
        h30_status = "registered for screen draws 6,7; real-data feature smoke passed, no model fit or DTI yet"
    h30_dti = h30_result["arms"]["T_PLUS_P_S"]["mean_dti"] if h30_result else None
    h30_gain = h30_gate["mean_gain_vs_best_paired_control"] if h30_gate else None
    h30_1_status = (f"P+S DTI {h30_dti:.6f}, paired gain {h30_gain:+.6f}; {h30_status}"
                    if h30_result else h30_status)
    A("## Current ranked geological hypotheses (H30; full signatures, novelty, sources, costs and gate in `knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md`)\n")
    A("| Rank | ID | Idea | Expected proxy ΔDTI (planning bracket) | Status |")
    A("|---|---|---|---|---|")
    A(f"| 1 | H30-1 | paired visible-tip cross-strike bridge × LiDAR scarp persistence | +0.001 to +0.008 | {h30_1_status} |")
    A("| 2 | H30-2 | visible-fault junction / accommodation-zone branch field | 0 to +0.006 | registered only; not fitted |")
    A("| 3 | H30-3 | scale-persistent terrain lineament | 0 to +0.005 | registered only; not fitted |")
    A("\nPlanning brackets are uncertain prioritization judgments, not estimates or live-score forecasts. H30-1 screen draws are 6,7; confirmation draws 8,9 are allowed only after a screen pass. Even confirmation is only proxy evidence and cannot grant slot approval by itself.\n")
    A("**Five-family factorial status:** the separate A–E Resolution V design is preserved in `evidence/factorial/`: 16 randomized design rows × 8 cells = 128 model cells, plus 24 reference cells (152 cell rows total). Its analyzer reproduced the tracked results byte-for-byte on 2026-10-03. H30 is additional, not a substitute. The handoff's 'unrun' note conflicts with these artifacts; see `IR-25-FACTORIAL-STATE`.\n")
    A("**H30 engineering smoke test:** one real-data fold/draw built aligned 83-column train/test matrices and finite, nonempty H30 features; no model was fitted and no DTI was evaluated. Full diagnostics: `evidence/h30_feature_smoke.json`.\n")
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
    A("6. **The owner-claim-calibrated model has a scope limit (IR-25-LIVE-MODEL-SCOPE):** conditional on its reported-score anchors, it matches the H19-5 family and blind lattice within 0.004 DTI but under-predicts surfaces outside that band by up to 0.059; it is not an independent score estimate.")
    A("7. **The frozen holdout comparator is environment-specific (IR-25-COMPARATOR-DRIFT):** 0.152003389 recomputes to 0.149668 here. Any future gate must recompute its comparator in the same run.\n")
    A("## Next work (order matters)\n")
    if h30_confirm:
        if h30_confirm.get("confirmation_gate_passed"):
            A("1. H30-1 passed its fresh-draw proxy gate. This is still not a slot approval: any later full-data candidate must be newly built from the confirmed specification, beat the current comparable same-run spatial holdout best, and pass an exact-file audit. Do not submit automatically.")
        else:
            A("1. H30-1 failed its fresh-draw confirmation. Stop this candidate; do not create a TIFF or use a weekly slot. Any new idea requires a genuinely new preregistration.")
    elif h30_screen:
        if h30_screen.get("screen_gate_passed"):
            A("1. H30-1 screen passed. Run only the frozen confirmation on draws 8,9 (`.venv/bin/python scripts/run_h30_relay_factorial.py --stage confirm && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_confirm`). No TIFF or weekly slot before confirmation and the subsequent same-run/exact-file gates.")
        else:
            A("1. H30-1 screen failed its registered paired gate. Stop; do not run confirmation, create a TIFF, or use a weekly slot. Any follow-up needs a new preregistration.")
    else:
        A("1. Run the frozen H30-1 paired-relay screen on draws 6,7 (`.venv/bin/python scripts/run_h30_relay_factorial.py --stage screen && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_screen`). The runner saves the design before fitting and refuses to overwrite evidence.")
    A("2. Keep the prior five-family A–E Resolution V factorial separate: its complete `evidence/factorial/` record is present and was reproduced byte-for-byte; see `IR-25-FACTORIAL-STATE` for the handoff-state discrepancy. H30 is an additional hypothesis-specific 2², not a replacement.")
    A("3. Keep H26/H27/H29 outcomes and registrations labeled as prior work. H27-1 failed its gate; the old H29 list is registered already and must not be relabeled as novel.")
    A("4. Refresh the official-source/evidence tables and static site/feed (`scripts/check_sources.py`, then `scripts/build_site.py` and `scripts/build_readme.py`). The feed must never request or follow `drivendata.org`.")
    A("5. Keep the existing D2.8 download format-validated but unscored/not slot-approved. A passing H30 proxy gate is not a competition score, not confirmation until the fresh draw, and not authorization to upload.")
    A("6. Open a PR from the fixed Arena session branch, review the checks, and merge only through the GitHub PR workflow if permitted; never claim an unverified merge or deployment.\n")
    A("## Standing session charter\n")
    A("Read this README, both the verbatim owner brief and the current continuation brief below, then `AGENTS.md` at the start of every session. First commands: `git fetch origin`, compare with the fixed session branch, `gh pr list --state open`. Pre-register before fitting. No weekly slot unless the specific candidate beats the current comparable same-run holdout best and passes the exact-file audit; no exception is authorized here. Never automate `drivendata.org`. Review in three passes. Unknown stays unknown.\n")
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
      "# H28: metric-model calibration conditional on owner-reported anchors, inverse design, holdout factorial (knowledge/10)\n"
      ".venv/bin/python scripts/restore_artifacts.py                # fetch + hash the 30 owner-mirrored competition rasters -> registry/artifact_ledger.json\n"
      ".venv/bin/python scripts/run_h28.py                        # anchors, checks, ceiling sweep, designs, sensitivity (~7 min)\n"
      ".venv/bin/python scripts/run_h28.py --habitat-only          # the section 5 misspecification diagnostic (~10 min)\n"
      ".venv/bin/python scripts/run_h28_mixture.py                 # two-band mixture test (D3)\n"
      ".venv/bin/python scripts/run_h28_holdout.py && .venv/bin/python scripts/analyze_h28_holdout.py   # historical run; see evidence/h28_holdout/\n"
      "# H30-1 is an additional preregistered paired-tip × scarp 2²; it does not replace the five-family design\n"
      ".venv/bin/python scripts/smoke_h30_features.py                # real-data feature check only; no model fit/DTI\n"
      ".venv/bin/python scripts/run_h30_relay_factorial.py --stage screen && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_screen\n"
      "# ONLY if the saved screen results.json says screen_gate_passed=true:\n"
      ".venv/bin/python scripts/run_h30_relay_factorial.py --stage confirm && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_confirm\n"
      "# forensics and emission model\n"
      ".venv/bin/python scripts/analyze_scored_rasters.py && .venv/bin/python scripts/emission_model.py && .venv/bin/python scripts/validate_emission_model.py && .venv/bin/python scripts/harness_references.py\n"
      "# files, site, README\n"
      ".venv/bin/python scripts/build_candidate.py --help            # train on the full catalogue, emit, verify (exploratory surface)\n"
      ".venv/bin/python scripts/package_submissions.py --exploratory-receipt docs/downloads/checks-<file>.json\n"
      ".venv/bin/python scripts/build_data_dictionary.py && .venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py\n"
      ".venv/bin/python -m pytest -q && .venv/bin/python -m ruff check src scripts tests\n```\n")
    A("Set `GEMS_DATA_DIR` / `GEMS_WORK_DIR` to keep the 419 MB raster and the ~1.5 GB feature cache outside the checkout.\n")
    A("## Repository map\n")
    A("| Path | Role |\n|---|---|\n| `src/gems25/` | metric (official DTI + brute-force twin), hide-and-recover holdout, thinning/NMS, families & features, H30 relay/scarp add-ons, factorial engine, experiment cells, strict submission writer/checker |\n| `scripts/` | restore, build, run, analyse, package, site, README, feed, score recorder |\n| `registry/` | sources (with verification status), irregularities, score ledger, data pins, shipped submissions |\n| `evidence/` | machine-readable results and forensics |\n| `knowledge/` | pre-registrations, ranked hypotheses, verified research digest, the brief |\n| `docs/`, `index.html` | GitHub Pages site (root `index.html` is the landing page; Pages builds from `main:/`) |\n| `tests/` | unit, parity, integrity and reproduction tests |\n")
    A("## Owner brief (verbatim) — read every session\n")
    A("<details><summary><strong>Full text of the owner's brief for this session</strong> (copied from the task message of 2026-10-02; link markup and whitespace as pasted)</summary>\n")
    A("```text\n" + brief + "\n```\n")
    A("</details>\n")
    A("## Current continuation task (2026-10-03; consolidated restatement, not a verbatim quote)\n")
    A("The current user message was condensed into the session handoff. The full active scope and acceptance criteria are preserved below, separately from the verbatim 2026-10-02 brief.\n")
    A("<details><summary><strong>Full continuation brief and current constraints</strong></summary>\n")
    A("~~~text\n" + active_brief + "\n~~~\n")
    A("</details>\n")
    (ROOT / "README.md").write_text("\n".join(L))
    print("README.md written,", len("\n".join(L)), "chars")


if __name__ == "__main__":
    main()
