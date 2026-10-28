# Pre-Registration — `H80-SCRA-PoE`: Sedimentary-Cover Regime-Adaptive Crustal–Morpho Fusion & Blind Hydrothermal-Suballuvial Fault Operators (`2026-10-28`)

## 0. Standing-Rule Compliance & Assigned Single Method Lane

- **Branch**: `arena/aa5d1b5b-gemsdoe25` (fast-forwarded to `origin/main` at `a728c9f`, PR `#71`).
- **Pre-registration before code/fitting (`AGENTS.md` Rule 4)**: This document is committed to Git **before** creating `src/gems25/h80_scra.py`, running `scripts/run_h80_experiments.py`, or generating any candidate GeoTIFF. No tuning on holdout outcomes is permitted; failed arms remain failed.
- **Assigned single method lane (`Parallel-Run Protocol` Rule 1)**: `h80-scra-poe-suballuvial-geotherm` — strictly Quaternary-catalogue-free (`0` `Family E` / `H27_tip` predictors in the blind candidate) two-expert **Sedimentary-Cover Regime-Adaptive Product-of-Experts (`SCRA-PoE`)** augmented with four untried sub-alluvial / geothermal-disequilibrium / conserved-radiometric / half-graben physical operators, emitted at the B2 (`d_cat > 2.0 px`) `37,654`-dot submodular budget via shared `gems25.greedy.greedy_dots` and `gems25.submission.write_submission`.
- **Execution budget (`Parallel-Run Protocol` Rule 6)**: Exactly **3 pre-registered experiments** on virgin seed draws **`140, 141, 142, 143`** (`< 2 hours` wall-clock on 2 vCPUs). Zero weekly submission slots will be consumed (`slot_approved = False`, `okay_to_submit = False`).
- **No automated DrivenData access (`AGENTS.md` Rule 3)**: Zero network requests to `drivendata.org`.

---

## 1. Pre-Implementation Candidate Geological Hypotheses (`H80-1` .. `H80-4`)

Starting directly from `knowledge/40_h79_cthm_poe_outcome_2026-10-27.md` Priority #1 (`H80-BM-PoE`), `knowledge/41_session_plan_2026-10-28.md`, and `knowledge/43_session_962e5a5b_review.md`, we formulate and rank four geological hypotheses not yet implemented in `GEMSDOE25`. Rankings reflect qualitative physical leverage vs. implementation cost (**not** numeric leaderboard/DTI projections).

