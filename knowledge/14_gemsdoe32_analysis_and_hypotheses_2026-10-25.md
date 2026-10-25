# GEMSDOE32 (0.2778) — why it scored, what we can and cannot verify, and the next hypotheses

Date: 2026-10-25 (UTC). Evidence classes: **OFFICIAL** (read at the cited page), **OWNER/GROUP CLAIM** (a sibling site's own
number or statement; not an organizer receipt), **COMPUTED** (script + JSON named here), **INFERENCE** (stated as such).

## 0. Scope and what was *not* done

* The DrivenData competition and leaderboard pages were **not** fetched by this agent. `AGENTS.md` rule 3 forbids automated
  access to drivendata.org. Every leaderboard figure below is a sibling site's claim.
* Nothing here is an organizer score. No file was uploaded.

## 1. What the GEMSDOE32 page says (fetched 2026-10-25, `fetch_page` on the page, 2 chunks)

Source: <https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html>

| Claim (sibling site) | Class | Status here |
|---|---|---|
| Primary file `gemsdoe32-h33-h33-2-b2-…-zeros.tif` = the 0.2708 base with every dot at distance ≤ 2 px from the catalogue deleted: 37,654 dots, 0 on-catalogue | OWNER/GROUP CLAIM | description only; file not inspected |
| Mechanism: "every unit of prediction mass that is not the best cover of a truth pixel costs 0.2"; break-even credit 0.0548 per dot | OWNER/GROUP CLAIM + COMPUTED | COMPUTED: `gems25.metric.marginal_inclusion_ratio(0.26) = 0.05485` (the ratio form αD/(1−αD)); the page's shorthand "0.2·0.26 = 0.0520" is the linear form and is off by ~0.0029 (IR-25-BREAKEVEN-SHORTHAND) |
| Live-mirror (own holdout, catalogue truth) +0.00487 over the 0.2708 base in 4/4 quadrants; projected 0.2747 | OWNER/GROUP CLAIM (projection) | not verified; a projection is never a score |
| Truth model: 12,691 px, σ = 1.85 px, from GEMSDOE25 H28 inference | INFERENCE (inherited) | the 12,691 and 1.85 px are fitted latent parameters, not verified hidden labels |
| Their own finding: the holdout (catalogue truth) and the truth model *disagree* about surface-greedy packing (+0.0100 holdout, −0.0033 truth model) | OWNER/GROUP CLAIM | noted; this is the key caution in §3 |
| Leaderboard: #1 nchuzhoy 0.3262, #2 DARD 0.3195, #3 alexoktaba 0.3042, "read 2026-10-04" | OWNER/GROUP CLAIM | not verified here (drivendata not accessed). **Conflicts** with the brief's "0.4413 high score" and "0.3195 highest" lines (IR-25-LEADERBOARD-CONFLICT) |

## 2. Why the 0.2778 file beat its 0.2708 base (our reading, INFERENCE unless marked)

1. **DTI is a budget.** DTI = TP / (TP + 0.2·FP + 0.8·FN). With a fixed emitted mass, the score rises only when the
   credit per emitted unit rises. A dot pays for itself only if its expected credit exceeds the break-even ratio
   αD/(1−αD) (COMPUTED: 0.0573 at D = 0.2708; 0.0588 at D = 0.2778). Removing a dot whose expected credit is below that
   ratio raises DTI even though it removes a little true credit.
2. **Dots within 2 px of the catalogue are the candidates for that removal, but only under one assumption.** The scorer
   masks known pixels, so a dot hugging the catalogue gets credit only from hidden truth within 3 px of it. If hidden
   faults rarely sit that close to mapped traces (plausible, because the catalogue already captures the nearby traces),
   those dots are pure false-positive mass. **Whether this holds for the real hidden set is unknown and is not testable
   from public data here** (INFERENCE; the group states the same limit, IR-32-PROXY-01).
3. **Scale check (COMPUTED on our own H31-C file, 48,714 dots):** only 964 dots (2.0 %) lie within 2 px of the catalogue
   and 3,862 (7.9 %) within 3 px. So the same pruning would touch very little of *this* file. Its effect is therefore a
   property of the 0.2708 base, not a general improvement.

**Verdict on the 0.2778 mechanism:** plausible and metric-consistent (it is a credit-per-pixel argument), but its key
premise, that hidden truth is rarely within 2–3 px of the catalogue, is an untested prior. It is not a validated gain.

