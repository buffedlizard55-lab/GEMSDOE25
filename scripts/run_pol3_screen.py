#!/usr/bin/env python3
"""Run the frozen POL3 holdout screen from knowledge/28 (no full-catalogue raster emission)."""
from __future__ import annotations

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
from gems25.paths import work_dir  # noqa: E402
from gems25.pol3 import POL3_NAMES, load_pol3_sidecar  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

DRAWS = (58, 59)
KFRAC = 0.035
MIN_DIST = 2.4
LEAKAGE_CAP = 0.90
OUT = ROOT / "evidence" / "pol3_screen_2026-10-26"


def fit_predict(cell: Cell, columns: list[int], h34: np.ndarray, pol3: np.ndarray | None, seed: int):
    xtr, xq = cell.Xtr[:, columns], cell.Xq[:, columns]
    ext = [np.asarray(h34[:, cell.train_idx], dtype=np.float32).T,
           np.asarray(h34[:, cell.q], dtype=np.float32).T]
    if pol3 is not None:
        ext[0] = np.hstack((ext[0], np.asarray(pol3[:, cell.train_idx], dtype=np.float32).T))
        ext[1] = np.hstack((ext[1], np.asarray(pol3[:, cell.q], dtype=np.float32).T))
    xtr = np.hstack((xtr, ext[0]))
    xq = np.hstack((xq, ext[1]))
    model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(xtr, cell.y)
    return model.predict_proba(np.ascontiguousarray(xq))[:, 1].astype(np.float32)


def emit(cell: Cell, p: np.ndarray) -> tuple[np.ndarray, dict]:
    k = int(round(KFRAC * cell.dom_c.sum()))
    score, top = cell.candidates(p, k)
    dots = score_ordered_dots(score, top, MIN_DIST)
    return dots, {"top_k": int(np.count_nonzero(top)), "emitted": int(dots.sum())}


def canaries(cell: Cell, pol3: np.ndarray) -> dict:
    idx = np.concatenate((cell.auc_pos, cell.auc_neg))
    y = np.concatenate((np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)))
    out = {}
    for i, name in enumerate(POL3_NAMES):
        vals = np.nan_to_num(np.asarray(pol3[i, cell.q], dtype=np.float64)[idx], nan=0.0)
        raw = float(roc_auc_score(y, vals)) if np.unique(vals).size > 1 else 0.5
        out[name] = {"raw_auc": raw, "canary_auc": max(raw, 1.0 - raw)}
    return out


def pooled(rows: list[dict]) -> dict:
    # Cell.evaluate exposes tp/fp/n_truth (not fn); exact identity is FN = n_truth - TP.
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    n = sum(r["n_truth"] for r in rows)
    fn = n - tp
    return {"dti": float(tp / (tp + 0.2 * fp + 0.8 * fn + 1e-7)), "withheld_positives": int(n),
            "tp": float(tp), "fp": float(fp), "fn": float(fn)}


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.mkdir(parents=True)
    design = {
        "experiment": "POL3 signed half-graben polarity screen",
        "preregistration": "knowledge/28_preregistered_pol3_signed_halfgraben_2026-10-26.md",
        "draws": list(DRAWS), "folds": list(range(4)), "evaluator": "gems25.holdout.v1.2-buffered-4quad-pooled-dti",
        "alpha": 0.2, "beta": 0.8, "kernel_radius_px": 3.0, "collar_px": 15,
        "candidate": "H35 plus four POL3 features", "control": "H35", "kfrac": KFRAC,
        "min_dist_px": MIN_DIST, "leakage_auc_cap": LEAKAGE_CAP,
        "gate": {"mean_gain_gt": 0.001, "folds_positive_min": 3, "worst_fold_min": -0.01,
                 "hug_delta_max": 0.10},
        "note": "Design written before fitting; this runner never emits a full-catalogue raster.",
    }
    (OUT / "design.json").write_text(json.dumps(design, indent=2) + "\n")
    t0 = time.time()
    ctx = load_context(work_dir())
    h34 = load_h34_sidecar(work_dir(), ctx.fi)
    pol3 = load_pol3_sidecar(work_dir(), ctx.static, ctx.static_names, ctx.foot, ctx.fi)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    rows = []
    for fold in range(4):
        for draw in DRAWS:
            cell = Cell(ctx, fold, draw, extras=True, h27=True)
            leak = canaries(cell, pol3)
            max_leak = max(v["canary_auc"] for v in leak.values())
            if max_leak > LEAKAGE_CAP:
                raise SystemExit(f"POL3 leakage canary failed: fold={fold}, draw={draw}, {leak}")
            pc = fit_predict(cell, cols, h34, None, draw)
            pp = fit_predict(cell, cols, h34, pol3, draw)
            ec, dc = emit(cell, pc)
            ep, dp = emit(cell, pp)
            rc, rp = cell.evaluate(ec), cell.evaluate(ep)
            row = {"fold": fold, "fold_name": FOLDS[fold], "draw": draw, "withheld_positives": rc["n_truth"],
                   "control": rc, "candidate": rp, "paired_gain": rp["dti"] - rc["dti"],
                   "hug_delta": rp["hug"] - rc["hug"], "control_emission": dc, "candidate_emission": dp,
                   "feature_canaries": leak}
            rows.append(row)
            with (OUT / "cells.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(f"fold={FOLDS[fold]} draw={draw} control={rc['dti']:.6f} candidate={rp['dti']:.6f} "
                  f"gain={row['paired_gain']:+.6f} canary={max_leak:.4f}", flush=True)
            del cell, pc, pp, ec, ep

    fold_gains = [float(np.mean([r["paired_gain"] for r in rows if r["fold"] == i])) for i in range(4)]
    mean_gain = float(np.mean(fold_gains))
    ci_half = float(student_t.ppf(0.975, 3) * np.std(fold_gains, ddof=1) / np.sqrt(4))
    c_pool, p_pool = pooled([r["control"] for r in rows]), pooled([r["candidate"] for r in rows])
    mean_hug_delta = float(np.mean([r["hug_delta"] for r in rows]))
    screen_gate = bool(mean_gain > 0.001 and sum(g > 0 for g in fold_gains) >= 3 and
                       min(fold_gains) >= -0.01 and mean_hug_delta <= 0.10)
    summary = {
        "evaluator": design["evaluator"], "draws": list(DRAWS), "cells": len(rows),
        "withheld_positives": sum(r["withheld_positives"] for r in rows),
        "control_pooled": c_pool, "candidate_pooled": p_pool,
        "paired_fold_mean_gain": mean_gain, "paired_fold_ci95": [mean_gain - ci_half, mean_gain + ci_half],
        "paired_gain_by_fold": fold_gains, "positive_folds": sum(g > 0 for g in fold_gains),
        "mean_hug_delta": mean_hug_delta,
        "max_canary_auc": max(v["canary_auc"] for r in rows for v in r["feature_canaries"].values()),
        "screen_gate_passed": screen_gate, "full_catalogue_raster_emitted": False,
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
