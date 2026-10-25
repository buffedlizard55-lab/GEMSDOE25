#!/usr/bin/env python3
"""H37-SEISALIGN — seismicity-alignment columns added to the H35 arm-B detector, holdout only.

Pre-registered in knowledge/22 (committed before any fit). Arms share one
`Cell(extras=True, h27=True)` per (fold, draw); emission sapd2.4 / kfrac 0.035 for all:
  BEST = BDE+7 + H27_tip + 3 H34 columns   (same-run comparator, = H35 arm B)
  SEIS = BEST + 3 H37 alignment columns    (PRIMARY)

    .venv/bin/python scripts/run_h37_seis.py --draws 40 41 --out evidence/h37_screen
    .venv/bin/python scripts/run_h37_seis.py --draws 42 43 --out evidence/h37_confirm  # only if screen passes
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
from gems25.h37 import H37_NAMES, load_h37_sidecar  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
MIN_DIST, KFRAC = 2.4, 0.035
# arm -> (use_tip, use_h34, use_h37)
ARMS = {"BEST": (True, True, False), "SEIS": (True, True, True)}
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) via gems25.experiment.Cell.evaluate"


def emit(cell: Cell, p: np.ndarray) -> np.ndarray:
    k = int(round(KFRAC * cell.dom_c.sum()))
    s_crop, top = cell.candidates(p, k)
    return score_ordered_dots(s_crop, top, MIN_DIST)


def fit_arm(cell: Cell, base_cols, tip_col, h34, h37, use_tip: bool, use_r: bool, use_z: bool, seed: int):
    cols = list(base_cols) + ([tip_col] if use_tip else [])
    Xtr = cell.Xtr[:, cols]
    Xq = cell.Xq[:, cols]
    extra_tr, extra_q = [], []
    if use_r:
        extra_tr.append(np.asarray(h34[:, cell.train_idx]).T)
        extra_q.append(np.asarray(h34[:, cell.q]).T)
    if use_z:
        extra_tr.append(np.asarray(h37[:, cell.train_idx]).T)
        extra_q.append(np.asarray(h37[:, cell.q]).T)
    if extra_tr:
        Xtr = np.hstack([Xtr] + extra_tr)
        Xq = np.hstack([Xq] + extra_q)
    t0 = time.time()
    model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    t0 = time.time()
    p = model.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=t_fit, predict_s=time.time() - t0)


def feature_aucs(cell: Cell, h37) -> dict[str, float]:
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    out = {}
    for j, name in enumerate(H37_NAMES):
        v = np.asarray(h37[j, cell.q], dtype=np.float64)[idx]
        out[name] = float(roc_auc_score(y, np.nan_to_num(v, nan=0.0))) if np.unique(v).size > 1 else 0.5
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--arms", nargs="+", default=["BEST", "SEIS"], choices=list(ARMS))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cells_path, design_path = out / "cells.jsonl", out / "design.json"
    if cells_path.exists() or design_path.exists():
        raise SystemExit(f"refusing to overwrite {out}; choose a fresh --out")
    design = dict(hypothesis="H37-SEISALIGN: seismicity structure-tensor alignment columns on H35 arm-B detector",
                  preregistration="knowledge/22_preregistered_h37_seisalign_2026-10-25.md",
                  draws=a.draws, folds=list(FOLD_IDS),
                  arms={k: {"use_tip": v[0], "use_h34": v[1], "use_h37": v[2]} for k, v in ARMS.items() if k in a.arms},
                  min_dist=MIN_DIST, kfrac=KFRAC,
                  model={"base": BASE, "extras": EXTRAS, "h34_columns": H34_NAMES, "h37_columns": H37_NAMES,
                         "tip_column": "H27_tip", "fit_seed": "draw"},
                  evaluator=EVALUATOR, leakage_auc_cap=0.90,
                  gate={"arm": "SEIS vs BEST", "mean_gain_gt": 0.001, "folds_positive_min": 3, "worst_fold_min": -0.010})
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    work = work_dir()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    h34 = load_h34_sidecar(work, ctx.fi)
    h37 = load_h37_sidecar(work, ctx.fi)
    base_cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    tip_col = ctx.col["H27_tip"]
    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = feature_aucs(cell, h37)
                for arm in a.arms:
                    use_tip, use_r, use_z = ARMS[arm]
                    p, timing = fit_arm(cell, base_cols, tip_col, h34, h37, use_tip, use_r, use_z, seed=draw)
                    t0 = time.time()
                    ev = cell.evaluate(emit(cell, p))
                    row = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                               use_tip=use_tip, use_h34=use_r, use_h37=use_z,
                               min_dist=MIN_DIST, kfrac=KFRAC,
                               auc=cell.auc(p), emit_s=round(time.time() - t0, 2),
                               feature_auc_canary=canary, **ev, **timing)
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {arm}: DTI={ev['dti']:.6f} "
                          f"emitted={ev['emitted']} hug={ev['hug']:.3f} auc={row['auc']:.4f} "
                          f"canary={ {k: round(v,3) for k,v in canary.items()} }", flush=True)
                    del p
                del cell
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
