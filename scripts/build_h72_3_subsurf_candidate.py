#!/usr/bin/env python3
"""Build the pre-registered H72-3 `C1_SUBSURF_PTTG_MTHS` full-footprint GeoTIFFs and run dual format audits.

Follows `knowledge/30_preregistered_h72_3_subsurf_blind_2026-10-26.md` §2 verbatim:
  * Columns (27 strictly DEM-free, LiDAR-free, catalogue-free columns):
      Family D (17) + X3_gm, X3_gd (2) + H34 (3) + PTTG_3 (3) + MTHS (2)
  * 3 deterministic component-withholding splits (`seed = 20261126 + m`), predicted on full footprint.
  * Emission: 12-px eroded domain, `ridge_nms(..., 1.0)`, `d_cat > 2.0 px` exclusion, `kfrac = 0.030`,
    `score_ordered_dots(..., min_dist=3.0)`. Zero pixels copied from any prior submission.
  * Dual automated validation: `gems25.submission.check_file` + independent `rasterio` + `zipfile` verifier.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_h72_candidate import independent_rasterio_audit  # noqa: E402
from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h72_pttg import (  # noqa: E402
    H72_MTHS_NAMES,
    H72_PTTG_NAMES,
    H72_SUBSURF_NAMES,
    load_h72_mths_sidecar,
    load_h72_pttg_sidecar,
)
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

KFRAC = 0.030
MIN_DIST = 3.0
CAT_BUF_PX = 2.0
BASE_SEED = 20261126
SLUG = "h72-3-subsurf-pttg-mths-sapd3-0-k3p0"
DATE = "20261026"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--verdict-note", required=True)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    args = ap.parse_args()

    t0 = time.time()
    work, data = work_dir(), data_dir()
    ext_dir = data / "external"
    ctx = load_context(work)
    h34_sc = load_h34_sidecar(work, ctx.fi)
    pttg_3 = load_h72_pttg_sidecar(work, ctx.fi)[:3]
    mths_sc = load_h72_mths_sidecar(work, ext_dir, ctx.fi)
    subsurf_cols = ctx.columns("D") + ctx.named(["X3_gm", "X3_gd"])
    H = ctx.holdout
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    E_zero = np.zeros((7, fi.size), dtype=np.float32)

    p_sum = np.zeros(fi.size, dtype=np.float32)
    ids = np.arange(1, H.n_comp + 1)

    for m in range(args.draws):
        seed_m = BASE_SEED + m
        rng = np.random.default_rng(seed_m)
        hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
        hidden = np.isin(H.comp, hid)
        pos = ctx.vec(hidden)
        near = distance_transform_edt(~hidden) <= 1.5
        cand = ctx.vec(foot & ~lab & ~near)
        neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
        idx = np.sort(np.concatenate([pos, neg]))
        y = np.isin(idx, pos).astype(np.int8)

        Xtr = np.hstack([
            gather_columns(ctx, E_zero, idx, True)[:, subsurf_cols],
            np.asarray(h34_sc[:, idx], dtype=np.float32).T,
            np.asarray(pttg_3[:, idx], dtype=np.float32).T,
            np.asarray(mths_sc[:, idx], dtype=np.float32).T,
        ])
        model = HistGradientBoostingClassifier(random_state=seed_m, **HGB_PARAMS).fit(Xtr, y)
        del Xtr

        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo + 500_000, fi.size))
            Xp = np.hstack([
                gather_columns(ctx, E_zero, sl, True)[:, subsurf_cols],
                np.asarray(h34_sc[:, sl], dtype=np.float32).T,
                np.asarray(pttg_3[:, sl], dtype=np.float32).T,
                np.asarray(mths_sc[:, sl], dtype=np.float32).T,
            ])
            p_sum[sl] += model.predict_proba(Xp)[:, 1].astype(np.float32)
            del Xp
        print(f"[{time.time() - t0:5.1f}s] draw {m} (seed={seed_m}) fit+predict complete ({int(y.sum()):,} pos)", flush=True)
        del model
        gc.collect()

    p_mean = (p_sum / float(args.draws)).astype(np.float32)
    scores_path = work / "h72_3_full_scores.npy"
    np.save(scores_path, p_mean)

    score_grid = np.zeros(foot.shape, dtype=np.float32)
    score_grid.ravel()[fi] = p_mean
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
    (ROOT / "evidence" / "h72_3_independent_audit_zeros.json").write_text(json.dumps(ind_z, indent=1) + "\n")
    (ROOT / "evidence" / "h72_3_independent_audit_nan.json").write_text(json.dumps(ind_n, indent=1) + "\n")

    note = make_note("H72-3 SUBSURF", args.verdict_note, cid, scored="unscored")
    assert len(note) <= 120, f"Note exceeds 120 chars ({len(note)}): {note}"

    receipt = dict(
        built_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        slug=SLUG,
        hypothesis="H72-3 C1_SUBSURF_PTTG_MTHS: 100% DEM-free & catalogue-free subsurface HGB combining Phillips gravity differential curvature, unit-consistent gravity THDR, local transtensional strain partitioning, MT pipe steps, and K-metasomatic alteration halos",
        subsurf_new_columns=H72_SUBSURF_NAMES,
        pttg_subset=H72_PTTG_NAMES[:3],
        mths_columns=H72_MTHS_NAMES,
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
        scores="work_dir()/h72_3_full_scores.npy (gitignored cache)",
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
