# Session review — 2026-10-29 (branch `arena/f486e4e3-gemsdoe25`)

**Decision: OK TO DOWNLOAD AND SUBMIT — NO, for every file in this repository and for every file on the nine focus sites.**
No new TIF was generated. Reason in one line: a new file built from the 0.2708 / 0.2778 lineage is a near-duplicate of a previous submission (Jaccard ≥ 0.93) and sits in the r13 lane (≥ 82.7% overlap at 37,654 dots, 99.92% for B2 itself). Under the lane protocol that is a duplicate, and no candidate has passed the holdout gate. Every number below is labelled: **COMPUTED** (script + receipt), **OFFICIAL** (read at the cited page), **OWNER-REPORTED** (a score the owner supplied), or **INFERENCE** (stated assumption).

## 0. Read first

| Question | Answer | Label |
|---|---|---|
| Is any file cleared to download and submit? | **No.** | Repo rule, `AGENTS.md` §5 |
| Estimated competition score for any new file? | **NOT ESTIMATED.** No calibrated projection exists. | Repo rule |
| Why does the portal say "Predicted values must be in range [0, 1]"? | A NaN-outside GeoTIFF fails a whole-array 0 ≤ x ≤ 1 test. Zeros-outside twins pass the range check. The organizer's validator text has not been read. | INFERENCE, consistent with `evidence/portal_safety_sweep_2026-10-29.json` |
| Did the GEMSDOE32 0.2778 claim get verified? | **Lineage: yes, from bytes. Score: no.** The 0.2778 score is an owner claim, not an organizer receipt. | COMPUTED (lineage) / OWNER-REPORTED (score) |

## 1. Official facts (read this session)

Source: DOE GEMS Prize Official Rules, September 2026, [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf). Read at sections 1.1, 3.2, 3.4, 3.5, 3.6.1 and 3.6.2.

- Submission is **a single GeoTIFF with a single raster layer at 100 m resolution** covering the whole GeoDAWN study area (§3.2).
- Up to **three submissions per week** (§3.2, §3.4).
- Scoring is a **distance-weighted Tversky index that penalizes false negatives more than false positives** (§3.6.1). The kernel and weights are "published on the competition website", which is login-walled. Their values are **not** in the official rules text.
- Phase 1 is scored on a **withheld** part of the new fault labels. Phase 2 is scored on an **expert-revised** full label set (§1.1, §3.6.2).
- You must pick **one** final submission before the deadline. The choice must be made without knowledge of private-set scores (§3.6.2).
- The narrative must **disclose the extent and manner of generative-AI use** (§3.2). See IR-29-AI-DISCLOSURE-REQUIRED.

Source: [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution), notebook `unet-mc-cv-reference-solution.ipynb` (contents-API blob `d45bf7bd…`). Read this session: its loss uses `alpha = 0.2` and `beta = 0.8`, matching the project's DTI weights. The repo contains **no scoring code**.

**Not verified this session:** the 300 m triangular kernel. The project's own docs record it from a DrivenData staff reply (`knowledge/06`, lines 34–35). The official rules do not state it. See IR-29-OFFICIAL-METRIC-NOT-READ.

## 2. The 0.2778 file — what was verified from bytes

Owner mirror: `buffedlizard55-lab/GEMSDOE32` at commit `0ffda7162e76…`, file `docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`, sha256 `c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`. Its own audit receipt, `…-audit.json`, records the same sha256.

Parent: `buffedlizard55-lab/GEMSDOE28` at commit `a1c0e18f4a4f…`, file `gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif`, sha256 `ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73`.

Catalogue: `existing_faults.tif` (restored from the pinned core group), sha256 `7ba308ccdc44…`. Its hash is identical to `labels.tif`.

Receipt: [`evidence/b2_lineage_recheck_2026-10-29.json`](../evidence/b2_lineage_recheck_2026-10-29.json), produced by `scripts/recheck_b2_lineage.py`.

