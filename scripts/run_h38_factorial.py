#!/usr/bin/env python3
"""H38 2x2 factorial (OSPC geology x 300 m submodular skeleton coverage) vs same-run H35 arm-B control.

Pre-registered in knowledge/25_preregistered_h38_ospc_submod_factorial_2026-10-25.md (committed pre-fit).
Four paired arms share one `Cell(extras=True, h27=True)` per (fold, draw):
  G0_S0 = H35 arm B (BDE+7 + H27_tip + 3 H34 cols, 55 cols), incumbent sapd2.4 / kfrac 0.035 -> M0 dots
  G0_S1 = exact G0 probability surface + 300 m submodular skeleton allocation matched to M0 dots
  G1_S0 = G0 + 4 H38-OSPC columns (59 cols), incumbent sapd2.4 / kfrac 0.035 -> M1 dots
  G1_S1 = exact G1 probability surface + 300 m submodular skeleton allocation matched to M1 dots (PRIMARY)

Usage:
    GEMS_DATA_DIR=/tmp/gems25_data .venv/bin/python scripts/run_h38_factorial.py --draws 24 25 --out evidence/h38_screen
    GEMS_DATA_DIR=/tmp/gems25_data .venv/bin/python scripts/run_h38_factorial.py --draws 26 27 --out evidence/h38_confirm
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
from gems25.h31 import EVALUATOR_VERSION  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h38_ospc import (  # noqa: E402
    DEFAULT_MIN_DIST_FLOOR_PX,
    DEFAULT_POOL_KFRAC,
    H38_NAMES,
    build_h38_ospc_columns,
    submodular_skeleton_dots,
)
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
MIN_DIST, KFRAC = 2.4, 0.035
EVALUATOR = f"gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) [{EVALUATOR_VERSION}]"


def score_crop(cell: Cell, p: np.ndarray) -> np.ndarray:
    g = cell._grid
    g[:] = 0.0
    g.ravel()[cell.ctx.fi[cell.q]] = np.nan_to_num(p, nan=0.0).astype(np.float32)
    return g[cell.sl].copy()


def emit_s0(cell: Cell, p: np.ndarray) -> np.ndarray:
    k = int(round(KFRAC * cell.dom_c.sum()))
    s_crop, top = cell.candidates(p, k)
    return score_ordered_dots(s_crop, top, MIN_DIST)


def emit_s1(cell: Cell, p: np.ndarray, *, n_dots: int, pi_true: float, r_train: float) -> np.ndarray:
    s_crop = score_crop(cell, p)
    return submodular_skeleton_dots(
        s_crop,
        cell.dom_c,
        cell.known_c,
        n_dots=n_dots,
        pi_true=pi_true,
        r_train=r_train,
        pool_kfrac=DEFAULT_POOL_KFRAC,
        min_dist_floor=DEFAULT_MIN_DIST_FLOOR_PX,
    )


def fit_surface(cell: Cell, cols: list[int], r_sidecar: np.ndarray, h38_sidecar: np.ndarray, use_ospc: bool, seed: int):
    Xtr = np.hstack([cell.Xtr[:, cols], np.asarray(r_sidecar[:, cell.train_idx]).T])
    Xq = np.hstack([cell.Xq[:, cols], np.asarray(r_sidecar[:, cell.q]).T])
    if use_ospc:
        Xtr = np.hstack([Xtr, np.asarray(h38_sidecar[:, cell.train_idx]).T])
        Xq = np.hstack([Xq, np.asarray(h38_sidecar[:, cell.q]).T])
    t0 = time.time()
    model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    del Xtr
    t0 = time.time()
    p = model.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=round(t_fit, 3), predict_s=round(time.time() - t0, 3), n_cols=int(Xq.shape[1]))


def feature_aucs(cell: Cell, r_sidecar: np.ndarray, h38_sidecar: np.ndarray, tip_col: int) -> dict[str, float]:
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])

    def auc(vec: np.ndarray) -> float:
        v = np.asarray(vec, dtype=np.float64)
        return float(roc_auc_score(y, np.nan_to_num(v, nan=0.0))) if np.unique(v).size > 1 else 0.5

    out: dict[str, float] = {}
    for j, name in enumerate(H38_NAMES):
        out[name] = auc(np.asarray(h38_sidecar[j, cell.q])[idx])
    for j, name in enumerate(H34_NAMES):
        out[name] = auc(np.asarray(r_sidecar[j, cell.q])[idx])
    out["H27_tip"] = auc(cell.Xq[:, tip_col][idx])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cells_path, design_path = out / "cells.jsonl", out / "design.json"
    if cells_path.exists() or design_path.exists():
        raise SystemExit(f"refusing to overwrite {out}; choose a fresh --out")

    design = dict(
        hypothesis="H38 2x2 factorial: OSPC static geology (4 cols) x 300 m submodular multi-scale skeleton allocation vs same-run H35 arm B (G0_S0)",
        preregistration="knowledge/25_preregistered_h38_ospc_submod_factorial_2026-10-25.md",
        draws=list(args.draws),
        folds=list(FOLD_IDS),
        arms={
            "G0_S0": {"use_OSPC": False, "use_SUBMOD": False, "role": "same-run H35 arm B control"},
            "G0_S1": {"use_OSPC": False, "use_SUBMOD": True, "role": "Factor S main arm"},
            "G1_S0": {"use_OSPC": True, "use_SUBMOD": False, "role": "Factor G main arm"},
            "G1_S1": {"use_OSPC": True, "use_SUBMOD": True, "role": "primary H38 joint candidate"},
        },
        s0_params={"min_dist": MIN_DIST, "kfrac": KFRAC},
        s1_params={
            "pool_kfrac": DEFAULT_POOL_KFRAC,
            "min_dist_floor": DEFAULT_MIN_DIST_FLOOR_PX,
            "skeleton": "ridge_nms(1.0) | ridge_nms(2.0)",
            "calibration": "King-Zeng case-control prior-odds from visible train fold",
            "budget": "exact cell-matched dot count M = M_S0",
        },
        model={
            "base": BASE,
            "extras": EXTRAS,
            "tip_column": "H27_tip",
            "h34_columns": list(H34_NAMES),
            "h38_columns": list(H38_NAMES),
            "fit_seed": "draw",
        },
        evaluator=EVALUATOR,
        leakage_auc_cap=0.90,
        gate={
            "primary_contrast": "G1_S1 vs G0_S0",
            "mean_gain_gt": 0.0010,
            "folds_positive_min": 3,
            "worst_fold_min": -0.0100,
            "mean_hug_increase_max": 0.10,
        },
    )
    design_path.write_text(json.dumps(design, indent=2) + "\n")

    t_all = time.time()
    work = work_dir()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")

    print(f"[{time.time() - t_all:.1f}s] loading/building H34 and H38 sidecars...", flush=True)
    r_sidecar = load_h34_sidecar(work, ctx.fi)
    h38_sidecar, _ = build_h38_ospc_columns(work, data_dir() / "external")
    cols = ctx.columns(BASE) + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    tip_col = ctx.col["H27_tip"]
    print(f"[{time.time() - t_all:.1f}s] sidecars ready (H38 shape={h38_sidecar.shape})", flush=True)

    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in args.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                pi_true = float((cell.draw.visible & cell.draw.train_region).sum()) / float(
                    max(int(cell.draw.train_region.sum()), 1)
                )
                r_train = float(cell.y.mean())
                canary = feature_aucs(cell, r_sidecar, h38_sidecar, tip_col)
                h38_canary_max = max(max(canary[n], 1.0 - canary[n]) for n in H38_NAMES)

                for g_tag, use_ospc in (("G0", False), ("G1", True)):
                    p, timing = fit_surface(cell, cols, r_sidecar, h38_sidecar, use_ospc, seed=draw)
                    surf_auc = cell.auc(p)

                    # S0: incumbent ridge_nms(1.0) + sapd2.4
                    t0 = time.time()
                    dots_s0 = emit_s0(cell, p)
                    t_s0 = round(time.time() - t0, 3)
                    ev_s0 = cell.evaluate(dots_s0)

                    # S1: exact 300 m submodular multi-scale skeleton allocation at cell-matched M
                    t0 = time.time()
                    dots_s1 = emit_s1(cell, p, n_dots=ev_s0["emitted"], pi_true=pi_true, r_train=r_train)
                    t_s1 = round(time.time() - t0, 3)
                    ev_s1 = cell.evaluate(dots_s1)

                    for s_tag, use_sub, t_emit, ev in (
                        ("S0", False, t_s0, ev_s0),
                        ("S1", True, t_s1, ev_s1),
                    ):
                        arm = f"{g_tag}_{s_tag}"
                        row = dict(
                            fold=fold,
                            fold_name=FOLDS[fold],
                            draw=draw,
                            arm=arm,
                            use_OSPC=use_ospc,
                            use_SUBMOD=use_sub,
                            pi_true=round(pi_true, 6),
                            r_train=round(r_train, 6),
                            auc=surf_auc,
                            emit_s=t_emit,
                            h38_canary_max=h38_canary_max,
                            feature_auc_canary=canary,
                            **ev,
                            **timing,
                        )
                        sink.write(json.dumps(row) + "\n")
                        sink.flush()
                        print(
                            f"[{time.time() - t_all:.0f}s] fold {fold} ({FOLDS[fold]}) draw {draw} {arm}: "
                            f"DTI={ev['dti']:.6f} tp={ev['tp']:.1f} emitted={ev['emitted']} "
                            f"hug={ev['hug']:.3f} auc={surf_auc:.4f} canary_max={h38_canary_max:.3f} emit_s={t_emit:.2f}s",
                            flush=True,
                        )
                    del p, dots_s0, dots_s1
                del cell
    print(f"DONE {cells_path} in {time.time() - t_all:.1f}s", flush=True)


if __name__ == "__main__":
    main()
