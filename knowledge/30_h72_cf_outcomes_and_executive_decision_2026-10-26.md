# 30 · H72 MBSP-MTG Outcomes, Nine-Site Executive Decision, and Unique GeoTIFF Audit (`1d7c1e9ea55f`, 2026-10-26)

* **Branch:** `arena/11487c37-gemsdoe25`
* **Pre-registration:** [`knowledge/29_h72_cf_hypotheses_and_preregistration_2026-10-26.md`](29_h72_hypotheses_and_preregistration_2026-10-26.md), commit `2750fe9` before feature implementation/fitting; Experiment 3 addendum commit `7ba8333` before untouched draws `[84,85]`.
* **Experiments:** `3 / 3` (Screen, frozen Confirmation, CatFree ablation); `0` weekly slots used.
* **Machine Run Card:** [`registry/run_card_h72_cf_2026-10-26.json`](../registry/run_card_h72_cf_2026-10-26.json).
* **Evidence labels:** all competition values are **OWNER-REPORTED** (unverified) unless backed by a receipt; this repository contains **zero ORGANIZER-CONFIRMED scores**. Every local number below is labeled **COMPUTED** or **HOLDOUT-DTI**. No DrivenData page was accessed.

---

## 0. Decision First: Downloadable, Unique Content; **DO NOT SUBMIT**

| Question | Evidence-Driven Answer |
| :--- | :--- |
| **File to download** | [`gems25-h72-mbsp-mtg-catfree-b2-37654-20261026-1d7c1e9ea55f-zeros.tif`](../docs/downloads/gems25-h72-mbsp-mtg-catfree-b2-37654-20261026-1d7c1e9ea55f-zeros.tif) · single-TIFF [ZIP](../docs/downloads/gems25-h72-mbsp-mtg-catfree-b2-37654-20261026-1d7c1e9ea55f-zeros.zip) |
| **OK to download for testing?** | **YES.** SHA-256 `e39517cc95ac4083653299efb69d25a3772bd2bb1bfd4580ff9eb3ae82a8f2bb`; content ID `1d7c1e9ea55f`; `37,654` binary dots; no prior-registry content-ID match among `90` unique file hashes (only the same-session NaN/zeros encoding twin matches). |
| **Estimated leaderboard score** | **NO DEFENSIBLE ESTIMATE.** The nearest detector-family diagnostic is **HOLDOUT-DTI `0.094781`**, 95% quadrant-cluster bootstrap CI **`[0.082252, 0.107311]`**, `22,334` withheld-positive occurrences, evaluator `gems25.holdout.v1.2-buffered-4quad-pooled-dti`. It is a catalogue-gap proxy, **not a leaderboard score**; the exact artifact emission was not re-run after the `3/3` experiment cap. |
| **Unique vs the requested GEMSDOE focus/top files?** | **YES by scored content** (`0` prior content-ID matches). Final 3-px overlap clears all `27` pinned top/focus rasters: worst `64.02%` vs `GEMSDOE63`; `45.65%` vs `GEMSDOE32 B2`; it clears this repo's own lineage (`49.86%`). |
| **Strict lane unique vs every registry raster?** | **NO.** Pre-placement surface passes (`max |Spearman| = 0.2177 <= 0.90`), but final dots violate `>70% within 3 px`: r13 lattice `100%`, `pindrop-nodes` `85.50%`, `h23-a-6pct` `81.79%`, `pindrop-discovery` `79.68%`, and `r7-nms3-dem10-scarp` `72.39%`. Protocol Rule 1 says **duplicate/stop**. No density exception or dot-jitter evasion was applied. |
| **Format-valid?** | **YES** against the SHA-256-pinned owner-mirror template (not organizer-authenticated): one `float32` band, `EPSG:32611`, `3730 × 3292`, exact `100 m` transform, zero NaN anywhere in the zeros file, every value in `[0,1]`, zero known-catalogue emissions, ZIP byte-exact. This prevents the reported `"Predicted values must be in range [0, 1]"` failure. |
| **OK to spend a weekly slot?** | **NO — DO NOT SUBMIT.** The shipped CatFree detector is **HOLDOUT-DTI `0.094781` vs same-run H35 `0.153786`**, paired `−0.059005`, 95% CI `[-0.077251, -0.044136]`, `0/4` folds positive; exact artifact emission untested at the experiment cap; strict final-dot lane fails. |
| **Record-only note (71/140 chars; do not paste in contest form)** | `H72-CF MBSP-MTG; no slot; unscored; not slot-approved | id 1d7c1e9ea55f` |

