# H28 — Conditional metric-model calibration on owner-reported score anchors, and emission design

**Pre-registered 2026-10-02 (UTC) before any fit was run.** Nothing in this document was written after
looking at a fitted value. `scripts/run_h28.py` implements exactly this plan and writes
`evidence/h28_calibration/`; deviations, if any, are recorded in §11 rather than silently folded in.

Owner-brief items this answers: *"explain why/how `h25-1-dotted-h19-5-d1-5` scored 0.2477 and whether a
higher score can be generated"*; *"design a new, unique strategy aiming above the 0.3195 leaderboard best"*;
*"replace one-factor-at-a-time testing with a designed experiment"*; *"do not spend a weekly submission slot
on an idea that has not beaten the current holdout best"*.

---

## 1. Why this experiment, and why now

Every number this group has ever shipped is a point on one curve: *emitted pixel mass* → *reported DTI*.
The group has 30 such points, spread over mass 44 k–514 k and DTI 0.0020–0.2477, and the rasters behind 25
of them are public in the owner's own mirrors with a hash-linked score. Nobody has ever fitted the physics of
the metric to that set. Instead, emission geometry has been a hard-coded constant inherited from one lucky
file (`BUDGET = 0.0245`, `DOT_MIN_DIST = 1.5`, and `min_dist = 2.4` in the H27 runner) and every experiment
since has been a *feature* experiment on top of it.

The published metric makes emission geometry the dominant term, not a detail (§3). This experiment therefore
does three things in order:

1. **Calibrate** the unknowns of the live problem — how many truth pixels are scored (`N`) and where they sit
   (`π`, the truth intensity) — from the group's own scored artefacts.
2. **Invert** the metric: derive the emission that maximises predicted DTI under the calibrated `(N, π)`.
3. **Validate** the design rule on the spatially-blocked hide-and-recover holdout, with the gate the owner
   requires before any weekly slot is touched.

## 2. Evidence classes (kept separate, per `AGENTS.md`)

| class | what it is here |
| --- | --- |
| OFFICIAL | the DTI definition (α=0.2, β=0.8, R=3 px triangular kernel) and the masking clarification, both transcribed and unit-tested in `src/gems25/metric.py` in earlier sessions |
| OWNER-reported | every DTI value in `registry/artifact_ledger.json`. **Unverified.** No DrivenData page was fetched or monitored in this session; `drivendata.org` is not reachable from the sandbox and `AGENTS.md` rule 3 forbids automating it |
| COMPUTED | SHA-256 of each fetched raster; all pixel geometry; every fitted parameter, prediction and residual in `evidence/h28_calibration/` |
| INFERENCE | "the truth intensity is enriched near known traces", "the optimal spacing is 6 px", the conditional DTI of a candidate. Each is stated with the assumptions it needs |

The whole calibration is **conditional on the owner-reported scores being true and belonging to the files
their hashes identify**. A hash match proves the mirror is unchanged and ties a file to a row of the owner's
own ledger; it cannot prove the organiser scored those bytes. This is stated in every output artefact.

## 3. The algebra (derived, then unit-tested against the published metric)

Write `p` for a submission, `G` for the hidden truth, `k(d)=max(1−d/3,0)`, and `π` for the truth intensity
normalised to 1 over the scored domain, with `N = |G|`. Model `G` as a draw of intensity `N·π`
(the metric pools all subset pixels into one index, so only the intensity matters, not the chunking).

```
TP = Σ_g max_x p(x) k(d(x,g))          →  E[TP] = N ⟨π, m_p⟩,   m_p(x) = max_o p(x+o) k(o)      (exact)
FP = Σ_x p(x) (1 − max_g k(d(x,g)))    →  E[FP] = Σ_x p(x) Ψ(ν_x),  ν_x = N (π * 1[d<3])(x)      (Poisson-exact
                                                                                    under locally flat π)
DTI = TP / (0.2 (TP + FP) + 0.8 N)
```

`E[TP]` is exact by linearity over truth pixels. `E[FP]` uses the exact Poisson law for a maximum,
`E[max_g k] = ∫₀¹ (1 − e^{−Λ(t)}) dt` with `Λ(t) = N·(π mass within 3(1−t))`; `Ψ(ν) = ∫₀¹ e^{−ν V(3(1−t))/V(3)} dt`
is a fixed one-dimensional function (`src/gems25/livecal.py`), whose first-order term is exactly the familiar
`FP ≈ M − N⟨π, u_p⟩` because `∫₀¹V(3(1−t))dt = Σ_o k(o) = 9.3803 = KERNEL_VOLUME`. `tests/test_livecal.py`
checks `E[TP]` and `E[FP]` against Monte-Carlo runs of `metric.dti_binary` (agreement < 0.01 DTI while
ν < 1, < 0.06 at ν ≈ 12).

Two consequences drive the design:

* **Redundancy theorem.** With `U = ⟨π, u_p⟩`, `T = ⟨π, m_p⟩` and `R = U − T ≥ 0`,
  `DTI = N(U−R) / (0.2M + 0.8N − 0.2NR)`, and `∂DTI/∂R ∝ (0.2NU − D) < 0` because `DTI ≤ 1 < 5`.
  **Overlapping kernels always lose score.** Two emitted pixels' kernels overlap iff their distance is
  `< 2R = 6 px`, so a redundancy-free emission needs **6 px (600 m) spacing** — not the 1.5 px (150 m) the
  group's best file uses, and not the 2.4 px used by the H27 runner.
