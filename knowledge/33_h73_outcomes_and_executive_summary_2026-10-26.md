# H73-PM outcomes, nine-site executive summary & the 0.2778 question (2026-10-26)

**Branch:** `arena/11c66d52-gemsdoe25` · **Pre-registration:** [`knowledge/32`](32_preregistered_h73_pm_2026-10-26.md)
(committed `88f75fe` before any fit) · **Run card:** [`registry/run_card_h73_2026-10-26.json`](../registry/run_card_h73_2026-10-26.json)

**Top-line decision — read this first:**

> **OK TO DOWNLOAD: YES** (unique research GeoTIFF below, for inspection/testing).
> **OK TO SUBMIT / SPEND A WEEKLY SLOT: NO — DO NOT SUBMIT.** H73-PM failed both frozen holdout gates.
> No file in any of the nine focus sites is currently eligible as a new submission.

| File to download | Score estimate (labelled) | Unique vs all listed GEMSDOE sites? | OK to submit? |
|---|---|---|---|
| [`gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros.tif`](../docs/downloads/gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros.tif) (42,997 dots; ZIP alongside) | **HOLDOUT-DTI 0.11343** (evaluator `gems25.metric.dti_binary`, α=0.2, β=0.8, R=3 px; 22,290 withheld-positive occurrences; cluster 95 % CI [0.0968, 0.1269]). This is a catalogue-gap proxy, **not** a leaderboard projection; no live estimate is claimed | **YES, density-aware** (`flagged_lane = []`, 80 rasters; 37.5 % of dots within 3 px of GEMSDOE32 B2, worst 56.0 % across 27 top-scorer rasters, worst 61.4 % own-lineage; surface \|ρ\| ≤ 0.129). Literal 70 % rule flags only the dense r13 lattice (206,895 dots) — geometrically unavoidable at this budget | **NO — DO NOT SUBMIT** (slot gate FAIL −0.03896 vs same-run CTRL_H35, CI entirely negative) |

DrivenData note (114 chars, for identification only — the file is not approved):
`GEMSDOE25 H73-PM | propensity-matched H35 deapron; holdout FAIL vs H35; DO NOT SUBMIT | id 1b7533ebb62b | unscored`

---

## 1. Executive summary — the nine focus sites

All historical scores are **OWNER-REPORTED** (no organizer receipt exists in any repo; none was fetched —
the agent never contacts DrivenData). Pixel counts/strata for the B2 chain were **recomputed this
session** from SHA-pinned mirrors; other rows carry forward the audited `knowledge/31` table.

| Rank | Site | Best historical submission (OWNER-REPORTED) | Dots | What it actually is | Eligible as a *new* submission? |
|---:|---|---|---:|---|---|
| 1 | GEMSDOE32 | `h33-h33-2-b2-…-e5eb6e7e-zeros` **0.2778** | 37,654 | `dot_thin(H19-5, 2.4) & (d_cat > 2 px)` — verified pixel-exact this session | **NO** — already scored; re-upload is a duplicate |
| 2 | GEMSDOE36 | `anderson-geothermal-pinn-38854-…` **0.2750** | 38,854 | B2 + 1,200 appended dots (96.9 % B2 overlap); appends *diluted* B2 | **NO** — already scored / near-copy |
| 3 | GEMSDOE28 | `h36-1-rung30-blind-r1-…` **0.2710**, `h27-4-r1-solo` **0.2708** | 37,660 / 40,199 | R1 = `D2.8 & (d_cat > 1 px)` verified pixel-exact | **NO** — already scored |
| 4 | GEMSDOE31 | `h27-4-solo-d28-…` **0.2708** | 40,199 | Mask-identical to GEMSDOE28 R1 | **NO** — duplicate of scored mask |
| 5 | GEMSDOE33 | `h33d-analog-tip-stepover-r30-…` **0.2632** | 41,865 | B2-family + tip/stepover additions (below B2: additions failed the 0.055 marginal-credit threshold) | **NO** — already scored |
| 6 | GEMSDOE25 (this repo) | `dotted-h19-5-d2-8-…` **0.2600**; supervised H66 **0.0742** | 44,090 | D2.8 = `dot_thin(H19-5, 2.4)` verified pixel-exact. New H73-PM research TIF above | Historical **NO**; H73-PM **download YES / submit NO** |
| 6= | GEMSDOE30 | `d28-poisson300m-offcat-44090-…` **0.2600** | 44,090 | Mask-identical to GEMSDOE25 D2.8 | **NO** — duplicate |
| 8 | GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-…` **0.2477** | 60,069 | `dot_thin(H19-5, 1.5)` | **NO** — already scored |
| 9 | GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-…` **0.2449**; best non-H19-5 `H29` **0.2190** | 61,328 / 38,012 | D1.5 derivative; H29 is a genuine supervised model | **NO** — already scored |

Strongest non-H19-5 architecture in the wider portfolio (context): GEMSDOE70 P8-OOF38k **0.2478**
(37,654 dots; strata recomputed this session 0.0 / 30.7 / 23.8 / 45.5 %, median 17.5 px) — proof that a
supervised model *can* approach B2 when its geometry matches B2's strata. Prompt-supplied overall
leaderboard figures (0.4413 and 0.3195) conflict and remain OWNER-REPORTED, unverified here.

## 2. Why 0.2778 — and what beating it requires (PhD-level synthesis, verified)