**Bottom line:** this session met the unique-TIF and automatic-format-validation requirement, but it did **not** earn scientific or lane authorization. A changed hash is not enough. The only truthful verdict is **negative**.

---

## 1. Executive Summary of the Nine Focus Sites

“Best” means the highest value supplied in the owner brief for that site; none is organizer-confirmed. Historical files are learning exemplars, not new submissions.

| Site | Highest Supplied Historical File | Evidence Label | Locally Verified Mechanism / Relation | Unique New Submission? | Executive Verdict |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `GEMSDOE24` | `h25-1-dotted-h19-5-d1-5-...-989f59505db1-nan` | **OWNER-REPORTED `0.2477`** | Exact `dot_thin(H19-5,1.5)`, `60,069` dots. New GVC1 file is OWNER-REPORTED `0.0859`. | **No** | Historical baseline; outperformed by later spacing/collar variants. Do not re-submit. |
| `GEMSDOE25` | `dotted-h19-5-d2-8-...-e56ea318af89-nan` | **OWNER-REPORTED `0.2600`** | Exact `dot_thin(H19-5,2.4)`, `44,090` dots; identical positive mask to GEMSDOE30. New H66 file is OWNER-REPORTED `0.0742`, validating the catalogue-hug collapse. | **No** | Duplicate historical mask; withdrawn here. |
| `GEMSDOE27` | `topo-gap-closure-t-v2-on-d1-5-...-5512495c6bd1-nan` | **OWNER-REPORTED `0.2449`** | D1.5 plus `1,259` bridge pixels; lower than D1.5. New genuinely independent H29 is OWNER-REPORTED `0.2190`, the strongest new 2026-10-25 focus-site detector. | **No** | Historical file already scored; H29 is useful independent evidence but below B2. |
| `GEMSDOE28` | `h36-1-rung30-blind-r1-...-b531dae0a36f-nan` | **OWNER-REPORTED `0.2710`** | R1/rung-30 thinning; tiny `+0.0002` claim vs R1 is not statistical proof. New MXTP is `0.0217`. | **No** | Runner-up family, still `0.0068` below B2. |
| `GEMSDOE30` | `d28-poisson300m-offcat-44090-...-91eae1ca` | **OWNER-REPORTED `0.2600`** | Pixel-identical positive mask to GEMSDOE25 D2.8. New MSDB1 is `0.1462`. | **No** | Not independent evidence; do not repackage. |
| `GEMSDOE31` | `h27-4-solo-d28-...-8acb75e1-nan` | **OWNER-REPORTED `0.2708`** | Pixel-identical to GEMSDOE28 R1; `D2.8 & {d(cat)>1 px}`. | **No** | Historical duplicate mask. |
| **`GEMSDOE32`** | **`h33-h33-2-b2-...-e5eb6e7e-zeros`** | **OWNER-REPORTED `0.2778`** | Exact `D2.8 & {d(cat)>2 px}`, `37,654` dots. Best supplied nine-site historical result. | **No** | **Best historical exemplar; already submitted; never a new-file choice.** |
| `GEMSDOE33` | `h33d-analog-tip-stepover-r30-...-cb490425926e` | **OWNER-REPORTED `0.2632`** | Changes R1 and re-admits low-yield tip/collar dots; below B2. | **No** | Structural narrative did not produce incremental score. |
| `GEMSDOE36` | `anderson-geothermal-pinn-...-9b9ea4e6-zeros` | **OWNER-REPORTED `0.2750`** | Exact superset `B2 + 1,200` dots; additions diluted the claim by `−0.0028`. | **No** | Near second; demonstrates that unranked additions hurt. |

