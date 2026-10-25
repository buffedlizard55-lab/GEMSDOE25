# 16 · Current task prompt — condensed restatement (2026-10-25)

**Source:** the user message of 2026-10-02/2026-10-25 (verbatim owner brief restated). This is a summary for quick session starts; the full message text is the authority.

## Core mandate
- Generate a **unique TIF submission** for the DOE GEMS Prize (DrivenData #306). Do not copy a previous submission unless for learning/education. It must be **obvious whether it is OK to download and submit the generated TIF**.
- Provide an **easy-to-download submission TIF** on the site; values must be in [0,1], NaN outside the footprint, CRS/shape/geotransform matching the template (fixes the "Predicted values must be in range [0, 1]" portal error caused by NaN inside the footprint).
- Give it a **unique name** and a short **Note (optional)** for the DrivenData submission form.
- Create an **executive summary subpage** explaining exactly how to make a submission (front and center on the site).
- Target: beat the reported high scores (GEMSDOE32's 0.2778; stated leaderboard target 0.3195).
- 3–5 **new geological hypotheses** (not relabels of H26–H30), each naming layers, physical signature, why it catches catalogue-missing faults, how it differs from repo work, expected DTI gain, cost. Validate the top candidate on the spatially-blocked holdout before any weekly slot.
- No DrivenData automation (leaderboard/data/submission access prohibited). No organizer receipts accessed. Treat all scores as unverified claims.
- Work autonomously, line by line, no hallucinations, flag irregularities. Three review passes, recorded in `registry/review_passes.json`.
- End with one JSON run card (hypothesis; mechanism; mimicking non-fault process; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output; submission name + ≤140 char note; verdict promote/negative).
- Create a PR from the session branch and merge via the repo's PR workflow; never claim an unverified merge/deployment/score.

## Repo constraints that bind this session
- 2 CPUs / 4 GB RAM, no GPU → HistGradientBoosting, not U-Net; no raw 1 m DEM processing.
- `data/` empty initially; inputs restored only from SHA-256-pinned owner mirrors (`scripts/restore_data.py`), never DrivenData automation.
- Hide-and-recover holdout = catalogue-gap proxy, not truth; proxy↔live Spearman was +0.33 (n=24, n.s.). Holdout win necessary, not sufficient.
- Promotion gate (pre-registered): beat the best comparable same-run holdout control (paired gain > +0.001, ≥3/4 folds positive, worst ≥ −0.01), leakage canary AUC ≤ 0.90, LANE check (registry raster |Spearman| ≤ 0.90, ≤70% of dots within 3 px of one registry raster's dots). Exact-file audit via `src/gems25/submission.py::check_file`.
- Slot discipline: no weekly slot unless the specific candidate beats the comparable same-run holdout best and passes the gate. Format-green is not gate-green.

## What this session did
- Restored 22 pinned inputs (419 MB feature raster, labels, template, LiDAR/radiometric/GDR layers, scored mirrors); built 64 static features; 106 tests pass.
- Studied GEMSDOE32's 0.2778 (knowledge/14): geometry-first thinning of a base surface; credit-per-pixel break-even ≈ 0.052 at DTI 0.26; needs ≈+25% more mean credit per pixel to reach ≈0.32; path = better detector + blurred-truth (σ≈1.85px) emission.
- Proposed 5 hypotheses (knowledge/15): GEM-1 blind magnetics (rank 1), GEM-2 vents × thermal (rank 2), GEM-3 off-trace dots (rank 3), GEM-4/GEM-5 deferred.
- Validated on holdout (evidence/gem_validation/): GEM-1 screen +0.0180 and confirmation +0.0216 vs same-run control, 4/4 folds each, AUC ≤0.561 (no leakage); GEM-2 fail; GEM-3 passes holdout but is a LANE duplicate (off-trace dots hug the catalogue; lattice-raster overlap degenerate) → not packaged.
- LANE check GEM-1: worst |Spearman| vs registry = 0.072 (cap 0.90); dot overlap vs substantive registry rasters ≤48.2% (cap 70%); lattice raster (5-px full-footprint grid) gives 100% overlap for any emission — logged as irregularity, not lane drift.
- Built unique TIF `gems25-gem1-blind-magnetics-20261025-279a305b80d2-nan.tif` (sha256 51d0b341…, 49,373 dots, format-verified, all hard checks pass).
- Status: **format-validated; holdout-validated vs same-run control; NOT slot-approved; not a live score.** OK to download for testing; NOT authorized for a weekly scoring slot on current evidence.
- Site: homepage + executive summary feature the GEM-1 download with explicit OK-to-download / NOT-OK-to-submit labeling and copy-ready submission note.

## Remaining work / limitations
- No organizer score exists for any artifact; live score cannot be verified from this sandbox (DrivenData access prohibited).
- GEM-1 does not beat the frozen 0.152003389 comparator (which doesn't reproduce here); a weekly slot is not authorized.
- GEM-2 (vents) failed; GEM-4/GEM-5 need external data not obtainable from the sandbox.
- Next session: decide whether to invest another slot in GEM-1 at full footprint, tune kfrac, or pursue a new preregistered hypothesis.
