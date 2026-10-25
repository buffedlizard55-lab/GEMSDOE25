# 21 · Pre-registered H36-TZC: coincident tilt-zero contact lines (written before any fit, 2026-10-25)

**Session lane (the single method paragraph for this run):** Add three *phase/location*
columns derived from the zero contours of the potential-field tilt angle — magnetic
tilt-zero proximity, gravity tilt-zero proximity, and their coincidence — to the
repo's validated HGB detector (families B+D+E + 7 add-ons, directed tip, H34
RESMAG-FLEX columns) and test, on the hide-and-recover holdout only, whether the
coincident-contact block raises pooled HOLDOUT-DTI against the *same-run* H35 arm-B
control (the current comparable holdout best). Emission, model, budget and evaluator
are frozen at the H35 settings (sapd 2.4 px, kfrac 0.035, `gems25.metric.dti_binary`,
α=0.2, β=0.8, R=3 px triangular kernel). Nothing else is varied in this lane.

## Why 0.2778 scored highest in the group (summary; full forensics in knowledge/17)

OWNER-reported chain (not ORGANIZER-CONFIRMED): solid h19-5 surface 0.1922 →
score-blind dotting 0.2477/0.2600 → better base surface (h27-4) 0.2708 →
deleting every dot within 2 px of the catalogue 0.2778. The largest gain is
emission economics (the metric's max-kernel credit makes redundant dots pure
0.2-weighted FP mass), then detector quality, then a catalogue-flank deletion
whose mechanism is unproven and in tension with the staff clarification that
test truth may include corrections within 300 m of known traces
(`registry/sources.json` dd-forum-11516). Beating 0.2778 therefore needs more
credit per emitted pixel from a *better detector*, not another emission trick.

## Candidate hypotheses generated this session (3–5, ranked before fitting)

| Rank | ID | Layers | Physical signature targeted | Why it should catch a catalogue-missing fault | Difference from anything implemented in this repo | Expected HOLDOUT-DTI gain (planning bracket) | Cost |
|---|---|---|---|---|---|---|---|
| 1 | **H36-TZC** coincident tilt-zero contacts | GeoDAWN TMI horizontal/vertical gradient bands (`tmi_hg` 03, `tmi_vg` 09) and isostatic gravity gradient bands (`iso_grav_anom_hg` 18, `iso_grav_anom_vg` 11) of the pinned 19-band feature raster (USGS GeoDAWN, DOI 10.5066/P93LGLVQ) | Tilt angle θ=atan2(vertical derivative, horizontal gradient) crosses **zero at a vertical contact edge** (Miller & Singh 1994); extract the 1-px zero-crossing lines of θ_mag and θ_grav, then distance-to-line and the coincidence field exp(−d_mag·d_grav/9 px²) | A buried basement fault juxtaposes magnetically *and* gravitationally different blocks under alluvial cover, so both tilt-zero lines coincide along it while no Quaternary scarp exists for the USGS/INGENIOUS catalogue to record | Family A feeds *pointwise* tilt values and horizontal-gradient ridge amplitudes to the HGB; H26-3/X3 uses ridge-amplitude products; H34 uses upward-continued RTP residual ridges. No code in `src/`, `scripts/` or `tests/` extracts a tilt **zero contour**, a distance-to-contour, or a cross-physics contour coincidence (verified by grep for `tilt`/`zero` before writing this document: only `A_mag_tilt`/`A_grav_tilt` pointwise columns exist) | 0 to +0.006 over the same-run H35-B control | ~2 h (bands already cached) |
| 2 | H36-SEISALIGN seismicity-alignment ridge | earthquake density bands `deq_n100a15` (10), `ieq_n100a15` (16) | Structure-tensor alignment/elongation ridge of the epicentre-density field: aligned microseismicity traces an active buried fault | Seismicity is independent of surface mapping; an aligned cluster can mark a fault with no scarp | Family C uses strain-rate gradients only; the density bands enter only as raw pointwise columns | 0 to +0.004 | ~2 h |
| 3 | H36-STRAINZX dilatation sign-change line | `geod_dilaterate` (08), `geod_shearrate` (07), `geod_2ndinv` (04) | Zero-crossing line of smoothed dilatation (extension↔contraction hinge), weighted by shear-rate magnitude | Extensional hinge lines localise normal-fault systems that may be buried | Family C uses gradients of 2nd-invariant/shear, never a dilatation phase boundary | −0.002 to +0.003 | ~2 h |
| 4 | H36-RADCURV radiometric ternary curvature | GeoDAWN radiometric extension ratios Th/K, U/K (external u8 grids, USGS GeoDAWN DOI 10.5066/P93LGLVQ) | Laplacian zero-crossing (curvature hinge) of Th/K: hydrothermal K-alteration fronts channelled by a buried fault | Alteration is a fluid-pathway proxy independent of the fault catalogue | Family D / X1 use ratio values and gradient-magnitude edges, not curvature phase lines | −0.002 to +0.003 | ~3 h |

