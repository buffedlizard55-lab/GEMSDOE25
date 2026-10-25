"""H31-1 tip-preserved lateral-flank shielding and multi-physics sub-scarp concordance.

All dynamic catalogue geometry (`H31_offflank_tip_halo` and the lateral-flank emission shield) is computed
strictly from `draw.visible` (in holdout) or `labels` (in the full-catalogue candidate build). Hidden holdout
labels are never passed to or read by any function in this module.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter
from scipy.stats import spearmanr, t

from .thinning import ridge_nms, select_top_positive

H31_FEATURE_NAMES = ["H31_subscarp_concord", "H31_offflank_tip_halo"]
H31_SURF_INPUTS = ("L_step_max", "L_ex_mean", "L_coh100")
H31_SUB_INPUTS = ("A_grav_hg_ridge", "A_mag_hg_ridge", "D_depth_base_grad", "D_cond_grad", "D_ThK_edge")
H31_BASE_EXTRAS = ["X1_K", "X1_ThK", "X1_UK", "X2_compat", "X2_compat_coh", "X3_gm", "X3_gd"]
H31_ARMS = {
    "M0_C0": (-1, -1),
    "M1_C0": (1, -1),
    "M0_C1": (-1, 1),
    "M1_C1": (1, 1),
}
H31_CONTROL = "CTRL_NO_TIP"
EVALUATOR_VERSION = "gems25.holdout.v1.2-buffered-4quad-pooled-dti"


def build_subscarp_concordance(
    static: np.ndarray,
    names: Sequence[str],
    scales: Mapping[str, tuple[float, float]],
) -> tuple[np.ndarray, dict[str, Any]]:
    """Build `H31_subscarp_concord` in [0, 1] as sqrt(mean_surf * mean_sub) over percentile-scaled static bands."""
    arr = np.asarray(static)
    if arr.ndim != 2 or arr.shape[0] != len(names):
        raise ValueError("static must be a (n_features, n_footprint) matrix aligned with names")
    name_to_idx = {str(n): i for i, n in enumerate(names)}
    required = (*H31_SURF_INPUTS, *H31_SUB_INPUTS)
    missing = [n for n in required if n not in name_to_idx or n not in scales]
    if missing:
        raise ValueError(f"static cache lacks H31 inputs/scales: {missing}")

    n_px = int(arr.shape[1])
    surf_acc = np.zeros(n_px, np.float32)
    sub_acc = np.zeros(n_px, np.float32)
    nonfinite_counts: dict[str, int] = {}

    for group_names, acc in ((H31_SURF_INPUTS, surf_acc), (H31_SUB_INPUTS, sub_acc)):
        for name in group_names:
            lo, hi = map(float, scales[name])
            if not np.isfinite([lo, hi]).all() or hi <= lo:
                raise ValueError(f"invalid percentile scale for {name}: {(lo, hi)}")
            raw = np.asarray(arr[name_to_idx[name]], dtype=np.float32)
            fin = np.isfinite(raw)
            nonfinite_counts[name] = int(n_px - np.count_nonzero(fin))
            scaled = np.zeros(n_px, np.float32)
            scaled[fin] = np.clip((raw[fin] - lo) / (hi - lo), 0.0, 1.0)
            acc += scaled

    surf_mean = surf_acc / float(len(H31_SURF_INPUTS))
    sub_mean = sub_acc / float(len(H31_SUB_INPUTS))
    out = np.clip(np.sqrt(np.maximum(surf_mean * sub_mean, 0.0)), 0.0, 1.0).astype(np.float32, copy=False)
    diag = {
        "surf_inputs": list(H31_SURF_INPUTS),
        "sub_inputs": list(H31_SUB_INPUTS),
        "source_nonfinite_counts": nonfinite_counts,
        "n_footprint_pixels": n_px,
        "nonzero_fraction": float(np.count_nonzero(out) / max(1, n_px)),
        "mean_value": float(out.mean()) if n_px else 0.0,
        "max_value": float(out.max(initial=0.0)),
    }
    return out, diag


def build_offflank_tip_halo(
    visible: np.ndarray,
    tip: np.ndarray,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
    *,
    flank_inner_px: float = 2.0,
    flank_ramp_px: float = 2.0,
    decay_px: float = 12.0,
) -> tuple[np.ndarray, dict[str, Any]]:
    """Return `H31_offflank_tip_halo` in [0, 1] as a footprint vector derived strictly from `visible` and `tip`.

    Suppresses the 0..2 px non-tip lateral scarp apron of mapped visible faults while preserving active
    visible-tip continuation cones (`tip`) and the 3..15 px piedmont/step-fault corridor.
    """
    vis = np.asarray(visible, dtype=bool)
    foot = np.asarray(footprint, dtype=bool)
    tip_vec = np.asarray(tip, dtype=np.float32)
    raw_idx = np.asarray(footprint_idx)
    if vis.ndim != 2 or foot.ndim != 2 or vis.shape != foot.shape:
        raise ValueError("visible and footprint must be aligned 2-D arrays")
    if raw_idx.ndim != 1 or (raw_idx.size and not np.issubdtype(raw_idx.dtype, np.integer)):
        raise ValueError("footprint_idx must be a 1-D integer array")
    fi = raw_idx.astype(np.int64, copy=False)
    h, w = foot.shape
    if fi.size and ((fi < 0).any() or (fi >= h * w).any() or not foot.ravel()[fi].all()):
        raise ValueError("footprint_idx must contain only valid flat indices inside the footprint")
    if tip_vec.shape != (fi.size,) or not np.isfinite(tip_vec).all():
        raise ValueError("tip must be a finite 1-D vector aligned with footprint_idx")
    if flank_inner_px < 0.0 or flank_ramp_px <= 0.0 or decay_px <= 0.0:
        raise ValueError("flank_inner_px >= 0, flank_ramp_px > 0, and decay_px > 0 are required")

    v = vis & foot
    if not v.any() or not fi.size:
        return np.zeros(fi.size, np.float32), {
            "visible_pixels": 0,
            "flank_suppressed_fraction": 0.0,
            "nonzero_fraction": 0.0,
            "mean_value": 0.0,
            "max_value": 0.0,
        }

    dist_vis = distance_transform_edt(~v).ravel()[fi].astype(np.float32)
    w_flank = np.clip((dist_vis - float(flank_inner_px)) / float(flank_ramp_px), 0.0, 1.0)
    piedmont = w_flank * np.exp(-np.maximum(dist_vis - 3.0, 0.0) / float(decay_px))
    tip_clamped = np.clip(tip_vec, 0.0, 1.0)
    out = np.clip(1.0 - (1.0 - piedmont) * (1.0 - tip_clamped), 0.0, 1.0).astype(np.float32)
    flank_zone = (dist_vis > 0.0) & (dist_vis <= float(flank_inner_px)) & (tip_clamped <= 0.0)
    diag = {
        "visible_pixels": int(np.count_nonzero(v)),
        "flank_suppressed_fraction": float(np.count_nonzero(flank_zone) / max(1, fi.size)),
        "nonzero_fraction": float(np.count_nonzero(out) / max(1, fi.size)),
        "mean_value": float(out.mean()),
        "max_value": float(out.max(initial=0.0)),
    }
    return out, diag


def candidates_flank_shielded(
    score_crop: np.ndarray,
    dom_crop: np.ndarray,
    known_crop: np.ndarray,
    tip_crop: np.ndarray,
    k: int,
    *,
    nms_sigma: float = 1.0,
    flank_radius_px: float = 2.5,
    tip_preserve_threshold: float = 0.05,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Select top-K ridge candidates after shielding the non-tip lateral flank (`d(visible) <= flank_radius_px`)."""
    s = np.nan_to_num(np.asarray(score_crop, np.float32), nan=0.0)
    dom = np.asarray(dom_crop, bool)
    known = np.asarray(known_crop, bool)
    tip = np.nan_to_num(np.asarray(tip_crop, np.float32), nan=0.0)
    if s.shape != dom.shape or s.shape != known.shape or s.shape != tip.shape:
        raise ValueError("score_crop, dom_crop, known_crop, and tip_crop must have identical 2-D shapes")
    if flank_radius_px < 0.0 or not (0.0 <= tip_preserve_threshold <= 1.0):
        raise ValueError("invalid flank_radius_px or tip_preserve_threshold")

    r = ridge_nms(s, dom, nms_sigma)
    if known.any():
        dv = distance_transform_edt(~known)
    else:
        dv = np.full(s.shape, np.inf, np.float32)
    shield_ok = (dv > float(flank_radius_px)) | (tip >= float(tip_preserve_threshold))
    raw_ridge_mask = r & ~known & dom
    shielded_ridge_mask = raw_ridge_mask & shield_ok
    sc = np.where(shielded_ridge_mask, s, 0.0)
    top = select_top_positive(sc, dom, k)
    diag = {
        "raw_ridge_candidates": int(np.count_nonzero(raw_ridge_mask)),
        "shielded_ridge_candidates": int(np.count_nonzero(shielded_ridge_mask)),
        "flank_removed_ridges": int(np.count_nonzero(raw_ridge_mask & ~shield_ok)),
        "tip_preserved_in_flank": int(np.count_nonzero(raw_ridge_mask & (dv <= float(flank_radius_px)) & (tip >= float(tip_preserve_threshold)))),
        "selected_top_k": int(np.count_nonzero(top)),
    }
    return s, top, diag


