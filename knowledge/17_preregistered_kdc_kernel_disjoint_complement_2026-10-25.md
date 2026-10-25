# 17 · Pre-registration — G25-K1 "Kernel-Disjoint Complement" (KDC) and the 2026-10-25 hypothesis register

**Status:** frozen and committed **before any model fit** of this design (AGENTS.md rule 4). Written 2026-10-25.
**Evidence classes:** OFFICIAL (read at cited page) · OWNER-REPORTED (score copied from the user brief; never an organizer receipt) ·
COMPUTED (script + JSON named) · INFERENCE (assumptions stated).

## 0. Why the GEMSDOE32 H33-2-B2 file got the group's highest reported score (0.2778, OWNER-REPORTED)

COMPUTED by `scripts/forensics_top_scorers.py` → `evidence/top_scorer_forensics.json` on rasters fetched by SHA-256 from the
owner's public repositories (`registry/top_scorer_sources.json`):

1. **H33-2-B2 is exactly the 0.2708 file `h27-4-r1-solo-d2-8` (GEMSDOE28 = GEMSDOE31) with every dot within 2 px (200 m) of the
   catalogue deleted** — reconstructed pixel-for-pixel (XOR = 0 of 37,654 pixels). SHA-256 `c55bafc4…` equals GEMSDOE32's own audit JSON.
2. **Every top file (0.2449–0.2778) is a ≥ 96.9 % subset of the single GEMSDOE19 surface H19-5 (0.1922).** No new detection
   happened after 30 Sep 2026: the gains came from (a) dot-thinning H19-5 to ~3 px spacing (0.1922 → 0.2477 → 0.2600) and
   (b) deleting dots near the catalogue (0.2600 → 0.2708 by ≤ 1 px; → 0.2778 by ≤ 2 px).
