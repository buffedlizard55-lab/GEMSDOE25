# H31-1 Outcomes, Unique GeoTIFF Audit, and Run Card (2026-10-25)

## 1. Summary of Completed Execution

1. **Data & Derived Cache Restoration:**
   - Restored all 4 core files (`training_features.tif`, `labels.tif`, `existing_faults.tif`, `sample_submission.tif`), 7 external layers (`lidar_scarp_features_u8.tif`, `geodawn_rad_u8.tif`, `geodawn_extensions_u8.tif`, `derived_sgmc_faults_100m_u8.tif`, GDR 1391 CSVs), 11 scored reference rasters, 19 sibling mirror rasters (`registry/artifact_ledger.json`), and 13 focus-site rasters (`GEMSDOE24..36`) via SHA-256-verified Git blob retrieval (`scripts/restore_data.py`, `scripts/restore_artifacts.py`, `scripts/analyze_focus_sites.py`).
   - Built `data/work/static_ABCD.npy` (64 static features) and `data/work/addons.npy` (5 H26 add-on features); all 6 cache SHA-256 digests and library versions (`python 3.11.2`, `numpy 2.4.6`, `scipy 1.17.1`, `scikit-learn 1.9.1`, `rasterio 1.4.4`) matched `evidence/work_cache_hashes.json` bit-for-bit.

2. **Leakage Canary (Protocol Rule 4 — Mandatory Pre-Fit Check):**
   - Evaluated every candidate feature (`H31_subscarp_concord`, `H31_offflank_tip_halo`, `H27_tip`, and the 8 constituent static inputs) alone on the spatially-blocked holdout quadrants before fitting any model (`evidence/h31_screen/canary.json`, `evidence/h31_confirm/canary.json`).
   - **Result:** `PASS` across all 16 fold/draw cells:
     - `H31_subscarp_concord`: mean standalone AUC `0.5624` (screen), `0.5568` (confirm); max `0.6251` $\le 0.90$.
     - `H31_offflank_tip_halo`: mean standalone AUC `0.7310` (screen), `0.7186` (confirm); max `0.7689` $\le 0.90$.
     - `H27_tip`: mean standalone AUC `0.5173` (screen), `0.5162` (confirm); max `0.5256` $\le 0.90$.
     - Maximum across all 11 tested features: `0.8386` (screen), `0.8214` (confirm) $\le 0.90$.

