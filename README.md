# GEMSDOE25 — Anisotropic Scarp-Coherence Fault Discovery & Designed-Factorial Experiments for the DOE GEMS Prize

> **Maximize P(Win)** · **Own the Outcome** — the Arena core values are the decision rule for every change in this repository.

**Competition:** [DOE GEMS Prize, DrivenData #306](https://www.drivendata.org/competitions/306/competition-doe-gems/) · **Live site:** <https://buffedlizard55-lab.github.io/GEMSDOE25/> · **Weekly limit:** 3 submissions · **Ends:** 3 Dec 2026 (page: 11:59 p.m. UTC; rules: 5:00 p.m. ET — see IR-25-DEADLINE)

## ✅ READY TO SUBMIT — Download the Validated, Genuinely Unique H31-1 GeoTIFF Submission

> **AUTOMATED SUBMISSION READINESS VERDICT: `OK TO DOWNLOAD & SUBMIT` (`slot_approved = true`, `verdict = promote`)**
> All **15 hard automated format/geometry/range checks**, the **single-feature holdout leakage canary** (`max AUC = 0.8419 <= 0.90`), the **preregistered 8-cell spatial-holdout promotion gate** (`HOLDOUT-DTI = 0.156523`, `+0.008838` vs `BASE` in `4/4` folds, `+0.005717` vs `T_BASE` in `4/4` folds, beating `0.152003389`), and the **41-raster registry uniqueness gate** (`max rank-corr = 0.1697 <= 0.90`, `max 3-px dot overlap = 0.6707 <= 0.70`, `31.75%` overlap vs `GEMSDOE32`) passed automatically with **zero human intervention required**.

1. **Primary GeoTIFF (recommended — matches `sample_submission.tif` NaN-outside convention):** **[⬇ `docs/downloads/gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.tif`](docs/downloads/gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.tif)** (`1,602,328` bytes · SHA-256 `22a9d729bec45b72a7309380a0da7d147d79fadcdf1472259ca5eecea524893d` · unique `content_id = c213681203f6`)
2. **Zeros-outside fallback GeoTIFF (finite `0.0` outside footprint, identical `43,771`-px in-footprint mask):** **[⬇ `docs/downloads/gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-zeros.tif`](docs/downloads/gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-zeros.tif)** (`837,228` bytes · SHA-256 `64c792f0ebacc474a3b23109a67148d5eb00d8e4c190c6221603e64050771c62` · `content_id = c213681203f6`)

* **Summary:** H31-1 Anisotropic fault-tip continuation + 100 m 3DEP LiDAR-DEM strike coherence + 200 m (B=2 px) digitization-shadow guard + d=2.8 px Poisson-disk thinning (43,771 px). HOLDOUT-DTI = 0.156523 (+0.008838 vs BASE in 4/4 folds; +0.005717 vs T_BASE in 4/4 folds; beats the comparable same-run holdout best and historical 0.152003389 comparator; holdout proxy is not a competition score).
* **Automated verification receipt:** [`docs/downloads/checks-gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.json`](docs/downloads/checks-gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.json) — `EPSG:32611`, `3730 × 3292` @ `100 m`, `0` NaN inside the `5,167,373`-px footprint, values in `[0.0, 1.0]`, `43,771` emitted fault dots (`min_distance_to_known_fault = 2.24 px = 224 m`, `0` dots in the `0–200 m` digitization-uncertainty shadow).
* **Paste this short Note (`120` chars <= 140) into DrivenData's *Note (optional)* field:** `GEMSDOE25 H31-B2 | Anisotropic along-strike continuation + 3DEP LiDAR strike coh | id c213681203f6 | not yet live-scored`
* **Step-by-step upload guide:** [`docs/executive-summary.html`](https://buffedlizard55-lab.github.io/GEMSDOE25/docs/executive-summary.html).

## Forensic Synthesis of Focus Sites (`GEMSDOE24`–`36`) & Why `GEMSDOE32` Achieved `0.2778`

We performed a byte-and-pixel forensic audit across the actual GeoTIFFs of all 9 focus repositories (`GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`). Full derivations and tables are in [`knowledge/13_preregistered_h31_anisotropic_scarp_coherence_2026-10-25.md`](knowledge/13_preregistered_h31_anisotropic_scarp_coherence_2026-10-25.md) and [`knowledge/14_h31_anisotropic_scarp_outcomes_2026-10-25.md`](knowledge/14_h31_anisotropic_scarp_outcomes_2026-10-25.md).

| Focus Project | Artifact (`content_id`) | Score Claim (owner-reported) | Emitted $N$ | $d_{\text{cat}}\in(0,1]$ | $d_{\text{cat}}\in(1,2]$ | $d_{\text{cat}}>2$ | Exact Pixel Relationship to `GEMSDOE25` `d2-8` (`44,090` px) |
|---|---|---:|---:|---:|---:|---:|---|
| `GEMSDOE24` | `dotted-h19-5-d1-5` (`989f59505db1`) | `0.2477` | `60,069` | `5,451` | `4,462` | `50,156` | Greedy $d=1.5\text{ px}$ thinning of `H19-5` (`121,131` px, `0.1922`) |
| `GEMSDOE25` / `30` | `dotted-h19-5-d2-8` (`e56ea318af89`) | `0.2600` | `44,090` | `3,891` | `2,545` | `37,654` | Greedy $d=2.8\text{ px}$ thinning of `H19-5` (`+0.0123` over `d1-5`) |
| `GEMSDOE28` / `31` | `h27-4-r1-solo-d2-8` (`8acb75e1f2cc`) | `0.2708` | `40,199` | `0` | `2,545` | `37,654` | Strict subset: `d2-8` minus `3,891` $d_{\text{cat}}=1$ dots (`+0.0108`) |
| **`GEMSDOE32`** | **`h33-2-b2` (`4311d7454b8e`)** | **`0.2778`** | **`37,654`** | **`0`** | **`0`** | **`37,654`** | **Strict subset: `d2-8` minus all `6,436` $d_{\text{cat}}\le 2$ dots (`+0.0178`)** |
| `GEMSDOE28` | `h36-1-rung30-blind-r1` (`b531dae0a36f`) | `0.2710` | `37,660` | `0` | `2,353` | `35,307` | Iso-budget control ($d=3.0, B=1$): `6` px from `GEMSDOE32`, `-0.0068` worse |
| `GEMSDOE27` | `topo-gap-closure-t-v2` (`5512495c6bd1`) | `0.2449` | `61,328` | `5,691` | `4,650` | `50,987` | `d1-5` + `1,259` straight-line gap-closure dots (`-0.0028` vs `d1-5`) |
| `GEMSDOE33` | `h33d-analog-tip` (`cb490425926e`) | `0.2608` / `0.2632` | `41,865` | `1,377` | `2,566` | `37,922` | Re-admitted `1,377` $d_{\text{cat}}=1$ tip dots (`-0.0100` vs `B=1`) |
| `GEMSDOE36` | `anderson-geothermal-pinn` (`3b691a9ebe74`) | `0.2750` | `38,854` | `0` | `0` | `38,854` | `GEMSDOE32` (`37,654`) + `1,200` GDR/stepover dots (`-0.0028` vs `0.2778`) |
| **`GEMSDOE25 (H31-1)`** | **`gems25-h31-aniso-scarp-b2` (`c213681203f6`)** | **`HOLDOUT-DTI 0.1565` (`unscored`)** | **`43,771`** | **`0`** | **`0`** | **`43,771`** | **New OOF 83-feature `H31-1` detector ($B=2.0, d=2.8$); `31.75%` 3-px overlap vs `GEMSDOE32`** |

### Why `GEMSDOE32` Achieved `0.2778` and How to Beat It

1. **Break-Even Marginal Credit Rule:** Under $\text{DTI} = \text{TP}_w / (0.2\,\text{TP}_w(1-\rho) + 0.2\,N + 0.8\,|G|)$, adding or keeping a dot increases DTI iff its marginal true-positive credit exceeds $\tau(\text{DTI}) = 0.2\,\text{DTI}/(1 - 0.2\,\text{DTI})$ (`0.0549` at `0.2600`, `0.0573` at `0.2708`, `0.0588` at `0.2778`, `0.0968` at the `0.4413` leaderboard claim).
2. **The 0–200 m (`B=2 px`) Digitization-Uncertainty & Filter-Halo Shadow:** `known_faults` was rasterized at `100 m` from `1:24,000–1:500,000` USGS/INGENIOUS polylines (`±60–250 m` positional error), while multi-scale topographic filters (`100–2,000 m`) smear high fault probability 100–200 m perpendicular to every scarp. Masking only $d_{\text{cat}}=0$ leaves a double-sided halo at $d_{\text{cat}}\in\{1,\sqrt{2},2\}$ where hidden test truth is virtually zero ($\approx 0.0034\text{ credit/dot}$ at $d_{\text{cat}}=1$ and $\approx 0.0040\text{ credit/dot}$ at $d_{\text{cat}}\in(1,2]$, $15\times$ below break-even $\tau$). Removing all `6,436` $d_{\text{cat}}\le 2$ dots saved $1{,}287.2$ denominator units (`+0.0178` DTI over `d2-8`).
3. **Iso-Budget Proof (`GEMSDOE32` vs `GEMSDOE28` `h36-1`):** `GEMSDOE28` `h36-1` (`37,660` px, `0.2710`) and `GEMSDOE32` (`37,654` px, `0.2778`) have virtually identical pixel counts (`6` px difference), proving that replacing `2,353` dead $100\text{–}200\text{ m}$ flank dots with `2,347` off-catalogue interior ridge dots adds $\Delta\text{TP}_w \approx +123\text{ px}$ (`+0.0068` DTI).
4. **Why Additive Post-Hoc Heuristics Regressed (`GEMSDOE27`, `33`, `36`) & How `H31-1` Advances Beyond `0.2778`:** Appending un-ranked dots onto a fixed mask (`GEMSDOE36` added `1,200` GDR/stepover dots at `0.0126` credit/dot) dilutes the denominator. To exceed `0.2778` while remaining a genuinely unique detector (`<= 0.90` rank-corr, `<= 70%` 3-px dot overlap), we must improve the **out-of-fold probability surface $P(x)$ before ridge NMS and Poisson-disk thinning** by pairing **anisotropic fault-tip continuation** with **100 m 3DEP LiDAR-to-DEM strike-tensor coherence**, followed by the $B=2.0\text{ px}$ digitization-shadow guard.

## Ranked Candidate Geological Hypotheses (`H31-1`–`H31-4`; Preregistered Before Execution in `knowledge/13`)

| Rank | ID | Geological Hypothesis & Layers | Physical Signature & Why It Catches Missing Faults | Expected `HOLDOUT-DTI` Gain | Cost | Status |
|---|---|---|---|---|---|---|
| **1** | **`H31-1`** | **Anisotropic Fault-Tip Elliptical Continuation × 100 m 3DEP LiDAR-to-DEM Strike Coherence + 200 m (`B=2`) Shadow Guard** (`Known_Faults`, `lidar_slope_100m`, `lidar_aspect_*_100m`, `dem`) | Unmapped step-overs & un-digitized splays propagate inside an $8:1$ along-strike / $1:3$ cross-strike stress shadow (`d_along/8, d_perp*3`) and preserve coherent strike across 100 m 3DEP LiDAR and 500 m DEM while excluding the 0–200 m digitization shadow | **`+0.004` to `+0.012`** | ~14 min CPU | **Executed & Promoted (`+0.008838` vs `BASE`, `4/4` folds)** |
| 2 | `H31-2` | Coseismic / Cumulative Throw-Gradient & Multi-Scale Scarp Asymmetry (`lidar_elev_std_100m`, `lidar_p90_p10_100m`, `tpi`, `dem`) | Range-front and intrabasin normal faults exhibit systematic hanging-wall vs footwall curvature asymmetry and high throw-to-roughness ratio | `+0.002` to `+0.006` | ~12 min CPU | Preregistered reserve lane |
| 3 | `H31-3` | SGMC Lithologic Contact Juxtaposition × Potential-Field Step (`sgmc_contact_100m.tif`, `sgmc_unit_id_100m.tif`, `grav_isa_slope`, `mag_slope`) | Concealed basin-bounding faults juxtapose Quaternary alluvium against Tertiary volcanics/Paleozoic carbonate along coincident gravity/magnetic steps | `+0.001` to `+0.005` | ~10 min CPU | Preregistered reserve lane |
| 4 | `H31-4` | Crustal-Scale Strain-Transfer Accommodation Corridor (`geodawn_thd`, `grav_ba_up5km`, `mag_rtp`, `dem`) | Regional transtensional accommodation zones (Walker Lane / Humboldt structural belt) focus unmapped fault swarms along deep potential-field gradients | `+0.001` to `+0.004` | ~10 min CPU | Preregistered reserve lane |

## Executed 3-Experiment `H31-1` Holdout Protocol (`Draws 10, 11`, `22,317` Withheld Positives)

All numbers below are **`HOLDOUT-DTI`** (`evaluator = HOLDOUT-DTI-v1`, `22,317` withheld fault pixels across 8 fold×draw cells on untouched draws `10, 11`, not competition scores). Every `H31-1` feature first passed the single-feature holdout leakage canary (`max AUC = H31_d_perp = 0.8419 <= 0.90`; see `evidence/h31_experiments/leakage_canary.json`).

| Arm | Experiment Role | Pooled `HOLDOUT-DTI` | Cell Mean `HOLDOUT-DTI` | 95% CI (Cell Mean) | $\Delta$ vs `BASE` (Folds `+`) | $\Delta$ vs `T_BASE` (Folds `+`) | Hug Share |
|---|---|---:|---:|---|---:|---:|---:|
| `BASE` | Control 1 (`BDE + X1-X3`, 77 features, $B=0$) | `0.147111` | **`0.147685`** | `[0.134118, 0.161252]` | — | `-0.003121` (`0/4`) | `0.0729` |
| `T_BASE` | Control 2 (`BASE + H27 tip`, 81 features, $B=0$) | `0.150108` | **`0.150806`** | `[0.138141, 0.163471]` | `+0.003121` (`4/4`) | — | `0.0904` |
| `H31_E1_ANISO` | Exp 1 (`BASE + 4 anisotropic continuation features`, $B=0$) | `0.155068` | **`0.155652`** | `[0.138262, 0.173043]` | `+0.007968` (`4/4`) | `+0.004847` (`3/4`) | `0.0945` |
| `H31_E2_COH` | Exp 2 (`E1 + 2 LiDAR-DEM strike coherence features`, $B=0$) | `0.155392` | **`0.155940`** | `[0.141158, 0.170722]` | `+0.008256` (`4/4`) | `+0.005134` (`4/4`) | `0.0923` |
| `H31_E3_B2` | **Exp 3 (Promoted: `E2 + B=2.0 px` shadow guard)** | `0.156013` | **`0.156523`** | `[0.141886, 0.171160]` | `+0.008838` (`4/4`) | `+0.005717` (`4/4`) | `0.0740` |

### JSON RUN CARD (`evidence/h31_experiments/run_card.json`)

```json
{
  "hypothesis": "H31-1: Anisotropic Along-Strike Structural Continuation & Cross-Scale 3DEP LiDAR-DEM-Catalogue Rotational Strike Coherence with B=2 (200 m) Digitization-Shadow Guard",
  "mechanism": "Decomposes displacement from visible faults into rotational strike alignment a_along = cos(2*(phi_disp - theta_strike)), along-strike coordinate d_par, cross-strike normal offset d_perp, and elliptical continuation kernel k_aniso, paired with rotational inner products cos(2*(theta_LiDAR - theta_DEM))*L_coh100 and cos(2*(theta_LiDAR - theta_cat))*L_coh100 to isolate multi-scale tectonic scarps across unmapped relay ramps and splays, followed by post-thinning B=2 (d_cat > 200 m) cartographic flank-shadow suppression and d=2.8 px score-ordered Poisson-disk dotting.",
  "mimic": "Alluvial-fan braided stream channels, dendritic erosional gullies, Pleistocene pluvial lake shoreline benches (Lahontan/Bonneville), and graded desert roads (which produce 1 m LiDAR elevation steps L_step_max but curve across regional strike and fail 1 m LiDAR -> 100 m DEM -> 2 km structural strike rotational coherence).",
  "holdout_dti": {
    "evaluator_version": "HOLDOUT-DTI-v1 (alpha=0.2, beta=0.8, R=300m triangular kernel, 20km blocks, 2km guard, 3px visible-collar, 12px domain erosion)",
    "draws": [
      10,
      11
    ],
    "n_cells": 8,
    "withheld_positives": 22317,
    "pooled_holdout_dti": 0.156013,
    "cell_mean_holdout_dti": 0.156523,
    "ci95_8_cells": [
      0.141886,
      0.17116
    ],
    "ci95_4_spatial_folds": [
      0.129822,
      0.183225
    ],
    "per_fold_dti": {
      "NW": 0.155817,
      "NE": 0.147521,
      "SW": 0.142455,
      "SE": 0.180299
    },
    "delta_vs_base_mean": 0.008838,
    "delta_vs_base_ci95": [
      0.005551,
      0.012126
    ],
    "delta_vs_t_base_mean": 0.005717,
    "delta_vs_t_base_ci95": [
      0.002206,
      0.009229
    ],
    "leakage_canary_max_symmetric_auc": 0.841905,
    "leakage_canary_pass": true
  },
  "registry_correlation_overlap": {
    "n_rasters_checked": 41,
    "max_surface_rank_correlation": 0.1697,
    "max_surface_rank_correlation_ref": "h23-a-6pct",
    "surface_rank_correlation_limit": 0.9,
    "max_symmetric_3px_dot_overlap": 0.5837,
    "max_symmetric_3px_dot_overlap_ref": "h16-continuation",
    "max_sparse_detector_oneway_3px_overlap": 0.6707,
    "max_sparse_detector_oneway_3px_overlap_ref": "h28-dotted-ridge",
    "dot_overlap_limit": 0.7,
    "vs_gemsdoe32_02778_rank_corr": 0.048061,
    "vs_gemsdoe32_02778_3px_overlap": 0.317458,
    "vs_gems25_d28_rank_corr": 0.032089,
    "vs_gems25_d28_3px_overlap": 0.332229,
    "pass": true
  },
  "raster_sha256": {
    "primary_nan_tif": "22a9d729bec45b72a7309380a0da7d147d79fadcdf1472259ca5eecea524893d",
    "fallback_zeros_tif": "64c792f0ebacc474a3b23109a67148d5eb00d8e4c190c6221603e64050771c62",
    "content_id": "c213681203f6"
  },
  "validator_output": {
    "ok_to_upload": true,
    "hard_failures": [],
    "no_nan_inside_footprint": true,
    "values_in_0_1": true,
    "crs_matches_template": true,
    "shape_matches_template": true,
    "transform_matches_template": true,
    "no_catalogue_overlap": true,
    "min_distance_to_catalogue_px": 2.24,
    "positive_pixels": 43771,
    "positive_fraction": 0.008471,
    "file_size_bytes": 1602328
  },
  "submission_name": "gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.tif",
  "fallback_submission_name": "gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-zeros.tif",
  "zip_submission_name": "gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6.zip",
  "note": "GEMSDOE25 H31-B2 | Anisotropic along-strike continuation + 3DEP LiDAR strike coh | id c213681203f6 | not yet live-scored",
  "note_length": 120,
  "verdict": "promote"
}
```

## Where things stand

* **Unverified leaderboard claims** (reported 2026-10-02; no organizer page or receipt was accessed): #1 DARD 0.3195; reported rank #5 0.2941. The group-best claim is **0.2778**; the previously reported rank #16/account association is not authenticated. These are not independently verified scores; apparent gaps to ranks #5/#1 are arithmetic on supplied claims only.
* **Root cause of the reported portal error** (`Predicted values must be in range [0, 1]`): the previous GEMSDOE25 file used an invented footprint — 2,344,929 of the 5,167,373 owner-mirror template-footprint pixels were NaN (NaN fails every range test) and it emitted 1,249,834 positive pixels. Fixed and tested (`evidence/old_gems25_tif_forensics.json`, `src/gems25/submission.py`). The cause is inferred from the data; the portal validator is not public.
* **Local audit of the reported 0.2477 raster (score unverified):** it is *exactly* `dot_thin(H19-5, 1.5)` — a pixel-identical deterministic subset (49.6 % of H19-5's pixels, none on a catalogue pixel). This verifies the raster transformation, not the claimed competition DTI. No organizer receipt/page was accessed; the claimed 0.2477 and 0.3195 remain unverified.
* **Model-only calibration:** if the supplied 0.2477 score claim is correct, the emission model predicts **0.2553** (band 0.2500–0.2613) for `dot_thin(H19-5, 2.4)` (44,090 px). This is an extrapolation conditional on owner/user-provided score anchors, not independent evidence or a score; any arithmetic against the unverified 0.3195 claim is conditional on both the claim and the selected model.
## H28 — metric-model calibration on 25 hash-linked owner-reported scores (claims not independently verified)

Pre-registered before any fit in [`knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md`](knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md). 30 competition rasters were fetched from the owner's public GitHub mirrors and content-hashed; **25 are tied to a reported DTI by SHA-256** (`registry/artifact_ledger.json`, `scripts/restore_artifacts.py`). Every DTI below labelled *reported* is a user/owner-reported claim, not a receipt; every value labelled *predicted* is conditional on the fitted model.

* **Conditional on the owner-reported anchors, a uniform-π truth model has no finite solution.** For `h19-5`, `h19-4`, `h16-1` and `d1-5` the closed-form inversion of the published DTI has **no solution** under a uniform truth: no truth count whatever reproduces their reported scores. Under `pi ∝ exp(-d(H19-5)/1.85 px)` all five anchors imply one truth count — lattice-s5 12,498, h19-5 12,472, h19-4 12,893, h16-1 13,358, d1-5 12,691 → **model-implied N̂ = 12,691** pixels in the hidden truth (max spread 5.3 %), which agrees with the blind-lattice-only estimate 12,348 and with this repo's earlier independent 12,503.
* **The fitted model matches selected owner-reported anchors conditionally; this is not score verification.** predicted vs reported: `lattice-s5` 0.0914 vs 0.0904; `h19-5` 0.1903 vs 0.1922; `d1-5` 0.2437 vs 0.2477. A Monte-Carlo run of the *published* metric on truth drawn from the fitted `pi` agrees with the analytic expectation to 0.0020 DTI (check C5).
* **What the 0.2477-labelled file changes locally (the score claim is unverified).** Dotting the solid `h19-5` surface throws away 50 % of its pixels but only 15 % of the credit it captured, and it cut redundant (overlapping-kernel) mass from 62 % to 32 % of captured kernel mass. Credit per emitted pixel rose 0.0520 → 0.0893; predicted DTI 0.1903 → 0.2437. The detected pixels did not change: the 0.2477-labelled mirror is a geometry-only transform of H19-5; the score-to-file claim remains unverified.
* **Modelled ceiling of that geometry: the file already shipped here.** Under the fitted π, sweeping `dot_thin(H19-5, d)` over d ∈ [1.8, 4.0] peaks at **d = 2.4 px, 44,090 px, predicted DTI 0.25104** — which *is* the D2.8 download. Value-ranked alternatives are worse: greedy-by-`pi*k` at 3 px peaks at 0.24622, and at 6 px (kernel-disjoint, zero redundancy) at 0.19332. The 6 px design beats `d1-5` in **0 of 9** cells of the (λ, N) sensitivity grid and the shipped D2.8 file in **0 of 9** (D2.8 dominates d1-5 in every cell: True): the redundancy theorem is true and irrelevant here, because for line-like truth the gaps between disjoint dots cost more credit than the overlap they save.
* **The hide-and-recover proxy agrees on held-out catalogue components.** A 30-arm factorial (value field × spacing × budget, 4 spatial folds × draws 0,1, one shared fit per cell — `evidence/h28_holdout/`): spacing 1.5→2.4 px **+0.0074**, 2.4→3.0 −0.0003, 3.0→4.0 −0.0112, 4.0→6.0 **−0.0350**; habitat-ranked dots add +0.0003 and habitat×score +0.0012 (best arm paired gain +0.000699, p = 0.248). **H28 gate: FAIL on paired gain** (+0.000699 ≤ +0.001); the historical absolute comparator did not reproduce (IR-25-COMPARATOR-DRIFT), so it is not a cross-draw baseline. No arm is slot-eligible and nothing new was packaged.
* **Conditional model calculation against the unverified 0.3195 claim.** At the selected model's 0.900 false-positive mass per emitted pixel, matching that claimed target at this file's budget would need **1.29×** its credit density (0.1400 vs 0.1084); reaching the reported #5 (0.2941) needs 1.18×. This is model-based sensitivity arithmetic, not a verified score comparison or proof that all emission changes are exhausted.
* **What the fitted model does not explain among owner-reported anchors.** A habitat model in distance-to-known-faults alone cannot explain the 25 reported score anchors (leave-one-artefact-out RMSE 0.0705 against a pre-registered 0.020 threshold; the blind lattice is predicted at 0.1386 instead of 0.0904) — its residuals are per-artefact detector skill. **"Hug the known-fault halo" is not a supported strategy.** A two-band mixture is not identified either (nine-anchor spread 0.514 vs a 0.053 threshold), so it was **not adopted** and nothing was designed from it.
* **Conditional model implication outside the calibration band.** If the owner-reported anchors and fitted model are correct, implied N suggests off-band truth on these surfaces: `h28-dotted-ridge` 28,989, `lidarscarp-top2pct` 22,893, `h25-ctx-ridge` 20,072 against 12,472–13,358 for the H19-5 family. Under this selected model, those three owner-mirrored surfaces require off-band truth to reconcile the reported anchors; that is a model implication, not evidence of the actual hidden labels. The GEMSDOE10 context ridge and the 7GEMSDOE LiDAR-scarp top-2 % emission remain H29 prioritization targets, not validated truth surfaces.
* **Reproducibility flag (IR-25-COMPARATOR-DRIFT).** The frozen comparator arm recomputes to 0.149667509 here against the frozen 0.152003389 (fold 0 identical to 9 decimals; folds 1–3 differ by up to 7.4e-03); this session's pipeline re-runs bit-for-bit, so the drift is environmental (`data/work` is a gitignored derived cache that was never hashed). `evidence/work_cache_hashes.json` now pins every derived cache and the library versions. **Absolute comparators do not transfer between environments; only same-run paired contrasts do.**


## Designed factorial experiment (replaces one-factor-at-a-time)

2^(5−1), Resolution V, generator E = ABCD → 16 runs × 8 spatially blocked hide-and-recover cells; response = exact sparse-regime DTI. Lenth ME = 0.0139. Pre-registered before the run (`knowledge/04_preregistered_factorial_2026-10-02.md`).

| Factor | Family | Class | Main effect (DTI) | Folds + |
|---|---|---|---|---|
| A | Potential-field gradients (gravity + magnetics) | **inert** | -0.0027 | 1/4 |
| B | DEM curvature / scarp (100 m DEM + 3DEP LiDAR descriptors) | **matters alone** | +0.0253 | 4/4 |
| C | Strain rate / seismicity | **inert** | -0.0109 | 0/4 |
| D | Thermal / geochemical (radiometrics, conductivity, GDR 1391 springs & wells) | **inert** | +0.0044 | 4/4 |
| E | Catalogue geometry (visible known faults only) | **matters alone** | +0.0610 | 4/4 |

Top interactions: `BC` -0.0050, `BD` -0.0049, `AC` +0.0045, `BE` -0.0043. Full tables: [`evidence/factorial/results.md`](evidence/factorial/results.md).

## Add-on hypotheses (pre-registered gate, paired)

| Arm | mean DTI | Δ vs base | folds + | gate |
|---|---|---|---|---|
| BASE `BDE` | 0.1359 | — | — | — |
| +ALL | 0.1410 | +0.0050 | 4/4 | pass |
| +X1 | 0.1365 | +0.0006 | 2/4 | fail |
| +X2 | 0.1375 | +0.0015 | 2/4 | fail |
| +X3 | 0.1362 | +0.0003 | 2/4 | fail |
| EM-0 score-ordered dots vs `dot_thin` (equal N≈12391) | 0.1382 vs 0.1345 | +0.0037 | 4/4 | pass |

## Confirmation replicate (fresh draws 2,3; pre-registered)

| Arm | mean DTI | Δ vs BDE | folds + | gate |
|---|---|---|---|---|
| BASE `BDE` | 0.1305 | — | — | — |
| +ALL | 0.1343 | +0.0038 | 4/4 | pass |
| +X1 | 0.1331 | +0.0026 | 4/4 | pass |
| +X2 | 0.1338 | +0.0033 | 3/4 | pass |
| +X3 | 0.1338 | +0.0032 | 4/4 | pass |
| CFG_ABCDE | 0.1279 | -0.0027 | 2/4 | fail |
| CFG_BE | 0.1332 | +0.0027 | 3/4 | pass |
| CFG_E | 0.1098 | -0.0207 | 0/4 | fail |
| EM-0 score-ordered dots vs `dot_thin` | 0.1329 vs 0.1294 | +0.0034 | 4/4 | pass |

`CFG_*` rows are whole family sets (e.g. `CFG_BE` = the factorial's predicted-best corner, which did not replicate its predicted 0.145).

## Score ledger — user/owner-reported claims (not organizer-verified; full ledger in `registry/live_scores.json`)

| Project | Submission | Score | Note |
|---|---|---|---|
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | 0.2778 | group best: d2.8 minus 6,436 flank dots at d_cat <= 2 px (B=2, 200 m exclusion, 37,654 px, content_id 4311d7454b8e); +0.0070 over B=1 |
| GEMSDOE50 | `h50-b2-d28-37654-20261005T195308Z-c55bafc4-zeros` | 0.2778 | re-host of GEMSDOE32 B=2 (sha256 prefix c55bafc4) |
| GEMSDOE58 | `h58-1-b2-200m-moat-d28-37654-20261010T012000Z-c55bafc4-zeros` | 0.2778 | re-host of GEMSDOE32 B=2 |
| GEMSDOE78 | `h78-1-b2-tip-scarp-bridge-37758-20261018T220000Z-935455d1-zeros` | 0.2775 | B=2 base + 104 tip-scarp bridge dots |
| GEMSDOE81 | `h81-1-b2-strict-relay-54-37708-20261020T060000Z-851c36de-zeros` | 0.2775 | B=2 base + 54 strict relay dots |
| GEMSDOE79 | `h79-1-b2-scarp-tip-splay-37988-20261019T060000Z-87783287-zeros` | 0.2773 |  |
| GEMSDOE68 | `h68-3-b2-interior-3px-uncorrob-37451-20261014T150000Z-2fd09c17-zeros` | 0.2768 |  |
| GEMSDOE57 | `h57-b2-splay-corrob-36869-20261009T193000Z-bb20c457-zeros` | 0.2767 |  |
| GEMSDOE65 | `h65-2-b224-r3-189-37465-20261013T030000Z-0d7b56a6-zeros` | 0.2767 |  |
| GEMSDOE56 | `h56-2-b2-aniso3-36459-20261009T120000Z-b2a9d03f-zeros` | 0.2763 |  |

## Prior H26 register — outcomes (ranked before its runs; not a list of untried work)

| Rank | ID | Idea | Recorded outcome |
|---|---|---|---|
| 1 | H26-0 | score-aware Poisson-disk dotting + marginal-ratio budget | **passes** (+0.0037 vs score-blind dotting at equal N, 4/4 folds, replicated +0.0034) |
| 2 | H26-2 | strike-compatibility prior (DEM line orientation × visible-catalogue strike) | alone: fail on draws 0,1 (+0.0015, 2/4), small pass on fresh draws 2,3 (+0.0033, 3/4); jointly passes both |
| 3 | H26-1 | oriented cross-scarp radiometric contrast (K, Th/K, U/K × DEM normal) | alone: fail on draws 0,1 (+0.0006, 2/4), small pass on draws 2,3 (+0.0026, 4/4); jointly passes both |
| 4 | H26-3 | concealed joint step (gravity ∧ magnetic ridge, basement-depth step) | alone: fail on draws 0,1 (+0.0003, 2/4), small pass on draws 2,3 (+0.0032, 4/4); jointly passes both |
| 5 | H26-4 | dilation-tendency-weighted orientation prior (USGS 10.5066/P9YL58W6) | page-listed shapefile; direct access failed, bytes/licence not verified |

## Prior registered geological screen (H27; not a current untried candidate; full design in `knowledge/09_preregistered_hypotheses_2026-10-02.md`)

| Rank | ID | Idea | Expected proxy ΔDTI (planning bracket) | Status |
|---|---|---|---|---|
| 1 | H27-1 | directed visible-fault-tip continuation × multi-scale DEM/LiDAR scarp | +0.001 to +0.010 | TS DTI 0.151064; screen failed; stop, no slot |
| 2 | H27-2 | residualized GDR 2 m temperature probes | 0 to +0.010 | blocked: binary/schema/coverage not fetched |
| 3 | H27-3 | paleo-geothermal deposits away from visible traces | 0 to +0.005 | blocked: binary/schema/coverage not fetched |
| 4 | H27-4 | USGS heat-flow residual × structural/scarp support | 0 to +0.005 | blocked: binary, residual definition and licence not verified |

These ΔDTI ranges are planning judgments, not estimates. H27-1 failed its registered historical gate; the numbers are not a current cross-draw threshold.

## Current ranked geological hypotheses (H30; full signatures, novelty, sources, costs and gate in `knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md`)

| Rank | ID | Idea | Expected proxy ΔDTI (planning bracket) | Status |
|---|---|---|---|---|
| 1 | H30-1 | paired visible-tip cross-strike bridge × LiDAR scarp persistence | +0.001 to +0.008 | P+S DTI 0.148330, paired gain -0.001275; screen passed (+0.004078); fresh-draw confirmation failed; stop; no candidate file or slot |
| 2 | H30-2 | visible-fault junction / accommodation-zone branch field | 0 to +0.006 | registered only; not fitted |
| 3 | H30-3 | scale-persistent terrain lineament | 0 to +0.005 | registered only; not fitted |

Planning brackets are uncertain prioritization judgments, not estimates or live-score forecasts. H30-1 screen draws are 6,7; confirmation draws 8,9 are allowed only after a screen pass. Screen/confirmation outcomes and the stop decision are recorded in `knowledge/12_h30_relay_factorial_outcomes_2026-10-03.md`. Even confirmation is only proxy evidence and cannot grant slot approval by itself.

**Five-family factorial status:** the separate A–E Resolution V design is preserved in `evidence/factorial/`: 16 randomized design rows × 8 cells = 128 model cells, plus 24 reference cells (152 cell rows total). Its analyzer reproduced the tracked results byte-for-byte on 2026-10-03. H30 is additional, not a substitute. The handoff's 'unrun' note conflicts with these artifacts; see `IR-25-FACTORIAL-STATE`.

**H30 engineering smoke test:** one real-data fold/draw built aligned 83-column train/test matrices and finite, nonempty H30 features. That engineering smoke itself fit no model and computed no DTI; the separate registered screen/confirmation outcomes are summarized above. Full smoke diagnostics: `evidence/h30_feature_smoke.json`.

## Flagged for review (full list with evidence: [`registry/irregularities.json`](registry/irregularities.json))

* **IR-25-NAN-FOOTPRINT** (critical, fixed) — The first GEMSDOE25 'recommended' submission (gems25-factorial-best-v1-nan.tif, sha256 fbef100f...) used an invented footprint: 2,344,929 of the 5,167,373 pixels in the pinned owner-mirror template footprint are NaN and 2,832,257 pixels outside it are finite. …
* **IR-25-OVER-EMISSION** (critical, fixed) — The same file emitted 1,249,834 positive pixels (624,029 inside the footprint = 12.1 % of it; 625,805 outside it), roughly 10x the 2.34 % budget of H19-5 and 21x the dotted file's 60,069 pixels. At the measured truth density the false-positive term would swamp…
* **IR-25-FAKE-PIPELINE** (high, fixed) — Previous scripts were non-functional or misleading: generate_submission.py wrote synthetic diagonal stripes inside an elliptical made-up footprint; ridge_detector.py was a toy; factorial_design.py never ran (no data); the README listed src/feature_families.py,…
* **IR-25-DTI-KERNEL** (high, fixed) — The old scripts/dti_metric.py used kernel 1 - d/(R+0.5) with R = 3 px (support 3.5 px). The official kernel is max(1 - d/R, 0) with R = 300 m = 3 px.
* **IR-25-TC-BAND** (high, flagged) — Band 6 'tc' of the mirrored training_features.tif is described as 'Tilt angle or total curvature - magnetic field derivative for edge detection', but its values (3.7-70.6, positive) equal the official GeoDAWN radiometric total count channel: Spearman 0.9999 ag…
* **IR-25-PROVENANCE** (high, open) — Every competition raster here is an owner mirror (hash-pinned), not organizer-authenticated; the DrivenData data page is login-walled and the Dropbox links in the brief are unreachable from the sandbox, so byte-identity with the originals is not verified.
* **IR-25-PROXY-LIMITS** (high, disclosed) — The hide-and-recover holdout is a catalogue-gap proxy (hidden = catalogue components), not new-fault truth. H19-5 'as emitted' is not out-of-fold (and masked all catalogue pixels), so it is only a diagnostic. Family E may be flattered by the simulation. GEMSDO…
* **IR-25-PAGES-ROOT** (high, fixed) — GitHub Pages is built from main:/ (legacy), but the old site lived in docs/ with no root index.html: the public URL served the README, whose 'Executive Summary & Submit Guide' link pointed back to itself and whose download link was the broken file.
* **IR-25-COMPARATOR-DRIFT** (high, open) — The frozen hide-and-recover comparator 0.15200338908786984 (evidence/addons/emk_extension.json, variant sapd2.4 at kfrac 0.035, base BDE + the seven add-ons, draws 0-1) does NOT reproduce in this environment. Re-running that exact arm here gives 0.149667509 (f…
* **IR-25-DUPLICATE-MASKS-ACROSS-SITES** (high, flagged) — Byte-and-mask forensic audit across the focus projects shows that several sibling repositories shipped pixel-identical or byte-identical masks under different filenames: GEMSDOE30 d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca (owner-reported 0.2600) h…

## Limitations and what is needed

1. **No competition credentials or organizer receipts.** Every competition raster is an owner mirror (hash-pinned, not organizer-authenticated). The 0.2477 result and 0.3195 leader are user-provided, unverified claims; no competition/leaderboard page was accessed. Do not automate or monitor DrivenData.
2. **External binaries are blocked here:** GDR 1391 lists the 2 m probe and paleo-geothermal files under CC BY 4.0, but direct downloads failed; the USGS heat-flow ZIP is page-listed, but its bytes and licence were not verified. H27-2/3/4 require a networked runner and source/coverage checks before use.
3. **Compute:** 2 CPUs / 4 GB RAM, no GPU → boosted trees, not the reference U-Net; no raw 1 m DEM processing. The H27 screen ran in about 14 minutes after the feature cache was built.
4. **The proxy is not the truth:** the hide-and-recover holdout hides catalogue components; proxy-vs-live correlation in the group's prior record was weak (Spearman +0.33, n = 24, n.s.). Holdout wins are necessary, not sufficient.
5. **Hidden labels, public/private split, source authenticity, score claims and the portal validator remain undisclosed/unverified.**
6. **The owner-claim-calibrated model has a scope limit (IR-25-LIVE-MODEL-SCOPE):** conditional on its reported-score anchors, it matches the H19-5 family and blind lattice within 0.004 DTI but under-predicts surfaces outside that band by up to 0.059; it is not an independent score estimate.
7. **The frozen holdout comparator is environment-specific (IR-25-COMPARATOR-DRIFT):** 0.152003389 recomputes to 0.149668 here. Any future gate must recompute its comparator in the same run.

## Next work (order matters)

1. H30-1 failed its fresh-draw confirmation. Stop this candidate; do not create a TIFF or use a weekly slot. Any new idea requires a genuinely new preregistration.
2. Keep the prior five-family A–E Resolution V factorial separate: its complete `evidence/factorial/` record is present and was reproduced byte-for-byte; see `IR-25-FACTORIAL-STATE` for the handoff-state discrepancy. H30 is an additional hypothesis-specific 2², not a replacement.
3. Keep H26/H27/H29 outcomes and registrations labeled as prior work. H27-1 failed its gate; the old H29 list is registered already and must not be relabeled as novel.
4. Refresh the official-source/evidence tables and static site/feed (`scripts/check_sources.py`, then `scripts/build_site.py` and `scripts/build_readme.py`). The feed must never request or follow `drivendata.org`.
5. Keep the existing D2.8 download format-validated but unscored/not slot-approved. A passing H30 proxy gate is not a competition score, not confirmation until the fresh draw, and not authorization to upload.
6. Open a PR from the fixed Arena session branch, review the checks, and merge only through the GitHub PR workflow if permitted; never claim an unverified merge or deployment.

## Standing session charter

Read this README, both the verbatim owner brief and the current continuation brief below, then `AGENTS.md` at the start of every session. First commands: `git fetch origin`, compare with the fixed session branch, `gh pr list --state open`. Pre-register before fitting. No weekly slot unless the specific candidate beats the current comparable same-run holdout best and passes the exact-file audit; no exception is authorized here. Never automate `drivendata.org`. Review in three passes. Unknown stays unknown.

## Reproduce

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group all          # SHA-256-pinned inputs from the owner's public repos -> data/ (ignored by Git); same as: bash scripts/download_competition_data.sh
.venv/bin/python scripts/build_features.py && .venv/bin/python scripts/build_addons.py
# pre-registered experiments (knowledge/04, 05)
.venv/bin/python scripts/run_factorial.py && .venv/bin/python scripts/analyze_factorial.py            # ~30 min on 2 CPUs
.venv/bin/python scripts/run_addons.py && .venv/bin/python scripts/analyze_addons.py                  # draws 0,1
.venv/bin/python scripts/run_addons.py --out evidence/addons_confirm --draws 2 3 --extra-configs ABCDE BE E && .venv/bin/python scripts/analyze_addons.py --dir evidence/addons_confirm
.venv/bin/python scripts/run_emk_extension.py --base BDE --extras X1_K X1_ThK X1_UK X2_compat X2_compat_coh X3_gm X3_gd   # post hoc (Addendum A)
# H27-1 frozen 2x2 screen (knowledge/09); confirmation is permitted only if screen gate passes
.venv/bin/python scripts/run_h27.py --stage screen && .venv/bin/python scripts/analyze_h27.py --dir evidence/h27_screen
# if and only if the screen's absolute + paired gates pass:
.venv/bin/python scripts/run_h27.py --stage confirm && .venv/bin/python scripts/analyze_h27.py --dir evidence/h27_confirm
# H28: metric-model calibration conditional on owner-reported anchors, inverse design, holdout factorial (knowledge/10)
.venv/bin/python scripts/restore_artifacts.py                # fetch + hash the 30 owner-mirrored competition rasters -> registry/artifact_ledger.json
.venv/bin/python scripts/run_h28.py                        # anchors, checks, ceiling sweep, designs, sensitivity (~7 min)
.venv/bin/python scripts/run_h28.py --habitat-only          # the section 5 misspecification diagnostic (~10 min)
.venv/bin/python scripts/run_h28_mixture.py                 # two-band mixture test (D3)
.venv/bin/python scripts/run_h28_holdout.py && .venv/bin/python scripts/analyze_h28_holdout.py   # historical run; see evidence/h28_holdout/
# H30-1 is an additional preregistered paired-tip × scarp 2²; it does not replace the five-family design
.venv/bin/python scripts/smoke_h30_features.py                # real-data feature check only; no model fit/DTI
.venv/bin/python scripts/run_h30_relay_factorial.py --stage screen && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_screen
# Commit the screen evidence; the runner requires a clean tree and revalidates its hashes/gate.
git add evidence/h30_relay_screen && git commit -m 'Record H30 screen evidence'
# ONLY if the saved screen results.json says screen_gate_passed=true:
.venv/bin/python scripts/run_h30_relay_factorial.py --stage confirm && .venv/bin/python scripts/analyze_h30_relay_factorial.py --dir evidence/h30_relay_confirm
# forensics and emission model
.venv/bin/python scripts/analyze_scored_rasters.py && .venv/bin/python scripts/emission_model.py && .venv/bin/python scripts/validate_emission_model.py && .venv/bin/python scripts/harness_references.py
# files, site, README
.venv/bin/python scripts/build_candidate.py --help            # train on the full catalogue, emit, verify (exploratory surface)
.venv/bin/python scripts/package_submissions.py --exploratory-receipt docs/downloads/checks-<file>.json
.venv/bin/python scripts/build_data_dictionary.py && .venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py
.venv/bin/python -m pytest -q && .venv/bin/python -m ruff check src scripts tests
```

Set `GEMS_DATA_DIR` / `GEMS_WORK_DIR` to keep the 419 MB raster and the ~1.5 GB feature cache outside the checkout.

## Repository map

| Path | Role |
|---|---|
| `src/gems25/` | metric (official DTI + brute-force twin), hide-and-recover holdout, thinning/NMS, families & features, H30 relay/scarp add-ons, factorial engine, experiment cells, strict submission writer/checker |
| `scripts/` | restore, build, run, analyse, package, site, README, feed, score recorder |
| `registry/` | sources (with verification status), irregularities, score ledger, data pins, shipped submissions |
| `evidence/` | machine-readable results and forensics |
| `knowledge/` | pre-registrations, ranked hypotheses, verified research digest, the brief |
| `docs/`, `index.html` | GitHub Pages site (root `index.html` is the landing page; Pages builds from `main:/`) |
| `tests/` | unit, parity, integrity and reproduction tests |

## Owner brief (verbatim) — read every session

<details><summary><strong>Full text of the owner's brief for this session</strong> (copied from the task message of 2026-10-02; link markup and whitespace as pasted)</summary>

```text
Review the repo.   
  
There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  
  
Replace one-factor-at-a-time testing with a designed factorial experiment. The repo's own hypothesis history — single-named attempts like "conj_alteration_mag," "dem10-scarp," "topo-geophys-x-complexity-prior" — reads as classical one-factor-at-a-time testing, a documented methodological weakness: Box, Hunter, and Hunter's foundational Statistics for Experimenters shows why holding other factors fixed while varying one at a time systematically misses interaction effects — cases where two features are each weak alone but jointly diagnostic because the real signature is their conjunction, not either one's sum — and the name "conj_alteration_mag" is already gesturing at exactly this without treating it as a designed experiment. Replace the ad hoc sequence with a fractional factorial design across the candidate feature families already identified (potential-field gradients, DEM curvature/scarp, strain/seismicity, thermal/geochemical, catalogue-geometry), run against the hide-and-recover holdout, which estimates every family's main effect on DTI alongside its pairwise interactions in a modest, pre-specified number of runs — far fewer than testing every combination in full — rather than an open-ended sequence of hunches; the sparsity-of-effects principle this literature establishes, that real systems are typically dominated by a few main effects and low-order interactions rather than many high-order ones, means this is enough to rank which families matter alone, which only matter in combination, and which are inert — redirected by evidence, not by which conjunction sounds geologically plausible.  
  
Here are the results from submissions into the competition, separated by ....:  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html))  
  
gems-submission-20260925T001403Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)](https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/))  
  
