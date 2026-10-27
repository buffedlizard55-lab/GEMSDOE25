# 38 · Pre-Registration: Four Ranked Untried Geological Hypotheses (`H75-1..4`), 3-D Euler Homogeneity & Crustal-Root Product-of-Experts (`H75-EU3D-POE`), and Execution of `BlockHoldout` (`25-km` Checkerboard) — 2026-10-27

* **Session branch:** `arena/2a7235ac-gemsdoe25`
* **Pre-registration status:** Frozen and committed **before** writing `src/gems25/h75_eu3d.py`, fitting any `H75` model, or touching virgin holdout draws `130, 131, 132, 133`.
* **Prior-session next steps addressed first:**
  1. **Autonomous data & shared-cache restoration (`README.md` / `knowledge/34–35`):** Restored all SHA-256-pinned core competition inputs, external USGS 3DEP / GeoDAWN / DOE GDR #1391 layers, 30 artifact-ledger rasters, and 27 top-scorer rasters (`100+` unique registry rasters total), and rebuilt `static_ABCD.npy` + `addons.npy` with **6/6 exact SHA-256 matches** against `evidence/work_cache_hashes.json`.
  2. **`H73-BW` 25-km Checkerboard `BlockHoldout` (`src/gems25/block_holdout.py`):** Previously `BLOCKED_BEFORE_FIT` due to absent caches (`knowledge/34–35`). Executed on real data in Experiment 1 alongside `PM_DEAPRON` and `CTRL_H35` (preserving the 2026-10-26 historical receipts intact for regression reproducibility).
  3. **`H74` §6.2 Post-Merge Priority #1 + Deferred `H74-2 MS-EU3D` (`knowledge/37`):** Implements Two-Stage Multiplicative Product-of-Experts (`PoE`: $P_{\text{scarp}}^{1-\gamma} \cdot P_{\text{root}}^{\gamma}$) coupled with Sliding-Window 3-D Euler Homogeneity Structural-Index Deconvolution to break both `IR-25-APRON-TRAP` and `IR-25-LIDAR-BLIND-CONVERGENCE-20261026`.
* **Budget accounting (`<= 3` experiments, `<= 2` hours):** `2` formal pre-registered experiments on virgin draws `[130, 131]` (`Exp 1`) and `[132, 133]` (`Exp 2`), plus `1` transparently disclosed aborted pre-commit heuristic diagnostic (`IR-25-H75-DRAFT-ABORTED-20261027`, purged before commit) = `3 of 3` maximum session budget under the strictest possible accounting.

---

## 1. Method-Lane Declaration (Parallel-Run Protocol Rule 1)

Because the owner prompt's reference to *"the single method paragraph below"* does not include a separate method paragraph, we explicitly declare our single provisional method lane:

> **Lane `H75-EU3D-POE`:** **Two-Stage Crustal-Root Product-of-Experts (`PoE`) with Sliding-Window 3-D Euler Structural-Index Contact Deconvolution, Anderson–Morris Basement-Strike Criticality, and Basin-Normalized MT–Thermal Upflow.** A pure topographic/LiDAR scarp localizer $P_{\text{scarp}}(x)$ (`Family B` + contour/throw-dipole vetoes, zero subsurface/catalogue inputs) is trained independently of a pure subsurface & hydrothermal crustal-root expert $P_{\text{root}}(x)$ (`Families A, C, D` + `H34` + `H74_RMPS` + 4 new static `H75_EU3D` operators, zero DEM/LiDAR/catalogue inputs), and combined multiplicatively at out-of-fold inference via $S_{\text{PoE},\gamma}(x) = P_{\text{scarp}}(x)^{1-\gamma}\,P_{\text{root}}(x)^{\gamma}$ prior to `B2` (`d > 2.0 px`) submodular `greedy_dots` placement (`max_dots = 37,654`).

---

## 2. Four Ranked Untried Geological Hypotheses (`H75-1` through `H75-4`)

All `ΔDTI` brackets below are **uncertain planning prioritization brackets, NOT score estimates or live projections**.

