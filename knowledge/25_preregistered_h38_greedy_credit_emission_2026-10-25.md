# 25 · Five ranked untried hypotheses + pre-registration H38 (2026-10-25)

Written and committed **before any H38 fit**. Novelty checked against this repo's
registers (knowledge/03 H26, /09 H27, /10 H28, /11–12 H30, /13–15 H31/GEM,
/17 KDC design, /18 H34 list, /19 H35, /21 XG1/H36/CF-1, /22–24 H37/XG1 outcomes)
and the nine focus sites named in the brief (GEMSDOE24, 25, 27, 28, 30, 31, 32,
33, 36). Every competition score cited is **OWNER-reported** unless labelled
**HOLDOUT-DTI** (`gems25.metric.dti_binary`, α=0.2, β=0.8, R=3 px). No number
here is ORGANIZER-CONFIRMED. Expected-Δ values are planning brackets, not forecasts.

## Why H33-2-B2 scored highest (the brief's question, answered before designing)

The chain is pixel-exact in this repo (COMPUTED, `evidence/focus_sites_forensics.json`,
re-verified session 7 in `evidence/h37_b2_recheck.json`, re-run this session):
H19-5 solid (121,131 px, OWNER 0.1922) → `dot_thin` 1.5 px (60,069, OWNER 0.2477)
→ dot 2.8 px **D2.8** (44,090, OWNER 0.2600) → delete dots ≤1 px from the
catalogue **B1** (40,199, OWNER 0.2708) → delete dots ≤2 px **B2** (37,654,
OWNER 0.2778); GEMSDOE36 = B2 + exactly 1,200 dots (OWNER 0.2750, lower).
Mechanism: the metric credits each truth pixel with the **maximum** triangular
kernel over nearby dots, so a redundant dot adds ≈0 credit but ≈1 unit of FP
mass charged at α=0.2. A dot pays for itself iff ΔTP/ΔFP > α·D/(1−α·D)
(= 0.0588 at D=0.2778, `gems25.metric.marginal_inclusion_ratio`). Inverting the
OWNER steps, the deleted 0–1 px and 1–2 px shells earned ≈0.001 and ≈0.005
credit/px — an order of magnitude below break-even. **The 0.2778 file therefore
won on emission economics (removing mass the scorer does not pay for), not on
new geological detection.** Beating it by +0.01 at fixed mass needs ≈+4 %
weighted credit; the brief's 0.3195 needs ≈+15 % and 0.4413 ≈+59 % (the two
leaderboard claims conflict, IR-25-LEADERBOARD-CONFLICT). Six sessions of
adding feature *columns* to the incumbent detector moved HOLDOUT-DTI by at most
±0.004 (H34/H35/XG1/H36/H37/CF-1). This session therefore changes the **decision
rule** (which dots to buy with the FP budget) and adds the missing
**off-catalogue instrument** needed to test B2-style pruning at all
(IR-25-HOLDOUT-DOES-NOT-TEST-PRUNING), instead of adding more columns.

## The single lane for this session (PARALLEL-RUN PROTOCOL item 1)

> **H38 — DTI-exact marginal-credit (greedy submodular) emission.** Keep the
> validated H35 detector surface bit-for-bit (BDE+7 + directed tip + 3 H34
> columns, `Cell(extras=True, h27=True)`, HGB seed=draw) and replace only the
> emission rule. From the *same* top-K ridge-candidate pool the control uses
> (ridge NMS σ=1.0, kfrac 0.035 of the eroded domain, catalogue pixels
> excluded), select dots one at a time by exact incremental triangular-kernel
> accounting against a plug-in truth density p̂ ∝ the detector surface
> (normalised so Σp̂ = N̂, N̂ = hide_frac/(1−hide_frac)·|visible catalogue in
> domain|): at each step take the candidate maximising ΔTP̂/ΔFP̂, where
> ΔTP̂ = Σ_g p̂_g·max(0, k(d_xg) − cur_g) with cur_g the current maximum kernel
> coverage, and ΔFP̂ = 1 − E[max_g k(d_xg)·Bern(p̂_g)] under spatial
> independence (exact sum over the ≤29 kernel neighbours). Stop when the best
> ratio no longer exceeds τ(D̂) = α·D̂/(1−α·D̂) at the running plug-in
> D̂ = TP̂/(0.2(TP̂+FP̂)+0.8N̂). No fixed dot count, no fixed spacing: dense
> where expected credit is dense, absent where it is not. Control A0 is the
> identical surface with the incumbent emission (score-ordered Poisson dots,
> 2.4 px), so the paired contrast is *purely* the selection rule.