| Check (COMPUTED) | Result |
|---|---|
| B2 dots | **37,654** (matches owner audit) |
| Parent (h27-4) dots | **40,199** |
| B2 ⊂ parent (no dot added) | **Yes** (0 added, 2,545 removed) |
| Jaccard(B2, parent) | **0.93669** |
| Max catalogue distance of a removed dot | **2.0 px** (200 m at 100 m pixels) |
| Removed dots within 2 px of catalogue | **2,545 of 2,545** |
| B2 dots within 2 px of catalogue | **0** |
| B2 dots on catalogue pixels | **0** |
| B2 dots within 3 px of r13 (registry lane raster) | **37,622 of 37,654 = 99.92%** |
| Parent dots within 3 px of r13 | **40,166 of 40,199 = 99.92%** |

The test `tests/test_nine_site_2026_10_28.py::test_recomputed_b2_subset_matches_receipt_when_mirrors_restored` previously skipped in every checkout. It now runs from pinned bytes: **8 passed** in the nine-site module.

## 3. Why did 0.2778 score highest? (PhD-level reading, labelled)

**What changed:** the 0.2708 parent was pruned. 2,545 dots were removed, all of them within 1–2 px of a known catalogue fault. No dot was added. The pruning is the whole difference, so the question is what the pruning does to the Tversky index.

**Mechanism (INFERENCE, not measured):** DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w + ε) (formula as recorded in `knowledge/06`). A removed dot does one of two things:
1. If it was a false positive, removing it lowers the FP term by 0.2 per unit weight and costs no TP credit. This is a gain.
2. If it was a true positive (a truth fault within the kernel radius), removing it costs credit. Its neighbours may still cover the truth through the max-over-kernel rule, but that is not guaranteed.

A net +0.0070 on the owner's public split means case 1 outweighed case 2 there. Because the 300 m kernel is a repo assumption (IR-29-OFFICIAL-METRIC-NOT-READ), the sign of this result depends on that assumption.

**The non-fault mimic that could fake this gain:** the new truth may lie within 300 m of known traces. Staff said so, as recorded in `knowledge/06` (not re-read this session). If so, pruning near the catalogue deletes true positives and the 0.2778 would fall on the private split.

**Strength of evidence:** one public split, one owner-reported number, no confidence interval, no repeated draw, and no organizer receipt. The public-to-private change is unknown (§3.6.1). A 0.007 difference on one split is not evidence of a better detector. It is evidence of a better trade-off on one split, and that is all it claims.

**Judgement:** the 0.2778 is the highest owner-reported score among the nine focus sites. It was achieved by a targeted prune of the lineage, not by a new detector. It is a previous submission and cannot be re-submitted as unique.

## 4. Can we beat 0.2778?

**Not demonstrated. Nothing in this session tested it.**

Routes that are principled (none run here):
1. **Catalogue-aware prune radius, with holdout.** Pre-register a sweep of prune radius (1, 2, 3 px) and a holdout that withholds whole catalogue segments with a buffer. Recompute the catalogue-derived pruning from visible faults only (AGENTS.md §4 and holdout design). This is the first experiment that could separate mechanism 1 from mechanism 2.
2. **Pruning under the lane rule.** Any prune of the 0.2708 lineage remains ≥ 99% r13 overlap. A lane-clean file would need a different detector, which the owner must authorise (IR-29-B2-LANE-VIOLATION-TOP-FILE).
3. **Metric check before any new score.** Read the official kernel and masking rule by hand (IR-29-OFFICIAL-METRIC-NOT-READ). Until then the holdout DTI is a local number.

Budget note: a pre-registered holdout run needs `data/` restored (done this session for core, scored and owner_mirror groups) and roughly one session of compute. It was not started, because the owner's rules require the design and the lane decision first.

## 5. The estimate table (required by the owner brief)

Every file below stays **NOT ESTIMATED**. Scores listed are owner-reported previous submissions, not projections. "Unique" means not a byte-identical or dot-set-identical copy of a previous submission. "Lane" means the r13 protocol result.

