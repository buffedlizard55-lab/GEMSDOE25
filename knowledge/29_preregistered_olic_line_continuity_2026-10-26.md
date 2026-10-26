# Pre-registration: OLIC multi-scale oriented line-continuity screen (2026-10-26)

**Status:** Frozen before implementation, any OLIC feature computation, canary, fit, or raster emission.
**Provisional lane (protocol item 1):** the normalized standing brief supplies no separate method
paragraph, so this session's lane is explicitly **2-D spatial-context / oriented line continuity
added to the H35 tabular base**. This is the rank-2 candidate in
`knowledge/27_ranked_hypotheses_and_review_2026-10-26.md` ("2-D spatial-context detector"),
implemented in its low-cost convolutional form (oriented line integrals feeding the shared HGB)
rather than a patch CNN (no GPU in this sandbox; CNN remains untested, not claimed).

## Ranked candidate hypotheses (before implementation)

| Rank | Hypothesis | Layers | Physical signature | Why a catalogue-missing fault | Difference from repo work | Non-fault mimic | Cost |
|---|---|---|---|---|---|---|---|
| 1 | **OLIC** oriented line continuity | `L_step_max`, `A_mag_hg_ridge`, `D_ThK_edge` (cached static stack) | Edge energy that stays coherent along one strike direction for 1.1–2.1 km (line means over ±5/±10 px, 4 directions; max-direction mean and anisotropy) | Young/buried normal faults produce weak per-pixel scarps but *long, straight* multi-physics edges; per-pixel HGB cannot see continuity, so such faults are exactly the ones a pixel model + catalogue misses | All prior arms are per-pixel columns, tip/catalogue geometry, sign tests (POL3), offset registration (ROD), or DIRECT unsupervised fields (H71). No oriented line-integral of edge fields exists in `src/gems25/` | Roads, canal/levee lines, volcanic flow margins, lithologic contacts (also long/straight) | Low |
| 2 | Patch CNN/U-Net on 19 bands | all supplied bands | Learned multi-scale patch geometry | Tips/stepovers visible only in neighbourhood context | Reference solution precedent; repo has no CNN | Correlated contacts/flow margins | High (no GPU) — not this session |
| 3 | Vent-pair dike corridor | GDR 1391 vents, `rtp`, `geod_dilaterate` | Inter-vent bearing alignment with magnetic lineaments | Dike-fed fissures buried by young lava, no Quaternary trace | GEM-2 used isotropic vent proximity only | Unrelated fissure/flow margins | Low–medium; sparse vents cap gain |
| 4 | Drainage-offset/knickpoint | raw 3DEP 1 m DEMs | Channel deflection at scarps | Buried scarps deflect fans | H71-3 AKF used supplied summaries and FAILED; raw-network version differs | Lithologic knickpoints, roads, avulsion | High; tile coverage unverified → not viable now |
| 5 | Radiometric offset registration (ROD) / signed polarity (POL3) | K/Th/U; elev/grav/basement | — | — | **Already run and negative (ROD 0.0690; POL3 −0.000858 gain). Retuning either is prohibited.** | — | — |

## Frozen OLIC feature definition (catalogue-free)

For each channel `E` in {`L_step_max`, `A_mag_hg_ridge`, `D_ThK_edge`}: scale to [0,1] by the
full-footprint 1st/99th percentiles of the cached static values (static data only, before labels).
On the full grid (zeros outside footprint), for directions d ∈ {(1,0),(0,1),(1,1),(1,−1)} compute
`L_s^d(p) = mean_{t=-s..s} E(p + t·d)` for s ∈ {5, 10}. Features per channel:
`OLIC_<ch>_L11 = max_d L_5^d`, `OLIC_<ch>_L21 = max_d L_10^d`,
`OLIC_<ch>_ANISO = max_d L_5^d − mean_d L_5^d`. 9 features, finite in [0,1] on the footprint.
No labels, catalogue, or holdout geometry is an input.

## Frozen holdout protocol (shared tools only)

- Evaluator `gems25.holdout.v1.2-buffered-4quad-pooled-dti`: hide whole components (buffer 15 px),
  catalogue features from visible faults only, visible pixels masked pixel-exactly, pooled DTI
  α=0.2, β=0.8, 300 m triangular kernel (`gems25.metric.dti_binary`).
- Control: H35 = columns(`BDE`) + extras(7) + `H27_tip` + H34 sidecar, fit per cell (seed=draw),
  emission `candidates(k=round(0.035·domain))` → `score_ordered_dots(min_dist=2.4)`.
- Candidate: identical + 9 OLIC columns appended. Same cells, training rows, seeds.
- **Screen (experiment 1):** draws [82, 83], 4 folds. Gate: every OLIC feature-alone canary
  `max(AUC,1−AUC) ≤ 0.90` on every cell; paired fold-mean gain > +0.001; ≥3/4 folds positive;
  worst fold ≥ −0.010; mean hug-share Δ ≤ +0.10.
- **Confirmation (experiment 2, only if screen passes):** draws [84, 85], identical settings;
  additionally paired 95% fold CI must exclude 0.
- **Artifact (only if confirmation passes):** pre-placement surface Spearman vs registry must be
  ≤0.90 in magnitude; build via the H35 production protocol (3 pseudo-new draws averaged) + OLIC;
  final-dot 3-px overlap vs every registry raster ≤70%; `check_file` must pass. Any lane failure =
  log duplicate and stop, no TIF. A pass still does **not** spend a weekly slot (selector step separate).
- Budget: ≤3 experiments, ≤2 h. Negative results are deliverables.

Official sources for manual review: [competition](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
[GDR 1391](https://gdr.openei.org/submissions/1391), [GeoDAWN](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7),
[EPSG:32611](https://epsg.io/32611), [Tversky](https://en.wikipedia.org/wiki/Tversky_index),
[reference solution](https://github.com/drivendataorg/gems-prize-reference-solution).
All reported sibling scores are OWNER-REPORTED; no ORGANIZER-CONFIRMED score exists in this repo.
