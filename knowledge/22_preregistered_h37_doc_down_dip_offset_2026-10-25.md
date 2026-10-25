# 22 · Pre-registration H37 — down-dip offset concordance (DOC), session 7 (2026-10-25)

Written **before any H37 feature is computed on real data and before any fit** (AGENTS.md
rule 4). Branch `arena/97b7bf66-gemsdoe25`. Evidence classes: OWNER = supplied in the
owner brief / read on sibling GitHub-Pages sites (not organizer receipts) · COMPUTED =
reproducible in this repo · HOLDOUT-DTI = hide-and-recover proxy numbers only ·
INFERENCE = reasoning with assumptions stated. **No number here is ORGANIZER-CONFIRMED.**
No DrivenData page is accessed by the agent (AGENTS.md rule 3).

## 0. What is already established (and is re-verified this session before any fit)

* The owner-reported 0.2778 file (`GEMSDOE32 h33-h33-2-b2`, 37,654 dots) is, COMPUTED
  from hash-pinned owner-mirror rasters (`evidence/focus_sites_forensics.json`,
  `evidence/why_0_2477.json`), pixel-identical to `D2.8 & (d(catalogue) > 2.0 px)`:
  the dot-thinned H19-5 surface at the 44,090-px budget minus 3,891 dots at ≤100 m and
  2,545 more at 100–200 m from the catalogue. The implied mean credit of the deleted
  shells (0.0010 and 0.0050 per px) is far below the DTI break-even
  `α·D/(1−α·D)` = 0.0588 at D=0.2778 (`gems25.metric.marginal_inclusion_ratio`), so the
  OWNER increment chain 0.1922 (solid) → 0.2477 (dotted d1.5) → 0.2600 (d2.8) →
  0.2708 (better base, B1) → 0.2778 (B2) is quantitatively consistent with
  *emission economics on a fixed detector*, not with new geology at steps 1 and 3.
  This session re-verifies the B1/B2 identities from restored rasters
  (`scripts/verify_b2_chain.py` → `evidence/h37_b2_recheck.json`) before fitting.
* Beating 0.2778 at constant emitted mass needs ≈+4 % mean credit per emitted pixel
  per +0.01 DTI; the owner's 0.3195 needs ≈+25 % (INFERENCE from the same algebra).
  Emission-only variation on existing surfaces is nearly exhausted in this repo's
  evidence (H28 calibration, H31 credit-field −0.0007, KDC complement efficiency
  R=0.505 < 1). The remaining lever is credit density from a better detector.
  **No live score above 0.2778 is claimed or claimed-able from the holdout alone**
  (proxy↔live Spearman +0.33, n=24, n.s., per GEMSDOE24 record).
* Leaderboard figures in the brief conflict (0.4413 vs 0.3195; GEMSDOE32 recorded
  0.3262 on 2026-10-04). IR-25-LEADERBOARD-CONFLICT stays open; no leaderboard number
  is used as a target or a gate.

## 1. The single lane for this session (PARALLEL-RUN PROTOCOL item 1)

> **H37-1 DOC — down-dip offset concordance.** Add exactly six static columns to the
> twice-holdout-validated H35 arm-B detector (BDE + 7 add-ons + `H27_tip` + 3 H34
> RESMAG-FLEX columns; HGB and emission `sapd2.4 / kfrac 0.035` frozen). For each of
> three subsurface ridge fields — isostatic-gravity HG ridge, TMI HG ridge, and the
> H34 conductive-base flexure ridge — sample the field at lags of +2 and +4 px along
> the local **downhill** unit vector of the smoothed detrended DEM (the basinward dip
> proxy for a ~60° normal fault) and at −2, −4 px uphill. The six columns per field
> pair are `down = max(S(x+2u), S(x+4u))` and `asym = down − max(S(x−2u), S(x−4u))`,
> evaluated at the candidate *surface-trace* pixel x. Nothing else changes. The
> comparator is H35 arm B recomputed in the same run (same Cell, same train sample).

