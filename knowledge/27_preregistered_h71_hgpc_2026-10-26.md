# 27 · Pre-Registered Hypotheses & Experimental Design (`H71-1` Signed Half-Graben Polarity Concordance as DIRECT emission, 2026-10-26)

**Branch / session namespace:** `arena/71b61fac-gemsdoe25` (`H71` prefix is the session-lane id; it is not GEMSDOE71).  
**Status at this commit:** Pre-registered **before any holdout model fit, single-feature holdout AUC computation, or candidate GeoTIFF emission**.  
**Core values:** **Maximize P(Win)** · **Own the Outcome**.  
**Parallel-Run Protocol:** 3 experiments / 2 hours; reuse `gems25.holdout`, `gems25.experiment.Cell.evaluate`, `gems25.thinning.score_ordered_dots`, `gems25.submission`; label every number HOLDOUT-DTI or OWNER-REPORTED (never ORGANIZER-CONFIRMED unless a receipt exists — none do); leakage canary AUC > 0.90 is a stop; rank-correlation > 0.90 or >70% of dots within 3 px of one registry raster is a duplicate-lane stop.

---

## 0. Why `GEMSDOE32` `h33-h33-2-b2` scored `0.2778` (OWNER-REPORTED) and why a clone is forbidden

Pixel-exact forensics already in this repo (`evidence/focus_sites_forensics.json`, `knowledge/26_h66_outcomes_2026-10-25.md`, `knowledge/26_h38_outcomes_and_0.2778_phd_synthesis_2026-10-25.md`) show the 9-site high-score chain is **geometry on one ancestor**, not a new detector:

| Step | File (OWNER-REPORTED score) | Exact pixel algebra (`COMPUTED`) |
|---|---|---|
| 0 | `19GEMSDOE` H19-5 (`0.1922`) | multi-line Hessian ridge, 121,131 px |
| 1 | `GEMSDOE24` D1.5 (`0.2477`) | `dot_thin(H19-5, 1.5)` |
| 2 | `GEMSDOE25`/`30` D2.8 (`0.2600`) | `dot_thin(H19-5, 2.4)` = 44,090 px |
| 3 | `GEMSDOE28`/`31` R1 (`0.2708`) | `D2.8 & (d(cat) > 1 px)` — deletes 3,891 collar dots at ~0.001 credit/px ≪ τ |
| **4** | **`GEMSDOE32` B2 (`0.2778`)** | **`R1 & (d(cat) > 2 px)` = 37,654 px** — deletes 2,545 further collar dots at ~0.005 credit/px ≪ τ ≈ 0.057 |
| 5 | `GEMSDOE36` PINN (`0.2750`) | `B2 ∪ 1,200` extra dots (credit/px < τ; **dilution**) |

**Implication (INFERENCE, labelled):** `0.2778` is the geometric optimum of post-processing H19-5, not the physical ceiling of Great Basin fault discovery. Beating it requires **new true-fault pixels H19-5 does not cover**, with credit per added dot > τ ≈ 0.056. Cloning B2 is a duplicate-lane stop (Protocol item 1) and is forbidden. Adding low-credit dots to B2 has already failed (`GEMSDOE36` −0.0028). Independent detectors in the cohort peak near `0.2478` (`GEMSDOE70`, 4.8% overlap with B2).

This session therefore tests a **catalogue-free DIRECT emission field** (not another HGB column on the H35/H19-5 lineage). That is the only way to (a) stay off the HGB-lineage 75–96% 3-px overlap wall (`IR-25-XG1-LANE-LINEAGE`) and (b) have any chance of covering buried basin-bounding faults that H19-5's topographic/openness ridges miss.

No ORGANIZER-CONFIRMED score exists in this repository. Conflicting prompt claims `0.3195` / `0.4413` remain OWNER-REPORTED / PUBLIC-LEADERBOARD-OBSERVATION (`IR-25-G87-STALE-PROMPT-CLAIM`).

---

## 1. Audit of already-tested ideas (do not repeat)

Already tested in `src/gems25/` and `knowledge/03..26` (excluded):

* Families A–E Resolution V factorial; H26 extras; H27 tip×scarp; H28 emission spacing; H30 relay; GEM-1/FUSE1 blind magnetics; H31 flank-shield and anisotropic scarp; KDC B2-complement; H34/H35 RESMAG×tip; CF-1 transverse mag/grav; XG1 unsigned cross-gradient; H36-TZC tilt-zero; H36-SPIGM unit-corrected analytic signal + submodular; H37 DOC / SPR / SEISALIGN; GMCE / MSCR; H38 greedy-credit; H38-OSPC monoclinal LiDAR polarity × submodular; H66-1 MGD-F geothermometry (screen pass, confirm fail); H66-2 SGMC-REACT as **HGB features** (screen +0.0138, tree-inversion `IR-25-SGMC-TREE-INVERSION`, unconfirmed).

