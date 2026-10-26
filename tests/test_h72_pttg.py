import numpy as np
import pytest

from gems25.h72_pttg import (
    H72_PTTG_NAMES,
    compute_pttg_grids,
    phillips_diff_curvature,
    unit_consistent_thdr,
)


def test_phillips_diff_curvature_is_azimuth_invariant_on_ns_vs_ew_steps():
    """Unlike E-W directional gravity gradient (band 18), K_diff responds equally to N-S and E-W steps."""
    n = 80
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    step_ns = np.tanh((xx - 40.0) / 3.0)
    step_ew = np.tanh((yy - 40.0) / 3.0)

    curv_ns = phillips_diff_curvature(step_ns, sigma_px=2.0)
    curv_ew = phillips_diff_curvature(step_ew, sigma_px=2.0)

    peak_ns = float(curv_ns[20:60, 20:60].max())
    peak_ew = float(curv_ew[20:60, 20:60].max())
    assert peak_ns > 0.01
    assert peak_ns == pytest.approx(peak_ew, rel=1e-5)

    # Confirm an E-W directional derivative (like band 18) is zero on the E-W striking step!
    _, gx_ew = np.gradient(step_ew)
    assert float(np.abs(gx_ew).max()) == pytest.approx(0.0, abs=1e-7)


def test_unit_consistent_thdr_peaks_on_contact_and_respects_units():
    n = 64
    _, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    # 2D vertical contact gravity step (atan) and corresponding vertical gradient (Lorentzian)
    z0 = 4.0  # 400 m in 100 m px
    g = np.arctan((xx - 32.0) / z0)
    # dg/dx in mGal/px = 1/z0 at x=32 -> 10 * dg/dx in mGal/km = 10/z0
    v_g = 10.0 * (xx - 32.0) / (z0 * z0 + (xx - 32.0) ** 2)  # antisymmetric vertical-like derivative
    thdr = unit_consistent_thdr(g, v_g, horiz_to_vert_scale=10.0, vert_scale=1.0, smooth_sigma=1.0)
    assert np.isfinite(thdr).all()
    center_col = int(np.argmax(thdr[32, 16:48]) + 16)
    assert abs(center_col - 32) <= 2


def test_compute_pttg_grids_finite_bounded_and_zero_outside_footprint():
    rng = np.random.default_rng(42)
    shape = (48, 52)
    foot = np.zeros(shape, dtype=bool)
    foot[4:44, 5:47] = True
    base = {
        "iso_grav_anom": rng.normal(0.0, 5.0, shape).astype(np.float32),
        "iso_grav_anom_vg": rng.normal(0.0, 2.0, shape).astype(np.float32),
        "geod_dilaterate": rng.normal(0.0, 10.0, shape).astype(np.float32),
        "geod_shearrate": np.abs(rng.normal(15.0, 5.0, shape)).astype(np.float32),
        "geod_2ndinv": np.abs(rng.normal(20.0, 6.0, shape)).astype(np.float32),
        "tmi": rng.normal(-100.0, 80.0, shape).astype(np.float32),
        "tmi_vg": rng.normal(0.0, 0.3, shape).astype(np.float32),
        "cond_surf": np.abs(rng.normal(5.0, 3.0, shape)).astype(np.float32),
        "det_elev_slope": np.abs(rng.normal(3.0, 2.0, shape)).astype(np.float32),
    }
    base["iso_grav_anom"][~foot] = np.nan
    grids = compute_pttg_grids(base, foot)
    assert list(grids.keys()) == H72_PTTG_NAMES
    for nm, g in grids.items():
        assert g.shape == shape, nm
        assert g.dtype == np.float32, nm
        assert np.isfinite(g).all(), nm
        assert float(g.min()) >= 0.0 and float(g.max()) <= 1.000001, nm
        assert float(np.abs(g[~foot]).max()) == 0.0, nm


def test_vccd_shoreline_veto_suppresses_contour_parallel_scarps(tmp_path):
    import rasterio
    from affine import Affine
    from gems25.features import LIDAR_BANDS
    from gems25.h72_pttg import H72_VCCD_NAMES, compute_vccd_grids

    shape = (64, 64)
    yy, xx = np.mgrid[0:64, 0:64].astype(np.float32)
    foot = np.ones(shape, dtype=bool)
    # Regional slope rises strictly East (grad z points East = azimuth 90 deg; contours run N-S = 0 deg)
    z = 10.0 * xx
    base = {
        "rtp": np.sin(xx / 4.0).astype(np.float32),
        "det_elev": z,
        "det_elev_slope": np.full(shape, 2.0, np.float32),
        "cond_surf": np.full(shape, 3.0, np.float32),
        "iso_grav_anom": (0.2 * xx).astype(np.float32),
        "depth_to_base_surf": (500.0 + 5.0 * xx).astype(np.float32),
    }
    # Write synthetic quantized lidar_scarp_features_u8.tif:
    # Left half: N-S strike (azimuth 0 deg, contour-parallel shoreline)
    # Right half: E-W strike (azimuth 90 deg, cross-contour fault scarp)
    rng = np.random.default_rng(7)
    q = rng.integers(80, 220, size=(len(LIDAR_BANDS), *shape), dtype=np.uint8)
    step_idx = LIDAR_BANDS.index("step_max")
    coh_idx = LIDAR_BANDS.index("coh100")
    strike_idx = LIDAR_BANDS.index("strike")
    valid_idx = LIDAR_BANDS.index("valid")
    down_idx = LIDAR_BANDS.index("downface_max")
    up_idx = LIDAR_BANDS.index("upface_max")
    q[valid_idx] = 255
    q[coh_idx] = 230
    q[step_idx, 16:48, :] = 230
    q[down_idx] = 220
    q[up_idx] = 40
    q[strike_idx, :, :32] = 1  # ~0 deg (contour-parallel shoreline)
    q[strike_idx, :, 32:] = 1 + int(round(254 * (90.0 / 180.0)))  # 90 deg (cross-contour scarp)
    with rasterio.open(
        tmp_path / "lidar_scarp_features_u8.tif",
        "w",
        driver="GTiff",
        height=64,
        width=64,
        count=len(LIDAR_BANDS),
        dtype="uint8",
        crs="EPSG:32611",
        transform=Affine(100, 0, 0, 0, -100, 6400),
    ) as dst:
        dst.write(q)
    # Write vents CSV INCLUDING quarantined column to prove usecols=["row","col"] ignores it
    (tmp_path / "gdr_volcanic_vents_in_footprint.csv").write_text(
        "row,col,dist_known_fault_px\n20,20,0.0\n"
    )
    grids = compute_vccd_grids(base, tmp_path, foot)
    assert list(grids.keys()) == H72_VCCD_NAMES
    ns = grids["RBDT_non_shoreline_scarp"]
    assert float(ns[16:48, 38:56].mean()) > 10.0 * float(ns[16:48, 8:26].mean() + 1e-6)

