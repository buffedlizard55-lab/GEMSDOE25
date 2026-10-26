#!/usr/bin/env python3
"""Pre-registered H71-1 HGPC DIRECT-emission holdout runner.

Frozen specification: ``knowledge/27_preregistered_h71_hgpc_2026-10-26.md``.
Writes ``design.json`` before any model fit. Refuses to overwrite an existing evidence dir.

    .venv/bin/python scripts/run_h71_experiments.py --exp h71_1 --draws 70 71 --out evidence/h71_1_screen
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.h34 import load_h34_sidecar  # noqa: E402
from gems25.h71 import H71_NAMES, load_h71_sidecar  # noqa: E402
from gems25.h71_akf import H71_AKF_NAMES, load_akf_sidecar  # noqa: E402
from gems25.h71_mag import H71_MAG_NAMES, load_mag_sidecar  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
KFRAC = 0.035
MIN_DIST = 3.0
MIN_DIST_H35 = 2.4
COLLAR_B2 = 2.0
LEAKAGE_AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px) via gems25.experiment.Cell.evaluate"


def canary_sidecar(cell: Cell, sidecar: np.ndarray, names: list[str]) -> dict[str, dict[str, float]]:
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    out: dict[str, dict[str, float]] = {}
    for j, nm in enumerate(names):
        v = np.nan_to_num(np.asarray(sidecar[j, cell.q], dtype=np.float64)[idx], nan=0.0)
        raw = float(roc_auc_score(y, v)) if np.unique(v).size > 1 else 0.5
        out[nm] = {"raw_auc": raw, "canary_auc": float(max(raw, 1.0 - raw))}
    return out


def emit_field(cell: Cell, score_q: np.ndarray, *, collar_px: float, min_dist: float) -> np.ndarray:
    k = int(round(KFRAC * cell.dom_c.sum()))
    g = cell._grid
    g[:] = 0
    g.ravel()[cell.ctx.fi[cell.q]] = np.nan_to_num(score_q, nan=0.0).astype(np.float32)
    s = g[cell.sl].copy()
    r = ridge_nms(s, cell.dom_c, 1.0)
    if collar_px > 0:
        far = distance_transform_edt(~cell.known_c) > float(collar_px)
    else:
        far = ~cell.known_c
    sc = np.where(r & far & cell.dom_c, s, 0.0)
    top = select_top_positive(sc, cell.dom_c, k)
    return score_ordered_dots(s, top, min_dist)


def fit_h35(cell: Cell, h34: np.ndarray, seed: int):
    cols = cell.ctx.columns(BASE) + cell.ctx.named(EXTRAS) + [cell.ctx.col["H27_tip"]]
    Xtr = np.hstack([cell.Xtr[:, cols], np.asarray(h34[:, cell.train_idx], dtype=np.float32).T])
    Xq = np.hstack([cell.Xq[:, cols], np.asarray(h34[:, cell.q], dtype=np.float32).T])
    t0 = time.time()
    m = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    t0 = time.time()
    p = m.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=round(t_fit, 3), predict_s=round(time.time() - t0, 3), n_features=int(Xtr.shape[1]))


def run_h71_1(draws: list[int], out: Path) -> None:
    design = dict(
        experiment="H71-1",
        hypothesis="DIRECT emission from signed gravity-basement half-graben polarity (H71_blind_hgpc), B=2 collar, sapd 3.0; no HGB, no Family E",
        preregistration="knowledge/27_preregistered_h71_hgpc_2026-10-26.md",
        draws=draws,
        folds=list(FOLD_IDS),
        kfrac=KFRAC,
        min_dist_primary=MIN_DIST,
        min_dist_h35_control=MIN_DIST_H35,
        collar_b2_px=COLLAR_B2,
        columns=H71_NAMES,
        arms=["CTRL_CREST_B2", "HGPC_BLIND_B2", "HGPC_SURF_B2", "CTRL_H35_24"],
        primary_arm="HGPC_BLIND_B2",
        controls=["CTRL_CREST_B2", "CTRL_H35_24"],
        evaluator=EVALUATOR,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010, mean_hug_increase_max=0.10),
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    ctx = load_context(work_dir())
    h71 = load_h71_sidecar(work_dir(), ctx.foot, ctx.fi, static=ctx.static, static_names=ctx.static_names)
    h34 = load_h34_sidecar(work_dir(), ctx.fi)
    name_idx = {n: i for i, n in enumerate(H71_NAMES)}

    t_all = time.time()
    with (out / "cells.jsonl").open("w") as sink:
        for fold in FOLD_IDS:
            for draw in draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = canary_sidecar(cell, h71, list(H71_NAMES))
                max_can = max(canary[n]["canary_auc"] for n in ("H71_blind_hgpc", "H71_surf_hgpc"))
                if max_can > LEAKAGE_AUC_CAP:
                    raise RuntimeError(f"LEAKAGE CANARY TRIGGERED H71-1 fold={fold} draw={draw}: {canary}")

                def row(arm: str, em: np.ndarray, extra: dict) -> dict:
                    ev = cell.evaluate(em)
                    rec = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                               feature_auc_canary=canary, **ev, **extra)
                    sink.write(json.dumps(rec) + "\n")
                    sink.flush()
                    return rec

                p_crest = np.asarray(h71[name_idx["H71_crest_ctrl"], cell.q], dtype=np.float32)
                em = emit_field(cell, p_crest, collar_px=COLLAR_B2, min_dist=MIN_DIST)
                row("CTRL_CREST_B2", em, dict(auc=cell.auc(p_crest), n_features=1, fit_s=0.0, predict_s=0.0))

                p_blind = np.asarray(h71[name_idx["H71_blind_hgpc"], cell.q], dtype=np.float32)
                em = emit_field(cell, p_blind, collar_px=COLLAR_B2, min_dist=MIN_DIST)
                row("HGPC_BLIND_B2", em, dict(auc=cell.auc(p_blind), n_features=1, fit_s=0.0, predict_s=0.0))

                p_surf = np.asarray(h71[name_idx["H71_surf_hgpc"], cell.q], dtype=np.float32)
                em = emit_field(cell, p_surf, collar_px=COLLAR_B2, min_dist=MIN_DIST)
                row("HGPC_SURF_B2", em, dict(auc=cell.auc(p_surf), n_features=1, fit_s=0.0, predict_s=0.0))

                p_h35, t_h35 = fit_h35(cell, h34, seed=draw)
                em = emit_field(cell, p_h35, collar_px=0.0, min_dist=MIN_DIST_H35)
                row("CTRL_H35_24", em, dict(auc=cell.auc(p_h35), **t_h35))
                print(f"  fold {FOLDS[fold]} draw {draw} done in {time.time() - t_all:.0f}s", flush=True)
    print(f"H71-1 complete in {time.time() - t_all:.0f}s -> {out}", flush=True)


def run_h71_2(draws: list[int], out: Path) -> None:
    design = dict(
        experiment="H71-3-AKF",
        hypothesis="DIRECT emission from aligned knickpoint / drainage-offset field (H71_akf_knick_align), B=2 collar, sapd 3.0; DEM hydrology only",
        preregistration="knowledge/27_preregistered_h71_hgpc_2026-10-26.md",
        draws=draws,
        folds=list(FOLD_IDS),
        kfrac=KFRAC,
        min_dist_primary=MIN_DIST,
        min_dist_h35_control=MIN_DIST_H35,
        collar_b2_px=COLLAR_B2,
        columns=list(H71_AKF_NAMES) + ["H71_crest_ctrl"],
        arms=["CTRL_CREST_B2", "AKF_B2", "CTRL_H35_24"],
        primary_arm="AKF_B2",
        controls=["CTRL_CREST_B2", "CTRL_H35_24"],
        evaluator=EVALUATOR,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010, mean_hug_increase_max=0.10),
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    ctx = load_context(work_dir())
    h71 = load_h71_sidecar(work_dir(), ctx.foot, ctx.fi, static=ctx.static, static_names=ctx.static_names)
    akf = load_akf_sidecar(work_dir(), ctx.foot, ctx.fi)
    h34 = load_h34_sidecar(work_dir(), ctx.fi)
    stacked = np.vstack([akf, h71[2:3]])  # AKF, crest
    stack_names = [H71_AKF_NAMES[0], "H71_crest_ctrl"]

    t_all = time.time()
    with (out / "cells.jsonl").open("w") as sink:
        for fold in FOLD_IDS:
            for draw in draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = canary_sidecar(cell, stacked, stack_names)
                if canary[H71_AKF_NAMES[0]]["canary_auc"] > LEAKAGE_AUC_CAP:
                    raise RuntimeError(f"LEAKAGE CANARY TRIGGERED H71-3 fold={fold} draw={draw}: {canary}")

                def row(arm: str, em: np.ndarray, extra: dict) -> None:
                    ev = cell.evaluate(em)
                    sink.write(json.dumps(dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                                               feature_auc_canary=canary, **ev, **extra)) + "\n")
                    sink.flush()

                p_crest = np.asarray(h71[2, cell.q], dtype=np.float32)
                row("CTRL_CREST_B2", emit_field(cell, p_crest, collar_px=COLLAR_B2, min_dist=MIN_DIST),
                    dict(auc=cell.auc(p_crest), n_features=1, fit_s=0.0, predict_s=0.0))
                p_akf = np.asarray(akf[0, cell.q], dtype=np.float32)
                row("AKF_B2", emit_field(cell, p_akf, collar_px=COLLAR_B2, min_dist=MIN_DIST),
                    dict(auc=cell.auc(p_akf), n_features=1, fit_s=0.0, predict_s=0.0))
                p_h35, t_h35 = fit_h35(cell, h34, seed=draw)
                row("CTRL_H35_24", emit_field(cell, p_h35, collar_px=0.0, min_dist=MIN_DIST_H35),
                    dict(auc=cell.auc(p_h35), **t_h35))
                print(f"  fold {FOLDS[fold]} draw {draw} done in {time.time() - t_all:.0f}s", flush=True)
    print(f"H71-3 AKF complete in {time.time() - t_all:.0f}s -> {out}", flush=True)


def run_h71_3(draws: list[int], out: Path) -> None:
    design = dict(
        experiment="H71-4-MAG",
        hypothesis="DIRECT emission from multi-scale structure-tensor persistence of shallow residual RTP, B=2 collar, sapd 3.0",
        preregistration="knowledge/27_preregistered_h71_hgpc_2026-10-26.md",
        draws=draws,
        folds=list(FOLD_IDS),
        kfrac=KFRAC,
        min_dist_primary=MIN_DIST,
        min_dist_h35_control=MIN_DIST_H35,
        collar_b2_px=COLLAR_B2,
        columns=list(H71_MAG_NAMES) + ["H71_crest_ctrl"],
        arms=["CTRL_CREST_B2", "MAG_ANISO_B2", "CTRL_H35_24"],
        primary_arm="MAG_ANISO_B2",
        controls=["CTRL_CREST_B2", "CTRL_H35_24"],
        evaluator=EVALUATOR,
        leakage_auc_cap=LEAKAGE_AUC_CAP,
        gate=dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010, mean_hug_increase_max=0.10),
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")
    ctx = load_context(work_dir())
    h71 = load_h71_sidecar(work_dir(), ctx.foot, ctx.fi, static=ctx.static, static_names=ctx.static_names)
    mag = load_mag_sidecar(work_dir(), ctx.foot, ctx.fi)
    h34 = load_h34_sidecar(work_dir(), ctx.fi)
    stacked = np.vstack([mag, h71[2:3]])
    stack_names = [H71_MAG_NAMES[0], "H71_crest_ctrl"]
    t_all = time.time()
    with (out / "cells.jsonl").open("w") as sink:
        for fold in FOLD_IDS:
            for draw in draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = canary_sidecar(cell, stacked, stack_names)
                if canary[H71_MAG_NAMES[0]]["canary_auc"] > LEAKAGE_AUC_CAP:
                    raise RuntimeError(f"LEAKAGE CANARY TRIGGERED H71-4 fold={fold} draw={draw}: {canary}")

                def row(arm: str, em: np.ndarray, extra: dict) -> None:
                    ev = cell.evaluate(em)
                    sink.write(json.dumps(dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                                               feature_auc_canary=canary, **ev, **extra)) + "\n")
                    sink.flush()

                p_crest = np.asarray(h71[2, cell.q], dtype=np.float32)
                row("CTRL_CREST_B2", emit_field(cell, p_crest, collar_px=COLLAR_B2, min_dist=MIN_DIST),
                    dict(auc=cell.auc(p_crest), n_features=1, fit_s=0.0, predict_s=0.0))
                p_mag = np.asarray(mag[0, cell.q], dtype=np.float32)
                row("MAG_ANISO_B2", emit_field(cell, p_mag, collar_px=COLLAR_B2, min_dist=MIN_DIST),
                    dict(auc=cell.auc(p_mag), n_features=1, fit_s=0.0, predict_s=0.0))
                p_h35, t_h35 = fit_h35(cell, h34, seed=draw)
                row("CTRL_H35_24", emit_field(cell, p_h35, collar_px=0.0, min_dist=MIN_DIST_H35),
                    dict(auc=cell.auc(p_h35), **t_h35))
                print(f"  fold {FOLDS[fold]} draw {draw} done in {time.time() - t_all:.0f}s", flush=True)
    print(f"H71-4 MAG complete in {time.time() - t_all:.0f}s -> {out}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp", default="h71_1", choices=["h71_1", "h71_2", "h71_3"])
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists() and (out / "cells.jsonl").exists():
        raise SystemExit(f"refusing to overwrite existing evidence at {out}")
    out.mkdir(parents=True, exist_ok=True)
    if args.exp == "h71_1":
        run_h71_1(list(args.draws), out)
    elif args.exp == "h71_2":
        run_h71_2(list(args.draws), out)
    elif args.exp == "h71_3":
        run_h71_3(list(args.draws), out)


if __name__ == "__main__":
    main()