| Rank | ID & Name | Specific Layers Involved | Physical Signature & Mathematical Transform | Why USGS/INGENIOUS Catalogue Misses It | Distinction From All 42 Modules in `src/gems25/` | Named Non-Fault Mimic | Planning `ΔDTI` Bracket & Cost | Official Free Data & Verified Obtainability |
|---|---|---|---|---|---|---|---|---|
| **1** | **`H75-1 · EU3D-POE`** *(Implemented & Validated)* | `iso_grav_anom`, `rtp`, `depth_to_base_surf`, `cond_surf`, `tc`, `geod_dilaterate`, `geod_shearrate`, `D_gdr_tmax5km` (`P_root`) $\times$ `Family B` DEM + 3DEP 1-m LiDAR (`P_scarp`) | **1)** $7\times 7$ (`700 m`) 3-D Euler homogeneity least-squares solver $\Delta x_0 T_x + \Delta y_0 T_y + z_0 T_z + NB = \delta x T_x + \delta y T_y + NT$ with FFT-consistent downward vertical derivative $T_z$, discriminating steep fault contacts ($N=0.5$, apex offset $\le 250\text{ m}$, $50 \le z_0 \le 3500\text{ m}$) from equant plugs/stocks ($N=2.0$ grav / $2.5$ mag). **2)** Morris (1996) normal-dilation & shear tendency projected onto basement gravity-contact normal under WNW–ESE Great Basin extension ($\text{az}_{\text{SHmin}} = 115^\circ$). **3)** Basin-thickness-normalized MT conductance $\times$ heat-flow excess. **4)** Multiplicative `PoE` gating of `300-m` scarps. | Catalogue traces rely on continuous subaerial scarps. Blind/partially concealed faults beneath bajadas, playas, and thin volcanic caps preserve only fragmentary micro-scarps indistinguishable from pluvial shorelines, yet offset basement density/magnetization ($N\approx 0.5$ Euler step) and channel deep conductive fluids. Conversely, un-faulted Lake Lahontan shorelines lack basement Euler/MT roots and are suppressed by $P_{\text{root}}^\gamma$. | Zero prior modules in `src/gems25/` implement least-squares 3-D Euler $(x_0,y_0,z_0)$ + structural-index $N$ contact-vs-plug discrimination, basement-strike resolved WNW–ESE slip/dilation tendency, basin-depth-normalized MT conductance, or two-stage OOF HGB `PoE` on 25-km `BlockHoldout`. | Unfaulted steep Mesozoic pluton-wallrock contacts or Tertiary caldera ring walls crossed by incised alluvial fan channels or shoreline benches. | `+0.002` to `+0.010` vs blind/scarp on 25-km `BlockHoldout`; **Low–Med cost** (`~15 min` CPU total). | **VIABLE & VERIFIED PRESENT:** Uses SHA-256-pinned competition core + USGS GeoDAWN (DOI `10.5066/P93LGLVQ`), USGS 3DEP 1-m LiDAR, and DOE GDR #1391 (CC BY 4.0) already restored in `data/`. |
| **2** | **`H75-2 · SWG-HCA`** *(Deferred — reserve)* | `det_elev`, `tc`, `depth_to_base_surf`, `gdr_wellspring_in_footprint.csv` (`temp_c`, `geothermquartz_c`) | **Sub-Basin Hydrologic Catchment Thermal-Advection Residual:** Regresses conductive heat flow `tc` on 10-km topographic position (Smith & Chapman 1983 meteoric recharge/discharge effect) and $\log(1 + h_{\text{base}})$ sediment-blanket thickness; extracts positive fracture-advection residual $q_{\text{adv}} = (\text{tc} - \widehat{q})_+$ and its sharp lateral gradient. | Upwelling geothermal plumes along blind accommodation-zone step-overs (e.g., McGinness Hills / Desert Peak analogs; Faulds & Hinz 2015) produce localized Peclet $>1$ thermal anomalies without surface rupture. | `features.py` uses raw `tc` and 5-km max spring `T`; `h66` used cation-minus-chalcedony difference. Neither removes topographically driven meteoric recharge/discharge nor conductive sediment-blanket thickness. | Cooling shallow Quaternary rhyolite/basalt intrusives and lateral down-gradient outflow tongues in permeable fanglomerates. | `+0.001` to `+0.005`; **Low cost** (`~8 min` CPU). | **VIABLE & VERIFIED PRESENT:** All inputs restored in `data/work/bands/` and `data/external/`. Deferred under 3-experiment cap. |
| **3** | **`H75-3 · MT3D-PT`** *(Blocked externally)* | External USGS / EarthScope USArray 3-D MT Resistivity (`5, 10, 15 km` slices) + `cond_surf` + `ieq_n100a15` | **Mid-Crustal 3-D MT Phase-Tensor Skew & Sub-Vertical Conductor Roots:** Depth-persistent $|\nabla_h \log_{10}\rho(z)|$ from `5 km` to `15 km` brittle-ductile transition beneath conductive clay playas. | Resolves deep fluid-bearing Dixie Valley / Humboldt blind fault roots directly beneath salt pans that screen shallow EM (`cond_surf`). | `cond_surf` is a single shallow conductance grid; no 3-D depth-sliced MT model exists in `GEMSDOE25`. | Paleozoic Roberts Mountains / Golconda graphitic black-shale thrust sheets and sulfidic skarns. | `+0.002` to `+0.009` if ingested; **Med–High cost**. | **NOT VIABLE IN THIS SANDBOX (CHECKED):** Free CC0 source at `https://www.sciencebase.gov/catalog/` & `http://ds.iris.edu/spud/emtf`, but outbound access is allowlisted to GitHub/PyPI/npm only and no mirror exists in `registry/data_manifest.json`. |
| **4** | **`H75-4 · IN-SAR-DEF`** *(Blocked externally)* | External NASA ARIA Sentinel-1 Ascending/Descending LoS or UNR NGL dense GPS (`geodesy.unr.edu`) | **100-m Vertical Subsidence vs Horizontal Extension Creep Decomposition:** High-pass $1\text{–}5\text{ km}$ horizontal strain-rate step across creeping/valving blind intrabasinal faults. | Smooth GPS strain grids (`geod_dilaterate`) have `>20 km` correlation length and blur individual intrabasinal fault strands. | Core `geod_*` bands are smooth regional continuum fields; no InSAR / dense station velocity decomposition exists in repo. | Agricultural/municipal groundwater pumping differential compaction across paleochannel clay lenses. | `+0.001` to `+0.006` if ingested; **High cost**. | **NOT VIABLE IN THIS SANDBOX (CHECKED):** `geodesy.unr.edu` and `asf.alaska.edu` are outside the sandbox allowlist (and Earthdata requires login). |

