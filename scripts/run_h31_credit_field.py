#!/usr/bin/env python3
"""H31-1 — credit-field candidate selection and dotting on the hide-and-recover holdout.

Pre-registered in ``knowledge/13_preregistered_h31_credit_field_emission_2026-10-25.md`` (committed before any run).

Arms share one HGB fit per (fold, draw) cell, exactly as in ``scripts/run_h28_holdout.py``:

* C  (control): raw-score ridge candidates, score-ordered dots, 2.4 px, kfrac 0.035 (the H28 comparator arm).
* A1 (primary): u = value_field(normalised score); candidates = top-K ridge NMS of u; dots ordered by u; 2.4 px; kfrac 0.035.
* A2 (secondary): as A1 with kfrac 0.0245.

Reproduction gate: the control arm's DTI must equal ``evidence/h28_holdout/cells.jsonl`` row-for-row (1e-6) for the same
fold/draw. A mismatch voids the run.

    python scripts/run_h31_credit_field.py --draws 0 1 --out evidence/h31_screen        # screen
    python scripts/run_h31_credit_field.py --draws 2 3 --out evidence/h31_confirm       # only if screen passes
    python scripts/analyze_h31_credit_field.py evidence/h31_screen ...                  # paired gate
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.livecal import value_field  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS, normalised  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
MIN_DIST = 2.4
ARMS = (
    {"arm": "C", "kind": "score", "kfrac": 0.035},
    {"arm": "A1", "kind": "credit", "kfrac": 0.035},
    {"arm": "A2", "kind": "credit", "kfrac": 0.0245},
)
H28_CELLS = ROOT / "evidence" / "h28_holdout" / "cells.jsonl"


def credit_emission(cell: Cell, p: np.ndarray, kfrac: float) -> tuple[np.ndarray, np.ndarray]:
    """A1 emission: candidates from the ridge NMS of the credit field u, dotted in u order."""
    s_crop, _ = cell.candidates(p, 0)  # score crop (domain-masked grid), k unused
    s_norm = normalised(s_crop, cell.dom_c)
    u = value_field(np.where(cell.dom_c, s_norm, 0.0))
    k = int(round(kfrac * cell.dom_c.sum()))
    r = ridge_nms(u, cell.dom_c, 1.0)
    sc = np.where(r & ~cell.known_c, u, 0.0)
    top = select_top_positive(sc, cell.dom_c, k)
    return score_ordered_dots(u, top, MIN_DIST), top


def h28_reference() -> dict:
    ref = {}
    for line in H28_CELLS.read_text().splitlines():
        row = json.loads(line)
        if row["value"] == "score" and row["min_dist"] == MIN_DIST and row["kfrac"] == 0.035:
            ref[(row["fold"], row["draw"])] = row["dti"]
    return ref


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cells_path, design_path = out / "cells.jsonl", out / "design.json"
    if cells_path.exists() or design_path.exists():
        raise SystemExit(f"refusing to overwrite {out}; choose a fresh --out")
    design = dict(
        hypothesis="H31-1 credit-field candidate selection and dotting",
        preregistration="knowledge/13_preregistered_h31_credit_field_emission_2026-10-25.md",
        draws=a.draws, folds=list(FOLD_IDS), arms=list(ARMS), min_dist=MIN_DIST,
        model={"base": BASE, "extras": EXTRAS, "fit_seed": "draw"},
        reference="evidence/h28_holdout/cells.jsonl (score, 2.4, 0.035)",
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")  # frozen before any fit

    ref = h28_reference()
    ctx = load_context(work_dir())
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True)
                p, timing = cell.fit_predict(cols, seed=draw)
                for arm in ARMS:
                    t0 = time.time()
                    k = int(round(arm["kfrac"] * cell.dom_c.sum()))
                    if arm["kind"] == "score":
                        s_crop, top = cell.candidates(p, k)
                        emitted = score_ordered_dots(s_crop, top, MIN_DIST)
                    else:
                        emitted, _ = credit_emission(cell, p, arm["kfrac"])
                    ev = cell.evaluate(emitted)
                    row = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm["arm"], kind=arm["kind"],
                               min_dist=MIN_DIST, kfrac=arm["kfrac"], auc=cell.auc(p),
                               emit_s=round(time.time() - t0, 2), **ev, **timing)
                    if arm["arm"] == "C":
                        row["h28_reference_dti"] = ref.get((fold, draw))
                        row["reproduces_h28"] = ref.get((fold, draw)) is not None and abs(ev["dti"] - ref[(fold, draw)]) <= 1e-6
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {arm['arm']}: DTI={ev['dti']:.6f} "
                          f"emitted={ev['emitted']}", flush=True)
                del cell
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
