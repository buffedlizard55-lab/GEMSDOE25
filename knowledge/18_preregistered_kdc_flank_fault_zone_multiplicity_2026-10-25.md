# 18 · Pre-registration — G25-K5 "fault-zone multiplicity flank complement" (experiment 2 of 3)

**Status:** frozen and committed before experiment 2 runs. Written 2026-10-25 after experiment 1 (`evidence/kdc_screen/`) failed
its gate. This is a *new* hypothesis with its own gate; it does not rescue or re-label G25-K1 (which stays failed).

## What experiment 1 established (COMPUTED, `evidence/kdc_screen/analysis.json`)

* G25-K1 K_self (complement anywhere outside the 3 px halo of the base's raw candidates): HOLDOUT-DTI 0.14906 vs CB 0.14975,
  paired −0.0007 (2/4 folds), pooled efficiency R = 0.505 but only 2/4 folds ≥ 0.50 → **FAIL**.
* GEM-1 complement R = 0.17, random complement R = 0.18 → GEM-1 carries no complement information on this holdout.
* Leakage canary clean (max single-feature AUC* 0.8045, model 0.834).
* At holdout DTI ≈ 0.15 the paired gate G1 requires R > 0.57 (holdout break-even 0.2·0.15/(1−0.03) ÷ CB's 0.054); this is stricter
  than the live break-even R\* ≤ 0.472. G1 stays in force (AGENTS.md rule 5).

## Hypothesis G25-K5

* **Layers:** the same HGB (BDE + 7 add-ons) score; geometry relative to the incumbent's raw candidate lines.
* **Physical signature:** Basin-and-Range normal-fault and Walker Lane dextral zones are commonly multi-stranded — synthetic/antithetic
  splays, step-overs and distributed parallel strands — so a mapped or detected strand predicts further strands a few hundred metres
  away (cf. distributed faulting and step-over architecture of the northern Walker Lane, Wesnousky 2005,
  <https://doi.org/10.1029/2004TC001645>). Complement dots are therefore restricted to the **flank band 3 < d ≤ 8 px (300–800 m)**
  from the incumbent's raw candidates, ranked by the HGB score.
* **Why catalogue-missing:** the band excludes ≤ 2 px of the catalogue (finding 3 of knowledge/17) and ≤ 3 px of the incumbent, so
  every dot is a would-be *additional* strand that neither the catalogue nor the incumbent touches.
* **Difference from repo/registry:** K1 used the whole eligible zone (far-field dominated); tip/step-over additions (GEMSDOE28/33) live
  *inside* H19-5; swap files replace dots. No registry file adds a parallel-strand band outside the H19-5 halo.
* **Named non-fault mimic:** parallel drainage/terrace risers and pluvial shoreline flights alongside range fronts.

## Frozen design (same cells as experiment 1: draws 0, 1; same model, CB base, M = round(0.4706·|CB|))

* `K_flank` (**primary**): CB + M score-ordered 2.4 px HGB ridge-NMS dots with 3 < d(raw top-K) ≤ 8 px, d(visible) > 2 px, in domain.
  If fewer than M dots exist the arm is reported with its count and is **ineligible for packaging** (lane share would not hold).
* `K_far` (contrast): same, d(raw top-K) > 8 px.
* `K_self` (reproducibility anchor): identical to experiment 1 (must reproduce its cells exactly).
* `K_rand` (gate G3, as experiment 1): random dots in the whole eligible zone.
* `K_rand_flank` (diagnostic only): random dots in the flank band — separates band effect from detector effect; not a gate.
* **Gate for K_flank (all must hold; then confirmation on draws 2, 3 with the same gate):** G1 paired vs the same-run best of C/CB:
  mean > +0.001, ≥ 3/4 folds positive, worst ≥ −0.01. G2 pooled R ≥ 0.50 and ≥ 3/4 folds ≥ 0.50. G3 K_rand pooled R < 0.50.
  G4 leakage canary (AUC* ≤ 0.90).
* Live build if and only if screen + confirmation pass: as knowledge/17 §3 but with the complement restricted to
  3 < d(H19-5) ≤ 8 px.
