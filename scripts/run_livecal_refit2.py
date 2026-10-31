#!/usr/bin/env python3
"""Experiment 2 of ``knowledge/57`` — corrected live-anchored truth refit (200 detector bins, lattice anchored).

For every byte-pinned artefact with an owner-reported DTI the script stores, per covariate cell
(distance-to-catalogue bin x reference-detector quantile bin), the kernel-max mass ``ta`` (drives TP),
the kernel-sum mass ``ua`` (FP credit) and the emitted mass ``ne`` (FP cost).  A truth model

    pi(cell)  ∝  f(d_bin) · g(z_bin),     |G| free

is fitted by least squares in the reported DTI and scored by artefact-level leave-one-out RMSE.

    python scripts/run_livecal_refit2.py           # writes evidence/livecal_refit2_2026-10-31.json
    python scripts/run_livecal_refit2.py --quick   # fewer optimiser starts (diagnostic only)

Evidence class of every number: COMPUTED.  Anchor scores: OWNER-REPORTED (no organizer receipt exists).
Nothing is uploaded and drivendata.org is never contacted.
"""
from __future__ import annotations

import argparse
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

N_ZB = 200
N_DB = livecal.N_BINS
N_CELL = N_DB * N_ZB

# (id, path relative to data/, owner-reported score, role)
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
    # knowledge/57 §3.2: the lattice joins the anchors - it is the only detector-independent probe of |G|
    ("lattice-s5", "scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904, "anchor"),
]

MODELS = ["uniform", "exp_dead", "step_dead", "pure_exp", "exp_halo", "two_scale"]
LINKS = ["none", "exp", "power", "betapdf"]
N_LINK_PARAM = {"none": 0, "exp": 1, "power": 1, "betapdf": 2}

# per-model bounds for the SHAPE parameters only (N and the link bounds are added in fit())
SHAPE_BOUNDS = {
    "uniform": ([], []),
    "pure_exp": ([0.0, 0.05], [400.0, 60.0]),
    "exp_halo": ([0.0, 0.05], [400.0, 60.0]),
    "exp_dead": ([0.0, 0.05], [1.0, 60.0]),
    "step_dead": ([0.0, 0.0], [1.0, 60.0]),
    "two_scale": ([0.0, 0.05, 0.0, 0.05], [400.0, 60.0, 400.0, 60.0]),
}
LINK_BOUNDS = {
    "none": ([], []),
    "exp": ([0.0], [25.0]),
    "power": ([0.0], [20.0]),
    "betapdf": ([0.05, 0.05], [30.0, 30.0]),
}
N_LO, N_HI = 2_000.0, 60_000.0


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


def detector_gain(params: np.ndarray, q: np.ndarray, link: str) -> np.ndarray:
    """Per-detector-bin truth multiplier.

    none    : flat (the detector carries no information)
    exp     : exp(gamma * q)                              monotone increasing
    power   : q ** gamma                                  monotone increasing
    betapdf : (q + e)^(a-1) (1 - q + e)^(b-1), normalised  can peak inside (0, 1)
    """
    if link == "none":
        return np.ones_like(q)
    if link == "exp":
        return np.exp(np.clip(float(params[0]), 0.0, 60.0) * q)
    if link == "power":
        return np.power(np.clip(q, 1e-6, 1.0), np.clip(float(params[0]), 0.0, 60.0))
    if link == "betapdf":
        a, b = float(params[0]), float(params[1])
        e = 1e-3
        g = np.power(np.clip(q, 0.0, 1.0) + e, a - 1.0) * np.power(1.0 - np.clip(q, 0.0, 1.0) + e, b - 1.0)
        g = np.nan_to_num(g, nan=0.0, posinf=0.0, neginf=0.0)
        s = g.sum()
        return g / s if s > 0 else g
    raise ValueError(link)


def cell_weights(theta: np.ndarray, model: str, reps: np.ndarray, q: np.ndarray, link: str) -> tuple[float, np.ndarray]:
    n = float(np.clip(theta[0], 1.0, 1e7))
    k = livecal.MODEL_PARAMS[model]
    shape = np.asarray(theta[1:1 + k], dtype=float)
    gpar = np.asarray(theta[1 + k:], dtype=float)
    f = livecal.pi_weights(shape, reps, model)          # (N_DB,), bin 0 = catalogue -> 0
    g = detector_gain(gpar, q, link)                    # (N_ZB,)
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


