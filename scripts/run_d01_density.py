#!/usr/bin/env python3
"""D01 — incumbent emission-density response on the hide-and-recover holdout.

Preregistered in knowledge/30_preregistered_d01_density_2026-10-26.md.
One fit per (quadrant, draw); emission at fixed full-footprint dot counts using the
shared Cell/candidates/metric. No geology changes; no submission TIF is written.
"""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from gems25.experiment import Cell, HGB_PARAMS, load_context  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from gems25.validation import feature_canary, pooled_dti  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier  # noqa: E402

OUT = ROOT / "evidence" / "d01_density_2026-10-26"
DRAWS = (60, 61)
FOOTPRINT = 5_167_373
COUNTS = (12_000, 21_713, 26_494, 37_654, 44_090, 59_472, 70_524)
CURRENT = 70_524
SEED, DRAWS_BOOT = 26026, 10_000


def save(name, value):
    def clean(v):
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, list):
            return [clean(x) for x in v]
        if isinstance(v, float) and not np.isfinite(v):
            return None
        return v
    (OUT / name).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    ctx = load_context(work_dir())
    h34 = load_h34_sidecar(work_dir(), ctx.fi)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    names = {v: k for k, v in ctx.col.items()}
    rows, canaries = [], []
    with (OUT / "cells.jsonl").open("w") as sink:
        for fold in range(4):
            for draw in DRAWS:
                if time.monotonic() - started > 5400:
                    raise SystemExit("time guard: incomplete diagnostic, no interpretation")
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                idx = np.concatenate([cell.auc_pos, cell.auc_neg])
                target = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
                checks = {f"incumbent:{names[j]}": feature_canary(cell.Xq[idx, j], target) for j in cols}
                checks.update({f"incumbent:{n}": feature_canary(h34[k, cell.q[idx]], target)
                               for k, n in enumerate(H34_NAMES)})
                canaries.append(dict(fold=fold, draw=draw, features=checks))
                save("feature_canaries.json", canaries)
                if not all(r["passed"] for r in checks.values()):
                    raise SystemExit("feature-alone leakage canary failed; stop before trusting performance")
                Xtr = np.hstack([cell.Xtr[:, cols], np.asarray(h34[:, cell.train_idx]).T])
                model = HistGradientBoostingClassifier(random_state=draw, **HGB_PARAMS).fit(Xtr, cell.y)
                del Xtr
                Xq = np.hstack([cell.Xq[:, cols], np.asarray(h34[:, cell.q]).T])
                pred = model.predict_proba(Xq)[:, 1].astype(np.float32)
                del Xq, model
                for n in COUNTS:
                    s, top = cell.candidates(pred, int(round(n / FOOTPRINT * cell.dom_c.sum())))
                    dots = score_ordered_dots(s, top, 2.4)
                    row = dict(fold=fold, draw=draw, count=n, **cell.evaluate(dots))
                    rows.append(row)
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"fold={fold} draw={draw} N={n} HOLDOUT-DTI={row['dti']:.6f} emitted={row['emitted']}", flush=True)
                del cell, pred, s, top, dots
                gc.collect()

    folds = sorted({r["fold"] for r in rows})
    totals = {n: np.array([[sum(r[k] for r in rows if r["count"] == n and r["fold"] == f)
                            for k in ("tp", "fp", "n_truth")] for f in folds]) for n in COUNTS}
    sample = np.random.default_rng(SEED).integers(0, len(folds), size=(DRAWS_BOOT, len(folds)))
    boots = {}
    for n, t in totals.items():
        b = t[sample].sum(axis=1)
        boots[n] = b[:, 0] / (0.2 * (b[:, 0] + b[:, 1]) + 0.8 * b[:, 2] + 1e-7)
    arms = {}
    for n in COUNTS:
        arms[str(n)] = dict(
            pooled_dti=pooled_dti([r for r in rows if r["count"] == n]),
            ci95=np.quantile(boots[n], [0.025, 0.975]).tolist(),
            emitted_median=float(np.median([r["emitted"] for r in rows if r["count"] == n])),
            withheld_positive_occurrences=int(totals[n][:, 2].sum()),
            fold_dti=[pooled_dti([r for r in rows if r["count"] == n and r["fold"] == f]) for f in folds],
            paired_gain_vs_current=float(
                pooled_dti([r for r in rows if r["count"] == n]) - pooled_dti([r for r in rows if r["count"] == CURRENT])),
            paired_ci95=np.quantile(boots[n] - boots[CURRENT], [0.025, 0.975]).tolist(),
        )
    best = max(COUNTS, key=lambda n: arms[str(n)]["pooled_dti"])
    summary = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        evidence_class="HOLDOUT-DTI density-response diagnostic; no new geology; not a leaderboard score",
        design=dict(folds=4, draws=list(DRAWS), counts=list(COUNTS), spacing_px=2.4,
                    footprint_px=FOOTPRINT, model="H35 columns + H34 sidecar, shared HGB_PARAMS",
                    note="one fit per cell shared by all densities; no arm selection for submission"),
        evaluator={p: __import__("gems25.submission", fromlist=["sha256_file"]).sha256_file(ROOT / p) for p in (
            "src/gems25/metric.py", "src/gems25/holdout.py", "src/gems25/experiment.py",
            "src/gems25/validation.py", "src/gems25/thinning.py", "scripts/run_d01_density.py")},
        arms=arms, best_pooled_count=best,
        lane_budget_count=21_713,
        interpretation=("Descriptive density response on the catalogue-gap proxy. The count that "
                        "maximises the proxy is NOT a validated method and must not be presented as one."),
    )
    save("analysis.json", summary)
    print(f"best pooled count={best} dti={arms[str(best)]['pooled_dti']:.6f}", flush=True)


if __name__ == "__main__":
    main()
