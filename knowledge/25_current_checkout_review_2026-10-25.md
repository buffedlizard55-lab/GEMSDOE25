# 25 · Current-checkout review: lane preflight, repository evidence, and next experiments

**Date:** 2026-10-25 UTC · **Branch:** `arena/e7df9bae-gemsdoe25` · **Purpose:** code and evidence review, not a new model experiment or competition submission.

## Executive decision

**Verdict: negative; no new TIF generated and no weekly slot authorized.** The checkout's `data/` directory contains only `.gitkeep`, so the shared cached feature stack, labels, sample template, and local full registry are not present. No fresh HOLDOUT-DTI, CI, raster hash, or template-based validation can therefore be reported. Existing artifacts and scores are historical owner-mirror evidence; they are not organizer receipts. The user-provided parallel-run text refers to a "single method paragraph below" but supplies no unique method paragraph. The lane selection is therefore ambiguous. Do not start a new fit or issue a new submission artifact on a guessed lane.

No DrivenData page, leaderboard, data endpoint, or submission form was accessed. No slot was used. The prior reports and receipts in this repository are not independently revalidated by this review.

## Review findings and code changes

### Fixed: candidate lane audit omitted the top-scorer registry and retained all decoded rasters in RAM

`scripts/validate_gem_candidate.py::load_registry_rasters` previously inspected `data/scored`, `data/calibration`, and `docs/downloads`, but omitted `data/registry_top`, where `scripts/fetch_top_scorers.py` places the high-scoring owner-mirror rasters (including the GEMSDOE32 B2 raster). That created a false-clearance risk. It also decoded and retained every full-grid raster simultaneously, which could consume multiple GiB at the competition grid size.

The loader now indexes the scored, calibration, top-scorer, and tracked-download directories, deduplicates by SHA-256, and reads one raster at a time for comparison. `tests/test_lane_preflight.py` verifies inclusion of `registry_top` and verifies that the loader does not keep the raster array resident.

### Fixed: surface lane was checked only after full-footprint candidate emission

The validator previously created each full-footprint emission before its first lane check. It now checks the full-grid candidate surface first. A surface with absolute Spearman above 0.90, undefined correlation, a shape mismatch, or no registry rows fails closed before holdout-dot emission and before full-footprint candidate placement. It then applies the existing literal final-dot comparison after placement. This implements the required order; it does not waive or reinterpret the 70% overlap stop.

Synthetic regression tests cover absolute negative correlation, undefined correlation, missing-registry failure, registry discovery, and memory behavior. These unit tests do not replace a full real-grid run.

### Unresolved: leakage canary is not uniformly feature-by-feature in the shared validator

The general `validate_gem_candidate.py` response currently summarizes AUC for each proposed surface/composite, but does not guarantee an isolated holdout canary for every raw input feature before combining them. Historical experiment evidence may include separate canaries, but the shared validator alone does not enforce that invariant for future candidates. Before a new run, extend the shared experiment interface to emit a single-feature canary table and fail closed when any feature is missing or has AUC >0.90. Do not hide this gap behind a composite AUC.

### Unresolved: current data and source limitations

`data/` is empty apart from `.gitkeep`; the pinned mirror files can be restored via `scripts/restore_data.py`, but their hashes establish owner-mirror consistency, not organizer provenance. The same-run baseline, withheld-positive count, 95% CI, leakage canaries, full registry comparison, and exact-template file validation were not rerun here. The prior local code paths and their stored receipts cannot be represented as fresh results.

## Focus-site evidence and the GEMSDOE32 0.2778 claim

The nine-site comparison and pixel-forensic audit are already documented in `knowledge/21_repo_review_2026-10-25.md`, `knowledge/17_focus_sites_and_0.2778_forensics_2026-10-25.md`, and `evidence/focus_sites_forensics.json`. The reported 0.2778 is an **OWNER-REPORTED** claim, not an **ORGANIZER-CONFIRMED** result in this checkout. The mirror audit supports an inference that B2 is a D2.8 emission with another near-catalogue shell removed; deleting redundant low-credit predictions can improve a Tversky-style objective by reducing false-positive cost without discovering new geology. This is conditional on the score claim and the mirrored pixels. The hide-and-recover proxy cannot establish whether the deleted near-catalogue pixels are false positives against the competition's hidden expert labels.

Accordingly, there is no defensible evidence here that a new artifact would exceed 0.2778 (or the conflicting user-supplied leaderboard figures 0.3195 and 0.4413). Those are not predictions or locally measured scores.

## Candidate hypotheses for a later, pre-registered lane

These are ranked for feasibility and scientific distinctiveness, not as scores or performance forecasts. The planning brackets below are uncertain prioritization ranges only. Only the first candidate uses data already listed in the owner's pinned mirror manifest; the other candidates are blocked until the official bytes, schema, area coverage, and licensing are actually checked.

