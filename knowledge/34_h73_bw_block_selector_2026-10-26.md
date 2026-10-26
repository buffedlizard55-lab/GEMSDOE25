# H73-BW 25-km block-withheld selector — pre-registration and blocked preflight

**Date:** 2026-10-26 (UTC)
**Status:** conditional diagnostic **GO**, pre-registered before any H73-BW fit; execution **BLOCKED_BEFORE_FIT** because the required shared cache is absent. No fit, H73-BW holdout score, candidate surface, or new GeoTIFF was produced in this checkout.
**Predecessor:** H73-PM failed the strict component-split far-field screen against H35, but showed a far-field gain over the catalogue-free control; this distinction resolves the conditional H73-BW plan in [`knowledge/32_preregistered_h73_pm_2026-10-26.md`](32_preregistered_h73_pm_2026-10-26.md), §1–2, versus the blocking-instrument priority in [`knowledge/33_h73_outcomes_and_executive_summary_2026-10-26.md`](33_h73_outcomes_and_executive_summary_2026-10-26.md), §4.
**Run card:** [`registry/run_card_h73_bw_2026-10-26.json`](../registry/run_card_h73_bw_2026-10-26.json)
**Shared evaluator:** [`src/gems25/block_holdout.py`](../src/gems25/block_holdout.py) (the new selector split reuses `Holdout` primitives without changing its historical source hash) and [`src/gems25/metric.py`](../src/gems25/metric.py).

## 1. Scope and method-lane ambiguity

The preserved active brief refers to a “single method paragraph below,” but no distinct paragraph selecting a method is identifiable in the checked-in prompt/README or the carried-forward task. This is recorded rather than silently guessed. The conservative interpretation for this selector is: **H73-PM is the only pre-existing candidate method; H73-BW changes only the holdout geography and is an evaluation instrument, not a new geological detector, feature set, output surface, or submission lane.** It adds no new geological hypothesis and does not authorize a TIF or weekly slot. The prior H73-PM method and its negative result remain unchanged.

The earlier H73 planning slate [`knowledge/32_preregistered_h73_pm_2026-10-26.md`](32_preregistered_h73_pm_2026-10-26.md) ranks the geological candidates. Three still-untried planning hypotheses are also recorded in [`knowledge/29_download_audit_and_next_hypotheses_2026-10-26.md`](29_download_audit_and_next_hypotheses_2026-10-26.md): (1) multi-scale oriented magnetic phase congruency with along-strike radiometric texture continuity and across-strike mismatch; (2) two-scale piecewise-planar basement/elevation/gravity ramp versus smooth quadratic basin; and (3) paired opposed scarp-normal steps bounding a graben, with a magnetic line on one flank. These remain **planning hypotheses, not approved or validated experiments**; H73-BW does not relabel or fit them.

## 1a. Resolve the H73-BW go/no-go wording

The two source statements set different thresholds and are not treated as interchangeable:

- `knowledge/32` §1 ranks H73-BW as useful only if rank-1 H73-PM “shows far-field signal”; §2 separately defines the **stronger candidate-screen gate** as beating both `CTRL_H35` and `CTRL_BLIND_BD` in far-field HOLDOUT-DTI. H73-PM is `0.082120` vs blind `0.075379` (**+0.006740**, 3/4 folds positive; 46.4% of emissions >20 px), but `0.097871` for same-run H35. Thus it shows signal over blind and meets the rank-2 diagnostic precondition, while failing the stronger H73-PM far-field screen and all promotion/slot gates.
- `knowledge/33` §4 calls the block selector the single blocking instrument. We interpret that as prioritizing **one diagnostic holdout-only test** of whether adjacent-component leakage explains the H73-PM/H35 contrast—not as permission to override the failed H73-PM gate, run its unapproved confirmation, or build/submit a raster.

**Decision: GO for this one pre-registered H73-BW diagnostic only; NO-GO for H73-PM confirmation, geological feature changes, full-footprint build, TIF creation, or a slot.** The selector changes only the evaluation split and re-scores the same three arms on identical cells. If the shared-cache preflight fails, stop before fit; do not rebuild. This is the conservative reading that honors both the rank-2 precondition and the stricter frozen promotion gate.

The carried-forward prompt's separate “single method paragraph below” remains unidentified. For this registered diagnostic only, H73-PM stays the sole candidate method and H73-BW is strictly the holdout instrument. If that missing paragraph is located before execution, reconcile it before continuing.

## 2. Frozen design

- **Purpose:** test whether the H73-PM propensity-matched model’s far-field signal persists when catalogue components in held-out geography are completely unavailable. This specifically addresses adjacent-fragment leakage in the component-split evaluator; it is not live-score calibration.
- **Grid and blocks:** the pinned study grid is 100 m. A 25-km block is therefore 250 pixels. Anchor the square grid at raster pixel `(row=0, col=0)`. For block row `br = row // 250` and column `bc = col // 250`, assign checkerboard fold `2 * (br mod 2) + (bc mod 2)`, yielding four interleaved fold colors. Outside-footprint pixels receive fold `-1`.
- **Truth hiding:** for a test fold, hide **every complete 8-connected catalogue component that intersects any test block**, including its portions crossing block edges. Do not sample a 20% subset of test components. The inherited 15-pixel (1.5-km) dilated collar excludes nearby components and pixels from training. In the remaining training region, sample pseudo-new positive components using the established 20% hide fraction. Features from catalogue geometry must use only the resulting visible catalogue; visible catalogue pixels are masked exactly during scoring.
- **Draws:** `94` and `95`; four checkerboard folds per draw. These are fresh relative to H73-PM draws `90–91`; draws `92–93` remain unused because the prior frozen H73-PM gates failed.
- **Arms, paired within each fold/draw:**
  1. `CTRL_H35`: same-run incumbent H35 (`BDE + EXTRAS + H27_tip + H34`), uniform training-negative sampler, unchanged H35 emission (`kfrac=0.035`, minimum spacing `2.4 px`, no additional catalogue buffer).
  2. `CTRL_BLIND_BD`: same-run catalogue-free control (`BD + EXTRAS + H34`), uniform sampler, unchanged de-apron emission (`kfrac=0.030`, spacing `2.8 px`, catalogue buffer `2.0 px`).
  3. `PM_DEAPRON`: H35 columns/HGB with the frozen H73-PM negative sampler (match training-negative `d_vis` bins to positive bin shares; seed `777 + 31*fold + draw + 5000`), and unchanged de-apron emission (`0.030 / 2.8 / 2.0 px`).
