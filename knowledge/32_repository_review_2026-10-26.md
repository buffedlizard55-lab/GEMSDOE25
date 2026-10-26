# Repository review addendum — 2026-10-26

**Checkout:** `arena/f5b9b632-gemsdoe25`, based on `606eef45e669a6da061ec24be4a3d870addadb0f`.

**Decision:** **No newly eligible submission. Do not spend a weekly slot. No TIF or experiment was created in this review.**

**Evidence class:** local computation and owner-mirror artifacts are distinguished below from owner-reported competition claims. No DrivenData page, leaderboard, submission endpoint, or credential was accessed.

## Executive status

The existing H72-3 file is useful for inspection/testing but is **not** a submission candidate:

- File: `docs/downloads/gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif`
- SHA-256: `51f6e3cb83d7371231f3a8cd3ef166f82d5fb7d80a584577500eb36bf7615346`; content ID `88bbebfe79b4`; 41,061 positive pixels.
- **Fresh format-only check in this review:** passed against the restored, SHA-pinned owner-mirror `sample_submission.tif` (EPSG:32611; 3730 × 3292; exact template grid/transform; footprint values in [0,1]; no footprint NaN/Inf; no hard failures). This is not novelty, performance, slot, or organizer approval.
- **Saved prior-run performance evidence, not rerun here:** `HOLDOUT-DTI = 0.0594316`, evaluator `gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px) via gems25.experiment.Cell.evaluate`, 22,334 withheld-positive occurrences, 95% CI `[0.049419, 0.073435]`; same-run H35 comparator `0.1537859`, paired gain `-0.0943543` (95% CI `[-0.110488, -0.081491]`). This is an offline proxy, **not** a competition-score estimate.
- **Saved prior-run strict-lane evidence, not recomputed here:** 100% of candidate dots lie within 3 px of the registered r13 lattice, exceeding the literal 70% stop. The density-aware audit's `flagged_lane = []` is a separate diagnostic and does not waive that rule. Three literal flags were recorded: r13 lattice, `pindrop-discovery`, and `pindrop-nodes`.
- The local template and the H72-3 file were freshly hashed/checked. The scored registry rasters and derived feature cache were not restored, so no fresh full-registry audit or holdout was performed.

## Highest supplied historical results — all OWNER-REPORTED

The following values and mask facts are from `evidence/focus_audit_2026-10-26.json` and its associated local artifacts. No organizer receipt was found, so these are not organizer-confirmed scores. They describe supplied historical exemplars, not fresh eligible submissions.

| Site | Highest supplied artifact | Reported DTI | Positive pixels | Review note |
|---|---|---:|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | 60,069 | H19-5 parent thinned at D1.5. |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | 44,090 | D2.8 mask; pixel-identical to the supplied GEMSDOE30 mask. |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | 61,328 | Gap-closure variant; reported below the stronger supplied exemplars. |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | 37,660 | Highest supplied GEMSDOE28 result; distinct from its R1 mask. |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | 44,090 | Same prediction mask as GEMSDOE25 D2.8; a different filename does not make it new. |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | 40,199 | Same mask as GEMSDOE28 R1; collar pruning, not a distinct discovery. |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | 37,654 | Highest supplied result across these focus sites; owner-reported, not receipt-verified. |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | 41,865 | Tip/stepover addition; reported below B2. |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | 38,854 | The focus audit says 0.2750; a separate G36 ledger says 0.2683. Preserve this discrepancy; neither has an organizer receipt here. |

The nine-site table in `knowledge/31_h72_outcomes_and_portfolio_synthesis_2026-10-26.md` is the longer historical analysis. The contradictory overall leaderboard values **0.3195** and **0.4413** (also appearing as 0.4437 in an owner snapshot) are not verified and cannot support a ranking or a calibrated estimate.

## GEMSDOE32 B2: plausible mechanism, bounded conclusion

Local pixel forensics identify B2 as the D2.8 mask after removing 6,436 predictions within 200 m of the supplied catalogue (`d_cat <= 2 px`). The owner-reported sequence is 0.2600 for D2.8, 0.2708 for R1, and 0.2778 for B2. This is consistent with a distance-weighted score in which thinning redundant ridge pixels and removing low-marginal-credit predictions can lower false-positive mass while retaining much of the nearby coverage.

That mechanism is **not proven**: hidden competition labels are unavailable, all three live-score values are owner-reported, and the local catalogue-gap holdout is not a calibrated live-score estimator. Statements in the older §2.2 of `knowledge/31` that assign specific proportions of B2's dots to non-fault mimics or answer “yes” as though a future improvement were established should be read as hypotheses/inferences, not facts. A unique prediction could exceed 0.2778 in principle; this repository has **not** demonstrated that it will, and no defensible numerical estimate is available. The latest H72-3 holdout run is substantially below its same-run H35 comparator and also fails the literal lane rule.

## Hypothesis work and experiment boundary

The current checkout's latest H72 session already used its full three-experiment allowance (draws 80–85). No extra experiment, cache rebuild, new TIF, promotion/selector decision, or weekly slot was used here. The task's referenced “single method paragraph” is not present as a distinct frozen method in this checkout; I did not invent a lane or run one.

Open PR [#47](https://github.com/buffedlizard55-lab/GEMSDOE25/pull/47) contains a proposed, planning-only queue of four untried repository-level hypotheses: (1) conductive-alteration/radiometric-edge co-orientation; (2) season-normalized Landsat surface-temperature residuals; (3) ASTER alteration-mineral boundaries; and (4) Sentinel-1 InSAR line-of-sight discontinuities. Its queue names candidate layers and transforms, blind-fault rationale, repository distinction, non-fault mimics, planning-only expected DTI brackets, engineering cost, and data/source limitations. It explicitly says sibling-project novelty is unverified; for three satellite ideas it does not establish AOI scene availability. The queue is **not in this checkout** because PR #47 is open and conflicting; no candidate was fit. I reviewed the relevant diff to avoid duplicating it.

## Three cumulative review passes

1. **Implement/verify:** Read the standing brief and prior session receipts; restored only the SHA-pinned `core` group; freshly validated H72-3 format against the template; compared the nine focus-site owner-mirror audit and the saved H72-3 performance/lane receipts; made no experiment or competition artifact.
2. **Bugs/assumptions/edge cases:** Found that `tests/test_h72_submission.py` asserted the density-aware `flagged_lane = []` condition without asserting the independent literal-lane failure. Strengthened the test to require both conditions, including the 100% r13 overlap and the strict duplicate/stop verdict. Verified that format validity does not imply eligibility and that the owner-reported score claims remain unverified.
3. **Original-request reconciliation:** Re-read the requirements against the results: no new eligible TIF, score estimate, official leaderboard result, external scene check, weekly slot, or organizer upload is claimed. The four-hypothesis queue remains pending with PR #47; no undefined method was silently selected. Next steps are to resolve the literal-lane policy/method ambiguity, restore the authorized shared cache and relevant registry data before any later experiment, and separately review/resolve PR #47 conflicts.

## Verification

After the regression assertion was added: `pytest` **320 passed, 4 skipped**. Skips require the scored-data group or external rasters that are not restored. Ruff, Python `compileall`, JavaScript syntax check, and `git diff --check` passed. The only new code change is the strict-lane regression test; no page, README, data manifest, or TIFF was rewritten. The only registry change is the cumulative review receipt.
