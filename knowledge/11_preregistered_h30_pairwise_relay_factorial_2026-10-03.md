# 11 · H30 preregistration — paired fault-interaction geometry × terrain support

**Frozen before H30 code or model fits (2026-10-03 UTC).** This register is for a genuinely new feature interaction, not a relabeling of the prior family factorial, H26 add-ons, H27 tip continuation, or H29 candidate list. The prior H27 tip-only result is an unconfirmed proxy screen; it remains a comparator, not a validated candidate. No DrivenData page, leaderboard, forum, or submission endpoint was accessed.

## 1. Decision and novelty boundary

The next highest-information experiment is a **2² factorial on paired, cross-strike fault-tip bridges (`P`) and a multi-descriptor LiDAR scarp-persistence feature (`S`)**, with the previously tested H27 tip-only model included as a same-run comparator. The primary candidate is the hierarchical `P+S` arm. The design tests whether paired fault interactions and terrain support work together; it does not promise a score gain.

Repository-wide novelty review (`rg` over `knowledge/`, `src/`, `scripts/`, `evidence/`) found prior work on the five A–E feature families, generic density/orientation/coherence, gravity–magnetic/depth conjunctions, radiometric cross-scarp contrast, single-tip continuation, single-tip × broad scarp support, live-surface unions/consensus plans, and blocked external-data candidates. None implements or tests a **pairwise, cross-strike bridge field between two distinct visible-fault components**. H29-3 applies the existing single-tip feature to a different parent; it is not the paired geometry registered here.

## 2. Ranked, untried geological hypotheses

Planning brackets below are judgments for prioritization, not predictions, confidence intervals, or live-score estimates. All three are implementable from already restored, hash-pinned local layers; none requires new external bytes. Competition rasters are owner mirrors, not organizer-authenticated.

| Rank | ID | Hypothesis and layers | Physical signature / why a fault missing from the catalogue could be found | Difference from prior repository work | Planning ΔDTI / cost / status |
|---:|---|---|---|---|---|
| 1 | **H30-1 paired relay bridge × scarp support** | Visible-only catalogue endpoints (`labels.tif` after each holdout hide), plus existing DEM/3DEP-derived `L_step_max`, `L_cross_max`, `L_coh100` descriptors. | Two distinct, subparallel fault traces can end across a short cross-strike gap; a concealed splay/relay bridge in that gap may be absent from the mapped catalogue. Terrain support can corroborate a subtle continuation without requiring an emitted pixel on a known trace. Faulds & Hinz’s Great Basin inventory reports step-overs/relay ramps and other fault-interaction settings among geothermal systems; this motivates a proxy test, not a claim that hidden competition labels share that distribution. | E contains distance, orientation, density, and coherence; H27-1 tests a **single** directed endpoint continuation and broad scarp support. This hypothesis explicitly pairs endpoints from distinct components and rejects collinear single-tip continuation. Its scarp feature is `step × cross-profile evidence × 100-m coherence`, not H27’s `step × crest/trough`. | **+0.001 to +0.008** (low confidence); **~1–2 days** including the paired holdout; **selected for preregistered test**. |
| 2 | **H30-2 junction / accommodation-zone branch field** | Visible-only catalogue topology; existing B-family curvature/scarp and C-family strain-rate bands. | A hidden splay can depart from a visible multi-branch intersection or an accommodation zone, where several orientations meet, rather than continuing a single line. The feature would distinguish branch/intersection neighborhoods from simple dense-but-parallel traces. | No current E column identifies graph branch degree or multi-azimuth junctions; H27 is endpoint continuation. The factorial has only broad density/orientation terms. | **0 to +0.006** (low confidence); **~1–2 days**; viable from restored layers, not yet implemented. |
| 3 | **H30-3 scale-persistent terrain lineament** | Existing detrended elevation and 3DEP-derived LiDAR scarp/lineament descriptors at their supplied scales. | A low-relief fault-related lineament may persist in orientation and cross-profile step evidence across independent terrain scales even when any single scale is weak; persistence could help find concealed or partly eroded traces. Anthropogenic edges and channels are important false-positive alternatives. | B already supplies raw/derived terrain predictors and H27 uses one broad scarp composite, but the repository has no explicit scale-persistence score over the cross-profile and orientation-coherence descriptors. This is an incremental feature-engineering hypothesis, not a new sensor. | **0 to +0.005** (very low confidence); **~0.5–1 day**; viable from restored layers, not yet implemented. |

