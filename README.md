# GEMSDOE25 — designed-factorial fault discovery for the DOE GEMS Prize

> **Maximize P(Win)** · **Own the Outcome** — the Arena core values are the decision rule for every change in this repository.

**Competition:** [DOE GEMS Prize, DrivenData #306](https://www.drivendata.org/competitions/306/competition-doe-gems/) · **Live site:** <https://buffedlizard55-lab.github.io/GEMSDOE25/> · **Weekly limit:** 3 submissions · **Ends:** 3 Dec 2026 (page: 11:59 p.m. UTC; rules: 5:00 p.m. ET — see IR-25-DEADLINE)

## ⬇ Download the format-validated GeoTIFF (not slot-approved)

**[↓ `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif`](docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif)** — Owner-mirrored H19-5 raster thinned by deterministic Poisson-disk dotting to 44,090 pixels (73% of the 0.2477-labelled mirror; 36% of H19-5). Conditional on unverified owner-reported score anchors, the H28 model estimates DTI 0.2510 and this file is its best point in the tested dot_thin(H19-5, d) sweep (d=1.8–4.0 px); this is a model output, not a competition score. The model-implied 12,691 truth count and 1.85-px concentration are fitted latent parameters, not verified hidden labels. This file is byte-identical to an owner-mirrored unscored alternate. It has not demonstrated a win over a comparable same-run holdout best and remains unscored/not slot-approved; the historical 0.152003389 comparator does not reproduce (IR-25-COMPARATOR-DRIFT).

* Format: single-band float32 GeoTIFF, EPSG:32611, 3730 × 3292, 100 m, values in [0, 1] at **all 5,167,373 footprint pixels**, NaN outside (verified against the pinned owner-mirror template, not organizer-authenticated; independent check receipt: `docs/downloads/checks-gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.json`).
* Unique content id `e56ea318af89` · SHA-256 `91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8` · 44,090 emitted pixels · status: **format-validated; unscored; not slot-approved**.
* **Note to paste** in DrivenData's *Note (optional)* field: `GEMSDOE25 D2.8 | H28 conditional model 0.251; not a score | unscored; not slot-approved | id e56ea318af89 | no slot`
* Format fallback (format troubleshooting only; not slot-approved): [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif`](docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) — Format fallback: same predictions, zeros outside the footprint (format fallback; unscored; not slot-approved; 44,090 px).
* Step-by-step upload guide: [`docs/executive-summary.html`](https://buffedlizard55-lab.github.io/GEMSDOE25/docs/executive-summary.html).

## Where things stand

* **Unverified leaderboard claims** (reported 2026-10-02; no organizer page or receipt was accessed): #1 DARD 0.3195; reported rank #5 0.2941. The group-best claim is **0.2477**; the previously reported rank #16/account association is not authenticated. These are not independently verified scores; apparent gaps to ranks #5/#1 are arithmetic on supplied claims only.
* **Root cause of the reported portal error** (`Predicted values must be in range [0, 1]`): the previous GEMSDOE25 file used an invented footprint — 2,344,929 of the 5,167,373 owner-mirror template-footprint pixels were NaN (NaN fails every range test) and it emitted 1,249,834 positive pixels. Fixed and tested (`evidence/old_gems25_tif_forensics.json`, `src/gems25/submission.py`). The cause is inferred from the data; the portal validator is not public.
* **Local audit of the reported 0.2477 raster (score unverified):** it is *exactly* `dot_thin(H19-5, 1.5)` — a pixel-identical deterministic subset (49.6 % of H19-5's pixels, none on a catalogue pixel). This verifies the raster transformation, not the claimed competition DTI. No organizer receipt/page was accessed; the claimed 0.2477 and 0.3195 remain unverified.
* **Model-only calibration:** if the supplied 0.2477 score claim is correct, the emission model predicts **0.2553** (band 0.2500–0.2613) for `dot_thin(H19-5, 2.4)` (44,090 px). This is an extrapolation conditional on owner/user-provided score anchors, not independent evidence or a score; any arithmetic against the unverified 0.3195 claim is conditional on both the claim and the selected model.
## H28 — metric-model calibration on 25 hash-linked owner-reported scores (claims not independently verified)

Pre-registered before any fit in [`knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md`](knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md). 30 competition rasters were fetched from the owner's public GitHub mirrors and content-hashed; **25 are tied to a reported DTI by SHA-256** (`registry/artifact_ledger.json`, `scripts/restore_artifacts.py`). Every DTI below labelled *reported* is a user/owner-reported claim, not a receipt; every value labelled *predicted* is conditional on the fitted model.

* **Conditional on the owner-reported anchors, a uniform-π truth model has no finite solution.** For `h19-5`, `h19-4`, `h16-1` and `d1-5` the closed-form inversion of the published DTI has **no solution** under a uniform truth: no truth count whatever reproduces their reported scores. Under `pi ∝ exp(-d(H19-5)/1.85 px)` all five anchors imply one truth count — lattice-s5 12,498, h19-5 12,472, h19-4 12,893, h16-1 13,358, d1-5 12,691 → **model-implied N̂ = 12,691** pixels in the hidden truth (max spread 5.3 %), which agrees with the blind-lattice-only estimate 12,348 and with this repo's earlier independent 12,503.
* **The fitted model matches selected owner-reported anchors conditionally; this is not score verification.** predicted vs reported: `lattice-s5` 0.0914 vs 0.0904; `h19-5` 0.1903 vs 0.1922; `d1-5` 0.2437 vs 0.2477. A Monte-Carlo run of the *published* metric on truth drawn from the fitted `pi` agrees with the analytic expectation to 0.0020 DTI (check C5).
* **What the 0.2477-labelled file changes locally (the score claim is unverified).** Dotting the solid `h19-5` surface throws away 50 % of its pixels but only 15 % of the credit it captured, and it cut redundant (overlapping-kernel) mass from 62 % to 32 % of captured kernel mass. Credit per emitted pixel rose 0.0520 → 0.0893; predicted DTI 0.1903 → 0.2437. The detected pixels did not change: the 0.2477-labelled mirror is a geometry-only transform of H19-5; the score-to-file claim remains unverified.
* **Modelled ceiling of that geometry: the file already shipped here.** Under the fitted π, sweeping `dot_thin(H19-5, d)` over d ∈ [1.8, 4.0] peaks at **d = 2.4 px, 44,090 px, predicted DTI 0.25104** — which *is* the D2.8 download. Value-ranked alternatives are worse: greedy-by-`pi*k` at 3 px peaks at 0.24622, and at 6 px (kernel-disjoint, zero redundancy) at 0.19332. The 6 px design beats `d1-5` in **0 of 9** cells of the (λ, N) sensitivity grid and the shipped D2.8 file in **0 of 9** (D2.8 dominates d1-5 in every cell: True): the redundancy theorem is true and irrelevant here, because for line-like truth the gaps between disjoint dots cost more credit than the overlap they save.
* **The hide-and-recover proxy agrees on held-out catalogue components.** A 30-arm factorial (value field × spacing × budget, 4 spatial folds × draws 0,1, one shared fit per cell — `evidence/h28_holdout/`): spacing 1.5→2.4 px **+0.0074**, 2.4→3.0 −0.0003, 3.0→4.0 −0.0112, 4.0→6.0 **−0.0350**; habitat-ranked dots add +0.0003 and habitat×score +0.0012 (best arm paired gain +0.000699, p = 0.248). **H28 gate: FAIL on paired gain** (+0.000699 ≤ +0.001); the historical absolute comparator did not reproduce (IR-25-COMPARATOR-DRIFT), so it is not a cross-draw baseline. No arm is slot-eligible and nothing new was packaged.
* **Conditional model calculation against the unverified 0.3195 claim.** At the selected model's 0.900 false-positive mass per emitted pixel, matching that claimed target at this file's budget would need **1.29×** its credit density (0.1400 vs 0.1084); reaching the reported #5 (0.2941) needs 1.18×. This is model-based sensitivity arithmetic, not a verified score comparison or proof that all emission changes are exhausted.
* **What the fitted model does not explain among owner-reported anchors.** A habitat model in distance-to-known-faults alone cannot explain the 25 reported score anchors (leave-one-artefact-out RMSE 0.0705 against a pre-registered 0.020 threshold; the blind lattice is predicted at 0.1386 instead of 0.0904) — its residuals are per-artefact detector skill. **"Hug the known-fault halo" is not a supported strategy.** A two-band mixture is not identified either (nine-anchor spread 0.514 vs a 0.053 threshold), so it was **not adopted** and nothing was designed from it.
* **Conditional model implication outside the calibration band.** If the owner-reported anchors and fitted model are correct, implied N suggests off-band truth on these surfaces: `h28-dotted-ridge` 28,989, `lidarscarp-top2pct` 22,893, `h25-ctx-ridge` 20,072 against 12,472–13,358 for the H19-5 family. Under this selected model, those three owner-mirrored surfaces require off-band truth to reconcile the reported anchors; that is a model implication, not evidence of the actual hidden labels. The GEMSDOE10 context ridge and the 7GEMSDOE LiDAR-scarp top-2 % emission remain H29 prioritization targets, not validated truth surfaces.
* **Reproducibility flag (IR-25-COMPARATOR-DRIFT).** The frozen comparator arm recomputes to 0.149667509 here against the frozen 0.152003389 (fold 0 identical to 9 decimals; folds 1–3 differ by up to 7.4e-03); this session's pipeline re-runs bit-for-bit, so the drift is environmental (`data/work` is a gitignored derived cache that was never hashed). `evidence/work_cache_hashes.json` now pins every derived cache and the library versions. **Absolute comparators do not transfer between environments; only same-run paired contrasts do.**


## Designed factorial experiment (replaces one-factor-at-a-time)

2^(5−1), Resolution V, generator E = ABCD → 16 runs × 8 spatially blocked hide-and-recover cells; response = exact sparse-regime DTI. Lenth ME = 0.0139. Pre-registered before the run (`knowledge/04_preregistered_factorial_2026-10-02.md`).

| Factor | Family | Class | Main effect (DTI) | Folds + |
|---|---|---|---|---|
| A | Potential-field gradients (gravity + magnetics) | **inert** | -0.0027 | 1/4 |
| B | DEM curvature / scarp (100 m DEM + 3DEP LiDAR descriptors) | **matters alone** | +0.0253 | 4/4 |
| C | Strain rate / seismicity | **inert** | -0.0109 | 0/4 |
| D | Thermal / geochemical (radiometrics, conductivity, GDR 1391 springs & wells) | **inert** | +0.0044 | 4/4 |
| E | Catalogue geometry (visible known faults only) | **matters alone** | +0.0610 | 4/4 |

Top interactions: `BC` -0.0050, `BD` -0.0049, `AC` +0.0045, `BE` -0.0043. Full tables: [`evidence/factorial/results.md`](evidence/factorial/results.md).

## Add-on hypotheses (pre-registered gate, paired)

| Arm | mean DTI | Δ vs base | folds + | gate |
|---|---|---|---|---|
| BASE `BDE` | 0.1359 | — | — | — |
| +ALL | 0.1410 | +0.0050 | 4/4 | pass |
| +X1 | 0.1365 | +0.0006 | 2/4 | fail |
| +X2 | 0.1375 | +0.0015 | 2/4 | fail |
| +X3 | 0.1362 | +0.0003 | 2/4 | fail |
| EM-0 score-ordered dots vs `dot_thin` (equal N≈12391) | 0.1382 vs 0.1345 | +0.0037 | 4/4 | pass |

## Confirmation replicate (fresh draws 2,3; pre-registered)

| Arm | mean DTI | Δ vs BDE | folds + | gate |
|---|---|---|---|---|
| BASE `BDE` | 0.1305 | — | — | — |
| +ALL | 0.1343 | +0.0038 | 4/4 | pass |
| +X1 | 0.1331 | +0.0026 | 4/4 | pass |
| +X2 | 0.1338 | +0.0033 | 3/4 | pass |
| +X3 | 0.1338 | +0.0032 | 4/4 | pass |
| CFG_ABCDE | 0.1279 | -0.0027 | 2/4 | fail |
| CFG_BE | 0.1332 | +0.0027 | 3/4 | pass |
| CFG_E | 0.1098 | -0.0207 | 0/4 | fail |
| EM-0 score-ordered dots vs `dot_thin` | 0.1329 vs 0.1294 | +0.0034 | 4/4 | pass |

`CFG_*` rows are whole family sets (e.g. `CFG_BE` = the factorial's predicted-best corner, which did not replicate its predicted 0.145).

## Score ledger — user/owner-reported claims (not organizer-verified; full ledger in `registry/live_scores.json`)

| Project | Submission | Score | Note |
|---|---|---|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | reported score 0.2477; local mask identity is verified, leaderboard/receipt association is not |
| 19GEMSDOE | `h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan` | 0.1922 | parent of the 0.2477 file |
| 19GEMSDOE | `h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan` | 0.1894 |  |
| GEMSDOE21 | `h19-4-reference-20260930-691e4dfa` | 0.1894 | re-host of h19-4 (same content id 691e4dfa) |
| 20GEMSDOE | `h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan` | 0.1890 |  |
| 16GEMSDOE | `h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan` | 0.1855 |  |
| GEMSDOE10 | `h28-dotted-ridge-20260928T020256236880Z-6452ae1d00` | 0.1839 | dotted version of the surface above: +44 % |
| GEMSDOE | `gems-submission-20260925T001403Z-7f00890a` | 0.1563 |  |
| 5GEMSDOE | `gems-submission-20260926T175114Z-7f00890a` | 0.1563 | same content id 7f00890a as the GEMSDOE entry |
| 8GEMSDOE | `Hedge-v2_submission` | 0.1563 | = ens12 off-catalogue pixels + all catalogue pixels; equal score shows masked known pixels do not matter |

## Prior H26 register — outcomes (ranked before its runs; not a list of untried work)

| Rank | ID | Idea | Recorded outcome |
|---|---|---|---|
| 1 | H26-0 | score-aware Poisson-disk dotting + marginal-ratio budget | **passes** (+0.0037 vs score-blind dotting at equal N, 4/4 folds, replicated +0.0034) |
| 2 | H26-2 | strike-compatibility prior (DEM line orientation × visible-catalogue strike) | alone: fail on draws 0,1 (+0.0015, 2/4), small pass on fresh draws 2,3 (+0.0033, 3/4); jointly passes both |
| 3 | H26-1 | oriented cross-scarp radiometric contrast (K, Th/K, U/K × DEM normal) | alone: fail on draws 0,1 (+0.0006, 2/4), small pass on draws 2,3 (+0.0026, 4/4); jointly passes both |
| 4 | H26-3 | concealed joint step (gravity ∧ magnetic ridge, basement-depth step) | alone: fail on draws 0,1 (+0.0003, 2/4), small pass on draws 2,3 (+0.0032, 4/4); jointly passes both |
| 5 | H26-4 | dilation-tendency-weighted orientation prior (USGS 10.5066/P9YL58W6) | page-listed shapefile; direct access failed, bytes/licence not verified |

## Prior registered geological screen (H27; not a current untried candidate; full design in `knowledge/09_preregistered_hypotheses_2026-10-02.md`)

| Rank | ID | Idea | Expected proxy ΔDTI (planning bracket) | Status |
|---|---|---|---|---|
| 1 | H27-1 | directed visible-fault-tip continuation × multi-scale DEM/LiDAR scarp | +0.001 to +0.010 | TS DTI 0.151064; screen failed; stop, no slot |
| 2 | H27-2 | residualized GDR 2 m temperature probes | 0 to +0.010 | blocked: binary/schema/coverage not fetched |
| 3 | H27-3 | paleo-geothermal deposits away from visible traces | 0 to +0.005 | blocked: binary/schema/coverage not fetched |
| 4 | H27-4 | USGS heat-flow residual × structural/scarp support | 0 to +0.005 | blocked: binary, residual definition and licence not verified |

These ΔDTI ranges are planning judgments, not estimates. H27-1 failed its registered historical gate; the numbers are not a current cross-draw threshold.

## Current ranked geological hypotheses (H30; full signatures, novelty, sources, costs and gate in `knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md`)

| Rank | ID | Idea | Expected proxy ΔDTI (planning bracket) | Status |
|---|---|---|---|---|
| 1 | H30-1 | paired visible-tip cross-strike bridge × LiDAR scarp persistence | +0.001 to +0.008 | P+S DTI 0.151567, paired gain +0.004078; screen passed; confirmation draws 8,9 required |
| 2 | H30-2 | visible-fault junction / accommodation-zone branch field | 0 to +0.006 | registered only; not fitted |
| 3 | H30-3 | scale-persistent terrain lineament | 0 to +0.005 | registered only; not fitted |

Planning brackets are uncertain prioritization judgments, not estimates or live-score forecasts. H30-1 screen draws are 6,7; confirmation draws 8,9 are allowed only after a screen pass. Even confirmation is only proxy evidence and cannot grant slot approval by itself.

**Five-family factorial status:** the separate A–E Resolution V design is preserved in `evidence/factorial/`: 16 randomized design rows × 8 cells = 128 model cells, plus 24 reference cells (152 cell rows total). Its analyzer reproduced the tracked results byte-for-byte on 2026-10-03. H30 is additional, not a substitute. The handoff's 'unrun' note conflicts with these artifacts; see `IR-25-FACTORIAL-STATE`.

**H30 engineering smoke test:** one real-data fold/draw built aligned 83-column train/test matrices and finite, nonempty H30 features; no model was fitted and no DTI was evaluated. Full diagnostics: `evidence/h30_feature_smoke.json`.

## Flagged for review (full list with evidence: [`registry/irregularities.json`](registry/irregularities.json))

* **IR-25-NAN-FOOTPRINT** (critical, fixed) — The first GEMSDOE25 'recommended' submission (gems25-factorial-best-v1-nan.tif, sha256 fbef100f...) used an invented footprint: 2,344,929 of the 5,167,373 pixels in the pinned owner-mirror template footprint are NaN and 2,832,257 pixels outside it are finite. …
* **IR-25-OVER-EMISSION** (critical, fixed) — The same file emitted 1,249,834 positive pixels (624,029 inside the footprint = 12.1 % of it; 625,805 outside it), roughly 10x the 2.34 % budget of H19-5 and 21x the dotted file's 60,069 pixels. At the measured truth density the false-positive term would swamp…
* **IR-25-FAKE-PIPELINE** (high, fixed) — Previous scripts were non-functional or misleading: generate_submission.py wrote synthetic diagonal stripes inside an elliptical made-up footprint; ridge_detector.py was a toy; factorial_design.py never ran (no data); the README listed src/feature_families.py,…
* **IR-25-DTI-KERNEL** (high, fixed) — The old scripts/dti_metric.py used kernel 1 - d/(R+0.5) with R = 3 px (support 3.5 px). The official kernel is max(1 - d/R, 0) with R = 300 m = 3 px.
* **IR-25-TC-BAND** (high, flagged) — Band 6 'tc' of the mirrored training_features.tif is described as 'Tilt angle or total curvature - magnetic field derivative for edge detection', but its values (3.7-70.6, positive) equal the official GeoDAWN radiometric total count channel: Spearman 0.9999 ag…
* **IR-25-PROVENANCE** (high, open) — Every competition raster here is an owner mirror (hash-pinned), not organizer-authenticated; the DrivenData data page is login-walled and the Dropbox links in the brief are unreachable from the sandbox, so byte-identity with the originals is not verified.
* **IR-25-PROXY-LIMITS** (high, disclosed) — The hide-and-recover holdout is a catalogue-gap proxy (hidden = catalogue components), not new-fault truth. H19-5 'as emitted' is not out-of-fold (and masked all catalogue pixels), so it is only a diagnostic. Family E may be flattered by the simulation. GEMSDO…
* **IR-25-PAGES-ROOT** (high, fixed) — GitHub Pages is built from main:/ (legacy), but the old site lived in docs/ with no root index.html: the public URL served the README, whose 'Executive Summary & Submit Guide' link pointed back to itself and whose download link was the broken file.
* **IR-25-COMPARATOR-DRIFT** (high, open) — The frozen hide-and-recover comparator 0.15200338908786984 (evidence/addons/emk_extension.json, variant sapd2.4 at kfrac 0.035, base BDE + the seven add-ons, draws 0-1) does NOT reproduce in this environment. Re-running that exact arm here gives 0.149667509 (f…

## Limitations and what is needed

1. **No competition credentials or organizer receipts.** Every competition raster is an owner mirror (hash-pinned, not organizer-authenticated). The 0.2477 result and 0.3195 leader are user-provided, unverified claims; no competition/leaderboard page was accessed. Do not automate or monitor DrivenData.
2. **External binaries are blocked here:** GDR 1391 lists the 2 m probe and paleo-geothermal files under CC BY 4.0, but direct downloads failed; the USGS heat-flow ZIP is page-listed, but its bytes and licence were not verified. H27-2/3/4 require a networked runner and source/coverage checks before use.
3. **Compute:** 2 CPUs / 4 GB RAM, no GPU → boosted trees, not the reference U-Net; no raw 1 m DEM processing. The H27 screen ran in about 14 minutes after the feature cache was built.
4. **The proxy is not the truth:** the hide-and-recover holdout hides catalogue components; proxy-vs-live correlation in the group's prior record was weak (Spearman +0.33, n = 24, n.s.). Holdout wins are necessary, not sufficient.
5. **Hidden labels, public/private split, source authenticity, score claims and the portal validator remain undisclosed/unverified.**
6. **The owner-claim-calibrated model has a scope limit (IR-25-LIVE-MODEL-SCOPE):** conditional on its reported-score anchors, it matches the H19-5 family and blind lattice within 0.004 DTI but under-predicts surfaces outside that band by up to 0.059; it is not an independent score estimate.
7. **The frozen holdout comparator is environment-specific (IR-25-COMPARATOR-DRIFT):** 0.152003389 recomputes to 0.149668 here. Any future gate must recompute its comparator in the same run.

## Next work (order matters)

1. H30-1 screen passed. First commit the complete screen evidence (`evidence/h30_relay_screen/`) so the confirmation runner starts from a clean, auditable tree; it rechecks the raw-cell hashes and recomputes the gate. Then run only the frozen confirmation on draws 8,9 (`.venv/bin/python scripts/run_h30_relay_factorial.py --stage confirm && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_confirm`). No TIFF or weekly slot before confirmation and the subsequent same-run/exact-file gates.
2. Keep the prior five-family A–E Resolution V factorial separate: its complete `evidence/factorial/` record is present and was reproduced byte-for-byte; see `IR-25-FACTORIAL-STATE` for the handoff-state discrepancy. H30 is an additional hypothesis-specific 2², not a replacement.
3. Keep H26/H27/H29 outcomes and registrations labeled as prior work. H27-1 failed its gate; the old H29 list is registered already and must not be relabeled as novel.
4. Refresh the official-source/evidence tables and static site/feed (`scripts/check_sources.py`, then `scripts/build_site.py` and `scripts/build_readme.py`). The feed must never request or follow `drivendata.org`.
5. Keep the existing D2.8 download format-validated but unscored/not slot-approved. A passing H30 proxy gate is not a competition score, not confirmation until the fresh draw, and not authorization to upload.
6. Open a PR from the fixed Arena session branch, review the checks, and merge only through the GitHub PR workflow if permitted; never claim an unverified merge or deployment.

## Standing session charter

Read this README, both the verbatim owner brief and the current continuation brief below, then `AGENTS.md` at the start of every session. First commands: `git fetch origin`, compare with the fixed session branch, `gh pr list --state open`. Pre-register before fitting. No weekly slot unless the specific candidate beats the current comparable same-run holdout best and passes the exact-file audit; no exception is authorized here. Never automate `drivendata.org`. Review in three passes. Unknown stays unknown.

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group all          # SHA-256-pinned inputs from the owner's public repos -> data/ (ignored by Git); same as: bash scripts/download_competition_data.sh
.venv/bin/python scripts/build_features.py && .venv/bin/python scripts/build_addons.py
# pre-registered experiments (knowledge/04, 05)
.venv/bin/python scripts/run_factorial.py && .venv/bin/python scripts/analyze_factorial.py            # ~30 min on 2 CPUs
.venv/bin/python scripts/run_addons.py && .venv/bin/python scripts/analyze_addons.py                  # draws 0,1
.venv/bin/python scripts/run_addons.py --out evidence/addons_confirm --draws 2 3 --extra-configs ABCDE BE E && .venv/bin/python scripts/analyze_addons.py --dir evidence/addons_confirm
.venv/bin/python scripts/run_emk_extension.py --base BDE --extras X1_K X1_ThK X1_UK X2_compat X2_compat_coh X3_gm X3_gd   # post hoc (Addendum A)
# H27-1 frozen 2x2 screen (knowledge/09); confirmation is permitted only if screen gate passes
.venv/bin/python scripts/run_h27.py --stage screen && .venv/bin/python scripts/analyze_h27.py --dir evidence/h27_screen
# if and only if the screen's absolute + paired gates pass:
.venv/bin/python scripts/run_h27.py --stage confirm && .venv/bin/python scripts/analyze_h27.py --dir evidence/h27_confirm
# H28: metric-model calibration conditional on owner-reported anchors, inverse design, holdout factorial (knowledge/10)
.venv/bin/python scripts/restore_artifacts.py                # fetch + hash the 30 owner-mirrored competition rasters -> registry/artifact_ledger.json
.venv/bin/python scripts/run_h28.py                        # anchors, checks, ceiling sweep, designs, sensitivity (~7 min)
.venv/bin/python scripts/run_h28.py --habitat-only          # the section 5 misspecification diagnostic (~10 min)
.venv/bin/python scripts/run_h28_mixture.py                 # two-band mixture test (D3)
.venv/bin/python scripts/run_h28_holdout.py && .venv/bin/python scripts/analyze_h28_holdout.py   # historical run; see evidence/h28_holdout/
# H30-1 is an additional preregistered paired-tip × scarp 2²; it does not replace the five-family design
.venv/bin/python scripts/smoke_h30_features.py                # real-data feature check only; no model fit/DTI
.venv/bin/python scripts/run_h30_relay_factorial.py --stage screen && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_screen
# Commit the screen evidence; the runner requires a clean tree and revalidates its hashes/gate.
git add evidence/h30_relay_screen && git commit -m 'Record H30 screen evidence'
# ONLY if the saved screen results.json says screen_gate_passed=true:
.venv/bin/python scripts/run_h30_relay_factorial.py --stage confirm && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_confirm
# forensics and emission model
.venv/bin/python scripts/analyze_scored_rasters.py && .venv/bin/python scripts/emission_model.py && .venv/bin/python scripts/validate_emission_model.py && .venv/bin/python scripts/harness_references.py
# files, site, README
.venv/bin/python scripts/build_candidate.py --help            # train on the full catalogue, emit, verify (exploratory surface)
.venv/bin/python scripts/package_submissions.py --exploratory-receipt docs/downloads/checks-<file>.json
.venv/bin/python scripts/build_data_dictionary.py && .venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q && .venv/bin/python -m ruff check src scripts tests
```

Set `GEMS_DATA_DIR` / `GEMS_WORK_DIR` to keep the 419 MB raster and the ~1.5 GB feature cache outside the checkout.

## Repository map

| Path | Role |
|---|---|
| `src/gems25/` | metric (official DTI + brute-force twin), hide-and-recover holdout, thinning/NMS, families & features, H30 relay/scarp add-ons, factorial engine, experiment cells, strict submission writer/checker |
| `scripts/` | restore, build, run, analyse, package, site, README, feed, score recorder |
| `registry/` | sources (with verification status), irregularities, score ledger, data pins, shipped submissions |
| `evidence/` | machine-readable results and forensics |
| `knowledge/` | pre-registrations, ranked hypotheses, verified research digest, the brief |
| `docs/`, `index.html` | GitHub Pages site (root `index.html` is the landing page; Pages builds from `main:/`) |
| `tests/` | unit, parity, integrity and reproduction tests |

## Owner brief (verbatim) — read every session

<details><summary><strong>Full text of the owner's brief for this session</strong> (copied from the task message of 2026-10-02; link markup and whitespace as pasted)</summary>

```text
Review the repo.   
  
There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  
  
Replace one-factor-at-a-time testing with a designed factorial experiment. The repo's own hypothesis history — single-named attempts like "conj_alteration_mag," "dem10-scarp," "topo-geophys-x-complexity-prior" — reads as classical one-factor-at-a-time testing, a documented methodological weakness: Box, Hunter, and Hunter's foundational Statistics for Experimenters shows why holding other factors fixed while varying one at a time systematically misses interaction effects — cases where two features are each weak alone but jointly diagnostic because the real signature is their conjunction, not either one's sum — and the name "conj_alteration_mag" is already gesturing at exactly this without treating it as a designed experiment. Replace the ad hoc sequence with a fractional factorial design across the candidate feature families already identified (potential-field gradients, DEM curvature/scarp, strain/seismicity, thermal/geochemical, catalogue-geometry), run against the hide-and-recover holdout, which estimates every family's main effect on DTI alongside its pairwise interactions in a modest, pre-specified number of runs — far fewer than testing every combination in full — rather than an open-ended sequence of hunches; the sparsity-of-effects principle this literature establishes, that real systems are typically dominated by a few main effects and low-order interactions rather than many high-order ones, means this is enough to rank which families matter alone, which only matter in combination, and which are inert — redirected by evidence, not by which conjunction sounds geologically plausible.  
  
Here are the results from submissions into the competition, separated by ....:  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html))  
  
gems-submission-20260925T001403Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)](https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/))  
  
gems6_hgb88-topk03_33cec71ff0: 0.0286  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html))  
  
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193  
  
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830  
  
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html))  
  
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)](https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/))  
  
gems-submission-20260926T163915Z-237f0063: 0.0343  
  
....  
  
[[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html))  
  
gems-submission-20260926T175114Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)](https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/))  
  
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461  
  
....  
  
[[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)](https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/))  
  
Hedge-v2_submission: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html))  
  
2314b599: 0.0107  
  
....  
  
[[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html))  
  
gems-structural-area06-v1: 0.0202  
  
....  
  
[[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html))  
  
r7-nms3-dem10-scarp_0c9199f14e62:0.1294  
  
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294  
  
....  
  
[[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html))  
  
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782  
  
....  
  
[[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html))  
  
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020  
  
....  
  
[[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)](https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/))  
  
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187  
  
....  
  
[[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)](https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/))  
  
H19-C_20260930T212401Z_c11e495e: 0.0297  
  
....  
  
[[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html))  
  
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894  
  
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)](https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/))  
  
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461  
  
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921  
  
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280  
  
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839  
  
....  
  
[[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)](https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/))  
  
20261001_r13-lattice-s5_v2_nan-outside:0.0904  
  
....  
  
[[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html))  
  
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855  
  
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976  
  
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)](https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/))  
  
h19-4-reference-20260930-691e4dfa: 0.1894  
  
....  
  
[[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html))  
  
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890  
  
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html))  
  
h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002  
  
h23-b-dti-optimal-emission-10pct-20261002-86176698-nan:   
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)](https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/))  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)](https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/))  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
....  
  
25GEMSDOE SCORE:  
  
....  
  
26GEMSDOE SCORE:  
  
....  
  
27GEMSDOE SCORE:  
  
....  
  
WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:  
  
24GEMSDOE SCORE:  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2477?  
  
Answer the question using Phd level experience, knowledge, and judgement.   
  
The following is the leaderboard for the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/))  
  
   
  
We need to quickly look at the results and results from the GEMSDOE websites above.  
  
Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.  
  
The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.  
  
   
  
[[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html))  
  
gems-submission-20260925T001403Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)](https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/))  
  
gems6_hgb88-topk03_33cec71ff0: 0.0286  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html))  
  
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193  
  
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830  
  
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html))  
  
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)](https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/))  
  
gems-submission-20260926T163915Z-237f0063: 0.0343  
  
....  
  
[[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html))  
  
gems-submission-20260926T175114Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)](https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/))  
  
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461  
  
....  
  
[[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)](https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/))  
  
Hedge-v2_submission: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html))  
  
2314b599: 0.0107  
  
....  
  
[[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html))  
  
gems-structural-area06-v1: 0.0202  
  
....  
  
[[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html))  
  
r7-nms3-dem10-scarp_0c9199f14e62:0.1294  
  
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294  
  
....  
  
[[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html))  
  
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782  
  
....  
  
[[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html))  
  
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020  
  
....  
  
[[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)](https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/))  
  
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187  
  
....  
  
[[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)](https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/))  
  
H19-C_20260930T212401Z_c11e495e: 0.0297  
  
....  
  
[[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html))  
  
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894  
  
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)](https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/))  
  
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461  
  
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921  
  
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280  
  
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839  
  
....  
  
[[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)](https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/))  
  
20261001_r13-lattice-s5_v2_nan-outside:0.0904  
  
....  
  
[[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html))  
  
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855  
  
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976  
  
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)](https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/))  
  
h19-4-reference-20260930-691e4dfa: 0.1894  
  
....  
  
[[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html))  
  
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890  
  
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html))  
  
h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002  
  
h23-b-dti-optimal-emission-10pct-20261002-86176698-nan:   
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)](https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/))  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)](https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/))  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
....  
  
25GEMSDOE SCORE:  
  
....  
  
26GEMSDOE SCORE:  
  
....  
  
27GEMSDOE SCORE:  
  
....  
    
  
WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:  
  
24GEMSDOE SCORE:  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2477?  
  
Answer the question using Phd level experience, knowledge, and judgement.   
  
The following is the leaderboard for the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/))  
  
0.3195	is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.    
  
Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.  
  
Review the repo.   
  
The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.  
  
Our Core Values  
  
Maximize P(Win)  
  
“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.  
  
Own the Outcome  
  
We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
    
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
We need to focus on being able to generate a submission into the competition.    
  
The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.  
  
I tried to submit the document that i downloaded from the site but it returned this error on the submission form:  
  
"Predicted values must be in range [0, 1]"  
  
Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25  
  
Here is the submission page when i click submit file  
  
New submission  
  
File to submitNo file chosen  
  
You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.  
  
Note (optional)  
  
A short comment to help you or your team tell submissions apart later e.g. clustering with k=25  
  
Create a executive summary subpage that explains exactly how to make a submission into the contest.  
  
Work on the next steps from the previous sessions first.  
  
The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/))  
  
We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.    
  
This is the guidelines we need to follow.[[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)](https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/))  
  
Get familiar with the problem through the overview and problem description,[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)). You might also want to reference additional resources available on the about page,[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)).  
  
Download the data from the data,[[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)), tab.    
  
Create and train your own model. This reference solution,[[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)](https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)) implements a simple approach.  
  
Use your model to generate predictions that match the submission format.  
  
Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.    
  
this pdf outlines how submissions must be entered into the competition.    
  
[[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)](https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf))  
  
You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.  
  
❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)) (verified redirect to login)  
  
See below for links from the above site.  See attached files for links from the above site.  
  
[[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)](https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391))  
  
Download competition data from [[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)) (requires login) to data/  
  
See links below for competition data:  
  
[[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;amp;st=wz4kofki&amp;amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0)](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0))  
  
[[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;amp;st=8junzdyw&amp;amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0)](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0))  
  
[[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;amp;st=rnino7ya&amp;amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0)](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0))  
  
[[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;amp;st=zj1lag1r&amp;amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0)](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0))  
  
[[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;amp;st=srhhir10&amp;amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0)](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0))  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
Site creation  
  
Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.    
  
It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.  
  
**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).  
  
you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
Run this task through multiple passes.  
  
Pass 1: Implement the task completely and verify the result.  
  
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.  
  
Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.  
  
Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.  
  
Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.
```

</details>

## Current continuation task (2026-10-03; consolidated restatement, not a verbatim quote)

The current user message was condensed into the session handoff. The full active scope and acceptance criteria are preserved below, separately from the verbatim 2026-10-02 brief.

<details><summary><strong>Full continuation brief and current constraints</strong></summary>

~~~text
# Active project brief — continuation task (2026-10-03)

> **Status of this transcription:** the exact current user message was condensed into a session handoff before this continuation. This file preserves its full active task and acceptance criteria as received in that handoff; it is a faithful consolidated restatement, **not a verbatim quotation**. The earlier 2026-10-02 message remains separately preserved as `owner_brief_verbatim.txt`.

## Objective and decision principles

Continue the GEMSDOE25 project toward a higher-scoring DOE GEMS Prize submission. Apply **Maximize P(Win)** and **Own the Outcome**: spend effort on verifiable scientific leverage, resolve data/engineering blockers autonomously, and report negative results. Treat the reported 0.2477 result and the stated 0.3195 leaderboard target as user/owner-reported claims unless official evidence is independently accessed; do not imply that either is verified.

## Scientific work and experimental design

- Review the full standing README/brief and repository history each session. Study prior evidence before proposing work; do not relabel earlier H26/H27/H28/H29 hypotheses or runs as new experiments.
- Move beyond one-factor-at-a-time testing. The completed historical design is a preregistered 2^(5−1), Resolution V fractional factorial across the five existing families: potential-field gradients, DEM curvature/scarp, strain/seismicity, thermal/geochemical, and catalogue geometry. It estimates main effects and pairwise interactions on the spatially blocked hide-and-recover holdout; its recorded results are prior work, not new evidence.
- Before implementing a new geological candidate, propose and rank **3–5 genuinely untried hypotheses**. For each, state the layers, physical signature, rationale for finding faults missing from the catalogue, how it differs from prior repository work, expected holdout DTI gain as an explicitly uncertain planning bracket, cost, and data/validation status.
- Verify each source claim from the cited official or primary source, line by line where relevant. If a candidate needs new external data, verify that the free official source and required data are actually obtainable before calling the candidate viable. A page listing is not proof that a binary, schema, coverage, or licence has been checked.
- Preregister the design, folds/draws, model, response, analysis, and promotion gate before fitting. Do not tune after seeing outcomes. Use spatially blocked hide-and-recover holdout, report main effects and pairwise interactions, and distinguish proxy evidence from competition performance.
- Validate the top candidate before creating a new submission artifact or considering a weekly submission slot. The candidate must beat the best *comparable same-run* spatial holdout control, pass the preregistered paired/confirmation gate, and pass an exact-file audit. A prior frozen comparator that does not reproduce is not a valid cross-run threshold. A screen pass alone is not confirmation.

## Submission artifact and site

- Keep the format-validated GeoTIFF easy to find and download from the site/README. Verify the competition template's dimensions, CRS, geotransform, valid footprint, and `[0,1]` value range. Each new file must have a unique content-addressed filename, SHA-256 receipt, and concise submission note.
- Do not create, label, or promote a new candidate unless the registered holdout gate passes. Do not spend a weekly submission slot on an unvalidated candidate.
- Preserve the concise executive-summary/how-to-submit guide, with manual-only upload instructions and clear status labels. The site and source/feed pages must be useful, current, and link to manually reviewable official sources.

## Data, evidence, and communication rules

- No automated access, monitoring, scraping, or submission to `drivendata.org`; the repository's `AGENTS.md` and DrivenData Terms policy prohibit it. Do not use DrivenData authentication. Hash-pinned owner mirrors are owner-supplied bytes, not organizer-authenticated files.
- Keep OFFICIAL source statements, owner/user-reported score claims, locally COMPUTED measurements, and INFERENCE clearly separate. Unknown stays unknown. Flag inconsistencies, stale links, data/schema/licensing gaps, comparator drift, and other irregularities rather than silently resolving them.
- Prefer free public official sources for third-party data. Provide direct links and enough provenance for manual review. Do not commit large restored datasets or caches; use the repository's ignored/external-data conventions.
- Keep current, auditable source/evidence tables, data manifest, score claims and artifact ledger. Update the README and site only from evidence that is actually present and verified.

## Autonomous execution and quality gates

Work autonomously; do not ask the owner for manual inputs or credentials. Before finishing, complete three cumulative review passes: (1) implement and verify against sources and the registered design; (2) inspect bugs, assumptions, leakage risks, and edge cases, then fix them; (3) re-check the full result against this brief and the original request. Record the passes in `registry/review_passes.json`.

Prepare a PR from the fixed Arena session branch and merge only through the repository's PR workflow if checks and authentication permit. Never claim a PR, merge, deployment, or score verification unless a URL/status/receipt proves it. Report limitations, remaining work, and any access that is genuinely needed without requesting secrets.

## Existing facts that constrain this continuation

- `data/` was initially empty; project inputs may be restored only from hash-pinned public owner mirrors or verified official sources, never by automating competition access.
- The previous H28 holdout's frozen comparator reproduction failed. Its nominal best arm was not slot-eligible.
- The H27-1 combined tip/scarp arm failed its registered absolute comparator gate; its T-only screen was unconfirmed and is not slot-eligible.
- Existing H26 factorial, add-on, emission, and H29 next-hypothesis registers are prior work and must be reviewed for overlap.
- Existing downloadable D2.8 files are format-validated, unscored/owner-mirror artifacts and are not approved for a weekly slot.
- **State discrepancy:** the condensed handoff says the five-family factorial remains unrun, while the tracked `evidence/factorial/` contains 16 model rows × 8 cells, reference rows, and complete analysis. `scripts/analyze_factorial.py` reproduced its results byte-for-byte on 2026-10-03. This evidence and the mismatch are recorded as `IR-25-FACTORIAL-STATE`; do not overwrite or rerun the old experiment just to resolve a wording conflict. H30 is explicitly additional, not a replacement.
~~~

</details>
