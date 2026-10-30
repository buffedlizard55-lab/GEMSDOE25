# Pre-registration: soft visible-catalogue prior on a catalogue-free ridge score (2026-10-30)

Status: **PRE-REGISTERED, committed before any run.** Experiment 1 of a 3-experiment / 2-hour budget (AGENTS.md rule 4 and 6).
Evidence class of every number produced by this design: **HOLDOUT-DTI** (catalogue-gap proxy, not organizer-confirmed).
Nothing here is a submission, a slot choice, or an organizer score. No DrivenData access.

## 1. Why this design (from the repo's own review, not new data)

* `knowledge/52_repo_review_2026-10-29_verified.md` §9 ranks the next step as: *design a candidate on a new mechanism, not a pruning of B2; pre-register; run the same-run comparator; check the lane rule on the surface and on the final dots.*
* `knowledge/51` §5 rank 1 names a **soft distance prior around the visible catalogue** as "untested". **That claim is wrong and is corrected here (IR-30-SOFT-PRIOR-NOT-NEW).** `src/gems25/h31.py::build_offflank_tip_halo` already applies `exp(-(d-3)/12)` to the distance `d` to visible catalogue (the H31 off-flank piedmont halo, `scripts/run_h31_factorial.py`). What is **not** in the repo, as far as this session's grep shows, is the form tested here: a multiplicative soft prior on a **catalogue-free** ridge score, at a **fixed dot budget**, compared in the same run against a hard 200 m exclusion and a sign-reversed control. This experiment is therefore a re-test of an existing mechanism in a new form, not a new mechanism.
* Rank 2 in `knowledge/51` names a **density-matched control**. This design includes a random-dot floor (arm A4) at the same dot count, which is the minimum version of that control.
* Pruning B2 (or any file derived from the nine focus-site rasters) is a copy of a previously submitted file and is excluded by the owner's uniqueness rule.

## 2. Hypothesis (H-SP1)

Hidden (new) fault pixels in a test quadrant lie closer to the visible catalogue more often than a random footprint pixel does, but the effect is **graded**, not a hard halo. Therefore a catalogue-free ridge score multiplied by a soft decreasing prior `w(d) = exp(-d / λ)`, with `d` the distance to the **visible** catalogue only, gives higher pooled DTI than (a) the same ridge score with no catalogue prior, and (b) the same score with a hard 200 m exclusion (the mechanism used by the 0.2778 family).

* **Layer(s):** `A_mag_hg_ridge` (magnetic horizontal-gradient ridge strength, from the TMI/RTP grid; `src/gems25/features.py` line ~128; no catalogue input) and `d_vis` (Euclidean distance to visible catalogue, recomputed per draw; `gems25.holdout.Draw.visible`).
* **Physical signature targeted:** linear magnetic/gravity-gradient ridges that continue along strike of mapped faults, plus clustering of faults near mapped faults. The ridge score is the detector; the prior only re-weights it.
* **Why it could catch a fault missing from the catalogue:** the prior does not copy mapped traces. Dots are placed on ridges, and the prior only up-weights ridges that are near (not on) mapped traces. Hidden faults are scored only where they are not masked.
* **Named non-fault mimic:** *mapping-density bias.* Geologists mapped faults more densely where faults are already dense and where field access is good. Ridges near mapped traces could then reflect survey coverage, not hidden faults. Mitigation: the holdout hides whole components with a 1.5 km collar, so the mimic would have to survive that split.
* **Difference from the repo (narrow):** H31 applies the soft decay to a tip/flank feature family that is itself catalogue-derived (visible-tip continuation), and the repo's hard buffers (`CAT_BUF_PX = 2.0` in `scripts/build_h72_candidate.py`, `CAT_BUF_BLIND = 2.0` in `scripts/run_h74_experiments.py`) are used on catalogue-free candidates. The narrow novelty here is the multiplicative combination with a catalogue-free ridge score at a fixed dot budget with a sign control. The mechanism is **not new**; the test is.

## 3. Arms (same run, same draws, same evaluator)

