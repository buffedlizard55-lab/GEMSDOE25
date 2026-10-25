# 26 · H38 outcomes: why 0.2778, whether we can beat it, and the first emission-rule win (2026-10-25)

All DTI values are **HOLDOUT-DTI** (`gems25.metric.dti_binary`, α=0.2, β=0.8,
R=3 px) unless labelled **OWNER** (owner-reported claims, not organizer receipts).
**No number in this repo is ORGANIZER-CONFIRMED.** Machine-readable card:
`registry/run_card_h38_2026-10-25.json`. Pre-registration: knowledge/25
(commit `766b590`, before any fit). Budget used: 1 experiment of 3 (screen +
confirmation of one hypothesis, with two secondary/diagnostic arms on the same
surfaces); no other hypothesis was fit.

## 1. Why the GEMSDOE32 B2 file scored highest — re-verified this session

`scripts/verify_b2_chain.py` was re-run on freshly restored, SHA-256-pinned
bytes (COMPUTED): D2.8 ⊆ H19-5 (0 px outside), B1 = D2.8 & (d(catalogue) > 1 px)
(XOR **0**), **B2 = D2.8 & (d(catalogue) > 2 px)** (XOR **0**, 37,654 px),
GEMSDOE36 = B2 + exactly 1,200 px (0 missing). So the OWNER chain
0.1922 → 0.2477 → 0.2600 → 0.2708 → **0.2778** is one detected set with
progressively less redundant / near-catalogue mass. The metric credits each
truth pixel with the **maximum** triangular kernel over nearby dots, so a dot
whose kernel support is already covered adds ≈0 credit but a full unit of FP
charged at α=0.2; a dot pays iff ΔTP/ΔFP > α·D/(1−α·D) = 0.0588 at D=0.2778.
The deleted shells earned ≈0.001–0.005 credit/px (knowledge/24 §1) — the win
was *emission economics on a shared detector*, not new geology. This session's
A2 diagnostic (§3) confirms the other side of the same coin: on a detector that
already hugs little, the B=2 prune is nearly neutral.

## 2. Can we generate a file that beats 0.2778?

**Still not demonstrated — but this session produced the strongest necessary
evidence so far.** Beating 0.2778 by +0.01 needs ≈+4 % weighted credit at fixed
mass; 0.3195 needs ≈+15 %; the brief's conflicting 0.4413 ≈+59 %
(IR-25-LEADERBOARD-CONFLICT). Six sessions of detector feature-columns moved
the proxy by ≤±0.004. The H38 result below — **+0.0050 pooled HOLDOUT-DTI
(+3.3 % relative) from the emission rule alone, at *fewer* emitted dots per
holdout cell and half the catalogue-hug** — is exactly the *kind* of gain the
B2 decomposition says is available (repricing dots the scorer does not pay
for), now obtained by pricing *every* dot instead of two distance shells. It
does **not** imply a live gain of the same size: the proxy-vs-live correlation
in the group's record is weak (Spearman +0.33, n.s.), the plug-in density is
the detector's own score, and the live value of greedy emission on the
*H19-5-family* surface (the B2 lineage) is untested because that surface
exists here only as binary rasters. Any statement "this file beats 0.2778"
would be a projection and is never written as a score.

## 3. The pre-registered experiment (knowledge/25)

One B35 (H35 arm-B) surface per cell; four emissions share it. Fresh draws
20–21 (screen) and 22–23 (confirmation, run because the screen passed).
Gate: paired fold-mean gain > +0.001, ≥3/4 folds, worst ≥ −0.010, canary ≤0.90.

| Stage | A0 sapd control | A1 greedy (primary) | A1−A0 paired (95 % CI), folds | pooled Δ | OC pooled Δ | Gate |
|---|---:|---:|---|---:|---:|---|
| Screen 20–21 | 0.1521 (pooled 0.1515) | 0.1576 (pooled 0.1565) | **+0.0055** (+0.0019…+0.0091), 4/4, worst +0.0031 | +0.0050 | +0.0056 | **PASS** |
| Confirmation 22–23 | 0.1609 (pooled 0.1620) | 0.1649 (pooled 0.1669) | **+0.0040** (−0.0025…+0.0105), 3/4, worst −0.0005 | +0.0050 | +0.0054 | **PASS** |
| Combined 20–23 | — | — | **+0.0048** (+0.0024…+0.0071), 4/4, worst +0.0032 | +0.0050 | +0.0055 | — |

Withheld positives per fold (combined means): [1972, 2333, 3611, 3239];
off-catalogue (>2 px from visible): [1948, 2309, 3518, 3182]. A1 emitted
*fewer* dots per cell than A0 (10,880/11,087 vs 11,586/11,666) with hug-share
0.043/0.044 vs 0.086/0.088: greedy declines to buy near-catalogue mass whose
kernel support is partly masked, the same direction as B2's shell deletion but
decided dot-by-dot. Canaries: base-surface max effective AUC 0.844/0.839,
line-score 0.828/0.833 (cap 0.90) — PASS (A1 adds no input feature).

Secondary/diagnostic arms (both negative results, deliverables):
* **A3 segment matched filter + greedy: FAIL both stages** (screen −0.0004,
  1/4 folds; confirmation −0.0033, 0/4). Line integration of the probability
  surface does not add recoverable structure in this harness; it also *raises*
  hug (0.12 vs 0.09). Do not retry longer segments post hoc.
