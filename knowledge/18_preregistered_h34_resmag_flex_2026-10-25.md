# 18 · Candidate hypotheses (new) + pre-registration H34-1 RESMAG-FLEX (2026-10-25)

Written and committed **before any H34 fit**. Novelty is checked against this repo's
registers (knowledge/03 H26, /09 H27, /10 H28, /11–12 H30, /13 H31, /14 H32, /15 GEM-1…5)
and the nine focus sites (knowledge/17). Expected gains are planning brackets, not forecasts.
Every score mentioned is OWNER-reported unless labelled HOLDOUT-DTI.

## The single lane for this session (PARALLEL-RUN PROTOCOL item 1)

> **H34-1 RESMAG-FLEX.** Add exactly three depth-sliced potential-field columns to the
> incumbent HGB detector (BDE + 7 add-ons, sapd2.4, kfrac 0.035 — all frozen): the
> horizontal-gradient ridge strength of the shallow RTP residual (RTP minus its 400 m
> upward continuation), the same for the mid residual (400 m minus 1200 m upward
> continuation), and the ridge strength of the horizontal-gradient magnitude of
> log depth-to-conductive-base. Upward continuation is the exact Fourier operator
> `exp(-2π·|f|·Δz)` on the pinned RTP band. Nothing else changes.

## Ranked candidate hypotheses

| Rank | ID | Layers → signature | Why it should catch a catalogue-missing fault | Difference from repo + focus sites | Expected Δ (holdout) | Cost | Validatable now? |
|---|---|---|---|---|---:|---|---|
| 1 | **H34-1 RESMAG-FLEX** | `rtp` (band 02) FFT upward-continued 400/1200 m → two residual HG-ridge columns; `depth_to_base_surf` (15) → ridge of log-depth gradient ("flexure line") | A fault offsetting magnetic basement/volcanics or the conductive base still produces a depth-localised potential-field edge under alluvial cover where no scarp exists for B/LiDAR or the catalogue to record. Shallow residual separates near-surface edges from deep basement steps. | Family A is single-scale (HG/VG, tilt, analytic signal, one ridge σ); no upward continuation anywhere in repo (pinned `TMI_up150` documented, unused); `D_depth_base_grad` is a magnitude, never ridge-localised. Not Euler (GEMSDOE28), not worms (GEMSDOE29/42 tracked maxima), not GEM-1's unsupervised grad×relief surface, not PF-only (GEMSDOE32 Arena41, which *replaced* the detector and failed its gates). | 0…+0.008 | ~0.5 day | **Yes** — all bands pinned locally |
| 2 | H34-2 marginal-credit greedy emission | incumbent probability surface → incremental submodular dot selection, stop at break-even α·D/(1−α·D) | Does not detect; re-prices every dot by *incremental* kernel credit net of overlap | H31 re-ordered by a smoothed credit field (negative); true incremental accounting + stopping rule untested here. GEMSDOE32 greedy contrasts flip sign across instruments → lane risk + weak prior | 0…+0.005 | 1 day | Yes, but deferred: run only as a separately pre-registered experiment |
| 3 | H34-3 GEM-1 as a model column | GEM-1 surface (knowledge/15) appended to BDE+7 | Blind-fault interaction (magnetic edge × no relief) given to the trees instead of used as a standalone surface | GEM-1 was only ever evaluated unsupervised (0.042 mean) vs a weak B_crest control; never as a column. Overlaps H34-1's RTP gradient, hence rank 3 | 0…+0.004 | hours | Yes |
| 4 | H34-4 radiometric alteration lineament | GeoDAWN K, Th/K, U/K → ridge of K-enrichment (F-parameter style) line strength | Hydrothermal K-metasomatism tracks permeable fault conduits that may lack Quaternary rupture | D uses ratios pointwise; X1 uses cross-scarp *contrast*; an alteration-index *ridge* is new. Mimic risk high (lithology) | 0…+0.003 | ~0.5 day | Yes |
| 5 | H34-5 paleo-shoreline offset / EQ-azimuth anisotropy | needs absolute-elevation DEM (only detrended elevation + LiDAR descriptors are pinned) or an official definition of `deq/ieq_n100a15` azimuth semantics (flagged IR-25-BAND-ALIASES) | Shorelines are datums a young fault must offset; aligned microseismicity traces blind structures | Neither is implementable from pinned bytes. Free official source for DEM: USGS 3DEP <https://www.usgs.gov/3d-elevation-program> — **not obtainable from this sandbox** (github/pypi/npm egress only; raw tiles not in owner mirror) | unknown | days + fetch | **No — blocked, not viable this session** |

