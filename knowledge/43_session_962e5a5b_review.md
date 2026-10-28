# Executive review — 28 October 2026 — session 962e5a5b

## Decision: DO NOT SUBMIT

**No new, gate-cleared competition TIFF is available.** The requested unique high-scoring scientific deliverable remains incomplete. No slot was selected, no upload occurred, and no organizer score estimate is justified. Existing downloads are research archives only. The [nine-site executive table](../docs/current-review.html) lists the highest supplied historical result per site, exact filenames, archive links, unknown estimates and duplicate-mask findings. It does not certify the best possible submission at any site.

## Three-pass work and verified findings

1. Read the standing instructions, README and prior review; fetched remote state and inspected open sibling PRs #47 and #65 without modifying them. Restored only the three pinned inputs needed by the shared capacity audit. Result: 6,514 eligible pixels outside the r13 three-pixel halo; a 37,654-dot raster must overlap by at least 82.7004%. At most 21,713 dots are not ruled out by this one necessary condition. **COMPUTED GEOMETRY**, not HOLDOUT-DTI. Evidence: [capacity receipt](../evidence/session_962e5a5b_lane_capacity.json).
2. Tested the checkout: initially 17 tests failed, including a stale download inventory, missing no-go warnings and a broken ZIP link in the executive summary. Rebuilt the published HTML using the maintained generator rather than hand-editing the output; refreshed the shared download audit. All 60 TIFs pass that validator's local hard format checks. Some NaN-outside archives still fail a strict whole-array range interpretation; no organizer acceptance is inferred. [Inventory](../evidence/session_962e5a5b_download_audit.json).
3. Hardened the shared readiness contract: require a whole-array finite/[0,1] receipt and an absolute HOLDOUT-DTI 95% CI as well as the existing positive paired-improvement CI. Malformed top-level receipts fail closed. Added regression tests for missing receipts, malformed/nonfinite/out-of-range confidence intervals and legacy NaN ambiguity. Full suite after regeneration: **456 passed, 5 skipped**. Skips require missing scored/external/work-cache inputs. Tests are not proof of scientific performance or organizer acceptance.

The validator retains its historical NaN-aware archive behavior for reproducibility; the stricter readiness gate does not grandfather those archives into selector eligibility. The legacy check key `outside_footprint_is_nan_official` remains for compatibility, but it is not official evidence. Removed the misleading 'NaN (official)' assertion from its adjacent check description.

## Why GEMSDOE32's reported result leads this supplied list

The prior forensic receipt identifies B2 as D2.8 minus 6,436 pixels near the known catalogue. Selective removal can plausibly reduce redundant or false-positive credit while retaining off-catalogue coverage. Hidden truth is unavailable: this does not establish the causal explanation, a future score, or superiority on a new submission. The reported 0.2778, 0.3195 and 0.4413 are **OWNER-REPORTED, UNCONFIRMED**, not ORGANIZER-CONFIRMED or HOLDOUT-DTI. We retain their evidence class instead of laundering them into either verified category.

## Research queue before implementation

The prior [preregistration](41_session_plan_2026-10-28.md) already ranks four planning hypotheses: magnetic contact interruption under cover; conserved-total-intensity K/Th/U compositional offset; repeated terrace displacement across drainages; magnetic spectral phase discontinuity. Each names layers, transforms and non-fault mimics. The ranking is qualitative leverage/cost, **not estimated DTI improvement**. None is proven globally untried across all sibling projects. The current prompt still does not designate its promised single-method lane; this review does not silently choose one. No fitting experiment was run (zero of the three-experiment budget).

Next scientific run: assign a lane explicitly, restore and hash-pin its existing feature cache, preregister a density consistent with the literal overlap rule, verify the entire registry before placement, run every feature-alone canary, and compare buffered whole-segment hide-and-recover DTI to a same-run control. Reuse `gems25.holdout`, `gems25.block_holdout` and `gems25.submission`; the literal requested evaluate_holdout.py/submission_writer.py filenames are not the tools present in this repository. Do not create private substitutes. A positive paired CI is a necessary gate, not permission to spend a slot.

## Access and official sources

- [Official reference code](https://github.com/drivendataorg/gems-prize-reference-solution): GitHub metadata retrieved this run; [receipt](../evidence/session_962e5a5b_official_reference.json). Metadata is not verification of geological mechanisms or data authenticity.
- [Competition description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [NLR PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf): manual-review source links, not retrieved this run. Host restrictions prevent verifying their current contents; standing repository rules also prohibit automated DrivenData access. No organizer receipt or current weekly cap is available.
- Owner-mirror hashes establish byte integrity, not organizer provenance. Missing lane, incomplete scientific inputs, registry completeness, and absent paired validation are genuine blockers; data placement alone is not the remaining blocker.

Only GEMSDOE25 is changed. Sibling sites are not deployed by this PR. Maximize P(Win): preserve slots rather than upload unsupported candidates. Own the Outcome: repair the misleading executive page and report the negative result rather than fabricate success.
