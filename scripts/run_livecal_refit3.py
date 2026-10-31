#!/usr/bin/env python3
"""Experiment 3a — refit the live-anchored truth model with a CAPPED detector dynamic range.

``knowledge/57`` selected ``step_dead+betapdf`` (LOO RMSE 0.0157) but its fitted detector response spans
a density ratio of ~1e73 between the best and worst detector bins.  A ratio that large is not defensible
from seventeen anchors and it produces a design that tries to put every dot in a few hundred pixels.
This script refits the three best families with the ratio capped at 1e2, 1e3 and 1e4 and re-scores them
by artefact-level leave-one-out RMSE, so the design is built on a model that is still the best
*predictor*, not on the most extreme one.

    python scripts/run_livecal_refit3.py        # writes evidence/livecal_refit3_2026-10-31.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25 import livecal, livecal_cells  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from run_livecal_refit2 import ANCHORS, N_LO, N_HI, SHAPE_BOUNDS, LINK_BOUNDS, cell_stats, make_starts  # noqa: E402

N_ZB = 200
N_CELL = livecal.N_BINS * N_ZB
COMBOS = [
    ("step_dead", "betapdf", 1e4, None),
    ("step_dead", "betapdf", 1e3, None),
    ("step_dead", "betapdf", 1e4, (1, 12.0)),   # dead zone limited to 1.2 km: physically plausible variant
    ("exp_dead", "betapdf", 1e4, None),
    ("uniform", "betapdf", 1e4, None),
]


def main() -> int:
    t0 = time.time()
    d, w = data_dir(), work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    z = np.load(w / "refdet_z.npy")
    d_cat = distance_transform_edt(~lab)
    code, reps, q = livecal_cells.cell_code(d_cat, foot, lab, z, N_ZB)
    nb = np.bincount(code[code >= 0].ravel(), minlength=N_CELL).astype(float)

    rows, ids, scores = [], [], []
    for aid, rel, score, role in ANCHORS:
        rows.append(cell_stats(d / rel, code, foot, lab))
        ids.append(aid)
        scores.append(score)
        print(f"  {aid:>20} dots={rows[-1]['positives']:>7,} score={score}", flush=True)
    scores = np.asarray(scores, dtype=float)

    def fit(use_rows, use_scores, model, link, ratio, starts):
        k = livecal.MODEL_PARAMS[model]
        slo, shi = SHAPE_BOUNDS[model]
        glo, ghi = LINK_BOUNDS[link]
        lo = np.array([N_LO] + list(slo) + list(glo), dtype=float)
        hi = np.array([N_HI] + list(shi) + list(ghi), dtype=float)

        def loss(th):
            th = np.clip(th, lo, hi)
            _, ww = livecal_cells.cell_weights(th, model, reps, q, link, k, ratio)
            if not np.isfinite(ww).all() or float(ww @ nb) <= 0:
                return 1e6
            return float(np.mean((livecal_cells.predict(use_rows, ww, nb, float(th[0])) - use_scores) ** 2))

        best, bfun = None, np.inf
        for s in starts:
            res = minimize(loss, np.clip(np.asarray(s, dtype=float), lo, hi), method="Nelder-Mead",
                           options=dict(maxiter=900, maxfev=1800, xatol=1e-7, fatol=1e-14))
            if res.fun < bfun:
                best, bfun = res, float(res.fun)
        th = np.clip(best.x, lo, hi)
        n_truth, ww = livecal_cells.cell_weights(th, model, reps, q, link, k, ratio)
        return dict(model=model, link=link, ratio=ratio, theta=th.tolist(), n_truth=n_truth,
                    rmse=float(np.sqrt(bfun)),
                    pred=livecal_cells.predict(use_rows, ww, nb, n_truth).tolist())

    results = {}
    for model, link, ratio, rcap in COMBOS:
        if rcap is not None:
            SHAPE_BOUNDS["step_dead"] = ([0.0, float(rcap[0])], [1.0, float(rcap[1])])
        else:
            SHAPE_BOUNDS["step_dead"] = ([0.0, 0.0], [1.0, 60.0])
        starts = make_starts(model, link)
        r = fit(rows, scores, model, link, ratio, starts)
        r["dead_zone_cap_px"] = None if rcap is None else float(rcap[1])
        loo = np.empty(len(rows))
        for i in range(len(rows)):
            keep = [r2 for j, r2 in enumerate(rows) if j != i]
            f = fit(keep, np.delete(scores, i), model, link, ratio, starts)
            _, ww = livecal_cells.cell_weights(np.array(f["theta"]), model, reps, q, link,
                                               livecal.MODEL_PARAMS[model], ratio)
            loo[i] = livecal_cells.predict([rows[i]], ww, nb, f["n_truth"])[0]
        r["loo_pred"] = loo.tolist()
        r["loo_rmse"] = float(np.sqrt(np.mean((loo - scores) ** 2)))
        r["loo_max_abs"] = float(np.max(np.abs(loo - scores)))
        key = f"{model}+{link}+r{ratio:g}" + (f"+dzcap{rcap[1]:g}" if rcap else "")
        results[key] = r
        print(f"{key:>28} rmse={r['rmse']:.4f} loo={r['loo_rmse']:.4f} N={r['n_truth']:>7.0f} "
              f"theta={[round(x, 3) for x in r['theta'][1:]]} "
              f"B2={loo[ids.index('GEMSDOE32-B2')]:.4f} lat={loo[ids.index('lattice-s5')]:.4f}", flush=True)

    order = sorted(results, key=lambda kk: (results[kk]["loo_rmse"], -len(kk)))
    best = results[order[0]]
    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        script="scripts/run_livecal_refit3.py",
        reason="knowledge/57 winner had a detector density range of ~1e73; capped refits",
        evidence_class="COMPUTED; anchors are OWNER-REPORTED scores, no ORGANIZER-CONFIRMED receipt exists",
        anchor_ids=ids, anchor_scores=scores.tolist(),
        results={kk: {k2: v2 for k2, v2 in v.items() if k2 != "pred"} for kk, v in results.items()},
        ranking=order, best_model=order[0],
        best=dict(**{k: v for k, v in best.items() if k not in ("pred", "loo_pred")},
                  loo_pred=dict(zip(ids, best["loo_pred"]))),
        gates=dict(
            G1_estimator_usable=bool(best["loo_rmse"] <= 0.030
                                     and abs(best["loo_pred"][ids.index("GEMSDOE32-B2")] - 0.2778) <= 0.040),
            G2_lattice_transfer=bool(abs(best["loo_pred"][ids.index("lattice-s5")] - 0.0904) <= 0.030),
        ),
        seconds=round(time.time() - t0, 1),
    )
    (ROOT / "evidence" / "livecal_refit3_2026-10-31.json").write_text(json.dumps(out, indent=1) + "\n")
    print("\nbest:", order[0], "loo_rmse=%.4f" % best["loo_rmse"], "gates:", out["gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
