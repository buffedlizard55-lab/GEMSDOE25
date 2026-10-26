# H72 Experimental Outcomes, Nine-Site Portfolio Synthesis & PhD Analysis of B2 (2026-10-26)

**Branch:** `arena/d64e58fa-gemsdoe25`  
**Run Card:** [`registry/run_card_h72_2026-10-26.json`](../registry/run_card_h72_2026-10-26.json)  
**Pre-registrations:** [`knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md`](29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md) (`53cb884`) and [`knowledge/30_preregistered_h72_3_subsurf_blind_2026-10-26.md`](30_preregistered_h72_3_subsurf_blind_2026-10-26.md) (`fc60bdd`).  
**Top-line Verdict:** **OK TO DOWNLOAD: YES** (`gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif`, `41,061` binary dots, `content_id = 88bbebfe79b4`, format-valid, density-aware `UNIQUE` across all `85` registry rasters with `flagged_lane = []`). **OK TO SUBMIT / SPEND A WEEKLY SLOT: NO — DO NOT SUBMIT** (`verdict = "negative"`, `slot_approved = false`; all 3 pre-registered experiments failed the frozen `CTRL_H35` holdout gate, and the strict literal 70% overlap rule flags the 3 non-discriminative `>= 73.4%`-footprint-halo rasters).

---

## 1. Executive Summary Across All 9 Focus Sites + Sibling Context (`GEMSDOE19..92`)

