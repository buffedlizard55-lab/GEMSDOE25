# 21 · Candidate hypotheses (new) + pre-registration GMCE-1 (2026-10-25, this session)

Written **before any GMCE fit** (AGENTS.md rule 4). Evidence classes: OWNER = owner-reported
claim in the 2026-10-25 brief (not an organizer receipt) · COMPUTED = reproducible in this repo ·
READ = recorded in `registry/sources.json` from the cited page in an earlier session ·
INFERENCE = reasoning with assumptions stated. **No number here is ORGANIZER-CONFIRMED.**
No DrivenData page was accessed this session (AGENTS.md rule 3); competition-format and metric
statements below cite the earlier READ records in `knowledge/06` and `src/gems25/metric.py` /
`src/gems25/submission.py`.

## 0. Why the focus-site best (GEMSDOE32, OWNER 0.2778) scored highest — one-paragraph answer

Pixel-exact forensics in this repo (`evidence/focus_sites_forensics.json`, `knowledge/17`) prove
the chain on local mirrors: `h19-5` solid (121,131 px, OWNER 0.1922) → score-blind geodesic
dotting `dot_thin(h19-5,1.5)` (60,069 px, OWNER 0.2477) → wider dotting to 44,090 px ("D2.8",
OWNER 0.2600) → delete dots with `d(catalogue) ≤ 1 px` (40,199 px, OWNER 0.2708) → delete dots
with `d(catalogue) ≤ 2 px` = **H33-2-B2** (37,654 px, OWNER 0.2778). Under the official metric as
transcribed in `src/gems25/metric.py` (DTI = TPw/(TPw+0.2·FPw+0.8·FNw), 300 m triangular kernel,
credit per truth pixel = **maximum** over nearby dots), a second dot covering already-covered
truth adds ≈0 credit but up to 1 unit of FP mass charged at 0.2. Steps 1–3 are therefore pure
*emission economics*: identical geology, less redundant and less near-catalogue mass. A zero-
credit-loss deletion predicts 0.27100/0.27871 for the last two steps vs the OWNER claims
0.2708/0.2778, implying the deleted 100 m / 100–200 m catalogue-flank dots carried only
≈0.00096 / ≈0.00503 credit per dot — 57×/11× below the break-even marginal ratio
τ(D)=0.2·D/(1−0.2·D) (`gems25.metric.marginal_inclusion_ratio`; τ(0.2778)=0.0588). **Caveats that
stay open:** every score in the chain is OWNER, not a receipt; the last step has no paired CI and
the realized claim exceeds GEMSDOE32's own projection (0.2747, READ in `knowledge/17`); and the
blanket 200 m deletion is in tension with the READ staff wording that test truth includes
"corrections or modifications" within 300 m of known traces (`knowledge/06`). Emission-only
gains on an existing surface are nearly exhausted in this repo's evidence (H28 spacing sweep,
H31 credit-field negative, KDC complement negative), so beating 0.2778 credibly requires more
*credit per emitted pixel from a better detector*: ≈+4 % mean credit/dot for +0.01 at constant
mass, ≈+25 % for the OWNER-stated 0.3195 (INFERENCE from the same algebra; the brief also carries
a conflicting 0.4413 leader claim — IR-25-LEADERBOARD-CONFLICT stays open). This session tests one
new *detector* block and labels every result HOLDOUT-DTI only; it claims no live score.

## 1. Ranked candidate hypotheses not yet tried in this repo

Novelty checked by grep over `src/`, `scripts/`, `knowledge/03–20`, `evidence/` this session.
"Registered only" = named in an earlier register but never implemented/fitted here.

