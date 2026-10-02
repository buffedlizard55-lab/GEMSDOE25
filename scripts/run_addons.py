#!/usr/bin/env python3
"""Pre-registered add-on hypothesis tests and emission experiment (knowledge/05_preregistered_addons_*)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.experiment import BUDGET, Cell, load_context  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import dot_thin, score_ordered_dots  # noqa: E402

ARMS = {
    "+X1": ["X1_K", "X1_ThK", "X1_UK"],
    "+X2": ["X2_compat", "X2_compat_coh"],
    "+X3": ["X3_gm", "X3_gd"],
    "+ALL": ["X1_K", "X1_ThK", "X1_UK", "X2_compat", "X2_compat_coh", "X3_gm", "X3_gd"],
}
K_GRID = [0.005, 0.0075, 0.01, 0.015, BUDGET]


def trunc_by_score(mask: np.ndarray, score: np.ndarray, n: int) -> np.ndarray:
    ids = np.flatnonzero(mask.ravel())
    if ids.size <= n:
        return mask
    keep = ids[np.lexsort((ids, -score.ravel()[ids]))[:n]]
    out = np.zeros_like(mask)
    out.ravel()[keep] = True
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None, help="override base family letters (default: best design row)")
    ap.add_argument("--out", default=str(ROOT / "evidence" / "addons"))
    ap.add_argument("--draws", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--extra-configs", nargs="*", default=[], help="extra family-letter combinations to fit (confirmation stage)")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = args.base or json.loads((ROOT / "evidence" / "factorial" / "results.json").read_text())["best_design_row"]["families"]
    ctx = load_context(work_dir())
    base_cols = ctx.columns(base)
    jl = out / "cells.jsonl"
    jl.write_text("")
    t_all = time.time()
    with jl.open("a") as sink:
        for fold in range(4):
            for seed in args.draws:
                cell = Cell(ctx, fold, seed, extras=True)
                p0, tm = cell.fit_predict(base_cols, seed=seed)
                s_crop, top = cell.candidates(p0)
                rows = []
                em, _ = cell.emit(p0)
                rows.append(dict(arm="BASE", **cell.evaluate(em), auc=cell.auc(p0), **tm))
                for arm, extra in ARMS.items():
                    if arm in ("+X2", "+ALL") and "E" not in base:
                        continue
                    p, tm2 = cell.fit_predict(base_cols + ctx.named(extra), seed=seed)
                    e, _ = cell.emit(p)
                    rows.append(dict(arm=arm, **cell.evaluate(e), auc=cell.auc(p), **tm2))
                for letters in args.extra_configs:
                    p, tm3 = cell.fit_predict(ctx.columns(letters), seed=seed)
                    e, _ = cell.emit(p)
                    rows.append(dict(arm=f"CFG_{letters}", **cell.evaluate(e), auc=cell.auc(p), **tm3))
                # EM-0: equal pixel count, score-blind dot_thin vs score-ordered Poisson disk
                dt = dot_thin(top, 1.5)
                sa = score_ordered_dots(s_crop, top, 1.5)
                n_eq = int(min(dt.sum(), sa.sum()))
                rows.append(dict(arm="EM0_dot_thin_eq", n_eq=n_eq, **cell.evaluate(trunc_by_score(dt, s_crop, n_eq))))
                rows.append(dict(arm="EM0_sapd_eq", n_eq=n_eq, **cell.evaluate(trunc_by_score(sa, s_crop, n_eq))))
                rows.append(dict(arm="EM0_dot_thin_raw", **cell.evaluate(dt)))
                rows.append(dict(arm="EM0_sapd_raw", **cell.evaluate(sa)))
                # EM-K: budget sweep
                for kf in K_GRID:
                    k = int(round(kf * cell.dom_c.sum()))
                    s_k, top_k = cell.candidates(p0, k)
                    for var, e in (("solid", top_k), ("dot1.5", dot_thin(top_k, 1.5)),
                                   ("sapd1.5", score_ordered_dots(s_k, top_k, 1.5)), ("sapd2.4", score_ordered_dots(s_k, top_k, 2.4))):
                        rows.append(dict(arm=f"EMK_{var}_{kf:.4f}", kfrac=kf, variant=var, **cell.evaluate(e)))
                for r in rows:
                    sink.write(json.dumps(dict(fold=fold, draw=seed, base=base, **r)) + "\n")
                sink.flush()
                print(f"[fold {fold} draw {seed}] " + " | ".join(f"{r['arm']}={r['dti']:.4f}" for r in rows[:5]) + f"  [{time.time() - t_all:.0f}s]", flush=True)
                del cell
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