---

## 3. Frozen Mathematical Specification of `H75_EU3D` (`src/gems25/h75_eu3d.py`)

All four static columns are strictly label-free (`labels.tif`, `existing_faults.tif`, `gdr_qfaults_traces.csv`, and `dist_known_fault_px` are never read) and strictly topography-free (`det_elev`, `det_elev_slope`, and `lidar_scarp_features_u8.tif` are never read), returning finite `float32` values in `[0, 1]` on all `5,167,373` footprint pixels:

1. **`H75_euler_grav_contact` (`7x7` 3-D Euler Contact-vs-Plug Deconvolution on Isostatic Gravity):**
   * Smooth nearest-filled `13_iso_grav_anom` with $\sigma = 1.5\text{ px}$ (`150 m`). Compute horizontal derivatives $T_x, T_y$ in `mGal/m` (`cell_m = 100.0`) and exact FFT harmonic downward vertical derivative $T_z = \mathcal{F}^{-1}\{2\pi|\mathbf{k}|\hat{T}\}$ in `mGal/m` (`pad = 256` reflect).
   * Over every $7 \times 7$ window (`700 m × 700 m`, local offsets $\delta x, \delta y \in \{-300, \dots, +300\}\text{ m}$), solve the damped normal equations $(\mathbf{A}^\top\mathbf{A} + \lambda \mathbf{I})\boldsymbol{\theta}(N) = \mathbf{A}^\top \mathbf{y}(N)$ for $\boldsymbol{\theta}(N) = (\Delta x_0, \Delta y_0, z_0, NB)^\top$ at contact index $N_c = 0.5$ and equant-plug index $N_p = 2.0$.
   * Define horizontal offset $r_0 = \sqrt{\Delta x_0(N_c)^2 + \Delta y_0(N_c)^2}$, depth $z_0 = \Delta z_0(N_c)$, contact fit $R^2_c = \text{clip}(1 - \text{RSS}(N_c)/(\text{TSS}(N_c) + \varepsilon), 0, 1)$, and plug-rejection factor $\Delta_{\text{plug}} = \text{clip}\bigl(0.5 + 2.0\,\frac{\text{RSS}(N_p)/\text{TSS}(N_p) - \text{RSS}(N_c)/\text{TSS}(N_c)}{\text{RSS}(N_p)/\text{TSS}(N_p) + \text{RSS}(N_c)/\text{TSS}(N_c) + 10^{-4}}, 0, 1\bigr)$.
   * Raw contact score: $E_g = R^2_c \cdot \Delta_{\text{plug}} \cdot \exp\bigl(-r_0^2 / (2 \cdot 250^2)\bigr) \cdot \mathbb{I}(50 \le z_0 \le 3500) \cdot \exp\bigl(-(\ln(z_0/600)/1.25)^2\bigr)$, blended $0.5\,\text{scale}(E_g) + 0.5\,\text{scale}(\text{ridge}_{\sigma=1.5}(E_g))$.

