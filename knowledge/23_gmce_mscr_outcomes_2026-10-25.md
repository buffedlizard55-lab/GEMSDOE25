# 23 · GMCE/MSCR session outcomes: why 0.2778 won, two new-detector tests, one unique TIF (2026-10-25)

All DTI values are **HOLDOUT-DTI** (`gems25.metric.dti_binary`, α=0.2, β=0.8, R=3 px via
`Cell.evaluate`) unless labelled **OWNER** (owner-reported claims from the brief/site list, no
organizer receipt). Machine-readable card: `registry/run_card_session_2026-10-25_gmce_mscr.json`.
Pre-registrations: `knowledge/21` (committed 8198a31 before any fit), `knowledge/22` (b9c5a5e).

## 1. Answer: why and how did GEMSDOE32's `h33-h33-2-b2` get the group best (OWNER 0.2778)?

Re-verified **this session, pixel by pixel**, from hash-pinned mirrors
(`scripts/verify_b2_chain.py` → `evidence/gmce_session_b2_chain_verification.json`; all 12
identities true):

| Step | Operation (exact, COMPUTED) | Dots | OWNER DTI |
|---|---|---:|---:|
| h19-5 | solid multi-line surface | 121,131 | 0.1922 |
| D1.5 | `dot_thin(h19-5, 1.5)` | 60,069 | 0.2477 |
| D2.8 | `dot_thin(h19-5, 2.4)` ≡ `dot_thin(h19-5, 2.8)` — a **re-thinning, not a subset of D1.5** (only 29,849 shared dots; new detail, IR-25-THINNING-NONNESTED) | 44,090 | 0.2600 |
| R1 | `D2.8 & (d(catalogue) > 1 px)` | 40,199 | 0.2708 |
| **B2** | `D2.8 & (d(catalogue) > 2 px)` | **37,654** | **0.2778** |
| G36 | `B2 ⊂ G36`, +1,200 dots | 38,854 | 0.2750 |

