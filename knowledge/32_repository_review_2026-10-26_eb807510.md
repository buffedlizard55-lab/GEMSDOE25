# Repository review — 2026-10-26 — `arena/eb807510-gemsdoe25`

## Executive decision

**No competition-ready GeoTIFF is approved. Do not submit any file from this checkout.** This review did not train a model, run a new geological experiment, create a raster, estimate a leaderboard score, or use a weekly slot. The current template, labels, and feature cache are absent from local `data/`; pinned public owner-mirror restore scripts exist, but those bytes are not organizer-authenticated. More importantly, the user message's required single geological-method paragraph is not present, so a parallel-run lane cannot be established safely. The explicit lane/stop rule takes precedence over manufacturing a TIFF or choosing a method without assignment.

The request's unique, gate-cleared TIF remains **unfulfilled**. Historical site TIFs and locally format-validated research files are not eligible new submissions merely because their names or bytes differ. No score projection is made; a catalogue-gap HOLDOUT-DTI is not a calibrated leaderboard score.

## Scope and evidence limits

- Reviewed the standing `AGENTS.md`, complete `README.md`, the current project brief and prior checkout/forensics notes, shared DTI/holdout/writer/feed implementations, relevant tests, and the open GitHub pull request.
- Current branch was `arena/eb807510-gemsdoe25` at `606eef45e669a6da061ec24be4a3d870addadb0f`, identical to `origin/main` at review start. No DrivenData page, leaderboard, login, or submission endpoint was accessed. The sites below are linked for manual review, not claimed as freshly fetched.
- The unmerged PR **#47** from `arena/198fa53f-gemsdoe25` is already open and has a passing `pytest` check, but GitHub reports `mergeable = CONFLICTING` / `mergeStateStatus = DIRTY`. It changes the site/readme/feed and includes a wider focus-site audit. This review does not alter that branch or claim its work as merged.
- The repository's source ledger records prior official-source verification dates and caveats. This review does not upgrade those stored statements or owner mirrors into fresh official verification.

## Findings

### Fixed in this review — source-feed DrivenData host-guard bypass

`is_blocked()` in `scripts/check_sources.py` previously compared the parsed hostname literally. I reproduced that it returned `false` for DNS-equivalent spellings such as `https://www.drivendata.org./...` and `https://www.drivendata。org/...`. Since `safe_request()` manually follows redirects, a configured URL or redirect using such a spelling could have bypassed the repository's no-automated-DrivenData policy. The guard now canonicalizes IDNA hostnames, strips terminal DNS dots before and after canonicalization, and fails closed for malformed hostnames. `tests/test_feed_host_safety.py` checks root/subdomains, repeated terminal dots, all three IDNA dot separators, lookalikes, and that a redirect is rejected before the destination is requested. Logged as `IR-26-FEED-DNS-CANONICALIZATION-20261026`.

### Existing project state — competition submission gates

- The existing top-level messaging correctly says **DO NOT SUBMIT** / no weekly slot. The H72-3 file linked in the current summary is research-only; its historical run record says it failed the same-run H35 holdout gate and fails the literal 70%-within-3-px lane rule for dense registry rasters. Its density-aware comparisons do not waive the literal stop.
- The README/site also uses the word “unique” for density-aware or content-distinct comparisons. Read that as a narrow mask/hash description, not a pass of the literal lane rule or permission to upload. PR #47 is already attempting to make this distinction more explicit; it is not merged.
- `src/gems25/submission.py` rejects non-finite or out-of-range predictions inside the pinned template footprint and checks the template grid, but `format_valid` is format-only. It cannot certify performance, novelty, organizer provenance, slot allowance, or acceptance by DrivenData.
- `data/` contained only `.gitkeep` at review time. `scripts/restore_data.py` can restore hash-pinned owner mirrors; this is an available engineering path, not a fresh official-data download and not evidence that current caches match historical experiment environments.

### Historical focus-site result

All scores in this table are the values supplied in the prompt / local owner ledger and must be read as **OWNER-REPORTED**, not ORGANIZER-CONFIRMED. The exact file/mask and duplicate audit is in [`docs/current-review.html`](../docs/current-review.html), [`evidence/focus_audit_2026-10-26.json`](../evidence/focus_audit_2026-10-26.json), and the linked focus-site review. Existing scoring claims do not make the archived files eligible as new submissions.