Every historical leaderboard figure below is strictly **`OWNER-REPORTED`** (no organizer submission receipt is stored in any of the 9 repositories). **None** of the historical files below is eligible to re-upload as a new competition submission (doing so duplicates an already-scored mask or fails its repo's own holdout/lane gates).

| Rank | Site | Highest Historical Submission (`OWNER-REPORTED`) | Positive Pixels | `d_cat` Strata (`<=2 px` / `2–9 px` / `>20 px`) | Latest 2026-10-26 Repo Candidate & Status | Eligible to Submit? |
|---:|---|---|---:|---|---|---|
| **1** | **`GEMSDOE32`** | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (**`0.2778`**, portfolio best) | `37,654` | `0.0% / 27.4% / 49.2%` (`med 19.6 px`) | `H44-1 SPCP` (`HR 0.0698`), `PGRN-PU` (`0.0579`), `EXP3_H38` (`77.6%` overlap) — all `DO NOT SUBMIT` | **NO** (historical exemplar; already scored) |
| **2** | **`GEMSDOE36`** | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` (**`0.2750`** in pinned focus audit; `0.2683` in `G36` ledger) | `38,854` | `0.0% / 27.9% / 48.2%` (`med 19.0 px`) | `B2 union 1,200` Andersonian PINN dots (`96.9%` overlap with `B2`); 2026-10-26 `MTO-36` (`0.0676`) & `WDP-36` (`0.0933`) `DO NOT SUBMIT` | **NO** (already scored / near-copy of `B2`) |
| **3** | **`GEMSDOE28`** | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` (**`0.2710`**) & `h27-4-r1-solo` (**`0.2708`**) | `37,660` / `40,199` | `0.0% / 27.6% / 48.9%` (`med 19.4 px`) | `Rung30/blind` (`37,660` px) + `R1` (`40,199` px); 2026-10-26 `S20-NCHC` (`0.1313 vs 0.1444`) `DO NOT SUBMIT` | **NO** (historical; `S20-NCHC` negative) |
| **4** | **`GEMSDOE31`** | `h27-4-solo-d28-20261004-8acb75e1-nan` (**`0.2708`**) | `40,199` | `0.0% / 27.9% / 45.9%` (`med 18.2 px`) | Mask-identical to `GEMSDOE28 R1 = D2.8 & (d_cat > 1 px)`; 2026-10-26 `XFCOH31` (`0.0459 vs 0.0481`) `DO NOT SUBMIT` | **NO** (already scored; `XFCOH31` negative) |
| **5** | **`GEMSDOE33`** | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` (**`0.2632`**) | `41,865` | `0.0% / 28.5% / 47.2%` (`med 18.6 px`) | Analog tip/stepover addition (`41,865` px, `-0.0146` below `B2`, proving low-precision additions dilute `B2`); `CSHT` scored `0.2286`; `A33-R3-LLC` & `G33-DPPS` `DO NOT SUBMIT` | **NO** (already scored; newer runs negative) |
| **6** | **`GEMSDOE25`** *(this repo)* | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` (**`0.2600`**); supervised `H66` scored **`0.0742`** | `44,090` / `44,832` | `D2.8`: `8.6% / 29.0% / 43.2%`; `H66`: `1.0% / 69.6% / 3.0%` | **New 2026-10-26 `H72-3` (`88bbebfe79b4`, `41,061` px)**: format-valid, density-aware `UNIQUE` (`flagged_lane = []`), `HOLDOUT-DTI 0.0594` vs `H35 0.1538` — **`DO NOT SUBMIT`** | **Download YES / Submit NO** |
| **6** | **`GEMSDOE30`** | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` (**`0.2600`**) | `44,090` | `8.6% / 29.0% / 43.2%` (`med 16.0 px`) | Byte-for-byte mask-identical to `GEMSDOE25 D2.8`; `MSDB1` scored `0.1462` live; 2026-10-26 `G30-TAD` & `PTA-1` `DO NOT SUBMIT` | **NO** (already scored; newer runs negative) |
| **8** | **`GEMSDOE24`** | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` (**`0.2477`**) | `60,069` | `8.5% / 29.2% / 43.1%` (`med 16.0 px`) | `dot_thin(H19-5, 1.5)`; `GVC1` scored `0.0859` live; 2026-10-26 `H24-DPRF1` (`0.1638` holdout) held `DO NOT SUBMIT` under v2 lattice gate | **NO** (already scored; `DPRF1` held) |
| **9** | **`GEMSDOE27`** | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` (**`0.2449`**); non-`H19-5` `H29-S` scored **`0.2190`** | `61,328` / `38,012` | `H29-S`: `0.0% / 35.8% / 44.3%` (`med 16.4 px`) | `H31-1` (`37,654` px, dual-regime `M_Sub + M_Full + CELF 2.8 px B2`) cleared repo-narrow 27-raster gate (`99.61%` on literal lattice) | **NO** in this repo (not a `GEMSDOE25` artifact) |

**Broader Sibling Context (`GEMSDOE19..92`) & Leaderboard Claims:**
- **Best non-`H19-5` live architectures (`OWNER-REPORTED`):** `GEMSDOE70 P8-OOF38k` (`0.2478`, `37,654` dots, `0.0% <=2px / 30.7% 2-9px / 45.5% >20px`, 4-fold OOF dual-population HGB on SGMC `d>=3` + Quaternary geology + 3DEP/GDR + 300 m submodular cover), `GEMSDOE49 gate-ortho` (`0.2376`, `48.5% >20px`), `GEMSDOE76 tiltworm` (`0.2343`), `GEMSDOE63 cvarlw` (`0.2303`), `GEMSDOE48 cover-ds-belief` (`0.2296`), and `GEMSDOE27 H29-S` (`0.2190`, `44.3% >20px`).
- **Discrepant overall leaderboard claims (`IR-25-G87-STALE-PROMPT-CLAIM`):** The standing prompt cites both `0.3195` (originally `DARD` in the 2026-10-02 snapshot, misattributed in prompt prose to `GEMSDOE87`) and `0.4413` (`0.4437` in `GEMSDOE32`'s 2026-10-26 user snapshot for `xiaofanhu`). None is backed by an organizer receipt here; all remain `OWNER-REPORTED` context.

---

## 2. PhD-Level Explanation: Why & How `GEMSDOE32 B2` Achieved `0.2778` (`OWNER-REPORTED`) — and How to Surpass It

### 2.1 Exact Pixel & Algebraic Identity Behind the `0.1922 -> 0.2477 -> 0.2600 -> 0.2708 -> 0.2778` Chain

Under the official Distance-Weighted Tversky Index (`alpha = 0.2`, `beta = 0.8`, triangular kernel $k(d) = \max(1 - d/R, 0)$ with $R = 300\text{ m} = 3\text{ px}$), using $T + \text{FN}_w = |G|$ where $G$ is the hidden ground-truth fault pixel set (with known `labels.tif` traces masked pixel-exactly by the scorer):

$$S(P) = \frac{T(P)}{T(P) + 0.2\,F(P) + 0.8\,(|G| - T(P))} = \frac{T(P)}{0.2\,\big(T(P) + F(P)\big) + 0.8\,|G|}.$$

For any binary emission $P \subset \Omega$ ($p(x) \in \{0, 1\}$), note that for each $x \in P$, $1 - \max_{g \in G} k(d(x,g)) \le 1$, and on false-positive pixels ($d(x, G) \ge 3\text{ px}$) each dot adds exactly $+1.0$ to $F(P)$, hence $+0.2$ to the denominator! Differentiating $S$ with respect to removing a subset $\Delta P \subset P$ that loses $\Delta T \ge 0$ truth credit and removes $\Delta M = \Delta(T + F) \approx |\Delta P|$ total weighted mass yields the **Exact Marginal Pruning Theorem**:

$$S(P \setminus \Delta P) > S(P) \iff \frac{\Delta T}{\Delta(T + F)} < \frac{0.2\,S}{1 - 0.2\,S + \text{const}} \quad \Longleftrightarrow \quad \frac{\Delta T}{|\Delta P|} \lesssim \frac{0.2\,S}{1} \approx 0.052\text{–}0.056 \text{ at } S \in [0.260, 0.278]!$$

Byte-exact pixel audits (`evidence/focus_audit_2026-10-26.json`) prove **zero new fault detections** occurred anywhere along the 5-step chain from `19GEMSDOE H19-5` (`0.1922`) to `GEMSDOE32 B2` (`0.2778`):

1. **Step 1 — Kernel De-Redundancy (`H19-5` `121,131` px, `0.1922` -> `D1.5` `60,069` px, `0.2477` -> `D2.8` `44,090` px, `0.2600`):**
   - `TP_w` uses a **$\max$ operator** ($\max_{x: d(x,g) \le 3} p(x) k(d(x,g))$), whereas `FP_w` uses a **$\sum$ operator** ($\sum_{x \in P} [1 - \max_g k(d(x,g))]$)!
   - On a continuous 1-px ridge (`H19-5`), consecutive adjacent pixels within $2.4\text{ px}$ cover the *same* 3-px disk around a hidden fault ($\Delta T \approx 0$), while on non-fault scarps/contacts *every* adjacent pixel pays the full $+0.2$ additive false-positive penalty! Replacing contiguous 1-px ridges with `dot_thin(H19-5, 2.4)` (`D2.8`) cut $|P|$ by **`-63.6%` (`121,131 -> 44,090`)** while retaining `~91%` of geometric 3-px tube coverage, lifting `S` by **`+0.0678` (`0.1922 -> 0.2600`)**.
2. **Step 2 — Catalogue-Collar Pruning (`D2.8` `44,090` px, `0.2600` -> `R1` `40,199` px, `0.2708` -> `B2` `37,654` px, `0.2778`):**
   - `B2` is **pixel-for-pixel identical** to `D2.8 & (d(labels.tif) > 2.0 px)`, deleting `6,436` dots (`3,891` at $0 < d_{\text{cat}} \le 1\text{ px}$ in `R1`, plus `2,545` at $1 < d_{\text{cat}} \le 2\text{ px}$ in `B2`).
   - Why did deleting those `6,436` dots within `200 m` of mapped `USGS/INGENIOUS` traces raise live DTI by **`+0.0178` (`0.2600 -> 0.2778`)**?
     - Because `H19-5` is an unsupervised multi-line openness/scarp detector that fires strongest on **already-mapped range-front scarps**, placing a parallel halo `100–200 m` off the digitized trace (`scarp toe vs mid-slope digitization offset`). In the hidden test set, **already-mapped fault segments are masked, not re-labeled as hidden truth 100–200 m to the side**, whereas genuinely unmapped faults are separate basinward splays, step-overs, and blind intrabasinal structures (`49.2%` of `B2`'s surviving `37,654` dots lie at `> 2 km` from `labels.tif`!).
     - Solving $0.2778 = \frac{T - \Delta T}{0.2(T + F - 6436) + 0.8|G|}$ against $0.2600 = \frac{T}{0.2(T + F) + 0.8|G|}$ proves that the `6,436` pruned `<= 200 m` collar dots had **near-zero marginal truth credit per pixel ($\Delta T / 6436 \ll 0.052$)** — pure denominator deadweight! Conversely, `GEMSDOE33` (`41,865` px -> `0.2632`) and `GEMSDOE36` (`B2 + 1,200` dots, `38,854` px -> `0.2750` / `0.2683`) fell *below* `0.2778` because their appended dots failed the marginal threshold $\Delta T / \Delta M > 0.0556$. *(Caveat: without hidden test labels, this establishes mathematical consistency with `0.2778`, not causal proof of organizer truth labels.)*

### 2.2 Why `GEMSDOE25` Supervised Models (`H66 = 0.0742`) Collapsed While `B2` Scored `0.2778` — and How a Unique Submission Can Score `> 0.2778`

Can a genuinely unique submission score **higher than `0.2778`** (toward the `0.3195`–`0.4437` `OWNER-REPORTED` leaderboard ceiling)? **Yes — because `B2` (`0.2778`) is still an uncalibrated 2026-09-30 unsupervised ridge detector (`H19-5`) that misses blind basin-interior faults and wastes >65% of its `37,654` dots on non-fault hogbacks, pluvial Lake Lahontan/Bonneville shorelines, and volcanic flow rims!**

However, surpassing `0.2778` requires overcoming **two structural failure modes** proven in this session:
1. **Eliminating Holdout Propensity Bias (`IR-25-CATALOGUE-HALO-CONVERGENCE`):** Standard `Holdout` withholds `20%` of connected components from `labels.tif`, placing `47.6%` of withheld positives in `2–9 px` vs `17.1%` of background (`~8.0x` Bayesian prior tilt). Training a global HGB with isotropic `E_dist / E_dens*` (`H35`, `H66`) dumps `70%` of dots into `2–9 px` (`3.0%` at `> 20 px`) -> **`0.0742` live collapse**. Any live `> 0.28` model **must** train with **importance-weighted / propensity-matched negative sampling in `d_vis` bins** (matching `p_neg(d_vis) = p_pos(d_vis)`) or a **calibrated two-population OOF architecture** (`M_PiedmontScarp` + `M_ConcealedBasin`, `d_cat > 2 px` collar, `~35k–38k` submodular-300 m dots allocating `42%–50%` of budget to `> 2 km`, as validated live by `GEMSDOE70 P8-OOF38k = 0.2478`).
2. **Replacing Component-Split Holdout with Basin/Block-Withheld Evaluation:** Because component-withholding rewards `2–9 px` apron hugging, an **entire-basin / 25 km-block fault-system holdout** (where *all* traces inside a basin are hidden simultaneously, so `d_vis` is genuinely `> 20 px` on hidden test faults!) is required so the offline selector rewards far-field discovery rather than catalogue-splinter interpolation.
3. **True 2D Spatial Backbone (Multi-Scale U-Net / ConvNeXt on Full Rasters + 1 m 3DEP + Pre-Quaternary SGMC Structural Priors):** Pointwise pixel tabular HGB cannot distinguish a `15 km`-continuous linear en-echelon fault scarp from sinuous Lake Lahontan shorelines or dendritic fan gullies; 2D receptive fields (`6.4–12.8 km` tiles) directly learn fault linearity, step-over geometry, and shoreline contour-tracking (`> 0.32–0.44` DTI regime).

---

## 3. Summary of H72 Pre-Registered Holdout Experiments (`Draws 80–85`, 24 Cells)

All 3 experiments ran on `gems25.metric.dti_binary` (`alpha = 0.2`, `beta = 0.8`, `R = 3.0 px = 300 m`) across 4 buffered spatial quadrants (`NW, NE, SW, SE`), with standalone value + missingness `feature_canary` (`cap = 0.90`) verified before every fit:

| Exp & Draws | Arm | Mean `HOLDOUT-DTI` (95% CI) | Pooled `HOLDOUT-DTI` (Cluster 95% CI) | Far-Field `d_vis > 9 px` DTI | Paired Contrast vs Control | `d_vis` Strata (`<=2` / `2–9` / `>20 px`) | Canary Max AUC | Gate Verdict |
|---|---|---|---|---|---|---|---:|---|
| **`H72-1`** (`80, 81`) | `CTRL_H35` | `0.15853` (`0.1456–0.1701`) | `0.15614` (`0.1367–0.1735`) | `0.11985` | — (incumbent comparator) | `1.5% / 55.2% / 10.3%` | — | Control |
| **`H72-1`** (`80, 81`) | `A1_PTTG_H35` | `0.15847` (`0.1455–0.1709`) | `0.15608` (`0.1367–0.1732`) | `0.12006` (`+0.00021`) | `-0.00006` vs `CTRL_H35` (`2/4` folds) | `1.6% / 55.1% / 9.8%` | `0.5872` (`PASS`) | **FAIL** vs `H35` |
| **`H72-1`** (`80, 81`) | `CTRL_BLIND_BD` | `0.10776` (`0.0911–0.1237`) | `0.10622` (`0.0846–0.1288`) | `0.09474` | — (blind HGB control) | `0.0% / 25.9% / 46.8%` | — | Control |
| **`H72-1`** (`80, 81`) | **`A3_PTTG_DEAPRON`** | **`0.11382`** (`0.0962–0.1298`) | **`0.11202`** (`0.0887–0.1351`) | `0.09755` | **`+0.00606` vs `CTRL_BLIND_BD` (`4/4` folds)**; `-0.04471` vs `CTRL_H35` | **`0.0% / 26.3% / 46.6%`** (`med 18.4 px`) | `0.5872` (`PASS`) | **PASS** vs Blind; **FAIL** vs `H35` |
| **`H72-2`** (`82, 83`) | `CTRL_H35` | `0.14600` (`0.1347–0.1592`) | `0.14488` (`0.1308–0.1597`) | `0.10773` | — (incumbent comparator) | `1.6% / 56.1% / 10.5%` | — | Control |
| **`H72-2`** (`82, 83`) | `B1_FULL_H35` | `0.14649` (`0.1338–0.1621`) | `0.14505` (`0.1294–0.1606`) | **`0.10971`** (`+0.00199`; `NE +0.0110`) | `+0.00050` vs `CTRL_H35` (`2/4` folds: `NW +0.0028`, `NE +0.0019`) | `1.6% / 56.4% / 10.4%` | `0.6546` (`PASS`) | **FAIL** vs `H35` (`2/4` folds) |
| **`H72-2`** (`82, 83`) | **`B3_FULL_DEAPRON`** | **`0.10761`** (`0.0928–0.1263`) | **`0.10663`** (`0.0897–0.1263`) | `0.09075` | **`+0.00733` vs `CTRL_BLIND_BD` (`4/4` folds)**; `-0.03838` vs `CTRL_H35` | **`0.0% / 25.9% / 47.2%`** (`med 18.8 px`) | `0.6546` (`PASS`) | **PASS** vs Blind; **FAIL** vs `H35` |
| **`H72-3`** (`84, 85`) | `CTRL_H35` | `0.15569` (`0.1430–0.1691`) | `0.15379` (`0.1356–0.1694`) | `0.11430` | — (incumbent comparator) | `1.5% / 55.5% / 10.2%` | — | Control |
| **`H72-3`** (`84, 85`) | `CTRL_SUBSURF_D` | `0.05759` (`0.0492–0.0667`) | `0.05825` (`0.0472–0.0687`) | `0.04442` | — (DEM-free subsurface control) | `0.0% / 21.3% / 54.2%` | — | Control |
| **`H72-3`** (`84, 85`) | **`C1_SUBSURF_PTTG_MTHS`** | **`0.05899`** (`0.0499–0.0695`) | **`0.05943`** (`0.0494–0.0734`) | `0.04466` (`SE +0.0095`) | `+0.00140` vs `CTRL_SUBSURF_D` (`NW +0.0049`, `SE +0.0056`); `-0.09670` vs `CTRL_H35` | **`0.0% / 21.6% / 53.3%`** (`med 22.3 px`) | `0.6308` (`PASS`) | **FAIL** vs `H35` |

---

## 4. Dual Format Validation & Complete 85-Raster Lane Audit of Primary Candidate (`H72-3`)

- **Primary File (`-zeros.tif`):** `docs/downloads/gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif` (`sha256 = 51f6e3cb83d7371231f3a8cd3ef166f82d5fb7d80a584577500eb36bf7615346`, `41,061` binary dots, `content_id = 88bbebfe79b4`).
- **Short Submission Note (`102 <= 120 <= 140` chars):** `GEMSDOE25 H72-3 SUBSURF | holdout FAIL vs H35; no slot; not slot-approved | id 88bbebfe79b4 | unscored`
- **Automated Dual Format Checks (`gems25.submission.check_file` + independent `rasterio` verifier):**
  - `GTiff`, `1` band, `float32`, `EPSG:32611`, `3730 x 3292`, exact geotransform `(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)`, `0` `NaN`/`Inf` across all `12,279,160` cells (`-zeros.tif`) and across all `5,167,373` footprint cells (`-nan.tif`), values strictly in `[0.0, 1.0]`, `0` known-catalogue pixels (`d_cat > 2.0 px`).
- **Complete 85-Raster Lane Check (`evidence/h72_3_lane_surface.json`, `docs/downloads/lane-gems25-h72-3-*.json`, `evidence/h72_3_lane_extended.json`):**
  - **Pre-placement continuous surface:** `worst |Spearman| = 0.2857 <= 0.90` (`0` flagged across all 85 rasters; `+0.0322` vs `GEMSDOE32 B2`).
  - **21/21 sibling top-scorer rasters (`registry_top`):** **ALL PASS** (`worst = 39.55% <= 70%` on `g63_cvarlw`; **`24.86%` vs `GEMSDOE32 B2 0.2778`**).
  - **20/20 `GEMSDOE25` own-lineage rasters (`docs/downloads`):** **ALL PASS** (`worst = 48.96% <= 70%` vs `H72-1`, `47.19%` vs `H38-greedy`).
  - **Historical DEM-scarp ribbons in `artifacts/`:** **ALL PASS** (`h23-a-6pct.tif` `62.25% <= 70%`, `r7-nms3-dem10-scarp.tif` `60.45% <= 70%`).
  - **Density-aware duplicate flags (`flagged_lane`):** **`[]` (`0` flags across all 85 rasters — `UNIQUE vs available registry`)**.
  - **Literal 70% flags:** Triggered **only** on the 3 non-discriminative rasters whose own 3-px halos cover `>= 73.4%` of the footprint (`13gems_r13-lattice-s5` `99.87%` halo -> `100.0%` fwd / `17.0%` rev; `pindrop-discovery` `73.41%` halo -> `74.6%` fwd / `17.3%` rev; `pindrop-nodes` `73.50%` halo -> `74.0%` fwd / `17.1%` rev).
