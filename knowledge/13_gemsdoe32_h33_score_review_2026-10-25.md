# GEMSDOE32 H33-2-B2: forensic review and safe next steps (2026-10-25)

> **Update (2026-10-25 continuation on `arena/30eec392-gemsdoe25`):** After fixing the GitHub REST API rate-limit fallback in `scripts/restore_data.py` and `scripts/restore_artifacts.py` (`IR-25-RESTORE-API-RATELIMIT`), all 22 manifest inputs, all 6 derived caches (`evidence/work_cache_hashes.json` matched 6/6), 30 registry rasters, and 13 focus-site rasters (`GEMSDOE24..36`) were restored and verified on disk. See [`14_preregistered_h31_flank_shielded_subscarp_factorial_2026-10-25.md`](14_preregistered_h31_flank_shielded_subscarp_factorial_2026-10-25.md) for the pixel-exact 9-site forensic proof and H31-1 preregistration, and [`15_h31_outcomes_and_run_card_2026-10-25.md`](15_h31_outcomes_and_run_card_2026-10-25.md) for the completed H31-1 screen + confirmation holdout results, the unique H31-1 GeoTIFF (`40bfe1d5b1c5`), the 57-raster duplicate-lane audit, and the completed Protocol Rule 5 Run Card (`evidence/h31_run_card_2026-10-25.json`).

## Evidence boundary

This note separates (1) the user-provided score claim, (2) the owner-published GEMSDOE32 repository artifacts, and (3) computations/results in this checkout. The official competition has not confirmed the score or artifact identity. No DrivenData page was contacted. Repository-hosted receipts and holdout values are secondary, owner-generated evidence, not organizer receipts.

## What the reported 0.2778 appears to represent

The user identifies `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` as scoring 0.2778. That is an **owner/user-reported score claim**, not an organizer-confirmed result available in this checkout. The cited GEMSDOE32 source is the public repository [README](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/README.md), its [H33 round-4 research record](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/research/hypotheses-round4.md), and [artifact audit JSON](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json). These can substantiate what the owner says was built and locally audited; they cannot independently substantiate 0.2778.

The published mechanism is a *deletion-only calibration of an existing prediction*: take the 0.2708-labelled base surface and remove every emitted dot within 2 pixels (200 m) of the catalogue, leaving 37,654 dots. Its accompanying owner-generated audit claims a 4-quadrant increase of 0.00487 under its “drift-corrected” holdout/live-mirror instrument, and projects 0.2747. The same repository explicitly labels 0.2747 a model projection, not an organizer score. The supplied 0.2778 is therefore not explained by the published projection alone; it may be a later actual score, but that cannot be verified from the local audit. Do not conflate those three numbers.

**Plausible mechanism (inference, not proof):** the competition metric charges prediction mass and credits nearby truth under a finite-radius triangular kernel. Removing predictions close to known faults can help if those predictions mostly spend false-positive mass while earning little off-catalogue truth credit. A 200 m exclusion may therefore improve the precision/credit trade-off without discovering any new geology. It can also hurt if a real unmapped fault lies near a mapped trace. The owner’s own holdout record warns that catalogue-hidden and off-catalogue-truth instruments disagree; the removal result cannot establish that the same trade-off holds on hidden test labels.

**Key conclusion:** H33-2-B2 is not a new geological discovery method, but an emission-domain restriction. The score claim does not establish that its pruning mechanism caused a generalizable gain. Nor does a high score from this one artifact prove its geological interpretation.

## Unique-artifact / lane gate

The candidate raster itself is not in this repository’s `registry/data_manifest.json` and the competition inputs/cached feature arrays are absent from `data/` (only `.gitkeep` is present). Thus we cannot compute the requested pre-placement or final-raster rank correlation and 3-pixel dot-overlap against the registry rasters. Under the parallel-run protocol, that means we **must not construct or promote an H33-derived raster**: the duplicate-lane test cannot be passed. No existing TIFF was relabelled or copied as a new submission. The current D2.8 file is explicitly documented in this project as an earlier, unscored, not-slot-approved artifact; it is not a substitute for a fresh, validated candidate.

A new GeoTIFF cannot be responsibly generated from absent inputs. Fabricating a surface or perturbing a prior TIFF would violate the uniqueness and scientific-validation requirements. The available H33 TIFF is not downloaded or included here.

