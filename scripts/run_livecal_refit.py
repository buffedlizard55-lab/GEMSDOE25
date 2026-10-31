#!/usr/bin/env python3
"""Experiment 1 of ``knowledge/56`` — refit the live-anchored truth intensity on distance x detector cells.

For every byte-pinned artefact with an owner-reported DTI the script stores, per covariate cell,
the kernel-max mass ``ta`` (drives TP), the kernel-sum mass ``ua`` (drives the FP credit) and the
emitted mass ``ne`` (drives the FP cost).  A truth model

    pi(cell)  ∝  f(d_bin) · exp(beta · s_bin),     |G| free

is then fitted by least squares in the reported DTI and scored by artefact-level leave-one-out RMSE.

    python scripts/run_livecal_refit.py            # writes evidence/livecal_refit_2026-10-31.json

Evidence class of every number: COMPUTED.  Anchor scores: OWNER-REPORTED (no organizer receipt exists).
Nothing is uploaded and drivendata.org is never contacted.
"""
from __future__ import annotations

import hashlib
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
from gems25 import livecal  # noqa: E402
from gems25.metric import ALPHA, BETA  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402

N_ZB = 6
N_DB = livecal.N_BINS
N_CELL = N_DB * N_ZB

# (id, path relative to data/, owner-reported score, anchor-or-holdout)
ANCHORS = [
    ("h19-5", "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", 0.1922, "anchor"),
    ("h19-4", "scored/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif", 0.1894, "anchor"),
    ("h16-1", "scored/gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif", 0.1855, "anchor"),
    ("d1-5", "scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477, "anchor"),
    ("d2-8", "scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600, "anchor"),
    ("hedge-v2", "scored/8GEMSDOE_Hedge-v2_submission.tif", 0.1563, "anchor"),
    ("h25-ctx-ridge", "scored/gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif", 0.1280, "anchor"),
    ("h28-dotted-ridge", "scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif", 0.1839, "anchor"),
    ("ens12", "scored/gemsdoe-ens12-adopted-7f00890a.tif", 0.1563, "anchor"),
    ("GEMSDOE27-topo-gap", "owner_mirrors/GEMSDOE27__gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449, "anchor"),
    ("GEMSDOE28-h36", "owner_mirrors/GEMSDOE28__gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710, "anchor"),
    ("GEMSDOE28-h27-4", "owner_mirrors/GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif", 0.2708, "anchor"),
    ("GEMSDOE31-h27-4", "owner_mirrors/GEMSDOE31__gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", 0.2708, "anchor"),
    ("GEMSDOE32-B2", "owner_mirrors/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778, "anchor"),
    ("GEMSDOE33-h33d", "owner_mirrors/GEMSDOE33__GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif", 0.2632, "anchor"),
    ("GEMSDOE36-anderson", "owner_mirrors/GEMSDOE36__gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", 0.2750, "anchor"),
    # held out per §4 G2: never an anchor, always a check
    ("lattice-s5", "scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904, "holdout"),
]

MODELS = ["uniform", "pure_exp", "exp_halo", "exp_dead", "step_dead", "two_scale"]
# (N, shape..., beta) bounds
# per-model bounds for the SHAPE parameters only (N and beta bounds are added in fit())
SHAPE_BOUNDS = {
    "uniform": ([], []),
    "pure_exp": ([0.0, 0.05], [400.0, 60.0]),
    "exp_halo": ([0.0, 0.05], [400.0, 60.0]),
    "exp_dead": ([0.0, 0.05], [1.0, 60.0]),
    "step_dead": ([0.0, 0.0], [1.0, 60.0]),
    "two_scale": ([0.0, 0.05, 0.0, 0.05], [400.0, 60.0, 400.0, 60.0]),
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def cell_stats(path: Path, code: np.ndarray, foot: np.ndarray, lab: np.ndarray) -> dict:
    with rasterio.open(path) as s:
        arr = np.nan_to_num(s.read(1), nan=0.0).astype(np.float32)
    if arr.shape != foot.shape:
        raise ValueError(f"{path.name}: shape {arr.shape} != {foot.shape}")
    raw_min, raw_max = float(np.nanmin(arr)), float(np.nanmax(arr))
    p = np.clip(arr, 0.0, 1.0) * np.float32(~lab) * np.float32(foot)
    m, u = livecal.emission_fields(p)
    c = code.ravel()
    ok = c >= 0
    idx = c[ok].astype(np.int64)
    return dict(
        ta=np.bincount(idx, weights=m.ravel()[ok], minlength=N_CELL),
        ua=np.bincount(idx, weights=u.ravel()[ok], minlength=N_CELL),
        ne=np.bincount(idx, weights=p.ravel()[ok], minlength=N_CELL),
        mass=float(p.sum()),
        on_catalogue_raw=float(np.clip(arr, 0, 1)[lab].sum()),
        raw_value_min=raw_min,
        raw_value_max=raw_max,
        sha256=sha256(path),
        positives=int((p > 0).sum()),
    )


def cell_weights(theta: np.ndarray, model: str, reps: np.ndarray, zlev: np.ndarray) -> np.ndarray:
    n = float(np.clip(theta[0], 1.0, 1e7))
    shape = np.asarray(theta[1:-1], dtype=float)
    beta = float(theta[-1])
    f = livecal.pi_weights(shape, reps, model)                       # (N_DB,), bin 0 = 0
    g = np.exp(np.clip(beta, -12.0, 12.0) * zlev)                    # (N_ZB,)
    return n, (f[:, None] * g[None, :]).ravel()


def predict(rows: list[dict], w: np.ndarray, nb: np.ndarray, n_truth: float) -> np.ndarray:
    z = float(w @ nb)
    out = np.empty(len(rows))
    nu = n_truth * w * float(livecal.DISC_COUNT_R) / z
    psi_nu = livecal.psi(nu)
    for i, r in enumerate(rows):
        t = float(w @ r["ta"]) / z
        tp = n_truth * t
        fp = float(r["ne"] @ psi_nu)
        den = ALPHA * (tp + fp) + BETA * n_truth
        out[i] = tp / den if den > 0 else 0.0
    return out


N_LO, N_HI, B_LO, B_HI = 2_000.0, 200_000.0, 0.0, 8.0


def fit(rows: list[dict], scores: np.ndarray, nb: np.ndarray, reps: np.ndarray, zlev: np.ndarray,
        model: str, with_beta: bool, starts: list[list[float]]) -> dict:
    k = livecal.MODEL_PARAMS[model]
    slo, shi = SHAPE_BOUNDS[model]
    lo = np.array([N_LO] + list(slo) + [B_LO if with_beta else 0.0], dtype=float)
    hi = np.array([N_HI] + list(shi) + [B_HI if with_beta else 0.0], dtype=float)
    assert lo.size == 2 + k and hi.size == 2 + k, (model, lo.size, hi.size, k)

    def loss(th):
        th = np.clip(th, lo, hi)
        _, w = cell_weights(th, model, reps, zlev)
        if not np.isfinite(w).all() or float(w @ nb) <= 0:
            return 1e6
        return float(np.mean((predict(rows, w, nb, float(th[0])) - scores) ** 2))

    best, bfun = None, np.inf
    for s in starts:
        s = np.clip(np.asarray(s, dtype=float), lo, hi)
        res = minimize(loss, s, method="Nelder-Mead",
                       options=dict(maxiter=4000, maxfev=8000, xatol=1e-8, fatol=1e-16))
        if res.fun < bfun:
            best, bfun = res, float(res.fun)
    th = np.clip(best.x, lo, hi)
    n_truth, w = cell_weights(th, model, reps, zlev)
    pred = predict(rows, w, nb, n_truth)
    return dict(model=model, with_beta=with_beta, theta=th.tolist(), n_truth=n_truth,
                rmse=float(np.sqrt(bfun)), pred=pred.tolist(), resid=(pred - scores).tolist())


def main() -> int:
    t0 = time.time()
    d, w = data_dir(), work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    zb = np.load(w / "refdet_z_bins.npy")
    d_cat = distance_transform_edt(~lab)
    dcode, reps = livecal.distance_bins(d_cat, foot)
    zlev = np.arange(N_ZB, dtype=float)
    zlev = (zlev - zlev.mean()) / max(zlev.std(), 1e-9)
    code = np.full(foot.shape, -1, np.int32)
    ok = (dcode >= 0) & (zb >= 0)
    code[ok] = dcode[ok].astype(np.int32) * N_ZB + zb[ok].astype(np.int32)
    nb = np.bincount(code[ok].ravel(), minlength=N_CELL).astype(float)

    rows, ids, scores, meta = [], [], [], {}
    for aid, rel, score, role in ANCHORS:
        p = d / rel
        st = cell_stats(p, code, foot, lab)
        st["role"] = role
        rows.append(st)
        meta[aid] = {k: v for k, v in st.items() if k not in ("ta", "ua", "ne")}
        if role == "anchor":
            ids.append(aid)
            scores.append(score)
    scores = np.asarray(scores, dtype=float)
    arows = [rows[i] for i, (a, _, _, r) in enumerate(ANCHORS) if r == "anchor"]
    hrows = {a: rows[i] for i, (a, _, _, r) in enumerate(ANCHORS) if r == "holdout"}

    shape_starts = {
        0: [[]],
        2: [[0.99, 3.0], [0.9, 1.5], [0.5, 8.0], [0.99, 6.0], [0.7, 12.0], [0.2, 2.0]],
        4: [[4.0, 1.0, 1.0, 10.0], [20.0, 1.0, 0.3, 25.0], [2.0, 3.0, 1.0, 8.0]],
    }
    raw = []
    for n in (8_000.0, 12_500.0, 20_000.0, 40_000.0):
        for b in (0.0, 0.3, 0.8, 1.5, 3.0, 5.0):
            for kk, shps in shape_starts.items():
                for shp in shps:
                    raw.append((kk, n, tuple(shp), b))
    results = {}
    for model in MODELS:
        k = livecal.MODEL_PARAMS[model]
        for wb in (False, True):
            seen, uniq = set(), []
            for kk, n, shp, b in raw:
                if kk != k:
                    continue
                cand = [n] + list(shp) + [b if wb else 0.0]
                key = tuple(cand)
                if key not in seen:
                    seen.add(key)
                    uniq.append(cand)
            r = fit(arows, scores, nb, reps, zlev, model, wb, uniq)
            # leave-one-out
            loo = np.empty(len(arows))
            for i in range(len(arows)):
                keep = [r2 for j, r2 in enumerate(arows) if j != i]
                ks = np.delete(scores, i)
                f = fit(keep, ks, nb, reps, zlev, model, wb, uniq)
                _, ww = cell_weights(np.array(f["theta"]), model, reps, zlev)
                loo[i] = predict([arows[i]], ww, nb, f["n_truth"])[0]
            r["loo_pred"] = loo.tolist()
            r["loo_rmse"] = float(np.sqrt(np.mean((loo - scores) ** 2)))
            r["loo_max_abs"] = float(np.max(np.abs(loo - scores)))
            n_truth, ww = cell_weights(np.array(r["theta"]), model, reps, zlev)
            for aid, hr in hrows.items():
                r[f"holdout_pred_{aid}"] = float(predict([hr], ww, nb, n_truth)[0])
            results[f"{model}{'+z' if wb else ''}"] = r
            print(f"{model:>11}{'+z' if wb else '  '}  rmse={r['rmse']:.4f}  loo_rmse={r['loo_rmse']:.4f}  "
                  f"N={r['n_truth']:.0f}  beta={r['theta'][-1]:.2f}  "
                  f"B2_loo={loo[ids.index('GEMSDOE32-B2')]:.4f}  lat={r.get('holdout_pred_lattice-s5', float('nan')):.4f}")

    order = sorted(results, key=lambda k: (results[k]["loo_rmse"], -len(k)))
    best = results[order[0]]
    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        preregistration="knowledge/56_preregistered_live_anchored_truth_refit_2026-10-31.md",
        evidence_class="COMPUTED; anchors are OWNER-REPORTED scores, no ORGANIZER-CONFIRMED receipt exists",
        n_anchors=len(ids), anchor_ids=ids, anchor_scores=scores.tolist(),
        holdout_ids=[a for a, _, _, r in ANCHORS if r == "holdout"],
        holdout_scores={a: s for a, _, s, r in ANCHORS if r == "holdout"},
        artefact_meta=meta,
        cells=dict(n_distance_bins=N_DB, n_detector_bins=N_ZB, n_pixels_per_cell=nb.astype(int).tolist()),
        results={k: {kk: vv for kk, vv in v.items() if kk != "pred"} for k, v in results.items()},
        ranking=order,
        best_model=order[0],
        best=dict(model=best["model"], with_beta=best["with_beta"], theta=best["theta"],
                  n_truth=best["n_truth"], loo_rmse=best["loo_rmse"], loo_max_abs=best["loo_max_abs"],
                  in_sample_rmse=best["rmse"]),
        gates=dict(
            G1_estimator_usable=bool(best["loo_rmse"] <= 0.030
                                     and abs(best["loo_pred"][ids.index("GEMSDOE32-B2")] - 0.2778) <= 0.040),
            G2_lattice_transfer=bool(abs(best.get("holdout_pred_lattice-s5", 9.0) - 0.0904) <= 0.030),
        ),
        seconds=round(time.time() - t0, 1),
    )
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence" / "livecal_refit_2026-10-31.json").write_text(json.dumps(out, indent=1) + "\n")
    print("\nbest:", order[0], "loo_rmse=%.4f" % best["loo_rmse"], "gates:", out["gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
