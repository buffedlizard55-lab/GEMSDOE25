#!/usr/bin/env python3
"""Paired analysis of ``run_addons.py`` output with the pre-registered gate (knowledge/05_preregistered_addons_*)."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def fold_means(rows, arm, key="dti"):
    by = defaultdict(list)
    for r in rows:
        if r["arm"] == arm:
            by[r["fold"]].append(r[key])
    return np.array([np.mean(by[f]) for f in range(4)]) if len(by) == 4 else None


def gate(cand, base, hug_c, hug_b, min_gain=0.001, max_loss=0.01, hug_margin=0.10):
    d = cand - base
    return dict(mean_gain=float(d.mean()), folds_positive=int((d > 0).sum()), worst_fold=float(d.min()),
                hug_delta=float(hug_c - hug_b),
                passed=bool(d.mean() > min_gain and (d > 0).sum() >= 3 and d.min() >= -max_loss and (hug_c - hug_b) <= hug_margin),
                per_fold=[float(x) for x in d])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "evidence" / "addons"))
    a = ap.parse_args()
    d = Path(a.dir)
    rows = [json.loads(line) for line in (d / "cells.jsonl").read_text().splitlines()]
    base_letters = rows[0]["base"]
    arms = sorted({r["arm"] for r in rows})
    out = dict(base=base_letters, n_cells=len({(r["fold"], r["draw"]) for r in rows}), arms={})
    base = fold_means(rows, "BASE")
    hug_b = float(np.mean([r["hug"] for r in rows if r["arm"] == "BASE"]))
    out["BASE"] = dict(mean_dti=float(base.mean()), per_fold=[float(x) for x in base], hug=hug_b,
                       auc=float(np.mean([r["auc"] for r in rows if r["arm"] == "BASE"])))
    for arm in arms:
        if arm.startswith(("+", "CFG_")):
            c = fold_means(rows, arm)
            hug_c = float(np.mean([r["hug"] for r in rows if r["arm"] == arm]))
            out["arms"][arm] = dict(mean_dti=float(c.mean()), auc=float(np.mean([r["auc"] for r in rows if r["arm"] == arm])),
                                    hug=hug_c, gate_vs_base=gate(c, base, hug_c, hug_b))
    # EM-0: score-ordered vs score-blind dotting at equal N
    dt, sa = fold_means(rows, "EM0_dot_thin_eq"), fold_means(rows, "EM0_sapd_eq")
    n_eq = float(np.mean([r["n_eq"] for r in rows if r["arm"] == "EM0_sapd_eq"]))
    out["EM0_equal_N"] = dict(n_eq_mean=n_eq, dot_thin=float(dt.mean()), sapd=float(sa.mean()), gate_sapd_vs_dot_thin=gate(sa, dt, 0, 0),
                              raw=dict(dot_thin=float(fold_means(rows, "EM0_dot_thin_raw").mean()), sapd=float(fold_means(rows, "EM0_sapd_raw").mean()),
                                       dot_thin_px=float(np.mean([r["emitted"] for r in rows if r["arm"] == "EM0_dot_thin_raw"])),
                                       sapd_px=float(np.mean([r["emitted"] for r in rows if r["arm"] == "EM0_sapd_raw"]))))
    emk = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["arm"].startswith("EMK_"):
            emk[(r["variant"], r["kfrac"])]["dti"].append(r["dti"])
            emk[(r["variant"], r["kfrac"])]["px"].append(r["emitted"])
            emk[(r["variant"], r["kfrac"])]["cov"].append(r["coverage"])
    out["EMK"] = [dict(variant=v, kfrac=k, dti=float(np.mean(x["dti"])), emitted=float(np.mean(x["px"])), coverage=float(np.mean(x["cov"])))
                  for (v, k), x in sorted(emk.items(), key=lambda t: (t[0][0], t[0][1]))]
    best = max(out["EMK"], key=lambda r: r["dti"])
    out["EMK_best"] = best
    (d / "results.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("EMK",)}, indent=1)[:4000])
    print("EMK:")
    for r in out["EMK"]:
        print(f"  {r['variant']:8s} K={r['kfrac']:.4f} DTI={r['dti']:.4f} px={r['emitted']:.0f} cov={r['coverage']:.3f}")


if __name__ == "__main__":
    main()