## 3. Can we exceed 0.2778? Honest answer

* **Not demonstrated.** No file in this repo has been scored above 0.2600 by a verified receipt. The 0.2778, 0.2750,
  0.2708 numbers are sibling claims.
* The holdout here uses catalogue components as truth. It **cannot** reward or punish catalogue-proximity pruning,
  because the hidden truth is the catalogue itself (IR-32-PROXY-01 applies here too). So our holdout cannot validate the
  0.2778 mechanism.
* The only lever the group's own analysis identifies as large is credit density at a fixed budget (≈ +25 % needed to reach
  0.3262). That requires a better detector, not just pruning (INFERENCE from their §"Can we beat 0.3262").

## 4. What this session ran (pre-registered H31-1; see `knowledge/13_…`)

| Item | Result | Class |
|---|---|---|
| Control C (H28 comparator config) reproduces `evidence/h28_holdout/cells.jsonl` per cell | 8/8 cells, max abs diff 0.0 | COMPUTED (`evidence/h31_screen/analysis.json`) |
| A1 credit-field candidate selection, paired vs C, 4 folds × draws 0–1 | mean gain −0.00068; 2/4 folds positive; worst −0.00366; **screen failed** | HOLDOUT-DTI, n withheld positives per fold 1,879 / 2,408 / 3,798 / 3,207 |
| A2 (kfrac 0.0245) | mean gain −0.00808; 1/4 folds positive; **negative** | HOLDOUT-DTI |
| Control C mean holdout DTI | 0.149668, 95% CI (fold t) 0.133069–0.166266 | HOLDOUT-DTI |

Per the pre-registration, A1 gets no confirmation run. **Verdict: negative.** One of the three allowed experiments is used.

## 5. Ranked hypotheses for the next step (expected DTI gain = planning bracket, not an estimate)

| Rank | ID | Layer(s) | Physical/statistical signature | Why it should find an off-catalogue fault | How it differs from the repo | Expected gain | Cost | Validation status |
|---|---|---|---|---|---|---|---|---|
| 1 | H32-1 | USGS/INGENIOUS catalogue geometry | distance-to-catalogue prior for *hidden* truth (credit-per-dot model) | faults the catalogue lacks may lie off the mapped traces; dots that cannot earn credit are FP mass | GEMSDOE32 mechanism; not in our repo | +0.00 to +0.01 (bracket) | low | **Not validatable on the current holdout** (truth = catalogue). Needs a holdout whose truth is restricted to components ≥ 200 m from visible traces; propose that as a new pre-registration |
| 2 | H32-2 | scarp/LiDAR + H28 score | break-even marginal credit pruning: delete dots below αD/(1−αD) using holdout-calibrated credit | removes low-credit mass without new physics | uses `marginal_inclusion_ratio`; the repo has the function but no holdout arm for it | 0.00 to +0.005 | low | testable on the holdout now (same harness as H31) |
| 3 | H32-3 | DEM orientation | along-strike anisotropic dot spacing (wider across strike, tighter along a ridge) | a linear truth covered by dots at a fixed radius wastes cross-strike FP | isotropic dotting everywhere in the repo; H26-2 used strike only as a prior, not for spacing | 0.00 to +0.005 | medium | testable on the holdout; not run |
| 4 | H32-4 | external | a new independent layer (e.g., a gravity or heat-flow grid from an official source) | a new physical channel, not a re-weighting of existing ones | the repo's layers are catalogue, GeoDAWN, LiDAR, SGMC, GDR | unknown | high | **Not viable yet**: no free official source of the required resolution and coverage was checked in this session. Must be checked before it is proposed as viable |

**Recommendation:** H32-2 is the only candidate testable today with the existing harness and gate. Run it only if the
owner wants a further experiment; the pre-registration rule (commit first, then run once) applies. H32-1 has the largest
possible leverage but needs a new holdout definition first; do not spend a slot on it before that holdout exists.

## 6. Sources (for manual review)

* GEMSDOE32 page (sibling; claims): <https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html>
* Competition metric and format (official page; cited by `src/gems25/metric.py`, read by the repo on 2026-10-02; **not re-fetched in this session** per AGENTS.md rule 3): <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
* Rules PDF (NLR document 96647, cited by the sibling): <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
* USGS/INGENIOUS and GeoDAWN (the competition's own data sources, as cited in the repo): see `registry/sources.json`
