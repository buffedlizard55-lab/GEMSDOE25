#!/usr/bin/env python3
"""H-N1 screen experiment: radiometric alteration-ratio edge x conductive-base edge.

Frozen design (committed first in knowledge/29_new_hypotheses_2026-10-26.md):
  * Surface: pct_norm(D_UK_edge) * pct_norm(D_depth_base_grad) from static_ABCD.npy (family D only;
    catalogue distance E_dist used solely as a hard exclusion mask at emission time).
  * Holdout: spatially blocked hide-and-recover, 4 folds x draws [0, 1] (screen),
    hide_frac 0.20 of whole catalogue components (src/gems25/holdout.py).
  * Emission (all arms): ridge NMS sigma 1.0 -> drop visible catalogue pixels pixel-exactly ->
    top-K K=0.0245 of eroded domain -> dot_thin(min_dist 1.5). Fixed pixel count across arms.
  * Control arm: same-run B_crest surface with identical emission.
  * Response: pooled exact sparse-regime DTI (alpha 0.2, beta 0.8, R = 300 m).
  * Leakage canary: standalone surface AUC vs hidden test labels <= 0.90.
  * Paired gate vs control: mean gain > +0.001, >= 3/4 folds positive, worst fold >= -0.01.
  * LANE (pre-placement): surface |Spearman| <= 0.90 vs every registry raster.
Run: python3 scripts/run_hn1_screen.py
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25.experiment import load_context  # noqa: E402
from gems25.holdout import Holdout  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, make_note, write_submission  # noqa: E402
from gems25.thinning import dot_thin, ridge_nms, select_top_positive  # noqa: E402

# ----------------------------------------------------------------------------------------------
# Frozen design
# ----------------------------------------------------------------------------------------------
DRAWS = [0, 1]
FOLDS = 4
FOLD_NAMES = ("NW", "NE", "SW", "SE")
HIDE_FRAC = 0.20
KFRAC = 0.0245
DOT_MIN_DIST = 1.5
NMS_SIGMA = 1.0
PAIRED_GATE_MIN_GAIN = 0.001
PAIRED_GATE_MIN_FOLDS_POSITIVE = 3
PAIRED_GATE_WORST_FOLD = -0.01
LEAKAGE_AUC_CAP = 0.90
LANE_CORR_CAP = 0.90
LANE_OVERLAP_CAP = 0.70
LANE_RADIUS_PX = 3.0

OUT_DIR = ROOT / "evidence" / "hn1"
REGISTRY_DIRS = [data_dir() / "scored", ROOT / "docs" / "downloads"]

FEATURE_UK_EDGE = "D_UK_edge"
FEATURE_BASE_GRAD = "D_depth_base_grad"
CONTROL_FEATURE = "B_crest"


# ----------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------
def pct_norm_grid(grid: np.ndarray, foot: np.ndarray) -> np.ndarray:
    v = np.where(foot, np.asarray(grid, np.float64), np.nan)
    f = v[np.isfinite(v)]
    if f.size == 0:
        return np.zeros_like(v, np.float32)
    lo, hi = float(np.percentile(f, 1.0)), float(np.percentile(f, 99.0))
    if hi <= lo:
        return np.zeros_like(v, np.float32)
    return np.clip((v - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def full_grid_from_col(static: np.ndarray, names: list[str], name: str, foot: np.ndarray) -> np.ndarray:
    g = np.zeros(foot.shape, np.float32)
    g.ravel()[np.flatnonzero(foot.ravel())] = np.asarray(static[names.index(name)], np.float32)
    return g


def emit_quadrant(score_q: np.ndarray, domain: np.ndarray, known: np.ndarray, k: int) -> np.ndarray:
    g = np.where(domain & np.isfinite(score_q), score_q, 0.0).astype(np.float32)
    r = ridge_nms(g, domain, NMS_SIGMA)
    eligible = domain & ~known
    sc = np.where(r & eligible, g, 0.0)
    top = select_top_positive(sc, domain, k)
    return dot_thin(top, DOT_MIN_DIST)


def load_registry_rasters() -> list[dict]:
    paths = []
    for directory in REGISTRY_DIRS:
        if directory.exists():
            paths.extend(sorted(directory.glob("*.tif")))
    out, seen = [], set()
    for p in paths:
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        out.append(dict(file=p.name, path=p, sha256=digest))
    return out


def registry_array(reg: dict, foot: np.ndarray) -> np.ndarray:
    import rasterio

    with rasterio.open(reg["path"]) as src:
        return np.nan_to_num(src.read(1), nan=0.0).astype(np.float32)


def surface_lane_check(ctx, surface: np.ndarray, registry: list[dict]) -> list[dict]:
    foot, fi = ctx.foot, ctx.fi
    candidate = np.where(foot, surface, np.nan).ravel()[fi]
    results = []
    for reg in registry:
        reg_arr = registry_array(reg, foot)
        if reg_arr.shape != foot.shape:
            results.append(dict(file=reg["file"], skipped="shape differs", duplicate=True))
            continue
        reference = np.where(foot, reg_arr, np.nan).ravel()[fi]
        finite = np.isfinite(candidate) & np.isfinite(reference)
        corr = float("nan")
        cv, rv = candidate[finite], reference[finite]
        if finite.sum() >= 1000 and cv.min() != cv.max() and rv.min() != rv.max():
            corr = float(spearmanr(cv, rv, nan_policy="omit").statistic)
        duplicate = not math.isfinite(corr) or abs(corr) > LANE_CORR_CAP
        results.append(dict(file=reg["file"], spearman=corr, abs_spearman=abs(corr) if math.isfinite(corr) else None,
                            flag_rank=bool(duplicate), duplicate=bool(duplicate)))
    return results


def lane_check(ctx, emitted: np.ndarray, surface: np.ndarray, registry: list[dict]) -> list[dict]:
    foot, fi = ctx.foot, ctx.fi
    H, W = foot.shape
    surf_finite = np.where(foot, surface, np.nan).ravel()[fi]
    my_dots = np.flatnonzero((emitted > 0).ravel() & foot.ravel())
    my_rc = np.column_stack([my_dots // W, my_dots % W]) if my_dots.size else np.empty((0, 2), int)
    results = []
    for reg in registry:
        reg_arr = registry_array(reg, foot)
        if reg_arr.shape != foot.shape:
            results.append(dict(file=reg["file"], skipped="shape differs", duplicate=True))
            continue
        reg_flat = np.where(foot, reg_arr, np.nan).ravel()[fi]
        finite = ~(np.isnan(surf_finite) | np.isnan(reg_flat))
        corr = float("nan")
        if finite.sum() >= 1000:
            corr = float(spearmanr(surf_finite[finite], reg_flat[finite], nan_policy="omit").statistic)
        reg_mask = (reg_arr > 0) & foot
        reg_n = int(reg_mask.sum())
        dist_to_reg = distance_transform_edt(~reg_mask) if reg_n else None
        coverage = float(((dist_to_reg <= LANE_RADIUS_PX) & foot).sum() / max(int(foot.sum()), 1)) if reg_n else 0.0
        overlap = reverse_overlap = 0.0
        if my_dots.size and reg_n:
            reg_dots = np.flatnonzero(reg_mask.ravel())
            reg_rc = np.column_stack([reg_dots // W, reg_dots % W])
            overlap = float((cKDTree(reg_rc).query(my_rc, k=1)[0] <= LANE_RADIUS_PX).mean())
            reverse_overlap = float((cKDTree(my_rc).query(reg_rc, k=1)[0] <= LANE_RADIUS_PX).mean())
        rho_flag = not math.isnan(corr) and abs(corr) > LANE_CORR_CAP
        overlap_flag = overlap > LANE_OVERLAP_CAP
        dense = coverage >= LANE_OVERLAP_CAP
        sym_min = float(min(overlap, reverse_overlap))
        lane_overlap = bool(sym_min > LANE_OVERLAP_CAP) if dense else bool(overlap_flag)
        results.append(dict(file=reg["file"], spearman=corr,
                            abs_spearman=abs(corr) if not math.isnan(corr) else None,
                            overlap_within_3px=overlap, reverse_overlap_within_3px=reverse_overlap,
                            flag_rank=rho_flag, flag_overlap=overlap_flag,
                            duplicate=bool(rho_flag or overlap_flag), duplicate_lane=bool(rho_flag or lane_overlap),
                            registry_dots=reg_n, halo_coverage_3px=coverage,
                            symmetric_min_overlap_3px=sym_min,
                            non_discriminative_dense=dense))
    return results


# ----------------------------------------------------------------------------------------------
# Holdout evaluation of one surface (mirrors validate_gem_candidate.evaluate_surface)
# ----------------------------------------------------------------------------------------------
def evaluate_surface(ctx, surface: np.ndarray, label: str) -> dict:
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    H = Holdout(foot, lab, HIDE_FRAC)
    fold_dti, fold_auc = {f: [] for f in range(FOLDS)}, {f: [] for f in range(FOLDS)}
    rows = []
    t0 = time.time()
    for fold in range(FOLDS):
        for draw in DRAWS:
            d = H.draw(fold, draw)
            sl = d.bbox
            surf_c = np.nan_to_num(surface[sl], nan=0.0).astype(np.float32)
            k = int(round(KFRAC * int(d.quadrant[sl].sum())))
            emitted_c = emit_quadrant(surf_c, d.quadrant[sl], d.visible[sl], k)
            res = dti_binary(emitted_c, d.hidden_test[sl], valid=d.quadrant[sl], known=d.visible[sl])
            fold_dti[fold].append(res["dti"])
            pos = d.hidden_test[sl] & d.quadrant[sl]
            neg = d.quadrant[sl] & ~lab[sl] & ~d.hidden_test[sl]
            if pos.any() and neg.any():
                vals = np.concatenate([surf_c[pos], surf_c[neg]])
                y = np.concatenate([np.ones(int(pos.sum())), np.zeros(int(neg.sum()))])
                fold_auc[fold].append(float(roc_auc_score(y, vals)))
            rows.append(dict(fold=fold, draw=draw, fold_name=FOLD_NAMES[fold], arm=label,
                             dti=float(res["dti"]), emitted=int(emitted_c.sum()),
                             coverage=float(res["coverage"]), tp=float(res["tp"]),
                             fp=float(res["fp"]), n_truth=int(res["n_truth"])))
    by_fold = [float(np.mean(fold_dti[f])) for f in range(FOLDS)]
    worst_auc = float(max([max(v) for v in fold_auc.values()] or [0.0]))
    return dict(label=label, by_fold=by_fold, mean_dti=float(np.mean(by_fold)),
                worst_auc=worst_auc, seconds=round(time.time() - t0, 1), rows=rows)


def paired_gate(candidate: list[float], control: list[float]) -> dict:
    d = np.asarray(candidate) - np.asarray(control)
    return dict(mean_gain=float(d.mean()), folds_positive=int((d > 0).sum()),
                worst_fold=float(d.min()), per_fold=[float(x) for x in d],
                passed=bool(d.mean() > PAIRED_GATE_MIN_GAIN
                            and (d > 0).sum() >= PAIRED_GATE_MIN_FOLDS_POSITIVE
                            and d.min() >= PAIRED_GATE_WORST_FOLD))


# ----------------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------------
def main() -> None:
    global DRAWS
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = work_dir()
    ctx = load_context(work)
    static = np.load(work / "static_ABCD.npy", mmap_mode="r")
    names = json.loads((work / "static_ABCD.npy.names.json").read_text())
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    for need in (FEATURE_UK_EDGE, FEATURE_BASE_GRAD, CONTROL_FEATURE):
        if need not in names:
            raise SystemExit(f"feature column missing: {need}")
    registry = load_registry_rasters()
    print(f"LANE registry: {len(registry)} rasters", flush=True)

    surf = pct_norm_grid(full_grid_from_col(static, names, FEATURE_UK_EDGE, foot), foot) * \
           pct_norm_grid(full_grid_from_col(static, names, FEATURE_BASE_GRAD, foot), foot)
    ctrl = pct_norm_grid(full_grid_from_col(static, names, CONTROL_FEATURE, foot), foot)

    # --- pre-placement surface lane check ---------------------------------------------------
    surf_rows = surface_lane_check(ctx, surf, registry)
    surf_clear = all(not r["duplicate"] for r in surf_rows)
    print(f"SURFACE LANE H-N1: {'CLEAR' if surf_clear else 'DUPLICATE/UNVERIFIED'}", flush=True)
    for r in surf_rows:
        print(f"  vs {r['file']}: rho={r.get('spearman', float('nan')):+.3f} {'DUPLICATE' if r['duplicate'] else 'ok'}", flush=True)

    # --- holdout: candidate and control -----------------------------------------------------
    cand = evaluate_surface(ctx, surf, "H-N1")
    ctrl_res = evaluate_surface(ctx, ctrl, "control_B_crest")
    gate = paired_gate(cand["by_fold"], ctrl_res["by_fold"])
    print(f"H-N1 mean DTI {cand['mean_dti']:.6f} worst AUC {cand['worst_auc']:.3f}", flush=True)
    print(f"control mean DTI {ctrl_res['mean_dti']:.6f}", flush=True)
    print(f"paired gain {gate['mean_gain']:+.6f} {gate['folds_positive']}/4 folds worst {gate['worst_fold']:+.6f} -> "
          f"{'PASS' if gate['passed'] else 'fail'}", flush=True)

    leakage_ok = cand["worst_auc"] <= LEAKAGE_AUC_CAP
    screen_ok = gate["passed"] and leakage_ok and surf_clear
    print(f"leakage_ok={leakage_ok} gate_passed={gate['passed']} surface_lane_clear={surf_clear} "
          f"SCREEN={'PASS' if screen_ok else 'FAIL'}", flush=True)

    report = dict(
        hypothesis="H-N1: radiometric alteration-ratio edge (D_UK_edge, GeoDAWN K/Th/U) x conductive-base edge "
                   "(D_depth_base_grad, MT depth-to-base); catalogue-free wall-to-wall blind-fault signature",
        mechanism="product of 1-px gradient edges on two independent physical grids; high only where both coincide",
        mimicking_non_fault_process="stratabound potassic/argillic alteration unrelated to faults; conductive-base "
                                    "edges at lithologic contacts not faulted",
        design=dict(draws=DRAWS, folds=FOLDS, hide_frac=HIDE_FRAC, kfrac=KFRAC, dot_min_dist=DOT_MIN_DIST,
                    gate=dict(min_gain=PAIRED_GATE_MIN_GAIN, min_folds_positive=PAIRED_GATE_MIN_FOLDS_POSITIVE,
                              worst_fold=PAIRED_GATE_WORST_FOLD),
                    leakage_auc_cap=LEAKAGE_AUC_CAP, lane_corr_cap=LANE_CORR_CAP, lane_overlap_cap=LANE_OVERLAP_CAP),
        surface_lane=surf_rows, surface_lane_clear=surf_clear,
        candidate={k: v for k, v in cand.items() if k != "rows"},
        control={k: v for k, v in ctrl_res.items() if k != "rows"},
        paired_vs_control=gate, leakage_ok=leakage_ok,
    )

    if not screen_ok:
        report["decision"] = dict(package_tif=False, reason="screen gate not passed: no TIF, no slot (negative result)")
        report["rows"] = cand["rows"]
        (OUT_DIR / "results.json").write_text(json.dumps(report, indent=1) + "\n")
        print("WROTE", OUT_DIR / "results.json")
        print("VERDICT: NEGATIVE — no TIF, no slot")
        return

    # --- confirmation draws [2, 3] ----------------------------------------------------------
    DRAWS = [2, 3]
    cand2 = evaluate_surface(ctx, surf, "H-N1 confirm")
    gate2 = paired_gate(cand2["by_fold"], ctrl_res["by_fold"])
    print(f"CONFIRM mean DTI {cand2['mean_dti']:.6f} paired gain {gate2['mean_gain']:+.6f} "
          f"{gate2['folds_positive']}/4 folds -> {'PASS' if gate2['passed'] else 'fail'}", flush=True)
    report["confirmation"] = {k: v for k, v in cand2.items() if k != "rows"}
    report["confirmation"]["paired_vs_control"] = gate2
    report["rows"] = cand["rows"]
    report["confirm_rows"] = cand2["rows"]

    # --- full-footprint emission + final-dot lane check -------------------------------------
    k = int(round(KFRAC * int(foot.sum())))
    emitted = emit_quadrant(np.where(foot, surf, 0.0).astype(np.float32), foot, lab, k)
    lane_rows = lane_check(ctx, emitted, surf, registry)
    lane_clear = all(not r["duplicate_lane"] for r in lane_rows)
    for r in lane_rows:
        print(f"LANE H-N1 vs {r['file']}: rho={r.get('spearman', float('nan')):+.3f} "
              f"overlap={r.get('overlap_within_3px', float('nan')):.3f} "
              f"{'DUPLICATE' if r['duplicate_lane'] else 'ok'}", flush=True)
    report["lane_final"] = lane_rows
    report["lane_final_clear"] = lane_clear

    all_ok = gate2["passed"] and lane_clear
    pred = np.where(emitted, 1.0, 0.0).astype(np.float32)
    tmpl = data_dir() / "sample_submission.tif"
    date = time.strftime("%Y%m%d", time.gmtime())
    cid = content_id(pred, foot, lab)
    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = f"hn1-rad-base-edge-{date}-{cid}"
    fname = make_filename(f"hn1-rad-base-edge-{date}", date, cid, "zeros")
    tif = write_submission(pred, tmpl, out_dir / fname, outside="zero")
    chk = check_file(tif, tmpl)
    note = make_note("H-N1", "radiometric alteration-ratio edge x conductive-base edge; catalogue-free; "
                             "screen+confirm gates; holdout DTI proxy only", cid, limit=140)
    rec = dict(file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size, sha256=chk["sha256"],
               content_id=cid, positive_pixels=int(emitted.sum()), format_ok=chk["ok_to_upload"],
               checks=chk["checks"], note=note,
               verdict=("PROMOTE" if all_ok else "NEGATIVE"),
               lane_clear=lane_clear, gate_passed=bool(gate2["passed"]), leakage_ok=bool(leakage_ok),
               build=dict(hypothesis="H-N1", date=date, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
    (out_dir / f"checks-{tif.stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    report["tif"] = rec
    report["decision"] = dict(
        package_tif=all_ok,
        reason=("H-N1 passed screen + confirmation, leakage canary and final-dot lane check; format-valid unique TIF "
                "packaged; selector may spend a slot" if all_ok
                else "confirmation or lane check failed: unique TIF built for testing only, DO NOT SUBMIT, no slot"))
    (OUT_DIR / "results.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("file", "bytes", "sha256", "content_id", "positive_pixels",
                                          "format_ok", "note", "verdict")}, indent=1))
    print("WROTE", OUT_DIR / "results.json")
    print(f"VERDICT: {rec['verdict']} — {'slot-eligible (selector decision)' if all_ok else 'testing only, DO NOT SUBMIT'}")


if __name__ == "__main__":
    main()