| Rank | ID & Name | Specific Layers Involved | Targeted Physical Signature & Transform | Why Missed by USGS/INGENIOUS Catalogue | Named Non-Fault Mimic | Novelty vs. Repo (`Family A–E`, `H27–H79`) & Cost / Data Availability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1 (Selected Lane)** | **`H80-1`: `SCRA-PoE` (Sedimentary-Cover Regime-Adaptive PoE + 4 Sub-Alluvial & Geothermal Operators)** | `training_features.tif` (`depth_to_base_surf`, `det_elev`, `det_elev_slope`, `rtp`, `tmi`, `tmi_hg`, `tmi_vg`, `iso_grav_anom_hg`, `cond_surf`, `tc`, `geod_dilaterate`, `deq_n100a15`, `ieq_n100a15`); `external/geodawn_extensions_u8.tif` (`TMI_up150`); `external/geodawn_rad_u8.tif` (`K`, `Th`, `U`, `TC`); `external/gdr_wellspring_in_footprint.csv` (`temp_c`, `geothermquartz_c`, `geothermchalc_c`, `geothermcat_c` only); `external/lidar_scarp_features_u8.tif` (`L_valid` + `Family B`); `external/derived_sgmc_faults_100m_u8.tif`. | **(a)** Shallow vertical-continuation magnetic ridge (`TMI - calib(TMI_up150)`) propagated axially across low-slope/deep-cover crossings (`H80_suballuvial_mag_continuity`); **(b)** `Na-K-Ca` minus `chalcedony` solute geothermometer disequilibrium (`Fournier & Truesdell, 1973`) diffused along crustal strike × microseismicity & MT/heatflow (`H80_geotherm_disequilibrium_upflow`); **(c)** `TC`-invariance-weighted cross-edge `ln(K/Th)` & `ln(U/Th)` juxtaposition (`H80_conserved_tc_rad_offset`); **(d)** basinward `depth_to_base_surf` rollover curvature × positive `geod_dilaterate` (`H80_halfgraben_rollover_hinge`); **(e)** continuous cover-gated exponent $\gamma_c(x) \in [0.52, 0.86]$ + bare steep-cliff deconfounder $w_{\text{regime}}(x)$. | USGS Qfaults / INGENIOUS mapping relies on exposed Quaternary scarps; Holocene sheetwash, Lake Lahontan silts, and bajada aggradation erase surface scarps over intrabasinal accommodation faults and blind fault-valve geothermal upflow zones (`Faulds & Hinz, 2015`). | **(a)** Buried Miocene basalt flow/sill edges; **(b)** lateral outflow plumes in perched thermal aquifers; **(c)** felsic-ash vs. arkosic-fan depositional contacts; **(d)** differential compaction hinges over buried paleochannels. | `H79` used uniform $\gamma_c=0.55$ (causing `75.55% > 70%` `h23-a-6pct` bare-scarp overlap), amplitude deficit `z_up150 - z_rtp` (no cover-crossing ridge propagation), max-threshold well temperatures (no `Na-K-Ca - chalcedony` disequilibrium), and lacked `TC`-conserved radiometric offset or half-graben rollover curvature. **Cost**: Low-Medium (`~30 min` CPU); **100% SHA-256-pinned in-repo inputs**. |
| **2 (Deferred)** | **`H80-2`: `CVTD` (Cross-Valley Fluvial Terrace Profile Displacement)** | `det_elev`, `det_elev_slope`, `external/lidar_scarp_features_u8.tif` (`step_max`, `coh100`, `strike`). | D8 drainage network extraction + quadratic longitudinal profile fitting across $\ge 3$ adjacent drainages to isolate laterally coherent same-sense terrace/thalweg elevation steps (`0.5–2 m`). | Distributed low-slip-rate (`< 0.1 mm/yr`) normal faults in dissected Tertiary volcanic plateaus leave segmented knickpoints overlooked in regional Quaternary fault compilations. | Resistant welded-tuff cliff ledges and recessional Lake Lahontan wave-cut shorelines (`~1,330 m` highstand). | `Family B`, `MSCR`, and `APFL` use local pixel/Hessian filters rather than hydrological catchment graph matching. **Cost**: High CPU (`3730×3292` D8 routing); pinned data available; deferred per single-lane rule. |
| **3 (Deferred)** | **`H80-3`: `MSPC` (Multiscale Riesz Monogenic Magnetic Phase Congruence)** | `rtp`, `tmi`, `tmi_hg`, `tmi_vg`, `external/geodawn_extensions_u8.tif` (`TMI_up150`). | 2-D Riesz monogenic phase $\varphi_s(x) = \operatorname{atan2}(|\mathbf{R}f_s|, f_s)$ congruence across scales $s \in \{200, 400, 800, 1600\}\text{ m}$ (`Kovesi, 1999`), amplitude-invariant across demagnetized zones. | Hydrothermally leached/oxidized fault cores have low magnetic amplitude (`A_mag_as` near zero) and are missed by amplitude ridges while retaining cross-scale phase jumps. | E–W aeromagnetic tie-line acquisition leveling seams and reversely magnetized Oligocene ignimbrite margins. | `H34` and `H75_EU3D` compute Hessian amplitude ridges and 3-D Euler homogeneity rather than 2-D Riesz monogenic phase congruence. **Cost**: Medium-High FFT RAM on `3.8 GiB` host; deferred per single-lane rule. |
| **4 (Blocked External)** | **`H80-4`: `3D-MT-BDR` (EarthScope USArray 3-D MT Phase-Tensor Skew at Brittle–Ductile Root)** | External USGS ScienceBase / EarthScope 3-D MT impedance cubes (`5–18 km` slices) + `cond_surf` + `tc`. | Galvanic-distortion-invariant Caldwell–Bibby–Brown (2004) phase-tensor skew $|\beta_{\text{MT}}|$ at `8–15 km` depth beneath shallow conductive (`1–5 Ω·m`) playa clays. | Deep crustal geothermal roots (`McGinness Hills` / `Tungsten Mountain` analogues) are electrostatically screened in shallow `cond_surf` by saline basin clays. | Paleozoic graphitic Roberts Mountains allochthon shales and closed-basin lithium-brine evaporites. | Repo contains only single-layer `cond_surf`. **External official source**: USGS ScienceBase / IRIS EarthScope MT (`https://www.usgs.gov/centers/gggsc`, CC0). **Obtainability check**: **NOT obtainable in-sandbox** (outbound network allowlist excludes `usgs.gov`/`sciencebase.gov`); flagged non-viable until mirrored into `registry/data_manifest.json`. |