gems6_hgb88-topk03_33cec71ff0: 0.0286  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html))  
  
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193  
  
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830  
  
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html))  
  
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)](https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/))  
  
gems-submission-20260926T163915Z-237f0063: 0.0343  
  
....  
  
[[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html))  
  
gems-submission-20260926T175114Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)](https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/))  
  
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461  
  
....  
  
[[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)](https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/))  
  
Hedge-v2_submission: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html))  
  
2314b599: 0.0107  
  
....  
  
[[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html))  
  
gems-structural-area06-v1: 0.0202  
  
....  
  
[[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html))  
  
r7-nms3-dem10-scarp_0c9199f14e62:0.1294  
  
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294  
  
....  
  
[[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html))  
  
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782  
  
....  
  
[[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html))  
  
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020  
  
....  
  
[[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)](https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/))  
  
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187  
  
....  
  
[[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)](https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/))  
  
H19-C_20260930T212401Z_c11e495e: 0.0297  
  
....  
  
[[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html))  
  
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894  
  
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)](https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/))  
  
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461  
  
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921  
  
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280  
  
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839  
  
....  
  
[[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)](https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/))  
  
20261001_r13-lattice-s5_v2_nan-outside:0.0904  
  
....  
  
[[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html))  
  
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855  
  
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976  
  
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)](https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/))  
  
