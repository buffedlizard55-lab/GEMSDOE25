# Repository review, verified — 29 October 2026 (session branch arena/87a0b9a8-gemsdoe25)

**Decision: nothing in this repository is cleared. OK to download and submit: NO. Estimated score: NOT ESTIMATED.**
No new GeoTIFF was generated, no holdout was run for a new candidate, and no weekly slot was used. The reasons are below.

Evidence classes used here: **COMPUTED** (a script in this repo, output file named), **OWNER-REPORTED** (a score a user or owner wrote down; not an organizer receipt), **OFFICIAL** (read at the cited page this session), **INFERENCE** (stated assumption). Nothing in this file is an organizer score.

## 1. What was checked, and how

| Check | Command or source | Result |
|---|---|---|
| Branch base | `git rev-parse origin/main`, `git ls-remote --heads origin main` | `main` = `2bd14f28f32603da8dffedf3396c12231371f180`; session branch identical at start. Not `b55a246` as stated in `REVIEW_2026-10-29.md`. |
| Open PRs | `gh pr list --state open` | #65 (`arena/5705fa30-gemsdoe25`, CBEC negative holdout and H78 quarantine) and #47 (`arena/198fa53f-gemsdoe25`, focus-site duplicates) are both open. Both touch README/index pages. |
| Dependencies | `pip install -r requirements.txt` into a venv | Installed (numpy 2.4.6, rasterio 1.4.4). |
| Lint (CI step) | `python -m ruff check src scripts tests` | All checks passed. |
| Tests, no data | `python -m pytest -q` | 547 passed, 15 skipped (competition inputs absent). |
| Restore core inputs | `scripts/restore_data.py --group core` | Restored and SHA-256 verified: `training_features.tif`, `labels.tif`, `existing_faults.tif`, `sample_submission.tif`. |
| Restore external + scored | `scripts/restore_data.py --group external`, `--group scored` | 7 + 11 files verified. |
| Tests, with owner mirrors | `python -m pytest -q` | **559 passed, 3 skipped.** The lineage test now runs. The 3 skips need competition band rasters or a shared work cache (see §7). |
| Portal range check, all checked-in TIFs | `rasterio` over `docs/downloads/*.tif` (62 files) | 32 pass, 30 fail. Every failure is a NaN-outside file with 7,111,787 non-finite cells. Zeros-outside twins pass. |
| Owner mirrors | `scripts/fetch_owner_mirrors.py` (new) — 8 files from public `buffedlizard55-lab/GEMSDOE*` repos via `api.github.com` | Each SHA-256 matches its pin in `evidence/nine_site_top_files_2026-10-28.json`. |
| Nine-site audit reproduction | `scripts/audit_nine_site_top_files.py` | Reproduces the checked-in evidence exactly, apart from `generated_utc`. |
| Label identity | `scripts/audit_label_identity.py` (new) | `labels.tif` and `existing_faults.tif` are byte-identical. `sample_submission.tif` has the same 60,988 ones as `labels.tif`. See §3. |
| Generator safety | ran `build_readme.py` and `build_site.py` on this branch, then reverted | They rewrote hand-maintained sections (the 29 October "Read first" section and the 29 October front-page banner). Reverted with `git checkout`. See §4. |

## 2. The 0.2778 question: what the bytes show

Sources (owner public repos; hashes match the pins):
- B2 0.2778 (`GEMSDOE32`): <https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif>, SHA-256 `c55bafc4…`
- H27-4 0.2708 (`GEMSDOE28`): <https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif>, SHA-256 `ab023001…`
- D2.8 0.2600 (`GEMSDOE25` file, same dot set as `GEMSDOE30`): <https://github.com/buffedlizard55-lab/GEMSDOE25/blob/main/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif>, SHA-256 `91eae1ca…` (hashed this session)

| Raster | Dots (>0, finite) | Subset of the next-larger raster? | Dots removed | Removed dots' distance to labelled catalogue |
|---|---:|---|---:|---|
| D2.8 | 44,090 | — | — | 6,436 within 2 px; 3,891 within 1 px |
| H27-4 | 40,199 | yes, of D2.8 | 3,891 | all 3,891 at distance 1 px (H27-4 has none within 1 px) |
| B2 | 37,654 | yes, of H27-4 | 2,545 | all 2,545 within 2 px (B2 has none within 2 px) |