**Which focus-site file should be downloaded and submitted as new?** **None.** `GEMSDOE32 B2` is the strongest historical exemplar, but submitting an old duplicate violates the lane and uniqueness rules. The new H72 file is content-new and format-valid, but its automated status is **DO NOT SUBMIT**.

---

## 2. Why `GEMSDOE32 B2` Plausibly Reached `0.2778` (and What Is Not Proven)

### 2.1 Pixel-Exact Lineage (`COMPUTED`)

The local SHA-256-pinned masks establish:

`H19-5 (121,131 px)` → re-thin at `1.5 px` (`D1.5`, `60,069 px`) → re-thin same parent at `2.4 px` (`D2.8`, `44,090 px`) → delete `d(cat)<=1 px` (`R1`, `40,199 px`) → delete `d(cat)<=2 px` (**B2, `37,654 px`**).

`D1.5 → D2.8` is a re-thinning of the same parent, not a nested subset (`IR-25-THINNING-NONNESTED`). `R1` and `B2` are exact nested deletions. `GEMSDOE36` is B2 plus exactly `1,200` dots.

### 2.2 Metric Economics (`COMPUTED algebra conditional on OWNER-REPORTED scores`)

For binary dots, `TP_w + FP_w = M`, so:

`DTI = TP_w / (0.2*M + 0.8*N)`.

A marginal dot improves a file at score `D` only when its added weighted truth credit per dot exceeds `0.2*D`; at `D=0.2778`, the threshold is `0.05556`. Conditional inversion of the rounded owner-reported scores implies that R1's removed `d<=1 px` collar dots and B2's removed `1<d<=2 px` shell had far less credit than that break-even. The measured H72 audit adds the mechanism: Family-E models place `~75%` of dots within `1 km` of already known faults and collapse to owner-reported `0.0742–0.0859`, while every supplied detector at `>=0.219` places only `30–38%` there. B2's `30.2%` and median `d(cat)=19.6 px` occupy the high-transfer regime.

This is a strong **conditional explanation**, not proof: hidden labels and submission receipts are unavailable, and holdout hides catalogue components rather than genuinely unmapped faults.

### 2.3 Can We Exceed `0.2778`?

**In principle yes; this session provides no evidence that its downloadable file will.** To beat B2, a detector must add or substitute genuinely new off-catalogue fault pixels above the metric's marginal-credit threshold without paying excessive prediction mass. Pure H19-5 collar/spacing variants are saturated near `0.278`; independent fleet results (`GEMSDOE70 0.2478`, `GEMSDOE49 0.2376`, `GEMSDOE63 0.2303`, `GEMSDOE27 H29 0.2190`; all OWNER-REPORTED) have not exceeded it. The route with the largest scientific ceiling remains a spatial-context neural model trained on multi-kilometer patches with a differentiable 300 m DTI objective—not another filename, collar tweak, or catalogue-proximity model.

The prompt's `0.3195` and `0.4413` leaderboard values conflict by date and have no receipts here. They remain unverified claims, not optimization labels.

---

## 3. H72 Experiments (`3/3`) and What We Learned

### 3.1 H72 Add-On Replicated on the Strong H35 Lineage

All values below are **HOLDOUT-DTI** (`gems25.holdout.v1.2-buffered-4quad-pooled-dti`, $\alpha=0.2$, $\beta=0.8$, `R=300 m`; quadrant-cluster percentile bootstrap, `10,000` draws; same-run comparators).

| Stage | Draws | Withheld + | H72 `G1_D0` [95% CI] | Same-Run H35 `G0_D0` [95% CI] | Paired Gain [95% CI] | Folds + | Frozen Gate |
| :--- | :---: | ---: | :--- | :--- | :--- | :---: | :---: |
| Screen | `80,81` | `22,348` | `0.161605 [0.146693,0.179572]` | `0.156138 [0.140111,0.173472]` | **`+0.005467 [+0.002703,+0.007598]`** | `4/4` | **PASS** |
| Confirmation | `82,83` | `22,929` | `0.146133 [0.135010,0.159433]` | `0.144881 [0.132432,0.159716]` | **`+0.001253 [-0.000905,+0.003195]`** | `3/4` | **PASS by frozen mean/fold/worst rules** |
| Combined | `80–83` | `45,277` | **`0.153837 [0.140837,0.169439]`** | `0.150486 [0.136856,0.166542]` | **`+0.003351 [+0.002636,+0.004224]`** | `4/4` | **PASS** |

