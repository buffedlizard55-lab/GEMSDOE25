# 19 · Pre-registration H35 — 2² factorial: RESMAG-FLEX (R) × directed tip continuation (T)

**Registered 2026-10-25, after the H34-1 screen result was recorded and committed
(`evidence/h34_screen/`, commit 94df062), before any H35 fit.** This is experiment 2 of the
session budget of 3. Sequential-design disclosure: H35's factors were chosen *because* of
prior results (below). That is legitimate sequential experimentation only because the
primary arm, draws, and gate are frozen here and the confirmation uses fresh draws.

## Prior evidence for the two factors (all HOLDOUT-DTI, this repo's harness)

| Factor | Evidence | Paired mean gain | Folds + |
|---|---|---:|---|
| R = H34 block (3 cols) | H34-1 screen, draws 0–1 (`evidence/h34_screen/analysis.json`) | +0.002332 | 2/4 (NW −0.0011, NE −0.0011, SW +0.0067, SE +0.0048) |
| T = `H27_tip` only | H27-1 screen, draws 4–5 (`evidence/h27_screen/`) | +0.009741 | 4/4 |
| T = `H27_tip` only | H30 T_BASE vs BASE_NO_TIP, draws 6–7 (`evidence/h30_relay_screen/`) | +0.001899 | 3/4 |
| T = `H27_tip` only | H30 T_BASE vs BASE_NO_TIP, draws 8–9 (`evidence/h30_relay_confirm/`) | +0.001849 | 2/4 |

Neither factor has ever been promoted (H27's gate was on the combined T+S arm vs a frozen
absolute comparator; H30's primary was P+S; H34 failed folds-positive). The **combination
R+T has never been run**. Rationale for complementarity (INFERENCE): R is a subsurface
potential-field edge (no catalogue input), T is catalogue-endpoint geometry (no geophysics);
their failure modes differ, and R's screen gains were southern while T's largest H27 gains
were northern — a 2² factorial estimates both main effects and R×T instead of assuming additivity.

**Named mimics:** R — lithologic/flow-margin magnetic edges, depositional base pinch-out
(knowledge/18). T — catalogue fragmentation/digitisation endpoints that are map artefacts,
not fault tips; the holdout also rewards T for reconnecting *hidden catalogue* segments,
which live faults may not resemble (hug-share gate below).

## Frozen design

* **Cells:** `Cell(extras=True, h27=True)`, folds NW/NE/SW/SE × **screen draws 10, 11**
  (unused by H26–H34 HGB screens); **confirmation draws 12, 13 only if the screen gate passes.**
* **Arms (one Cell, four fits, seed=draw, identical emission sapd2.4 / kfrac 0.035):**
  `C` = BDE+7 · `R` = C + 3 H34 columns · `T` = C + `H27_tip` · `B` = C + `H27_tip` + 3 H34
  columns (**primary**). H34 columns are appended in the same order as in the H34 runner.
* **Canary:** per-cell AUC of each of the 4 added columns alone (3 H34 + tip, tip taken
  from the Cell matrix) vs hidden-test labels; any AUC > 0.90 → stop, negative.
* **Gate (primary B vs same-run C, each stage separately):** mean paired gain > +0.001,
  ≥3/4 folds positive, worst fold ≥ −0.010, **and** mean hug-share increase ≤ +0.10
  (the H27 preregistration's catalogue-hug guard, `knowledge/09`).
* **Reporting:** HOLDOUT-DTI (evaluator `gems25.metric.dti_binary`, α=0.2, β=0.8, R=3 px),
  withheld positives per fold, 95 % CI (t over 4 fold means), plus descriptive 2² effects
  (R, T, R×T) per fold. `R` and `T` single-factor arms are **diagnostics only — never
  promotable post hoc**, whatever they score.
* **TIF selection rule (frozen):** if B passes screen *and* confirmation, the session's
  primary unique TIF is the full-footprint B build (promote-eligible, subject to lane +
  exact-file audit). Otherwise the primary TIF is the already-registered H34 arm-A build
  (knowledge/18), labelled negative / do-not-submit, and no H35 TIF is built.
