#!/usr/bin/env python3
"""Frozen OLIC screen/confirmation runner (knowledge/29). Never emits a full-catalogue raster."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.h34 import load_h34_sidecar  # noqa: E402
from gems25.olic import OLIC_NAMES, load_olic_sidecar  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

KFRAC, MIN_DIST, LEAKAGE_CAP = 0.035, 2.4, 0.90


def fit_predict(cell, columns, h34, olic, seed):
    ext_tr = [np.asarray(h34[:, cell.train_idx], np.float32).T]
    ext_q = [np.asarray(h34[:, cell.q], np.float32).T]
    if olic is not None:
        ext_tr.append(np.asarray(olic[:, cell.train_idx], np.float32).T)
        ext_q.append(np.asarray(olic[:, cell.q], np.float32).T)
    xtr = np.hstack([cell.Xtr[:, columns], *ext_tr])
    xq = np.hstack([cell.Xq[:, columns], *ext_q])
    m = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(xtr, cell.y)
    return m.predict_proba(np.ascontiguousarray(xq))[:, 1].astype(np.float32)


def emit(cell, p):
    k = int(round(KFRAC * cell.dom_c.sum()))
    score, top = cell.candidates(p, k)
    dots = score_ordered_dots(score, top, MIN_DIST)
    return dots, {"top_k": int(np.count_nonzero(top)), "emitted": int(dots.sum())}


def canaries(cell, olic):
    idx = np.concatenate((cell.auc_pos, cell.auc_neg))
    y = np.concatenate((np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)))
    out = {}
    for i, name in enumerate(OLIC_NAMES):
        vals = np.nan_to_num(np.asarray(olic[i, cell.q], np.float64)[idx], nan=0.0)
        raw = float(roc_auc_score(y, vals)) if np.unique(vals).size > 1 else 0.5
        out[name] = {"raw_auc": raw, "canary_auc": max(raw, 1.0 - raw)}
    return out


def pooled(rows):
    tp = sum(r["tp"] for r in rows); fp = sum(r["fp"] for r in rows); n = sum(r["n_truth"] for r in rows)
    return {"dti": float(tp / (tp + 0.2 * fp + 0.8 * (n - tp) + 1e-7)), "withheld_positives": int(n),
            "tp": float(tp), "fp": float(fp), "fn": float(n - tp)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stage", choices=["screen", "confirmation"], required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    design = {"experiment": f"OLIC line-continuity {a.stage}", "preregistration": "knowledge/29_preregistered_olic_line_continuity_2026-10-26.md",
              "draws": list(a.draws), "folds": list(range(4)), "evaluator": "gems25.holdout.v1.2-buffered-4quad-pooled-dti",
              "alpha": 0.2, "beta": 0.8, "kernel_radius_px": 3.0, "collar_px": 15,
              "candidate": "H35 plus 9 OLIC features", "control": "H35 (same-run recomputed)", "kfrac": KFRAC,
              "min_dist_px": MIN_DIST, "leakage_auc_cap": LEAKAGE_CAP}
    (out / "design.json").write_text(json.dumps(design, indent=2) + "\n")
    t0 = time.time()
    ctx = load_context(work_dir())
    h34 = load_h34_sidecar(work_dir(), ctx.fi)
    olic = load_olic_sidecar(work_dir(), ctx.static, ctx.static_names, ctx.foot, ctx.fi)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    rows = []
    for fold in range(4):
        for draw in a.draws:
            cell = Cell(ctx, fold, draw, extras=True, h27=True)
            leak = canaries(cell, olic)
            max_leak = max(v["canary_auc"] for v in leak.values())
            if max_leak > LEAKAGE_CAP:
                raise SystemExit(f"OLIC leakage canary failed fold={fold} draw={draw}: {leak}")
            pc = fit_predict(cell, cols, h34, None, draw)
            pp = fit_predict(cell, cols, h34, olic, draw)
            ec, dc = emit(cell, pc); ep, dp = emit(cell, pp)
            rc, rp = cell.evaluate(ec), cell.evaluate(ep)
            row = {"fold": fold, "fold_name": FOLDS[fold], "draw": draw, "withheld_positives": rc["n_truth"],
                   "control": rc, "candidate": rp, "paired_gain": rp["dti"] - rc["dti"],
                   "hug_delta": rp["hug"] - rc["hug"], "control_emission": dc, "candidate_emission": dp,
                   "feature_canaries": leak}
            rows.append(row)
            with (out / "cells.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(f"fold={FOLDS[fold]} draw={draw} control={rc['dti']:.6f} candidate={rp['dti']:.6f} gain={row['paired_gain']:+.6f} canary={max_leak:.4f}", flush=True)
            del cell, pc, pp, ec, ep
    fold_gains = [float(np.mean([r["paired_gain"] for r in rows if r["fold"] == i])) for i in range(4)]
    mean_gain = float(np.mean(fold_gains))
    ci_half = float(student_t.ppf(0.975, 3) * np.std(fold_gains, ddof=1) / np.sqrt(4)) if np.std(fold_gains, ddof=1) > 0 else 0.0
    gate = bool(mean_gain > 0.001 and sum(g > 0 for g in fold_gains) >= 3 and min(fold_gains) >= -0.01
                and float(np.mean([r["hug_delta"] for r in rows])) <= 0.10)
    if a.stage == "confirmation":
        gate = bool(gate and (mean_gain - ci_half) > 0)
    summary = {"stage": a.stage, "evaluator": design["evaluator"], "draws": list(a.draws), "cells": len(rows),
               "withheld_positives": sum(r["withheld_positives"] for r in rows),
               "control_pooled": pooled([r["control"] for r in rows]), "candidate_pooled": pooled([r["candidate"] for r in rows]),
               "paired_fold_mean_gain": mean_gain, "paired_fold_ci95": [mean_gain - ci_half, mean_gain + ci_half],
               "paired_gain_by_fold": fold_gains, "positive_folds": int(sum(g > 0 for g in fold_gains)),
               "mean_hug_delta": float(np.mean([r["hug_delta"] for r in rows])),
               "max_canary_auc": max(v["canary_auc"] for r in rows for v in r["feature_canaries"].values()),
               "gate_passed": gate, "full_catalogue_raster_emitted": False, "elapsed_seconds": round(time.time() - t0, 1)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
