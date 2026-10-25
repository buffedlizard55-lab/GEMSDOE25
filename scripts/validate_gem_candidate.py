#!/usr/bin/env python3
"""Preregistered holdout validation of new GEM candidates (knowledge/15).

Frozen design (committed before any run):
  * Hypotheses: GEM-1 (blind magnetics: |grad RTP| x low relief), GEM-2
    (vent proximity x thermal gradient), GEM-3 (blurred-truth emission rule:
    dots restricted to the 1.5-3 px annulus around visible catalogue traces,
    never on catalogue pixels).
  * Holdout: spatially blocked hide-and-recover, 4 folds x draws 0, 1 (screen
    stage; confirmation draws 2,3 only after a screen pass), hide_frac 0.20 of
    whole catalogue components per draw (src/gems25/holdout.py).
  * Emission (all arms): Hessian ridge NMS (sigma 1.0) -> drop visible catalogue
    pixels -> top-K (K = 0.0245 x eroded-domain pixels) -> dot_thin(min_dist 1.5).
    Fixed pixel count across arms so no contrast is won by emitting more mass.
  * Control arm: family B scarp surface (B_crest) with identical emission.
  * Response: exact sparse-regime DTI (alpha 0.2, beta 0.8, R = 300 m) of the
    emitted dots vs the draw's hidden test truth (holdout.score), averaged over
    the 2 draws per fold -> 4 fold means.
  * Leakage canary: AUC of the candidate surface vs hidden test labels within
    the scored domain; AUC > 0.90 => leakage, stop.
  * Paired gate vs same-run control: mean gain > +0.001 DTI, >= 3/4 folds
    positive, worst fold >= -0.01. No gate pass => no TIF, no slot.
  * LANE check: Spearman(|surface| vs each registry raster) <= 0.90 and <= 70%
    of emitted dots within 3 px of any one registry raster's dots, else log as
    duplicate and stop (PARALLEL-RUN PROTOCOL).

Run: .venv/bin/python scripts/validate_gem_candidate.py
"""
from __future__ import annotations

import argparse
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
from gems25.thinning import dot_thin, ridge_nms, select_top_positive  # noqa: E402

# ----------------------------------------------------------------------------------------------
# Frozen design (override draws with --draws; screen = 0 1, confirmation = 2 3)
# ----------------------------------------------------------------------------------------------
_DRAWS_DEFAULT = [0, 1]
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

OUT_DIR = ROOT / "evidence" / "gem_validation"
REGISTRY_DIR = ROOT / "data" / "scored"