Deferred (not viable without new external data): 1 m 3DEP stream-offset/knickpoint
concordance — raw tiles are not in the pinned cache and the tile table is
login-walled at DrivenData; the specific free official source needed is the USGS
3DEP 1 m DEM via The National Map (https://apps.nationalmap.gov/downloader/),
obtainability from this sandbox not verified, so it is **not** proposed as viable.

## Frozen design for H36-TZC (top candidate only; budget ≤3 experiments)

- **Columns (sidecar, footprint vectors, float32):**
  `H36_tzc_mag_prox = exp(−d_mag²/(2·2²))`, `H36_tzc_grav_prox = exp(−d_grav²/(2·2²))`,
  `H36_tzc_coincide = exp(−d_mag·d_grav/9)`, where d_mag/d_grav are Euclidean
  distances (px) to the nearest tilt-zero-crossing pixel. Zero-crossing pixel:
  θ finite, |θ| ≤ 0.05 rad, and a 4-neighbour with opposite sign (or θ exactly 0).
  Gradients nearest-filled only for the tilt computation; columns are finite
  everywhere inside the footprint by construction (distance transforms).
  *Sign convention check before fitting:* if `tmi_hg`/`iso_grav_anom_hg` contain
  negative values they are components, not magnitudes — then THDR is recomputed
  as sqrt(hg²+vg²) is wrong too; the code must instead use |hg| as THDR proxy and
  record the observed band ranges in the evidence JSON. (Decision rule written
  before seeing the holdout result; band ranges are a data property, not an outcome.)
- **Arms (per fold × draw cell, same `Cell(extras=True, h27=True)`):**
  `BEST` = BDE+7 + H27_tip + 3 H34 columns (= H35 arm B, the comparator);
  `TZC` = BEST + 3 H36 columns (primary). Attribution arm `CONLY` = BDE+7 +
  H27_tip + 3 H36 columns (no H34) is run only if TZC passes the screen.
- **Draws:** screen 30–31, confirmation 32–33 (fresh; unused by H34/H35/KDC/GEM runs),
  folds NW/NE/SW/SE. Confirmation only if the screen passes.
- **Emission:** identical for every arm: ridge NMS σ=1.0 → drop catalogue pixels →
  top-K at kfrac 0.035 → score-ordered dots at 2.4 px (`score_ordered_dots`).
- **Leakage canary:** single-feature ROC-AUC of each H36 column on each cell's
  holdout quadrant (hidden positives vs sampled negatives); any column with
  AUC > 0.90 (or < 0.10) fails the run as leakage until proven otherwise.
- **Gate (frozen):** primary comparison TZC vs BEST, paired by (fold, draw):
  mean gain > +0.001 HOLDOUT-DTI, ≥3/4 folds positive on fold-mean gains,
  worst fold ≥ −0.010, canary ≤ 0.90. Screen pass → confirmation on fresh draws;
  both must pass for `promote`. A projection is never written as a score.
- **Lane (protocol item 1):** Spearman of the full-footprint TZC score surface vs
  every registry raster ≤ 0.90 in absolute value, and ≤70% of final dots within
  3 px of any one registry raster, checked on the surface before placement and
  on the final dots. The dense r13 5-px lattice is reported separately and also
  under the literal rule; both readings are recorded, neither is hidden.
- **Validator:** `gems25.submission.check_file` against the pinned template:
  no NaN/Inf inside the footprint, values in [0,1], CRS/shape/transform match.
  The shipped primary is the **zeros-outside** variant (whole-array finite, so
  the DrivenData "Predicted values must be in range [0, 1]" error cannot recur);
  NaN-outside twin is a fallback only.
- **Slot rule:** no weekly slot is spent by the agent. `promote` means only
  "eligible for the owner's separate selector step".

## Named non-fault mimics

Lithologic contacts and volcanic flow margins produce coincident magnetic/gravity
tilt-zero lines with no fault; basin-margin facies pinch-outs produce gravity
contacts; survey line-levelling artefacts can produce straight tilt-zero segments.
Any of these would spend FP mass (0.2-weighted) with no hidden-truth credit.

## Sources (verified / read)

- USGS GeoDAWN data release, DOI 10.5066/P93LGLVQ —
  https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
  (publisher page read via web search this session; the raster itself is the
  SHA-256-pinned owner mirror in `registry/data_manifest.json`, not
  organizer-authenticated — IR-25-PROVENANCE).
- Miller & Singh (1994) tilt-angle concept (zero over source edges, amplitude-
  normalised): abstract at https://www.sciencedirect.com/science/article/abs/pii/0926985194900221
  (search-result abstract read this session; full text not fetched).
- Competition metric (α=0.2, β=0.8, 300 m triangular kernel) and staff masking
  clarification: `registry/sources.json` ids `dd-problem`, `dd-forum-11516`
  (read 2026-10-02, recorded there). CRS EPSG:32611: https://epsg.io/32611.
- No DrivenData page was accessed in this session (AGENTS.md rule 3).

## Amendment 1 (2026-10-25, before any holdout fit — operator correction, not outcome tuning)

The original operator (tilt from the provider derivative bands) is scale-broken on
this raster, measured on data properties only (no model was fitted and no holdout
outcome was seen): `tmi_hg` (median 13.15, always ≥ 0) is ~7× the spatial total
horizontal derivative of `tmi` (median 1.87 nT/px, Spearman 0.991 at σ=1 — i.e. a
per-km scaling), while `tmi_vg` has median |value| 0.051, ~300× smaller, so
atan2(vg, hg) ≈ 0 almost everywhere and the resulting "zero line" covered
1,456,226 px (28% of the footprint; gravity: 151,824 px). A proximity column built
on that mask has mean 0.55 and is >0.5 on 60% of the footprint — not a contact line.

**Corrected frozen operator (same hypothesis, same three columns, same gate):**
tilt is computed from each *field itself* (`tmi` band 14, `iso_grav_anom` band 13)
by the spectral derivative theorem at a 200 m upward-continued level —
VDR spectrum = 2π|k|·exp(−2π|k|·200 m)·F spectrum (reflect-pad 256 px, as in H34),
THDR from spatial gradients of the continued field — so both derivatives share
units and the tilt spans (−π/2, π/2). Zero-crossing extraction
(|θ| ≤ 0.05 rad with an opposite-sign 4-neighbour), proximity σ=2 px and the
coincidence field exp(−d_mag·d_grav/9) are unchanged. This amendment and the code
implementing it are committed before the first holdout fit.
