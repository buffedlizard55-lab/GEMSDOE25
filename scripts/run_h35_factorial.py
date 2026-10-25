#!/usr/bin/env python3
"""H35 — 2x2 factorial RESMAG-FLEX (R) x directed tip (T) on the hide-and-recover holdout.

Pre-registered in knowledge/19 (committed before any fit). Four paired arms share one
`Cell(extras=True, h27=True)` per (fold, draw); emission sapd2.4 / kfrac 0.035 for all:
  C = BDE+7 · R = C+3 H34 cols · T = C+H27_tip · B = C+H27_tip+3 H34 cols (PRIMARY)

    .venv/bin/python scripts/run_h35_factorial.py --draws 10 11 --out evidence/h35_screen
    .venv/bin/python scripts/run_h35_factorial.py --draws 12 13 --out evidence/h35_confirm  # only if screen passes
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
MIN_DIST, KFRAC = 2.4, 0.035
ARMS = {"C": (False, False), "R": (True, False), "T": (False, True), "B": (True, True)}
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) via gems25.experiment.Cell.evaluate"


def emit(cell: Cell, p: np.ndarray) -> np.ndarray:
    k = int(round(KFRAC * cell.dom_c.sum()))
    s_crop, top = cell.candidates(p, k)
    return score_ordered_dots(s_crop, top, MIN_DIST)


def fit_arm(cell: Cell, base_cols, tip_col, sidecar, use_r: bool, use_t: bool, seed: int):
    cols = list(base_cols) + ([tip_col] if use_t else [])
    Xtr = cell.Xtr[:, cols]
    Xq = cell.Xq[:, cols]
    if use_r:
        Xtr = np.hstack([Xtr, np.asarray(sidecar[:, cell.train_idx]).T])
        Xq = np.hstack([Xq, np.asarray(sidecar[:, cell.q]).T])
    t0 = time.time()
    model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    t0 = time.time()
    p = model.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=t_fit, predict_s=time.time() - t0)


def feature_aucs(cell: Cell, sidecar, tip_col) -> dict[str, float]:
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    out = {}
    for j, name in enumerate(H34_NAMES):
        v = np.asarray(sidecar[j, cell.q], dtype=np.float64)[idx]
        out[name] = float(roc_auc_score(y, np.nan_to_num(v, nan=0.0))) if np.unique(v).size > 1 else 0.5
    v = np.asarray(cell.Xq[:, tip_col], dtype=np.float64)[idx]
    out["H27_tip"] = float(roc_auc_score(y, np.nan_to_num(v, nan=0.0))) if np.unique(v).size > 1 else 0.5
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cells_path, design_path = out / "cells.jsonl", out / "design.json"
    if cells_path.exists() or design_path.exists():
        raise SystemExit(f"refusing to overwrite {out}; choose a fresh --out")
    design = dict(hypothesis="H35 2x2 factorial: R (H34 RESMAG-FLEX) x T (H27_tip); primary arm B = R+T",
                  preregistration="knowledge/19_preregistered_h35_resmag_x_tip_factorial_2026-10-25.md",
                  draws=a.draws, folds=list(FOLD_IDS),
                  arms={k: {"use_R": v[0], "use_T": v[1]} for k, v in ARMS.items()},
                  min_dist=MIN_DIST, kfrac=KFRAC,
                  model={"base": BASE, "extras": EXTRAS, "h34_columns": H34_NAMES, "tip_column": "H27_tip",
                         "fit_seed": "draw"},
                  evaluator=EVALUATOR, leakage_auc_cap=0.90,
                  gate={"arm": "B vs C", "mean_gain_gt": 0.001, "folds_positive_min": 3,
                        "worst_fold_min": -0.010, "mean_hug_increase_max": 0.10})
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    work = work_dir()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    sidecar = load_h34_sidecar(work, ctx.fi)
    base_cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    tip_col = ctx.col["H27_tip"]
    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = feature_aucs(cell, sidecar, tip_col)
                for arm, (use_r, use_t) in ARMS.items():
                    p, timing = fit_arm(cell, base_cols, tip_col, sidecar, use_r, use_t, seed=draw)
                    t0 = time.time()
                    ev = cell.evaluate(emit(cell, p))
                    row = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                               use_R=use_r, use_T=use_t, min_dist=MIN_DIST, kfrac=KFRAC,
                               auc=cell.auc(p), emit_s=round(time.time() - t0, 2),
                               feature_auc_canary=canary, **ev, **timing)
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {arm}: DTI={ev['dti']:.6f} "
                          f"emitted={ev['emitted']} hug={ev['hug']:.3f} auc={row['auc']:.4f} "
                          f"canary_max={max(canary.values()):.3f}", flush=True)
                    del p
                del cell
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
