# 25 · Pre-Registered Hypotheses & Experimental Design (`H66-1` MGD-F × Flank Shield & `H66-2` SGMC-REACT, 2026-10-25)

**Branch / session namespace:** `arena/66ca912a-gemsdoe25` (`H66` prefix prevents naming collisions with parallel branches, `IR-25-PARALLEL-SESSION-COLLISIONS`).  
**Status at commit:** Pre-registered **before any holdout model fit, single-feature holdout AUC computation, or candidate GeoTIFF emission**.  
**Core values:** **Maximize P(Win)** · **Own the Outcome**.

---

## 1. Exhaustive Audit of Prior Tested Ideas & Untapped Pinned Data

Every prior register (`knowledge/03..24`) and codebase module (`src/gems25/*.py`) was audited before formulating this register:

* **Already tested (excluded from repetition):** 5-family `A–E` Resolution V factorial (`knowledge/04`); `H26-0..3` score-ordered Poisson-disk dotting, cross-scarp `K/ThK/UK`, DEM-catalogue strike compatibility, potential-field products (`knowledge/05`); `H27-1` directed tip continuation × scarp (`knowledge/09`); `H28` metric-model calibration & emission spacing/budget sweep (`knowledge/10`); `H30-1` paired-tip relay bridge (`knowledge/11`); `GEM-1/2/3` & `GEM-FUSE1` blind magnetics / isotropic vent distance (`knowledge/15, 18`); `H31-1` flank-shielded sub-scarp concordance (`knowledge/14`); `H31-aniso` anisotropic tip continuation + LiDAR strike coherence + `B=2` (`knowledge/13`); `KDC` `B2` + HGB complement (`knowledge/17, 19`); `H34` / `H35` `RESMAG-FLEX × H27_tip` (`knowledge/18–20`); `CF-1` transverse mag/grav slopes (`knowledge/21`); `XG1` unsigned cross-gradient (`knowledge/21–22`); `H36-TZC` spectral tilt-zero coincidence (`knowledge/21, 23`); `H37-SEIS` seismicity alignment (`knowledge/22–23`); `H37-1 DOC` down-dip lagged ridges & `H37-2 SPR` spring-line density (`knowledge/22–24`); `GMCE-1` gravity–magnetic gradient parallelism & `MSCR-1` multi-scale DEM crest persistence (`knowledge/21–23`, PR #27).
* **Pre-preregistration raw-band hygiene check (zero `labels.tif` / holdout access):**
  * `external/geodawn_extensions_u8.tif` Band 4 (`TMI_up150`) is unused in `features.py`, **but** across the footprint its raw Spearman correlation with `14_tmi.npy` is `0.9838` (`0.9482` on `|∇TMI|`), proving INGENIOUS `tmi` already incorporates the GeoDAWN aeromagnetic compilation. Excluded as a separate hypothesis to avoid collinearity waste.
  * `external/gdr_qfaults_traces.csv` (`1,126` rows) contains trace-centroid attributes of the INGENIOUS Quaternary fault catalogue itself; excluded to prevent hidden-component label leakage (`IR-25-QFAULTS-CSV-LEAKAGE`).
  * **Genuinely unused physical/geochemical/structural signals verified on disk (SHA-256 pinned in `registry/data_manifest.json`):**
    1. `external/gdr_wellspring_in_footprint.csv` ([DOE GDR 1391](https://gdr.openei.org/submissions/1391), DOI `10.15121/1881483`, CC BY 4.0): `features.py` read only `thermalclass == 'Hot'` (`1,994` rows), `temp_c`, and `geothermquartz_c`. It **never** read `geothermcat_c` (`1,185` cation geothermometer samples across `610` unique cells), `geothermchalc_c` (`966` chalcedony geothermometer samples across `570` unique cells), **masked reservoir thermal disequilibrium** `ΔT_cat = geothermcat_c - temp_c` (median `+48.3 °C`, p90 `+106.5 °C`) or `ΔT_chalc = geothermchalc_c - temp_c` (median `+41.9 °C`, p90 `+77.3 °C`), `'Warm'` manifestations (`2,245` rows), or natural `'spring_*'` (`1,958` rows) vs human-drilled `'well_*'` (`24,634` rows).
    2. `external/geodawn_rad_u8.tif` Band 4 (`TC`) and `external/geodawn_extensions_u8.tif` Band 3 (`UTh`): **Efimov (1978) potassic metasomatism $F$-parameter ridge** ($F = K \cdot eU / eTh$) was noted as untried (`H34-4` / `H37-4`) and never implemented.
    3. `external/derived_sgmc_faults_100m_u8.tif` ([USGS Data Series 1052, Horton et al. 2017](https://www.usgs.gov/data/state-geologic-map-compilation-sgmc-geodatabase-conterminous-united-states), DOI `10.5066/F7WH2N65`, CC0 1.0): `83,593` bedrock fault pixels across all four quadrants (`NW 32,742`, `NE 30,751`, `SW 4,155`, `SE 15,945`), never loaded in any `src/gems25/` model.

---

## 2. Ranked Register of 5 Untried Geological Hypotheses (`H66-1` to `H66-5`)

| Rank | ID | Hypothesis & Exact Data Layers | Physical Signature & Why Missing from USGS/INGENIOUS `existing_faults.tif` | Named Non-Fault Mimic Process & How It Differs from All Repo Work | Planning `ΔDTI` Bracket, Cost & Verified Official Free Sources |
|---:|---|---|---|---|---|
| **1** | **`H66-1` (`MGD-F × C`)** | **Masked Geothermometry Disequilibrium (`ΔT_cat`, `ΔT_chalc`, Natural Spring Upflow) + Efimov Potassic-Metasomatism $F$-Ridge × Tip-Preserved Flank Shielding (`C`) on `H35`** — `external/gdr_wellspring_in_footprint.csv` (`geothermcat_c`, `geothermchalc_c`, `temp_c`, `layer`, `thermalclass`; `dist_known_fault_px` strictly excluded), `external/geodawn_rad_u8.tif` (`K`, `TC`), `external/geodawn_extensions_u8.tif` (`UTh`), `H35` (`BDE+7+H27_tip+H34`). | ~39% of Great Basin geothermal systems are **blind** (no mapped Quaternary surface scarp in QFFDB; Faulds & Hinz 2015). Fluids ascending slowly through concealed intrabasin or piedmont fault conduits cool conductively (`temp_c` drops to $18\text{–}45^\circ\text{C}$, invisible to `Hot`-only filters), while Na–K–Ca cation (Fournier & Truesdell 1973) and chalcedony (Fournier 1977) chemical equilibria preserve deep $110\text{–}220^\circ\text{C}$ reservoir temperatures ($\Delta T = T_{\text{geotherm}} - T_{\text{meas}} \gg 0$) and precipitate linear illite/adularia K-metasomatism ($F = K \cdot eU/eTh$ ridges) along unmapped permeable fault traces. Combining with tip-preserved lateral-flank shielding (`d(vis) > 2.5 px` or `tip >= 0.05`) removes `1–2.5 px` scarp-apron false positives on `H35` for the first time. | **Mimic:** Perched meteoric outflow plumes in alkali-rhyolite ash-flow tuffs (primary glass dissolution elevating Na–K–Ca and $K \cdot U/Th$ along unfaulted paleochannels or playa margins). **Difference:** `features.py` never read `geothermcat_c`, `geothermchalc_c`, `Warm` springs, `spring_*` vs `well_*`, `TC`, or Efimov $F$-ridges; `H35` was never paired with tip-preserved flank shielding (`C`) or `min_dist=3.0` (`R=300 m`) Poisson-disk spacing. | **`+0.001` to `+0.006`** HOLDOUT-DTI; ~8 min / stage on 2 CPUs. Sources: [DOE GDR 1391](https://gdr.openei.org/submissions/1391) (`10.15121/1881483`, CC BY 4.0); [USGS GeoDAWN](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) (`10.5066/P93LGLVQ`). Pinned & restored locally. |
| **2** | **`H66-2` (`SGMC-REACT`)** | **Neotectonically Reactivated Pre-Quaternary Bedrock Faults (`USGS SGMC × 3DEP LiDAR Scarp Strike × Geodetic Strain`)** — `external/derived_sgmc_faults_100m_u8.tif` × `L_step_max`, `L_coh100`, `L_strike` (`external/lidar_scarp_features_u8.tif`) × `geod_2ndinv` (Band 4) & `iso_grav_anom` (Band 13). | Pre-Quaternary/Tertiary bedrock faults mapped at 1:50k–1:500k in SGMC lack mapped `<1.6 Ma` alluvial scarps in QFFDB (`existing_faults.tif`). Where an SGMC bedrock fault is **actively loaded by modern GPS strain (`geod_2ndinv`) and shares strike with a subtle 1 m 3DEP LiDAR scarp**, it marks a reactivated range-front or intrabasin bedrock fault missed by QFFDB. Gating strictly by modern scarp/strain suppresses the ~85–90% of inactive Paleozoic/Mesozoic Sevier/Antler thrust traces that caused raw SGMC emissions to score `0.0360` (`16GEMSDOE`). | **Mimic:** Differential erosion along inactive dipping Mesozoic thrust sheets or welded-tuff hogbacks producing fault-line scarps without Quaternary slip; plus **compilation-overlap proxy risk (`IR-25-SGMC-PROXY-CONTAMINATION`)** where SGMC and QFFDB share regional map corridors. **Difference:** `derived_sgmc_faults_100m_u8.tif` has never been loaded in `src/gems25/`; we explicitly separate physics-gated reactivation (`SGMC_REACT_ONLY`) from ungated proximity (`SGMC_ALL3`). | **`+0.001` to `+0.010`** proxy (`0.000` to `+0.005` live transfer after compilation caveat); ~6 min on 2 CPUs. Sources: [USGS DS 1052 SGMC](https://www.usgs.gov/data/state-geologic-map-compilation-sgmc-geodatabase-conterminous-united-states) (`10.5066/F7WH2N65`, CC0 1.0); [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) (public domain). Pinned & restored locally. |
| **3** | **`H66-3` (`VENT-DIKE`)** | **Quaternary Volcanic Vent-Pair Fissure Corridor × Magnetic Dike Alignment** — `external/gdr_volcanic_vents_in_footprint.csv` (`21` vents) × `02_rtp.npy` Hessian strike × `08_geod_dilaterate.npy`. | Monogenetic Quaternary basaltic vents ascend along $\sigma_3$-perpendicular dilational normal/transtensional dike-fault corridors whose young lava flows bury surface scarps (Parsons & Thompson 1991). | **Mimic:** Unfaulted basaltic lava-flow lobe margins in paleovalleys. **Difference:** `GEM-2` used isotropic `exp(-d_vent/6 px) * |∇cond|`; directional vent-pair corridor alignment with RTP magnetic ridges is untried. Ranked #3 because 21 vents cover `<5%` of the footprint. | **`-0.0005` to `+0.002`** HOLDOUT-DTI; ~4 min. Source: [DOE GDR 1391](https://gdr.openei.org/submissions/1391) (`10.15121/1881483`, CC BY 4.0). |
| **4** | **`H66-4` (`SG-STRAT`)** | **Signed 3-Field Half-Graben Polarity Concordance (`sgn(∂_n z) == -sgn(∂_n g_iso) == sgn(∂_n D_base)`)** — `12_det_elev.npy`, `13_iso_grav_anom.npy`, `15_depth_to_base_surf.npy`, `L_strike`. | Normal-fault hanging walls drop surface elevation, drop isostatic gravity (low-density basin fill), and deepen conductive basement in the **same** cross-strike direction. | **Mimic:** Unfaulted alluvial-fan / pediment depositional onlap wedges thickening basinward. **Difference:** `XG1`, `CF-1`, and `H37-DOC` used unsigned magnitudes or lags; signed 3-field polarity concordance is untried. | **`0.000` to `+0.003`** HOLDOUT-DTI; ~5 min. Sources: INGENIOUS competition raster ([GDR 1391](https://gdr.openei.org/submissions/1391)). |
| **5** | **`H66-5` (`PALEO-HF-EXT`)** | **Paleo-Geothermal Sinter/Travertine Horizons × Residual Conductive Heat Flow** — `paleo_geothermal_regional.zip` + USGS Great Basin heat-flow wells. | Fossil siliceous sinter and travertine precipitate at water-table intersections of permeable fault conduits even where modern surface scarps are eroded or buried. | **Mimic:** Pleistocene Lake Lahontan shoreline tufa (`~1,330 m` contour). **Difference & blocker:** Registered in `knowledge/09` (`H27-3/4`), blocked in this sandbox (`github.com/pypi/npm` network allowlist only). | **`+0.002` to `+0.008`** once fetched on a networked runner. Sources: [DOE GDR 1391](https://gdr.openei.org/submissions/1391) (CC BY 4.0); [USGS Heat Flow `10.5066/P9BZPVUC`](https://www.sciencebase.gov/catalog/item/62da2accd34e2842e52c5576) (CC0). |

---

## 3. Pre-Registered Experimental Sequence (Within 3-Experiment / 2-Hour Budget)

### Experiment 1: `H66-1` $2^2$ Factorial (`G` × `C`) on Untouched Screen Draws `50, 51`

* **Shared holdout evaluator:** `gems25.holdout.Holdout(foot, labels, hide_frac=0.20)` (`COLLAR_PX=15`, 4 spatial quadrants `NW, NE, SW, SE`, 8 `(fold, draw)` cells) scored by `gems25.metric.dti_binary` (`alpha=0.2, beta=0.8, R=3.0 px = 300 m`) via `Cell.evaluate`.
* **Factor `G` (`4` static catalogue-free columns in `[0, 1]`, stored in `work_dir()/h66_mgd_columns.npy`):**
  1. `H66_mgd_cat_excess`: From `gdr_wellspring_in_footprint.csv` (`dist_known_fault_px` never read), $\Delta T_{\text{cat}} = \text{clip}(T_{\text{geothermcat}} - T_{\text{meas}}, 0, 180) \cdot w_{\text{spring}}$ ($w_{\text{spring}} = 1.5$ if `layer` starts with `"spring_"`, else $1.0$), cellwise maximum on the $3730 \times 3292$ grid, smoothed by a peak-normalized Gaussian lateral-outflow kernel ($\sigma = 15\text{ px} = 1.5\text{ km}$), $\log(1 + \cdot)$, footprint $(p_1, p_{99})$ scaled to $[0, 1]$.
  2. `H66_mgd_chalc_excess`: Identical operator for $\Delta T_{\text{chalc}} = \text{clip}(T_{\text{geothermchalc}} - T_{\text{meas}}, 0, 150) \cdot w_{\text{spring}}$, smoothed at $\sigma = 15\text{ px}$, $\log(1 + \cdot)$, $(p_1, p_{99})$ scaled to $[0, 1]$.
  3. `H66_spring_upflow_prox`: $\exp(-d(x, M_{\text{upflow}}) / 20.0\text{ px})$ where $M_{\text{upflow}}$ marks footprint cells with `layer` starting with `"spring_"` or `thermalclass.strip() in {"Hot", "Warm"}`.
  4. `H66_efimov_f_ridge`: Efimov potassic metasomatism index $F = (K/255) \cdot (UTh/255)$ (nearest-filled from `geodawn_rad_u8.tif` Band 1 and `geodawn_extensions_u8.tif` Band 3), localized via `ridge_strength(F, sigma=2.0)` $\times (0.5 + 0.5 \cdot \text{norm}(|\nabla TC|_{\sigma=1.5}))$ (`TC` = `geodawn_rad_u8.tif` Band 4), $(p_1, p_{99})$ scaled to $[0, 1]$.
* **Factor `C` (Tip-preserved lateral-flank shielding + `R=3.0 px` kernel-radius Poisson-disk emission):**
  * Candidate budget fixed across all $2^2$ arms at `kfrac = 0.035` (`k = round(0.035 * dom_c.sum())`), `score_ordered_dots(..., min_dist=3.0)` (`NN >= 3.0 px = 300 m`, eliminating sub-kernel diagonal `2.83 px` pairs).
  * `C = -1`: unshielded `cell.candidates(p, k)`.
  * `C = +1`: `cell.candidates_flank_shielded(p, k, flank_radius_px=2.5, tip_preserve_threshold=0.05)` computed strictly from `draw.visible` and `cell.tip_c`.
* **Arms evaluated in every `(fold, draw)` cell:**
  * `CTRL_BDE7`: `BDE + 7 extras` (`78` cols), `C = -1`, `sapd3.0`.
  * `CTRL_H35_24`: Exact `H35` champion recipe (`BDE + 7 + H27_tip + H34` = `82` cols, `C = -1`, `sapd2.4, kfrac=0.035` — zero extra fit, evaluated from `G0_C0` probabilities so `G1_C1` cannot win by weakening `H35`!).
  * `G0_C0`: `H35` (`82` cols), `C = -1`, `sapd3.0`.
  * `G1_C0`: `H35 + 4 G cols` (`86` cols), `C = -1`, `sapd3.0`.
  * `G0_C1`: `H35` (`82` cols), `C = +1`, `sapd3.0`.
  * `G1_C1` (**PRIMARY CANDIDATE ARM**): `H35 + 4 G cols` (`86` cols), `C = +1`, `sapd3.0`.
* **Frozen Screen Gate (`H66-1`, draws `50, 51`):**
  1. **Leakage Canary:** Every one of the 4 `G` columns tested alone in every cell has `max(AUC, 1 - AUC) <= 0.90`.
  2. **Paired Holdout Gate vs Pointwise Best Same-Run Control (`BEST_CTRL` = per-fold max of `CTRL_BDE7`, `CTRL_H35_24`, `G0_C0`):**
     * 4-fold mean paired gain `mean(G1_C1 - BEST_CTRL) > +0.0010` DTI,
     * `>= 3/4` spatial folds strictly positive,
     * `min(G1_C1 - BEST_CTRL) >= -0.010` DTI,
     * mean hug-share delta `<= +0.10`.
* **Frozen Confirmation Rule (would count as Experiment 2 of 3):**
  * **If and only if** `H66-1` (`G1_C1`) passes the screen gate on draws `50, 51`, run frozen confirmation on untouched draws `52, 53` with identical parameters and gate. If `H66-1` fails screen, do **not** run confirmation draws `52, 53`.

### Next Experiment in Sequence (Experiment 2 of 3 if `H66-1` fails screen, or Experiment 3 of 3 if `H66-1` runs confirmation): `H66-2` (`SGMC-REACT`) on Untouched Draws `54, 55`

* **3 static catalogue-free SGMC columns (`work_dir()/h66_sgmc_columns.npy`, zero `labels.tif` input):**
  1. `H66_sgmc_prox4`: $\exp(-d(x, \text{SGMC}) / 4.0\text{ px})$ (`400 m` scale matching 1:250k–1:500k map positional error).
  2. `H66_sgmc_scarp_compat`: $\exp(-d(x, \text{SGMC}) / 4.0) \cdot \max(0, \cos 2(\theta_{\text{SGMC}} - \theta_{\text{LiDAR}})) \cdot L_{\text{coh100}} \cdot \text{norm}(L_{\text{step\_max}})$.
  3. `H66_sgmc_strain_react`: $\exp(-d(x, \text{SGMC}) / 4.0) \cdot \text{norm}(\text{geod\_2ndinv}) \cdot \text{norm}(|\nabla \text{iso\_grav\_anom}|_{\sigma=1.5})$.
* **Arms in every `(fold, draw)` cell on draws `54, 55`:**
  * `CTRL_H35_24`: Exact `H35` (`sapd2.4, kfrac=0.035, C=-1`).
  * `CTRL_H35_C1`: `H35 + Factor C` (`sapd3.0, kfrac=0.035, C=+1`).
  * `SGMC_REACT_ONLY` (**PRIMARY CANDIDATE ARM**): `H35 + Factor C` + `[H66_sgmc_scarp_compat, H66_sgmc_strain_react]` (`84` cols, `sapd3.0, C=+1`), deliberately excluding raw `H66_sgmc_prox4`.
  * `SGMC_ALL3` (ablation diagnostic): `H35 + Factor C` + all 3 SGMC columns (`85` cols, `sapd3.0, C=+1`) to measure compilation-overlap inflation vs physics-gated reactivation (`IR-25-SGMC-PROXY-CONTAMINATION`).
* **Frozen Gate (`H66-2`, draws `54, 55`):**
  * All 3 SGMC columns pass single-feature canary `max(AUC, 1 - AUC) <= 0.90`;
  * `SGMC_REACT_ONLY` beats `max(CTRL_H35_24, CTRL_H35_C1)` per fold by `> +0.0010` mean DTI, `>= 3/4` folds positive, `worst >= -0.010`, `hug_delta <= +0.10`.
  * Even if `H66-2` passes screen (and confirmation on `56, 57` if budget remains), `IR-25-SGMC-PROXY-CONTAMINATION` is disclosed so no slot is spent without owner review.

---

## 4. Frozen Unique Full-Catalogue GeoTIFF & Verdict Rule

1. **Which `H66` specification is built into the session's unique GeoTIFF:**
   * If `H66-1` (`G1_C1`) passes both screen (`50, 51`) and confirmation (`52, 53`), build from `H66-1` (`G1_C1`).
   * Otherwise, if neither experiment clears a two-stage confirmation within the 3-experiment budget, build the mandatory unique research GeoTIFF from **`H66-1` (`G1_C1`)** (pure catalogue-free geochemical/alteration + tip-preserved `C=1` + `sapd3.0`, free of SGMC compilation-overlap bias) trained once on full `labels.tif` with deterministic `random_state = 20261025`.
2. **Programmatic validation & lane checks (zero human intervention):**
   * Write both `-zeros.tif` (`outside="zero"`, primary) and `-nan.tif` (`outside="nan"`, twin) + `.zip` via `src/gems25/submission.py::write_submission`.
   * Run `gems25.submission.check_file` AND `scripts/verify_candidate_independent.py` (verifying `EPSG:32611`, `3730x3292`, `100 m` transform, `5,167,373` finite `[0, 1]` footprint pixels, zero `NaN` in `-zeros.tif`, zero catalogue-pixel emissions).
   * Run `scripts/check_lane_duplicates.py`, `scripts/check_lane_surface.py`, and `scripts/lane_check_extended.py`.
3. **Verdict & slot rule:**
   * Under repository-wide policy (`tests/test_repo_integrity.py`, `IR-25-LANE-DENSITY`, Protocol #1 & #6), `slot_approved` remains `false`; if either the two-stage holdout confirmation gate OR the literal strict lane check (`13gems` 5-px lattice covers `99.87%` of the footprint within `3 px`) fails, the Run Card verdict and front-page status are set automatically to `negative` / `DO NOT SUBMIT` (`OK to download: YES`, `OK to spend a weekly slot: NO`).