## Candidate ideas to preregister only after the required inputs and registry checks

These are **screening hypotheses, not viable candidates or score forecasts**. Each needs the prescribed feature-alone leakage canary (AUC ≤ 0.90), buffered whole-segment hide-and-recover evaluation, and registry similarity checks before any complete model is built. Novelty is only relative to the GEMSDOE25 code reviewed here; it is not a claim of global novelty.

| Rank | Hypothesis | Specific layers / target signature | Why it might find an uncatalogued fault | Difference from current GEMSDOE25 implementation | Expected DTI improvement / cost | Data and status |
|---|---|---|---|---|---|---|
| 1 | **Multi-scale curvature zero-crossing on elevation** | Cached `det_elev` and `det_elev_slope`; compare signed curvature zero-crossing persistence at pre-fixed scales (e.g., 2, 4, 8 pixels), not raw local maxima | A buried or subdued break may form a persistent flexure/curvature boundary even where a mapped trace/scarp is absent; persistence across scale can suppress single-scale artifact | Current GEMSDOE25 H30 uses lidar scarp descriptors and tip/relay features, not this curvature-scale-space signature. This is not globally novel: GEMSDOE32 describes related curvature work, so registry/raster similarity is a mandatory blocker | Unknown (no estimate supported); medium implementation cost, low after cache restored | Required cached DEM-derived bands are named in sibling GEMSDOE32 material, but absent locally. Must run one-feature canary and spatial holdout; do not call it viable before both. |
| 2 | **Differential geodetic-strain ridge × basement-depth discontinuity** | Cached geodetic dilation/shear-rate bands plus `depth_to_base_surf`; signed cross-gradient alignment / ridge coincidence | A mechanically loaded, permeable structure could localize strain and align with a basement step beyond the mapped trace network | Current repo’s families use geodetic and basement information as broad predictors; the proposed target is a pre-specified cross-gradient geometry rather than a generic interaction. Related transtensional and basement hypotheses exist in GEMSDOE32, so this is not presumed novel across projects | Unknown; medium/high feature-engineering and leakage-control cost | All named layers are competition bands, but files are not present locally. Must inspect band manifest and run each input alone before any interaction. |
| 3 | **Scarp-free, multi-physics edge agreement** | Gravity horizontal-gradient, magnetic anomaly gradient, and basement-depth gradient; test co-located edge ridges with one frozen tolerance | Buried faults can create coincident physical-property boundaries without a strong surface scarp | Related concealed-step idea H26-3 is already documented in this repository and therefore this exact concept is **not new here**; retained only as a low-priority replication/negative-control possibility, not a “novel” candidate | Unknown; low/moderate if caches exist | Competition bands would suffice; absent locally. Do not spend an experiment unless a materially different, pre-registered signature is specified. |
| 4 | **Hydrothermal water-chemistry / temperature discontinuity** | Official USGS NWIS groundwater temperature and chemistry observations, spatially aggregated with sampling-date and well-depth controls; target coherent anomalies along blind structures | Geothermal upflow can produce thermal and solute anomalies; a spatially coherent, independently measured anomaly could identify active systems rather than simply mapped faults | Not implemented in this repository; an external observational layer, not another raster transform | Unknown; high data-linkage, sampling-bias, and spatial-support cost | Specific free official source: [USGS Water Services API](https://waterservices.usgs.gov/). Availability and usable Great Basin coverage were **not checked** in this environment, so this is blocked and not viable until the endpoint is verified and coverage/schema/licence inspected. Sparse, non-random well sampling is a major confounder. |

**Ranking caveat:** candidate 1 ranks first only by input availability and lower engineering cost if the cache is restored; its novelty is already qualified by GEMSDOE32’s published work. None is expected to beat 0.2778 or 0.3195 on present evidence. The user-provided 0.3195 “leader” is also unverified. Do not state a score projection as a score.

## Required next run (no slot)

1. Restore inputs using the repository’s pinned `scripts/restore_data.py` process on a runner with sufficient memory/disk; retain its receipts. Verify the cache hashes against `evidence/work_cache_hashes.json`; a mismatch means the historical baseline must be recomputed in the same run.
2. Obtain candidate and registry rasters by pinned SHA from their owner repositories (owner mirrors, not organizer-authenticated). Before placement, calculate rank-correlation and nearest-dot overlap against every registry surface. If correlation exceeds 0.90 or >70% of new dots lie within 3 px of a registry raster, mark duplicate and stop.
3. Pre-register one candidate before fitting. For the feature-alone canary, hide whole fault components with a buffer, derive catalogue features from visible faults only, mask visible faults pixel-exactly, then score pooled DTI with α=0.2, β=0.8 and the 300 m triangular kernel. Report evaluator version, number of withheld positives, and 95% CI for every DTI number. Do not combine feature evidence before screening for leakage (AUC >0.90).
4. Run no more than three experiments or two hours. Promote nothing unless the specific exact artifact beats the comparable same-run holdout best and passes the exact grid/range audit. A holdout pass is still not an organizer score.
5. Only then build a new, content-addressed TIF and validate shape, CRS, affine transform, single band, finite `[0,1]` values over the complete footprint, and zero leakage. The local submission-validation path does not submit a file and cannot verify acceptance by the organizer.

## Repo review and checks

- This checkout already contains extensive scientific registrations and results through H30, a prominent format-validated download, an executive submission guide, a no-slot policy, provenance caveats, and the verbatim owner brief at `knowledge/owner_brief_verbatim.txt`. The README is the start-of-session project brief; the user’s requested manual-check reduction is represented by the source feed, but the competition site is intentionally not automatically polled.
- Significant risk: current source files and cached model features are missing; only the generated D2.8 pair is in `docs/downloads/`. The test/format claims in tracked evidence are historical and should not be mistaken for a fresh run in this environment.
- Initial runner lacked pytest/Ruff. After creating the ignored local `.venv` and installing the pinned `requirements.txt`, the first pytest collection exposed a real configuration defect: `pyproject.toml` added `scripts/` rather than the repository root to pytest's import path, breaking `from scripts...` test imports. Fixed it to `pythonpath = [".", "src"]`. Final check: `.venv/bin/pytest -q` → **103 passed, 3 skipped** (the three explicitly require restored scored rasters); `.venv/bin/ruff check src scripts tests` → **All checks passed**; `git diff --check` passed. The score/artifact source remains secondary and does not verify competition scores.
- Pull request #10 was opened from the required Arena branch to `main`: https://github.com/buffedlizard55-lab/GEMSDOE25/pull/10. At this note's update, CI is queued/in progress. No merge is claimed until checks complete. No competition slot was spent.

## Three review passes

1. **Implementation/review pass:** inspected README, standing instructions, source tree, evidence, registry records, and the cited GEMSDOE32 repository’s H33 audit and hypothesis documentation. No candidate raster was copied or generated.
2. **Bug/assumption pass:** distinguished owner-reported score, local format audit, proxy holdout and projected DTI; noted that DTI/leaderboard numbers are not organizer-confirmed; marked similarity testing impossible without cached rasters; fixed the pytest import-path defect and reran tests/lint.
3. **Request pass:** confirmed no fresh TIF can be honestly generated or certified under the no-duplicate lane gate. Existing submission is not represented as new. Next safe action is data/cache restoration followed by preregistration, canary, blocked holdout and registry comparison.

### Run card (current session; no experiment run)

```json
{
  "hypothesis": "H33-2-B2 prunes base-emission dots within 200 m of mapped faults; interpreted as a precision/false-positive-mass trade-off, not a new geothermal discovery",
  "mechanism": "Remove dots near the catalogue that may spend false-positive mass while earning little off-catalogue triangular-kernel credit; may also remove genuine blind faults",
  "named_non_fault_mimic": "Mapped-catalogue ascertainment density and correlated terrain/road or basin-margin edges",
  "holdout_dti_and_95pct_ci": "NOT RUN IN THIS CHECKOUT; evaluator version, withheld-positive count and CI unavailable",
  "correlation_overlap_vs_registry": "NOT COMPUTABLE: candidate/registry rasters and feature cache absent locally; duplicate gate not passed",
  "raster_sha256": "NONE GENERATED",
  "validator_output": "NOT RUN; no new TIFF. Required checks: no NaN inside footprint; values in [0,1]; exact template CRS/shape/transform",
  "submission_name": "NONE — no slot-ready artifact",
  "submission_note": "No new TIF generated: data/cache absent and duplicate-lane gate could not be evaluated.",
  "verdict": "negative"
}
```