def factorial_2x2_effects(responses: Mapping[str, float]) -> dict[str, float]:
    """Return coded H31 M/C main effects and interaction (half the difference-in-differences)."""
    if set(responses) != set(H31_ARMS):
        raise ValueError(f"responses must have exactly these arms: {sorted(H31_ARMS)}")
    y00, y10, y01, y11 = (float(responses[k]) for k in ("M0_C0", "M1_C0", "M0_C1", "M1_C1"))
    if not np.isfinite([y00, y10, y01, y11]).all():
        raise ValueError("all four 2x2 design responses must be finite")
    return {
        "M": (y10 + y11 - y00 - y01) / 2.0,
        "C": (y01 + y11 - y00 - y10) / 2.0,
        "M_x_C": (y00 - y10 - y01 + y11) / 2.0,
        "M_x_C_difference_in_differences": y00 - y10 - y01 + y11,
    }


def pooled_dti_summary(
    cell_rows: Sequence[Mapping[str, Any]],
    *,
    alpha: float = 0.2,
    beta: float = 0.8,
    eps: float = 1e-7,
    evaluator_version: str = EVALUATOR_VERSION,
) -> dict[str, Any]:
    """Compute pooled DTI across all cells, per-fold pooled DTI, withheld-positive count, and 95% t-CI."""
    if not cell_rows:
        raise ValueError("cell_rows must not be empty")
    tp_total = float(sum(float(r["tp"]) for r in cell_rows))
    fp_total = float(sum(float(r["fp"]) for r in cell_rows))
    n_truth_total = int(round(sum(float(r["n_truth"]) for r in cell_rows)))
    fn_total = float(n_truth_total) - tp_total
    pooled_dti = float(tp_total / (tp_total + alpha * fp_total + beta * fn_total + eps))

    fold_pooled: list[float] = []
    for fold in range(4):
        f_rows = [r for r in cell_rows if int(r["fold"]) == fold]
        if f_rows:
            ftp = float(sum(float(r["tp"]) for r in f_rows))
            ffp = float(sum(float(r["fp"]) for r in f_rows))
            fnt = float(sum(float(r["n_truth"]) for r in f_rows))
            ffn = fnt - ftp
            fold_pooled.append(float(ftp / (ftp + alpha * ffp + beta * ffn + eps)))
    arr = np.asarray(fold_pooled, dtype=float)
    se = float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else 0.0
    crit = float(t.ppf(0.975, arr.size - 1)) if arr.size > 1 else 0.0
    ci_lo = float(pooled_dti - crit * se)
    ci_hi = float(pooled_dti + crit * se)
    label = (
        f"HOLDOUT-DTI {pooled_dti:.6f} "
        f"(evaluator={evaluator_version}, withheld_positives={n_truth_total}, 95% CI [{ci_lo:.6f}, {ci_hi:.6f}])"
    )
    return {
        "evaluator_version": evaluator_version,
        "pooled_dti": pooled_dti,
        "withheld_positives": n_truth_total,
        "tp_total": tp_total,
        "fp_total": fp_total,
        "fn_total": fn_total,
        "fold_pooled_dti": fold_pooled,
        "se_across_folds": se,
        "ci_95": [ci_lo, ci_hi],
        "formatted_label": label,
    }