**H66-4 (signed 3-field half-graben polarity) was listed and never implemented.** H38-OSPC's `H38_monoclinal_polarity` is **LiDAR downface≫upface scarp asymmetry**, not gravity–basement sign concordance, and was consumed as an HGB column on H35, not as the emission field.

**Unused pinned layers still available (no new external download required):** `12_det_elev.npy`, `13_iso_grav_anom.npy`, `15_depth_to_base_surf.npy` (competition raster, GDR 1391 / GeoDAWN compilation); `08_geod_dilaterate.npy`; `external/gdr_volcanic_vents_in_footprint.csv` (21 vents). `gdr_qfaults_traces.csv` remains quarantined. Paleogeothermal / USGS heat-flow binaries are still not in the sandbox allowlist (`H66-5` / `H27-3/4` remain blocked).

---

## 2. Ranked register of 5 untried geological hypotheses (`H71-1` … `H71-5`)

| Rank | ID | Layers & physical signature | Why it can catch a fault **missing** from USGS/INGENIOUS `labels.tif` | Named non-fault mimic | Difference from everything in this repo | Planning ΔDTI (proxy) | Cost |
|---:|---|---|---|---|---|---|---|
| **1** | **`H71-1` `HGPC-BLIND`** | **Signed gravity–basement half-graben polarity as the DIRECT emission field.** Bands `13_iso_grav_anom`, `15_depth_to_base_surf`. Local normal **n** = unit gravity gradient. Concordance: `sgn(∂n g) == −sgn(∂n D_base)`. Score = indicator × geometric mean of percentile-scaled `\|∂n g\|` and `\|∂n D\|`, then Hessian ridge NMS → visible-catalogue **B=2** mask → `score_ordered_dots` `min_dist=3.0`, `kfrac=0.035`. **Zero HGB. Zero Family E. Zero DEM.** | Blind / buried basin-bounding normal faults offset dense basement and fill the hanging wall with low-density alluvium, producing a concordant gravity low and MT basement step **even where Quaternary scarps are buried or never formed** (Faulds & Hinz 2015: ~39% of GB geothermal systems are blind). QFFDB requires a mapped <1.6 Ma scarp. | Unfaulted depositional onlap wedge (basinward thickening without a discrete fault); caldera / lithologic density contacts; MT inversion artefacts. | H38 polarity is LiDAR face asymmetry on H35; H36-SPIGM / Family A are **unsigned** analytic-signal / gradient magnitudes; XG1 / CF-1 are unsigned cross-field products; H37-DOC is lagged conductivity. **No module emits from signed g↔D polarity.** | `+0.001` to `+0.008` vs unsupervised crest; **not** expected to beat H35 (Family E +0.061) on the catalogue-gap proxy | ~8 min, 2 CPUs, no new data |
| **2** | **`H71-2` `HGPC-SURF`** | Same operator plus `12_det_elev`: three-field concordance `sgn(∂n z)==sgn(∂n g)==−sgn(∂n D)` with **n** from the elevation gradient (range-front). Diagnostic arm in Experiment 1. | Mapped range-front faults missing from QFFDB because scarps are eroded or the trace is mis-digitised by >200 m. | Pediment / fan onlap; lithologic hogbacks. | 3-field signed product is untried; DEM scarps themselves are Family B (already tested). | `0` to `+0.004` vs crest | same run as Exp 1 |
| **3** | **`H71-3` `AKF`** | **Aligned knickpoint / χ drainage-offset detector** from `12_det_elev` only: priority-flood fill, D8 accumulation, channels (`A≥2 km²`), χ (`m=0.45`), along-channel slope breaks clustered into across-stream lines. | A buried or highly eroded fault still warps channel long-profiles (Kirby & Whipple; Seeber & Gornitz). QFFDB does not map knickpoint alignments. | Lithologic contacts (welded tuff over basin fill) also knick channels. | **No hydrology / χ / knickpoint code exists in this repo.** Geometry follows valleys, not ridges → expected low overlap with H19-5. | `0` to `+0.005` vs crest | ~15 min if Exp 1 fails |
| **4** | **`H71-4` `MAG-ANISO`** | Structure-tensor lineaments of **shallow residual RTP** (`rtp − upward_continue(rtp, 400 m)`), persistence across σ=1 and σ=2. | Magnetic basement fabric / dike-fault corridors under cover; QFFDB is a scarp catalogue. | Unfaulted volcanic-flow edges; survey heading noise. | H34 uses residual-mag **ridge strength** (unsigned Hessian) as HGB columns, not structure-tensor directors as the emission field. | `0` to `+0.003` | ~6 min |
| **5** | **`H71-5` `HARD-SGMC`** | Direct skeleton of USGS SGMC bedrock faults **hard-zeroed** unless `L_coh100>0` AND `cos 2Δθ>0` AND strain in the top decile (binary, 85% of footprint zero). | Reactivated pre-Quaternary faults lacking QFFDB scarps. | Inactive Sevier thrusts; **compilation overlap with QFFDB** (`IR-25-SGMC-PROXY-CONTAMINATION`, 35% 3-px). | H66-2 used SGMC as **smooth HGB multipliers** (tree inversion). Hard-zero direct emission is untried. **Held last because the holdout win may be QFFDB recovery, not new-fault discovery.** | `+0.005` to `+0.015` proxy (transfer suspect) | ~6 min; not slot-eligible without owner review |

