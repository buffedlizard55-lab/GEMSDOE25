# 17 · Focus-site forensics: why 0.2778 is the group best, and what would have to be true to beat it

**Date:** 2026-10-25 (this session, branch `arena/a499a7dc-gemsdoe25`).
**Evidence classes:** `OWNER` = supplied in the owner's 2026-10-25 message or read on a sibling
GitHub-Pages site (not an organizer receipt) · `COMPUTED` = reproducible in this repo ·
`READ` = read at the cited page in a previous session and recorded in `registry/` ·
`INFERENCE` = reasoning with assumptions stated. No DrivenData page was accessed in this
session (AGENTS.md rule 3). **No number below is ORGANIZER-CONFIRMED.**

## 1. The nine focus sites — highest owner-reported score on each

| Site | Highest artefact named by the owner | Owner-reported DTI | Class |
|---|---|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | OWNER |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | OWNER (see IR note §5) |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | OWNER |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | OWNER |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | OWNER (see IR note §5) |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | OWNER |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | OWNER |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | OWNER |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | OWNER |

Sibling pages re-read this session (2026-10-25) for the two highest:
<https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html> and
<https://buffedlizard55-lab.github.io/GEMSDOE36/docs/>. GEMSDOE32's page now states the
H33-2-B2 file "was already submitted — owner-reported score 0.2778. Do not resubmit it",
and carries newer, unscored lanes (Arena41 PF-only, gates failed; H32-WIN-46090). Those
newer files are **not** in this repo's pinned registry, so lane checks here cannot include
them (limitation, recorded in the run card).

## 2. The 0.2778 file, decomposed (what each step bought, on owner-reported numbers)

The champion is a three-step chain, and each step's owner-reported increment can be read off
the focus table plus the older registry (`registry/live_scores.json`):

| Step | Transformation | Owner DTI | Δ |
|---|---|---:|---:|
| 0 | `h19-5` solid multiline surface (121,131 px; COMPUTED count in `evidence/why_0_2477.json`) | 0.1922 | — |
| 1a | `dot_thin(h19-5, 1.5)` — score-blind geodesic dotting (COMPUTED pixel-identical in this repo) | 0.2477 | +0.0555 |
| 1b | wider dotting to the 44,090-px "d2.8" budget | 0.2600 | +0.0123 |
| 2 | better base surface: `h27-4-solo-d28` at the same d2.8-style budget | 0.2708 | +0.0108 |
| 3 | `h33-2-b2`: delete every dot within 2 px (200 m) of the catalogue → 37,654 dots, zeros outside | 0.2778 | +0.0070 |

**Reading (INFERENCE, from the metric in `src/gems25/metric.py`, α=0.2, β=0.8, 300 m
triangular kernel):** DTI = TPw / (TPw + 0.2·FPw + 0.8·FNw). A truth pixel's credit is the
*maximum* kernel value over nearby dots, so the second dot covering the same truth pixel
adds ≈0 credit but ≈1 unit of FP mass (charged 0.2). Step 1 is therefore pure emission
economics — same geology, less redundant mass — and it is the largest single gain in the
whole group history (+0.068 over steps 1a+1b). Step 2 says detector quality still matters
at fixed emission (+0.011 for a different surface). Step 3 is another deletion: a dot is
worth keeping iff its marginal credit/FP ratio exceeds α·D/(1−α·D)
(`gems25.metric.marginal_inclusion_ratio`); at D=0.2778 that bar is 0.0588. Deleting the
≈2.5k catalogue-flank dots helps **iff** their mean marginal ratio was below the bar.

**Why step 3's mechanism is not proven (flagged, not assumed):**
1. It is a single artefact with no paired CI; GEMSDOE32's own page projected 0.2747 for it,
   not 0.2778 — the realised claim exceeds its own model.
