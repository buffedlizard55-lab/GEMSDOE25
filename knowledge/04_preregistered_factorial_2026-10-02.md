# 04 · Pre-registration — fractional factorial across the five feature families (frozen 2026-10-02, before any run)

Status: **frozen before execution**. Anything that deviates is reported as a deviation in
`evidence/factorial/results.json` (`deviations` field), never silently changed.
Method source: Box, Hunter & Hunter, *Statistics for Experimenters* (2nd ed., Wiley 2005) — fractional
factorials, aliasing/resolution, sparsity of effects; Lenth (1989) *Technometrics* 31:469-473 for unreplicated
screening designs. (Textbook content is cited from memory of the method; the repository's tests verify the
arithmetic — orthogonality, aliasing, effect recovery, Lenth's rule — not the book's page numbers.)

## 1. Question
Which feature families carry detection signal **alone**, which only **in combination** (interaction), and which
are **inert** — decided by a pre-specified design, not by which conjunction sounds geologically plausible.

## 2. Factors (two levels: family excluded = −1, included = +1)
Columns come from `src/gems25/families.py` (single source of truth; 64 static + 7 per-draw columns).

| Factor | Family | Columns (n) |
|---|---|---|
| A | potential-field gradients | gravity & magnetic bands + tilt, analytic signal, Hessian ridge "worms" (16) |
| B | DEM curvature / scarp | detrended elevation, slope, 100 m curvature/TPI/relief/crest/trough + 13 3DEP-LiDAR scarp descriptors (24) |
| C | strain / seismicity | 3 geodetic strain-rate invariants, 2 earthquake bands, 2 strain-gradient edges (7) |
| D | thermal / geochemical | radiometric `tc`, K/Th/U + ratios + ratio edges, MT conductivity, GDR 1391 spring/well proximity, density, Tmax, quartz geothermometer (17) |
| E | catalogue geometry | distance, nearest-fault orientation, 3 densities, orientation coherence — from the **visible** catalogue only (7) |

## 3. Design
2^(5−1), generator **E = ABCD**, defining relation **I = ABCDE**, **Resolution V**, 16 runs. All 5 main effects
and all 10 two-factor interactions are estimable; each main effect is aliased with a 4-factor interaction and
each two-factor interaction with a 3-factor interaction (assumed negligible by sparsity of effects). Every run
has 1, 3 or 5 active families (never 0). Execution order is randomised (seed 20261002) and recorded.

## 4. Response and the hide-and-recover cell
* Cell = (test quadrant k ∈ {NW, NE, SW, SE}) × (draw d ∈ {0, 1}); 8 cells per run; 128 model fits. The
  same cells are used by every run (common random numbers; folds are blocks).
* Draw: hide whole 8-connected catalogue components until 20 % of catalogue pixels are hidden in the test
  quadrant (these are the "new faults") and, separately, 20 % in the training region (pseudo-new positives);
  the rest stays **visible** and is masked in scoring (staff, thread 11516). 1.5 km collar; components touching
  the collar are never training positives; catalogue-geometry features use visible faults only.
* Model: `HistGradientBoostingClassifier(max_iter=100, learning_rate=0.12, max_leaf_nodes=31, min_samples_leaf=50,
  l2_regularization=1.0, class_weight={0:1, 1:5}, early_stopping=False)`, trained on all pseudo-new positives of
  the training region + 300 000 random non-catalogue pixels (>1.5 px from positives), same sample for all runs.
* Fixed emission for every run: Hessian ridge NMS (σ = 1 px) → drop visible-catalogue pixels → top 2.45 % of the
  scored domain (the H19-5 budget) → deterministic Poisson-disk dotting at 1.5 px (`dot_thin`, the transform
  behind the 0.2477 file). Scored domain = quadrant eroded by 12 px (NMS halo).
* **Primary response: exact sparse-regime DTI** (`gems25.metric.dti_binary`; known pixels masked) averaged over
  cells. Secondary: AUC of the raw score for hidden-vs-random pixels; emitted pixels; credit coverage;
  **hug-share** (emitted pixels within 3 px of the visible catalogue — the signature of the live failures,
  ≥45 % of off-catalogue emission scored ≤ 0.046 in the group's record).
* Same-harness reference rows: unsupervised topographic ridge (U-topo), unsupervised potential-field ridge
  (U-geo), random ridge-free dots at equal budget (null).

## 5. Analysis (frozen)
1. Contrast estimates of 5 main effects + 10 two-factor interactions on the run means; also per fold (mean of the
   2 draws), giving mean, SE (n = 4 folds, t on 3 d.f.) and the number of folds with positive sign.
2. Lenth pseudo standard error, ME and SME at α = 0.05 on the 15 pooled contrasts.
3. Classification rule (applied mechanically):
   * **matters alone** — main effect > 0, |effect| > ME, positive in ≥ 3 of 4 folds;
   * **matters in combination** — fails the above alone, but belongs to a two-factor interaction that is > 0,
     |effect| > ME and positive in ≥ 3 of 4 folds;
   * **harmful** — main effect < −ME;
   * **inert** — none of the above.
4. Report effects in DTI units and as a percentage of the all-families run.
5. Confirmation (BH&H practice): one fresh-draw replicate (draws 2, 3) of (i) the all-families run, (ii) the
   model-predicted best subset, (iii) the best single family. The prediction (additive + 2fi model) is
   published before the confirmation runs; the residual is reported.

## 6. Candidate gate (pre-registered; no weekly slot otherwise)
A candidate surface/emission must, in the same harness and paired cells, beat its comparator by > 0.001 mean
sparse DTI, win in ≥ 3 of 4 folds, and lose no fold by > 0.01. The comparator is the best same-harness row
(all-families run or the dotted-H19-5 diagnostics, whichever is higher). A pass is **necessary, not sufficient**:
on 24 scored artefacts the group measured Spearman +0.33 (n.s.) between catalogue-gap proxies and live score.

## 7. Known limits stated in advance
* The catalogue is not new-fault truth; hidden components are a *catalogue-gap* simulation.
* Family E may be flattered by the simulation (faults cluster; hidden and visible components are neighbours).
  If E's apparent gain comes with a high hug-share it must NOT be used for a live slot.
* H19-5 as emitted is *not* an out-of-fold surface (it saw the whole catalogue); it is reported only as a
  diagnostic and never as a beaten baseline.
* No score is promised. Unknowns stay unknown.

## Supersession note for current slot decisions (2026-10-02)
This document records an earlier factorial gate and remains the historical preregistration for those runs. Its same-harness candidate gate is not a substitute for the current rule: a specific candidate must beat the current spatially blocked holdout best, pass its paired/confirmation criteria, and pass the exact-file audit before any weekly slot is considered. No exception is authorized; see `AGENTS.md`, `knowledge/09_preregistered_hypotheses_2026-10-02.md` and the current `registry/submissions.json`.
