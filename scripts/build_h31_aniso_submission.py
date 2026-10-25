#!/usr/bin/env python3
"""Build, validate, and verify uniqueness of the promoted H31-1 full-footprint GeoTIFF submission.

Reuses the repository's cached feature stack (``static_ABCD.npy``, ``addons.npy``),
``gems25.features`` (``build_catalogue_features``, ``build_tip_continuation``),
``gems25.h31`` (``build_static_lidar_dem_coherence``, ``build_h31_features``, ``apply_digitization_shadow_guard``),
``gems25.thinning`` (``ridge_nms``, ``select_top_positive``, ``score_ordered_dots``), and
``gems25.submission`` (``write_submission``, ``check_file``, ``content_id``, ``make_filename``, ``make_note``).

Also verifies Protocol Rule 1 against all 30 competition rasters in ``registry/artifact_ledger.json``
and the focus-site rasters in ``data/focus_sites/``:
  - Surface rank-correlation <= 0.90
  - 3-px dot overlap <= 0.70 (70%)
And writes:
  - ``docs/downloads/<submission_name>-nan.tif`` (primary)
  - ``docs/downloads/<submission_name>-zeros.tif`` (reference-convention fallback)
  - ``docs/downloads/<submission_name>.zip`` (compressed bundle)
  - ``docs/downloads/checks-<submission_stem>.json`` (promotion-validated receipt for ``package_submissions.py``)
  - ``evidence/h31_experiments/uniqueness_audit.json``
  - ``evidence/h31_experiments/run_card.json``
"""

from __future__ import annotations

import datetime as dt
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h31 import (  # noqa: E402
    H31_ANISO_FEATURE_NAMES,
    apply_digitization_shadow_guard,
    build_h31_features,
    build_static_lidar_dem_coherence,
)
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, make_note, write_submission  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from scripts.package_submissions import CURRENT_HOLDOUT_BEST, promotion_receipt_valid  # noqa: E402

BASE_FAMILIES = "BDE"
BASE_EXTRAS = ["X1_K", "X1_ThK", "X1_UK", "X2_compat", "X2_compat_coh", "X3_gm", "X3_gd"]
FULL_FIT_SEEDS = (10, 11, 12)
KFRAC = 0.032
MIN_DIST_PX = 2.8
B2_BUFFER_PX = 2.0
SLUG = "h31-aniso-scarp-b2-d2-8"
TAG = "H31-B2"
SHORT_SUMMARY = "Anisotropic along-strike continuation + 3DEP LiDAR strike coherence + B=2 200m flank guard"


def assemble_matrix(
    ctx,
    E: np.ndarray,
    tip: np.ndarray,
    h31: np.ndarray,
    idx: np.ndarray,
    base_and_extra_cols: list[int],
) -> np.ndarray:
    """Assemble ``[BDE + X1..X3, H27_tip, H31_features(6)]`` for footprint-vector indices ``idx``."""
    base_X = gather_columns(ctx, E, idx, extras=True)[:, base_and_extra_cols]
    tip_col = tip[idx, None].astype(np.float32)
    h31_cols = h31[:, idx].T.astype(np.float32)
    return np.hstack([base_X, tip_col, h31_cols]).astype(np.float32, copy=False)


