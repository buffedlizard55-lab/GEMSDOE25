#!/usr/bin/env python3
"""Build the unique GEMSDOE25 H31-1 full-catalogue GeoTIFF, verify format checks, and run the duplicate-lane audit.

Trains the preregistered H31-1 (`M1_C1`) model on 3 hide-and-recover draws of the full catalogue:
- Features: families B, D, E + H26 add-ons (X1, X2, X3) + H27_tip + H31_subscarp_concord + H31_offflank_tip_halo
- Emission: Hessian ridge NMS (sigma=1.0) -> tip-preserved lateral-flank shield (d(cat) > 2.5 px or H27_tip >= 0.05)
  -> top-K (K = 0.035 * footprint) -> score-ordered Poisson-disk dotting (min_dist = 2.4 px).
- Verifies all 16 format checks via `gems25.submission.check_file` and checks Protocol Rule 1
  (surface Spearman rank correlation <= 0.90 and 3-px dot overlap <= 0.70) against all restored registry
  and focus-site rasters.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h31 import (  # noqa: E402
    H31_BASE_EXTRAS,
    H31_FEATURE_NAMES,
    build_offflank_tip_halo,
    candidates_flank_shielded,
    check_duplicate_lane_against_registry,
)
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, make_note, write_submission  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402


def assemble_matrix(ctx, E: np.ndarray, tip: np.ndarray, halo: np.ndarray, idx: np.ndarray) -> np.ndarray:
    ns, ne = ctx.static.shape[0], E.shape[0]
    n_extra = len(ctx.extra_names)
    X = np.empty((idx.size, ns + ne + n_extra + 3 + 2 + 2), np.float32)
    gather_columns(ctx, E, idx, extras=True, out=X)
    j = ns + ne + n_extra
    scarp = ctx.h27_scarp[idx]
    t_sub = tip[idx]
    X[:, j] = t_sub
    X[:, j + 1] = scarp
    X[:, j + 2] = t_sub * scarp
    j += 3
    X[:, j] = 0.0
    X[:, j + 1] = 0.0
    j += 2
    X[:, j] = ctx.h31_subscarp[idx]
    X[:, j + 1] = halo[idx]
    return X


def list_all_registry_raster_paths(d: Path) -> dict[str, Path]:
    rasters: dict[str, Path] = {}
    for folder in (d / "scored", d / "artifacts", d / "sibling_focus"):
        if not folder.exists():
            continue
        for p in sorted(folder.glob("*.tif")):
            rasters[f"{folder.name}/{p.name}"] = p
    return rasters


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--kfrac", type=float, default=0.035)
    ap.add_argument("--min-dist", type=float, default=2.4)
    ap.add_argument("--flank-radius", type=float, default=2.5)
    ap.add_argument("--tip-threshold", type=float, default=0.05)
    ap.add_argument("--date", default="20261025")
    ap.add_argument("--slug", default="h31-1-flank-subscarp-sapd24")
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    args = ap.parse_args()

    t0 = time.time()
    w = work_dir()
    d = data_dir()
    ctx = load_context(w)
    ctx.ensure_h31_subscarp()
    cols = ctx.columns("BDE") + ctx.named(H31_BASE_EXTRAS) + ctx.named(["H27_tip"]) + ctx.named(H31_FEATURE_NAMES)
    H = ctx.holdout
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    print(f"[{time.time() - t0:.0f}s] H31-1 full-catalogue build: {len(cols)} feature columns", flush=True)

    E_full = build_catalogue_features(lab, fi)
    tip_full = build_tip_continuation(lab, foot, fi)
    halo_full, halo_full_diag = build_offflank_tip_halo(lab, tip_full, foot, fi)

    cached_scores = w / "h31_full_scores.npy"
    if cached_scores.exists():
        p = np.load(cached_scores)
        print(f"[{time.time() - t0:.0f}s] loaded cached full-catalogue scores from {cached_scores}", flush=True)
    else:
        p_sum = np.zeros(fi.size, np.float32)
        ids = np.arange(1, H.n_comp + 1)
        for m in range(args.draws):
            rng = np.random.default_rng(531_000 + m)
            hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
            hidden = np.isin(H.comp, hid)
            visible = lab & ~hidden
            E_vis = build_catalogue_features(visible, fi)
            tip_vis = build_tip_continuation(visible, foot, fi)
            halo_vis, _ = build_offflank_tip_halo(visible, tip_vis, foot, fi)

            pos = ctx.vec(hidden)
            near = distance_transform_edt(~hidden) <= 1.5
            cand = ctx.vec(foot & ~lab & ~near)
            neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
            idx = np.sort(np.concatenate([pos, neg]))
            y = np.isin(idx, pos).astype(np.int8)
            X = assemble_matrix(ctx, E_vis, tip_vis, halo_vis, idx)[:, cols]
            model = HistGradientBoostingClassifier(random_state=100 + m, **HGB_PARAMS).fit(X, y)
            print(f"[{time.time() - t0:.0f}s] draw {m}: fit on {idx.size:,} rows ({int(y.sum()):,} positives)", flush=True)
            del X, E_vis, tip_vis, halo_vis

            for lo in range(0, fi.size, 500_000):
                sl = np.arange(lo, min(lo + 500_000, fi.size))
                X_chunk = assemble_matrix(ctx, E_full, tip_full, halo_full, sl)[:, cols]
                p_sum[sl] += model.predict_proba(X_chunk)[:, 1].astype(np.float32)
        p = p_sum / float(args.draws)
        np.save(cached_scores, p)
    del E_full, halo_full, ctx
    import gc

    gc.collect()
    grid = np.zeros(foot.shape, np.float32)
    grid.ravel()[fi] = p
    tip_grid = np.zeros(foot.shape, np.float32)
    tip_grid.ravel()[fi] = tip_full
    del tip_full
    gc.collect()

    k = int(round(args.kfrac * foot.sum()))
    score_crop, top_candidates, shield_diag = candidates_flank_shielded(
        grid,
        foot,
        lab & foot,
        tip_grid,
        k,
        nms_sigma=1.0,
        flank_radius_px=args.flank_radius,
        tip_preserve_threshold=args.tip_threshold,
    )
    del grid, tip_grid
    gc.collect()
    em = score_ordered_dots(score_crop, top_candidates, args.min_dist)
    del score_crop, top_candidates
    gc.collect()
    assert not (em & lab).any(), "emission on a known catalogue pixel"

    pred = np.where(em, 1.0, 0.0).astype(np.float32)
    tmpl = d / "sample_submission.tif"
    cid = content_id(pred, foot, lab)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    fname_nan = make_filename(args.slug, args.date, cid, "nan")
    fname_zero = fname_nan.replace("-nan.tif", "-zeros.tif")
    tif_nan = write_submission(pred, tmpl, out_dir / fname_nan, outside="nan")
    tif_zero = write_submission(pred, tmpl, out_dir / fname_zero, outside="zero")

    chk_nan = check_file(tif_nan, tmpl)
    chk_zero = check_file(tif_zero, tmpl)
    del pred
    gc.collect()

    # Protocol Rule 1: Duplicate-lane check on BOTH continuous surface and final dots vs registry + focus sites
    reg_rasters = list_all_registry_raster_paths(d)
    dup_audit = check_duplicate_lane_against_registry(p, em, foot, reg_rasters)
    if not dup_audit["passed"]:
        raise SystemExit(f"DUPLICATE-LANE GATE VIOLATION: {json.dumps(dup_audit, indent=2)}")

    dist_cat = distance_transform_edt(~(lab & foot))
    em_dc = dist_cat[em]
    dist_profile = {
        "on_catalogue_0px": int((em & lab).sum()),
        "d_in_0_1px": int((em & (dist_cat > 0.0) & (dist_cat <= 1.0)).sum()),
        "d_in_1_2px": int((em & (dist_cat > 1.0) & (dist_cat <= 2.0)).sum()),
        "d_in_2_2p5px": int((em & (dist_cat > 2.0) & (dist_cat <= 2.5)).sum()),
        "d_in_2p5_3px": int((em & (dist_cat > 2.5) & (dist_cat <= 3.0)).sum()),
        "d_gt_3px": int((em & (dist_cat > 3.0)).sum()),
        "min_dist_to_catalogue_px": float(em_dc.min()),
        "p5_dist_to_catalogue_px": float(np.percentile(em_dc, 5)),
        "median_dist_to_catalogue_px": float(np.median(em_dc)),
        "hug_share_within_3px": float(np.mean(em_dc <= 3.0)),
    }

    note_nan = make_note(
        "H31-1",
        "flank-shielded subscarp sapd2.4; unscored; not slot-approved",
        cid,
        scored="no slot",
    )
    note_zero = make_note(
        "H31-1 zeros",
        "format fallback, zeros outside; unscored; not slot-approved",
        cid,
        scored="no slot",
    )

    receipt_doc = {
        "file": tif_nan.name,
        "path": f"docs/downloads/{tif_nan.name}",
        "bytes": tif_nan.stat().st_size,
        "sha256": chk_nan["sha256"],
        "content_id": cid,
        "positive_pixels": chk_nan["positive_pixels"],
        "format_ok": chk_nan["ok_to_upload"],
        "hard_failures": chk_nan["hard_failures"],
        "official_nan_outside": chk_nan["official_nan_outside"],
        "footprint_pixels": chk_nan["footprint_pixels"],
        "checks": chk_nan["checks"],
        "note": note_nan,
        "fallback": {
            "file": tif_zero.name,
            "path": f"docs/downloads/{tif_zero.name}",
            "bytes": tif_zero.stat().st_size,
            "sha256": chk_zero["sha256"],
            "positive_pixels": chk_zero["positive_pixels"],
            "format_ok": chk_zero["ok_to_upload"],
            "note": note_zero,
        },
        "distance_to_catalogue_profile": dist_profile,
        "shield_diagnostics": shield_diag,
        "offflank_halo_diagnostics": halo_full_diag,
        "duplicate_lane_check": {
            "passed": dup_audit["passed"],
            "n_registry_rasters_checked": dup_audit["n_registry_rasters_checked"],
            "max_spearman_surface": dup_audit["max_spearman_surface"],
            "max_dot_share_within_3px": dup_audit["max_dot_share_within_3px"],
            "thresholds": dup_audit["thresholds"],
        },
        "build": {
            "hypothesis": "H31-1 (M1_C1)",
            "base_families": "BDE",
            "addons": H31_BASE_EXTRAS,
            "extra_features": ["H27_tip", *H31_FEATURE_NAMES],
            "draws": args.draws,
            "kfrac": args.kfrac,
            "min_dist_px": args.min_dist,
            "flank_radius_px": args.flank_radius,
            "tip_preserve_threshold": args.tip_threshold,
            "seconds": round(time.time() - t0, 1),
        },
    }
    receipt_path = out_dir / f"checks-{tif_nan.stem}.json"
    receipt_path.write_text(json.dumps(receipt_doc, indent=1) + "\n")

    dup_path = ROOT / "evidence" / "h31_duplicate_lane_audit.json"
    dup_path.write_text(json.dumps(dup_audit, indent=1) + "\n")

    print(
        json.dumps(
            {
                "file": receipt_doc["file"],
                "sha256": receipt_doc["sha256"],
                "content_id": cid,
                "positive_pixels": receipt_doc["positive_pixels"],
                "format_ok": receipt_doc["format_ok"],
                "note": note_nan,
                "duplicate_lane_passed": dup_audit["passed"],
                "max_spearman_surface": dup_audit["max_spearman_surface"],
                "max_dot_share_within_3px": dup_audit["max_dot_share_within_3px"],
                "distance_to_catalogue_profile": dist_profile,
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