Physical target: a buried piedmont/basin-margin normal fault offsets basin fill
against bedrock at depth; the potential-field / conductive-base step produced by
that contrast is laterally displaced 100–400 m basinward (down-dip) of the eroded or
buried surface trace. Every existing concordance feature in this repo is zero-lag
(pixel-coincident products: X3, H31 sub-scarp, H34 flexure ridge), so a tree given
only zero-lag fields cannot represent "strong step 300 m downhill of a weak scarp".

**Named non-fault mimics (in advance):** (i) alluvial-fan wedges prograding off an
unfaulted bedrock slope (a downslope-offset density/conductivity step with no fault);
(ii) lava-flow and intrusion margins (magnetic step offset from a topographic break);
(iii) pluvial Lake Lahontan shoreline benches (topographic break whose downhill
direction tracks contours, with coincidental subsurface steps).

This operationalizes H31-2 ("anisotropic dip-asymmetric gravity–topography step",
knowledge/14 flank register, ranked #2 there, **proposed but never implemented or
fit**) and generalizes it from one gravity field to three subsurface fields with an
explicit signed asymmetry. It is not H34 (depth-sliced zero-lag ridges), not Euler
deconvolution (GEMSDOE28 lanes), not worm tracking (GEMSDOE29/42), and not any
focus-site winner's mechanism (all H19-5-family ridge surfaces + dotting/pruning).

## 2. Ranked untried hypotheses (3–5, as required; only rank 1 is run this session)

Expected gains are ordinal planning brackets for HOLDOUT-DTI, not forecasts.

| Rank | ID | Layers → signature | Why it should catch a catalogue-missing fault | Difference from implemented work + mimic | Expected Δ (holdout) | Cost | Validatable now? |
|---|---|---|---|---|---:|---|---|
| 1 | **H37-1 DOC down-dip offset concordance** (lane, §1) | `det_elev` (12) gradient direction; lagged ridges of `iso_grav_anom_hg` (18), `tmi_hg` (03), H34 base-flexure field from `depth_to_base_surf` (15) | Buried basin-margin faults keep a depth step after the scarp is eroded/buried, so the catalogue (Quaternary surface mapping) and family B (scarp) both miss them; the step is offset down-dip, invisible to zero-lag products | All repo concordances are zero-lag (X3, H31, H34). Mimics: fan wedges, flow margins, shorelines (§1) | 0…+0.006 | ~2 h (sidecar, h34 pattern) | **Yes** — bands pinned & restored |
| 2 | H37-2 spring-line alignment ridge | GDR 1391 hot-spring points (`external/gdr_wellspring_in_footprint.csv`) → KDE σ=3 px → Hessian ridge + structure-tensor elongation of the KDE field | Permeable unmapped faults discharge *aligned* springs along strike; alignment is evidence of a linear conduit even where no scarp exists | Family D uses the points only isotropically (`D_gdr_dist_hot/kde2km/tmax5km`); never an alignment/ridge statistic. Mimic: fan-toe / lithologic-contact spring lines, road-biased sampling | 0…+0.004 | ~3 h | Yes — CSV pinned & restored |
| 3 | H37-3 SGMC geologic-fault distance/strike | `external/derived_sgmc_faults_100m_u8.tif` (USGS SGMC geodatabase, DOI 10.5066/F7WH2N65, Horton et al. 2017) → distance-to-SGMC-fault + nearest-strike compatibility | State geologic maps record bedrock faults absent from the Quaternary catalogue; newly-mapped INGENIOUS faults may reactivate/coincide with some | Pinned in `registry/data_manifest.json` as "proxy only; not used in the factorial"; no code in this repo reads it. Caveats: SGMC is a ~1:1,000,000-scale compilation (positional error ≫ 100 m), and standalone SGMC-off-catalogue files on sibling sites carry OWNER claims of only 0.049–0.051 (GEMSDOE29/72 rows in the brief) — weak prior. Mimic: compilation artefacts/seams | 0…+0.005 | ~2 h | Yes — raster pinned & restored. Canary is decisive: if SGMC traces coincide with hidden catalogue components, AUC inflation is proxy leakage and the arm stops |
| 4 | H37-4 radiometric F-parameter alteration ridge (= H34-4 operationalized) | GeoDAWN K, eTh, eU (`external/geodawn_rad_u8.tif`) → F = K·(eU/eTh) (Efimov 1978; F≈1.2–1.3 unaltered, 2–5 altered) → ridge strength | Hydrothermal K-metasomatism tracks permeable fault conduits, including faults with no Quaternary rupture | D uses K/Th/U ratios pointwise and ThK/UK edges; X1 uses cross-scarp *contrast*; an F-index *ridge* is new. Mimic: potassic volcanics (lithology, not alteration) | 0…+0.003 | ~2 h | Yes — grids pinned & restored |
| 5 | H37-5 catalogue branch-node proximity | Visible catalogue only → degree≥3 branch nodes → distance + 2 km node density (dynamic per holdout draw) | Fault intersections host ~22 % of inventoried Great Basin geothermal systems (Faulds & Hinz 2015, read record in knowledge/03); unmapped linking strands concentrate at network nodes | Family E has distance/density/coherence but no explicit branch-node geometry; H27/H30 use endpoints, not junctions. Mimic: digitization junctions; catalogue-hug proxy inflation (hug gate applies) | 0…+0.003 | ~4 h (per-cell build) | Yes, but deferred behind ranks 1–4 on cost |

