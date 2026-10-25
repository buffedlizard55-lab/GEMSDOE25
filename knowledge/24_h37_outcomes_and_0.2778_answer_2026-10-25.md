# 24 · Session-7 answer: why 0.2778, whether we can beat it, and two new negatives (2026-10-25)

All DTI values are **HOLDOUT-DTI** (`gems25.metric.dti_binary`, α=0.2, β=0.8,
R=3 px) unless labelled **OWNER** (owner-reported claims, not organizer receipts).
**No number in this repo is ORGANIZER-CONFIRMED.** Machine-readable card:
`registry/run_card_h37_2026-10-25.json`. Pre-registrations: knowledge/22 (commit
7618687, before any fit) and knowledge/23 (commit 75696c8).

## 1. Why the GEMSDOE32 B2 file scored highest — re-verified this session

`scripts/verify_b2_chain.py` fetched the GEMSDOE28/32/36 rasters from the owner's
public GitHub repos, required SHA-256 to equal the pins in
`evidence/focus_sites_forensics.json`, and recomputed every identity
(`evidence/h37_b2_recheck.json`, COMPUTED):

| Relation | XOR (px) |
|---|---:|
| D2.8 (44,090) ⊆ H19-5 (121,131) | 0 outside |
| B1/r1 (40,199) = D2.8 & (d(catalogue) > 1 px) | **0** |
| **B2 (37,654) = D2.8 & (d(catalogue) > 2 px)** | **0** |
| GEMSDOE36 (38,854) = B2 + extra | exactly +1,200, 0 missing |

So the OWNER chain 0.1922 (solid H19-5) → 0.2477 (dot-thin 1.5) → 0.2600 (D2.8)
→ 0.2708 (B1) → **0.2778 (B2)** is, at steps 1 and 3, *the same detected set with
less redundant/near-catalogue mass* — not new geology. The mechanism is the
metric's algebra (COMPUTED, `src/gems25/metric.py`): a truth pixel's credit is the
**maximum** triangular-kernel value over nearby dots, so a second dot covering the
same truth adds ≈0 credit but ≈1 FP unit charged at α=0.2. A dot is worth keeping
iff its marginal credit/FP ratio exceeds `α·D/(1−α·D)` = 0.0588 at D=0.2778.
Inverting the reported steps (assuming |G|≈12,691 px, `evidence/focus_sites_forensics.json`):
the deleted 0–1 px shell carried ≈0.0010 credit/px and the 1–2 px shell
≈0.0050/px — 10–50× below break-even — and GEMSDOE36's 1,200 added dots carried
≈0.0134/px, also below break-even, consistent with its lower 0.2750 (OWNER).
Caveats stay on record: this is one artefact per step with no paired CI, and a
blanket 200 m exclusion is in tension with the recorded staff wording that test
labels include "corrections or modifications" within 300 m of known traces
(knowledge/17 §2). The decomposition explains the numbers **conditional on the
OWNER scores being correct**; it does not prove the hidden-label mechanism.

## 2. Can we generate a file that beats 0.2778?

**Honest answer: not demonstrated by any session so far, including this one.**
At fixed emitted mass and truth size, DTI ≈ TP/(0.2·m + 0.8·|G|) scales
near-proportionally with total weighted credit TP, so beating 0.2778 by +0.01
needs ≈+4 % credit at the same mass; 0.3195 needs ≈+15 % (the +25 % figure
quoted from GEMSDOE32 was from a 0.26 baseline); the brief's conflicting 0.4413
(IR-25-LEADERBOARD-CONFLICT) would need ≈+59 % — if real, it cannot come from
emission tweaks on H19-5-family surfaces and implies a categorically better
detector (e.g. raw 1 m LiDAR scarp mapping or expert geologic sources this
sandbox cannot fetch). Emission economics on existing surfaces is measured to be
nearly exhausted here (H28 calibration; H31 credit-field; KDC complement
efficiency 0.505 < 1). The only remaining lever is detector credit density, and
the catalogue-gap holdout can only certify it as a proxy (proxy↔live Spearman
+0.33, n.s.). Any statement "this file beats 0.2778" would be a projection and
is never written as a score here.

