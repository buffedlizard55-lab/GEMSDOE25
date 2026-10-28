#!/usr/bin/env python3
"""Holdout (hide-and-recover) evaluation of a binary emission array.

Reports per-draw DTI, pooled DTI (sum TP/FP/FN across draws, then DTI) and a
bootstrap 95% CI over draws. All numbers are HOLDOUT-DTI (catalogue-gap proxy,
not organizer-confirmed).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.holdout import Holdout  # noqa: E402

DRAWS = [(f, s) for s in (140, 141) for f in range(4)]  # 8 spatially blocked draws
ALPHA, BETA, EPS = 0.2, 0.8, 1e-7


def pooled(rows):
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    return tp / (tp + ALPHA * fp + BETA * fn + EPS)


def bootstrap_ci(rows, nrep: int = 10000, seed: int = 7):
    rng = np.random.default_rng(seed)
    m = len(rows)
    out = []
    for _ in range(nrep):
        idx = rng.integers(0, m, m)
        sub = [rows[i] for i in idx]
        out.append(pooled(sub))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def eval_array(ho: Holdout, arr: np.ndarray, tag: str) -> dict:
    rows = []
    for fold, seed in DRAWS:
        d = ho.draw(fold, seed)
        s = ho.score(d, arr)
        rows.append(dict(fold=fold, seed=seed,
                         tp=float(s["tp"]), fp=float(s["fp"]), fn=float(s["fn"]),
                         n_truth=int(s["n_truth"]), dti=float(s["dti"]),
                         coverage=float(s["coverage"])))
    dti = pooled(rows)
    lo, hi = bootstrap_ci(rows)
    return dict(tag=tag, draws=rows, pooled_dti=float(dti), ci95=[lo, hi],
                n_truth_total=int(sum(r["n_truth"] for r in rows)))


def main() -> int:
    with rasterio.open(ROOT / "data" / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    labels = rasterio.open(ROOT / "data" / "labels.tif").read(1)
    ho = Holdout(foot, labels, hide_frac=0.20)

    out = {}
    for tif in sys.argv[1:]:
        p = Path(tif)
        arr = rasterio.open(p).read(1)
        res = eval_array(ho, arr, p.name)
        out[p.name] = res
        print(json.dumps(res, indent=1, default=float))
    Path("/tmp/holdout_results.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
