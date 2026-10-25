# GEMSDOE32 H33-2-B2 (0.2778) forensic + 5 new hypotheses (2026-10-25)

**Evidence classes:** OFFICIAL (read at cited page), OWNER-CLAIM (sibling site reported score/receipt, not organizer receipt), COMPUTED (script+JSON in this repo), INFERENCE (stated assumption). No drivendata.org page was fetched (AGENTS.md rule 3).

## 1. Why h33-h33-2-b2-…-e5eb6e7e scored 0.2778 (OWNER-CLAIM 0.2778, not organizer receipt)

**Source:** GEMSDOE32 docs (fetched via GitHub API 2026-10-25, hash-pinned in this repo's `registry/data_manifest.json` for the cited rasters). The live leaderboard claim (0.2778) is OWNER-CLAIM; the byte-level forensic is COMPUTED from owner-mirrored rasters (not organizer-authenticated, IR-25-PROVENANCE).

### Mechanism (COMPUTED from rasters)

- Base file D2.8 (44,090 dots, owner-claim 0.2600) → H27-4-R1-SOLO (40,199 dots, 0.2708): exactly `D2.8 dots within 1 px (100 m) of existing_faults.tif deleted` (3,891 dots). Verified pixel-exact: `(D2.8 AND dist>1) == 0.2708`, 0 discrepancies. `existing_faults.tif sha256 == labels.tif sha256 == 7ba308ccdc…` (COMPUTED).
- H33-2-B2 (37,654 dots, 0.2778): exactly `0.2708 base with dots at 1<d≤2 px (100-200 m) deleted` (2,545 dots). `champ == b2synth` pixel-exact (COMPUTED, GEMSDOE32 evidence/arena41_forensic.json, independently reproduced here via `scripts/arena_forensic_check.py` pattern).
- D2.8 shell counts (COMPUTED): 0<d≤1: 3,891; 1<d≤2: 2,545; 2<d≤3: 2,171; 3<d≤5: 3,466; >5 px: 32,017.

### Why deletion helps (metric arithmetic, OFFICIAL metric page 967)

DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w) with triangular kernel k(d)=max(1-d/300m,0). Adding one dot changes denominator by exactly 0.2 regardless of credit, so the inclusion condition is **credit > 0.2*DTI** (COMPUTED: ~0.0520 at DTI 0.26, 0.0556 at 0.2778, `src/gems25/metric.py::marginal_inclusion_ratio`). The live-scored inversion (DTI gap +0.0108 for deleting 3,891 dots) implies those 3,891 dots earned mean credit **0.002-0.004 per dot** — far below 0.052-0.0556 break-even (COMPUTED via DTI inversion, `evidence/arena41_forensic.json` family table). Shell 1<d≤2 earned **0.004-0.016 per dot** (SGMC proxy) — still <0.0556. Removing them is a pure denominator reduction.

### Why it was the highest of the listed sites

- All other listed rasters keep those low-credit flank dots. The D2.8→B1→B2 pruning chain removes ~14.6% of D2.8 mass (3,891+2,545) that the scorer (which masks catalogue pixels, staff thread 11516, OFFICIAL forum clarification via secondary citation in GEMSDOE32) gives near-zero credit for, unless hidden truth sits within 200 m of a mapped trace.
- The group's own SGMC off-catalogue instrument shows 70.9% of D2.8 mass lies within 300 m kernel of a mapped fault — i.e., mostly flank mass — so the prune has large leverage at this operating point (OWNER-CLAIM instrument, not organizer truth).
- No other listed site does this exact B=2 exclusion; GEMSDOE31 h27-4-solo-d28 (0.2708) is B=1 only; GEMSDOE28 variants (0.2707-0.2710) use tip/euler geometry, not flank pruning.

### Limits (INFERENCE, flagged)

- Pruning helps IFF hidden truth rarely lies within 200 m of a mapped trace. That prior is untestable from public data (IR-32-PROXY-01, IR-25-PROXY-LIMITS). The hide-and-recover holdout truth IS the catalogue, so it cannot validate or falsify flank pruning — it rewards hugging the catalogue.
- The 0.2778 projection (0.2747) vs owner-claim 0.2778 differ by 0.0031, within model noise; no organizer receipt exists for either. The current organizer leader (0.4413, OWNER-CLAIM from sibling site reading drivendata leaderboard via human snapshot) would need +25% credit density (0.0652 vs 0.0520) — pruning alone cannot reach it (INFERENCE, GEMSDOE32 §4).
- The lattice raster (13GEMSDOE, 206k dots, 5-px grid) gives 100% dot-overlap for ANY emission — a density artefact, not a lane violation (IR-25-LANE-DENSITY, logged).

