# Session review — 2026-10-29 (branch `arena/fd0738b9-gemsdoe25`)

**Decision: OK TO DOWNLOAD AND SUBMIT — NO.** No file in `docs/downloads/` is cleared, and no new candidate was generated, because none passed the holdout gate. Estimated competition score for every file: **NOT ESTIMATED** (no calibrated projection exists).

This session was a read-only review plus portal-format verification. It did not run a new experiment, did not restore the 419 MB feature cache, did not select a slot, and did not access DrivenData (AGENTS.md rule 3).

## 1. What the portal error means (verified here)

The portal message is `Predicted values must be in range [0, 1]`.

Re-reading the downloaded GeoTIFFs (`scripts/check_portal_files_2026_10_29.py` → `evidence/portal_file_recheck_2026-10-29.json`):

| File (`docs/downloads/`) | NaN cells | Finite min–max | Positive cells | Portal range check | SHA-256 (first 16) |
|---|---|---|---|---|---|
| `…h75-dchb-cg…e035d75ca5d5-nan.tif` | 7,111,787 | 0.0–1.0 | 37,654 | **FAIL** (NaN is outside [0,1]) | `11dcd970ee3a7337` |
| `…h75-dchb-cg…e035d75ca5d5-zeros.tif` | 0 | 0.0–1.0 | 37,654 | pass | `da94fdf9d744f06f` |
| `…h79-cthm…e7ad8a4bf3ed-nan.tif` | 7,111,787 | 0.0–1.0 | 37,654 | **FAIL** | `f9167cc515cce613` |
| `…h79-cthm…e7ad8a4bf3ed-zeros.tif` | 0 | 0.0–1.0 | 37,654 | pass | `df13471fe77d6eb6` |
| `…h36-spigm…3937b96ce366-nan.tif` | 7,111,787 | 0.0–1.0 | 37,654 | **FAIL** | `c103482fb70b4eb4` |
| `…h36-spigm…3937b96ce366-zeros.tif` | 0 | 0.0–1.0 | 37,654 | pass | `182f9e5f03cb6603` |

All six share EPSG 32611, shape 3730×3292, float32, and 1 band.

**Mechanism (inference, consistent with the data):** a NaN-outside file fails any whole-array `0 <= x <= 1` test because NaN fails every comparison. The zeros-outside twin passes. The organizer's exact validator has **not** been read, so this is the most likely cause, not a confirmed one.

**Do not infer that the zeros file is submit-ready.** Passing the format check is not a gate. The zeros-outside files still fail the lane and holdout gates described in §3.

## 2. Test and reproduction status

- `pytest tests` in a fresh venv (Python 3.11.2, `requirements.txt`): **538 passed, 15 skipped**. Every skip names a missing input (competition template, scored rasters, owner mirrors, or the shared work cache).
- `git ls-remote`: local `main` and `origin/main` both at `ca851a8`. The session branch did not exist on the remote before this session.
- Open PRs before this session: #65 (`arena/5705fa30-gemsdoe25`) and #47 (`arena/198fa53f-gemsdoe25`). Neither is this session's branch.

## 3. Gate status (why nothing is cleared)

Taken from `README.md`, `AGENTS.md`, and `knowledge/47_repo_review_2026-10-28.md`:

1. **Holdout gate:** no candidate beat the same-run comparator on the pooled-DTI holdout. The latest result, H81 (`H81_JUNC_CG`), scored HOLDOUT-DTI 0.111126 against 0.121443 for `CTRL_BLIND_ABCD` (paired gain −0.010317, 95% CI [−0.012437, −0.006948], 95,188 withheld-positive occurrences; evaluator `gems25.metric.dti_binary`, alpha 0.2, beta 0.8, 300 m triangular kernel). It failed.
2. **Lane gate (r13):** at 37,654 dots, at least **82.70%** of dots must lie within 3 px of registry raster r13. The literal 70% cap is reachable only at ≤ 21,713 dots (`evidence/lane_bound_r13_2026-10-28.json`). The literal rule and the scoring objective conflict. This is an owner decision.
3. **Lineage:** the 0.2778 GEMSDOE32 B2 file is a pruned subset of the 0.2708 h27-4 raster (37,654 dots vs 40,199; Jaccard 0.9367), per `evidence/nine_site_top_files_2026-10-28.json`. It is a previous submission and may not be copied.

## 4. The 0.2778 question — what the repo can and cannot say