**Official free sources (already pinned / restored, no new host required):**

* INGENIOUS / GDR 1391 numerical features (isostatic gravity, MT depth-to-base, 100 m DEM): <https://gdr.openei.org/submissions/1391> (`DOI 10.15121/1881483`, CC BY 4.0).
* USGS GeoDAWN magnetics: <https://doi.org/10.5066/P93LGLVQ> (Glen & Earney 2024, CC0).
* USGS 3DEP (LiDAR, only used in H71-5): <https://www.usgs.gov/3d-elevation-program>.
* USGS SGMC (H71-5 only): <https://doi.org/10.5066/F7WH2N65> (Horton et al. 2017, CC0).
* Competition metric / grid: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>, EPSG:32611 <https://epsg.io/32611>, Tversky index <https://en.wikipedia.org/wiki/Tversky_index>, reference solution <https://github.com/drivendataorg/gems-prize-reference-solution>.
* Blind-system context: Faulds & Hinz 2015, *Proceedings World Geothermal Congress* (play types in the Great Basin). Gravity of grabens: Vening Meinesz isostatic residual over low-density basin fill (standard potential-field interpretation; the competition band is the INGENIOUS isostatic gravity anomaly).

H71-3/4/5 need **no new external data**. H66-5 paleogeothermal / USGS heat-flow remain blocked on the sandbox allowlist and are **not** proposed as viable this session.

---

## 3. Frozen Experiment 1 — `H71-1` HGPC DIRECT screen (draws `70, 71`)

This is Experiment **1 of 3**. Design is committed before any `Cell.fit_predict`, any sidecar AUC, and any GeoTIFF write.

### 3.1 Static catalogue-free columns (`work_dir()/h71_hgpc_columns.npy`)

Computed once from `work/bands/{12_det_elev,13_iso_grav_anom,15_depth_to_base_surf}.npy`. **`labels.tif` is never read.** σ = 2.0 px Gaussian. Footprint (p1, p99) scaling to `[0, 1]`.

1. `H71_blind_hgpc` — n = unit ∇g; score = `1[sgn(∂n g)==−sgn(∂n D)] · √(|∂n g|_01 · |∂n D|_01)`.
2. `H71_surf_hgpc` — n = unit ∇z; score = `1[sgn(∂n z)==sgn(∂n g)==−sgn(∂n D)] · (|∂n z|_01 · |∂n g|_01 · |∂n D|_01)^{1/3}`.
3. `H71_crest_ctrl` — percentile-scaled `B_crest` copied from the static cache (same emission machinery; **not** a new hypothesis).

### 3.2 Holdout harness (shared tools only)

* `gems25.holdout.Holdout(foot, labels, hide_frac=0.20)`, `COLLAR_PX=15`, folds NW/NE/SW/SE.
* Draws **`70, 71`** (untouched; H66 used 50–55, H38 used 24–27, H36 used 20–23, H31 used 10–13).
* Score: `gems25.experiment.Cell.evaluate` → `gems25.metric.dti_binary` (α=0.2, β=0.8, R=3.0 px = 300 m).
* Catalogue-geometry features, when used, come **only** from `draw.visible`. Visible faults are masked pixel-exactly in scoring.
* Emission (all HGPC / crest arms): ridge NMS (`Cell.candidates`) → drop pixels with `EDT(~visible) ≤ b` → `score_ordered_dots(..., min_dist=3.0)`, `k = round(0.035 · |domain|)`.

### 3.3 Arms (every fold × draw)