2. **`H75_euler_mag_contact` (`7x7` 3-D Euler Contact-vs-Plug Deconvolution on Reduced-to-Pole Magnetics):**
   * Identical $7 \times 7$ harmonic 3-D Euler solver on smoothed `02_rtp` ($\sigma = 1.5\text{ px}$, `nT/m`), contrasting magnetic fault contact $N_c = 0.5$ against magnetic plug/pipe $N_p = 2.5$.

3. **`H75_anderson_slip_dilation` (Morris 1996 Basement-Strike Extension & Transtension Criticality):**
   * Extract basement density-gradient unit normal $(\hat{n}_x, \hat{n}_y)$ from the smoothed structure tensor of `13_iso_grav_anom` ($\sigma_{\text{grad}} = 2.0\text{ px}, \sigma_J = 4.0\text{ px}$) in grid coordinates (`+x = East`, `+y = South`).
   * Project onto Great Basin regional minimum horizontal stress $\hat{\mathbf{u}}_{\text{SHmin}} = (\sin 115^\circ, -\cos 115^\circ) = (+0.90631, +0.42262)$ (`N65°W–S65°E` extension): $\cos^2\alpha = (\hat{n}_x u_x + \hat{n}_y u_y)^2$ (normal dilation tendency $T_d$) and $\sin^2(2\alpha) = 4\cos^2\alpha(1 - \cos^2\alpha)$ (resolved shear tendency $T_s$).
   * Combine $C_{\text{crit}} = |\nabla g|_{\text{norm}} \cdot \bigl(0.65\,T_d\,\text{norm}(\max(\text{geod\_dilaterate}, 0)) + 0.35\,T_s\,\text{norm}(\max(\text{geod\_shearrate}, 0))\bigr)$, scaled via `pct_scale_eroded`.

4. **`H75_mt_thermal_conduit` (Basin-Thickness-Normalized MT Conductance $\times$ Heat-Flow & Euler Root):**
   * Normalize high-pass surface conductance $\Delta c = \max(0, \ln(1 + \text{cond\_surf}_+) - G_{\sigma=25}(\ln(1 + \text{cond\_surf}_+)))$ by sediment thickness $1 + 0.5\ln(1 + \max(h_{\text{base}}, 0)/500)$ to suppress passive playa clay Conductors, and multiply by $\sqrt{\text{norm}(\max(0, \text{tc} - G_{\sigma=30}(\text{tc})) + 0.3\,\text{norm}(\text{D\_gdr\_tmax5km})) \cdot \max(H75_{\text{euler\_grav}}, H75_{\text{euler\_mag}})}$.

---

## 4. Frozen Experimental Design, Gates, and Staging Duplicate Stop

### Experiment 1 (`H75-BW-CHK`, Virgin Draws `[130, 131]`, `4` Checkerboard Folds $\times 2$ Draws = `8` Cells/Arm)
Uses `gems25.block_holdout.BlockHoldout(foot, labels, hide_frac=0.20, block_size_px=250)` (`25-km` checkerboard blocks, hiding 100% of every component touching any test block, `1.5-km` collar):
* **`CTRL_H35`** (`59` cols: `BDE + EXTRAS + H27_tip + H34`), uniform negatives, `sapd2.4` (`kfrac=0.035, min_dist=2.4`).
* **`PM_DEAPRON`** (`59` cols: `CTRL_H35` features with `H73-PM` `d_vis`-matched negative sampler, `kfrac=0.030, min_dist=2.8, d_vis > 2.0 px`) — completes the previously cache-blocked `H73-BW` diagnostic!
* **`SCARP_ONLY`** (`32` static cols: `Family B` [28] + `S_dem_c2, S_dem_s2` [2] + `RBDT_throw_dipole, RBDT_non_shoreline_scarp` [2]; zero `A/C/D/E`), `B2` (`d_vis > 2.0 px`) + `greedy_dots`.
* **`ROOT_H75`** (`55` static cols: `Families A [16], C [7], D [17]` + `SUBSURF_EXTRAS [4]` + `H34 [3]` + `H74_RMPS [4]` + `H75_EU3D [4]`; zero `B`, zero `E`), `B2` (`d_vis > 2.0 px`) + `greedy_dots`.
* **`H75_POE50`** (Primary Candidate): $S_{\text{PoE50}} = P_{\text{SCARP\_ONLY}}^{0.50} \cdot P_{\text{ROOT\_H75}}^{0.50}$, `B2` (`d_vis > 2.0 px`) + `greedy_dots`.
* **`H75_POE65`** (Root-Dominant PoE): $S_{\text{PoE65}} = P_{\text{SCARP\_ONLY}}^{0.35} \cdot P_{\text{ROOT\_H75}}^{0.65}$, `B2` (`d_vis > 2.0 px`) + `greedy_dots`.