* **Optimal design + marginal rule.** For a redundancy-free binary emission the DTI collapses to
  `DTI(P) = N Σ_{p∈P} u(p) / (0.2|P| + 0.8N)` with `u = π * k`. It is maximised by taking the highest-`u`
  pixels under a 6 px exclusion, and the budget stops where `u_(M) ≤ 0.2·DTI/N`.

## 4. Data

`registry/artifact_mirrors.json` (locations, read from GitHub tree listings) +
`evidence/provenance/gemsdoe27_live_scores_snapshot.json` (the owner's hash↔score ledger) →
`scripts/restore_artifacts.py` → `data/artifacts/`, `registry/artifact_ledger.json`.

**Pre-registered inclusion rule.** An artefact enters the fit **iff** its computed SHA-256 equals the
SHA-256 of a row in the owner's ledger that carries a numeric score. That yields 25 rows (0.0020 … 0.2477).
Everything else is recorded with `fit=false` and a reason:

* `d2-8` — no reported score anywhere (it is this repo's own unscored alternate).
* `hedge-v2` — score is brief-only (no ledger row). Kept as a **validation**: it is provably `ens12`
  off-catalogue plus all 60 988 catalogue pixels, so after the metric's masking it must produce *identical*
  statistics to `ens12`, and the owner reports the *same* 0.1563. That is a direct empirical test of the
  masking rule this repo implements.
* `h18-4-geologic-map-faults-gap` (0.0360), `h20-1` (0.1890), `h23-a-6pct` (0.1002) — brief-only scores with
  no ledger row; the file↔score link is unverified, so they are reported as diagnostics, not fitted.

No artefact is dropped for being an outlier, and no artefact is added after seeing residuals.

## 5. Truth-intensity model family (all of it a function of public information only)

Covariate: `d_cat`, the Euclidean distance (in 100 m pixels) from each scored pixel to the nearest **known**
USGS/INGENIOUS catalogue pixel — the layer the organisers publish and mask. Known pixels themselves carry
**zero** truth mass (they are masked out of scoring; staff thread 11516). Bins: 1 px wide to 20 px, then
21–30, 31–50, 51+.

| model | `w(d)` (unnormalised intensity) | free parameters |
| --- | --- | --- |
| `uniform` | 1 | `N` |
| `exp_halo` | `1 + A e^{−d/ρ}` | `N, A, ρ` |
| `step_halo` | `1 + A·1[d ≤ r]` | `N, A, r` |
| `pure_exp` | `(1+A) e^{−d/ρ}` | `N, A, ρ` |
| `two_scale` | `1 + A₁e^{−d/ρ₁} + A₂e^{−d/ρ₂}` | `N, A₁, ρ₁, A₂, ρ₂` |

Rationale for the covariate: staff say new truth may lie within 300 m of known traces ("corrections or
modifications"), which is a statement about `d_cat` and nothing else. Anything the group's own detectors
compute is deliberately **not** in the basis: putting a detector output into `π` would make the fit
self-confirming, because the artefacts are built from those same detectors.

**Fitting.** Ordinary least squares on DTI (not on log DTI, not weighted), all 25 rows equally, Nelder-Mead
from a pre-registered multi-start grid (`N ∈ {8k, 12.5k, 20k, 40k}` × `A ∈ {0.5, 3, 20}` ×
`ρ ∈ {1, 3, 10}`), bounds `N ∈ [2 000, 120 000]`, `A ∈ [0, 400]`, `ρ ∈ [0.05, 60]`.

**Model selection (pre-registered).** Choose the model with the lowest leave-one-artefact-out RMSE. Adopt a
richer model over a nested simpler one only if LOO RMSE improves by ≥ 20 %. Report all five.

## 6. Acceptance criteria for the calibration (checked before any design is built)

| # | criterion | threshold | if it fails |
| --- | --- | --- | --- |
| C1 | LOO RMSE of the selected model | ≤ 0.020 | report the calibration as misspecified; **do not** design a submission from it |
| C2 | Blind-lattice anchor (`lattice-s5`, information-free geometry) | predicted within ±0.005 of 0.0904 | the algebra or `N` is wrong; stop |
| C3 | Masking validation (`hedge-v2` vs `ens12`) | identical statistics to 6 decimals | the metric transcription is wrong; stop |
| C4 | worst absolute residual over the 25 fitted rows | ≤ 0.05 | report per-artefact and flag the offending rows as irregularities |
| C5 | Monte-Carlo check of the analytic prediction at the fitted `(N, π̂)` for 3 artefacts spanning the mass range | \|analytic − MC\| ≤ 0.01 | the Poisson/flat-π approximation is not adequate; report and stop before designing |

## 7. Design rule (inverse problem)

Given the selected `(N̂, π̂)`:

1. `u = π̂ * k` at full resolution; eligible = inside footprint ∧ not a known pixel.
2. Greedy: take eligible pixels in decreasing `u`, breaking ties by flat index, rejecting any pixel within
   6.0 px of one already taken (maximal 6-px packing ⇒ redundancy-free).
3. Budget: the pre-registered marginal rule — the largest `M` on the greedy curve with
   `u_(M) > 0.2·DTI(M)/N̂`, i.e. `argmax_M DTI(M)`. No tuning on any reported score.
4. Re-verify the chosen design with the full analytic prediction *and* a Monte-Carlo truth draw; report both.

Outputs: the design mask, its predicted DTI with a bootstrap interval, and the same numbers for the group's
best file (`d1-5`) and this repo's shipped alternate (`d2-8`) under the identical calibrated model, so the
comparison is apples-to-apples.

## 8. Holdout validation (the owner's gate) — a designed factorial, not OFAT

The score-anchor calibration cannot be validated against the competition's hidden labels here. The hide-and-recover harness
(`src/gems25/holdout.py`, four spatial folds × draws 2 and 3, pseudo-new labels sampled from 20 % of catalogue components)
provides a **catalogue-gap proxy** for comparing the registered design rule; it is not real hidden-fault truth. Emission factors are crossed as a **3 × 2 full factorial** (six arms, all evaluated on the *same*
fitted surface per cell, so the model fit is shared and the comparison is paired):

* **V — value field used to rank and place dots** (3 levels)
  * `V0` baseline: the current pipeline's emission — ridge-NMS score → top-2.45 % of the eroded domain →
    `dot_thin(min_dist=1.5)`;
  * `V1` habitat: `u = π̂_cat * k`, where `π̂_cat` is built from the fold's **visible** catalogue with the
    selected model shape parameters (`A, ρ`) — no held-out catalogue labels enter the feature construction;
  * `V2` habitat × detector: `u = (π̂_cat · ŝ) * k` with `ŝ` the out-of-fold HGB score, min-max normalised.
* **S — spacing / exclusion** (2 levels): `1.5` px (status quo) and `6.0` px (kernel-disjoint, §3).
* Budget for every arm: the marginal rule of §7 evaluated with `N̂` scaled by cell area (a *density* rule, so
  it transfers between the full footprint and a crop). `V0` keeps its inherited 2.45 % budget, since changing
  two things at once would confound the comparison.

Cells: folds {NW, NE, SW, SE} × draws {2, 3} = 8, the same cells as the H27 screen, so the comparator is
directly reusable. Gate (`src/gems25/design.py::h27_promotion_gate`, unchanged):

* mean DTI over the 8 cells **> 0.152003389** (the historical holdout best),
* mean gain over the paired `V0×S1.5` baseline **> 0.001**,
* ≥ 6 of 8 cells positive, worst cell ≥ −0.01,
* catalogue-hug delta ≤ 0.10 (no arm may win by hugging known faults in a proxy whose truth *is* known faults).

**Known bias, declared in advance:** the proxy hides whole catalogue components, so its truth is far more
"on-catalogue" than the live truth (which excludes every known pixel). The harness therefore *under*-rewards
a habitat design relative to live scoring if live truth really is enriched near known traces, and *over*-rewards
it if live truth is not. This asymmetry is why the gate result is reported as a gate, not as a live prediction,
and why the live-calibrated prediction and the holdout result are published side by side whatever they say.

## 9. Decisions this pre-registration commits to

* If C1–C5 pass and the design's predicted DTI > 0.2477, the design becomes the repo's **primary downloadable
  candidate**, packaged with a content-addressed name, a ≤120-char note and a machine-readable receipt, and
  labelled *conditional prediction, unscored*.
* A weekly submission slot is claimed **only** if the holdout gate of §8 also passes for the shipped arm.
  Otherwise the file stays "format-validated, not slot-approved" exactly as `d2-8` does today.
* No arm is promoted post hoc. If the winning arm is not the pre-registered primary design, we report that
  and ship nothing new.
* If the calibration fails C1 or C2, the deliverable of this session is the *negative* result plus the algebra,
  and the shipped download stays `d2-8`.

## 10. What would falsify the interesting claims

* **Redundancy is a first-order loss** — falsified if, at matched mass, artefacts with smaller mean
  nearest-neighbour spacing do *not* score higher (measured on the 25 rows, §11 of the output JSON).
* **Truth is enriched near known traces** — falsified if `Â ≤ 1` or if `exp_halo` does not beat `uniform` on
  LOO RMSE by ≥ 20 %.
* **6 px is the right spacing** — falsified if the S main effect on the holdout is ≤ 0.
* **N ≈ 12 k** — falsified if the fitted `N̂` lies outside 8 k–20 k with a bootstrap CI that excludes the
  lattice-only estimate 12 503.

## 11. Deviations log

### D1 — 2026-10-02, after the §5 habitat fit failed C1–C4, before any anchor number was computed

The §5 fit ran as pre-registered. Result: `uniform` LOO RMSE 0.0809, `step_halo` 0.0705, `exp_halo` 0.0812,
`pure_exp` 0.0751, `two_scale` 0.0806; selected model `uniform`; **C1 FAIL, C2 FAIL (blind lattice predicted
0.2057 vs reported 0.0904), C4 FAIL (worst residual −0.1787 on `d1-5`)**. Per §9 that means no submission may
be designed from the §5 model. The failure is itself the finding recorded in §12.

The reason is identifiable without any further data: the 25 rows differ in *detector skill*, which is a
per-artefact property of how each surface happens to lie on the one realised truth set. A habitat model in
`d_cat` has no term for it, so its residuals are skill, not noise. Only artefacts whose skill is **known by
construction** can identify `(N, π)`:

* the blind lattice — information-free by construction, so it carries no skill;
* a *family* of rasters derived from one parent surface by a deterministic transformation — skill is held
  fixed inside the family, so score differences inside a family are pure emission geometry.

The following estimator was written down and its acceptance thresholds fixed **before it was run**. It replaces
§5 as the calibration of record; §5 stays in the outputs as the misspecification evidence.

### 5b. Anchor estimator (pre-registered amendment D1)

For one artefact with reported score `s`, emitted mass `M` (after masking known pixels) and a candidate truth
intensity `π`, the algebra of §3 with the *linear* FP term inverts in closed form for `N`:

```
N(s, M, T, U) = 0.2 s M / [ T (1 − 0.2 s) − 0.8 s + 0.2 s U ],   T = <pi, m_p>,  U = <pi, u_p>
```

A negative denominator means **no** `N` can produce that score under that `π` — a falsification, not a fit.

Anchor set and candidate `π` (both fixed in advance):

* `π_uniform` over the scored domain, applied to `lattice-s5` → the primary `N` estimate. Because the lattice's
  kernel-max field is periodic with period 5 px, `T` is nearly independent of `π`'s shape, so this estimate is
  robust; the run reports it under seven `π` shapes to show that.
* `π_λ ∝ exp(−d_parent/λ)` restricted to the scored domain, where `d_parent` is the distance to the **H19-5**
  ridge surface (the parent of the group's best file) and `λ ∈ {6, 4, 3, 2, 1.5, 1, 0.7}` px, applied to the
  family anchors `h19-5` (0.1922), `h19-4` (0.1894), `h16-1` (0.1855), `d1-5` (0.2477) and to `lattice-s5`.

**Selection rule (fixed in advance).** Choose `λ̂` minimising the maximum relative deviation of the five implied
`N` values from their median; then `N̂` = that median. Report the whole scan, not just the selected row.

**Acceptance criteria.**

| # | criterion | threshold | if it fails |
| --- | --- | --- | --- |
| A1 | `π_uniform` is falsified for at least one group surface (no finite `N` reproduces its score) | required — this is the claim "the truth is not uniform" | if a finite `N` exists, drop the claim |
| A2 | a single `(N̂, λ̂)` reproduces all five anchors | max relative spread of implied `N` ≤ 20 % | report the calibration as not identified; do not design from it |
| A3 | `N̂` agrees with the lattice-only estimate and with the repo's earlier independent estimate 12 503 | within ±25 % of both | flag as an irregularity |
| A4 | `N̂` bootstrap-free sanity: `0.8 N̂` ≤ implied truth mass ≤ `1.2 N̂` for every anchor | required | stop |

### 6b. What the anchor model is allowed to be used for

`π_λ̂` is *not* an independent habitat model: it is a statement that the realised truth lies within roughly
`λ̂` pixels of the H19-5 ridge surface. It may therefore be used to (i) compare emissions **whose support lies
inside that band** — the group's own surfaces and any rearrangement of them — and (ii) size the redundancy loss
of each artefact. It may **not** be used to claim a score for an emission that leaves the band, because it has
no mass there by construction. Any candidate that explores away from H19-5 must be justified by the holdout
(§8) alone, and that is stated on the download page.

### 7b. Selection-rule experiment on the live surface (pre-registered amendment D1)

Parent = `h19-5` (the source of the 0.2477 file). For budgets
`M ∈ {15 000, 20 000, 26 000, 32 000, 44 000, 60 000}` and for each of these selection rules, compute the
*exact* predicted DTI under `(N̂, π_λ̂)` — `T = <π̂, m_P>` from a distance transform and
`FP = Σ_p Ψ(ν_p)` from the saturating Poisson term, no heuristics:

* `R0` `dot_thin(parent, d)` with `d` chosen to hit `M` — the status quo (this is exactly how 0.2477 was made);
* `R1` greedy by `u = π̂ * k` with 6.0 px exclusion (kernel-disjoint, §3), ties broken by a deterministic hash
  jitter so the dots spread along the network instead of filling raster order;
* `R2` `R1` restricted to the parent's pixels (a pure re-selection, no new support);
* `R3` `R1` with 3.0 px exclusion — tests how much of the gain is disjointness and how much is ranking;
* `R4` budget sweep of `R0` (the repo's existing emission curve) for continuity.

**Decision rule (fixed in advance).** The shipped candidate is the `(rule, M)` with the highest predicted DTI
*only if* its prediction exceeds `d2-8`'s 0.2553 conditional prediction **and** the winner is stable across the
sensitivity grid `λ ∈ {λ̂/1.5, λ̂, 1.5λ̂} × N ∈ {0.85N̂, N̂, 1.15N̂}` (i.e. it is the argmax in at least 7 of the
9 cells). Otherwise nothing new is shipped and `d2-8` remains the download.

### 8b. Redundancy theorem — empirical test on the 25 fitted rows

Independent of any `π`: at matched emitted mass, artefacts with a larger share of emitted pixels whose
nearest emitted neighbour is closer than 6 px must score lower. The run reports, for every artefact, its mass,
median nearest-neighbour spacing, the share of pixels with a neighbour inside 6 px, and its reported score, and
the Spearman correlation of that share with the score **within mass strata** (±12 500 px). This uses only
COMPUTED geometry and OWNER-reported scores.

### D2 — 2026-10-02, after the §5b anchor scan and the §7b design sweep, before the holdout run

Two changes to §8, both made before any holdout cell was fitted:

1. **Draws.** §8 said draws {2, 3}. The frozen comparator `0.152003389` was produced on draws **{0, 1}**
   (`evidence/addons/emk_extension.json`, variant `sapd2.4`, `kfrac = 0.035`, base `BDE` + the seven add-ons,
   `Cell(..., extras=True)`, `fit_predict(seed=draw)`). Comparing a new arm on different draws against a
   comparator computed on draws 0–1 would not be a paired comparison, so the H28 holdout runs on draws {0, 1}
   and **reproduces the comparator arm bit-for-bit as its first check**. If that reproduction fails, the whole
   holdout run is void.
2. **Spacing levels.** §8 crossed spacing {1.5, 6.0}. The §7b sweep under the selected owner-claim-calibrated
   model puts the status-quo family optimum near `min_dist ≈ 2.8` px, not 6.0; under that model's line-like spatial
   intensity, the 6 px gaps are estimated to cost more credit than the redundancy they save. The 6.0 arm is
   retained as a catalogue-gap proxy test of the redundancy theorem, and the factor is widened to
   {1.5, 2.4, 3.0, 4.0, 6.0} so the response surface has a shape instead of two points.
3. **Budget.** §8 said the marginal rule with `N̂` scaled by cell area. That rule needs a value field in the
   units of `π`, which only the habitat arms have; applying it to some arms and not others would confound the
   budget factor with the value factor. All arms therefore use the comparator's own budget rule
   (`kfrac ∈ {0.0245, 0.035}` of the eroded domain), which is a genuine factor of the design, and the marginal
   rule is reported only for the live design (§7b), where it is well defined.

Design as run: **value field {model score, habitat `π̂_cat * k`, habitat × score} × spacing {1.5, 2.4, 3.0, 4.0,
6.0} × budget {2.45 %, 3.5 %} = 30 arms**, on 4 spatial folds × draws {0, 1} = 8 cells, one shared model fit per
cell, all arms evaluated on the same candidate pool. `λ̂` for the habitat field is taken from §5b unchanged
(1.85 px) and applied to distance to the fold's **visible** catalogue — a transfer assumption, since §5b
calibrated it against distance to the H19-5 ridge surface, not to the catalogue. Gate: `h27_promotion_gate`
on fold means (draws averaged) of the best arm versus the comparator arm, plus the absolute comparator.

### D3 — 2026-10-02, after §7b and its sensitivity grid, before the mixture model was run

Under the selected model, §7b's 6 px kernel-disjoint design beat `d1-5` in **0 of 9** `(λ, N)` sensitivity cells; the best point in the tested status-quo sweep was `min_dist ≈ 2.4` px (modelled DTI 0.25104, corresponding to the file shipped for research). Under this spatial model, estimated credit in the gaps between dots exceeds the estimated redundancy saved; this is not evidence about actual hidden labels.

The single-parent `π̂` of §5b under-predicts two owner-mirrored GEMSDOE10 surfaces by 0.037 and 0.059 DTI relative to their owner-reported claims. These residuals indicate off-band model mismatch; they do not establish that those surfaces contain hidden truth. A two-band mixture was preregistered as a test of this model limitation:

```
pi_b  ∝  exp(-d(P1)/λ̂) + b · exp(-d(P2)/λ̂),   λ̂ = 1.85 px (unchanged from §5b), b ≥ 0
P1 = h19-5;  P2 ∈ {h25-ctx-ridge, r7-nms3-dem10-scarp, lidarscarp-top2pct, pindrop-nodes}
```

Estimator: identical to §5b — for each anchor, invert its reported score for `N`; scan `b`; choose the
`(P2, b)` pair minimising the maximum relative spread of the implied `N` over the nine anchors whose scores are
hash-verified (`lattice-s5`, `h19-5`, `h19-4`, `h16-1`, `d1-5`, `h25-ctx-ridge`, `h28-dotted-ridge`,
`r7-nms3-dem10-scarp`, `lidarscarp-top2pct`); `N̂` = the median of the nine.

**Adoption rule (fixed in advance).** Adopt the mixture only if *both*: (i) its max relative spread is ≤ the
single-parent value 0.0525; and (ii) the mean absolute DTI residual over the nine anchors improves by ≥ 25 %
against the single-parent `π̂` at its own `N̂`. Otherwise the single-parent model stands and nothing new is
designed. If adopted, the candidate designs are `dot_thin(P1 ∪ P2, d)` and greedy-by-`π̂_mix * k` at
`d ∈ {2.4, 2.8, 3.2}`, scored with the same exact algebra, and a new file is packaged **only** if it beats
0.25104 in at least 7 of the 9 cells of the `(λ, N)` sensitivity grid.

## 12. Findings — written only from `evidence/h28_calibration/` and `evidence/h28_holdout/`

All DTI values labelled *reported* are user/owner-reported claims matched to bytes by SHA-256, not receipts.
All values labelled *predicted* come from the calibrated model of §3/§5b and are conditional on it.

### 12.1 Conditional forward-model calibration on owner-reported score claims

Conditional on the hash-linked owner-reported anchors and the selected model, the fit is `π̂ ∝ exp(−d(H19-5)/1.85 px)` on the scored domain (known pixels excluded), with model-implied `N̂ = 12 691` pixels (`evidence/h28_calibration/anchors.json`). This is not a verified hidden-label count or competition-score model.

| check | result |
| --- | --- |
| A1 uniform `π` candidate | **PASS conditionally** — under the published metric algebra and the supplied owner-reported scores, no truth count under uniform `π` reproduces four anchors. This makes uniform `π` inconsistent with those claims; it does not establish the actual hidden-label distribution. |
| A2 one `(N, λ)` for five anchors | **PASS conditionally** — model-implied `N` = 12 498 / 12 472 / 12 893 / 13 358 / 12 691 for `lattice-s5` / `h19-5` / `h19-4` / `h16-1` / `d1-5`; max relative spread **5.3 %** |
| A3 agreement with independent estimates | **PASS** — lattice-only 12 348 (uniform `π`), 12 498 (at `π̂`); this repo's earlier independent estimate 12 503 |
| A4 sanity | **PASS** — every implied `N`/`N̂` ∈ [0.98, 1.06] |
| C3 masking | **PASS** — `hedge-v2` and `ens12` are statistically identical after the metric masks known pixels (mass 166 519 both; max \|ΔTA\| < 1e-3), and both are reported at 0.1563 |
| C5 Monte Carlo | **PASS** — analytic vs 6 exact-metric draws from `π̂`: lattice 0.09140/0.09144, `d1-5` 0.24372/0.24532, `h19-5` 0.19035/0.19232, `h28-dotted-ridge` 0.12509/0.12568; worst error 0.0020 |

Under the selected model, predicted values against owner-reported claims are: `lattice-s5` 0.0914 vs 0.0904, `h19-5` 0.1904 vs 0.1922, and `d1-5` 0.2437 vs 0.2477; `d2-8` is predicted at **0.2510** (unscored). Off-family predictions are lower than the owner-reported claims (`h25-ctx-ridge` 0.0907 vs 0.1280, `h28-dotted-ridge` 0.1251 vs 0.1839); these residuals delimit model scope, not verified hidden truth. Mean absolute residual over the nine hash-linked owner-reported anchors: **0.0172**.

### 12.2 What the 0.2477-labelled raster changes locally

| raster | emitted px | median NN | redundancy `R/U` | credit/px | reported | predicted |
| --- | --- | --- | --- | --- | --- | --- |
| `h19-5` (solid ridge) | 121 131 | 1.00 | 0.62 | 0.0520 | 0.1922 | 0.1904 |
| `d1-5` = `dot_thin(h19-5, 1.5)` | 60 069 | 2.24 | 0.32 | 0.0893 | 0.2477 | 0.2437 |
| `d2-8` = `dot_thin(h19-5, 2.4)` | 44 090 | 3.00 | 0.07 | 0.1084 | unscored | 0.2510 |

Under the selected model, dotting the solid surface removes 50 % of its pixels but only 15 % of its captured credit, reducing redundant (overlapping-kernel) mass from 62 % to 32 %; the modelled DTI changes by +0.053. The 0.2477-labelled raster is a geometry-only transform of the 0.1922-labelled surface (pixel identity verified locally), but the score-to-file association and the cause of any competition-score difference remain unverified.

### 12.3 Modelled ceiling within the tested H19-5 dotting sweep

Under the selected model, the `dot_thin(h19-5, d)` sweep over `d ∈ [1.8, 4.0]` peaks at **d = 2.4 px, M = 44 090,
modelled DTI 0.25104** — the `d2-8` research download. The value-ranked alternatives are lower under this model:
greedy-by-`π̂*k` at 3 px exclusion peaks at 0.2462 (M = 44 000), and at 6 px exclusion (kernel-disjoint, zero
redundancy) peaks at 0.1933 (M = 26 000). In **0 of the 9** cells of the `(λ, N)` sensitivity grid does the
6 px design beat `d1-5`. This is a ceiling only for the tested H19-5 emission family and selected model, not a
validated live score or global ceiling. The redundancy theorem of §3 still holds; under this selected spatial
model, the estimated credit in the gaps between disjoint dots exceeds the estimated redundancy saved.

### 12.4 The catalogue-gap holdout proxy

`evidence/h28_holdout/` — 30 arms (value field × spacing × budget), four spatial folds × draws {0, 1}, one shared
model fit per cell. The held-out labels are hidden catalogue components, not independently verified new-fault truth:

* spacing main effects: 1.5→2.4 **+0.0074**, 2.4→3.0 −0.0003, 3.0→4.0 −0.0112, 4.0→6.0 −0.0350. Within the tested proxy grid, 2.4–3.0 px is near-optimal, consistent with the selected metric model; 6 px costs 0.045 DTI.
* value field: `habitat − score` **+0.0003**, `both − score` **+0.0012** (best arm `both`/3.0/3.5 %:
  +0.000699 paired, 4/8 cells positive, p = 0.248). Neither reaches the +0.001 paired threshold.
* budget: 3.5 % beats 2.45 % by +0.0069…+0.0087 for every value field.
* **The registered gate did not pass.** The best arm's paired gain was +0.000699 ≤ +0.001. The historical absolute comparator (0.152003389) also failed reproduction (IR-25-COMPARATOR-DRIFT), so it is not a valid cross-run baseline. No arm is slot-eligible; nothing new was packaged.

### 12.5 Reproduction of the frozen comparator FAILED — and that is a finding

The comparator arm (`score`/2.4/3.5 %, base `BDE` + the seven add-ons, draws 0–1) recomputes to
**0.149667509** in this environment against the frozen **0.152003389** (fold 0 identical to 9 decimals; folds
1–3 differ by +0.0023, −0.0042, −0.0074). Re-running one cell in isolation reproduces this session's value
bit-for-bit, so this session's pipeline is deterministic; the drift is environmental (`data/work` is a
gitignored derived cache and no library-independent pin existed). Recorded as **IR-25-COMPARATOR-DRIFT** with
`evidence/work_cache_hashes.json` (SHA-256 of every derived cache plus the exact library versions) so the next
session can detect it. Consequence for policy: **absolute comparators do not transfer between environments;
only same-run paired contrasts do.** Every conclusion above that matters (spacing optimum, value-field
neutrality, budget) is a same-run paired contrast.

### 12.6 What the fitted model implies about off-band owner-reported claims

* The selected single-band `π̂` basis does not fit several owner-reported scores (§5, LOO RMSE 0.070–0.081,
  C1/C2/C4 fail). This is evidence of model misspecification relative to those claims; residuals may reflect
  score-link problems, artifact-specific detector differences, or a different hidden-label distribution.
  **It does not locate actual hidden faults.** "Hug the catalogue halo" is not supported by this fitted model.
* Two-band mixtures (D3) are not identified under these anchors: the best (`h25-ctx-ridge`, b = 1.0) reaches a
  nine-anchor spread of 0.514 (threshold 0.053) and makes the mean absolute residual worse (0.0335 vs 0.0172).
  Not adopted; no design was built from it.
* Model-implied `N` per off-band surface is a misspecification diagnostic under the selected `π̂`, not a direct
  measure of hidden truth: `h28-dotted-ridge` 28 989, `lidarscarp-top2pct` 22 893, `h25-ctx-ridge` 20 072
  versus 12 472–13 358 for the H19-5 family. These owner-mirrored surfaces are H29 exploration priorities
  (§13), not verified locations or counts of hidden labels.
* Ledger-wide, the share of emitted pixels with a neighbour inside 6 px correlates with the reported score at
  Spearman **−0.670 (p = 6.9e-5, n = 29)** — consistent with the redundancy theorem — but inside mass strata
  the correlation is not significant (n = 7: −0.32, p = 0.48; n = 6: +0.76, p = 0.077), because skill and mass
  are confounded across the ledger. The theorem is proved algebraically; the ledger is only consistent with it.

### 12.7 Conditional model arithmetic against the unverified 0.3195 claim

The following is sensitivity arithmetic, not a verified comparison: 0.2477, 0.2941, and 0.3195 are owner/user-reported claims, not independently authenticated scores. Under the selected model's estimated `φ = 0.900` false-positive mass per emitted pixel, the modelled credit density `TP/M` required to produce each target is:

| target DTI | M = 20 000 | M = 30 000 | M = 44 090 | M = 60 069 |
| --- | --- | --- | --- | --- |
| 0.2477 (group best) | 0.1792 | 0.1351 | 0.1069 | 0.0910 |
| 0.2941 (reported #5) | 0.2149 | 0.1620 | 0.1282 | 0.1091 |
| **0.3195 (reported #1)** | 0.2347 | 0.1770 | **0.1400** | 0.1191 |

The best point in the tested H19-5 dotting sweep has modelled credit density 0.1084 at M = 44 090 (predicted DTI 0.25104 under the selected `π̂`). Conditional on that model and on the unverified 0.3195 target, matching it at the same budget would require **1.29×** that estimated credit density; the analogous ratio for 0.2941 is 1.18×. These calculations do not establish a live-score gap, prove that every emission alternative is exhausted, or validate the off-band model. The H28 proxy promotion gate failed (§12.4).

## 13. Ranked next hypotheses (H29) — from this evidence, not from taste

Each entry names the layer(s), the physical signature, why it should catch a fault **missing** from the
USGS/INGENIOUS catalogue rather than one already in it, how it differs from anything already implemented, and
its obtainability. ΔDTI values are **planning brackets, not estimates**; every one requires a pre-registration
and a same-run paired holdout gate before a weekly slot (see §12.5 — the frozen absolute comparator does not
transfer between environments).

### H29-1 · Multi-band parent: test surfaces with model-implied N̂ above the H19-5 family — *rank 1*

* **Layers**: the three hash-verified owner mirrors `h19-5` (multi-scale Hessian ridge over the GeoDAWN DEM/
  geophysics bands), `h25-ctx-ridge`/`h28-dotted-ridge` (GEMSDOE10 context ridge) and `lidarscarp-top2pct`
  (7GEMSDOE LiDAR scarp index, top 2 %); all are built from provided bands, none has a pixel on a known fault.
* **Signature**: 1-px-wide ridge crests and scarp-continuity maxima — i.e. the geomorphic expression of a
  displacement surface, at three different resolutions and from three different band families.
* **Why it could find *missing* faults**: §12.6 reports model-implied counts of 20 072, 22 893, and 28 989
  against 12 472–13 358 for the H19-5 family. These are conditional diagnostics from unverified owner-reported
  scores, not measured hidden truth or proof of spatial complementarity. A union could add candidate coverage
  outside the visible catalogue; the held-out catalogue-gap proxy must test whether that helps.
* **Difference from what exists**: the group built ensembles by *probability union* at arbitrary budgets
  (`ens12` 0.1563, `dual-family-union` 0.1560, `F-ensemble-2pct` 0.0187). Nobody has built a **credit-ranked
  union emitted at the DTI-optimal spacing (2.4–3.0 px) and marginal-rule budget**, and nobody has selected the
  components by measured credit per emitted pixel (§12.6's table).
* **Planning ΔDTI**: +0.00 to +0.03 on the proxy (very uncertain; not an estimate or live-score forecast).
  **Cost: low** — all owner-mirror bytes are already on disk and hash-verified. Needs either a ≥3-band `π̂`
  that passes a D3-style adoption rule, or holdout-only validation with competition performance explicitly unknown.

### H29-2 · Skill-weighted consensus pruning of a fixed parent — *rank 2*

* **Layers**: the 25 hash-verified competition rasters themselves — a free panel of structurally independent
  detectors (ridge, scarp, node-based, magnetics/gravity conjunction, ensembles, a blind lattice as the floor).
* **Signature**: agreement between detectors that use different physics, weighted by each detector's measured
  credit per emitted pixel (§12.6: 0.0893 for `d1-5` down to 0.0043 for `placeholder`, floor 0.0228 for the
  information-free lattice).
* **Why it finds *missing* faults**: a pixel that several independent detectors flag, and that is not a catalogue
  pixel, is more likely to be a genuinely unmapped fault than one detector's ridge crest. The repo's own
  break-even analysis (consensus pruning pays only if dropped dots carry < 52 % of average credit) can now be
  evaluated with measured weights instead of assumed ones.
* **Difference from what exists**: `ens12`/`dual-family-union` are *unweighted* unions; the holdout's `both` arm
  (habitat × score) was the only ranking test and gained +0.0012 (p = 0.25). A **skill-weighted vote used to
  prune a fixed parent at fixed spacing** has never been built here.
* **ΔDTI**: +0.00 to +0.02. **Cost: low–medium** — no new data, ~1 h of compute.

### H29-3 · Directed tip continuation × multi-scale scarp, applied to the union parent — *rank 3*

* **Layers**: `labels.tif` ≡ `existing_faults.tif` (visible trace endpoints), DEM curvature/scarp bands
  (`L_step_max`, `B_crest`, `B_trough`), LiDAR scarp index.
* **Signature**: along-strike extrapolation of a mapped trace past its digitised end, gated by crest/trough
  support — the "wing-crack"/step-scarp geometry of a propagating rupture.
* **Why it finds *missing* faults**: mapped traces stop where the mapper's data or generation stopped (alluvial
  cover, image edge, older mapping vintage). An abrupt trace termination with continuing topographic expression
  is the canonical catalogue gap, and it is off-catalogue by construction.
* **Difference from what exists**: implemented as the H27-1 features (`H27_tip`, `H27_scarp`, `H27_tip_x_scarp`)
  and measured at **+0.008120 on the proxy, 4/4 folds** — the only positive factor in that screen. It has never
  been combined with a multi-band parent, and it failed only the environment-specific absolute comparator.
* **ΔDTI**: +0.00 to +0.010 on the proxy; live unknown. **Cost: medium** — `scripts/run_h27.py` exists; re-run
  screen and confirmation with a same-run comparator.

### H29-4 · USGS Great Basin heat-flow `residual` × structural support — *rank 4, blocked on bytes*

* **Layers**: the point coverage in DOI [10.5066/P9BZPVUC](https://doi.org/10.5066/P9BZPVUC) (DeAngelo, Burns,
  Gentry, Batir, Lindsey, Mordensky 2022, INGENIOUS DE-EE0009254), whose `residual` attribute is a well's
  departure from the estimated **conductive background** heat flow (definition read from the ScienceBase item
  metadata this session); crossed with the DEM/scarp support and distance-to-known-fault.
* **Signature**: positive convective residuals — groundwater upflow along a permeable damage zone — coincident
  with a structural or scarp expression.
* **Why it finds *missing* faults**: convective anomalies mark *permeable* structures, which is what a
  geothermal vent needs, and they are measured at wells, not at traces; a permeable structure in covered basin
  fill can be invisible to both the catalogue and the geomorphic bands.
* **Difference from what exists**: nothing in this repo uses heat flow. Family D (thermal) is radiometric/
  thermal-conductivity from the provided bands and was **inert** in the factorial (+0.0044).
* **Obtainability**: metadata, file names, sizes and MD5s verified this session
  (`heat_flow_maps_and_supporting_data_for_the_Great_Basin_USA.zip` 130 154 244 B, MD5
  `2f7aed23c8801a9541dc48e50eedb131`; FGDC XML 43 972 B, MD5 `945050ba62d120e38c51bf15862aaca0`), but
  `www.sciencebase.gov` is **unreachable from this sandbox**, so the bytes and the licence statement on the item
  page are unverified. **Blocked**; needs a networked runner and a licence/schema/coverage check before any test.
* **ΔDTI**: 0 to +0.010. **Cost: high** (blocked).

### H29-5 · INGENIOUS GDR 1391 geodetics + seismicity — *rank 5, blocked on bytes*

* **Layers**: [GDR submission 1391](https://gdr.openei.org/submissions/1391) (DOI 10.15121/1881483, CC BY 4.0):
  `geodetics_INGENIOUS_regional_data.zip` (51.99 MB) and `seismicity_INGENIOUS_regional_data.zip` (22.98 MB),
  with `wellspringdata.gdb.zip` (19.85 MB) as the permeability cross-check. The repo already holds footprint
  subsets (`gdr_wellspring_in_footprint.csv`, `gdr_qfaults_traces.csv`, `gdr_volcanic_vents_in_footprint.csv`).
* **Signature**: dilatational strain axes and relocated microseismic lineaments that cross or terminate at
  mapped traces; vent/spring clusters aligned off-trace.
* **Why it finds *missing* faults**: strain and microseismicity reveal active structures with no surviving
  geomorphic expression (the failure mode of every band in families A–D), and they are not derived from the
  catalogue, so agreement with a trace is corroboration while disagreement is a candidate gap.
* **Difference from what exists**: family C (strain/seismicity) was **inert** in the factorial (−0.0109) *using
  the provided GeoDAWN bands*; the raw GDR geodetics/seismicity have never been ingested (the `X2_compat`
  add-ons use only the shipped columns).
* **Obtainability**: direct URLs verified under `https://gdr.openei.org/files/1391/`, CC BY 4.0, but
  `gdr.openei.org` is **unreachable from this sandbox**. **Blocked**.
* **ΔDTI**: 0 to +0.005. **Cost: high** (blocked).

### What would change the shipping decision

The existing `d2-8` file remains format-validated, unscored, and not slot-approved. Its 0.25104 value is a conditional model prediction within the tested H19-5 spacing sweep; the H28 catalogue-gap proxy gate failed, and the absolute comparator did not reproduce. These results do not establish a global emission ceiling or prove that only a new parent surface/new physics can help. Any future candidate must be newly preregistered, beat a comparable same-run spatial holdout control, pass its paired/confirmation gates, and pass the exact-file audit; competition performance remains unknown without official score evidence.
