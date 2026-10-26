# 29 · Ranked untried hypotheses + frozen pre-registration (session 2026-10-26, branch `arena/f1967d4f-gemsdoe25`)

Written **before any model fit in this session**. Data state at writing: 22 manifest inputs restored
and SHA-256-verified; `data/work` caches rebuilt and **bit-identical** to `evidence/work_cache_hashes.json`
(6/6 hashes match: static `fe584a12…`, addons `ad31ff14…`, footprint `c4460947…`, labels `d77fa88a…`);
21 top-scorer registry rasters restored to `data/registry_top`. No DrivenData page was accessed
(AGENTS.md rule 3). All sibling scores are **OWNER-REPORTED**; no ORGANIZER-CONFIRMED receipt exists in this repo.

## 0. Lane (Parallel-Run Protocol item 1 — declared, because the brief supplies no method paragraph)

> **Lane = training-objective / sampling-design on the frozen validated stack.** Detector columns are
> exactly the H35 arm-B stack (`BDE` families + 7 add-on extras + `H27_tip` + 3 H34 columns), the model
> class is scikit-learn `HistGradientBoosting*`, and emission is exactly H38's validated rule
> (ridge-NMS → top-3.5 % pool → lazy-greedy marginal-credit selection, `gems25.greedy`).
> The **only** scientific variables are (Exp 1) the training target/sampling geometry around the
> pseudo-hidden trace and (Exp 2, if run) hard-negative mining. No new geological feature column,
> no new external data, no emission-rule change.

Lane discipline: surface Spearman and final-dot 3-px overlap will be computed against all 21 restored
top-scorer rasters (incl. GEMSDOE32 B2) and this repo's own downloads. Caps |ρ| ≤ 0.90, overlap ≤ 0.70.
The r13 dense lattice and same-lineage unscored predecessors are reported literally as well; under the
merged strict-literal policy they flag every dotted file (`IR-25-LANE-DENSITY`, `IR-25-LATTICE-CAP-20261026`:
only 6,514 eligible pixels lie >3 px from lattice dots, so any >21,713-dot file must flag). Both readings
will be printed on the run card; neither will be hidden.

## 1. Why this lane: what 20+ sessions have established (evidence, not opinion)

* Seven+ new **feature-column** blocks (GMCE, MSCR, XG1, CF1, H36-TZC/SPIGM, H37-DOC/SEIS/SPR, H66, H71
  direct detectors, POL3, ROD, APFL…) each moved paired HOLDOUT-DTI by roughly **−0.10 … +0.002** vs the
  same-run H35 comparator; the only two gate passes in repo history are **H35** (tip×resmag interaction,
  +0.0042 combined) and **H38 greedy emission** (+0.0050 pooled, screen+confirm). Feature-column mining on
  the same 19 bands is, on this evidence, exhausted at the ±0.004 level.
* The live (OWNER-REPORTED) record is dominated by emission economics on one unsupervised surface
  (H19-5 → D1.5 → D2.8 → R1 → **B2 0.2778**), while supervised per-pixel submissions from sibling sites
  mostly score 0.02–0.25. The catalogue-gap holdout rewards Family-E proximity by construction and
  correlates only weakly with live scores (Spearman +0.33, n.s., n=24 — repo record). A holdout win is
  therefore treated as **necessary, not sufficient**, exactly as AGENTS.md requires.
* One part of the pipeline has **never been varied in this repo** (verified by grep 2026-10-26: no
  `HistGradientBoostingRegressor`, no soft/dilated label, no `sample_weight`, no hard-negative code in
  `src/` or `scripts/`): the **training target geometry**. Every fit labels exact 1-px pseudo-hidden
  trace pixels positive, excludes negatives only within 1.5 px of them, and therefore trains the model
  to call pixels 1.5–3 px from a fault trace — the scarp-crest zone where the physical signal actually
  peaks and where the official metric still pays k(d)=1−d/3 credit — *negative*.

## 2. Five candidate hypotheses, ranked by expected value (planning judgement, not scores)