All six H72 feature-alone canaries passed (`max symmetric/missingness AUC = 0.598 <= 0.90`). Scientific conclusion: **macro-contour scarp and concealed subsurface/swarm signatures carry reproducible incremental information when regional catalogue geometry supplies strike/context**.

### 3.2 Debiased D1 Emission Failed; CatFree H72 Helps Its Weak Baseline but Does Not Beat H35

* `D1` short-range censoring + greedy output did not solve its intended objective: it still placed `58.5%` of dots within `d(visible)<=10 px`, and `G1_D1` off-flank paired gain vs H35 was `−0.00304` (Screen), `−0.00688` (Confirmation). Stop.
* Experiment 3 removed **all** `E_*`, `X2_*`, and `H27_*` features. `CF_G1` improved `CF_G0` by HOLDOUT-DTI `+0.004536` pooled (`+0.003940` fold mean; `3/4` folds; off-flank `+0.004832` fold mean), passing its frozen ablation gate.
* But `CF_G1` remained far below same-run H35: **`0.094781 [0.082252,0.107311]` vs `0.153786 [0.136740,0.169435]`**, paired **`−0.059005 [-0.077251,-0.044136]`**, `0/4` folds. That fail controls the downloadable artifact's verdict.
* The CatFree file successfully broke local geometry cloning (`49.9%` max overlap vs own lineage, `45.6%` vs B2) and placed `68.6%` of dots beyond `1 km` (`median d(cat)=17.9 px`), but geology and uniqueness are necessary, not sufficient: four old broad detector halos still exceed the literal `70%` cap.

---

## 4. Verification and Limitations

1. **Data restored autonomously:** `22/22` manifest inputs and `27/27` top/focus records SHA-256 verified from public owner mirrors; all `19` base bands, `64` static columns and add-ons built in the shared cache. Original organizer identity remains unverified.
2. **Ledger corruption fixed:** `21` fabricated `registry/live_scores.json` rows (`h50-b2...` through `h92-tpcr...`) were discovered by direct git-tree / historical-index / prompt cross-check and purged (`IR-25-HALLUCINATED-LEDGER-ROWS-20261026`). Authentic owner-reported values replaced them; no score was silently promoted.
3. **Shared path bug fixed:** default registry loading now honors `GEMS_DATA_DIR`; external-data runs can no longer silently skip `data/scored/` and the dense lattice (`IR-25-VALIDATOR-DATA-DIR-FIXED-20261026`).
4. **Proxy bias:** catalogue hide-and-recover is necessary but not sufficient; prior proxy/live rank correlation is weak. The exact full-file emission differs from the CatFree holdout diagnostic and was not granted a fourth experiment.
5. **No GPU:** only 2 CPU cores / 3.8 GiB RAM were available, preventing the ranked 2D ResUNet hypothesis within the two-hour experiment budget.
6. **No organizer access:** current weekly allowance, leaderboard, private/public split and live score are unknown; no upload was automated.

## 5. Next Work in P(Win) Order

1. **Do not submit H72-CF.** Preserve the negative and exact bytes.
2. Retain H72 MBSP-MTG columns as a validated add-on, but do not regenerate another H35-lineage TIFF under this parallel lane; it would violate own-lineage overlap and the experiment cap.
3. Resolve the literal dense-lattice and broad-artifact overlap policy in a separate selector/policy decision—never by jittering dots.
4. Next independent lane should be the pre-registered spatial-context ResUNet with strict patch/group splits and differentiable 300 m DTI loss, on GPU. Test against same-run H35 and CatFree P5-style controls; preserve all feature/missingness canaries.
5. Obtain and pin official NASA OPERA displacement tiles only in a future network-enabled session before declaring the InSAR hypothesis viable.
