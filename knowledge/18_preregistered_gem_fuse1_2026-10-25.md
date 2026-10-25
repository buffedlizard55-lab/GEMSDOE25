# Pre-registration GEM-FUSE1 — blind magnetics surface + B2-pruned emission (2026-10-25)

**Date committed:** 2026-10-25 (before any GEM-FUSE1 fit). **Status:** proxy evidence only; not a competition score. **Source:** `knowledge/17_gemsdoe32_h33_forensic_and_new_hypotheses_2026-10-25.md`.

## 1. Question
Does combining the holdout-validated blind-magnetics surface (GEM-1: norm(|grad RTP|) × (1-norm(relief)), HOLDOUT-DTI +0.018 screen / +0.0216 confirmation vs B_crest, AUC 0.56) with the H33-validated emission pruning (delete emitted dots within 2 px / 200 m of visible catalogue traces) beat the same-run B_crest control on the spatially-blocked hide-and-recover holdout, without leaking catalogue geometry (AUC>0.90) or duplicating a registry lane (>0.90 Spearman or >70% dot overlap)?

## 2. What is new vs repo
- GEM-1 surface + H31/H26-0 emission was validated (knowledge/15) without pruning.
- H33-2 B=2 pruning was only on the old H19-5 HGB surface (GEMSDOE32 owner-mirrored bytes, not this repo's code).
- No prior experiment in this repo combines an unsupervised physics surface with a catalogue-distance emission rule. It is not a relabel of H26-0..H30-3, H31-1, or H27/H28.

## 3. Design (frozen)

**Surface:** `surface_gem1` as in `scripts/validate_gem_candidate.py` (RTP 02 + relief 22, pct_norm 1-99, gaussian σ1.0 grad). Full-footprint grid, NaN outside →0.

**Holdout:** `gems25.holdout.Holdout` (footprint + labels), hide_frac 0.20 whole catalogue components, collar 1.5 km, 4 spatial folds (NW/NE/SW/SE) × draws [0,1] screen, [2,3] confirmation only if screen passes. Catalogue features derived from visible faults only, visible faults masked pixel-exact, scored with `gems25.metric.dti_binary` (α0.2 β0.8 R=3 px, triangular kernel max(1-d/R,0), ε1e-7).

**Emission (all arms same budget, same code path `src/gems25/thinning.py`):**
- Control C: B_crest surface (`B_relief5` static channel nscale) → Hessian ridge NMS σ1.0 → drop visible catalogue → top-K (K=0.0245×eroded domain px) → dot_thin 1.5 px
- Candidate FUSE1: GEM-1 surface → same NMS → drop visible → top-K identical K → dot_thin 1.5 px → **prune**: delete dots where `distance_transform_edt(~visible & quadrant) ≤2.0 px` (200 m). Catalogue pixels never emitted (staff masking, pixel-exact). K is fixed per cell; pruning reduces emitted count vs control by ~5-10% (like H33), but the gate is paired DTI, not count.

**Response:** per-cell DTI of emitted dots vs hidden test truth (holdout.score), averaged over draws per fold → 4 fold means.

**Leakage canary (pre-fit, per feature alone):** AUC of candidate surface vs hidden test labels within scored domain; AUC>0.90 → leakage until proven otherwise → stop (protocol rule 4). GEM-1 already passed (0.56); re-checked here.

**Lane check:** Spearman(cand surface, registry raster) on 400k footprint sample + dot overlap within 3 px vs each registry raster in `data/scored/*.tif` (registry/data_manifest.json pins). >0.90 correlation or >70% candidate dots within 3 px of one registry raster → duplicate → stop, log.

**Reproduction:** Control C per-cell DTI must match prior `evidence/gem_validation/results.json` control cells within 1e-6 (void if not).

## 4. Gate (frozen)

- **Screen pass:** mean paired gain (FUSE1 - C) >+0.001, ≥3/4 folds positive, worst fold ≥-0.01. Leakage canary AUC≤0.90 and lane clean vs substantive registry rasters (lattice dens artefact logged, not a lane, IR-25-LANE-DENSITY).
- **Confirmation (draws 2,3, fresh) only if screen passes:** same three conditions.
- **Verdict:** pass both → `promote` (eligible for separate slot-selector plus exact-file audit). Otherwise → `negative`. Negative is a deliverable; do not re-run.

## 5. Limits stated in advance

- Holdout truth = catalogue components (IR-25-PROXY-LIMITS); cannot test whether B=2 pruning would hurt if real hidden truth lies within 200 m of a mapped trace (IR-32-PROXY-01). Proxy↔live Spearman +0.33 (n=24, n.s.) — proxy win is necessary, not sufficient.
- No new external data; bands are from competition raster + 3DEP LiDAR descriptors (both already pinned).
- Budget 3 experiments / 2 h (protocol rule 6).