* **A2 B=2 prune of the incumbent emission: near-neutral** (+0.0003 screen,
  +0.0005 confirmation; off-catalogue +0.0007/+0.0009 pooled). On this detector
  only ~1.5 % of dots sit ≤2 px from the visible catalogue (vs 14.6 % of D2.8's
  mass), so the operation that won on the H19-5 family has almost nothing to
  delete here. The new off-catalogue response (truth >2 px from visible)
  tracks the standard response closely for every arm, because ~98 % of hidden
  catalogue-component pixels are themselves >2 px from *visible* components in
  this hide-and-recover design — the instrument works, but the proxy's
  near-catalogue truth population is too small to price flank behaviour
  precisely (a limitation, recorded, not a licence to extrapolate to the live
  "corrections within 300 m" wording).

## 4. Lane

Surface (pre-placement): worst |Spearman| **0.154** vs every restored registry
raster (cap 0.90) — pass. Final dots vs 28 other-site/scored rasters: worst
3-px overlap **0.683** (gems10 ctx-ridge; cap 0.70), vs GEMSDOE32 B2 **0.316**,
worst |ρ| 0.387 — no other-site flag. Literal lattice overlap 1.000 with halo
coverage 0.9987 (density-aware symmetric 0.189; IR-25-LANE-DENSITY). **True
duplicate vs this repo's own unscored lineage**: 1.000 of candidate dots within
3 px of the H35 sapd file (same surface protocol, same candidate pool; greedy
buys a denser subset of the same ridges), 0.77–0.93 vs the other
H31/H36/H37/XG1/CF-1 files. Under the frozen lane rule the file is therefore
**not lane-clear**. Structurally this is now sharper than knowledge/24 §4:
even a *different decision rule* on the incumbent surface cannot be
lane-distinct from the incumbent's own emission — the ridges are the same.
Distinctness from every *scored* raster is genuine; distinctness from its own
lineage would require discarding the validated surface.

## 5. The unique file and the automated submit decision

`gems25-h38-greedy-credit-k3p5-20261025-18de99d38bb0-zeros.tif`
(54,472 dots; SHA-256 `03b9d4c0…6dae2`; NaN twin + single-TIF zip alongside).
Greedy diagnostics on the full build: 180,858 candidates → 54,472 selected,
plug-in D̂ 0.188, stopped at break-even (last accepted ratio 0.03917).
Independent verification (`scripts/verify_h38_independent.py`, plain rasterio,
receipt `evidence/h38_verify_independent.json`): EPSG:32611, 3730×3292,
transform (100, 0, 243350, 0, −100, 4508550), all 5,167,373 footprint pixels
finite in {0,1}, **strict whole-array [0,1] with zero NaN anywhere** (the form
behind the reported portal error), 0 dots on catalogue pixels, 0 outside the
footprint, twins pixel-identical inside, zip byte-equal, content id and
SHA-256 match the registry, and the shipped dots **re-derive exactly** from
the saved surface. DrivenData note (105 chars, research identifier unless the
owner selector approves): `GEMSDOE25 H38 greedy-credit k3.5% | PASSx2 +0.005; unscored; not slot-approved; no slot | id 18de99d38bb0`.

> **OK to download (local testing): YES · OK to submit / spend a weekly slot:
> NO — DO NOT SUBMIT** (verdict negative on lane only: duplicate vs this
> repo's own unscored H35 lineage + literal lattice rule; holdout and format
> gates both PASS). `slot_approved` remains false.

## 6. What to do next (ranked by P(Win))

1. **Owner selector decision (the decision this session tees up).** H38 is the
   first file blocked *only* by lane policy against its own unscored
   predecessors. If the owner explicitly adopts the supersession reading
   (this file replaces H35/H31-C/etc.; never submit the predecessors) plus the
   density-aware lattice treatment, H38 becomes the slot candidate and its
   organizer receipt would be the first live anchor for greedy emission. The
   agent does not approve this; the literal rule as written says duplicate.
2. **Greedy emission on a lane-distinct surface** (new pre-registration):
   apply `gems25.greedy` to a detector whose dots are not the incumbent's
   ridges — e.g. the SGMC off-catalogue universe (knowledge/25 rank 3,
   canary decisive) or a KDC-style complement pool. Emission and distinctness
   are now separable problems with a tested pricing rule for the first.
3. **Greedy pricing of the B2 lineage itself** needs the continuous H19-5
   parent surface, which is not in any restored mirror (binary rasters only).
   If the owner can supply it, one paired holdout run (greedy vs dot_thin/B2
   on that surface) prices the exact live lineage.
4. **Raw 1 m 3DEP scarp-profile detector** on a networked runner remains the
   largest-headroom lever (knowledge/25 rank 5; free official source
   <https://www.usgs.gov/3d-elevation-program>; egress-blocked here).
5. Do **not** iterate on greedy hyperparameters (N̂ scaling, pool size, τ)
   against these draws; any variant is a new pre-registration on fresh draws.

## 7. Limitations

Proxy truth is withheld catalogue components (not live hidden faults);
proxy↔live Spearman +0.33 n.s. Plug-in density = the detector's own
uncalibrated score with an independence FP approximation (unit-tested against
Monte Carlo and brute force, `tests/test_greedy.py`, but still an
approximation — correlated false lineaments are under-priced). Off-catalogue
distances are computed inside each quadrant crop (domain eroded 12 px, so
cross-boundary visible faults cannot affect scored pixels' 2-px class except
at footprint-edge bbox corners). Four spatial folds ⇒ wide CIs; the
confirmation paired CI includes zero (−0.0025…+0.0105) although its pooled
delta (+0.0050) matches the screen's. Template and labels are owner-mirrored,
not organizer-authenticated (IR-25-PROVENANCE). All competition scores cited
are OWNER claims.
