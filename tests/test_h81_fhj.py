"""Analytical & real-data invariants for H81 (FHJ-SD + CLR + SLUTH) static features."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from gems25.h81_fhj import (
    H81_FHJ_NAMES,
    aitchison_clr_raw_jump,
    combine_junction_corridor_scores,
    compute_cation_silica_diseq_halo,
    compute_h81_fhj_grids,
    forstner_junction_invariant,
    load_h81_fhj_sidecar,
    relay_tip_divergence,
    sluth_local_exponent,
)
from gems25.paths import work_dir

ROOT = Path(__file__).resolve().parents[1]


def test_h81_source_never_references_labels_or_qfaults() -> None:
    src = (ROOT / "src" / "gems25" / "h81_fhj.py").read_text()
    # Docstring/guard mentions are explicitly checked; ensure no file open on labels/existing_faults/qfaults
    for forbidden in (
        '"labels.tif"',
        '"existing_faults.tif"',
        '"gdr_qfaults_traces.csv"',
        "_labels.npy",
    ):
        assert forbidden not in src


def test_forstner_junction_vanishes_on_planar_step_and_peaks_at_intersection() -> None:
    yy, xx = np.mgrid[0:128, 0:128].astype(np.float32)
    planar = np.tanh((xx - 64.0) / 2.0)
    j_planar = forstner_junction_invariant(planar, sig_grad=1.8, sig_ten=5.0)
    assert float(j_planar[64, 64]) < 1e-6

    crossing = np.tanh((xx - 64.0) / 2.0) + np.tanh((yy - 64.0) / 2.0)
    j_cross = forstner_junction_invariant(crossing, sig_grad=1.8, sig_ten=5.0)
    # Junction center must dominate both planar step and far-field single-arm segments
    assert float(j_cross[64, 64]) > 25.0 * float(j_cross[64, 16])
    assert float(j_cross[64, 64]) > 25.0 * float(j_cross[16, 64])


def test_relay_tip_divergence_peaks_at_en_echelon_stepover_tips() -> None:
    yy, xx = np.mgrid[0:128, 0:128].astype(np.float32)
    # Two overlapping en-echelon N-S fault steps terminating near y=64, offset across x=60 vs x=68
    seg1 = 0.5 * (1.0 + np.tanh((60.0 - yy) / 2.0)) * np.tanh((xx - 60.0) / 2.0)
    seg2 = 0.5 * (1.0 + np.tanh((yy - 68.0) / 2.0)) * np.tanh((xx - 68.0) / 2.0)
    field = (seg1 + seg2).astype(np.float32)
    rdiv = relay_tip_divergence(field, sig_grad=1.8, sig_disp=8.0)
    relay_box = float(rdiv[56:73, 56:73].max())
    mid_seg = float(rdiv[20:30, 56:65].mean())
    assert relay_box > 4.0 * mid_seg


def test_aitchison_clr_jump_exact_moisture_attenuation_invariance() -> None:
    yy, xx = np.mgrid[0:96, 0:96].astype(np.float64)
    # Compositional jump across x=48 (high K on left, high U on right)
    s = 0.5 * (1.0 + np.tanh((xx - 48.0) / 2.0))
    k = 3.0 * (1.0 - s) + 1.0 * s
    th = np.full_like(xx, 2.0)
    u = 1.0 * (1.0 - s) + 4.0 * s
    nx = np.ones_like(xx, dtype=np.float32)
    ny = np.zeros_like(xx, dtype=np.float32)

    j_dry = aitchison_clr_raw_jump(k, th, u, nx, ny, sigma=1.8)
    # Spatially varying positive soil-moisture / clearance attenuation factor m(x, y) in [0.25, 3.75]
    moisture = 2.0 + 1.5 * np.sin(xx / 9.0) * np.cos(yy / 11.0)
    j_wet = aitchison_clr_raw_jump(k * moisture, th * moisture, u * moisture, nx, ny, sigma=1.8)

    np.testing.assert_allclose(j_dry, j_wet, rtol=1e-6, atol=1e-6)
    assert float(j_dry[48, 48]) > 20.0 * float(j_dry[48, 16])


def test_sluth_exponent_separates_step_contact_from_compact_dipole() -> None:
    yy, xx = np.mgrid[-64:64, -64:64].astype(np.float64) * 100.0  # meters
    z0 = 150.0
    # 1-D buried vertical fault contact step potential derivative ~ arctan(x / z0) => N = 0 => eta ~ 1
    f_step = np.arctan2(xx, z0).astype(np.float32)
    eta_step, _ = sluth_local_exponent(f_step, z1_m=150.0, z2_m=400.0, z_ref_m=z0, cell_m=100.0, pad=64)

    # 3-D compact point source at z0: vertical field ~ z0 / (r^2 + z0^2)^(3/2) => N = 2 => eta ~ 3
    r2 = xx * xx + yy * yy + z0 * z0
    f_dip = (z0 / np.power(r2, 1.5) * 1e7).astype(np.float32)
    eta_dip, _ = sluth_local_exponent(f_dip, z1_m=150.0, z2_m=400.0, z_ref_m=z0, cell_m=100.0, pad=64)

    assert 0.70 < float(eta_step[64, 64]) < 1.35
    assert float(eta_dip[64, 64]) > 2.20


def test_cation_silica_diseq_rejects_forbidden_label_column() -> None:
    foot = np.ones((32, 32), dtype=bool)
    cond = np.ones((32, 32), dtype=np.float32)
    bad_ws = pd.DataFrame({"row": [10], "col": [10], "dist_known_fault_px": [3.0], "temp_c": [60.0]})
    empty_v = pd.DataFrame({"row": pd.Series(dtype=int), "col": pd.Series(dtype=int)})
    with pytest.raises(ValueError, match="dist_known_fault_px"):
        compute_cation_silica_diseq_halo(bad_ws, empty_v, cond, foot)


def test_compute_h81_fhj_grids_synthetic_and_coupling_bounds() -> None:
    rng = np.random.default_rng(80)
    h, w = 64, 64
    foot = np.zeros((h, w), dtype=bool)
    foot[4:60, 4:60] = True
    ws = pd.DataFrame(
        {
            "row": [20, 40],
            "col": [22, 42],
            "layer": ["spring_chem", "well_chem"],
            "thermalclass": ["Hot", "Warm"],
            "temp_c": [45.0, 32.0],
            "geothermquartz_c": [145.0, 110.0],
            "geothermchalc_c": [120.0, 88.0],
            "geothermcat_c": [175.0, 135.0],
        }
    )
    vents = pd.DataFrame({"row": [30], "col": [30]})
    grids = compute_h81_fhj_grids(
        rtp=rng.normal(size=(h, w)).astype(np.float32),
        iso_grav=rng.normal(size=(h, w)).astype(np.float32),
        iso_grav_vg=rng.normal(size=(h, w)).astype(np.float32),
        depth_to_base=np.abs(rng.normal(loc=300.0, scale=100.0, size=(h, w))).astype(np.float32),
        cond_surf=np.abs(rng.normal(loc=0.05, scale=0.03, size=(h, w))).astype(np.float32),
        geod_shear=rng.normal(loc=20.0, scale=5.0, size=(h, w)).astype(np.float32),
        geod_dilate=rng.normal(loc=5.0, scale=3.0, size=(h, w)).astype(np.float32),
        deq_seis=np.abs(rng.normal(size=(h, w))).astype(np.float32),
        ieq_seis=np.abs(rng.normal(size=(h, w))).astype(np.float32),
        rad_k_u8=rng.integers(1, 220, size=(h, w), dtype=np.uint8),
        rad_th_u8=rng.integers(1, 220, size=(h, w), dtype=np.uint8),
        rad_u_u8=rng.integers(1, 220, size=(h, w), dtype=np.uint8),
        rad_tc_u8=rng.integers(1, 220, size=(h, w), dtype=np.uint8),
        wellspring_df=ws,
        vent_df=vents,
        footprint=foot,
    )
    assert list(grids.keys()) == H81_FHJ_NAMES
    for nm, g in grids.items():
        assert g.dtype == np.float32 and g.shape == (h, w)
        assert np.isfinite(g).all(), nm
        assert float(g[foot].min()) >= 0.0 and float(g[foot].max()) <= 1.0, nm
        assert np.all(g[~foot] == 0.0), nm

    s = combine_junction_corridor_scores(
        np.linspace(0.01, 0.99, 100),
        np.linspace(0.99, 0.01, 100),
        np.full(100, 0.4),
        np.arange(100) % 2 == 0,
    )
    assert s.dtype == np.float32 and np.isfinite(s).all() and (s >= 0.0).all() and (s <= 1.0).all()


def test_real_data_h81_sidecar_if_restored() -> None:
    w = work_dir()
    foot_p = w / "bands" / "_footprint.npy"
    if not foot_p.exists():
        pytest.skip("restored competition bands not present")
    foot = np.load(foot_p)
    fi = np.flatnonzero(foot.ravel())
    arr = load_h81_fhj_sidecar(w, fi)
    assert arr.shape == (len(H81_FHJ_NAMES), fi.size)
    assert arr.dtype == np.float32
    assert np.isfinite(arr).all()
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
    for i, nm in enumerate(H81_FHJ_NAMES):
        assert float(np.std(arr[i])) > 0.01, f"{nm} collapsed to near-constant"
