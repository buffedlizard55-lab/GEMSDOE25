# H73 — Ranked untried hypotheses + pre-registration: propensity-matched H35 (2026-10-26)

**Branch:** `arena/11c66d52-gemsdoe25` · **Session lane (PARALLEL-RUN PROTOCOL item 1):** H73-PM only.
This document is committed **before any H73 fit** (AGENTS rule 4). Design, response, analysis rule and
gates below are frozen. A failed arm stays failed.

## 0. What is already proven (re-verified this session, COMPUTED)

Independently recomputed 2026-10-26 from the SHA-pinned restored rasters (`/tmp/verify_b2.py` logic,
`gems25.thinning.dot_thin`, `scipy` EDT on `data/labels.tif`):

* `B2 == D2.8 & (d(labels) > 2.0 px)` pixel-exactly; `R1 == D2.8 & (d > 1.0 px)` pixel-exactly;
  `dot_thin(H19-5, 2.4) == D2.8` pixel-exactly (xor = 0). Counts: H19-5 121,131 → D1.5 60,069 →
  D2.8 44,090 → R1 40,199 → B2 37,654. **Zero new detections along the whole 0.1922 → 0.2778 chain**
  (all OWNER-REPORTED scores; no organizer receipt exists in any repo).
* B2 `d_cat` strata (recomputed): ≤2 px 0.0 %, 2–9 px 27.4 %, 9–20 px 23.4 %, >20 px 49.2 %, median 19.7 px.
  GEMSDOE70 P8-OOF38k (best non-H19-5 live architecture, OWNER-REPORTED 0.2478): 0.0 / 30.7 / 23.8 / 45.5 %,
  median 17.5 px, also exactly 37,654 dots. GEMSDOE25 H66 (OWNER-REPORTED live 0.0742): 1.0 / 69.6 / 26.4 /
  3.0 %, median 5.8 px. **Live score tracks far-field share, not holdout rank.**