External-data candidates that remain **blocked, not viable from this sandbox**
(checked, not assumed): raw 3DEP 1 m DEM tiles / NHD stream geometry (knowledge/21
rank 2) and ScienceBase-hosted releases (slip/dilation tendency DOI 10.5066/P9YL58W6;
heat flow DOI 10.5066/P9BZPVUC) — hosts are outside this sandbox's egress allowlist
(github/pypi/npm only) and no bytes are pinned in `registry/data_manifest.json`.
Free official sources for a networked runner: USGS 3DEP
<https://www.usgs.gov/3d-elevation-program>, USGS SGMC
<https://www.usgs.gov/data/state-geologic-map-compilation-sgmc-geodatabase-conterminous-united-states>,
GDR 1391 <https://gdr.openei.org/submissions/1391>, USGS GeoDAWN
<https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>.

## 3. Frozen experimental design (experiment 1 of the 3-experiment budget)

* **Harness (shared tools, no fork):** `gems25.experiment.Cell(extras=True, h27=True)`
  — hide-and-recover: whole 8-connected components hidden, `hide_frac 0.20`,
  1.5 km collar, every catalogue-based feature derived only from the visible
  faults, visible faults masked pixel-exactly in emission and scoring;
  `gems25.metric.dti_binary` (α=0.2, β=0.8, R=3 px = 300 m triangular kernel);
  `gems25.submission` writer/checker. Evaluator string recorded in every receipt.
* **Arms (same Cell, paired; HGB `random_state=draw`; emission ridge-NMS → top-K
  kfrac 0.035 → `score_ordered_dots` 2.4 px for both):**
  * `C37` control — H35 arm B exactly: BDE + X1_K,X1_ThK,X1_UK,X2_compat,
    X2_compat_coh,X3_gm,X3_gd + `H27_tip` + 3 H34 columns, in the H35 runner's
    column order. Recomputed this run (IR-25-COMPARATOR-DRIFT rule).
  * `A37` candidate — `C37` + the 6 DOC columns (§1; formulas frozen in
    `src/gems25/h37.py`, unit-tested on synthetics before the run).
* **Cells:** folds NW/NE/SW/SE × screen draws **14, 15** (unused by H26–H35 screens;
  verified by grep over `knowledge/`, `evidence/*/design.json`). Confirmation
  draws **16, 17 only if the screen gate passes**. Screen+confirmation = 1
  experiment. No other experiment is run this session unless A37 passes both
  stages; a failed arm stays failed (no lag/direction tuning on outcomes).
* **Leakage canary (before any gate is read):** per-cell AUC of each DOC column
  alone vs that cell's hidden-test labels on the Cell's fixed AUC index sets.
  Any AUC > 0.90 (or < 0.10) → leakage until proven otherwise; stop, negative.