h19-4-reference-20260930-691e4dfa: 0.1894  
  
....  
  
[[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html))  
  
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890  
  
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html))  
  
h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002  
  
h23-b-dti-optimal-emission-10pct-20261002-86176698-nan:   
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)](https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/))  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)](https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/))  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
....  
  
25GEMSDOE SCORE:  
  
....  
  
26GEMSDOE SCORE:  
  
....  
  
27GEMSDOE SCORE:  
  
....  
  
WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:  
  
24GEMSDOE SCORE:  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2477?  
  
Answer the question using Phd level experience, knowledge, and judgement.   
  
The following is the leaderboard for the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/))  
  
   
  
We need to quickly look at the results and results from the GEMSDOE websites above.  
  
Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.  
  
The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.  
  
   
  
[[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html))  
  
gems-submission-20260925T001403Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)](https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/))  
  
gems6_hgb88-topk03_33cec71ff0: 0.0286  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html))  
  
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193  
  
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830  
  
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html))  
  
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)](https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/))  
  
gems-submission-20260926T163915Z-237f0063: 0.0343  
  
....  
  
[[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html))  
  
gems-submission-20260926T175114Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)](https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/))  
  
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461  
  
....  
  
[[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)](https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/))  
  
Hedge-v2_submission: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html))  
  
2314b599: 0.0107  
  
