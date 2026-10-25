# 22 — H36 Outcomes, 9-Site Forensics, Physical Bug Audit, and Zero-Topography Submodular GeoTIFF (`2026-10-25`)

**Session branch:** `arena/867f087d-gemsdoe25`  
**Pre-registration (committed before any experiment):** [`knowledge/21_preregistered_h36_spigm_submodular_2026-10-25.md`](21_preregistered_h36_spigm_submodular_2026-10-25.md) (`2c5e873`, frozen runner/analyzer commit `1138a18`)  
**Protocol budget:** `3 / 3` experiments used (`E1` screen on draws `20,21`; `E2` confirmation on draws `22,23`; `E3` 4-fold LOQO full-footprint build + 47-raster lane audit + dual automated `[0, 1]` portal validation), `< 35 min` compute total (`<= 2 h` cap), `0` post-hoc parameter tweaks.  
**Run Card:** [`registry/run_card_h36_2026-10-25.json`](../registry/run_card_h36_2026-10-25.json)

---

## 1. Executive Answer: Why `GEMSDOE32` (`0.2778`) Beat Every Other Focus Site — and What Can Beat `0.2778`

### 1.1 Exact pixel-level lineage across `GEMSDOE24..36` (`COMPUTED` on SHA-256-pinned rasters + `OWNER-REPORTED` unverified scores)

Every competition score below is an **owner-reported, unverified claim** (no `drivendata.org` page or organizer receipt is accessed under `AGENTS.md` Rule 3). Every pixel relation is **computed locally** on the SHA-256-pinned GeoTIFFs (`evidence/focus_sites_forensics.json`, `data/scored/*.tif`, `data/registry_top/*.tif`):

| Rank in focus set | Site | File / ID | Owner-reported score (unverified) | Emitted pixels (`>0`) | Exact mathematical relation (`COMPUTED`) |
|---:|---|---|---:|---:|---|
| 1 | `GEMSDOE32` | `h33-h33-2-b2-…-e5eb6e7e-zeros.tif` (`c55bafc4…`) | **`0.2778`** | `37,654` | **`D2.8 & (d(catalogue) > 2.0 px)`** (`0` pixel XOR difference vs deleting the `100–200 m` collar from `B1`) |
| 2 | `GEMSDOE36` | `gems36-h36-3-pinns-…-zeros.tif` | `0.2750` | `38,854` | Exact superset `B2 ∪ Δ_1200` (`37,654 + 1,200` additive PINN dots; implied marginal credit `~0.0365/dot < τ = 0.0588`) |
| 3 | `GEMSDOE28` / `31` | `gems28-h27-4-…` / `gems31-h31-2-…` (`B1` / `solo`) | `0.2708` | `40,199` | **`D2.8 & (d(catalogue) > 1.0 px)`** (deletes `3,891` 100 m collar dots from `D2.8`) |
| 4 | `GEMSDOE33` | `gems33-h33-4-b15-…` (`B1.5`) | `0.2632` | `41,865` | Intermediate `1.5 px` (`150 m`) catalogue collar prune |
| 5 | `GEMSDOE25` / `30` | `…-d2-8-…-e56ea318af89-nan.tif` (`D2.8`) | `0.2600` | `44,090` | `dot_thin(H19-5, min_dist = 2.4 px)` (greedy coordinate-order Poisson disk on binary `H19-5`) |
| 6 | `GEMSDOE24` | `…-d1-5-…-989f59505db1-nan.tif` (`D1.5`) | `0.2477` | `60,069` | `dot_thin(H19-5, min_dist = 1.5 px)` |
| 7 | `GEMSDOE27` | `gems27-…` | `0.2449` | `61,328` | Near-`D1.5` thinning of `H19-5` |
| — | `19GEMSDOE` (ancestor) | `19gems_…_h19-5_…` (`80d47e1ab2ee`) | `0.1922` | `121,131` | Solid ridge band (`96.9%–100%` superset of every `>= 0.2449` focus-site file above) |
| — | `GEMSDOE70` (independent lane) | `gems70-…` (`d0e41ce9…`) | `0.2478` | `37,654` | **Non-`H19-5` independent lane**: 4-fold OOF dual-population HGB + exact 300 m submodular cover (`62%` within 3 px of `H19-5`, only `14.3%` pixel overlap) |