---

## 2. Frozen Mathematical Specification of `H80-1` (`src/gems25/h80_scra.py`)

### 2.1 Four Static Quaternary-Catalogue-Free Columns (`H80_NAMES`)

All four grids are computed strictly from geophysical, topographic, radiometric, and allowlisted well-chemistry layers (`existing_faults.tif` and `dist_known_fault_px` are never read; enforced via `WELLSPRING_ALLOWED_COLS` assertion and unit tests) and scaled via `pct_scale_eroded(..., footprint)`:

1. **`H80_suballuvial_mag_continuity`**:
   - Compute core z-scored shallow continuation residual $\Delta z_{\text{shal}} = z(\text{TMI}) - z(\text{TMI}_{\text{up150}})$ where `TMI_up150 > 0` (`0` outside GeoDAWN extension footprint), isolating `100–600 m` sub-alluvial magnetic contacts from deep plutonic background.
   - Extract shallow contact ridge $r_{\text{mag}} = \text{ridge\_strength}(|\nabla G_{1.2}(\Delta z_{\text{shal}})| + 0.5\,|\text{tmi\_hg}|_{\text{norm}}, \sigma=1.5)$.
   - Estimate local magnetic strike $(\cos 2\theta_m, \sin 2\theta_m)$ via structure tensor on $\Delta z_{\text{shal}}$, and propagate $r_{\text{mag}}$ axially (`sigma_along = 14 px = 1.4 km`, `sigma_across = 1.8 px`) across 4 strike bases `{0°, 45°, 90°, 135°}`.
   - Gate by **bridge-across-cover amplification**: $r_{\text{bridge}}(x) = p_{\text{axial}}(x)\cdot (0.35 + 0.65\,c(x))$, rewarding persistent basement magnetic contacts extending beneath flat/thick sedimentary cover $c(x)$.

2. **`H80_geotherm_disequilibrium_upflow`**:
   - From `gdr_wellspring_in_footprint.csv` using strictly allowlisted columns `{"row", "col", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"}`:
     $$\Delta T_{\text{cc}} = \max(T_{\text{NaKCa}} - T_{\text{chalc}},\, 0), \qquad \Delta T_{\text{up}} = \max(\max(T_{\text{NaKCa}}, T_{\text{quartz}}) - T_{\text{spring}},\, 0)$$
     Impulse weight $I_{\text{diseq}}(r, c) = \ln\!\bigl(1 + \operatorname{clip}(\Delta T_{\text{cc}} / 35^\circ\text{C}, 0, 3) + 0.7\,\operatorname{clip}(\Delta T_{\text{up}} / 45^\circ\text{C}, 0, 3)\bigr)$.
   - Diffuse $I_{\text{diseq}}$ anisotropically (`sigma_along = 16 px`, `sigma_across = 2.5 px`) along the gravity+basement strike director, and couple multiplicatively with deep-to-intermediate microseismic conduit rate $S_{\text{eq}} = \text{pct}(\ln(1 + \max(\text{deq\_n100a15}, 0)) + 0.5\,\ln(1 + \max(\text{ieq\_n100a15}, 0)))$ and conductive-thermal anomaly $\sqrt{(0.25 + 0.75\,\text{pct}(\ln(1+\text{cond\_surf})))(0.25 + 0.75\,\text{pct}(\text{tc}))}$.