| Rank | ID | Layers / inputs | Physical signature targeted | Why it should catch catalogue-missing faults | Difference from everything in this repo | Named non-fault mimic / failure mode | Expected HOLDOUT-DTI effect (planning bracket) | Cost | Validatable now? |
|---:|---|---|---|---|---|---|---:|---|---|
| **1** | **TENT — kernel (tent) regression target** | No new layer. Frozen BDE+7+tip+H34 stack; labels only | Training target = max triangular-kernel credit to the pseudo-hidden trace, `k(d)=max(1−d/3px,0)` — the exact function the official metric pays (`gems25.metric`) | USGS/INGENIOUS traces are cartographic polylines displaced from the physical scarp (repo record: 100–400 m offsets vs 1 m LiDAR crests, knowledge/13). Binary training teaches suppression of crest pixels 1.5–3 px off-trace; tent training lets the model fire on the *scarp itself*, which is the only observable an uncatalogued fault offers | Every model in repo history is a binary classifier on exact trace pixels. No regressor / soft target has ever been run | Failure mode: tent blurs localisation — dots land 1–2 px off the hidden polyline and earn 0.33–0.67 instead of 1.0; squared-error regression may underweight the rare trace class | **+0.002 … +0.010** | Low (reuse `Cell`; one custom training sampler) | **Yes — Exp 1 below** |
| **2** | **HARDNEG — hard-negative mining** | No new layer. Same stack | Two-stage fit: stage-2 negatives are 50 % uniform + 50 % the highest-scoring train-region pixels >3 px from any (pseudo-)fault — i.e. the model's own worst false lineaments | The top-3.5 % emission head is decided against fault-*like* non-faults (roads, shorelines, contacts, survey seams), which uniform sampling (300 k of ~3.9 M, mostly easy basin floor) almost never shows the model | Negative sampling has never been varied; `Cell` hard-codes one uniform draw | Mimics are the training signal itself: roads/graded tracks, pluvial shoreline benches, lithologic contacts; risk: second stage suppresses genuine fault-like scarps that resemble them | +0.001 … +0.008 | Low–medium (one extra predict+fit per cell) | **Yes — Exp 2 below (frozen, run only if budget remains)** |
| **3** | **LINE — along-strike line-support features** | Ridge grids `B_crest`, `L_step_max`, `A_mag_hg_ridge`, `A_grav_hg_ridge` | For each pixel: max over 8 orientations of mean ridge strength along a ±7 px (1.5 km) line through the pixel, plus along/across ratio | Unmapped faults are long, straight lineaments; many false ridges are short/curved erosional fragments. Per-pixel features cannot express "part of a 1.5 km straight line" | `line_max_mean` exists only as a post-hoc filter on the HGB *output* (H38 arm A3, secondary); never as input features on raw physical channels. MSCR was scale persistence, not directional support | Roads/railways/canals are longer and straighter than faults — may promote exactly the wrong lines | 0 … +0.006 | Medium (new static sidecar convolutions) | Yes, but not run this session unless Exp 1+2 both finish inside budget (they are cheaper and more mechanistic) |
| **4** | **CNN — compact 2-D patch network, soft-DTI loss** | 19 supplied bands (+LiDAR descriptors) as image channels | Learned multi-scale spatial filters: paired edges, step-overs, branching; trained against a differentiable 300 m tent-max Tversky loss | Fault-network topology is invisible to per-pixel trees; the official reference solution (U-Net, Prof. John Lipor, github.com/drivendataorg/gems-prize-reference-solution — read via GitHub, no licence file found, treated as precedent only) shows the task is usually framed as segmentation | No neural network exists in this repo | Lithologic contacts / flow margins form coherent multi-band edges; patch-boundary leakage if blocking is sloppy | Highest ceiling, lowest single-run success probability on 2 CPUs / 3 GB RAM | **High** (PyTorch CPU install, patch pipeline, leakage-safe blocking, hours of CPU training) | Feasible in principle, **not** attempted this session: expected value per hour is below TENT/HARDNEG, and a half-trained CNN would be an unverifiable deliverable |
| **5** | **SHORE — pluvial shoreline offset** | **Absolute-elevation DEM (not pinned)** | Lake Lahontan shoreline benches are horizontal datums; a young fault offsets bench elevation along strike even where no scarp survives in the detrended DEM | Basin-floor faults under playa/fan cover are the catalogue's known blind spot | Never implementable from pinned bytes: `det_elev` is detrended, so absolute bench elevation is unrecoverable | Wave-cut benches on lithologic contacts mimic offset datums | Unknown | High | **NO — blocked.** Free official source: USGS 3DEP, https://www.usgs.gov/3d-elevation-program (National Map staging hosts are outside this sandbox's egress allowlist github.com/pypi.org/registry.npmjs.org; raw tiles are not in any owner mirror in `registry/data_manifest.json`). Not proposed as viable until tiles are actually obtained and coverage-verified |