Jaccard B2 vs H27-4 = 0.936690; H27-4 vs D2.8 = 0.911749. CRS EPSG:32611, shape 3730×3292, transform `(100, 0, 243350; 0, −100, 4508550)` for all three, matching the restored template.

**What this establishes (COMPUTED):** the 0.2778 file is an exact nested pruning of the 0.2708 file, which is an exact nested pruning of the 0.2600 file. Each step removed only dots that sit next to the labelled catalogue. The owner-reported scores rose at each step.

**What it does not establish:** why the organizer's score rose. Three points from one owner's uploads are not a dose–response curve. Scores are OWNER-REPORTED, not organizer receipts.

**INFERENCE (not proven):** the direction is hard to reconcile with `labels.tif` being the scored target. If the scored target equalled the catalogue, removing catalogue-adjacent dots should lower the score. The owner-reported direction is the opposite. That points toward either (a) the scorer discounting known faults, or (b) the mirrored `labels.tif` not being the scored target. Only an organizer-side receipt can separate these (see §3 and §6).

## 3. Irregularity raised as critical: labels equal the catalogue

COMPUTED on the restored bytes (`evidence/label_identity_audit_2026-10-29.json`):
- `labels.tif` and `existing_faults.tif`: identical SHA-256 `7ba308cc…`; arrays equal; 60,988 positives each.
- `sample_submission.tif`: 5,167,373 finite cells (the footprint); exactly 60,988 ones; the ones match `labels.tif` pixel for pixel.

`knowledge/08_data_dictionary_2026-10-02.md` already records the byte-identity but does not flag it as a risk. It is now registered as **IR-29-LABELS-EQUALS-CATALOGUE (critical, open)**.

Why it matters: if the organizer's inputs really coincide, the "catalogue" and the "target" are the same, and every catalogue-based holdout (hide-and-recover, DTI, catalogue-distance results) is suspect. If the owner mirror copied one file over another, the holdout may be fine. The repo cannot decide which, and the organizer data page is login-walled and must not be automated. **A human owner must read that page and record what it says.**

## 4. Irregularity: the generators are unsafe on this branch

`IR-28-GENERATOR-DRIFT` is still open. I ran `scripts/build_readme.py` and `scripts/build_site.py` to test whether they reproduce the committed pages. They do not. The rebuilt README dropped the 29 October "Read first" standing rules and the 29 October decision section, and the rebuilt front page reverted to 28 October content. I reverted all generator output (`git checkout`). Nothing was published from the rebuilt output.

Consequence: front-page and README edits are hand-made on this branch. A future automated rebuild would silently delete the current decision record.

## 5. Other irregularities (registered in `registry/irregularities.json`)

- **IR-29-GEMSDOE25-FILE-LABEL (medium):** the evidence row and older tables name the GEMSDOE25 file `gems24-h25-1-dotted-…-d2-8…`. The GEMSDOE25 repo hosts `gems25-dotted-…-d2-8…-nan.tif` (same bytes). The GEMSDOE25 repo also hosts a zeros-outside twin with the same dots. That twin passes the format check but is a copy of an already-scored dot set. It is not a new submission.
- **IR-29-FRONTPAGE-DOWNLOAD-OF-INVALID-DIAGNOSTIC (medium):** the front page offers the 29 October mag/radiometric-decoupling raster as "download for inspection: YES", while the same page records its holdout as invalid (0.00000 from contaminated placement). The owner should decide whether that stays on the front page.
- **IR-29-REVIEW-STALE-FACTS (low, fixed here):** `REVIEW_2026-10-29.md` cites a different commit and says tests could not run. See the correction note appended to that file.
- **IR-29-OWNER-MIRROR-RESTORE-GAP (low, fixed here):** the nine-site lineage test skipped because no committed script populated `data/owner_mirrors`. Fixed by `scripts/fetch_owner_mirrors.py`.
- **IR-29-B2-LINEAGE-REPRODUCED (info, verified):** the lineage claim in §2 is reproduced from bytes.
- **Stale README count (fixed here):** the README said 60 GeoTIFFs with 30 NaN-outside. The current count is 62, with 30 NaN-outside.
- **IR-29-LEADERBOARD-CONFLICT (open, existing):** the prompt gives 0.4413 and 0.3195 as the top score. Neither is verified here.