The evidence for structural setting is from official DOE-hosted Faulds & Hinz (2015), which reports approximate shares for inventoried Great Basin systems; it does **not** establish the distribution of the competition’s hidden fault pixels. USGS 3DEP states that its elevation products are free and without use restrictions. A separate USGS data release demonstrates scarp/tectonic-lineation mapping from 1-m 3DEP topography and derivatives, with field validation at select locations; it is a methods example outside this competition footprint, not a validation of these predictors. The exact H30 input rasters are owner-derived mirrors and their source authenticity/organizer identity remains unverified.

Previously registered but not repeated here: H26-4 stress/dilation tendency; H27-2 shallow 2-m temperature, H27-3 paleo-geothermal deposits, H27-4 heat-flow residuals; and H29-4/5 heat flow or geodetics/seismicity. H27-2/3/4 binaries have not been verified locally; no claim is made that their official listing alone establishes downloadable bytes or usable coverage. H29-1/2/3 are also prior registered ideas, not new candidates for this experiment.

## 3. Primary H30-1 feature definitions (frozen)

### Factor P — paired cross-strike bridge

For each holdout cell, use **only `draw.visible`** (the visible catalogue after both test and training hide operations):

1. Detect degree-1 pixels in the 8-neighbor visible-fault raster. Ignore tips without full 3×3 footprint support. Label visible 8-connected components.
2. Form endpoint pairs from **different** visible components with Euclidean spacing `2.0–15.0` grid pixels (200–1,500 m). Estimate doubled-angle line strike and orientation coherence at each tip by the same 2-pixel smoothed structure-tensor construction used for family E. Require both endpoint coherences ≥0.25 and `cos(2Δstrike) ≥0.5`.
3. Reject nearly collinear continuation: the pair separation must have a cross-strike component ≥0.35 relative to the mean axial strike. This makes P a paired offset/relay-gap feature, not H27’s single-tip along-strike extension.
4. Give each accepted tip-to-tip segment weight `exp(-distance/8) × clip((cos2−0.5)/0.5, 0, 1) × sqrt(coherence_1 × coherence_2) × cross_strike_fraction`. Rasterize the segment at ≤0.5-pixel spacing and expand it by a 2-pixel disk using a local maximum. Clip to the competition footprint; output finite `float32` values in `[0,1]`.
5. Do not use full-catalogue components, held-out `hidden_test`, hidden training labels, scored submission rasters, or any feature derived from them. The existing candidate-emission code continues to remove visible catalogue pixels before scoring.

If no eligible pair exists, P is the all-zero feature. Pair counts and feature nonzero fraction are diagnostic only; no thresholds may be changed after inspecting DTI.

### Factor S — terrain scarp persistence

From the existing static columns, percentile-scale with the already frozen `Context.scale` values and compute

`S = clip(scale(L_step_max) × scale(L_cross_max) × scale(L_coh100), 0, 1)`.

For reproducibility, `Context.scale` samples 200,000 footprint pixels without replacement using NumPy `default_rng(1)`, takes the 1st/99th percentiles of finite sampled values, and uses `[lo, lo+1]` if the sampled 99th percentile is not greater than the 1st. H30 uses these existing scales unchanged. The exact draw-independent scaling parameters are computed before any H30 cell fit and saved with the run diagnostics.

Replace nonfinite inputs by zero only after documenting their count; do not fill from labels. This differs from H27’s `L_step_max × max(B_crest, B_trough)`. No additional raster, outside-data download, or per-run tuning is allowed.

The fitted HGB may learn P×S splits in the both-on arm. The pre-registered 2×2 **response** interaction is separately computed from the DTI outcomes; no post-hoc feature product is added.

## 4. Holdout design and primary response

- **Screen draws:** 6 and 7, not previously executed. H27 had conditionally reserved these only if its draws 4–5 screen passed; that condition failed, so no H27 confirmation was run and these draws remain unused. **Confirmation draws:** 8 and 9, used only if the screen passes.
- **Spatial blocks:** existing NW, NE, SW, SE quadrants; 1.5-km collar; visible-only catalogue features; 20% component hide; same holdout implementation as `src/gems25/holdout.py`. These are four spatial blocks, not eight independent geographies.
- **Randomized row order:** one saved permutation of the five rows, NumPy generator seed **20261004**, reused unchanged in every fold×draw cell.
- **Model:** existing BDE feature families plus fixed H26 add-ons X1–X3; existing HGB parameters, same seeded 300,000-negative sample and common holdout draw for every arm. No parameter search.
- **Arms:** a same-run no-tip baseline (`BDE+X1–X3`), plus a complete 2² factorial over new factors P and S on top of the **H27 tip-only** control: `T`, `T+P`, `T+S`, `T+P+S`. The randomized order of all five rows is frozen in each `design.json`. The `P+S` arm is the only primary candidate; single-factor arms are diagnostic and cannot be promoted post hoc.
- **Emission held fixed:** Hessian ridge NMS σ=1 px; drop visible catalogue; top `K = round(0.035 × scored-domain pixels)`; deterministic score-ordered Poisson-disk dots at 2.4 px. The metric, crop, seed, and budget are unchanged across arms.
- **Primary response:** exact sparse-regime binary DTI in the existing metric, mean over the eight fold×draw cells. Secondary: AUC, coverage, emitted count, and hug-share (fraction within 3 px of visible faults). Report each draw and fold; factorial effects use the four fold means after averaging the two draws.
- **Factorial analysis:** coded P and S main effects and their 2-factor interaction; report DTI-unit effects, fold signs, standard error and t interval on four fold blocks. Report the interaction both as coded effect and as difference-in-differences. No claim of conventional large-sample significance from four blocks.

