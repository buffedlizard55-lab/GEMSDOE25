# 21 · Pre-registration XG1 — surface-free cross-gradient alignment block (2026-10-25)

**Status:** registered before any XG1 fit, feature build on real data, or holdout run in this
session. Session branch `arena/60dab308-gemsdoe25`. Budget: protocol rule 6 (≤3 experiments
or 2 h of experiment time). This document is experiment 1 of this session; a confirmation
stage on fresh draws is experiment 2 and is allowed only if the screen gate passes.

**Evidence classes:** OFFICIAL = read at the cited page (in an earlier session and recorded in
`registry/`, or cited here for manual review) · OWNER = owner-reported score claim in the
brief / `registry/live_scores.json` (never an organizer receipt) · COMPUTED = reproducible in
this repo by a named script + JSON · INFERENCE = reasoning, assumptions stated.
**No number in this repository is ORGANIZER-CONFIRMED.** No DrivenData page is accessed by
automation (AGENTS.md rule 3); the agent never uploads a submission.

**Lane irregularity (flagged, IR candidate):** the brief's PARALLEL-RUN PROTOCOL says "Your
lane is the single method paragraph below", but the message as received in this session
contains no single method paragraph that assigns a distinct lane (the same generic protocol
text appears in the stored brief). This session therefore self-assigns ONE lane — the XG1
cross-gradient block defined in §3 — after checking `knowledge/03–20`, `src/gems25/families.py`
and `registry/` for prior use, and stays inside it. If the owner intended a different lane,
this session's work is a labelled negative/positive result for XG1 only, not for that lane.

---

## 1. Why did GEMSDOE32 `h33-h33-2-b2…-zeros` score the group best (OWNER 0.2778)?

Pixel-exact forensics already in this repo (`evidence/focus_sites_forensics.json`,
`evidence/top_scorer_forensics.json`, COMPUTED from hash-pinned owner mirrors; scores OWNER):

| Step | File (dots) | OWNER DTI | Δ |
|---|---|---:|---:|
| Solid detector | `h19-5` multiline-corroborated surface (121,131 px) | 0.1922 | — |
| Dot it | `dot_thin(h19-5, 1.5 px)` (60,069 px) | 0.2477 | +0.0555 |
| Dot wider | D2.8 budget (44,090 px) | 0.2600 | +0.0123 |
| Delete ≤1 px shell | R1 = D2.8 & d(cat)>1 px (40,199 px; −3,891) | 0.2708 | +0.0108 |
| Delete ≤2 px shell | **B2 = D2.8 & d(cat)>2 px (37,654 px; −2,545 more)** | **0.2778** | +0.0070 |

Mechanism (INFERENCE from the official metric, `src/gems25/metric.py`: α=0.2, β=0.8,
R=300 m triangular kernel, known-fault pixels masked): a truth pixel's credit is the
*maximum* over nearby dots, so a second dot covering the same truth adds ≈0 credit and
≈1 unit of FP mass. Dotting is therefore pure emission economics (+0.068 with no new
geology). A dot set is worth keeping/deleting by its marginal ratio
ΔTP/ΔFP vs τ = α·DTI/(1−α·DTI) ≈ 0.055–0.059 at these scores
(`gems25.metric.marginal_inclusion_ratio`). The nested-chain inversion (COMPUTED, conditional
on OWNER scores and N̂=12,691) implies the deleted 0–1 px shell earned ≈0.0010 credit/px and
the 1–2 px shell ≈0.0050 credit/px — both ≪ τ, so deleting them raised DTI by shrinking the
denominator. It does **not** prove hidden faults avoid mapped traces: the recorded staff
wording says test labels include "corrections or modifications" within 300 m of known
traces, and the catalogue-gap holdout cannot test catalogue-proximity pruning
(IR-25-HOLDOUT-DOES-NOT-TEST-PRUNING).

## 2. Can emission tweaks around B2 beat 0.2778? New registry arithmetic (this session)

`scripts/analyze_b2_microvariants.py` (to be run this session; numbers below were computed
from `registry/live_scores.json` and must reproduce from that script before they are cited
elsewhere) extracts every OWNER-scored post-B2 variant dated ≥2026-10-05 whose label carries
a B2-family emission (excluding the two 37,654-px re-hosts of B2 itself, both OWNER 0.2778):

