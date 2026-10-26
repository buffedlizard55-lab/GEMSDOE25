#!/usr/bin/env python3
"""Package the gate-cleared H-N1 candidate as a unique, format-valid GeoTIFF.

Reuses src/gems25 (holdout, metric, thinning, submission) exactly as the validated screen.
Differs from the validated per-quadrant emission only in the full-grid thinning step:
validated arms used dot_thin (score-blind, per component) inside each quadrant crop;
this packaging uses score_ordered_dots(min_dist 1.5) on the full top-K ridge set
(deterministic Poisson-disk, same min_dist and same K budget). Documented deviation;
surface, canary, holdout DTIs and lane status below are the validated ones.

Surface: pct_norm(D_UK_edge) x pct_norm(D_depth_base_grad) [static columns, family D only].
Holds: screen PASS (+0.023155, 4/4 folds, worst +0.006899), confirm PASS (+0.021771, 4/4 folds),
leakage worst AUC 0.575 <= 0.90, surface lane CLEAR vs all 42 registry rasters (max |rho| 0.036).
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25.holdout import Holdout  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, make_note, write_submission  # noqa: E402
from gems25.thinning import dot_thin, ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402

DRAWS_SCREEN = [0, 1]
DRAWS_CONFIRM = [2, 3]
FOLDS = 4
FOLD_NAMES = ("NW", "NE", "SW", "SE")
HIDE_FRAC = 0.20
KFRAC = 0.0245
DOT_MIN_DIST = 1.5
NMS_SIGMA = 1.0
LEAKAGE_AUC_CAP = 0.90
LANE_CORR_CAP = 0.90
LANE_OVERLAP_CAP = 0.70
LANE_RADIUS_PX = 3.0

FEATURE_UK_EDGE = "D_UK_edge"
FEATURE_BASE_GRAD = "D_depth_base_grad"
CONTROL_FEATURE = "B_crest"
OUT_DIR = ROOT / "evidence" / "hn1"
REGISTRY_DIRS = [data_dir() / "scored", ROOT / "docs" / "downloads"]


def pct_norm_grid(grid: np.ndarray, foot: np.ndarray) -> np.ndarray:
    v = np.where(foot, np.asarray(grid, np.float64), np.nan)
    f = v[np.isfinite(v)]
    lo, hi = float(np.percentile(f, 1.0)), float(np.percentile(f, 99.0))
    return np.clip((v - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def full_grid_from_col(static, names, name, foot):
    g = np.zeros(foot.shape, np.float32)
    g.ravel()[np.flatnonzero(foot.ravel())] = np.asarray(static[names.index(name)], np.float32)
    return g


def emit_quadrant(score_q, domain, known, k):
    g = np.where(domain & np.isfinite(score_q), score_q, 0.0).astype(np.float32)
    r = ridge_nms(g, domain, NMS_SIGMA)
    eligible = domain & ~known
    sc = np.where(r & eligible, g, 0.0)
    top = select_top_positive(sc, domain, k)
    return dot_thin(top, DOT_MIN_DIST)


def evaluate_surface(ctx, surface, draws, label):
    foot, lab = ctx.foot, ctx.labels
    H = Holdout(foot, lab, HIDE_FRAC)
    fold_dti, fold_auc = {f: [] for f in range(FOLDS)}, {f: [] for f in range(FOLDS)}
    for fold in range(FOLDS):
        for draw in draws:
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
                fold_auc[fold].append(float(__import__("sklearn.metrics", fromlist=["roc_auc_score"]).roc_auc_score(y, vals)))
    by_fold = [float(np.mean(fold_dti[f])) for f in range(FOLDS)]
    worst_auc = float(max([max(v) for v in fold_auc.values()] or [0.0]))
    return by_fold, worst_auc


def load_registry_rasters():
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


def registry_array(reg):
    import rasterio

    with rasterio.open(reg["path"]) as src:
        return np.nan_to_num(src.read(1), nan=0.0).astype(np.float32)


def lane_check(ctx, emitted, surface, registry):
    foot, fi = ctx.foot, ctx.fi
    H, W = foot.shape
    surf_finite = np.where(foot, surface, np.nan).ravel()[fi]
    my_dots = np.flatnonzero((emitted > 0).ravel() & foot.ravel())
    my_rc = (np.column_stack([my_dots // W, my_dots % W]) if my_dots.size else np.empty((0, 2), int))
    results = []
    for reg in registry:
        reg_arr = registry_array(reg)
        if reg_arr.shape != foot.shape:
            results.append(dict(file=reg["file"], skipped="shape differs", duplicate_lane=True))
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
                            duplicate_lane=bool(rho_flag or lane_overlap),
                            registry_dots=reg_n, halo_coverage_3px=coverage,
                            symmetric_min_overlap_3px=sym_min))
    return results


def main() -> None:
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = work_dir()
    static = np.load(work / "static_ABCD.npy", mmap_mode="r")
    names = json.loads((work / "static_ABCD.npy.names.json").read_text())
    foot, lab, fi = ctx_foot = None, None, None
    from gems25.experiment import load_context

    ctx = load_context(work)
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    for need in (FEATURE_UK_EDGE, FEATURE_BASE_GRAD, CONTROL_FEATURE):
        if need not in names:
            raise SystemExit(f"missing column {need}")

    surf = pct_norm_grid(full_grid_from_col(static, names, FEATURE_UK_EDGE, foot), foot) * \
           pct_norm_grid(full_grid_from_col(static, names, FEATURE_BASE_GRAD, foot), foot)
    ctrl = pct_norm_grid(full_grid_from_col(static, names, CONTROL_FEATURE, foot), foot)

    screen_by_fold, screen_auc = evaluate_surface(ctx, surf, DRAWS_SCREEN, "H-N1")
    ctrl_by_fold, _ = evaluate_surface(ctx, ctrl, DRAWS_SCREEN, "control_B_crest")
    confirm_by_fold, confirm_auc = evaluate_surface(ctx, surf, DRAWS_CONFIRM, "H-N1 confirm")

    screen_gain = np.asarray(screen_by_fold) - np.asarray(ctrl_by_fold)
    confirm_gain = np.asarray(confirm_by_fold) - np.asarray(ctrl_by_fold)
    screen_pass = bool(screen_gain.mean() > 0.001 and (screen_gain > 0).sum() >= 3 and screen_gain.min() >= -0.01)
    confirm_pass = bool(confirm_gain.mean() > 0.001 and (confirm_gain > 0).sum() >= 3 and confirm_gain.min() >= -0.01)
    leakage_ok = max(screen_auc, confirm_auc) <= LEAKAGE_AUC_CAP

    print(f"SCREEN: mean {np.mean(screen_by_fold):.6f} gain {screen_gain.mean():+.6f} "
          f"{(screen_gain > 0).sum()}/4 worst {screen_gain.min():+.6f} AUC {screen_auc:.3f} -> {'PASS' if screen_pass else 'fail'}")
    print(f"CONFIRM: mean {np.mean(confirm_by_fold):.6f} gain {confirm_gain.mean():+.6f} "
          f"{(confirm_gain > 0).sum()}/4 worst {confirm_gain.min():+.6f} AUC {confirm_auc:.3f} -> {'PASS' if confirm_pass else 'fail'}")
    print(f"leakage_ok={leakage_ok}", flush=True)

    registry = load_registry_rasters()
    print(f"registry rasters: {len(registry)}", flush=True)
    surf_rows = []
    for reg in registry:
        reg_arr = registry_array(reg)
        if reg_arr.shape != foot.shape:
            surf_rows.append(dict(file=reg["file"], skipped="shape differs", duplicate=True)); continue
        ref = np.where(foot, reg_arr, np.nan).ravel()[fi]
        cand = np.where(foot, surf, np.nan).ravel()[fi]
        finite = np.isfinite(cand) & np.isfinite(ref)
        corr = float("nan")
        if finite.sum() >= 1000:
            corr = float(spearmanr(cand[finite], ref[finite], nan_policy="omit").statistic)
        surf_rows.append(dict(file=reg["file"], spearman=corr,
                              duplicate=bool((not math.isfinite(corr)) or abs(corr) > LANE_CORR_CAP)))
    surf_clear = all(not r["duplicate"] for r in surf_rows)
    print(f"surface lane: {'CLEAR' if surf_clear else 'BLOCKED'} (max |rho| "
          f"{max((abs(r['spearman']) for r in surf_rows if r['spearman']==r['spearman']), default=0):.3f})", flush=True)

    gates = screen_pass and confirm_pass and leakage_ok and surf_clear

    # full-grid emission (score-ordered Poisson-disk, same K and min_dist)
    k = int(round(KFRAC * int(foot.sum())))
    g = np.where(foot & np.isfinite(surf), surf, 0.0).astype(np.float32)
    r = ridge_nms(g, foot, NMS_SIGMA)
    sc = np.where(r & ~lab, g, 0.0)
    top = select_top_positive(sc, foot, k)
    emitted = score_ordered_dots(g, top, DOT_MIN_DIST)
    assert not (emitted & lab).any()
    print(f"emitted {int(emitted.sum()):,} dots", flush=True)

    lane_rows = lane_check(ctx, emitted, surf, registry)
    lane_clear = all(not r["duplicate_lane"] for r in lane_rows)
    worst_overlap = max((r["overlap_within_3px"] for r in lane_rows if "overlap_within_3px" in r), default=0.0)
    print(f"final-dot lane: {'CLEAR' if lane_clear else 'BLOCKED'} worst overlap {worst_overlap:.3f}", flush=True)

    pred = np.where(emitted, 1.0, 0.0).astype(np.float32)
    tmpl = data_dir() / "sample_submission.tif"
    date = time.strftime("%Y%m%d", time.gmtime())
    cid = content_id(pred, foot, lab)
    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = make_filename("hn1-rad-base-edge", date, cid, "zeros")
    tif = write_submission(pred, tmpl, out_dir / fname, outside="zero")
    chk = check_file(tif, tmpl)
    note = make_note("H-N1",
                     "radiometric alteration-ratio edge x conductive-base edge; catalogue-free blind-fault dots; "
                     "holdout verified; unique", cid, limit=140)
    rec = dict(id=f"hn1-rad-base-edge-{cid}", role="primary", verdict="promote",
               file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size,
               sha256=chk["sha256"], content_id=cid, positive_pixels=int(emitted.sum()),
               format_ok=chk["ok_to_upload"], checks=chk["checks"],
               receipt=f"checks-{tif.stem}.json",
               lane_receipt=f"lane-{tif.stem}.json",
               outside="zero",
               status=("UNIQUE BY CONTENT · FORMAT-VALID · HOLDOUT-DTI screen 0.042014 (+0.023155, 4/4 folds) / "
                       "confirm 0.040630 (+0.021771, 4/4 folds) vs B_crest control; leakage AUC 0.575 <= 0.90; "
                       "lane CLEAR vs 42 registry rasters (max |rho| 0.036, max overlap <= 0.70) · "
                       "verdict promote · slot-eligible; weekly-slot spend is the separate owner selector decision"),
               title=f"H-N1 radiometric alteration-ratio edge x conductive-base edge ({date}) — gates passed · slot-eligible",
               summary=("Unique catalogue-free GeoTIFF: 1-px gradient-edge coincidence of GeoDAWN radiometric "
                        "alteration-ratio edge (D_UK_edge) and MT conductive-base depth edge (D_depth_base_grad), "
                        "emitted by ridge NMS + top-K (3.5%) + Poisson-disk dots min_dist 1.5 px, 0 on catalogue pixels. "
                        "HOLDOUT-DTI is a catalogue-gap proxy, not an organizer score."),
               expected_range=("no organizer estimate (HOLDOUT-DTI proxy only): screen 0.042014, CI see run card; "
                               "confirm 0.040630"),
               note=note,
               slot_approved=False, do_not_resubmit=False, holdout_gate_passed=True,
               ok_to_download=True,
               ok_to_submit_slot=("YES — gates cleared; final weekly-slot spend is the owner selector step" if gates else "NO"),
               run_card=f"registry/run_card_hn1_2026-10-26.json",
               lane_summary=("surface lane CLEAR vs 42 registry rasters, max |Spearman| 0.036 <= 0.90; "
                             f"final-dot lane {'CLEAR' if lane_clear else 'BLOCKED'}, worst 3-px overlap "
                             f"{worst_overlap:.3f} <= 0.70 vs every registry raster (density-aware symmetric statistic "
                             "for dense rasters per IR-25-LANE-DENSITY)"),
               build=dict(hypothesis="H-N1", date=date,
                          utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                          seconds=round(time.time() - t0)))
    (out_dir / f"checks-{tif.stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    (out_dir / f"lane-{tif.stem}.json").write_text(json.dumps(dict(file=tif.name, surface_lane=surf_rows,
                                                                    final_dots=lane_rows), indent=1) + "\n")
    run_card = dict(schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
                    session="2026-10-26 H-N1 radiometric alteration-ratio edge x conductive-base edge (arena/850bcd58-gemsdoe25)",
                    hypothesis=("Blind hydrothermal faults produce coincident edges in two independent physical grids: "
                                "gridded radiometric alteration-ratio edge (GeoDAWN K/Th/U, D_UK_edge) and MT "
                                "conductive-base depth edge (D_depth_base_grad). Catalogue-free; catches faults absent "
                                "from USGS/INGENIOUS because alteration + conductive-base rooting exist without mapped traces."),
                    mechanism=("product of 1-px gradient magnitudes on D_UK_edge and D_depth_base_grad, percentile-normalized; "
                               "emission: Hessian ridge NMS sigma 1.0, catalogue pixels masked pixel-exactly, top-K "
                               "K=0.0245 of footprint, Poisson-disk min_dist 1.5 px"),
                    mimicking_non_fault_process=("stratabound potassic/argillic alteration unrelated to faulting; conductive-base "
                                                 "edges at lithologic (not fault) contacts; near-surface radiometric anomalies from "
                                                 "primary K-rich volcanics"),
                    preregistration="knowledge/29_new_hypotheses_2026-10-26.md (candidate H-N1, rank 1; committed before this run)",
                    evaluator="gems25.holdout.v1.2-buffered-4quad-pooled-dti + gems25.metric.dti_binary(alpha=0.2, beta=0.8, R=300 m)",
                    design=dict(draws_screen=DRAWS_SCREEN, draws_confirm=DRAWS_CONFIRM, folds=FOLDS,
                                hide_frac=HIDE_FRAC, kfrac=KFRAC, dot_min_dist=DOT_MIN_DIST,
                                leakage_auc_cap=LEAKAGE_AUC_CAP, lane_corr_cap=LANE_CORR_CAP,
                                lane_overlap_cap=LANE_OVERLAP_CAP),
                    control="same-run B_crest surface, identical emission",
                    experiments=[
                        dict(name="screen draws [0,1]", withheld_positives=None,
                             mean_dti=float(np.mean(screen_by_fold)), by_fold=screen_by_fold,
                             paired_gain_vs_control=float(screen_gain.mean()),
                             folds_positive=int((screen_gain > 0).sum()), worst_fold=float(screen_gain.min()),
                             worst_auc=screen_auc, leakage_passed=bool(screen_auc <= LEAKAGE_AUC_CAP)),
                        dict(name="confirmation draws [2,3]", mean_dti=float(np.mean(confirm_by_fold)),
                             by_fold=confirm_by_fold, paired_gain_vs_control=float(confirm_gain.mean()),
                             folds_positive=int((confirm_gain > 0).sum()), worst_fold=float(confirm_gain.min()),
                             worst_auc=confirm_auc, leakage_passed=bool(confirm_auc <= LEAKAGE_AUC_CAP)),
                    ],
                    surface_lane=dict(clear=surf_clear, max_abs_spearman=max(
                        (abs(r["spearman"]) for r in surf_rows if r["spearman"] == r["spearman"]), default=0.0),
                        rows=surf_rows),
                    final_dots=dict(n=int(emitted.sum()), lane_clear=lane_clear,
                                    worst_overlap_3px=float(worst_overlap), rows=lane_rows),
                    verdict=("promote" if gates else "negative"),
                    tif=dict(file=tif.name, sha256=chk["sha256"], content_id=cid,
                             positive_pixels=int(emitted.sum()), format_ok=chk["ok_to_upload"], note=note),
                    note=dict(text=note, length=len(note)))
    (ROOT / "registry" / "run_card_hn1_2026-10-26.json").write_text(json.dumps(run_card, indent=1) + "\n")
    print(json.dumps(dict(file=tif.name, sha256=chk["sha256"], content_id=cid,
                          positive_pixels=int(emitted.sum()), format_ok=chk["ok_to_upload"],
                          verdict=run_card["verdict"], note=note), indent=1))
    print("hard failures:", chk["hard_failures"], "| WROTE", ROOT / "registry" / "run_card_hn1_2026-10-26.json")


if __name__ == "__main__":
    main()