**Non-fault process that could mimic the signal (named in advance):** none new
geologically — H38 inherits the H35 detector's mimics (lithologic/intrusive
contacts and basin-margin pinch-outs that step magnetics/depth without
faulting). The lane-specific failure mode is statistical: p̂ is the detector's
own uncalibrated score, so greedy selection can amplify the detector's
systematic errors (it spends most where the surface is most confident, right
or wrong) and the independence approximation for ΔFP̂ understates FP along
continuous false lineaments (roads, flight-line levelling, fan-lobe edges),
where neighbouring "truth" events are in reality perfectly correlated.

## Five candidate hypotheses, ranked (expected HOLDOUT-DTI gain ÷ cost)

| Rank | ID | Layer(s) → physical signature | Why a catalogue-*missing* fault, not a catalogued one | Difference from everything in this repo | Expected Δ | Cost | Validatable now? |
|---|---|---|---|---|---|---|---|
| 1 | **H38-1 greedy marginal-credit emission** (this lane, primary arm A1) | Incumbent H35 probability surface → exact incremental kernel-credit pricing with break-even stopping (formulas above) | Catalogue-missing faults are the low/moderate-score ridges; fixed-spacing, fixed-budget dotting (sapd2.4/K3.5 %) force-spends FP mass in barren terrain and under-covers rich, short, high-credit segments. Pricing every dot by *incremental* credit buys coverage exactly where the max-kernel rule still pays. | H31 credit-field *re-ordered* by a smoothed density (negative); sapd uses isotropic spacing; `dot_thin` is score-blind. True incremental max-kernel accounting + plug-in FP + adaptive stopping is untested here (listed deferred as H34-2, knowledge/18). GEMSDOE70/82 used submodular selection on *different* surfaces live (OWNER 0.2478/0.1886) — never paired against sapd on one surface in this harness. | 0…+0.008 | ~half day | **Yes** — surface and harness exist |
| 2 | **H38-2 segment matched-filter surface** (secondary arm A3, same cells) | H35 surface → max over 8 orientations of the 15-px along-line mean (line-integral matched filter), then ridge-NMS + greedy emission | A blind fault under cover is a *faint but long coherent* alignment: per-pixel scores stay mediocre, so pixel top-K fragments it; integrating along the line raises SNR ~√length and bridges alluvial gaps. | No line-integral/object-level filter exists in this repo (all detectors are per-pixel HGB or local ridge transforms). Sibling Radon files (GEMSDOE74/75, OWNER 0.0669/0.1627) filtered raw bands, not the validated probability surface, and used different emissions. | −0.005…+0.008 | hours (reuses surfaces) | **Yes** |
| 3 | **H38-3 SGMC off-catalogue candidate universe** | Pinned `external/derived_sgmc_faults_100m_u8.tif` (USGS SGMC, Horton et al. 2017, DOI 10.5066/F7WH2N65, CC0) → candidates = SGMC fault pixels >2 px from the catalogue, ranked by the H35 surface, dotted | Bedrock geologic maps record faults from lithologic offset that have no Quaternary rupture and so never entered the Quaternary/INGENIOUS catalogue — exactly the hidden population's definition. | Registered as an idea (knowledge/22 #3 / knowledge/24 next-4) but never run in this repo. Sibling SGMC submissions scored low live (GEMSDOE29 OWNER 0.0512; GEMSDOE72 0.0492) with unknown emission — a warning, recorded, not hidden. Leakage canary is decisive: if the SGMC raster re-traces the catalogue, single-feature AUC vs hidden components will expose it. | unknown (wide) | ~half day | Yes (bytes pinned) — deferred: needs its own pre-registration; **not** run this session |
| 4 | **H38-4 radiometric alteration-index ridge** (H34-4, still unrun) | GeoDAWN K/Th/U (pinned `geodawn_rad_u8`) → Efimov F-parameter / Th-normalised K-enrichment, ridge-localised | Hydrothermal K-metasomatism tracks permeable fault conduits that may lack Quaternary rupture or scarp. | Family D uses ratios *pointwise*; X1 uses cross-scarp contrast; an alteration *ridge* was listed (knowledge/18 rank 4) but never implemented. Mimic risk high (felsic lithology). Another column-block on the same detector — the pattern that has failed six times — hence rank 4 despite low cost. | 0…+0.003 | ~half day | Yes — not run this session |
| 5 | **H38-5 raw 1 m 3DEP scarp-profile detector** | USGS 3DEP 1 m DEM tiles → cross-strike profile step/height at 1 m, aggregated to 100 m | Young scarps 0.2–2 m high in alluvium are invisible at 100 m and in the aggregated LiDAR descriptors; profile shape (not just max step in a cell) separates tectonic scarps from channels/roads. Only identified lever with leader-gap-sized headroom (knowledge/24 §6). | This repo has only 100 m-aggregated descriptors derived elsewhere; no raw-tile processing anywhere in the repo. | unknown, potentially large | days + fetch | **No — not viable in this sandbox.** Free official source: USGS 3DEP / The National Map <https://www.usgs.gov/3d-elevation-program>, <https://apps.nationalmap.gov/downloader/> (no use restrictions recorded in `registry/data_manifest.json`). Sandbox egress is github/pypi/npm only and the owner mirrors contain no raw tiles, so obtainability is verified at listing level only. Requires a networked runner; do not propose as this session's candidate. |