Ranking rule: expected paired HOLDOUT-DTI gain × probability the mechanism is real ÷ implementation
cost, with validatability as a hard filter. TENT ranks first because it repairs a *demonstrated*
contradiction between the training labels and both (a) the official metric's credit function and
(b) the documented cartographic offset between trace and scarp — at near-zero cost and with zero
new-data risk.

## 3. Frozen design — Experiment 1 (TENT)

* **Evaluator:** HOLDOUT-DTI via `gems25.experiment.Cell.evaluate` → `gems25.metric.dti_binary`
  (α=0.2, β=0.8, R=3 px triangular kernel), hide-and-recover `gems25.holdout` (4 quadrants,
  hide_frac 0.20, 15-px collar, catalogue features from visible faults only, visible pixels masked).
  Secondary response: off-catalogue HOLDOUT-DTI (truth restricted to hidden pixels >2 px from visible
  catalogue), as in H38.
* **Cells:** folds NW/NE/SW/SE × draws **90, 91** (screen). Draws 90+ are unused in any prior design in
  `evidence/*/design.json` / knowledge docs (prior maximum 78/79). **Confirmation draws 92, 93 run only
  if the screen passes the gate.** No other draws will be looked at for this hypothesis.
* **Features (all arms):** `Cell(extras=True, h27=True)`; columns = `BASE="BDE"` + `EXTRAS` (7) +
  `H27_tip` + 3 H34 sidecar columns — identical to H38's B35 surface. **No new column.**
* **Arms (one fit each per cell; emission identical for all):**
  * `BIN` (control, comparator recomputed same-run): `HistGradientBoostingClassifier(**HGB_PARAMS)`
    on `Cell`'s default training set (positives = `hidden_train`; 300 k uniform negatives from
    train region excluding all catalogue pixels and d≤1.5 px to `hidden_train`). This reproduces
    `run_xg1_factorial.fit_arm` B35 exactly (seed = draw).
  * `TENT` (primary): `HistGradientBoostingRegressor` with `HGB_PARAMS` minus `class_weight`
    (max_iter 100, lr 0.12, max_leaf_nodes 31, min_samples_leaf 50, l2 1.0, no early stopping),
    seed = draw. Training pixels drawn **only from `draw.train_region`**:
    trace pixels (`hidden_train`, target 1.0) + ring pixels (`0 < EDT(hidden_train) ≤ 3`, not on any
    catalogue pixel, target `1 − d/3`) + far negatives (uniform sample, size `min(300_000, pool)`,
    RNG seed `777 + 31*fold + draw` — the same seed formula `Cell` uses — from train region pixels
    that are not catalogue pixels and have `EDT(hidden_train) > 3`, target 0.0). No sample weights.
    Prediction clipped at ≥0 for ranking/emission.
  * `IGN3` (diagnostic, never promotable alone): classifier identical to `BIN` except negatives are
    sampled with the `EDT(hidden_train) > 3` exclusion (same seed formula, same 300 k cap). Isolates
    "stop contradicting the crest zone" (IGN3) from "also price it with the kernel" (TENT).
* **Emission (all arms, primary response):** H38 rule — `Cell.candidates` top pool (ridge-NMS σ=1.0,
  visible-catalogue pixels removed, k = 3.5 % of eroded domain) → `gems25.greedy.greedy_dots`
  with `n_hat = 0.25 × |visible catalogue pixels in domain|`. Secondary diagnostic response:
  `score_ordered_dots(min_dist=2.4)` on the same pool (arm suffix `-S`), recorded but not gated.
* **Primary contrast:** `TENT` vs `BIN` (greedy emission). **Gate (each stage separately):**
  fold-mean paired gain > +0.001, ≥3/4 folds positive, worst fold ≥ −0.010, mean hug-share
  increase ≤ +0.10. Report pooled DTI (sum TP/FP/N over cells through the metric identity),
  withheld-positive counts per fold, and quadrant-bootstrap 95 % CI following the repo's ROD
  convention. A failed arm stays failed; no retuning of target radius, weights, or sampler on outcomes.
