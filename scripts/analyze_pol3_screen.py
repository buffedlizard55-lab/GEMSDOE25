#!/usr/bin/env python3
"""Analyze already-fitted POL3 screen cells without refitting or tuning."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "pol3_screen_2026-10-26"


def pooled(rows: list[dict], key: str) -> dict:
    items = [row[key] for row in rows]
    tp, fp, n = sum(x["tp"] for x in items), sum(x["fp"] for x in items), sum(x["n_truth"] for x in items)
    fn = n - tp
    dti = tp / (tp + 0.2 * fp + 0.8 * fn + 1e-7)
    return {"dti": float(dti), "withheld_positives": int(n), "tp": float(tp), "fp": float(fp), "fn": float(fn)}


def main() -> None:
    design = json.loads((OUT / "design.json").read_text())
    rows = [json.loads(line) for line in (OUT / "cells.jsonl").read_text().splitlines() if line.strip()]
    if len(rows) != 8:
        raise SystemExit(f"expected 8 completed registered cells, found {len(rows)}")
    gains = [float(np.mean([r["paired_gain"] for r in rows if r["fold"] == fold])) for fold in range(4)]
    mean = float(np.mean(gains))
    half = float(student_t.ppf(0.975, 3) * np.std(gains, ddof=1) / np.sqrt(4))
    max_canary = max(v["canary_auc"] for r in rows for v in r["feature_canaries"].values())
    hug_delta = float(np.mean([r["hug_delta"] for r in rows]))
    gate = bool(max_canary <= design["leakage_auc_cap"] and mean > design["gate"]["mean_gain_gt"] and
                sum(x > 0 for x in gains) >= design["gate"]["folds_positive_min"] and
                min(gains) >= design["gate"]["worst_fold_min"] and hug_delta <= design["gate"]["hug_delta_max"])
    summary = {
        "evaluator": design["evaluator"], "draws": design["draws"], "cells": len(rows),
        "withheld_positives": sum(r["withheld_positives"] for r in rows),
        "control_pooled": pooled(rows, "control"), "candidate_pooled": pooled(rows, "candidate"),
        "paired_fold_mean_gain": mean, "paired_fold_ci95": [mean - half, mean + half],
        "paired_gain_by_fold": gains, "positive_folds": sum(x > 0 for x in gains),
        "mean_hug_delta": hug_delta, "max_canary_auc": max_canary,
        "screen_gate_passed": gate, "full_catalogue_raster_emitted": False,
        "analysis_note": "Computed from saved cells.jsonl only; no model refit, parameter change, or candidate raster emission.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
