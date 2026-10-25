# 14 · GEMSDOE32's 0.2778 submission — analysis and what it implies (written 2026-10-25)

**Source read:** https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html (two chunks, fetched 2026-10-25). This is a sibling repo's public page; every number below is *their* claim and is NOT organizer-verified. No DrivenData page was accessed.

## The submission in question

| Field | Value |
|---|---|
| Site | GEMSDOE32, https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html |
| File | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` |
| Reported score | 0.2778 (their site lists it as their primary; the brief quotes 0.2778) |
| Submission name | `GEMSDOE32-H33-2-B2` |
| Note (177/200 chars) | `GEMSDOE32 H33-2-B2 | flank B=2 prune on the 0.2708 base: 37,654 dots, 0 within 200 m of the catalogue; live-mirror +0.00487 in 4/4 folds, safety 2.08, projected 0.2747; UNSCORED` |
| Format | single-band float32, EPSG:32611, 100 m, 3292×3730, 37,654 predicted pixels, every cell finite, values in [0,1], 0 NaN anywhere, no nodata tag, sha256 prefix `c55bafc470054e82…` |
| Fallback | NaN-outside twin `...-e5eb6e7e-nan.tif` (baeae3219bba6a19…); already-scored fallback anchor 0.2708 |
| Method (their words) | "flank B=2 prune on the 0.2708 base: 37,654 dots, 0 within 200 m of the catalogue" — i.e. dots taken from a 0.2708-scored base surface (h27-4-solo-d28 lineage, also seen as GEMSDOE28 h27-4-r1-solo-d2-8: 0.2708), with every dot at d(catalogue) <= 2 px deleted |

## Why it scored highest (their analysis, plus this repo's arithmetic)

The page's central claim: **the metric is a budget**. In the official DTI, every emitted pixel's false-positive mass is charged at alpha = 0.2, while one pixel covering a truth pixel earns at most 1.0 credit (kernel max at zero distance). Thinning a thick surface while keeping its geometry removes prediction mass whose truth was already covered by a neighbour, raising **credit per emitted pixel**. The break-even bar a pixel must clear is `k > 0.2 · DTI`; at DTI ≈ 0.26 that is `0.052` credit per dot. The group measured 0.0548 empirically — two routes, one answer.

This matches this repo's own measurement for the dotted H19-5 family (0.2477-labelled mirror = `dot_thin(H19-5, 1.5)`): credit per emitted pixel rose 0.0520 → 0.0893 when dotting removed redundant (overlapping-kernel) mass from 62% to 32% of captured kernel mass (`knowledge/10`, README H28 section).

Their live-anchored Monte Carlo truth model (source: this repo's H28 inference — 12,691 truth pixels, σ = 1.85 px) finds:
- `greedy_smoothfield_44090` beats `incumbent_dot_thin_44090` by **+0.0140 ± 0.0003 DTI, 16/16 draws positive** under the official metric
- Their shipped file scores 0.3038 MC mean DTI vs incumbent 0.2791 (**+0.0247, 12/12 draws**)
- Holdout proxy (catalogue truth, 4 blocked folds, matched pixel counts): greedy fixed-budget beats dot-thin matched **+0.0100, 4/4 folds**

## Can we beat 0.2778 / 0.3195? (conditional on their claims)

Their own gap math: public leader #1 (their verified read: nchuzhoy 0.3262; the user's stated target 0.3195 = DARD) vs the group's best owner claim 0.26 (this repo's D2.8 file) = **+0.0662, i.e. ≈ +25.5% in the score**, which through the metric's arithmetic is ≈ +25% more mean credit per emitted pixel at constant mass. Their stated conclusion: no public catalogue can supply that (the newest public compilation is already inside the given catalogue; 59,065 px, all but one within 300 m of it). The path they name: **a better detector plus the two-round objective** — cover the truth surface blurred by σ ≈ 1.85 px, not the surface itself; catalogue pixels excluded from the emission field.

## Caveats (evidence class = OWNER-REPORTED CLAIM)

- No organizer leaderboard page or receipt was accessed by this repo or by the GEMSDOE32 page authors; "0.2778" and even the leaderboard values are user-reported.
- The holdout truth is the visible catalogue, so it cannot reward a genuinely new fault (their IR-32-PROXY-01, matching this repo's IR-25-PROXY-LIMITS).
- Holdout-vs-live correlation in this group's prior record was weak (Spearman +0.33, n = 24, n.s.).
- Their MC truth model parameters (12,691 px, σ = 1.85 px) come from H28 inference conditional on owner-reported anchors — not verified hidden labels.

## What this repo should do differently

GEMSDOE32's approach is *geometry-first* (thinning/pruning a base surface). This repo's validated lever H26-0 (score-aware dotting, +0.0037, 4/4 folds, replicated +0.0034) is the same family. What is NOT yet tried here, per GEMSDOE32's own conclusion, is:

1. A **better detector** for faults missing from the catalogue (new geological features — see knowledge/15).
2. An **emission rule that targets the blurred truth**: dots placed 1–3 px *off* visible catalogue traces (the σ = 1.85 px blur scale), rather than on them, with catalogue pixels excluded. This is a genuine departure from `dot_thin` (keeps on-surface pixels) and `score_ordered_dots` (re-selects on-surface pixels by score).

Both are cheap, unsupervised, and validatable now on the spatially blocked holdout.
