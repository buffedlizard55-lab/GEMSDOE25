from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gems25.h75_dchb import (
    H75_DCHB_NAMES,
    combine_corridor_gated_scores,
    compute_h75_dchb_grids,
    compute_quartz_upflow_halo,
    destripe_ew_flightlines,
    estimate_blind_n_hat,
    load_h75_dchb_sidecar,
)
from gems25.paths import work_dir

ROOT = Path(__file__).resolve().parents[1]


def test_h75_source_never_reads_catalogue_or_sgmc_files():
    src = (ROOT / "src" / "gems25" / "h75_dchb.py").read_text()
    # Strip module docstring before checking code body
    body = src.split('"""', 2)[2]
    for banned in ("labels.tif", "existing_faults.tif", "gdr_qfaults_traces", "derived_sgmc_faults"):
        assert banned not in body, f"Forbidden reference {banned} found in h75_dchb.py code body"


def test_quartz_upflow_rejects_label_derived_column():
    foot = np.ones((20, 20), dtype=bool)
    df_bad = pd.DataFrame({
        "row": [10], "col": [10], "layer": ["spring_test"], "thermalclass": ["Hot"],
        "temp_c": [85.0], "geothermquartz_c": [180.0], "dist_known_fault_px": [3.2],
    })
    with pytest.raises(ValueError, match="dist_known_fault_px"):
        compute_quartz_upflow_halo(df_bad, foot)


def test_destripe_ew_flightlines_suppresses_ew_corrugation_and_preserves_ns_step():
    yy, xx = np.mgrid[0:120, 0:120].astype(np.float32)
    ns_fault_step = np.tanh((xx - 60.0) / 3.0) * 50.0
    ew_corrugation = 10.0 * np.sin(2.0 * np.pi * yy / 3.0)  # 300 m E-W flight-line ripple
    noisy = ns_fault_step + ew_corrugation
    cleaned = destripe_ew_flightlines(noisy, sigma_ns=2.0, sigma_ew=14.0)
    resid_before = float(np.std(noisy - ns_fault_step))
    resid_after = float(np.std(cleaned[15:-15, 15:-15] - ns_fault_step[15:-15, 15:-15]))
    assert resid_after < 0.25 * resid_before


def test_oblique_piedmont_inflection_suppresses_contour_parallel_shoreline():
    H, W = 96, 96
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    foot = np.ones((H, W), dtype=bool)
    # Eastward-sloping range-to-basin ramp (macro contours run N-S, strike = 90 deg)
    det_elev = 1500.0 - 6.0 * xx
    # Patch A (top half, col 48): contour-parallel N-S shoreline bench (strike = 90 deg)
    # Patch B (bottom half, col 48): cross-contour E-W relay scarp (strike = 0 deg, orthogonal to contour)
    lid_valid = np.ones((H, W), dtype=np.float32)
    lid_step = np.zeros((H, W), dtype=np.float32)
    lid_coh = np.zeros((H, W), dtype=np.float32)
    lid_strike = np.full((H, W), 90.0, dtype=np.float32)

    lid_step[16:40, 46:50] = 0.6
    lid_coh[16:40, 46:50] = 0.9
    lid_strike[16:40, 46:50] = 90.0  # parallel to N-S elevation contours (Lahontan bench)

    lid_step[56:80, 36:60] = 0.6
    lid_coh[56:80, 36:60] = 0.9
    lid_strike[56:80, 36:60] = 0.0   # orthogonal to N-S elevation contours (cross-fan fault splay)

    z_f = np.zeros((H, W), dtype=np.float32)
    u8_mid = np.full((H, W), 128, dtype=np.uint8)
    ws = pd.DataFrame(columns=["row", "col", "layer", "thermalclass", "temp_c", "geothermquartz_c"])
    grids = compute_h75_dchb_grids(
        det_elev=det_elev,
        cond_surf=z_f + 0.05,
        depth_to_base=np.full((H, W), 400.0, dtype=np.float32),
        rtp=z_f,
        iso_grav=z_f,
        geod_shear=z_f + 10.0,
        rad_th_u8=u8_mid,
        ext_uth_u8=u8_mid,
        ext_up150_u8=u8_mid,
        lidar_step_max=lid_step,
        lidar_coh100=lid_coh,
        lidar_strike_deg=lid_strike,
        lidar_valid=lid_valid,
        wellspring_df=ws,
        footprint=foot,
    )
    ob = grids["H75_oblique_piedmont_inflection"]
    shoreline_score = float(ob[20:36, 47:49].mean())
    cross_splay_score = float(ob[60:76, 40:56].mean())
    assert cross_splay_score > 5.0 * max(shoreline_score, 1e-4)
    for k in H75_DCHB_NAMES:
        assert np.isfinite(grids[k]).all()


