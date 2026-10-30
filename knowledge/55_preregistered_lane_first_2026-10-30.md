# Pre-registration: lane-first construction, does a lane-compliant file score anything? (2026-10-30)

Status: **PRE-REGISTERED, committed before any run.** Experiment 2 of 3 (budget: 3 experiments or 2 hours; experiment 1 is `knowledge/54`).
Evidence class of every number: **HOLDOUT-DTI** (catalogue-gap proxy, not organizer-confirmed). No DrivenData access, no upload, no slot choice.

## 1. Why this experiment

* Experiment 1 (`knowledge/54`, `evidence/soft_catalogue_prior_exp1_2026-10-30.json`) failed gate G1: random dots beat the soft-prior arm. The arm's file also **fails the literal lane rule**: 99.87% of its 21,000 dots lie within 3 px of registry raster r13 (`evidence/checks_hsp1_candidate_2026-10-30.json`, `scripts/check_lane_duplicates.py`, verdict "DUPLICATE/LANE OVERLAP - stop; do not package"). The check fails closed at the first duplicate by design (`break` in `audit()`), so "registry_checked: 1" is not a coverage gap, but a pass would require the full loop.
* Repo bound (`evidence/lane_bound_r13_2026-10-28.json`, reproduced 2026-10-30): r13 covers almost the whole footprint. Only **6,514** footprint pixels are outside both the r13 3-px halo and the catalogue. A catalogue-free file with more than **21,713** dots therefore has at least 70% of its dots within the halo, and a file with 21,000 dots must place about 94% of its dots on those 6,514 pixels to pass.
* The only lane-compliant construction is therefore **lane-first**: choose dots only from pixels outside the r13 halo. This experiment asks whether such a file has any holdout signal.

## 2. Hypothesis (H-LF1)

Restricting emission to pixels outside the r13 3-px halo and outside the visible catalogue keeps a ridge-based detector's signal above the random floor. A soft catalogue prior (`exp(-d/10 px)`) still helps within that restricted set.

* **Layer:** `A_mag_hg_ridge` (catalogue-free magnetic ridge); `d_vis` (visible catalogue distance, per draw); r13 halo (registry raster, not catalogue).
* **Physical signature:** the same as `knowledge/54` §2, now restricted to the r13-free area.
* **Named non-fault mimic:** the r13-free pixels are concentrated in the zones r13 did not sample (its lattice gaps). A holdout signal from those zones could be lattice-gap geometry, not faults. The holdout cannot separate this, so a positive result would not establish a fault signal.
* **Repo difference:** no lane-first construction exists in `scripts/` or `src/`; `scripts/build_unique_submission.py` (lattice-gap publisher) is retired for lacking exactly this gate (`knowledge/43`).

## 3. Arms (same run, same draws, same evaluator)

Per draw: `V` = visible catalogue; `H` = pixels within 3 px of any r13 dot (r13 dots = `r13 > 0` inside footprint; `distance_transform_edt(~r13dots) <= 3.0`, as in `check_lane_duplicates.py`); `E = footprint & ~V & ~H`; `d` = distance to `V` (px). `K = 6,000` dots (fixed; below the smallest per-draw `|E|`, asserted at runtime).

| Arm | Emission rule |
|---|---|
| **L0** | top-`K` of `S` (`A_mag_hg_ridge`) over `E` (comparator, no prior) |
| **L1** | top-`K` of `S · exp(-d/λ)`, `λ = 10 px`, over `E` (**candidate H-LF1**) |
| **L2** | top-`K` of `S` over `E ∩ {d > 2 px}` (hard 200 m buffer) |
| **L3** | top-`K` of `S · exp(+d/λ)` over `E` (sign control) |
| **L4** | `K` uniformly random pixels from `E` (floor), seed `1000 + 10·seed + fold` |

`K = 6,000` and `λ = 10 px` are fixed here and not tuned on outcomes.

## 4. Draws, metric, statistics

* Development draws: seeds 140–141, folds 0–3 (8 draws). Not virgin (used by `scripts/holdout_eval.py`).
* Confirmatory draws: seeds 144–147, folds 0–3 (16 draws). Not used in any holdout draw definition (`knowledge/54` §4 search). Seeds 142–143 are excluded (spent on H80).
* Metric: `gems25.metric.dti_binary` through `Holdout.score`; pooled over draws; alpha 0.2, beta 0.8, 300 m kernel. Paired bootstrap over draws (10,000 resamples, seed 7). Withheld positives (`n_truth_total`) reported.

## 5. Gates (pre-registered, same structure as `knowledge/54` §6)

* **G0 (leakage):** all single-feature AUCs (`A_mag_hg_ridge`, `-d`) ≤ 0.90 within `E` on each draw. Otherwise stop.
* **G1 (dev):** L1 > L0, L1 > L2, L1 > L4, with paired 95% CI lower bound > 0 for L1−L0, L1−L2 and L1−L4.
* **G2 (confirm):** the same test on seeds 144–147 alone.
* **G3 (sign):** L1 > L3 on both splits.
* **G4 (lane):** satisfied **by construction** (every dot is outside the r13 halo); verified only if a file is built. Any file still needs the full `check_lane_duplicates.py` loop and the independent verifier.
* **Verdict:** `promote-to-file-build` only if G0–G3 pass. A pass still does not clear any file or approve a slot. `negative` otherwise.

## 6. Interpretation rules (fixed in advance)

* A lane-compliant file with a holdout score **below the random floor L4** is a negative result for this construction.
* A positive result with L1 > L4 is still a proxy result; it is not evidence of organizer score.
* Any new number is labelled HOLDOUT-DTI with its draws, withheld count and CI.