def fit(rows, scores, nb, reps, q, model, link, starts, maxiter) -> dict:
    k = livecal.MODEL_PARAMS[model]
    slo, shi = SHAPE_BOUNDS[model]
    glo, ghi = LINK_BOUNDS[link]
    lo = np.array([N_LO] + list(slo) + list(glo), dtype=float)
    hi = np.array([N_HI] + list(shi) + list(ghi), dtype=float)
    assert lo.size == 1 + k + len(glo), (model, link, lo.size)

    def loss(th):
        th = np.clip(th, lo, hi)
        _, w = cell_weights(th, model, reps, q, link)
        if not np.isfinite(w).all() or float(w @ nb) <= 0:
            return 1e6
        return float(np.mean((predict(rows, w, nb, float(th[0])) - scores) ** 2))

    best, bfun = None, np.inf
    for s in starts:
        s = np.clip(np.asarray(s, dtype=float), lo, hi)
        res = minimize(loss, s, method="Nelder-Mead",
                       options=dict(maxiter=maxiter, maxfev=2 * maxiter, xatol=1e-7, fatol=1e-14))
        if res.fun < bfun:
            best, bfun = res, float(res.fun)
    th = np.clip(best.x, lo, hi)
    n_truth, w = cell_weights(th, model, reps, q, link)
    pred = predict(rows, w, nb, n_truth)
    return dict(model=model, link=link, theta=th.tolist(), n_truth=n_truth,
                rmse=float(np.sqrt(bfun)), pred=pred.tolist(), resid=(pred - scores).tolist())