## Pre-registration — H38 screen + confirmation (frozen)

* **Harness (shared tools, no fork):** `gems25.experiment.Cell` hide-and-recover
  (whole 8-connected components hidden, hide_frac 0.20, 1.5 km collar,
  catalogue features from visible faults only, visible faults masked
  pixel-exactly), `gems25.metric.dti_binary` (α=0.2, β=0.8, R=3 px),
  `gems25.submission` writer/checker. New code is additive only:
  `gems25.greedy` (selection rule + line filter), unit-tested on synthetics
  (including brute-force vs lazy-greedy agreement and Monte-Carlo check of the
  ΔFP̂ formula) **before** the screen runs.
* **Cells:** folds NW/NE/SW/SE × draws **20, 21** (screen; fresh — prior
  sessions used ≤19). Confirmation draws **22, 23 only if** a gated arm passes
  the screen. Budget: this is experiment 1 of ≤3; no other hypothesis is fit
  this session.
* **Arms (same Cell, same fitted B35 surface per cell, paired):**
  * `A0` control — ridge-NMS → top-K (kfrac 0.035) → score-ordered dots 2.4 px.
  * `A1` **PRIMARY** — same top-K pool → greedy marginal-credit selection (above).
  * `A2` diagnostic — A0 dots with every dot ≤2 px from the *visible*
    catalogue deleted (the B2 operation, finally measurable).
  * `A3` secondary — line-matched-filter surface (15 px, 8 orientations) →
    its own ridge-NMS top-K pool → greedy selection with p̂ from the filtered surface.
* **Responses:** primary = standard **HOLDOUT-DTI** per cell (`Cell.evaluate`);
  secondary = **off-catalogue HOLDOUT-DTI** with truth restricted to hidden
  pixels >2 px from the visible catalogue (same evaluator, truth subset;
  withheld-positive counts reported for both). Also emitted count, hug share,
  coverage, surface AUC.
* **Leakage canary (read before any gate):** A1/A2 add no input feature (report
  the base-surface AUC); for A3, AUC of the line-filtered score alone vs the
  cell's hidden labels on the frozen AUC index sets. Effective AUC
  max(AUC, 1−AUC) > 0.90 → leakage until proven otherwise, stop, negative.
* **Gate (screen and confirmation separately; primary A1 vs A0, secondary A3 vs A0):**
  mean paired gain over fold means > **+0.001**, ≥3/4 folds positive, worst
  fold ≥ −0.010. Report pooled DTI, per-fold withheld positives, 95 % CI
  (t over 4 fold means). A2 has no gate (diagnostic of the B2 mechanism).
  If A1 fails the screen but A3 passes it, confirmation draws test A3 (and A0/A1
  for pairing); the built file follows the arm that passed both stages,
  else A1 (owner mandate: a unique file is built regardless, labelled by gates).
* **Lane check (surface before placement AND final dots):** Spearman of the
  full-build surface vs every restored registry raster (cap |ρ| 0.90) and
  final-dot 3-px overlap (cap 70 %), with per-raster 3-px halo coverage,
  reverse overlap and symmetric-min printed (the density-aware audit of
  knowledge/24 §4; literal numbers always shown). Overlap vs this repo's own
  H31/H35 lineage is reported separately as supersession, never silently cleared.
* **Full build (after gates are read):** 3 pseudo-new draws on the full
  catalogue exactly as `scripts/build_h35_candidate.py`, averaged surface,
  then the gated arm's emission over the full footprint (N̂ from the full
  catalogue count × 0.20/0.80). Primary file zeros-outside (every cell finite
  in [0,1] — the strict whole-array form behind the reported portal error),
  NaN twin + single-TIF zip. `slot_approved` stays **false**: promotion to a
  weekly slot is the owner's separate selector step; the agent never uploads.
* **Run card:** `registry/run_card_h38_2026-10-25.json` — hypothesis, mechanism,
  named non-fault mimic, HOLDOUT-DTI + CI + withheld counts (both responses),
  correlation/overlap vs registry, raster SHA-256, validator output
  (no NaN inside footprint, values in [0,1], CRS/shape/transform match),
  submission name + note ≤140 chars, verdict promote/negative. Negative is a deliverable.
