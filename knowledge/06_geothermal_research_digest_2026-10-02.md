# 06 · Geothermal / fault research digest — statements verified at the cited page (2026-10-02)

Evidence classes: **READ** = text I read at the link this session · **COMPUTED** = reproducible here (script/JSON named) ·
**INFERENCE** = my reasoning, assumptions stated · **UNVERIFIED** = carried over, not read here. Nothing below is a leaderboard fact unless marked.

## 1. Why faults are the target (hidden geothermal systems)
| Statement | Class | Source |
|---|---|---|
| In the Great Basin most geothermal systems are fault-controlled and amagmatic; "nearly all" lie proximal to Quaternary faults. | READ | [Faulds et al., play-fairway keynote](https://www.osti.gov/servlets/purl/1724109) |
| ">85 %" of systems, "especially the relatively high-temperature systems (>130 °C)", sit in *fault interaction zones* — terminations, intersections, step-overs / relay ramps, accommodation zones, displacement-transfer zones — "as opposed to the main segments of range-front faults". | READ | same |
| Upwelling fluids may surface many km from the source or stay blind; the blind McGinness Hills field produces ~88 MW. | READ | same |
| "Promising sites in Cenozoic basins cannot be recognized without detailed geophysical surveys." | READ | same |
| 426 known systems ≥37 °C; ~39 % blind; "as much as 75 %" of the resource may be blind. Settings: step-overs/relay ramps ~32 %, normal-fault terminations 25 %, intersections 22 %, accommodation zones 9 %, transfer zones 5 %, pull-aparts 3 %, bends 2 %, major range-front faults 1 %. | READ | [Faulds & Hinz 2015](https://www.osti.gov/servlets/purl/1724082) |
| Density of geothermal systems and plant capacity correlate generally with tectonic strain rates; "geothermal systems are rare along major range-front faults". | READ | same |
| In north-central Nevada the distance between USGS Quaternary faults and expert labels "can be up to 400 m"; many faults make scarps visible in elevation/slope. | READ | [Hermant et al. 2025](https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2025/Hermant.pdf) |

**INFERENCE for this competition.** The labels reward *faults*, not vents. Interaction zones are where mapped traces end, step over or intersect, so
unmapped secondary strands should cluster at the nodes of the known network (hypothesis family E / H26-3); concealed faults need geophysics
(family A), surface scarps need topography (family B). Whether the hidden test faults follow this is not disclosed by the organizers.

## 2. Data products behind the provided layers
| Product | Fact | Class | Link |
|---|---|---|---|
| INGENIOUS Great Basin Regional Dataset Compilation (GDR 1391) | DOI 10.15121/1881483; **CC BY 4.0**; contents: 2 m temperature probes, earthquake-density models, MT conductance (USGS 10.5066/P9TWT2LU), elevation trend/detrended elevation (10.5066/P9MQRCBY), geodetic shear & dilation, gravity & magnetics (10.5066/P9Z6SA1Z), heat flow (10.5066/P9BZPVUC), paleo-geothermal features, Quaternary faults v1/v2, volcanics, well & spring temperature/chemistry, slip & dilation tendency (10.5066/P9YL58W6). | READ | [GDR 1391](https://gdr.openei.org/submissions/1391) |
| INGENIOUS project | DOE GTO award DE-EE0009254; 1 Feb 2021 – 30 Jun 2025; lists the data releases above plus Kreemer & Young 2022 (crustal strain rates and earthquake rates). | READ | [GBCGE](https://gbcge.org/current-projects/ingenious/) |
| GeoDAWN (USGS) | Airborne magnetics + radiometrics, 2021-11-01 → 2022-11-20; 149,030 line-km over 51,857 km²; Area 1 (Clayton Valley) 200 m lines / 100–150 m drape, Area 2 400 m lines / 150–200 m drape; four acquisition blocks (Winnemucca, Fallon, Hawthorne, Tonopah); "variable terrain clearance should be considered when modeling". DOI 10.5066/P93LGLVQ. | READ | [ScienceBase](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) |
| USGS 3DEP | "All 3DEP products are available free of charge and without use restrictions"; the page advertises a Seamless 1 Meter DEM (S1M) product and 3DEP lidar acquisition "for parts of Nevada & California". Regional S1M availability: UNVERIFIED. | READ (page) | [3DEP](https://www.usgs.gov/3d-elevation-program) |
| Slip & dilation tendency (Siler 2022) | Per-fault-segment results for Quaternary faults "to help identify faults ... appropriately oriented to be stress-loaded for slip or to dilate"; includes the stress data used; shapefile (INGENIOUS area) 27.35 MB. | READ | [ScienceBase](https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d) |
| Reference solution | U-Net (ResNet18), 128 px patches, 5 Monte-Carlo splits, Tversky loss 0.2/0.8, all 19 bands min-max scaled; no DTI implementation. | READ | [GitHub](https://github.com/drivendataorg/gems-prize-reference-solution) |

## 3. Competition mechanics that drive strategy
| Statement | Class | Source |
|---|---|---|
| DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w + ε), triangular kernel, R = 300 m (3 px); TP/FN use the max over predictions within R, FP charges every pixel with p > 0. | READ | [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) |
| Known USGS/INGENIOUS pixels are masked, pixel-exact, identical to the training labels; near-known-but-wrong pixels are fully penalised; new truth can lie within 300 m of known traces ("corrections or modifications"). | READ | [staff 11516/4](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4) |
| Public and private scores each pool the subset's pixels into one Tversky index; chunking undisclosed; final re-evaluation on the whole GeoDAWN area. | READ | [staff 11550](https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-test-pixels-or-mean-of-per-chunk-scores/11550) |
| Training labels come from the INGENIOUS compilation (Ayling et al. 2022); test labels are new faults from NLR/USGS experts; Phase 1 $50 k (top 5 on the private set), Phase 2 $250 k on an expert-expanded label set. | READ | [rules §2, §3.3](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [home](https://www.drivendata.org/competitions/306/competition-doe-gems/) |
| Identity DTI = TP_w / (0.2 (TP_w + FP_w) + 0.8 |G|); adding a pixel helps iff extra credit / extra FP mass > 0.2 DTI / (1 − 0.2 DTI) ≈ 0.052 if DTI were 0.2477. | COMPUTED (algebra, tested; example is conditional) | `src/gems25/metric.py`, `tests/test_metric.py` |
| Conditional hidden-truth size ≈ 12.5 k px (blind-lattice claim 0.0904) and ≈ 12.8 k px (H19-5→dotted claims 0.1922→0.2477): two user/owner-reported, **unverified** inputs give estimates within 2 %. | COMPUTED (unverified owner/user-reported inputs; not live-score verification) | `evidence/why_0_2477.json` |

## 4. Overlooked or under-used official sources (obtainability checked)
| Source | Why it might matter | Obtainable? |
|---|---|---|
| USGS slip/dilation-tendency release incl. stress data | physical orientation prior (H26-4) | Free (item page lists files); **not downloadable from this sandbox** — needs a networked runner |
| GDR 1391 heat-flow maps, 2 m probes, paleo-geothermal (sinter/tufa), volcanics, spring/well chemistry | thermal conduits; sparse, access-biased sampling | Free, CC BY 4.0; spring/well points + probes + paleo already mirrored; heat-flow rasters **not** fetched |
| 3DEP 1 m lidar (raw) | scarp cross-profile templates, drainage offsets (highest ceiling) | Free, no restrictions; raw tiles need CI; descriptors for 706/716 tiles already mirrored |
| GeoDAWN radiometric K/Th/U grids | surface lithology / alteration contrasts across scarps (H26-1) | Free (USGS release); derived 100 m grids mirrored (licence line not on the page text I read) |

## 5. Addendum 2026-10-03 — the organizer's own reference solution, and the H28 recalibration

| Fact | Class | Where / link for manual review |
|---|---|---|
| The organizers publish a **reference solution** (U-Net + Monte-Carlo cross-validation; author Prof. John Lipor, Portland State University). Read on GitHub — *not* on drivendata.org, so AGENTS.md rule 3 is not engaged. It corroborates: `TverskyLoss(alpha=0.2, beta=0.8, mode="binary")` = the published DTI weights; nodata handled as `X[X < -1e38] = NaN` (the mirror's sentinel is −3.4028234663852886e+38); labels read as `y[y < 1] = 0`; per-channel min–max normalisation to [0,1]; 128-px patches, 5 MC splits, test patches zeroed out of the global image to avoid leakage; band semantics taken from **each band's own TIFF tags** (`description`, `data_category`). | OFFICIAL | [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) — README + notebook cells 5, 6, 12, 16; `registry/sources.json#dd-reference-solution` |
| Its submission writer uses the **labels'** CRS/transform, `dtype=y_final.dtype` (float32), `count=1` and **no `nodata` tag**, so the official example file is finite everywhere (zeros outside the study area). This repo's primary download instead writes NaN outside the footprint to match the owner-mirrored `sample_submission.tif`, and ships a zeros-outside fallback. Both conventions are now published side by side; the portal validator is still not public. | OFFICIAL + COMPUTED | notebook cell 19; IR-25-REFSOL-FORMAT |
| The author's inline note — *"it may be advantageous to threshold this map for better scoring"* — points the same way as this repo's binary-optimality lemma: for a fixed support the DTI is a linear-fractional function of `p`, so the optimum is bang-bang and soft values in (0,1) cannot beat a binary emission. | OFFICIAL hint + COMPUTED lemma | notebook cells 17, 20; `evidence/h28_calibration/design.json` |
| The reference keeps a patch only where **"valid elevation data (channel 4)"** is finite, i.e. channel *index* 4 = the 5th band, while the mirror tags its 5th band "Isostatic gravity anomaly slope" (detrended elevation is band 12). Resolved, not left as a doubt: 18 of the 19 bands have **identical** non-finite masks (7,112,688 px = exactly the area outside the 5,167,373-px footprint); the only exception is band 6 `tc`, differing by 12 px of 12,279,292. Channel 4 is therefore a data-validity proxy, **not** an elevation claim, and there is **no band-order discrepancy** between the mirror and the organizer's file. | COMPUTED | IR-25-REFSOL-CHANNEL4 (closed) |
| **Supersedes the §3 row on hidden-truth size** (≈12.5 k from the lattice claim, ≈12.8 k from the H19-5→dotted pair). Five hash-verified anchors — blind lattice 0.0904, H19-5 0.1922, H19-4 0.1894, H16-1 0.1855, d1-5 0.2477 — imply a *single* count under `π ∝ exp(−d(H19-5)/1.85 px)`: 12,498 / 12,472 / 12,893 / 13,358 / 12,691, i.e. **N = 12,691** (max spread 5.3 %). A **uniform** truth is falsified: for the four group surfaces the inversion has no finite solution at all. | COMPUTED, conditional on OWNER-reported scores | `knowledge/10` §5b and §12.1; `evidence/h28_calibration/anchors.json` |
| Emission geometry is now exhausted: `dot_thin(H19-5, d)` peaks at **d = 2.4 px, 44,090 px → predicted 0.25104**, which is the file this repo already ships; a 6-px kernel-disjoint design loses in 9/9 sensitivity cells and costs 0.045 DTI on the holdout. Reaching the reported #1 (0.3195) needs **1.29×** that file's credit density at the same budget — a detection problem, not a geometry one. | COMPUTED (model validated: Monte-Carlo ≤ 0.0020; three anchors reproduced within 0.004) | `knowledge/10` §12.3, §12.4, §12.7; `evidence/h28_calibration/design.json`, `evidence/h28_holdout/results.json` |