Under DTI (α=0.2, β=0.8, 300 m triangular kernel), `S = T / (0.2 (T+F) + 0.8 |G|)`. `TP_w` takes a
**max** over each truth pixel's 3-px disk; `FP_w` **sums** over emitted pixels. Hence (i) adjacent dots
on a ridge are redundant for credit but each pays full false-positive mass — dotting H19-5 removed
63.6 % of pixels at ~zero credit loss (0.1922 → 0.2600); (ii) a subset deletion raises `S` iff its mean
credit/pixel < `αS/(1−αS)` = 0.055 at S=0.26 — the 6,436 collar dots within 200 m of mapped traces were
deadweight because the scorer masks catalogue pixels and hidden faults are not offset copies of mapped
ones (0.2600 → 0.2778). **Zero new detections occurred along the chain** (all identities re-verified
pixel-exactly this session). Beating 0.2778 therefore requires *higher credit density at B2-like
strata* (≈37–44k dots, 0 % ≤2 px, ~45–50 % >20 px) — i.e. better far-field fault detection, not better
emission geometry. Two failure modes block supervised models: catalogue-apron propensity tilt in
training (addressed by H73-PM, below) and a component-split holdout that rewards apron-hugging and so
cannot certify far-field discovery (not yet fixed — see §4).

## 3. H73-PM Experiment 1 — results (HOLDOUT-DTI, draws 90–91, 8 cells/arm)

Full receipts: `evidence/h73_pm_screen/{design.json,cells.jsonl,analysis.json,results.md}`.
Leakage canary: every fitted column ≤ 0.843 AUC (cap 0.90; the max is `−d_vis` itself — the bias being
removed, computed from visible faults only).

| Arm | Pooled HOLDOUT-DTI | Far-field (>9 px) DTI | AUC | Dots 2–9 px | Dots >20 px |
|---|---:|---:|---:|---:|---:|
| CTRL_H35 (incumbent) | 0.15239 | 0.09787 | 0.809 | 55.4 % | 11.6 % |
| CTRL_BLIND_BD | 0.09395 | 0.07538 | 0.663 | 25.9 % | 47.1 % |
| PM_H35 | 0.11516 | 0.08264 | 0.729 | 20.3 % | 42.6 % |
| PM_DEAPRON | 0.11343 | 0.08212 | 0.729 | 24.7 % | 46.4 % |

* **Slot gate: FAIL.** PM_DEAPRON vs same-run CTRL_H35 paired gain −0.03896, cluster 95 % CI
  [−0.04717, −0.02456], 0/4 folds positive.
* **Far-field screen: FAIL** (one clause): PM_DEAPRON far-field 0.08212 beats CTRL_BLIND_BD (+0.00674,
  3/4 folds) with B2-like strata (46.4 % >20 px ≥ 35 %), but does **not** beat CTRL_H35 far-field
  (0.09787). Even at >9 px, hidden *catalogue components* remain splinters of visible systems that
  family-E density features legitimately localize — the component-split holdout cannot distinguish
  that from live far-field discovery.
* **What H73 proved:** propensity matching (a) mechanically restores live-like geometry without any
  emission trick (PM_H35 with H35 emission already puts 42.6 % of dots >20 px vs H35's 11.6 %),
  (b) adds real signal over catalogue-free training (+0.0195 overall, +0.0067 far-field vs blind), and
  (c) cannot be certified by the current holdout. Per the frozen rule, Experiments 2–3 were not run;
  the full-footprint TIF was built for inspection only (deviation logged, IR-25-H73-BUILD-AFTER-GATE-FAIL).

## 4. Next steps, ranked (for the next session — do these first)

1. **H73-BW block-withheld selector** (pre-register before running): hide *all* components intersecting
   ~25-km blocks so test-truth `d_vis` is genuinely large; re-score CTRL_H35 vs PM_DEAPRON vs blind on
   identical cells. This is now the single blocking instrument — without it, no de-biased model's live
   value can be distinguished from holdout bias, and no slot decision is defensible.
2. If (1) shows PM ≥ H35 on block-withheld far-field: confirmation draws + two-population calibration
   (piedmont/concealed, GEMSDOE70-style budget split) as a fresh pre-registered experiment.
3. Only after a same-run gate pass on a *live-relevant* selector: rebuild, lane-audit, and let the
   owner (separate selector step, weekly cap) decide on a slot. Never spend a slot from an agent session.

## 5. Limitations & honesty notes

* No ORGANIZER-CONFIRMED score exists anywhere in this portfolio; every live number is OWNER-REPORTED.
* HOLDOUT-DTI is a catalogue-gap proxy with measured weak live correlation (GEMSDOE24: Spearman +0.33,
  n.s., n=24). It is used here only as a *paired, same-run* gate, never as a score forecast.
* Sandbox limits actually hit: no GPU / no `torch` in pinned requirements (~4 GB RAM, 2 cores) — the
  2-D CNN lane (knowledge/32 rank 4) and Sentinel-1 lane (rank 5, needs owner Earthdata credentials)
  are not viable from here. DrivenData is never contacted by the agent (Terms of Use); competition
  files come from the owner's SHA-pinned public GitHub mirrors, which proves mirror integrity, not
  organizer authentication.
* Data/doc irregularities found this session: IR-25-H73-BUILD-AFTER-GATE-FAIL (process),
  IR-25-D28-STRATA-DOC (D2.8 "8.6 % ≤2 px" in older tables is the ≤1-px share; ≤2-px share is 14.6 %).

Official sources for manual review: [competition](https://www.drivendata.org/competitions/306/competition-doe-gems/) ·
[problem & metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) ·
[rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) ·
[reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) ·
[GDR 1391](https://gdr.openei.org/submissions/1391) ·
[USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) ·
[INGENIOUS](https://gbcge.org/current-projects/ingenious/) · [EPSG:32611](https://epsg.io/32611) ·
[Tversky index](https://en.wikipedia.org/wiki/Tversky_index)
