"""Unit tests for H79 CTHM-PoE + SGMC crustal-thermomechanical operators and PoE fusion."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine

from gems25.h79_cthm import (
    H79_ALL_NAMES,
    H79_CTHM_NAMES,
    H79_SGMC_NAMES,
    WELLSPRING_ALLOWED_COLS,
    _elliptical_gaussian_kernel,
    _load_label_free_conduit_impulses,
    compute_h79_grids,
    fuse_poe_scores,
    rank01_domain,
)


def _write_u8_tif(path: Path, bands: list[np.ndarray]) -> None:
    h, w = bands[0].shape
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=len(bands),
        dtype="uint8",
        crs="EPSG:32611",
        transform=Affine.translation(300000.0, 4400000.0) @ Affine.scale(100.0, -100.0),
    ) as dst:
        for idx, arr in enumerate(bands, start=1):
            dst.write(arr.astype(np.uint8), idx)


def test_h79_feature_names_and_label_free_allowlist() -> None:
    assert len(H79_CTHM_NAMES) == 4
    assert len(H79_SGMC_NAMES) == 1
    assert H79_ALL_NAMES == H79_CTHM_NAMES + H79_SGMC_NAMES
    assert "dist_known_fault_px" not in WELLSPRING_ALLOWED_COLS


def test_elliptical_kernel_and_poe_fusion_invariants() -> None:
    k_ns = _elliptical_gaussian_kernel(8.0, 2.0, 0.0, truncate=3.0)
    c = k_ns.shape[0] // 2
    assert k_ns.sum() == pytest.approx(1.0, abs=1e-5)
    # 0 deg cw from North -> elongated along row axis (dy), narrow along col axis (dx)
    assert float(k_ns[c - 6, c]) > 5.0 * float(k_ns[c, c + 6])

    r = rank01_domain(np.array([10.0, 20.0, 20.0, 40.0], dtype=np.float32))
    assert r.tolist() == pytest.approx([0.25, 0.625, 0.625, 1.0])

    # Floor-protected PoE keeps high-crustal zero-morpho targets strictly above low-crustal zero-morpho background
    p_c = np.array([0.01, 0.99, 0.50, 0.95], dtype=np.float32)
    p_m = np.array([0.00, 0.00, 0.80, 0.95], dtype=np.float32)
    fused = fuse_poe_scores(p_c, p_m)
    assert fused.dtype == np.float32
    assert ((fused >= 0.0) & (fused <= 1.0)).all()
    assert float(fused[1]) > float(fused[0])
    assert float(fused[3]) == pytest.approx(float(fused.max()))


def test_compute_h79_grids_end_to_end_and_zero_leakage(tmp_path: Path) -> None:
    shape = (80, 80)
    yy, xx = np.mgrid[0:80, 0:80].astype(np.float32)
    foot = np.ones(shape, dtype=bool)
    # Synthetic N-S blind fault corridor around col x = 40
    iso_grav = np.tanh((xx - 40.0) / 3.0).astype(np.float32) * 18.0
    iso_vg = (-9.0 * (xx - 40.0) / (9.0 * np.cosh((xx - 40.0) / 3.0) ** 2)).astype(np.float32)
    depth_base = (150.0 + 400.0 / (1.0 + np.exp(-(xx - 40.0) / 3.0))).astype(np.float32)
    det_elev = (1200.0 - 20.0 * np.tanh((xx - 40.0) / 4.0)).astype(np.float32)
    # Magnetite oxidation trough along x = 40 relative to deep upward-continued field
    rtp = (-70.0 * np.exp(-0.5 * ((xx - 40.0) / 2.5) ** 2) + 5.0 * np.sin(yy / 7.0)).astype(np.float32)
    tmi_vg = (0.04 * (xx - 40.0) * np.exp(-0.5 * ((xx - 40.0) / 3.0) ** 2)).astype(np.float32)
    # Antiparallel MT gouge conductivity step (higher on hangingwall x > 40 -> opposite gradient if grav drops, or ridge)
    cond = (0.02 + 0.30 * np.exp(-0.5 * ((xx - 40.0) / 2.5) ** 2)).astype(np.float32)
    e2nd = np.full(shape, 45.0, dtype=np.float32)
    ieq = (2.0 * np.exp(-0.5 * ((xx - 40.0) / 4.0) ** 2)).astype(np.float32)

    base = {
        "iso_grav_anom": iso_grav,
        "iso_grav_anom_vg": iso_vg,
        "depth_to_base_surf": depth_base,
        "det_elev": det_elev,
        "rtp": rtp,
        "tmi_vg": tmi_vg,
        "cond_surf": cond,
        "geod_2ndinv": e2nd,
        "ieq_n100a15": ieq,
    }

    up150 = np.clip(128.0 + 20.0 * np.sin(yy / 7.0), 10, 250)
    _write_u8_tif(tmp_path / "geodawn_extensions_u8.tif", [up150, up150, up150, up150])
    k_u8 = np.clip(80.0 + 110.0 * np.exp(-0.5 * ((xx - 40.0) / 2.5) ** 2), 10, 250)
    th_u8 = np.full(shape, 90.0)
    _write_u8_tif(tmp_path / "geodawn_rad_u8.tif", [k_u8, th_u8])
    sgmc = np.zeros(shape, dtype=np.uint8)
    sgmc[:, 40] = 1  # N-S fault (strike ~ 0 deg cw, near 15 deg normal optimum)
    _write_u8_tif(tmp_path / "derived_sgmc_faults_100m_u8.tif", [sgmc])

    ws_csv = tmp_path / "gdr_wellspring_in_footprint.csv"
    ws_csv.write_text(
        "row,col,temp_c,geothermquartz_c,thermalclass,dist_known_fault_px\n"
        "40,40,68.0,135.0,Hot Spring,0.0\n"
    )
    (tmp_path / "gdr_volcanic_vents_in_footprint.csv").write_text("row,col\n20,40\n")

    grids_a = compute_h79_grids(base, foot, tmp_path)
    assert set(grids_a.keys()) == set(H79_ALL_NAMES)
    for nm, arr in grids_a.items():
        assert arr.shape == shape and arr.dtype == np.float32, nm
        assert np.all(np.isfinite(arr)), nm
        assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0, nm

    # Plume elongates N-S along col=40 rather than E-W along row=40
    plume = grids_a["H79_aniso_conduit_plume"]
    assert float(plume[28, 40]) > float(plume[40, 28])
    assert float(grids_a["H79_demag_argillic_crest"][:, 39:42].mean()) > 2.5 * float(
        grids_a["H79_demag_argillic_crest"][:, 8:15].mean()
    )
    assert float(grids_a["H79_sgmc_coulomb_react"][:, 40].mean()) > 5.0 * float(
        grids_a["H79_sgmc_coulomb_react"][:, 10].mean()
    )

    # Zero-leakage proof: mutating dist_known_fault_px in CSV produces bit-identical impulses
    ws_csv.write_text(
        "row,col,temp_c,geothermquartz_c,thermalclass,dist_known_fault_px\n"
        "40,40,68.0,135.0,Hot Spring,99999.0\n"
    )
    imp_mut = _load_label_free_conduit_impulses(tmp_path, shape)
    ws_csv.write_text(
        "row,col,temp_c,geothermquartz_c,thermalclass,dist_known_fault_px\n"
        "40,40,68.0,135.0,Hot Spring,0.0\n"
    )
    imp_orig = _load_label_free_conduit_impulses(tmp_path, shape)
    assert np.array_equal(imp_orig, imp_mut)