3. **`H80_conserved_tc_rad_offset`**:
   - From `geodawn_rad_u8.tif` bands `(K, Th, U, TC)` on valid pixels `(K > 0) & (Th > 0) & (TC > 0)`:
     Compute smoothed log-ratios $\ell_{\text{KTh}} = G_{1.5}(\ln((K+1)/(Th+1)))$ and $\ell_{\text{UTh}} = G_{1.5}(\ln((U+1)/(Th+1)))$, and core z-scored total count $z_{\text{TC}} = G_{1.5}(z(TC))$.
   - Compute compositional cross-gradient $g_{\text{comp}} = \sqrt{|\nabla \ell_{\text{KTh}}|^2 + |\nabla \ell_{\text{UTh}}|^2}$ and total-count invariance weight $w_{\text{TC}} = \exp(-|\nabla z_{\text{TC}}| / \sigma_{\text{TC}})$ where $\sigma_{\text{TC}}$ is the 65th percentile of $|\nabla z_{\text{TC}}|$ on valid core pixels.
   - Output `pct_scale_eroded(ridge_strength(g_comp * w_TC, 1.5), foot)`.

4. **`H80_halfgraben_rollover_hinge`**:
   - Smooth `depth_to_base_surf` ($z_b = G_{3.0}(\text{depth\_to\_base\_surf})$) and compute positive Hessian curvature $\kappa_+(z_b) = \max(\lambda_1(\mathbf{H}(z_b)), \lambda_2(\mathbf{H}(z_b)), 0)$ (concave-upward flexural rollover hinge in hanging-wall basin fill).
   - Compute medium-range (`sigma = 25 px = 2.5 km`) proximity halo $h_{\text{master}} = G_{25}(\text{pct}(\text{iso\_grav\_anom\_hg}))$ to master basin-bounding gravity steps, and positive geodetic dilation factor $d_+ = \text{pct}(\max(\text{geod\_dilaterate}, 0))$.
   - Output `pct_scale_eroded(kappa_plus * (0.25 + 0.75 * h_master) * (0.30 + 0.70 * d_+), foot)` where $z_b > 120\text{ m}$.

### 2.2 Continuous Sedimentary-Cover Regime-Adaptive PoE (`SCRA-PoE`)

Define the strictly geophysical/topographic **Sedimentary-Basin Cover Index** $c(x) \in [0, 1]$ and **Bare Steep-Cliff Deconfounder** $w_{\text{regime}}(x) \in [0.65, 1.0]$:
$$c_{\text{depth}}(x) = \operatorname{clip}\!\left(\frac{z_{\text{base}}(x) - 100\text{ m}}{900\text{ m}}, 0, 1\right), \qquad c_{\text{flat}}(x) = \exp\!\left(-\frac{\text{slope\_deg}(x)}{3.5^\circ}\right)$$
$$c(x) = \operatorname{clip}\!\bigl(0.55\,c_{\text{depth}}(x) + 0.35\,c_{\text{flat}}(x) + 0.10\,(1 - L_{\text{valid}}(x)),\; 0,\; 1\bigr)$$
$$w_{\text{regime}}(x) = 1.0 - 0.35\,\bigl(1.0 - c_{\text{depth}}(x)\bigr)\,\operatorname{clip}\!\left(\frac{\text{slope\_deg}(x) - 8.0^\circ}{12.0^\circ}, 0, 1\right)$$
$$\gamma_c(x) = \gamma_{\text{range}} + (\gamma_{\text{basin}} - \gamma_{\text{range}})\,c(x)$$
$$S_{\text{SCRA}}(x) = w_{\text{regime}}(x)\,\bigl(f_c + (1 - f_c)\,R_c(x)\bigr)^{\gamma_c(x)}\,\bigl(f_m + (1 - f_m)\,R_m(x)\bigr)^{1 - \gamma_c(x)}$$
with frozen primary parameters $(\gamma_{\text{range}}, \gamma_{\text{basin}}, f_c, f_m) = (0.52, 0.86, 0.05, 0.10)$ (`H80_SCRA_POE`) and pre-specified sparse-uniqueness fallback $(\gamma_{\text{range}}, \gamma_{\text{basin}}, f_c, f_m) = (0.66, 0.92, 0.05, 0.14)$ (`H80_SCRA_DEEP`). Here $R_c(x), R_m(x) \in (0, 1]$ are within-quadrant rank-normalized probabilities of `M_crustal` (`60` cols: `56`-col `H79` crustal+SGMC + `4` `H80` cols) and `M_morpho` (`26` cols: `Family B` + `S_dem_c2, S_dem_s2`).

