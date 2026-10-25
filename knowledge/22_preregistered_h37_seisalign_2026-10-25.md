# 22 · Pre-registered H37-SEISALIGN: seismicity-alignment ridge (Experiment 2, written before any fit, 2026-10-25)

**Trigger:** Experiment 1 (H36-TZC, knowledge/21) failed its frozen screen gate —
paired gain −0.0013 HOLDOUT-DTI vs the same-run H35-B control, 2/4 folds,
95% CI [−0.0119, +0.0094], leakage canary 0.588 (clean). Per knowledge/21 no
confirmation was run for TZC. This document pre-registers the rank-2 hypothesis
from knowledge/21's ranked table as the session's second (of at most three)
experiments. The lane changes only in the added feature block; detector,
emission, evaluator, comparator and gate are identical, so the result is paired
against the same current holdout best.

**Lane paragraph:** Add three structure-tensor alignment columns derived from
the two earthquake-density bands to the repo's validated HGB detector
(B+D+E + 7 add-ons + directed tip + H34 block) and test whether aligned
seismicity raises pooled HOLDOUT-DTI against the same-run H35 arm-B control.

## Hypothesis

- **Layers:** `deq_n100a15` (band 10) and `ieq_n100a15` (band 16) of the pinned
  19-band feature raster (owner mirror; band semantics per knowledge/08:
  provider "density of earthquakes, n=100 km, a=15°" parameters — see mimic note).
- **Physical signature:** local structure tensor of the log earthquake-density
  field: coherence c = sqrt((Jxx−Jyy)² + (2Jxy)²)/(Jxx+Jyy) ∈ [0,1] of the
  σ=5 px-smoothed gradient tensor of the σ=2 px-smoothed log-density, and the
  alignment-weighted ridge `ridge_strength(log-density, 2.0) × coherence`.
  Columns: `H37_seis_deq_coh`, `H37_seis_deq_alignridge`, `H37_seis_ieq_alignridge`.
- **Why catalogue-missing:** epicentre density is independent of surface
  mapping; microseismicity aligned along a buried seismogenic fault traces it
  where no Quaternary scarp exists for the catalogue to record.
- **Difference from repo work:** family C enters the factorial only as raw
  density columns and strain-rate gradients (`C_2ndinv_grad`, `C_shear_grad`);
  no structure-tensor coherence or alignment-weighted ridge exists in `src/`
  (grep `coherence` finds only the unrelated LiDAR `L_coh100` descriptor).
- **Named non-fault mimics:** aftershock/swarm elongation along non-fault
  structures; induced seismicity around geothermal production; epicentre
  location-error smearing; and — flagged in advance — the provider density
  kernel itself (band name encodes a 15° azimuth parameter), so apparent
  alignment could be a kernel artefact rather than geology. A holdout pass
  would not by itself distinguish these.
- **Expected gain (planning bracket):** 0 to +0.004 HOLDOUT-DTI (knowledge/21).

## Frozen design (identical to knowledge/21 except the block)

- Arms per (fold, draw) cell, same `Cell(extras=True, h27=True)`:
  `BEST` = BDE+7 + H27_tip + 3 H34 columns; `SEIS` = BEST + 3 H37 columns.
- Draws: screen 40–41; confirmation 42–43 only if the screen passes. Folds NW/NE/SW/SE.
- Emission frozen: ridge NMS σ=1.0 → drop catalogue → top-K kfrac 0.035 →
  score-ordered dots 2.4 px. Evaluator `gems25.metric.dti_binary` (α=0.2, β=0.8, R=3 px).
- Leakage canary: single-feature ROC-AUC per H37 column per cell; >0.90 or <0.10 fails.
- Gate (frozen): paired SEIS−BEST mean > +0.001, ≥3/4 folds positive (fold means),
  worst fold ≥ −0.010. Screen pass → confirmation; both must pass for `promote`.
- Lane and validator rules as in knowledge/21 (Spearman ≤0.90, ≤70% dots within
  3 px vs any registry raster, lattice reported both literally and separately;
  `check_file` hard checks; zeros-outside primary). No slot is spent by the agent.