# ----------------------------------------------------------------------------------------------
# Surfaces (full footprint grids, NaN outside footprint -> 0)
# ----------------------------------------------------------------------------------------------
def _pct_norm(a: np.ndarray, foot: np.ndarray) -> np.ndarray:
    v = np.where(foot, np.asarray(a, np.float64), np.nan)
    f = v[np.isfinite(v)]
    if f.size == 0:
        return np.zeros_like(v, np.float32)
    lo, hi = float(np.percentile(f, 1.0)), float(np.percentile(f, 99.0))
    if hi <= lo:
        return np.zeros_like(v, np.float32)
    return np.clip((v - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def grad_mag(a: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    from scipy.ndimage import gaussian_filter
    gy, gx = np.gradient(gaussian_filter(a, sigma))
    return np.sqrt(gx * gx + gy * gy)


def surface_gem1(foot: np.ndarray, bands_dir: Path) -> np.ndarray:
    """GEM-1: blind-magnetics indicator = norm(|grad RTP|) x (1 - norm(relief))."""
    rtp = np.load(bands_dir / "02_rtp.npy")
    relief_p = bands_dir / "22_B_relief5.npy"
    if relief_p.exists():
        relief = np.load(relief_p)
    else:
        z = np.load(bands_dir / "12_det_elev.npy")
        from scipy.ndimage import maximum_filter, minimum_filter
        relief = maximum_filter(z, 21) - minimum_filter(z, 21)
    mag = grad_mag(rtp, 1.0)
    return _pct_norm(mag, foot) * (1.0 - _pct_norm(relief, foot))


def surface_gem2(foot: np.ndarray, bands_dir: Path) -> np.ndarray:
    """GEM-2: vent proximity x thermal gradient (21 GDR Quaternary vents, local CSV)."""
    import pandas as pd

    csv_path = data_dir() / "external" / "gdr_volcanic_vents_in_footprint.csv"
    df = pd.read_csv(csv_path)
    df = df[(df.row >= 0) & (df.row < foot.shape[0]) & (df.col >= 0) & (df.col < foot.shape[1])]
    vents = np.zeros(foot.shape, bool)
    vents[df.row.to_numpy(), df.col.to_numpy()] = True
    dist = distance_transform_edt(~vents & foot)
    dist = np.where(foot, dist, np.inf)
    prox = np.where(np.isfinite(dist), np.exp(-dist / 6.0), 0.0)  # 600 m scale
    cond = np.load(bands_dir / "17_cond_surf.npy")
    g = grad_mag(cond, 1.0)
    return (_pct_norm(prox, foot) * _pct_norm(g, foot)).astype(np.float32)


def off_trace_mask(visible: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """GEM-3 rule: pixels 1.5-3 px from visible traces, never on a trace."""
    dist = distance_transform_edt(~visible & foot)
    return (dist >= 1.5) & (dist <= 3.0) & foot & ~visible


def emit(score_full: np.ndarray, domain: np.ndarray, known: np.ndarray, k: int,
         min_dist: float, restrict: np.ndarray | None = None) -> np.ndarray:
    """Ridge NMS -> drop known -> optional restrict mask -> top-K -> dot thinning."""
    g = np.where(domain & np.isfinite(score_full), score_full, 0.0).astype(np.float32)
    r = ridge_nms(g, domain, NMS_SIGMA)
    eligible = domain & ~known
    if restrict is not None:
        eligible = eligible & restrict
    sc = np.where(r & eligible, g, 0.0)
    top = select_top_positive(sc, domain, k)
    return dot_thin(top, min_dist)


# ----------------------------------------------------------------------------------------------
# Holdout evaluation of one surface
# ----------------------------------------------------------------------------------------------
def evaluate_surface(ctx, surface: np.ndarray, label: str, restrict: np.ndarray | None = None) -> dict:
    foot, lab = ctx.foot, ctx.labels
    H = Holdout(foot, lab, HIDE_FRAC)
    fold_dti = {f: [] for f in range(FOLDS)}
    fold_auc = {f: [] for f in range(FOLDS)}
    rows = []
    t0 = time.time()
    for fold in range(FOLDS):
        for draw in DRAWS:
            d = H.draw(fold, draw)
            sl = d.bbox
            surf_c = np.nan_to_num(surface[sl], nan=0.0).astype(np.float32)
            k = int(round(KFRAC * int(d.quadrant[sl].sum())))
            restrict_c = None if restrict is None else restrict[sl]
            emitted_c = emit(surf_c, d.quadrant[sl], d.visible[sl], k, DOT_MIN_DIST, restrict_c)
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
# LANE check vs registry rasters
# ----------------------------------------------------------------------------------------------
def load_registry_rasters() -> list[dict]:
    """Load every local registry GeoTIFF available, including shipped downloads.

    Do not silently ignore an unreadable raster: a partial registry is not a
    lane clearance. The caller records/raises on a read failure.
    """
    import rasterio
    paths = []
    for directory in (REGISTRY_DIR, data_dir() / "calibration", ROOT / "docs" / "downloads"):
        if directory.exists():
            paths.extend(sorted(directory.glob("*.tif")))
    out = []
    seen = set()
    for p in paths:
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        try:
            with rasterio.open(p) as s:
                arr = np.nan_to_num(s.read(1), nan=0.0).astype(np.float32)
        except Exception as e:
            raise RuntimeError(f"lane registry raster unreadable: {p}: {e}") from e
        out.append(dict(file=p.name, arr=arr, sha256=digest))
    return out


def lane_check(ctx, emitted: np.ndarray, surface: np.ndarray, registry: list[dict]) -> dict:
    """Apply the literal parallel-lane rule to one full-footprint candidate.

    ``emitted`` must be on the same full grid as the registry rasters. Failing
    closed on cropped arrays prevents interpreting crop-local indices as global
    coordinates; an empty registry cannot certify uniqueness.
    """
    foot, fi = ctx.foot, ctx.fi
    if emitted.shape != foot.shape or surface.shape != foot.shape:
        raise ValueError("lane check requires full-grid emitted and surface arrays")
    surf_finite = np.where(foot, surface, np.nan).ravel()[fi]
    my_dots = np.flatnonzero((emitted > 0).ravel() & foot.ravel())
    H, W = foot.shape
    my_rc = np.column_stack([my_dots // W, my_dots % W]) if my_dots.size else np.empty((0, 2), int)
    results = []
    for reg in registry:
        if reg["arr"].shape != foot.shape:
            results.append(dict(file=reg["file"], skipped="shape differs", duplicate=True))
            continue
        reg_flat = np.where(foot, reg["arr"], np.nan).ravel()[fi]
        finite = ~(np.isnan(surf_finite) | np.isnan(reg_flat))
        corr = float("nan")
        if finite.sum() >= 1000:
            corr = float(spearmanr(surf_finite[finite], reg_flat[finite], nan_policy="omit").statistic)
        overlap = 0.0
        reverse_overlap = 0.0
        coverage = 0.0
        reg_n = 0
        reg_mask = (reg["arr"] > 0) & foot
        reg_n = int(reg_mask.sum())
        if reg_n:
            dist_to_reg = distance_transform_edt(~reg_mask)
            coverage = float(((dist_to_reg <= LANE_RADIUS_PX) & foot).sum() / max(int(foot.sum()), 1))
        if my_dots.size and reg_n:
            reg_dots = np.flatnonzero(reg_mask.ravel())
            reg_rc = np.column_stack([reg_dots // W, reg_dots % W])
            dist = cKDTree(reg_rc).query(my_rc, k=1)[0]
            overlap = float((dist <= LANE_RADIUS_PX).mean())
            rdist = cKDTree(my_rc).query(reg_rc, k=1)[0]
            reverse_overlap = float((rdist <= LANE_RADIUS_PX).mean())
        rho_flag = not math.isnan(corr) and abs(corr) > LANE_CORR_CAP
        overlap_flag = overlap > LANE_OVERLAP_CAP
        # Density-aware companion (pre-registered knowledge/22 section 4): a registry
        # raster whose own 3-px halo covers >= 70% of the footprint fails *any* dot
        # set (including a uniformly random one, whose expected overlap is the halo
        # coverage), so for those rasters the symmetric statistic decides. The
        # literal flag above is kept unchanged and always reported.
        dense_nondiscriminative = bool(coverage >= LANE_OVERLAP_CAP)
        sym_min = float(min(overlap, reverse_overlap))
        lane_overlap_flag = bool(sym_min > LANE_OVERLAP_CAP) if dense_nondiscriminative else bool(overlap_flag)
        results.append(dict(file=reg["file"], spearman=corr, abs_spearman=abs(corr) if not math.isnan(corr) else None,
                            overlap_within_3px=overlap, flag_rank=rho_flag, flag_overlap=overlap_flag,
                            duplicate=bool(rho_flag or overlap_flag),
                            registry_dots=reg_n, halo_coverage_3px=coverage,
                            reverse_overlap_within_3px=reverse_overlap,
                            symmetric_min_overlap_3px=sym_min,
                            excess_overlap_over_coverage=float(overlap - coverage),
                            non_discriminative_dense=dense_nondiscriminative,
                            flag_overlap_lane=lane_overlap_flag,
                            duplicate_lane=bool(rho_flag or lane_overlap_flag)))
    return results


def lane_is_clear(results: list[dict]) -> bool:
    """A missing/unreadable registry is not evidence of uniqueness."""
    return bool(results) and all(not row.get("duplicate", True) for row in results)


def lane_is_clear_density_aware(results: list[dict]) -> bool:
    """Density-aware lane verdict (knowledge/22 section 4); fails closed like lane_is_clear."""
    return bool(results) and all(not row.get("duplicate_lane", True) for row in results)


def full_footprint_emission(surface: np.ndarray, foot: np.ndarray, labels: np.ndarray,
                            restrict: np.ndarray | None = None) -> np.ndarray:
    """Generate the exact full-grid emission used by the registered candidate recipe."""
    k = int(round(KFRAC * int(foot.sum())))
    return emit(surface, foot, labels, k, DOT_MIN_DIST, restrict)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, nargs="+", default=_DRAWS_DEFAULT,
                    help="hide-and-recover draws (screen=0 1; confirmation=2 3)")
    args = ap.parse_args()
    global DRAWS
    DRAWS = list(args.draws)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = work_dir()
    ctx = load_context(work)
    bands_dir = work / "bands"
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi

    candidates = {
        "GEM-1_blind_magnetics": surface_gem1(foot, bands_dir),
        "GEM-2_vents_x_thermal": surface_gem2(foot, bands_dir),
    }
    restrict_gem3 = off_trace_mask(lab, foot)
    candidates["GEM-3_off_trace_dots"] = candidates["GEM-1_blind_magnetics"]
    _ctrl_vec = np.asarray(ctx.static[ctx.static_names.index("B_crest")], np.float32)
    control_surface = np.zeros(foot.shape, np.float32)
    control_surface.ravel()[fi] = _ctrl_vec

    registry = load_registry_rasters()
    print(f"LANE: {len(registry)} registry rasters loaded", flush=True)

    report = {"design": {"draws": DRAWS, "folds": FOLDS, "hide_frac": HIDE_FRAC, "kfrac": KFRAC,
                         "dot_min_dist": DOT_MIN_DIST, "gate": {"min_gain": PAIRED_GATE_MIN_GAIN,
                                                                "min_folds_positive": PAIRED_GATE_MIN_FOLDS_POSITIVE,
                                                                "worst_fold": PAIRED_GATE_WORST_FOLD},
                         "leakage_auc_cap": LEAKAGE_AUC_CAP,
                         "lane": {"corr_cap": LANE_CORR_CAP, "overlap_cap": LANE_OVERLAP_CAP,
                                  "radius_px": LANE_RADIUS_PX}},
            "candidates": {}}

    control_res = evaluate_surface(ctx, control_surface, "control_B_crest")
    report["candidates"]["control_B_crest"] = {k: v for k, v in control_res.items() if k != "rows"}
    print(f"control mean DTI {control_res['mean_dti']:.6f} worst AUC {control_res['worst_auc']:.3f}",
          flush=True)

    for label, surface in candidates.items():
        restrict = restrict_gem3 if label.startswith("GEM-3") else None
        res = evaluate_surface(ctx, surface, label, restrict)
        report["candidates"][label] = {k: v for k, v in res.items() if k != "rows"}
        gate = paired_gate(res["by_fold"], control_res["by_fold"])
        report["candidates"][label]["paired_vs_control"] = gate
        print(f"{label}: mean DTI {res['mean_dti']:.6f} worst AUC {res['worst_auc']:.3f} | "
              f"paired gain {gate['mean_gain']:+.6f} {gate['folds_positive']}/4 folds "
              f"worst {gate['worst_fold']:+.6f} -> {'PASS' if gate['passed'] else 'fail'}",
              flush=True)

    # Lane checks are computed independently for EVERY candidate surface and its
    # exact full-footprint emission. A fold-cropped emission is never passed into
    # a full-grid proximity test.
    lane_by_candidate = {}
    per_candidate = {}
    for cand, surface in candidates.items():
        if cand == "GEM-3_off_trace_dots":
            restrict = off_trace_mask(lab, foot)
        else:
            restrict = None
        emitted = full_footprint_emission(surface, foot, lab, restrict)
        lane_rows = lane_check(ctx, emitted, surface, registry)
        lane_by_candidate[cand] = lane_rows
        lane_ok = lane_is_clear(lane_rows)
        for row in lane_rows:
            print(f"LANE {cand} vs {row['file']}: "
                  f"rho={row.get('spearman', float('nan')):+.3f} "
                  f"overlap={row.get('overlap_within_3px', float('nan')):.3f} "
                  f"{'DUPLICATE' if row.get('duplicate', True) else 'ok'}", flush=True)
        gate = report["candidates"][cand]["paired_vs_control"]
        leakage_ok = report["candidates"][cand]["worst_auc"] <= LEAKAGE_AUC_CAP
        per_candidate[cand] = {
            "gate_passed": bool(gate["passed"]),
            "leakage_ok": bool(leakage_ok),
            "lane_ok": bool(lane_ok),
            "eligible_for_artifact": bool(gate["passed"] and leakage_ok and lane_ok),
            "lane_registry_checked": len(lane_rows),
            "emitted_full_footprint": int(emitted.sum()),
        }
    report["lane_by_candidate"] = lane_by_candidate
    eligible = [name for name, values in per_candidate.items() if values["eligible_for_artifact"]]
    package_candidate = eligible[0] if eligible else None
    report["decision"] = {
        "per_candidate": per_candidate,
        "package_tif": package_candidate is not None,
        "package_candidate": package_candidate,
        "reason": ("A candidate passed the paired holdout, leakage and strict lane checks." if package_candidate
                   else "No candidate passed all gates. The parallel-run rule is literal: any absolute Spearman > 0.90 or >70% of candidate dots within 3 px of any single registry raster is a duplicate and stops packaging. An empty registry also fails closed."),
    }
    print("DECISION:", json.dumps(report["decision"]), flush=True)
    (OUT_DIR / "results.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT_DIR / 'results.json'}", flush=True)


if __name__ == "__main__":
    main()
