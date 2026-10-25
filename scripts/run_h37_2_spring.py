#!/usr/bin/env python3
"""H37-2 SPR vs same-run H35 arm-B control on the hide-and-recover holdout.

Pre-registered in knowledge/23 (amendment disclosed there). Two paired arms share
one `Cell(extras=True, h27=True)` per (fold, draw); emission sapd2.4 / kfrac 0.035:
  C37  = BDE+7 + H27_tip + 3 H34 cols          (H35 arm B, recomputed this run)
  A37S = C37 + 2 SPR cols (`gems25.h37`)       (candidate)

    .venv/bin/python scripts/run_h37_2_spring.py --draws 18 19 --out evidence/h37_2_screen
    .venv/bin/python scripts/run_h37_2_spring.py --draws 20 21 --out evidence/h37_2_confirm  # only if screen passes
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
from gems25.h37 import SPR_NAMES, load_spr_sidecar  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
MIN_DIST, KFRAC = 2.4, 0.035
ARMS = {"C37": False, "A37S": True}
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) via gems25.experiment.Cell.evaluate"


def emit(cell: Cell, p: np.ndarray) -> np.ndarray:
    k = int(round(KFRAC * cell.dom_c.sum()))
    s_crop, top = cell.candidates(p, k)
    return score_ordered_dots(s_crop, top, MIN_DIST)


def fit_arm(cell: Cell, cols, r_sidecar, spr_sidecar, use_spr: bool, seed: int):
    Xtr = np.hstack([cell.Xtr[:, cols], np.asarray(r_sidecar[:, cell.train_idx]).T])
    Xq = np.hstack([cell.Xq[:, cols], np.asarray(r_sidecar[:, cell.q]).T])
    if use_spr:
        Xtr = np.hstack([Xtr, np.asarray(spr_sidecar[:, cell.train_idx]).T])
        Xq = np.hstack([Xq, np.asarray(spr_sidecar[:, cell.q]).T])
    t0 = time.time()
    model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    del Xtr
    t0 = time.time()
    p = model.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=t_fit, predict_s=time.time() - t0, n_cols=int(Xq.shape[1]))


def feature_aucs(cell: Cell, r_sidecar, spr_sidecar, tip_col) -> dict[str, float]:
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])

    def auc(vec) -> float:
        v = np.asarray(vec, dtype=np.float64)
        return float(roc_auc_score(y, np.nan_to_num(v, nan=0.0))) if np.unique(v).size > 1 else 0.5

    out = {}
    for j, name in enumerate(SPR_NAMES):
        out[name] = auc(np.asarray(spr_sidecar[j, cell.q])[idx])
    for j, name in enumerate(H34_NAMES):
        out[name] = auc(np.asarray(r_sidecar[j, cell.q])[idx])
    out["H27_tip"] = auc(cell.Xq[:, tip_col][idx])
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
    design = dict(hypothesis="H37-2 SPR spring-line alignment ridge: A37S = H35 arm B + 2 SPR columns vs C37 = H35 arm B recomputed same-run",
                  preregistration="knowledge/23_preregistered_h37_2_spring_line_2026-10-25.md",
                  draws=a.draws, folds=list(FOLD_IDS),
                  arms={k: {"use_SPR": v} for k, v in ARMS.items()},
                  min_dist=MIN_DIST, kfrac=KFRAC,
                  model={"base": BASE, "extras": EXTRAS, "tip_column": "H27_tip",
                         "h34_columns": H34_NAMES, "spr_columns": SPR_NAMES, "fit_seed": "draw"},
                  evaluator=EVALUATOR, leakage_auc_cap=0.90,
                  gate={"arm": "A37S vs C37", "mean_gain_gt": 0.001, "folds_positive_min": 3,
                        "worst_fold_min": -0.010, "mean_hug_increase_max": 0.10})
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    work = work_dir()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    r_sidecar = load_h34_sidecar(work, ctx.fi)
    spr_sidecar = load_spr_sidecar(work, ctx.fi)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    tip_col = ctx.col["H27_tip"]
    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = feature_aucs(cell, r_sidecar, spr_sidecar, tip_col)
                spr_canary_max = max(max(canary[n], 1.0 - canary[n]) for n in SPR_NAMES)
                for arm, use_spr in ARMS.items():
                    p, timing = fit_arm(cell, cols, r_sidecar, spr_sidecar, use_spr, seed=draw)
                    t0 = time.time()
                    ev = cell.evaluate(emit(cell, p))
                    row = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                               use_SPR=use_spr, min_dist=MIN_DIST, kfrac=KFRAC,
                               auc=cell.auc(p), emit_s=round(time.time() - t0, 2),
                               feature_auc_canary=canary, **ev, **timing)
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {arm}: DTI={ev['dti']:.6f} "
                          f"emitted={ev['emitted']} hug={ev['hug']:.3f} auc={row['auc']:.4f} "
                          f"spr_canary_max={spr_canary_max:.3f}", flush=True)
                    del p
                del cell
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