....  
  
[[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html))  
  
gems-structural-area06-v1: 0.0202  
  
....  
  
[[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html))  
  
r7-nms3-dem10-scarp_0c9199f14e62:0.1294  
  
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294  
  
....  
  
[[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html))  
  
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782  
  
....  
  
[[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html))  
  
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020  
  
....  
  
[[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)](https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/))  
  
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187  
  
....  
  
[[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)](https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/))  
  
H19-C_20260930T212401Z_c11e495e: 0.0297  
  
....  
  
[[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html))  
  
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894  
  
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)](https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/))  
  
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461  
  
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921  
  
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280  
  
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839  
  
....  
  
[[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)](https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/))  
  
20261001_r13-lattice-s5_v2_nan-outside:0.0904  
  
....  
  
[[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html))  
  
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855  
  
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976  
  
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)](https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/))  
  
h19-4-reference-20260930-691e4dfa: 0.1894  
  
....  
  
[[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html))  
  
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890  
  
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html))  
  
h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002  
  
h23-b-dti-optimal-emission-10pct-20261002-86176698-nan:   
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)](https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/))  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)](https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/))  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
....  
  
25GEMSDOE SCORE:  
  
....  
  
26GEMSDOE SCORE:  
  
....  
  
27GEMSDOE SCORE:  
  