| Site | Best supplied historical file (short identifier) | Score class | New-file score estimate | New submission eligible? |
|---|---|---|---|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5` | OWNER-REPORTED 0.2477 | Unknown / not calibrated | No |
| GEMSDOE25 | `dotted-h19-5-d2-8` | OWNER-REPORTED 0.2600 | Unknown / not calibrated | No |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5` | OWNER-REPORTED 0.2449 | Unknown / not calibrated | No |
| GEMSDOE28 | `h36-1-rung30-blind-r1` | OWNER-REPORTED 0.2710 | Unknown / not calibrated | No |
| GEMSDOE30 | `d28-poisson300m-offcat-44090` | OWNER-REPORTED 0.2600 | Unknown / not calibrated | No |
| GEMSDOE31 | `h27-4-solo-d28` | OWNER-REPORTED 0.2708 | Unknown / not calibrated | No |
| GEMSDOE32 | `h33-h33-2-b2` | OWNER-REPORTED 0.2778 | Unknown / not calibrated | No — historical exemplar |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30` | OWNER-REPORTED 0.2632 (conflicts with 0.2608 ledger entry; `IR-25-GEMSDOE33-DUAL-SCORE-CLAIM`) | Unknown / not calibrated | No |
| GEMSDOE36 | `anderson-geothermal-pinn-38854` | OWNER-REPORTED 0.2750 in focus audit; 0.2683 in the G36 ledger | Unknown / not calibrated | No |

The supplied overall-leader claims `0.3195` and `0.4413` conflict and were not checked against DrivenData. Do not call either a current verified leaderboard value.

### Why GEMSDOE32 B2 plausibly led these nine

The pinned owner-mirror forensics record the mask lineage `H19-5 (121,131 px) -> D1.5 (60,069) -> D2.8 (44,090) -> R1 (40,199) -> B2 (37,654)`. D1.5-to-D2.8 is a re-thinning, not a nested deletion; R1 and B2 are catalogue-distance deletions from D2.8. GEMSDOE25/GEMSDOE30 share D2.8; the B2 mask deletes the `d(cat) <= 2 px` shell; GEMSDOE36 adds 1,200 dots to B2. These are computed owner-mirror geometry facts, not proof of a file-to-score association at the organizer. See [`knowledge/30`](30_h72_cf_outcomes_and_executive_decision_2026-10-26.md), [`knowledge/31`](31_h72_outcomes_and_portfolio_synthesis_2026-10-26.md), and `IR-25-GEMSDOE32-B2-PARADOX`.

Under `src/gems25/metric.py`, DTI uses triangular-kernel truth credit and penalizes off-truth prediction mass. If the owner-reported `0.2778` is accurate, a marginal change improves DTI only when its added truth credit is large enough relative to its added false-positive mass: `marginal_inclusion_ratio(D) = alpha*D/(1-alpha*D)`, about `0.0588` at `D=0.2778`; equivalently, credit per unit of added total prediction mass must exceed `alpha*D`, about `0.05556`. Conditional inversion of rounded owner-reported scores is consistent with the removed catalogue-near shell having low marginal credit. It does **not** establish that every deleted dot was false, or that catalogue proximity is generally harmful.

There is also a specific holdout leakage trap: `IR-25-GEMSDOE32-B2-PARADOX` records that scoring the pre-built full-catalogue B2 mask against `hidden_test` yields an artificial DTI of `0.0041`, because `hidden_test` is a subset of the full labels used to create B2's collar mask. The valid hide-and-recover procedure must build any collar only from `draw.visible` inside each out-of-fold cell. Its Factor-C result is positive in 8/8 fold-blocks across screen and confirmation, but that is **not** a holdout validation of the exact B2 artifact or proof of its organizer score. The proxy itself hides known components; it does not reveal the distribution of genuinely unmapped competition faults. No organizer receipt exists here, so B2's `0.2778` remains OWNER-REPORTED and no numeric estimate for a new TIFF is defensible.

## Ranked hypotheses for a future, explicitly assigned lane

These are planning hypotheses only. “Untried” means the exact proposed transform/combination is not recorded as implemented in the reviewed checkout; this is not a claim of global novelty across all sibling repositories. No numerical gain or score forecast is asserted. Rank reflects qualitative expected proxy value and testability, with uncertainty high.

| Rank | Layers and target signature | Why it may reveal a catalogue-missing fault | Difference from recorded methods | Named non-fault mimic | Expected proxy value / implementation cost / data status |
|---:|---|---|---|---|---|
| 1 | Cached RTP magnetic and K/Th/U radiometric bands; multi-scale magnetic phase congruency combined with along-strike radiometric texture continuity and across-strike texture mismatch | A concealed basement break could preserve a coherent magnetic edge under cover while changing the shallow compositional texture on its flanks; detector need not use catalogue proximity | H71 MAG-ANISO studies magnetic structure orientation/persistence; ROD studies tangential registration offsets. This tests cross-modality phase/texture asymmetry rather than either transform alone | Buried volcanic-flow or lithologic contacts; airborne mosaic seam | **Best screening value, uncertain** / medium / prior audit identifies these among supplied numerical layers (hash-pinned owner mirror); current inputs/cache are absent and the mirror is not organizer-authenticated |
| 2 | Cached gravity anomaly, basement-depth and DEM context; compare robust piecewise-planar ramp residuals across candidate lines against a smooth quadratic basin background at two window scales | Buried growth faults may produce a localized basin-fill slope break where surface scarps have been eroded | Earlier code tests gravity/basement steps and signed polarity; this tests local model-selection improvement over smooth background, not just step sign or gradient magnitude | Depositional wedge, broad flexure, interpolation seams in basement-depth products | **Low-to-moderate, uncertain** / medium-high / no new external source required for a first cached-layer screen; uncertainty and feature coverage must be measured after restoring data |
| 3 | DEM / LiDAR scarp descriptors plus RTP magnetics; paired, opposed scarp-normal steps bounding a narrow graben, with stable inter-wall spacing and one-flank magnetic support | Small antithetic splays can be omitted from a regional map even near a larger range-front system | H30 relay/tip and H31 scarp/coherence features do not explicitly require paired opposite walls with persistent spacing; this is not just a single scarp ridge | Drainage incision, roads/canals, erosional terraces, lava-flow margins | **Low/uncertain** / high / a high-resolution extension would need official [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) DEM tiles. Exact AOI tiles, coverage, and access were not checked in this session; do **not** call that extension viable yet. A cached 100 m proxy is a separate, weaker test. |

### Validation decision

The user prompt says to stay inside “the single method paragraph below,” but it contains no separate method paragraph or lane assignment. This is an unresolved protocol ambiguity, not permission to pick a lane. Consequently, no candidate surface was built, no standalone AUC canary or holdout was run, no registry surface/final-dot comparison was made, and no TIF was written. The three-experiment / two-hour budget used by this review is **0 experiments**. The ranked table is for a later preregistered run after the lane is explicitly present in the task; it is not a result or promotion recommendation.

## Verification and review passes

1. **Pass 1 — implementation:** read the standing brief and shared feed/metric/holdout/submission code; reproduced the DNS-equivalent host bypass; canonicalized the guard; added regression tests; logged the irregularity; recorded the existing nine-site and B2 status without upgrading claims.
2. **Pass 2 — bug and edge-case review:** tested root and subdomains, uppercase/DNS-dot spellings, repeated terminal dots, Unicode IDNA dot separators, non-DrivenData lookalikes, malformed URLs, and redirect behavior; verified that the redirect destination is never requested. Reviewed download gates and current PR status; did not change another branch or weaken the strict lane rule.
3. **Pass 3 — original-request reconciliation:** confirmed the focus-site table and B2 analysis are linked; score estimates remain unknown; no candidate TIF, holdout score, registry clearance, upload, or slot approval is claimed. The missing method paragraph prevents a safe new experiment. Remaining limitations are listed below.

**Local verification:** `.venv/bin/python -m pytest -q` — 323 passed, 12 skipped (data/template-dependent tests; `data/` has only `.gitkeep`); `.venv/bin/python -m ruff check src scripts tests` — passed; `.venv/bin/python -m compileall -q scripts tests src` — passed; `node --check docs/assets/app.js` — passed; `git diff --check` — passed. No model experiment was included in these checks.

## Official manual-review links and limitations

- [Competition problem and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [competition rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf): not fetched in this session; obey the repository policy against automated DrivenData access.
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution): available for manual source review; no current model claim is derived from it here.
- [USGS GeoDAWN release](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [DOE GDR 1391](https://gdr.openei.org/submissions/1391), [EPSG:32611](https://epsg.io/32611): links are supplied for review; new page, binary, tile, coverage, schema, and license verification was not performed in this review.
- No organizer score receipt is in the reviewed checkout; no external leaderboard score estimate can be supported.
- The current run is compute-ready only after restoring the pinned owner mirrors and rebuilding/validating the matching shared cache. The protocol's absent lane paragraph is an additional blocker to a geological run.

## Suggested next steps, in order

1. Preserve the feed-host canonicalization fix and regression test; check the CI result on the resulting pull request.
2. Resolve the missing lane assignment by carrying the single intended method paragraph into the next task/session; do not infer it from past candidate names.
3. Restore data only when the lane is set; verify SHA pins, grid metadata, band semantics and cache hashes before any fitting.
4. Freeze a preregistration for one top hypothesis, its same-run incumbent control, holdout draws/folds, canaries, analysis/CI and stop gate. Run only through shared holdout utilities.
5. Enforce surface and final-dot uniqueness against a complete registry before calling the shared writer. If any hard gate fails, leave the TIF absent and publish the negative result.
6. Resolve the existing open PR #47's GitHub merge conflict separately; do not treat a sibling branch's work as merged.
