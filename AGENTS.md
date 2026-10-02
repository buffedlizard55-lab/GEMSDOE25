# Standing project instructions (read first, every session)

1. **Read the whole README, including the verbatim owner brief at its bottom, before doing anything.** Keep the Arena core values
   — **Maximize P(Win)** and **Own the Outcome** — as the decision rule: prefer verified scientific leverage over cosmetic work, resolve
   engineering/data blockers yourself, report negative results, and never pass an unverified claim off as done.
2. **First commands:** `git fetch origin`; compare `origin/<session branch>` with `HEAD`; `gh pr list --state open`;
   `git ls-remote --heads origin 'arena/*'`. A sibling session of the same account can run from the same base commit (it happened on
   GEMSDOE24, see its `registry/irregularities.json` IR-PARALLEL-SESSION-PR7). Read any open PR first, never push to another branch.
3. **Never automate access to drivendata.org** (leaderboard, forum, data, submission pages). Its Terms of Use forbid "any robot, spider or
   other automatic device, process or means to access the Website for any purpose, including monitoring". Leaderboard rows and scores are
   *human-read snapshots*: `scripts/record_live_score.py` records what the owner reads. The agent never uploads a submission.
   (`tests/test_repo_integrity.py` enforces that the feed script contains no DrivenData host.)
4. **Pre-register before you run** (commit the document first): design, response, analysis rule, gate. Do not tune on outcomes; a failed
   arm stays failed. Experiments are *designed* (fractional factorial), not one-factor-at-a-time hunches.
5. **No weekly slot unless the candidate beats the current comparable hide-and-recover best and passes the exact-file audit**, or the owner
   explicitly accepts a declared exception recorded in `registry/submissions.json`. Format-green is not gate-green. A holdout win is
   necessary, not sufficient (proxy-vs-live Spearman measured +0.33, n.s., on 24 artefacts by GEMSDOE24).
6. **Evidence classes stay separate:** OFFICIAL (read at the cited page), OWNER-reported score, COMPUTED (script + JSON named), INFERENCE
   (assumptions stated). Unknown stays unknown. Dates, hashes and links are recorded in `registry/`.
7. **A renamed reference is not new work.** Every shipped TIF has a unique, content-addressed name, a short DrivenData note and a
   machine-readable receipt; byte-identical copies of earlier files are labelled as such.
8. Large inputs stay out of Git; restore them with `scripts/restore_data.py` (SHA-256 pinned). Do not commit rasters except the few
   submission files in `docs/downloads/`.
9. **Review three times** before finishing: (i) implement and verify against sources, (ii) hunt bugs / assumptions / edge cases, (iii) re-read
   the original brief line by line. Keep the receipts in `registry/review_passes.json`.
10. Open a PR from the fixed session branch; merge only through GitHub and only claim a merge/deployment you can show a URL/status for.
    Never ask for credentials; if GitHub authentication fails, ask the owner to reconnect it.
