#!/usr/bin/env python3
"""Pre-registered APFL holdout runner (knowledge/29, committed before any fit).

Exp 1 (``--exp direct``): APFL-DIRECT B2 vs same-run H35 control vs B_crest floor.
Exp 2 (``--exp hgb``):    H35 + APFL columns (HGB) vs same-run H35 control;
                          plus descriptive B2-collar re-emissions (OCEM, no new fit)
                          and off-catalogue restricted scoring (``dti_offcat2``).

    .venv/bin/python scripts/run_apfl_experiments.py --exp direct --draws 60 61 --out evidence/apfl_direct_screen
    .venv/bin/python scripts/run_apfl_experiments.py --exp hgb    --draws 62 63 --out evidence/apfl_hgb_screen

Refuses to overwrite an existing evidence dir. Every DTI is HOLDOUT-DTI only.
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

from gems25.apfl import APFL_NAMES, load_apfl_sidecar  # noqa: E402
from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.h34 import load_h34_sidecar  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
KFRAC = 0.035
MIN_DIST_DIRECT = 3.0
MIN_DIST_H35 = 2.4
COLLAR_B2 = 2.0
LEAKAGE_AUC_CAP = 0.90
EVALUATOR = "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px) via gems25.experiment.Cell.evaluate"
GATE = dict(mean_gain_gt=0.001, folds_positive_min=3, worst_fold_min=-0.010, mean_hug_increase_max=0.10)


def canary_sidecar(cell: Cell, sidecar: np.ndarray, names: list[str]) -> dict[str, dict[str, float]]:
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    out: dict[str, dict[str, float]] = {}
    for j, nm in enumerate(names):
        v = np.nan_to_num(np.asarray(sidecar[j, cell.q], dtype=np.float64)[idx], nan=0.0)
        raw = float(roc_auc_score(y, v)) if np.unique(v).size > 1 else 0.5
        miss = (~np.isfinite(np.asarray(sidecar[j, cell.q], dtype=np.float64)[idx])).astype(float)
        mauc = float(roc_auc_score(y, miss)) if np.unique(miss).size > 1 else 0.5
        out[nm] = {"raw_auc": raw, "canary_auc": float(max(raw, 1.0 - raw, mauc, 1.0 - mauc))}
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


def offcat2_dti(cell: Cell, emitted_c: np.ndarray) -> float:
    """Descriptive OCEM score: truth restricted to hidden pixels >=2 px from visible catalogue."""
    far_truth = cell.truth_c & (distance_transform_edt(~cell.known_c) >= 2.0)
    if not far_truth.any():
        return float("nan")
    return float(dti_binary(emitted_c, far_truth, valid=cell.dom_c, known=cell.known_c)["dti"])


def fit_hgb(cell: Cell, h34: np.ndarray, apfl: np.ndarray | None, seed: int):
    cols = cell.ctx.columns(BASE) + cell.ctx.named(EXTRAS) + [cell.ctx.col["H27_tip"]]
    blocks_tr = [cell.Xtr[:, cols], np.asarray(h34[:, cell.train_idx], dtype=np.float32).T]
    blocks_q = [cell.Xq[:, cols], np.asarray(h34[:, cell.q], dtype=np.float32).T]
    if apfl is not None:
        blocks_tr.append(np.asarray(apfl[:, cell.train_idx], dtype=np.float32).T)
        blocks_q.append(np.asarray(apfl[:, cell.q], dtype=np.float32).T)
    Xtr = np.hstack(blocks_tr)
    Xq = np.hstack(blocks_q)
    t0 = time.time()
    m = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(Xtr, cell.y)
    t_fit = time.time() - t0
    t0 = time.time()
    p = m.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
    return p, dict(fit_s=round(t_fit, 3), predict_s=round(time.time() - t0, 3), n_features=int(Xtr.shape[1]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp", required=True, choices=["direct", "hgb"])
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if (out / "cells.jsonl").exists() or (out / "design.json").exists():
        raise SystemExit(f"refusing to overwrite {out}; choose a fresh --out")
    out.mkdir(parents=True, exist_ok=True)

    if a.exp == "direct":
        arms = ["CTRL_CREST_B2", "APFL_DIRECT_B2", "CTRL_H35_24"]
        primary, controls = "APFL_DIRECT_B2", ["CTRL_CREST_B2", "CTRL_H35_24"]
        hyp = "DIRECT emission from reconstructed APFL piedmont-flexure product, B=2 collar, sapd 3.0; no HGB"
    else:
        arms = ["CTRL_H35_24", "H35_PLUS_APFL", "CTRL_H35_B2", "H35_PLUS_APFL_B2"]
        primary, controls = "H35_PLUS_APFL", ["CTRL_H35_24"]
        hyp = "H35 HGB + 7 APFL columns, sapd 2.4; B2 arms are descriptive OCEM re-emissions (no new fit)"
    design = dict(
        experiment=f"APFL-{a.exp.upper()}", hypothesis=hyp,
        preregistration="knowledge/29_preregistered_apfl_completion_2026-10-26.md",
        reconstruction_note="APFL re-implemented in src/gems25/apfl.py from the frozen knowledge/27 formula; original builder absent from repo",
        draws=a.draws, folds=list(FOLD_IDS), kfrac=KFRAC,
        min_dist_direct=MIN_DIST_DIRECT, min_dist_h35=MIN_DIST_H35, collar_b2_px=COLLAR_B2,
        columns=list(APFL_NAMES), arms=arms, primary_arm=primary, controls=controls,
        base=BASE, extras=EXTRAS, evaluator=EVALUATOR, leakage_auc_cap=LEAKAGE_AUC_CAP, gate=GATE,
    )
    (out / "design.json").write_text(json.dumps(design, indent=1) + "\n")

    ctx = load_context(work_dir())
    apfl = load_apfl_sidecar(work_dir(), ctx.static, ctx.static_names)
    h34 = load_h34_sidecar(work_dir(), ctx.fi)
    prod_j = APFL_NAMES.index("APFL_product")
    crest_j = APFL_NAMES.index("APFL_crest")

    t_all = time.time()
    with (out / "cells.jsonl").open("w") as sink:
        for fold in FOLD_IDS:
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                canary = canary_sidecar(cell, apfl, list(APFL_NAMES))
                max_can = max(v["canary_auc"] for v in canary.values())
                if max_can > LEAKAGE_AUC_CAP:
                    raise RuntimeError(f"LEAKAGE CANARY TRIGGERED APFL-{a.exp} fold={fold} draw={draw}: {canary}")

                def row(arm: str, em: np.ndarray, extra: dict) -> None:
                    ev = cell.evaluate(em)
                    ev["dti_offcat2"] = offcat2_dti(cell, em)
                    sink.write(json.dumps(dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=arm,
                                               feature_auc_canary=canary, **ev, **extra)) + "\n")
                    sink.flush()

                if a.exp == "direct":
                    p_crest = np.asarray(apfl[crest_j, cell.q], dtype=np.float32)
                    row("CTRL_CREST_B2", emit_field(cell, p_crest, collar_px=COLLAR_B2, min_dist=MIN_DIST_DIRECT),
                        dict(auc=cell.auc(p_crest), n_features=1, fit_s=0.0, predict_s=0.0))
                    p_apfl = np.asarray(apfl[prod_j, cell.q], dtype=np.float32)
                    row("APFL_DIRECT_B2", emit_field(cell, p_apfl, collar_px=COLLAR_B2, min_dist=MIN_DIST_DIRECT),
                        dict(auc=cell.auc(p_apfl), n_features=1, fit_s=0.0, predict_s=0.0))
                    p_h35, t_h35 = fit_hgb(cell, h34, None, seed=draw)
                    row("CTRL_H35_24", emit_field(cell, p_h35, collar_px=0.0, min_dist=MIN_DIST_H35),
                        dict(auc=cell.auc(p_h35), **t_h35))
                else:
                    p_h35, t_h35 = fit_hgb(cell, h34, None, seed=draw)
                    row("CTRL_H35_24", emit_field(cell, p_h35, collar_px=0.0, min_dist=MIN_DIST_H35),
                        dict(auc=cell.auc(p_h35), **t_h35))
                    row("CTRL_H35_B2", emit_field(cell, p_h35, collar_px=COLLAR_B2, min_dist=MIN_DIST_H35),
                        dict(auc=cell.auc(p_h35), **t_h35, descriptive_ocem=True))
                    p_new, t_new = fit_hgb(cell, h34, apfl, seed=draw)
                    row("H35_PLUS_APFL", emit_field(cell, p_new, collar_px=0.0, min_dist=MIN_DIST_H35),
                        dict(auc=cell.auc(p_new), **t_new))
                    row("H35_PLUS_APFL_B2", emit_field(cell, p_new, collar_px=COLLAR_B2, min_dist=MIN_DIST_H35),
                        dict(auc=cell.auc(p_new), **t_new, descriptive_ocem=True))
                print(f"  fold {FOLDS[fold]} draw {draw} done in {time.time() - t_all:.0f}s (canary_max={max_can:.3f})", flush=True)
                del cell
    print(f"APFL-{a.exp} complete in {time.time() - t_all:.0f}s -> {out}", flush=True)


if __name__ == "__main__":
    main()