def test_corridor_gated_coupling_suppresses_isolated_cliff_and_calibrates_lidar_gap():
    # Pixel 0: isolated LiDAR cliff (low corridor 0.02, high trace 0.80)
    # Pixel 1: corroborated fault in LiDAR (high corridor 0.60, high trace 0.60)
    # Pixels 2..5: LiDAR-valid background
    # Pixels 6..9: LiDAR-gap pixels with strictly increasing (p_cor, p_gap)
    p_cor = np.array([0.02, 0.60, 0.05, 0.10, 0.20, 0.35, 0.04, 0.12, 0.25, 0.58], dtype=np.float32)
    p_tr = np.array([0.80, 0.60, 0.04, 0.08, 0.15, 0.30, 0.01, 0.01, 0.01, 0.01], dtype=np.float32)
    p_gp = np.array([0.10, 0.50, 0.04, 0.08, 0.15, 0.30, 0.03, 0.10, 0.22, 0.55], dtype=np.float32)
    lv = np.array([True, True, True, True, True, True, False, False, False, False])

    s = combine_corridor_gated_scores(p_cor, p_tr, p_gp, lv, gamma=0.60, gap_scale=0.95)
    assert s.dtype == np.float32 and np.isfinite(s).all()
    assert (s >= 0.0).all() and (s <= 1.0).all()
    # Corroborated fault strictly beats isolated LiDAR cliff despite lower raw p_tr (0.60 < 0.80)
    assert s[1] > 2.5 * s[0]
    # Strict monotonicity preserved across the L_valid == 0 gap
    assert np.all(np.diff(s[6:]) > 0)

    # Edge cases: all-valid, all-gap, and invalid gamma / gap_scale guards
    s_all_valid = combine_corridor_gated_scores(p_cor, p_tr, p_gp, np.ones_like(lv, dtype=bool))
    assert np.isfinite(s_all_valid).all() and (s_all_valid >= 0.0).all() and (s_all_valid <= 1.0).all()
    s_all_gap = combine_corridor_gated_scores(p_cor, p_tr, p_gp, np.zeros_like(lv, dtype=bool))
    assert np.isfinite(s_all_gap).all() and (s_all_gap >= 0.0).all() and (s_all_gap <= 1.0).all()
    with pytest.raises(ValueError):
        combine_corridor_gated_scores(p_cor, p_tr, p_gp, lv, gamma=1.5)
    with pytest.raises(ValueError):
        combine_corridor_gated_scores(p_cor, p_tr, p_gp, lv, gap_scale=0.0)


def test_estimate_blind_n_hat_handles_component_and_block_holdout():
    dom_c = np.ones((40, 40), dtype=bool)
    known_nonempty = np.zeros((40, 40), dtype=bool)
    known_nonempty[5, :] = True  # 40 visible fault px -> 0.25 * 40 = 10 -> floor 100
    known_nonempty[10:25, :] = True  # 640 visible fault px -> 0.25 * 640 = 160
    assert estimate_blind_n_hat(known_nonempty, dom_c) == pytest.approx(160.0)

    # BlockHoldout case: 0 visible faults inside dom_c, estimated from train_region visible faults
    known_empty = np.zeros((40, 40), dtype=bool)
    train_region = np.ones((100, 100), dtype=bool)
    vis_train = np.zeros((100, 100), dtype=bool)
    vis_train[:8, :] = True  # 800 visible px = 8% of train_region; divide by 0.8 -> 10% total prevalence
    n_hat_blk = estimate_blind_n_hat(
        known_empty, dom_c, visible_train=vis_train, train_region=train_region, hide_frac=0.20
    )
    assert n_hat_blk == pytest.approx(0.10 * 1600.0)


def test_real_h75_sidecar_if_cache_present():
    w = work_dir()
    foot_p = w / "bands" / "_footprint.npy"
    if not foot_p.exists():
        pytest.skip("shared work cache not populated")
    foot = np.load(foot_p)
    fi = np.flatnonzero(foot.ravel())
    arr = load_h75_dchb_sidecar(w, fi)
    assert arr.shape == (5, fi.size)
    assert arr.dtype == np.float32
    assert np.isfinite(arr).all()
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
