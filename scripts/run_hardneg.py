#!/usr/bin/env python3
"""Exp 2 (knowledge/29 §4) — HARDNEG two-stage hard-negative mining vs BIN, hide-and-recover holdout.

Per (fold, draw): stage-1 = the BIN classifier (frozen B35 columns, ``HGB_PARAMS``, seed=draw)
trained on ``Cell``'s default sample — its quadrant surface is the BIN arm and the same model
scores every candidate-negative pixel of the train region.  Stage-2 retrains with identical
positives and negatives = 150k uniform (seed 777+31*fold+draw) + the 150k highest stage-1-scored
remaining pool pixels (ties by raster index).  Pool = train region, non-catalogue,
EDT(hidden_train) > 3 px.  Emission identical to Exp 1 (greedy primary, sapd2.4 diagnostic).

    .venv/bin/python scripts/run_hardneg.py --draws 94 95 --out evidence/hardneg_screen_2026-10-26
    .venv/bin/python scripts/run_hardneg.py --draws 96 97 --out evidence/hardneg_confirm_2026-10-26  # only on pass
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.greedy import greedy_dots  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.objective import assert_within, sampled_far, tent_masks  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402
from run_tent import canary_aucs, feature_matrix, quadrant_matrix  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
ARMS = ("BIN", "HNEG")
KFRAC, MIN_DIST = 0.035, 2.4
N_UNIFORM, N_HARD, CHUNK = 150_000, 150_000, 250_000
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) via gems25.experiment.Cell.evaluate"


def fit_clf(cell, idx, y, cols, h34_sidecar, Xq, draw):
    Xtr = feature_matrix(cell, idx, cols, h34_sidecar)
    t0 = time.time()
    model = HistGradientBoostingClassifier(random_state=int(draw), **HGB_PARAMS).fit(Xtr, y)
    t_fit = time.time() - t0
    del Xtr
    t0 = time.time()
    p = model.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return model, p, dict(fit_s=t_fit, predict_s=time.time() - t0, n_features=int(Xq.shape[1]),
                           train_rows=int(idx.size))


def score_pool(model, cell, pool_idx, cols, h34_sidecar):
    out = np.empty(pool_idx.size, np.float32)
    for lo in range(0, pool_idx.size, CHUNK):
        sl = pool_idx[lo:lo + CHUNK]
        out[lo:lo + CHUNK] = model.predict_proba(
            np.ascontiguousarray(feature_matrix(cell, sl, cols, h34_sidecar)))[:, 1]
    return out


def emit_all(cell, p, n_hat):
    k = int(round(KFRAC * cell.dom_c.sum()))
    s_crop, top = cell.candidates(p, k)
    greedy, diag = greedy_dots(s_crop, top, cell.dom_c, cell.known_c, n_hat)
    return {"greedy": (greedy, diag), "sapd": (score_ordered_dots(s_crop, top, MIN_DIST), {})}


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
    work = work_dir()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or None
    design = dict(
        hypothesis="HARDNEG two-stage hard-negative mining vs BIN on the frozen B35 stack (knowledge/29 Exp 2)",
        preregistration="knowledge/29_ranked_hypotheses_and_preregistration_2026-10-26.md",
        implementation_commit=head,
        draws=a.draws, folds=list(FOLD_IDS), arms=list(ARMS),
        features=dict(base=BASE, extras=EXTRAS, tip_column="H27_tip", h34_columns=H34_NAMES),
        classifier=HGB_PARAMS,
        hardneg_rule="stage2 negatives = 150k uniform (seed 777+31*fold+draw) + 150k highest stage-1-scored remaining pool pixels; pool = train_region & ~catalogue & EDT(hidden_train)>3; positives identical to BIN",
        emission_primary="greedy marginal-credit on ridge-NMS top-3.5% pool (H38 rule), n_hat=0.25*|visible in domain|",
        emission_diagnostic="score_ordered_dots min_dist=2.4 on the same pool",
        evaluator=EVALUATOR, leakage_auc_cap=0.90,
        gate={"primary": "HNEG-greedy vs BIN-greedy", "mean_gain_gt": 0.001, "folds_positive_min": 3,
              "worst_fold_min": -0.010, "mean_hug_increase_max": 0.10},
        runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    h34_sidecar = load_h34_sidecar(work, ctx.fi)
    base_cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    cols = list(base_cols) + [ctx.col["H27_tip"]]
    tip_pos, h34_start = len(cols) - 1, len(cols)

    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                Xq = quadrant_matrix(cell, cols, h34_sidecar)
                canary = canary_aucs(cell, tip_pos, Xq, h34_start)
                canary_eff = {k: (max(v, 1.0 - v) if np.isfinite(v) else float("inf")) for k, v in canary.items()}
                if max(canary_eff.values()) > 0.90:
                    (out / "canary_failure.json").write_text(json.dumps(
                        dict(fold=fold, draw=draw, canary=canary, effective=canary_eff), indent=1) + "\n")
                    raise SystemExit(f"LEAKAGE CANARY FAIL fold {fold} draw {draw}: {canary_eff}")
                dist_vis = distance_transform_edt(~cell.known_c)
                truth_oc = cell.truth_c & (dist_vis > 2.0)
                n_hat = 0.25 * int((cell.known_c & cell.dom_c).sum())

                # stage 1 = BIN (identical training sample/columns/seed to fit_arm's B35)
                m1, p_bin, t_bin = fit_clf(cell, cell.train_idx, cell.y, cols, h34_sidecar, Xq, draw)
                # stage-2 sample: positives = same trace pixels; negatives from the far pool
                _, trace, _, far = tent_masks(cell.draw.hidden_train, ctx.labels, cell.draw.train_region)
                pos_idx = ctx.vec(trace)
                pool_idx = ctx.vec(far)
                assert_within(pool_idx, ctx.vec(cell.draw.train_region))
                t0 = time.time()
                pool_scores = score_pool(m1, cell, pool_idx, cols, h34_sidecar)
                t_pool = time.time() - t0
                del m1
                uni = sampled_far(pool_idx, N_UNIFORM, 777 + 31 * fold + draw)
                rest_mask = ~np.isin(pool_idx, uni)
                rest_idx, rest_scores = pool_idx[rest_mask], pool_scores[rest_mask]
                order = np.lexsort((rest_idx, -rest_scores.astype(np.float64)))
                hard = rest_idx[order[:min(N_HARD, rest_idx.size)]]
                s2_idx = np.sort(np.concatenate([pos_idx, uni, hard]))
                s2_y = np.isin(s2_idx, pos_idx).astype(np.int8)
                assert_within(s2_idx, ctx.vec(cell.draw.train_region))
                sample_diag = dict(n_pool=int(pool_idx.size), n_uniform=int(uni.size), n_hard=int(hard.size),
                                   n_pos=int(pos_idx.size), pool_score_seconds=round(t_pool, 1),
                                   hard_score_min=float(rest_scores[order[min(N_HARD, rest_idx.size) - 1]])
                                   if hard.size else None)
                del pool_scores, rest_idx, rest_scores
                _, p_hn, t_hn = fit_clf(cell, s2_idx, s2_y, cols, h34_sidecar, Xq, draw)
                surfaces = {"BIN": (p_bin, t_bin), "HNEG": (p_hn, t_hn)}
                del Xq

                for arm in ARMS:
                    p, timing = surfaces[arm]
                    auc = cell.auc(p)
                    for emission, (em, diag) in emit_all(cell, p, n_hat).items():
                        assert not (em & cell.known_c).any(), f"{arm}/{emission} on visible catalogue"
                        ev = cell.evaluate(em)
                        oc = dti_binary(em, truth_oc, valid=cell.dom_c, known=cell.known_c)
                        row = dict(
                            fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm, emission=emission,
                            auc=auc, n_hat=n_hat, kfrac=KFRAC, min_dist=MIN_DIST,
                            n_truth_offcat=int(truth_oc.sum()), dti_offcat=oc["dti"], tp_offcat=oc["tp"],
                            fp_offcat=oc["fp"], coverage_offcat=oc["coverage"],
                            feature_auc_canary=canary, feature_auc_canary_effective=canary_eff,
                            sample_diag=sample_diag,
                            **ev, **timing, greedy_diag={k2: v2 for k2, v2 in diag.items()
                                                         if isinstance(v2, (int, float))},
                        )
                        sink.write(json.dumps(row) + "\n")
                        sink.flush()
                        print(f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {arm}/{emission}: "
                              f"DTI={ev['dti']:.6f} OC={oc['dti']:.6f} emitted={ev['emitted']} "
                              f"hug={ev['hug']:.3f} auc={auc:.4f} canary_max={max(canary_eff.values()):.3f}", flush=True)
                del cell, surfaces
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
