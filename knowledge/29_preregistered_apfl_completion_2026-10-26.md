# 29 · Pre-registration — APFL completion + off-catalogue emission diagnostic (2026-10-26, session arena/8aa4ff79)

**Status: frozen before any fit in this session.** This document is committed before
`scripts/run_apfl_experiments.py` is run. Data restoration / feature-cache building
(no labels-based fitting, no DTI computed) may precede it. Budget: 3 experiments
(Parallel-Run Protocol #6). No weekly slot is chosen here; promotion is a separate
selector step (Protocol #6, AGENTS.md rule 5).

## Lane (Protocol #1 — the single method paragraph for this session)

> Catalogue-free alluvial-piedmont flexure lineament detection: 3DEP LiDAR sub-metre
> scarp texture (`L_step_max`, gated by `L_valid`) × 100 m DEM flexure (`B_tpi11`
> positive part, `B_crest`) × isostatic-gravity analytic-signal gradient
> (`A_grav_as`) × depth-to-conductive-base gradient (`D_depth_base_grad`) × surface
> conductivity gradient (`D_cond_grad`), combined as the frozen product in
> `knowledge/27_apfl_hypotheses_ranked_2026-10-26.md` §3, emitted by Hessian
> ridge-NMS + score-ordered Poisson-disk dotting with a B=2 px catalogue collar.
> No magnetic (TMI/RTP) term, no strain/seismic term, no catalogue-distance
> feature in the *detector* (the visible catalogue is used only to mask/collar
> emission, exactly as the organizer masks known pixels), no GDR wells/springs.

Lane stop rule (literal, no waivers): if the pre-placement surface's rank
correlation with any registry scored raster exceeds |0.90|, or >70% of final dots
fall within 3 px of one registry scored raster's dots, log DUPLICATE and stop.
The dense r13 5-px lattice and own-lineage testing files are reported separately
as diagnostics (IR-25-LANE-DENSITY), never silently dropped.

**Irregularity disclosed up front:** the 2026-10-26 APFL TIF in `docs/downloads/`
(`8aebdab87158`) has a run card and a frozen formula (knowledge/27) but **no
builder code in `src/` or `scripts/`** (verified by grep this session). This
session therefore *re-implements* APFL from the frozen formula in
`src/gems25/apfl.py`. The re-implementation is a reconstruction, not the original
private code; any numerical difference from the shipped APFL TIF is expected and
will be measured (surface correlation + dot overlap vs that file) and reported.

## Why this lane (next step from previous sessions, done first)

knowledge/28 §"Next selector gate" left exactly one pending test: *"Run APFL
holdout screen on draws 60,61 (2 of 3 experiments left); need pooled HOLDOUT-DTI
>+0.001 vs H35, ≥3/4 folds positive, worst ≥−0.010, hug ≤+0.10, canary AUC
≤0.90"*. That screen was never run (no `evidence/apfl*` directory exists).
POL3 (draws 58,59: 0.160280 vs H35 0.161275, FAIL), ROD (0.0690 vs 0.1523,
FAIL + lane stop) and H71 (three DIRECT screens, all FAIL vs H35) are closed
negatives and are not retuned here.

## Ranked candidate hypotheses considered for this session (3–5, pre-fit)

| Rank | ID | Layers (source) | Physical signature | Why catalogue-missing? | Difference vs implemented | Mimic (non-fault) | Planning bracket (not a forecast) | Cost | Validatable now? |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **APFL piedmont flexure** (this lane; Exp 1 DIRECT, Exp 2 as HGB columns) | `L_step_max/L_valid` (USGS 3DEP 1 m descriptors, pinned mirror), `B_tpi11/B_crest` (100 m DEM bands 12/19), `A_grav_as` (iso-gravity bands 13/18/11), `D_depth_base_grad` (band 15), `D_cond_grad` (band 17) — all in the pinned static cache | Product `S = Lvalid·(Lstep^0.35·gravAS^0.30·depthGrad^0.20·condGrad^0.05·TPIpos^0.10)·(1+0.5·crest)`, p1–p99 scaled, ridge-NMS | Blind piedmont faults under Qal show subtle LiDAR step + DEM warp + basement gravity/depth step but no bedrock scarp; systematically under-mapped in QFFDB | H31 used LiDAR×mag/grav ridges w/o depth/TPI conjunction; H71 used gravity×depth polarity w/o LiDAR/DEM; no prior arm uses this 5-term product | Unfaulted alluvial-fan onlap wedges, axial drainage incision, aeolian deflation (same TPI/depth gradients, no gravity step) | DIRECT: unknown, prior DIRECT lanes scored 0.05–0.07 pooled; HGB-columns: 0 to +0.005 vs H35 | ~30 min (8 HGB fits/screen) | **Yes** — all bands cached after restore |
| 2 | **OCEM off-catalogue emission diagnostic** (Exp 3, no new fit) | None new; re-emits Exp 1/2 + H35 cell surfaces at B∈{0,1,2,3} px collars | Credit density by distance-to-visible-catalogue shell; B2 champion deleted shells earning 0.0010/0.0050 per px vs break-even τ≈0.056 | Tests the *emission* half of the 0.2778 result, which the standard catalogue-gap holdout cannot identify (its truth is catalogue) | knowledge/20 proposed this off-catalogue-truth holdout; never built. Here: standard holdout re-scored with truth restricted to hidden pixels ≥2 px from visible traces (descriptive only) | Mapped-trace misregistration (100–200 m) and genuine near-catalogue splays/corrections (staff: corrections within 300 m are scored) | Diagnostic; no DTI gain claimed | Minutes (re-emission only) | **Yes** |
| 3 | Seed/draw HGB ensemble (variance reduction) | Same H35 columns | Average of ≥3 HGB fits (seeds/draws) before NMS | No new geology; stabilises dot placement | Full-footprint builders already average 3 draws, but no paired holdout arm has isolated ensembling | None (estimator, not geology) | 0 to +0.003 | 3× fit cost | Yes, but deferred — not a geological hypothesis; only if Exp 1/2 pass and budget remains |
| 4 | Directional vent-pair fissure corridor | GDR 1391 vents (21 pts, pinned CSV), RTP strike, dilatation | Vent-pair alignment corridors × magnetic dike ridge | Feeder dikes mark blind extensional faults buried by young lava | Prior vent use was isotropic proximity (GEM-2, knowledge/15); directional pair corridors untested | Volcanic fissures without through-going faults; flow-margin lineaments | −0.001 to +0.002 (21 vents, low power) | ~1 h | Yes, deferred (low power) |
| 5 | Paleo-sinter × heat-flow residual | GDR 1391 paleo-geothermal + USGS heat-flow (DOI 10.5066/P9BZPVUC) | Fossil sinter/travertine at paleo water-table × conductive heat-flow high | Preserves conduit evidence where scarps eroded | Never implemented | Non-tectonic spring deposits along lithologic contacts | Unknown | Fetch + audit first | **No** — hosts outside sandbox allowlist (github/pypi only); obtainable in principle from GDR/ScienceBase, not verified byte-level here; not proposed as viable this session |

## Frozen design

- **Evaluator:** `gems25.metric.dti_binary` (α=0.2, β=0.8, R=3 px / 300 m
  triangular kernel) via `gems25.experiment.Cell.evaluate`; hide-and-recover
  `gems25.holdout` (whole 8-connected components hidden, hide_frac 0.20, 15 px
  collar, 4 spatial quadrants NW/NE/SW/SE). Every number labelled
  **HOLDOUT-DTI (evaluator, withheld positives, 95% CI)** or **OWNER-REPORTED**.
  No projection is written as a score.
- **Comparator (same run, AGENTS.md rule 5):** H35 arm B = base `BDE` + 7 add-ons
  + `H27_tip` + 3 H34 RESMAG columns, HGB `HGB_PARAMS`, sapd2.4, kfrac 0.035
  (exactly `scripts/run_h35_factorial.py` arm B). Cross-session absolute numbers
  are records, not baselines (IR-25-COMPARATOR-DRIFT).
- **Exp 1 — APFL-DIRECT (screen, draws 60,61):** arms per cell:
  `CTRL_H35_24` (above), `APFL_DIRECT_B2` (APFL product → ridge-NMS → exclude
  visible catalogue, EDT(~visible)>2 → score-ordered dots, min_dist 3.0,
  k = round(0.035·domain)), `CTRL_CREST_B2` (same emission on scaled `B_crest`,
  unsupervised floor). Primary contrast: APFL_DIRECT_B2 vs CTRL_H35_24.
- **Exp 2 — APFL-HGB (screen, fresh draws 62,63):** arms: `CTRL_H35_24`,
  `H35_PLUS_APFL` (H35 columns + 5 APFL component columns + APFL product as HGB
  features, sapd2.4, kfrac 0.035). Rationale disclosed pre-fit: DIRECT lanes
  have repeatedly failed vs H35 (H71 ×3, ROD); the HGB-columns form tests the
  same physical signature with the incumbent estimator. This is a second
  experiment, not a retune of Exp 1 (different draws, frozen here).
- **Exp 3 — OCEM diagnostic (no fit):** from saved Exp 1/2 cell scores if
  retained, else from one re-emission pass on the Exp 2 cells: B∈{0,1,2,3}
  collars scored (a) standard, (b) truth restricted to hidden pixels with
  EDT(~visible)≥2. Descriptive only; cannot promote anything by itself.
- **Confirmation rule:** only if a screen passes the gate below may fresh
  confirmation draws (64,65) be run, and they count against the 3-experiment
  budget (so at most one of Exp 1/2 can be confirmed; if both screens were run,
  confirmation replaces Exp 3).
- **Leakage canary (Protocol #4):** every APFL component + product alone vs
  hidden truth per cell (raw, inverted `max(AUC,1−AUC)`); any canary AUC > 0.90
  stops the run as presumed leakage. APFL uses no label-derived input by
  construction; the canary is still mandatory.
- **Gate (frozen, from knowledge/27/28):** pooled/fold-mean paired gain
  > +0.001 vs same-run CTRL_H35_24, ≥3/4 folds positive, worst fold ≥ −0.010,
  mean hug-delta ≤ +0.10, canary ≤ 0.90. Fail ⇒ verdict negative, no
  confirmation, any TIF built is testing-only / DO NOT SUBMIT.
- **Full-footprint TIF:** built from the best *screen* arm's recipe only after
  screens finish (promote only if gate + confirmation pass; otherwise
  testing-only). Zeros-outside primary (strict `((a>=0)&(a<=1)).all()`),
  NaN-outside twin, single-band float32 EPSG:32611 3730×3292, template
  transform, content-addressed filename, ≤140-char note. Lane checks on surface
  (pre-placement) and final dots vs registry scored rasters + top-scorers +
  own downloads (Spearman, 3-px overlap both directions + density diagnostic).
- **Score estimation for the executive table:** OWNER-REPORTED live values for
  historical files; for new files only HOLDOUT-DTI (measured) plus an explicitly
  labelled *planning projection* (assumptions stated; proxy↔live Spearman
  +0.33, n=24, n.s. — GEMSDOE24). Break-even arithmetic (τ = 0.2·D/(1−0.2·D),
  credit/px required at candidate N) is exact algebra, not a score.

## Stopping

After 3 experiments or 2 h of compute, stop. Negative results are deliverables.
The agent never uploads to DrivenData and never accesses drivendata.org
(AGENTS.md rule 3).