- **Owner-reported, not organizer-confirmed:** GEMSDOE32, `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, 0.2778 (`docs/data/live_scores.json`, `group_best_public_dti_claim`, status "user/owner-reported claim").
- **Lineage is recorded, not re-derived here:** the parent raster is not stored in this checkout (`docs/downloads/` has no `h33` file). The lineage claim rests on the earlier audit in `evidence/nine_site_top_files_2026-10-28.json`, which needs the owner mirrors to recompute (test skipped in this sandbox).
- **Why it may score higher than its parent (hypothesis, not proof):** it removes 2,545 dots that lie within 2 px of labelled catalogue pixels, and it puts 0 dots within 2 px of the catalogue. Two mechanisms fit this, and the repo cannot separate them: (a) removing near-known false positives helps; (b) corrections near known faults earn credit that the deletion removes. `knowledge/48` does not decide between them. See `knowledge/47` §"What the 0.2778 result does and does not show".

## 5. Leaderboard numbers — conflict flagged

| Claim | Value | Source | Status |
|---|---|---|---|
| "Current leaderboard high score" (owner prompt) | 0.4413 (participant DARD) | owner prompt; `docs/data/live_scores.json` `best_public_dti_latest_claim` | OWNER-REPORTED |
| Leaderboard snapshot rank 1 | 0.3195 (participant DARD, 12 submissions) | `docs/data/live_scores.json` `leaderboard_snapshot.top10` | Human-read snapshot, not organizer-confirmed |
| Group high score claimed | 0.2778 (GEMSDOE32 B2) | owner prompt | OWNER-REPORTED |

**IRREGULARITY IR-29-LEADERBOARD-CONFLICT:** the same participant (DARD) appears at 0.4413 (claim) and 0.3195 (snapshot). One of these is stale or mis-transcribed. The owner should read the leaderboard by hand and record the value, with the timestamp, in `registry/live_scores.json`. The agent did not fetch the leaderboard (AGENTS.md rule 3).

## 6. Candidate hypotheses (requested before implementation)

No new hypothesis was implemented, and none was holdout-tested. `knowledge/47` already ranks four proposals. The layer names below were checked against the code (`det_elev`, `det_elev_slope`, `cond_surf`, `depth_to_base_surf`, `coh100`, `step_max`, `strike` all appear in `src/` or `scripts/`). Expected DTI benefit is **unknown** until measured.

| Rank | Hypothesis | Layers | Physical signature | Non-fault mimic | Difference from repo | Cost | Status |
|---|---|---|---|---|---|---|---|
| 1 | Cross-drainage profile-offset consensus | `det_elev`, `det_elev_slope`, LiDAR `step_max`, `coh100`, `strike` | same-sense offsets in ≥3 drainage profiles | resistant ledges, fan incision, Lahontan shorelines | `knowledge/03` line 71 lists the same drainage-offset / knickpoint concordance idea (H24-6, carried from GEMSDOE24). No fitted result was found in the repo. Novelty across sibling repos is unverified | high | Not validated; shared cache absent in this checkout |
| 2 | Depth-resolved MT vertical coherence | `cond_surf`, `depth_to_base_surf`, gravity/magnetic structure | shallow conductivity edge connected to a deeper conductor | graphitic bedrock, playa brine | Repo has only the single surface conductivity map | high | **Blocked:** GDR submission 1391 was not fetched (not on the outbound allowlist); depth data availability unverified |
| 3 | Focal-mechanism stress test | USGS ComCat focal mechanisms, plus structural orientation | small-event mechanism consistent with fault-plane orientation | quarry blasts, volcano-tectonic swarms | Competition channels are derived proxies, not mechanism vectors | high | **Blocked:** ComCat not fetched (not on the outbound allowlist) |
| 4 | InSAR deformation-gradient lineaments | NASA/JPL ARIA Sentinel-1 products, `cond_surf` as corroborator | persistent linear displacement gradient across independent interferograms | pumping, seasonal soil moisture, decorrelation seams | Repo's geodetic channels are smooth scalars, not displacement series | very high | **Blocked:** ARIA not fetched; coverage unverified |

Official sources for these candidates, not fetched in this session and listed for manual review: [GDR submission 1391](https://gdr.openei.org/submissions/1391), [USGS ComCat](https://earthquake.usgs.gov/data/comcat/), [NASA/JPL ARIA](https://aria.jpl.nasa.gov/), [GeoDAWN USGS data page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [EPSG:32611](https://epsg.io/32611).

## 7. Irregularities flagged for review

- **IR-29-LEADERBOARD-CONFLICT:** 0.4413 claim vs 0.3195 snapshot for the same participant (§5).
- **IR-29-NAN-DEFAULT-DOWNLOAD:** `REVIEW_2026-10-28.md` §3 records that some front-page links still point to NaN-outside files, which the portal rejects. Not re-checked page by page this session; the README's top section now links zeros-outside files. Needs a page-by-page audit.
- **IR-29-NINE-SITE-SCORES-OWNER-ONLY:** every score for the nine focus sites is OWNER-REPORTED. None is ORGANIZER-CONFIRMED.
- **IR-29-LANE-RULE-UNSATISFIABLE-AT-BUDGET:** the 70% r13 rule cannot be met at 37,654 dots (82.70% minimum). This is an owner decision, not something to engineer around.
- **IR-29-ZEROS-NOT-ORGANIZER-CONFIRMED:** the zeros-outside file passes the range check, but the organizer's exact acceptance rule has not been read. Do not treat format-pass as submit approval.
- **Earlier open items (not changed here):** `registry/irregularities.json` still lists open entries, including IR-25-PROVENANCE, IR-25-LIVE-MODEL-SCOPE, IR-26-LANE-BUDGET-CONFLICT, and IR-28-GENERATOR-DRIFT.
- **IR-28-GENERATOR-DRIFT (still open):** `scripts/build_readme.py`, `build_site.py`, and `build_current_review.py` do not reproduce the hand-edited README sections. This session edited the README by hand and did not run any generator.

## 8. Limitations and what is needed

1. **DrivenData access:** the sandbox cannot log in, and the agent is not allowed to automate access. The owner must read the leaderboard and submission page and record receipts.
2. **Network allowlist:** only `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, and `files.pythonhosted.org` are reachable. GDR, USGS, and NASA/JPL are not, so no external-data candidate can be tested from here.
3. **Shared cache:** `data/` is empty in this checkout. The holdout pipeline needs `scripts/restore_data.py --group core`, and the core group's pinned mirrors must be re-verified before use.
4. **Comparator drift:** AGENTS.md rule 5 says a frozen comparator from an earlier session is not a baseline. Any new test must recompute the comparator in the same run.

