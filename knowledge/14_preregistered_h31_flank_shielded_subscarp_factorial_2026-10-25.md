# H31 — Preregistered 2² Factorial: Tip-Preserved Lateral-Flank Shielding × Multi-Physics Sub-Scarp Concordance (2026-10-25)

## 1. Evidence boundary and forensic motivation across the 9 focus sites

All competitionGeoTIFF bytes analyzed below were fetched from the owner's public GitHub repositories via bare Git blob retrieval (`scripts/analyze_focus_sites.py` $\to$ `evidence/focus_sites_forensics.json`) without contacting `drivendata.org`. All competition DTI figures (`0.1922`, `0.2477`, `0.2600`, `0.2708`, `0.2778`, `0.2750`, `0.3195`, `0.4413`) are **user/owner-reported claims**, not organizer-confirmed receipts.

### Pixel-exact forensic chain (`19GEMSDOE -> GEMSDOE24 -> GEMSDOE25/30 -> GEMSDOE28/31 -> GEMSDOE32 -> GEMSDOE36`)

| Site | Artifact label | SHA-256 (first 12) | Emitted px | Min $d(\text{cat})$ | Verified pixel identity | Reported DTI (unverified claim) |
|---|---|---|---:|---:|---|---:|
| 19GEMSDOE | `h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan` | `ec1f9b56b83c` | 121,131 | 1.00 px | Parent solid multi-line ridge mask (`0` on catalogue) | 0.1922 |
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | `68d0e2e4fcc5` | 60,069 | 1.00 px | Exact `dot_thin(H19-5, 1.5)` | 0.2477 |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | `91eae1ca42ec` | 44,090 | 1.00 px | Exact `dot_thin(H19-5, 2.4)` (`== dot_thin(H19-5, 2.8)`) | 0.2600 |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | `5f963b8bca5e` | 44,090 | 1.00 px | Footprint-identical to GEMSDOE25 `D2.8` (`44,090 == 44,090` px) | 0.2600 |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | `33003374335d` | 61,328 | 1.00 px | `D1.5` (`60,069` px) $+ 1,259$ gap-closure dots | 0.2449 |
| GEMSDOE28 | `h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan` | `ab0230015224` | 40,199 | 1.41 px | **Exact** `D2.8 & (d(cat) > 1.0 px)` (`-3,891` px at $d=1.0$) | 0.2708 |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | `07b6db440535` | 40,199 | 1.41 px | Footprint-identical to GEMSDOE28 `r1` (`40,199 == 40,199` px) | 0.2708 |
| GEMSDOE28 | `h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan` | `04d31922f5c1` | 42,294 | 1.00 px | Pre-thinned tip + Euler deconvolution on `D2.8` | 0.2649 |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | `5556aa1438fd` | 37,660 | 1.41 px | Rung-30 blind detector with $d(\text{cat}) > 1.0\text{ px}$ | 0.2710 |
| GEMSDOE28 | `h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan` | `81d5b87bc842` | 37,860 | 1.41 px | Strict superset of `h36-1` (`37,660` px) $+ 200$ extra pixels | 0.2707 |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | `bc3af2a5fcb4` | 41,865 | 1.00 px | Shares `33,670` px with `r1`, swaps `6,529` for `8,195` tip/stepover px | 0.2632 |
| **GEMSDOE32** | **`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`** | **`c55bafc47005`** | **37,654** | **2.24 px** | **Exact `D2.8 & (d(cat) > 2.0 px)` (`-6,436` px at $d \le 2.0$)** | **0.2778** |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | `e15891020b9c` | 38,854 | 2.24 px | **Strict superset** of GEMSDOE32 `B2` (`37,654` px) $+ 1,200$ extra dots | 0.2750 |

### Why and how `GEMSDOE32` (`h33-h33-2-b2`, reported `0.2778`) achieved the highest score among those sites