### 1.2 Three quantitative mechanisms behind `0.2778`

1. **Asymmetric Tversky (`α = 0.2, β = 0.8`) + `R = 300 m` max-pool saturation (`COMPUTED`):**  
   $$\mathrm{DTI}(\hat Y, G) = \frac{\mathrm{TP}_w}{0.2\,(\mathrm{TP}_w + \mathrm{FP}_w) + 0.8\,|G|}, \qquad \tau(D) = \frac{0.2\,D}{1 - 0.8\,D}.$$
   Because `dilate_tversky` takes a **pointwise `maximum_filter`**, a single binary `1.0` dot at distance `d_px ∈ {0, 1, 2}` covers a `29`-pixel disk with kernel weights `(1.000, 0.667, 0.528, 0.333, 0.257, 0.057)` summing to **`12.405` weighted pixel-equivalents**, while paying `FP_w <= 1.0` (`0` if `k_G = 1.0`). Solid `H19-5` (`121,131` px) wastes `~69%` of its `FP` mass re-covering truth pixels already saturated by adjacent dots (`0.1922 -> 0.2600` upon `2.4 px` thinning).
2. **200 m expert mapping-shadow depletion (`INFERENCE` conditional on reported scores):**  
   Organizer staff confirmed mapped USGS/INGENIOUS pixels are masked (`0` TP, `0` FP). Furthermore, when USGS/NBMG geologists digitise a Quaternary scarp on aerial/LiDAR imagery, any parallel strand within `100–200 m` is already captured or sits inside the `100 m` rasterisation halo of the mapped trace. Conditional on `0.2600 -> 0.2708 -> 0.2778` (`|G| ≈ 12,500–13,500` px):
   - Deleting `3,891` dots in `0 < d(cat) <= 100 m` (`D2.8 -> B1`) removes dots with implied marginal credit **`~0.0085 / dot` `<<` `τ(0.2600) = 0.0537`**.
   - Deleting `2,545` dots in `100 < d(cat) <= 200 m` (`B1 -> B2`) removes dots with implied marginal credit **`~0.0110 / dot` `<<` `τ(0.2708) = 0.0568`**.
3. **Why `H19-5` pruning alone hits a hard ceiling near `~0.283` (`COMPUTED`):**  
   At `D = 0.2778`, break-even marginal credit is **`τ(0.2778) = 0.05883 / dot`**, whereas `B2`'s average dot earns `~0.1306 / dot`. No further thinning or collar deletion of `H19-5` can reach the owner-reported `#5` (`0.3195`) or `#1` (`0.4413`, `IR-25-LEADERBOARD-CONFLICT`). Reaching `> 0.30` requires **replacing scarp-only false positives (erosional range-front facets, Lake Lahontan shorelines, volcanic flow margins) with buried/blind hydrothermal structures under basin cover** AND **replacing greedy spacing with exact submodular marginal-credit allocation**.

---

## 2. Two Previously Undiagnosed Repository Bugs Discovered and Verified (`COMPUTED`)

1. **`IR-25-POTENTIAL-FIELD-UNIT-MISMATCH` (`src/gems25/features.py` `Family A`):**
   - Direct physical inspection of `data/training_features.tif` / `data/work/bands/` revealed that band `15_tmi_hg` (`p50 = 1.678`, `p99 = 12.66`) equals **`200.0 × ||∇_h TMI||`** (`nT per 200 m` central-difference span, median ratio vs central difference of `07_tmi_rtp` is `200.1`), whereas band `09_tmi_vg` (`p50 = 0.0156`, `p99 = 0.1456`) is in **`nT / m`**.
   - Consequently, `features.py` lines 69–70 computed `asig = sqrt(tmi_hg² + tmi_vg²)` where `tmi_hg²` dominates `tmi_vg²` by **`40,000×`**, turning `A_mag_as` into `|tmi_hg|` and making `A_mag_tilt = atan2(tmi_vg, |tmi_hg|)` `200×` too small (`~0.009 rad` instead of physical `~1.08 rad`).
   - Simultaneously, band `18_iso_grav_anom_hg` (`min = -3.997`, `p50 = +0.025`, `max = +4.864`) is signed and correlates `r = +0.9459` with `∂g/∂x` and `+0.3576` with `∂g/∂y` — a **directional `~N110°E` derivative**, blinding `A_grav_hg` to `N110°E` transfer/accommodation faults.
   - **Clean fix without invalidating pinned `static_ABCD.npy`:** `src/gems25/h36.py` computes unit-consistent local potential-field source wavenumber `k_mag = sqrt((∂TMI_rtp/∂x)² + (∂TMI_rtp/∂y)² + (100 · tmi_vg)²) / (|TMI_rtp| + ε)` (`SPI_mag`, Thurston & Smith 1997) and omnidirectional `||∇_h g_iso||` (`SPI_grav`) directly from `07_tmi_rtp`, `09_tmi_vg`, and `17_iso_grav_anom`.