## 9. Next steps (in order)

1. Owner reads the DrivenData leaderboard by hand and records the top value, with timestamp, in `registry/live_scores.json` (resolves IR-29-LEADERBOARD-CONFLICT).
2. Owner confirms the accepted format from the submission-page text or an organizer reply (resolves IR-29-ZEROS-NOT-ORGANIZER-CONFIRMED).
3. Owner decides the lane rule for r13 at the chosen dot count (IR-29-LANE-RULE-UNSATISFIABLE-AT-BUDGET).
4. Agent restores the core cache with `scripts/restore_data.py --group core`, re-verifies the hashes, and recomputes the 0.2778-family lineage (this closes the lineage gap in §4). Do not run the README/site generators first (IR-28-GENERATOR-DRIFT).
5. Pre-register one candidate from §6 rank 1 before running it, then run the 3-experiment / 2-hour budget. Promotion remains a separate selector step.

## 10. Run card

```json
{
  "date": "2026-10-29",
  "hypothesis": "No new hypothesis tested. Review-only: verify portal format of existing downloads and document gates.",
  "mechanism": "NaN-outside GeoTIFFs fail the whole-array [0,1] range check; zeros-outside twins pass. Mechanism is inferred from the data, not read from the organizer validator.",
  "named_non_fault_mimic": "not applicable (no new signal tested)",
  "holdout_dti": "NOT COMPUTED in this session (no experiment run)",
  "correlation_overlap_vs_registry": "NOT COMPUTED in this session; prior r13 lane result stands (82.70% minimum overlap at 37,654 dots)",
  "raster_sha256": {
    "h75_zeros": "da94fdf9d744f06f… (first 16 hex chars)",
    "h79_zeros": "df13471fe77d6eb6…",
    "h36_zeros": "182f9e5f03cb6603…"
  },
  "validator_output": "evidence/portal_file_recheck_2026-10-29.json: NaN cells 0 for zeros files, 7,111,787 for NaN files; finite values in [0,1]; EPSG 32611; shape 3730x3292; float32 single band",
  "submission_name": "none (no submission)",
  "submission_note": "none",
  "verdict": "negative",
  "ok_to_download_and_submit": false,
  "estimated_competition_score": "NOT ESTIMATED"
}
```

## 11. Review passes

1. **Implementation pass:** read `README.md`, `AGENTS.md`, `knowledge/47`, `docs/data/live_scores.json`, and the registry. Installed dependencies and ran the test suite (538 passed, 15 skipped). Wrote and ran `scripts/check_portal_files_2026_10_29.py`.
2. **Bug and assumption pass:** checked the new script's logic. NaN is counted directly from the pixel array; the `nodata` tag is recorded only as information (the zeros files carry no nodata tag, the NaN files tag NaN). No bug was found in this pass. The one assumption (that NaN causes the portal error) is labelled as inference in §1.
3. **Original-request pass:** each request in the owner prompt was checked against this review (§§1–9). Not done: a new unique TIF that clears all gates; the 0.4413 score is not verified; the hypotheses are not holdout-tested; the full prompt is stored in normalized form (see `README.md`).

Sources not fetched in this session (outbound allowlist): DrivenData pages (automation forbidden by AGENTS.md rule 3), GDR, USGS ComCat, NASA/JPL ARIA, epsg.io. Every number above comes from a local file or a command output shown in this session.