Let `S` = `A_mag_hg_ridge` on the footprint, `V` = visible-catalogue mask of the draw, `d` = distance (pixels) to `V`, `K` = 21,000 dots.
Pixels eligible for emission: footprint and not `V` (visible catalogue is never emitted, matching the real file's rule).

| Arm | Emission rule | Role |
|---|---|---|
| **A0** | top-`K` of `S` | comparator: ridge, no catalogue prior |
| **A1** | top-`K` of `S · exp(-d/λ)`, `λ = 10 px` (1 km) | **candidate H-SP1** |
| **A2** | pixels with `d > 2 px` only; top-`K` of `S` | comparator: hard 200 m exclusion (B2-style mechanism) |
| **A3** | top-`K` of `S · exp(+d/λ)` | sign control: if A3 ≈ A1, the prior is not doing what it claims |
| **A4** | `K` uniformly random eligible pixels, seed fixed per draw | floor: random dots, same count |

Parameters `K = 21,000` and `λ = 10 px` are fixed here and are **not tuned** on outcomes. `K = 21,000` is below the literal lane cap of **21,713** dots (`evidence/lane_bound_r13_2026-10-28.json`, reproduced 2026-10-30 by `scripts/audit_r13_lane_bound.py`). A file at that count can pass the literal 70% r13 rule only if its dots lie outside the r13 halo, which is not guaranteed; the lane check in §6 is still required.

## 4. Draws, metric, and statistics

* **Development draws:** seeds 140–141, folds 0–3 (8 draws). These are the seeds used by `scripts/holdout_eval.py` for the wider repo, so they are **not virgin**; they are used here only for the development read.
* **Confirmatory draws:** seeds 144–147, folds 0–3 (16 draws). A search of `scripts/`, `src/`, `knowledge/` and `registry/` found no use of these seeds as holdout draws. Seeds 142–143 were already spent on H80 (`scripts/run_h80_experiments.py`) and are **not** used.
* Metric: pooled DTI over draws (sum TP, FP, FN across draws, then DTI), alpha 0.2, beta 0.8, triangular kernel 300 m (3 px). Implemented by `gems25.metric.dti_binary` via `Holdout.score`.
* Uncertainty: paired bootstrap over draws (10,000 resamples, seed 7). Reported: pooled DTI per arm, 95% CI, and **paired differences** A1−A0, A1−A2, A1−A3, A1−A4 with 95% CIs.
* Withheld-positive count: `n_truth_total` per run (reported with every number).

## 5. Leakage canary (run first)

For each feature alone (`S`, and `d` with sign as-is), compute AUC of its values for predicting `hidden_test` pixels within the test quadrant (non-visible footprint). **AUC above 0.90 = leakage until proven otherwise; the experiment stops.** Canaries are reported for dev and confirmatory draws.

## 6. Gates (pre-registered)

* **G0 (leakage):** all canary AUCs ≤ 0.90. Otherwise stop, report negative.
* **G1 (dev):** A1 pooled DTI > A0 AND > A2 AND > A4, with the paired 95% CI lower bound > 0 for A1−A0 and A1−A2.
* **G2 (confirm):** the same G1 test on seeds 144–147 alone.
* **G3 (sign control):** A3 pooled DTI < A1 (the prior must help in the claimed direction).
* **G4 (lane, only if G1–G3 pass):** build the 21,000-dot file on the full footprint with the full visible catalogue; run `scripts/check_lane_duplicates.py` (|Spearman| ≤ 0.90 and ≤ 70% of dots within 3 px of any registry raster) against every registry raster in `data/scored`, `docs/downloads`, and the nine focus-site rasters; run `scripts/verify_candidate_independent.py`. Any failure = **no file is cleared**.
* **Verdict:** `promote` only if G0–G4 all pass. Otherwise `negative`. A promotion still does **not** approve a weekly slot, and does not authorize submission (AGENTS.md rules 3, 5).

## 7. Budget and stop rule

* Experiment 1 of 3. Budget two hours of wall time from the start of the run, including the feature cache (already built this session, `data/work/static_ABCD.npy`).
* If the canary fails or G1 fails, the result is **negative** and recorded. No re-tuning of `K`, `λ`, the buffer, or the score to rescue it in this session. A follow-up would need its own pre-registration.

## 8. Searches done before writing this design (grep, 2026-10-30)

* First grep (`exp(-` with "soft") was **incomplete**: it returned `src/gems25/h31.py:124` (`piedmont = w_flank * np.exp(-np.maximum(dist_vis - 3.0, 0.0) / float(decay_px))`) among other exponential proximity terms (`h30.py:178`, `h36.py:111`, `h66_mgd_sgmc.py:135`, `h72_pttg.py:230`, `h75_eu3d.py:276`). The H31 hit is a soft catalogue-distance prior and falsifies the earlier "not found" claim.
* Hard buffers in the repo: `CAT_BUF_PX = 2.0` (`scripts/build_h72_candidate.py:56`, `scripts/build_h72_3_subsurf_candidate.py:54`), `CAT_BUF_BLIND = 2.0` (`scripts/run_h74_experiments.py:49`).
* Seeds 142–143 used by H80; 144–147 found in no holdout draw definition.
