# 22 · Experiment 2 pre-registration — MSCR-1 multi-scale crest persistence (2026-10-25)

Written **before any MSCR fit**, after Experiment 1 read out. This is experiment **2 of the
3-experiment budget** (protocol item 6). GMCE-1 stays failed; nothing below retunes it.

## Experiment 1 result (for the record, HOLDOUT-DTI only)

GMCE-1 screen (draws 20–21, `evidence/gmce_screen/`): GMCE pooled **HOLDOUT-DTI 0.150125**
(fold-pooled 95 % CI 0.1386–0.1616) vs same-run BEST 0.151492; paired mean gain **−0.001209**
(95 % CI −0.0092…+0.0067), **1/4 folds** positive, worst fold −0.007532 (SE); leakage canary
max single-column AUC 0.560 ≤ 0.90 (pass); withheld positives 22,232 pooled across cells.
Frozen gate **FAIL** → no GMCE confirmation. Reading (INFERENCE): a potential-field-family
derivative added nothing on fresh draws, consistent with the Resolution-V factorial's family-A
main effect (−0.0027, classified inert, `evidence/factorial/results.md`) — the incumbent stack
already extracts what gravity/magnetics magnitudes carry on this proxy, and gradient-*azimuth*
agreement does not separate hidden catalogue components from background at 100 m.

## Why experiment 2 is MSCR-1 (rank 4 in knowledge/21), not ranks 2–3

Sequential, documented re-ranking — not outcome-tuning of a tested arm (the MSCR formulas below
were not fitted or peeked at before this commit):

* Rank 2 (junction field) carries the proxy/live sign conflict already flagged in knowledge/21
  (catalogue-proximate by construction vs OWNER live evidence that near-catalogue dots earn ≈0);
  a holdout pass would not be credible promotion evidence. It also needs new per-draw dynamic
  code inside the harness (1–2 days), outside the remaining budget.
* Rank 3 (RADCON-1) is a D-family derivative; family D's factorial main effect is small
  (+0.0044), the radiometric grids are uint8-percentile quantised, and X1 cross-scarp contrasts
  are already in the control. Weakest prior per unit cost.
* **MSCR-1 is a B-family derivative; B is one of only two families that "matter alone"**
  (main effect +0.0253, 4/4 folds). Its specific gap is real and checkable in code: `B_crest` /
  `B_trough` are single-scale (σ=1.5, `src/gems25/features.py`), the LiDAR descriptors summarize
  *within* one 100 m cell, and no column measures whether a topographic line persists from the
  100 m to the 400 m scale or exists only at the broad scale (graben/range-front troughs and
  crests). Static sidecar → cheap, leakage-safe, identical harness.

## The lane for experiment 2

> **MSCR-1.** Add exactly three static columns from the pinned `det_elev` band (band 12) to the
> same frozen control as Experiment 1 (H35-B configuration recomputed in the run: BDE + 7
> add-ons + `H27_tip` + 3 H34 columns), model/emission unchanged:
> with `z = nearest_fill(det_elev)`, `c1`/`c4` = percentile-scaled (1st–99th, footprint)
> `ridge_strength(z, σ)` at σ=1/4:
> 1. `MSCR_crest_s4 = ridge_strength(z, 4.0)` (raw, ≥ 0; 400 m-scale crest)
> 2. `MSCR_crest_persist = sqrt(c1 · c4)` ∈ [0,1] (line present at both 100 m and 400 m scales)
> 3. `MSCR_trough_s4 = ridge_strength(−z, 4.0)` (raw, ≥ 0; 400 m-scale trough / graben axis)
> Formulas frozen in `src/gems25/mscr.py`, unit-tested on synthetics before the fit.

**Physical signature / why catalogue-missing:** a fault-controlled range front or graben margin
is a topographic line over ~10²–10³ m of relief wavelength; at σ=1.5 px it is indistinguishable
from a gully edge, while the LiDAR within-cell step descriptors miss fronts whose individual
100 m cells are unremarkable. Broad-scale crest/trough strength + cross-scale persistence
target exactly the older, broader, or partly buried fronts that Quaternary-rupture compilation
(the catalogue) omits, while single-scale fluvial noise fails the persistence product.
**Named mimic (in advance):** lithologic strike ridges/valleys — dipping resistant beds
(hogbacks) and strike valleys eroded along soft units are persistent multi-scale lines with no
fault; fluvial terrace edges can also persist across these two scales.

## Frozen design

Identical to knowledge/21 §3 except: columns = MSCR (sidecar `mscr_columns.npy`); screen draws
**22, 23** (fresh; Experiment 1 used 20–21); confirmation draws **24, 25 only if the screen
passes** (that would be experiment 3 — then stop, whatever it says). Gate: paired mean gain
> +0.001, ≥ 3/4 folds positive, worst fold ≥ −0.010, canary max single-column AUC ≤ 0.90 read
before the gate, **and mean hug-share increase ≤ +0.10** (added because a B-family block could
win by hugging the catalogue on this proxy; hug was reported-but-not-gated in Experiment 1,
where it was −0.001). Evaluator/labels: HOLDOUT-DTI, `gems25.metric.dti_binary`
(α=0.2, β=0.8, R=3 px) via `Cell.evaluate`, withheld counts + 95 % CIs as before.

## TIF supersession (recorded before any build)

Knowledge/21 promised a GMCE-arm TIF "whatever the gate says". To keep exactly **one** obvious
primary download (the owner's requirement), that build is superseded here, before it happened:
the session's single primary TIF will be the **MSCR arm** (BEST + MSCR), built with the same
3-draw full-catalogue production protocol and identical emission. Its site/README verdict:
**promote** only if MSCR screen + confirmation + sparse-registry lane + exact-file audit all
pass; otherwise **negative — testing only, DO NOT SUBMIT**. The GMCE deliverable is its holdout
evidence + this record; no GMCE TIF will be shipped (avoiding two same-session downloads with
different verdicts was the failure mode of several earlier sessions' download folders).

Run card: `registry/run_card_gmce_2026-10-25.json` is replaced by a single session card
`registry/run_card_session_2026-10-25_gmce_mscr.json` covering both experiments (hypotheses,
mimics, HOLDOUT-DTI + CIs, canaries, lane checks, raster hashes, validator output, filename +
≤140-char note, verdict). Protocol budget after this: experiment 3 = MSCR confirmation only.
