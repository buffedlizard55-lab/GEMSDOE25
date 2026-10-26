# Pre-registration: POL3 signed half-graben polarity screen (2026-10-26)

**Status:** Frozen before implementation, any standalone feature AUC computation, candidate fit, or raster emission. Hypothesis was previously listed but not run as H66-4 in `knowledge/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md`; this is a new frozen test protocol, not a claim that the geological idea was never proposed.

## Hypothesis and lane

`POL3`: faults omitted from the USGS/INGENIOUS Quaternary catalogue are more likely where a LiDAR-derived strike normal intersects a three-field polarity signature: (1) detrended surface elevation descends across the normal, (2) isostatic gravity changes in the opposite direction, and (3) conductive-basement depth deepens in the elevation-change direction. A sign-agreement composite weighted by the geometric mean of the three standardized gradient magnitudes is the detector. The fixed feature stack, visible-catalogue-only features, buffered whole-component holdout, DTI evaluator and submission writer are reused; no private fork.

**Named non-fault mimic:** basinward thickening alluvial-fan deposits / depositional onlap can co-produce a surface slope, gravity contrast and deeper conductive basement without active fault displacement. Secondary mimics include lithologic contacts and sensor/processing boundaries.

## Layers, feature definition, and leakage controls

1. Inputs are static and catalogue-free: cached `det_elev`, `iso_grav_anom`, `depth_to_base_surf`, `L_strike_c2`, `L_strike_s2`, `L_valid`. Do not read `labels.tif`, hidden components, `dist_known_fault_px`, or any held-out component geometry when constructing them.
2. Recover the undirected strike angle as `theta = 0.5 * atan2(L_strike_s2, L_strike_c2)` and set the strike-normal vector `n=(-sin(theta), cos(theta))`. A sign flip of `n` changes all three signed derivatives together and leaves the joint polarity condition invariant.
3. Gaussian-smooth each scalar field at fixed `sigma=1.5 px`; compute pixel gradients; project onto `n`. Define `g_z`, `g_g`, `g_d` as projected derivatives for elevation, gravity and basement depth. Normalize `abs(g_*)` to `[0,1]` by the fixed full-footprint 1st/99th percentiles (determined from static features only, before labels or holdout evaluation). Set the three individual canary channels to these normalized magnitudes, gated by `L_valid >= 0.5`.
4. Composite channel: `sqrt(z01*g01*d01)` where `sign(g_z)==sign(g_d)` and `sign(g_g)==-sign(g_z)`, otherwise zero; also gated by `L_valid >= 0.5`. Finite in `[0,1]` inside the footprint; no label-derived fill.
5. **Leakage canary:** each of the four added channels is scored individually on each holdout cell's withheld positives vs the fixed negative sample using the shared `Cell` and `roc_auc_score`; use `max(AUC, 1-AUC)`. Any value `>0.90` is a canary failure and stops the arm pending leakage investigation.

## Frozen holdout and comparison

- Shared evaluator: `gems25.holdout.v1.2-buffered-4quad-pooled-dti`, `hide_frac=0.20`, 4 spatial quadrants, 15-pixel buffer, whole connected catalogue components; `gems25.metric.dti_binary` with alpha `0.2`, beta `0.8`, `R=3.0 px` triangular kernel. Derive catalogue predictors only from visible components; visible known pixels masked exactly.
- **Screen**: draws `[58,59]`, all four quadrants; seed is also HGB random state. The candidate and control use identical training and test pixels, training samples, base model settings, and emission. Candidate uses H35 base (`BDE+7+H27-tip+H34`) plus four POL3 columns. Control is H35 base only. Use fixed top-candidate fraction `kfrac=0.035`, score-ordered Poisson dots `min_dist=2.4 px`, and identical visible-catalogue exclusion. No tuning after observing results.
- Report pooled HOLDOUT-DTI, total withheld positive count, 4-fold mean and 95% t-CI of paired fold gains; also per-fold gains, hug delta, and canary results. The score is a proxy for recovering withheld catalogue components, not live new-fault truth.
- **Screen gate:** all canaries `<=0.90`; candidate mean paired gain strictly `>+0.0010` HOLDOUT-DTI; `>=3/4` spatial folds strictly positive; worst fold gain `>=-0.0100`; mean hug-share increase `<=+0.10`. If any condition fails, stop. If all pass, confirmation is a second experiment on untouched draws `[60,61]` with identical code/settings and thresholds. No tuning or alternate feature definitions.
- **Confirmation / artifact gate:** candidate must also beat the same-run best control, have a paired 95% fold CI excluding zero, and meet the registered fold/hug gates. Only after that may the full-catalogue surface be computed. Compare the continuous surface against the full available registry before placement (`|Spearman| <=0.90` required); then perform final binary-dot 3-px overlap check against every registered raster (`<=70%` required). Any failed lane threshold means duplicate-lane log and stop. Exact template audit must pass before a candidate TIFF can be emitted. A pass does not authorize a weekly submission slot; selector approval is separate.

## Source and availability status

All required bands are in the restored work cache built from SHA-256-pinned **owner mirrors**, not organizer-authenticated data. Source links for manual review: [DOE GDR 1391](https://gdr.openei.org/submissions/1391), [USGS GeoDAWN](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program). The metric/competition page is referenced in `registry/sources.json`; this session will not automate access to DrivenData.

## Budget

One 2-draw screen experiment. At most one 2-draw confirmation if screen passes. No third experiment. Total wall-clock budget two hours. No weekly slot or competition upload is used by this protocol.
