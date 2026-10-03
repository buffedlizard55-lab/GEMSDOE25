#!/usr/bin/env python3
"""H28 stage 2 — the pre-registered 3 x 5 x 2 emission factorial on the hide-and-recover holdout.

`knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md` §8 as amended by D2. One model
fit per (fold, draw) cell is shared by all 30 arms, so every contrast is paired:

* value field : `score` (the fitted HGB surface, i.e. the status quo), `habitat` (``pi_cat * k`` from the fold's
  *visible* catalogue with the live-calibrated concentration scale), `both` (habitat x score, then ``* k``);
* spacing     : 1.5, 2.4, 3.0, 4.0, 6.0 px exclusion;
* budget      : 2.45 %, 3.5 % of the eroded domain.

The first thing the run does is reproduce the frozen comparator (`sapd2.4`, kfrac 3.5 %, draws 0-1,
DTI 0.15200338908786984). If that reproduction fails the run is void and says so.

    .venv/bin/python scripts/run_h28_holdout.py
    .venv/bin/python scripts/analyze_h28_holdout.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.design import H27_HISTORICAL_HOLDOUT_BEST  # noqa: E402
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.livecal import value_field  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402

DRAWS = (0, 1)
FOLDS = ("NW", "NE", "SW", "SE")
BASE = "BDE"
EXTRAS = ["X1_K", "X1_ThK", "X1_UK", "X2_compat", "X2_compat_coh", "X3_gm", "X3_gd"]
KFRACTS = (0.0245, 0.035)
SPACINGS = (1.5, 2.4, 3.0, 4.0, 6.0)
VALUES = ("score", "habitat", "both")
LAMBDA_HAT = 1.85          # from §5b, evidence/h28_calibration/anchors.json
COMPARATOR = {"value": "score", "min_dist": 2.4, "kfrac": 0.035}
COMPARATOR_DTI = H27_HISTORICAL_HOLDOUT_BEST
DESIGN_SEED = 20261003


def arms() -> list[dict]:
    return [{"value": v, "min_dist": s, "kfrac": k} for k in KFRACTS for s in SPACINGS for v in VALUES]


def habitat_value(known_c: np.ndarray, dom_c: np.ndarray, lam: float) -> np.ndarray:
    """``pi_cat * k`` on the crop: the live-calibrated shape applied to distance to the *visible* catalogue."""
    d = distance_transform_edt(~known_c)
    pi = np.where(dom_c & ~known_c, np.exp(-np.minimum(d, 80.0) / lam), 0.0)
    z = pi.sum()
    return value_field(pi / z) if z > 0 else np.zeros_like(pi)


def normalised(score: np.ndarray, where: np.ndarray) -> np.ndarray:
    v = np.where(where, np.nan_to_num(score, nan=0.0), np.nan)
    finite = v[np.isfinite(v)]
    if finite.size == 0:
        return np.zeros_like(score, dtype=np.float32)
    lo, hi = float(finite.min()), float(finite.max())
    out = np.nan_to_num((v - lo) / (hi - lo) if hi > lo else np.zeros_like(v), nan=0.0)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "evidence" / "h28_holdout"))
    ap.add_argument("--folds", type=int, nargs="*", default=[0, 1, 2, 3])
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    design_path, cells_path = out / "design.json", out / "cells.jsonl"
    if design_path.exists() or cells_path.exists():
        raise SystemExit(f"refusing to overwrite an existing run in {out}; choose a fresh --out")

    canonical = arms()
    order = np.random.default_rng(DESIGN_SEED).permutation(len(canonical)).tolist()
    randomized = [canonical[i] for i in order]
    design = {
        "hypothesis": "H28 holdout emission factorial",
        "preregistration": "knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md#8",
        "amendment": "D2 (draws 0-1 to match the frozen comparator; spacing widened to five levels; budget as a factor)",
        "draws": list(DRAWS), "spatial_folds": list(FOLDS),
        "factors": {"value": list(VALUES), "min_dist": list(SPACINGS), "kfrac": list(KFRACTS)},
        "lambda_hat_px": LAMBDA_HAT,
        "lambda_provenance": "evidence/h28_calibration/anchors.json (live-anchored, §5b)",
        "model": {"base": BASE, "extras": EXTRAS, "h27_columns": False, "fit_seed": "draw"},
        "comparator": {**COMPARATOR, "dti": COMPARATOR_DTI,
                       "source": "evidence/addons/emk_extension.json variant sapd2.4 kfrac 0.035"},
        "design_seed": DESIGN_SEED,
        "canonical_matrix": canonical, "row_order_zero_based": order, "randomized_matrix": randomized,
        "note": ("All arms share one HGB fit and one candidate pool per cell; only the value field, the exclusion "
                 "radius and the budget differ. The habitat field uses the fold's visible catalogue only."),
    }
    design_path.write_text(json.dumps(design, indent=1) + "\n")  # freeze before any fit

    ctx = load_context(work_dir())
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)

    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in args.folds:
            for draw in DRAWS:
                cell = Cell(ctx, fold, draw, extras=True)
                p, timing = cell.fit_predict(cols, seed=draw)
                hab = habitat_value(cell.known_c, cell.dom_c, LAMBDA_HAT)
                caches: dict[tuple[float, tuple], tuple] = {}
                for run_order, cfg in enumerate(randomized, start=1):
                    key = (cfg["kfrac"],)
                    if key not in caches:
                        caches[key] = cell.candidates(p, int(round(cfg["kfrac"] * cell.dom_c.sum())))
                    s_crop, top = caches[key]
                    if cfg["value"] == "score":
                        val = s_crop
                    elif cfg["value"] == "habitat":
                        val = hab
                    else:
                        val = value_field(np.where(cell.dom_c, hab * normalised(s_crop, top), 0.0))
                    t0 = time.time()
                    emitted = score_ordered_dots(val, top, cfg["min_dist"])
                    row = {"fold": fold, "fold_name": FOLDS[fold], "draw": draw, "run_order": run_order,
                           **cfg, "auc": cell.auc(p), "emit_s": round(time.time() - t0, 2),
                           **cell.evaluate(emitted), **timing}
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    if cfg == COMPARATOR or run_order % 10 == 0:
                        print(f"[fold {fold} draw {draw} {run_order}/30 {cfg['value']}/{cfg['min_dist']}/"
                              f"{cfg['kfrac']}] DTI={row['dti']:.6f} emitted={row['emitted']} "
                              f"elapsed={time.time() - t_all:.0f}s", flush=True)
                del cell
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