def make_starts(model: str, link: str) -> list[list[float]]:
    k = livecal.MODEL_PARAMS[model]
    shapes = {
        0: [[]],
        2: [[0.99, 3.0], [0.8, 8.0], [0.4, 20.0], [0.99, 12.0]],
        4: [[4.0, 1.0, 1.0, 10.0], [20.0, 1.0, 0.3, 25.0]],
    }[k]
    gpars = {
        "none": [[]],
        "exp": [[2.0], [8.0], [16.0]],
        "power": [[0.5], [2.0], [6.0]],
        "betapdf": [[2.0, 1.0], [1.0, 2.0], [3.0, 3.0], [1.5, 6.0], [6.0, 1.5]],
    }[link]
    out, seen = [], set()
    for n in (9_000.0, 13_000.0, 20_000.0):
        for shp in shapes:
            for gp in gpars:
                cand = [n] + list(shp) + list(gp)
                key = tuple(cand)
                if key not in seen:
                    seen.add(key)
                    out.append(cand)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="fewer optimiser iterations (diagnostic only)")
    args = ap.parse_args()
    maxiter = 400 if args.quick else 1200
    t0 = time.time()
    d, w = data_dir(), work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    z = np.load(w / "refdet_z.npy")
    d_cat = distance_transform_edt(~lab)
    dcode, reps = livecal.distance_bins(d_cat, foot)
    elig = foot & ~lab
    edges = np.quantile(z[elig], np.linspace(0, 1, N_ZB + 1)[1:-1])
    zb = np.full(foot.shape, -1, np.int32)
    zb[elig] = np.searchsorted(edges, z[elig], side="right").astype(np.int32)
    q = (np.arange(N_ZB, dtype=float) + 0.5) / N_ZB
    code = np.full(foot.shape, -1, np.int32)
    okc = (dcode >= 0) & (zb >= 0)
    code[okc] = dcode[okc].astype(np.int32) * N_ZB + zb[okc].astype(np.int32)
    nb = np.bincount(code[okc].ravel(), minlength=N_CELL).astype(float)
    print(f"detector bins: {N_ZB} equal-count bins of {int(elig.sum()) // N_ZB} px; cells with pixels: "
          f"{int((nb > 0).sum())}", flush=True)

    rows, ids, scores, meta = [], [], [], {}
    for aid, rel, score, role in ANCHORS:
        st = cell_stats(d / rel, code, foot, lab)
        st["role"] = role
        rows.append(st)
        meta[aid] = {kk: vv for kk, vv in st.items() if kk not in ("ta", "ua", "ne")}
        ids.append(aid)
        scores.append(score)
        print(f"  artefact {aid:>20}  dots={st['positives']:>7,}  score={score}", flush=True)
    scores = np.asarray(scores, dtype=float)

    results = {}
    for model in MODELS:
        for link in LINKS:
            starts = make_starts(model, link)
            r = fit(rows, scores, nb, reps, q, model, link, starts, maxiter)
            loo = np.empty(len(rows))
            for i in range(len(rows)):
                keep = [r2 for j, r2 in enumerate(rows) if j != i]
                ks = np.delete(scores, i)
                f = fit(keep, ks, nb, reps, q, model, link, starts, maxiter)
                _, ww = cell_weights(np.array(f["theta"]), model, reps, q, link)
                loo[i] = predict([rows[i]], ww, nb, f["n_truth"])[0]
            r["loo_pred"] = loo.tolist()
            r["loo_rmse"] = float(np.sqrt(np.mean((loo - scores) ** 2)))
            r["loo_max_abs"] = float(np.max(np.abs(loo - scores)))
            results[f"{model}+{link}"] = r
            print(f"{model:>11}+{link:<8} rmse={r['rmse']:.4f} loo={r['loo_rmse']:.4f} N={r['n_truth']:>7.0f} "
                  f"theta={[round(x, 3) for x in r['theta'][1:]]} "
                  f"B2={loo[ids.index('GEMSDOE32-B2')]:.4f} lat={loo[ids.index('lattice-s5')]:.4f}", flush=True)

    n_lat = float(meta["lattice-s5"]["positives"])
    s_lat = 0.0904
    bounds = {}
    for c_min in (0.30, 0.35, 0.45):
        den = c_min * (1.0 - 0.2 * s_lat) - 0.8 * s_lat
        bounds[f"max_N_at_coverage_{c_min:.2f}"] = float(0.2 * s_lat * n_lat / den) if den > 0 else None
    order = sorted(results, key=lambda kk: (results[kk]["loo_rmse"], -len(kk)))
    best = results[order[0]]
    out = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        script="scripts/run_livecal_refit2.py",
        preregistration="knowledge/57_preregistered_livecal_refit_experiment2_2026-10-31.md",
        evidence_class="COMPUTED; anchors are OWNER-REPORTED scores, no ORGANIZER-CONFIRMED receipt exists",
        quick_mode=bool(args.quick),
        n_anchors=len(ids), anchor_ids=ids, anchor_scores=scores.tolist(),
        artefact_meta=meta,
        cells=dict(n_distance_bins=N_DB, n_detector_bins=N_ZB),
        results={kk: {k2: v2 for k2, v2 in v.items() if k2 != "pred"} for kk, v in results.items()},
        ranking=order,
        best_model=order[0],
        best=dict(model=best["model"], link=best["link"], theta=best["theta"], n_truth=best["n_truth"],
                  loo_rmse=best["loo_rmse"], loo_max_abs=best["loo_max_abs"], in_sample_rmse=best["rmse"],
                  loo_pred=dict(zip(ids, best["loo_pred"]))),
        lattice_identifiability=dict(
            lattice_positives=n_lat, lattice_score=s_lat,
            note=("closed form: N = 0.2 s n / (c(1-0.2 s) - 0.8 s) from the published DTI with FP <= n_lat "
                  "and coverage c >= c_min; a fit above this bound is UNIDENTIFIED, not a measurement"),
            **bounds),
        gates=dict(
            G1_estimator_usable=bool(best["loo_rmse"] <= 0.030
                                     and abs(best["loo_pred"][ids.index("GEMSDOE32-B2")] - 0.2778) <= 0.040),
            G2_lattice_transfer=bool(abs(best["loo_pred"][ids.index("lattice-s5")] - 0.0904) <= 0.030),
        ),
        seconds=round(time.time() - t0, 1),
    )
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence" / "livecal_refit2_2026-10-31.json").write_text(json.dumps(out, indent=1) + "\n")
    print("\nlattice identifiability:", {k: (round(v, 0) if v else v) for k, v in bounds.items()})
    print("best:", order[0], "loo_rmse=%.4f" % best["loo_rmse"], "gates:", out["gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
