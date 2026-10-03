# Knowledge index (start here after the README)

| File | Purpose |
|---|---|
| `../README.md` | current status, standing charter, the 2026-10-02 owner brief (verbatim), and the 2026-10-03 continuation brief (consolidated, not verbatim) |
| `../AGENTS.md` | rules for every session (first commands, no DrivenData automation, slot discipline) |
| `owner_brief_verbatim.txt` | the brief exactly as received (also embedded in the README) |
| `03_hypotheses_ranked_2026-10-02.md` | historical H26 pre-run ranking and dated validation addendum; not a current list of untried hypotheses |
| `04_preregistered_factorial_2026-10-02.md` | frozen 2^(5−1) design and historical analysis rules, with current slot-policy supersession note |
| `05_preregistered_addons_2026-10-02.md` | historical frozen add-on/emission tests plus an explicit supersession of its old primary-download rule by the current no-slot-without-holdout-win policy |
| `06_geothermal_research_digest_2026-10-02.md` | source-checked geoscience/competition facts with links, explicit score-claim caveats, and overlooked sources |
| `07_findings_2026-10-02.md` | what the forensics, the factorial, the add-on tests and the emission model show; deviations from the pre-registrations |
| `08_data_dictionary_2026-10-02.md` | every provided band and external layer: shipped description vs official wording, statistics, family, flags, licences (generated) |
| `09_preregistered_hypotheses_2026-10-02.md` | fresh, ranked H27 hypotheses; official source/obtainability checks; frozen H27-1 2² test and submission gate |
| `10_preregistered_h28_live_anchored_emission_design_2026-10-02.md` | H28 metric-model calibration conditional on owner-reported, hash-linked claims; DTI-optimal emission design and findings (§12); its H29 ideas (§13) are already registered, not new work |
| `11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md` | frozen H30-1 paired-tip relay × terrain 2² holdout design, ranked H30 hypotheses, stage/confirmation gates, and explicit novelty boundary |
| `12_h30_relay_factorial_outcomes_2026-10-03.md` | registered H30 screen pass + fresh-confirmation failure, weighted-credit analyzer correction, stop decision, and proxy limitations |
| `current_project_brief_2026-10-03.md` | full active scope and acceptance criteria from the condensed handoff, labeled as a consolidated restatement rather than a verbatim prompt |
| `../registry/*.json` | sources (with verification status), irregularities, score ledger, data pins, shipped submissions, **artefact ledger** (30 competition rasters with SHA-256 ↔ reported-score links), artefact mirrors |
| `../evidence/*` | machine-readable results (prior factorial/add-ons/H27/H28, H30 feature smoke plus registered screen/confirmation results, score-claim audit, emission model, forensics, work-cache hashes, and provenance) |

## How to read the H28 evidence

| File | What it settles |
|---|---|
| `../evidence/h28_calibration/anchors.json` | the λ scan, five model-implied truth counts, and checks A1–A4 conditional on owner-reported score claims (uniform-π candidate falsified; fitted N = 12,691) |
| `../evidence/h28_calibration/design.json` | C3/C5 checks, the 30-row credit-per-pixel skill table, the ceiling sweep, every design, the (λ, N) sensitivity grid, the credit density each leaderboard target requires |
| `../evidence/h28_calibration/mixture.json` | two-band mixture scan and why it was **not** adopted; conditional model-implied N diagnostics per owner-mirrored surface (not verified hidden truth) |
| `../evidence/h28_calibration/habitat_fit.json` | the distance-to-known-faults habitat model and its failure (LOO RMSE 0.070–0.081) |
| `../evidence/h28_holdout/results.json` | the 30-arm factorial, the comparator reproduction check, contrasts, promotion gate |
| `../evidence/work_cache_hashes.json` | SHA-256 of every derived cache plus library versions (IR-25-COMPARATOR-DRIFT) |
