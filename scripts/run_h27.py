#!/usr/bin/env python3
"""Run the frozen H27-1 2² tip/terrain holdout design (knowledge/09...)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.design import H27_ARMS, H27_HISTORICAL_HOLDOUT_BEST  # noqa: E402
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402

PRE_REGISTERED_DRAWS = {"screen": [4, 5], "confirm": [6, 7]}
BASE_EXTRAS = ["X1_K", "X1_ThK", "X1_UK", "X2_compat", "X2_compat_coh", "X3_gm", "X3_gd"]
EMISSION_KFRAC = 0.035
EMISSION_MIN_DIST = 2.4
DESIGN_SEED = 20261003


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=PRE_REGISTERED_DRAWS, default="screen")
    ap.add_argument("--draws", type=int, nargs="+", default=None,
                    help="fixed by preregistration: screen=4,5; confirm=6,7")
    ap.add_argument("--out", default=None, help="output directory (must not already contain a run)")
    args = ap.parse_args()
    draws = PRE_REGISTERED_DRAWS[args.stage]
    if args.draws is not None and args.draws != draws:
        ap.error(f"the frozen {args.stage} stage requires draws {draws}; refusing an unregistered draw set")
    if args.stage == "confirm":
        screen_path = ROOT / "evidence" / "h27_screen" / "results.json"
        if not screen_path.exists() or not json.loads(screen_path.read_text()).get("slot_eligible", False):
            raise SystemExit("confirmation is preregistered only after the draws 4,5 screen passes both frozen gates")

    out = Path(args.out) if args.out else ROOT / "evidence" / f"h27_{args.stage}"
    out.mkdir(parents=True, exist_ok=True)
    design_path, cells_path = out / "design.json", out / "cells.jsonl"
    if design_path.exists() or cells_path.exists():
        raise SystemExit(f"refusing to overwrite an existing H27 run in {out}; choose a fresh --out directory")

    canonical = [{"arm": arm, "T": levels[0], "S": levels[1]} for arm, levels in H27_ARMS.items()]
    order = np.random.default_rng(DESIGN_SEED).permutation(len(canonical)).tolist()
    randomized = [canonical[i] for i in order]
    design = {
        "hypothesis": "H27-1",
        "stage": args.stage,
        "preregistration": "knowledge/09_preregistered_hypotheses_2026-10-02.md",
        "draws": draws,
        "spatial_folds": ["NW", "NE", "SW", "SE"],
        "design_seed": DESIGN_SEED,
        "canonical_matrix": canonical,
        "row_order_zero_based": order,
        "randomized_matrix": randomized,
        "historical_holdout_best": H27_HISTORICAL_HOLDOUT_BEST,
        "fixed_model_families": "BDE",
        "fixed_addons": BASE_EXTRAS,
        "emission": {"method": "score_ordered_dots", "kfrac": EMISSION_KFRAC, "min_dist_px": EMISSION_MIN_DIST},
        "notes": "Rows are fit in the saved randomized order within every fold/draw; same HGB seed and common hide draw across rows.",
    }
    ctx = load_context(work_dir())
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("H26 add-on feature cache is absent or malformed; run scripts/build_addons.py first")
    required_static = {"L_step_max", "B_crest", "B_trough"}
    if not required_static.issubset(ctx.static_names):
        raise SystemExit(f"static cache lacks H27-1 layers: {sorted(required_static - set(ctx.static_names))}")
    if not np.isfinite(ctx.h27_scarp).all() or not (ctx.h27_scarp > 0).any():
        raise SystemExit("H27 scarp feature is empty or non-finite; check the DEM/LiDAR cache")
    base_cols = ctx.columns("BDE") + ctx.named(BASE_EXTRAS)
    arm_cols = {
        "BASE": base_cols,
        "T": base_cols + ctx.named(["H27_tip"]),
        "S": base_cols + ctx.named(["H27_scarp"]),
        "TS": base_cols + ctx.named(["H27_tip", "H27_scarp", "H27_tip_x_scarp"]),
    }
    design_path.write_text(json.dumps(design, indent=1) + "\n")  # freeze the exact matrix before any model scores

    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in range(4):
            for draw_seed in draws:
                cell = Cell(ctx, fold, draw_seed, extras=True, h27=True)
                k = int(round(EMISSION_KFRAC * cell.dom_c.sum()))
                for run_order, cfg in enumerate(randomized, start=1):
                    arm = cfg["arm"]
                    p, timing = cell.fit_predict(arm_cols[arm], seed=draw_seed)
                    score_crop, candidates = cell.candidates(p, k)
                    emitted = score_ordered_dots(score_crop, candidates, EMISSION_MIN_DIST)
                    row = {
                        "stage": args.stage,
                        "fold": fold,
                        "fold_name": design["spatial_folds"][fold],
                        "draw": draw_seed,
                        "run_order": run_order,
                        "arm": arm,
                        "T": cfg["T"],
                        "S": cfg["S"],
                        "design_seed": DESIGN_SEED,
                        "kfrac": EMISSION_KFRAC,
                        "min_dist_px": EMISSION_MIN_DIST,
                        "auc": cell.auc(p),
                        **cell.evaluate(emitted),
                        **timing,
                    }
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(
                        f"[{args.stage} fold {fold} draw {draw_seed} row {run_order}/4 {arm}] "
                        f"DTI={row['dti']:.6f} emitted={row['emitted']} "
                        f"fit={row['fit_s']:.1f}s elapsed={time.time() - t_all:.0f}s",
                        flush=True,
                    )
                del cell
    print(f"DONE: raw cells in {cells_path}", flush=True)


if __name__ == "__main__":
    main()