* **Leakage canaries:** (i) single-feature AUC for `H27_tip` + 3 H34 columns per cell (the newest
  columns in the stack; the remaining columns are unchanged and were canaried ≤0.80 in prior runs on
  other draws) — effective AUC `max(a,1−a) > 0.90` stops the experiment as leakage; (ii) code-level
  assertion + unit test that every TENT/IGN3 training index lies in `train_region` and that targets
  derive only from `hidden_train` (never `hidden_test`); (iii) AUC of each fitted surface reported
  as a diagnostic (not a gate).
* **Engineering-failure rule:** a crash before any cell completes may be fixed and restarted once,
  with the failure logged; a crash after outcomes exist is not a licence to redesign.

## 4. Frozen design — Experiment 2 (HARDNEG), run only if budget (≤3 experiments) and time remain

* Draws **94, 95** (screen), confirmation **96, 97** only on a screen pass. Same cells/features/evaluator.
* `BIN` control as above. `HNEG`: stage-1 = `BIN` fit; predict stage-1 scores on **all** train-region
  candidate-negative pixels (not catalogue, `EDT(hidden_train) > 3`); stage-2 training negatives =
  150 k uniform from that pool + the 150 k highest-scoring pool pixels (deterministic tie-break by
  raster index; if pool < 300 k take all, split cannot exceed pool); positives identical to `BIN`;
  stage-2 classifier `HGB_PARAMS`, seed = draw. Emission and gate identical to Exp 1 (primary
  contrast `HNEG` vs `BIN`, greedy emission).
* Exp 2 is frozen against the `BIN` base **regardless of Exp 1's outcome** (no sequential stacking
  of a possibly-failed idea). Combining TENT+HARDNEG would require a new pre-registration.

## 5. Final-candidate build rule (after experiments)

Exactly one new full-footprint candidate will be built, from the best **gate-passing** arm if one
exists; otherwise from `BIN` (i.e. a fresh H38-protocol surface — new seeds/draws make it a new file,
but it will be labelled with the negative verdict it earns, see §6). Build protocol is
`scripts/build_h38_candidate.py` verbatim except the training scheme of the chosen arm:
3 pseudo-hidden draws (20 % of components hidden over the full footprint, seeds 424200+m),
per-draw E/tip from visible catalogue only, prediction on full-catalogue features, surface averaged,
ridge-NMS top-3.5 % pool, greedy emission `n_hat = 0.25 × |catalogue|`, catalogue pixels never emitted,
zeros-outside primary TIF (+NaN twin + single-TIF zip) via `gems25.submission`, content-addressed name,
≤140-char note stating the verdict. **No B=2 collar prune is added**: H38's A2 diagnostic measured it
near-neutral on this detector family, and the holdout cannot price it honestly (knowledge/23, /26).

## 6. Verdict labelling (owner's "obvious whether OK to submit" requirement)

The site banner, run card and submission note will state three separate, machine-checked facts —
never merged into one green light:

1. **Format:** `check_file` hard checks (single band float32, EPSG:32611, 3730×3292, exact template
   transform, all footprint values finite in [0,1], zeros variant passes the strict whole-array
   `[0,1]` test behind the portal error *"Predicted values must be in range [0, 1]"*).
2. **Uniqueness:** SHA-256 ≠ every registry/download raster; 3-px dot overlap and |Spearman| vs the
   21 top-scorers and own downloads printed with the 0.70 / 0.90 caps; literal lattice/lineage flags
   printed separately.
3. **Science gate:** PASS only if the chosen arm passed screen **and** confirmation vs the same-run
   `BIN` comparator. `OK to spend a weekly slot` is **the owner's separate selector decision**; this
   session's maximum claim is "eligible for the selector" (verdict `promote`) or "DO NOT SUBMIT".

## 7. Budget

Experiments this session ≤ 3 (Exp 1 screen+confirm = 1, Exp 2 screen+confirm = 1, one spare kept
unspent unless a gate-passing arm needs a build-stage check). Weekly slots used by the agent: **0**
(the agent never uploads; AGENTS.md rule 3).
