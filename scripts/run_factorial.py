#!/usr/bin/env python3
"""Execute the pre-registered 2^(5-1) fractional factorial (knowledge/04_preregistered_factorial_*.md).

Cell-major loop: for each (test quadrant, draw) build features / sample once, then run the 16 design rows and
the same-harness reference rows. Results are appended to ``evidence/factorial/cells.jsonl`` (resumable).
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
from gems25 import factorial as fx  # noqa: E402
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.holdout import FOLD_NAMES  # noqa: E402
from gems25.paths import work_dir  # noqa: E402

TOPO = ["L_step_max", "L_ex_max", "L_lapneg_max", "B_crest", "B_slope_grad"]
GEO = ["A_mag_hg_ridge", "A_grav_hg_ridge"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--folds", type=int, nargs="+", default=[0, 1, 2, 3])
    ap.add_argument("--out", default=str(ROOT / "evidence" / "factorial"))
    ap.add_argument("--order-seed", type=int, default=20261002)
    ap.add_argument("--limit-runs", type=int, default=0, help="debug: only the first N rows of the order")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    jl = out / "cells.jsonl"
    done = set()
    if jl.exists():
        for line in jl.read_text().splitlines():
            r = json.loads(line)
            done.add((r["row"], r["fold"], r["draw"]))
    ctx = load_context(work_dir())
    d = fx.design(5, {"E": "ABCD"})
    X, names = d["X"], d["names"]
    order = np.random.default_rng(args.order_seed).permutation(d["runs"])
    if args.limit_runs:
        order = order[: args.limit_runs]
    (out / "design.json").write_text(json.dumps(dict(
        names=names, X=X.tolist(), order=[int(o) for o in order], generators=d["generators"],
        alias=fx.alias_structure(5, d["generators"]),
    ), indent=1))
    t_all = time.time()
    with jl.open("a") as sink:
        for fold in args.folds:
            for seed in args.draws:
                cell = Cell(ctx, fold, seed)
                print(f"[cell fold={FOLD_NAMES[fold]} draw={seed}] prep {cell.prep_seconds:.0f}s  "
                      f"truth px={int(cell.truth_c.sum())} K={cell.K} train rows={cell.y.size} pos={int(cell.y.sum())}", flush=True)
                refs = {
                    "REF_topo": cell.unsupervised(TOPO),
                    "REF_geo": cell.unsupervised(GEO),
                    "REF_null": np.random.default_rng(99 + seed + 7 * fold).random(cell.q.size).astype(np.float32),
                }
                for ref, sc in refs.items():
                    if (ref, fold, seed) in done:
                        continue
                    em, top = cell.emit(sc)
                    row = dict(row=ref, fold=fold, draw=seed, auc=cell.auc(sc), **cell.evaluate(em))
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                for ri in order:
                    key = (int(ri), fold, seed)
                    if key in done:
                        continue
                    letters = "".join(n for n, v in zip(names, X[ri]) if v > 0)
                    p, tm = cell.fit_predict(ctx.columns(letters), seed=seed)
                    em, top = cell.emit(p)
                    row = dict(row=int(ri), fold=fold, draw=seed, families=letters, auc=cell.auc(p),
                               dti_undotted=cell.evaluate(top)["dti"], **cell.evaluate(em), **tm)
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"   run {ri:2d} [{letters:5s}] DTI={row['dti']:.4f} (undotted {row['dti_undotted']:.4f}) "
                          f"auc={row['auc']:.3f} hug={row['hug']:.2f} em={row['emitted']} "
                          f"fit={tm['fit_s']:.0f}s pred={tm['predict_s']:.0f}s  [{time.time() - t_all:.0f}s]", flush=True)
                del cell
    print("DONE", time.time() - t_all, flush=True)


if __name__ == "__main__":
    main()