Under the official Distance-weighted Tversky Index ($\alpha = 0.2, \beta = 0.8, R = 300\text{ m} = 3\text{ px}$):
$$\text{DTI}(P) = \frac{\text{TP}_w(P)}{0.2\big(\text{TP}_w(P) + \text{FP}_w(P)\big) + 0.8|G|}$$
1. **Step 1 (`D2.8 -> R1`, $44,090 \to 40,199\text{ px}$, reported $0.2600 \to 0.2708$):**
   Deleting the $\Delta M_1 = 3,891$ dots of `D2.8` at $d(\text{catalogue}) = 1.0\text{ px}$ ($100\text{ m}$ orthogonal adjacency to mapped traces) removes $778.2$ units from $0.2\,\text{FP}_w$. Under the calibrated truth count $|G| \approx 12,691$, a **zero-credit-loss deletion** ($\Delta \text{TP}_w = 0$) predicts $\text{DTI} = 0.27100$ against the reported `0.2708`, implying those $3,891$ adjacent dots carried only $\Delta \text{TP}_w \approx 3.74$ units of truth credit ($\approx 0.00096$ credit/px, $57\times$ below the break-even inclusion threshold $\tau(0.2600) = 0.0549$).
2. **Step 2 (`R1 -> B2`, $40,199 \to 37,654\text{ px}$, reported $0.2708 \to 0.2778$):**
   Deleting the next $\Delta M_2 = 2,545$ dots at $1.0 < d(\text{catalogue}) \le 2.0\text{ px}$ ($d \in \{\sqrt{2}, 2.0\}\text{ px}$, i.e., the $141\text{–}200\text{ m}$ collar around mapped traces) removes another $509.0$ units from $0.2\,\text{FP}_w$. A zero-credit-loss deletion from `D2.8` predicts $\text{DTI} = 0.27871$ against the reported `0.2778`, implying those $2,545$ dots carried only $\Delta \text{TP}_w \approx 12.80$ units of truth credit ($\approx 0.00503$ credit/px, $11\times$ below $\tau(0.2708) = 0.0573$).
3. **Physical explanation:**
   Mapped faults in the USGS/INGENIOUS catalogue sit along range-front scarps whose colluvial wedge, footwall erosion slope, and Gaussian filter responses ($\sigma = 1.5\text{–}3.0\text{ px}$) span $100\text{–}250\text{ m}$ ($1\text{–}2.5\text{ px}$) on either side of the digitized centerline. When only $d = 0$ is masked, the parallel side-lobe of the *already-mapped* fault at $1 \le d \le 2\text{ px}$ survives and captures $14.6\%$ of `D2.8`'s dots while earning essentially zero off-catalogue truth credit.
4. **Why post-hoc deletion (`B2`) has a hard ceiling ($\approx 0.278$) and cannot reach `0.3195` or `0.4413` by itself:**
   `B2` is a pure deletion of `D2.8` (`H19-5`): it discovers **zero new unmapped fault segments** and does not reallocate the $6,436$ deleted dots to genuine unmapped structures, nor does it distinguish between non-tip lateral flanks (where $d \le 2.5\text{ px}$ is a side-lobe artifact) and **directed fault-tip continuation cones** ($\text{H27\_tip} > 0$, where unmapped faults physically propagate outward from visible fault terminations).

---

## 2. Four ranked candidate geological hypotheses (untried in GEMSDOE25)