## 3. Two new pre-registered experiments — both negative (deliverables)

Comparator in both: H35 arm B recomputed **in the same run** (the rebuilt caches
are bit-identical to `evidence/work_cache_hashes.json`, verified this session).

| Exp | Candidate | Draws | Candidate HOLDOUT-DTI (fold-mean, 95 % CI) | Pooled | Control | Paired gain (95 % CI), folds + | Canary | Gate |
|---|---|---|---|---:|---:|---|---:|---|
| E1 H37-1 DOC | C37 + 6 down-dip lagged-ridge cols | 14–15 | 0.1498 (0.1374–0.1622) | 0.1493 | 0.1507 / 0.1500 | **−0.0009** (−0.0069…+0.0052), 2/4 | 0.560 | **FAIL** |
| E2 H37-2 SPR | C37 + 2 spring-line alignment cols | 18–19 | 0.1606 (0.1209–0.2003) | 0.1590 | 0.1596 / 0.1580 | **+0.00094** (−0.0006…+0.0024), 3/4 | 0.522 | **FAIL** (< +0.001) |

Withheld positives per fold: E1 [1905, 2333, 3689, 3164]; E2 [1834, 2367, 3688,
3302]. Reading: (i) lagged down-dip sampling adds nothing over the zero-lag
fields already in the stack (ridge fields are spatially smooth, so a 2–4 px lag
mostly re-reads the same ridge) — southern folds positive, northern negative,
with no hug movement (+0.0006); (ii) the spring-alignment signal is small and
consistent in sign (3/4 folds, worst −0.0002, pooled +0.0010) but its support is
sparse (SPR ridge nonzero on 5.7 % of the footprint; one of eight cells emitted
identical TP/FP/emitted counts with/without the columns) and it **missed the frozen gate by
0.000063**. A near-miss is not a pass: no confirmation draws were run, no lags,
sigmas or point subsets were retried. Any SPR follow-up needs a new
pre-registration that owns this near-miss in advance.

## 4. Lane result (shared-tool fix, pre-registered in knowledge/22 §4)

`scripts/check_lane_duplicates.py` and `scripts/validate_gem_candidate.py`
lane_check now also report each registry raster's 3-px **halo coverage** (the
overlap a uniformly random dot set would score), excess-over-coverage, reverse
overlap, and symmetric-min. For the r13 lattice the coverage is **0.9987** —
the literal 70 % rule fails essentially every possible file against it, so it
cannot discriminate duplicate lanes; the density-aware symmetric statistic
decides for coverage-≥0.70 rasters only, with the literal number always printed.
Applied to the session file: clean vs other-site substantive scored rasters
(worst overlap 0.682, worst surface |ρ| 0.152 before placement; vs B2 itself
0.312) — but a true duplicate vs this repo's own H31/H35 lineage (0.928 vs H35),
as expected for added columns on the same detector. **Structural conclusion for
future sessions:** incremental feature blocks on the incumbent detector cannot
produce a lane-distinct file; a distinct lane needs a distinct candidate
universe/detector (the GEM-1/KDC pattern), which is also what a step-change in
live score would require.

## 5. The unique file and the automated submit decision