3. Three independent anchor pairs agree that **dots within 2 px of the catalogue have below-break-even live value**:
   d2-8 → h27-4 (−3,891 near-catalogue dots, +0.0108); h27-4 → H33-2-B2 (−2,545, +0.0070); h27-4 → h32-1 (+2,119 near-catalogue
   dots, −0.0059). INFERENCE: the hidden expert-labelled faults are depleted within ~200 m of USGS Qfaults traces (consistent with
   the rules: test labels are *newly identified* faults, catalogue pixels masked — OFFICIAL, [rules §2](https://docs.nlr.gov/docs/fy26osti/96647.pdf)).
4. **The overlooked lever.** Since H33-2-B2 every sibling (GEMSDOE70/73/82/91: exactly 37,654 dots; GEMSDOE49/76: 40,000/39,200)
   held the dot budget fixed and *swapped* 34–49 % of the dots out of the H19-5 halo; all scored lower (0.18–0.25). Swapping
   replaces above-average dots with below-average dots, so it must lose unless the new dots are better than the H19-5 ones. **Nobody
   *added* dots outside the incumbent's kernel footprint.** The DTI algebra (`src/gems25/metric.py::marginal_inclusion_ratio`) says
   adding a pixel raises DTI iff its marginal credit / marginal false-positive mass exceeds `0.2·DTI/(1−0.2·DTI)` = **0.0588** at 0.2778.

INFERENCE (assumption grid N ∈ {10k, 12.7k, 16k} hidden pixels, r = TP/Σk ∈ [1, 2.3]): B2's average dot has TP/FP ≈ 0.125–0.177, so a
complement dot is worth adding iff its efficiency is ≥ **R\* = 0.333–0.472** of B2's average (most conservative 0.472). The swap files
imply (fixed-denominator approximation, DTI ∝ TP at equal dot count) that their off-H19-5 dots earned ≈ 0.70 (GEMSDOE70, GEMSDOE49)
down to ≈ 0.17 (GEMSDOE82) of B2's per-dot credit — i.e. **good complement dots exist above R\***, and were being used to *replace*
rather than *add*. This is a model-based reading of owner-reported scores, not a measurement.

**Can we beat 0.2778?** Only by adding credit outside the H19-5 halo at efficiency ≥ R\*. Under the stated algebra, adding 17,720
complement dots at efficiency 0.70 × B2 would give ≈ 0.307; at 0.50 × ≈ 0.286; at 0.30 × ≈ 0.264 (a loss). These are projections,
**never scores**.

## 1. Hypothesis register (new in this repository; ranked by expected ΔDTI × validatability ÷ cost)

| Rank | ID | Layers | Physical / statistical signature | Why it targets catalogue-missing faults | Difference from repo + sibling registry | Expected ΔDTI (bracket, not a forecast) | Cost | Validatable now? |
|---|---|---|---|---|---|---|---|---|
| 1 | **G25-K1 KDC** | full BDE + 7 add-on stack (HGB, visible-catalogue features only) + H19-5/B2 as an exclusion mask | HGB ridge (NMS) dots placed **> 3 px from every incumbent pixel and > 2 px from the catalogue**, *added* to the incumbent rather than swapped | H19-5 is "multiline corroborated": a corroboration filter is precise but structurally rejects faults expressed in only one field. KDC spends budget only where the incumbent has zero kernel coverage, and never near catalogue traces (finding 3) | No registry file adds dots outside the H19-5 halo at scale (forensics: top files ≤ 3.1 % outside; swap files *replace*). Budget re-optimisation after B2 is untried | −0.01 … +0.03 | low (reuses cache, holdout, writer) | **yes** (relative efficiency on hide-and-recover) |
| 2 | G25-K3 single-field blind-basin complement | `rtp` gradient × (1 − local relief of `det_elev`) (GEM-1 surface) | magnetic-block juxtaposition with no scarp | concealed faults lack Quaternary scarps → absent from Qfaults by construction | GEM-1 surface exists (PR #12) but only as a stand-alone emission; here it is a secondary *complement detector* arm | −0.01 … +0.01 | low | yes (secondary arm) |
| 3 | G25-K2 geodetic strain-deficit prior | `geod_2ndinv`, `geod_shearrate` vs catalogue density at 20–50 km | where geodetic strain rate is high but mapped Quaternary faults are sparse, unmapped faults must carry the deformation | targets catalogue gaps by definition | repo uses geodetic bands and catalogue density only pointwise; no deficit ratio anywhere | unknown | low | **no**: hide-and-recover truth is catalogue-distributed, so the proxy structurally cannot reward a deficit prior → needs a live slot; not proposed for a slot |
| 4 | G25-K4 pluvial-shoreline false-positive suppression | absolute elevation (NOT in the cache: band `det_elev` is detrended) + scarp candidates | Lake Lahontan highstand wave-cut benches (~1,330 m, [USGS Benson & Thompson 1987](https://pubs.usgs.gov/publication/70015223); 1,318–1,341 m after isostatic rebound, [Adams & Wesnousky 1998](https://pubs.geoscienceworld.org/gsa/gsabulletin/article/110/10/1318/183306/)) mimic fault scarps in lidar/DEM; contour-parallel candidates in that band are likely shorelines | frees budget from a named non-fault mimic | no shoreline mask anywhere in the repo | unknown | medium + data | **no**: needs absolute DEM — free official source USGS 3DEP via The National Map (<https://apps.nationalmap.gov/downloader/>); not reachable from this sandbox (host not allow-listed) → blocked, not viable here |

Not proposed (already owned by another lane): deeper catalogue-distance pruning (GEMSDOE32 H33 lane; `prune400` built there today),
tip/step-over additions (GEMSDOE28/33), swap-at-fixed-budget (GEMSDOE49/70/76/82/91).

## 2. Frozen design — experiment E1 (screen) and E2 (confirmation)

* **Holdout:** `src/gems25/holdout.py` hide-and-recover, 4 spatial quadrant folds, `hide_frac` 0.20 of whole 8-connected catalogue
  components, 1.5 km collar, catalogue features from visible faults only, visible faults masked pixel-exactly, exact DTI
  (`gems25.metric.dti_binary`, α 0.2, β 0.8, 300 m triangular kernel). Screen = draws 0, 1; confirmation = draws 2, 3 (only after a screen pass).
* **Model:** one HGB fit per (fold, draw) on BDE + 7 add-ons (`run_h28_holdout.BASE/EXTRAS`, seed = draw) — identical to the H28/H31 comparator.
* **Arms (all from the same fit):**
  * `C` comparator: top-K ridge candidates (kfrac 0.035), score-ordered dots 2.4 px. Must reproduce `evidence/h28_holdout/cells.jsonl` (≤ 1e-6).
  * `CB`: C minus every dot ≤ 2 px from the visible catalogue (incumbent recipe analogue).
  * Exclusion zone `X` = within 3 px of any of C's raw top-K candidates (the analogue of the undotted H19-5 surface) ∪ within 2 px of
    the visible catalogue ∪ outside the eroded domain.
  * `K_self` (**primary**): CB + M complement dots, M = round(0.4706·|CB|) (CB share 68 %, the lane margin), chosen as score-ordered
    2.4 px dots among HGB ridge-NMS pixels outside X.
  * `K_gem1` (secondary): CB + M dots from GEM-1 surface ridge-NMS pixels outside X (score-ordered, 2.4 px).
  * `K_rand` (negative control): CB + M score-ordered 2.4 px dots on a seeded uniform-random score over all pixels outside X.
* **Responses per cell:** DTI, TP, FP, n_truth (withheld positives), emitted; complement efficiency
  `R = (ΔTP/ΔFP) / (TP_CB/FP_CB)` with Δ relative to CB.
* **Leakage canary:** AUC* = max(AUC, 1−AUC) of every single model column, of the model score and of GEM-1, vs hidden test truth on the
  cell's AUC sample. Any AUC* > 0.90 ⇒ leakage until proven otherwise ⇒ stop.
* **Gate (primary K_self; all must hold on the screen AND again on the confirmation):**
  1. Paired vs the same-run best control (`C` or `CB`, whichever has the higher mean): mean gain > +0.001, ≥ 3/4 folds positive, worst fold ≥ −0.01.
  2. Pooled R ≥ **0.50** and R ≥ 0.50 in ≥ 3/4 folds (live break-even R\* ≤ 0.472 rounded up).
  3. Informativeness: pooled R of `K_rand` < 0.50 (otherwise the R gate is uninformative and the run is void).
  4. Leakage canary clean.
* **No tuning on outcomes:** M, spacing, exclusion radii, thresholds are fixed here. A failed arm stays failed.

## 3. Experiment E3 (only if E1 and E2 pass) — build, lane check, validate

* Full-catalogue HGB (BDE + 7, 3 pseudo-new draws, `scripts/build_candidate.py` code path) → probability → ridge NMS.
* Complement pixels: footprint, not catalogue, > 2 px from the catalogue, > 3 px from every H19-5 pixel (which contains all B2 dots),
  score-ordered 2.4 px dots, best M = 17,720 (so the 37,654 B2 dots are 68.0 % of the file).
* Final file = H33-2-B2 dots (owner's same-team artifact, disclosed) ∪ complement; value 1.0 at dots, 0.0 elsewhere in the footprint.
* LANE (PARALLEL-RUN PROTOCOL): pre-placement Spearman of the HGB surface vs every registry raster; final-file Spearman and the
  fraction of final dots within 3 px of each registry raster's dots. Caps 0.90 / 70 %. The 13GEMSDOE 5-px lattice is degenerate
  (every pixel lies within ≈ 3.5 px of it) and is reported but not used as a lane criterion (IR-25-LANE-DENSITY).
* Validator: `gems25.submission.check_file` (single band, float32, EPSG:32611, 3730 × 3292, template transform, all footprint values
  finite in [0, 1]). Primary file = **zeros outside the footprint (no NaN anywhere)** because the scored H33-2-B2 upload was the
  `-zeros` variant.
* Verdict "promote" means: OK to download and eligible for the separate selector step. It never means an upload was made.


---
**Outcome (appended after the run; the frozen text above is unchanged):** NEGATIVE. See `knowledge/19_kdc_results_2026-10-25.md` and `registry/run_card_kdc_2026-10-25.json`.
