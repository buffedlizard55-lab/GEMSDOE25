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
| Identity DTI = TP_w / (0.2 (TP_w + FP_w) + 0.8 |G|); adding a pixel helps iff extra credit / extra FP mass > 0.2 DTI / (1 − 0.2 DTI) ≈ 0.052 at DTI 0.2477. | COMPUTED (algebra, tested) | `src/gems25/metric.py`, `tests/test_metric.py` |
| Hidden-truth size ≈ 12.5 k px (blind lattice 0.0904) and ≈ 12.8 k px (H19-5 → dotted pair): two independent live-score readings agree within 2 %. | COMPUTED (owner-reported inputs) | `evidence/why_0_2477.json` |

## 4. Overlooked or under-used official sources (obtainability checked)
| Source | Why it might matter | Obtainable? |
|---|---|---|
| USGS slip/dilation-tendency release incl. stress data | physical orientation prior (H26-4) | Free (item page lists files); **not downloadable from this sandbox** — needs a networked runner |
| GDR 1391 heat-flow maps, 2 m probes, paleo-geothermal (sinter/tufa), volcanics, spring/well chemistry | thermal conduits; sparse, access-biased sampling | Free, CC BY 4.0; spring/well points + probes + paleo already mirrored; heat-flow rasters **not** fetched |
| 3DEP 1 m lidar (raw) | scarp cross-profile templates, drainage offsets (highest ceiling) | Free, no restrictions; raw tiles need CI; descriptors for 706/716 tiles already mirrored |
| GeoDAWN radiometric K/Th/U grids | surface lithology / alteration contrasts across scarps (H26-1) | Free (USGS release); derived 100 m grids mirrored (licence line not on the page text I read) |
