# Owner brief review — 2026-10-29 (branch `arena/30397b95-gemsdoe25`)

**Decision: OK TO DOWNLOAD AND SUBMIT — NO, for every file.** No new TIFF was generated in this session, because no candidate passed the holdout gate and the lane gate is currently unsatisfiable at the competition's dot budget. Estimated organizer score for every file: **NOT ESTIMATED**. Every score quoted here is **OWNER-REPORTED** unless stated otherwise.

This note answers the three questions in the brief, lists what was verified and how, and records what is still missing. Evidence classes: **COMPUTED** (script + JSON receipt in this repo), **HOLDOUT-DTI** (repo evaluator, proxy only), **OWNER-REPORTED** (from the owner's prompt or a page the owner read), **ORGANIZER-CONFIRMED** (none exists for any file).

---

## 1. Why GEMSDOE32 B2 scored 0.2778 (the highest of the nine sites)

**Verified mechanism (COMPUTED on owner-mirror bytes).** The 0.2778 file is its parent raster with every dot within 200 m of the labelled USGS/INGENIOUS catalogue removed, in two steps:

| Step | Parent | Dots | Removed | Max distance to catalogue of removed dots |
|---|---|---|---|---|
| 0 | GEMSDOE25 / GEMSDOE30 "D2.8" `…d2-8…` (0.2600, owner) | 44,090 | — | — |
| 1 | `gemsdoe28-h27-4-r1-solo` (0.2708 family) | 40,199 | 3,891 | ≤ 1 px (100 m) |
| 2 | GEMSDOE32 B2 (0.2778, owner) | 37,654 | 2,545 | ≤ 2 px (200 m) |

Checks (canonical script `scripts/recheck_b2_lineage.py`, receipt `evidence/b2_lineage_recheck_2026-10-29.json`; inputs from `scripts/restore_data.py --group owner_mirror`; the D2.8 parent is the tracked, byte-identical `docs/downloads/gems25-dotted-h19-5-d2-8-…-zeros.tif`, added to the script this session):

* B2 is a strict subset of both parents (`b2_subset_of_parent` and `d2_8_parent.b2_subset_of_d2_8`: true).
* All 6,436 dots removed from D2.8 (`d2_8_parent.removed_within_2px_catalogue`) and all 2,545 removed from h27-4 (`removed_dots_within_2px_catalogue`) lie within 2 px of a catalogue pixel.
* B2 has **0** dots within 200 m of the catalogue and **0** on it (`b2_dots_within_2px_catalogue`, `b2_dots_on_catalogue_pixels`).
* SHA-256 of the B2 and h27-4 bytes match the pins in `evidence/nine_site_top_files_2026-10-28.json` (`sha256` in the receipt).
* The same rule is already a repo parameter: `CAT_BUF_BLIND = 2.0` px and `FULL_B2_BUDGET = 37_654` in `scripts/run_h74_experiments.py`. The B2 recipe is therefore a known design in this repo, not a new discovery.

**Why it might score higher (INFERENCE, not proven).** Under the official metric (`gems25.metric`, alpha 0.2, beta 0.8, 300 m triangular kernel), a dot adds FP weight `1 − max k` when no truth lies within its kernel. Dots packed against the *known* faults are most likely to sit on pixels that are already catalogued (masked) or on continuous lineaments that are not hidden truth, so their expected FP cost is high. Removing them cuts FP more than it cuts TP. The step-1 and step-2 rules are consistent with this: nothing within 200 m is kept.

**Named non-fault process that could mimic the gain:** the removed dots may simply be the densest cluster in the parent, so the gain could come from thinning rather than from the buffer. A density-matched control (random thinning to 37,654 dots) has **not** been run; it is the first test required before crediting the buffer.

**What the local holdout proxy says (HOLDOUT-DTI, not live).** The repo's standard holdout (draws 140–141, 8 cells, evaluator `gems25.metric.dti_binary`, 22,001 withheld-positive occurrences per arm; source `evidence/h81_exp1/summary.json`):

| Arm | Pooled HOLDOUT-DTI | Mean AUC | Mean emitted dots |
|---|---|---|---|
| CTRL_H35 | 0.157011 | 0.8076 | 11,604 |
| CTRL_SUBSURF (B2-style greedy, 200 m buffer) | 0.050554 | 0.5332 | 9,212 |

The 95% CIs for these two rows are **not** in that summary and were **not** recomputed here. The proxy ranks the B2-style arm far below H35, while the owner-reported live score ranks B2 at the top of the nine sites. The proxy also emits about 9–12k dots, not the 37–44k of the live files. **This is an irregularity** (IR-30397B95-PROXY-DISCORDANCE, §7): the holdout proxy does not reproduce the live ranking of this family, so it must not be used to select a file.

## 2. Can a unique file beat 0.2778? — what the evidence allows

* **Not shown.** No candidate has a holdout result that beats the same-run comparator, and the live leaderboard score of any new file is unknown until an organizer receipt exists.
* **The obvious variant is blocked.** Pruning the parent at 300 m or at other radii would create a unique file, but its effect on the live score is unknown and the lane gate (§3) still applies. Rule 5 of `AGENTS.md` forbids a slot without a same-run holdout win.
* **Burning a slot would be a guess.** The repo's own calibration says proxy-versus-live Spearman is +0.33 and not significant (`AGENTS.md`, rule 5).

## 3. Lane gate — now measured on the bytes (irregularity)

`evidence/b2_lane_vs_r13_2026-10-29.json` (COMPUTED): B2 has **37,622 of 37,654 dots (99.92%)** within 3 px of the registry raster r13 (206,895 dots). The r13 lattice covers almost the whole footprint: 5,160,724 of 5,167,373 footprint pixels lie in its 3-px halo (`evidence/lane_bound_r13_2026-10-28.json`). The repo's *minimum* possible overlap at 37,654 dots is 82.70%, and the literal 70% cap is reachable only at ≤ 21,713 dots.

So under the literal parallel-run rule, **no catalogue-free file of this size can pass**, including the 0.2778 file itself. The rule was written for coordinating parallel sessions, not for the competition's scoring. Whether it should block submissions is an owner decision (IR-29-LANE-RULE-UNSATISFIABLE-AT-BUDGET, confirmed here with bytes).

## 4. Nine-site executive table

Source: `evidence/nine_site_top_files_2026-10-28.json` (re-hashed against pins: match). Format column: whole-array `0 ≤ x ≤ 1` check from `scripts/audit_nine_site_top_files.py`. "Unique" means not a previous submission *and* not an exact dot-set twin of another focus top.

| Site | File to download (owner mirror) | Owner score | Format | Dots | Unique vs the other focus tops? | Estimated organizer score | OK to download AND submit? |
|---|---|---|---|---|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif` | 0.2477 | **NaN outside: portal rejects** | 60,069 | No: max Jaccard 0.979 (GEMSDOE27) | NOT ESTIMATED | **NO** (portal format; previous submission) |
| GEMSDOE25 | `gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (byte-identical to local `docs/downloads/gems25-dotted-h19-5-d2-8-…-nan.tif`) | 0.2600 | **NaN outside: portal rejects** | 44,090 | **No: exact dot-set twin of GEMSDOE30** | NOT ESTIMATED | **NO** |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` | 0.2449 | **NaN outside: portal rejects** | 61,328 | No: max Jaccard 0.979 (GEMSDOE24) | NOT ESTIMATED | **NO** |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` | 0.2710 | **NaN outside: portal rejects** | 37,660 | Yes vs other tops (max Jaccard 0.557) | NOT ESTIMATED | **NO** (format; previous submission) |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-…-91eae1ca-nanoutside.tif` | 0.2600 | **NaN outside: portal rejects** | 44,090 | No: exact dot-set twin of GEMSDOE25 | NOT ESTIMATED | **NO** |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif` | 0.2708 | **NaN outside: portal rejects** | 40,199 | No: max Jaccard 0.937 (GEMSDOE32) | NOT ESTIMATED | **NO** |
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (SHA `c55bafc4…`, matches pin) | **0.2778** | Zeros outside: passes | 37,654 | No: max Jaccard 0.969 (GEMSDOE36); subset of GEMSDOE25 and GEMSDOE28 parents | NOT ESTIMATED | **NO** — already a submitted file; copying it is forbidden |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif` | 0.2632 | **NaN outside: portal rejects** | 41,865 | Yes vs other tops (max Jaccard 0.696) | NOT ESTIMATED | **NO** |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-…-9b9ea4e6-zeros.tif` | 0.2750 | Zeros outside: passes | 38,854 | No: max Jaccard 0.969 (GEMSDOE32) | NOT ESTIMATED | **NO** — already a submitted file |

**Bottom line for the owner:** no file on the nine sites is both top-scoring and eligible. The highest owner-reported score that is also portal-valid (0.2778, GEMSDOE32) is a file that was already submitted. The next portal-valid option (0.2750, GEMSDOE36) is also already submitted. Every other top file is NaN-outside, which the portal rejects with the `Predicted values must be in range [0, 1]` error.

The format check is **not** submit approval. The zeros-outside files pass the local range check but the organizer's exact validator and its outside-footprint handling have not been read (IR-29-ZEROS-NOT-ORGANIZER-CONFIRMED).

## 5. Ranked candidate hypotheses (not yet tested)

Each is checked against the source tree (grep in `src/` and `scripts/`). None has a holdout result. Expected DTI gain is unknown.

1. **Soft distance prior around the visible catalogue (rank 1; implementation cost low).**
   * *Layer:* visible-catalogue distance transform `d_vis` (already computed) × detector score.
   * *Signal:* hidden truth density as a smooth function of `d_vis` (the 1.5 km collar already exists in `block_holdout.py` as an analysis device), instead of a hard 200 m exclusion.
   * *Why not catalogue:* it targets faults the catalogue missed, by estimating how they cluster near mapped faults on the holdout, not by copying mapped traces.
   * *Non-fault mimic:* mapping density bias (where geologists mapped more faults, more faults appear near catalogue).
   * *Repo difference:* the repo uses only a hard buffer (`CAT_BUF_BLIND`, `greedy.py`) and `d_vis` as features. No soft prior was found by grep.
   * *Test:* pre-register; compare hard 200 m, soft prior, and density-matched random thinning in the same run on draws 140–141 and 142–143.
2. **Density-matched thinning control (rank 2; cost very low).** Not a new fault signal, but required before any credit is given to the buffer (§1). Random thinning of the parent to 37,654 dots, same run, same evaluator.
3. **Radiometric K/Th alteration halos along magnetic lineaments (rank 3; blocked).** The source is GeoDAWN radiometric data already restored (`external/geodawn_rad_u8.tif`). The repo's README states that quantized K/Th/U values are code-space ratios, not concentrations, so the band calibration must be confirmed from the official GeoDAWN metadata before this can be tested.
4. **Quaternary slip-rate and focal-mechanism stress tests (rank 4; blocked by allowlist).** Needs USGS data not on this sandbox's outbound allowlist (`registry/sources.json`). Not fetched, so not viable from here.

Already implemented, so **not** new: break-even greedy selection (`src/gems25/greedy.py`, H38), relay/tip features (H30/H36), junction corridors (H81, retracted), and a hard catalogue buffer (`CAT_BUF_BLIND`).

## 6. Verification log

| Check | Result | Command / receipt |
|---|---|---|
| Local HEAD vs `origin/main` | Both `b55a246` | `git rev-parse` |
| Session branch on remote | Did not exist before this session | `git ls-remote --heads origin 'arena/30397b95*'` |
| Open PRs | #65 and #47 (sibling sessions), no PR for this branch | `gh pr list --state open` |
| Test suite before data restore | 547 passed, 15 skipped | `.venv/bin/python -m pytest -q` |
| Core data restore (hash-pinned) | 4 files verified | `scripts/restore_data.py --group core` |
| Scored + external restore | 11 + 7 files verified | `--group scored`, `--group external` |
| Static feature cache | 64 static features built | `scripts/build_features.py` |
| Test suite with data | **561 passed, 1 skipped** | `.venv/bin/python -m pytest -q` (111 s) |
| Independent format validator, 3 zeros files | All hard checks pass; `okay_to_submit: false` | `scripts/verify_candidate_independent.py` |
| B2 lineage on bytes (incl. D2.8 parent) | Consistent with pruning rule | `scripts/recheck_b2_lineage.py` → `evidence/b2_lineage_recheck_2026-10-29.json` |
| B2 lane vs r13 | 99.915% within 3 px | `scripts/audit_b2_lane_vs_r13.py` → `evidence/b2_lane_vs_r13_2026-10-29.json` |
| Holdout canary | **Not rerun**: `run_h81_experiments.py` refuses to overwrite `evidence/h81_exp1`; the recorded numbers above come from that committed file | `evidence/h81_exp1/summary.json` |

Restored owner-mirror inputs are integrity-pinned, not organizer-authenticated (`registry/data_manifest.json`).

## 7. Irregularities flagged for review

* **IR-30397B95-PROXY-DISCORDANCE:** the holdout proxy ranks the B2-style arm (0.0506) far below H35 (0.1570), and the live leaderboard ranks B2 at the top of the nine sites. The proxy is not a valid selector for this family.
* **IR-30397B95-PROXY-DOT-BUDGET:** holdout arms emit about 9–12k dots; live files have 37–44k. The proxy is not evaluated at the competition budget.
* **IR-30397B95-BUILD-README-DESTRUCTIVE:** `scripts/build_readme.py` regenerates an older README and drops the 28 and 29 October sections (confirmed by running it and reverting). A guard was added in this session; see `registry/irregularities.json`.
* **IR-29-LEADERBOARD-CONFLICT (open):** the owner prompt says 0.4413 is the current leaderboard high score; the snapshot in `docs/data/live_scores.json` says 0.3195 for the same participant. The owner must read the leaderboard and record the value.
* **IR-29-LANE-RULE-UNSATISFIABLE-AT-BUDGET (open, now measured):** B2 is 99.92% within 3 px of r13; the literal cap cannot be met at 37,654 dots (§3).
* **IR-30397B95-DUPLICATE-TWINS:** GEMSDOE25 and GEMSDOE30 are exact dot-set twins (both 44,090 dots, same dot-set hash `141a24cbd356c412`, from the receipt; the GEMSDOE25 file was also re-read locally and is byte-identical to its scored twin).
* **IR-29-NAN-DEFAULT-DOWNLOAD (still open):** front-page links to NaN-outside files were not checked page by page in this session.
* **Lineage notes:** the B2 file's score is owner-reported. The receipt and the pruning audit both support the lineage, but the organizer has not confirmed any score for these files.

## 8. Limitations and what is needed

1. **DrivenData access:** not automated (AGENTS.md rule 3). The owner must read the leaderboard and the submission page and record receipts.
2. **Organizer validator:** the portal's exact range and outside-footprint rule has not been read. Ask the organizer or check the submission page text.
3. **Holdout proxy:** not calibrated against live scores (Spearman +0.33, not significant, per `AGENTS.md`), and evaluated at a much lower dot budget than the live files.
4. **Lane rule:** an owner decision. Either the rule applies only to parallel-session coordination (then the competition has no lane limit), or the budget must drop to ≤ 21,713 dots.
5. **External data:** USGS slip-rate, focal-mechanism, and GDR data are not on the outbound allowlist (`github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`). The restored GitHub-mirror inputs are the only data available here.

## 9. Next steps (in order, for the next session)

1. Owner reads the DrivenData leaderboard and submission page by hand; record receipts in `registry/live_scores.json`.
2. Owner decides whether the r13 lane rule is a competition rule or only a coordination rule (IR-29-LANE-RULE-UNSATISFIABLE-AT-BUDGET).
3. Pre-register (commit first) a single 3-arm experiment: hard 200 m buffer, soft prior (rank 1), and density-matched random thinning (rank 2), same run, same evaluator, draws 140–143, with 95% CIs. Stop after 3 experiments or 2 hours.
4. Only a candidate that beats the same-run density-matched control on the holdout, and passes the format audit, may be proposed for a slot. Promotion stays a separate owner selection step.

## 10. Source links for manual review

* Competition page and data: https://www.drivendata.org/competitions/306/competition-doe-gems/ and https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (not accessed by the agent; AGENTS.md rule 3)
* Leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ (owner must read by hand)
* Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
* USGS GeoDAWN radiometric/magnetic survey: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
* Submission format PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf
* EPSG:32611 (grid CRS): https://epsg.io/32611
* Tversky index (background for the DTI form): https://en.wikipedia.org/wiki/Tversky_index
* Owner mirror used for the B2 bytes (GitHub blob, not organizer-authenticated): https://github.com/buffedlizard55-lab/GEMSDOE32/blob/main/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif
