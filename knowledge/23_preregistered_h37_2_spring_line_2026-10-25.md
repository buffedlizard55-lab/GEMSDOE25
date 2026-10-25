# 23 · Pre-registration H37-2 — spring-line alignment ridge (experiment 2, 2026-10-25)

**Amendment disclosure.** knowledge/22 §3 said "No other experiment is run this
session unless A37 passes both stages." A37 failed its screen (paired −0.000883,
2/4 folds; `evidence/h37_screen/analysis.json`, commit 9724485). That sentence was
stricter than this repo's standing rules (AGENTS.md rule 4 forbids tuning a failed
arm; it does not forbid a *separately pre-registered* experiment — the H34→H35 and
KDC E1→E2 sessions both ran a second pre-registered experiment after a failure,
within the protocol budget of 3). This document therefore **amends that one
sentence**: experiment 2 below was already ranked (#2) in knowledge/22 before any
H37 fit, uses fresh draws, and its formulas/gate are frozen here, before the
spring features are computed on real data. H37-1's failed arm is untouched and
stays negative. The deviation is recorded in the session run card
(IR-25-H37-AMENDMENT). No H37-1 lag, direction, or field is retried.

## Lane (single method paragraph, experiment 2)

> **H37-2 SPR — spring-line alignment ridge.** Add exactly two static columns to
> the same H35 arm-B detector (comparator C37 recomputed same-run; HGB/emission
> frozen as in knowledge/22). From the GDR 1391 well/spring points already pinned
> (`data/external/gdr_wellspring_in_footprint.csv`, SHA-256 in
> `registry/data_manifest.json`), take the `thermalclass == "Hot"` points
> (1,994 rows, 929 unique pixels; label-free input inventory computed before this
> document). Build a count grid, KDE with Gaussian σ=3 px, normalize by its
> footprint maximum → `k`. Columns:
> **`SPR_kde_ridge` = ridge_strength(k, 1.5)** and
> **`SPR_ridge_x_elong` = SPR_kde_ridge × coherence**, where coherence is the
> structure-tensor coherence of `gaussian_filter(k, 2)` with tensor smoothing
> σ=2: `sqrt((Jxx−Jyy)² + 4Jxy²) / (Jxx+Jyy+1e-12)`, clipped to [0,1], and 0 where
> `Jxx+Jyy == 0`. The CSV's label-derived `dist_known_fault_px` column is NOT
> used (as in `gems25.features._gdr_features`).

Physical target: aligned hot-spring discharge along a permeable, possibly
unmapped fault — a ridge/elongation in the spring density field, not merely
spring proximity. Family D already uses these points isotropically
(distance-to-hot, σ=20 px KDE, 5 km max temperature); no alignment statistic of
the point field exists in this repo.

**Named non-fault mimics:** fan-toe and lithologic-contact spring lines
(groundwater emerges along permeability contrasts with no fault), valley-floor /
road-biased well and spring sampling, and spring clusters around a single
geothermal field's infrastructure.

## Frozen design

* Arms: `C37` (H35-B, same-run recomputed) vs `A37S` (C37 + 2 SPR columns
  appended after the H34 columns). Same `Cell(extras=True, h27=True)`, same
  train sample, HGB `random_state=draw`, emission sapd2.4 / kfrac 0.035.
* Cells: folds NW/NE/SW/SE × screen draws **18, 19** (unused; verified by grep
  as in knowledge/22). Confirmation draws **20, 21 only if the screen passes**.
* Leakage canary: each SPR column alone per cell; max(AUC, 1−AUC) > 0.90 → stop,
  negative. (A high canary here would mean the spring compilation itself was
  collected along mapped faults — proxy inflation, treated as leakage per protocol.)
* Gate (each stage separately): mean paired gain > +0.001, ≥3/4 folds positive,
  worst ≥ −0.010, mean hug increase ≤ +0.10. Report fold-mean + pooled
  HOLDOUT-DTI, 95 % CI (t, 4 folds), withheld positives per fold, evaluator id.
* TIF policy (knowledge/22 §5 unchanged): the session's unique downloadable TIF
  is the A37S full build **only if** A37S passes screen+confirmation and the
  lane/exact-file audits; otherwise the already-run A37 (H37-1) full build is the
  session file, labelled negative / DO NOT SUBMIT, and no A37S TIF is built.
  This keeps exactly one new file for the session, chosen by the frozen gates —
  not by which outcome looks better afterwards.
* Budget: this is experiment 2 of 3. If A37S fails its screen, experiments stop;
  no third experiment is run (remaining session time goes to the TIF, audit,
  site, and review passes).