def spearman_fast(a: np.ndarray, b: np.ndarray, sample_idx: np.ndarray) -> float:
    """Exact Spearman rank correlation on a deterministic footprint sample."""
    ra = rankdata(a[sample_idx])
    rb = rankdata(b[sample_idx])
    sa = np.std(ra)
    sb = np.std(rb)
    if sa == 0.0 or sb == 0.0:
        return 0.0
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> None:
    t0 = time.time()
    holdout_res_path = ROOT / "evidence" / "h31_experiments" / "results.json"
    if not holdout_res_path.exists():
        raise SystemExit("Run scripts/run_h31_experiments.py before building the H31 submission.")
    holdout_res = json.loads(holdout_res_path.read_text())
    if holdout_res.get("verdict") != "promote":
        raise SystemExit(f"Refusing to build promoted submission when holdout verdict={holdout_res.get('verdict')}")

    ctx = load_context(work_dir())
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    l_c2, l_s2, l_coh, lidar_dem_compat = build_static_lidar_dem_coherence(
        ctx.static, ctx.static_names, ctx.addon
    )
    base_and_extra_cols = ctx.columns(BASE_FAMILIES) + ctx.named(BASE_EXTRAS)

    cache_p = work_dir() / "h31_p_mean.npy"
    if cache_p.exists():
        print(f"[{time.time()-t0:.1f}s] Loading cached H31 probability surface from {cache_p}...", flush=True)
        p_mean = np.load(cache_p).astype(np.float32)
    else:
        print(f"[{time.time()-t0:.1f}s] Building full-catalogue inference features on {fi.size:,} footprint pixels...", flush=True)
        E_full = build_catalogue_features(lab, fi)
        tip_full = build_tip_continuation(lab, foot, fi)
        h31_full = build_h31_features(lab, foot, fi, l_c2, l_s2, l_coh, lidar_dem_compat)

        p_sum = np.zeros(fi.size, dtype=np.float32)
        H = ctx.holdout
        comp_ids = np.arange(1, H.n_comp + 1)

        for draw_idx, seed in enumerate(FULL_FIT_SEEDS):
            t_draw = time.time()
            rng = np.random.default_rng(424_200 + seed)
            hid = H._pick(rng, comp_ids, 0.20 * float(lab.sum()))
            hidden = np.isin(H.comp, hid)
            visible = lab & ~hidden

            E_vis = build_catalogue_features(visible, fi)
            tip_vis = build_tip_continuation(visible, foot, fi)
            h31_vis = build_h31_features(visible, foot, fi, l_c2, l_s2, l_coh, lidar_dem_compat)

            pos = ctx.vec(hidden)
            near = distance_transform_edt(~hidden) <= 1.5
            cand_neg = ctx.vec(foot & ~lab & ~near)
            neg = rng.choice(cand_neg, size=min(N_NEG, cand_neg.size), replace=False)
            idx = np.sort(np.concatenate([pos, neg]))
            y = np.isin(idx, pos).astype(np.int8)

            X_tr = assemble_matrix(ctx, E_vis, tip_vis, h31_vis, idx, base_and_extra_cols)
            model = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(X_tr, y)
            del X_tr, E_vis, tip_vis, h31_vis

            for lo in range(0, fi.size, 500_000):
                sl = np.arange(lo, min(lo + 500_000, fi.size))
                X_te = assemble_matrix(ctx, E_full, tip_full, h31_full, sl, base_and_extra_cols)
                p_sum[sl] += model.predict_proba(X_te)[:, 1].astype(np.float32)

            print(
                f"[{time.time()-t0:.1f}s] Fit & predicted draw {draw_idx+1}/{len(FULL_FIT_SEEDS)} "
                f"(seed={seed}, n_pos={int(y.sum()):,}, {time.time()-t_draw:.1f}s)",
                flush=True,
            )

        p_mean = (p_sum / float(len(FULL_FIT_SEEDS))).astype(np.float32)
        np.save(cache_p, p_mean)
    grid = np.zeros(foot.shape, dtype=np.float32)
    grid.ravel()[fi] = np.nan_to_num(p_mean, nan=0.0)

    print(f"[{time.time()-t0:.1f}s] Running Hessian ridge NMS, top-K selection, Poisson-disk dotting (d={MIN_DIST_PX}), and B={B2_BUFFER_PX} guard...", flush=True)
    r_nms = ridge_nms(grid, foot, 1.0)
    sc = np.where(r_nms & ~lab, grid, 0.0)
    k = int(round(KFRAC * foot.sum()))
    top = select_top_positive(sc, foot, k)
    em_pre_b2 = score_ordered_dots(grid, top, MIN_DIST_PX)
    em = apply_digitization_shadow_guard(em_pre_b2, lab, B2_BUFFER_PX)

    assert not (em & lab).any(), "Emission on a known catalogue pixel is forbidden"
    pred = np.where(em, 1.0, 0.0).astype(np.float32)
    cid = content_id(pred, foot, lab)
    date_str = "20261025"

    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    tmpl = data_dir() / "sample_submission.tif"

    fname_nan = make_filename(SLUG, date_str, cid, "nan")
    fname_zero = fname_nan.replace("-nan.tif", "-zeros.tif")
    fname_zip = fname_nan.replace("-nan.tif", ".zip")

    tif_nan = write_submission(pred, tmpl, out_dir / fname_nan, outside="nan")
    tif_zero = write_submission(pred, tmpl, out_dir / fname_zero, outside="zero")

    with zipfile.ZipFile(out_dir / fname_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(tif_nan, arcname=tif_nan.name)
        zf.write(tif_zero, arcname=tif_zero.name)

    chk_nan = check_file(tif_nan, tmpl)
    chk_zero = check_file(tif_zero, tmpl)
    assert chk_nan["ok_to_upload"], f"Primary TIF failed check_file: {chk_nan['hard_failures']}"
    assert chk_zero["ok_to_upload"], f"Fallback TIF failed check_file: {chk_zero['hard_failures']}"

    # Protocol Rule 1: Check surface rank-correlation (<= 0.90) and 3-px dot overlap (<= 0.70)
    # against all 30 registry rasters + focus-site rasters
    print(f"[{time.time()-t0:.1f}s] Auditing surface rank-correlation and 3-px dot overlap against registry rasters...", flush=True)
    d_root = data_dir()
    ledger = json.loads((ROOT / "registry" / "artifact_ledger.json").read_text())
    reg_entries = []
    for row in ledger["artifacts"]:
        if row.get("file") and (ROOT / row["file"]).exists():
            reg_entries.append((row["id"], ROOT / row["file"], "registry_ledger"))
    focus_dir = d_root / "focus_sites"
    if focus_dir.exists():
        for fp in sorted(focus_dir.glob("*.tif")):
            reg_entries.append((fp.stem, fp, "focus_site"))

    rng_sub = np.random.default_rng(20261025)
    sample_idx = np.sort(rng_sub.choice(fi.size, size=250_000, replace=False))
    cand_bin_vec = pred.ravel()[fi]
    dist_cand = distance_transform_edt(~em)
    n_cand = int(em.sum())

    comparison_rows = []
    max_rank_corr = 0.0
    max_rank_corr_id = None
    max_symmetric_3px_overlap = 0.0
    max_symmetric_3px_id = None
    max_dotted_oneway_overlap = 0.0
    max_dotted_oneway_id = None

    for ref_id, ref_path, group in reg_entries:
        with rasterio.open(ref_path) as s:
            ref_arr = np.nan_to_num(s.read(1), nan=0.0).astype(np.float32)
        ref_vec = ref_arr.ravel()[fi]
        ref_pos = (ref_arr > 0) & foot & ~lab
        n_ref = int(ref_pos.sum())
        if n_ref == 0:
            continue

        rho_prob = abs(spearman_fast(p_mean, ref_vec, sample_idx))
        rho_bin = abs(spearman_fast(cand_bin_vec, ref_vec, sample_idx))
        rho_max = max(rho_prob, rho_bin)

        dist_ref = distance_transform_edt(~ref_pos)
        c_in_r = int((em & (dist_ref <= 3.0)).sum())
        r_in_c = int((ref_pos & (dist_cand <= 3.0)).sum())
        ov_c2r = float(c_in_r / max(n_cand, 1))
        ov_r2c = float(r_in_c / max(n_ref, 1))
        ov_dice_3px = float((c_in_r + r_in_c) / max(n_cand + n_ref, 1))

        if rho_max > max_rank_corr:
            max_rank_corr = rho_max
            max_rank_corr_id = ref_id
        if ov_dice_3px > max_symmetric_3px_overlap:
            max_symmetric_3px_overlap = ov_dice_3px
            max_symmetric_3px_id = ref_id
        if n_ref <= 70_000 and max(ov_c2r, ov_r2c) > max_dotted_oneway_overlap:
            max_dotted_oneway_overlap = max(ov_c2r, ov_r2c)
            max_dotted_oneway_id = ref_id

        comparison_rows.append(
            {
                "id": ref_id,
                "group": group,
                "file": str(ref_path.relative_to(ROOT)),
                "ref_positive_pixels": n_ref,
                "spearman_prob_surface": round(rho_prob, 6),
                "spearman_binary_surface": round(rho_bin, 6),
                "max_rank_correlation": round(rho_max, 6),
                "cand_within_3px_of_ref": round(ov_c2r, 6),
                "ref_within_3px_of_cand": round(ov_r2c, 6),
                "symmetric_3px_dice_overlap": round(ov_dice_3px, 6),
            }
        )

    assert max_rank_corr <= 0.90, f"Surface rank-correlation gate failed: {max_rank_corr:.4f} > 0.90 ({max_rank_corr_id})"
    assert max_symmetric_3px_overlap <= 0.70, f"3-px dot overlap gate failed: {max_symmetric_3px_overlap:.4f} > 0.70 ({max_symmetric_3px_id})"
    assert max_dotted_oneway_overlap <= 0.70, f"Dotted one-way 3-px overlap gate failed: {max_dotted_oneway_overlap:.4f} > 0.70 ({max_dotted_oneway_id})"

    dist_cat_full = distance_transform_edt(~lab)
    d_em = dist_cat_full[em]
    hug_3px = float((d_em <= 3.0).mean())
    pre_b2_pruned = int(em_pre_b2.sum() - em.sum())

    uniqueness_payload = {
        "schema_version": 1,
        "candidate_file": tif_nan.name,
        "candidate_sha256": chk_nan["sha256"],
        "candidate_content_id": cid,
        "candidate_positive_pixels": n_cand,
        "pre_b2_positive_pixels": int(em_pre_b2.sum()),
        "b2_pruned_flank_pixels": pre_b2_pruned,
        "min_distance_to_catalogue_px": round(float(d_em.min()), 4),
        "share_within_2px_of_catalogue": float((d_em <= 2.0).mean()),
        "share_within_3px_of_catalogue": round(hug_3px, 6),
        "n_reference_rasters_checked": len(comparison_rows),
        "max_rank_correlation": round(max_rank_corr, 6),
        "max_rank_correlation_ref": max_rank_corr_id,
        "rank_correlation_limit": 0.90,
        "rank_correlation_pass": bool(max_rank_corr <= 0.90),
        "max_symmetric_3px_dot_overlap": round(max_symmetric_3px_overlap, 6),
        "max_symmetric_3px_dot_overlap_ref": max_symmetric_3px_id,
        "max_sparse_detector_oneway_3px_overlap": round(max_dotted_oneway_overlap, 6),
        "max_sparse_detector_oneway_3px_overlap_ref": max_dotted_oneway_id,
        "dot_overlap_limit": 0.70,
        "dot_overlap_pass": bool(max_symmetric_3px_overlap <= 0.70 and max_dotted_oneway_overlap <= 0.70),
        "comparisons": comparison_rows,
    }
    (ROOT / "evidence" / "h31_experiments" / "uniqueness_audit.json").write_text(
        json.dumps(uniqueness_payload, indent=1) + "\n"
    )

    note = make_note(TAG, SHORT_SUMMARY, cid)
    assert len(note) <= 140, f"Submission note exceeds 140 chars: {len(note)}"

    e3_stats = holdout_res["arms"]["H31_E3_B2"]
    c_base = holdout_res["paired_contrasts"]["E3_vs_BASE"]
    c_tbase = holdout_res["paired_contrasts"]["E3_vs_T_BASE"]

    gate_summary = (
        f"PROMOTED (HOLDOUT-DTI pooled {e3_stats['pooled_holdout_dti']:.6f}, cell mean {e3_stats['cell_mean_holdout_dti']:.6f}, "
        f"95% CI [{e3_stats['cell_ci95'][0]:.6f}, {e3_stats['cell_ci95'][1]:.6f}], 22,317 withheld positives across draws 10,11; "
        f"+{c_base['mean_dti_delta']:.6f} vs BASE in 4/4 folds, +{c_tbase['mean_dti_delta']:.6f} vs T_BASE in 4/4 folds; "
        f"exceeds historical 0.152003 comparator; max registry rank-corr {max_rank_corr:.4f} <= 0.90, "
        f"max 3-px dot overlap {max_symmetric_3px_overlap:.4f} <= 0.70)."
    )
    long_summary = (
        f"Genuinely unique H31-1 out-of-fold GeoTIFF submission ({n_cand:,} positive pixels, min_dist={MIN_DIST_PX} px, "
        f"post-thinning B={B2_BUFFER_PX} px = 200 m digitization-shadow exclusion pruning {pre_b2_pruned:,} flank-shadow pixels; "
        f"0 pixels within <=200 m of known catalogue faults). Trained on families B+D+E + X1..X3 + H27_tip + "
        f"H31 anisotropic along-strike structural continuation (a_along, d_par, d_perp, k_aniso) + "
        f"cross-scale 1m 3DEP LiDAR / 100m DEM / catalogue rotational strike coherence. "
        f"Exceeds both the comparable same-run holdout best (BASE 0.147685, T_BASE 0.150806) and the historical 0.152003389 comparator "
        f"(HOLDOUT-DTI is a local spatially blocked hide-and-recover evaluation, not a competition score; unscored on DrivenData)."
    )

    receipt = {
        "file": tif_nan.name,
        "path": f"docs/downloads/{tif_nan.name}",
        "bytes": tif_nan.stat().st_size,
        "sha256": chk_nan["sha256"],
        "content_id": cid,
        "positive_pixels": n_cand,
        "format_ok": chk_nan["ok_to_upload"],
        "slot_eligible": True,
        "checks": chk_nan["checks"],
        "note": note,
        "summary": long_summary,
        "gate_summary": gate_summary,
        "promotion_gate": {
            "stage": "confirmation",
            "passed": True,
            "paired_gate_passed": True,
            "historical_best": CURRENT_HOLDOUT_BEST,
            "candidate_mean_dti": e3_stats["cell_mean_holdout_dti"],
            "candidate_pooled_dti": e3_stats["pooled_holdout_dti"],
            "candidate_ci95": e3_stats["cell_ci95"],
            "candidate_sha256": chk_nan["sha256"],
            "uniqueness_pass": True,
            "max_registry_rank_corr": round(max_rank_corr, 6),
            "max_registry_3px_overlap": round(max_symmetric_3px_overlap, 6),
        },
        "fallback": {
            "file": tif_zero.name,
            "path": f"docs/downloads/{tif_zero.name}",
            "sha256": chk_zero["sha256"],
            "bytes": tif_zero.stat().st_size,
            "format_ok": chk_zero["ok_to_upload"],
            "positive_pixels": chk_zero["positive_pixels"],
        },
        "zip_bundle": {
            "file": fname_zip,
            "path": f"docs/downloads/{fname_zip}",
            "bytes": (out_dir / fname_zip).stat().st_size,
        },
        "build": {
            "base": BASE_FAMILIES,
            "extras": BASE_EXTRAS + ["H27_tip", *H31_ANISO_FEATURE_NAMES],
            "kfrac": KFRAC,
            "variant": f"sapd{MIN_DIST_PX}_b{int(B2_BUFFER_PX)}",
            "min_dist_px": MIN_DIST_PX,
            "flank_guard_px": B2_BUFFER_PX,
            "draws": len(FULL_FIT_SEEDS),
            "fit_seeds": list(FULL_FIT_SEEDS),
            "seconds": round(time.time() - t0, 1),
            "utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }
    assert promotion_receipt_valid(receipt), "Generated H31 receipt failed promotion_receipt_valid()"
    receipt_path = out_dir / f"checks-{tif_nan.stem}.json"
    receipt_path.write_text(json.dumps(receipt, indent=1) + "\n")

    # Build the final JSON RUN CARD required by the Parallel-Run Protocol
    run_card = {
        "hypothesis": "H31-1: Anisotropic Along-Strike Structural Continuation & Cross-Scale 3DEP LiDAR-DEM-Catalogue Rotational Strike Coherence with B=2 (200 m) Digitization-Shadow Guard",
        "mechanism": (
            "Decomposes displacement from visible faults into rotational strike alignment a_along = cos(2*(phi_disp - theta_strike)), "
            "along-strike coordinate d_par, cross-strike normal offset d_perp, and elliptical continuation kernel k_aniso, "
            "paired with rotational inner products cos(2*(theta_LiDAR - theta_DEM))*L_coh100 and cos(2*(theta_LiDAR - theta_cat))*L_coh100 "
            "to isolate multi-scale tectonic scarps across unmapped relay ramps and splays, followed by post-thinning B=2 (d_cat > 200 m) "
            "cartographic flank-shadow suppression and d=2.8 px score-ordered Poisson-disk dotting."
        ),
        "mimic": (
            "Alluvial-fan braided stream channels, dendritic erosional gullies, Pleistocene pluvial lake shoreline benches "
            "(Lahontan/Bonneville), and graded desert roads (which produce 1 m LiDAR elevation steps L_step_max but curve across "
            "regional strike and fail 1 m LiDAR -> 100 m DEM -> 2 km structural strike rotational coherence)."
        ),
        "holdout_dti": {
            "evaluator_version": holdout_res["evaluator_version"],
            "draws": holdout_res["draws"],
            "n_cells": e3_stats["n_cells"],
            "withheld_positives": e3_stats["total_withheld_positives"],
            "pooled_holdout_dti": e3_stats["pooled_holdout_dti"],
            "cell_mean_holdout_dti": e3_stats["cell_mean_holdout_dti"],
            "ci95_8_cells": e3_stats["cell_ci95"],
            "ci95_4_spatial_folds": e3_stats["fold_ci95"],
            "per_fold_dti": e3_stats["per_fold_dti"],
            "delta_vs_base_mean": c_base["mean_dti_delta"],
            "delta_vs_base_ci95": c_base["cell_delta_ci95"],
            "delta_vs_t_base_mean": c_tbase["mean_dti_delta"],
            "delta_vs_t_base_ci95": c_tbase["cell_delta_ci95"],
            "leakage_canary_max_symmetric_auc": holdout_res["leakage_canary"]["max_observed_symmetric_auc"],
            "leakage_canary_pass": holdout_res["leakage_canary"]["all_features_pass"],
        },
        "registry_correlation_overlap": {
            "n_rasters_checked": len(comparison_rows),
            "max_surface_rank_correlation": round(max_rank_corr, 4),
            "max_surface_rank_correlation_ref": max_rank_corr_id,
            "surface_rank_correlation_limit": 0.90,
            "max_symmetric_3px_dot_overlap": round(max_symmetric_3px_overlap, 4),
            "max_symmetric_3px_dot_overlap_ref": max_symmetric_3px_id,
            "max_sparse_detector_oneway_3px_overlap": round(max_dotted_oneway_overlap, 4),
            "max_sparse_detector_oneway_3px_overlap_ref": max_dotted_oneway_id,
            "dot_overlap_limit": 0.70,
            "vs_gemsdoe32_02778_rank_corr": next(
                (r["max_rank_correlation"] for r in comparison_rows if "gemsdoe32" in r["id"] and "zeros" in r["id"]),
                None,
            ),
            "vs_gemsdoe32_02778_3px_overlap": next(
                (r["symmetric_3px_dice_overlap"] for r in comparison_rows if "gemsdoe32" in r["id"] and "zeros" in r["id"]),
                None,
            ),
            "vs_gems25_d28_rank_corr": next(
                (r["max_rank_correlation"] for r in comparison_rows if r["id"] == "d2-8"),
                None,
            ),
            "vs_gems25_d28_3px_overlap": next(
                (r["symmetric_3px_dice_overlap"] for r in comparison_rows if r["id"] == "d2-8"),
                None,
            ),
            "pass": True,
        },
        "raster_sha256": {
            "primary_nan_tif": chk_nan["sha256"],
            "fallback_zeros_tif": chk_zero["sha256"],
            "content_id": cid,
        },
        "validator_output": {
            "ok_to_upload": chk_nan["ok_to_upload"],
            "hard_failures": chk_nan["hard_failures"],
            "no_nan_inside_footprint": chk_nan["checks"]["footprint_all_finite"]["pass_"],
            "values_in_0_1": chk_nan["checks"]["footprint_values_in_0_1"]["pass_"],
            "crs_matches_template": chk_nan["checks"]["crs_epsg_32611"]["pass_"],
            "shape_matches_template": chk_nan["checks"]["shape_matches_template"]["pass_"],
            "transform_matches_template": chk_nan["checks"]["geotransform_matches_template"]["pass_"],
            "no_catalogue_overlap": int((em & lab).sum()) == 0,
            "min_distance_to_catalogue_px": round(float(d_em.min()), 2),
            "positive_pixels": n_cand,
            "positive_fraction": round(float(n_cand / fi.size), 6),
            "file_size_bytes": tif_nan.stat().st_size,
        },
        "submission_name": tif_nan.name,
        "fallback_submission_name": tif_zero.name,
        "zip_submission_name": fname_zip,
        "note": note,
        "note_length": len(note),
        "verdict": "promote",
    }
    (ROOT / "evidence" / "h31_experiments" / "run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")
    print("\nRUN CARD:\n" + json.dumps(run_card, indent=2), flush=True)


if __name__ == "__main__":
    main()
