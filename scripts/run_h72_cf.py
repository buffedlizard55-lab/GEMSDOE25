#!/usr/bin/env python3
"""Run the pre-registered H72 (MBSP-MTG x DEBIAS) 2x2 factorial holdout experiment.

Pre-registered in ``knowledge/29_h72_cf_hypotheses_and_preregistration_2026-10-26.md``
(committed at ``2750fe9`` before feature implementation or fitting).

Arms evaluated on the exact same holdout cells (no comparator drift):
* ``G0_D0``: Exact same-run H35 champion control (``BDE+7 + H27_tip + H34``, unclamped E, ``sapd2.4``).
* ``G1_D0``: ``H35 + H72`` (6 catalogue-free MBSP-MTG cols), unclamped E, ``sapd2.4``.
* ``G0_D1``: ``H35`` features with training+test short-range catalogue-proximity censoring
             (``E_dist >= 15 px``, ``E_dens5`` dropped) + ``B2-Tip`` 37,654-dot greedy 300 m tent allocation.
* ``G1_D1``: ``H35 + H72`` with training+test short-range catalogue-proximity censoring +
             ``B2-Tip`` 37,654-dot greedy 300 m tent allocation.

Evaluates both pre-registered instruments in one pass:
* Instrument A1: Standard full buffered ``HOLDOUT-DTI`` (``d_vis > 0``, ``Cell.evaluate``).
* Instrument A2: Off-flank blind discovery ``HOLDOUT-DTI`` (``d_vis > 10 px`` = ``> 1 km`` from visible).
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import t as student_t
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import HGB_PARAMS, Cell, load_context  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h72_cf import CENSOR_MIN_DIST_PX, H72_NAMES, emit_debiased_b2_greedy, load_h72_sidecar  # noqa: E402
from gems25.metric import ALPHA, BETA, dti_binary  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from gems25.validation import feature_canary  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402

FOLD_IDS = (0, 1, 2, 3)
ARMS = ("G0_D0", "G1_D0", "G0_D1", "G1_D1")
CATFREE_ARMS = ("G0_D0", "CF_G0", "CF_G1")
CATFREE_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm", "X3_gd")
D0_KFRAC = 0.035
D0_MIN_DIST = 2.4
OFF_FLANK_PX = 10.0
LEAKAGE_AUC_CAP = 0.90
PRED_CHUNK = 350_000
EVALUATOR_ID = "gems25.holdout.v1.2-buffered-4quad-pooled-dti"


def _fit_predict_arm(
    cell: Cell,
    base_cols: list[int],
    side_tr: np.ndarray,
    side_q: np.ndarray,
    *,
    censor_e_dist_pos: int | None,
    seed: int,
) -> tuple[np.ndarray, dict]:
    t0 = time.time()
    x_tr_base = np.array(cell.Xtr[:, base_cols], dtype=np.float32, copy=True)
    if censor_e_dist_pos is not None:
        x_tr_base[:, censor_e_dist_pos] = np.maximum(
            x_tr_base[:, censor_e_dist_pos], np.float32(np.log1p(CENSOR_MIN_DIST_PX))
        )
    x_tr = np.hstack([x_tr_base, side_tr])
    del x_tr_base
    model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(x_tr, cell.y)
    del x_tr
    t_fit = time.time() - t0

    t1 = time.time()
    n_q = cell.Xq.shape[0]
    preds = np.empty(n_q, dtype=np.float32)
    for lo in range(0, n_q, PRED_CHUNK):
        hi = min(lo + PRED_CHUNK, n_q)
        xb = np.array(cell.Xq[lo:hi, base_cols], dtype=np.float32, copy=True)
        if censor_e_dist_pos is not None:
            xb[:, censor_e_dist_pos] = np.maximum(
                xb[:, censor_e_dist_pos], np.float32(np.log1p(CENSOR_MIN_DIST_PX))
            )
        xq = np.hstack([xb, side_q[lo:hi]])
        preds[lo:hi] = model.predict_proba(xq)[:, 1].astype(np.float32)
        del xb, xq
    t_pred = time.time() - t1
    del model
    return preds, dict(fit_s=round(t_fit, 2), predict_s=round(t_pred, 2))


def _fold_ci95(fold_vals: list[float]) -> tuple[float, list[float]]:
    arr = np.asarray(fold_vals, dtype=np.float64)
    mean = float(arr.mean())
    if arr.size < 2:
        return mean, [mean, mean]
    se = float(arr.std(ddof=1) / np.sqrt(arr.size))
    crit = float(student_t.ppf(0.975, df=arr.size - 1))
    return mean, [float(mean - crit * se), float(mean + crit * se)]


def _pooled_dti(rows: list[dict], tp_key: str = "tp", fp_key: str = "fp", n_key: str = "n_truth") -> float:
    tp = sum(float(r[tp_key]) for r in rows)
    fp = sum(float(r[fp_key]) for r in rows)
    nt = sum(float(r[n_key]) for r in rows)
    denom = ALPHA * (tp + fp) + BETA * nt
    return float(tp / denom) if denom > 0 else 0.0


def analyze_cells(
    rows: list[dict],
    canary_rows: list[dict],
    stage: str,
    draws: list[int],
    mode: str = "factorial",
) -> dict:
    arm_list = CATFREE_ARMS if mode == "catfree" else ARMS
    by_arm: dict[str, dict] = {}
    for arm in arm_list:
        ar = [r for r in rows if r["arm"] == arm]
        fold_std = [float(np.mean([r["dti"] for r in ar if r["fold"] == f])) for f in FOLD_IDS]
        fold_off = [float(np.mean([r["dti_off10"] for r in ar if r["fold"] == f])) for f in FOLD_IDS]
        mean_std, ci_std = _fold_ci95(fold_std)
        mean_off, ci_off = _fold_ci95(fold_off)
        by_arm[arm] = dict(
            pooled_dti=_pooled_dti(ar, "tp", "fp", "n_truth"),
            fold_mean_dti=mean_std,
            fold_ci95_dti=ci_std,
            per_fold_dti={FOLDS[f]: fold_std[f] for f in FOLD_IDS},
            withheld_positives_total=int(sum(r["n_truth"] for r in ar)),
            pooled_dti_off10=_pooled_dti(ar, "tp_off10", "fp_off10", "n_truth_off10"),
            fold_mean_dti_off10=mean_off,
            fold_ci95_dti_off10=ci_off,
            per_fold_dti_off10={FOLDS[f]: fold_off[f] for f in FOLD_IDS},
            withheld_positives_off10_total=int(sum(r["n_truth_off10"] for r in ar)),
            mean_emitted=float(np.mean([r["emitted"] for r in ar])),
            mean_hug_3px=float(np.mean([r["hug"] for r in ar])),
            mean_share_d_le_10=float(np.mean([r["share_d_le_10"] for r in ar])),
            mean_med_d_vis=float(np.mean([r["med_d_vis"] for r in ar])),
            mean_auc=float(np.mean([r["auc"] for r in ar])),
        )

    def _contrast(metric_key: str, fn) -> dict:
        fvals = []
        for f in FOLD_IDS:
            sub_draws = sorted({r["draw"] for r in rows if r["fold"] == f})
            dvals = []
            for d in sub_draws:
                m = {r["arm"]: r[metric_key] for r in rows if r["fold"] == f and r["draw"] == d}
                dvals.append(float(fn(m)))
            fvals.append(float(np.mean(dvals)))
        mean, ci = _fold_ci95(fvals)
        return dict(
            mean=mean,
            ci95=ci,
            folds_positive=int(sum(x > 0 for x in fvals)),
            worst_fold=float(min(fvals)),
            per_fold={FOLDS[f]: fvals[f] for f in FOLD_IDS},
        )

    max_by_feat = {}
    for nm in H72_NAMES:
        sub = [c for c in canary_rows if c["feature"] == nm]
        max_by_feat[nm] = dict(
            max_canary_auc=float(max(c["canary_auc"] for c in sub)),
            max_missingness_auc=float(max(c["missingness_auc"] for c in sub)),
            all_passed=bool(all(c["passed"] for c in sub)),
        )
    canary_passed = bool(all(v["all_passed"] for v in max_by_feat.values()))

    if mode == "catfree":
        contrasts_std = dict(
            CFG1_vs_CFG0=_contrast("dti", lambda m: m["CF_G1"] - m["CF_G0"]),
            CFG1_vs_G0D0=_contrast("dti", lambda m: m["CF_G1"] - m["G0_D0"]),
            CFG0_vs_G0D0=_contrast("dti", lambda m: m["CF_G0"] - m["G0_D0"]),
        )
        contrasts_off10 = dict(
            CFG1_vs_CFG0=_contrast("dti_off10", lambda m: m["CF_G1"] - m["CF_G0"]),
            CFG1_vs_G0D0=_contrast("dti_off10", lambda m: m["CF_G1"] - m["G0_D0"]),
            CFG0_vs_G0D0=_contrast("dti_off10", lambda m: m["CF_G0"] - m["G0_D0"]),
        )
        c_cf = contrasts_std["CFG1_vs_CFG0"]
        c_cf_off = contrasts_off10["CFG1_vs_CFG0"]
        gate_cf = bool(
            canary_passed
            and c_cf["mean"] >= 0.0010
            and c_cf["folds_positive"] >= 3
            and c_cf["worst_fold"] >= -0.0050
        )
        return dict(
            stage=stage,
            mode=mode,
            evaluator=EVALUATOR_ID,
            draws=draws,
            leakage_canary=dict(passed=canary_passed, cap=LEAKAGE_AUC_CAP, max_by_feature=max_by_feat),
            arms=by_arm,
            contrasts_standard_holdout=contrasts_std,
            contrasts_off_flank_gt10px=contrasts_off10,
            gates=dict(
                S_catfree_CFG1_vs_CFG0=dict(passed=gate_cf, detail_std=c_cf, detail_off10=c_cf_off),
            ),
        )

    contrasts_std = dict(
        G1D0_vs_G0D0=_contrast("dti", lambda m: m["G1_D0"] - m["G0_D0"]),
        G1D1_vs_G0D0=_contrast("dti", lambda m: m["G1_D1"] - m["G0_D0"]),
        G1D1_vs_G0D1=_contrast("dti", lambda m: m["G1_D1"] - m["G0_D1"]),
        G_main=_contrast("dti", lambda m: 0.5 * ((m["G1_D0"] - m["G0_D0"]) + (m["G1_D1"] - m["G0_D1"]))),
        D_main=_contrast("dti", lambda m: 0.5 * ((m["G0_D1"] - m["G0_D0"]) + (m["G1_D1"] - m["G1_D0"]))),
        G_x_D=_contrast("dti", lambda m: 0.5 * ((m["G1_D1"] - m["G0_D1"]) - (m["G1_D0"] - m["G0_D0"]))),
    )
    contrasts_off10 = dict(
        G1D0_vs_G0D0=_contrast("dti_off10", lambda m: m["G1_D0"] - m["G0_D0"]),
        G1D1_vs_G0D0=_contrast("dti_off10", lambda m: m["G1_D1"] - m["G0_D0"]),
        G1D1_vs_G0D1=_contrast("dti_off10", lambda m: m["G1_D1"] - m["G0_D1"]),
        G_main=_contrast("dti_off10", lambda m: 0.5 * ((m["G1_D0"] - m["G0_D0"]) + (m["G1_D1"] - m["G0_D1"]))),
        D_main=_contrast("dti_off10", lambda m: 0.5 * ((m["G0_D1"] - m["G0_D0"]) + (m["G1_D1"] - m["G1_D0"]))),
        G_x_D=_contrast("dti_off10", lambda m: 0.5 * ((m["G1_D1"] - m["G0_D1"]) - (m["G1_D0"] - m["G0_D0"]))),
    )

    c_std = contrasts_std["G1D0_vs_G0D0"]
    gate_s_std = bool(
        canary_passed
        and c_std["mean"] >= 0.0010
        and c_std["folds_positive"] >= 3
        and c_std["worst_fold"] >= -0.0050
    )
    c_off_vs_h35 = contrasts_off10["G1D1_vs_G0D0"]
    c_off_vs_d1 = contrasts_off10["G1D1_vs_G0D1"]
    gate_s_off10 = bool(
        canary_passed
        and c_off_vs_h35["mean"] > 0.0020
        and c_off_vs_h35["folds_positive"] >= 3
        and c_off_vs_d1["mean"] > 0.0005
        and c_off_vs_d1["folds_positive"] >= 3
    )

    return dict(
        stage=stage,
        mode=mode,
        evaluator=EVALUATOR_ID,
        draws=draws,
        leakage_canary=dict(passed=canary_passed, cap=LEAKAGE_AUC_CAP, max_by_feature=max_by_feat),
        arms=by_arm,
        contrasts_standard_holdout=contrasts_std,
        contrasts_off_flank_gt10px=contrasts_off10,
        gates=dict(
            S_std_G1D0_vs_H35=dict(passed=gate_s_std, detail=c_std),
            S_off10_G1D1_discovery=dict(
                passed=gate_s_off10,
                vs_H35=c_off_vs_h35,
                vs_G0D1=c_off_vs_d1,
            ),
        ),
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, nargs="+", required=True)
    ap.add_argument("--stage", default="screen")
    ap.add_argument("--mode", choices=["factorial", "catfree"], default="factorial")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cells_path = out / "cells.jsonl"
    canary_path = out / "canary.jsonl"
    analysis_path = out / "analysis.json"
    if cells_path.exists() or analysis_path.exists():
        raise SystemExit(f"Refusing to overwrite existing evidence in {out}")

    t_start = time.time()
    work, ext_dir = work_dir(), data_dir() / "external"
    ctx = load_context(work)
    h34 = load_h34_sidecar(work, ctx.fi)
    h72 = load_h72_sidecar(work, ext_dir, ctx.foot, ctx.fi)

    base_d0 = ctx.columns(BASE) + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    base_cf = ctx.columns("ABCD") + ctx.named(CATFREE_EXTRAS)
    e_dens5_idx = ctx.col["E_dens5"]
    e_dist_idx = ctx.col["E_dist"]
    base_d1 = [c for c in base_d0 if c != e_dens5_idx]
    censor_pos_d1 = base_d1.index(e_dist_idx)

    rows: list[dict] = []
    canary_rows: list[dict] = []

    with cells_path.open("w") as f_cells, canary_path.open("w") as f_can:
        for fold in FOLD_IDS:
            for draw in args.draws:
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                # 1. Standalone leakage canary on all 6 H72 columns
                eval_q_idx = np.concatenate([cell.auc_pos, cell.auc_neg])
                y_can = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
                h34_q = np.asarray(h34[:, cell.q], dtype=np.float32).T
                h72_q = np.asarray(h72[:, cell.q], dtype=np.float32).T
                h34_tr = np.asarray(h34[:, cell.train_idx], dtype=np.float32).T
                h72_tr = np.asarray(h72[:, cell.train_idx], dtype=np.float32).T

                for j, nm in enumerate(H72_NAMES):
                    rec = feature_canary(h72_q[eval_q_idx, j], y_can, cap=LEAKAGE_AUC_CAP)
                    crow = dict(
                        fold=fold,
                        fold_name=FOLDS[fold],
                        draw=draw,
                        feature=nm,
                        raw_auc=rec["auc"],
                        canary_auc=rec["canary_auc"],
                        missingness_auc=rec["missingness_auc"],
                        passed=bool(rec["passed"]),
                    )
                    canary_rows.append(crow)
                    f_can.write(json.dumps(crow) + "\n")
                    if not crow["passed"]:
                        raise RuntimeError(f"LEAKAGE CANARY FAILED on {nm}: {crow}")
                f_can.flush()

                side_g0_tr = h34_tr
                side_g0_q = h34_q
                side_g1_tr = np.hstack([h34_tr, h72_tr])
                side_g1_q = np.hstack([h34_q, h72_q])

                dv = distance_transform_edt(~cell.known_c)
                off10 = dv > OFF_FLANK_PX

                if args.mode == "catfree":
                    arm_specs = [
                        ("G0_D0", base_d0, side_g0_tr, side_g0_q, None, False),
                        ("CF_G0", base_cf, side_g0_tr, side_g0_q, None, False),
                        ("CF_G1", base_cf, side_g1_tr, side_g1_q, None, False),
                    ]
                else:
                    arm_specs = [
                        ("G0_D0", base_d0, side_g0_tr, side_g0_q, None, False),
                        ("G1_D0", base_d0, side_g1_tr, side_g1_q, None, False),
                        ("G0_D1", base_d1, side_g0_tr, side_g0_q, censor_pos_d1, True),
                        ("G1_D1", base_d1, side_g1_tr, side_g1_q, censor_pos_d1, True),
                    ]

                for arm_name, bcols, str_m, sq_m, cpos, is_d1 in arm_specs:
                    p, timing = _fit_predict_arm(
                        cell, bcols, str_m, sq_m, censor_e_dist_pos=cpos, seed=draw
                    )
                    auc_val = cell.auc(p)
                    t_em = time.time()
                    if not is_d1:
                        k_d0 = int(round(D0_KFRAC * cell.dom_c.sum()))
                        s_crop, top = cell.candidates(p, k_d0)
                        em = score_ordered_dots(s_crop, top, D0_MIN_DIST)
                        emit_diag = dict(mode="sapd2.4", emit_s=round(time.time() - t_em, 2))
                    else:
                        g = cell._grid
                        g[:] = 0.0
                        g.ravel()[cell.ctx.fi[cell.q]] = np.nan_to_num(p, nan=0.0).astype(np.float32)
                        s_crop = g[cell.sl].copy()
                        g[:] = 0.0
                        em, ddiag = emit_debiased_b2_greedy(
                            s_crop, cell.dom_c, cell.known_c, cell.tip_c
                        )
                        emit_diag = dict(
                            mode="debiased_b2_greedy",
                            emit_s=round(time.time() - t_em, 2),
                            spaced_pool=ddiag["spaced_pool"],
                            stop_reason=ddiag["greedy"].get("stop_reason"),
                        )

                    assert not (em & cell.known_c).any(), f"{arm_name} emitted on known catalogue"
                    ev_std = cell.evaluate(em)
                    ev_off = dti_binary(
                        em & off10, cell.truth_c & off10, valid=cell.dom_c & off10
                    )
                    d_em = dv[em]
                    share_le_10 = float((d_em <= 10.0).mean()) if d_em.size else 0.0
                    med_d = float(np.median(d_em)) if d_em.size else 0.0

                    row = dict(
                        fold=fold,
                        fold_name=FOLDS[fold],
                        draw=draw,
                        arm=arm_name,
                        auc=auc_val,
                        **ev_std,
                        dti_off10=ev_off["dti"],
                        tp_off10=ev_off["tp"],
                        fp_off10=ev_off["fp"],
                        n_truth_off10=ev_off["n_truth"],
                        emitted_off10=int((em & off10).sum()),
                        share_d_le_10=share_le_10,
                        med_d_vis=med_d,
                        **timing,
                        **emit_diag,
                    )
                    rows.append(row)
                    f_cells.write(json.dumps(row) + "\n")
                    f_cells.flush()
                    print(
                        f"[{time.time() - t_start:5.1f}s] {FOLDS[fold]} d={draw} {arm_name}: "
                        f"STD_DTI={row['dti']:.5f} | OFF10_DTI={row['dti_off10']:.5f} | "
                        f"emit={row['emitted']:5d} (d<=10:{share_le_10:.3f}, med_d:{med_d:.1f}) | "
                        f"hug={row['hug']:.3f} | auc={auc_val:.4f}",
                        flush=True,
                    )
                    del p, s_crop, em

                del cell, h34_q, h72_q, h34_tr, h72_tr, side_g1_tr, side_g1_q
                gc.collect()

    summary = analyze_cells(rows, canary_rows, args.stage, list(args.draws), mode=args.mode)
    summary["runtime_seconds"] = round(time.time() - t_start, 2)
    summary["h34_columns"] = H34_NAMES
    summary["h72_columns"] = H72_NAMES
    analysis_path.write_text(json.dumps(summary, indent=1) + "\n")
    print(f"\n=== {args.stage.upper()} SUMMARY ({summary['runtime_seconds']}s) ===", flush=True)
    print(json.dumps(summary["gates"], indent=2), flush=True)


if __name__ == "__main__":
    main()
