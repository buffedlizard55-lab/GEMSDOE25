# Repository review and decision record — 2026-10-26

## Executive decision

**No file in this checkout is cleared for a competition slot. Do not submit any download from this repository at this time.** The current testing download can be downloaded for local inspection only. It is format-valid against the recorded owner-mirror grid, but it fails the literal parallel-run lane gate and its registered holdout screen failed against the same-run H35 comparator. No projected leaderboard score is provided.

The exact site download is `docs/downloads/gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif` (SHA-256 `44ee60289f21030b119122c04fb1508584df1e88ce2a4c607adbde9f8eba1808`). The primary page and executive summary state **OK to download for testing: YES · OK to submit: NO — DO NOT SUBMIT**. This is a content-distinct artifact, not a lane-unique submission under the strict rule.

## What the strongest focus-site evidence does and does not say

The site scores below are OWNER-REPORTED claims from the supplied repository evidence, not organizer-confirmed receipts. The file IDs and mask relationships were recorded in `evidence/focus_audit_2026-10-26.json` and `evidence/focus_sites_forensics.json`; they are not new score estimates. The competition's hidden evaluation labels/receipts are not present in this checkout.

| Site | Highest supplied artifact | Supplied score (evidence class) | Pixel identity / lineage finding | New-slot decision |
|---|---|---:|---|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 0.2477 (OWNER-REPORTED) | D1.5 thinning of the older H19-5 parent; historical baseline | No |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 0.2600 (OWNER-REPORTED) | Exact mask duplicate of GEMSDOE30 D2.8 | No |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 0.2449 (OWNER-REPORTED) | Topographic gap-closure variant; supplied audit says 97.95% of its pixels belong to the H19-5 lineage | No |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 (OWNER-REPORTED) | Same R1 mask as GEMSDOE31; highest of its four supplied variants by 0.0002 over 0.2708 | No |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | 0.2600 (OWNER-REPORTED) | Exact mask duplicate of GEMSDOE25 D2.8 | No |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 0.2708 (OWNER-REPORTED) | Same R1 mask as GEMSDOE28 | No |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | 0.2778 (OWNER-REPORTED) | B2 mask = D2.8 after pruning the within-200 m catalogue collar; nested, not a fresh discovery | No; historical and not eligible as a new artifact |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | 0.2632 (OWNER-REPORTED) | R1-related mask with collar/tip pixels re-admitted | No |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | 0.2750 (OWNER-REPORTED) | B2 plus 1,200 additional pixels; not equal to B2 | No |

The pairwise exact identity claims above are only those explicitly measured in the available mask audit. A different mask does not imply a distinct method, a clean 3-pixel lane, a superior score, or slot eligibility. The automated summary now makes those distinctions explicit. It does not characterize the reported values as forecasts.

## Why GEMSDOE32 B2 plausibly led the supplied focus results

Local pixel forensics place B2 in a nested sequence: H19-5 → D2.8 thinning → R1 collar pruning → B2 removes an additional near-catalogue shell. The reported B2 score is 0.2778, versus 0.2708 for R1 and 0.2600 for D2.8. Under distance-weighted Tversky-style scoring, a prediction may contribute false-positive mass without supplying much additional proximity-weighted truth credit. Removing redundant or low-credit emissions can therefore improve the ratio even when no geological detector becomes more sensitive.

That is a mathematically plausible interpretation conditional on the supplied score labels and locally hashed masks. It is not proof that the removed dots were false positives against the private organizer truth, nor proof that B2's score gain was caused by that deletion. No hidden test labels or organizer receipts were available for independent attribution. The same caution applies to supplied overall-leader figures 0.3195 and 0.4413; they remain unverified and conflicting claims.

## Current testing artifact: measured status, not score projection

Saved prior-session H71 evidence in `registry/run_card_h71_2026-10-26.json` reports:

- **HOLDOUT-DTI 0.050577**, evaluator `gems25.holdout.v1.2-buffered-4quad-pooled-dti`, 21,835 withheld-positive occurrences, 95% CI [0.037264, 0.063890]. This is the stored H71-1 result, not a fresh run in this repository review.
- Same-run H35 HOLDOUT-DTI was 0.149887 (95% CI [0.119261, 0.180513]); the candidate failed the pre-registered comparison. All three H71 direct-emission screens failed against H35.
- Feature-alone canaries had maximum AUC 0.6945, below the 0.90 leakage alarm, for the tested H71-1 feature set.
- The H71 final-lane receipt identifies the registered r13 lattice as flagged: all candidate dots are within 3 px (`dots_within_3px = 1.0`), above the protocol's 0.70 cap. Its separate density-aware statistic does not waive the strict rule. Surface rank correlation against that lattice is near zero, but the lane rule is an OR: passing one criterion does not negate the overlap failure.
- **No leaderboard estimate is defensible.** HOLDOUT-DTI measures recovery of withheld catalogue components, not organizer test performance. The submission-page score cannot be calculated from this holdout or inferred from filenames.