Mechanism (from the metric's algebra, `src/gems25/metric.py`): credit per truth pixel is a
**maximum** over dots within 300 m, so extra dots on already-covered truth add ≈0 credit but
full FP mass (charged α=0.2). Each step removes or spaces low-marginal-value dots. Inverting the
OWNER scores under the stated approximations (hidden truth N=12,691 px, TP_w+FP_w ≈ emitted
mass; `analyze_focus_sites` convention) gives implied credit per deleted dot of **0.00096**
(100 m collar) and **0.00503** (100–200 m collar) against a break-even ratio τ≈0.055–0.059:
the near-catalogue dots were carrying almost no *marginal* truth credit. G36's added dots imply
0.0134/dot — still below τ — hence 0.2750 < 0.2778. Geologically this reads as: the parent
surface's near-catalogue dots are mostly scarp-apron/digitization-shadow echoes of *already
mapped* faults, not new-fault pixels. **Unresolved tension (flagged, not smoothed over):** staff
wording recorded in this repo says test truth includes corrections within 300 m of known traces,
which a blanket B2 delete would sacrifice; the OWNER score pair implies those specific dots
nevertheless earned ≈0 *marginally* (correction truth may still exist but be already covered by
the surviving 2–3 px dots, or be rare). One artefact, no CI; the realized claim also exceeds
GEMSDOE32's own 0.2747 projection.

## 2. Can we generate something higher than 0.2778?

**Not demonstrated — and this session's two designed attempts say the easy routes are closed.**
At fixed mass, +0.01 needs ≈+3.6 % credit/dot (0.1319→0.1367 under the same inversion), 0.3195
needs +15 % (0.1520), 0.4413 needs +60 % (0.2110; both targets are conflicting OWNER claims,
IR-25-LEADERBOARD-CONFLICT). Emission tricks are exhausted (thinning swept, B-collar at/over
break-even by 2–3 px, complements/greedy negative in prior sessions), so the remaining lever is
credit density from a better detector. This session tested the two cheapest *untried* detector
blocks against the **same-run recomputed holdout best** — both negative:

| Exp | Candidate vs BEST (paired, same cells) | Candidate HOLDOUT-DTI pooled (95 % CI) | Gain (folds) | Canary max AUC | Gate |
|---|---|---:|---:|---:|---|
| 1 GMCE-1 (draws 20–21) | +3 gravity–magnetic gradient-parallelism columns | 0.150125 (0.1386–0.1616) vs BEST 0.151492 | −0.001209 (1/4, worst −0.0075) | 0.560 | FAIL |
| 2 MSCR-1 (draws 22–23) | +3 multi-scale crest persistence columns | 0.161954 (0.1214–0.2025) vs BEST 0.161968 | −0.000373 (1/4, worst −0.0054) | 0.654 | FAIL |

(Withheld positives: 22,232 / 22,391 pooled across cells. Work caches bit-identical to the
2026-10-03 pins — six of six SHA-256 match — so comparator drift is excluded here.)

**PhD-level reading:** two *a-priori* reasonable, independent physical transforms of the same 19
bands both land within noise of zero on fresh draws, in different families (A-derivative, then
B-derivative). Combined with H34's earlier near-miss (+0.0023, 2/4) and H35's tip-driven pass,
the parsimonious conclusion is that this HGB stack has extracted essentially all the
*holdout-visible* signal in the supplied bands; remaining live headroom, if any, lives in
**new data** (the blocked rank-5 layers: GDR paleo-geothermal, USGS heat flow, raw 1 m DEM
tiles) or in **label-side knowledge we cannot ethically obtain** — not in another transform.
Chasing further static columns on this proxy now has an unfavorable P(Win)/slot-risk ratio.

## 3. The unique TIF (must-generate requirement) — and its obvious status

**`gems25-mscr-multiscale-crest-sapd2-4-k3p5-20261025-dd2bb4b09cd2-zeros.tif`**
(48,442 dots; SHA-256 `0c8b7e91…db7ea5`; content id `dd2bb4b09cd2`; NaN twin + single-TIF ZIP
in `docs/downloads/`). New full-catalogue fit; **no previous submission's dots are copied** —
vs B2 only 31.5 % of its dots lie within 3 px, surface Spearman vs B2 +0.055.
Independent exact-file audit (plain rasterio, `scripts/verify_candidate_independent.py`):
single-band float32, EPSG:32611, 3730×3292, transform identical to template, **all
5,167,373 footprint values finite in [0,1]**, zeros file passes the strict whole-array
`0≤x≤1` test (the reported portal error cannot be triggered by this file's *values*), 0 dots on
catalogue pixels, ZIP contains exactly its bytes.

> ### ✅ OK to download (local testing/reproduction): **YES**
> ### ❌ OK to submit / spend a weekly slot: **NO — DO NOT SUBMIT**
> Both pre-registered holdout gates FAILED (necessary condition not met) and the literal strict
> lane rule stops it (100 % of dots within 3 px of the dense r13 lattice; 0.76–0.92 vs this
> repo's own H31/H35 lineage). Note to paste *if a future selector ever reverses this*:
> `GEMSDOE25 MSCR-1 sapd2.4 k3.5% | holdout gate FAIL; no slot; unscored; not slot-approved | id dd2bb4b09cd2` (106 chars).
> This status is machine-generated from the gates + lane checks — no human inspection step remains.

## 4. What was verified without human intervention this session

Data restored by SHA-256 (core/external/scored groups + 30-raster artefact ledger + 21
top-scorer mirrors); caches rebuilt and hash-matched; B2 chain identities recomputed; canaries
run before gates; BUILD→writer→independent audit→lane (strict + extended: 50 external sparse
rows, lattice, 8 own-lineage) all scripted; run card assembled only from tracked JSONs
(`scripts/build_run_card_session.py` asserts every input exists). Nothing contacted
drivendata.org (AGENTS rule 3); no submission was uploaded by the agent.

## 5. Limitations, irregularities, next work (owner decisions in **bold**)

* Scores 0.1922…0.2778, leader 0.3195/0.4413: **OWNER claims; supply an organizer receipt to
  upgrade any of them to ORGANIZER-CONFIRMED.** The brief's two leader numbers conflict.
* **Lane policy:** under the merged literal rule *no* file can ever clear the dense-lattice test
  (any in-footprint dot is within ≤2.83 px of a 5-px grid). Promoting anything in future needs
  either an owner waiver for dense registry rasters or a sparse-registry definition — a policy
  decision, recorded at IR-25-LANE-DENSITY, not an agent decision.
* Holdout = catalogue-gap proxy (Spearman +0.33 n.s. vs live): even a pass would be
  necessary-not-sufficient. A catalogue-distance-stratified holdout would let B2-style pruning
  and junction fields be tested honestly (IR-25-HOLDOUT-DOES-NOT-TEST-PRUNING).
* Blocked data (need a networked runner; sandbox allows github/pypi/npm only): GDR 1391
  `paleo_geothermal_regional.zip`, USGS heat flow DOI 10.5066/P9BZPVUC, USGS slip/dilation
  DOI 10.5066/P9YL58W6, raw 3DEP 1 m tiles (10 missing tiles, IR-25-DEM-TILES).
* Session budget used: 2/3 experiments; confirmation deliberately not run after screen FAILs.
* Recommended next session, in order: (1) fetch+pin one blocked external layer on a networked
  runner and pre-register its test; (2) build the distance-stratified holdout variant;
  (3) only then consider a new detector experiment. Do not queue more same-band transform columns.