## 2. Can we beat 0.2778? Honest answer (COMPUTED + INFERENCE)

- Not on pruning alone. The B=2 shell is already near the break-even bar (0.016 vs 0.0556). B=3 shell (2<d≤3) earns 0.064 per dot (SGMC proxy) >0.0556, so B=3 prune would likely hurt (+0.0013 live-mirror, safety 1.27 <2.0, GEMSDOE32 Table §2.3).
- To reach 0.3195-0.3262 needs +18-25% mean credit per dot at fixed budget (COMPUTED: 0.1400 vs 0.1084 at DTI 0.26). That requires a better detector, not just emission trimming (INFERENCE from H28 model, `evidence/emission_model.json`).
- GEM-1 blind magnetics gives +0.018-0.0216 HOLDOUT-DTI vs B-crest control (COMPUTED, `evidence/gem_validation/results.json`, 4/4 folds, AUC 0.56 no leakage). It is a detector improvement on the catalogue-gap proxy, but proxy↔live Spearman is +0.33 (n=24, n.s.), so not a live guarantee (IR-25-PROXY-LIMITS).

## 3. Five new candidate hypotheses (ranked by expected DTI improvement × validatability ÷ cost)

All differ from GEMSDOE25 families A-E, H26-0..H30-3, H31-1 (checked vs `knowledge/03`, `11`, `13`, `15` and `src/gems25/families.py`).