2. **`IR-25-STUDY-AREA-VALID-PIXELS-CORRECTION`:**
   - `registry/irregularities.json` previously claimed only `1,154,738` pixels (`11,547 km²`) had valid features across all 19 bands. Direct byte-level verification on `data/training_features.tif` proves **`5,164,300` of `5,167,373` footprint pixels (`99.941%`) have all 19 bands finite** (`51,643.00 km²`), and the full `3730 × 3292` grid is `122,791.60 km²`. Only 3DEP 1 m LiDAR (`L_valid`, `data/external/`) is restricted (`3,894,460` valid px inside footprint = `75.37%`; `1,272,913` footprint px = `24.63%` have `L_valid = 0`).

---

## 3. Ranked Untried Geological Hypotheses (`knowledge/21`)

All five hypotheses were pre-registered before any experiment in [`knowledge/21_preregistered_h36_spigm_submodular_2026-10-25.md`](21_preregistered_h36_spigm_submodular_2026-10-25.md):

| Rank | ID | Hypothesis | Named layers | Expected `Δ HOLDOUT-DTI` (planning bracket, NOT a score) | Compute cost | Status |
|---:|---|---|---|---|---|---|
| **1** | **`H36-1`** | **Unit-Corrected `SPI-GM` Subsurface Blind-Fault Expert × Elkan Prior-Shift Calibration × Exact 300 m Submodular Marginal-Credit Cover (`Submod300`)** | `07_tmi_rtp`, `09_tmi_vg`, `17_iso_grav_anom`, `12_earthquakes`, `13_heatflow`, `14_mt2000m`, `16_dem_conductive_base`, `C_heat..C_mt_grad`, `E_d_fault..E_dens_r50` (+ `BDE+7` PoE fusion arm) | `+0.002` to `+0.010` | ~23 min (`E1+E2+E3`) | **Tested (`E1`, `E2`, `E3` complete)** |
| 2 | `H36-2` | Curvature-Gravity Euler Deconvolution (`SI = 0.5`) Fault-Contact Depth-Clustering (`Euler-GravMag`) | `07_tmi_rtp`, `09_tmi_vg`, `17_iso_grav_anom`, `16_dem_conductive_base` | `+0.001` to `+0.006` | ~18 min | Registered only; untried |
| 3 | `H36-3` | Hydrothermal Upflow Plume Conduit Junctions (`Heat × MT-2km × CondBase-Cupola × Geothermometer`) | `13_heatflow`, `14_mt2000m`, `16_dem_conductive_base`, GDR `1391` geothermometry (obtainable via GitHub mirror; direct `gdr.openei.org` blocked here) | `+0.001` to `+0.005` | ~15 min | Registered only; untried |
| 4 | `H36-4` | Seismogenic-to-Aseismic Brittle Transition Relay Corridors (`Seis-MT-Bridge`) | `12_earthquakes`, `14_mt2000m`, fold-clean `E` | `+0.000` to `+0.004` | ~15 min | Registered only; untried |
| 5 | `H36-5` | Airborne Radiometric `K/(Th+ε)` Potassium-Adularia Metasomatic Fault-Valve Alteration (`RadK-FaultValve`) | `R_K`, `R_Th`, `R_U`, `13_heatflow`, `16_dem_conductive_base` | `+0.000` to `+0.004` | ~15 min | Registered only; untried |

