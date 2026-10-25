# H31-1 Post-Run Outcomes & Cross-Site Forensic Synthesis (2026-10-25)

**Status:** Completed (`verdict = promote`).
**Preregistration:** [`13_preregistered_h31_anisotropic_scarp_coherence_2026-10-25.md`](13_preregistered_h31_anisotropic_scarp_coherence_2026-10-25.md).
**Evidence directory:** [`../evidence/h31_experiments/`](../evidence/h31_experiments/).

---

## 1. Cross-Site Forensic Analysis (`GEMSDOE24`, `25`, `27`, `28`, `30`, `31`, `32`, `33`, `36`) & Why `GEMSDOE32` Achieved `0.2778`

We performed a byte-and-pixel forensic audit across the actual GeoTIFFs of the 9 focus projects (`data/scored/` and `data/focus_sites/`). All owner-reported competition numbers below are explicitly labeled as **owner-reported claims** (not organizer receipts).

### 1.1 Exact Metric Mechanics & Break-Even Marginal Credit
Under the official Distance-Tolerant IoU (`DTI`, $\alpha=0.2$, $\beta=0.8$, 300 m = 3 px triangular kernel $K(r)=\max(0,1-r/3)$):

$$\text{DTI}(P,G)=\frac{\text{TP}_w}{0.2\,\text{TP}_w + 0.2\,\text{FP}_w + 0.8\,\text{FN}_w} = \frac{\text{TP}_w}{0.2\,\text{TP}_w(1-\rho) + 0.2\,N + 0.8\,|G|}$$

Adding $\Delta N$ binary dots with marginal kernel-weighted true-positive credit $c = \Delta\text{TP}_w/\Delta N$ increases DTI if and only if:

$$c > \tau(\text{DTI}) = \frac{0.2\,\text{DTI}}{1 - 0.2\,\text{DTI}}$$

| Reference Score (owner-reported) | Break-even marginal credit $\tau$ per dot | Minimum hit rate at $d=1\text{ px}$ ($K=2/3$) |
|---|---|---|
| `0.2477` (`GEMSDOE24` `d1.5`) | `0.0521` | `7.82 %` |
| `0.2600` (`GEMSDOE25` / `GEMSDOE30` `d2.8`) | `0.0549` | `8.23 %` |
| `0.2708` (`GEMSDOE28` / `GEMSDOE31` `B=1`) | `0.0573` | `8.59 %` |
| **`0.2778` (`GEMSDOE32` `B=2`)** | **`0.0588`** | **`8.82 %`** |
| `0.3195` (earlier leaderboard snapshot) | `0.0683` | `10.24 %` |
| `0.4413` (latest leaderboard claim) | `0.0968` | `14.52 %` |

### 1.2 The Nested Subset Hierarchy (`0.1922 -> 0.2477 -> 0.2600 -> 0.2708 -> 0.2778`)
Byte-exact pixel comparison proves that five landmark group submissions form a strict nested subset chain derived from the same raw ridge mask (`H19-5`, `121,131` px):

$$\text{H19-5}_{121{,}131} \supset \text{GEMSDOE24}_{60{,}069} \supset \text{GEMSDOE25/30}_{44{,}090} \supset \text{GEMSDOE28/31}_{40{,}199} \supset \text{GEMSDOE32}_{37{,}654}$$

