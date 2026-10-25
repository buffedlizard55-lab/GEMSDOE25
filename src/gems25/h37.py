"""H37-1 DOC — down-dip offset concordance columns (pre-registered, knowledge/22).

Six static columns, computed once from the pinned competition bands and stored as a
footprint-vector sidecar so the shared harness (`gems25.experiment.Cell`) is untouched
(same pattern as `gems25.h34`):

For each subsurface ridge field S in {isostatic-gravity HG ridge, TMI HG ridge,
conductive-base flexure ridge (the H34 definition)} and the local **downhill** unit
vector u of the smoothed detrended DEM (the basinward dip proxy):

* ``DOC_<f>_down = max(S(x+2u), S(x+4u))``     — strongest step 200-400 m down-dip
* ``DOC_<f>_asym = DOC_<f>_down - max(S(x-2u), S(x-4u))`` — signed down/up asymmetry

Columns are evaluated at the candidate *surface-trace* pixel x; bilinear sampling,
``mode="nearest"`` at grid edges. Where the DEM gradient magnitude is <= 1e-6 the
direction is 0, so ``down`` reduces to the zero-lag value and ``asym`` to exactly 0.

Physical target: a buried basin-margin normal fault keeps a potential-field /
conductive-base step at depth, laterally displaced down-dip of its eroded/buried
surface trace; every concordance feature already in this repo is zero-lag.
Named mimics: alluvial-fan wedges prograding off unfaulted bedrock slopes,
lava-flow / intrusion margins, pluvial-shoreline benches (knowledge/22 section 1).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from .features import grad_mag, nearest_fill, ridge_strength

H37_NAMES = [
    "DOC_grav_down", "DOC_grav_asym",
    "DOC_mag_down", "DOC_mag_asym",
    "DOC_base_down", "DOC_base_asym",
]
RIDGE_SIGMA = 1.5
DEM_SMOOTH_SIGMA = 2.0
LAGS_PX = (2.0, 4.0)
GRAD_EPS = 1e-6


def downhill_unit(det_elev: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(u_row, u_col) downhill unit vector of the smoothed DEM; 0 where |grad| <= eps.

    ``det_elev`` must be finite (fill nodata first). Array (row, col) coordinates are
    used consistently for both the gradient and the lag sampling.
    """
    z = np.asarray(det_elev, dtype=np.float64)
    if z.ndim != 2 or not np.isfinite(z).all():
        raise ValueError("downhill_unit needs a finite 2-D elevation grid (fill nodata first)")
    gy, gx = np.gradient(gaussian_filter(z, DEM_SMOOTH_SIGMA))
    mag = np.hypot(gy, gx)
    ok = mag > GRAD_EPS
    u_row = np.where(ok, -gy / np.maximum(mag, 1e-300), 0.0).astype(np.float32)
    u_col = np.where(ok, -gx / np.maximum(mag, 1e-300), 0.0).astype(np.float32)
    return u_row, u_col


def lag_sample(field: np.ndarray, u_row: np.ndarray, u_col: np.ndarray, lag: float,
               block: int = 256) -> np.ndarray:
    """S(x + lag*u) by bilinear sampling, computed in row blocks to bound memory."""
    S = np.asarray(field, dtype=np.float64)
    if S.shape != u_row.shape or S.shape != u_col.shape:
        raise ValueError("field and direction grids must have equal shapes")
    H, W = S.shape
    out = np.empty((H, W), np.float32)
    cols = np.arange(W, dtype=np.float64)
    for r0 in range(0, H, block):
        r1 = min(H, r0 + block)
        rows = np.arange(r0, r1, dtype=np.float64)[:, None]
        rr = rows + lag * u_row[r0:r1].astype(np.float64)
        cc = cols[None, :] + lag * u_col[r0:r1].astype(np.float64)
        out[r0:r1] = map_coordinates(S, [rr, cc], order=1, mode="nearest").astype(np.float32)
    return out


