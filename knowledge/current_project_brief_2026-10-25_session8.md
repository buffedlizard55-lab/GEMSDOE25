# Session 8 Consolidated Project Brief & Active Acceptance Criteria (2026-10-25)

> **Provenance note (`IR-25-PROMPT-CONDENSED`):** This file records the exact consolidated Session 8 task scope, focus-site list, and active `Parallel-Run Protocol` constraints carried into Session 8 on branch `arena/97f7dfaa-gemsdoe25`. The verbatim earlier owner briefs (`knowledge/owner_brief_verbatim.txt` and `knowledge/current_project_brief_2026-10-25.md`) remain untouched and embedded in `README.md`.

## Focus Scope & Core Questions
1. Review `GEMSDOE25` with focus on the highest-scoring submissions from **`GEMSDOE24`, `GEMSDOE25`, `GEMSDOE27`, `GEMSDOE28`, `GEMSDOE30`, `GEMSDOE31`, `GEMSDOE32`, `GEMSDOE33`, `GEMSDOE36`** (plus cross-repository context across the sibling GEMSDOE repositories through `GEMSDOE92`).
2. Explain at PhD level **why and how** `GEMSDOE32`'s `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` achieved `0.2778` (`OWNER-REPORTED`), and assess mathematically and empirically whether a higher-scoring submission (`> 0.2778`; owner briefs also cite leaderboard highs `0.3195` and `0.4413`) can be generated — verifying every statement line by line with zero hallucinations.
3. Formulate **3–5 untried candidate geological hypotheses** specifying:
   - exact layer(s) and official free data sources (with obtainability verified),
   - physical signature and mathematical transform,
   - why each catches faults missing from the USGS / INGENIOUS catalogue rather than already-mapped ones,
   - named non-fault geological mimics,
   - how each differs from every prior feature/hypothesis in the repository,
   - planning `HOLDOUT-DTI` gain bracket and implementation cost.
4. Validate the top candidate in a **single method lane** on the shared spatially-blocked buffered hide-and-recover holdout (`alpha = 0.2, beta = 0.8, 300 m` triangular kernel), recomputing same-run controls (`IR-25-COMPARATOR-DRIFT`), checking standalone leakage canaries (`AUC <= 0.90`), and enforcing `<= 3` experiments / `<= 2` hours.
5. **Highest-urgency deliverable:** Generate a **unique** competition GeoTIFF (`.tif`) submission (never a copy of a prior GEMSDOE submission), automatically validated without human intervention (`[0, 1]` range, no NaN inside footprint, `EPSG:32611`, `3730 x 3292`, geotransform match, unique filename, `<= 140`-char note), emit a complete JSON Run Card, and surface at the very top of `index.html`, `docs/index.html`, `docs/executive-summary.html`, and `README.md` an unmistakable automated verdict on **OK TO DOWNLOAD** vs **OK TO SUBMIT / DO NOT SUBMIT**.
6. Maintain auditable source tables with verified official links, embed the brief in `README.md`, execute **3 cumulative verification passes**, document limitations and prioritized next steps, and open + merge a PR onto `main`.