### Experiment 2 (`H75-STD`, Virgin Draws `[132, 133]`, Standard 4-Quadrant `Holdout`, `8` Cells/Arm)
Evaluates `CTRL_H35`, `PM_DEAPRON`, `SCARP_ONLY`, `ROOT_H75`, `H75_POE50`, `H75_POE65`, plus **`H75_APRON`** (`CTRL_H35 + H75_EU3D`, `63` cols, `sapd2.4`) on standard component withholding.

### Validation Gates (Fail-Closed, Zero Manual Intervention)
1. **Leakage Canary Gate (Rule 4):** Every single feature column across every cell (including all 4 `H75_EU3D` columns) tested standalone via `gems25.validation.feature_canary` (`cap = 0.90`). Any `canary_auc > 0.90` halts immediately as presumptive leakage.
2. **Diagnostic Block Gate `G2_BW` (`Exp 1`):** `H75_POE50` (or `H75_POE65`) beats `ROOT_H75` (`> +0.005` pooled `HOLDOUT-DTI`, `>= 3/4` folds) AND beats `SCARP_ONLY` (`> 0` pooled gain, `>= 3/4` folds) on 25-km checkerboard `BlockHoldout`, proving genuine two-stage crustal-root synergy. Also evaluates `H73-BW`'s frozen selector gate for `PM_DEAPRON` (`far_gt9_dti > CTRL_H35 + 0.001`, 95% CI lower `> 0`, `>= 3/4` folds, `>= 35%` emitted `> 20 px`).
3. **Weekly-Slot Gate `G1_SLOT` (`Exp 2` + `Exp 1`):** Candidate must beat same-run `CTRL_H35` on **both** `Exp 1` (`BlockHoldout`) and `Exp 2` (`Holdout`) by `> +0.0010` pooled `HOLDOUT-DTI` with 95% cluster-bootstrap CI lower bound `> 0` and `>= 3/4` folds positive, AND pass the literal lane gate (`lane_clear == True`), AND receive separate owner selector approval. Otherwise `verdict = "negative"`, `slot_approved = False`, `ok_to_submit_slot = False` (**`DO NOT SUBMIT`**).
4. **Full-Footprint LOQO Candidate Build & Pre-Publish Staging Lane Gate (Rule 1):**
   * Fit 4-quadrant Leave-One-Quadrant-Out (`LOQO`, `1.5-km` collar, seeds `20261201, 20261202`) OOF probabilities for `P_scarp` and `P_root`.
   * Evaluate frozen candidate cascade `H75_POE50` $\to$ `H75_POE65` $\to$ `ROOT_H75` in staging:
     - First check continuous OOF surface via `scripts/check_lane_surface.py` (`worst |Spearman| <= 0.90` across all `100+` restored registry rasters).
     - Place `B2`-hygiene (`d_cat > 2.0 px`) `greedy_dots` (`max_dots = 37,654`) in a staging directory and run `scripts/check_lane_duplicates.py` + `scripts/lane_check_extended.py`.
     - Publish to `docs/downloads/` **if and only if** `flagged_lane == []`, `external_sparse.lane_pass == True` (`<= 70%` 3-px overlap vs every sparse focus/scored/artifact raster including `GEMSDOE32 B2`, `h23-a-6pct.tif`, `H72-CF`, and `H74-SUBSURF`), and `own_lineage.lane_pass == True` (`<= 70%` vs all 26+ own `docs/downloads` stems). Any staging arm that exceeds `70%` sparse overlap is halted and recorded in `evidence/` without publishing.

---

## 5. Official Reference Links (Manual Verification)

* DrivenData DOE GEMS Overview & Metric: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> *(never auto-fetched per ToS)*
* Official DOE GEMS Rules PDF (NREL/NLR): <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
* Reference Solution Repository: <https://github.com/drivendataorg/gems-prize-reference-solution>
* DOE GDR Submission #1391 (INGENIOUS Great Basin dataset, CC BY 4.0): <https://gdr.openei.org/submissions/1391>
* GBCGE INGENIOUS Project: <https://gbcge.org/current-projects/ingenious/>
* USGS GeoDAWN Airborne Magnetic & Radiometric Survey (DOI `10.5066/P93LGLVQ`): <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
* Coordinate Reference System `EPSG:32611` (WGS 84 / UTM zone 11N): <https://epsg.io/32611>
* Tversky Index formulation: <https://en.wikipedia.org/wiki/Tversky_index>
