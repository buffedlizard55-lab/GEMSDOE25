# Pre-registration 56: lane bound-fill file (H-BF1) and the 0.2778 mechanism control (H-REP1) (2026-10-31)

Status: **PRE-REGISTERED, committed before any run.** Session branch `arena/967c20f7-gemsdoe25`.
Budget (this session): **3 experiments or 2 hours**. Experiments 1 and 2 of this session are E3 and E4 below; one remains unused.
Evidence class of every number produced here: **HOLDOUT-DTI** (catalogue-gap proxy; evaluator `gems25.metric.dti_binary` via `gems25.holdout.Holdout.score`; not organizer-confirmed).
No DrivenData access, no upload, no slot choice. The agent does not promote any file.

## 1. Why these two experiments

* **Why 0.2778 scored highest (computed, `evidence/submission_inventory_2026-10-31.json`).** GEMSDOE32 B2 has 37,654 dots, 0 of them within 200 m (2 px) of the labelled catalogue. Its parents have 6.3% (h27-4, 40,199 dots) and 14.6% (D2.8, 44,090 dots). Owner-reported scores rose 0.2600 → 0.2708 → 0.2778 along that chain. The chain is a strict subset chain (`evidence/b2_lineage_recheck_2026-10-29.json`). Hypothesis (inference): under DTI, a dot within 2 px of a known fault that is not on hidden truth adds false-positive weight; removing such dots helps. **Untested control:** removal could help simply because the file has fewer dots (density). E4 separates the two.
* **Lane bound (verified on the bytes, `/tmp`-style check reproduced in `scripts/inventory_submissions.py`).** Outside the r13 3-px halo and the catalogue there are **6,514** footprint pixels. A file whose dots are at least 30% outside that halo can have at most **21,713** dots (the 70% lane rule of the parallel-run protocol). E3 asks whether such a file can carry holdout signal when it uses every lane-free pixel and fills the rest of the budget from the halo by the ridge score.

## 2. Shared definitions

