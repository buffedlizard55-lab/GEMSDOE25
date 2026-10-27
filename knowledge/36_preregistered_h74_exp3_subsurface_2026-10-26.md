# 36 · Pre-Registration Addendum: Experiment 3 (`3/3`) — Topography-Free Subsurface `H74_SUBSURF` on Virgin Draws `112, 113` — 2026-10-26

* **Session branch:** `arena/3a62ee32-gemsdoe25` (following `knowledge/35_preregistered_h74_rmps_bw_2026-10-26.md`, commit `af10a19`).
* **Pre-registration status:** Frozen and committed **before** implementing or running Experiment 3 (`3 of 3` hard experiment cap). Zero reuse of draws `110, 111`.

---

## 1. Readout of Experiments 1–2 (`draws 110, 111`) & Why `H74_BLIND` (`ABCD`) Stopped at Staging

1. **Key scientific findings from Experiments 1 & 2 (`evidence/h74_joint_analysis.json`, all `688` leakage canaries `<= 0.8259 <= 0.90`):**
   * **Confirmation of the `25-km` block-withheld hypothesis (`knowledge/33` §4, `knowledge/34` §Next Action #3):** Moving from standard `20%` component withholding (`Exp 1`, `22,359` withheld occurrences, median `d_vis = 9.33 px`, `20.89%` at `d_vis > 20 px`) to `25-km` spatial-block component withholding (`Exp 2`, `H74-BW`, `27,455` withheld occurrences, median `d_vis = 66.91 px`, `87.62%` at `d_vis > 20 px`) **collapsed `CTRL_H35`'s apparent apron advantage over `CTRL_BLIND` by `62.9%`** (`+0.06353` $\to$ `+0.02356`), dropping `CTRL_H35` from `0.15116` to `0.12582` while raising `H74_BLIND` from `0.09156` to `0.10464` (with `H74_BLIND` beating `CTRL_H35` outright by `+0.02343` in Quadrant SE).
   * **Both `H74_APRON` and `H74_BLIND` passed Gate G2 on `25-km` block-withheld `H74-BW` (`Exp 2`):** `H74_BLIND` beat `CTRL_BLIND` by `+0.00237` pooled `HOLDOUT-DTI` (`3/4` folds positive; `+0.00674` NE, `+0.00165` SW, `+0.00409` SE; also `+0.00394` pooled on `Exp 1` with `+0.01903` in volcanic-heavy NE), and `H74_APRON` beat `CTRL_H35` by `+0.00038` (`3/4` folds positive). Neither passed Slot Gate G1 (`>= +0.0020` over `CTRL_H35` on standard `Holdout`), so **zero weekly slots are authorized**.
2. **Automated staging stop on `H74_BLIND` (`ABCD`, `evidence/h74_blind_abcd_stopped_lane.json`):**
   * Pre-placement continuous surface passed all `101` registry rasters (`worst |Spearman| = 0.2136 <= 0.90`).
   * However, final `37,654` submodular dots on `ABCD` (`78` cols including `28` `Family B` DEM / 1-m LiDAR scarp columns) triggered the pre-registered density-aware duplicate stop (`> 70%` 3-px dot overlap) on **two `Family B`-driven rasters**: `h23-a-6pct.tif` (`76.88%`) and `gems25-h72-mbsp-mtg-catfree-b2-37654` (`74.52%`). Per `knowledge/35` §4, `build_h74_candidate.py` **halted immediately in staging without writing any GeoTIFF to `docs/downloads/`**.
   * **Physical diagnosis (`IR-25-LIDAR-BLIND-CONVERGENCE-20261026`):** When `Family B` (`1-m` LiDAR `L_step_max`, `L_ex_max`, `B_slope`) is included alongside subsurface geophysical columns in a catalogue-free HGB, exposed scarp splits dominate `>74%` of top-scoring ridges, causing any two `Family B` blind HGBs to converge onto the same exposed fault scarps. Meanwhile, **all four `H74-1` (`RMPS-BFP`) operators are 100% topography-free crustal geophysical/geomechanical observables (`Families A, C, D`)** designed specifically for concealed basins and volcanic plateaus where `Family B` scarps are absent!

---

## 2. Frozen Specification of Experiment 3 (`3 of 3` Final Budget) — `H74_SUBSURF` on Virgin Draws `112, 113`

* **Evaluation split:** `25-km` spatial-block component-withheld selector (`H74-BW`, `draw_block25km`, `block_px = 250`) on **fresh virgin draws `112, 113`** (`4 folds × 2 draws = 8 cells/arm`; `evidence/h74_exp3_subsurf_bw25km`). Draws `110, 111` are never touched again.
* **Three paired arms recomputed in the same run (`IR-25-COMPARATOR-DRIFT`):**
  1. **`CTRL_H35` (`59` cols):** Exact incumbent (`BDE + EXTRAS + H27_tip + H34`, `sapd2.4` emission).
  2. **`CTRL_SUBSURF` (`43` static topography-free & catalogue-free cols):** `ACD` (`36` static potential-field, geodetic/seismic, radiometric/MT/spring cols; **zero** `Family B` DEM/LiDAR, **zero** `Family E` catalogue) + non-DEM add-ons (`X1_K, X1_ThK, X1_UK, X3_gm` = `4` cols; excluding DEM-based `X2_compat, X2_compat_coh, X3_gd`) + `H34` (`3` cols), emitted on `d_vis > 2.0 px` via shared `gems25.greedy.greedy_dots` (`ridge_nms(1.0)`, `kfrac = 0.035`, `n_hat = 0.25 * |known_c & dom_c|`, `max_dots` scaled to `37,654` full-footprint budget).
  3. **`H74_SUBSURF` (`47` static topography-free & catalogue-free cols):** `CTRL_SUBSURF + H74_RMPS` (`+4` cols: `H74_remanent_skew_crest`, `H74_biharmonic_plate_hinge`, `H74_simpson_pore_crit`, `H74_laplace_harmonic_defect`), identical `B2`-hygiene `greedy_dots` emission.
* **Leakage canary:** `gems25.validation.feature_canary` (`cap = 0.90`) on every column in every `(fold, draw)` cell.
* **Subsurface causal hypothesis gate (`G3_SUBSURF`):** `H74_SUBSURF` beats `CTRL_SUBSURF` on `25-km` block-withheld `HOLDOUT-DTI` (`paired_gain > 0` in `>= 3/4` folds, zero canary failures). Because `H74_SUBSURF` omits `Family B` exposed LiDAR scarps, it is **not** expected to beat `CTRL_H35` overall and **cannot** unlock a weekly submission slot (`slot_approved = False` unconditionally).
* **Full-Footprint Unique Research GeoTIFF Rule (Strict Fail-Closed):**
  * Build the 4-quadrant spatially blocked Out-of-Fold (`LOQO`, `seeds = (20261101, 20261102)`) full-footprint `H74_SUBSURF` surface (`47` static subsurface columns, zero `Family B`, zero `Family E`) and `B2`-hygiene `greedy_dots` (`max_dots = 37,654`) **in staging first**.
  * Publish content-addressed `-zeros.tif`, `-nan.tif`, and `.zip` to `docs/downloads/` **ONLY IF** pre-placement continuous surface passes `|Spearman| <= 0.90` across all `101` rasters AND final binary dots pass density-aware uniqueness (`flagged_lane == []` in `check_lane_duplicates.py`, `external_sparse.lane_pass == True`, and `own_lineage.lane_pass == True` across all sparse, focus-winner, and own-lineage rasters, including `h23-a-6pct.tif`, `H72-CF`, and `H72-3-subsurf`)!
  * If ANY `flagged_lane` duplicate remains even on `H74_SUBSURF`, **halt in staging and write zero `.tif` files to `docs/downloads/`**.
  * If `flagged_lane == []` clears, publish the validated `[0, 1]` GeoTIFF with explicit `lane_clear = False` (reporting literal `r13-lattice-s5` + `pindrop` dense-halo flags transparently), `verdict = "negative"`, `slot_approved = False`, `ok_to_download = True` (research/inspection only), `ok_to_submit_slot = False` (`DO NOT SUBMIT`).
