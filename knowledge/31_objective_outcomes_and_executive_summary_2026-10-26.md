# 31 · Outcomes + nine-site executive summary (2026-10-26, training-objective session)

Branch `arena/f1967d4f-gemsdoe25` · Pre-registrations: [knowledge/29](29_ranked_hypotheses_and_preregistration_2026-10-26.md)
(commit `005e115`, before any fit), [knowledge/30](30_preregistered_ign3_experiment3_2026-10-26.md) (commit `7806b5c`)
· Run card: [`registry/run_card_objective_2026-10-26.json`](../registry/run_card_objective_2026-10-26.json)
· Experiments used: **3 / 3**. No DrivenData page was accessed (AGENTS.md rule 3); the agent never uploads.

## 0. The generated GeoTIFF — is it OK?

| Question | Answer | Automated evidence (no human inspector involved) |
|---|---|---|
| File | [`docs/downloads/gems25-obj-bin-greedy-k3p5-20261026-3646faf70507-zeros.tif`](../docs/downloads/gems25-obj-bin-greedy-k3p5-20261026-3646faf70507-zeros.tif) (+ NaN twin + single-TIF `.zip`) | SHA-256 `160dbdc0c2abc25bd40a3f38a36c2a69f8a02503337dea7ab706f6d77a08934d`, content id `3646faf70507`, **53,522** binary dots |
| **OK to download for testing?** | **YES** | Independent rasterio audit (`evidence/objective_independent_audit_zeros.json`): single-band float32, EPSG:32611, 3730×3292, transform exactly the template's, all 5,167,373 footprint values finite in [0,1], **strict whole-array [0,1] passes** (zeros outside — the portal error *"Predicted values must be in range [0, 1]"* cannot trigger), 0 dots on catalogue pixels, ZIP contains exactly this TIF |
| **Unique vs previous *submissions*?** | **YES** | New SHA/content; vs 31 scored/external registry rasters incl. all 21 top-scorer mirrors: worst 3-px dot overlap **0.692** ≤ 0.70 cap, worst surface \|Spearman\| **0.108** ≤ 0.90; **vs GEMSDOE32 B2 (0.2778): overlap 0.320, ρ_surface 0.059** (`evidence/objective_lane_extended.json`) |
| **OK to spend a weekly slot?** | **NO — DO NOT SUBMIT** | All 3 pre-registered experiments failed to beat the same-run comparator (§3). Strict lane also fails vs this repo's own *unscored* HGB lineage (87.2 % vs H38 greedy file — same frozen stack, fresh seeds) and vs the dense r13 lattice (100 %, `IR-25-LANE-DENSITY`). Verdict `negative`; promotion is the owner's separate selector step and this evidence does not support it |
| Research note (116 chars — **not** for the competition form) | `GEMSDOE25 BIN greedy k3.5% \| HOLDOUT negative; DO NOT SUBMIT; no slot; not slot-approved; unscored \| id 3646faf70507` | Written into the checks JSON by the builder |

## 1. Nine focus sites — executive summary (fresh local audit, `evidence/focus_audit_local_2026-10-26.json`)

Every raster was re-read this session from SHA-256-pinned local mirrors (`data/registry_top`, pins in
`registry/top_scorer_sources.json`). Geometry below is **COMPUTED**; every score is **OWNER-REPORTED**
(no organizer receipt exists in this repo). "Best for the site" = highest supplied result; **none of
these files is eligible as a new submission** — they are prior submissions or pixel-identical copies.

