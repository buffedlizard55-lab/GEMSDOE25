# 03 · Candidate hypotheses not yet tried — ranked (written 2026-10-02, BEFORE any add-on run)

**Evidence classes.** READ = text I read at the cited official page this session · COMPUTED = reproducible in this repo ·
INFERENCE = my reasoning, assumptions stated. *Novelty is relative to the reviewed code and registers* (this repo and
GEMSDOE24's `knowledge/01,02,05,07` + `evidence/group_review.json` summaries of 19/16/20/13 GEMSDOE); it is not a claim about
other competitors. Expected-gain figures are ordinal planning judgments, **not forecasts**; no score is promised.

**Context that constrains every hypothesis (READ).** The test labels are *new* faults, "any fault pixel not already captured by
USGS/INGENIOUS", including "corrections or modifications" within 300 m of known traces; known pixels are masked and
near-known-but-wrong pixels are fully penalised ([staff, thread 11516 #4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4)).
A candidate therefore has to be informative about faults **away from** the catalogue. Geothermal motivation (READ, Faulds & Hinz 2015,
[OSTI 1724082](https://www.osti.gov/servlets/purl/1724082)): of 426 known systems ≥37 °C ~39 % are blind; step-overs/relay ramps host ~32 %,
fault terminations 25 %, intersections 22 %, accommodation zones 9 %; "geothermal systems are rare along major range-front faults".

## Ranking

| Rank | ID | One line | Layers | Expected ΔDTI (ordinal) | Cost | Validatable now? |
|---|---|---|---|---|---|---|
| 1 | **H26-0** | Score-aware Poisson-disk dotting + marginal-ratio budget | any continuous surface | +0.005…+0.02 (direct live evidence for the mechanism: dotting alone gave 0.1922 → 0.2477) | hours | **yes** — paired, equal-N |
| 2 | **H26-2** | Strike-compatibility prior | DEM line orientation × visible-catalogue strike field | 0…+0.01 | ~1 day | **yes** |
| 3 | **H26-1** | Oriented cross-scarp radiometric contrast (conjunction) | GeoDAWN K, Th/K, U/K × DEM gradient normal | 0…+0.02 (uncertain) | ~1 day | **yes** |
| 4 | **H26-3** | Concealed joint step (gravity ridge ∧ magnetic ridge ∧ basement-depth gradient) | iso-gravity HG, TMI HG, depth-to-base | small | ~1 day | **yes** |
| 5 | **H26-4** | Dilation-tendency-weighted orientation prior | USGS slip/dilation tendency + stress data (new) | 0…+0.01 | ~2 days + fetch | **no** — needs external data (see below) |

Ranking criterion: (expected gain × probability that the hide-and-recover proxy can validate it) ÷ cost. H26-0 is first only
because it is the single item with direct live evidence; it is *not geology* and cannot find a fault — it lowers the price of every
candidate trace.

## H26-0 — score-aware Poisson-disk dotting and a marginal-ratio budget (generation system, not geology)
* **Layers:** none new — a transform of a continuous score surface.
* **Signature:** the metric credits a truth pixel `1 − d/3` from the nearest emitted pixel but charges every emitted pixel's false-positive
  mass; adding a pixel helps iff (extra credit)/(extra FP mass) > `0.2·DTI/(1−0.2·DTI)` ≈ 0.052 at DTI 0.2477 (COMPUTED identity,
  `gems25.metric.marginal_inclusion_ratio`). The 0.2477 file is `dot_thin(H19-5, 1.5)`: score-blind, anchored at each component's first raster pixel.
  Keep the **highest-scoring** pixel of each neighbourhood instead, and choose K where the marginal ratio meets the threshold.
* **Why it catches faults missing from the catalogue:** it does not find them; for any set of candidate traces it raises credit per false-positive pixel.
  Emission never touches catalogue pixels (masked anyway).
* **Difference from the repo:** `dot_thin` (GEMSDOE24) and the greedy kernel-cover control are score-blind; no sibling applies score-ordered dotting.
* **Validation:** equal-pixel-count paired comparison vs `dot_thin` on the factorial-best surface (pre-registered in `05_preregistered_addons_*`).

## H26-2 — strike-compatibility prior
* **Layers:** DEM line orientation (structure tensor of detrended elevation, 100 m) × orientation of the nearest **visible** known fault (catalogue only through its strike field).
* **Signature:** `cos 2(θ_candidate − θ_nearest-known)` — near-parallel lineaments in a structural domain are fault-like; roads, mine benches, shorelines and
  channel banks have unrelated strikes (INFERENCE; roads/benches can also follow terrain).
* **Why it catches missing faults:** the prior is the *domain's strike family*, not the traces themselves, so it up-weights unmapped traces of the same family and does not reward
  sitting on known pixels (hug-share is reported).
* **Difference:** orientation exists only as raw tree features in sibling pipelines; GEMSDOE24 lists "strike-compatibility prior" as top geological item **not yet run**.

## H26-1 — oriented cross-scarp radiometric contrast (a conjunction, i.e. an interaction)
* **Layers:** GeoDAWN K, Th/K, U/K grids (USGS release DOI 10.5066/P93LGLVQ, via the pinned mirror) × DEM gradient normal.
* **Signature:** `|v(x + 3 n) − v(x − 3 n)|` of each radiometric field across the local topographic edge normal `n`: a fault scarp can juxtapose different soils / alluvial ages / bedrock and
  hydrothermal alteration changes K, while a road cut or channel bank makes a topographic step with no radiometric step (INFERENCE).
* **Why it catches missing faults:** needs two physically independent observables to agree on one oriented edge; neither is the catalogue.
* **Difference:** siblings use radiometric channels pointwise or as isotropic edge magnitude (here `D_ThK_edge`, `D_UK_edge` in family D); the oriented contrast conditional on the topographic normal is new.
  This is exactly the "weak alone, diagnostic jointly" case that the factorial's B×D interaction measures at family level.

## H26-3 — concealed basin-margin joint step
* **Layers:** isostatic-gravity horizontal-gradient ridge, TMI horizontal-gradient ridge, `depth_to_base_surf` gradient (competition bands).
* **Signature:** coincident ridges of two potential-field gradients (different physical properties, different depth sensitivity) plus a basement-depth step.
* **Why it catches missing faults:** buried range-front / intra-basin faults without a scarp are not mapped as Quaternary faults; coincidence suppresses single-field noise.
* **Difference:** potential-field bands enter siblings only as raw channels or single-field worms; GEMSDOE24 lists "concealed basin-margin step" as small/uncertain, untested.
  READ caution (Faulds & Hinz): geothermal systems are rare along *major range-front* faults — this signature may preferentially hit the least geothermal-relevant faults.

## H26-4 — dilation-tendency-weighted orientation prior (needs external data — obtainability checked)
* **Layers:** USGS "Shapefile for slip tendency and dilation tendency calculated for Quaternary faults in the Great Basin" (Siler 2022, DOI 10.5066/P9YL58W6) — fault geometry **and the stress data used**.
* **Signature:** replace the learned strike family of H26-2 by the *physical* dilation tendency of a candidate's strike under the regional stress field (faults well oriented to dilate are likelier conduits).
* **Obtainability (READ at [ScienceBase item 6296974dd34ec53d276bb33d](https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d)):** free USGS data release; files listed: `Shapefile_INGENIOUS area.zip` 27.35 MB, `Shapefile_Full Study.zip` 34.25 MB, KMZ versions, FGDC metadata.
  **Not downloaded here**: `sciencebase.gov` is unreachable from this sandbox (TLS reset), so it is *obtainable but unvalidated*; viable only after a networked fetch (GitHub Actions). Not proposed for a weekly slot.
* **Difference:** physical stress-conditioned orientation prior; the repo has no stress-field feature (the geodetic bands are scalars).

## Deferred (named, not ranked)
* **Drainage-offset / knickpoint concordance** (raw 10 m / 1 m 3DEP) — high cost, needs byte-verified coverage; carried over from GEMSDOE24 (H24-6).
* **Scarp cross-profile template on raw 1 m DEM** — highest ceiling, needs CI over 706 tiles; the mirror stores only per-100 m descriptors, which cannot support profile templates.

---
## Addendum (written AFTER the runs; the register above is unchanged since its commit)

### Validation outcomes on the spatially blocked hide-and-recover holdout (frozen gate; details in `07_findings_2026-10-02.md`)
| ID | Outcome (draws 0,1, base BDE) | Status |
|---|---|---|
| **H26-0** score-ordered dotting | +0.0037 vs score-blind `dot_thin` at equal pixel count, 4/4 folds, t = 8.5 (3 d.f.) | **passes the gate** — the top-ranked candidate is validated; it needs a *continuous* surface, so it is used by the exploratory file, not by the binary H19-5 file |
| H26-2 strike compatibility | +0.0015, 2/4 folds | fails alone |
| H26-1 oriented cross-scarp radiometric contrast | +0.0006, 2/4 folds | fails alone |
| H26-3 concealed joint step | +0.0003, 2/4 folds | fails alone |
| H26-1+2+3 together | +0.0050, 4/4 folds, t = 1.97 (weak) | passes the gate jointly (confirmation: see `07_*`) |
| H26-4 dilation-tendency prior | not run | **not validatable here**: needs the USGS shapefile (free, 27 MB, obtainable) but `sciencebase.gov` is unreachable from this sandbox; not proposed for a slot |

### Continuity with the previous GEMSDOE25 session's list (README @ 9b01f27)
* its #1 "calibrated factorial ensemble" → executed (the 2^(5−1) design, E/B active);
* its #2 "strike-compatibility prior" → this register's H26-2 (tested, fails alone);
* its #3 "scarp cross-profile template (1 m 3DEP)" → still deferred: needs raw tiles on a networked runner;
* its #4 "map-scale correction corridor (INGENIOUS MAPSCALE)" → not tested: needs a per-pixel map-scale raster from GDR 1391 Qfaults (CI fetch);
* its #5 "concealed basin-margin step" → this register's H26-3 (tested, fails alone).

### Untested strategy ideas recorded for the next session (not hypotheses about geology)
* **H26-7 consensus-ordered dotting** — keep H19-5's *candidate set* (live-validated detections) but choose the dots inside each neighbourhood by an independent out-of-fold surface. Equal pixel count, so no credit/false-positive trade-off is introduced; if the surface is uninformative within H19-5's neighbourhoods it is a no-regret re-selection. Needs the full-footprint score vector from `build_candidate.py --keep-scores`; protocol: paired vs `dot_thin` and vs random-score dotting at equal N.
* **Consensus pruning** (drop dots a second detector rejects) needs a strongly informative second detector: `evidence/emission_model.json → consensus_pruning_break_even` shows the dropped dots must carry < ~52 % of the average credit per pixel.
* **Phase-2 aware final choice** (INFERENCE): the final round re-scores against labels expanded by expert review of *all* submissions, so crisp, expert-verifiable lineaments may be worth more there than the Phase-1 optimum; this cannot be tested before the experts act.