---

## 4. Pre-Registered Spatial Holdout Outcomes (`E1` + `E2`, Untouched Draws `20..23`)

**Evaluator label:** `HOLDOUT-DTI` via `gems25.holdout.Holdout(v1, 4-quadrant, collar=15px, hide_frac=0.20, erode=12) + gems25.metric.dti_binary(alpha=0.2, beta=0.8, R=3.0px)` (`evidence/h36_screen/analysis.json`, `evidence/h36_confirm/analysis.json`, `evidence/h36_pooled_16cells.json`).
- **Withheld positives:** `E1` (`draws 20,21`, `8` cells) = **`22,232`** (`11,172` + `11,060`); `E2` (`draws 22,23`, `8` cells) = **`22,391`** (`10,893` + `11,498`); 16-cell combined = **`44,623`**.
- **Protocol Rule 4 — Standalone Feature Leakage Canary:** **8 / 8 features PASS** (`max_canary_auc = 0.6503 <= 0.90`: `H27_tip 0.6355`, `H36_burial_regime 0.6503`, `H36_chem_diseq 0.6088`, `H36_gm_strike_concord 0.5317`, `H36_grav_spi_k 0.5465`, `H36_mag_spi_k 0.5726`, `H36_transtension_iq 0.5809`, `H36_up150_persist 0.5703`).

### 4.1 Complete 16-cell (`draws 20..23`) `HOLDOUT-DTI` summary

| Arm | Description | `E1` (`draws 20,21`) Pooled `HOLDOUT-DTI` (`n_pos=22,232`) | `E2` (`draws 22,23`) Pooled `HOLDOUT-DTI` (`n_pos=22,391`) | 16-Cell Pooled `HOLDOUT-DTI` (`95% CI`, `n_pos=44,623`) | 16-Cell Mean Fold `HOLDOUT-DTI` | Mean dots / cell | Catalogue hug (`<=6 px`) |
|---|---|---:|---:|---|---:|---:|---:|
| `C0_BDE_ctrl` | Same-run incumbent `BDE + 7 add-ons` + `SAPD(2.4, 3.5%, d>2)` | `0.142882` | `0.155446` | `0.149190` (`[0.140218, 0.159790]`) | `0.148697` | `11,655` | `0.072` |
| `H36_PoE_sapd` | `PoE(P_surf, P_sub; α_sub)` + `SAPD(2.4, 3.5%, d>2)` (detector-only contrast vs `C0`) | `0.143115` | `0.159185` | **`0.151172`** (`[0.140310, 0.162448]`) | **`0.150965`** (`+0.002268` vs `C0`) | `11,636` | `0.070` |
| `H36_PoE_submod` | Primary `PoE` + Elkan calibration + exact `Submod300(N_target=9,414, d>2)` | `0.140640` | **`0.158570`** (`+0.003124` vs `C0`) | **`0.149635`** (`[0.136482, 0.162894]`) | **`0.149403`** (`+0.000706` vs `C0`) | `9,041` | **`0.039`** |
| `C1_Sub_ctrl` | Zero-topography (`C+E`) control + `SAPD(2.4, 3.5%, d>2)` | `0.126284` | `0.139990` | `0.133164` (`[0.123406, 0.142797]`) | `0.133092` | `11,061` | `0.090` |
| `H36_S_sapd` | Zero-topography (`C+E+H36`) + `SAPD(2.4, 3.5%, d>2)` | `0.125735` | `0.140066` | `0.132926` (`[0.123338, 0.142591]`) | `0.132934` | `11,066` | `0.090` |
| **`H36_S_submod`** | **Zero-topography (`C+E+H36`) + Elkan + exact `Submod300` (packaged GeoTIFF spec)** | **`0.127590`** (`+0.001769` fold vs `C1`) | **`0.141301`** (`+0.001832` fold vs `C1`, **`3/4` folds `+`**) | **`0.134467`** (`[0.122950, 0.145988]`) | **`0.134892`** (**`+0.001801` vs `C1`, `3/4` folds `+`, `11/16` cells `+`**) | **`8,901`** | **`0.036`** |