| Rank | File (where it lives) | Owner-reported score | Estimate for a new submission | Unique vs focus sites? | Lane (r13 ≤ 70%?) | OK to download & submit? |
|---|---|---|---|---|---|---|
| 1 | GEMSDOE32 B2 `…e5eb6e7e-zeros.tif` (owner repo, not in `docs/downloads/`) | 0.2778 | NOT ESTIMATED | **No** — prune of the GEMSDOE28 h27-4 raster (Jaccard 0.9367); it is itself a previous submission | **FAIL** (99.92%) | **NO** |
| 2 | GEMSDOE28 h27-4 r1 `…8acb75e1f2cc-nan.tif` | 0.2708 | NOT ESTIMATED | No — parent of B2; its R1 is recorded as identical to GEMSDOE31 in the README (not re-checked here) | FAIL (99.92%) | **NO** (NaN-outside also fails portal) |
| 3 | GEMSDOE36 anderson-geothermal-pinn `…9b9ea4e6-zeros` | 0.2750 | NOT ESTIMATED | Not checked this session (owner mirror not restored) | not checked | **NO** |
| 4 | GEMSDOE28 h36-1-rung30-blind-r1 `…b531dae0a36f-nan` | 0.2710 | NOT ESTIMATED | Not checked this session | not checked | **NO** |
| 5 | Any file in `docs/downloads/` (62 GeoTIFFs; 32 portal-safe) | none | NOT ESTIMATED | Not cleared (`knowledge/48`, §3) | not cleared | **NO** |

Rows 3–4 are listed because they are owner-reported near-top scores. Their uniqueness and lane status were not checked this session, and the table does not claim either.

## 6. Leaderboard conflict (unchanged, still open)

| Claim | Value | Source | Status |
|---|---|---|---|
| Owner prompt: current GEMSDOE high score | 0.4413 | owner prompt; `docs/data/live_scores.json` | OWNER-REPORTED |
| Snapshot: rank 1 | 0.3195 (DARD, 12 submissions) | `docs/data/live_scores.json` `leaderboard_snapshot` | Human-read snapshot |

**IR-29-LEADERBOARD-CONFLICT remains open.** The agent did not read the DrivenData leaderboard (`AGENTS.md` §3). The owner must read it and record the value and timestamp in `registry/live_scores.json`.

## 7. Verification log (what was run, with outcomes)

| Step | Command | Outcome |
|---|---|---|
| Fresh venv, `requirements.txt` | `python3 -m venv /tmp/gemsvenv && pip install -r requirements.txt` | Installed |
| Full test suite, before edits | `pytest -q` | 547 passed, 15 skipped |
| Lint | `ruff check src scripts tests` | All checks passed |
| Core restore (hash-pinned) | `scripts/restore_data.py --group core` | 4 files verified |
| Scored restore | `scripts/restore_data.py --group scored` | 11 files verified |
| Portal sweep, re-run to `/tmp` | `check_file` over `docs/downloads/*.tif` | 62 total, 32 portal-safe, 30 rejected, 0 other hard failures (matches `evidence/portal_safety_sweep_2026-10-29.json`) |
| r13 bound arithmetic | 6,514 eligible pixels ÷ 0.30 = 21,713; 1 − 6,514/37,654 = 0.827 | Matches `evidence/lane_bound_r13_2026-10-28.json` |
| Owner-mirror restore, from scratch (new group) | move `data/owner_mirrors` aside, `restore_data.py --group owner_mirror` | 2 files restored, both sha256 match |
| Lineage test | `pytest tests/test_nine_site_2026_10_28.py` | 8 passed (previously skipped) |
| Lineage receipt | `scripts/recheck_b2_lineage.py` | `evidence/b2_lineage_recheck_2026-10-29.json` written |
| Full suite, after edits | `pytest -q` | 559 passed, 3 skipped |
| Lint, after edits | `ruff check src scripts tests` | All checks passed |

## 8. Irregularities (all in `registry/irregularities.json`)

- **IR-29-B2-LANE-VIOLATION-TOP-FILE** (high, open): the top file fails the literal lane rule at 99.92%.
- **IR-29-OFFICIAL-METRIC-NOT-READ** (medium, open): the 300 m kernel and masking rule are not in the official text. The organizer metric page is login-walled.
- **IR-29-AI-DISCLOSURE-REQUIRED** (medium, open): official §3.2 requires an AI-use statement in the narrative.
- **IR-29-OWNER-MIRROR-NOT-IN-MANIFEST** (low, fixed): the lineage check now has pinned inputs.
- **IR-29-LEADERBOARD-CONFLICT** (from `knowledge/48`, open): 0.4413 vs 0.3195.
- **IR-29-ZEROS-NOT-ORGANIZER-CONFIRMED** (from `knowledge/48`, open): the organizer's validator text has not been read.

