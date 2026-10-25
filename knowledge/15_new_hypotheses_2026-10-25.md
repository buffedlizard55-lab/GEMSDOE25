# 15 · New, untried candidate hypotheses (drafted 2026-10-25, pre-fit)

**Evidence classes:** READ = official/primary source read this session · COMPUTED = reproducible in this repo · INFERENCE = reasoning, assumptions stated.
**Novelty boundary:** these are NOT relabels of H26-0…H26-4, H27-1…H27-4, H28, or H30-1…H30-3 (knowledge/03–04, 09–12). Expected-gain figures are ordinal planning brackets (uncertain), not forecasts. The hide-and-recover holdout is a catalogue-gap proxy; it cannot reward a genuinely new fault, so a pass is necessary, not sufficient.

**Constraint from GEMSDOE32's analysis (knowledge/14, owner-reported claim, not verified):** to move from ≈0.26 to ≈0.32 the file needs ≈+25% more mean credit per emitted pixel at constant mass. Two levers: (a) a better detector for catalogue-missing faults, (b) an emission rule that covers the blurred truth (σ ≈ 1.85 px) rather than the catalogue surface itself, with catalogue pixels excluded.

---

## GEM-1 — Blind-fault magnetics indicator: RTP edge strength × low topographic relief (rank 1)

* **Layers:** `rtp` band 02 (reduced-to-pole magnetics, GeoDAWN DOI 10.5066/P93LGLVQ via pinned mirror) × `det_elev` band 12 (detrended elevation) → local relief (max-min in a ~5 km window).
* **Physical signature:** A concealed fault juxtaposes magnetically different blocks without breaking the surface → strong RTP horizontal-gradient magnitude co-located with *low* relief (no scarp, so the fault is absent from the Quaternary/INGENIOUS catalogue). High RTP gradient + high relief = a mapped scarp (catalogue); high RTP gradient + low relief = a blind candidate.
* **Why it catches catalogue-missing faults:** it is deliberately anti-correlated with surface expression; known faults already carry scarp features (family B/LiDAR), so this surfaces what the catalogue missed by construction.
* **Difference from repo work:** family A uses tmi_hg/tmi_vg/iso_grav_anom_hg as *pointwise raw channels* and ridge strengths; nothing conditions a magnetic edge on the *absence* of topographic expression. H26-3 tested gravity∧magnetic ridge coincidence but not relief suppression.
* **Expected ΔDTI (planning bracket):** 0…+0.010. Cost: ~half a day (two full grids already in cache).
* **Validatable now?** Yes — all arrays local. AUC canary: feature vs holdout hidden truth must be ≤ 0.90 (else leakage).

## GEM-2 — Quaternary volcanic-vent proximity × near-surface thermal gradient (rank 2)

* **Layers:** `gdr_volcanic_vents_in_footprint.csv` (21 Quaternary vents, GDR 1391 / DOE 10.15121/1881483, CC BY 4.0, local) → distance-to-vent grid; × `cond_surf` band 17 (surface conductivity) gradient magnitude.
* **Physical signature:** Blind geothermal systems cluster at young volcanic centres; faults that host them may be unmapped. A vent is a surface expression of a magmatic/geothermal plumbing system; the fault feeding it need not be in the Quaternary catalogue.
* **Why it catches catalogue-missing faults:** vents are independent of the fault catalogue; proximity-to-vent highlights the plumbing faults that the INGENIOUS/USGS compilation may have missed because they lack Quaternary surface rupture.
* **Difference from repo work:** GDR springs/wells (`D_gdr_*`) are family D features, but volcanic vents are not used anywhere in this repo or in GEMSDOE24's register. H27-3 (paleo-geothermal deposits) was blocked on data fetch; vents are already local and verified (22-line CSV, 21 vents).
* **Expected ΔDTI (planning bracket):** 0…+0.008 (vent count is tiny — 21 points — so the signal is sparse). Cost: ~half a day.
* **Validatable now?** Yes — CSV restored. AUC canary applies.

## GEM-3 — Blurred-truth emission rule: dots placed 1–3 px OFF visible catalogue traces (rank 3)

* **Layers:** none new — a transform of any continuous surface; uses the visible catalogue only for the exclusion/offset rule.
* **Physical signature:** the H28-implied hidden truth is scattered around catalogue traces at σ ≈ 1.85 px (GEMSDOE25 H28 inference, owner-reported-claim-derived). Dots should sit in the 1–3 px annulus around visible traces (where blurred truth is likeliest), not on the traces themselves, and never on catalogue pixels (masked anyway).
* **Why it catches catalogue-missing faults:** it doesn't detect faults; it re-spends a fixed pixel budget where truth is most likely given the metric's blur kernel (max credit at zero distance, but truth itself is offset from the visible trace).
* **Difference from repo work:** `dot_thin` keeps on-surface pixels (score-blind); `score_ordered_dots` (H26-0) re-selects on-surface pixels by score. Neither places dots off-trace. This is the emission-rule half of GEMSDOE32's "two-round objective".
* **Expected ΔDTI (planning bracket):** 0…+0.008 on a weak surface; larger on a strong one. Cost: a few hours (unsupervised, no model fit).
* **Validatable now?** Yes.

## GEM-4 (deferred) — 3DEP 1 m DEM stream-offset / knickpoint concordance

* **Layers:** raw 3DEP 1 m DEM tiles; streams from NHD. Faults offset channels; knickpoints mark active scarps.
* **Viability:** deferred. Only per-100 m descriptors are cached; raw tiles are not obtainable from this sandbox (the 1 m DEM link table is login-walled at DrivenData; the mirrored JSON tile list is OCR-recovered). Needs a networked runner + byte-verified coverage. Carried over from GEMSDOE24 (H24-6).

## GEM-5 (deferred) — INGENIOUS map-scale correction corridor

* **Layers:** per-fault map-scale raster from GDR 1391 Qfaults (NBMG INGENIOUS). Low map-scale (generalized) traces are less reliable; high-detail traces near a prediction are more credible.
* **Viability:** deferred. Listed in sources but binary/coverage/licence not verified (README IR-25 lists it as needing a CI fetch).

---

## Ranking (expected gain × proxy-validatability ÷ cost)

| Rank | ID | Idea | Validatable now | Cost | Expected ΔDTI bracket |
|---|---|---|---|---|---|
| 1 | GEM-1 | RTP edge × low relief (blind magnetics) | Yes | ~0.5 day | 0…+0.010 |
| 2 | GEM-2 | Vent proximity × thermal gradient | Yes | ~0.5 day | 0…+0.008 |
| 3 | GEM-3 | Blurred-truth off-trace dots | Yes | few hours | 0…+0.008 (surface-dependent) |
| 4 | GEM-4 | 3DEP 1 m stream-offset | No (raw tiles) | days + fetch | deferred |
| 5 | GEM-5 | INGENIOUS map-scale corridor | No (external fetch) | ~1 day + fetch | deferred |

**Validation order:** run GEM-3 first (cheapest, isolates the emission-rule lever GEMSDOE32 credits most), then GEM-1 (best detector lever). A candidate must beat the best comparable same-run holdout control and pass the paired gate (mean gain > +0.001 DTI, ≥3/4 folds positive, worst fold ≥ −0.01) *and* the leakage canary (AUC ≤ 0.90) before any TIF is packaged.