### 4.2 Scientific takeaways from the `E1` + `E2` design

1. **Zero-topography `H36_S_submod` passes its paired subsurface gate (`+0.001801` fold gain, `3/4` folds `+`, `11/16` cells `+`) and improves `3.4×` over prior blind-magnetics lanes:**  
   Earlier non-topographic lanes in this repository (`GEM-1` and `GEM-FUSE1`, `HOLDOUT-DTI ≈ 0.040`) lost `> 73%` of incumbent holdout performance. Combining unit-corrected `SPI-GM` (`H36`), thermal/MT/seismicity (`C`), fold-clean structural context (`E`), Elkan prior-shift calibration, and exact 300 m submodular cover reaches **`0.1345` pooled `HOLDOUT-DTI`** (`89.9%` of full DEM+LiDAR `C0_BDE_ctrl`) with **zero DEM and zero LiDAR inputs** and halves near-catalogue hugging (`0.090 -> 0.036`).
2. **Product-of-Experts (`H36_PoE_sapd`) improves detector quality (`+0.002268` fold gain, `0.151172` vs `0.149190` pooled), while fixed-`9,414`-budget `Submod300` reveals a strong West-vs-East Great Basin tectonic contrast:**  
   On the western Great Basin quadrants (`Fold 0 NW: +0.013540`, `Fold 2 SW: +0.004586` — Walker Lane / Humboldt / Dixie Valley / Carson Sink Playas, where buried hydrothermal structures have strong conductive/magnetic contrast and sparse mapped scarps), `H36_PoE_submod` beats `C0_BDE_ctrl` decisively. On the eastern carbonate/range-front quadrants (`Fold 1 NE: -0.011653`, `Fold 3 SE: -0.003648`, where mapped catalogue density is high and `C0` emits `12,100` dots vs fixed `9,414`), a uniform `N_target / 4 = 9,414` under-allocates dots relative to regional fault length (`2/4` folds `+` -> honest **`verdict = "negative"`**).

---

## 5. `E3` Unique GeoTIFF Deliverable & 47-Raster Lane Audit (`evidence/h36_build/build_manifest.json`)

Per pre-registered `knowledge/21` §3.3, full-footprint 4-fold LOQO `H36_PoE_submod` exceeded `70%` 3-px dot overlap against this repository's own DEM-lineage rasters (`0.7920` vs `H35`), so `scripts/build_h36_submission.py` automatically selected and packaged the **zero-topography `H36_S_submod`** arm (`0` DEM / `0` LiDAR features):

- **Primary deliverable (`-zeros.tif`):** `docs/downloads/gems25-h36-spigm-subsurface-submod300-20261025-3937b96ce366-zeros.tif`  
  - `SHA-256`: `182f9e5f03cb66033d7106d1e7ca29cdc50280d10fe0306438138bf52e1540bc`
  - `content_id`: `3937b96ce366` · `37,654` binary (`1.0`) off-catalogue dots (`0` on-catalogue pixels) · `826,824` bytes
- **Template-convention fallback (`-nan.tif`):** `docs/downloads/gems25-h36-spigm-subsurface-submod300-20261025-3937b96ce366-nan.tif`  
  - `SHA-256`: `c103482fb70b4eb447a4fd9ae5b4a82baa2bcf41b161e34170f86cf5fdce8778` · `1,590,810` bytes
- **Automated dual validation (zero human intervention):**
  1. `gems25.submission.check_file`: **PASS** (`0` hard failures; `EPSG:32611`, `3730 × 3292`, `100 m` affine transform, `0` NaN/Inf inside `5,167,373`-px footprint, values in `[0.0, 1.0]`, `nodata = None`).
  2. Independent strict whole-array validator: **PASS** (`((arr >= 0.0) & (arr <= 1.0)).all() == True` across all `12,279,160` cells of `-zeros.tif`, directly preventing `"Predicted values must be in range [0, 1]"`).
