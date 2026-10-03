# Knowledge index (start here after the README)

| File | Purpose |
|---|---|
| `../README.md` | status, standing charter, the owner brief (verbatim) |
| `../AGENTS.md` | rules for every session (first commands, no DrivenData automation, slot discipline) |
| `owner_brief_verbatim.txt` | the brief exactly as received (also embedded in the README) |
| `03_hypotheses_ranked_2026-10-02.md` | historical H26 pre-run ranking and dated validation addendum; not a current list of untried hypotheses |
| `04_preregistered_factorial_2026-10-02.md` | frozen 2^(5−1) design and historical analysis rules, with current slot-policy supersession note |
| `05_preregistered_addons_2026-10-02.md` | historical frozen add-on/emission tests plus an explicit supersession of its old primary-download rule by the current no-slot-without-holdout-win policy |
| `06_geothermal_research_digest_2026-10-02.md` | source-checked geoscience/competition facts with links, explicit score-claim caveats, and overlooked sources |
| `07_findings_2026-10-02.md` | what the forensics, the factorial, the add-on tests and the emission model show; deviations from the pre-registrations |
| `08_data_dictionary_2026-10-02.md` | every provided band and external layer: shipped description vs official wording, statistics, family, flags, licences (generated) |
| `09_preregistered_hypotheses_2026-10-02.md` | fresh, ranked H27 hypotheses; official source/obtainability checks; frozen H27-1 2² test and submission gate |
| `10_preregistered_h28_live_anchored_emission_design_2026-10-02.md` | **current**: the live-anchored calibration of the hidden truth (N, concentration scale), the DTI-optimal emission design, the redundancy theorem, amendments D1–D3 and the findings (§12) with the ranked H29 next hypotheses (§13) |
| `../registry/*.json` | sources (with verification status), irregularities, score ledger, data pins, shipped submissions, **artefact ledger** (30 competition rasters with SHA-256 ↔ reported-score links), artefact mirrors |
| `../evidence/*` | machine-readable results (factorial, add-ons, H27 screen/confirmation, score-claim audit, why-0.2477, emission model, forensics, **h28_calibration**, **h28_holdout**, **work_cache_hashes**, **provenance**) |

## How to read the H28 evidence

| File | What it settles |
|---|---|
| `../evidence/h28_calibration/anchors.json` | the λ scan, the five implied truth counts, checks A1–A4 (uniform truth falsified; N = 12 691) |
| `../evidence/h28_calibration/design.json` | C3/C5 checks, the 30-row credit-per-pixel skill table, the ceiling sweep, every design, the (λ, N) sensitivity grid, the credit density each leaderboard target requires |
| `../evidence/h28_calibration/mixture.json` | the two-band mixture scan and why it was **not** adopted; implied N per surface (where off-band truth lives) |
| `../evidence/h28_calibration/habitat_fit.json` | the distance-to-known-faults habitat model and its failure (LOO RMSE 0.070–0.081) |
| `../evidence/h28_holdout/results.json` | the 30-arm factorial, the comparator reproduction check, contrasts, promotion gate |
| `../evidence/work_cache_hashes.json` | SHA-256 of every derived cache plus library versions (IR-25-COMPARATOR-DRIFT) |
