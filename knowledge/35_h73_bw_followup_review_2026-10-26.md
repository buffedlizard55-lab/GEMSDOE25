# H73-BW follow-up review and current stop decision — 2026-10-26

**Branch:** `arena/c1c20eed-gemsdoe25`
**Outcome:** one evaluation-only H73-BW diagnostic was conditionally authorized by the prior plan, but its cache gate stopped the run before fitting. **No block-holdout score, new candidate surface, new TIFF, live-score estimate, or submission approval exists.**
**Current summary:** [`docs/current-review.html`](../docs/current-review.html) · [`README.md`](../README.md) · [H73-BW run card](../registry/run_card_h73_bw_2026-10-26.json) · [preflight receipt](../evidence/h73_bw_preflight_2026-10-26.json).

## Decision and evidence

The prior H73-PM screen is the only relevant candidate-model result. Its `PM_DEAPRON` arm scored **HOLDOUT-DTI 0.113429** (evaluator `gems25.metric.dti_binary`, α=0.2, β=0.8, R=3 px; 22,290 withheld-positive occurrences; 95% cluster CI `[0.096769, 0.126862]`) against same-run `CTRL_H35` **0.152389**. The paired gain was `−0.038960` (95% CI `[−0.047169, −0.024562]`, 0/4 folds positive). It is not a competition score. See [`registry/run_card_h73_2026-10-26.json`](../registry/run_card_h73_2026-10-26.json) and [`knowledge/33`](33_h73_outcomes_and_executive_summary_2026-10-26.md).

The H73-BW plan had a wording conflict. `knowledge/32` §1 says the block selector is worthwhile if H73-PM “shows far-field signal”; §2 defines a stronger candidate-screen gate requiring a win over both H35 and blind. H73-PM did **not** pass that stronger gate (`0.082120` far-field vs H35 `0.097871`), but did show the narrower diagnostic signal over blind (`0.082120` vs `0.075379`, gain `+0.006740`, 3/4 folds positive, 46.4% of emitted dots >20 px). `knowledge/33` §4 calls the block selector the “single blocking instrument.” This review therefore resolves the conflict as **GO for one pre-registered, evaluation-only H73-BW diagnostic** to test the component-split explanation, while preserving **NO-GO** for H73-PM confirmation, a geological-method change, full-footprint build, TIFF, and weekly slot. This interpretation and its limits are recorded in [`knowledge/34`](34_h73_bw_block_selector_2026-10-26.md) and `IR-26-H73-BW-CONDITIONAL-GATE-RESOLUTION-20261026`.

## Why the diagnostic did not run

The read-only preflight found all eight required cache artifacts absent under `/home/user/GEMSDOE25/data/work`: footprint, labels, pinned static feature matrix and names, pinned add-on matrix and names, and H34 matrix and names. The tracked work-cache hash manifest does not include an H34 pin. `src/gems25/h34.py::load_h34_sidecar` builds that sidecar if missing, so the preflight intentionally does not import or call it. A missing or mismatched pinned cache is a hard stop; this review did not restore raw competition inputs or rebuild features.

The full block-selector design, frozen draws/arms/holdout/analysis gates and source links are in [`knowledge/34`](34_h73_bw_block_selector_2026-10-26.md). Its status is conditional diagnostic GO but operationally `blocked_before_fit`. All H73-BW metric, CI, canary, surface/lane, raster, and submission fields remain null or explicitly not run in the run card.

## Code and verification

- Added [`src/gems25/block_holdout.py`](../src/gems25/block_holdout.py), a checkerboard `BlockHoldout` subclass with 250-pixel (25-km at 100 m/pixel) blocks, four anchored parity folds, complete-component hiding, inherited collar behavior, and deterministic pseudo-hidden training components. The historical `src/gems25/holdout.py` was left unchanged to preserve saved H73-PM source hashes.
- Added a read-only [`scripts/preflight_h73_bw.py`](../scripts/preflight_h73_bw.py) and regression tests. It requires expected SHA pins for the six already-pinned shared-cache artifacts, verifies H34 names when present, records the unpinned H34 sidecar hash, and never restores, builds or fits. Missing manifest pins fail closed.
- The checkerboard geometry and leakage-prevention properties were tested on synthetic arrays only. The real competition grid/cache was unavailable; therefore the block selector itself was not validated against real data.
- Generated the current executive page and README status from the registries/evidence. The page explicitly distinguishes the old H73-PM inspection-only raster from a new approved TIF and labels its saved metric as HOLDOUT-DTI.

## Exact-file and score status

No new H73-BW TIFF exists. The prior H73-PM artifact at [`docs/downloads/gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros.tif`](../docs/downloads/gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros.tif) (content id `1b7533ebb62b`) remains available for inspection only, **DO NOT SUBMIT**: the saved strict literal audit flags the dense r13 lattice, in addition to its failed same-run H35 gate. No file created in this turn passed the surface/final-dot duplicate audit or the shared GeoTIFF writer because no candidate was generated.

The reported GEMSDOE32 B2 `0.2778` and supplied overall scores `0.3195` / `0.4413` remain owner-reported/unverified; no receipt or live leaderboard was accessed. The nine-site comparison and conditional B2 mechanism remain in [`knowledge/33`](33_h73_outcomes_and_executive_summary_2026-10-26.md); three ranked geological planning hypotheses and their layers, signatures, mimics, novelty boundaries and data limits remain in [`knowledge/29`](29_download_audit_and_next_hypotheses_2026-10-26.md). None was fit in this selector session.

## Three review passes

1. **Implement and verify:** preserved the prior evaluator hash; implemented the new selector in a separate module; added a fail-closed cache gate; re-read the H73-PM preregistration/outcomes; generated the current site/README from saved evidence. No DrivenData, upload, score, restore, or model fit.
2. **Bug/assumption/edge-case review:** exercised zero-target sampling, checkerboard parity, complete-component hiding, deterministic draws, invalid fold/size handling, cache absence, cache hash mismatch, missing manifest pins, and H34-name mismatch on synthetic fixtures. A full-suite run caught that initially putting the class directly in `holdout.py` invalidated the saved H73 evaluator hash; the implementation was isolated in `block_holdout.py`, restoring the historical source and passing the consistency test.
3. **Original-brief reconciliation:** no unapproved method lane or feature was added; the unidentified “single method paragraph” remains explicitly unresolved; H73-BW is evaluation-only; the holdout remains unrun on real data; no HOLDOUT-DTI is invented; no projection, TIF, slot, or submission is approved. The `Maximize P(Win)` / `Own the Outcome` stop is recorded rather than evaded.

## Verification status

- `pytest -q`: final full suite **350 passed, 12 skipped** after integrating latest `origin/main` at `c04766f`. The first run had 1 failure because the initial class placement changed the frozen H73-PM evaluator hash; isolating the selector in `block_holdout.py` restored that hash, and the full suite passed afterward. Skips require competition template, scored rasters, or external inputs not restored.
- `ruff check .`, `python -m compileall -q scripts src`, `node --check docs/assets/app.js`, and `git diff --check`: passed in the final review.
- H73-BW preflight: `blocked_before_fit`; eight required artifacts missing; no restore/feature build/H34 loader/model fit. The receipt records environment/package versions, cache-manifest hash, and seven evaluator-source SHA-256 values.
- No competition TIF, organizer-confirmed score, submission, weekly slot, or DrivenData access.

Manual source links are retained in the pre-registration for owner review; no official website was freshly fetched in this turn.
