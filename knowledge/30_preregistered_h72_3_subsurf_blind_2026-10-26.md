# Pre-Registered Experiment 3 (`H72-3 PTTG+MTHS-SUBSURF`, Untouched Draws `84, 85`) — 2026-10-26

**Branch:** `arena/d64e58fa-gemsdoe25`  
**Budget status:** Experiment `3 of 3` (hard stop after this experiment per Parallel-Run Protocol Rule 6).  
**Untouched holdout draws:** `84, 85` (`80–83` consumed in `evidence/h72_1_screen/` and `evidence/h72_2_screen/`).

## 1. Triggering Finding from Complete 83-Raster Lane Audit (`IR-25-ARTIFACTS-RIBBON-SATURATION`)

1. In `H72-1` (`draws 80, 81`) and `H72-2` (`draws 82, 83`), stripping isotropic Family `E` (`E_dist`, `E_dens*`) completely broke `GEMSDOE25`'s `own_lineage` halo convergence (`55.52% <= 70%` max overlap across all `19` prior `GEMSDOE25` downloads, and `60.43% <= 70%` max overlap across all `21` sibling top-scorer rasters; `42.4%` vs `G32 B2 0.2778`) while achieving `HOLDOUT-DTI = 0.11382` (`+0.00606` over `CTRL_BLIND_BD`, `4/4` folds positive).
2. However, after our in-place shared-tool fix added `research/` and `artifacts/` (`83` total unique rasters) to `check_lane_duplicates.py` and `lane_check_extended.py`, `H72-1 A3_PTTG_DEAPRON` triggered `flagged_lane` on two un-thinned historical DEM-scarp rasters in `artifacts/`: `h23-a-6pct.tif` (`335,879` positive pixels = `6.50%` of footprint, `82.0%` forward 3-px overlap) and `r7-nms3-dem10-scarp.tif` (`103,347` positive pixels, `72.9%` forward overlap), because Family `B` concentrates tree splits along topographic scarps already covered by those wide DEM scarp ribbons.
3. Per Parallel-Run Protocol Rule 1, `gems25-h72-pttg-deapron-sapd2-8-k3p0-20261026-a07ef071c49e-zeros.tif` is logged as a DEM-ribbon lane collision (`role = "alternate"`, `DO NOT SUBMIT`) and is **not** modified or post-processed to dodge ribbons.

## 2. Frozen Specification for Experiment 3 (`H72-3`: Pure Subsurface `PTTG + MTHS`, Zero DEM/LiDAR & Zero Family `E`)

To test a genuinely distinct **100% subsurface / cover-blind supervised lane** (combining Rank #1's DEM-free `PTTG` trio with Rank #3's `MTHS` MT Conductive-Pipe & K-Metasomatic Alteration Concordance from `knowledge/29`), Experiment 3 removes **all topographic/DEM/LiDAR features (`Family B`, `X1_*`, `X2_*`, `det_elev_slope`)** and **all Family `E` catalogue features**:

- **Subsurface base columns (`D + X3`, 19 cols):** Family `D` (`17` radiometric, MT conductance/depth-to-base, and GDR #1391 thermal-spring columns) + `X3_gm`, `X3_gd` (`2` gravity–magnetic / gravity–basement cross-products) + `H34` (`3` upward-continued RTP residual & basement-flexure ridges) = `22` control columns (`CTRL_SUBSURF_D`).
- **New `H72_SUBSURF` columns (`5` strictly DEM-free, label-free static columns):**
  1. `PTTG_grav_diffcurv`: Multi-scale (`200 m x 500 m`) Phillips isotropic differential horizontal gravity curvature persistence.
  2. `PTTG_grav_thdr_unit`: Unit-consistent (`mGal/km`) isotropic gravity tilt horizontal derivative.
  3. `PTTG_transtension_loc`: `25 km`-demeaned geodetic dilatation-partitioning transtension anomaly.
  4. `MTHS_pipe_step`: Subvertical MT conductive clay-cap / damage-zone pipe step `sqrt(norm(log1p(cond_surf)) * norm(|grad_h log1p(depth_to_base_surf)|))`.
  5. `MTHS_k_metasom_halo`: Potassium-metasomatic / redox hydrothermal halo `sqrt(norm_inv(D_ThK) * norm(D_UK_edge)) * exp(-d_quartz_gt100C / 40 px)` from GeoDAWN `Th/K`, `U/K` edge, and GDR #1391 `geothermquartz_c > 100 C` upflow points (`dist_known_fault_px` strictly excluded).
- **Paired Arms on Untouched Draws `84, 85` (`evidence/h72_3_screen/`):**
  1. `CTRL_H35`: Exact same-run incumbent (`BDE + EXTRAS + H27_tip + H34`, `sapd2.4`, `kfrac=0.035`).
  2. `CTRL_SUBSURF_D`: Same-run DEM-free & catalogue-free subsurface HGB control (`D + X3_gm + X3_gd + H34`, `d_vis > 2.0 px`, `sapd3.0`, `kfrac=0.030`).
  3. `C1_SUBSURF_PTTG_MTHS`: `CTRL_SUBSURF_D + H72_SUBSURF (5 cols)` (`d_vis > 2.0 px`, `sapd3.0`, `kfrac=0.030`).
- **Leakage Canary:** Every `H72_SUBSURF` column checked via `gems25.validation.feature_canary(..., cap=0.90)` in all 8 cells prior to fitting.
- **Stopping & Packaging Rule:** Hard stop immediately after Experiment 3 (`3/3` budget). Build full-footprint GeoTIFFs (`gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-<cid>-zeros.tif` + `-nan.tif`) from `C1_SUBSURF_PTTG_MTHS`, run all four validators (`check_file`, independent `rasterio`, `check_lane_surface.py`, `check_lane_duplicates.py` + `lane_check_extended.py` across all `85` rasters), and set `verdict = "negative"` (`DO NOT SUBMIT`, `slot_approved = False`) unless both the holdout gate vs `CTRL_H35` (which requires a confirmation stage we have no remaining budget for) and the strict literal lane check pass.