* **Gate (screen and confirmation separately, A37 vs same-run C37):** mean paired
  gain (fold means) > +0.001, ≥3/4 folds positive, worst fold ≥ −0.010, mean
  hug-share increase ≤ +0.10. Reporting: HOLDOUT-DTI fold-mean **and pooled**
  (TP,FP,N summed over cells via the identity
  DTI = TP/(0.2·(TP+FP)+0.8·N)), evaluator, withheld positives per fold, 95 % CI
  (t over 4 fold means). CIs will be wide at 4 folds; that is stated, not hidden.
* **Reproduction diagnostic:** C37 per-cell DTI on draws 14–15 has no historical
  comparator (fresh draws); instead report (a) cache hash check vs
  `evidence/work_cache_hashes.json` for the rebuilt static stack, and (b) C37's
  fold-mean on draws 14–15 alongside H35-B's recorded draws 10–13 means as
  *context only* (not a paired test).

## 4. Lane / duplicate rule for this session (frozen before placement)

The protocol caps: Spearman ≤ 0.90 and ≤ 70 % of candidate dots within 3 px of any
one registry raster's dots, checked on the continuous surface (before placement)
and on the final dots. One pre-registered refinement, implementing knowledge/20
next-step #4 as a shared-tool fix in `scripts/check_lane_duplicates.py` (reported,
not private): for every registry raster also report its **halo coverage** (fraction
of footprint pixels within 3 px of its dots — the overlap a uniformly random dot
set would score) and the **reverse overlap**. A registry raster with halo coverage
≥ 0.70 cannot discriminate duplicates by the candidate-side statistic (a random
file fails it); for those rasters the lane test uses the symmetric statistic
`min(candidate-side, reverse) ≤ 0.70`, while the literal candidate-side number is
still printed in every receipt and on the site. For all rasters with coverage
< 0.70 the literal 70 % rule applies unchanged. Byte-identity and Spearman rules
are unchanged. Own-lineage predecessors (H31-C/H35 files in `docs/downloads/`) are
reported as their own tier: a candidate that is lane-clean vs other-site
substantive rasters but > 70 % vs its own superseded predecessor is labelled
**"supersedes <predecessor> — never submit both"**, not silently clean.

If any applicable lane test fails: log as duplicate, stop promotion (verdict
negative), keep the file as a testing download only.

## 5. TIF policy and automated submit decision

A unique full-footprint TIF of arm A37 (3 pseudo-new draws averaged, H35-candidate
build pattern, full-catalogue tip field) is generated whatever the gate says (the
owner's highest-urgency deliverable), in both outside conventions; the
**zeros-outside** file is primary (it passes the strictest whole-array [0,1]
validator behind the reported portal error "Predicted values must be in range
[0, 1]"; zeros-outside accepted values are an organizer question only the portal
can settle — no acceptance is asserted). The README/site state in one line:

* **OK TO SUBMIT** only if ALL automated gates pass: screen+confirmation holdout
  gate, leakage canary, lane (§4), exact-file validator (`check_file`: no NaN
  inside the 5,167,373-px footprint, values in [0,1], EPSG:32611, 3730×3292,
  transform match), unique content id not in any ledger. Upload itself stays
  manual (agent never contacts DrivenData); "OK" means *eligible for the owner's
  selector step within the weekly cap*, verdict `promote`.
* Otherwise **DO NOT SUBMIT — download for testing only**, verdict `negative`,
  with the failed gate named. Negative results are deliverables.

## 6. Run card

One JSON: `registry/run_card_h37_2026-10-25.json` — hypothesis, mechanism, named
non-fault mimics, HOLDOUT-DTI (fold-mean + pooled, CI, withheld counts,
evaluator), correlation/overlap vs registry (surface + dots, all tiers of §4),
raster SHA-256 + content id, validator output, submission name + note ≤ 140
chars, verdict promote/negative. Every score-like number is labelled
HOLDOUT-DTI, OWNER, or PROJECTION — never an unlabelled "score".
