# H78 status correction and fail-closed audit — 2026-10-27

> Historical parallel review. A later audit restored the pinned owner mirrors and recomputed full-footprint lane statistics; see [the corrected nine-site review](38_h78_mhscf_and_phd_focus_sites_analysis_2026-10-27.md). The H78 DO NOT SUBMIT decision remains unchanged.

## Decision

**The preserved H78 GeoTIFF is downloadable for inspection only. It is not eligible for competition submission. No new TIFF was generated in this review, no weekly slot was used, and no score projection is made.**

This correction supersedes H78 promotion language in the earlier H78 run card, validation receipt, builder output, and PhD synthesis. Those artifacts are retained as provenance; their unsupported performance/promotion claims must not be repeated.

## Evidence and reasons

1. **Format only:** `docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif` is present and its file-level tests read it as a single-band float32 GeoTIFF on EPSG:32611, shape 3730 × 3292, with finite values in [0, 1]. These are format results only. They do not establish score, lane uniqueness, or eligibility. See `tests/test_h78_submission.py` and the exact-file validation receipt.
2. **Strict lane failure:** the saved lane audit identifies the r13 lattice raster and reports `dots_within_3px = 1.0` for H78. That is 100% of H78 dots within 3 px, exceeding the prompt's literal 70% cutoff. Although the same audit also has a density-aware diagnostic that does not flag the raster, that alternative statistic cannot waive the stated literal trigger. The correct result is **duplicate lane / stop**.
3. **No defensible score estimate:** the previous `0.2785` was hard-coded in `scripts/build_h78_submission.py` and described as a calibration to GEMSDOE32 B2 plus an assumed conduit gain. No independent calibrated model, organizer receipt, or candidate-specific experimental evidence in this checkout supports that numerical leaderboard estimate or confidence interval. It is removed from the current run card and receipt. The run-card `0.1512` value also lacked a candidate-specific, verifiable H78 holdout receipt, so it is not retained as a HOLDOUT-DTI result.
4. **Claimed uniqueness did not satisfy the protocol:** “unique content” / different file hash does not mean non-duplicate under the strict dot-proximity rule. Surface rank correlation alone also cannot cancel final-dot overlap.

## Code change

The H78 builder now exits before loading inputs or writing anything. This prevents a future rerun from creating another file in a lane already shown to violate the literal rule or from repeating a hard-coded score projection. The TIF and its format receipt remain available only as research-inspection artifacts.

## What this does not establish

- It does not show that H78 would score exactly 0.1512 or any other value on the competition leaderboard.
- It does not identify the masked/private test faults, prove a geothermal origin for any particular unmapped lineament, or verify the owner-reported 0.2778 for GEMSDOE32.
- It does not make an organizer-confirmed score claim. No DrivenData page was accessed and no submission was uploaded.
- It does not validate any new geological hypothesis. Candidate testing remains blocked until the project's shared cached feature stack and trusted registry rasters are available and the pre-registered hide-and-recover experiment passes all performance, leakage, and strict-lane gates.

## Reproducibility

- Exact TIF: `docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif`
- Format receipt: `docs/downloads/checks-gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.json`
- Lane receipt: `docs/downloads/lane-gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.json`
- Run card: `registry/run_card_h78_2026-10-27.json`
- Gating tests: `tests/test_h78_submission.py`

**Machine-readable verdict:** `negative`. `ok_to_download=true` means research inspection only; `ok_to_submit=false`.