| Rank | ID | Hypothesis | Specific layers & physical signature | Why it catches faults missing from the USGS/INGENIOUS catalogue | Named non-fault mimic | Difference from prior GEMSDOE25 work (H26–H30) | Planning $\Delta$DTI (HOLDOUT-DTI) & cost | Data / viability status |
|---:|---|---|---|---|---|---|---|---|
| **1** | **H31-1** | **Tip-preserved lateral-flank shielding $\times$ multi-physics subdued-scarp concordance (`C` $\times$ `M`)** | **Layers:** `L_step_max`, `L_ex_mean`, `L_coh100`, `A_grav_hg_ridge`, `A_mag_hg_ridge`, `D_depth_base_grad`, `D_cond_grad`, `D_ThK_edge`, plus visible-only `d(visible)` and `H27_tip`. **Signature:** Geometric mean $\sqrt{\bar{S}_{\text{surf}}\cdot\bar{S}_{\text{sub}}}$ of fine 3DEP LiDAR scarp persistence and subsurface potential-field/MT/radiometric edges (`H31_subscarp_concord`), paired with an off-flank/tip habitat field (`H31_offflank_tip_halo`) and tip-preserved lateral-flank emission shielding ($d(\text{visible}) > 2.5\text{ px} \lor \text{H27\_tip} \ge 0.05$). | Major range-front scarps are already mapped; unmapped faults are either (i) **piedmont / intra-basin step faults** $>250\text{ m}$ outboard of range fronts where surface relief is subdued ($<1\text{–}3\text{ m}$ in 3DEP LiDAR) but corroborated by subsurface density/magnetic/MT/alteration boundaries, or (ii) **along-strike continuations/splays** propagating out of visible fault tips ($\text{H27\_tip} > 0$). Shielding the non-tip lateral flank stops the top-$K$ selector from wasting budget on mapped-fault scarp aprons and reallocates those dots to unmapped structures. | Pleistocene Lake Lahontan wave-cut shorelines, alluvial fan-toe incision scarps, or dipping volcanic flow margins coinciding with lithologic contacts. | `H26-3` used only `grav*mag` and `grav*depth` with no LiDAR or MT/radiometric coupling and no flank shielding. `H27-1` and `H30-1` had zero lateral-flank shielding ($d(\text{visible}) > 0$ only) and no subsurface multi-physics concordance. Unlike `GEMSDOE32`'s static post-hoc deletion, `H31-1` trains and reallocates top-$K$ candidates inside our out-of-fold HGB + `sapd2.4` pipeline while preserving tip cones. | **$+0.0015$ to $+0.0060$** HOLDOUT-DTI; **Low cost** ($\sim 7\text{ min}$ total for screen + confirm). | **VIABLE NOW:** all inputs present and SHA-256-verified in `data/work/static_ABCD.npy` + `addons.npy`. |
| 2 | H31-2 | Anisotropic dip-asymmetric gravity–topography step | `12_det_elev`, `18_iso_grav_anom_hg`, `A_grav_tilt`, `L_downface_max`, `L_upface_max`. Signed cross-strike offset ($1\text{–}4\text{ px}$ down-slope) between surface scarp face and hanging-wall gravity-gradient maximum for $\sim 60^\circ$ dipping normal faults. | Buried range-front/piedmont normal faults have their subsurface basin-fill density step displaced $100\text{–}400\text{ m}$ down-dip from the eroded surface scarp; pixel-coincident ($d=0$) products miss this dip offset. | Asymmetric alluvial fan wedges prograding off unfaulted bedrock slopes. | `H26-1` evaluated symmetric $\pm 3\text{ px}$ radiometric differences across DEM normals, never signed down-dip gravity-gradient offset. | $+0.0005$ to $+0.0040$ HOLDOUT-DTI; Medium cost. | Viable (cached bands present); ranked #2 behind H31-1 on expected leverage. |
| 3 | H31-3 | Transtensional dilational strain-rate $\times$ K/Th alteration corridor | `07_geod_shearrate`, `08_geod_dilaterate`, `D_K`, `D_ThK`, `D_cond_grad`. Conjunction of positive geodetic dilation ($\dot{\varepsilon}_{\text{dil}} > 0$) with localized radiometric potassium-enrichment edges and MT conductance gradients. | Blind hydrothermal upflow zones in Walker Lane / Humboldt transtensional stepovers distribute strain across fracture swarms without a single tall scarp, leaving K-metasomatism and clay-alteration boundaries under positive crustal dilation. | Evaporitic playa margins and unaltered potassic ash-flow tuff contacts. | Family `C` and `D` were tested only as broad additive families in the Resolution V screen, not as a dilation-gated alteration edge. | $0.0000$ to $+0.0030$ HOLDOUT-DTI; Low–Medium cost. | Viable (cached bands present); ranked #3. |
| 4 | H31-4 | USGS 2022 heat-flow residual $\times$ slip/dilation-tendency stress prior | External USGS ScienceBase releases: DeAngelo et al. (2022) Great Basin heat flow ([https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28)) and Siler (2022) slip/dilation tendency ([https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d](https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d)). | Faults striking perpendicular to $\sigma_{h,\min}$ remain hydraulically conductive and produce conductive heat-flow anomalies even when completely buried beneath Quaternary playa sediment. | Lateral warm-water outflow plumes advected down hydraulic gradient in shallow alluvial aquifers. | Listed as blocked in `H26-4`/`H27-4`; never implemented. | Unknown; High data-engineering cost. | **BLOCKED / NOT VIABLE HERE:** `www.sciencebase.gov` is outside the sandbox network allowlist and the external binaries are not in `registry/data_manifest.json`. |

