# 28 · Executive Summary: Which Focus-Site Submission Is Best & What Would Beat 0.2778 (2026-10-26)

**Scope:** GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36 (owner-reported scores from sibling repos, not organizer-confirmed; no drivendata.org page accessed, AGENTS.md Rule 3). All rasters compared pixel-exact vs pinned mirrors (`data/scored`, `artifact_ledger.json`).

## Focus-Site Score Table (OWNER-REPORTED claims — zero ORGANIZER-CONFIRMED receipts in this repo)

| Focus Site | Best Submission (owner claim) | Dots | Exact Transform vs H19-5 lineage (COMPUTED) | Why it is best in that site | Verdict for weekly slot |
|---|---|---|---|---|---|
| **GEMSDOE24** | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` **0.2477** | 60,069 | `D1.5 = dot_thin(H19-5,1.5)` (−61,062 redundant neighbours, 50.4% FP cut, 99.9% kernel coverage retained) | Only file in 24; parent of all later improvements | Outperformed by 0.2600+ successors — not the choice |
| **GEMSDOE25** | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` **0.2600** | 44,090 | `D2.8 = dot_thin(H19-5,2.4)` (−15,979 vs D1.5, Poisson-disk ≥2.83 px eliminates cone-overlap FP) | Optimal spacing at 2.4 px per H28 sweep (0.251 model ceiling) | Outperformed by B1/B2 pruning — not the choice |
| **GEMSDOE27** | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` **0.2449** | 61,328 | D1.5 ∪ 1,259 topo-gap bridge pixels (97.95% in H19-5) | Bridges add denominator without credit (0.2477→0.2449) | Worse than D1.5 alone — not the choice |
| **GEMSDOE28** | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` **0.2710** | 40,199* | `R1 = D2.8 & EDT(~cat)>1` (deletes 3,891 d≤1 px collar dots at 0.0010/px << τ=0.0549) | Highest among 28's four variants (others 0.2708,0.2649,0.2707); rung30 blind adds +0.0002 vs base R1 | Best in 28, but 0.2708/0.2710 < 0.2778 — runner-up only |
| **GEMSDOE30** | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` **0.2600** | 44,090 | Exact D2.8 (zeros outside) — byte-identical to 25's D2.8 | Same as 25 — tie | Same as D2.8 — not best overall |
| **GEMSDOE31** | `h27-4-solo-d28-20261004-8acb75e1-nan` **0.2708** | 40,199 | Exact R1 (B=1) — deletes same 3,891 collar dots as 28's best, different lineage | Ties 28's R1 | B=1 only — 0.0070 short of B2 |
| **GEMSDOE32** | **`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` 0.2778** | **37,654** | **`B2 = D2.8 & EDT>2` (deletes additional 2,545 at 1<d≤2 px, 0.0050/px << τ=0.0573)** | **Only focus winner that removes both low-credit shells; 52× and 11× below break-even; pure denominator reduction** | **Current best among all 9 focus sites (OWNER-REPORTED) — but no organizer receipt; do not re-submit this exact file (duplicate lane would be flagged >70% overlap)** |
| **GEMSDOE33** | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` **0.2632** | 41,865 | R1 ∪ 1,666 tip-adjacent d≤1 dots from D2.8 (re-admits low-credit collar) | Re-admission drops 0.2708→0.2632 (−0.0076) — negative control proving B1→B2 was correct | Worse than R1/B2 — not the choice |
| **GEMSDOE36** | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` **0.2750** | 38,854 | B2 ∪ 1,200 extra dots (96.91% is exact B2) at 0.0126/px < τ=0.0588 | Extra dots dilute B2 (−0.0028) — shows B2 is near-optimal budget | Close second (−0.0028) but still below 0.2778 |

**Clear winner among focus sites:** **GEMSDOE32 B2 0.2778** (37,654 px). It is 0.0068–0.0301 above every other focus-site best (next best is 36's 0.2750, then 28's 0.2710). The live leaderboard claim 0.3195–0.4413 is 0.0417–0.1635 above B2; reaching it would need +21–55% credit density (0.0672–0.0864 vs B2's 0.0556 break-even), which pruning alone cannot supply (H28 ceiling 0.251 for H19-5 family, B3 would hurt at 0.064/px > τ).

## Why B2 Won (PhD forensic summary)

See `knowledge/27_apfl_hypotheses_ranked_2026-10-26.md` §1 for full pixel-exact proof. Metric arithmetic `τ=0.2·D` makes any dot earning <0.052–0.0556 a net loss; B2's deleted shells earned 0.0010 and 0.0050. Geology: QFFDB vector traces offset 100–200 m from true scarp; unsupervised ridges parallel catalogue at d≤2 px carry no hidden-fault signal; hidden truth lies >200 m away, so pruning is safe if catalogue rarely within 200 m of hidden fault (untestable prior, IR-25-PROXY-LIMITS).

## Can we beat 0.2778 with a unique, competition-legal file?

**Yes — but only with a new detector, not by re-emitting H19-5.** Current repo's H28 model shows H19-5 family ceiling 0.251 (uniform N) / 0.2778 observed (non-uniform truth); 0.3195 needs +0.0317 beyond B2 = +0.1400 vs 0.1084 per-pixel credit (+29%). Our APFL piedmont-flexure detector (§2 ranked #1) targets the catalogue's biggest blind spot — Qal-piedmont faults — with catalogue-free LiDAR+gravity+depth coincidence, giving planning bracket +0.002 to +0.008 vs H35 control before pruning; combined with B2-style flank shielding (C-factor) it is the only lane with a non-zero mathematical path to 0.283–0.286 without re-using H19-5 dots.

Current download **gems25-apfl-piedmont-flexure-s3p0-k3p5-20261026-8aebdab87158-zeros.tif** (43,798 dots, 3.0 px) is **format-valid (16/16 hard checks), lane-unique (max |ρ| 0.15 vs 0.90, max 3-px overlap 0.30 vs 0.70, 1.00 vs lattice reported as non-discriminative halo 0.9987 → symmetric 0.30), content-unique (SHA 6648cbe… vs all scored mirrors), hug 3.9%**, and uses **zeros outside** (passes strict `(a>=0)&(a<=1).all()` validator that rejected old NaN-inside files). **OK to download: YES · OK to submit to weekly slot: NO — HOLDOUT-DTI gate not yet passed (pending draws 60,61), so it is testing-only, DO NOT SUBMIT until selector approves a fresh winning holdout.** Re-submitting any focus-site file byte-for-byte (e.g., B2's SHA c55bafc…) would be duplicate (>70% within 3 px) and violate Parallel-Run Protocol #1 — flagged as duplicate and stopped.

**Next selector gate:** Run APFL holdout screen on draws 60,61 (2 of 3 experiments left); need pooled HOLDOUT-DTI >+0.001 vs H35, ≥3/4 folds positive, worst ≥−0.010, hug ≤+0.10, canary AUC ≤0.90, and density-aware lane clean — then, and only then, a weekly slot may be considered.
