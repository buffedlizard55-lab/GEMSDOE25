# Owner brief — 2026-10-25 (consolidated restatement, NOT a verbatim quote)

The 2026-10-25 message is long and mixes several requests. This file keeps every requirement, condensed and grouped.
The earlier verbatim brief remains in `knowledge/owner_brief_verbatim.txt`. Any gap between this text and the original
message is a restatement error to flag, not a new instruction.

## A. Highest urgency (stated as "must be followed")

1. **Generate a unique TIF submission for the competition.** Do not copy a previous submission (learning and education
   copies are allowed). The file must be easy to download from the site's first screen.
2. **It must be obvious whether the file is OK to download and submit.** The status shown must say so in plain words.
3. **Validation must run through the project, without human inspection.** Read the whole brief; several sites mention a
   human inspector, but validation must be automated and verifiable.
4. **Portal error to prevent:** `Predicted values must be in range [0, 1]`.
5. **Each submission needs a unique name and a short note** (≤ 140 characters) to tell submissions apart.
6. **An executive-summary subpage** explains how to submit, and sits at the top of the site.

## B. Research and analysis requests

7. Study the GEMSDOE32 page (0.2778, `h33-h33-2-b2-…-zeros`): why it scored, how, and whether we can exceed 0.2778.
   Answer with PhD-level reasoning, and verify line by line with no hallucinations.
8. Review the high-scoring GEMSDOE sites (24, 25, 27, 28, 30, 31, 32, 33, 36). Explain their methods and how they
   differ. Note the sibling claims as claims.
9. Generate 3–5 new geological hypotheses. For each, name the layers, the physical signature, why it should find a fault
   missing from the USGS/INGENIOUS catalogue, and how it differs from the repo. Rank by expected gain and cost. Validate
   the top one on the spatially blocked holdout before spending a weekly slot. If a candidate needs new data, name the
   free official source and check it can be obtained first.
10. Use a PARALLEL-RUN PROTOCOL: a lane limit, reuse of the shared holdout/evaluator/writer, labelled numbers
    (HOLDOUT-DTI vs ORGANIZER-CONFIRMED), a leakage canary (single-feature AUC > 0.90 means leakage until proven),
    a run card (JSON), and a budget (3 experiments or 2 hours).
11. Work with verified official sources and give links for manual review. Flag irregularities. No hallucinations.
12. Find overlooked data sources and new hypotheses, and store all verified knowledge in the repo as a base for later work.

## C. Standing product requirements

13. Put this brief into the README and read it at the start of every session.
14. Core values: **Maximize P(Win)** and **Own the Outcome**. They are the decision rule for every change.
15. A site that is clean, simple, organized and current, with a live feed and official source links.
16. Run work in three passes: implement and verify; review for bugs and assumptions; re-check against this brief.
17. Open a pull request from the session branch and merge it to `main` if checks pass. Make suggestions for next work and
    list the limitations, for the next session.

## D. Limits that stay in force (from AGENTS.md)

* No automated access to drivendata.org, and no submission uploaded by the agent. The owner submits manually.
* A weekly slot is used only for a candidate that beats the same-run comparable holdout best and passes the exact-file
  audit. A format-valid file is not a slot-approved file.
* Holdout DTI is a proxy. It is never a competition score.