- **47-raster surface & final-dot lane check (`evidence/h36_lane_surface.json`, `evidence/h36_lane_duplicates_canonical.json`):**
  - Pre-placement continuous surface `|Spearman|` across all 47 rasters: **`max = 0.1193 <= 0.90` (`0` flags — PASS)**.
  - Final-dot `|Spearman|` across all 47 rasters: **`max = 0.5622 <= 0.90` (`0` flags — PASS)**.
  - **Against ALL `31` non-lattice scored & sibling top-scorer rasters (`GEMSDOE10..91`, including all 9 focus sites + `GEMSDOE70`):** **`31 / 31` CLEAR (`max 3-px overlap = 0.5985 <= 0.70`)** — specifically:
    - vs `GEMSDOE32` `H33-2-B2` (`0.2778`): **`23.95%`** (`0.2395`)
    - vs `GEMSDOE36` `PINNs` (`0.2750`): **`24.39%`** (`0.2439`)
    - vs `GEMSDOE28` `H27-4` (`0.2708`): **`25.13%`** (`0.2513`)
    - vs `GEMSDOE25` `D2.8` (`0.2600`): **`25.56%`** (`0.2556`)
    - vs `GEMSDOE70` (`0.2478`): **`21.23%`** (`0.2123`)
    - vs `KDC` (`55,374` px): **`38.28%`** (`0.3828`)
    - vs `GEM-FUSE1` (`37,654` px): **`16.73%`** (`0.1673`)
  - **Symmetric / mutual 3-px overlap (`min(A->B, B->A)`) across all 47 rasters:** **`max = 0.5794 <= 0.70`**.
  - **Literal strict all-47 one-way check (`PR #14` rule):** flags synthetic `r13-lattice-s5` (`1.0000`, `IR-25-LANE-DENSITY`) and this repo's unscored `48,849`-dot `H35` (`0.7073` one-way, `0.5570` reverse — `273` dots above `70%` due to shared `Family E` catalogue distance/density halo, logged as `IR-25-CATALOGUE-HALO-CONVERGENCE`). Under strict repo policy: **`lane_clear = False`, `verdict = "negative"`, `ok_to_download = True`, `ok_to_submit_slot = False` (DO NOT SUBMIT)**.

---

## 6. Explicit Limitations & Prioritized Remaining Work

1. **No organizer score receipts or `drivendata.org` access (`AGENTS.md` Rule 3):** All competition scores (`0.2778`, `0.3195`, `0.4413`, etc.) remain unverified owner-reported claims (`IR-25-LEADERBOARD-CONFLICT`). `HOLDOUT-DTI` measures recovery of withheld mapped fault components (`hug`), not unknown blind faults verified by drilling.
2. **Quadrant budget allocation in `Submod300`:** Fixing `N_cell = N_target / 4 = 9,414` on holdout hurt the fault-dense eastern quadrants (`NE`, `SE`) while strongly helping western basin-fill quadrants (`NW +0.0135`, `SW +0.0046`). Future pre-registered work should replace fixed `N_target` with a **calibrated marginal-credit stopping threshold `ΔF(p | S) >= τ_cal`** so each tectonic domain receives dots proportional to its calibrated expected credit rather than a fixed pixel count.
3. **Catalogue-halo uniqueness convergence (`IR-25-CATALOGUE-HALO-CONVERGENCE`):** Even with `0` topographic features, including `Family E` (`E_d_fault`, `E_dens_r50`) concentrates dots within `2–12 px` of mapped fault traces, producing `70.73%` one-way 3-px overlap against `48,849`-dot `H35`. A future zero-`E` or distal-basin (`d(catalogue) > 6 px`) subsurface complement arm (`H36-2` `Euler-GravMag` + `H36-3` `Heat × MT-2km × CondBase-Cupola`) can eliminate shared catalogue-halo overlap entirely.
4. **Hardware / U-Net gap:** Sandbox compute (`2` vCPUs, `3.8 GiB` RAM, no GPU) precludes training multi-scale 2D spatial U-Nets (`drivendataorg/gems-prize-reference-solution`) that learn fault continuity directly without `Family E` distance proxies; running a 4-fold spatial U-Net on a GPU host over the unit-corrected `SPI-GM` + `3DEP` stack is the highest-upside external compute step.
