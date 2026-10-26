# New untried geological hypotheses — GEMSDOE25 session 2026-10-26

**Session lane:** wall-to-wall *gridded geophysical* blind-fault signatures derived only from the pinned competition feature stack (static_ABCD.npy: families A–D + E catalogue geometry). No new external data required for any candidate; candidates 4–5 use only layers already in the repo (GDR CSV, LiDAR, geodawn radiometrics, InSAR geodesy, magnetics). Emission recipe for every arm: Hessian ridge NMS (sigma 1.0) → drop visible catalogue pixels pixel-exactly → top-K (K = 0.0245 of eroded domain) → dot_thin(min_dist 1.5 px), fixed pixel count across arms so no contrast is won by emitting more mass. Holdout: spatially blocked hide-and-recover, 4 folds × draws [0,1] screen / [2,3] confirmation, hide_frac 0.20 of whole catalogue components (src/gems25/holdout.py), response = pooled exact sparse-regime DTI (alpha 0.2, beta 0.8, R = 300 m triangular kernel). Leakage canary: standalone feature AUC <= 0.90. Paired gate vs same-run B_crest control: mean gain > +0.001 DTI, >= 3/4 folds positive, worst fold >= -0.01. LANE: pre-placement surface |Spearman| <= 0.90 and final-dot 3-px overlap <= 0.70 vs every registry raster (density-aware symmetric statistic for dense rasters per IR-25-LANE-DENSITY). Pre-register: this document is committed BEFORE any run; a failed arm stays failed.

## Background already established (do not re-propose)
- Family B (DEM curvature/scarp, +0.0253 alone, 4/4 folds) and Family E (catalogue geometry, +0.0610 alone, 4/4 folds) matter alone; A and C are inert alone (knowledge/04). Every owner-reported scorer >= 0.2449 is a pixel subset of GEMSDOE19 H19-5 (catalogue-proximity surface); truth is depleted within ~200 m of mapped faults (forensics, knowledge/26). H35 (BDE+7 add-ons + directed tip + H34 RESMAG-FLEX) passed holdout twice but is a lane stop vs own H31/H35 lineage. H66-1 MGD-F (sparse GDR well geothermometers) screen passed / confirmation failed. GMCE/MSCR/XG1/KDC/GEM/GEM-FUSE1/H31/H36/H37/H38 all negative or lane-blocked (knowledge/19–28).
- What has NOT been tried: wall-to-wall gridded radiometric *ratio* edges (GeoDAWN K/U/Th), the MT conductive-base depth edge combined with radiometric alteration edges, InSAR dilation rate combined with potential-field tilt, and conductivity-gradient × radiometric-edge intersection — all catalogue-free, wall-to-wall, and computed from features already in static_ABCD.npy.

## Candidate 1 (TOP): radiometric alteration-ratio edge × conductive-base edge — H-N1

*Layers:* GeoDAWN gridded radiometrics (bands K, Th, U from `geodawn_rad_u8.tif`/`geodawn_extensions_u8.tif`, columns `D_K`, `D_Th`, `D_U`, `D_ThK`, `D_UK`, `D_UTh`) and MT depth-to-base surface (`depth_to_base_surf`, column `D_depth_base_grad`); family D only, plus catalogue distance `E_dist` as a hard exclusion mask (never a signal).

*Physical signature:* edge-detection (gradient magnitude, 1 px) on two independent physical grids: (a) hydrothermal alteration ratio edges — K-metasomatism or argillic (K-depleted) halos around blind faults appear as sharp K/(Th·U) ratio contrasts in airborne radiometrics; (b) the edge of the conductive geothermal reservoir base (depth_to_base gradient), where blind fault conduits root into the conductive zone. The product is high only where BOTH edges coincide — a narrow, catalogue-free structural line.

*Why it catches catalogue-missing faults:* radiometric alteration and the conductive-base edge respond to subsurface fluid/alteration geometry, not to mapped traces; blind faults hidden under young cover have no scarp (no B signal) and are absent from USGS/INGENIOUS (no E signal), but still cut the radiometric and MT fields. H66 MGD used the same physics at *sparse well points* (610 cells, draw-dependent, confirmation failed); H-N1 applies it wall-to-wall from gridded rasters — different data support, different spatial support.

*How it differs from repo implementations:* no HGB detector, no tip continuation (H27/H31/H35), no submodular cover (H36/H38), no cross-gradient (XG1), no multi-scale crest (MSCR), no SGMC gating (H66-2). Pure physics surface, fixed thin emission. Uses only static columns already computed (zero new data, zero external fetch).

*Expected DTI improvement:* medium-high (alteration + base-edge coincidence is a classic blind-geothermal signature; D main effect was +0.0044 with 4/4 folds positive in the factorial). *Implementation cost:* low (~60 lines, existing columns).

## Candidate 2: geodetic dilation × potential-field tilt — H-N2

*Layers:* InSAR geodetic dilation rate (`geod_dilaterate`, column `geod_dilaterate` + `C_shear_grad`) and magnetic potential-field tilt (`A_mag_tilt`); families C × A.

*Physical signature:* surface dilation (pressurized geothermal upwelling inflates the surface) co-located with the potential-field edge of a blind structure (tilt angle zero-crossings / strong gradient). Product targets blind faults that are actively slipping/inflating but unmapped.

*Why it catches catalogue-missing faults:* dilation is a time-dependent process signal; blind faults active in the InSAR window are invisible to static catalogue mapping. C alone was inert in the factorial (+0.0109? actually C main effect -0.0109, 0/4 folds) — the untested part is C × A conjunction, not C alone.

*How it differs:* H38 OSPC used LiDAR scarp *coherence*, not InSAR dilation; no session combined geodetic rate with potential-field tilt. Cost low. Expected DTI improvement: medium.

## Candidate 3: conductive-clay-cap gradient × total-count radiometric edge — H-N3

*Layers:* MT conductivity gradient (`D_cond_grad`, family D) and edge of gridded total-count radiometrics (gradient of `tc`, the GeoDAWN total-count band).

*Physical signature:* edge of a near-surface conductive clay cap (argillic alteration above blind faults) intersecting a radiometric anomaly edge — a near-surface expression of blind fault-controlled hydrothermal flow, independent of topography.

*Why it catches catalogue-missing faults:* clay-cap and radiometric anomalies form over blind faults with no surface rupture; the intersection is narrow and off-catalogue by construction.

*How it differs:* H-N1 targets the *deep* conductive-base edge; H-N3 targets the *shallow* clay-cap edge — complementary depth windows. No session used D_cond_grad × edge(tc). Cost low. Expected DTI improvement: medium-low.

## Candidate 4: LiDAR strike coherence × off-catalogue radiometric anomaly — H-N4

*Layers:* 3DEP LiDAR strike coherence (`L_coh100`, family B) × gridded radiometric anomaly (`tc`), restricted to pixels > 3 px from any visible catalogue trace (hard E_dist exclusion).

*Physical signature:* persistent linear LiDAR scarp strike (coherence over ~100 m) co-located with radiometric heat, outside the mapped catalogue.

*Why it catches catalogue-missing faults:* LiDAR reveals scarps too subtle for mapping; radiometrics confirm hydrothermal affinity; the off-catalogue restriction forces novelty. Uses B (which matters alone) but the B×D conjunction off-catalogue is untried.

*How it differs:* H31 used LiDAR strike coherence but only as an add-on to catalogue-anchored H35/H36 surfaces; H-N4 is catalogue-exclusion-first. Cost low-medium. Expected DTI improvement: medium-low (B-family signal overlaps E-correlated truth).

## Candidate 5: microseismicity/strain clustering near GDR hot springs — H-N5

*Layers:* earthquake density (`ieq_n100a15`) + strain second-invariant gradient (`C_2ndinv_grad`, family C) × GDR hot-spring proximity (`D_gdr_dist_hot < 2 km`, family D).

*Physical signature:* microseismic/strain clustering funneling into surface hot springs — blind faults as fluid conduits expressed by seismicity, not by mapped traces.

*Why it catches catalogue-missing faults:* seismicity illuminates active blind structures directly; hot springs confirm thermal connection. Requires no new data (GDR CSV already restored). Cost medium (point-process rasterization already implemented in _gdr_features). Expected DTI improvement: low-medium (C inert alone; sparse springs = sparse support).

## Ranking (expected DTI improvement, then cost)

| Rank | Hypothesis | Layers | Signature | Catches unmapped faults because… | Differs from repo by… | Cost |
|---|---|---|---|---|---|---|
| 1 | H-N1 radiometric ratio edge × conductive-base edge | D_K/D_Th/D_U, D_depth_base_grad | gradient-edge coincidence | alteration + reservoir base exist without mapped traces | wall-to-wall gridded radiometry vs H66 sparse wells; no HGB/submodular/tip | low |
| 2 | H-N2 geodetic dilation × magnetic tilt | geod_dilaterate, A_mag_tilt | dilation co-located with potential-field edge | active upwelling over blind structure invisible to catalogue | C×A conjunction never tried; H38 used LiDAR not InSAR | low |
| 3 | H-N3 clay-cap gradient × TC radiometric edge | D_cond_grad, edge(tc) | shallow conductive cap × radiometric anomaly edge | near-surface anomaly over blind fault, no rupture | shallow depth window vs H-N1's deep base edge | low |
| 4 | H-N4 LiDAR coherence × radiometric anomaly off-catalogue | L_coh100, tc, E_dist mask | linear scarp coherence + radiometrics, >3 px from catalogue | LiDAR sees unmapped scarps; radiometrics confirm thermal affinity | exclusion-first; H31 used coherence only as catalogue-anchored add-on | low-med |
| 5 | H-N5 microseismicity × GDR hot springs | ieq_n100a15, C_2ndinv_grad, D_gdr_dist_hot | seismicity/strain funnel into hot springs | seismicity images active blind faults directly | sparse point support; C inert alone | medium |

## Validation rule (this session)
Run H-N1 screen (draws [0,1]) first. Only if the paired gate passes AND leakage canary passes AND surface lane is clear do confirmation (draws [2,3]) and full-footprint TIF packaging proceed. Every other candidate remains documented-but-untried; no slot is spent on an unvalidated idea. Negative screen → H-N1 reported negative, H-N2 becomes next priority (separate session).