def h31_promotion_gate(
    candidate_by_fold: Sequence[float],
    controls_by_fold: Mapping[str, Sequence[float]],
    candidate_hug_by_fold: Sequence[float],
    controls_hug_by_fold: Mapping[str, Sequence[float]],
    *,
    min_gain: float = 0.001,
    max_fold_loss: float = 0.01,
    max_hug_increase: float = 0.10,
) -> dict[str, Any]:
    """Compare primary arm (M1_C1) to the per-fold best same-run control (CTRL_NO_TIP and M0_C0)."""
    candidate = np.asarray(candidate_by_fold, dtype=float)
    candidate_hug = np.asarray(candidate_hug_by_fold, dtype=float)
    if candidate.shape != (4,) or candidate_hug.shape != (4,) or not np.isfinite(candidate).all() or not np.isfinite(candidate_hug).all():
        raise ValueError("candidate DTI and hug arrays must contain four finite fold means")
    if set(controls_by_fold) != {H31_CONTROL, "M0_C0"} or set(controls_hug_by_fold) != set(controls_by_fold):
        raise ValueError("controls must be CTRL_NO_TIP and M0_C0, with matching hug arrays")
    controls = {k: np.asarray(v, dtype=float) for k, v in controls_by_fold.items()}
    control_hug = {k: np.asarray(v, dtype=float) for k, v in controls_hug_by_fold.items()}
    if any(v.shape != (4,) or not np.isfinite(v).all() for v in controls.values()):
        raise ValueError("each control DTI array must contain four finite fold means")
    if any(v.shape != (4,) or not np.isfinite(v).all() for v in control_hug.values()):
        raise ValueError("each control hug array must contain four finite fold means")

    names = (H31_CONTROL, "M0_C0")
    chosen = np.argmax(np.vstack([controls[n] for n in names]), axis=0)
    reference = np.array([controls[names[idx]][fold] for fold, idx in enumerate(chosen)])
    reference_hug = np.array([control_hug[names[idx]][fold] for fold, idx in enumerate(chosen)])
    delta = candidate - reference
    hug_delta = candidate_hug - reference_hug
    mean_gain = float(delta.mean())
    positive_folds = int(np.count_nonzero(delta > 0.0))
    worst_fold = float(delta.min())
    mean_hug_delta = float(hug_delta.mean())
    passed = bool(
        mean_gain > min_gain
        and positive_folds >= 3
        and worst_fold >= -max_fold_loss
        and mean_hug_delta <= max_hug_increase
    )
    return {
        "candidate_mean_dti": float(candidate.mean()),
        "reference_mean_dti": float(reference.mean()),
        "reference_arm_by_fold": [names[int(i)] for i in chosen],
        "mean_gain_vs_best_paired_control": mean_gain,
        "folds_positive": positive_folds,
        "worst_fold_gain": worst_fold,
        "mean_hug_share_delta": mean_hug_delta,
        "hug_share_delta_by_fold": [float(x) for x in hug_delta],
        "paired_gate_passed": passed,
        "per_fold_gain": [float(x) for x in delta],
    }