**Non-fault process that could mimic H34-1 (named in advance):** lithologic contacts and
lava-flow/intrusion margins produce identical residual-magnetic edges without faulting, and
a depositional basin-margin pinch-out produces a conductive-base gradient ridge without a
fault. Survey line-levelling artefacts can also create linear residual features.

## Pre-registration — H34-1 screen + confirmation (frozen)

* **Harness (shared tools, no fork):** `gems25.experiment.Cell` (hide-and-recover:
  whole 8-connected components hidden, hide_frac 0.20, 1.5 km collar, catalogue features
  from visible faults only, visible faults masked pixel-exactly in scoring),
  `gems25.metric.dti_binary` (α=0.2, β=0.8, R=3 px = 300 m triangular kernel),
  `gems25.submission` writer/checker. Evaluator id: `gems25.metric.dti_binary` at repo HEAD.
* **Cells:** folds NW/NE/SW/SE × draws 0,1 (screen). Confirmation draws 2,3 **only** if the
  screen passes. Budget: ≤3 experiments total this session; H34-1 screen+confirmation = 1.
* **Arms (same Cell, same train sample, paired):**
  * `C` control — BDE + X1_K,X1_ThK,X1_UK,X2_compat,X2_compat_coh,X3_gm,X3_gd; HGB seed=draw;
    emission: ridge-NMS candidates → top-K (kfrac 0.035 of eroded domain) → score-ordered
    dots at 2.4 px. This is the H28 comparator configuration, **recomputed in this run**.
  * `A` candidate — identical, plus the 3 H34 columns (formulas in
    `src/gems25/h34.py`, unit-tested on synthetics before the run).
* **Leakage canary (before any gate is read):** per-cell AUC of each H34 column alone vs the
  cell's hidden-test labels on the Cell's fixed AUC index sets. Any AUC > 0.90 → leakage
  until proven otherwise; stop, verdict negative.
* **Reproduction diagnostic:** C's per-cell DTI vs `evidence/h28_holdout/cells.jsonl`
  (score, 2.4, 0.035). Reported cell-by-cell; if C's mean differs from the H28 same-arm
  mean (0.149668) by > 0.002, the run is flagged IR and only the paired contrast is read.
* **Gate (screen and confirmation separately):** mean paired gain (fold means of A−C)
  > +0.001, ≥3/4 folds positive, worst fold ≥ −0.010. Response labelled
  **HOLDOUT-DTI** with evaluator id, withheld positives per fold, and a 95 % CI
  (t over the 4 fold means, as in the H31 run card).
* **Lane check (before packaging):** final dots + surface vs every restored registry raster
  (`scripts/check_lane_duplicates.py`): Spearman ≤ 0.90 and ≤70 % of dots within 3 px of any
  one registry raster's dots. The dense 13GEMSDOE lattice caveat (IR-25-LANE-DENSITY)
  is reported, not silently overridden: both directions of overlap are printed.
* **TIF policy (per the owner's 2026-10-25 brief):** a unique full-footprint TIF of arm A is
  generated whatever the gate says (3-draw full-catalogue build, same emission), in both
  outside conventions; the **zeros-outside** file is the primary download because it passes
  the strictest whole-array [0,1] validator (the reported portal error), with the
  NaN-outside twin kept as the template-convention alternate. The site/README state in one
  line whether it is OK to submit: **promote** only if screen+confirmation+lane+exact-file
  audit all pass; otherwise **negative — download for inspection only, do not spend a slot**.
* **Run card:** one JSON (`registry/run_card_h34_2026-10-25.json`) with hypothesis, mechanism,
  mimicking process, HOLDOUT-DTI + CI + withheld counts, lane correlations/overlaps, raster
  SHA-256, validator output, submission name + note ≤140 chars, verdict promote/negative.
  Negative is a deliverable. No weekly slot is spent by the agent; upload stays manual.