def doc_pair(field: np.ndarray, u_row: np.ndarray, u_col: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(down, asym) for one subsurface ridge field at the frozen lags (+/-2, +/-4 px)."""
    down = np.maximum(lag_sample(field, u_row, u_col, LAGS_PX[0]),
                      lag_sample(field, u_row, u_col, LAGS_PX[1]))
    up = np.maximum(lag_sample(field, u_row, u_col, -LAGS_PX[0]),
                    lag_sample(field, u_row, u_col, -LAGS_PX[1]))
    return down.astype(np.float32), (down - up).astype(np.float32)


def h37_grids(det_elev: np.ndarray, iso_grav_hg: np.ndarray, tmi_hg: np.ndarray,
              depth_to_base: np.ndarray) -> dict[str, np.ndarray]:
    """The six DOC grids from raw band grids (NaN nodata allowed; filled internally).

    Ridge fields use the repo's existing definitions: ``A_grav_hg_ridge`` /
    ``A_mag_hg_ridge`` (`gems25.features.build_static`) and ``H34_baseflex_ridge``
    (`gems25.h34.h34_grids`).
    """
    u_row, u_col = downhill_unit(nearest_fill(np.asarray(det_elev, dtype=np.float32)))
    grav = ridge_strength(nearest_fill(np.asarray(iso_grav_hg, dtype=np.float32)), RIDGE_SIGMA)
    mag = ridge_strength(np.log1p(
        nearest_fill(np.asarray(tmi_hg, dtype=np.float32))), RIDGE_SIGMA)
    depth_f = nearest_fill(np.asarray(depth_to_base, dtype=np.float32))
    base = ridge_strength(grad_mag(np.log1p(np.maximum(depth_f, 0.0)), 1.0), RIDGE_SIGMA)
    out: dict[str, np.ndarray] = {}
    for name, field in (("grav", grav), ("mag", mag), ("base", base)):
        down, asym = doc_pair(field, u_row, u_col)
        out[f"DOC_{name}_down"] = down
        out[f"DOC_{name}_asym"] = asym
    return {n: out[n] for n in H37_NAMES}


def build_h37_sidecar(band_dir: Path, footprint_idx: np.ndarray, out_path: Path) -> list[str]:
    """Build (6, n_footprint) float32 sidecar + names JSON from ``work/bands`` grids."""
    band_dir = Path(band_dir)
    grids = h37_grids(
        np.load(band_dir / "12_det_elev.npy"),
        np.load(band_dir / "18_iso_grav_anom_hg.npy"),
        np.load(band_dir / "03_tmi_hg.npy"),
        np.load(band_dir / "15_depth_to_base_surf.npy"),
    )
    fi = np.asarray(footprint_idx)
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32,
                                   shape=(len(H37_NAMES), fi.size))
    for j, name in enumerate(H37_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"H37 column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(H37_NAMES))
    return list(H37_NAMES)


def load_h37_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load the sidecar, building it from the cached bands if absent. Returns (6, n_foot)."""
    work = Path(work)
    path = work / "h37_doc_columns.npy"
    if not path.exists():
        build_h37_sidecar(work / "bands", footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != H37_NAMES or arr.shape != (len(H37_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"H37 sidecar mismatch: names={names} shape={arr.shape}")
    return arr


# --- H37-2 SPR: spring-line alignment ridge (pre-registered knowledge/23) --------

SPR_NAMES = ["SPR_kde_ridge", "SPR_ridge_x_elong"]
SPR_KDE_SIGMA = 3.0
SPR_TENSOR_SMOOTH = 2.0


def spring_kde(rows: np.ndarray, cols: np.ndarray, shape: tuple, footprint: np.ndarray) -> np.ndarray:
    """Gaussian KDE (sigma=3 px) of point counts, normalized by its footprint max."""
    cnt = np.zeros(shape, np.float32)
    r = np.asarray(rows)
    c = np.asarray(cols)
    ok = (r >= 0) & (r < shape[0]) & (c >= 0) & (c < shape[1])
    np.add.at(cnt, (r[ok], c[ok]), 1.0)
    k = gaussian_filter(cnt, SPR_KDE_SIGMA)
    foot = np.asarray(footprint, bool)
    mx = float(k[foot].max()) if foot.any() else 0.0
    return (k / mx if mx > 0 else k).astype(np.float32)


def structure_coherence(k: np.ndarray) -> np.ndarray:
    """Structure-tensor coherence of the smoothed field, in [0, 1]; 0 where flat."""
    s = gaussian_filter(np.asarray(k, dtype=np.float64), SPR_TENSOR_SMOOTH)
    gy, gx = np.gradient(s)
    jxx = gaussian_filter(gx * gx, SPR_TENSOR_SMOOTH)
    jyy = gaussian_filter(gy * gy, SPR_TENSOR_SMOOTH)
    jxy = gaussian_filter(gx * gy, SPR_TENSOR_SMOOTH)
    trace = jxx + jyy
    coh = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy**2) / (trace + 1e-12)
    return np.where(trace > 0, np.clip(coh, 0.0, 1.0), 0.0).astype(np.float32)


def spr_grids(rows: np.ndarray, cols: np.ndarray, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """The two frozen SPR grids (knowledge/23) from hot-spring point coordinates."""
    foot = np.asarray(footprint, bool)
    k = spring_kde(rows, cols, foot.shape, foot)
    ridge = ridge_strength(k, RIDGE_SIGMA)
    elong = structure_coherence(k)
    return {SPR_NAMES[0]: ridge, SPR_NAMES[1]: (ridge * elong).astype(np.float32)}


def build_spr_sidecar(csv_path: Path, footprint: np.ndarray, footprint_idx: np.ndarray,
                      out_path: Path) -> list[str]:
    """Build (2, n_footprint) float32 SPR sidecar from the pinned GDR 1391 CSV.

    Only ``thermalclass == "Hot"`` points are used; the CSV's label-derived
    ``dist_known_fault_px`` column is never read into a feature.
    """
    import pandas as pd

    df = pd.read_csv(csv_path)
    hot = df[df.thermalclass.astype(str).str.strip() == "Hot"]
    grids = spr_grids(hot.row.to_numpy(), hot.col.to_numpy(), np.asarray(footprint, bool))
    fi = np.asarray(footprint_idx)
    mm = np.lib.format.open_memmap(Path(out_path), mode="w+", dtype=np.float32,
                                   shape=(len(SPR_NAMES), fi.size))
    for j, name in enumerate(SPR_NAMES):
        v = np.asarray(grids[name], dtype=np.float32).ravel()[fi]
        if not np.isfinite(v).all():
            raise ValueError(f"SPR column {name} has non-finite values inside the footprint")
        mm[j] = v
    mm.flush()
    Path(str(out_path) + ".names.json").write_text(json.dumps(SPR_NAMES))
    return list(SPR_NAMES)


def load_spr_sidecar(work: Path, footprint_idx: np.ndarray) -> np.ndarray:
    """Load the SPR sidecar, building it from the pinned CSV if absent. (2, n_foot)."""
    from .paths import data_dir

    work = Path(work)
    path = work / "h37_spr_columns.npy"
    if not path.exists():
        foot = np.load(work / "bands" / "_footprint.npy")
        build_spr_sidecar(data_dir() / "external" / "gdr_wellspring_in_footprint.csv",
                          foot, footprint_idx, path)
    arr = np.load(path, mmap_mode="r")
    names = json.loads(Path(str(path) + ".names.json").read_text())
    if names != SPR_NAMES or arr.shape != (len(SPR_NAMES), np.asarray(footprint_idx).size):
        raise ValueError(f"SPR sidecar mismatch: names={names} shape={arr.shape}")
    return arr