`gems25-h37-doc-dipoffset-sapd2-4-k3p5-20261025-558c08ce13bf-zeros.tif`
(48,662 dots; SHA-256 `099fe8c1…04349a`; NaN twin + zip in `docs/downloads/`).
Format: every one of the 5,167,373 footprint pixels finite in [0,1] (passes the
strictest whole-array validator behind the "Predicted values must be in range
[0, 1]" portal error), EPSG:32611, 3730×3292, transform matches the pinned
owner-mirror template (not organizer-authenticated). Note for the DrivenData
form **(research identifier only — do not use, see verdict)**:
`GEMSDOE25 H37 DOC sapd2.4 k3.5% | unscored; not slot-approved; no slot (holdout gates failed) | id 558c08ce13bf`

> **OK to download (local testing): YES · OK to submit / spend a weekly slot:
> NO — DO NOT SUBMIT** (verdict negative: both holdout screens failed; lane
> duplicate vs own H31/H35 lineage).

The featured site download therefore stays the KDC file (IR-25-FEATURED-DOWNLOAD-RATIONALE),
also DO NOT SUBMIT. **No downloadable file in this repo is currently OK to submit.**

## 6. What to do next (ranked by P(Win))

1. **Owner/meta decision on the lane policy + one anchoring slot.** Every file
   from the incumbent detector family fails the literal lane vs the lattice
   (coverage 0.9987, any file fails) and vs its own lineage. If the owner wants
   any incumbent-lineage file ever submitted, they must explicitly adopt the
   density-aware + supersession reading (knowledge/22 §4) for the H35 file —
   the only twice-gate-passed candidate — and spend one weekly slot on it; the
   resulting organizer receipt would recalibrate every proxy in this repo.
   The agent does not approve this; `slot_approved` stays false.
2. **Off-catalogue holdout instrument** (truth restricted to components ≥200 m
   from visible traces): the current proxy cannot test B2-style pruning or
   genuinely blind detectors (IR-25-HOLDOUT-DOES-NOT-TEST-PRUNING).
3. **Raw 1 m 3DEP scarp-profile detector on a networked runner** — the only
   identified lever with leader-gap-sized headroom; blocked here by egress,
   free source: <https://www.usgs.gov/3d-elevation-program>.
4. **H37-3 SGMC columns** (knowledge/22 #3): source now read directly — USGS
   SGMC geodatabase, Horton et al. 2017, DOI 10.5066/F7WH2N65, CC0 1.0; source
   state maps range 1:50,000–1:1,000,000 and a 2026 GeMS update
   (DOI 10.5066/P1A3DQZK) is recommended by USGS — use the pinned derived raster
   first, canary decisive (knowledge/22's "~1:1,000,000-scale" shorthand is
   refined here; positional accuracy at 100 m remains the caveat).
5. **SPR follow-up only as a fresh pre-registration** (e.g. temperature-weighted
   alignment as a *new* hypothesis), never as extra draws appended to E2.

## 7. Limitations

Lane registry here = restored `data/scored` (11) + `docs/downloads` (15) +
three pinned focus rasters; newer sibling-session lanes remain unchecked
(IR-25-GEMSDOE32-NEW-LANES-UNCHECKED). Pin proves mirror-consistency, not
organizer authenticity (IR-25-PROVENANCE). Four spatial folds give wide CIs;
the E2 paired CI (−0.0006…+0.0024) includes zero improvement. Sandbox egress
(github/pypi/npm) blocks ScienceBase/GDR/National-Map primary fetches; their
obtainability was checked at the listing level only where stated.

## 8. Merge note (name collision with a parallel session)

A parallel session independently used the label "H37-SEISALIGN" for a different
hypothesis (seismicity structure-tensor alignment; `knowledge/22_preregistered_h37_seisalign_2026-10-25.md`,
also negative) and its code/evidence landed on `main` first (PR #26) at
`src/gems25/h37.py`, `tests/test_h37.py`, `evidence/h37_screen/`. To merge
without overwriting either session's work, this session's module/tests/evidence
were renamed to `src/gems25/h37_doc_spr.py`, `tests/test_h37_doc_spr.py`,
`evidence/h37_doc_screen/` in the merge commit; numbers and file contents are
unchanged. "H37" in knowledge/22_doc, knowledge/23 and knowledge/24 always
means the DOC/SPR lane of this session.