| Rank | Hypothesis; layers and target signature | Why it could find a catalogue-missing fault; difference from prior work; named mimic | Planning gain bracket; cost; status |
|---|---|---|---|
| 1 | **Directional vent-to-vent conductive-edge continuity.** GDR 1391 Quaternary vent points + `cond_surf` (band 17) + `depth_to_base_surf` (band 15); multi-scale conductivity-boundary ridge tangents aligned with vent-to-vent / vent-to-structure bearings, scored as a sparse connected corridor. | A blind permeable fault could connect hydrothermal manifestations without a Quaternary surface trace. Distinct from the already-tested radial vent-proximity × conductivity-gradient GEM-2 product. Mimics: lithologic conductivity contacts, volcanic flow margins, and non-tectonic clustering of vents. | `0…+0.005` ΔDTI (planning only); medium cost. Inputs are in the owner-mirror manifest, but absent in this checkout; restore and hash-check before pre-registration/feature-alone canary. The earlier radial GEM-2 screen was negative, so the directional variant has a low prior and must earn its own evidence. |
| 2 | **Channel-offset / knickpoint concurrence.** Raw USGS 3DEP 1 m DEM + USGS National Hydrography Dataset channel geometry; paired-bank displacement and aligned multi-channel knickpoints with cross-scale orientation coherence. | Fault displacement can offset drainage where 100 m terrain descriptors smooth the signal. This uses raw channel geometry rather than current scarp/tip descriptors. Mimics: lithologic knickpoints, fan-head incision, roads/ditches, and DEM seams. | `0…+0.008` ΔDTI (planning only); high cost. **Blocked:** USGS 3DEP and National Map Downloader are public records, but target tile coverage, data bytes, NHD schema, and exact licences were not verified here. Sources: [3DEP](https://www.usgs.gov/3d-elevation-program), [National Map Downloader](https://apps.nationalmap.gov/downloader/). |
| 3 | **Shallow-temperature residuals × conductive-base edge.** GDR 1391 2 m temperature-probe observations + `cond_surf` + `depth_to_base_surf`; deconfounded spatial residuals coherent with an edge away from mapped faults. | Could reveal active circulation along blind structures. Existing thermal/geochemical features use other summaries; H27-2 was registered but blocked, not fitted. Mimics: seasonality, elevation, land use, groundwater flow, and biased probe locations. | `0…+0.006` ΔDTI (planning only); medium/high cost. **Blocked:** the [GDR 1391 record](https://gdr.openei.org/submissions/1391) lists records, but the individual binary, schema, coverage, and licence need verification before it is viable. |
| 4 | **Stress-permeability orientation × blind basement edge.** USGS Great Basin slip/dilation-tendency data + `depth_to_base_surf` / potential-field edges; score predicted dilatant orientations at uncatalogued basement discontinuities. | A physical permeability prior distinct from scalar geodetic invariants and visible-fault orientation. Mimics: regional-to-local stress mismatch, stress-model error, and lithologic boundaries. | `0…+0.006` ΔDTI (planning only); high data cost. **Blocked:** the [USGS ScienceBase record](https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d) is a source listing, not proof that the required binary, current coverage, or licence was checked. |

**Top candidate recommendation:** rank 1 only for feasibility and independent information; it is not a validated winner. Before fitting: preregister one directional transform, folds/draws, same-run comparator, feature-alone leakage canaries, paired gate and strict lane checks. Validate on the project holdout before any real-slot selection. Because the current lane method is unspecified and the registry/data are absent, this review did not run it.

## Verification and three passes

1. **Pass 1 — review and fix:** inspected README/AGENTS, data placement, current run cards/score provenance, submission writer, holdout/evaluator, registry loader, candidate validator, source manifest, site download metadata and focus-site forensics. Fixed `registry_top` coverage, sequential raster reading, and pre-placement surface-lane stop logic.
2. **Pass 2 — bug/edge review:** added regression tests for missing/empty registry, undefined Spearman, absolute correlation, raster discovery, and memory-safe loading. Checked that final dot comparison remains literal and that density-aware helper output does not replace the validator's `lane_is_clear` strict decision. Verified the changed code and test suite using the pinned requirements.
3. **Pass 3 — original-brief re-check:** no new candidate TIF, slot, organizer score, or fresh model result is claimed. Every proposed performance range is labelled planning-only. The request for a unique artifact is not marked complete because the necessary data, a specified single lane, and fresh validation are absent.

### Test result

`.venv/bin/python -m pytest -q`: **166 passed, 5 skipped** at the end of the original review changes. After integrating the concurrently merged main update, the suite passed **184 passed, 5 skipped**; the skipped cases require restored scored rasters or the sample-submission template. `.venv/bin/ruff check src scripts tests`: passed after integration. `git diff --check`: passed.

The integration also brought in the GMCE/MSCR lane's new experiment evidence and testing-only GeoTIFF from PR #27. Per its recorded run card, those two holdout screens were negative and the literal lane rule fails; the file is explicitly **DO NOT SUBMIT**. This review did not generate or revalidate that artifact.

## Sources and provenance

- Official competition format page, manual review only: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>. No page was accessed in this review; the project forbids automated DrivenData access.
- Official reference implementation: <https://github.com/drivendataorg/gems-prize-reference-solution>.
- GDR 1391 INGENIOUS data record: <https://gdr.openei.org/submissions/1391>.
- USGS GeoDAWN record: <https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7>.
- USGS 3DEP and National Map Downloader: <https://www.usgs.gov/3d-elevation-program> · <https://apps.nationalmap.gov/downloader/>.
- USGS slip/dilation-tendency record: <https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d>.

The source registry contains historical read notes; non-GitHub sources were not re-fetched because this runner's outbound host allowlist does not include those domains. Manual verification remains required for source availability and dataset licensing.

## Run card

See [`registry/run_card_current_checkout_review_2026-10-25.json`](../registry/run_card_current_checkout_review_2026-10-25.json). No value in that card is an organizer-confirmed score.