---

## 3. Pre-Registered 3-Experiment Design (`Virgin Draws 140–143`)

All arms are evaluated on identical splits per `(fold, draw)` cell using `gems25.metric.dti_binary` (`alpha = 0.2, beta = 0.8, 300 m` triangular kernel, `R = 3.0 px`), whole-segment buffered hiding (`ctx.holdout.draw` or `draw_block25km(..., block_px=250)`), visible-only `Family E` / `H27_tip` reconstruction for `H35` arms, and pixel-exact `known_c` masking.

1. **Leakage Canary Pre-Check (`Rule 4`)**:
   Every feature column across `M_crustal` (`60` cols), `M_morpho` (`26` cols), and `CTRL_H35` (`59` cols) is evaluated standalone on `truth_c` in every `(fold, draw)` cell. **Hard stop if any single feature has `AUC > 0.90`.**

2. **Experiment 1 — `25-km` Block-Withheld $2^2$ Factorial Screen (`--mode block25km --draws 140 141`, `8` quadrant-draw cells/arm)**:
   - `CTRL_H35`: Same-run visible-catalogue `H35` control (`59` cols, `sapd2.4`).
   - `CTRL_CRUSTAL56`: Shipped `H79` `56`-col zero-topography crustal+SGMC single-HGB baseline (`B2` `37,654`-scaled `greedy_dots`).
   - `F0_G0` (`H79_UNIFORM_POE`): `56`-col crustal × `26`-col morpho, uniform $\gamma_c = 0.55$, $w_{\text{regime}} \equiv 1$.
   - `F1_G0` (`H80_UNIFORM_POE`): `60`-col (`+4 H80`) crustal × `26`-col morpho, uniform $\gamma_c = 0.55$, $w_{\text{regime}} \equiv 1$.
   - `F0_G1` (`H79_SCRA_POE`): `56`-col crustal × `26`-col morpho, adaptive `SCRA-PoE` `(0.52, 0.86)` + $w_{\text{regime}}$.
   - `F1_G1` (`H80_SCRA_POE`): `60`-col (`+4 H80`) crustal × `26`-col morpho, adaptive `SCRA-PoE` `(0.52, 0.86)` + $w_{\text{regime}}$.
   - Fixed-raster empirical readout (zero fitting): PR `#70`'s `aa0104874adb` (`6,430`-dot `r13`-gap raster) scored on the identical `8` cells to establish its previously missing `HOLDOUT-DTI`.

3. **Experiment 2 — Standard `20%`-Component Holdout & Catalogue-Hybrid Test (`--mode standard --draws 140 141`, `8` cells/arm)**:
   - `CTRL_H35`, `CTRL_CRUSTAL56`, `F1_G1` (`H80_SCRA_POE`), and `H80_PLUS_H35` (`CTRL_H35 + 4 H80 cols`, `63` cols, `sapd2.4`).

4. **Experiment 3 — Virgin Out-of-Sample `25-km` Block-Withheld Confirmation (`--mode block25km --draws 142 143`, `8` cells/arm)**:
   - Evaluates `CTRL_H35`, `CTRL_CRUSTAL56`, `F0_G0` (`H79_UNIFORM_POE`), `F1_G1` (`H80_SCRA_POE`), `H80_SCRA_DEEP` (`(0.66, 0.92)` fallback), and `H80_PLUS_H35` on completely untouched virgin draws `[142, 143]`.

---

## 4. Frozen Decision Gates & Deterministic Candidate Staging Rule