## 9. The owner brief in the README

The README holds a normalized summary of the owner brief, not the verbatim text (`knowledge/48`). The verbatim text is about 25,000 characters and was not copied by hand, because a hand copy at that length risks a transcription error, which the owner's rules forbid. **Open item:** the owner should either paste the verbatim brief into `registry/owner_brief_verbatim.md` or confirm that the normalized version is accepted.

## 10. Next steps (in order)

1. **Owner:** read the DrivenData leaderboard and record the top value (resolves the 0.4413 / 0.3195 conflict).
2. **Owner:** read the metric page and record the kernel radius, weights and masking rule verbatim (resolves IR-29-OFFICIAL-METRIC-NOT-READ).
3. **Owner:** decide the lane rule for an already-scored lineage (IR-29-B2-LANE-VIOLATION-TOP-FILE). This decides whether any 0.2708-family file can be considered at all.
4. **Owner:** review `AI_DISCLOSURE.md` against official §3.2 (IR-29-AI-DISCLOSURE-REQUIRED).
5. **Agent (after steps 2–3):** pre-register a catalogue-aware prune-radius experiment with a catalogue-holdout, run it within the 3-experiment / 2-hour budget, and report the result as HOLDOUT-DTI with an evaluator version, withheld-positive count and 95% CI. Promotion stays a separate selector step.

## 11. Run card

```json
{
  "date": "2026-10-29",
  "branch": "arena/f486e4e3-gemsdoe25",
  "hypothesis": "Lineage review only: verify the GEMSDOE32 B2 (0.2778, owner-reported) parent relation from bytes, and check the lane and portal gates. No new candidate.",
  "mechanism": "B2 = h27-4 minus 2,545 dots within 2 px of the catalogue. Net effect on DTI is an untested trade-off (INFERENCE).",
  "named_non_fault_mimic": "New truth lying within 300 m of known traces (staff statement recorded in knowledge/06, not re-read); pruning would then delete true positives.",
  "holdout_dti": "NOT COMPUTED. No pre-registered holdout run this session.",
  "correlation_overlap_vs_registry": "B2 vs r13: 99.92% of dots within 3 px (lane FAIL vs 70%). Parent: 99.92%. Rank correlation not computed.",
  "raster_sha256": {
    "B2_zeros_owner_mirror": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "h27_4_parent_nan_owner_mirror": "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
    "existing_faults_catalogue": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
  },
  "validator_output": "Portal sweep (62 TIFs): 32 portal-safe, 30 rejected by the [0,1] finite check, 0 other hard failures. B2 lineage receipt: subset true, 0 added, 2,545 removed, Jaccard 0.93669.",
  "submission_name": "none",
  "submission_note": "none",
  "verdict": "negative",
  "ok_to_download_and_submit": false,
  "estimated_competition_score": "NOT ESTIMATED"
}
```

## 12. Review passes

1. **Implement and verify.** Installed, tested, linted, restored the core and scored groups, re-ran the portal sweep, and restored the owner-mirror lineage inputs from their public owner repos. Wrote `scripts/recheck_b2_lineage.py` and added the owner-mirror manifest group.
2. **Bugs, assumptions, edge cases.** Checked the catalogue choice (`existing_faults.tif`, which equals `labels.tif` by hash), the 2-px distance convention (100 m pixels), and the `nan_to_num > 0` mask convention. Found one overstatement in the first draft: the "mechanism" paragraph reads as a finding but is labelled INFERENCE. The manifest rewrite reformatted the whole file, so it was reverted and redone as a minimal insertion.
3. **Original request, line by line.** Checked against the owner brief. Delivered: official-source facts with links; the 0.2778 lineage verified from bytes; the 0.2778 mechanism; the "beat 0.2778" routes; the estimate table with NOT ESTIMATED; the leaderboard conflict flagged; the irregularities; the run card. Not delivered: a new unique TIF (blocked, see §0); a verbatim brief in the README (§9); a leaderboard read (`AGENTS.md` §3).

Receipts: `registry/review_passes_session_f486e4e3_2026-10-29.json`.