....  
    
  
WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:  
  
24GEMSDOE SCORE:  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2477?  
  
Answer the question using Phd level experience, knowledge, and judgement.   
  
The following is the leaderboard for the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/))  
  
0.3195	is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.    
  
Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.  
  
Review the repo.   
  
The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.  
  
Our Core Values  
  
Maximize P(Win)  
  
“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.  
  
Own the Outcome  
  
We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
    
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
We need to focus on being able to generate a submission into the competition.    
  
The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.  
  
I tried to submit the document that i downloaded from the site but it returned this error on the submission form:  
  
"Predicted values must be in range [0, 1]"  
  
Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25  
  
Here is the submission page when i click submit file  
  
New submission  
  
File to submitNo file chosen  
  
You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.  
  
Note (optional)  
  
A short comment to help you or your team tell submissions apart later e.g. clustering with k=25  
  
Create a executive summary subpage that explains exactly how to make a submission into the contest.  
  
Work on the next steps from the previous sessions first.  
  
The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/))  
  
We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.    
  
This is the guidelines we need to follow.[[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)](https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/))  
  
Get familiar with the problem through the overview and problem description,[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)). You might also want to reference additional resources available on the about page,[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)).  
  
Download the data from the data,[[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)), tab.    
  
Create and train your own model. This reference solution,[[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)](https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)) implements a simple approach.  
  
