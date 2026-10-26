# Executive review — 2026-10-26

## Decision first

**No historical file is approved as a new submission.** GEMSDOE32 B2 is the highest **OWNER-REPORTED** historical result in the supplied nine-site list, not a new candidate and not an organizer-confirmed winner. The separate selector step has not authorized a slot. Read the machine-readable ROD run card and current review page for this session's test outcome; an unfinished or negative result never becomes a green download button.

The repo's repeated "single remaining blocker is data placement" statement was stale. This session restored and SHA-256-verified all 22 manifest inputs, restored all 21 top-scorer records, prepared all 19 base bands and rebuilt the shared static/add-on cache through its original builders. No fake/synthetic competition footprint was used. Raw inputs and caches remain gitignored. Their original organizer provenance remains unverified: pins establish owner-mirror integrity, not organizer authenticity.

## Nine focus sites: which historical result is strongest?

Every performance number in the following table is **OWNER-REPORTED**, transcribed from the user's supplied results and tied to a pinned mirror where available. None is ORGANIZER-CONFIRMED. These are comparisons for learning, **not picks for a weekly slot**. “Best” means the largest supplied historical result for that site, not a fresh query of every submission on that website.

| Site | Highest supplied result | Historical exemplar | Executive assessment |
|---|---:|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | 0.2477 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | Dotted H19-5 family. The newer GVC1 report (0.0859) does not replace it. Existing work, not a new submission. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | 0.2600 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | More aggressive spatial thinning. Pixel-identical to GEMSDOE30; newer H66 report (0.0742) is substantially weaker. Do not repackage it. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | 0.2449 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | Gap closure did not outperform the supplied D1.5 parent result. Newer hydrothermal-piedmont report (0.2190) is lower. |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | 0.2710 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | Highest supplied variant; R1 0.2708, prethin 0.2649 and HF-Euler 0.2707 are lower. Tiny public-score differences do not establish statistical superiority. Newer MXTP report is 0.0217. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | 0.2600 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | Same mask as GEMSDOE25, not independent evidence. Newer MSDB1 report is 0.1462. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | 0.2708 | `h27-4-solo-d28-20261004-8acb75e1-nan` | Same mask as GEMSDOE28 R1. Do not count this as independent replication or a novel submission. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | **0.2778** | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | Strongest supplied historical comparator, but already submitted. Its useful lesson is error-cost-aware pruning, not its filename. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | 0.2632 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | Analog tip/stepover alternative; lower supplied result than B2. A structural narrative is not sufficient evidence of incremental skill. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | 0.2750 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | Exactly B2 plus 1,200 dots in the restored mask. Lower supplied result than B2; a PINN label does not establish that new physical discoveries caused its performance. |

Fresh geometry/format receipts: [`evidence/focus_audit_2026-10-26.json`](../evidence/focus_audit_2026-10-26.json), [`evidence/focus_format_2026-10-26.json`](../evidence/focus_format_2026-10-26.json). Source revisions for all nine repositories are recorded there. These revisions establish source availability; they do not prove the historical scores.

## Why B2 could score better — established facts vs inference

**COMPUTED, fresh pixel-exact identities:**

* GEMSDOE25 D2.8 = GEMSDOE30 prediction mask.
* GEMSDOE28 R1 = D2.8 ∩ {distance to supplied catalogue >1 pixel} = GEMSDOE31 mask.
* GEMSDOE32 B2 = D2.8 ∩ {distance to supplied catalogue >2 pixels}.
* D2.8 → B2 removes 6,436 predictions. The mirrored grid resolution is 100 m.
* GEMSDOE36 retains every B2 prediction and adds 1,200.

**Metric algebra, not a hidden-label measurement:** let T be weighted true-positive credit, F weighted false-positive mass, and N the number of hidden truth pixels. With the repo's transcribed DTI,

`S = T / (0.2*(T+F) + 0.8*N)`.

Removing predictions that lose t credit but save f false-positive mass improves S exactly when `t/f < 0.2*S/(1-0.2*S)` (for f>0). Dot thinning can eliminate redundant nearby emissions while preserving much of the maximum triangular-kernel credit. B2's catalogue collar can further suppress low-value predictions adjacent to known traces. This is a defensible **conditional explanation**, not a proof that its deleted pixels were false positives: the hidden labels and organizer scoring receipts are unavailable. A near-catalogue offset could equally reflect mapped trace misregistration or geological splays; only hidden labels settle that.

The hide-and-recover proxy does not identify the distribution of genuinely unmapped faults. Applying an already-built full-catalogue B2 mask to withheld catalogue truth is not honest out-of-fold evaluation: it has already removed the targets and their collar. Every catalogue feature and mask must instead use only visible faults in that draw.

**Can we exceed the reported 0.2778?** In principle, yes; this session has no evidence warranting a claim that a new file will. The supplied overall-leader figures 0.3195 and 0.4413 conflict in timing and both lack receipts. They are not current verified targets. Neither an elaborate physical name, a better proxy result nor a changed SHA guarantees a leaderboard gain. Sparse historical scores cannot uniquely recover the private truth.

## The lane constraint is quantitatively severe, not universally impossible

