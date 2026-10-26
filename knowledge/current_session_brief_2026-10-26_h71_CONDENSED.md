# 2026-10-26 session brief (condensed, not verbatim)

The owner's message is the standing GEMSDOE25 charter plus the Parallel-Run Protocol. Actionable constraints used this session:

* Generate a **unique** GeoTIFF (not a byte or near-duplicate of any GEMSDOE24–36 / sibling top-scorer). Values in `[0, 1]`, no NaN inside the footprint (zeros-outside primary to avoid "Predicted values must be in range [0, 1]").
* Study why GEMSDOE32 `h33-h33-2-b2` OWNER-REPORTED `0.2778` scored (it is `D2.8 & d(cat)>2`), and whether a **non-clone** can beat it.
* Before implementing: rank 3–5 **untried** geological hypotheses (layers, signature, why missing from the catalogue, mimic, difference from this repo). Validate the top candidate on hide-and-recover holdout. Do not spend a weekly slot.
* Lane: rank-corr > 0.90 or >70% of dots within 3 px of one registry raster = duplicate stop. Reuse cached features, `evaluate` / `submission` writers. Leakage canary AUC > 0.90 = stop. Budget: 3 experiments / 2 hours.
* Label numbers HOLDOUT-DTI or OWNER-REPORTED. Never DrivenData automation. Negative results are deliverables.
* Site: obvious download + OK-to-download / OK-to-submit banners. Executive summary. PR from this branch, then merge.

Full frozen design: `knowledge/27_preregistered_h71_hgpc_2026-10-26.md`.
The historical owner brief copies remain in `knowledge/owner_brief_*.txt`; this file is a working condensation, not a verbatim transcript (`IR-25-BRIEF-RECONSTRUCTED` class).