* Footprint `F` = finite cells of `data/sample_submission.tif` (5,167,373 px). Catalogue `C` = `labels.tif == 1` inside `F` (60,988 px).
* Score layer `S` = `A_mag_hg_ridge` (catalogue-free magnetic ridge) from `data/work/static_ABCD.npy` (`names.index("A_mag_hg_ridge")`).
* Registry lane raster `R13` = `data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (sha256 pinned in `scripts/run_lane_first_prior.py`); halo `H` = `distance_transform_edt(~(R13>0 & F)) <= 3.0`.
* Per draw `(fold, seed)` from `gems25.holdout.Holdout`: visible catalogue `V` (`d.visible`), distance `d` to `V` (px). Eligible pixels `E = F & ~V`. Scoring uses `Holdout.score`, which masks `V` and restricts to the test quadrant.
* Draws: **development** = seeds 140–141 × folds 0–3 (8 draws, not virgin: used by `holdout_eval.py`). **Virgin confirmation** = seeds **150–153** × folds 0–3 (16 draws, never used before this file). Seeds 144–147 were spent on 30 Oct and are NOT used as confirmation.
* Metric: pooled DTI over draws (`tp/(tp + 0.2 fp + 0.8 fn + 1e-7)`), paired bootstrap over draws (10,000 resamples, seed 7), 95% percentile CI. Withheld positives (`n_truth_total`) reported per arm.

## 3. E3 (H-BF1): bound-fill, lane-compliant construction

K = **21,713** (the lane bound). Let `E_h = E & ~H` (lane-free, not visible) and `Hh = E & H` (halo, not visible).

| Arm | Emission rule |
|---|---|
| **F1 (candidate)** | all of `E_h` **plus** the top `K − |E_h|` pixels of `S` over `Hh` |
| **F2 (control)** | all of `E_h` **plus** `K − |E_h|` pixels drawn uniformly at random from `Hh` (rng seed `2000 + 10·seed + fold`) |
| **F3 (reference, NOT lane-compliant)** | top-`K` of `S` over `E` |
| **F4 (floor)** | `K` uniform random pixels from `E` (rng seed `3000 + 10·seed + fold`) |

Gates (pre-registered, all must pass):
* **G0 (leakage canary):** per draw, AUC of `S` and of `−d` within `E` each ≤ 0.90 (any draw above 0.90 = stop).
* **G1 (dev):** F1 − F2 > 0 with 95% CI lower bound > 0 (the halo score matters); F1 − F4 > 0 with CI lower bound > 0.
* **G2 (virgin confirmation, seeds 150–153):** the same two tests.
* **G3 (lane, by construction):** every F1 dot is either in `E_h` (outside the halo) or in the halo: the halo share is `(K − |E_h|)/K` by design, which must be ≤ 70%. Verified as an assertion in the script, and later on the built file by `scripts/check_lane_duplicates.py`.
* **Verdict:** `compliant-file-holdout-signal` if G0–G3 pass; otherwise `negative`. A pass allows a file build and the full duplicate/format audit. It does **not** clear a file or approve a slot.

## 4. E4 (H-REP1): is the B2 effect repulsion or thinning? (mechanism control)

Base `B` = top-`K_B` of `S` over `E`, with `K_B = 37,654` (B2's count). Let `N2 = {x : d(x, V) <= 2 px}`.

| Arm | Emission rule |
|---|---|
| **P0** | base `B` |
| **P1 (B2-style repulsion, count drops)** | `B \ N2` (no refill) |
| **P2 (density-matched random thinning)** | `B` minus the same number of dots as P1, chosen uniformly at random from `B` (rng seed `4000 + 10·seed + fold`) |
| **P3 (repulsion, count matched)** | `B \ N2` refilled with the next-best `S` ranks over `E \ N2` until `|P3| = K_B` |

Gates:
* **G1 (dev) and G2 (virgin, seeds 150–153):** P1 − P2 > 0 with 95% CI lower bound > 0 on **both** splits ⇒ the B2 effect is repulsion beyond thinning (`mechanism-supported`).
* If P1 − P2 is not significant on both splits ⇒ `thinning-explains-B2` (the removal of catalogue-adjacent dots adds nothing beyond removing dots).
* P3 − P0 is reported as the count-matched repulsion effect (no gate).

## 5. Interpretation rules (fixed in advance)

* A holdout gain is a proxy result. It does not give an organizer score. The owner-reported 0.2778 and the holdout values are never mixed in one number.
* A negative on E3 means no lane-compliant file of this size has holdout signal, and the file build is blocked. A negative on E4 means the 0.2778 mechanism is not repulsion.
* Results are written to `evidence/bound_fill_exp3_2026-10-31.json` and `evidence/repulsion_exp4_2026-10-31.json`. Nothing is tuned after seeing outcomes; a failed arm stays failed.

## 6. E5 (H-CLEAN1): the protocol-clean construction, pre-registered AFTER E3/E4 and before E5 runs (disclosed)

**Disclosure.** E3 showed that the ridge ranking inside the r13 halo is worse than random (F1 < F2). The construction that clears the full registry lane check (`evidence/lane_check_bound_fill_candidate_2026-10-31.json` flagged the first candidate against `pindrop-discovery.tif` at 71.05%) is different: the halo fill ranks halo pixels by **ascending coverage by the other 121 registry rasters**, not by the ridge. E5 is therefore added here, as the third and last experiment of this session, to test that construction before any file is labelled. It was added after E3 and E4 results were known; this is stated, not hidden.

* **Arms (per draw, same `E_h` as §3):** C1 = `E_h` plus top-`(K − |E_h|)` halo pixels (not visible) by **ascending** `kother` (count of the other 121 registry halos covering the pixel; ties broken by rng seed `5000 + 10·seed + fold`). C2 = `E_h` plus random halo pixels (rng seed `6000 + 10·seed + fold`). C3 = `K` uniform random pixels from `E` (floor, rng seed `7000 + 10·seed + fold`).
* **Draws:** development = seeds 140–141 (not virgin). **Virgin confirmation = seeds 160–163** (never used: 150–153 spent on E3/E4).
* **Gates:** G0 canary as §5 (AUC ≤ 0.90). G1 (dev): C1 − C2 > 0 with CI lower > 0; C1 − C3 > 0 with CI lower > 0. G2 (virgin 160–163): the same two tests. Verdict `clean-construction-holdout-signal` if all pass, else `negative`.
* **Use of the verdict.** A pass allows labelling the protocol-clean file as holdout-positive (still not organizer-confirmed, still not a slot approval). A negative keeps the file as a unique, format-valid, **NOT cleared** deliverable.