| Rank | ID | Layers → signature | Why it should catch a catalogue-*missing* fault | Difference from this repo + the 9 focus sites | Expected holdout Δ (planning bracket, not a forecast) | Cost | Validatable now? |
|---|---|---|---|---|---:|---|---|
| **1** | **GMCE-1 — Gravity–Magnetic Coherent Edge (gradient-vector parallelism)** | `iso_grav_anom` (band 13) + `rtp` (band 2), both pinned competition bands derived from USGS GeoDAWN (DOI 10.5066/P93LGLVQ, READ `registry/sources.json`). Signature: angle Δθ between the two fields' smoothed (σ=2 px) gradient *vectors*; coherent-edge strength = min(pct-scaled log gradient magnitudes)·\|cos Δθ\|, its signed twin (·cos Δθ), and the Hessian ridge strength of the coherent-edge grid. | A fault that offsets basement juxtaposes blocks differing in **both** density and magnetization across the *same* plane, so both potential fields step across one line: their gradient vectors are (anti)parallel (both normal to strike) on a co-located edge — even under alluvial cover where no Quaternary scarp exists for the USGS/INGENIOUS catalogue to record. Mag-only edges (dikes/flows) and grav-only edges (basin thickness) fail the min(·) and/or parallelism test. | Family A carries each field's gradient *magnitudes*, tilt and one ridge σ, but **no gradient azimuth for either field** (`tmi_hg` is a magnitude; verified min ≥ 0 in `evidence/band_stats.json`), so no existing column can express "the two edges are the same line". Add-on `X3_gm` is an *ungated* pointwise product of ridge strengths — it fires where two unrelated ridges merely cross. H34 depth-slices RTP alone; GEMSDOE28/40 Euler and GEMSDOE29/42 worms are single-field; no focus-site winner uses cross-field vector alignment. | 0…+0.006 | ~0.5 day (sidecar on cached bands) | **Yes** — pinned bytes local |
| 2 | H30-2 — visible-fault junction / accommodation-zone branch field (registered 2026-10-03, never fitted) | Visible-catalogue raster topology (degree ≥ 3 branch pixels, multi-azimuth resultant) × B-scarp support | Unmapped splays can depart from multi-branch intersections / accommodation zones rather than continuing one line; Faulds & Hinz (2015, READ `knowledge/06`) put ~22 % of Great Basin geothermal systems at intersections. | E has distance/density/coherence, H27/H35 use degree-1 *tips*; no column identifies branch degree. **Ranked below GMCE-1 because it is catalogue-proximate by construction: the hide-and-recover proxy (truth = catalogue components) would flatter it, while the OWNER live evidence (B1/B2 deletions) says near-catalogue dots earn ≈0 — a proxy/live conflict the holdout cannot resolve.** | 0…+0.006 on the proxy, live sign unknown | 1 day | Yes, with the stated proxy caveat |
| 3 | RADCON-1 — radiometric multivariate contact ridge | GeoDAWN K/Th/U uint8 grids (external mirror, pinned) → multivariate edge = ‖∇(standardized K,Th,U)‖ then Hessian ridge; optional Efimov-style F = K·(U/Th) ridge | A fault juxtaposing different lithologies, or a K-metasomatized permeable conduit, is a *compositional* boundary even where relief and magnetics are quiet; Quaternary-rupture mapping can miss buried contacts. | D uses ratios pointwise + single-ratio gradient magnitudes (`D_ThK_edge`); X1 uses cross-scarp *contrast*; a joint-composition edge *ridge* is new here. H34-4 named this idea but no code/results exist (grep-verified). Mimic risk high (depositional contacts), uint8 quantisation crude → rank 3. | 0…+0.003 | ~0.5 day | Yes |
| 4 | H30-3 — scale-persistent terrain lineament (registered only) | `det_elev` (band 12) ridge strength at σ = 1/2/4 px → persistence = geometric mean across scales | A real fault scarp is a line at several smoothing scales; single-scale crests include fluvial/lithologic noise that a catalogue (field-checked) would already have filtered — persistence should enrich for the unmapped-but-real scarps. | B has single-scale `B_crest`/`B_trough` (σ=1.5) + LiDAR descriptors; no cross-scale persistence product here. GEMSDOE42's worm-persistence live result (OWNER 0.0581, standalone) lowers the prior → rank 4. | 0…+0.004 | hours | Yes |
| 5 | PALEO/HEAT — paleo-geothermal deposits × residual heat flow | Needs GDR 1391 `paleo_geothermal_regional.zip` (listed, CC BY 4.0; earlier fetch failed — `knowledge/09` H27-3) and USGS Great Basin heat-flow release DOI 10.5066/P9BZPVUC (124 MB ScienceBase ZIP, `knowledge/09` H27-4) | Sinter/tufa and convective heat-flow residuals record former/present fluid upflow on conduits that may never have ruptured the surface in the Quaternary. | Neither layer exists in any family. **Not viable this session:** both official sources are outside this sandbox's network allowlist (github/pypi/npm only) and no hash-pinned mirror exists in `registry/data_manifest.json`. Named here so it is not re-proposed as "available"; obtaining it needs a networked runner + byte/coverage/licence verification first. | unknown | days + external fetch | **No — blocked** |

