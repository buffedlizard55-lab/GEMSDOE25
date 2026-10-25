#!/usr/bin/env python3
"""H38 — greedy marginal-credit emission vs incumbent sapd on identical H35 (B35) surfaces.

Pre-registered in knowledge/25 (committed before any fit). One B35 surface is fitted
per (fold, draw) with the shared harness (``run_xg1_factorial.fit_arm``: BDE+7 + tip +
H34, HGB seed=draw); four emission arms share that surface, so every contrast is
purely the selection rule:

  A0 control   ridge-NMS top-K (kfrac 0.035) -> score-ordered dots 2.4 px
  A1 PRIMARY   same top-K pool -> greedy marginal-credit selection (gems25.greedy)
  A2 diagnostic A0 minus dots <=2 px from the *visible* catalogue (the B2 operation)
  A3 secondary 15-px line matched-filter surface -> own top-K pool -> greedy

Responses: standard HOLDOUT-DTI (``Cell.evaluate``) and off-catalogue HOLDOUT-DTI
(truth restricted to hidden pixels >2 px from the visible catalogue).

    .venv/bin/python scripts/run_h38.py --draws 20 21 --out evidence/h38_screen
    .venv/bin/python scripts/run_h38.py --draws 22 23 --out evidence/h38_confirm  # only if screen passes
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.greedy import greedy_dots, line_max_mean  # noqa: E402
from gems25.h34 import load_h34_sidecar  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402
from run_xg1_factorial import fit_arm  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
MIN_DIST, KFRAC = 2.4, 0.035
LINE_LEN, LINE_ORIENT = 15, 8
ARMS = ("A0", "A1", "A2", "A3")
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) via gems25.experiment.Cell.evaluate"


def crop_auc(score_c: np.ndarray, truth_c: np.ndarray, dom_c: np.ndarray, known_c: np.ndarray) -> float:
    """Leakage-canary AUC of a crop score vs hidden truth (fixed 150k-negative sample, rng 5)."""
    pos = np.flatnonzero((truth_c & dom_c).ravel())
    neg_pool = np.flatnonzero((dom_c & ~known_c & ~truth_c).ravel())
    if pos.size == 0 or neg_pool.size == 0:
        return float("nan")
    neg = np.random.default_rng(5).choice(neg_pool, size=min(150_000, neg_pool.size), replace=False)
    y = np.concatenate([np.ones(pos.size), np.zeros(neg.size)])
    v = np.nan_to_num(score_c.ravel()[np.concatenate([pos, neg])].astype(np.float64), nan=0.0)
    return float(roc_auc_score(y, v)) if np.unique(v).size > 1 else 0.5


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cells_path, design_path = out / "cells.jsonl", out / "design.json"
    if cells_path.exists() or design_path.exists():
        raise SystemExit(f"refusing to overwrite {out}; choose a fresh --out")
    design = dict(
        hypothesis="H38 greedy marginal-credit emission (A1 primary, A3 secondary) vs sapd2.4 (A0) on identical B35 surfaces; A2 = A0 with B=2 visible-catalogue prune (diagnostic)",
        preregistration="knowledge/25_preregistered_h38_greedy_credit_emission_2026-10-25.md",
        draws=a.draws,
        folds=list(FOLD_IDS),
        arms=list(ARMS),
        min_dist=MIN_DIST,
        kfrac=KFRAC,
        line_filter=dict(length=LINE_LEN, orientations=LINE_ORIENT),
        model=dict(base=BASE, extras=EXTRAS, tip_column="H27_tip", h34_columns="H34 3 cols", fit_seed="draw"),
        n_hat_rule="0.20/0.80 * |visible catalogue pixels inside the eroded domain|",
        evaluator=EVALUATOR,
        leakage_auc_cap=0.90,
        gate={"arms": "A1 vs A0 (primary), A3 vs A0 (secondary)", "mean_gain_gt": 0.001,
              "folds_positive_min": 3, "worst_fold_min": -0.010},
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    work = work_dir()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    h34_sidecar = load_h34_sidecar(work, ctx.fi)
    base_cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    tip_col = ctx.col["H27_tip"]
    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                p, timing = fit_arm(cell, base_cols, tip_col, h34_sidecar, None, (True, True, False), seed=draw)
                k = int(round(KFRAC * cell.dom_c.sum()))
                s_crop, top = cell.candidates(p, k)
                dist_vis = distance_transform_edt(~cell.known_c)
                truth_oc = cell.truth_c & (dist_vis > 2.0)
                n_visible_dom = int((cell.known_c & cell.dom_c).sum())
                n_hat = 0.25 * n_visible_dom
                base_auc = cell.auc(p)

                emissions: dict[str, np.ndarray] = {}
                diags: dict[str, dict] = {}
                t0 = time.time()
                emissions["A0"] = score_ordered_dots(s_crop, top, MIN_DIST)
                diags["A0"] = dict(emit_s=round(time.time() - t0, 2))
                t0 = time.time()
                a1, d1 = greedy_dots(s_crop, top, cell.dom_c, cell.known_c, n_hat)
                emissions["A1"] = a1
                diags["A1"] = dict(emit_s=round(time.time() - t0, 2), greedy=d1)
                emissions["A2"] = emissions["A0"] & (dist_vis > 2.0)
                diags["A2"] = dict(emit_s=0.0, pruned=int(emissions["A0"].sum() - emissions["A2"].sum()))
                t0 = time.time()
                s_line = line_max_mean(s_crop, cell.dom_c, LINE_LEN, LINE_ORIENT)
                r3 = ridge_nms(s_line, cell.dom_c, 1.0)
                top3 = select_top_positive(np.where(r3 & ~cell.known_c, s_line, 0.0), cell.dom_c, k)
                a3, d3 = greedy_dots(s_line, top3, cell.dom_c, cell.known_c, n_hat)
                emissions["A3"] = a3
                line_auc = crop_auc(s_line, cell.truth_c, cell.dom_c, cell.known_c)
                diags["A3"] = dict(emit_s=round(time.time() - t0, 2), greedy=d3, line_score_auc=line_auc)

                for arm in ARMS:
                    em = emissions[arm]
                    assert not (em & cell.known_c).any(), f"{arm} emitted on a visible catalogue pixel"
                    ev = cell.evaluate(em)
                    oc = dti_binary(em, truth_oc, valid=cell.dom_c, known=cell.known_c)
                    row = dict(
                        fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                        min_dist=MIN_DIST, kfrac=KFRAC, auc=base_auc,
                        n_hat=n_hat, n_visible_domain=n_visible_dom,
                        n_truth_offcat=int(truth_oc.sum()),
                        dti_offcat=oc["dti"], tp_offcat=oc["tp"], fp_offcat=oc["fp"],
                        coverage_offcat=oc["coverage"],
                        **ev, **timing, **diags[arm],
                    )
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(
                        f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {arm}: DTI={ev['dti']:.6f} "
                        f"OC={oc['dti']:.6f} emitted={ev['emitted']} hug={ev['hug']:.3f} auc={base_auc:.4f}",
                        flush=True,
                    )
                del cell, p, emissions, s_line
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
