#!/usr/bin/env python3
"""Build the pre-registered H72-1 `A3_PTTG_DEAPRON` full-footprint GeoTIFFs and run dual format audits.

Follows `knowledge/29_preregistered_h72_pttg_ranked_hypotheses_2026-10-26.md` §3.3 verbatim:
  * Arm `A3_PTTG_DEAPRON` (`0.75 * rank01(M_blind_PTTG) + 0.25 * rank01(M_tip_PTTG)`):
    - `M_blind_PTTG`: `BD + EXTRAS + H34 + H72_PTTG` (55 columns, zero Family `E` or `H27_tip`).
    - `M_tip_PTTG`:   `BD + EXTRAS + H27_tip + H30_pair_bridge + H34 + H72_PTTG` (57 columns,
      strictly strike-directed tip/bridge geometry; zero isotropic `E_dist` or `E_dens*` columns).
  * 3 deterministic component-withholding splits (`seed = 20261026 + m`), predicted on full `labels.tif`.
  * Emission: 12-px eroded domain, `ridge_nms(..., 1.0)`, `d_cat > 2.0 px` exclusion, `kfrac = 0.030`,
    `score_ordered_dots(..., min_dist=2.8)`. Zero pixels copied from any prior submission.
  * Dual automated validation: `gems25.submission.check_file` + independent `rasterio` + `zipfile` verifier.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_erosion, distance_transform_edt
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_tip_continuation  # noqa: E402
from gems25.h30 import build_paired_tip_bridge  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h72_pttg import H72_PTTG_NAMES, load_h72_pttg_sidecar  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import (  # noqa: E402
    check_file,
    content_id,
    make_filename,
    make_note,
    write_submission,
    zip_single,
)
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import EXTRAS  # noqa: E402

KFRAC = 0.030
MIN_DIST = 2.8
CAT_BUF_PX = 2.0
BASE_SEED = 20261026
SLUG = "h72-pttg-deapron-sapd2-8-k3p0"
DATE = "20261026"


def rank01(v: np.ndarray) -> np.ndarray:
    a = np.nan_to_num(np.asarray(v, dtype=np.float64), nan=0.0)
    return ((rankdata(a, method="average") - 1.0) / float(max(a.size - 1, 1))).astype(np.float32)


def independent_rasterio_audit(
    tif_path: Path,
    tmpl_path: Path,
    lab: np.ndarray,
    expect_all_finite: bool,
    zip_path: Path | None = None,
) -> dict:
    with rasterio.open(tmpl_path) as tmpl, rasterio.open(tif_path) as src:
        tmpl_arr = tmpl.read(1)
        foot = np.isfinite(tmpl_arr)
        arr = src.read(1)
        checks = dict(
            driver_gtiff=bool(src.driver == "GTiff"),
            single_band=bool(src.count == 1),
            dtype_float32=bool(src.dtypes[0] == "float32"),
            crs_epsg32611=bool(src.crs == tmpl.crs and str(src.crs) == "EPSG:32611"),
            shape_3730x3292=bool(src.shape == tmpl.shape and src.shape == (3730, 3292)),
            geotransform_exact=bool(src.transform == tmpl.transform),
            footprint_no_nan_or_inf=bool(np.isfinite(arr[foot]).all()),
            footprint_in_0_1=bool((arr[foot] >= 0.0).all() and (arr[foot] <= 1.0).all()),
            whole_array_finite_in_0_1=bool(
                np.isfinite(arr).all() and (arr >= 0.0).all() and (arr <= 1.0).all()
            )
            if expect_all_finite
            else bool(np.isnan(arr[~foot]).all()),
            zero_known_catalogue_overlap=bool(not ((arr > 0.0) & foot & lab).any()),
        )
    all_ok = bool(all(checks.values()))
    out = dict(
        file=tif_path.name,
        bytes=tif_path.stat().st_size,
        sha256=hashlib.sha256(tif_path.read_bytes()).hexdigest(),
        positive_pixels=int(((np.nan_to_num(arr, nan=0.0) > 0.0) & foot).sum()),
        checks=checks,
        all_hard_checks_pass=all_ok,
    )
    if zip_path is not None:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            out["zip"] = dict(
                file=zip_path.name,
                bytes=zip_path.stat().st_size,
                sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),
                entries=names,
                single_tif_at_root=bool(len(names) == 1 and names[0] == tif_path.name),
            )
            out["all_hard_checks_pass"] = bool(all_ok and out["zip"]["single_tif_at_root"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--verdict-note", required=True)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    args = ap.parse_args()

    t0 = time.time()
    work, data = work_dir(), data_dir()
    ctx = load_context(work)
    h34_sc = load_h34_sidecar(work, ctx.fi)
    pttg_sc = load_h72_pttg_sidecar(work, ctx.fi)
    bd7_cols = ctx.columns("BD") + ctx.named(EXTRAS)
    H = ctx.holdout
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi

    E_zero = np.zeros((7, fi.size), dtype=np.float32)
    tip_full = build_tip_continuation(lab, foot, fi)
    bridge_full, _ = build_paired_tip_bridge(lab, foot, fi)

    p_blind_sum = np.zeros(fi.size, dtype=np.float32)
    p_tip_sum = np.zeros(fi.size, dtype=np.float32)
    ids = np.arange(1, H.n_comp + 1)

    for m in range(args.draws):
        seed_m = BASE_SEED + m
        rng = np.random.default_rng(seed_m)
        hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
        hidden = np.isin(H.comp, hid)
        visible = lab & ~hidden
        pos = ctx.vec(hidden)
        near = distance_transform_edt(~hidden) <= 1.5
        cand = ctx.vec(foot & ~lab & ~near)
        neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
        idx = np.sort(np.concatenate([pos, neg]))
        y = np.isin(idx, pos).astype(np.int8)

        X_base = gather_columns(ctx, E_zero, idx, True)[:, bd7_cols]
        X_blind = np.hstack([
            X_base,
            np.asarray(h34_sc[:, idx], dtype=np.float32).T,
            np.asarray(pttg_sc[:, idx], dtype=np.float32).T,
        ])
        m_blind = HistGradientBoostingClassifier(random_state=seed_m, **HGB_PARAMS).fit(X_blind, y)
        del X_blind

        tip_vis = build_tip_continuation(visible, foot, fi)
        bridge_vis, _ = build_paired_tip_bridge(visible, foot, fi)
        X_tip = np.hstack([
            X_base,
            tip_vis[idx].astype(np.float32)[:, None],
            bridge_vis[idx].astype(np.float32)[:, None],
            np.asarray(h34_sc[:, idx], dtype=np.float32).T,
            np.asarray(pttg_sc[:, idx], dtype=np.float32).T,
        ])
        m_tip = HistGradientBoostingClassifier(random_state=seed_m + 1000, **HGB_PARAMS).fit(X_tip, y)
        del X_base, X_tip, tip_vis, bridge_vis

        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo + 500_000, fi.size))
            Xb_p = gather_columns(ctx, E_zero, sl, True)[:, bd7_cols]
            sc_h34 = np.asarray(h34_sc[:, sl], dtype=np.float32).T
            sc_pttg = np.asarray(pttg_sc[:, sl], dtype=np.float32).T
            p_blind_sum[sl] += m_blind.predict_proba(np.hstack([Xb_p, sc_h34, sc_pttg]))[:, 1].astype(np.float32)
            p_tip_sum[sl] += m_tip.predict_proba(
                np.hstack([
                    Xb_p,
                    tip_full[sl].astype(np.float32)[:, None],
                    bridge_full[sl].astype(np.float32)[:, None],
                    sc_h34,
                    sc_pttg,
                ])
            )[:, 1].astype(np.float32)
            del Xb_p, sc_h34, sc_pttg
        print(f"[{time.time() - t0:5.1f}s] draw {m} (seed={seed_m}) fit+predict complete ({int(y.sum()):,} pos)", flush=True)
        del m_blind, m_tip
        gc.collect()

    p_blind = (p_blind_sum / float(args.draws)).astype(np.float32)
    p_tip = (p_tip_sum / float(args.draws)).astype(np.float32)
    p_dual = (0.75 * rank01(p_blind) + 0.25 * rank01(p_tip)).astype(np.float32)
    scores_path = work / "h72_full_scores.npy"
    np.save(scores_path, p_dual)

    score_grid = np.zeros(foot.shape, dtype=np.float32)
    score_grid.ravel()[fi] = p_dual
    domain = binary_erosion(foot, iterations=DOMAIN_ERODE)
    d_cat = distance_transform_edt(~lab).astype(np.float32)
    r = ridge_nms(score_grid, domain, 1.0)
    sc_clean = np.where(r & domain & ~lab & (d_cat > CAT_BUF_PX), score_grid, 0.0)
    k_budget = int(round(KFRAC * float(domain.sum())))
    top = select_top_positive(sc_clean, domain, k_budget)
    dots = score_ordered_dots(sc_clean, top, MIN_DIST)
    assert not (dots & lab).any(), "emitted pixel overlapped known catalogue"

    dv = d_cat[dots]
    d_cat_strata = dict(
        frac_le2=round(float((dv <= 2.0).mean()), 5),
        frac_2_9=round(float(((dv > 2.0) & (dv <= 9.0)).mean()), 5),
        frac_9_20=round(float(((dv > 9.0) & (dv <= 20.0)).mean()), 5),
        frac_gt20=round(float((dv > 20.0).mean()), 5),
        median_d_cat_px=round(float(np.median(dv)), 3),
    )

    pred = np.where(foot, dots.astype(np.float32), np.float32(0.0))
    cid = content_id(pred, foot, lab)
    tmpl = data / "sample_submission.tif"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    zpath = out / make_filename(SLUG, DATE, cid, "zeros")
    npath = out / make_filename(SLUG, DATE, cid, "nan")
    write_submission(pred, tmpl, zpath, outside="zero")
    write_submission(pred, tmpl, npath, outside="nan")
    zzip = zip_single(zpath)

    zchk = check_file(zpath, tmpl)
    nchk = check_file(npath, tmpl)
    assert zchk["ok_to_upload"] and not zchk["hard_failures"], zchk["hard_failures"]
    assert nchk["ok_to_upload"] and not nchk["hard_failures"], nchk["hard_failures"]

    ind_z = independent_rasterio_audit(zpath, tmpl, lab, expect_all_finite=True, zip_path=zzip)
    ind_n = independent_rasterio_audit(npath, tmpl, lab, expect_all_finite=False, zip_path=None)
    assert ind_z["all_hard_checks_pass"], ind_z
    assert ind_n["all_hard_checks_pass"], ind_n
    (ROOT / "evidence" / "h72_independent_audit_zeros.json").write_text(json.dumps(ind_z, indent=1) + "\n")
    (ROOT / "evidence" / "h72_independent_audit_nan.json").write_text(json.dumps(ind_n, indent=1) + "\n")

    note = make_note("H72-1 PTTG-DA", args.verdict_note, cid, scored="unscored")
    assert len(note) <= 120, f"Note exceeds 120 chars ({len(note)}): {note}"

    receipt = dict(
        built_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        slug=SLUG,
        hypothesis="H72-1 A3_PTTG_DEAPRON: Phillips gravity differential curvature + unit-consistent gravity/mag THDR + local transtensional strain partitioning in de-aproned dual-regime HGB (zero isotropic E_dist/E_dens*)",
        pttg_columns=H72_PTTG_NAMES,
        h34_columns=H34_NAMES,
        draws=args.draws,
        base_seed=BASE_SEED,
        kfrac=KFRAC,
        min_dist=MIN_DIST,
        cat_buf_px=CAT_BUF_PX,
        domain_erode_px=DOMAIN_ERODE,
        positive_pixels=int(dots.sum()),
        d_cat_strata=d_cat_strata,
        content_id=cid,
        note=note,
        note_chars=len(note),
        seconds=round(time.time() - t0, 1),
        scores="work_dir()/h72_full_scores.npy (gitignored cache)",
        files=dict(zeros=zchk, nan=nchk, zip=zzip.name),
    )
    receipt_path = out / f"checks-{zpath.stem}.json"
    receipt_path.write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps(dict(
        zeros=zpath.name,
        nan=npath.name,
        zip=zzip.name,
        content_id=cid,
        positive_pixels=int(dots.sum()),
        d_cat_strata=d_cat_strata,
        note=note,
        note_chars=len(note),
        zeros_ok=zchk["ok_to_upload"],
        nan_ok=nchk["ok_to_upload"],
        seconds=receipt["seconds"],
    ), indent=2))


if __name__ == "__main__":
    main()