## 5. Frozen screen and confirmation gate

In each stage, define the paired reference per fold as the **better DTI of the two same-run controls** (`BDE+X1–X3` without H27 tip, or the H27 tip-only `T` arm), averaging the two draws within fold. `P+S` must:

1. improve over that reference by **more than 0.001 mean DTI**;
2. be positive in at least **3 of 4 folds**, with no fold worse than **−0.010**;
3. increase mean hug-share by no more than **0.10** over the same reference; and
4. pass the same gates again on fresh confirmation draws 8,9 before it can be considered for a full-data build.

This paired rule is intentional: the prior frozen 0.152003 comparator did not reproduce in H28 (0.149667 recomputed; reproduction verdict FAIL), so its absolute number is not a valid cross-run baseline. H27’s T-only mean 0.152882 (draws 4,5) is an unconfirmed historical proxy screen, not a live score and not independently comparable across new hide draws. Both are retained for context; neither replaces the same-run controls. If H30 fails either stage, report it as failed and make no TIFF from it.

Even two proxy passes are **necessary, not sufficient** for a slot. Any later full-data artifact must be built only after confirmation, carry a unique content-addressed filename and concise submission note, pass the exact competition-grid/CRS/geotransform and finite `[0,1]` audit, and beat the same-run current holdout comparator. Do not access or upload to DrivenData; the owner makes any manual submission decision.

## 6. Reproduction, source, and access record

- Official structural literature: Faulds & Hinz (2015), DOE OSTI, [https://www.osti.gov/servlets/purl/1724082](https://www.osti.gov/servlets/purl/1724082); 2013 dataset record, [https://www.osti.gov/dataexplorer/biblio/dataset/1148722](https://www.osti.gov/dataexplorer/biblio/dataset/1148722). Both were read in this session.
- Official elevation-data rights and product description: USGS 3DEP, [https://www.usgs.gov/3d-elevation-program/about-3dep-products-services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services); fault-scarp methods example, [https://www.usgs.gov/data/quaternary-fault-mapping-zapata-and-blanca-sections-sangre-de-cristo-fault-zone-high](https://www.usgs.gov/data/quaternary-fault-mapping-zapata-and-blanca-sections-sangre-de-cristo-fault-zone-high). Read 2026-10-03.
- Local inputs: restored and SHA-256 checked against `registry/data_manifest.json` via `scripts/restore_data.py --group all`; 19-band training mirror hash `4371c82e…`, label/existing-fault mirror `7ba308cc…`, LiDAR scarp descriptor mirror `d580bb8b…`. These pins prove consistency with the owner’s mirror, not organizer authenticity. All inputs remain ignored under `data/`.
- No new third-party data are needed for H30-1. The official GDR 1391 page was read and its CC BY 4.0 file listing was confirmed, but a separate H27 2-m-probe binary is not used here; a direct TLS download attempt from this sandbox failed. Do not infer bytes/schema/coverage from the listing.

## 7. Deviation and clarification log

- **2026-10-03, pre-fit implementation clarification (commit `97494c2`):** after H30 feature code was authored but before the real-data feature smoke test or any H30 model fit, the already-existing `Context.scale` procedure was written out exactly: 200,000 footprint indices sampled without replacement with `default_rng(1)`, finite-value 1st/99th percentiles, and the `[lo, lo+1]` fallback when the upper percentile is not greater. The feature transform and its use of `Context.scale` did not change; no model, DTI, or holdout outcome had been observed. The runner now records the exact three scales. This is an implementation-provenance clarification, not an outcome-driven design change.
- **2026-10-03, engineering-only smoke:** fold 0/draw 6 constructed aligned real-data feature matrices and nonempty H30 fields. No model was fitted and no DTI was evaluated; see `evidence/h30_feature_smoke.json`. No design feature, threshold, draw, metric, or gate was changed after this check.

No experimental outcome has been observed. Never alter the frozen arm matrix, features, draws, metric, or gate to fit an outcome.
