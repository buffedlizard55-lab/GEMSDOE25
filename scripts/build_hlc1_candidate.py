#!/usr/bin/env python3
"""Experiment 3b — build the DTI-optimal unique candidate under the live-anchored truth model.

The emission is chosen by a **marginal-gain greedy** on the published DTI, not by the kernel-sum
rank used in ``livecal.greedy_disjoint``.  A dot is worth emitting while

    dTP > 0.2 * DTI * psi(nu_y)          (dTP = the increase of the kernel-MAX field weighted by pi,
                                          psi(nu_y) = the false-positive mass of that dot)

which is the exact marginal condition of ``DTI = TP / (0.2(TP+FP) + 0.8 N)``.  Packing dots closer than
2R = 6 px makes the kernel-sum rank actively harmful: it keeps adding dots that only duplicate credit the
kernel-max field has already banked.

    python scripts/build_hlc1_candidate.py            # writes docs/downloads/<content-addressed>.tif
    python scripts/build_hlc1_candidate.py --cal evidence/livecal_refit3_2026-10-31.json

Evidence class: COMPUTED.  The predicted DTI is a MODEL ESTIMATE calibrated on OWNER-REPORTED scores;
it is not a leaderboard score and not an organizer receipt.  Nothing is uploaded; drivendata.org is
never contacted.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25 import livecal, livecal_cells  # noqa: E402
from gems25.metric import ALPHA, BETA  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import (check_file, content_id, make_filename, make_note,  # noqa: E402
                               sha256_file, write_submission, zip_single)
from run_livecal_refit2 import ANCHORS  # noqa: E402

N_ZB = 200
SLUG = "gems25-hlc1-liveanchored"
MIN_DISTS = (2.4, 2.8, 3.5)
POOL = 250_000
BATCH = 100
OUT_DIR = ROOT / "docs" / "downloads"
B2_REL = "owner_mirrors/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"


def offsets(min_dist: float) -> tuple[np.ndarray, np.ndarray]:
    rad = int(np.ceil(min_dist))
    dy, dx = np.meshgrid(np.arange(-rad, rad + 1), np.arange(-rad, rad + 1), indexing="ij")
    keep = (np.hypot(dy, dx) < min_dist).ravel()
    return dy.ravel()[keep].astype(np.int64), dx.ravel()[keep].astype(np.int64)


def emission_rows_from_mask(mask: np.ndarray, code: np.ndarray, foot: np.ndarray, lab: np.ndarray) -> dict:
    p = (mask & foot & ~lab).astype(np.float32)
    m, u = livecal.emission_fields(p)
    c = code.ravel()
    ok = c >= 0
    idx = c[ok].astype(np.int64)
    ncell = livecal.N_BINS * N_ZB
    return dict(ta=np.bincount(idx, weights=m.ravel()[ok], minlength=ncell),
                ua=np.bincount(idx, weights=u.ravel()[ok], minlength=ncell),
                ne=np.bincount(idx, weights=p.ravel()[ok], minlength=ncell),
                mass=float(p.sum()), positives=int((p > 0).sum()))


def marginal_greedy(pi: np.ndarray, nu: np.ndarray, psi_nu: np.ndarray, pool_flat: np.ndarray,
                    shape: tuple[int, int], min_dist: float, n_truth: float,
                    kmax: int = 250_000) -> tuple[np.ndarray, list[float]]:
    """Vectorised lazy greedy on the exact marginal DTI condition.  Returns the picked flat indices."""
    H, W = shape
    offs = livecal.KERNEL_OFFSETS
    wts = livecal.KERNEL_WEIGHTS
    m = np.zeros(H * W, dtype=np.float64)
    pi_flat = pi.ravel()
    nu_flat = nu.ravel()
    psi_flat = psi_nu.ravel()
    ody, odx = offsets(min_dist)
    blocked = np.zeros(H * W, dtype=bool)
    picked: list[int] = []
    gains: list[float] = []
    tp = 0.0
    fp = 0.0
    pool = pool_flat.copy()
    ptr = 0
    while len(picked) < kmax and ptr < pool.size:
        cand = pool[ptr:ptr + BATCH]
        ptr += BATCH
        cand = cand[~blocked[cand]]
        if cand.size == 0:
            continue
        y, x = np.divmod(cand, W)
        gain = np.zeros(cand.size, dtype=np.float64)
        for (dy, dx), k in zip(offs, wts):
            ny, nx = y + dy, x + dx
            okk = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
            idx = np.where(okk, ny * W + nx, 0)
            contrib = np.where(okk, np.maximum(k - m[idx], 0.0) * pi_flat[idx], 0.0)
            gain += contrib
        order = np.argsort(-gain)
        for j in order:
            f = int(cand[j])
            if blocked[f]:
                continue
            dti = tp / (ALPHA * (tp + fp) + BETA * n_truth) if (tp + fp) > 0 else 0.0
            # exact marginal condition: N*gain > alpha*psi*TP/(alpha*FP + beta*N) = alpha*psi*DTI/(1-alpha*DTI)
            thr = ALPHA * dti * float(psi_flat[f]) / (n_truth * max(1.0 - ALPHA * dti, 1e-9))
            if not np.isfinite(gain[j]) or gain[j] <= thr:
                continue
            picked.append(f)
            gains.append(float(gain[j]))
            tp += n_truth * gain[j]
            fp += float(psi_flat[f])
            yy, xx = divmod(f, W)
            ny = np.clip(yy + ody, 0, H - 1)
            nx = np.clip(xx + odx, 0, W - 1)
            valid = ((yy + ody) >= 0) & ((yy + ody) < H) & ((xx + odx) >= 0) & ((xx + odx) < W)
            blocked[ny[valid] * W + nx[valid]] = True
            # refresh the max field locally
            for (dy, dx), k in zip(offs, wts):
                ay, ax = yy + dy, xx + dx
                if 0 <= ay < H and 0 <= ax < W:
                    i2 = ay * W + ax
                    if k > m[i2]:
                        m[i2] = k
        if ptr >= pool.size:
            break
    return np.asarray(picked, dtype=np.int64), gains


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cal", default="evidence/livecal_refit3_2026-10-31.json")
    args = ap.parse_args()
    t0 = time.time()
    d, w = data_dir(), work_dir()
    cal = json.loads((ROOT / args.cal).read_text())
    best = cal["results"][cal["best_model"]]
    model, link = best["model"], best["link"]
    ratio = float(best.get("ratio", np.inf))
    theta = np.asarray(best["theta"], dtype=float)
    n_shape = livecal.MODEL_PARAMS[model]
    n_truth = float(best["n_truth"])
    print(f"model {cal['best_model']}  theta={[round(x, 4) for x in theta]}  N={n_truth:.0f}  "
          f"loo_rmse={best['loo_rmse']:.4f}  ratio={ratio}", flush=True)

    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    z = np.load(w / "refdet_z.npy")
    d_cat = distance_transform_edt(~lab)
    H, W = foot.shape
    code, reps, q = livecal_cells.cell_code(d_cat, foot, lab, z, N_ZB)
    nb = np.bincount(code[code >= 0].ravel(), minlength=livecal.N_BINS * N_ZB).astype(float)
    _, wts = livecal_cells.cell_weights(theta, model, reps, q, link, n_shape, ratio)
    ztot = float(wts @ nb)
    pi_cell = wts / ztot                                   # per-cell truth probability per pixel
    pi = np.zeros(foot.size, dtype=np.float64)
    okc = code.ravel() >= 0
    pi[okc] = pi_cell[code.ravel()[okc]]
    nu = n_truth * pi * float(livecal_cells.DISC_COUNT_R)
    psi_nu = livecal.psi(nu)
    pi = pi.reshape(foot.shape)
    nu = nu.reshape(foot.shape)
    psi_nu = psi_nu.reshape(foot.shape)
    print(f"truth support {(pi > 0).sum():,} px;  pi p99={np.quantile(pi[pi > 0], 0.99):.3e};  "
          f"nu p99={np.quantile(nu[pi > 0], 0.99):.3f}", flush=True)

    value = livecal.value_field(pi)
    elig = foot & ~lab
    pool_flat = np.flatnonzero(elig.ravel())
    vv = value.ravel()[pool_flat]
    top = np.argsort(-vv)[:POOL]
    pool_flat = pool_flat[np.sort(top)]
    print(f"candidate pool {pool_flat.size:,} px (value range {vv[top].min():.3e}..{vv[top].max():.3e})", flush=True)

    grid = []
    designs = {}
    for md in MIN_DISTS:
        picks, gains = marginal_greedy(pi, nu, psi_nu, pool_flat, foot.shape, md, n_truth)
        designs[md] = picks
        for K in sorted({int(len(picks) * f) for f in (0.25, 0.5, 0.75, 1.0)} | {20000, 37654, 60000}):
            if K <= 0 or K > len(picks):
                continue
            mask = np.zeros(foot.size, bool)
            mask[picks[:K]] = True
            mask = mask.reshape(foot.shape)
            row = emission_rows_from_mask(mask, code, foot, lab)
            dti = float(livecal_cells.predict([row], wts, nb, n_truth)[0])
            grid.append(dict(min_dist=md, budget=K, predicted_dti=dti, dots=int(row["positives"]),
                             tp=round(float(wts @ row["ta"]) / ztot * n_truth, 1),
                             fp=round(float(row["ne"] @ livecal.psi(n_truth * wts * livecal_cells.DISC_COUNT_R / ztot)), 1),
                             frac_d_gt_30=round(float((d_cat[mask] > 30.5).mean()), 4),
                             frac_z_top5=round(float((z[mask] > np.quantile(z[elig], 0.95)).mean()), 4)))
            print(f"  md={md} K={K:>7,} pred DTI={dti:.4f} dots={grid[-1]['dots']:,} "
                  f"tp={grid[-1]['tp']:.0f} fp={grid[-1]['fp']:.0f} "
                  f"d>30={grid[-1]['frac_d_gt_30']:.2f} ztop5={grid[-1]['frac_z_top5']:.2f}", flush=True)
        print(f"  md={md}: stopping rule kept {len(picks):,} dots", flush=True)

    best_row = min(grid, key=lambda r: -r["predicted_dti"])
    md, K = best_row["min_dist"], best_row["budget"]
    print("chosen design:", best_row, flush=True)

    mask = np.zeros(foot.size, bool)
    mask[designs[md][:K]] = True
    mask = mask.reshape(foot.shape)
    pred = np.where(mask, np.float32(1.0), np.float32(0.0))
    template = d / "sample_submission.tif"
    date = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    cid = content_id(pred, foot, lab)
    name = make_filename(f"{SLUG}-md{md:g}", date, cid, outside="zeros")
    tif = OUT_DIR / f"{name}.tif"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_submission(pred, template, tif, outside="zero")
    zip_path = zip_single(tif)
    fmt = check_file(tif, template)

    with rasterio.open(tif) as s:
        arr = s.read(1)
    with rasterio.open(d / B2_REL) as s:
        b2 = np.nan_to_num(s.read(1)) > 0
    inter = int((mask & b2).sum())
    overlap = dict(
        jaccard_vs_b2=round(inter / (int(mask.sum()) + int(b2.sum()) - inter), 4),
        cand_within_3px_of_b2=round(float((distance_transform_edt(~b2)[mask] <= 3.0).mean()), 4),
        b2_within_3px_of_cand=round(float((distance_transform_edt(~mask)[b2] <= 3.0).mean()), 4),
    )
    note = make_note("GEMSDOE25 H-LC1", f"live-anchored marginal-gain design, {K} dots at {md} px, "
                                        f"model est {best_row['predicted_dti']:.3f} (not a score)", cid)
    rec = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        script="scripts/build_hlc1_candidate.py",
        calibration=args.cal,
        model=dict(name=cal["best_model"], theta=[float(x) for x in theta], n_truth=n_truth,
                   loo_rmse=best["loo_rmse"], loo_max_abs=best["loo_max_abs"], ratio=ratio,
                   gates=cal["gates"], evidence_class="MODEL ESTIMATE (OWNER-REPORTED anchors)"),
        design_grid=grid, chosen=best_row,
        file=dict(name=tif.name, sha256=sha256_file(tif), bytes=tif.stat().st_size,
                  zip=zip_path.name, zip_sha256=sha256_file(zip_path),
                  content_id=cid, note=note, note_len=len(note)),
        format_check=fmt,
        array_checks=dict(finite_inside_footprint=bool(np.isfinite(arr[foot]).all()),
                          min_inside=float(arr[foot].min()), max_inside=float(arr[foot].max()),
                          zeros_outside=bool((arr[~foot] == 0).all()),
                          positives=int((pred > 0).sum()),
                          positives_on_catalogue=int((mask & lab).sum()),
                          min_distance_to_catalogue_px=float(d_cat[mask].min()),
                          median_distance_to_catalogue_px=float(np.median(d_cat[mask]))),
        uniqueness_vs_b2=overlap,
        evidence_class="COMPUTED; the predicted DTI is a MODEL ESTIMATE, not a score, not ORGANIZER-CONFIRMED",
        seconds=round(time.time() - t0, 1),
    )
    (ROOT / "evidence" / "hlc1_candidate_2026-10-31.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if k != "design_grid"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