## 2. The single lane for this session (PARALLEL-RUN PROTOCOL item 1)

> **GMCE-1.** Add exactly three static columns, computed from the pinned `iso_grav_anom` and
> `rtp` bands, to the **current holdout-best arm recomputed in the same run** — H35 arm B
> (BDE + 7 add-ons + `H27_tip` + 3 H34 RESMAG-FLEX columns; `knowledge/19–20`) — with the model
> (HGB, `gems25.experiment.HGB_PARAMS`), training sample, and emission (ridge-NMS candidates →
> top-K at kfrac 0.035 → score-ordered Poisson dots at 2.4 px) all frozen. Nothing else changes.
> Column formulas are frozen in `src/gems25/gmce.py` (written after this doc, unit-tested on
> synthetics before any fit):
> with `G = gaussian(nearest_fill(iso_grav_anom), 2)`, `M = gaussian(nearest_fill(rtp), 2)`,
> `cosᵟ = (∇G·∇M)/(|∇G||∇M|+ε)`, `e_G, e_M` = log1p gradient magnitudes percentile-scaled
> (1st–99th over footprint) to [0,1], `e_min = min(e_G, e_M)`:
> 1. `GMCE_par_min = e_min · |cosᵟ|` ∈ [0,1]
> 2. `GMCE_signed_min = e_min · cosᵟ` ∈ [−1,1]
> 3. `GMCE_ridge_par = ridge_strength(GMCE_par_min, σ=1.5)` ≥ 0 (`gems25.features.ridge_strength`)

**Named non-fault process that could mimic it (in advance):** a lithologic contact — an
intrusion margin or a stratigraphic pinch-out — changes density and magnetization across the
same non-fault boundary and produces an identical coherent edge. Survey-levelling lineaments
shared by both grids could also align spuriously (their gradients would be parallel along the
flight-line direction); the canary + paired holdout are the only guards available here.

## 3. Pre-registration — GMCE-1 screen + confirmation (frozen)

* **Harness (shared tools, no fork):** `gems25.experiment.Cell` hide-and-recover (whole
  8-connected components hidden, hide_frac 0.20, 1.5 km collar, catalogue features from the
  *visible* catalogue only, visible faults masked pixel-exactly in scoring),
  `gems25.metric.dti_binary` (α=0.2, β=0.8, R=3 px = 300 m triangular kernel),
  `gems25.submission` writer/checker. Evaluator id recorded in every output row.
* **Cells:** folds NW/NE/SW/SE × **draws 20, 21** (screen; unused by any prior run in
  `evidence/` — prior screens used 0–13). Confirmation on **draws 22, 23 only if the screen
  passes**. Budget: screen = experiment 1, confirmation = experiment 2, candidate build is not
  an experiment; hard stop at 3 experiments / 2 h of fitting (protocol item 6).
* **Arms (same Cell, paired):** `BEST` = H35-B configuration recomputed this run;
  `GMCE` = `BEST` + the 3 GMCE columns appended. Fit seed = draw, as in `run_h35_factorial.py`.
