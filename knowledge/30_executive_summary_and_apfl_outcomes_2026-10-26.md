# 30 · Executive summary — nine focus sites, why 0.2778 won, and this session's APFL test (2026-10-26)

**Session:** `arena/8aa4ff79-gemsdoe25` · **Pre-registration:** knowledge/29 (commit `e78a10b`, before any fit) ·
**Run card:** `registry/run_card_apfl2_2026-10-26.json` · **Evidence:** `evidence/apfl_direct_screen/`,
`evidence/apfl_hgb_screen/`, `evidence/focus_audit_session_2026-10-26.json`, `evidence/apfl2_lane_surface.json`,
`evidence/apfl2_score_scenarios.json`. No DrivenData page was accessed (AGENTS.md rule 3). The agent never uploads.

**Evidence classes:** OWNER-REPORTED = score supplied in the owner brief / sibling ledger, no organizer receipt in
this repo · HOLDOUT-DTI = local catalogue-gap proxy (evaluator + withheld count + CI always stated) · COMPUTED =
re-derived here from pinned bytes (script named) · INFERENCE = algebra/scenario with assumptions stated. A projection
is never written as a score.

---

## 1. Decision first — what to download, estimated score, uniqueness

> ## ⛔ OK TO SUBMIT A NEW FILE THIS SESSION: **NO**
> Both pre-registered APFL screens failed the frozen gate vs the same-run H35 control. The new GeoTIFF below is
> format-valid and unique vs every focus site, but it is **testing-only — DO NOT SUBMIT**. The historical best
> (GEMSDOE32 B2, 0.2778 OWNER-REPORTED) was already submitted; resubmitting it (or any file >70% within 3 px of it)
> would be a duplicate, not a new entry. There is no honest "download this and submit it" file today.

| # | File to download | What it is | Score / estimate (class) | Unique vs the 9 focus sites? | OK to download | OK to submit |
|---|---|---|---|---|---|---|
| 1 | `docs/downloads/gems25-apfl2-h35plus-apfl-b2-sapd2-4-k3p5-20261026-2e9e4189f554-zeros.tif` (48,658 dots, SHA-256 `8be65a3e…93c8ad`, + `.zip`) | **New this session.** H35 HGB + 7 reconstructed APFL piedmont-flexure columns, B=2 collar, sapd2.4, zeros outside (passes strict whole-array [0,1]) | **HOLDOUT-DTI 0.149487** (recipe arm, evaluator `gems25.holdout.v1.2-buffered-4quad-pooled-dti`, 22,931 withheld positives, 95% CI in run card) — *screen FAIL*. **Live: no reliable estimate exists.** INFERENCE scenarios only: 0.223 if it earned dotted-H19-5 credit/px, 0.319 if it earned B2 credit/px (`evidence/apfl2_score_scenarios.json`); the HGB lineage's live anchor in the brief is 0.0742 (H66, OWNER-REPORTED), so live could be far below both | **YES** — dots within 3 px: 24: 35.8% · 25: 34.4% · 27: 37.9% · 28: 32.9% · 30: 34.4% · 31: 33.3% · **32 (B2): 31.6%** · 33: 34.0% · 36: 32.1% (cap 70%); surface \|ρ\| 0.158 (cap 0.90); not byte-identical to any registry raster. **NO vs this repo's own HGB testing lineage** (75–93%, same H35 family) — disclosed, see §5 | **YES** (testing) | **NO — DO NOT SUBMIT** |
| 2 | `docs/downloads/gems25-apfl2-h35plus-apfl-b2-sapd2-4-k3p5-20261026-2e9e4189f554-nan.tif` | Same dots, NaN-outside (official convention) twin | Same as above | Same dots as #1 | YES (testing) | **NO** (also fails the strict whole-array validator variant; use zeros twin if a future file is ever cleared) |
| 3 | — (not hosted as a new download) | GEMSDOE32 `h33-h33-2-b2-…-e5eb6e7e-zeros` (37,654 dots) | **0.2778 OWNER-REPORTED** (no organizer receipt) — highest supplied result among focus sites | It *is* a focus-site file; any near-copy is a duplicate lane | Learning only via pinned mirror | **NO — already submitted; do not resubmit** |
| 4 | Older testing TIFs in `docs/downloads/` (H71, H66, H38, …) | Prior sessions' negatives | HOLDOUT-DTI per their run cards; no live scores except H66 0.0742 OWNER-REPORTED in brief | Varies per run card | YES (testing) | **NO** |

