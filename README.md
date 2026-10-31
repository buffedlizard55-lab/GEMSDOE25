# GEMSDOE25 — designed-factorial fault discovery for the DOE GEMS Prize

## START HERE — current review 2026-10-31

**Current verdict: NO TIFF is cleared for download and submission; new score estimate: NOT ESTIMATED.** No lane was assigned, `data/` contains only `.gitkeep`, no experiment or submission TIFF was produced, and the organizer-side meaning of the mirrored label/catalogue identity is unresolved. Read the [31 Oct executive review](docs/review-2026-10-31.html), [full findings and ranked hypotheses](knowledge/56_repo_review_2026-10-31.md), and [negative JSON run card](registry/run_card_session_2026-10-31.json) before continuing. Related initial snapshot: [REVIEW_2026-10-31.md](REVIEW_2026-10-31.md); it records the earlier base checkout and likewise makes no submission claim.

**Correction:** the GEMSDOE25 historical D2.8 filename is `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (not `gems24-...`); see `knowledge/52_repo_review_2026-10-29_verified.md`.

## START HERE — owner brief 2026-10-30 (branch `arena/68c7ea9e-gemsdoe25`)

> Read this section first every session. Standing rule: **Maximize P(Win)** and **Own the Outcome** decide tradeoffs, but no gate is bypassed to reach a number. Normalized brief (not a verbatim transcript; see IR-30-PROMPT-NORMALIZED). Full executive summary: [`docs/owner-brief-2026-10-30.html`](docs/owner-brief-2026-10-30.html).

**OK TO DOWNLOAD AND SUBMIT: NO. No file on the nine focus sites or in this branch is cleared. Estimated organizer score: NOT ESTIMATED for every file.**

### What you asked for, and what the evidence says

| Requirement | Status (verified 30 Oct) |
|---|---|
| Unique TIF that is OK to download and submit | **Not met.** The one TIF generated today (H-SP1 arm A1, 21,000 dots) is a **99.87% literal lane duplicate of r13** and was removed from `docs/downloads`. A lane-compliant file tested today (H-LF1) has holdout signal equal to the random floor. |
| Portal range check (`Predicted values must be in range [0, 1]`) | Explained: NaN-outside files fail. Only GEMSDOE32 and GEMSDOE36 use zeros outside, and both are previous submissions. |
| Name and short note for each file | Format used: `gems25-<slug>-<date>-<content id>-zero.tif`, note ≤140 characters (protocol limit; the code default is 120) with the id and status (see `scripts/build_hsp1_candidate.py`). The only note written today says `NOSUBMIT`. |
| Gates before submission (format, holdout, lane, uniqueness) | Implemented and run without a human in the loop: `scripts/verify_candidate_independent.py`, `scripts/check_lane_duplicates.py`, `scripts/run_soft_catalogue_prior.py`, `scripts/run_lane_first_prior.py`. A human check of organizer data is still required (IR-29-LABELS-EQUALS-CATALOGUE). |
| Estimated score per file | **NOT ESTIMATED.** The holdout proxy scores 0.005–0.03; owner-reported leaderboard-family scores are 0.25–0.28. The proxy is off-scale (IR-30-HOLDOUT-SCALE-MISMATCH). |
| Why 0.2778 was highest, and can we beat it | See below. **Not shown** that anything beats 0.2778. |
| Highest-scoring submission to submit | **None cleared.** GEMSDOE32 (0.2778) and GEMSDOE36 (0.2750) are the top portal-valid files, but both are previous submissions. |

### Executive summary: the nine focus sites

Owner-reported scores; organizer receipts: none. "Previous submission" = listed as submitted on its site. Full table with partner Jaccard values: [`docs/owner-brief-2026-10-30.html`](docs/owner-brief-2026-10-30.html). Recomputed 30 Oct: [`evidence/nine_site_top_files_2026-10-28.json`](evidence/nine_site_top_files_2026-10-28.json).

| Site | File to download (owner mirror) | Owner score | Portal format | Previous submission? | Unique among the nine? | Estimated score | OK to download AND submit? |
|---|---|---|---|---|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-…-nan.tif` | 0.2477 | Fails (NaN) | Yes | No (Jaccard 0.979, GEMSDOE27) | NOT ESTIMATED | **NO** |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 0.2600 | Fails (NaN) | Yes | No (exact twin of GEMSDOE30) | NOT ESTIMATED | **NO** |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-…-nan.tif` | 0.2449 | Fails (NaN) | Yes | No (Jaccard 0.979, GEMSDOE24) | NOT ESTIMATED | **NO** |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-…-nan.tif` | 0.2710 | Fails (NaN) | Yes | Yes (max Jaccard 0.557) | NOT ESTIMATED | **NO** |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-…-nanoutside.tif` | 0.2600 | Fails (NaN) | Yes | No (exact twin of GEMSDOE25) | NOT ESTIMATED | **NO** |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-…-nan.tif` | 0.2708 | Fails (NaN) | Yes | No (Jaccard 0.937, GEMSDOE32) | NOT ESTIMATED | **NO** |
| GEMSDOE32 | `gemsdoe32-h33-h33-2-b2-…-e5eb6e7e-zeros.tif` (SHA-256 `c55bafc4…`) | **0.2778** | Passes (zeros) | **Yes** | No (Jaccard 0.969, GEMSDOE36) | NOT ESTIMATED | **NO: already submitted** |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-…-nanoutside.tif` | 0.2632 | Fails (NaN) | Yes | No vs others (Jaccard 0.696, GEMSDOE31) | NOT ESTIMATED | **NO** |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-…-zeros.tif` (SHA-256 `e1589102…`) | 0.2750 | Passes (zeros) | **Yes** | No (Jaccard 0.969, GEMSDOE32) | NOT ESTIMATED | **NO: already submitted** |

### Why GEMSDOE32 scored 0.2778 (inference, with verified facts)

* **Verified on the bytes:** B2 (37,654 dots) is an exact subset of the H27-4 raster (40,199 dots; GEMSDOE31 and the GEMSDOE28 `h27-4-r1` file share this dot set), which is a subset of D2.8 (44,090 dots; GEMSDOE25 and GEMSDOE30). The removed dots lie within 1–2 px of the labelled catalogue; B2 has **0** dots within 2 px of it. Owner scores rose 0.2600 → 0.2708 → 0.2778 at each step. (`scripts/audit_nine_site_top_files.py`, `scripts/recheck_b2_lineage.py`.)
* **Mechanism (inference, not proven):** under DTI with α = 0.2 on false positives, dots next to already-mapped faults add false-positive weight on the hidden target. Removing them can help. This has **not** been separated from plain thinning: no density-matched control has been run on the nine-site family.

### Can we beat 0.2778? Experiments run today (budget: 3 experiments, 2 hours; 2 used)

Both experiments are pre-registered before running and use the repo's holdout evaluator (`gems25.holdout`, `gems25.metric`). Numbers are **HOLDOUT-DTI** (catalogue-gap proxy): evaluator version, withheld positives and 95% CIs are in the receipts.

| Exp | Pre-registration | Question | Result | Verdict |
|---|---|---|---|---|
| 1 · H-SP1 | [`knowledge/54`](knowledge/54_preregistered_soft_catalogue_prior_2026-10-30.md) · [`evidence/soft_catalogue_prior_exp1_2026-10-30.json`](evidence/soft_catalogue_prior_exp1_2026-10-30.json) | Does a soft catalogue prior on a catalogue-free ridge beat a hard 200 m buffer and random dots at 21,000 dots? | Soft prior beats hard buffer: dev +0.0106 (95% CI [0.0053, 0.0150]). **Random dots beat the prior:** dev −0.0105 (CI [−0.0179, −0.0049]); confirm −0.0106 (CI [−0.0164, −0.0052]). Random floor 0.0337 vs prior 0.0232 (dev, 8 draws; 23,923 withheld positives). Canary: ridge AUC 0.47–0.55; −distance AUC 0.70–0.82 (below 0.90). | **Negative** (G1 failed) |
| 2 · H-LF1 | [`knowledge/55`](knowledge/55_preregistered_lane_first_2026-10-30.md) · [`evidence/lane_first_exp2_2026-10-30.json`](evidence/lane_first_exp2_2026-10-30.json) | Does a lane-compliant file (dots only outside the r13 halo; 6,000 dots) carry any holdout signal? | Every arm 0.0042–0.0056 (confirm and dev); point differences to the random floor ≤ 0.0003, CIs cross or sit at zero. | **Negative** (no signal at the random floor) |

The 1st experiment's file is a lane duplicate (99.87% of dots within 3 px of r13, `check_lane_duplicates.py`), so it is **not packaged**. Its arm A1 also lost to random dots. The 2nd experiment built no file.

### Lane bound, which decides what a unique file can look like

Reproduced 30 Oct with `scripts/audit_r13_lane_bound.py`: the r13 3-px halo leaves only **6,514** eligible footprint pixels (outside the halo and the catalogue). Any catalogue-free file with more than **21,713** dots has at least 70% of its dots within the halo and fails the literal lane rule. A competitive-size file (37,654 dots) has a minimum overlap of **82.7%**. A lane-compliant file must use fewer dots, and experiment 2 found that such a file had no signal at 6,000 dots. This is an arithmetic fact about the registry, not a policy. Whether the 70% rule applies to the competition is an owner decision (IR-30-LANE-BOUND-CAP).

### Decisions only the owner can make (no manual input is assumed by the agent)

1. **Organizer data check (critical):** `labels.tif` and `existing_faults.tif` are byte-identical (60,988 catalogue pixels). Read the organizer data page and record whether the hidden target differs (IR-29-LABELS-EQUALS-CATALOGUE). Until then, every holdout is suspect.
2. **Lane rule:** does the 70% r13 overlap rule apply to the competition? If yes, competitive-size files cannot pass. If no, remove the rule from the protocol explicitly.
3. **Leaderboard value:** the brief gives 0.4413 in one place and 0.3195 in another. [`registry/live_scores.json`](registry/live_scores.json) records both (0.3195 earlier snapshot; 0.4413 latest claim). Read the leaderboard by hand and record a receipt (IR-30-LEADERBOARD-THREE-VALUES).
4. **Next experiment:** the third experiment needs a new, pre-registered mechanism. A density-matched thinning control (knowledge/51 rank 2) is the cheapest. Choosing it is an owner decision.

### Corrections made today (do not repeat)

* **Soft prior is not new.** `knowledge/51` §5 rank 1 said a soft catalogue prior was untested. `src/gems25/h31.py::build_offflank_tip_halo` already applies `exp(-(d-3)/12)`. Logged as IR-30-SOFT-PRIOR-NOT-NEW.
* **Lane check fails closed.** `check_lane_duplicates.py` stops at the first duplicate (`break`), so `registry_checked: 1` is by design, not missing coverage.
* **Do not run `build_site.py` or `build_readme.py` on this branch** (IR-28-GENERATOR-DRIFT). This section was added by hand.

### Read-first files for next session

[`docs/owner-brief-2026-10-30.html`](docs/owner-brief-2026-10-30.html) · [`registry/run_card_2026-10-30.json`](registry/run_card_2026-10-30.json) · [`registry/review_passes_2026-10-30.json`](registry/review_passes_2026-10-30.json) · [`registry/irregularities.json`](registry/irregularities.json) (IR-30-*) · [`evidence/lane_bound_r13_2026-10-28.json`](evidence/lane_bound_r13_2026-10-28.json)

### Links for manual review (official sources)

