# ROD-1 pre-registration — 2026-10-26

## Scope and decision

The supplied prompt refers to a single method paragraph but contains none. This session explicitly adopts **radiometric offset discontinuity (ROD-1)** as its one provisional geological lane, not an interpretation that another parallel session has reserved it. No other geological candidate will be run. Next-step review first: H66-2 is a pending confirmation, but SGMC tree-inversion/compilation contamination remains unresolved; it is not silently promoted. Strict literal overlap rules remain in force, including the dense lattice.

Before outcome inspection: one screen (four quadrants, draws 60 and 61), at most a confirmation on draws 62 and 63 if all gates pass. Budget <=3 experiments / 2 hours. No competition slot or automated DrivenData access. Negative results are deliverables.

## Ranked hypotheses (scientific judgments, NOT score predictions)

Novelty scope is this checkout's implementation, not all research or every sibling repository. Search of `src/` and `knowledge/` found no implementation of the following specific transforms. All use SHA-pinned owner mirrors already restored; no new official-source bytes or licenses are asserted. Official source records for manual review: [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [3DEP](https://www.usgs.gov/3d-elevation-program), [GDR 1391](https://gdr.openei.org/submissions/1391). These hosts cannot be re-fetched from this environment. Availability of mirrored inputs is not authentication of the original data.

| Priority / expected improvement (qualitative) | Layers and specific signature | Missing-fault mechanism and difference from prior implementation | Named non-fault mimic | Cost |
|---|---|---|---|---|
| 1 / uncertain, best testability | GeoDAWN K, Th, U cached channels + 3DEP step/coherence: across four orientations, compare cross-line radiometric mismatch at zero along-line shift with mismatch at +/-200 m shift; retain positive normalized matching improvement, corroborated by a scarp. | A discontinuously displaced compositional pattern can mark shear without a mapped Quaternary trace. Unlike X1 directional contrast, ROD tests **registration improvement from tangential translation**, not the size of an edge. | Offset volcanic flow lobes, fan sediment sorting, airborne mosaic seams; magnetic/thermal data cannot make these causal claims certain. | Low/medium, CPU stencil and one paired screen. Selected. |
| 2 / uncertain, lower prior | Same K/Th/U + detrended elevation: local radiometric texture correlation on opposing fan sectors after reflecting about terrain ridges, detecting truncated fan provenance. | Blind fault segmentation may interrupt depositional continuity; distinct from pointwise ratios and DEM crests. | Drainage capture and avulsion. | Medium; not run. |
| 3 / uncertain, lower prior | RTP and gravity: orientation-resolved zero-crossing separation asymmetry under upward smoothing, conditioned on multi-scale basement-depth change. | Asymmetric widening of two opposite contact flanks could flag concealed tilted blocks rather than known surface scarps. Unlike DOC's one fixed lag or GMCE's gradient parallelism, use change in **paired-flank width asymmetry**. | Dipping intrusive contacts and remanent magnetization. | Medium/high; not run. |
| 4 / uncertain, lowest prior | GDR spring/well chemistry + elevation: local salinity/temperature rank discontinuity across equipotential terrain bands, conditional on matched elevations and sample type. | Tests compartmentalization across blind seals rather than proximity to hot points (H66/MGD). | Pumping, evaporation and lithologic aquifer boundaries. | High; sparse sampling may make it non-identifiable; not run. |

No numeric expected DTI gain is fabricated. These are falsifiable interpretations, not independently verified discoveries of faults or vents. The contest response is fault pixels, not geothermal-vent locations.

## Frozen ROD computation

Normalize each cached D_K/D_Th/D_U channel to [0,1] with footprint 1st/99th percentiles, retaining a joint finite-data mask. Use integer normals (1,0), (0,1), (1,1), (1,-1); opposite sides are sampled at +/-2 times the normal, with the second side shifted by +/-2 times its perpendicular tangent. Diagonal stencils therefore have longer physical lengths; this is explicitly a discrete multiorientation detector, not isotropic 200 m sampling. For each orientation compute squared three-channel mismatch D0 and minimum shifted mismatch Ds. Offset evidence is max(0,(D0-Ds)/(D0+Ds+0.01)) * sqrt(D0/3), maximized across orientations. Missing support or out-of-grid samples contribute zero, never wraparound. Scarp support = sqrt(percentile_scaled(L_step_max) * clip(L_coh100,0,1)). Primary surface = sqrt(offset * scarp_support). No labels enter these surfaces.

Diagnostic 2x2 response: uniform, offset only, scarp only, primary offset x scarp. Shared ridge NMS / score-ordered dots, 3.5% top budget, spacing 2.4 px; mask visible catalogue pixels exactly. Uniform arm has deterministic ties and is a diagnostic, never a meaningful geological comparator. Same-run H35 (BDE+7+H27_tip+H34 columns) is the required incumbent comparator; no prebuilt full-catalogue raster is scored as out-of-fold truth. Use shared Holdout/Cell/metric/writer, no private evaluator or writer.

## Ordered safety and performance gates

1. Full-grid primary surface rank audit against the available restored registry before placement; missing, incompatible, undefined or |rho|>0.90 -> stop. Registry incompleteness beyond restored manifests must remain disclosed.
2. Each used feature separately on each buffered whole-component hide-and-recover cell: finite-pair AUC, missingness AUC and max(AUC,1-AUC). Missing classes / no finite values / suspicious discriminative AUC >0.90 -> block trust. Run incumbent feature canaries too; a failed incumbent audit prevents a 'beats best' claim.
3. Pooled HOLDOUT-DTI (alpha .2 beta .8, triangular radius 300 m) from sums of TP/FP/FN; 95% spatial quadrant cluster-bootstrap CI, 10,000 resamples, seed 26026. Report summed positive occurrences and distinct withheld pixels separately. Four clusters give weak uncertainty resolution; no claimed leaderboard forecast.
4. Primary must beat same-run H35: pooled gain >0.001, paired cluster-bootstrap lower bound >0, >=3/4 positive fold gains, worst fold >=-0.010. Screen pass is not confirmation; only fresh confirmation passing the same conditions permits promotion consideration.
5. Final full-footprint dots are checked against every available registry raster; >70% of candidate dots within 3px of ANY raster, or |rho|>0.90 => duplicate-lane stop, no second hypothesis or density waiver. If stopped before writing, raster/name/validator remain null. Do not generate random/jittered dots to evade this gate. Unique bytes alone are insufficient.
6. Writer and exact-file validator are called only after the final-dot gate passes. A gate-negative but lane-clean diagnostic may be saved with DO NOT SUBMIT status; it is not a slot recommendation. Automatic readiness additionally requires fresh confirmation, registry completeness, exact-template validation and separate selector authorization. No authorization is available this session.

## Evidence labeling

Historical user figures (including 0.2778, 0.3195 and 0.4413) remain OWNER-REPORTED, not ORGANIZER-CONFIRMED; refusing to mislabel them takes precedence over forcing every number into one of two inaccurate categories. All freshly measured performance is HOLDOUT-DTI with evaluator hash, counts and CI. Geometry counts, AUC and hashes are COMPUTED diagnostics, not DTI scores.