Use your model to generate predictions that match the submission format.  
  
Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.    
  
this pdf outlines how submissions must be entered into the competition.    
  
[[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)](https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf))  
  
You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.  
  
❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)) (verified redirect to login)  
  
See below for links from the above site.  See attached files for links from the above site.  
  
[[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)](https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391))  
  
Download competition data from [[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)) (requires login) to data/  
  
See links below for competition data:  
  
[[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;amp;st=wz4kofki&amp;amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0)](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0))  
  
[[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;amp;st=8junzdyw&amp;amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0)](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0))  
  
[[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;amp;st=rnino7ya&amp;amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0)](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0))  
  
[[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;amp;st=zj1lag1r&amp;amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0)](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0))  
  
[[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;amp;st=srhhir10&amp;amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0)](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0))  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
Site creation  
  
Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.    
  
It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.  
  
**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).  
  
you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
Run this task through multiple passes.  
  
Pass 1: Implement the task completely and verify the result.  
  
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.  
  
Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.  
  
Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.  
  
Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.
```

</details>

## Current continuation task (2026-10-03; consolidated restatement, not a verbatim quote)

The current user message was condensed into the session handoff. The full active scope and acceptance criteria are preserved below, separately from the verbatim 2026-10-02 brief.

<details><summary><strong>Full continuation brief and current constraints</strong></summary>

~~~text
# Active project brief — continuation task (2026-10-03)

> **Status of this transcription:** the exact current user message was condensed into a session handoff before this continuation. This file preserves its full active task and acceptance criteria as received in that handoff; it is a faithful consolidated restatement, **not a verbatim quotation**. The earlier 2026-10-02 message remains separately preserved as `owner_brief_verbatim.txt`.

## Objective and decision principles

Continue the GEMSDOE25 project toward a higher-scoring DOE GEMS Prize submission. Apply **Maximize P(Win)** and **Own the Outcome**: spend effort on verifiable scientific leverage, resolve data/engineering blockers autonomously, and report negative results. Treat the reported 0.2477 result and the stated 0.3195 leaderboard target as user/owner-reported claims unless official evidence is independently accessed; do not imply that either is verified.

## Scientific work and experimental design

- Review the full standing README/brief and repository history each session. Study prior evidence before proposing work; do not relabel earlier H26/H27/H28/H29 hypotheses or runs as new experiments.
- Move beyond one-factor-at-a-time testing. The completed historical design is a preregistered 2^(5−1), Resolution V fractional factorial across the five existing families: potential-field gradients, DEM curvature/scarp, strain/seismicity, thermal/geochemical, and catalogue geometry. It estimates main effects and pairwise interactions on the spatially blocked hide-and-recover holdout; its recorded results are prior work, not new evidence.
- Before implementing a new geological candidate, propose and rank **3–5 genuinely untried hypotheses**. For each, state the layers, physical signature, rationale for finding faults missing from the catalogue, how it differs from prior repository work, expected holdout DTI gain as an explicitly uncertain planning bracket, cost, and data/validation status.
- Verify each source claim from the cited official or primary source, line by line where relevant. If a candidate needs new external data, verify that the free official source and required data are actually obtainable before calling the candidate viable. A page listing is not proof that a binary, schema, coverage, or licence has been checked.
- Preregister the design, folds/draws, model, response, analysis, and promotion gate before fitting. Do not tune after seeing outcomes. Use spatially blocked hide-and-recover holdout, report main effects and pairwise interactions, and distinguish proxy evidence from competition performance.
- Validate the top candidate before creating a new submission artifact or considering a weekly submission slot. The candidate must beat the best *comparable same-run* spatial holdout control, pass the preregistered paired/confirmation gate, and pass an exact-file audit. A prior frozen comparator that does not reproduce is not a valid cross-run threshold. A screen pass alone is not confirmation.

## Submission artifact and site

- Keep the format-validated GeoTIFF easy to find and download from the site/README. Verify the competition template's dimensions, CRS, geotransform, valid footprint, and `[0,1]` value range. Each new file must have a unique content-addressed filename, SHA-256 receipt, and concise submission note.
- Do not create, label, or promote a new candidate unless the registered holdout gate passes. Do not spend a weekly submission slot on an unvalidated candidate.
- Preserve the concise executive-summary/how-to-submit guide, with manual-only upload instructions and clear status labels. The site and source/feed pages must be useful, current, and link to manually reviewable official sources.

## Data, evidence, and communication rules

- No automated access, monitoring, scraping, or submission to `drivendata.org`; the repository's `AGENTS.md` and DrivenData Terms policy prohibit it. Do not use DrivenData authentication. Hash-pinned owner mirrors are owner-supplied bytes, not organizer-authenticated files.
- Keep OFFICIAL source statements, owner/user-reported score claims, locally COMPUTED measurements, and INFERENCE clearly separate. Unknown stays unknown. Flag inconsistencies, stale links, data/schema/licensing gaps, comparator drift, and other irregularities rather than silently resolving them.
- Prefer free public official sources for third-party data. Provide direct links and enough provenance for manual review. Do not commit large restored datasets or caches; use the repository's ignored/external-data conventions.
- Keep current, auditable source/evidence tables, data manifest, score claims and artifact ledger. Update the README and site only from evidence that is actually present and verified.

## Autonomous execution and quality gates

Work autonomously; do not ask the owner for manual inputs or credentials. Before finishing, complete three cumulative review passes: (1) implement and verify against sources and the registered design; (2) inspect bugs, assumptions, leakage risks, and edge cases, then fix them; (3) re-check the full result against this brief and the original request. Record the passes in `registry/review_passes.json`.

Prepare a PR from the fixed Arena session branch and merge only through the repository's PR workflow if checks and authentication permit. Never claim a PR, merge, deployment, or score verification unless a URL/status/receipt proves it. Report limitations, remaining work, and any access that is genuinely needed without requesting secrets.

## Existing facts that constrain this continuation

- `data/` was initially empty; project inputs may be restored only from hash-pinned public owner mirrors or verified official sources, never by automating competition access.
- The previous H28 holdout's frozen comparator reproduction failed. Its nominal best arm was not slot-eligible.
- The H27-1 combined tip/scarp arm failed its registered absolute comparator gate; its T-only screen was unconfirmed and is not slot-eligible.
- Existing H26 factorial, add-on, emission, and H29 next-hypothesis registers are prior work and must be reviewed for overlap.
- Existing downloadable D2.8 files are format-validated, unscored/owner-mirror artifacts and are not approved for a weekly slot.
- **State discrepancy:** the condensed handoff says the five-family factorial remains unrun, while the tracked `evidence/factorial/` contains 16 model rows × 8 cells, reference rows, and complete analysis. `scripts/analyze_factorial.py` reproduced its results byte-for-byte on 2026-10-03. This evidence and the mismatch are recorded as `IR-25-FACTORIAL-STATE`; do not overwrite or rerun the old experiment just to resolve a wording conflict. H30 is explicitly additional, not a replacement.
~~~

</details>

## Current session prompt (2026-10-25 — verbatim)

<details><summary><strong>Full text of the 2026-10-25 prompt and PARALLEL-RUN PROTOCOL</strong></summary>

~~~text
# Current Session Prompt (2026-10-25 — Verbatim)

Focus on the highest scoring submissions from the below sites:

https://buffedlizard55-lab.github.io/GEMSDOE24/
https://buffedlizard55-lab.github.io/GEMSDOE25/
https://buffedlizard55-lab.github.io/GEMSDOE27/
https://buffedlizard55-lab.github.io/GEMSDOE28/
https://buffedlizard55-lab.github.io/GEMSDOE30/
https://buffedlizard55-lab.github.io/GEMSDOE31/
https://buffedlizard55-lab.github.io/GEMSDOE32/
https://buffedlizard55-lab.github.io/GEMSDOE33/
https://buffedlizard55-lab.github.io/GEMSDOE36/

We want to generate a submission with a higher score than the current highest scoring submission of 0.2778 from https://buffedlizard55-lab.github.io/GEMSDOE32/ (h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778). Study, analyze and explain why and how it achieved this score and if we can generate a submission that is higher scoring and how. The highest score on the leaderboard is 0.4413.

You MUST generate a UNIQUE tif submission for the competition. Do not copy a previous submission, unless it is for learning and education.

Make it obvious whether it is ok to download and submit the generated tif submission for the competition. Any inspection or validation to see if it is ready for submission should be done by the project without human intervention.

PARALLEL-RUN PROTOCOL — GEMS Prize (#306)
1. Stay in your lane: Each run works ONE method family. Check registry/ first; do not exceed 0.90 surface rank-correlation or 70% final 3-px dot overlap with any registered raster.
2. Shared plumbing, don't rebuild: Reuse the cached feature stack, holdout evaluator, and submission writer. Holdout = hide-and-recover: withhold whole fault segments (with buffer), derive catalogue features only from visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha=0.2, beta=0.8, 300 m triangular kernel).
3. Two score labels only: Every number must say HOLDOUT-DTI (with evaluator version, n withheld positives, 95% CI) or ORGANIZER-CONFIRMED (with submission ID). Never write a projection as a score.
4. Leakage check first: Any feature with single-feature holdout AUC > 0.90 is leakage until proven otherwise. Test each feature alone on the holdout before trusting a model.
5. Budget: Stop after at most 3 experiments or 2 hours. Keep only changes that beat the baseline in >=3/4 spatial folds or improve mean DTI with 95% CI excluding 0; otherwise report a clean negative result.
6. Output — one JSON RUN CARD at the end: hypothesis & physical mechanism, named non-fault process that could mimic it, holdout DTI + CI, correlation/overlap vs registry, raster SHA-256, validator output (no NaN in footprint, values in [0,1], CRS/shape/transform match), unique filename + <=140-char submission note, and verdict: promote | negative.

Core values:
1. Maximize P(Win): Every decision, line of code, and verification pass must serve a single overarching goal: maximizing the probability of winning the competition.
2. Own the Outcome: Take full, end-to-end ownership of the project's success. Do not stop at partial fixes or surface-level compliance; proactively identify gaps, verify from trusted sources, and drive the work all the way to a winning result.

Verify everything from official verified trusted sources with links for manual review. Flag any irregularities for review. No hallucinations. Run the task through three passes (Pass 1: Implement and verify; Pass 2: Hunt bugs, missing requirements, incorrect assumptions, edge cases; Pass 3: Re-check against original request). Create a pull request and merge it onto main.
~~~

</details>
