# Session review 2026-10-31 (branch arena/967c20f7-gemsdoe25)

Evidence labels: HOLDOUT-DTI (proxy, off-scale), OWNER-REPORTED (brief), COMPUTED (repo scripts), NOT ESTIMATED (no organizer score exists).
Outcome: **no file cleared for a slot; the clean TIF is unique, format-valid, and NOT submittable.**

## 1. Experiments (pre-registered in knowledge/56; budget 3 this session, see §5)
| Id | Question | Verdict | Key numbers (HOLDOUT-DTI, pooled, 95% CI) |
|---|---|---|---|
| E3 H-BF1 | Does a lane-compliant bound-fill beat random halo fill? | negative | F1 ridge halo 0.0140 dev / 0.0135 conf; F2 random halo 0.0274 / 0.0304; F4 random floor 0.0319 / 0.0323. F1−F2 = −0.0134 dev, −0.0169 conf (CIs exclude 0). |
| E4 H-REP1 | Does repulsion beyond density explain B2? | thinning-explains-B2 | P1 repulsion 0.01763 / 0.01779 vs P2 density-matched 0.01772 / 0.01789. P1−P2 = −0.00009 dev [−0.00025, +0.00009]; conf −0.00010 [−0.00027, +0.00009]. Not significant. |
| E5 H-CLEAN1 | Does lowest-registry-coverage halo fill (protocol-clean) beat random? | negative | C1 0.00435 dev / 0.00423 conf; C2 0.02655 / 0.02819; C3 floor 0.03608 / 0.03265. C1−C2 = −0.0222 dev, −0.0240 conf. |

Leakage canary (G0): ridge AUC 0.47–0.55 on every split (passes); negative-distance AUC 0.69–0.82 (as expected from catalogue proximity, not treated as leakage because it is a physically motivated feature, not a single unexplained feature).

Finding: registry-coverage avoidance selects against holdout truth (E5). Cause not separated (catalogue-proximity confound vs crowd-information effect). See IR-31-REGISTRY-COVERAGE.

## 2. Nine-site status (COMPUTED + OWNER-REPORTED)
All nine top files are NOT unique under the brief's lane rule (within-3 px share 97.6–100% against a denser site). Zeros outside: GEMSDOE32 (0.2778) and GEMSDOE36 (0.2750), both already submitted. Full table: README and docs/executive-summary-2026-10-31.html.

## 3. Hypotheses (ranked; none validated)
| Rank | Id | Layer | Why it could catch a missing fault | Cost | Status |
|---|---|---|---|---|---|
| 1 | H-HF1 | USGS Great Basin heat-flow maps, DOI 10.5066/P9BZPVUC ([catalog.data.gov](https://catalog.data.gov/dataset/heat-flow-maps-and-supporting-data-for-the-great-basin-usa)) | Independent physical channel: conductive heat-flow residual where upflow follows faults. Mimic: pluton or sediment-blanket heat flow. | medium (124 MB) | **BLOCKED**: sciencebase.gov unreachable |
| 2 | H-REG1 | Registry coverage (diagnostic only) | Tests whether registry-avoided pixels predict truth. E5 says anti-predictive. | none | diagnostic; do not use to pick dots without owner review (crowd-information leakage risk) |
| 3 | H-GRAD1 | NBMG/SMU Temperature Gradient Map of the Great Basin ([geothermaldata.org metadata](https://data.wu.ac.at/schema/geothermaldata_org/MTEzMzRlOGYtOGJlNy00OTUwLWFlOWEtM2QyYzYyYjkzOTky)) | Shallow gradient excess not explained by the catalogue; wells in known geothermal areas excluded. | low once fetched | **BLOCKED**: host not in allowlist |
| 4 | H-QF1 | USGS Quaternary Fault and Fold Database ([USGS Faults](https://www.usgs.gov/programs/earthquake-hazards/faults), DOI 10.5066/P9BCVRCK) | Independent fault prior | low | partly tested (GDR QFaults-derived layers used earlier); expected gain low |

Not new (already tested or rejected): LiDAR scarps, GeoDAWN, Euler, seismicity, SGMC, B2-style repulsion (E4), tip-stepover (H33d), soft catalogue prior (E1), lane-first (E2), bound-fill (E3), clean halo (E5).

## 4. Irregularities
See registry/irregularities.json IR-31-* (12 new entries plus IR-31-BF1-BUILD-RECORD-DELETED). Highest severity: GEOM-HORSE-GRID, NAN-SCORED, UNIQUENESS-METRIC, REGISTRY-COVERAGE, HOLDOUT-PROXY-OFFSCALE, LEADERBOARD-CONFLICT, SCIENCEBASE-BLOCKED.

## 5. Budget (owner decision)
Stated budget: 3 experiments or 2 hours. This session ran E3, E4, E5 (3). Earlier pre-registrations E1 (H-SP1) and E2 (H-LF1) are in the same numbered series (knowledge/54, /55). If they count, the cap was exceeded. Wall clock is about 1.7 hours. Owner decides whether to accept.

## 6. Next steps
1. Owner: lane-rule scope and uniqueness definition for the competition.
2. Owner: resolve geom-horse-ensemble grid, or confirm the correct reference.
3. Owner: pinned copy of the USGS heat-flow ZIP or NBMG grid (or allow hosts). Then pre-register H-HF1 or H-GRAD1 before running.
4. Owner: organizer receipts for every scored file; resolve NaN-scored and leaderboard conflicts.
5. No slot without a unique file that beats its paired comparator on fresh virgin seeds and passes the lane gate on all readable rasters with no UNVERIFIED reference.

## 7. Run card
See evidence/run_card_967c20f7_2026-10-31.json.
