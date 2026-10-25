#!/usr/bin/env python3
"""H34-1 RESMAG-FLEX — paired hide-and-recover screen/confirmation (knowledge/18, frozen).

Arms share one `gems25.experiment.Cell` per (fold, draw); only the feature set differs:
  C — BDE + 7 add-ons (H28 comparator configuration, recomputed here), seed=draw
  A — C plus the 3 H34 columns (`gems25.h34.load_h34_sidecar`), seed=draw
Emission for both: ridge-NMS candidates -> top-K (kfrac 0.035) -> score-ordered dots 2.4 px.
Per-cell leakage canary: AUC of each H34 column alone vs hidden-test labels (cap 0.90).

    .venv/bin/python scripts/run_h34_resmag_flex.py --draws 0 1 --out evidence/h34_screen
    .venv/bin/python scripts/run_h34_resmag_flex.py --draws 2 3 --out evidence/h34_confirm   # only if screen passes
    .venv/bin/python scripts/analyze_h34_resmag_flex.py evidence/h34_screen
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
MIN_DIST = 2.4
KFRAC = 0.035
ARMS = ("C", "A")
H28_CELLS = ROOT / "evidence" / "h28_holdout" / "cells.jsonl"
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) via gems25.experiment.Cell.evaluate"


def h28_reference() -> dict:
    ref = {}
    for line in H28_CELLS.read_text().splitlines():
        row = json.loads(line)
        if row["value"] == "score" and row["min_dist"] == MIN_DIST and row["kfrac"] == KFRAC:
            ref[(row["fold"], row["draw"])] = row["dti"]
    return ref


def emit(cell: Cell, p: np.ndarray) -> np.ndarray:
    k = int(round(KFRAC * cell.dom_c.sum()))
    s_crop, top = cell.candidates(p, k)
    return score_ordered_dots(s_crop, top, MIN_DIST)


def feature_aucs(cell: Cell, sidecar: np.ndarray) -> dict[str, float]:
    out = {}
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    for j, name in enumerate(H34_NAMES):
        v = np.asarray(sidecar[j, cell.q], dtype=np.float64)[idx]
        out[name] = float(roc_auc_score(y, np.nan_to_num(v, nan=0.0))) if np.unique(v).size > 1 else 0.5
    return out


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
        hypothesis="H34-1 RESMAG-FLEX (depth-sliced RTP residual ridges + conductive-base flexure ridge as HGB columns)",
        preregistration="knowledge/18_preregistered_h34_resmag_flex_2026-10-25.md",
        draws=a.draws, folds=list(FOLD_IDS), arms=list(ARMS), min_dist=MIN_DIST, kfrac=KFRAC,
        model={"base": BASE, "extras": EXTRAS, "h34_columns": H34_NAMES, "fit_seed": "draw"},
        evaluator=EVALUATOR, leakage_auc_cap=0.90,
        gate={"mean_gain_gt": 0.001, "folds_positive_min": 3, "worst_fold_min": -0.010},
        reference="evidence/h28_holdout/cells.jsonl (score, 2.4, 0.035) — diagnostic only; gate is paired vs same-run C",
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")  # frozen before any fit

    ref = h28_reference()
    work = work_dir()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    t_side = time.time()
    sidecar = load_h34_sidecar(work, ctx.fi)
    print(f"H34 sidecar {sidecar.shape} ready in {time.time() - t_side:.0f}s", flush=True)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True)
                canary = feature_aucs(cell, sidecar)
                # control: exactly the shared-harness path
                p_c, timing_c = cell.fit_predict(cols, seed=draw)
                # candidate: same rows/order plus the 3 H34 columns appended last
                t0 = time.time()
                Xtr_a = np.hstack([cell.Xtr[:, cols], np.asarray(sidecar[:, cell.train_idx]).T])
                Xq_a = np.hstack([cell.Xq[:, cols], np.asarray(sidecar[:, cell.q]).T])
                model = HistGradientBoostingClassifier(random_state=draw, **HGB_PARAMS).fit(Xtr_a, cell.y)
                t_fit_a = time.time() - t0
                t0 = time.time()
                p_a = model.predict_proba(np.ascontiguousarray(Xq_a))[:, 1].astype(np.float32)
                timing_a = dict(fit_s=t_fit_a, predict_s=time.time() - t0)
                del Xtr_a, Xq_a, model
                for arm, p, timing in (("C", p_c, timing_c), ("A", p_a, timing_a)):
                    t0 = time.time()
                    ev = cell.evaluate(emit(cell, p))
                    row = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                               min_dist=MIN_DIST, kfrac=KFRAC, auc=cell.auc(p),
                               emit_s=round(time.time() - t0, 2),
                               feature_auc_canary=canary, **ev, **timing)
                    if arm == "C":
                        row["h28_reference_dti"] = ref.get((fold, draw))
                        row["reproduces_h28"] = (ref.get((fold, draw)) is not None
                                                 and abs(ev["dti"] - ref[(fold, draw)]) <= 1e-6)
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {arm}: DTI={ev['dti']:.6f} "
                          f"emitted={ev['emitted']} auc={row['auc']:.4f} "
                          f"canary_max={max(canary.values()):.3f}", flush=True)
                del cell, p_c, p_a
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
