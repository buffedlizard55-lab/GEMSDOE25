# Preregistered review — 2026-10-28

> **Later checkpoint:** shared caches were rebuilt and their six recorded hashes match; see the [current review](43_latticegap_review_2026-10-28.md). The lane remains unassigned and none of the ideas below was fitted or evaluated.

No geological experiments are authorized in this run: the owner brief references a single method paragraph but supplies no identifiable lane assignment. Do not silently pick a competing lane. Budget: zero fitting experiments; no upload or slot selection.

First independently rerun the existing pinned three-raster capacity audit. If impossible at the historical dot budgets, record the stop without generating a cosmetic TIFF. Reuse the shared writer and holdout implementations; do not introduce private replacements. Implement a fail-closed readiness evidence gate, test missing/nonfinite/conflicting evidence and exact threshold boundaries, and publish the audit outcome before historical downloads.

Four planning-only hypotheses, ordered by qualitative scientific leverage then cost (not predicted scores):

1. **Magnetic contact interruption across sediment cover**: residual magnetic intensity and DEM; detect an abrupt break in a persistent magnetic edge where low relief hides scarps. Could recover buried displacement rather than visible scarps. Mimic: lithological contact or flight-line seam. Distinct proposed test: matched edge continuity on both sides of a cover crossing, rather than existing magnetic-flank/tilt amplitude. Medium cost, unknown DTI gain.
2. **Radiometric compositional offset with conserved total intensity**: K, Th, U channels; opposing cross-edge log-ratio gradients with a weak total-count edge. Could expose subtle juxtaposition under weathered cover. Mimic: soil moisture or depositional sorting. Unlike generic alteration fusion, explicitly condition on total-count invariance. Medium cost, unknown DTI gain.
3. **Cross-valley matched terrace displacement**: DEM; repeated same-sense elevation residual offsets across multiple drainages after fitting local valley profiles. Could reveal weak scarps missed by catalogue mapping. Mimic: fluvial incision or Lake Lahontan shorelines. Different from generic curvature/ridge detectors by requiring repeated geomorphic displacement. High cost, unknown DTI gain.
4. **Magnetic spectral phase discontinuity**: residual magnetic intensity; multiscale local phase jumps without requiring strong edge amplitude. Could identify weak buried contacts. Mimic: acquisition seams and lithological boundaries. Different from existing worm-persistence and Euler-depth pipelines by testing phase rather than amplitude/depth. High cost, unknown DTI gain.

These are untested proposals, not proven new across all sibling repositories, and not viable execution lanes until assigned and cached layer metadata is checked. No new external data is required in principle, but this checkout initially has no feature cache. Official source for layer provenance: USGS GeoDAWN https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and (not accessible under this environment's host allowlist). Official reference code: https://github.com/drivendataorg/gems-prize-reference-solution . Do not claim external-source verification from an inaccessible page.

Maximize P(Win): avoid unsupported performance claims and conserve slots. Own the Outcome: automate fail-closed checks rather than mark an untested artifact ready.