* Competition: [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) · [problem page and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) · [about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) · [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
* Submission format: [NLR PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · reference solution: [drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
* Data context: [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [INGENIOUS (GBCGE)](https://gbcge.org/current-projects/ingenious/) · [EPSG:32611](https://epsg.io/32611) · [Tversky index](https://en.wikipedia.org/wiki/Tversky_index)
* Not reachable from this sandbox: drivendata.org, dropbox.com, gdr.openei.org (outbound allowlist: github.com, pypi.org, npm). No DrivenData automation (AGENTS.md rule 3).

### Limitations and what is needed to succeed

* **Organizer access:** a human must read the data page, leaderboard and submission receipts. No automation is authorized.
* **Identity of inputs:** the labels problem above; scores are owner-reported, not organizer receipts.
* **Proxy:** the holdout measures catalogue-gap recovery, not hidden-fault truth, and is off the leaderboard scale.
* **External layers are owner-derived:** the LiDAR scarp features come from the owner's CI run on USGS 3DEP 1-m DEM tiles (706 of 716 tiles; the tile list was OCR-recovered from the competition PDF). The GeoDAWN radiometric grids (DOI 10.5066/P93LGLVQ) and GDR 1391 CSVs (DOI 10.15121/1881483) are restored by hash from owner mirrors. None was re-derived from its official host here (`registry/data_manifest.json`).
* **Lane rule:** unresolved owner decision (above).

---

## START HERE — owner brief 2026-10-29 (session `arena/30397b95-gemsdoe25`)

> Read this section first every session. It is the normalized owner brief (not a verbatim transcript): the requirements below are the operative text, with the full review in [`knowledge/51`](knowledge/51_owner_brief_session_review_2026-10-29_30397b95.md). Maximize **P(Win)** and **Own the Outcome** are the decision rule.

**OK TO DOWNLOAD AND SUBMIT: NO — for every file on the nine focus sites and in this repository. Estimated competition score: NOT ESTIMATED.** No new TIFF was generated this session, because no candidate passed the holdout gate and the r13 lane gate cannot be met at the competition's dot budget (§ *Why no file is cleared*). Nothing was uploaded to DrivenData (automation is forbidden; AGENTS.md rule 3).

### Executive summary — the nine focus sites (owner-reported scores; organizer receipts: none)

| Site | File to download (owner mirror) | Owner score | Format (portal `[0,1]` check) | Unique? | Estimated organizer score | OK to download AND submit? |
|---|---|---|---|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-…-nan.tif` | 0.2477 | Fails (NaN outside) | No (max Jaccard 0.979, GEMSDOE27) | NOT ESTIMATED | **NO** |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (= local mirror) | 0.2600 | Fails (NaN outside) | No (exact dot-set twin of GEMSDOE30) | NOT ESTIMATED | **NO** |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-…-nan.tif` | 0.2449 | Fails (NaN outside) | No (max Jaccard 0.979, GEMSDOE24) | NOT ESTIMATED | **NO** |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-…-nan.tif` | 0.2710 | Fails (NaN outside) | Yes vs other tops; previous submission | NOT ESTIMATED | **NO** |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-…-nanoutside.tif` | 0.2600 | Fails (NaN outside) | No (exact dot-set twin of GEMSDOE25) | NOT ESTIMATED | **NO** |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-…-nan.tif` | 0.2708 | Fails (NaN outside) | No (max Jaccard 0.937, GEMSDOE32) | NOT ESTIMATED | **NO** |
| **GEMSDOE32** | `gemsdoe32-h33-h33-2-b2-…-e5eb6e7e-zeros.tif` (SHA `c55bafc4…`, verified) | **0.2778** (highest) | Passes (zeros outside) | No: **already submitted**; subset of two parents | NOT ESTIMATED | **NO** — copying a previous submission is not allowed |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-…-nanoutside.tif` | 0.2632 | Fails (NaN outside) | Yes vs other tops (max Jaccard 0.696); previous submission | NOT ESTIMATED | **NO** |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-…-zeros.tif` | 0.2750 | Passes (zeros outside) | No: **already submitted** (max Jaccard 0.969) | NOT ESTIMATED | **NO** |

Per-file SHA-256, dot counts and receipts: [`evidence/nine_site_top_files_2026-10-28.json`](evidence/nine_site_top_files_2026-10-28.json). **No file is both the top score and eligible.** The highest portal-valid score (0.2778) is a file that was already submitted.

### Why GEMSDOE32 B2 scored 0.2778 (verified on the bytes)

* B2 is its parent raster with every dot within 200 m of the labelled catalogue removed, in two steps: D2.8 (44,090 dots) → h27-4 (40,199; 3,891 removed within 1 px) → B2 (37,654; 2,545 removed within 2 px). All 6,436 + 2,545 removed dots lie within 200 m of the catalogue; B2 has **0** dots there. Receipt: [`evidence/b2_lineage_recheck_2026-10-29.json`](evidence/b2_lineage_recheck_2026-10-29.json) (script `scripts/recheck_b2_lineage.py`, pinned `--group owner_mirror` inputs).
* **Mechanism (inference, not proven):** under the metric, a dot near a known fault that does not sit on hidden truth adds false-positive weight. Removing such dots improves the balance. A density-matched thinning control has **not** been run, so the buffer is not yet separated from plain thinning.
* **The repo's holdout proxy does not agree:** on draws 140–141, the B2-style arm scores HOLDOUT-DTI 0.050554 against 0.157011 for the H35 control (evidence in `evidence/h81_exp1/summary.json`; 95% CIs not recomputed here). The proxy cannot be used to select a file.

### Can we beat 0.2778?

**Not shown.** The only candidate family matching the verified mechanism is the B2 family itself, and any variant (other radii, thinning) has no holdout win. The lane gate also blocks any file of this size: B2 has **99.92%** of its dots within 3 px of registry raster r13, while the literal cap is 70% (the minimum possible at 37,654 dots is 82.70%). That rule is a parallel-session coordination rule, and whether it applies to the competition is an **owner decision**.

Ranked, untested hypotheses and the pre-registration path are in [`knowledge/51`](knowledge/51_owner_brief_session_review_2026-10-29_30397b95.md#5-ranked-candidate-hypotheses-not-yet-tested).

### Owner requirements (normalized) that govern every file

1. **Unique file, not a copy.** Do not resubmit a previous file except for learning. Each file has a unique content-addressed name and note.
2. **Obvious status.** Every page and file says whether it is OK to download and submit. Today: **NO** for all.
3. **Format:** single-band float32 GeoTIFF on EPSG:32611, 3730×3292, the template transform, finite values in [0, 1]. NaN-outside files fail the portal check. The organizer's exact outside-footprint rule is not yet confirmed.
4. **Validation without a human, through the project:** `scripts/verify_candidate_independent.py`, the holdout gate, and the lane check. A format pass is not submit approval.
5. **Labels for every number:** HOLDOUT-DTI (with evaluator, withheld count and CI), ORGANIZER-CONFIRMED (receipt only), OWNER-REPORTED, COMPUTED, or NOT ESTIMATED. No projection is written as a score.
6. **No DrivenData automation.** The owner reads the leaderboard and submission pages and records receipts. The agent never uploads.
7. **Pre-register, then test.** Commit the design first. Budget: 3 experiments or 2 hours. Recompute the comparator in the same run.
8. **Review three times** and record receipts in `registry/review_passes_*.json`. Flag irregularities; no hallucinated results.
9. **Leaderboard conflict:** the owner prompt gives 0.4413 as the current high score, and the snapshot in `docs/data/live_scores.json` gives 0.3195 for the same participant. The owner must read the leaderboard by hand (IR-29-LEADERBOARD-CONFLICT).

### Links for manual review

* Competition: [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
* [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) · [Submission format PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) · [GeoDAWN USGS data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) · [EPSG:32611](https://epsg.io/32611) · [Tversky index](https://en.wikipedia.org/wiki/Tversky_index)
* Session review: [`knowledge/51`](knowledge/51_owner_brief_session_review_2026-10-29_30397b95.md) · run card: [`registry/run_card_session_30397b95_2026-10-29.json`](registry/run_card_session_30397b95_2026-10-29.json) · reviews: [`registry/review_passes_session_30397b95_2026-10-29.json`](registry/review_passes_session_30397b95_2026-10-29.json)
## Review alert — 30 October 2026 (session 69c4ad1e, read first)

**OK TO DOWNLOAD AND SUBMIT: NO, for every file on the nine focus sites and in this repository. Estimated score: NOT ESTIMATED.** No new TIF was generated: no candidate passed the holdout gate, and the holdout is uncertified (below).

| Site | Best file (owner mirror) | Owner score | Passes [0,1] portal check | Unique? | Estimated score | OK to download AND submit? |
|---|---|---|---|---|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-…-nan.tif` | 0.2477 | No (NaN outside) | No (Jaccard 0.980 vs GEMSDOE27) | NOT ESTIMATED | **NO** |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` | 0.2600 | No (NaN outside) | No (identical dot set to GEMSDOE30) | NOT ESTIMATED | **NO** |
| GEMSDOE27 | `GEMSDOE27__gems27-topo-gap-closure-t-v2-on-d1-5-…-nan.tif` | 0.2449 | No (NaN outside) | No (Jaccard 0.980 vs GEMSDOE24) | NOT ESTIMATED | **NO** |
| GEMSDOE28 | `GEMSDOE28__gems28-h36-1-rung30-blind-r1-…-nan.tif` | 0.2710 | No (NaN outside) | Yes vs other tops (max Jaccard 0.557) | NOT ESTIMATED | **NO** |
| GEMSDOE30 | `GEMSDOE30__gemsdoe30-d28-poisson300m-offcat-44090-…-nanoutside.tif` | 0.2600 | No (NaN outside) | No (identical dot set to GEMSDOE25) | NOT ESTIMATED | **NO** |
| GEMSDOE31 | `GEMSDOE31__gemsdoe31-h27-4-solo-d28-…-nan.tif` | 0.2708 | No (NaN outside) | No (Jaccard 0.937 vs GEMSDOE32) | NOT ESTIMATED | **NO** |
| GEMSDOE32 | `GEMSDOE32__gemsdoe32-h33-h33-2-b2-…-e5eb6e7e-zeros.tif` (SHA-256 `c55bafc4…`) | **0.2778** (highest) | Yes (zeros outside) | No: already submitted | NOT ESTIMATED | **NO**, a previous submission |
| GEMSDOE33 | `GEMSDOE33__GEMSDOE33-h33d-analog-tip-stepover-r30-…-nanoutside.tif` | 0.2632 | No (NaN outside) | Yes vs other tops (max Jaccard 0.696) | NOT ESTIMATED | **NO** |
| GEMSDOE36 | `GEMSDOE36__gemsdoe36-anderson-geothermal-pinn-38854-…-zeros.tif` | 0.2750 | Yes (zeros outside) | No: already submitted (Jaccard 0.969 vs GEMSDOE32) | NOT ESTIMATED | **NO**, a previous submission |

* Every number is OWNER-REPORTED or COMPUTED. No organizer receipt exists in this repo. Nothing was uploaded to DrivenData.
* **Critical, open (IR-29-LABELS-EQUALS-CATALOGUE, re-verified 30 Oct):** `labels.tif` and `existing_faults.tif` are byte-identical, and the sample submission's 60,988 ones equal the same pixels. The holdout uses labels as hidden truth, so its numbers are not certified. Owner: compare the organizer data-page file to SHA-256 `7ba308cc…`.
* **Leaderboard conflict (IR-29-LEADERBOARD-CONFLICT):** the owner prompt gives 0.4413 and 0.3195 as the high score. Owner to read the leaderboard by hand.
* Full review, reproduced audit and blockers: [`knowledge/53`](knowledge/53_repo_review_2026-10-30_69c4ad1e.md) · run card: [`registry/run_card_session_69c4ad1e_2026-10-30.json`](registry/run_card_session_69c4ad1e_2026-10-30.json) · review passes: [`registry/review_passes_session_69c4ad1e_2026-10-30.json`](registry/review_passes_session_69c4ad1e_2026-10-30.json).
* Re-run the checks: `python scripts/restore_data.py --group scored` (and the other groups), then `python scripts/audit_nine_site_top_files.py` and `python scripts/verify_candidate_independent.py <file>`. Do not run `build_site.py` or `build_readme.py`; they rewrite hand-maintained sections (IR-28-GENERATOR-DRIFT).

## Review alert — 29 October 2026

**OK TO DOWNLOAD AND SUBMIT: NO. Nothing in this repository is cleared. Estimated score: NOT ESTIMATED.**

* **Critical, open (IR-29-LABELS-EQUALS-CATALOGUE):** the owner-mirror `labels.tif` and `existing_faults.tif` are byte-identical, and `sample_submission.tif` carries the same 60,988 fault pixels. A human must check the organizer data page. Until then, holdout results on these inputs are not certified. Evidence: [`evidence/label_identity_audit_2026-10-29.json`](evidence/label_identity_audit_2026-10-29.json).
* **Verified from bytes (29 Oct):** the GEMSDOE32 B2 raster is an exact subset of the GEMSDOE28 H27-4 raster, which is a subset of the D2.8 raster. The removed dots are the 2,545 H27-4 dots within 2 px of the labelled catalogue. Scores remain OWNER-REPORTED. Receipt: [`evidence/nine_site_top_files_2026-10-28.json`](evidence/nine_site_top_files_2026-10-28.json) (reproduced 29 Oct).
* **Do not run `build_site.py` or `build_readme.py` on this branch.** They rewrite hand-maintained sections and delete the 29 October content (IR-28-GENERATOR-DRIFT).
* Session review and run card: [`knowledge/52_repo_review_2026-10-29_verified.md`](knowledge/52_repo_review_2026-10-29_verified.md) · [`registry/review_passes_87a0b9a8_2026-10-29.json`](registry/review_passes_87a0b9a8_2026-10-29.json).

## Session 2026-10-29 (branch `arena/f486e4e3-gemsdoe25`) — decision first

**OK TO DOWNLOAD AND SUBMIT: NO, for every file.** Estimated competition score: **NOT ESTIMATED** for every new file. No new TIF was generated: any file built from the GEMSDOE32 0.2778 lineage is a near-duplicate of a previous submission, and fails the r13 lane rule.

* **Executive summary and estimate table:** [`knowledge/49_session_review_2026-10-29_f486e4e3.md`](knowledge/49_session_review_2026-10-29_f486e4e3.md) (section 5 is the table; section 3 answers "why did 0.2778 score highest").
* **0.2778 lineage verified from bytes:** the GEMSDOE32 B2 file is the 0.2708 GEMSDOE28 h27-4 raster minus 2,545 dots, all within 2 px of the known catalogue; none added. Receipt: [`evidence/b2_lineage_recheck_2026-10-29.json`](evidence/b2_lineage_recheck_2026-10-29.json). The 0.2778 score itself is still OWNER-REPORTED.
* **Top file fails the lane rule:** 99.92% of B2's dots lie within 3 px of registry raster r13 (the literal limit is 70%). Owner decision: [IR-29-B2-LANE-VIOLATION-TOP-FILE](registry/irregularities.json).
* **Official rules (NLR, Sept 2026), read this session:** [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf). One single-band GeoTIFF at 100 m; at most three submissions per week; metric is a distance-weighted Tversky index; the narrative must disclose generative-AI use. The 300 m kernel is **not** in the rules text (IR-29-OFFICIAL-METRIC-NOT-READ).
* **Reproduce the lineage check:** `python scripts/restore_data.py --group core`, then `--group owner_mirror`, then `python scripts/recheck_b2_lineage.py`.
* **Open items for the owner:** read the leaderboard by hand (0.4413 vs 0.3195 conflict); read the metric page; decide the lane rule; review the AI disclosure; provide the verbatim brief if it must be in the README.


## Current result — 29 October 2026 (read before using any download)

**New unique-content research file:** [download `gems25-mag-rad-decoupling-20261029-8e2e136eddc8-zero.tif`](docs/downloads/gems25-mag-rad-decoupling-20261029-8e2e136eddc8-zero.tif). **OK to download for inspection: YES. OK to submit: NO — DO NOT SUBMIT.** Organizer score estimate: **UNKNOWN, not projected.** The file is a valid single-band float32 TIFF on the pinned owner-mirror grid, with all values finite and within [0,1]; SHA-256 `82cda4c3e3e79b4038763526f720702a850b10fa8ae40262809d2100a177bde2`. The full-surface and final-dot audits cover 151 aligned pinned references, but one pinned historical raster has an off-grid transform, so global uniqueness cannot be certified. The *invalid* holdout diagnostic is 0.00000 (95% CI [0,0]; 23,923 withheld-positive occurrences; `gems25.metric.dti_binary`, alpha .2 beta .8, 300 m triangular kernel); the full labelled catalogue was used during dot placement, leaking withheld locations. This is **not** an eligible hide-and-recover result. [Executive summary](docs/executive-summary.html) · [run card](registry/run_card_decoupling_2026-10-29.json) · [frozen design and correction](knowledge/50_preregistered_decoupling_feasible_allocation_2026-10-29.md). No competition slot used. The 0.2778 GEMSDOE32 historical result remains **OWNER-REPORTED**, not a new submission, and no evidence here supports a prediction above it.

The earlier 27 October owner prompt and its Parallel-run Protocol are archived later in this README; the active 29 October requirements below are a normalized session brief, not a verbatim transcript. Maintain **Maximize P(Win)** and **Own the Outcome** without promoting negative or contaminated diagnostics.

**29 October follow-up review:** core, external, and scored files restored and SHA-256 checked against the owner-mirror manifest (mirror integrity only); full suite: 562 passed, 4 skipped. The shared `data/work` feature cache is still absent; no new experiment, raster, slot selection, or upload occurred. **OK TO SUBMIT: NO — DO NOT SUBMIT.** [Current review, hypotheses and run card](knowledge/52_repo_review_2026-10-29.md) · [Input restore audit](evidence/data_restore_audit_2026-10-29.json) · [Executive summary and historical download table](docs/executive-summary.html) · [H81 review and retracted score estimates](knowledge/47_repo_review_2026-10-28.md)

## Read first — active owner brief, 29 October 2026 (normalized from this session; not a verbatim transcript)

**OK TO DOWNLOAD AND SUBMIT: NO — DO NOT SUBMIT any current research TIFF.** No new candidate has passed all scientific, holdout, lane, exact-file, and selector gates. A new submission's expected score is **UNKNOWN / NOT ESTIMATED**; never substitute a local DTI or a projection for an organizer score.

* Review the highest supplied files from GEMSDOE24/25/27/28/30/31/32/33/36. The reported 0.2778 for GEMSDOE32 B2 is OWNER-REPORTED, not an organizer receipt. Keep a clear table of filename, reported score, new-score estimate, exact-duplicate status, validator status, and submit decision. Never copy/re-name a previous submission.
* Research geothermal systems only as a possible structural prior: the competition target is fault prediction, not confirmed vent detection. Before a method is implemented, rank 3–5 unvalidated hypotheses by expected leverage and cost, name layers/signature/missing-fault rationale/non-fault mimics, and check official-source availability. Any projected score must remain UNKNOWN unless calibrated and validated.
* Follow the parallel-run protocol archived below. Use one explicit method lane; shared cached features/evaluator/writer; whole-segment buffered hide-and-recover; visible-fault-only catalogue features; exact visible-fault masking; pooled DTI α=.2/β=.8/300 m triangular kernel; per-feature leakage canaries (AUC >.90 is leakage until resolved); same-run controls and paired 95% CI. Stop after three experiments or two hours. Do not select a slot or upload.
* Audit both the surface before placement and final dots against every comparable registry raster. `|rank correlation| > .90` or `>70%` within 3 px is a duplicate stop. An incomparable/off-grid reference prevents claiming global uniqueness. Validate the full raster for finiteness, [0,1], single band, CRS/shape/transform, exact catalogue mask, unique identity and note length (≤140 characters).
* Keep score classes separate: HOLDOUT-DTI with evaluator/withheld-positive count/95% CI; ORGANIZER-CONFIRMED only from a submission-page receipt; owner-supplied results are OWNER-REPORTED. Never upload or automate access to DrivenData.
* Current irregularity: the supplied overall-leader values 0.3195 and 0.4413 conflict. Neither is verified here. Current data restore and test status, ranked proposals, official review links, and the JSON run card are recorded in [`knowledge/52_repo_review_2026-10-29.md`](knowledge/52_repo_review_2026-10-29.md). The earlier 29 October decoupling diagnosis is in [`knowledge/48_session_review_2026-10-29.md`](knowledge/48_session_review_2026-10-29.md); it has no eligible candidate.

The full earlier prompt from 27 October is archived verbatim later in this README. This active-session text is explicitly normalized and supplements, rather than replaces, that historical archive. `AGENTS.md` requires reading this README at the start of every work session.


## 29 October 2026 — audit correction

**NO competition-ready submission. DO NOT SUBMIT.** The historical vent probe's HOLDOUT-DTI 0.01037 exceeded the spread-only control 0.00311, not the reverse; it was below H35 0.12165. Its recorded CI, evaluator and positive count are in the [correction](docs/vent-probe-correction.html). Its lane clearance was overstated: one registry raster was skipped and a pre-placement surface audit is not documented. The run card reports known-fault positives, and the historical builder is disabled. The final-dot checker now fails closed on mixed aligned and off-grid registry inputs. No new experiment or slot was used. The active brief still does not identify one unambiguous method lane. Core, external, and scored inputs have since been restored and hash-checked from the pinned mirrors, but the shared derived `data/work` feature cache remains absent. [Current ranked proposals and review](knowledge/52_repo_review_2026-10-29.md) are not validated; the requested submit-cleared TIF remains undelivered.

## Nine-site brief (28 October 2026) — what to download, and why nothing is OK to submit

**OK TO DOWNLOAD AND SUBMIT: NO — no file in this repository or on the nine focus sites is cleared.**
Estimated competition score: **UNKNOWN / NOT ESTIMATED** for every file (no calibrated projection exists).

* **Portal error explained (verified):** a NaN-outside GeoTIFF fails the portal's whole-array range check
  (`NaN` fails every `0 <= x <= 1` test). The reference solution writes finite values only
  (`unet-mc-cv-reference-solution.ipynb` at pinned commit `aebe92f`; `evidence/official_reference_2026-10-26.json`). The validator now enforces this (`portal_all_cells_finite_in_0_1`).
  Of 62 GeoTIFFs in `docs/downloads/` (counted 29 Oct 2026), 32 are portal-safe (zeros outside) and 30 are NaN-outside (7,111,787 non-finite cells each).
* **The 0.2778 file (GEMSDOE32 B2) is a pruned copy of the 0.2708 h27-4 raster:** its 37,654 dots are a strict subset of
  the 40,199 dots in `gemsdoe28-h27-4-r1-solo` (2,545 removed; Jaccard 0.9367).
  It is portal-safe, has zero dots on the labelled catalogue, and is a previous submission, so it may not be copied.
* **Lane bound (r13, verified):** at 37,654 dots at least **82.70%** of dots must sit within 3 px of r13.
  The literal 70% cap is reachable only at or below **21,713** dots. This is an owner decision.
* Full table, per-file links and receipts: [docs/nine-site-brief.html](docs/nine-site-brief.html) ·
  [nine-site receipt](evidence/nine_site_top_files_2026-10-28.json) · [portal sweep](evidence/portal_safety_sweep_2026-10-28.json) ·
  [r13 bound](evidence/lane_bound_r13_2026-10-28.json).


## Latest result — H81 failed promotion; no eligible submission (28 October 2026)

**OK TO SUBMIT: NO — DO NOT SUBMIT. New-submission score: NOT ESTIMATED.** H81 did not publish a TIFF or receive slot approval. On the 25-km checkerboard holdout, `H81_JUNC_CG` scored **HOLDOUT-DTI 0.111126** vs same-run `CTRL_BLIND_ABCD` **0.121443** (paired gain **-0.010317**, 95% CI **[-0.012437, -0.006948]**, **95,188 withheld-positive occurrences**; evaluator `gems25.metric.dti_binary`, alpha 0.2, beta 0.8, 300 m triangular kernel). H81 also failed the primary H35 gate and the final-dot lane gate (72.20% within 3 px of H75; limit 70%).

The previous public H81 empirical bands (0.2250–0.2250 and a “kernel-matched optimum” band) are **retracted**: the gated audit matched zero historical rasters and those bands were not leaderboard scores. The best supplied historical result among the nine requested sites is GEMSDOE32 B2 at 0.2778 (**OWNER-REPORTED, unconfirmed**), not a new submission recommendation.

[Executive summary and nine-site table](docs/executive-summary.html) · [Current repository review, ranked research proposals and next gates](knowledge/47_repo_review_2026-10-28.md) · [H81 evidence and gates](evidence/h81_gates.json) · [H81 run card](registry/run_card_h81_2026-10-28.json) · [This review's JSON run card](registry/run_card_repo_review_2026-10-28.json) · [Three-pass review receipt](registry/review_passes_repo_review_2026-10-28.json).

Earlier experiment results below are historical records, not claims that this was the latest outcome.


## H81 outcome — negative; no eligible submission

**OK TO SUBMIT: NO — DO NOT SUBMIT. Estimated competition score: NOT ESTIMATED.** H81 did not publish a TIFF or receive slot approval. On the 25-km checkerboard holdout, `H81_JUNC_CG` scored HOLDOUT-DTI 0.111126 vs same-run `CTRL_BLIND_ABCD` 0.121443 (paired gain -0.010317, 95% CI [-0.012437, -0.006948], 95,188 withheld-positive occurrences; evaluator `gems25.metric.dti_binary`, alpha 0.2, beta 0.8, R=300 m). It also failed the primary `CTRL_H35` gate. Final dots exceeded the strict 70% registry overlap limit (72.20% vs H75).

The earlier public H81 empirical score band of 0.2250–0.2250 and its “kernel-matched optimum” band are **retracted**: the gated audit has zero matched historical rows, and local/model estimates are not leaderboard scores. The best supplied historical result among the nine focus sites remains GEMSDOE32 B2 at 0.2778, OWNER-REPORTED and unconfirmed; it is not a new or recommended submission. No new candidate was tested in this review.

[Executive summary and nine-site audit](docs/executive-summary.html) · [Current review and next steps](knowledge/47_repo_review_2026-10-28.md) · [H81 evidence and gates](evidence/h81_gates.json) · [H81 run card](registry/run_card_h81_2026-10-28.json).

<!-- CURRENT-REVIEW-2026-10-27 -->
## Current decision — 2026-10-27

> Historical summary, not the current run: follow its linked original receipts for evaluator version, withheld counts and confidence intervals. The shared evaluator has since been corrected; no historical score was re-computed here. “Proof” in older titles is analysis, not proof of hidden-label causation.

**Research-archive download: YES (inspection/testing only) · Competition-ready TIF: NO · OK TO SUBMIT: NO · weekly slot: NO — DO NOT SUBMIT.**

Latest verified **H79-CTHM+SGMC Crustal-Thermomechanical LOQO B2 research GeoTIFF** ([`gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed-zeros.tif`](docs/downloads/gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed-zeros.tif), content id `e7ad8a4bf3ed`, `37,654` dots, `0` NaNs across all `12,279,160` cells in `[0, 1]`; [NaN twin](docs/downloads/gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed-nan.tif); [ZIP](docs/downloads/gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed.zip); note `GEMSDOE25 H79-CTHM | no slot, not slot-approved; DO NOT SUBMIT | id e7ad8a4bf3ed | unscored`) is for inspection/testing only (**DO NOT SUBMIT**). Pre-registered at [`b59b129`](knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md), all 2,232 standalone feature canaries passed (`<= 0.8656 <= 0.90`): on virgin 25-km block draws `116–117`, **`H79_POE` (`0.07246`) beat single concatenated HGB on identical 81 features by `+0.01160` (95% CI `[+0.0001, +0.0287]`)**, and strike-aligned SGMC reactivation raised **`H79_POE_SGMC` to `0.08524` (`+0.01278`, `4/4` folds; `0.10059` on very-far `>20 px` faults)**; shipped 56-col zero-topography `H79_CRUSTAL_SGMC` scored `HOLDOUT-DTI = 0.05319` (`+36.2%` vs `H74_SUBSURF`), below `CTRL_H35 = 0.12369`. **Clears ALL 106 sparse rasters across the 109-raster post-merge portfolio** (`<= 58.02%` max vs `h19-c.tif`, `23.54%` vs `GEMSDOE32 B2`, `44.20%` vs `H75-DCHB-CG`, `44.17%` vs `H75-EU3D-POE65`, `29.14%` vs `H78`, `20.61%` vs `H79-scaffold`), while literal `70%` flags `r13` (**82.70%** geometric minimum at 37,654 dots; 100.00% actual) and `pindrop`. [Full H79-CTHM report, 9-site table & 0.2778 analysis (not causal proof)](knowledge/40_h79_cthm_poe_outcome_2026-10-27.md) · [H79-CTHM run card](registry/run_card_h79_cthm_2026-10-27.json) · [3 review passes](registry/review_passes_h79_2026-10-27.json).

Latest verified **H75-DCHB-CG Corridor-Gated Dual-Regime LOQO B2 research GeoTIFF** ([`gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif`](docs/downloads/gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif), content id `e035d75ca5d5`, `37,654` dots; [NaN twin](docs/downloads/gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-nan.tif); [ZIP](docs/downloads/gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5.zip); note `GEMSDOE25 H75-DCHB-CG | no slot, not slot-approved; DO NOT SUBMIT | id e035d75ca5d5 | unscored`) is for inspection/testing only (**DO NOT SUBMIT**). Pre-registered at [`12931bb`](knowledge/38_preregistered_h75_dchb_cg_2026-10-27.md), all 2,184 standalone feature canaries passed (`<= 0.8179 <= 0.90`): on **Exp 3 25-km Full Checkerboard `BlockHoldout`** (virgin draws `122–123`, `95,188` withheld `+`), **Gate G2 PASSED** — **`H75_CG_BLIND` (`0.12210`, 95% CI `[0.1036, 0.1376]`) beat `CTRL_SUBSURF` (`+0.02031`, `4/4` folds) AND `CTRL_BLIND_ABCD` (`+0.00384`, `3/4` folds)** and beat `CTRL_H35` on `L_valid=0` gap (`0.10816` vs `0.10602`), while pooled Slot Gate G1 vs `CTRL_H35` (`-0.00377`) remained negative. Cleared all `108` pre-merge sparse rasters (`68.58% <= 70%` vs `h23-a-6pct.tif`, `34.83%` vs B2), while post-merge full-footprint 116-raster audit flags literal `r13` (**82.70%** geometric minimum at 37,654 dots; 100.00% actual) and `72.34%` 3-px dot convergence vs concurrent `h75-eu3d-poe65` (surface Spearman `0.1106`). [Full H75-DCHB-CG report & 27-repo table](knowledge/40_h75_dchb_cg_outcomes_and_executive_summary_2026-10-27.md) · [H75-DCHB-CG run card](registry/run_card_h75_dchb_cg_2026-10-27.json) · [3 review passes](registry/review_passes_h75_dchb_cg_2026-10-27.json).

Concurrent verified **H75-EU3D-POE65 research GeoTIFF** ([`gems25-h75-eu3d-poe65-catfree-b2-37654-20261027-0a97fd71c3f3-zeros.tif`](docs/downloads/gems25-h75-eu3d-poe65-catfree-b2-37654-20261027-0a97fd71c3f3-zeros.tif), content id `0a97fd71c3f3`, `37,654` dots; [NaN twin](docs/downloads/gems25-h75-eu3d-poe65-catfree-b2-37654-20261027-0a97fd71c3f3-nan.tif); [ZIP](docs/downloads/gems25-h75-eu3d-poe65-catfree-b2-37654-20261027-0a97fd71c3f3.zip); note `GEMSDOE25 H75-POE65 | no slot, not slot-approved; DO NOT SUBMIT | id 0a97fd71c3f3 | unscored`) is for inspection/testing only (**DO NOT SUBMIT**). Pre-registered at [`3053f69`](knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md), all 1,520 standalone feature canaries passed (`<= 0.8038 <= 0.90`): **`H75_APRON` (`0.15118`) beat `CTRL_H35` (`0.14942`) by `+0.00176` (`4/4` folds PASS, 95% CI `[+0.00066, +0.00262]`)** on standard `Holdout`, and **`PM_DEAPRON` (`0.13942`) beat `CTRL_H35` (`0.13749`) by `+0.00193`** on 25-km Checkerboard `BlockHoldout`, while shipped CatFree `H75_POE65` (`0.08641` std / `0.03243` BlockHoldout) cleared all `106` rasters diagnostically (`35.77%` vs B2, `69.84% <= 70%` max sparse) but failed literal `r13` overlap (**82.70%** geometric minimum at 37,654 dots; 100.00% actual) and `CTRL_H35`. [Full H75 outcomes, 9-site table & 0.2778 analysis (not causal proof)](knowledge/39_h75_outcomes_and_executive_summary_2026-10-27.md) · [H75 run card](registry/run_card_h75_2026-10-27.json) · [Preflight](evidence/lane_preflight_2026-10-27.json) · [lane hypotheses](knowledge/39_lane_hypotheses_and_preflight_2026-10-27.md) · [continuation run card](registry/run_card_2026-10-27.json).

The existing [H78 zero-outside TIFF](docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif) passes a local format audit only, but **100% of its 43,550 dots overlap the r13 halo; DO NOT SUBMIT**. Prior H78 holdout, hard-coded score estimate and submit-ready claims are retracted as unsupported. [Correction](knowledge/38_h78_mhscf_and_phd_focus_sites_analysis_2026-10-27.md) · [format audit](evidence/h78_independent_reaudit_2026-10-27.json) · [literal lane re-audit](evidence/h78_literal_lane_reaudit_2026-10-27.json). The reported portal error “Predicted values must be in range [0, 1]” is consistent with earlier NaNs inside the mirrored footprint; the exact organizer validation behavior and acceptance of zero outside are unverified.

The [H79 random-dot scaffold](docs/downloads/gems25-h79-spatial-poisson-disc-b2-20261027-66772eeec27a-zeros.tif), added independently by a parallel PR, is also **DO NOT SUBMIT**: **99.8699% overlap r13** and **416 positives are on catalogue pixels**. No geological predictor or blocked holdout was used. [Mask audit](evidence/h79_independent_reaudit_2026-10-27.json) · [lane audit](evidence/h79_literal_lane_reaudit_2026-10-27.json) · [corrected card](registry/run_card_h79_2026-10-27.json).

GEMSDOE32's **0.2778 is OWNER-REPORTED**, not organizer-confirmed. B2 is exactly D2.8 pruned of 6,436 pixels within 200 m of the catalogue; sparsity and selective pruning could explain improved local credit/false-positive balance, but hidden-label causation and future scores are unknown. A fresh nine-site audit also finds GEMSDOE28's 0.2710 Rung30 winner differs from GEMSDOE31; only its lower-scoring R1 is identical to GEMSDOE31. [Executive summary & downloads](docs/executive-summary.html) · [pixel and source audit](evidence/focus_winners_reaudit_2026-10-27.json).

Prior archives, including [H74](docs/downloads/gems25-h74-rmps-subsurf-catfree-b2-37654-20261026-3751606e1ce5-zeros.tif) and [H72-3](docs/downloads/gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif), remain inspection-only and are not lane-cleared; [H74 prior analysis](knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md) · [H74 run card](registry/run_card_h74_2026-10-26.json). Read the standing owner brief below every session; Maximize P(Win) and Own the Outcome do not justify submitting a failed candidate.


## Current review and reproducibility

[Executive summary and nine-site downloads](docs/executive-summary.html) · [current review](docs/current-review.html) · [historical archive](docs/history.html) · [three review passes](registry/review_passes_2026-10-27.json) · [irregularities](registry/irregularities.json) · [sources](registry/sources.json). Scores without organizer receipts are owner-reported, not verified.

To reproduce the audits without accessing the competition website:

```sh
python scripts/restore_data.py --group core
python scripts/restore_data.py --group scored
python scripts/fetch_top_scorers.py
python scripts/audit_lane_feasibility.py --preregistration-commit 95149bc7373fc939313c1bb09cbc8940ed3fad78 --output evidence/lane_preflight_2026-10-27.json
python scripts/audit_focus_winners.py
python scripts/verify_candidate_independent.py docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif --require-zip
python scripts/check_lane_duplicates.py docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif --reference data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif  # exits 2: literal failure
python scripts/verify_candidate_independent.py docs/downloads/gems25-h79-spatial-poisson-disc-b2-20261027-66772eeec27a-zeros.tif --require-zip  # exits 2: catalogue mask
python scripts/check_lane_duplicates.py docs/downloads/gems25-h79-spatial-poisson-disc-b2-20261027-66772eeec27a-zeros.tif --reference data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif  # exits 2: literal failure
python scripts/build_readme.py && python scripts/build_site.py
```

The restored inputs are public owner mirrors. Their pinned hashes establish integrity, not organizer authenticity. No automatic organizer interaction or upload is authorized.

## Archived research files

These existing files may be downloaded for learning only. No file in this table is approved for a weekly slot; a format pass or content difference is not lane clearance.

| File | Content ID | Status |
|---|---|---|
| [gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif](docs/downloads/gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif) | `e035d75ca5d5` | Inspection only; no slot approval |
| [gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed-zeros.tif](docs/downloads/gems25-h79-cthm-crustal-sgmc-b2-37654-20261027-e7ad8a4bf3ed-zeros.tif) | `e7ad8a4bf3ed` | Inspection only; no slot approval |
| [gems25-h75-eu3d-poe65-catfree-b2-37654-20261027-0a97fd71c3f3-zeros.tif](docs/downloads/gems25-h75-eu3d-poe65-catfree-b2-37654-20261027-0a97fd71c3f3-zeros.tif) | `0a97fd71c3f3` | Inspection only; no slot approval |
| [gems25-h74-rmps-subsurf-catfree-b2-37654-20261026-3751606e1ce5-zeros.tif](docs/downloads/gems25-h74-rmps-subsurf-catfree-b2-37654-20261026-3751606e1ce5-zeros.tif) | `3751606e1ce5` | Inspection only; no slot approval |
| [gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros.tif](docs/downloads/gems25-h73-pm-deapron-sapd2-8-k3p0-20261026-1b7533ebb62b-zeros.tif) | `1b7533ebb62b` | Inspection only; no slot approval |
| [gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif](docs/downloads/gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif) | `88bbebfe79b4` | Inspection only; no slot approval |
| [gems25-h72-mbsp-mtg-catfree-b2-37654-20261026-1d7c1e9ea55f-zeros.tif](docs/downloads/gems25-h72-mbsp-mtg-catfree-b2-37654-20261026-1d7c1e9ea55f-zeros.tif) | `1d7c1e9ea55f` | Inspection only; no slot approval |
| [gems25-h72-pttg-deapron-sapd2-8-k3p0-20261026-a07ef071c49e-zeros.tif](docs/downloads/gems25-h72-pttg-deapron-sapd2-8-k3p0-20261026-a07ef071c49e-zeros.tif) | `a07ef071c49e` | Inspection only; no slot approval |
| [gems25-obj-bin-greedy-k3p5-20261026-3646faf70507-zeros.tif](docs/downloads/gems25-obj-bin-greedy-k3p5-20261026-3646faf70507-zeros.tif) | `3646faf70507` | Inspection only; no slot approval |
| [gems25-apfl2-h35plus-apfl-b2-sapd2-4-k3p5-20261026-2e9e4189f554-zeros.tif](docs/downloads/gems25-apfl2-h35plus-apfl-b2-sapd2-4-k3p5-20261026-2e9e4189f554-zeros.tif) | `2e9e4189f554` | Inspection only; no slot approval |
| [gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif](docs/downloads/gems25-h71-hgpc-blind-b2-sapd3-k3p5-20261026-9eb0c31e5149-zeros.tif) | `9eb0c31e5149` | Inspection only; no slot approval |
| [gems25-apfl-piedmont-flexure-s3p0-k3p5-20261026-8aebdab87158-zeros.tif](docs/downloads/gems25-apfl-piedmont-flexure-s3p0-k3p5-20261026-8aebdab87158-zeros.tif) | `8aebdab87158` | Inspection only; no slot approval |
| [gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif](docs/downloads/gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif) | `da617550a0e9` | Inspection only; no slot approval |
| [gems25-h38-ospc-submod-20261025-680d62616417-zeros.tif](docs/downloads/gems25-h38-ospc-submod-20261025-680d62616417-zeros.tif) | `680d62616417` | Inspection only; no slot approval |
| [gems25-h36-spigm-subsurface-submod300-20261025-3937b96ce366-zeros.tif](docs/downloads/gems25-h36-spigm-subsurface-submod300-20261025-3937b96ce366-zeros.tif) | `3937b96ce366` | Inspection only; no slot approval |
| [gems25-h38-greedy-credit-k3p5-20261025-18de99d38bb0-zeros.tif](docs/downloads/gems25-h38-greedy-credit-k3p5-20261025-18de99d38bb0-zeros.tif) | `18de99d38bb0` | Inspection only; no slot approval |
| [gems25-mscr-multiscale-crest-sapd2-4-k3p5-20261025-dd2bb4b09cd2-zeros.tif](docs/downloads/gems25-mscr-multiscale-crest-sapd2-4-k3p5-20261025-dd2bb4b09cd2-zeros.tif) | `dd2bb4b09cd2` | Inspection only; no slot approval |
| [gems25-xg1-crossgrad-sapd2-4-k3p5-20261025-52e65fb521f9-zeros.tif](docs/downloads/gems25-xg1-crossgrad-sapd2-4-k3p5-20261025-52e65fb521f9-zeros.tif) | `52e65fb521f9` | Inspection only; no slot approval |
| [gems25-kdc-b2-plus-hgb-complement-55374-20261025T211001Z-f74e9238cc1c-zeros.tif](docs/downloads/gems25-kdc-b2-plus-hgb-complement-55374-20261025T211001Z-f74e9238cc1c-zeros.tif) | `f74e9238cc1c` | Inspection only; no slot approval |
| [gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-zeros.tif](docs/downloads/gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-zeros.tif) | `c213681203f6` | Inspection only; no slot approval |
| [gems25-gem-fuse1-blind-magnetics-prune2-20261025-c2097a554ef2-zeros.tif](docs/downloads/gems25-gem-fuse1-blind-magnetics-prune2-20261025-c2097a554ef2-zeros.tif) | `c2097a554ef2` | Inspection only; no slot approval |
| [gems25-h31-control-sapd2-4-k3p5-bde7-20261025-9edd6bed8268-zeros.tif](docs/downloads/gems25-h31-control-sapd2-4-k3p5-bde7-20261025-9edd6bed8268-zeros.tif) | `9edd6bed8268` | Inspection only; no slot approval |
| [gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif](docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | `e56ea318af89` | Inspection only; no slot approval |
| [gems25-h31-1-flank-subscarp-sapd24-20261025-40bfe1d5b1c5-zeros.tif](docs/downloads/gems25-h31-1-flank-subscarp-sapd24-20261025-40bfe1d5b1c5-zeros.tif) | `40bfe1d5b1c5` | Inspection only; no slot approval |
| [gems25-h35-resmag-tip-sapd2-4-k3p5-20261025-d5d4cde1e719-zeros.tif](docs/downloads/gems25-h35-resmag-tip-sapd2-4-k3p5-20261025-d5d4cde1e719-zeros.tif) | `d5d4cde1e719` | Inspection only; no slot approval |
| [gems25-cf1-transverse-negative-20261025-22e2f9eddad9-zeros.tif](docs/downloads/gems25-cf1-transverse-negative-20261025-22e2f9eddad9-zeros.tif) | `22e2f9eddad9` | Inspection only; no slot approval |
| [gems25-h36-tiltzero-coincide-sapd2-4-k3p5-20261025-92562b7b7fea-zeros.tif](docs/downloads/gems25-h36-tiltzero-coincide-sapd2-4-k3p5-20261025-92562b7b7fea-zeros.tif) | `92562b7b7fea` | Inspection only; no slot approval |
| [gems25-h37-doc-dipoffset-sapd2-4-k3p5-20261025-558c08ce13bf-zeros.tif](docs/downloads/gems25-h37-doc-dipoffset-sapd2-4-k3p5-20261025-558c08ce13bf-zeros.tif) | `558c08ce13bf` | Inspection only; no slot approval |

Historical records: [H28 preregistration](knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md) · [objective outcomes](knowledge/31_objective_outcomes_and_executive_summary_2026-10-26.md) · [H74 outcomes](knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md). Old records are preserved as historical evidence and may be superseded by the current lane and correction receipts.

## Owner prompts and standing briefs — read each session

The original brief is preserved below exactly as saved. The latest session handoff was condensed; we do not claim the condensed text is a verbatim transcript.

<details><summary>Current owner brief 2026-10-28 — normalized, not verbatim</summary>

````text
# Active owner brief — normalized, not verbatim (28 October 2026)

Read README and AGENTS at each session start. Goal: a genuinely unique high-performing fault-prediction GeoTIFF, automated exact-file validation, obvious download/submit status and executive submission instructions. Learn from the nine focus sites GEMSDOE24/25/27/28/30/31/32/33/36 and broader sibling results including GEMSDOE92, KANLER, WBG, EUG, GINNY, karage, Apart and SASS projects. The full earlier owner brief remains archived verbatim below this normalized update; this is not a new verbatim transcript.

Highest urgency: **MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.** Make clear if it is actually OK to submit. This request remains unfulfilled unless every mandatory scientific and strict novelty gate passes. Do not fabricate a TIFF, forecast or approval to satisfy the wording.

Before implementing, rank 3–5 geological hypotheses with layers, signatures, missing-catalogue rationale, differences from existing methods, non-fault mimics, expected benefit (qualitative/unknown unless measured), cost and checked obtainable official free data. Reuse shared cached features, whole-segment buffered hide-and-recover, visible-only catalogue features, exact visible masking, pooled DTI (alpha .2, beta .8, triangular 300 m) and shared writer. Test each feature alone for inverted/value/missingness AUC; above .90 is presumptive leakage. Compare to same-run best; require positive paired CI before selector consideration.

Stay in one explicit lane. Surface |rank correlation| above .90 or final-dot overlap above 70% within 3 px of ANY registry raster is a duplicate and stop. No dense-reference exception or changing the budget to evade the audit. The current message refers to an assigned method paragraph but supplies none: proposed diagnostic work is not an owner assignment. Report that uncertainty. A negative result is a deliverable.

Label local metrics HOLDOUT-DTI with evaluator/version, withheld positives and 95% CI. ORGANIZER-CONFIRMED requires a submission-page receipt. Supplied 0.2778/0.3195/0.4413 and all other historical scores are OWNER-REPORTED until supported. A projection is never a score. Explain GEMSDOE32 B2's exact pixel lineage without inventing hidden-label causation. Do not promise a high leaderboard score from a proxy.

Stop at three experiments or two hours. No slot selection or automated uploads; promotion is a separate selector step within the verified weekly cap. Follow the standing no-automated-DrivenData-access policy. No credentials in chat. Use pinned public mirrors when possible; byte integrity is not organizer provenance. Prevent NaN/Inf/range errors and validate single-band CRS/shape/transform, catalogue mask, unique identity, ZIP and a note at most 140 characters.

Keep sources/knowledge auditable; no claim of deep official-source verification for unread or unavailable sources. Competition target is unmapped faults, not confirmed geothermal vents. Respect Maximize P(Win) and Own the Outcome: own errors and negative findings. Build clean consistent GitHub Pages with nine-site filenames, score estimates explicitly unknown when uncalibrated, novelty/readiness and a dated source feed. Work autonomously, do three cumulative review passes, create and merge a PR from the fixed session branch, report exact remaining limitations and next steps. Do not claim full completion if no gate-cleared TIFF exists.
````

</details>

<details><summary>Owner brief 2026-10-27 (H75-DCHB-CG session) — saved as verbatim</summary>

````text
Review the repo.

I want to focus on  the highest scoring submissions from the following sites, GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36.  I want an executive summary on every site that is clear and obvious which is the best submission to submit to obtain a high score on the leaderboard.  It should also be unique and not an exact duplicate of any previous submission that is the same as below.  Keep iterating and testing until we have the highest scoring submission to download and submit.

We should be able to estimate the score for a submission.  I want a table in the executive summary that clearly lists what file to download, what the estimate score is, and whether it is a unique submission unlike any of the other GEMDOE sites listed below.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py) and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)

gems-submission-20260926T163915Z-237f0063: 0.0343

....

[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)

Hedge-v2_submission: 0.1563

....

[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)

2314b599: 0.0107

....

[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)

gems-structural-area06-v1: 0.0202

....

[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)

H19-C_20260930T212401Z_c11e495e: 0.0297

....

[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)

h19-4-reference-20260930-691e4dfa: 0.1894

....

[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859

....

[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748

....

[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)

h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE26/](https://buffedlizard55-lab.github.io/GEMSDOE26/)

dilcond-oof-v1-20261003-47629f496133-nan: 0.1223

....

[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

....

[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

....

[https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html)

h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778

....

[https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html)

h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418

....

[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

....

[https://buffedlizard55-lab.github.io/GEMSDOE37/](https://buffedlizard55-lab.github.io/GEMSDOE37/)

h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193

....

[https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html)

D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763

....

[https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html)

xscale-worm-persistence-20261006T000541Z-nan: 0.0581

....

[https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html)

sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: 0.0424

....

[https://buffedlizard55-lab.github.io/GEMSDOE45/](https://buffedlizard55-lab.github.io/GEMSDOE45/)

h51-km-faultzone-20261006-zeros: 0.0106

....

[https://buffedlizard55-lab.github.io/GEMSDOE49/](https://buffedlizard55-lab.github.io/GEMSDOE49/)

gate_ortho_w0.25-40k-20261006T213721Z-nan: 0.2376

....

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

....

[https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html)

efd28-repro-20261003-1cc7dc534d51-nan: 0.2600

repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041

sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512

wormrank-d28-20261003-59dcaf6dd11d-zeros:0.2560

wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532

xfit-c0-habitat-20261003-ca879db0089a-zeros:0.0439

xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros: 0.0356

....

[https://buffedlizard55-lab.github.io/GEMSDOE46/](https://buffedlizard55-lab.github.io/GEMSDOE46/)

r11f-scarp-radiometric-fusion-00e049b51218-zeros:0.1589

r12-scarp-rad-concordance-23e807e2de9f-zeros: 0.0843

....

[https://buffedlizard55-lab.github.io/GEMSDOE39/](https://buffedlizard55-lab.github.io/GEMSDOE39/)

h40-e-disc-h40e-30k-zeros: 0.0339

....

[https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html)

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: 0.0355

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard: 0.0397

h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros: 0.0984

....

[https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html)

h42-submission-primary: 0.0245

....

[https://buffedlizard55-lab.github.io/GEMSDOE44/docs/](https://buffedlizard55-lab.github.io/GEMSDOE44/docs/)

h46-twostageAB_20261006T160000Z_b0cfe956-zeros: 0.0715

....

[https://buffedlizard55-lab.github.io/GEMSDOE47/](https://buffedlizard55-lab.github.io/GEMSDOE47/)

h60-lidarscarp-s2p0-20261007-nanoutside: 0.0430

....

[https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html)

h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8: 0.2296

....

[https://buffedlizard55-lab.github.io/GEMSDOE50/](https://buffedlizard55-lab.github.io/GEMSDOE50/)

h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite: 0.0764

....

[https://buffedlizard55-lab.github.io/GEMSDOE51/](https://buffedlizard55-lab.github.io/GEMSDOE51/)

h53-twostage-20261008T040951Z-9a0b32c871: 0.1047

....

[https://buffedlizard55-lab.github.io/GEMSDOE52/](https://buffedlizard55-lab.github.io/GEMSDOE52/)

h97b-candidate: 0.0856

....

[https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html)

h8-tiprelay-ridgeconcord-pr2-n80000-20261009-49bec522-zeros: 0.0159

....

[https://buffedlizard55-lab.github.io/GEMSDOE54/docs/](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/)

h54c-manifest-edge-20261009T025732Z-73454bc5:0.0449

....

[https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html)

tensor_full-n16000-sep3-20261009T211747Z-nan: 0.0290

....

[https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html)

h56-final-dotted-ridge-d2p8-20261009T190421Z:0.0658

....

[https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html)

h57r-joint-strata-38000dots-20261010T214547Z-00cf5b2066f1-zeros: 0.0254

....

[https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html)

ml-binary-ridge-20261012T000000Z: 0.0180

....

[https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html)

h59j-coherence-consensus-dotted-20261011T043000Z: 0.0499

....

[https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html)

h73-chi-coherent-corridor-12000-20261011T195818Z-zeros: 0.0351

....

[https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html)

h61a-basement-step-20000dots-20261011T012029Z-eb2ae4bb024b-zeros: 0.0009

h61o-vardepth-none-40000dots-20261011T160711Z-28d4fac611ea-zeros-zeros:0.0751

....

[https://buffedlizard55-lab.github.io/62GEMSDOE/](https://buffedlizard55-lab.github.io/62GEMSDOE/)

datum-lahontan-strain-gauge-defensible-440dots-zeros: 0.0000

....

[https://buffedlizard55-lab.github.io/GEMSDOE63/](https://buffedlizard55-lab.github.io/GEMSDOE63/)

cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-zeros: 0.2303

....

[https://buffedlizard55-lab.github.io/GEMSDOE64/](https://buffedlizard55-lab.github.io/GEMSDOE64/)

h64-lidar-scarp-cv-20261011T220000Z:0.0383

....

[https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html)

sar-em-propensity-half-20261011T223500Z-5e4660cd-zeros:0.0431

....

[https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html)

gems66-lidar03-cvretrain-reliefdecile-37654dots-20261020T190152Z-zeros:0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE67/](https://buffedlizard55-lab.github.io/GEMSDOE67/)

h67a-orientip-lane-29447dots-20261012T021226Z-allfinite:0.0356

ovtr-ml-cover-tau3p0-20261012-nan:0.1426

....

[https://buffedlizard55-lab.github.io/GEMSDOE68/](https://buffedlizard55-lab.github.io/GEMSDOE68/)

gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-nan:0.0437

gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-zeros: 0.0437

....

[https://buffedlizard55-lab.github.io/GEMSDOE69/](https://buffedlizard55-lab.github.io/GEMSDOE69/)

gems69-joint-relayramp-pullapart-38669-20261020T201504Z-f29b6df5:0.0053

....

[https://buffedlizard55-lab.github.io/GEMSDOE70/](https://buffedlizard55-lab.github.io/GEMSDOE70/)

gems70-p5-dual-submod300-oof38k-20261020:0.2478

....

[https://buffedlizard55-lab.github.io/GEMSDOE71/](https://buffedlizard55-lab.github.io/GEMSDOE71/)

gems71-hydro-conduit-38800-20261020T120000Z-zeros: 0.0558

....

[https://buffedlizard55-lab.github.io/GEMSDOE72/](https://buffedlizard55-lab.github.io/GEMSDOE72/)

gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-zeros: 0.0492

....

[https://buffedlizard55-lab.github.io/GEMSDOE73/](https://buffedlizard55-lab.github.io/GEMSDOE73/)

gems73-h73-mcsc-seamfree-blakely-37654dots-20261021T073716Z-b27ac445-zeros: 0.1917

....

[https://buffedlizard55-lab.github.io/GEMSDOE74/](https://buffedlizard55-lab.github.io/GEMSDOE74/)

gemsdoe74-triregime-radon-piedmont-37654-20261021T051000Z-zeros:0.0669

....

[https://buffedlizard55-lab.github.io/GEMSDOE75/](https://buffedlizard55-lab.github.io/GEMSDOE75/)

gems75-trlt-radon-loco-ridge-20261021-zeros:0.1627

....

[https://buffedlizard55-lab.github.io/GEMSDOE76/](https://buffedlizard55-lab.github.io/GEMSDOE76/)

gems76_h76_3_geotherm_tilt_axial_submod_20261021_zeros:0.1555

gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros:0.2343

....

[https://buffedlizard55-lab.github.io/GEMSDOE77/](https://buffedlizard55-lab.github.io/GEMSDOE77/)

gems85-h85-edti-collar35-skel-r33-20261021-d97b248e-zeros:0.0964

....

[https://buffedlizard55-lab.github.io/GEMSDOE78/](https://buffedlizard55-lab.github.io/GEMSDOE78/)

gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros:0.1564

....

[https://buffedlizard55-lab.github.io/GEMSDOE79/](https://buffedlizard55-lab.github.io/GEMSDOE79/)

gems79-tilt-ring-100000dots-20261022T212135Z-50a5d7498c71-zeros:0.0005

....

[https://buffedlizard55-lab.github.io/GEMSDOE80/](https://buffedlizard55-lab.github.io/GEMSDOE80/)

gemsdoe80-h80g-choquet-tworegime-20261022T000000Z-zeros:0.0943

....

[https://buffedlizard55-lab.github.io/GEMSDOE81/](https://buffedlizard55-lab.github.io/GEMSDOE81/)

gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros:0.0041

....

[https://buffedlizard55-lab.github.io/GEMSDOE82/](https://buffedlizard55-lab.github.io/GEMSDOE82/)

gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros:0.1886

....

[https://buffedlizard55-lab.github.io/GEMSDOE83/](https://buffedlizard55-lab.github.io/GEMSDOE83/)

gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros:0.0573

....

[https://buffedlizard55-lab.github.io/GEMSDOE84/](https://buffedlizard55-lab.github.io/GEMSDOE84/)

gems84-h84-kthm-tworegime-58000px-20261022T235900Z-zeros:0.0132

....

[https://buffedlizard55-lab.github.io/GEMSDOE85/](https://buffedlizard55-lab.github.io/GEMSDOE85/)

gemsdoe85-hjcd-ventbridge-submod-zeros: 0.1110

....

[https://buffedlizard55-lab.github.io/GEMSDOE86/](https://buffedlizard55-lab.github.io/GEMSDOE86/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE87/](https://buffedlizard55-lab.github.io/GEMSDOE87/)

h87-h87-cmgep-20261022T060000Z-8f394f43:0.0500

....

[https://buffedlizard55-lab.github.io/GEMSDOE88/](https://buffedlizard55-lab.github.io/GEMSDOE88/)

gems88-bpwd88-baranov-worm-conduit-37654-20261025-b8543782-zeros-DO-NOT-SUBMIT:

....

[https://buffedlizard55-lab.github.io/GEMSDOE89/](https://buffedlizard55-lab.github.io/GEMSDOE89/)

gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros:0.0301

....

[https://buffedlizard55-lab.github.io/GEMSDOE90/](https://buffedlizard55-lab.github.io/GEMSDOE90/)

gems90-cnc-35000dots-20261024T084324Z:0.0749

....

[https://buffedlizard55-lab.github.io/GEMSDOE91/](https://buffedlizard55-lab.github.io/GEMSDOE91/)

gems91-s17-cwpc-e3-37654dots-20261025T150000Z-4d124f1d-zeros:0.1367

gems91-s17-lftg-20261025T160014Z-7b6bf90844-zeros:0.1823

gems91-S18-UNIQUE-curvtilt-20000dots-20261025T182858Z-29db2405:

gems91-s22-omtj-e1-20261026-a99b8923f0-zeros:0.0298

....

[https://buffedlizard55-lab.github.io/GEMSDOE92/](https://buffedlizard55-lab.github.io/GEMSDOE92/)

gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros:0.0255

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

gems24-gvc1-negative-geothermal-lineament-submod-20261025-abe8e51c719d-zeros:0.0859

....

[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros:0.0742

....

[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886-allfinite:0.2190

gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite:0.2250

....

[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

gems28-s18-mxtp-20261025-3e95505c011a-allfinite:0.0217

gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite:0.0206

....

[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

gems30-MSDB1-edge44090-20261025-e7856ec3f14a:0.1462

....

[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

gemsdoe33-s33-seisdil-strain-seismicity-37654-20261026-3463540a7e02-zeros:0.0963

....

[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros: 0.1647

....

[https://kanlerxz87-cyber.github.io/KANLERGEMSDOE3/docs/index.html](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE3/docs/index.html)

:

....

[https://kanlerxz87-cyber.github.io/KANLERGEMSDOE1/](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE1/)

:

....

[https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/](https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/)

kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros:

....

[https://eugboogieman123-ops.github.io/EUGGEMSDOE3/](https://eugboogieman123-ops.github.io/EUGGEMSDOE3/)

:

....

[https://eugboogieman123-ops.github.io/EUGGEMSDOE2/](https://eugboogieman123-ops.github.io/EUGGEMSDOE2/)

:

....

[https://eugboogieman123-ops.github.io/EUGGEMSDOE1/](https://eugboogieman123-ops.github.io/EUGGEMSDOE1/)

:

....

[https://wingbangboozle1-lang.github.io/WBGGEMSDOE3/docs/index.html](https://wingbangboozle1-lang.github.io/WBGGEMSDOE3/docs/index.html)

:

....

[https://wingbangboozle1-lang.github.io/WBGGEMSDOE2/docs/](https://wingbangboozle1-lang.github.io/WBGGEMSDOE2/docs/)

:

....

[https://wingbangboozle1-lang.github.io/WBGGEMSDOE1/docs/index.html](https://wingbangboozle1-lang.github.io/WBGGEMSDOE1/docs/index.html)

:

....

[https://ginnymcfiner23-ux.github.io/GINNYGEMSDOE3/](https://ginnymcfiner23-ux.github.io/GINNYGEMSDOE3/)

:

....

[https://ginnymcfiner23-ux.github.io/GINNYGEMSDOE2/](https://ginnymcfiner23-ux.github.io/GINNYGEMSDOE2/)

:

....

[https://ginnymcfiner23-ux.github.io/GINNYGEMSDOE1/](https://ginnymcfiner23-ux.github.io/GINNYGEMSDOE1/)

:

....

I think it makes sense that in order for a submission to be validated that it needs to pass certain high scoring validation gates before confirming whether a file is unique and can be submitted for scoring.

The following is the leaderboard for the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See below for more links and information related to the competition:

[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)

[https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

[https://gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/)

[https://epsg.io/32611](https://epsg.io/32611)

[https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195	is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)

“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.

Own the Outcome

We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.



Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission

File to submitNo file chosen

You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.

Note (optional)

A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow.[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)

Get familiar with the problem through the overview and problem description,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want to reference additional resources available on the about page,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).

Download the data from the data,[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), tab.

Create and train your own model. This reference solution,[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.

[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (verified redirect to login)

See below for links from the above site.  See attached files for links from the above site.

[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (requires login) to data/

See links below for competition data:

[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0)

[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0)

[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0)

[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0)

[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0)

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.

Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.

Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.
````

</details>

<details><summary>Current 2026-10-27 session scope — condensed, not verbatim</summary>

````text
# Current Session Standing Prompt — 2026-10-27 (Read Before Every Session)

Review the repo.

1. FOCUS SITES & PORTFOLIO AUDIT:
   Focus on the highest scoring submissions from the nine focus sites:
   GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36
   (plus broader sibling context GEMSDOE..GEMSDOE92, KANLERGEMSDOE1..3, EUGGEMSDOE1..3, WBGGEMSDOE1..3, GINNYGEMSDOE1..3).
   Provide a clear, unmistakable executive summary table listing for every site:
   - Exact file to download / historical reference file
   - Properly labeled score / holdout proxy (HOLDOUT-DTI with evaluator version, withheld positives, 95% CI; or OWNER-REPORTED vs ORGANIZER-CONFIRMED; never write a projection as a score; Estimated competition score = NOT ESTIMATED unless organizer-confirmed)
   - Uniqueness vs all GEMSDOE registry rasters
   - Explicit readiness verdict: OK TO DOWNLOAD vs OK TO SUBMIT (YES / NO — DO NOT SUBMIT)

2. HIGHEST URGENCY MANDATE — UNIQUE & VALIDATED GEOTIFF:
   MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.
   - Validate automatically without human intervention (single-band float32, EPSG:32611, 3730 x 3292, geotransform (100, 0, 243350, 0, -100, 4508550), 0 NaN/Inf inside 5,167,373-px footprint, values strictly in [0, 1] fixing "Predicted values must be in range [0, 1]", unique content-addressed filename, note <= 140 / <= 120 chars).
   - Provide one-click download at the very beginning of the site and an executive-summary subpage explaining exactly how to submit on DrivenData.

3. PARALLEL-RUN PROTOCOL (ITEMS 1–6):
   - 1. LANE: Stay inside one method lane. Check continuous surface BEFORE placement AND final binary dots against all registry rasters. |Spearman| > 0.90 or > 70% of candidate dots within 3 px of a registry raster => log duplicate and stop.
   - 2. REUSE, DON'T REBUILD: Use shared cached feature stack, Holdout / BlockHoldout, dti_binary (alpha=0.2, beta=0.8, R=300 m = 3 px triangular kernel), and submission.py. Derive every catalogue feature strictly from visible faults; mask visible faults pixel-exactly.
   - 3. LABEL EVERY NUMBER: HOLDOUT-DTI (evaluator, withheld positives, 95% CI) or ORGANIZER-CONFIRMED (or OWNER-REPORTED user claim). A projection is never written as a score.
   - 4. LEAKAGE CANARY: Test each feature alone on the holdout before trusting any result; AUC > 0.90 is presumptive leakage.
   - 5. RUN CARD: Emit one complete JSON card (hypothesis, mechanism, named non-fault mimic, holdout DTI + CI, correlation/overlap vs registry, raster sha256, validator output, submission name + note <= 140 chars, verdict promote / negative). Negative results are deliverables.
   - 6. BUDGET: Stop after 3 experiments or 2 hours. Do not pick submissions: promotion to a real weekly slot is a separate selector step.

4. PHD FORENSIC PROOF & NOVEL GEOLOGICAL HYPOTHESES:
   - Study, analyze, and prove at a PhD level why GEMSDOE32 h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros achieved 0.2778 (OWNER-REPORTED) and how to surpass 0.2778 (noting unverified overall leaderboard figures 0.4413 and 0.3195).
   - Before implementing, propose and rank 3–5 untried geological hypotheses naming layers, physical signature/transform, why missed by USGS/INGENIOUS, distinction from repo code, non-fault mimic, planning ΔDTI bracket, cost, and verified obtainability of any free official external data.
   - Work on next steps from previous sessions first, complete data placement autonomously (`scripts/download_competition_data.sh` / `restore_data.py` + `prepare_data.py`), never automate access to drivendata.org, uphold Arena Core Values (`Maximize P(Win)` and `Own the Outcome`), run 3 verification passes, flag all irregularities, and open + merge the PR onto `main`.

5. OFFICIAL VERIFIED REFERENCE LINKS (MANUAL REVIEW):
   - Competition overview & metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
   - Competition leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/
   - Rules PDF (NREL/NLR): https://docs.nlr.gov/docs/fy26osti/96647.pdf
   - Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution
   - USGS GeoDAWN: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
   - GBCGE INGENIOUS: https://gbcge.org/current-projects/ingenious/
   - DOE GDR #1391: https://gdr.openei.org/submissions/1391
   - EPSG:32611: https://epsg.io/32611
   - Tversky index: https://en.wikipedia.org/wiki/Tversky_index
````

</details>

<details><summary>Current standing protocol — normalized, not verbatim</summary>

````text
# Current owner prompt — 2026-10-26, normalized standing brief

This is a **normalized restatement, not a claimed verbatim transcript** of the current long message. Historical verbatim/reconstructed prompt archives remain unchanged in this repo. Read this brief and the README before every session. Repeated passages are consolidated; user-supplied score claims are preserved as claims in the focused review and existing score ledger, not organizer receipts.

## Highest urgency — owner's wording

> MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

The goal is a genuinely new, high-scoring competition GeoTIFF, with a one-click download at the beginning of the site, a unique name and a note of at most 140 characters. Validate through the project without relying on a human inspector. Prevent the portal error **“Predicted values must be in range [0, 1]”**. Match the official single-band format's CRS, shape and geotransform; keep every prediction in the footprint finite and in range. An executive-summary subpage must explain exactly how to submit. Format validation is not authorization or expected leaderboard performance.

## Focus and scientific questions

Review this repo and the strongest supplied historical submissions from **GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33 and GEMSDOE36**. Give an executive finding for every site, including the strongest supplied result and whether any file is actually eligible as a new submission. Learn from all supplied sibling results through GEMSDOE92; do not pretend to have freshly verified unexamined websites.

Explain why GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` reportedly obtained **0.2778**, and whether a genuinely new candidate can improve on it. The prompt supplies conflicting overall-leader values **0.4413** and **0.3195**; neither is an organizer-confirmed current snapshot here.

Before implementation, propose and rank **3–5 untried geological hypotheses**. Each must identify layers, physical signature/transform, catalogue-missing-fault rationale, distinction from existing code, non-fault mimic, expected improvement (clearly a planning judgment, not a score) and cost. Check actual obtainable free official data before calling an externally dependent idea viable. Investigate geothermal science, but do not substitute vent labels for the competition's fault-label task. Store auditable evidence and knowledge for future work.

## Parallel-run protocol — mandatory constraints

1. Stay within one method lane. The current message refers to a “single method paragraph below” but does not actually supply a separate method. Record any provisional lane choice explicitly. If surface/final rank correlation exceeds 0.90 in magnitude or more than 70% of candidate dots are within 3 px of any registry raster's dots, log a duplicate and stop. Check before placement and on final dots. Do not silently waive dense-registry cases.
2. Reuse the shared cached features, hide-and-recover evaluator and submission writer. The actual equivalents in this checkout are `gems25.holdout`, `gems25.experiment`, `gems25.metric` and `gems25.submission`, not files literally named `evaluate_holdout.py` / `submission_writer.py`. Hide whole fault components with a buffer, derive catalogue features only from visible faults, mask visible pixels exactly, and report pooled DTI with alpha 0.2, beta 0.8 and the 300 m triangular kernel. Fix shared bugs once, not in private forks.
3. Distinguish HOLDOUT-DTI (evaluator version, withheld-positive count, 95% CI) from ORGANIZER-CONFIRMED scores backed by receipts. The existing user-provided figures must remain OWNER-REPORTED rather than being forced into a false organizer-confirmed label. Geometric counts and diagnostic AUC are not DTI scores. Projections never become scores.
4. Test every feature alone on the holdout; AUC above 0.90 is presumed leakage until resolved. Include inverted and missingness discrimination. An untested feature cannot receive an implicit pass.
5. End with one JSON run card: hypothesis, mechanism, named non-fault mimic, holdout DTI and CI, registry correlation/overlap, raster SHA-256, validator output, name and short note, promote/negative verdict. Unknown/not-created fields are null, never invented. Negative results are deliverables.
6. Stop after 3 experiments or 2 hours. Do not spend a weekly slot or choose a submission for a real slot. Promotion is a separate selector step within the verified weekly cap. Recompute the best comparable control in the same run and require a genuine paired holdout improvement before consideration.

The request to always create a new TIF can conflict with a duplicate-lane stop. Do not evade this by copying, jittering, renaming or blessing a failed file. Explicitly report the unfulfilled artifact requirement if the safety/scientific gates stop the run.

## Autonomous execution, sources and review

Work on prior-session next steps first. Use **Maximize P(Win)** and **Own the Outcome** as decision principles: prefer verified leverage, own engineering failures, and preserve negative results. Work autonomously without asking for secrets or manual data placement when pinned public mirrors are available. Use free official sources for external data; record bytes/schema/coverage/license verification separately from page availability. Provide official links for manual review, flag irregularities, and never claim all lines or sources are independently verified when they are not.

Official reference links: [competition](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [official reference repository](https://github.com/drivendataorg/gems-prize-reference-solution), [rules](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [GDR 1391](https://gdr.openei.org/submissions/1391), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), [EPSG:32611](https://epsg.io/32611). The historical brief preserves the supplied Dropbox links. Links are not assertions that they were fetched or authenticated this session. Respect the repo's no-automated-DrivenData-access policy.

Build a clean GitHub Pages site with an immediate status, downloadable approved artifacts only when earned, executive instructions, evidence/source tables and an honestly dated source feed. Keep the prompt and core values in README as the standing starting point. Complete three cumulative passes: implementation and verification; bug/assumption/edge-case review and fixes; full request reconciliation and remaining limitations. Open a PR from the fixed session branch, wait for checks, merge onto main through the explicit GitHub PR number, and report only verified merge/deployment status. Do not claim that this work fully met the request if no gate-cleared novel TIF was produced.
````

</details>

<details><summary>Owner brief 2026-10-26 — saved as verbatim</summary>

````text
Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py) and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)

gems-submission-20260925T001403Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)

gems6_hgb88-topk03_33cec71ff0: 0.0286

....

[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)

pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193

pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830

pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)

gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560

....

[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)

gems-submission-20260926T163915Z-237f0063: 0.0343

....

[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)

gems-submission-20260926T175114Z-7f00890a: 0.1563

....

[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)

lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461

....

[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)

Hedge-v2_submission: 0.1563

....

[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)

2314b599: 0.0107

....

[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)

gems-structural-area06-v1: 0.0202

....

[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)

r7-nms3-dem10-scarp_0c9199f14e62:0.1294

r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294

....

[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)

gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782

....

[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)

GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020

....

[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)

17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187

....

[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)

H19-C_20260930T212401Z_c11e495e: 0.0297

....

[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)

h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894

h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922

....

[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)

h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461

h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921

H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280

h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839

....

[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)

20261001_r13-lattice-s5_v2_nan-outside:0.0904

....

[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)

h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855

h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976

h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360

....

[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)

h19-4-reference-20260930-691e4dfa: 0.1894

....

[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)

h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890

h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859

....

[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)

h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002

h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748

....

[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)

h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352

....

[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)

h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477

....

[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)

dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE26/](https://buffedlizard55-lab.github.io/GEMSDOE26/)

dilcond-oof-v1-20261003-47629f496133-nan: 0.1223

....

[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)

topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449

....

[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)

d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600

....

[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)

h27-4-solo-d28-20261004-8acb75e1-nan:0.2708

....

[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)

h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632

....

[https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html)

h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778

....

[https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html)

h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418

....

[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)

anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750

....

[https://buffedlizard55-lab.github.io/GEMSDOE37/](https://buffedlizard55-lab.github.io/GEMSDOE37/)

h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193

....

[https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html)

D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763

....

[https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html)

xscale-worm-persistence-20261006T000541Z-nan: 0.0581

....

[https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html)

sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: 0.0424

....

[https://buffedlizard55-lab.github.io/GEMSDOE45/](https://buffedlizard55-lab.github.io/GEMSDOE45/)

h51-km-faultzone-20261006-zeros: 0.0106

....

[https://buffedlizard55-lab.github.io/GEMSDOE49/](https://buffedlizard55-lab.github.io/GEMSDOE49/)

gate_ortho_w0.25-40k-20261006T213721Z-nan: 0.2376

....

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

....

[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)

h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708

h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649

h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710

h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707

....

[https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html)

efd28-repro-20261003-1cc7dc534d51-nan: 0.2600

repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041

sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512

wormrank-d28-20261003-59dcaf6dd11d-zeros:0.2560

wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532

xfit-c0-habitat-20261003-ca879db0089a-zeros:0.0439

xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros: 0.0356

....

[https://buffedlizard55-lab.github.io/GEMSDOE46/](https://buffedlizard55-lab.github.io/GEMSDOE46/)

r11f-scarp-radiometric-fusion-00e049b51218-zeros:0.1589

r12-scarp-rad-concordance-23e807e2de9f-zeros: 0.0843

....

[https://buffedlizard55-lab.github.io/GEMSDOE39/](https://buffedlizard55-lab.github.io/GEMSDOE39/)

h40-e-disc-h40e-30k-zeros: 0.0339

....

[https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html)

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: 0.0355

h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard: 0.0397

h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros: 0.0984

....

[https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html)

h42-submission-primary: 0.0245

....

[https://buffedlizard55-lab.github.io/GEMSDOE44/docs/](https://buffedlizard55-lab.github.io/GEMSDOE44/docs/)

h46-twostageAB_20261006T160000Z_b0cfe956-zeros: 0.0715

....

[https://buffedlizard55-lab.github.io/GEMSDOE47/](https://buffedlizard55-lab.github.io/GEMSDOE47/)

h60-lidarscarp-s2p0-20261007-nanoutside: 0.0430

....

[https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html)

h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8: 0.2296

....

[https://buffedlizard55-lab.github.io/GEMSDOE50/](https://buffedlizard55-lab.github.io/GEMSDOE50/)

h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite: 0.0764

....

[https://buffedlizard55-lab.github.io/GEMSDOE51/](https://buffedlizard55-lab.github.io/GEMSDOE51/)

h53-twostage-20261008T040951Z-9a0b32c871: 0.1047

....

[https://buffedlizard55-lab.github.io/GEMSDOE52/](https://buffedlizard55-lab.github.io/GEMSDOE52/)

h97b-candidate: 0.0856

....

[https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html)

h8-tiprelay-ridgeconcord-pr2-n80000-20261009-49bec522-zeros: 0.0159

....

[https://buffedlizard55-lab.github.io/GEMSDOE54/docs/](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/)

h54c-manifest-edge-20261009T025732Z-73454bc5:0.0449

....

[https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html)

tensor_full-n16000-sep3-20261009T211747Z-nan: 0.0290

....

[https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html)

h56-final-dotted-ridge-d2p8-20261009T190421Z:0.0658

....

[https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html)

h57r-joint-strata-38000-20261010T214547Z-00cf5b2066f1-zeros: 0.0254

....

[https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html)

ml-binary-ridge-20261012T000000Z: 0.0180

....

[https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html)

h59j-coherence-consensus-dotted-20261011T043000Z: 0.0499

....

[https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html)

h73-chi-coherent-corridor-12000-20261011T195818Z-zeros: 0.0351

....

[https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html)

h61a-basement-step-20000dots-20261011T012029Z-eb2ae4bb024b-zeros: 0.0009

h61o-vardepth-none-40000dots-20261011T160711Z-28d4fac611ea-zeros-zeros:0.0751

....

[https://buffedlizard55-lab.github.io/62GEMSDOE/](https://buffedlizard55-lab.github.io/62GEMSDOE/)

datum-lahontan-strain-gauge-defensible-440dots-zeros: 0.0000

....

[https://buffedlizard55-lab.github.io/GEMSDOE63/](https://buffedlizard55-lab.github.io/GEMSDOE63/)

cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-zeros: 0.2303

....

[https://buffedlizard55-lab.github.io/GEMSDOE64/](https://buffedlizard55-lab.github.io/GEMSDOE64/)

h64-lidar-scarp-cv-20261011T220000Z:0.0383

....

[https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html)

sar-em-propensity-half-20261011T223500Z-5e4660cd-zeros:0.0431

....

[https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html)

gems66-lidar03-cvretrain-reliefdecile-37654dots-20261020T190152Z-zeros:0.1152

....

[https://buffedlizard55-lab.github.io/GEMSDOE67/](https://buffedlizard55-lab.github.io/GEMSDOE67/)

h67a-orientip-lane-29447dots-20261012T021226Z-allfinite:0.0356

ovtr-ml-cover-tau3p0-20261012-nan:0.1426

....

[https://buffedlizard55-lab.github.io/GEMSDOE68/](https://buffedlizard55-lab.github.io/GEMSDOE68/)

gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-nan:0.0437

gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-zeros: 0.0437

....

[https://buffedlizard55-lab.github.io/GEMSDOE69/](https://buffedlizard55-lab.github.io/GEMSDOE69/)

h69-joint-relayramp-pullapart-38669-20261020T201504Z-f29b6df5:0.0053

....

[https://buffedlizard55-lab.github.io/GEMSDOE70/](https://buffedlizard55-lab.github.io/GEMSDOE70/)

gems70-p5-dual-submod300-oof38k-20261020:0.2478

....

[https://buffedlizard55-lab.github.io/GEMSDOE71/](https://buffedlizard55-lab.github.io/GEMSDOE71/)

gems71-hydro-conduit-38800-20261020T120000Z-zeros: 0.0558

....

[https://buffedlizard55-lab.github.io/GEMSDOE72/](https://buffedlizard55-lab.github.io/GEMSDOE72/)

gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-zeros: 0.0492

....

[https://buffedlizard55-lab.github.io/GEMSDOE73/](https://buffedlizard55-lab.github.io/GEMSDOE73/)

gems73-h73-mcsc-seamfree-blakely-37654dots-20261021T073716Z-b27ac445-zeros: 0.1917

....

[https://buffedlizard55-lab.github.io/GEMSDOE74/](https://buffedlizard55-lab.github.io/GEMSDOE74/)

gemsdoe74-triregime-radon-piedmont-37654-20261021T051000Z-zeros:0.0669

....

[https://buffedlizard55-lab.github.io/GEMSDOE75/](https://buffedlizard55-lab.github.io/GEMSDOE75/)

gems75-trlt-radon-loco-ridge-20261021-zeros:0.1627

....

[https://buffedlizard55-lab.github.io/GEMSDOE76/](https://buffedlizard55-lab.github.io/GEMSDOE76/)

gems76_h76_3_geotherm_tilt_axial_submod_20261021_zeros:0.1555

gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros:0.2343

....

[https://buffedlizard55-lab.github.io/GEMSDOE77/](https://buffedlizard55-lab.github.io/GEMSDOE77/)

gems85-h85-edti-collar35-skel-r33-20261021-d97b248e-zeros:0.0964

....

[https://buffedlizard55-lab.github.io/GEMSDOE78/](https://buffedlizard55-lab.github.io/GEMSDOE78/)

gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros:0.1564

....

[https://buffedlizard55-lab.github.io/GEMSDOE79/](https://buffedlizard55-lab.github.io/GEMSDOE79/)

gems79-tilt-ring-100000dots-20261022T212135Z-50a5d7498c71-zeros:0.0005

....

[https://buffedlizard55-lab.github.io/GEMSDOE80/](https://buffedlizard55-lab.github.io/GEMSDOE80/)

gemsdoe80-h80g-choquet-tworegime-20261022T000000Z-zeros:0.0943

....

[https://buffedlizard55-lab.github.io/GEMSDOE81/](https://buffedlizard55-lab.github.io/GEMSDOE81/)

gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros:0.0041

....

[https://buffedlizard55-lab.github.io/GEMSDOE82/](https://buffedlizard55-lab.github.io/GEMSDOE82/)

gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros:0.1886

....

[https://buffedlizard55-lab.github.io/GEMSDOE83/](https://buffedlizard55-lab.github.io/GEMSDOE83/)

gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros:0.0573

....

[https://buffedlizard55-lab.github.io/GEMSDOE84/](https://buffedlizard55-lab.github.io/GEMSDOE84/)

gems84-h84-kthm-tworegime-58000px-20261022T235900Z-zeros:0.0132

....

[https://buffedlizard55-lab.github.io/GEMSDOE85/](https://buffedlizard55-lab.github.io/GEMSDOE85/)

gemsdoe85-hjcd-ventbridge-submod-zeros: 0.1110

....

[https://buffedlizard55-lab.github.io/GEMSDOE86/](https://buffedlizard55-lab.github.io/GEMSDOE86/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE87/](https://buffedlizard55-lab.github.io/GEMSDOE87/)

h87-h87-cmgep-20261022T060000Z-8f394f43:0.0500

....

[https://buffedlizard55-lab.github.io/GEMSDOE88/](https://buffedlizard55-lab.github.io/GEMSDOE88/)

:

....

[https://buffedlizard55-lab.github.io/GEMSDOE89/](https://buffedlizard55-lab.github.io/GEMSDOE89/)

gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros:0.0301

....

[https://buffedlizard55-lab.github.io/GEMSDOE90/](https://buffedlizard55-lab.github.io/GEMSDOE90/)

gems90-cnc-35000dots-20261024T084324Z:0.0749

....

[https://buffedlizard55-lab.github.io/GEMSDOE91/](https://buffedlizard55-lab.github.io/GEMSDOE91/)

gems91-s17-cwpc-e3-20261025T163842Z-5c025d56-zeros:0.1367

gems91-s17-lftg:0.1823

....

[https://buffedlizard55-lab.github.io/GEMSDOE92/](https://buffedlizard55-lab.github.io/GEMSDOE92/)

gemsdoe92-sbf-c2-rankmean-thr0p8-20261023T081905Z-fa0404c1-zeros:0.0255

....

I think it makes sense that in order for a submission to be validated that it needs to pass certain high scoring validation gates before confirming whether a file is unique and can be submitted for scoring.

The highest score right now is 0.4413 on the leaderboard.

The following is the leaderboard for the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See below for more links and information related to the competition:

[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)

[https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)

[https://gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/)

[https://epsg.io/32611](https://epsg.io/32611)

[https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195	is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win)

"Maximize the Probability of Winning": our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena first.

Own the Outcome

We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:

"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file

New submission

File to submitNo file chosen

You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.

Note (optional)

A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:

[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow.[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)

Get familiar with the problem through the overview and problem description,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want to reference additional resources available on the about page,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).

Download the data from the data,[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), tab.

Create and train your own model. This reference solution,[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.

[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (verified redirect to login)

See below for links from the above site.  See attached files for links from the above site.

[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (requires login) to data/

See links below for competition data:

[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0)

[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0)

[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0)

[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0)

[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0)

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Site creation

Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Run this task through multiple passes.

Pass 1: Implement the task completely and verify the result.

Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.

Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.

---

### Session 20 Standing Prompt Addendum (2026-10-26 — Focused 9-Site Brief)

Review the repo and work on the next steps from the previous sessions first. We need to focus on generating a unique submission into the competition (`https://www.drivendata.org/competitions/306/competition-doe-gems/`). Never submit a previous submission into the competition unless it is clearly stated for educational purposes — never submit duplicates, and make it obvious without human visual inspection whether the generated TIF is OK to download and OK to submit after passing automated high-scoring validation gates.

Focused 9-site fleet list from the user prompt (`2026-10-26`):
- `https://buffedlizard55-lab.github.io/GEMSDOE24/` (`H26 (s28-d28): 0.2477`, `H27 (s28-d28): 0.0859`)
- `https://buffedlizard55-lab.github.io/GEMSDOE25/` (`H28 (s30-d25): 0.2600`, `H38 (s28-d28): 0.0742`)
- `https://buffedlizard55-lab.github.io/GEMSDOE27/` (`H27 (s30-d28): 0.2449`, `H29 (s28-d25): 0.2190`)
- `https://buffedlizard55-lab.github.io/GEMSDOE28/` (`H38 (s28-d28): 0.2710`, `H31-c2 (s28-d28): 0.2708`, `H38-b2 (s28-d28): 0.2707`, `H24 (s28-d28): 0.2649`, `H45 (s28-d28): 0.0217`)
- `https://buffedlizard55-lab.github.io/GEMSDOE30/` (`H30 (s30-d25): 0.2600`, `H43 (s28-d28): 0.1462`)
- `https://buffedlizard55-lab.github.io/GEMSDOE31/` (`h31-h31-s28-c2-20261004T193000Z-c0f76c74: 0.2708`)
- `https://buffedlizard55-lab.github.io/GEMSDOE32/` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778`)
- `https://buffedlizard55-lab.github.io/GEMSDOE33/` (`h33-c2-p25-d28-zeros: 0.2632`)
- `https://buffedlizard55-lab.github.io/GEMSDOE36/` (`h40-b2-t0960-zeros: 0.2750`)

Key standing requirements preserved verbatim:
- Clear, obvious executive summary on every one of the 9 sites above identifying the best submission without duplication.
- PhD-level analysis of why and how `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778`) obtained the highest reported score among the 9 sites, and how to surpass `0.2778` / `0.3195` toward leaderboard top `0.4413`.
- PARALLEL-RUN PROTOCOL (`LANE`, `REUSE, DON'T REBUILD`, `LABEL EVERY NUMBER`, `LEAKAGE CANARY`, `RUN CARD`, `BUDGET` 3 experiments / 2 hours), Arena AI Core Values (`Maximize P(Win)` and `Own the Outcome`), `[0, 1]` range validation (`"Predicted values must be in range [0, 1]"` fix), 3-pass execution (`Pass 1`, `Pass 2`, `Pass 3`), and PR creation + merge onto `main`.

</details>

</details>
````

</details>

<details><summary>Owner brief 2026-10-25 — saved as verbatim</summary>

````text
Review the repo.

I want to focus on  the highest scoring submissions from the following sites, GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py) and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:

0.4413

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)
gems-submission-20260925T001403Z-7f00890a: 0.1563
....
[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477
....
[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)
dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600
....
[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)
topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449
....
[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)
h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708
h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649
h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710
h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707
....
[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)
d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600
....
[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)
h27-4-solo-d28-20261004-8acb75e1-nan:0.2708
....
[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778
....
[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)
h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632
....
[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)
anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750
....
[https://buffedlizard55-lab.github.io/GEMSDOE92/](https://buffedlizard55-lab.github.io/GEMSDOE92/)
gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros:0.0255

I think it makes sense that in order for a submission to be validated that it needs to pass certain high scoring validation gates before confirming whether a file is unique and can be submitted for scoring.

The following is the leaderboard for the competition:
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

See below for more links and information related to the competition:
https://github.com/drivendataorg/gems-prize-reference-solution
https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
https://gbcge.org/current-projects/ingenious/
https://epsg.io/32611
https://en.wikipedia.org/wiki/Tversky_index

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Our Core Values
Maximize P(Win)
Own the Outcome

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:
"Predicted values must be in range [0, 1]"
Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).
you need to complete the above task by yourself.

Run this task through multiple passes.
Pass 1: Implement the task completely and verify the result.
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.
Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.
````

</details>

<details><summary>Owner brief 2026-10-25 session 6 — reconstructed, not verbatim</summary>

````text
PROVENANCE WARNING (IR-25-BRIEF-RECONSTRUCTED): this is the owner's 2026-10-25 brief as RECONSTRUCTED by the agent after
its working context was condensed. It is NOT guaranteed to be verbatim (whitespace, link markup and possibly wording may differ).
Cross-check: the 21 owner-reported scores independently transcribed into registry/top_scorer_sources.json all appear here (21/21).
Owner action: paste the original message over this file to make it authoritative. Older verbatim brief: knowledge/owner_brief_verbatim.txt. Shorter parallel-session copy: knowledge/owner_brief_2026-10-25_verbatim.txt.
==================================================================================================================
Review the repo.

I want to focus on  the highest scoring submissions from the following sites, GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, GEMSDOE36.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.  IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE GENERATED TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  A lot of sites mention inspection only and a human inspector, but the inspection needs to be done through the project and needs to be validated for submission without human intervention.

PARALLEL-RUN PROTOCOL — read first. This session is one of several running from this same prompt.

1. LANE. Your lane is the single method paragraph below. Stay inside it. If your raster's rank-correlation with any registry raster exceeds [0.90], or more than [70%] of your dots fall within 3 px of one registry raster's dots, you have drifted into another lane: log it as a duplicate and stop. Check this on the surface before placement AND on the final dots.

2. REUSE, DON'T REBUILD. Use the template's cached feature stack, evaluate_[holdout.py](http://holdout.py) and submission_[writer.py](http://writer.py). Holdout = hide-and-recover: withhold whole fault segments with a buffer, derive every catalogue-based feature only from the visible faults, mask visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is wrong, fix it once in the template and report it; never keep a private fork.

3. LABEL EVERY NUMBER as HOLDOUT-DTI (evaluator version, number of withheld positives, 95% CI) or ORGANIZER-CONFIRMED (copied from a submission-page receipt). A projection is never written as a score.

4. LEAKAGE CANARY. Test each feature alone on the holdout before trusting any result. AUC above [0.90] means leakage until proven otherwise.

5. RUN CARD. End with one JSON card: hypothesis; mechanism; the named non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs registry; raster sha256; validator output (no NaN inside the footprint, values in [0,1], CRS/shape/transform match); submission name + note of at most 140 characters; verdict promote / negative. Negative results are deliverables.

6. BUDGET. Stop after [3] experiments or [2] hours. Do not pick submissions: promotion to a real slot is a separate selector step, within the weekly cap shown on the submission page.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:
[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?
Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Current competition leaderboard GEMSDOE high score:
0.4413

(The two paragraphs above were repeated verbatim in the message.)

[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)
gems-submission-20260925T001403Z-7f00890a: 0.1563
....
[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)
gems6_hgb88-topk03_33cec71ff0: 0.0286
....
[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152
....
[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560
....
[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)
gems-submission-20260926T163915Z-237f0063: 0.0343
....
[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)
gems-submission-20260926T175114Z-7f00890a: 0.1563
....
[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461
....
[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)
Hedge-v2_submission: 0.1563
....
[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)
2314b599: 0.0107
....
[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)
gems-structural-area06-v1: 0.0202
....
[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)
r7-nms3-dem10-scarp_0c9199f14e62:0.1294
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294
....
[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782
....
[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020
....
[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187
....
[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)
H19-C_20260930T212401Z_c11e495e: 0.0297
....
[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922
....
[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839
....
[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)
20261001_r13-lattice-s5_v2_nan-outside:0.0904
....
[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360
....
[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)
h19-4-reference-20260930-691e4dfa: 0.1894
....
[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859
....
[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)
h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002
h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748
....
[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)
h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352
....
[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477
....
[https://buffedlizard55-lab.github.io/GEMSDOE25/](https://buffedlizard55-lab.github.io/GEMSDOE25/)
dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600
....
[https://buffedlizard55-lab.github.io/GEMSDOE26/](https://buffedlizard55-lab.github.io/GEMSDOE26/)
dilcond-oof-v1-20261003-47629f496133-nan: 0.1223
....
[https://buffedlizard55-lab.github.io/GEMSDOE27/](https://buffedlizard55-lab.github.io/GEMSDOE27/)
topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449
....
[https://buffedlizard55-lab.github.io/GEMSDOE30/](https://buffedlizard55-lab.github.io/GEMSDOE30/)
d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600
....
[https://buffedlizard55-lab.github.io/GEMSDOE31/docs/](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/)
h27-4-solo-d28-20261004-8acb75e1-nan:0.2708
....
[https://buffedlizard55-lab.github.io/GEMSDOE33/](https://buffedlizard55-lab.github.io/GEMSDOE33/)
h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632
....
[https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html)
h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778
....
[https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html)
h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418
....
[https://buffedlizard55-lab.github.io/GEMSDOE36/docs/](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/)
anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750
....
[https://buffedlizard55-lab.github.io/GEMSDOE37/](https://buffedlizard55-lab.github.io/GEMSDOE37/)
h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193
....
[https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html)
D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763
....
[https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html)
xscale-worm-persistence-20261006T000541Z-nan: 0.0581
....
[https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html)
sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: 0.0424
....
[https://buffedlizard55-lab.github.io/GEMSDOE45/](https://buffedlizard55-lab.github.io/GEMSDOE45/)
h51-km-faultzone-20261006-zeros: 0.0106
....
[https://buffedlizard55-lab.github.io/GEMSDOE49/](https://buffedlizard55-lab.github.io/GEMSDOE49/)
gate_ortho_w0.25-40k-20261006T213721Z-nan: 0.2376
....
[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)
h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778
....
[https://buffedlizard55-lab.github.io/GEMSDOE28/](https://buffedlizard55-lab.github.io/GEMSDOE28/)
h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708
h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649
h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710
h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: 0.2707
....
[https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html)
efd28-repro-20261003-1cc7dc534d51-nan: 0.2600
repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041
sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512
wormrank-d28-20261003-59dcaf6dd11d-zeros:0.2560
wormsurv-filter-20261003-921f10960d6e-zeros: 0.0532
xfit-c0-habitat-20261003-ca879db0089a-zeros:0.0439
xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros: 0.0356
....
[https://buffedlizard55-lab.github.io/GEMSDOE46/](https://buffedlizard55-lab.github.io/GEMSDOE46/)
r11f-scarp-radiometric-fusion-00e049b51218-zeros:0.1589
r12-scarp-rad-concordance-23e807e2de9f-zeros: 0.0843
....
[https://buffedlizard55-lab.github.io/GEMSDOE39/](https://buffedlizard55-lab.github.io/GEMSDOE39/)
h40-e-disc-h40e-30k-zeros: 0.0339
....
[https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html)
h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: 0.0355
h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard: 0.0397
h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros: 0.0984
....
[https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html)
h42-submission-primary: 0.0245
....
[https://buffedlizard55-lab.github.io/GEMSDOE44/docs/](https://buffedlizard55-lab.github.io/GEMSDOE44/docs/)
h46-twostageAB_20261006T160000Z_b0cfe956-zeros: 0.0715
....
[https://buffedlizard55-lab.github.io/GEMSDOE47/](https://buffedlizard55-lab.github.io/GEMSDOE47/)
h60-lidarscarp-s2p0-20261007-nanoutside: 0.0430
....
[https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html)
h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8: 0.2296
....
[https://buffedlizard55-lab.github.io/GEMSDOE50/](https://buffedlizard55-lab.github.io/GEMSDOE50/)
h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite: 0.0764
....
[https://buffedlizard55-lab.github.io/GEMSDOE51/](https://buffedlizard55-lab.github.io/GEMSDOE51/)
h53-twostage-20261008T040951Z-9a0b32c871: 0.1047
....
[https://buffedlizard55-lab.github.io/GEMSDOE52/](https://buffedlizard55-lab.github.io/GEMSDOE52/)
h97b-candidate: 0.0856
....
[https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE53/docs/index.html)
h8-tiprelay-ridgeconcord-pr2-n80000-20261009-49bec522-zeros: 0.0159
....
[https://buffedlizard55-lab.github.io/GEMSDOE54/docs/](https://buffedlizard55-lab.github.io/GEMSDOE54/docs/)
h54c-manifest-edge-20261009T025732Z-73454bc5:0.0449
....
[https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/55GEMSDOE/docs/index.html)
tensor_full-n16000-sep3-20261009T211747Z-nan: 0.0290
....
[https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/56GEMSDOE/docs/index.html)
h56-final-dotted-ridge-d2p8-20261009T190421Z:0.0658
....
[https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/57GEMSDOE/docs/index.html)
h57r-joint-strata-38000-20261010T214547Z-00cf5b2066f1-zeros: 0.0254
....
[https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/58GEMSDOE/docs/index.html)
ml-binary-ridge-20261012T000000Z: 0.0180
....
[https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/59GEMSDOE/docs/index.html)
h59j-coherence-consensus-dotted-20261011T043000Z: 0.0499
....
[https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/60GEMSDOE/docs/index.html)
h73-chi-coherent-corridor-12000-20261011T195818Z-zeros: 0.0351
....
[https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/61GEMSDOE/docs/index.html)
h61a-basement-step-20000dots-20261011T012029Z-eb2ae4bb024b-zeros: 0.0009
h61o-vardepth-none-40000dots-20261011T160711Z-28d4fac611ea-zeros-zeros:0.0751
....
[https://buffedlizard55-lab.github.io/62GEMSDOE/](https://buffedlizard55-lab.github.io/62GEMSDOE/)
datum-lahontan-strain-gauge-defensible-440dots-zeros: 0.0000
....
[https://buffedlizard55-lab.github.io/GEMSDOE63/](https://buffedlizard55-lab.github.io/GEMSDOE63/)
cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4-zeros: 0.2303
....
[https://buffedlizard55-lab.github.io/GEMSDOE64/](https://buffedlizard55-lab.github.io/GEMSDOE64/)
h64-lidar-scarp-cv-20261011T220000Z:0.0383
....
[https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE65/docs/index.html)
sar-em-propensity-half-20261011T223500Z-5e4660cd-zeros:0.0431
....
[https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE66/docs/index.html)
gems66-lidar03-cvretrain-reliefdecile-37654dots-20261020T190152Z-zeros:0.1152
....
[https://buffedlizard55-lab.github.io/GEMSDOE67/](https://buffedlizard55-lab.github.io/GEMSDOE67/)
h67a-orientip-lane-29447dots-20261012T021226Z-allfinite:0.0356
ovtr-ml-cover-tau3p0-20261012-nan:0.1426
....
[https://buffedlizard55-lab.github.io/GEMSDOE68/](https://buffedlizard55-lab.github.io/GEMSDOE68/)
gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-nan:0.0437
gems68-autoctx-s3-strands-35000dots-20261020T210000Z-849a0f04-zeros: 0.0437
....
[https://buffedlizard55-lab.github.io/GEMSDOE69/](https://buffedlizard55-lab.github.io/GEMSDOE69/)
h69-joint-relayramp-pullapart-38669-20261020T201504Z-f29b6df5:0.0053
....
[https://buffedlizard55-lab.github.io/GEMSDOE70/](https://buffedlizard55-lab.github.io/GEMSDOE70/)
gems70-p5-dual-submod300-oof38k-20261020:0.2478
....
[https://buffedlizard55-lab.github.io/GEMSDOE71/](https://buffedlizard55-lab.github.io/GEMSDOE71/)
gems71-hydro-conduit-38800-20261020T120000Z-zeros: 0.0558
....
[https://buffedlizard55-lab.github.io/GEMSDOE72/](https://buffedlizard55-lab.github.io/GEMSDOE72/)
gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-zeros: 0.0492
....
[https://buffedlizard55-lab.github.io/GEMSDOE73/](https://buffedlizard55-lab.github.io/GEMSDOE73/)
gems73-h73-mcsc-seamfree-blakely-37654dots-20261021T073716Z-b27ac445-zeros: 0.1917
....
[https://buffedlizard55-lab.github.io/GEMSDOE74/](https://buffedlizard55-lab.github.io/GEMSDOE74/)
gemsdoe74-triregime-radon-piedmont-37654-20261021T051000Z-zeros:0.0669
....
[https://buffedlizard55-lab.github.io/GEMSDOE75/](https://buffedlizard55-lab.github.io/GEMSDOE75/)
gems75-trlt-radon-loco-ridge-20261021-zeros:0.1627
....
[https://buffedlizard55-lab.github.io/GEMSDOE76/](https://buffedlizard55-lab.github.io/GEMSDOE76/)
gems76_h76_3_geotherm_tilt_axial_submod_20261021_zeros:0.1555
gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d-zeros:0.2343
....
[https://buffedlizard55-lab.github.io/GEMSDOE77/](https://buffedlizard55-lab.github.io/GEMSDOE77/)
gems85-h85-edti-collar35-skel-r33-20261021-d97b248e-zeros:0.0964
....
[https://buffedlizard55-lab.github.io/GEMSDOE78/](https://buffedlizard55-lab.github.io/GEMSDOE78/)
gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros:0.1564
....
[https://buffedlizard55-lab.github.io/GEMSDOE79/](https://buffedlizard55-lab.github.io/GEMSDOE79/)
gems79-tilt-ring-100000dots-20261022T212135Z-50a5d7498c71-zeros:0.0005
....
[https://buffedlizard55-lab.github.io/GEMSDOE80/](https://buffedlizard55-lab.github.io/GEMSDOE80/)
gemsdoe80-h80g-choquet-tworegime-20261022T000000Z-zeros:0.0943
....
[https://buffedlizard55-lab.github.io/GEMSDOE81/](https://buffedlizard55-lab.github.io/GEMSDOE81/)
gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros:0.0041
....
[https://buffedlizard55-lab.github.io/GEMSDOE82/](https://buffedlizard55-lab.github.io/GEMSDOE82/)
gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199-zeros:0.1886
....
[https://buffedlizard55-lab.github.io/GEMSDOE83/](https://buffedlizard55-lab.github.io/GEMSDOE83/)
gems83-h83-gvcd-dink300-37654dots-20261021-1a373694-zeros:0.0573
....
[https://buffedlizard55-lab.github.io/GEMSDOE84/](https://buffedlizard55-lab.github.io/GEMSDOE84/)
gems84-h84-kthm-tworegime-58000px-20261022T235900Z-zeros:0.0132
....
[https://buffedlizard55-lab.github.io/GEMSDOE85/](https://buffedlizard55-lab.github.io/GEMSDOE85/)
gemsdoe85-hjcd-ventbridge-submod-zeros: 0.1110
....
[https://buffedlizard55-lab.github.io/GEMSDOE86/](https://buffedlizard55-lab.github.io/GEMSDOE86/)
:
....
[https://buffedlizard55-lab.github.io/GEMSDOE87/](https://buffedlizard55-lab.github.io/GEMSDOE87/)
h87-h87-cmgep-20261022T060000Z-8f394f43:0.0500
....
[https://buffedlizard55-lab.github.io/GEMSDOE88/](https://buffedlizard55-lab.github.io/GEMSDOE88/)
:
....
[https://buffedlizard55-lab.github.io/GEMSDOE89/](https://buffedlizard55-lab.github.io/GEMSDOE89/)
gemsdoe89-bh-rtp-habc-20261024-d7e1507c-zeros:0.0301
....
[https://buffedlizard55-lab.github.io/GEMSDOE90/](https://buffedlizard55-lab.github.io/GEMSDOE90/)
gems90-cnc-35000dots-20261024T084324Z:0.0749
....
[https://buffedlizard55-lab.github.io/GEMSDOE91/](https://buffedlizard55-lab.github.io/GEMSDOE91/)
gems91-s17-cwpc-e3-37654dots-20261025T150000Z-4d124f1d-zeros:0.1367
gems91-s17-lftg-20261025T160014Z-7b6bf90844-zeros:0.1823
gems91-S18-UNIQUE-curvtilt-20000dots-20261025T182858Z-29db2405:
....
[https://buffedlizard55-lab.github.io/GEMSDOE92/](https://buffedlizard55-lab.github.io/GEMSDOE92/)
gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros:0.0255
....

I think it makes sense that in order for a submission to be validated that it needs to pass certain high scoring validation gates before confirming whether a file is unique and can be submitted for scoring.

The following is the leaderboard for the competition:
[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)

See below for more links and information related to the competition:
[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)
[https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
[https://gbcge.org/current-projects/ingenious/](https://gbcge.org/current-projects/ingenious/)
[https://epsg.io/32611](https://epsg.io/32611)
[https://en.wikipedia.org/wiki/Tversky_index](https://en.wikipedia.org/wiki/Tversky_index)

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.
Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values
Maximize P(Win)
"Maximize the Probability of Winning": our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena first.

Own the Outcome
We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.
Verify no hallucinations.
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form:
"Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file
New submission
File to submitNo file chosen
You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.
Note (optional)
A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:
[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow.[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)
Get familiar with the problem through the overview and problem description,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). You might also want to reference additional resources available on the about page,[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/).
Download the data from the data,[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), tab.
Create and train your own model. This reference solution,[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution) implements a simple approach.
Use your model to generate predictions that match the submission format.
Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition.
[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (verified redirect to login)
See below for links from the above site.  See attached files for links from the above site.
[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)

Download competition data from [https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (requires login) to data/
See links below for competition data:
[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0)
[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0)
[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0)
[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0)
[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0)

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.
Verify no hallucinations.
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Site creation
Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.

It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).

you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

Run this task through multiple passes.
Pass 1: Implement the task completely and verify the result.
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.
Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.
Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.
````

</details>

<details><summary>Owner brief 2026-10-25 — consolidated, not verbatim</summary>

````text
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
````

</details>

<details><summary>Session 8 scope — consolidated, not verbatim</summary>

````text
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
````

</details>

<details><summary>Continuation scope — consolidated, not verbatim</summary>

````text
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
````

</details>

<details><summary>Session handoff — condensed, not verbatim</summary>

````text
# Condensed Session Brief (`arena/66ca912a-gemsdoe25`, 2026-10-25)

> **Provenance note (`IR-25-BRIEF-RECONSTRUCTED`):** The initial turn of this session was condensed into Arena session memory before this document was written, so the text below is an explicit, non-fabricated summary of active requirements rather than a claimed verbatim transcript. Verbatim and reconstructed earlier copies remain preserved in `knowledge/owner_brief_verbatim.txt`, `knowledge/owner_brief_2026-10-25_verbatim.txt`, and `knowledge/owner_brief_2026-10-25_s6_RECONSTRUCTED.txt`.

## Active Scope & Standing Requirements

1. **Core values & README mandate:** Keep Arena Core Values (**Maximize P(Win)** and **Own the Outcome**) and the session prompt in `README.md` and read at the start of every session.
2. **Unique competition GeoTIFF & unmistakable status:** Generate a genuinely unique `.tif` submission (never copy a prior submission except labeled learning/education audit). Make it immediately obvious at the top of the GitHub Pages site (`index.html`) and executive summary (`docs/executive-summary.html`) whether the generated `.tif` is **OK to download** and **OK to submit / spend a weekly slot**, with unique filename and short note (`<= 120` / `<= 140` chars).
3. **Programmatic exact-file validation:** Validate automatically without human intervention against the template CRS (`EPSG:32611`), shape (`3730 x 3292`), geotransform (`100 m`), footprint finiteness (zero `NaN` inside the `5,167,373`-pixel footprint), and strict `[0, 1]` range to prevent `"Predicted values must be in range [0, 1]"`.
4. **PhD-level review of focus sites & `0.2778` (`GEMSDOE32`):** Review `GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36` (and listed sibling submissions through `GEMSDOE92`), explain why `GEMSDOE32` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, owner-reported `0.2778`) achieved the highest group score, and analyze what is mathematically and geophysically required to exceed `0.2778` (and the conflicting unverified leaderboard figures `0.3195` / `0.4413`).
5. **6-Point Parallel-Run Protocol:**
   - **Lane check (surface + final dots):** `|Spearman| > 0.90` or `> 70%` of dots within `3 px` of any registry raster triggers duplicate-lane logging and stop.
   - **Shared template stack:** Reuse cached feature stack, buffered whole-segment spatial holdout (`src/gems25/holdout.py`, `alpha=0.2, beta=0.8, R=300 m`), and strict writer/checker (`src/gems25/submission.py`); fix shared tools in-place (`scripts/lane_check_extended.py`), never fork privately.
   - **Metric hygiene:** Label every DTI value as `HOLDOUT-DTI` (evaluator version, withheld positives, 95% CI) or `ORGANIZER-CONFIRMED` (organizer receipt only; owner-reported claims explicitly labeled unverified; model projections never presented as scores).
   - **Leakage canary:** Test every new feature alone on holdout first; standalone `max(AUC, 1-AUC) > 0.90` is presumptive leakage until proven otherwise.
   - **JSON Run Card:** End with one machine-verified JSON Run Card containing hypothesis, physical mechanism, named non-fault mimic process, holdout DTI + CI, registry correlation/overlap, raster SHA-256, validator output, submission name + note (`<= 140` chars), and verdict (`promote` / `negative`).
   - **Budget & slot discipline:** Rank 3–5 untried geological hypotheses before implementing; pre-register and commit before fitting; stop within 3 experiments or 2 hours; never automate `drivendata.org`; promotion to a weekly slot is a separate owner selector step; execute 3 explicit verification passes; open and merge PR onto `main` from `arena/66ca912a-gemsdoe25`.
````

</details>

<details><summary>Original owner brief (2026-10-02) — verbatim archive</summary>

````text
Review the repo.   
  
There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.  
  
Replace one-factor-at-a-time testing with a designed factorial experiment. The repo's own hypothesis history — single-named attempts like "conj_alteration_mag," "dem10-scarp," "topo-geophys-x-complexity-prior" — reads as classical one-factor-at-a-time testing, a documented methodological weakness: Box, Hunter, and Hunter's foundational Statistics for Experimenters shows why holding other factors fixed while varying one at a time systematically misses interaction effects — cases where two features are each weak alone but jointly diagnostic because the real signature is their conjunction, not either one's sum — and the name "conj_alteration_mag" is already gesturing at exactly this without treating it as a designed experiment. Replace the ad hoc sequence with a fractional factorial design across the candidate feature families already identified (potential-field gradients, DEM curvature/scarp, strain/seismicity, thermal/geochemical, catalogue-geometry), run against the hide-and-recover holdout, which estimates every family's main effect on DTI alongside its pairwise interactions in a modest, pre-specified number of runs — far fewer than testing every combination in full — rather than an open-ended sequence of hunches; the sparsity-of-effects principle this literature establishes, that real systems are typically dominated by a few main effects and low-order interactions rather than many high-order ones, means this is enough to rank which families matter alone, which only matter in combination, and which are inert — redirected by evidence, not by which conjunction sounds geologically plausible.  
  
Here are the results from submissions into the competition, separated by ....:  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html))  
  
gems-submission-20260925T001403Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)](https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/))  
  
gems6_hgb88-topk03_33cec71ff0: 0.0286  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html))  
  
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193  
  
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830  
  
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html))  
  
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)](https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/))  
  
gems-submission-20260926T163915Z-237f0063: 0.0343  
  
....  
  
[[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html))  
  
gems-submission-20260926T175114Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)](https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/))  
  
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461  
  
....  
  
[[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)](https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/))  
  
Hedge-v2_submission: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html))  
  
2314b599: 0.0107  
  
....  
  
[[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html))  
  
gems-structural-area06-v1: 0.0202  
  
....  
  
[[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html))  
  
r7-nms3-dem10-scarp_0c9199f14e62:0.1294  
  
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294  
  
....  
  
[[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html))  
  
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782  
  
....  
  
[[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html))  
  
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020  
  
....  
  
[[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)](https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/))  
  
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187  
  
....  
  
[[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)](https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/))  
  
H19-C_20260930T212401Z_c11e495e: 0.0297  
  
....  
  
[[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html))  
  
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894  
  
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)](https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/))  
  
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461  
  
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921  
  
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280  
  
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839  
  
....  
  
[[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)](https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/))  
  
20261001_r13-lattice-s5_v2_nan-outside:0.0904  
  
....  
  
[[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html))  
  
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855  
  
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976  
  
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)](https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/))  
  
h19-4-reference-20260930-691e4dfa: 0.1894  
  
....  
  
[[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html))  
  
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890  
  
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html))  
  
h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002  
  
h23-b-dti-optimal-emission-10pct-20261002-86176698-nan:   
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)](https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/))  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)](https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/))  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
....  
  
25GEMSDOE SCORE:  
  
....  
  
26GEMSDOE SCORE:  
  
....  
  
27GEMSDOE SCORE:  
  
....  
  
WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:  
  
24GEMSDOE SCORE:  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2477?  
  
Answer the question using Phd level experience, knowledge, and judgement.   
  
The following is the leaderboard for the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/))  
  
   
  
We need to quickly look at the results and results from the GEMSDOE websites above.  
  
Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.  
  
The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.  
  
   
  
[[https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html))  
  
gems-submission-20260925T001403Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/)](https://buffedlizard55-lab.github.io/6GEMSDOE/](https://buffedlizard55-lab.github.io/6GEMSDOE/))  
  
gems6_hgb88-topk03_33cec71ff0: 0.0286  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html))  
  
pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193  
  
pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830  
  
pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html))  
  
gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/)](https://buffedlizard55-lab.github.io/GEMSDOE4/](https://buffedlizard55-lab.github.io/GEMSDOE4/))  
  
gems-submission-20260926T163915Z-237f0063: 0.0343  
  
....  
  
[[https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html))  
  
gems-submission-20260926T175114Z-7f00890a: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/)](https://buffedlizard55-lab.github.io/7GEMSDOE/](https://buffedlizard55-lab.github.io/7GEMSDOE/))  
  
lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461  
  
....  
  
[[https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/)](https://buffedlizard55-lab.github.io/8GEMSDOE/](https://buffedlizard55-lab.github.io/8GEMSDOE/))  
  
Hedge-v2_submission: 0.1563  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html))  
  
2314b599: 0.0107  
  
....  
  
[[https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html))  
  
gems-structural-area06-v1: 0.0202  
  
....  
  
[[https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html))  
  
r7-nms3-dem10-scarp_0c9199f14e62:0.1294  
  
r7-nms3-dem10-scarp_0c9199f14e62_allfinite:0.1294  
  
....  
  
[[https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html))  
  
gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782  
  
....  
  
[[https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html))  
  
GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020  
  
....  
  
[[https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/)](https://buffedlizard55-lab.github.io/17GEMSDOE/](https://buffedlizard55-lab.github.io/17GEMSDOE/))  
  
17GEMSDOE_F-ensemble-2pct_20260930T050626Z:0.0187  
  
....  
  
[[https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/)](https://buffedlizard55-lab.github.io/18GEMSDOE/](https://buffedlizard55-lab.github.io/18GEMSDOE/))  
  
H19-C_20260930T212401Z_c11e495e: 0.0297  
  
....  
  
[[https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html))  
  
h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894  
  
h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/)](https://buffedlizard55-lab.github.io/GEMSDOE10/](https://buffedlizard55-lab.github.io/GEMSDOE10/))  
  
h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461  
  
h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921  
  
H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280  
  
h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839  
  
....  
  
[[https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/)](https://buffedlizard55-lab.github.io/13GEMSDOE/](https://buffedlizard55-lab.github.io/13GEMSDOE/))  
  
20261001_r13-lattice-s5_v2_nan-outside:0.0904  
  
....  
  
[[https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html))  
  
h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855  
  
h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976  
  
h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/)](https://buffedlizard55-lab.github.io/GEMSDOE21/](https://buffedlizard55-lab.github.io/GEMSDOE21/))  
  
h19-4-reference-20260930-691e4dfa: 0.1894  
  
....  
  
[[https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html)](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html](https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html))  
  
h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890  
  
h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan:  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html)](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html))  
  
h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002  
  
h23-b-dti-optimal-emission-10pct-20261002-86176698-nan:   
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/)](https://buffedlizard55-lab.github.io/GEMSDOE23/](https://buffedlizard55-lab.github.io/GEMSDOE23/))  
  
....  
  
[[https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/)](https://buffedlizard55-lab.github.io/GEMSDOE24/](https://buffedlizard55-lab.github.io/GEMSDOE24/))  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
....  
  
25GEMSDOE SCORE:  
  
....  
  
26GEMSDOE SCORE:  
  
....  
  
27GEMSDOE SCORE:  
  
....  
    
  
WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:  
  
24GEMSDOE SCORE:  
  
h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477  
  
Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2477?  
  
Answer the question using Phd level experience, knowledge, and judgement.   
  
The following is the leaderboard for the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/))  
  
0.3195	is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.    
  
Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.  
  
Review the repo.   
  
The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.  
  
Our Core Values  
  
Maximize P(Win)  
  
“Maximize the Probability of Winning”: our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). “Maximize P(Win)” frees us from constraints and clarifies that we must put Arena first.  
  
Own the Outcome  
  
We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
    
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
We need to focus on being able to generate a submission into the competition.    
  
The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.  
  
I tried to submit the document that i downloaded from the site but it returned this error on the submission form:  
  
"Predicted values must be in range [0, 1]"  
  
Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25  
  
Here is the submission page when i click submit file  
  
New submission  
  
File to submitNo file chosen  
  
You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first.  
  
Note (optional)  
  
A short comment to help you or your team tell submissions apart later e.g. clustering with k=25  
  
Create a executive summary subpage that explains exactly how to make a submission into the contest.  
  
Work on the next steps from the previous sessions first.  
  
The goal of this project is to place top of the leaderboard in this competition.  The following is the competition:  
  
[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/))  
  
We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.    
  
This is the guidelines we need to follow.[[https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/)](https://www.drivendata.org/competitions/306/competition-doe-gems/](https://www.drivendata.org/competitions/306/competition-doe-gems/))  
  
Get familiar with the problem through the overview and problem description,[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)). You might also want to reference additional resources available on the about page,[[https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)).  
  
Download the data from the data,[[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)), tab.    
  
Create and train your own model. This reference solution,[[https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)](https://github.com/drivendataorg/gems-prize-reference-solution](https://github.com/drivendataorg/gems-prize-reference-solution)) implements a simple approach.  
  
Use your model to generate predictions that match the submission format.  
  
Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.    
  
this pdf outlines how submissions must be entered into the competition.    
  
[[https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)](https://docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf))  
  
You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.  
  
❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from [[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)) (verified redirect to login)  
  
See below for links from the above site.  See attached files for links from the above site.  
  
[[https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391)](https://gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391))  
  
Download competition data from [[https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)) (requires login) to data/  
  
See links below for competition data:  
  
[[https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;amp;st=wz4kofki&amp;amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0)](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&amp;st=wz4kofki&amp;dl=0](https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0))  
  
[[https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;amp;st=8junzdyw&amp;amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0)](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&amp;st=8junzdyw&amp;dl=0](https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0))  
  
[[https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;amp;st=rnino7ya&amp;amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0)](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&amp;st=rnino7ya&amp;dl=0](https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0))  
  
[[https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;amp;st=zj1lag1r&amp;amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0)](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&amp;st=zj1lag1r&amp;dl=0](https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0))  
  
[[https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;amp;st=srhhir10&amp;amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0)](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&amp;st=srhhir10&amp;dl=0](https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0))  
  
Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
Site creation  
  
Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.    
  
It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.  
  
**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU).  
  
you need to complete the above task by yourself.  Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.                        
  
Verify no hallucinations.      
  
The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.  
  
Run this task through multiple passes.  
  
Pass 1: Implement the task completely and verify the result.  
  
Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find.  
  
Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues.  
  
Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.  Work line by line verify everything no hallucinations.  
  
Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.
````

</details>
