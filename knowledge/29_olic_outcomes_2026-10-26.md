# 29 · OLIC outcomes + nine-site executive summary (2026-10-26)

**Lane:** 2-D spatial-context / oriented line continuity (OLIC) added to H35 — provisional lane recorded
in `knowledge/29_preregistered_olic_line_continuity_2026-10-26.md` (commit `c756dc7`, before any fit).
**Experiments used: 1 / 3** (screen failed its frozen gate → confirmation and artifact steps prohibited).
**Verdict: NEGATIVE. No OLIC GeoTIFF exists. OK TO SUBMIT: NO.**

## Executive table — what to download, estimated score, uniqueness

| File to download for submission | Estimated leaderboard score | Unique vs the nine focus sites? |
|---|---|---|
| **NONE — no file is approved** | **NOT ESTIMABLE** (no ORGANIZER-CONFIRMED anchor; a projection is never written as a score) | N/A — no candidate raster was placed, so surface/final-dot lane checks are **NOT RUN**, not passed |
| H71 research TIF `…9eb0c31e5149-zeros.tif` (testing only, DO NOT SUBMIT) | NOT ESTIMABLE; HOLDOUT-DTI 0.0506 vs H35 0.1499 | Density-aware unique vs 21 top-scorers (15.4% vs B2); literal lattice flag `IR-25-LANE-DENSITY` |

## Nine focus sites (all scores OWNER-REPORTED; no organizer receipt in this repo)

| Site | Best supplied file | Reported | Best-submission guidance |
|---|---|---:|---|
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | Strongest historical exemplar; already submitted → historical only |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-…-zeros` | 0.2750 | = B2 + 1,200 dots (computed); additions diluted |
| GEMSDOE28 | `h36-1-rung30-blind-r1-…-nan` | 0.2710 | R1-style variant; historical only |
| GEMSDOE31 | `h27-4-solo-d28-…-nan` | 0.2708 | Pixel-identical mask to GEMSDOE28 R1 — not independent |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-…` | 0.2632 | B2-family variant, lower claim |
| GEMSDOE25 | `dotted-h19-5-d2-8-…-nan` | 0.2600 | D2.8 emission of H19-5 |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-…` | 0.2600 | Identical 44,090-px mask to GEMSDOE25 — not independent |
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-…-nan` | 0.2477 | `dot_thin(H19-5,1.5)` exactly (computed) |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-…-nan` | 0.2449 | D1.5 + 1,259 gap-closure px; below D1.5's claim |

Source: `knowledge/27_ranked_hypotheses_and_review_2026-10-26.md` (freshly recomputed pixel identities,
`evidence/focus_sites_forensics.json`). Conflicting overall-leader claims 0.4413 / 0.3195 are unverified.

## Why B2 (0.2778, OWNER-REPORTED) led, and can we beat it?

Computed chain: H19-5 (0.1922) → D1.5 (0.2477) → D2.8 (0.2600) → R1 (0.2708) → **B2 = D2.8 minus
6,436 dots within 2 px of the catalogue (0.2778)**. Under DTI `S=T/(0.2(T+F)+0.8N)`, removing a dot
helps iff its credit/false-positive ratio < `0.2S/(1−0.2S)` ≈ 0.059 at S=0.2778; collar dots near
known traces plausibly carry near-zero *new*-truth credit. GEMSDOE36 adding 1,200 dots back lowered
the claim (0.2750) — consistent, not proof (hidden labels unavailable).
**Beating it requires new true-fault pixels at credit/dot > τ ≈ 0.059 that H19-5's surface misses.**
OLIC was a candidate source of such pixels; its holdout screen says the line-continuity signal, added
to H35, does not recover withheld catalogue faults better than H35 alone.

## OLIC screen result (HOLDOUT-DTI, evaluator `gems25.holdout.v1.2-buffered-4quad-pooled-dti`, α=0.2, β=0.8, R=300 m)

Draws [82, 83] × 4 folds, 22,929 withheld positives. Candidate pooled **0.147690** vs same-run H35
**0.146976**; paired fold-mean gain **+0.000849**, 95% CI [−0.004778, +0.006475], **2/4 folds positive**
(NW −0.001128, NE +0.004661, SW −0.003017, SE +0.002879). Leakage canary PASS (max feature-alone
AUC 0.6205 ≤ 0.90). Gate (gain > +0.001 ∧ ≥3/4 folds ∧ worst ≥ −0.010 ∧ hug Δ ≤ +0.10): **FAIL**
(gain and folds). Per the frozen rule: no confirmation on draws [84, 85], no retune, no raster.
Mimic that likely explains the null: roads/contacts/flow margins supply long straight edges that
HGB already prices in per-pixel; continuity adds little beyond the edge magnitudes themselves.

Data restored this session from SHA-256-pinned owner mirrors (`scripts/restore_data.py` core/external/scored);
work cache rebuilt bit-identical to `evidence/work_cache_hashes.json` (all 6 hashes MATCH — no comparator drift).
Official links: [competition](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) ·
[GDR 1391](https://gdr.openei.org/submissions/1391) · [GeoDAWN](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) ·
[EPSG:32611](https://epsg.io/32611) · [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
