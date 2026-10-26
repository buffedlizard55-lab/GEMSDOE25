#!/usr/bin/env python3
"""Exp 1 (knowledge/29) — TENT kernel-regression target vs BIN classifier, hide-and-recover holdout.

One ``Cell(extras=True, h27=True)`` per (fold, draw); three fits share its features:

  BIN   status-quo classifier (``run_xg1_factorial.fit_arm`` B35: BDE+7 + H27_tip + 3 H34 cols)
  TENT  PRIMARY — HistGradientBoostingRegressor on the tent target (gems25.objective)
  IGN3  diagnostic classifier whose negatives exclude d<=3 px to the pseudo-hidden trace

Emission is identical for every surface: greedy marginal-credit (primary response;
H38 rule, top-3.5% ridge-NMS pool, n_hat = 0.25|visible in domain|) and, as a recorded
diagnostic, score-ordered dots at 2.4 px.

    .venv/bin/python scripts/run_tent.py --draws 90 91 --out evidence/tent_screen_2026-10-26
    .venv/bin/python scripts/run_tent.py --draws 92 93 --out evidence/tent_confirm_2026-10-26  # only on screen pass
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
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.greedy import greedy_dots  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.objective import build_objective_samples  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
ARMS = ("BIN", "TENT", "IGN3")
KFRAC, MIN_DIST = 0.035, 2.4
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3px) via gems25.experiment.Cell.evaluate"
REG_PARAMS = {k: v for k, v in HGB_PARAMS.items() if k != "class_weight"}


def feature_matrix(cell: Cell, idx: np.ndarray, cols, h34_sidecar):
    """Same column layout as run_xg1_factorial.fit_arm (base cols, then H34 block)."""
    X = cell._gather(idx)[:, cols]
    return np.hstack([X, np.asarray(h34_sidecar[:, idx]).T]).astype(np.float32, copy=False)


def quadrant_matrix(cell: Cell, cols, h34_sidecar):
    return np.hstack([cell.Xq[:, cols], np.asarray(h34_sidecar[:, cell.q]).T]).astype(np.float32, copy=False)


def canary_aucs(cell: Cell, cols_tip_pos: int, Xq_full: np.ndarray, h34_start: int) -> dict:
    out = {"H27_tip": cell.auc(np.asarray(Xq_full[:, cols_tip_pos], np.float64))}
    for j, name in enumerate(H34_NAMES):
        out[name] = cell.auc(np.asarray(Xq_full[:, h34_start + j], np.float64))
    return out


def emit_all(cell: Cell, p: np.ndarray, n_hat: float):
    k = int(round(KFRAC * cell.dom_c.sum()))
    s_crop, top = cell.candidates(p, k)
    greedy, diag = greedy_dots(s_crop, top, cell.dom_c, cell.known_c, n_hat)
    sapd = score_ordered_dots(s_crop, top, MIN_DIST)
    return {"greedy": (greedy, diag), "sapd": (sapd, {})}


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
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        head = None
    design = dict(
        hypothesis="TENT kernel-regression training target vs BIN binary classifier on the frozen B35 stack (knowledge/29 Exp 1)",
        preregistration="knowledge/29_ranked_hypotheses_and_preregistration_2026-10-26.md",
        preregistration_commit=head,
        draws=a.draws, folds=list(FOLD_IDS), arms=list(ARMS),
        features=dict(base=BASE, extras=EXTRAS, tip_column="H27_tip", h34_columns=H34_NAMES),
        classifier=HGB_PARAMS, regressor=REG_PARAMS,
        tent_rule="target=k(EDT(hidden_train)) on trace+ring (0<d<=3, non-catalogue); 300k uniform far negatives d>3; seed 777+31*fold+draw; train_region only",
        emission_primary="greedy marginal-credit on ridge-NMS top-3.5% pool (H38 rule), n_hat=0.25*|visible in domain|",
        emission_diagnostic="score_ordered_dots min_dist=2.4 on the same pool",
        evaluator=EVALUATOR, leakage_auc_cap=0.90,
        gate={"primary": "TENT-greedy vs BIN-greedy", "mean_gain_gt": 0.001, "folds_positive_min": 3,
              "worst_fold_min": -0.010, "mean_hug_increase_max": 0.10},
        cache_hashes_file="evidence/work_cache_hashes.json",
        runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    h34_sidecar = load_h34_sidecar(work, ctx.fi)
    base_cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    cols = list(base_cols) + [ctx.col["H27_tip"]]
    tip_pos = len(cols) - 1
    h34_start = len(cols)

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
                samples = build_objective_samples(ctx, cell.draw, fold, draw)
                from run_xg1_factorial import fit_arm  # late import: writes nothing on import

                surfaces: dict[str, tuple[np.ndarray, dict]] = {}
                # BIN — exact status quo via the shared fit_arm
                p_bin, timing_bin = fit_arm(cell, base_cols, ctx.col["H27_tip"], h34_sidecar, None,
                                            (True, True, False), seed=draw)
                surfaces["BIN"] = (p_bin, timing_bin)
                # TENT — regressor on tent targets
                tent_idx, tent_y = samples["tent"]
                Xtr = feature_matrix(cell, tent_idx, cols, h34_sidecar)
                t0 = time.time()
                reg = HistGradientBoostingRegressor(random_state=draw, **REG_PARAMS).fit(Xtr, tent_y)
                t_fit = time.time() - t0
                del Xtr
                t0 = time.time()
                p_tent = np.maximum(reg.predict(np.ascontiguousarray(Xq)), 0.0).astype(np.float32)
                surfaces["TENT"] = (p_tent, dict(fit_s=t_fit, predict_s=time.time() - t0,
                                                 n_features=int(Xq.shape[1]), train_rows=int(tent_idx.size)))
                del reg
                # IGN3 — classifier, negatives exclude d<=3 ring
                ign_idx, ign_y = samples["ign3"]
                Xtr = feature_matrix(cell, ign_idx, cols, h34_sidecar)
                t0 = time.time()
                clf = HistGradientBoostingClassifier(random_state=draw, **HGB_PARAMS).fit(Xtr, ign_y)
                t_fit = time.time() - t0
                del Xtr
                t0 = time.time()
                p_ign = clf.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
                surfaces["IGN3"] = (p_ign, dict(fit_s=t_fit, predict_s=time.time() - t0,
                                                n_features=int(Xq.shape[1]), train_rows=int(ign_idx.size)))
                del clf, Xq

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
                            sample_diag=samples["diag"],
                            **ev, **timing, greedy_diag={k2: v2 for k2, v2 in diag.items()
                                                         if isinstance(v2, (int, float))},
                        )
                        sink.write(json.dumps(row) + "\n")
                        sink.flush()
                        print(f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {arm}/{emission}: "
                              f"DTI={ev['dti']:.6f} OC={oc['dti']:.6f} emitted={ev['emitted']} "
                              f"hug={ev['hug']:.3f} auc={auc:.4f} canary_max={max(canary_eff.values()):.3f}", flush=True)
                del cell, surfaces, samples
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