def check_duplicate_lane_against_registry(
    surface_vec: np.ndarray,
    emitted_mask: np.ndarray,
    footprint: np.ndarray,
    registry_rasters: Mapping[str, np.ndarray],
    *,
    max_rank_corr: float = 0.90,
    max_dot_overlap_3px: float = 0.70,
    sample_size: int = 250_000,
    seed: int = 20261025,
) -> dict[str, Any]:
    """Check Protocol Rule 1 on both the continuous score surface (Spearman <= 0.90) and final dots (3-px overlap <= 0.70)."""
    foot = np.asarray(footprint, bool)
    em = np.asarray(emitted_mask, bool) & foot
    fi = np.flatnonzero(foot.ravel())
    surf = np.asarray(surface_vec, np.float32)
    if surf.shape == foot.shape:
        surf = surf.ravel()[fi]
    if surf.shape != (fi.size,):
        raise ValueError("surface_vec must be a footprint vector or 2-D footprint-aligned grid")

    rng = np.random.default_rng(seed)
    sub = np.sort(rng.choice(fi.size, size=min(sample_size, fi.size), replace=False))
    s_sub = surf[sub]
    n_em = int(np.count_nonzero(em))
    if n_em == 0:
        raise ValueError("emitted_mask has zero positive pixels inside the footprint")

    yy, xx = np.mgrid[-3:4, -3:4]
    disk_3px = (yy * yy + xx * xx) <= 9
    dil_em = binary_dilation(em, structure=disk_3px) & foot
    n_foot = float(foot.sum())

    per_raster: dict[str, dict[str, float | int | bool]] = {}
    max_corr_seen = -1.0
    max_corr_id = None
    max_ov_dotted_seen = -1.0
    max_ov_dotted_id = None
    max_sym_ov_seen = -1.0
    max_sym_ov_id = None
    max_raw_oneway_seen = -1.0
    max_raw_oneway_id = None

    for rid, reg_source in registry_rasters.items():
        if hasattr(reg_source, "__fspath__") or isinstance(reg_source, str):
            import rasterio

            with rasterio.open(reg_source) as src_ds:
                if src_ds.shape != foot.shape:
                    continue
                arr = src_ds.read(1)
        else:
            arr = np.asarray(reg_source)
            if arr.shape != foot.shape:
                continue
        reg_sub = np.nan_to_num(arr.ravel()[fi[sub]], nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        if np.all(reg_sub == reg_sub[0]) or np.all(s_sub == s_sub[0]):
            rho = 0.0
        else:
            rho = float(spearmanr(s_sub, reg_sub).statistic)
            if not np.isfinite(rho):
                rho = 0.0
        reg_pos = (arr > 0) & np.isfinite(arr) & foot
        n_reg_pos = int(np.count_nonzero(reg_pos))
        if n_reg_pos > 0:
            dil = binary_dilation(reg_pos, structure=disk_3px) & foot
            ov_3px = float(np.mean(dil[em]))
            rev_3px = float(np.mean(dil_em[reg_pos]))
            sym_min = float(min(ov_3px, rev_3px))
            sym_f1 = float(2.0 * ov_3px * rev_3px / max(ov_3px + rev_3px, 1e-12))
            bg_cov = float(np.count_nonzero(dil) / max(n_foot, 1.0))
            exact_ov = float(np.mean(reg_pos[em]))
            del dil
        else:
            ov_3px = rev_3px = sym_min = sym_f1 = bg_cov = exact_ov = 0.0
        del arr, reg_pos, reg_sub
        is_comparable_dotted = bool(0 < n_reg_pos <= 100_000)
        dup = bool(
            rho > max_rank_corr
            or sym_min > max_dot_overlap_3px
            or (is_comparable_dotted and ov_3px > max_dot_overlap_3px)
        )
        per_raster[rid] = {
            "spearman_surface": rho,
            "dot_share_within_3px": ov_3px,
            "reverse_share_within_3px": rev_3px,
            "symmetric_min_overlap_3px": sym_min,
            "symmetric_f1_overlap_3px": sym_f1,
            "registry_3px_footprint_coverage": bg_cov,
            "dot_share_exact_0px": exact_ov,
            "registry_positive_px": n_reg_pos,
            "is_comparable_dotted_submission": is_comparable_dotted,
            "duplicate_violation": dup,
        }
        if rho > max_corr_seen:
            max_corr_seen, max_corr_id = rho, rid
        if is_comparable_dotted and ov_3px > max_ov_dotted_seen:
            max_ov_dotted_seen, max_ov_dotted_id = ov_3px, rid
        if sym_min > max_sym_ov_seen:
            max_sym_ov_seen, max_sym_ov_id = sym_min, rid
        if ov_3px > max_raw_oneway_seen:
            max_raw_oneway_seen, max_raw_oneway_id = ov_3px, rid

    passed = bool(
        max_corr_seen <= max_rank_corr
        and max_sym_ov_seen <= max_dot_overlap_3px
        and max_ov_dotted_seen <= max_dot_overlap_3px
    )
    return {
        "passed": passed,
        "thresholds": {
            "max_spearman_surface": max_rank_corr,
            "max_dot_share_within_3px": max_dot_overlap_3px,
        },
        "candidate_emitted_px": n_em,
        "n_registry_rasters_checked": len(per_raster),
        "max_spearman_surface": {"raster_id": max_corr_id, "value": float(max_corr_seen)},
        "max_dot_share_within_3px": {"raster_id": max_ov_dotted_id, "value": float(max_ov_dotted_seen)},
        "max_symmetric_min_overlap_3px": {"raster_id": max_sym_ov_id, "value": float(max_sym_ov_seen)},
        "max_unadjusted_oneway_including_dense_grids": {"raster_id": max_raw_oneway_id, "value": float(max_raw_oneway_seen)},
        "per_raster": per_raster,
    }


# --- H31 Anisotropic Along-Strike Continuation & 3DEP LiDAR-DEM Strike Coherence (c213681203f6 lane) ---

H31_ANISO_NAMES = (
    "H31_a_along",
    "H31_d_par",
    "H31_d_perp",
    "H31_k_aniso",
)
H31_COH_NAMES = (
    "H31_lidar_dem_compat",
    "H31_lidar_cat_compat",
)
H31_ANISO_FEATURE_NAMES = H31_ANISO_NAMES + H31_COH_NAMES
H31_ALL_NAMES = H31_ANISO_FEATURE_NAMES

H31_ANISO_ARMS = (
    "BASE",
    "T_BASE",
    "H31_E1_ANISO",
    "H31_E2_COH",
    "H31_E3_B2",
)


def build_static_lidar_dem_coherence(
    static: np.ndarray,
    static_names: list[str],
    addon: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(l_c2, l_s2, l_coh, lidar_dem_compat)`` over the footprint index vector ``fi``."""
    idx_c2 = static_names.index("L_strike_c2")
    idx_s2 = static_names.index("L_strike_s2")
    idx_coh = static_names.index("L_coh100")

    l_c2 = np.nan_to_num(np.asarray(static[idx_c2], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    l_s2 = np.nan_to_num(np.asarray(static[idx_s2], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    l_coh = np.clip(
        np.nan_to_num(np.asarray(static[idx_coh], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0),
        0.0,
        1.0,
    )
    dem_c2 = np.nan_to_num(np.asarray(addon[3], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    dem_s2 = np.nan_to_num(np.asarray(addon[4], dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)

    lidar_dem_compat = np.clip((l_c2 * dem_c2 + l_s2 * dem_s2) * l_coh, -1.0, 1.0).astype(np.float32)
    return l_c2, l_s2, l_coh, lidar_dem_compat


def build_h31_features(
    visible: np.ndarray,
    footprint: np.ndarray,
    footprint_idx: np.ndarray,
    l_c2: np.ndarray,
    l_s2: np.ndarray,
    l_coh: np.ndarray,
    lidar_dem_compat: np.ndarray,
    chunk_size: int = 500_000,
) -> np.ndarray:
    """Compute the 6 H31 columns ``(6, n_footprint)`` strictly from the visible fault mask and static caches.

    Columns:
      0: ``H31_a_along``          — cos(2*(phi_disp - theta_strike)) in [-1, 1]
      1: ``H31_d_par``            — log1p(min(d_parallel, 60.0))
      2: ``H31_d_perp``           — log1p(min(d_perpendicular, 60.0))
      3: ``H31_k_aniso``          — exp(-d_par_raw/12 - d_perp_raw/3) * max(0, a_along)
      4: ``H31_lidar_dem_compat`` — cos(2*(theta_LiDAR - theta_DEM)) * L_coh100
      5: ``H31_lidar_cat_compat`` — cos(2*(theta_LiDAR - theta_cat)) * L_coh100
    """
    v = np.asarray(visible, dtype=bool) & np.asarray(footprint, dtype=bool)
    fi = np.asarray(footprint_idx, dtype=np.int64)
    H, W = v.shape
    out = np.zeros((6, fi.size), dtype=np.float32)
    out[4] = lidar_dem_compat
    if not v.any() or fi.size == 0:
        return out

    dist, (iy, ix) = distance_transform_edt(~v, return_indices=True)
    s = gaussian_filter(v.astype(np.float32), 2.0)
    gy, gx = np.gradient(s)
    jxx = gaussian_filter(gx * gx, 2.0)
    jyy = gaussian_filter(gy * gy, 2.0)
    jxy = gaussian_filter(gx * gy, 2.0)
    th_grad2 = np.arctan2(2.0 * jxy, jxx - jyy)
    c2 = (-np.cos(th_grad2)).astype(np.float32)
    s2 = (-np.sin(th_grad2)).astype(np.float32)
    del s, gy, gx, jxx, jyy, jxy, th_grad2

    dist_flat = dist.ravel()
    iy_flat = iy.ravel()
    ix_flat = ix.ravel()
    c2_flat = c2.ravel()
    s2_flat = s2.ravel()

    for start in range(0, fi.size, chunk_size):
        stop = min(fi.size, start + chunk_size)
        ids = fi[start:stop]
        rr = (ids // W).astype(np.float32)
        cc = (ids % W).astype(np.float32)
        nr = iy_flat[ids].astype(np.float32)
        nc = ix_flat[ids].astype(np.float32)
        near_flat = iy_flat[ids].astype(np.int64) * W + ix_flat[ids].astype(np.int64)

        dr = rr - nr
        dc = cc - nc
        d_fi = dist_flat[ids].astype(np.float32)
        d2 = np.maximum(dr * dr + dc * dc, 1e-12)
        disp_c2 = (dc * dc - dr * dr) / d2
        disp_s2 = (2.0 * dc * dr) / d2

        nc2 = c2_flat[near_flat]
        ns2 = s2_flat[near_flat]
        a_along = np.clip(nc2 * disp_c2 + ns2 * disp_s2, -1.0, 1.0)

        d_par_raw = d_fi * np.sqrt(np.maximum(0.0, 0.5 * (1.0 + a_along)))
        d_perp_raw = d_fi * np.sqrt(np.maximum(0.0, 0.5 * (1.0 - a_along)))

        out[0, start:stop] = a_along.astype(np.float32)
        out[1, start:stop] = np.log1p(np.minimum(d_par_raw, 60.0)).astype(np.float32)
        out[2, start:stop] = np.log1p(np.minimum(d_perp_raw, 60.0)).astype(np.float32)
        out[3, start:stop] = (
            np.exp(-d_par_raw / 12.0 - d_perp_raw / 3.0) * np.maximum(0.0, a_along)
        ).astype(np.float32)
        out[5, start:stop] = np.clip(
            (l_c2[start:stop] * nc2 + l_s2[start:stop] * ns2) * l_coh[start:stop],
            -1.0,
            1.0,
        ).astype(np.float32)

    return out


def apply_digitization_shadow_guard(
    emitted: np.ndarray,
    known_faults: np.ndarray,
    buffer_px: float = 2.0,
) -> np.ndarray:
    """Suppress emitted dots within ``buffer_px`` (default B=2.0 px = 200 m) of known/visible fault traces."""
    em = np.asarray(emitted, dtype=bool)
    kn = np.asarray(known_faults, dtype=bool)
    if em.shape != kn.shape:
        raise ValueError("emitted and known_faults must have identical 2-D shapes")
    if buffer_px <= 0.0 or not kn.any():
        return em & ~kn
    dist_known = distance_transform_edt(~kn)
    return em & (dist_known > float(buffer_px))