The previous ROD and POL3 sessions were also negative; ROD stopped after its pre-placement/final-dot duplicate-lane failure, and POL3 stopped at the holdout screen. No experiment was run in this repository-review pass. No new TIF was generated, no weekly slot was spent, and no DrivenData access or upload was attempted.

## Exact-file audit performed in this review

The `data/` directory contains only `.gitkeep`; the actual sample-submission/template and training stack are absent from this checkout. I independently read the existing H71 GeoTIFF with Rasterio and recomputed its SHA-256. Measured file properties:

- SHA-256: `44ee60289f21030b119122c04fb1508584df1e88ce2a4c607adbde9f8eba1808` (matches the registry/run-card digest).
- One band, Float32, EPSG:32611; dimensions 3,730 × 3,292; affine transform `(100, 0, 243350, 0, -100, 4508550)`.
- All pixels finite; observed values are exactly `{0, 1}`, so the entire array is within `[0,1]` and no NaN occurs inside any footprint.
- This verifies the downloaded file's own properties against the grid values recorded in the existing receipt. It is **not** a fresh byte comparison against the official competition template, because the template is not present. Owner-mirror provenance remains unresolved.

Consequently, format-valid means only that these locally testable file checks pass. It does not cure lane duplication, failed holdout performance, missing source authentication, current-slot uncertainty, or organizer acceptance.

## Ranked hypothesis work and prior tests

The previous pre-registration already provides the required candidate slate; it was not silently repeated here. See `knowledge/27_preregistered_rod_2026-10-26.md` for the ranked, pre-fit ROD hypotheses and its negative result, and `knowledge/27_preregistered_h71_hgpc_2026-10-26.md` / `knowledge/27_apfl_hypotheses_ranked_2026-10-26.md` for earlier candidate slates. The repository records experiments and failures in their run cards. In this session, the experiment budget was **0 new experiments**; no candidate was fitted or tuned.

The strongest future step is not another speculative fit: first resolve the literal dense-lattice conflict without silently waiving the protocol, then restore hash-pinned data and design one new lane that is demonstrably outside the registry before placement. Require a same-run comparator, per-feature canaries, fresh confirmation, exact-file validation and a separate selector decision. If the lane rule is retained literally, do not construct a candidate whose predicted dots fall over 70% within 3 px of any raster in the registry.

## Source / provenance boundaries

Manual-review links (the pages are recorded as official links in the repository; they were **not freshly retrieved during this review**):

- [Competition problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN dataset description](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)

The competition problem/data and organizer leaderboard were not accessed. The competition inputs and sibling submissions in this repository are owner mirrors, not organizer-authenticated copies. No automatic DrivenData monitoring or upload was performed.

## Remaining blockers / limitations

1. No authoritative training/template rasters in `data/`; H71's exact template match cannot be freshly reproduced in this checkout.
2. Literal dense-lattice overlap makes the current H71 TIF ineligible despite low surface correlation and density-aware reports. The lane rule needs explicit resolution; do not apply a private exception.
3. HOLDOUT-DTI is a proxy for catalogue-gap recovery. It is not a calibrated leaderboard-score estimator, and no live score estimate should be invented.
4. The shared one-click download is intentionally testing-only. No artifact meets the combined uniqueness + comparative holdout + confirmation + validator gates.
5. Score claims, public-sibling file provenance, competition-data redistribution permissions, organizer receipt, and remaining weekly submission allowance are unverified.
6. Recent official sources were not freshly web-fetched in this pass. No claim of current leaderboard status or deployment status is made.

## What changed in this review

- Added a clear candidate assessment table to the landing/executive pages with a blank/explicitly unestimated organizer score, saved HOLDOUT-DTI and CI, the literal uniqueness result, and a “DO NOT SUBMIT” verdict.
- Reworked the nine-site table to show filenames, owner-reported score labels, measured exact-mask relationships, and per-site historical/no-slot status.
- Corrected overly broad “unique” language: H71 is content-distinct but fails the literal lane rule.
- Updated the short submission note and receipt so it says both holdout/lane fail, no slot and unscored leaderboard.
- Added regression coverage for score-class separation, H71 lane disclosure, and exact duplicate pairs.