* **15 micro-variants of B2** (add 54–334 dots, delete 189–4,548 dots, B=2.24/B=2.5/C=2.5
  shells, d=2.9/3.1 spacing, playa/uncorroborated/splay prunes): OWNER scores **0.2720–0.2775,
  every one below 0.2778** (−0.0003 to −0.0058). The two smallest additions (+54 strict-relay
  dots → 0.2775; +104 tip-scarp dots → 0.2775) prove those added sets were below break-even
  (a pure addition that lowers DTI had ΔTP/ΔFP < τ, by the marginal-ratio lemma).
* **4 independent-detector swaps at the same B2/d2.8 emission**: 0.2478, 0.2343, 0.1823,
  0.1816 — far below B2. A better *holdout* detector has repeatedly failed to transfer live
  in this group (proxy↔live Spearman +0.33, n=24, n.s., recorded by GEMSDOE24).

Conclusion (INFERENCE): B2 sits at a local optimum of its emission neighbourhood; the
remaining lever with headroom is mean credit per emitted pixel from a genuinely different
detector signal (≈+4 % for +0.01 DTI at fixed mass; ≈+25–29 % for the OWNER leader claims
0.3195/0.4413, which conflict — IR-25-LEADERBOARD-CONFLICT). Any such claim from this session
will be labelled HOLDOUT-DTI only; a projection is never written as a score.

## 3. Five candidate hypotheses (ranked; top one is this session's lane)

All five were checked against `knowledge/03–20` and `src/` (grep) for prior implementation.
"Expected Δ" is an ordinal planning bracket for HOLDOUT-DTI, not a forecast or a live score.

