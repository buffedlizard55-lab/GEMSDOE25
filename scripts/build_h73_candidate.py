#!/usr/bin/env python3
"""Build the H73-PM full-footprint research GeoTIFF (PM_DEAPRON surface) + dual format audits.

Status: HOLDOUT-NEGATIVE research artifact. Experiment 1 (`evidence/h73_pm_screen`) failed both
pre-registered gates vs same-run CTRL_H35, so this file is **not slot-approved**; it exists so the
owner can inspect the unique surface. The build-for-inspection deviation from knowledge/32 §2
(Exp 3) is logged as IR-25-H73-BUILD-AFTER-GATE-FAIL; no gate is waived or relabelled.

Method (mirrors the screened PM_DEAPRON arm exactly): H35 columns
(`BDE + EXTRAS + H27_tip` + H34 sidecar), propensity-matched negatives in d_vis bins
(`gems25.h73_pm`), 3 component-withholding splits predicted on the full catalogue, de-apron
emission (12-px eroded domain, ridge NMS, d_cat > 2 px, kfrac 0.030, score-ordered dots 2.8 px).
Zero pixels are copied from any prior submission.
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
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h73_pm import propensity_matched_negatives  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, make_note, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import EXTRAS  # noqa: E402

KFRAC, MIN_DIST, CAT_BUF_PX = 0.030, 2.8, 2.0
BASE_SEED = 20261027
SLUG = "h73-pm-deapron-sapd2-8-k3p0"
DATE = "20261026"


def independent_audit(tif_path: Path, tmpl_path: Path, lab: np.ndarray, expect_all_finite: bool, zip_path: Path | None = None) -> dict:
    with rasterio.open(tmpl_path) as tmpl, rasterio.open(tif_path) as src:
        foot = np.isfinite(tmpl.read(1))
        arr = src.read(1)
        checks = dict(
            driver_gtiff=bool(src.driver == "GTiff"),
            single_band=bool(src.count == 1),
            dtype_float32=bool(src.dtypes[0] == "float32"),
            crs_epsg32611=bool(src.crs == tmpl.crs and str(src.crs) == "EPSG:32611"),
            shape_3730x3292=bool(src.shape == tmpl.shape == (3730, 3292)),
            geotransform_exact=bool(src.transform == tmpl.transform),
            footprint_no_nan_or_inf=bool(np.isfinite(arr[foot]).all()),
            footprint_in_0_1=bool((arr[foot] >= 0.0).all() and (arr[foot] <= 1.0).all()),
            outside_ok=bool(np.isfinite(arr).all() and (arr >= 0.0).all() and (arr <= 1.0).all())
            if expect_all_finite
            else bool(np.isnan(arr[~foot]).all()),
            zero_known_catalogue_overlap=bool(not ((np.nan_to_num(arr, nan=0.0) > 0.0) & foot & lab).any()),
        )
    out = dict(
        file=tif_path.name,
        bytes=tif_path.stat().st_size,
        sha256=hashlib.sha256(tif_path.read_bytes()).hexdigest(),
        positive_pixels=int(((np.nan_to_num(arr, nan=0.0) > 0.0) & foot).sum()),
        checks=checks,
        all_hard_checks_pass=bool(all(checks.values())),
    )
    if zip_path is not None:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
        out["zip"] = dict(file=zip_path.name, bytes=zip_path.stat().st_size,
                          sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(), entries=names,
                          single_tif_at_root=bool(names == [tif_path.name]))
        out["all_hard_checks_pass"] = bool(out["all_hard_checks_pass"] and out["zip"]["single_tif_at_root"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    args = ap.parse_args()
    t0 = time.time()
    work, data = work_dir(), data_dir()
    ctx = load_context(work)
    h34 = load_h34_sidecar(work, ctx.fi)
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    H = ctx.holdout
    ns = ctx.static.shape[0]
    h35_cols = ctx.columns("BDE") + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    tip_col = ctx.col["H27_tip"]
    base_cols = [c for c in h35_cols if c != tip_col]
    assert all(c < ns + 7 + 7 for c in base_cols)  # static + E(7) + extras(7) width from gather_columns

    E_full = build_catalogue_features(lab, fi)
    tip_full = build_tip_continuation(lab, foot, fi)

    def design_matrix(E, tip, idx):
        base = gather_columns(ctx, E, idx, True)
        return np.hstack([base[:, base_cols], tip[idx].astype(np.float32)[:, None], np.asarray(h34[:, idx], dtype=np.float32).T])

    p_sum = np.zeros(fi.size, dtype=np.float32)
    ids = np.arange(1, H.n_comp + 1)
    diags = []
    for m in range(args.draws):
        seed_m = BASE_SEED + m
        rng = np.random.default_rng(seed_m)
        hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
        hidden = np.isin(H.comp, hid)
        visible = lab & ~hidden
        E_vis = build_catalogue_features(visible, fi)
        tip_vis = build_tip_continuation(visible, foot, fi)
        d_vis_vec = distance_transform_edt(~visible).ravel()[fi]
        pos = ctx.vec(hidden)
        near = distance_transform_edt(~hidden) <= 1.5
        pool = ctx.vec(foot & ~lab & ~near)
        neg, diag = propensity_matched_negatives(d_vis_vec, pos, pool, min(N_NEG, int(pool.size)), seed=seed_m + 5000)
        diags.append(diag)
        idx = np.sort(np.concatenate([pos, neg]))
        y = np.isin(idx, pos).astype(np.int8)
        model = HistGradientBoostingClassifier(random_state=seed_m, **HGB_PARAMS).fit(design_matrix(E_vis, tip_vis, idx), y)
        del E_vis, tip_vis
        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo + 500_000, fi.size))
            p_sum[sl] += model.predict_proba(design_matrix(E_full, tip_full, sl))[:, 1].astype(np.float32)
        print(f"[{time.time() - t0:5.1f}s] split {m} (seed={seed_m}) fit+predict complete ({int(y.sum()):,} pos, {int(neg.size):,} matched neg)", flush=True)
        del model
        gc.collect()
    p_mean = (p_sum / float(args.draws)).astype(np.float32)
    scores_path = work / "h73_full_scores.npy"
    np.save(scores_path, p_mean)

    score_grid = np.zeros(foot.shape, dtype=np.float32)
    score_grid.ravel()[fi] = p_mean
    domain = binary_erosion(foot, iterations=DOMAIN_ERODE)
    d_cat = distance_transform_edt(~lab).astype(np.float32)
    r = ridge_nms(score_grid, domain, 1.0)
    sc_clean = np.where(r & domain & ~lab & (d_cat > CAT_BUF_PX), score_grid, 0.0)
    top = select_top_positive(sc_clean, domain, int(round(KFRAC * float(domain.sum()))))
    dots = score_ordered_dots(sc_clean, top, MIN_DIST)
    assert not (dots & lab).any()
    dv = d_cat[dots]
    strata = dict(
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
    if zpath.exists() or npath.exists():
        raise SystemExit(f"refusing to overwrite {zpath}")
    write_submission(pred, tmpl, zpath, outside="zero")
    write_submission(pred, tmpl, npath, outside="nan")
    zzip = zip_single(zpath)
    zchk, nchk = check_file(zpath, tmpl), check_file(npath, tmpl)
    assert zchk["format_valid"] and nchk["format_valid"], (zchk["hard_failures"], nchk["hard_failures"])
    ind_z = independent_audit(zpath, tmpl, lab, True, zzip)
    ind_n = independent_audit(npath, tmpl, lab, False)
    assert ind_z["all_hard_checks_pass"] and ind_n["all_hard_checks_pass"]
    (ROOT / "evidence" / "h73_independent_audit_zeros.json").write_text(json.dumps(ind_z, indent=1) + "\n")
    (ROOT / "evidence" / "h73_independent_audit_nan.json").write_text(json.dumps(ind_n, indent=1) + "\n")
    note = make_note("H73-PM", "propensity-matched H35 deapron; holdout FAIL vs H35; DO NOT SUBMIT", cid, scored="unscored")
    assert len(note) <= 140, note
    receipt = dict(
        built_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        slug=SLUG, content_id=cid, note=note, note_chars=len(note),
        verdict="negative", slot_approved=False, ok_to_download_inspection=True, ok_to_submit_slot=False,
        hypothesis="H73-PM propensity-matched H35 (knowledge/32)",
        holdout_evidence="evidence/h73_pm_screen/analysis.json",
        draws=args.draws, base_seed=BASE_SEED, kfrac=KFRAC, min_dist=MIN_DIST, cat_buf_px=CAT_BUF_PX,
        domain_erode_px=DOMAIN_ERODE, positive_pixels=int(dots.sum()), d_cat_strata=strata,
        pm_sampler_per_split=diags,
        columns=[ctx.all_names[i] for i in h35_cols] + list(H34_NAMES),
        scores_npy=str(scores_path), seconds=round(time.time() - t0, 1),
        files=dict(zeros=ind_z, nan=ind_n),
        checks_zeros=zchk, checks_nan=nchk,
    )
    rp = ROOT / "evidence" / "h73_build" / "build_receipt.json"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(receipt, indent=1) + "\n")
    (out / f"checks-{zpath.stem}.json").write_text(json.dumps(zchk, indent=1) + "\n")
    (out / f"checks-{npath.stem}.json").write_text(json.dumps(nchk, indent=1) + "\n")
    print(json.dumps({k: receipt[k] for k in ("content_id", "positive_pixels", "d_cat_strata", "note")}, indent=1))
    print(f"zeros={zpath.name}\nnan={npath.name}\nzip={zzip.name}")


if __name__ == "__main__":
    main()