---

## 3. Preregistered Experimental Design for Top Candidate `H31-1`

### 3.1 Spatially blocked hide-and-recover holdout (`gems25.holdout.Holdout`)
- **Spatial blocks:** 4 contiguous quadrants (`NW`, `NE`, `SW`, `SE`) split at the median row/column of the 5,167,373-pixel footprint, with a **15-pixel ($1.5\text{ km}$) buffer collar** (`COLLAR_PX = 15`) excluded between training and test quadrants and a 12-pixel domain erosion (`DOMAIN_ERODE = 12`).
- **Withholding rule:** In each draw, whole 8-connected fault components (`hide_frac = 0.20`) are withheld as `hidden_test` (in the test quadrant) and `hidden_train` (outside the buffered test quadrant). All remaining catalogue pixels form `draw.visible`.
- **Zero-leakage guarantee:** Every dynamic catalogue feature (`E_dist`, `E_cos2`, `E_sin2`, `E_dens5`, `E_dens20`, `E_dens50`, `E_coh20`, `X2_compat`, `X2_compat_coh`, `H27_tip`, `H31_offflank_tip_halo`) and the lateral-flank shield `d(visible)` are derived **strictly from `draw.visible`**. Visible faults (`draw.visible`) are masked pixel-exactly during emission and scoring.
- **Draws:**
  - **Screen stage (`--stage screen`):** draws `[10, 11]` across all 4 spatial folds ($4 \times 2 = 8$ cells).
  - **Confirmation stage (`--stage confirm`):** fresh draws `[12, 13]` across all 4 spatial folds ($4 \times 2 = 8$ cells), permitted **only if** the screen stage passes its frozen gate.

### 3.2 Leakage Canary (Protocol Rule 4 — mandatory before trusting any fit)
Before any model fit in the screen stage, evaluate each candidate feature **alone** on the holdout quadrant test sets across all 4 spatial folds (`Cell.feature_canary_auc`):
- `H31_subscarp_concord`
- `H31_offflank_tip_halo`
- `H27_tip`
- Each constituent static input (`L_step_max`, `L_ex_mean`, `L_coh100`, `A_grav_hg_ridge`, `A_mag_hg_ridge`, `D_depth_base_grad`, `D_cond_grad`, `D_ThK_edge`)
**Hard gate:** If any single feature has mean holdout ROC-AUC ($\max(\text{AUC}, 1-\text{AUC})$) $> 0.90$, abort immediately as suspected label leakage.

### 3.3 Coded $2^2$ Factorial Matrix (`M` $\times$ `C`) plus Same-Run No-Tip Control
Fixed base features: Family set `BDE` + H26 add-ons (`X1_K`, `X1_ThK`, `X1_UK`, `X2_compat`, `X2_compat_coh`, `X3_gm`, `X3_gd`).
Fixed classifier: `HistGradientBoostingClassifier` (`max_iter=100, learning_rate=0.12, max_leaf_nodes=31, min_samples_leaf=50, l2_regularization=1.0, class_weight={0:1, 1:5}, early_stopping=False, random_state=draw`).
Fixed emission budget & dotting: Hessian ridge NMS ($\sigma = 1.0$) $\to$ top-$K$ ($K = 0.035 \times |\text{dom}|$) $\to$ score-ordered Poisson-disk dotting (`sapd2.4`, $d_{\min} = 2.4\text{ px}$).