| Rank | ID | Layers (official source) | Physical signature | Why catalogue-missing? | Difference from this repo | Expected Δ (planning) | Cost | Validatable here? |
|---:|---|---|---|---|---|---:|---|---|
| 1 | **XG1 cross-gradient triple alignment** | Band 13 `iso_grav_anom`, band 02 `rtp`, band 15 `depth_to_base_surf` (competition raster; GeoDAWN DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ), gravity/MT via INGENIOUS GDR 1391 DOI [10.15121/1881483](https://gdr.openei.org/submissions/1391)) | Horizontal-gradient **vectors** of gravity, RTP magnetics and log depth-to-conductive-base are pairwise *parallel* (cross-gradient ≈ 0 in the Gallardo–Meju sense) and jointly strong at σ=1.5 px | A buried fault offsets density, magnetization and basement depth across the *same* plane but makes no scarp; surface mapping (and family B) miss it, single-field edges (family A, factorial main effect −0.0027) are too ambiguous | `X3_gm`/`X3_gd` are orientation-blind products of Hessian *ridge magnitudes*; H31 sub-scarp is a mean of percentile-scaled magnitudes incl. LiDAR; H34 is single-field RTP depth-slicing. No prior column uses gradient-direction alignment, and XG1 is surface-free (no DEM/LiDAR/catalogue input) | 0 to +0.006 | ~1 h (static sidecar from cached bands) | **Yes** |
| 2 | CURV-PERSIST profile-curvature zero-crossing persistence | Band 12 `det_elev` (100 m DEM in competition raster) | Signed profile-curvature zero-crossing persists within 1 px across σ∈{1,2,4,8} px with stable gradient azimuth (monoclinal flexure over a buried fault) | A flexured-but-unbroken surface has no discrete scarp for family B / LiDAR step detectors to catch, so the fault stays uncatalogued | B carries Laplacians at two fixed scales as raw HGB channels; no explicit cross-scale persistence/azimuth-stability conjunction exists. (Listed as GEM-CURV in knowledge/17 of a parallel session; never implemented) | 0 to +0.005 | ~2 h | Yes |
| 3 | SPRING-ALIGN hot-spring/well alignment density | `external/gdr_wellspring_in_footprint.csv` (GDR 1391, CC BY 4.0, already pinned) — temperature-weighted points | Anisotropic (oriented-kernel) line density: max over 12 strikes of along-strike hot-point density minus isotropic density | Geothermal upflow localises along permeable concealed faults; aligned springs trace the fault even where no trace is mapped. Vents/samples are independent of the fault catalogue | Family D uses isotropic distance/KDE/max-temperature only (`D_gdr_*`); GEM-2 used vent *proximity* (failed). No oriented-alignment transform exists | 0 to +0.004 | ~3 h (point data are sparse/biased) | Yes, weakly (sampling bias) |
| 4 | EQ-RIDGE seismicity-density gradient ridge | Bands 10/16 `deq_n100a15`/`ieq_n100a15` | Ridge strength of log earthquake density × structure-tensor coherence (linear seismicity boundary) | An active blind fault can bound a seismicity cluster before it is mapped geologically | Family C uses strain invariants + raw densities; no log-density ridge/coherence. **Weak prior:** the 100 km / 15° kernel implied by the band name cannot localise to 300 m, and band semantics are aliased (IR-25-BAND-ALIASES) | ≈0 to +0.002 | ~1 h | Yes, low value |
| 5 | SHORELINE-SUPPRESS Lahontan bench mimic mask | Absolute elevation — **not in the provided bands** (`det_elev` is detrended). Free official source: USGS 3DEP staged DEMs via [The National Map downloader](https://apps.nationalmap.gov/downloader/) | Suppress scarp features whose absolute elevation lies in the Lake Lahontan highstand bench band (~1318–1341 m; Adams & Wesnousky 1998, cited in knowledge/19) | Removes the named non-fault mimic (pluvial shoreline benches) that family B mistakes for scarps, raising credit density of kept dots | No absolute-elevation layer exists in this repo; the LiDAR cache holds only per-100 m derivative descriptors | Unknown | Days + external fetch | **No — blocked here:** `apps.nationalmap.gov` is outside the sandbox allowlist (github/pypi/npm only) and no byte-pinned absolute DEM is in `registry/data_manifest.json`. Deferred, not viable in this session |

**Named non-fault mimic for XG1:** a lithologic/intrusive contact (e.g. caldera ring margin or
a dipping flow contact) steps gravity, magnetics and apparent basement depth along one
boundary with parallel gradients and no fault offset. Survey line-levelling artefacts can
also align gradients in RTP and gravity grids if both were levelled to the same flight lines.

## 4. Frozen XG1 feature definition (no tuning after outcomes)

From the cached band grids in `data/work/bands/` (`02_rtp.npy`, `13_iso_grav_anom.npy`,
`15_depth_to_base_surf.npy`), after `gems25.features.nearest_fill`:

1. Smooth each field with a Gaussian σ=1.5 px; take horizontal gradients (gy, gx) by
   `numpy.gradient`. Depth field is `log1p(max(depth,0))` before smoothing.
2. Normalise each gradient *magnitude* by its 99th percentile over the footprint
   (computed on a fixed 200k-pixel sample, `numpy.random.default_rng(1)`, mirroring
   `gems25.experiment.Context` scaling; the exact sample rule is in the code and unit-tested).
3. For each pair (g,m), (g,d), (m,d): alignment `A = |u·v|` of the unit gradient vectors
   (0 where either magnitude is 0); joint strength `S = min(|u|n, |v|n)` of the normalised
   magnitudes; column = `ridge_strength(A·S, σ=1.5)` clipped to finite float32.
   Columns: `XG_gm_align_ridge`, `XG_gd_align_ridge`, `XG_md_align_ridge`.
4. Sidecar `data/work/xgrad_columns.npy` (3 × n_footprint float32) + `.names.json`, built by
   `src/gems25/xgrad.py` (pattern copied from `src/gems25/h34.py`). No catalogue/label input
   anywhere ⇒ the only leakage route is a bug; the per-feature holdout AUC canary (≤0.90)
   is still run and reported for every cell.

## 5. Frozen holdout design (reuse, don't rebuild)

* Harness: `gems25.experiment.Cell(extras=True, h27=True)`, hide-and-recover
  (`gems25.holdout`: whole 8-connected components hidden, 1.5 km collar, visible-only
  catalogue features, visible faults masked pixel-exactly), evaluator
  `gems25.metric.dti_binary` (α=0.2, β=0.8, R=3 px/300 m triangular kernel) via
  `Cell.evaluate`. Emission for every arm: ridge-NMS → drop visible-catalogue pixels →
  top-K with KFRAC=0.035 → `score_ordered_dots(..., 2.4)` (sapd2.4), exactly as
  `scripts/run_h35_factorial.py`.
* Arms (one shared Cell per fold×draw; HGB `HGB_PARAMS`, seed=draw):
  `C` = BDE+7 · `B35` = C + `H27_tip` + 3 H34 columns (the H35 primary; **best same-run
  control**) · `X` = B35 + 3 XG1 columns (**primary**).
  A diagnostic `Xonly` = C + 3 XG1 columns may be reported but is **never promotable**.
* **Screen draws 14, 15** (unused by H26–H35 screens/confirmations: used draws are
  0–13 as recorded in knowledge/04–20). **Confirmation draws 16, 17 only if the screen
  gate passes.** No re-runs, no post-hoc arm/draw changes.
* **Gate (primary X vs same-run B35, each stage separately):** mean paired gain > +0.001,
  ≥3/4 folds positive, worst fold ≥ −0.010, mean hug-share increase ≤ +0.10, canary
  max(single-feature AUC, 1−AUC) ≤ 0.90 for all 3 XG1 columns in every cell.
  Reported per stage: HOLDOUT-DTI per arm (fold means, mean, 95 % CI by t over 4 folds),
  withheld positives per fold, paired per-fold gains + CI, hug, canary.
* Comparator discipline (IR-25-COMPARATOR-DRIFT): only same-run paired contrasts are gates;
  historical absolute numbers (e.g. 0.152003389) are records, not baselines.

## 6. Lane, file-build and slot rules (frozen)

* Lane check on the **pre-placement surface** and the **final dots** vs every restored
  registry raster (`scripts/check_lane_duplicates.py` outputs + a density diagnostic):
  duplicate/stop if |Spearman| > 0.90 or >70 % of candidate dots lie within 3 px of one
  registry raster's dots. The dense 5-px r13 lattice calibration probe makes the *literal*
  rule fail for every possible in-footprint file (100 % of pixels are within √8≈2.83 px of a
  5-px grid point; IR-25-LANE-DENSITY) — both the literal verdict and the verdict against
  substantive (sparse detector) registry rasters are reported, never silently substituted.
* **A unique TIF is built in either gate outcome** (owner's highest-urgency deliverable),
  from the full-footprint X recipe (3 pseudo-new draws, pattern of
  `scripts/build_h35_candidate.py`), written only via
  `gems25.submission.write_submission` / audited by `check_file`: single-band float32,
  EPSG:32611, 3730×3292, template geotransform, values in [0,1] at all 5,167,373 footprint
  pixels. Primary convention: **zeros outside** (no NaN anywhere ⇒ passes the strictest
  whole-array [0,1] validator behind the reported portal error); NaN-outside twin shipped
  alongside. No B=2 catalogue-shell prune is applied (the holdout recipe is kept exact;
  B=2 is a live-calibrated step for a *different* surface and applying it here would break
  holdout↔file correspondence — recorded as a limitation).
* **Slot verdict follows the gate, not the build:** `promote` only if screen **and**
  confirmation pass, the substantive lane check passes, and the exact file passes all hard
  format checks. Otherwise `negative` / DO NOT SUBMIT. `slot_approved` stays false in all
  registry entries created by this session (promotion to a weekly slot is the owner's
  separate selector step; the agent never uploads).
* Unique content-addressed filename `gems25-xg1-crossgrad-…-<content_id>-zeros.tif`,
  SHA-256 receipt, DrivenData note ≤140 characters, one JSON run card
  (`registry/run_card_xg1_2026-10-25.json`) with: hypothesis; mechanism; named mimic;
  HOLDOUT-DTI + CI + withheld positives + evaluator; correlation/overlap vs registry;
  raster sha256; validator output; submission name + note; verdict promote/negative.

## 7. Limitations stated in advance

* HOLDOUT-DTI is a catalogue-gap proxy, not a competition score; XG1 is designed for
  *buried* faults, which the proxy (truth = hidden catalogue components, mostly
  surface-expressed) may under-reward. A holdout pass is necessary, not sufficient.
* All competition scores above are OWNER claims; leaderboard claims 0.3195 vs 0.4413
  conflict and neither is verified here.
* Inputs are SHA-256-pinned owner mirrors, not organizer-authenticated bytes
  (IR-25-PROVENANCE).
* 2 CPUs / ~4 GB RAM, no GPU: HGB only, no raw 1 m DEM processing.
