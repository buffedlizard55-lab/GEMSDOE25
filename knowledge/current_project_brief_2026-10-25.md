# Current Session Prompt (2026-10-25 — Verbatim)

Focus on the highest scoring submissions from the below sites:

https://buffedlizard55-lab.github.io/GEMSDOE24/
https://buffedlizard55-lab.github.io/GEMSDOE25/
https://buffedlizard55-lab.github.io/GEMSDOE27/
https://buffedlizard55-lab.github.io/GEMSDOE28/
https://buffedlizard55-lab.github.io/GEMSDOE30/
https://buffedlizard55-lab.github.io/GEMSDOE31/
https://buffedlizard55-lab.github.io/GEMSDOE32/
https://buffedlizard55-lab.github.io/GEMSDOE33/
https://buffedlizard55-lab.github.io/GEMSDOE36/

We want to generate a submission with a higher score than the current highest scoring submission of 0.2778 from https://buffedlizard55-lab.github.io/GEMSDOE32/ (h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778). Study, analyze and explain why and how it achieved this score and if we can generate a submission that is higher scoring and how. The highest score on the leaderboard is 0.4413.

You MUST generate a UNIQUE tif submission for the competition. Do not copy a previous submission, unless it is for learning and education.

Make it obvious whether it is ok to download and submit the generated tif submission for the competition. Any inspection or validation to see if it is ready for submission should be done by the project without human intervention.

PARALLEL-RUN PROTOCOL — GEMS Prize (#306)
1. Stay in your lane: Each run works ONE method family. Check registry/ first; do not exceed 0.90 surface rank-correlation or 70% final 3-px dot overlap with any registered raster.
2. Shared plumbing, don't rebuild: Reuse the cached feature stack, holdout evaluator, and submission writer. Holdout = hide-and-recover: withhold whole fault segments (with buffer), derive catalogue features only from visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha=0.2, beta=0.8, 300 m triangular kernel).
3. Two score labels only: Every number must say HOLDOUT-DTI (with evaluator version, n withheld positives, 95% CI) or ORGANIZER-CONFIRMED (with submission ID). Never write a projection as a score.
4. Leakage check first: Any feature with single-feature holdout AUC > 0.90 is leakage until proven otherwise. Test each feature alone on the holdout before trusting a model.
5. Budget: Stop after at most 3 experiments or 2 hours. Keep only changes that beat the baseline in >=3/4 spatial folds or improve mean DTI with 95% CI excluding 0; otherwise report a clean negative result.
6. Output — one JSON RUN CARD at the end: hypothesis & physical mechanism, named non-fault process that could mimic it, holdout DTI + CI, correlation/overlap vs registry, raster SHA-256, validator output (no NaN in footprint, values in [0,1], CRS/shape/transform match), unique filename + <=140-char submission note, and verdict: promote | negative.

Core values:
1. Maximize P(Win): Every decision, line of code, and verification pass must serve a single overarching goal: maximizing the probability of winning the competition.
2. Own the Outcome: Take full, end-to-end ownership of the project's success. Do not stop at partial fixes or surface-level compliance; proactively identify gaps, verify from trusted sources, and drive the work all the way to a winning result.

Verify everything from official verified trusted sources with links for manual review. Flag any irregularities for review. No hallucinations. Run the task through three passes (Pass 1: Implement and verify; Pass 2: Hunt bugs, missing requirements, incorrect assumptions, edge cases; Pass 3: Re-check against original request). Create a pull request and merge it onto main.