- **Implementation:** use `gems25.block_holdout.BlockHoldout` (subclassing the shared holdout primitives), `gems25.experiment.Cell`, H73-PM feature/sampling/emission helpers, `gems25.metric.dti_binary`, and `gems25.validation.pooled_summary`. `Context.holdout` must be set to the block selector before constructing each cell; the historical `gems25.holdout.py` source remains unchanged so prior evaluator hashes stay reproducible. Do not duplicate metric, feature, or writer logic. This selector writes cell evidence only; it does not invoke a full-catalogue builder or the submission writer.
- **Leakage canary:** before trusting any cell, run `gems25.validation.feature_canary` on every feature used by the candidate/control arms, including raw/inverted values and missingness, and on `-d_vis` alone. Record each feature/cell result. Any effective AUC `> 0.90`, missing class, or unverifiable feature stops the experiment as leakage/unverified.
- **Primary response:** pooled sparse-regime `HOLDOUT-DTI`, using evaluator `gems25.metric.dti_binary`, alpha `0.2`, beta `0.8`, radius `3 px` (300 m triangular kernel); report the evaluator/code identity, withheld-positive occurrences, and 95% cluster-bootstrap CI. Also report far-field `HOLDOUT-DTI` on held-out truth pixels with distance to the visible catalogue `d_vis > 9 px`, per-fold gains, emission distance strata, and feature-canary results. No live-score projection is permitted.
- **Selector-open gate:** `PM_DEAPRON` must exceed `CTRL_H35` in pooled far-field DTI by `> 0.001`, the paired four-fold cluster-bootstrap 95% CI lower bound must be `> 0`, at least `3/4` fold gains must be positive, it must also exceed `CTRL_BLIND_BD` in pooled far-field DTI, and at least `35%` of PM_DEAPRON emitted dots must be `>20 px` from visible catalogue. The canary must pass. Failure stops; no confirmation or slot build.
- **Separate overall holdout gate:** report overall `PM_DEAPRON` versus same-run `CTRL_H35`, but the selector-open gate is **not** a weekly-slot gate. Any follow-up confirmation and any future submission would require a separate pre-registration and must independently pass the existing overall same-run gate, fresh-draw confirmation, exact-file audit, and literal lane rule. H73-BW alone cannot approve a submission.
- **Budget:** one selector experiment, at most 8 fold/draw cells and 3 paired arms; stop after this single screen or 2 hours, whichever comes first. No tuning, no confirmation under this registration, and no weekly slot.

## 3. Safe cache preflight — no rebuilds

Before any model fit, confirm reuse of the existing shared work cache and record the actual paths, byte counts, SHA-256 values, Python/library versions, and evaluator source hashes. Required work-cache artifacts:

- `bands/_footprint.npy`
- `bands/_labels.npy`
- `static_ABCD.npy` and `static_ABCD.npy.names.json`
- `addons.npy` and `addons.npy.names.json`
- `h34_columns.npy` and `h34_columns.npy.names.json`

The current `evidence/work_cache_hashes.json` pins the first six files by cache identity (including the `.names.json` sidecars); it does **not** pin the H34 sidecar. If a pinned file is missing or hash-mismatched, stop rather than rebuild. If the H34 sidecar is missing, stop rather than call `load_h34_sidecar`: that loader silently builds the file from `work/bands`. If it exists, record its exact hash and names and disclose that no prior expected H34 hash is stored. Do not restore raw inputs or build any feature cache as part of this selector.

**Preflight result in this checkout (COMPUTED 2026-10-26):** `GEMS_DATA_DIR` and `GEMS_WORK_DIR` are unset; `data/` contains only `.gitkeep`; the read-only preflight recorded all eight required artifacts absent in the resolved default work directory. Therefore required shared caches are unavailable and H73-BW is **BLOCKED_BEFORE_FIT**. The run card records null holdout metrics and null raster fields; no data restore, feature rebuild, fit, or experiment was run.

## 4. Interpretation and limitations

The four checkerboard folds are spatial blocks, not four independent regional populations. The cluster-bootstrap CI has only four fold clusters and should be labelled low-resolution; repeated/connected catalogue components can span blocks even though each complete component is hidden wherever it intersects a test fold. This selector evaluates catalogue-gap generalization only. It does not establish blind-fault truth, organizer score, competition rank, or eligibility for the weekly slot.

## 5. Official/manual-review sources

- [Official DOE GEMS problem and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — reference link only; this session did not access DrivenData.
- [Competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — manual review link.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) and [INGENIOUS](https://gbcge.org/current-projects/ingenious/) — context/data provenance links; no new external binary is required for this selector.
- [EPSG:32611](https://epsg.io/32611) — grid reference.

No DrivenData page was fetched, monitored, authenticated, or submitted to. No organizer score was obtained.
