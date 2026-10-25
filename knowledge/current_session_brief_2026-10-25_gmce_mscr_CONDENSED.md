# Current session brief (2026-10-25, GMCE/MSCR session) — CONDENSED, NOT verbatim

Stored at the owner's standing instruction ("put this prompt into the repo … and read it every
time we work on the project"). This is an agent-made condensation for working use; it is **not**
claimed verbatim (see IR-25-BRIEF-RECONSTRUCTED for earlier copies and their status).

Operative requirements of the received prompt, in the owner's priority order:

1. Focus on the highest-scoring submissions of GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36.
   Group best to beat: GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` at 0.2778
   (owner-reported). Explain at PhD level why/how it scored highest and whether higher is
   achievable. Leader claims in the brief: 0.3195 and 0.4413 (conflicting).
2. MUST generate a UNIQUE TIF submission (never copy a previous one); it must be obvious from
   the site whether it is OK to download and submit; validation must be automated by the
   project, no human inspection step.
3. PARALLEL-RUN PROTOCOL: one lane; stay in it (surface |Spearman| ≤ 0.90 and ≤ 70 % dots
   within 3 px vs registry, else duplicate/stop); reuse cached stack + holdout evaluator +
   submission writer; label numbers HOLDOUT-DTI (evaluator, withheld count, 95 % CI) or
   ORGANIZER-CONFIRMED; leakage canary AUC > 0.90 stops; end with one JSON RUN CARD;
   ≤ 3 experiments / 2 h; agent never spends a slot.
4. Before implementing: 3–5 untried geological hypotheses with layers, physical signature,
   catalogue-missing rationale, and difference vs this repo; rank by expected gain/cost;
   validate the top one on the spatially blocked holdout before any slot is considered;
   ideas needing new external data must name a free official source and its obtainability.
5. The generated file must fix the owner's portal error "Predicted values must be in range
   [0, 1]"; unique filename + short DrivenData Note; executive-summary subpage explains
   exactly how to submit; site's first screen makes download + submit-readiness obvious.
6. Core values: Maximize P(Win); Own the Outcome. Verify line by line from official sources
   with links; flag irregularities; no hallucinations; three passes; end with a PR merged to
   main plus remaining-work/limitations suggestions.

Session execution record: `knowledge/21` (hypotheses + GMCE-1 pre-registration), `knowledge/22`
(MSCR-1 pre-registration), `knowledge/23` (outcomes), run card
`registry/run_card_session_2026-10-25_gmce_mscr.json`. Standing rules in `AGENTS.md` (read first).