2. This repo's READ record of the staff clarification (`knowledge/03`) says test labels
   include "corrections or modifications" **within 300 m of known traces**. A blanket
   200 m exclusion deletes exactly the pixels that could earn correction credit.
   GEMSDOE36's page asserts adjacent-to-known dots earn "zero credit" — that contradicts
   the staff wording as recorded here, so it is treated as a sibling inference, not a fact.
3. The catalogue-gap holdout cannot test catalogue-proximity pruning: its truth *is*
   catalogue components (IR-25-HOLDOUT-DOES-NOT-TEST-PRUNING).

## 3. Can a new file beat 0.2778? (honest, quantitative answer)

* Arithmetically, +0.01 over 0.2778 at constant mass needs ≈+4 % mean credit per emitted
  pixel; reaching the owner's 0.3195 needs ≈+25 % (GEMSDOE32's own gap math vs its
  0.3262 leader read; both leader numbers are OWNER claims here, and the brief also
  contains a conflicting 0.4413 — IR-25-LEADERBOARD-CONFLICT stays open).
* Emission-only tricks on an *existing* surface are nearly exhausted in this repo's
  evidence: the H28 holdout factorial found spacing 2.4–3.0 px near-flat, the modelled
  `dot_thin(h19-5,d)` ceiling is the already-shipped d2.4 file, H31's credit-field
  re-selection was negative (−0.0007), and GEMSDOE32's greedy-vs-dot-thin contrast flips
  sign between its two instruments (+0.0100 holdout / −0.0045 truth-model). The remaining
  lever with headroom is **credit density from a better detector** — step 2 above bought
  +0.011 with no emission change.
* **Not demonstrated, and not demonstrable from the holdout alone.** The holdout is a
  catalogue-gap proxy (proxy↔live Spearman +0.33, n=24, n.s., GEMSDOE24). This session
  therefore tests one new *detector* block under a frozen gate (knowledge/18) and labels
  the result HOLDOUT-DTI only. Any statement "this beats 0.2778" would be a projection,
  and per protocol a projection is never written as a score.

## 4. What makes this session's lane different from all nine focus sites

Focus-site winners share: an h19-5/h27-4-family ridge surface, score-blind or score-ordered
dotting at ≈37–44k dots, and (32/36) a B=2 catalogue-flank prune; 36 adds an Anderson
orientation filter; 28's variants add Euler-deconvolution tips. This session's lane
(knowledge/18) keeps this repo's validated HGB detector + sapd2.4 emission **fixed** and
adds a *depth-sliced potential-field* feature block (FFT upward-continuation residuals of
RTP + conductive-base flexure) that no focus site and no prior arm in this repo uses
(family A is single-scale; the pinned `TMI_up150` band is documented but unused —
verified by grep over `src/`, `scripts/`, `tests/`). Uniqueness is additionally enforced
mechanically: Spearman + 3-px dot-overlap vs every restored registry raster
(`scripts/check_lane_duplicates.py`) before the file is promoted.

## 5. Irregularities in the supplied list (flagged for owner review)

* **Same raster, three names/scores:** the D2.8 content (`e56ea318af89`, SHA-256
  `91eae1ca…`) appears as GEMSDOE25's 0.2600, GEMSDOE30's
  `d28-poisson300m-offcat-44090-…-91eae1ca` 0.2600, and in this repo's registry as an
  *unscored* GEMSDOE24 alternate that was withdrawn here as a duplicate download
  (IR-25-DUPLICATE-DOWNLOAD). The score claim is now recorded as OWNER; the file itself
  remains "do not submit as new" in this repo.
* **Leaderboard conflict unresolved:** brief states 0.4413 and 0.3195; GEMSDOE32 states
  0.3262 (#1, read 2026-10-04). None verified here.
* Several listed artefacts share content-id prefixes across sites (e.g. `8acb75e1` on
  GEMSDOE28 and GEMSDOE31 at the same 0.2708) — consistent with re-hosting, recorded as
  such, not as independent confirmations.