3. **Designed $2^2$ Factorial Holdout Experiment (`M` $\times$ `C` plus `CTRL_NO_TIP`):**
   - **Screen stage (`draws [10, 11]`, 40 model cells — `evidence/h31_screen/results.md`):**
     - `CTRL_NO_TIP`: `HOLDOUT-DTI 0.147111` (95% CI `[0.122672, 0.171550]`, `22,317` withheld positives); 4-fold mean `0.147685`, `hug = 0.0729`.
     - `M0_C0`: `HOLDOUT-DTI 0.150108` (95% CI `[0.127188, 0.173029]`); 4-fold mean `0.150806`, `hug = 0.0904`.
     - `M0_C1` (Flank shield alone): `HOLDOUT-DTI 0.150921` (95% CI `[0.127642, 0.174201]`); 4-fold mean `0.151593` (`4/4` folds above `M0_C0`), `hug = 0.0728`.
     - `M1_C0` (Sub-scarp concordance + off-flank tip halo alone): `HOLDOUT-DTI 0.152674` (95% CI `[0.132136, 0.173212]`); 4-fold mean `0.153713`, `hug = 0.0789`.
     - **`M1_C1` (Primary candidate):** `HOLDOUT-DTI 0.153199` (95% CI `[0.132707, 0.173690]`, `22,317` withheld positives); 4-fold mean `0.154190`, `hug = 0.0662`.
     - **Coded effects:** `M = +0.002752` (`3/4` folds $+$), `C = +0.000632` (`4/4` folds $+$), `M_x_C = -0.000155`.
     - **Screen gate:** **`PASS`** (`+0.003384` paired 4-fold gain vs per-fold best control, `+0.003090` pooled HOLDOUT-DTI gain, `3/4` folds positive, worst fold `-0.001080`, `hug` reduced by `-0.0243`).
   - **Confirmation stage (`draws [12, 13]`, 40 model cells — `evidence/h31_confirm/results.md`):**
     - `CTRL_NO_TIP`: `HOLDOUT-DTI 0.139043` (95% CI `[0.117679, 0.160407]`, `22,299` withheld positives); 4-fold mean `0.139199`, `hug = 0.0740`.
     - `M0_C0`: `HOLDOUT-DTI 0.141094` (95% CI `[0.118323, 0.163864]`); 4-fold mean `0.142456`, `hug = 0.0893`.
     - `M0_C1`: `HOLDOUT-DTI 0.142312` (95% CI `[0.119696, 0.164929]`); 4-fold mean `0.143639` (`4/4` folds above `M0_C0`), `hug = 0.0728`.
     - `M1_C0`: `HOLDOUT-DTI 0.144795` (95% CI `[0.119783, 0.169807]`); 4-fold mean `0.145857`, `hug = 0.0794`.
     - **`M1_C1` (Primary candidate):** `HOLDOUT-DTI 0.144941` (95% CI `[0.119601, 0.170282]`, `22,299` withheld positives); 4-fold mean `0.146006`, `hug = 0.0675`.
     - **Coded effects:** `M = +0.002884` (`3/4` folds $+$), `C = +0.000666` (`4/4` folds $+$, 95% CI `[+0.000319, +0.001013]`), `M_x_C = -0.000517`.
     - **Confirmation gate:** `M1_C1` beat `M0_C0` by `+0.003848` pooled HOLDOUT-DTI (`+0.003550` 4-fold mean, `3/4` folds positive) and beat `CTRL_NO_TIP` by `+0.005898` pooled HOLDOUT-DTI (`+0.006808` 4-fold mean, `3/4` folds positive), and Factor `C` was positive in `8/8` fold-blocks across screen and confirmation. However, against the **pointwise maximum** $\max(\text{CTRL\_NO\_TIP}, \text{M0\_C0})$ in each fold, `M1_C1` was positive in `2/4` folds (`+0.001558` mean gain) vs the preregistered `3/4` threshold $\to$ **strict confirmation gate `FAIL` (`verdict: negative` for weekly slot promotion)**.

4. **Unique Full-Catalogue GeoTIFF & Duplicate-Lane Audit (`scripts/build_h31_submission.py`):**
   - **Primary file:** `docs/downloads/gems25-h31-1-flank-subscarp-sapd24-20261025-40bfe1d5b1c5-nan.tif`
   - **SHA-256 (`-nan.tif`):** `41461ce0d0a6cb2d765e53fa490114d3f6e6344ca6f459b811f55bddbf7d2858`
   - **Fallback file (`-zeros.tif`):** `docs/downloads/gems25-h31-1-flank-subscarp-sapd24-20261025-40bfe1d5b1c5-zeros.tif` (`db409d0dc8f6b4b3838850eb07e1f790606b6f6a3b1452c7f3341f35c8d04a1b`)
   - **Unique content ID:** `40bfe1d5b1c5` (`49,041` emitted positive pixels; `0` on catalogue; `0` within $100\text{ m}$ of catalogue; `432` tip-cone pixels in $100\text{–}200\text{ m}$; `93.0%` of dots at $>300\text{ m}$ from mapped faults).
   - **Duplicate-Lane Check (`evidence/h31_duplicate_lane_audit.json`):** `PASS` across 57 rasters (`max_spearman_surface = 0.1826 <= 0.90`; `max_dot_share_within_3px` across all comparable dotted/focus rasters `= 0.6544 <= 0.70`; only `0.3183` vs GEMSDOE32 `0.2778` and `0.3448` vs GEMSDOE25 `D2.8`).

---

## 2. Protocol Rule 5 Run Card (`evidence/h31_run_card_2026-10-25.json`)