| Project | Artifact (`content_id`) | Score Claim | Emitted $N$ | $d_{\text{cat}}=0$ | $d_{\text{cat}}\in(0,1]$ | $d_{\text{cat}}\in(1,2]$ | $d_{\text{cat}}\in(2,3]$ | $d_{\text{cat}}>3$ | Exact Relationship to `GEMSDOE25` `d2-8` (`44,090` px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `GEMSDOE20` | `h19-5` (`80d47e1ab2ee`) | `0.1922` | `121,131` | `0` | `11,012` | `8,997` | `7,941` | `93,181` | Raw connected skeleton (`62%` kernel overlap waste) |
| `GEMSDOE24` | `d1-5` (`989f59505db1`) | `0.2477` | `60,069` | `0` | `5,451` | `4,462` | `3,925` | `46,231` | Greedy $d=1.5\text{ px}$ thinning (`+0.0555` over raw) |
| `GEMSDOE25` / `30` | `d2-8` (`e56ea318af89`) | `0.2600` | `44,090` | `0` | `3,891` | `2,545` | `3,530` | `34,124` | Greedy $d=2.8\text{ px}$ thinning (`+0.0123` over `d1-5`) |
| `GEMSDOE28` / `31` | `h27-4` (`8acb75e1f2cc`) | `0.2708` | `40,199` | `0` | `0` | `2,545` | `3,530` | `34,124` | `d2-8` minus `3,891` $d_{\text{cat}}=1$ dots (`+0.0108`) |
| **`GEMSDOE32`** | **`h33-2-b2` (`4311d7454b8e`)** | **`0.2778`** | **`37,654`** | **`0`** | **`0`** | **`0`** | **`3,530`** | **`34,124`** | **`d2-8` minus all `6,436` $d_{\text{cat}}\le 2$ dots (`+0.0178`)** |
| `GEMSDOE28` | `h36-1` (`b531dae0a36f`) | `0.2710` | `37,660` | `0` | `0` | `2,353` | `3,108` | `32,199` | Iso-budget control ($d=3.0, B=1$): `6` px from `GEMSDOE32`, `-0.0068` worse |
| `GEMSDOE27` | `t-v2` (`5512495c6bd1`) | `0.2449` | `61,328` | `0` | `5,691` | `4,650` | `4,067` | `46,920` | `d1-5` + `1,259` straight-line gap dots (`-0.0028` vs `d1-5`) |
| `GEMSDOE33` | `h33d` (`cb490425926e`) | `0.2608` / `0.2632` | `41,865` | `0` | `1,377` | `2,566` | `3,551` | `34,371` | Re-admitted `1,377` $d_{\text{cat}}=1$ tip dots (`-0.0100` vs `B=1`) |
| `GEMSDOE36` | `pinn` (`3b691a9ebe74`) | `0.2750` | `38,854` | `0` | `0` | `0` | `3,646` | `35,208` | `GEMSDOE32` + `1,200` GDR/stepover dots (`-0.0028` vs `B=2`) |

### 1.3 Why `GEMSDOE32` Achieved `0.2778` (Three Interlocking Physical & Mathematical Mechanisms)
1. **Elimination of the 100–200 m Digitization-Uncertainty & Smoothing-Halo Zone ($d_{\text{cat}}\le 2\text{ px}$):**
   - `known_faults` was rasterized at 100 m from 1:24,000–1:500,000 Quaternary/structural fault polylines (`±60–250 m` positional error). Because the organizer holds out whole unmapped fault segments rather than parallel traces 100–200 m beside mapped faults, `known_faults` creates a 200 m **digitization shadow** where $P(G=1 \mid 0 < d_{\text{cat}} \le 2) \approx 0$.
   - Meanwhile, the classifier's multi-scale topographic filters (`100–2,000 m`) smear high fault probability 100–250 m perpendicular to every scarp. Masking only $d_{\text{cat}}=0$ leaves a double-sided "halo" of false positives at $d_{\text{cat}}\in\{1,\sqrt{2},2\}$.
   - Exact metric inversion shows:
     - The `3,891` $d_{\text{cat}}=1$ dots removed by `GEMSDOE28` (`0.2600 -> 0.2708`) carried only **$\approx 0.0034$ credit/dot** ($17\times$ below break-even $\tau=0.0549$), saving `778.2` denominator units.
     - The `2,545` $d_{\text{cat}}\in\{\sqrt{2},2\}$ dots removed by `GEMSDOE32` (`0.2708 -> 0.2778`) carried only **$\approx 0.0040$ credit/dot** ($14.7\times$ below break-even $\tau=0.0573$), saving `509.0` denominator units.
2. **Iso-Budget Proof (`GEMSDOE32` vs `GEMSDOE28` `h36-1`):**
   - `GEMSDOE28` `h36-1` (`37,660` px, `0.2710`) and `GEMSDOE32` (`37,654` px, `0.2778`) have virtually identical dot budgets ($\Delta N = -6\text{ px}$), yet `GEMSDOE32` scores **`+0.0068` higher**. Replacing `2,353` dead $100\text{–}200\text{ m}$ flank dots with `2,347` off-catalogue ($d_{\text{cat}}>2$) interior ridge dots adds $\Delta\text{TP}_w \approx +123\text{ px}$ at constant denominator.
3. **Why `GEMSDOE27`, `GEMSDOE33`, and `GEMSDOE36` Regressed:**
   - Every post-hoc additive heuristic that appended extra dots onto a fixed base (`GEMSDOE36`'s `+1,200` GDR/stepover dots achieved only `0.0126` credit/dot vs $\tau=0.0588$) diluted the denominator. Even `GEMSDOE78`/`81` (`+104`/`+54` bridge dots) regressed slightly (`0.2775`).
   - Conversely, to genuinely improve the detector while remaining a **unique surface** (`<= 0.90` surface rank-correlation and `<= 70%` 3-px dot overlap against all registry rasters), we must improve the **out-of-fold probability surface $P(x)$ before non-maximum suppression and Poisson-disk dotting**, then enforce the $B=2.0\text{ px}$ digitization-shadow guard.

---

## 2. Execution of the Preregistered 3-Experiment `H31-1` Protocol

All 3 experiments were executed inside the single `H31-1` method lane on fresh holdout draws `10, 11` (`8` fold×draw cells, `22,317` withheld positive fault pixels across the 4 quadrant blocks) via `scripts/run_h31_experiments.py`.

### 2.1 Single-Feature Leakage Canary (`evidence/h31_experiments/leakage_canary.json`)
Every `H31` feature was tested alone on the withheld fault pixels across all 8 holdout cells before trusting any model result:

| Feature | Pooled Holdout AUC | Cell Mean AUC | Cell Max AUC | Gate (`<= 0.90`) |
|---|---:|---:|---:|---|
| `H31_d_along` | `0.6929` | `0.6939` | `0.7330` | `PASS` |
| `H31_d_perp` | `0.7995` | `0.7996` | `0.8419` | `PASS` |
| `H31_aniso_ratio` | `0.6143` | `0.6152` | `0.6317` | `PASS` |
| `H31_strike_align` | `0.5621` | `0.5621` | `0.6184` | `PASS` |
| `H31_lidar_coh` | `0.6085` | `0.6119` | `0.6788` | `PASS` |
| `H31_aniso_x_coh` | `0.6657` | `0.6676` | `0.6968` | `PASS` |

### 2.2 Holdout-DTI Progression Across the 3 Preregistered Experiments (`evidence/h31_experiments/results.json`)
All figures below are **`HOLDOUT-DTI`** (`evaluator = HOLDOUT-DTI-v1`, `22,317` withheld fault pixels across 8 fold×draw cells on untouched draws `10, 11`, not competition scores):

| Arm | Description | Pooled `HOLDOUT-DTI` | Cell Mean `HOLDOUT-DTI` | 95% CI (Cell Mean) | $\Delta$ vs `BASE` (Mean / Folds `+`) | $\Delta$ vs `T_BASE` (Mean / Folds `+`) | Mean Hug Share |
|---|---|---:|---:|---|---:|---:|---:|
| `BASE` | `BDE + X1–X3` (`77` features, $d=2.8$, $B=0$) | `0.147111` | `0.147685` | `[0.134118, 0.161252]` | `0.000000` (`0/4`) | `-0.003121` (`0/4`) | `0.0729` |
| `T_BASE` | `BASE + H27 directed tip` (`81` features, $d=2.8$, $B=0$) | `0.150108` | `0.150806` | `[0.138141, 0.163471]` | `+0.003121` (`4/4`) | `0.000000` (`0/4`) | `0.0904` |
| **`H31_E1_ANISO`** | **Exp 1:** `BASE + 4 anisotropic continuation features` (`81` features, $B=0$) | `0.155068` | `0.155652` | `[0.141416, 0.169889]` | **`+0.007968` (`4/4`)** | **`+0.004847` (`4/4`)** | `0.0972` |
| **`H31_E2_COH`** | **Exp 2:** `E1 + 2 LiDAR-to-DEM strike-coherence features` (`83` features, $B=0$) | `0.155392` | `0.155940` | `[0.141551, 0.170330]` | **`+0.008256` (`4/4`)** | **`+0.005134` (`4/4`)** | `0.0960` |
| **`H31_E3_B2`** | **Exp 3 (Promoted):** `E2 + B=2.0 px (200 m) digitization-shadow guard` | **`0.156013`** | **`0.156523`** | **`[0.141886, 0.171160]`** | **`+0.008838` (`4/4`)** | **`+0.005717` (`4/4`)** | **`0.0740`** |

Per-fold mean `HOLDOUT-DTI` for promoted `H31_E3_B2`:
- `NW ( Fold 0 )`: `0.155817` (`+0.005929` vs `BASE`, `+0.001937` vs `T_BASE`)
- `NE ( Fold 1 )`: `0.147521` (`+0.011056` vs `BASE`, `+0.006378` vs `T_BASE`)
- `SW ( Fold 2 )`: `0.142455` (`+0.011220` vs `BASE`, `+0.008777` vs `T_BASE`)
- `SE ( Fold 3 )`: `0.180299` (`+0.007148` vs `BASE`, `+0.005777` vs `T_BASE`)

Every promotion gate passed:
- Beats `BASE` (`+0.008838`, `4/4` folds), `T_BASE` (`+0.005717`, `4/4` folds), and historical `CURRENT_HOLDOUT_BEST` (`0.156523 > 0.152003389`).
- Reduces near-catalogue hug share from `0.0960` (`E2`) and `0.0904` (`T_BASE`) down to `0.0740` (`-0.0164` vs `T_BASE`), matching `BASE` (`0.0729`) while adding `+0.008838` `HOLDOUT-DTI`.

---

## 3. Full-Footprint Submission & Registry Uniqueness Audit (`evidence/h31_experiments/uniqueness_audit.json`)

The promoted 4-fold × 2-draw (8-model) out-of-fold ensemble was evaluated across all `1,154,738` valid pixels inside the competition footprint (`Known_Faults == 0` and `B = 2.0 px` Euclidean distance guard from mapped faults, followed by 5-px NMS ridge skeletonization and $d = 2.8\text{ px}$ Poisson-disk thinning):

- **Primary file:** `docs/downloads/gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.tif`
  - **File SHA-256:** `22a9d729bec45b72a7309380a0da7d147d79fadcdf1472259ca5eecea524893d`
  - **Content ID (mask SHA-256 prefix):** `c213681203f6` (`c213681203f6982a101908db7c72f71105677f2caaa28c88fb89d0c597378459`)
  - **Emitted positive pixels:** `43,771` (`3.7905%` of valid footprint; min distance to `Known_Faults` = `2.24 px = 224 m`; `0` pixels at $d_{\text{cat}}\le 2\text{ px}$)
  - **Validator status:** `ALL 15 HARD AUTOMATED CHECKS PASSED` (`0` NaN inside footprint, values in `[0.0, 1.0]`, `EPSG:32611`, `3730 x 3292`, `100 m` pixel size)
- **Zeros-outside fallback:** `docs/downloads/gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-zeros.tif` (`sha256 = 64c792f0ebacc474a3b23109a67148d5eb00d8e4c190c6221603e64050771c62`)
- **Uniqueness audit across all 41 rasters (`data/scored/`, `data/artifacts/`, `data/focus_sites/`):**
  - Max surface rank correlation (`Spearman` inside valid footprint): **`0.1697 <= 0.90`** (`PASS`)
  - Max symmetric 3-px (`300 m`) dot overlap: **`0.5837 <= 0.70`** (`PASS`)
  - Max sparse (`<= 65k px`) one-way 3-px overlap: **`0.6707 <= 0.70`** (`PASS`)
  - 3-px overlap with `GEMSDOE32` (`0.2778` group best): **`0.3175`** (`31.75%`)
  - 3-px overlap with `GEMSDOE25` (`d2-8`, `0.2600`): **`0.3322`** (`33.22%`)

---

## 4. JSON RUN CARD (`evidence/h31_experiments/run_card.json`)

```json
{
  "hypothesis": "H31-1: Anisotropic Fault-Tip Elliptical Continuation x Multi-Scale 3DEP LiDAR-to-DEM Strike-Tensor Coherence with 200 m (B=2 px) Digitization-Shadow Suppression",
  "mechanism": "Unmapped fault segments that bridge mapped traces or extend past mapped fault tips propagate inside an anisotropic stress shadow (d_along / 8, d_perp * 3 along the fault tip's local tangent) and preserve coherent topographic strike orientation across both the 100 m 3DEP LiDAR scarp surface (lidar_slope_100m, lidar_aspect_sin_100m, lidar_aspect_cos_100m) and the 100-500 m smoothed regional DEM, while suppressing the 0-200 m (d_cat <= 2 px) catalogue digitization-uncertainty shadow where mapped-fault positional jitter and filter halos produce zero-credit false positives.",
  "mimic": "Linear Pleistocene pluvial lake shorelines (Lahontan/Bonneville highstands), incised alluvial-fan terrace risers, and columnar-jointed basaltic mesa rims — mitigated by weighting the 100 m 3DEP LiDAR-to-DEM strike coherence by the anisotropic fault-tip continuation decay (H31_aniso_x_coh) and multi-depth gravity/magnetic basement gradient features inside the 83-feature ensemble.",
  "holdout_dti": {
    "evaluator": "HOLDOUT-DTI-v1",
    "withheld_positives_total": 22317,
    "n_cells": 8,
    "folds": 4,
    "draws": [10, 11],
    "pooled_dti": 0.156013,
    "cell_mean_dti": 0.156523,
    "ci_95": [0.141886, 0.171160],
    "gain_vs_base_mean": 0.008838,
    "gain_vs_base_ci_95": [0.005551, 0.012126],
    "gain_vs_t_base_mean": 0.005717,
    "gain_vs_t_base_ci_95": [0.002206, 0.009229],
    "folds_positive_vs_base": 4,
    "folds_positive_vs_t_base": 4
  },
  "registry_correlation_overlap": {
    "n_registry_rasters_checked": 41,
    "max_surface_rank_correlation": 0.1697,
    "surface_rank_correlation_limit": 0.9,
    "max_symmetric_3px_overlap": 0.5837,
    "max_sparse_3px_overlap": 0.6707,
    "overlap_3px_vs_gemsdoe32_02778": 0.3175,
    "overlap_3px_vs_gemsdoe25_d28": 0.3322,
    "overlap_limit": 0.7,
    "passes_uniqueness_gate": true
  },
  "raster_sha256": {
    "primary_nan_tif": "22a9d729bec45b72a7309380a0da7d147d79fadcdf1472259ca5eecea524893d",
    "fallback_zeros_tif": "64c792f0ebacc474a3b23109a67148d5eb00d8e4c190c6221603e64050771c62",
    "content_id": "c213681203f6"
  },
  "validator_output": {
    "all_hard_passed": true,
    "no_nan_inside_footprint": true,
    "values_in_0_1": true,
    "crs": "EPSG:32611",
    "shape": [3730, 3292],
    "pixel_size_m": [100.0, 100.0],
    "emitted_positive_pixels": 43771,
    "emitted_fraction_of_footprint": 0.037905,
    "known_fault_overlap_pixels": 0,
    "min_distance_to_known_fault_px": 2.2361
  },
  "submission_name": "gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.tif",
  "note": "GEMSDOE25 H31-B2 | Anisotropic along-strike continuation + 3DEP LiDAR strike coh | id c213681203f6 | not yet live-scored",
  "verdict": "promote"
}
```
