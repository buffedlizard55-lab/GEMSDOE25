# Active project brief — continuation task (2026-10-03)

> **Status of this transcription:** the exact current user message was condensed into a session handoff before this continuation. This file preserves its full active task and acceptance criteria as received in that handoff; it is a faithful consolidated restatement, **not a verbatim quotation**. The earlier 2026-10-02 message remains separately preserved as `owner_brief_verbatim.txt`.

## Objective and decision principles

Continue the GEMSDOE25 project toward a higher-scoring DOE GEMS Prize submission. Apply **Maximize P(Win)** and **Own the Outcome**: spend effort on verifiable scientific leverage, resolve data/engineering blockers autonomously, and report negative results. Treat the reported 0.2477 result and the stated 0.3195 leaderboard target as user/owner-reported claims unless official evidence is independently accessed; do not imply that either is verified.

## Scientific work and experimental design

- Review the full standing README/brief and repository history each session. Study prior evidence before proposing work; do not relabel earlier H26/H27/H28/H29 hypotheses or runs as new experiments.
- Move beyond one-factor-at-a-time testing. The completed historical design is a preregistered 2^(5−1), Resolution V fractional factorial across the five existing families: potential-field gradients, DEM curvature/scarp, strain/seismicity, thermal/geochemical, and catalogue geometry. It estimates main effects and pairwise interactions on the spatially blocked hide-and-recover holdout; its recorded results are prior work, not new evidence.
- Before implementing a new geological candidate, propose and rank **3–5 genuinely untried hypotheses**. For each, state the layers, physical signature, rationale for finding faults missing from the catalogue, how it differs from prior repository work, expected holdout DTI gain as an explicitly uncertain planning bracket, cost, and data/validation status.
- Verify each source claim from the cited official or primary source, line by line where relevant. If a candidate needs new external data, verify that the free official source and required data are actually obtainable before calling the candidate viable. A page listing is not proof that a binary, schema, coverage, or licence has been checked.
- Preregister the design, folds/draws, model, response, analysis, and promotion gate before fitting. Do not tune after seeing outcomes. Use spatially blocked hide-and-recover holdout, report main effects and pairwise interactions, and distinguish proxy evidence from competition performance.
- Validate the top candidate before creating a new submission artifact or considering a weekly submission slot. The candidate must beat the best *comparable same-run* spatial holdout control, pass the preregistered paired/confirmation gate, and pass an exact-file audit. A prior frozen comparator that does not reproduce is not a valid cross-run threshold. A screen pass alone is not confirmation.

## Submission artifact and site

- Keep the format-validated GeoTIFF easy to find and download from the site/README. Verify the competition template's dimensions, CRS, geotransform, valid footprint, and `[0,1]` value range. Each new file must have a unique content-addressed filename, SHA-256 receipt, and concise submission note.
- Do not create, label, or promote a new candidate unless the registered holdout gate passes. Do not spend a weekly submission slot on an unvalidated candidate.
- Preserve the concise executive-summary/how-to-submit guide, with manual-only upload instructions and clear status labels. The site and source/feed pages must be useful, current, and link to manually reviewable official sources.

## Data, evidence, and communication rules

- No automated access, monitoring, scraping, or submission to `drivendata.org`; the repository's `AGENTS.md` and DrivenData Terms policy prohibit it. Do not use DrivenData authentication. Hash-pinned owner mirrors are owner-supplied bytes, not organizer-authenticated files.
- Keep OFFICIAL source statements, owner/user-reported score claims, locally COMPUTED measurements, and INFERENCE clearly separate. Unknown stays unknown. Flag inconsistencies, stale links, data/schema/licensing gaps, comparator drift, and other irregularities rather than silently resolving them.
- Prefer free public official sources for third-party data. Provide direct links and enough provenance for manual review. Do not commit large restored datasets or caches; use the repository's ignored/external-data conventions.
- Keep current, auditable source/evidence tables, data manifest, score claims and artifact ledger. Update the README and site only from evidence that is actually present and verified.

## Autonomous execution and quality gates

Work autonomously; do not ask the owner for manual inputs or credentials. Before finishing, complete three cumulative review passes: (1) implement and verify against sources and the registered design; (2) inspect bugs, assumptions, leakage risks, and edge cases, then fix them; (3) re-check the full result against this brief and the original request. Record the passes in `registry/review_passes.json`.

Prepare a PR from the fixed Arena session branch and merge only through the repository's PR workflow if checks and authentication permit. Never claim a PR, merge, deployment, or score verification unless a URL/status/receipt proves it. Report limitations, remaining work, and any access that is genuinely needed without requesting secrets.

## Existing facts that constrain this continuation

- `data/` was initially empty; project inputs may be restored only from hash-pinned public owner mirrors or verified official sources, never by automating competition access.
- The previous H28 holdout's frozen comparator reproduction failed. Its nominal best arm was not slot-eligible.
- The H27-1 combined tip/scarp arm failed its registered absolute comparator gate; its T-only screen was unconfirmed and is not slot-eligible.
- Existing H26 factorial, add-on, emission, and H29 next-hypothesis registers are prior work and must be reviewed for overlap.
- Existing downloadable D2.8 files are format-validated, unscored/owner-mirror artifacts and are not approved for a weekly slot.
- **State discrepancy:** the condensed handoff says the five-family factorial remains unrun, while the tracked `evidence/factorial/` contains 16 model rows × 8 cells, reference rows, and complete analysis. `scripts/analyze_factorial.py` reproduced its results byte-for-byte on 2026-10-03. This evidence and the mismatch are recorded as `IR-25-FACTORIAL-STATE`; do not overwrite or rerun the old experiment just to resolve a wording conflict. H30 is explicitly additional, not a replacement.