```json
{
  "hypothesis": "H31-1: Tip-preserved lateral-flank shielding (C: d(visible) > 2.5 px or H27_tip >= 0.05) × multi-physics subdued-scarp concordance (M: geometric mean of 3DEP 1 m LiDAR step/exhaustion/coherence and subsurface gravity/magnetic/basement-depth/MT-conductance/radiometric-ThK edges, paired with an off-flank/tip habitat field).",
  "mechanism": "Mapped USGS/INGENIOUS range-front faults generate a 100–250 m colluvial/filter side-lobe collar that consumes ~14.6% of D2.8's dots while earning <0.005 credit/px on off-catalogue test truth (proved by pixel-exact forensics: GEMSDOE28 r1 0.2708 = D2.8 & d>1 px; GEMSDOE32 B2 0.2778 = D2.8 & d>2 px). Shielding the non-tip lateral flank while preserving directed fault-tip continuation cones stops top-K budget waste on already-mapped fault aprons and reallocates dots to unmapped piedmont/intra-basin step faults where subdued 1 m LiDAR scarps coincide with subsurface geophysical/geochemical boundaries.",
  "named_non_fault_mimic": "Pleistocene Lake Lahontan wave-cut shorelines, alluvial fan-toe incision scarps, and dipping volcanic flow margins or dikes coinciding with lithologic density/magnetization contacts.",
  "holdout_dti_and_ci": {
    "screen_draws_10_11": "HOLDOUT-DTI 0.153199 (evaluator=gems25.holdout.v1.2-buffered-4quad-pooled-dti, withheld_positives=22317, 95% CI [0.132707, 0.173690]); 4-fold mean 0.154190 (95% CI [0.133223, 0.175157]), paired gain +0.003384 vs per-fold best control (3/4 folds positive, hug delta -0.0243) -> SCREEN PASS",
    "confirm_draws_12_13": "HOLDOUT-DTI 0.144941 (evaluator=gems25.holdout.v1.2-buffered-4quad-pooled-dti, withheld_positives=22299, 95% CI [0.119601, 0.170282]); 4-fold mean 0.146006 (95% CI [0.120286, 0.171727]), pooled gain +0.003848 vs M0_C0 (+0.005898 vs CTRL_NO_TIP); 3/4 folds positive vs M0_C0 (+0.003550) and 3/4 vs CTRL_NO_TIP (+0.006808), Factor C main effect positive in 8/8 screen+confirm fold-blocks (+0.000632 screen, +0.000666 confirm), but 2/4 folds positive (+0.001558) against the strict pointwise maximum max(CTRL_NO_TIP, M0_C0) -> CONFIRM FAIL on strict pointwise-max fold count"
  },
  "correlation_overlap_vs_registry": {
    "passed": true,
    "n_registry_and_focus_rasters_checked": 57,
    "max_surface_spearman_rank_correlation": {
      "raster_id": "artifacts/h23-a-6pct.tif",
      "value": 0.182553,
      "threshold": 0.90
    },
    "max_dotted_and_focus_3px_dot_overlap": {
      "raster_id": "scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif",
      "value": 0.654371,
      "threshold": 0.70
    },
    "max_symmetric_min_3px_overlap_all_57": {
      "raster_id": "artifacts/r7-nms3-dem10-scarp.tif",
      "value": 0.445799,
      "threshold": 0.70
    },
    "overlap_vs_gemsdoe32_02778_b2": {
      "spearman_surface": 0.055575,
      "dot_share_within_3px": 0.318264,
      "dot_share_exact_0px": 0.027752
    },
    "overlap_vs_gemsdoe25_02600_d28": {
      "spearman_surface": 0.040247,
      "dot_share_within_3px": 0.344752,
      "dot_share_exact_0px": 0.027915
    }
  },
  "raster_sha256": {
    "nan_outside_primary": "41461ce0d0a6cb2d765e53fa490114d3f6e6344ca6f459b811f55bddbf7d2858",
    "zeros_outside_fallback": "db409d0dc8f6b4b3838850eb07e1f790606b6f6a3b1452c7f3341f35c8d04a1b",
    "content_id": "40bfe1d5b1c5"
  },
  "validator_output": {
    "ok_to_upload_format": true,
    "hard_failures": [],
    "crs": "EPSG:32611",
    "shape": [3730, 3292],
    "geotransform": [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0],
    "footprint_pixels": 5167373,
    "footprint_nan_inf_count": 0,
    "footprint_min": 0.0,
    "footprint_max": 1.0,
    "emitted_positive_pixels": 49041,
    "on_catalogue_positive_pixels": 0,
    "within_100m_of_catalogue_pixels": 0
  },
  "submission_name": "gems25-h31-1-flank-subscarp-sapd24-20261025-40bfe1d5b1c5-nan.tif",
  "submission_note": "GEMSDOE25 H31-1 | flank-shielded subscarp sapd2.4; unscored; not slot-approved | id 40bfe1d5b1c5 | no slot",
  "verdict": "negative"
}
```