* **Leakage canary (read before any gate):** per-cell AUC of each GMCE column *alone* vs that
  cell's hidden-test labels on the Cell's fixed AUC index sets. Any AUC > 0.90 → leakage until
  proven otherwise; stop, verdict negative. (GMCE columns are functions of two static
  geophysical bands only — no label is read by `gmce.py` — so a canary failure would indicate a
  harness bug, which is exactly what the canary is for.)
* **Gate (screen and confirmation separately):** mean paired gain over the 4 fold means
  (GMCE − BEST) **> +0.001**, **≥ 3/4 folds positive**, **worst fold ≥ −0.010**, canary passed.
  Response labelled **HOLDOUT-DTI** with evaluator id, withheld-positive count, and a 95 % CI
  (t over the 4 fold means around the pooled DTI, as in the H31/H35 run cards; pooled DTI =
  ΣTP/(ΣTP+0.2·ΣFP+0.8·ΣFN) over all cells of the stage).
* **Lane checks (before the file is called submittable):** (a) *pre-placement surface* — Spearman
  rank correlation of the full-footprint GMCE probability surface vs every restored registry
  raster must be ≤ 0.90 in absolute value; (b) *final dots* — ≤ 70 % of candidate dots within
  3 px of any one registry raster's dots. Registry = `registry/artifact_ledger.json` rasters +
  the 9 focus-site winners in `evidence/focus_sites_forensics.json`. The dense r13 5-px lattice
  is reported separately with both overlap directions and its density caveat
  (IR-25-LANE-DENSITY: a ≥1-dot-per-25-px raster puts ~every possible dot within 3 px, so
  candidate-side overlap against it is not discriminative); it is **not** silently waived.
  Overlap vs this repo's own earlier HGB-lineage downloads (H31/H35/KDC) is also reported, as a
  lineage flag, because those files are prior iterations of this same site rather than other
  sites' lanes. If the sparse-registry lane fails → duplicate; stop; verdict negative.
* **TIF policy:** one unique full-footprint TIF of the GMCE arm is generated whatever the gate
  says (3-draw full-catalogue production protocol of `scripts/build_h35_candidate.py`, same
  emission; **no B2 post-prune**, because that step was not part of the holdout emission and
  adding it untested would break holdout↔build identity). Both outside conventions are written;
  the **zeros-outside** file is primary because it passes the strictest whole-array [0,1]
  validator consistent with the owner's reported portal error ("Predicted values must be in
  range [0, 1]"; root-cause record in `src/gems25/submission.py`). The site/README first screen
  states in one line whether spending a slot is OK: **promote only if screen + confirmation +
  sparse lane + exact-file audit all pass**; otherwise **negative — download for testing only,
  DO NOT SUBMIT**.
* **Run card:** one JSON (`registry/run_card_gmce_2026-10-25.json`): hypothesis, mechanism,
  mimicking process, HOLDOUT-DTI + CI + withheld counts + paired gain + folds, canary, lane
  correlations/overlaps (sparse registry, lattice, own-lineage), raster SHA-256 + content id,
  validator output, submission filename + note ≤ 140 chars, verdict promote/negative.
  Negative is a deliverable. The agent never uploads; slot spend remains the owner's manual act.

## 4. Sources for manual review (no new page was fetched this session)

* Metric & format (READ record): <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> via `knowledge/06`, `src/gems25/metric.py`, `src/gems25/submission.py`.
* CRS: <https://epsg.io/32611> (EPSG:32611, WGS 84 / UTM 11N; grid pinned in `gems25.submission.EXPECTED`).
* Geophysics layer provenance: USGS GeoDAWN data release, DOI 10.5066/P93LGLVQ, <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> (licence line not on the page text read earlier — IR-25-LICENSE-GEODAWN remains open).
* Geothermal structural settings (READ): Faulds & Hinz 2015, <https://www.osti.gov/servlets/purl/1724082>.
* Blocked external layers (rank 5): GDR 1391 <https://gdr.openei.org/submissions/1391>; USGS heat flow DOI 10.5066/P9BZPVUC <https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28>.
* Gradient-parallelism definition is elementary vector geometry (cosine of the angle between two
  gradient fields), implemented and unit-tested here; no external factual claim is loaded on it.