The literal registry lattice halo covers 5,099,871 of 5,106,385 eligible pixels (COMPUTED; 99.8724%). Only 6,514 eligible pixels are farther than 3 px from its dots. At least 30% of any lane-clean candidate's unique pixel-dots must be among those uncovered pixels. Consequently, even without spacing constraints, a candidate exceeding `floor(6514/0.30) = 21,713` dots cannot meet the literal 70% rule against this raster. Smaller candidates are **not** automatically unique or good. Moving dots into uncovered locations merely to defeat the check would optimize the registry rather than geology and was not done.

This is a real conflict with typical prior budgets, not permission to drop the lattice from the registry. A density-adjusted overlap statistic can be scientifically useful as a diagnostic, but cannot override the owner's literal gate. A policy change belongs to a separate selector/policy decision, not an unannounced implementation exception.

## ROD result: negative — stopped, no new TIFF

**HOLDOUT-DTI:** ROD pooled **0.069041**, spatial-quadrant bootstrap **95% CI [0.055788, 0.077235]**, versus same-run H35 **0.152308**, **95% CI [0.140188, 0.166509]**. Both use **22,813 withheld-positive occurrences / 19,515 distinct pixels** over four quadrants and draws 60/61. Evaluator: `gems25.metric.dti_binary`, alpha 0.2, beta 0.8, 300 m triangular kernel; exact evaluator/source hashes are in [`analysis.json`](../evidence/rod_2026-10-26/analysis.json). Paired pooled difference **−0.083267**, **95% CI [−0.099102, −0.067832]**. All four quadrant gains are negative. This is a rejection even against H35; no claim is made that H35 exhausts every later historical incumbent (such as H38's emission variants).

**COMPUTED diagnostics:** all 67 feature/input canaries passed in each of eight cells, including inverted and missingness AUC (maximum 0.802517). Passing a canary does not prove absence of all leakage. The uniform diagnostic emitted no ridges under NMS, so its zero response is not a meaningful space-filling null and is not the promotion comparator.

Surface maximum absolute Spearman was 0.038982 against 60 distinct available registry rasters. The final candidate had 70,524 dots; **100%** were within 3 px of the registered lattice, triggering the mandatory duplicate-lane stop. Final maximum absolute Spearman was 0.013141. Low correlation did not waive the overlap failure. The candidate-mask hash is recorded, but **no TIF was written**, so raster SHA-256, filename and exact-file validator output are honestly null. No confirmation, second geological experiment or competition submission followed. The first engineering preflight was interrupted before any fit to fix the file-backed validator bug; it was not a second scientific experiment.

This does **not** satisfy the requested new unique TIF deliverable. Producing or blessing a file despite the stop would contradict the explicit parallel-run protocol. Historical TIFs remain downloadable for learning only, clearly labeled as old files. A byte-different output would not solve the lane-uniqueness failure.

## Scientific work and engineering fixes

Four hypotheses and their novelty limits, physical signatures, mimics, inputs and qualitative priority were committed before the ROD test in [`knowledge/27_preregistered_rod_2026-10-26.md`](27_preregistered_rod_2026-10-26.md). ROD uses cross-line radiometric registration improvement, not another edge detector. It has no catalogue-derived inputs. Quaternary fault detection remains the response; calling the task “vent discovery” does not turn these rasters into vent truth.

The shared final-dot validator had a real path-backed-registry bug: it loaded `reg_arr` then accessed nonexistent `reg['arr']`. Fixed in the shared tool, with file-backed regression coverage. Undefined final-dot correlations now fail closed, consistent with the surface check. The shared single-feature canary now measures finite-value and missingness discrimination and rejects inverted leakage or missing classes. The submission checker now returns a negative receipt instead of crashing for an all-nodata file, and explicitly labels its legacy `ok_to_upload` flag as format-only.

## Official-source verification and access limits

Freshly read official source: [DrivenData reference solution, pinned commit aebe92f](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b). README documents CPU-only operation. Notebook cells 3, 16 and 19 show CPU fallback, Tversky training-loss weights, and one-band georeferenced output. **The notebook is not an independent implementation of the competition's 300 m distance-weighted scoring rule.** Do not conflate its training loss with leaderboard DTI. The existing metric transcription and brute-force tests remain local evidence, with historical source provenance in `registry/sources.json`.

Official records supplied for manual review, **not freshly fetched from this sandbox**: [problem/format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [GDR 1391](https://gdr.openei.org/submissions/1391), [INGENIOUS](https://gbcge.org/current-projects/ingenious/). Current rules, eligibility, weekly remaining slots and score receipts were not verified. No DrivenData scraping or upload occurred. No credentials are requested.

## Next session, in order

1. Treat the ROD run card as authoritative for this experiment; never repeat/tune a negative arm under the same preregistration.
2. Resolve the literal dense-lattice lane constraint explicitly before allocating another large-budget fit. Preserve all historical duplicate flags.
3. Repair or quarantine old validator/packager routes that do not require every feature canary and exact-artifact gate. No website claim should elevate `format_valid` into approval.
4. H66 SGMC confirmation remains blocked on a meaningful compilation-overlap ablation, not a blind tree multiplication that retains the same proxy geometry.
5. Verify original-source bytes, licensing, survey resolution and registration before claiming new external data are viable. Quantized radiometrics do not support confident sub-cell displacement inference.
6. Require same-run best comparator, fresh confirmation, surface/final-dot checks, exact-file validation and a separate selector decision. Record an organizer receipt only after a genuinely authorized submission. Do not manufacture one to satisfy a desired label.