| Site | Best supplied submission | OWNER score | Dots | Exact relation to the H19-5 parent (COMPUTED this session) | Executive verdict |
|---|---|---:|---:|---|---|
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | 37,654 | `B2 = D2.8 & (d(catalogue) > 2 px)` — identity re-verified XOR-free | **Strongest historical exemplar of the nine.** Already submitted; copying it would be a duplicate, not a strategy |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-…-9b9ea4e6-zeros` | 0.2750 | 38,854 | Exactly B2 + 1,200 dots (B2 ⊊ file verified) | The 1,200 additions *lowered* the reported score — direct evidence B2 sits near the useful-budget edge |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-…-b531dae0a36f-nan` | 0.2710 | 37,660 | Not a superset of R1: differs by +9,807 / −12,346 dots vs R1 at similar count | Best of 28's variants, but +0.0002 over plain R1 with ~22 k dot swaps — most along-ridge dot swaps are score-neutral |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-…-8acb75e1-nan` | 0.2708 | 40,199 | Mask identical to GEMSDOE28 R1 = `D2.8 & (d>1 px)` | Same submission geometry as 28's R1 under another name; B=1 prune only |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-…-cb490425926e` | 0.2632 | 41,865 | Re-admits near-catalogue dots: 1,377 at d≤1 px, 2,517 at 1–2 px | Negative control for B2: putting collar dots back cost 0.0146 vs B2 |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-…-e56ea318af89-nan` | 0.2600 | 44,090 | `D2.8 = dot_thin(H19-5, 2.4)`; shells: 3,891 dots at d≤1, 2,545 at 1–2 px | The parent geometry of R1/B2; superseded by its own pruned children |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-…-91eae1ca` | 0.2600 | 44,090 | Mask identical to GEMSDOE25 D2.8 | Not independent evidence for anything except the mask's score reproducibility |
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-…-989f59505db1-nan` | 0.2477 | 60,069 | `D1.5 = dot_thin(H19-5, 1.5)` ⊊ H19-5 (121,131 px, 0.1922) | The original dotting step: −61,062 redundant pixels bought +0.0555 reported DTI |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-…-5512495c6bd1-nan` | 0.2449 | 61,328 | Exactly D1.5 + 1,259 bridge pixels | Gap-closure additions *reduced* the reported score vs D1.5 — added mass without credit |

**If the owner ever wants the single strongest historical reference point, it is GEMSDOE32 B2
(OWNER-REPORTED 0.2778).** It must not be re-submitted (duplicate), and its score is not
organizer-confirmed in this repo. The brief's overall-leader figures **0.3195** and **0.4413** are
mutually conflicting owner claims with no receipt here (`IR-25-LEADERBOARD-CONFLICT`); they are not
used as targets anywhere in this session's arithmetic.

## 2. Why did B2 get the highest reported score, and can a unique file beat 0.2778?

**Why (conditional explanation — facts COMPUTED, score deltas OWNER-REPORTED).** The official metric
(`src/gems25/metric.py`, α=0.2, β=0.8, 300 m triangular kernel) credits each truth pixel with the
*maximum* kernel value over nearby dots. A second dot covering the same truth therefore adds ≈0
credit but a full false-positive unit. The whole 0.1922 → 0.2778 chain is one detected set with
progressively less redundant mass: geodesic dotting (D1.5/D2.8) removes neighbours whose kernel
support is already covered, and the B1/B2 steps delete the 3,891 + 2,545 dots hugging the mapped
catalogue at ≤200 m. A dot only pays for itself above the break-even ratio
τ = αD/(1−αD) ≈ 0.056–0.059 at these scores; both deletions *raising* the reported score implies —
conditional on the reported scores — that the deleted shells earned below τ. GEMSDOE36 (+1,200 dots
→ lower score) and GEMSDOE33 (collar dots restored → lower score) are independent signposts of the
same economics. **What is not proven:** that B2's deleted dots were individually false (hidden
labels are unavailable, one artefact per step, no paired CI), and a blanket 200 m exclusion sits in
tension with the recorded staff clarification that test truth includes corrections within 300 m of
known traces. The safe statement is: *on the reported numbers, near-catalogue mass on this surface
was not earning its keep*.

**Can a unique file beat 0.2778?** Arithmetically yes; demonstrated **no**. At constant emitted
mass, +0.01 DTI needs ≈+4 % weighted credit; 0.3195 would need ≈+15 % credit over B2 and 0.4413
≈+59 % (identities in `gems25.metric`; both targets unverified). Emission economics on the H19-5
surface is exhausted (B3 shell already prices above τ in prior inversions), so the gap can only
come from a *detector* that finds true faults H19-5 misses or localises them better. This session
tested the remaining cheap detector lever — training-objective geometry — three times (§3) and
found nothing that beats the incumbent stack even on the friendly proxy. No file generated here is
claimed, projected, or expected to score above 0.2778.

## 3. Experiments (all HOLDOUT-DTI; evaluator `gems25.metric.dti_binary`, α=0.2, β=0.8, R=3 px; hide-and-recover, 4 quadrants, hide 20 %, collar 15 px)

Comparator recomputed in **the same run** every time (`IR-25-COMPARATOR-DRIFT`); caches bit-identical
to `evidence/work_cache_hashes.json` (6/6 SHA-256 match this session). Features froze at the H35-B
stack (BDE + 7 extras + `H27_tip` + 3 H34); emission froze at H38 greedy (primary) / sapd2.4
(diagnostic). Canaries = single-feature AUC for `H27_tip` + H34 columns (cap 0.90) plus
train-region containment assertions for the new samplers (unit-tested, `tests/test_objective.py`).

| Exp | Arm (primary) | Draws | Withheld + | Candidate pooled DTI | BIN pooled DTI | Paired fold-mean Δ [95 % CI] (folds +, worst) | Pooled Δ (boot CI) | OC pooled Δ | Canary max | Gate |
|---|---|---|---:|---:|---:|---|---:|---:|---|
| 1 | **TENT** kernel-regression target | 90–91 | 22,290 | 0.157223 | 0.157371 | **−0.000274** [−0.0077, +0.0071] (2/4, −0.0057) | −0.000148 ([−0.0045, +0.0036]) | −0.000908 | 0.6209 PASS | **FAIL** |
| 2 | **HARDNEG** hard-negative mining | 94–95 | 22,073 | 0.115419 | 0.155776 | **−0.042691** [−0.0703, −0.0151] (0/4, −0.0645) | −0.040356 ([−0.0564, −0.0286]) | −0.039676 | 0.6239 PASS | **FAIL** |
| 3 | **IGN3** ring-excluded negatives | 100–101 | 22,397 | 0.154630 | 0.155492 | **−0.000895** [−0.0033, +0.0015] (1/4, −0.0024) | −0.000861 ([−0.0019, +0.0004]) | −0.000896 | 0.6301 PASS | **FAIL** |

Reading, in one paragraph each:

* **TENT** is a wash with the wrong side-effects: pooled Δ −0.0001, surface AUC 0.809 → 0.793,
  hug-share 0.044 → 0.093. Pricing the credit ring pulls emission toward the *visible* catalogue;
  a proxy whose truth *is* catalogue polylines cannot reward scarp-crest firing. The live rationale
  (trace-vs-crest offset) remains untestable with this proxy — and untestable claims do not spend slots.
* **HARDNEG** is decisively harmful (−0.043, boot CI entirely negative): the "hardest negatives"
  under a catalogue-trained model are mostly genuine fault-like scarps near the catalogue system,
  so stage-2 training teaches broad suppression of exactly the target signature (AUC 0.803 → 0.749).
* **IGN3** shows the Exp-1 diagnostic (+0.0020, SE-fold driven) was noise: on fresh draws it is
  −0.0009 with 1/4 folds positive. Ring-pixel label noise, at the 1.5 px exclusion already in
  `Cell`, is evidently not costing measurable pooled DTI.

## 4. What this session changes for the selector

Nothing about the incumbent: the BIN stack (H35-B surface + H38 greedy emission, twice
gate-passed in October sessions) remains this repo's holdout best, and the new TIF is a fresh-seed
rebuild of it. The session's deliverable is the *negative knowledge* that training-target geometry
and hard-negative mining — the two cheapest untested levers — do not move this stack, plus the
fresh nine-site audit (§1). Per protocol, promotion to a real weekly slot is a separate selector
step; this session used **0 slots**.

## 5. Next work, ranked by P(Win) (for a future session, each needs its own pre-registration)

1. **Resolve the lane-policy deadlock first** (`IR-25-LANE-DENSITY`): under the literal rule no
   >21,713-dot file can ever clear the registry (the lattice halo leaves 6,514 eligible pixels),
   and same-stack rebuilds always flag vs own lineage. A density-normalised two-sided overlap
   statistic, decided as policy (not smuggled into code), is the blocker for *any* future promotion.
2. **Get one organizer-anchored score for the H35/H38 lineage** (owner's selector decision): a
   single real receipt would recalibrate the proxy-vs-live relationship that every gate here leans on.
3. **2-D spatial-context model** (knowledge/29 rank 4): the only remaining high-ceiling detector
   lever; needs GPU-class compute or a patient CPU schedule and patch-leakage safeguards.
4. **LINE along-strike support features** (knowledge/29 rank 3): cheap, untested, but the
   feature-column track record (±0.004 across 7+ blocks) sets a low prior.
5. **External absolute-elevation shoreline test** (rank 5): blocked until USGS 3DEP tiles are
   actually obtained and coverage-verified on a machine that can reach the National Map.

## 6. Official sources for manual review (linked, not fetched by automation this session)

[Competition](https://www.drivendata.org/competitions/306/competition-doe-gems/) ·
[Problem & metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) ·
[Rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) ·
[Reference solution (read this session via GitHub)](https://github.com/drivendataorg/gems-prize-reference-solution) ·
[GDR 1391](https://gdr.openei.org/submissions/1391) ·
[USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) ·
[USGS 3DEP](https://www.usgs.gov/3d-elevation-program) ·
[EPSG:32611](https://epsg.io/32611) ·
[Tversky index](https://en.wikipedia.org/wiki/Tversky_index)