- **Gate G1 (Weekly-Slot Eligibility Gate)**: Requires beating same-run `CTRL_H35` with positive paired 95% CI (`ci_lo > 0`) AND passing `gems25.readiness.assess_readiness` (`selector_eligible = True`, including literal full-registry `<= 0.90` surface rank correlation and `<= 0.70` 3-px dot overlap). Even if `selector_eligible` were `True`, `okay_to_submit` remains `False` (weekly slot selection is a separate human selector step).
- **Gate G2 (Shipped Blind Discovery Gate vs. Prior Shipped `H79_CRUSTAL_SGMC`)**: On virgin Experiment 3 (`draws [142, 143]`), candidate pooled `HOLDOUT-DTI` exceeds `CTRL_CRUSTAL56` with `10,000`-draw paired bootstrap 95% CI strictly above zero (`ci_lo > 0`).
- **Gate G3 (Two-Stage Sparse-Portfolio Uniqueness Gate & Deterministic Staging Order)**:
  Build 4-quadrant LOQO OOF `M_crustal` (`60` cols) and `M_morpho` (`26` cols) surfaces once (`seed = 8000 + fold`). Evaluate in strict order:
  1. `H80_SCRA_POE` `(0.52, 0.86)` -> check Stage 1 surface `|Spearman| <= 0.90` across all aligned registry + `2026-10-28` extended sibling rasters AND Stage 2 `37,654`-dot B2 `greedy_dots` 3-px overlap `<= 0.70` across all aligned sparse rasters (`halo_cov < 0.70`, including `h23-a-6pct.tif`, `H79`, `H75-DCHB-CG`, `H75-POE65`, `B2`, `PR #70`).
  2. If `H80_SCRA_POE` exceeds `0.70` on any sparse raster (e.g., `h23-a-6pct.tif`), step to pre-specified `H80_SCRA_DEEP` `(0.66, 0.92)`.
  3. If `H80_SCRA_DEEP` still exceeds `0.70` on any sparse raster, step to `H80_CRUSTAL60` (`gamma_c = 1.0`).
  4. Package the first specification in `1 -> 2 -> 3` that passes both Gate G2 and Gate G3 (`outside="zero"` primary `.tif` + `-nan.tif` twin + `.zip`), then run literal `verify_candidate_independent.py`, `check_lane_surface.py`, `check_lane_duplicates.py`, and `check_readiness.py` without waiving `r13`, `pindrop`, or `geom-horse-ensemble.tif`.

## Pre-fit protocol correction (28 October, 16:35 UTC)

The paragraph above is an investigator-proposed **diagnostic lane**, not an owner-assigned method. No separate method paragraph was supplied by the owner. G3's proposed density-aware fallback and packaging sequence is **withdrawn before fitting**: the literal rule permits no sparse-only exception, and a duplicate requires stop, not another placement arm. The already-established r13 bound rules out packaging at the frozen 37,654-dot budget. This run may evaluate research hypotheses on hide-and-recover, but will generate **no new competition TIFF or full-footprint emission**. All staging, promotion and selector claims remain negative. No changing dot density or masking lattice gaps to evade the rule.

The named literature and numerical geological examples above have not been retrieved from official sources in this environment. They are hypothesis motivation, **not verified evidence**. `geothermcat_c` is an undocumented mirrored column here: interpret as a supplied geothermometer channel, not an independently established Na-K-Ca measurement. K/Th/U/TC uint8 bands are separately percentile-quantized: ratios of their codes are **compositional proxies, not physical concentration ratios**. EarthScope/ScienceBase external data lack a checked downloadable record, license and bytes and are NOT a viable proposal in this run. No empirical gain or hidden-fault causal explanation is assumed. The prior statement that source data placement was the single blocker is false: provenance, lane assignment and strict novelty still block submission.

Correction to diagnostic arm enumeration: include `H80_CRUSTAL60` as a measured readout of the same fitted expert in all experiments (no extra fit); no selective packaging. All raw per-feature and regime-weight canaries must be saved, including missingness and inverted AUC. Frozen feature code hash and cache hashes accompany the result. Fixed PR #70 raster evaluation is descriptive only: that historical raster was built using the complete catalogue mask, so its holdout readout is contaminated and must not enter model comparisons or promotion decisions. We will not treat it as valid hide-and-recover evidence.
