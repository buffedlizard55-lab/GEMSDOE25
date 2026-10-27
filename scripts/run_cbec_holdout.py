#!/usr/bin/env python3
"""Run the preregistered CBEC 2x2 on the shared 25-km block-withheld evaluator.

This is an experiment driver only: it does not generate or register a GeoTIFF.
The metric, component/block withholding, catalogue features, HGB settings, SAPD emitter,
canary, and paired bootstrap are imported from the project's shared implementations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import DOMAIN_ERODE, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h34 import load_h34_sidecar  # noqa: E402
from gems25.h74_rmps import BLOCK_PX_DEFAULT, draw_block25km  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.validation import feature_canary, pooled_summary  # noqa: E402
from run_h74_experiments import (  # noqa: E402
    EVALUATOR,
    FOLD_IDS,
    FOLDS,
    HGB_PARAMS,
    KFRAC_H35,
    MIN_DIST_H35,
    emit_sapd,
    eval_arm,
    fit_predict,
)

DRAWS = (116, 117)
ARMS = ("CTRL_H35", "COND_BASE", "GRAV_EDGE", "CBEC")
NEW_FEATURES = ("CBEC_cond_base", "CBEC_gravity_edge", "CBEC_joint")
CANARY_CAP = 0.90


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scaled(ctx, name: str) -> np.ndarray:
    v = np.asarray(ctx.static[ctx.static_names.index(name)], dtype=np.float32)
    lo, hi = ctx.scale[name]
    return np.clip((v - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def build_candidate_features(ctx) -> dict[str, np.ndarray]:
    """Fixed, catalogue-independent fields from the frozen cached feature stack."""
    c = scaled(ctx, "D_cond_grad")
    d = scaled(ctx, "D_depth_base_grad")
    g = scaled(ctx, "A_grav_hg_ridge")
    cond_base = np.sqrt(c * d, dtype=np.float32)
    joint = np.sqrt(cond_base * g, dtype=np.float32)
    return {
        "CBEC_cond_base": cond_base,
        "CBEC_gravity_edge": g,
        "CBEC_joint": joint,
    }


def make_cell(ctx, h34, custom, fold: int, draw: int):
    d = draw_block25km(ctx.holdout, fold, draw, block_px=BLOCK_PX_DEFAULT)
    if (d.visible & d.hidden_test).any() or (d.visible & d.hidden_train).any():
        raise RuntimeError("visible catalogue intersects withheld labels")
    if (d.train_region & d.quadrant).any():
        raise RuntimeError("training area intersects the spatial test quadrant")

    E_vis = build_catalogue_features(d.visible, ctx.fi)
    tip_vis = build_tip_continuation(d.visible, ctx.foot, ctx.fi)
    rng = np.random.default_rng(777 + 31 * fold + draw)
    pos = ctx.vec(d.hidden_train)
    near = distance_transform_edt(~d.hidden_train) <= 1.5
    neg_pool = ctx.vec(d.train_region & ~ctx.labels & ~near)
    neg = rng.choice(neg_pool, size=min(N_NEG, neg_pool.size), replace=False)
    train_idx = np.sort(np.concatenate([pos, neg]))
    y = np.isin(train_idx, pos).astype(np.int8)
    q_idx = ctx.vec(d.quadrant)
    fi_q = ctx.fi[q_idx]

    def matrix(idx):
        base = gather_columns(ctx, E_vis, idx, extras=True)
        tip = tip_vis[idx, None].astype(np.float32)
        h34_part = np.asarray(h34[:, idx], dtype=np.float32).T
        new = np.column_stack([custom[k][idx] for k in NEW_FEATURES]).astype(np.float32)
        return np.column_stack([base, tip, h34_part, new]).astype(np.float32)

    Xtr, Xq = matrix(train_idx), matrix(q_idx)
    sl = d.bbox
    dom_q = binary_erosion(d.quadrant, iterations=DOMAIN_ERODE)
    dom_c = dom_q[sl]
    truth_c = (d.hidden_test & dom_q)[sl]
    known_c = d.visible[sl]
    d_vis_c = distance_transform_edt(~known_c).astype(np.float32)
    dq = dom_q.ravel()[ctx.fi][q_idx]
    hq = (d.hidden_test & dom_q).ravel()[ctx.fi][q_idx]
    cq = ctx.labels.ravel()[ctx.fi][q_idx]
    pos_auc = np.flatnonzero(hq)
    neg_auc_pool = np.flatnonzero(dq & ~cq)
    neg_auc = np.random.default_rng(5).choice(neg_auc_pool, size=min(150_000, neg_auc_pool.size), replace=False)
    auc_idx = np.concatenate([pos_auc, neg_auc])
    auc_y = np.concatenate([np.ones(pos_auc.size, dtype=np.int8), np.zeros(neg_auc.size, dtype=np.int8)])
    canaries = {
        name: feature_canary(Xq[auc_idx, Xq.shape[1] - len(NEW_FEATURES) + j], auc_y, cap=CANARY_CAP)
        for j, name in enumerate(NEW_FEATURES)
    }
    meta = dict(
        fold=int(fold), fold_name=FOLDS[fold], draw=int(draw),
        n_withheld_positive=int(truth_c.sum()), n_train=int(train_idx.size),
        n_hidden_train=int(pos.size),
    )
    return d, Xtr, Xq, y, q_idx, fi_q, sl, dom_c, truth_c, known_c, d_vis_c, auc_idx, auc_y, canaries, meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "evidence" / "cbec_screen_2026-10-27"))
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"Refusing to overwrite run directory: {out}")
    out.mkdir(parents=True, exist_ok=False)

    work = work_dir()
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing/mismatched; stop before fitting")
    h34 = load_h34_sidecar(work, ctx.fi)
    custom = build_candidate_features(ctx)
    missing = [n for n in ("D_cond_grad", "D_depth_base_grad", "A_grav_hg_ridge") if n not in ctx.static_names]
    if missing:
        raise SystemExit(f"required frozen feature columns absent: {missing}")

    # Save the experiment design before the first model fit.
    design = {
        "experiment": "CBEC_2x2_BLOCK25KM",
        "preregistration": "knowledge/39_preregistered_current_review_2026-10-27.md",
        "draws": list(DRAWS), "folds": list(FOLD_IDS), "fold_names": list(FOLDS),
        "block_px": BLOCK_PX_DEFAULT, "arms": list(ARMS),
        "factors": {"conductive_basement_edge": [0, 1], "gravity_edge": [0, 1]},
        "emitter": {"type": "shared H35 SAPD", "kfrac": KFRAC_H35, "min_dist_px": MIN_DIST_H35},
        "leakage_canary_cap": CANARY_CAP,
        "evaluator": EVALUATOR,
        "evaluator_hashes": {p: sha(ROOT / p) for p in (
            "src/gems25/metric.py", "src/gems25/holdout.py", "src/gems25/block_holdout.py",
            "src/gems25/validation.py", "src/gems25/h74_rmps.py", "src/gems25/experiment.py",
            "src/gems25/h34.py", "scripts/run_h74_experiments.py", "scripts/run_cbec_holdout.py",
        )},
        "cache_hashes": {p: sha(work / p) for p in (
            "static_ABCD.npy", "static_ABCD.npy.names.json", "addons.npy", "addons.npy.names.json",
            "bands/_footprint.npy", "bands/_labels.npy", "h34_columns.npy", "h34_columns.npy.names.json",
        )},
        "hgb_params": HGB_PARAMS,
        "note": "The fixed primary arm is CBEC (both factors plus their interaction); no TIFF is produced.",
    }
    (out / "design.json").write_text(json.dumps(design, indent=2) + "\n")

    # Phase 1: every feature alone across every spatially-blocked cell. A failure stops before any fit.
    canary_rows = []
    t0 = time.time()
    for fold in FOLD_IDS:
        for draw in DRAWS:
            cell = make_cell(ctx, h34, custom, fold, draw)
            _, _, _, _, _, _, _, _, _, _, _, _, _, canaries, meta = cell
            canary_rows.append({**meta, "features": canaries})
            del cell
    canary_path = out / "feature_canaries.json"
    canary_path.write_text(json.dumps(canary_rows, indent=1) + "\n")
    failed = [(r["fold_name"], r["draw"], n, x.get("canary_auc"))
              for r in canary_rows for n, x in r["features"].items() if not x["passed"]]
    if failed:
        (out / "status.json").write_text(json.dumps({"status": "STOP_LEAKAGE_CANARY", "failed": failed}, indent=2) + "\n")
        raise SystemExit(f"CBEC leakage canary failed before fitting: {failed}")

    # Phase 2: paired 2x2 fit/emit/score, using the identical blocked cells and shared writer/emitter.
    rows = []
    grid_buf = np.zeros(ctx.foot.shape, dtype=np.float32)
    cells_path = out / "cells.jsonl"
    with cells_path.open("w") as sink:
        for fold in FOLD_IDS:
            for draw in DRAWS:
                cell = make_cell(ctx, h34, custom, fold, draw)
                _, Xtr, Xq, y, q_idx, fi_q, sl, dom_c, truth_c, known_c, d_vis_c, auc_idx, auc_y, canaries, meta = cell
                for arm in ARMS:
                    if arm == "CTRL_H35":
                        cols = np.arange(Xtr.shape[1] - len(NEW_FEATURES), dtype=np.int32)
                    elif arm == "COND_BASE":
                        cols = np.r_[np.arange(Xtr.shape[1] - len(NEW_FEATURES)), Xtr.shape[1] - 3]
                    elif arm == "GRAV_EDGE":
                        cols = np.r_[np.arange(Xtr.shape[1] - len(NEW_FEATURES)), Xtr.shape[1] - 2]
                    else:
                        cols = np.arange(Xtr.shape[1], dtype=np.int32)
                    p, fitmeta = fit_predict(Xtr[:, cols], y, Xq[:, cols], seed=draw)
                    auc = float(__import__("sklearn.metrics", fromlist=["roc_auc_score"]).roc_auc_score(auc_y, p[auc_idx]))
                    em, emeta = emit_sapd(grid_buf, fi_q, sl, dom_c, known_c, p)
                    row = eval_arm(
                        em, truth_c, dom_c, known_c, d_vis_c, auc, {},
                        {**meta, "arm": arm, "canary_max_auc": max(x["canary_auc"] for x in canaries.values()),
                         **fitmeta, **emeta},
                    )
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    rows.append(row)
                    print(f"{FOLDS[fold]} draw={draw} {arm}: HOLDOUT-DTI={row['dti']:.6f}; withheld={row['n_truth']}; canary_max={row['canary_max_auc']:.4f}", flush=True)
                    del p, em
                del cell

    result = pooled_summary(rows, candidate="CBEC", control="CTRL_H35", seed=261027)
    per_arm = {arm: result["arms"][arm] for arm in ARMS}
    summary = {
        "label": "HOLDOUT-DTI",
        "evaluator": EVALUATOR,
        "draws": list(DRAWS),
        "withheld_positive_occurrences": result["arms"]["CBEC"]["withheld_positive_occurrences"],
        "arms": per_arm,
        "cbec_vs_h35": {"paired_gain": result["paired_gain"], "ci95": result["paired_ci95"],
                         "fold_gains": result["fold_gains"], "screen_gate_passed": result["screen_passed"]},
        "canary_max": max(x["canary_auc"] for r in canary_rows for x in r["features"].values()),
        "canary_all_passed": not bool(failed),
        "ci_method": result["ci_method"],
        "elapsed_s": round(time.time() - t0, 1),
        "interpretation": "catalogue-gap holdout proxy; not an organizer score or leaderboard projection",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "status.json").write_text(json.dumps({"status": "SCREEN_COMPLETE", "gate_passed": result["screen_passed"]}, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