**Why no point estimate for the new file?** (i) The holdout is a catalogue-gap proxy; its association with live
scores measured by GEMSDOE24 is Spearman +0.33 (n=24, not significant). (ii) The only live anchor for this repo's
supervised HGB lineage in the supplied list is 0.0742 — far below its holdout numbers — while the live champion is
an *unsupervised* ridge surface. Averaging those into a single "estimated score" would be a hallucination. The
scenario bracket above is exact DTI algebra under two stated credit-per-pixel assumptions, not a forecast.

---

## 2. Executive summary for every focus site (fresh pixel audit this session)

Recomputed line by line from pinned mirrors (`scripts/audit_focus_sites_session.py` → `evidence/focus_audit_session_2026-10-26.json`).
All nine SHA-256s match their pins; all nine pass the hard format checks vs the pinned template; zero dots sit on
catalogue pixels in any of them. Scores are OWNER-REPORTED in every row.

| Site | Best supplied submission | Score (OWNER) | Dots (COMPUTED) | Pixel-exact identity (COMPUTED) | Strict `[0,1]` whole-array? | Executive verdict |
|---|---|---:|---:|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `h25-1-dotted-h19-5-d1-5-…-989f59505db1-nan` | 0.2477 | 60,069 | `dot_thin(H19-5, 1.5)` | No (NaN outside) | The dotting breakthrough (+0.0555 over solid H19-5). Superseded by wider dotting. Learning only. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `dotted-h19-5-d2-8-…-e56ea318af89-nan` | 0.2600 | 44,090 | Wider dotting (D2.8) | No (NaN outside) | Emission optimum for the H19-5 surface. Mask identical to GEMSDOE30 — not independent evidence. Do not repackage. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `topo-gap-closure-t-v2-on-d1-5-…-5512495c6bd1-nan` | 0.2449 | 61,328 | D1.5 ∪ exactly 1,259 extra dots (superset verified) | No (NaN outside) | Gap-closure dots *hurt* (−0.0028 vs D1.5): denominator without credit. Negative control for "more dots". |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `h36-1-rung30-blind-r1-…-b531dae0a36f-nan` | 0.2710 | **37,660** (corrects knowledge/28's "40,199*") | Distinct ~B2-budget surface: only 26,248 exact pixels shared with B2, but 95.5% within 3 px of B2 | No (NaN outside) | Best of 28's four (0.2707–0.2710 spread is within noise; no CIs exist). Near-B2 geometry without being B2. Runner-up tier, already submitted. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `d28-poisson300m-offcat-44090-…-91eae1ca` | 0.2600 | 44,090 | Mask **identical** to GEMSDOE25 D2.8 (verified) | No (NaN outside)* | Same prediction set as 25 under a new name. Zero independent information. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `h27-4-solo-d28-…-8acb75e1-nan` | 0.2708 | 40,199 | = R1 = `D2.8 & EDT(~cat)>1` (verified; deletes 3,891 dots at d≤1 px) | No (NaN outside) | Proves the first collar shell was near-worthless. One shell short of B2. Already submitted. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | **`h33-h33-2-b2-…-e5eb6e7e-zeros`** | **0.2778** | **37,654** | = `D2.8 & EDT(~cat)>2` (verified; deletes 6,436 total: 3,891 at d≤1 + 2,545 at 1<d≤2) | **Yes** (zeros outside) | **Clear winner of the nine.** Only file that removes both low-credit shells. Already submitted — the lesson (prune below break-even) is reusable, the file is not. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `h33d-analog-tip-stepover-r30-…-cb490425926e` | 0.2632 | 41,865 | Re-admits near-catalogue/tip dots vs R1 lineage | No (NaN outside) | Re-adding collar dots costs −0.0076 vs R1. Second negative control confirming B-collar direction. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `anderson-geothermal-pinn-38854-…-9b9ea4e6-zeros` | 0.2750 | 38,854 | = B2 ∪ exactly 1,200 extra dots (superset verified) | **Yes** (zeros outside) | The 1,200 "PINN" extras dilute B2 by −0.0028. Shows B2's budget is near a local optimum for that surface; a physics label is not evidence of new detections. |

\* GEMSDOE30's pinned mirror checked here is the NaN-outside byte variant; a zeros-outside twin would pass strict.

**Obvious best historical submission: GEMSDOE32 B2 (0.2778).** It leads the next focus site (36: 0.2750, itself
96.9% B2) and every non-B2-derived file by ≥0.0068. **Obvious best *new* submission: none yet** — see §4–5.

---

## 3. Why and how did B2 get 0.2778? (PhD-level answer, verified line by line)

**Lineage (COMPUTED pixel identities + OWNER scores):**
H19-5 solid unsupervised ridge surface (121,131 px, 0.1922) → score-blind dotting at 1.5 px (60,069 px, 0.2477,
**+0.0555**) → wider dotting D2.8 (44,090 px, 0.2600, **+0.0123**) → B=1 collar R1 (40,199 px, 0.2708, **+0.0108**)
→ B=2 collar B2 (37,654 px, 0.2778, **+0.0070**). Two of the three gains change *no geology at all* — they delete pixels.

**Metric mechanism (exact algebra).** DTI = T / (0.2·(T+F) + 0.8·N) with a 300 m triangular kernel crediting each
truth pixel by the *maximum* kernel value over nearby dots. A second dot covering the same truth pixel therefore
adds ≈0 credit but full false-positive mass. A marginal pixel helps iff (extra credit)/(extra FP mass) >
τ = 0.2·D/(1−0.2·D) — at D=0.2778, τ=0.0588 (per-pixel credit bar 0.2·D=0.0556; both forms in the audit JSON).
Prior live-anchor modelling in this repo (knowledge/27, conditional on the owner scores) puts the deleted shells'
mean credit at 0.0010/px (d≤1) and 0.0050/px (1<d≤2) — 50× and 11× below break-even. Deleting them is almost pure
denominator reduction. This session re-verified the counts (3,891 + 2,545 = 6,436) and identities exactly; the
per-shell credit figures remain model-based INFERENCE, not hidden-label measurements.

**Geological reading (INFERENCE).** Catalogue traces are 100 m polylines that can sit 100–200 m from the true scarp
crest; an unsupervised ridge detector fires parallel duplicates 1–2 px off mapped faults. Those flank dots cannot
earn "new fault" credit (known pixels are masked; near-known wrong pixels are penalised), while genuinely unmapped
faults (blind piedmont scarps, step-over splays) lie farther away. Pruning the 0–200 m collar therefore trades away
almost no coverage of hidden truth. **Caveat that stays on record:** staff wording recorded in knowledge/03 says
test labels include "corrections or modifications" within 300 m of known traces, so a blanket collar is *not*
risk-free in principle; B2's single owner-reported result (no CI, no receipt) does not prove the mechanism, and
GEMSDOE32's own page projected 0.2747 for this file, not 0.2778.

**Why the others lost, in one line each:** 27/33/36 each *added* dots below break-even credit density and paid for
them (−0.0028, −0.0076, −0.0028 respectively); 24/25/30 kept redundant neighbours the kernel had already paid for;
28/31 stopped one shell early. Emission economics, not detector branding, separates the table.

---

## 4. Can we generate something higher than 0.2778? What this session tested

**Arithmetic requirement (INFERENCE, N≈12,503 hidden-truth px from the blind-lattice calibration):** B2's implied
credit is ≈4,871 weighted TP (0.1294/px). At the new file's 48,658 dots, tying 0.2778 needs 0.1127 credit/px;
reaching 0.3195 needs 0.1296/px; 0.4413 would need ≈0.179/px at that budget (or a much leaner file at B2-like
credit density). No emission trick on the H19-5 surface supplies this (its modelled ceiling is the already-scored
D2.8/B2 family). **Beating 0.2778 requires a detector with higher credit density on truly hidden faults — and a
live anchor proving it, which no supervised model in this group yet has.**

**This session (3/3 experiment budget, all HOLDOUT-DTI, evaluator `gems25.holdout.v1.2-buffered-4quad-pooled-dti`):**

| Exp | Arm | HOLDOUT-DTI pooled [95% CI] | Withheld | Same-run H35 | Paired gain (folds) | Canary max AUC | Gate |
|---|---|---|---:|---|---|---:|---|
| 1 | APFL-DIRECT B2 (draws 60–61) | 0.045617 [0.020452, 0.070781] | 22,813 | 0.152308 | −0.1062 (0/4) | 0.640 | **FAIL** (beats crest floor 0.0265 in 4/4) |
| 2 | H35+APFL (draws 62–63) | 0.148880 [CI in run card] | 22,931 | 0.148977 | −0.0009 (1/4) | 0.615 | **FAIL** |
| 2d | H35+APFL B2 (descriptive) | 0.149487 | 22,931 | 0.148977 (B2 ctrl 0.149166) | — | — | descriptive only |
| 3 | OCEM off-catalogue diagnostic | `dti_offcat2 == dti` in all 32 cells | — | — | — | — | Finding: ≥200 m restriction vacuous by construction |

**Interpretation.** (i) Catalogue-free DIRECT physics fields keep failing on the catalogue-gap proxy (H71 ×3, ROD,
now APFL) while beating unsupervised floors — the proxy rewards catalogue-like recovery, so these negatives do not
prove the geology is wrong for *live* hidden faults; they prove it is not validated. (ii) As HGB columns, APFL adds
nothing over H35 (gain −0.0009, CI includes 0): the incumbent features already contain its information on this proxy.
(iii) B2-style collaring with budget *refill* is ~neutral on the proxy (+0.0002…+0.0006 pooled); the live B2 effect
was deletion *without* refill at constant surface — a different operation the proxy cannot score honestly (its truth
is catalogue). Any future claim to beat 0.2778 must therefore be anchored by an actual organizer receipt for this
lineage, not by another proxy decimal.

---

## 5. Automatic validation gates for the new TIF (no human inspector)

All checks run by project code (`gems25.submission.check_file`, lane checkers, holdout harness) and re-verified
independently with plain `rasterio` this session. **Format-green is not slot-green.**

| Gate | Rule | New file (`…2e9e4189f554-zeros.tif`) | Receipt |
|---|---|---|---|
| Format | Single-band float32, EPSG:32611, 3730×3292, template transform, finite [0,1] in 5,167,373-px footprint | **PASS** (0 hard failures; values {0,1}; 48,658 positives; 0 on catalogue) | `docs/downloads/checks-…-zeros.json` |
| Portal `[0,1]` error | Strict `((a>=0)&(a<=1)).all()` incl. outside footprint | **PASS** (zeros outside, no NaN anywhere) — NaN twin FAILS this variant by design | independent rasterio check, §1 |
| Leakage canary | Every APFL feature alone (raw/inverted/missingness) AUC ≤ 0.90 | **PASS** (max 0.640 Exp1, 0.615 Exp2) | `evidence/apfl_*/cells.jsonl` |
| Holdout vs same-run best | Gain >+0.001, ≥3/4 folds, worst ≥−0.010, hug ≤+0.10 | **FAIL** twice (Exp1 −0.106 0/4; Exp2 −0.001 1/4) | `evidence/apfl_*/analysis.json` |
| Lane — surface | \|Spearman\| ≤ 0.90 pre-placement vs registry | **PASS** (0.158) | `evidence/apfl2_lane_surface.json` |
| Lane — final dots vs focus/scored | ≤70% within 3 px vs any focus/external scored raster | **PASS** (worst focus 37.9%, worst external 67.1%, B2 31.6%) | `docs/downloads/lane-…-zeros.json` |
| Lane — own lineage + lattice (literal) | ≤70% vs *any* registry raster incl. own downloads | **FAIL** (own HGB lineage 75–93%; r13 lattice 100%, halo covers 99.87% of footprint) | same receipt; IR-25-LANE-DENSITY |
| Slot approval | All above + separate selector step | **NO — DO NOT SUBMIT** | `registry/run_card_apfl2_2026-10-26.json` |

Unique name + note for the new file (research identifier only, 106 chars):
`GEMSDOE25 APFL2 H35+APFL B2 sapd2.4 | holdout FAIL; no slot; unscored; not slot-approved | id 2e9e4189f554`

---

## 6. Exactly how to submit — *only* for a future gate-cleared file

1. Confirm this page's banner for the *specific* file says **OK to spend a weekly slot: YES** (today: **NO** for every file).
2. Download the **zeros-outside** `.tif` (or its single-TIF `.zip`) from the download card; verify the SHA-256 shown matches your download.
3. On DrivenData → DOE GEMS → *Make a submission*: choose that one file (`.tif` or `.zip` containing a single GeoTIFF).
4. Paste the file's note (≤140 chars) from its download card into **Note**.
5. Submit once; save the organizer receipt/score screenshot. Record it with `scripts/record_live_score.py` so the score becomes ORGANIZER-anchored instead of owner-reported.
6. Never submit two same-lineage files expecting independent information (this file shares >90% dot neighbourhoods with the H35 testing file).

If the portal ever returns *"Predicted values must be in range [0, 1]"*: you uploaded a NaN-outside or otherwise
non-finite file — use the zeros-outside twin whose strict whole-array check passes, and re-run
`gems25.submission.check_file` on the exact bytes first.

---

## 7. Irregularities flagged for review (this session)

1. **APFL builder was missing.** The shipped APFL TIF (`8aebdab87158`) had a run card + frozen formula but no code in `src/`/`scripts/`. Fixed by reconstruction (`src/gems25/apfl.py`); the reconstruction's product differs from the shipped file (new HGB file's overlap vs shipped APFL dots: 22.6% within 3 px) — treat shipped-APFL claims as unreproduced.
2. **knowledge/28 dot-count error:** GEMSDOE28 rung30 has 37,660 dots, not "40,199*" (that's R1/GEMSDOE31). Corrected in §2 from fresh counts.
3. **Off-catalogue holdout as previously proposed is vacuous at ≥200 m** (whole-component hiding ⇒ truth ≥2 px from visible by construction). A useful variant needs ≥3–5 px or distance-stratified scoring — not run here (would be post-hoc tuning on used draws).
4. **Leaderboard conflict unresolved:** brief states both 0.4413 and 0.3195 as "the" high score; neither has a receipt here. All planning uses B2 0.2778 (OWNER-REPORTED) as comparator, not either leader claim.
5. **No ORGANIZER-CONFIRMED score exists in this repo.** Every live number above is OWNER-REPORTED; every local number is HOLDOUT-DTI. Template/data are owner mirrors (SHA-pinned, not organizer-authenticated — IR-25-PROVENANCE).
6. **Lane policy tension:** the literal 70% rule vs the r13 lattice (99.87% halo) + accumulated own-lineage downloads makes *any* HGB-lineage file a literal duplicate. Reported, not waived; resolving it is a selector/policy decision (knowledge/20 item 4).

## 8. Limitations — what I need / cannot do

- ❌ No DrivenData access (auth + ToS + AGENTS.md rule 3): cannot verify leaderboard, receipts, weekly cap, or upload. Scores stay OWNER-REPORTED until the owner supplies a receipt.
- ❌ Sandbox egress is GitHub/PyPI only: free official sources beyond the pinned mirrors (USGS ScienceBase/3DEP raw tiles, GDR downloads, ComCat) cannot be byte-verified here; hypotheses needing them (knowledge/29 ranks 4–5) are *not viable this session*.
- ⚠️ Holdout ≠ hidden-fault truth; 4 folds give wide CIs; single HGB seeds per cell (production file averages 3 draws, so recipe holdout ≠ exact-file holdout).
- ⚠️ Compute: CPU-only here is sufficient for HGB screens (~4–7 min each) but not for raw-1 m-DEM profile templates over 706 tiles (needs a networked runner).

## 9. Next steps, ranked by P(Win) — *Maximize P(Win) · Own the Outcome*

1. **Get one organizer receipt for the HGB lineage** (owner selector decision, one weekly slot on a *previously gate-passed* file such as H35 per knowledge/20 — not this session's failed file). A single anchored point recalibrates every proxy and the credit-density model; without it, "beat 0.2778" is unfalsifiable.
2. **Distance-stratified holdout (≥5 px shells)** as a *fresh pre-registered* instrument to test collar/deletion emission honestly, then re-test B-deletion (no refill) vs refill on the H35 surface.
3. **Unsupervised-surface programme for live, supervised for proxy:** live evidence favours unsupervised ridges (H19-5 family) while the proxy favours HGB — design the next detector screen with *both* instruments pre-registered and require the live-anchor model (H28) to agree before any slot.
4. **Resolve IR-25-LANE-DENSITY** with the density-normalised two-sided statistic (knowledge/22 §4) adopted explicitly by policy, so own-lineage/lattice flags stop masking real duplication.
5. Networked-runner data upgrades (raw 3DEP tiles, Siler dilation-tendency shapefile DOI 10.5066/P9YL58W6, GDR paleo layers) — each byte-verified before pre-registration.

## Sources for manual review

Competition: <https://www.drivendata.org/competitions/306/competition-doe-gems/> · problem:
<https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> · rules PDF:
<https://docs.nlr.gov/docs/fy26osti/96647.pdf> · reference solution:
<https://github.com/drivendataorg/gems-prize-reference-solution> · USGS GeoDAWN: <https://doi.org/10.5066/P93LGLVQ> ·
GDR 1391 (INGENIOUS): <https://gdr.openei.org/submissions/1391> · INGENIOUS project:
<https://gbcge.org/current-projects/ingenious/> · EPSG:32611: <https://epsg.io/32611> · Tversky index:
<https://en.wikipedia.org/wiki/Tversky_index>. Internal: knowledge/03 (staff clarifications as recorded),
knowledge/17 & 27 (prior 0.2778 forensics), knowledge/29 (this session's pre-registration).