| Arm | Field | Collar b | Role |
|---|---|---|---|
| `CTRL_CREST_B2` | `H71_crest_ctrl` | 2.0 px | physics-matched unsupervised control |
| `HGPC_BLIND_B2` | `H71_blind_hgpc` | 2.0 px | **PRIMARY CANDIDATE** |
| `HGPC_SURF_B2` | `H71_surf_hgpc` | 2.0 px | diagnostic (H71-2) |
| `CTRL_H35_24` | H35 HGB (`BDE+7+H27_tip+H34`, sapd 2.4, no extra HGPC columns) | 0 (exact visible only, as in the H35 recipe) | current holdout champion, same-run |

`CTRL_H35_24` is the **slot-relevant** comparator. `CTRL_CREST_B2` is the **physics** comparator (same emission, different field). HGPC is **not** added as HGB columns (that would recreate the lineage overlap wall).

### 3.4 Leakage canary (Protocol item 4)

Before trusting any DTI, every one of `H71_blind_hgpc`, `H71_surf_hgpc` is scored **alone** on the holdout pos/neg index of each cell. `max(AUC, 1−AUC) > 0.90` **aborts the experiment** (presumptive leakage). `H71_crest_ctrl` is a known Family-B feature; its canary is recorded but is not a stop (it is the control).

### 3.5 Frozen screen gate (`HGPC_BLIND_B2` vs pointwise `BEST_CTRL` = per-fold max of `CTRL_CREST_B2`, `CTRL_H35_24`)

Pass iff **all** of:

1. Leakage canary passed.
2. 4-fold mean paired gain `mean(HGPC_BLIND_B2 − BEST_CTRL) > +0.0010` DTI.
3. `≥ 3/4` spatial folds strictly positive.
4. `min(fold gain) ≥ −0.010`.
5. Mean hug-share delta `≤ +0.10`.

### 3.6 Confirmation / stopping (Experiments 2 and 3)

* **If screen PASSES:** Experiment 2 = frozen confirmation on untouched draws **`72, 73`**, identical arms and gate. Only a two-stage pass can even be *considered* for the separate owner selector (this agent still will not set `slot_approved=true`; Protocol item 6).
* **If screen FAILS:** do **not** run draws 72, 73. Experiment 2 = `H71-3` AKF knickpoint DIRECT emission vs `CTRL_CREST_B2` on draws **`74, 75`**, same gate vs crest (H35 optional if budget remains). Experiment 3 only if Experiment 2 screen passes (AKF confirmation on `76, 77`) **or**, if Experiment 2 fails and budget remains, `H71-4` MAG-ANISO screen on `78, 79`.
* **H71-5 HARD-SGMC is not run in this 3-experiment budget** unless 1–4 are all blocked on engineering failure (not a negative result). Compilation-overlap risk is disclosed in §2.

---

## 4. Frozen unique GeoTIFF & verdict rule

1. **Which specification is built** (mandatory unique research GeoTIFF even if all gates fail — negative results are deliverables):
   * If `HGPC_BLIND_B2` passes two-stage confirmation: emit from the full-footprint `H71_blind_hgpc` field (ridge NMS, B=2 against **full** `labels.tif`, sapd 3.0, kfrac 0.035).
   * Else: still emit from **`HGPC_BLIND_B2`** (the pre-registered primary physics, catalogue-free). Do **not** emit an H35/H19-5 clone.
2. Writer: `gems25.submission.write_submission` both `-zeros.tif` (primary, `outside="zero"`) and `-nan.tif` (twin) + `.zip`. Independent audit: `check_file` and `scripts/verify_candidate_independent.py`.
3. Lane: `scripts/check_lane_duplicates.py`, `scripts/check_lane_surface.py`, `scripts/lane_check_extended.py`. Duplicate if `|Spearman|>0.90` or `>70%` of candidate dots within 3 px of one registry raster. The dense r13 5-px lattice covering ~100% of the footprint (`IR-25-LANE-DENSITY`) is reported and, under standing policy, blocks `slot_approved`.
4. **Verdict:** `ok_to_download = true` iff format-valid and unique-by-content. `ok_to_submit_slot = false` unless (two-stage holdout pass) **and** (strict lane pass vs scored/sibling rasters) **and** (owner selector — out of scope). This session's default is **DO NOT SUBMIT**. Research note ≤120 characters, must contain `no slot`, `unscored`, `not slot-approved`.
5. Filename slug: `h71-hgpc-blind-b2-sapd3-k3p5`. Date `20261026`. Content id = `gems25.submission.content_id`.

---

## 5. What this session will not claim

* No live DTI, no projection of HOLDOUT-DTI onto `0.2778` / `0.3195` / `0.4413`.
* No DrivenData access (Terms of Use; `AGENTS.md` §3).
* Beating `0.2778` with a unique non-H19-5 detector is **possible in principle** (new true-fault pixels with credit > τ) and **not demonstrated** until an organizer receipt exists. Independent cohort ceiling so far is OWNER-REPORTED `0.2478`.