| Arm | Factor $M$ (`H31` features) | Factor $C$ (Tip-preserved flank shield) | Include `H27_tip` | Factorial $2^2$ member | Description |
|---|---:|---:|---|---|---|
| `CTRL_NO_TIP` | $-1$ | $-1$ | `False` | `False` | Same-run no-tip control (`BDE + H26`, standard emission $d(\text{vis}) > 0$) |
| `M0_C0` | $-1$ | $-1$ | `True` | `True` | Same-run tip control (`BDE + H26 + H27_tip`, standard emission $d(\text{vis}) > 0$) |
| `M1_C0` | $+1$ | $-1$ | `True` | `True` | Add `H31_subscarp_concord` + `H31_offflank_tip_halo`, standard emission |
| `M0_C1` | $-1$ | $+1$ | `True` | `True` | Base + tip features, tip-preserved lateral-flank shield ($d(\text{vis}) > 2.5 \lor \text{H27\_tip} \ge 0.05$) |
| **`M1_C1`** | **$+1$** | **$+1$** | **`True`** | **`True`** | **Primary candidate: `H31` features + tip-preserved lateral-flank shield** |

Execution order of the 5 arms is randomized by frozen seed `20261025`.

### 3.4 Response Metrics and Promotion Gate
1. **Primary metric (Protocol Rule 3):** Both (a) **Pooled HOLDOUT-DTI** ($\alpha=0.2, \beta=0.8, R=300\text{ m}$ triangular kernel pooled over all quadrant test pixels, labeled with evaluator version `gems25.holdout.v1.2-buffered-4quad-pooled-dti`, withheld-positive count, and 95% $t$-CI across the 4 spatial blocks) and (b) **4-fold block-mean HOLDOUT-DTI** (`NW`, `NE`, `SW`, `SE`).
2. **Paired promotion gate (`h31_promotion_gate`):**
   Compare `M1_C1` against the **per-fold best same-run control** ($\max(\text{CTRL\_NO\_TIP}, \text{M0\_C0})$ in each spatial fold):
   - Mean paired gain across the 4 spatial folds $> +0.0010$ DTI;
   - Positive paired gain in $\ge 3$ of 4 spatial folds;
   - Worst-fold paired change $\ge -0.0100$ DTI;
   - Mean catalogue-hugging share (`hug`, fraction of emitted dots within $3\text{ px}$ of `draw.visible`) change $\le +0.1000$ (in fact expected to be negative, i.e., *less* catalogue hugging).
3. **Full-data unique GeoTIFF generation & Registry Duplicate-Lane Gate (Protocol Rule 1):**
   Only if **both** `--stage screen` (draws `[10, 11]`) and `--stage confirm` (draws `[12, 13]`) pass the paired promotion gate:
   - Train the full-catalogue `M1_C1` model (`scripts/build_h31_submission.py`) using hide-and-recover pseudo-new positives, emit via tip-preserved flank shielding + `sapd2.4`, and verify that:
     1. Continuous surface Spearman rank correlation $\rho \le 0.90$ against **every** raster in `registry/artifact_ledger.json` (30 rasters) and `evidence/focus_sites_forensics.json` (13 focus artifacts);
     2. Final emitted dots 3-px overlap $\le 0.70$ ($70\%$) against **every** registry and focus-site raster;
     3. All 16 format checks in `src/gems25/submission.py::check_file` pass (`0` NaNs inside footprint, values in `[0, 1]`, `EPSG:32611`, `3730 × 3292`, 100 m geotransform).
   - Even after passing screen, confirmation, format, and duplicate-lane gates, `slot_approved` remains `False` (`no slot` in the DrivenData note) because weekly competition slot selection is a separate human selector step under Protocol Rule 6 and `AGENTS.md` Rule 5.