| Rank | ID | Layers (official source) | Physical signature | Why it catches catalogue-missing faults | Difference from repo | Expected ΔDTI (planning bracket, not forecast) | Cost | Validatable now? |
|---|---|---|---|---|---|---|---|
| 1 | **GEM-FUSE1: blind magnetics + B2 pruned emission** | RTP band 02 (GeoDAWN DOI 10.5066/P93LGLVQ, via pinned mirror) × relief band 22 (LiDAR-derived, 3DEP) → GEM-1 surface; then emission with catalogue buffer 2 px (= H33-2 mechanism) | RTP horizontal-gradient max where relief is low (concealed block juxtaposition without scarp; vent-poor blind fault). Emission: Hessian ridge NMS (σ1.0) → drop catalogue → top-K (0.0245×eroded domain) → score-ordered Poisson 2.4 px + delete dots ≤2 px of catalogue | Blind faults lack Quaternary scarp, so they hide in the low-relief edge population that family B (scarp) misses. Pruning removes the low-credit flank mass that the live scorer penalizes (verified B2 shells → <0.016 credit/dot) | No prior file combines a non-scarp magnetic detector with H33-2 emission pruning. H33 used the old H19-5 surface; GEM-1 is unsupervised physics surface, not HGB | 0 to +0.010 (detector) + up to +0.007 (prune) = bracket 0…+0.012 on holdout; live unknown | ~1 h (surface already cached) | Yes — both layers cached, AUC canary already 0.56, lane pre-checked vs registry (max 0.162 substantive overlap). **Top candidate** |
| 2 | **GEM-CURV: multi-scale curvature zero-crossing persistence** | Cached `det_elev` + `det_elev_slope` bands 12/19 (100 m DEM, USGS 3DEP via competition raster) → signed curvature at σ=2,4,8 px, zero-crossing persistence | Persistent flexure/curvature boundary across scales marks buried break even where mapped trace absent; scale persistence suppresses single-scale noise that creates false LiDAR scarps | Current H30 uses LiDAR scarp descriptors (max/step/relief) and tip/relay geometry, not curvature-scale-space persistence. GEMSDOE32 describes related curvature work, so registry overlap check is mandatory | Unknown; medium (filter stack) | Requires cache restore (done); needs leakage canary before fit |
| 3 | **GEM-XGRAD: differential geodetic-strain ridge × basement-depth discontinuity** | Geodetic dilation/shear bands 07/08 (UNAVCO GNSS strain, via competition) × depth_to_base_surf band 15 (USGS basement) → cross-gradient alignment ridge | Loaded, permeable structure localizes strain and coincides with basement step beyond mapped network (transtensional jog, blind segment) | Repo uses these as generic HGB channels; this is a frozen cross-gradient geometry (co-located ridge coincidence with tolerance), not a generic interaction | Unknown; medium-high (leakage control per-input) | Bands present; needs per-input AUC canary |
| 4 | **GEM-SCARP-FREE: multi-physics edge agreement (no DEM)** | Gravity HG band 18 × magnetic HG band 03 × basement gradient band 15 → co-located edge ridges within frozen tolerance | Buried fault creates coincident density/magnetization/depth boundary without surface scarp, invisible to LiDAR family B | Related concealed-step H26-3 exists in repo (gravity∧magnetic) but not plus basement, not scarp-free by design; this is deferred as replication control, not novel | Unknown; low/moderate if caches exist | Caches exist but flagged as not novel here; not spending slot |
| 5 | **GEM-HYDRO: hydrothermal water-chemistry / temperature discontinuity** | USGS Water Services API (https://waterservices.usgs.gov/) — groundwater T + chemistry (NWIS), aggregated with sampling-date/well-depth controls → coherent TDS/temperature anomalies along blind structures | Geothermal upflow produces thermal/solute halos; coherent anomaly identifies active system, not just mapped fault | Not implemented anywhere in this org; external observational layer, not raster transform | Unknown; high (bias, support, coverage) | **Blocked:** endpoint not verified from sandbox (was not checked this session), coverage/schema/licence unchecked; needs free official source check before viable (deferred) |

Ranking rationale: GEM-FUSE1 ranks first by combined expected gain and immediate validatability (surface exists, holdout harness exists, lane pre-check clean, leakage already passed, 0.5-day cost). GEM-CURV and GEM-XGRAD are viable but costlier and overlap published GEMSDOE32 curvature/basement work, requiring registry similarity checks. GEM-HYDRO is blocked on external data verification.

## 4. Sources (for manual review)

- Competition metric (DTI α0.2 β0.8 R300m): https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (OFFICIAL, read 2026-10-02, cited in `src/gems25/metric.py`)
- Masking clarification (staff thread 11516: known fault pixels masked pixel-exact): https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516 (OFFICIAL secondary, via GEMSDOE32 citation)
- GeoDAWN magnetic/gravity/radiometric grids: https://doi.org/10.5066/P93LGLVQ (OFFICIAL, USGS)
- Competition data mirrors (hash-pinned owner mirrors, not organizer-authenticated): `registry/data_manifest.json` (pins: training_features 4371c82e…, sample_submission 2176d08e…, labels 7ba308cc…, GeoDAWN-derived extensions a35a9c6d…)
- GEMSDOE32 forensic (owner-mirrored rasters bytes + owner-claim 0.2778, not receipt): https://buffedlizard55-lab.github.io/GEMSDOE32/docs/research/why-02778-analysis-20261025.html and `evidence/arena41_forensic.json` (OWNER-CLAIM claim + COMPUTED forensic)
- This repo's holdout evaluator `src/gems25/metric.py` (OFFICIAL metric implementation verified 300 trials) and `src/gems25/holdout.py` (buffered whole-segment hide-and-recover, α0.2 β0.8 300m triangular kernel, mask visible faults pixel-exact, score pooled DTI)

## 5. What this session will do (frozen before any new fit, AGENTS.md rule 4)

1. Validate GEM-FUSE1 on spatially-blocked hide-and-recover (folds NW/NE/SW/SE × draws 0,1 screen → 2,3 confirmation if screen passes). Response: pooled DTI α0.2 β0.8 R=3 px. Leakage canary AUC ≤0.90 per feature alone before fit. Lane check vs registry (Spearman>0.90 or >70% dots within 3 px = duplicate → stop). Gate: mean paired gain vs same-run B_crest control >+0.001, ≥3/4 folds positive, worst ≥-0.01. No weekly slot unless gate passes on exact artifact plus `src/gems25/submission.py::check_file` audit (CRS/shape/transform match, 5,167,373 footprint pixels finite in [0,1], NaN outside).
2. Do not rebuild GEMSDOE32's H33 file; the lane check forbids >0.90 correlation or >70% dot overlap with any registry raster (PARALLEL-RUN PROTOCOL lane 1).
3. Budget: 3 experiments / 2 h. End with one JSON run card (hypothesis; mechanism; mimicking non-fault process; holdout DTI+CI; correlation/overlap vs registry; raster sha256; validator output; submission name+≤140ch note; verdict promote/negative). Negative is a deliverable.