## 6. Can we beat 0.2778? Current answer: not demonstrated, and not by a new file this session

1. **Pruning further is closed by the project's own lane rule.** Any subset of a registered raster has 100% of its dots within 3 px of that raster's dots. B2 is a registered top-scorer (`registry/top_scorer_sources.json`), so any further pruning of B2 is an automatic lane duplicate (rule: more than 70% within 3 px). The same holds for any subset of H27-4 or D2.8.
2. **Any new mechanism has to be validated before it is submitted.** A holdout score needs the labels question (§3) resolved first. A holdout built on possibly-coincident inputs cannot certify a score.
3. **No other candidate has a holdout result on the restored inputs.** No new experiment was run this session. The protocol allows up to three, but none is justified until the labels question (§3) is settled, and no candidate has passed a gate.

So the honest answer to "can we exceed 0.2778?" is **unknown**. The only evidence-backed direction (drop catalogue-adjacent dots) is closed by the lane rule for any direct descendant of B2. A higher score would need a different mechanism, validated on a holdout whose inputs are first confirmed.

## 7. Limitations: what I could not check

- **Not reachable from this sandbox:** DrivenData pages (forbidden by the standing policy), `docs.nlr.gov` (the submission-format PDF; not on the allowed-host list), `gdr.openei.org` (GDR 1391; not on the allowed-host list). The format claims therefore rest on the owner's notes plus the repo's own `scripts/` checks, not on the organizer's text.
- **The leaderboard and the submission page** were not read. Every score in this repo is OWNER-REPORTED.
- **The 3 remaining skipped tests** need the competition band rasters (`test_h36_spigm`, `test_h81_fhj`) or a populated shared work cache (`test_h75_dchb`, `data/work`). No committed script builds these from a clean checkout in this sandbox.
- **Global uniqueness is not certified.** The registry is incomplete (see `IR-28-NINE-SITE-DUPLICATES` and the 29 October decision section).

## 8. Owner decisions and manual checks needed (no automation)

1. **Read the organizer data page** (login required) and record whether `labels.tif` and `existing_faults.tif` are distinct, and what `sample_submission.tif` is. This blocks any further holdout claim. Record the answer in `registry/irregularities.json` under IR-29-LABELS-EQUALS-CATALOGUE.
2. **Read the submission-page text** and record the accepted format and the exact per-submission note limit. Record it as an ORGANIZER-CONFIRMED receipt (IR-29-ZEROS-NOT-ORGANIZER-CONFIRMED).
3. **Read the leaderboard by hand** and settle 0.4413 vs 0.3195 (IR-29-LEADERBOARD-CONFLICT).
4. **Decide the front-page policy** for inspection-only downloads of invalid diagnostics (IR-29-FRONTPAGE-DOWNLOAD-OF-INVALID-DIAGNOSTIC).
5. **Reconcile the generators** with the hand-maintained pages before anyone runs them again (IR-28-GENERATOR-DRIFT).
6. **Merge or close the two open PRs** (#65, #47), since both touch the same README and front pages this branch edits.

## 9. Next steps, ranked by what they unlock

1. Resolve IR-29-LABELS-EQUALS-CATALOGUE from the organizer page (owner, manual). Everything else depends on it.
2. Reconcile the generators (IR-28-GENERATOR-DRIFT), so the README and the front page can be rebuilt without losing the current decision record.
3. Design a candidate on a **new** mechanism, not a pruning of B2. Pre-register it, run the same-run comparator, and check the lane rule on the surface and on the final dots. The lane rule and the holdout are the gates.
4. Keep the portal check in CI. It already catches NaN-outside files.

## 10. Verdict

The repo's tests and checks are healthy: 558 pass with the core inputs restored, and ruff is clean. The science is not ready to submit anything. The most important new fact is the input-identity irregularity, and it is open until a human reads the organizer page.