* Mechanism (algebra, `gems25.metric`): with `T + FN_w = |G|`, `S = T / (0.2 (T+F) + 0.8 |G|)`. `TP_w` is a
  **max** over the 3-px kernel disk, `FP_w` a **sum** over emitted pixels. Removing pixels raises `S` iff
  their mean credit per pixel is below `alpha·S/(1 − alpha·S)` = 0.055 at S = 0.26
  (`metric.marginal_inclusion_ratio`). Dotting removed 63.6 % of H19-5's pixels at ~zero marginal credit;
  the ≤2-px collar (6,436 px) was deadweight because the scorer masks catalogue pixels and hidden truth is
  not a 100–200 m offset copy of mapped traces. That is the whole 0.2778: an unsupervised scarp detector
  plus two geometry-only prunes. It follows that >0.2778 requires **higher credit density at B2-like
  strata**, i.e. genuinely better far-field detection — no emission re-arrangement of an apron-hugging
  surface can get there (H66's 0.0742 is the counterexample).
* Minor doc inconsistency flagged (IR candidate): older GEMSDOE25 tables give D2.8 "8.6 % ≤2 px"; the
  recomputed value is 14.6 % (6,436 / 44,090). 8.8 % is the ≤1-px share. No conclusion changes.

## 1. Five candidate hypotheses not yet tried in this repo, ranked

Expected-DTI figures are **planning brackets (judgment), never scores**.

| Rank | Hypothesis | Layers / signature | Why catalogue-missing faults | Differs from implemented code | Named mimic | Planning bracket / cost / viable here? |
|---:|---|---|---|---|---|---|
| **1** | **H73-PM propensity-matched training of the H35 stack** *(selected lane)* | No new layer. Training-set intervention on `BDE + EXTRAS + H27_tip + H34` (DEM/LiDAR scarp family B, radiometric/conductivity family D, visible-catalogue family E): negatives resampled so `p_neg(bin(d_vis)) = p_pos(bin(d_vis))`, removing the ~8× apron prior tilt documented in `knowledge/31` §2.2 | The tilt is exactly why supervised models hug mapped traces (H66: 69.6 % of dots at 2–9 px, live 0.0742) while hidden truth sits far-field (49.2 % of B2 dots >20 px). Matching forces the HGB to earn separation from scarp/potential-field evidence that also exists on unmapped piedmont/basin faults | Every prior fit (`experiment.Cell`) draws negatives uniformly; "de-aproned" arms (H72) changed only emission/features, never the sampler. Grep-verified: propensity matching is mentioned only as future work in `knowledge/31` | Pluvial Lake Lahontan shoreline scarps and alluvial-fan channel levees far from any mapped fault — linear DEM breaks the de-biased model may now over-fire on | Far-field HOLDOUT-DTI +0.005…+0.020 vs blind control (bracket); ~30 min/run; **YES, all inputs local & SHA-pinned** |
| 2 | H73-BW 25-km block-withheld selector | Evaluation-only: hide *all* components intersecting checkerboard blocks so `d_vis` on test truth is genuinely large; reuse `gems25.metric.dti_binary` | Component-split holdout cannot distinguish discovery from splinter interpolation; a block selector is the only offline proxy that rewards the B2/G70 strata profile | `gems25.holdout.Holdout` hides components per quadrant; no block mode exists | — (evaluator change; risk is small-n variance, not a geological mimic) | No direct DTI gain; prevents a wasted weekly slot. ~2 h. Viable, but only worth building if rank 1 shows far-field signal |
| 3 | H73-SOFT graded-probability emission | Emission-only: emit calibrated `p ∈ (0,1]` instead of binary dots on the same support | — | All 90+ portfolio submissions are binary | — | **Theory says no**: for fixed support, `S(p) = pT/(0.2p(T+F)+0.8|G|)` is increasing in uniform `p`, and per-pixel grading only helps if it re-ranks support — which top-K already does. Bracket ≤ +0.002; 1 h offline check on stored surfaces. Deprioritised on proof, not taste |
| 4 | H73-2D patch CNN (U-Net/ConvNeXt) on 6.4-km raster tiles | `training_features.tif` 19 bands + 3DEP LiDAR sidecar as image channels; 2-D receptive field learns lineament continuity vs sinuous shorelines | Pointwise HGB cannot see that a scarp continues linearly for 5 km; unmapped faults are exactly the long, low-relief lineaments | No neural code in repo (HGB only) | Shoreline contour-tracking learned as "fault-like" (Lahontan high-stands are also long & linear locally) | Unknown bracket; **NOT viable this session**: no `torch` in pinned requirements, no GPU, ~4 GB RAM sandbox. Named honestly, not proposed |
| 5 | H73-INSAR Sentinel-1 creep/lineament layer | Sentinel-1 IW SLC pairs (free: Alaska Satellite Facility DAAC, https://search.asf.alaska.edu — requires free NASA Earthdata login); LOS velocity discontinuities | Creeping blind faults under playa with no scarp and no potential-field offset | No SAR input anywhere in the portfolio | Groundwater-pumping subsidence bowls (agricultural valleys) mimic fault-bounded LOS steps | **NOT viable this session**: Earthdata credentials are the owner's to create (agent never handles credentials), and SLC processing is days of compute. Recorded for owner decision |

## 2. Frozen design — Experiment 1 (H73-PM screen)

* **Evaluator:** `gems25.metric.dti_binary` (α = 0.2, β = 0.8, R = 3.0 px = 300 m triangular kernel) via
  `gems25.experiment.Cell.evaluate`; pooled DTI + quadrant-cluster bootstrap 95 % CI
  (`gems25.validation.pooled_summary`). Every number labelled **HOLDOUT-DTI** with withheld-positive count.
* **Cells:** 4 spatial folds (NW, NE, SW, SE) × fresh draws **90, 91** (`gems25.holdout.Holdout`,
  hide_frac 0.20, 1.5-km collar, visible-catalogue-only family E, pixel-exact known masking). Draws
  80–85 were consumed by H72; 90–91 are unused.
* **Arms (paired, same cells):**
  1. `CTRL_H35` — exact incumbent: cols `BDE + EXTRAS + H27_tip` + H34 sidecar, `Cell` uniform sampler,
     emission kfrac 0.035, `score_ordered_dots` min_dist 2.4, catalogue buffer 0.
  2. `CTRL_BLIND_BD` — `BD + EXTRAS` + H34, uniform sampler, de-apron emission (0.030 / 2.8 / 2.0 px).
  3. `PM_H35` — CTRL_H35 columns, **propensity-matched sampler**, H35 emission (isolates the sampler).
  4. `PM_DEAPRON` — same PM surface as arm 3, de-apron emission (the live-geometry candidate surface).
* **PM sampler (deterministic, frozen):** `d_vis` = EDT distance to the draw's *visible* catalogue on the
  full grid, sampled at footprint vectors. Bins (px): `[0,2], (2,5], (5,9], (9,15], (15,25], (25,40],
  (40,80], >80`. Positives = `hidden_train` (identical to `Cell`). Negative pool = `train_region &
  ~labels & (EDT(hidden_train) > 1.5)` (identical to `Cell`). Target total = `min(300_000, pool)`;
  per-bin quota ∝ positive bin shares, capped at pool bin size, shortfall redistributed proportionally
  among uncapped bins; within-bin choice uniform without replacement, RNG seed `777 + 31·fold + draw +
  5000`. No sample weights. HGB params = `experiment.HGB_PARAMS` unchanged; fit seed = draw.
* **Leakage canary (protocol item 4):** `gems25.validation.feature_canary` (cap 0.90, value + inverted +
  missingness) on **every fitted column** of arm 3, every cell, before its DTI is trusted; plus `-d_vis`
  alone each cell to document the bias being removed. Any canary > 0.90 ⇒ stop, treat as leakage.
* **Responses per arm/cell:** HOLDOUT-DTI, far-field HOLDOUT-DTI (`d_vis > 9` px sub-truth, same
  evaluator), AUC, emitted count, `d_vis` strata, canary maxima.
* **Gates (both pre-registered; no post-hoc substitution):**
  * *Far-field screen (PM_DEAPRON):* pooled far-field DTI > CTRL_H35 and > CTRL_BLIND_BD; ≥3/4 folds
    positive vs CTRL_BLIND_BD far-field; >20-px dot share ≥ 35 %.
  * *Slot gate (AGENTS rule 5, unchanged):* pooled overall HOLDOUT-DTI gain vs same-run CTRL_H35
    > +0.001, paired cluster-CI lower bound > 0, ≥3/4 folds positive, worst fold ≥ −0.010.
  * Stated expectation: PM may **fail** the slot gate precisely because component-split holdout rewards
    apron-hugging. If so: verdict **negative, DO NOT SUBMIT**, run card says so, and the follow-up
    (rank-2 block selector) is left as next-session work. A far-field win never overrides the slot gate.
* **Lane gate (protocol item 1):** before any packaging, PM surface Spearman vs every registry raster
  and final-dot 3-px overlap (`scripts/check_lane_duplicates.py`, `scripts/lane_check_extended.py`);
  >0.90 |ρ| or >70 % overlap (density-aware flags reported alongside literal flags) ⇒ duplicate, stop.
* **Budget (protocol item 6):** max 3 experiments / 2 h compute. Exp 2 (confirmation draws 92–93, same
  arms) runs **only if** the Exp-1 far-field screen passes. Exp 3 = full-footprint build, **only if**
  the slot gate passes on pooled Exp 1+2. No weekly slot is spent by this session under any outcome;
  promotion remains a separate selector step by the owner.

## 3. Deliverables regardless of outcome

`evidence/h73_pm_screen/` (design.json written before fits, cells.jsonl, analysis), one JSON run card
(`registry/run_card_h73_2026-10-26.json`) with hypothesis / mechanism / mimic / HOLDOUT-DTI + CI /
registry correlation-overlap / raster SHA-256 (or null) / validator output / name + ≤140-char note /
promote-or-negative verdict, an executive-summary update with the download table (file, HOLDOUT-DTI
estimate labelled as such — never a projected live score, unique YES/NO, submit YES/NO), and three
review passes recorded in `registry/review_passes_h73_2026-10-26.json`.

Official sources for manual review: competition https://www.drivendata.org/competitions/306/competition-doe-gems/ ·
problem/metric https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ ·
rules PDF https://docs.nlr.gov/docs/fy26osti/96647.pdf ·
reference solution https://github.com/drivendataorg/gems-prize-reference-solution ·
GDR 1391 https://gdr.openei.org/submissions/1391 ·
USGS GeoDAWN https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ·
INGENIOUS https://gbcge.org/current-projects/ingenious/ · EPSG:32611 https://epsg.io/32611
(no DrivenData page is fetched by the agent; links are for the owner's manual review).
