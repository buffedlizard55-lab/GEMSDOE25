#!/usr/bin/env python3
"""Build the genuinely unique H72-CF (MBSP-MTG 100% Catalogue-Free OOF) full-footprint GeoTIFFs.

Follows `knowledge/29_h72_hypotheses_and_preregistration_2026-10-26.md` §3.3:
  * Feature stack (78 strictly catalogue-free columns, matching Experiment 3 arm `CF_G1`):
      Families A + B + C + D (64) + X1_K, X1_ThK, X1_UK, X3_gm, X3_gd (5)
      + H34 residual-magnetic/base-flexure contrasts (3) + H72 MBSP-MTG (6).
      Zero Family E, zero X2_*, and zero H27_* catalogue columns are used in training or inference.
  * Spatially blocked 4-quadrant Out-Of-Fold (OOF) prediction across 3 deterministic draws
    (`seed = 20261026 + m`, 12 models total, 15 px inter-quadrant buffer): every footprint
    pixel is scored strictly by models that never saw that quadrant's faults or covariates.
  * Emission: 1.0 px ridge NMS -> B2 known-fault collar (`EDT(~labels) > 2.0 px`) ->
    `score_ordered_dots(min_dist=2.8)` capped to top `37,654` ridge dots (matching G32 B2 / G70 budget).
  * Writes `-zeros.tif` (strict whole-array `0 <= x <= 1`), `-nan.tif`, `.zip`, and receipt JSON.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation, binary_erosion, distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, load_context  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h72 import H72_NAMES, load_h72_sidecar  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import FOLDS  # noqa: E402

CATFREE_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm", "X3_gd")
KFRAC = 0.040
MIN_DIST = 2.8
COLLAR_B2_PX = 2.0
TARGET_DOTS = 37_654
BUFFER_PX = 15
BASE_SEED = 20261026
DATE = "20261026"
SLUG = "h72-mbsp-mtg-catfree-b2-37654"
PRED_CHUNK = 400_000



def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument(
        "--verdict-note",
        default="H72-CF MBSP-MTG; no slot; unscored; not slot-approved",
    )
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    args = ap.parse_args()

    t0 = time.time()
    work, ext_dir = work_dir(), data_dir() / "external"
    ctx = load_context(work)
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    h34 = load_h34_sidecar(work, fi)
    h72 = load_h72_sidecar(work, ext_dir, foot, fi)

    base_cf_cols = ctx.columns("ABCD") + ctx.named(CATFREE_EXTRAS)
    base_cf_names = [k for k, v in sorted(ctx.col.items(), key=lambda kv: kv[1]) if v in base_cf_cols]
    assert not any(n.startswith(("E_", "X2_", "H27_", "H30_", "H31_")) for n in base_cf_names)

    # Assemble static + exact derived CATFREE_EXTRAS + H34 + H72 once on the footprint vector.
    # IMPORTANT: ctx.addon's last 2 cached rows are S_dem_c2/S_dem_s2, NOT X3_gm/X3_gd;
    # reproduce gather_columns() exactly so full inference matches Experiment 3 CF_G1.
    X_static = np.asarray(ctx.static[ctx.columns("ABCD")], dtype=np.float32)  # (64, N)
    gh = ctx.nscale("A_grav_hg_ridge", np.asarray(ctx.static[ctx.col["A_grav_hg_ridge"]]))
    mh = ctx.nscale("A_mag_hg_ridge", np.asarray(ctx.static[ctx.col["A_mag_hg_ridge"]]))
    db = ctx.nscale("D_depth_base_grad", np.asarray(ctx.static[ctx.col["D_depth_base_grad"]]))
    X_add = np.vstack([
        np.asarray(ctx.addon[:3], dtype=np.float32),
        (gh * mh).astype(np.float32),
        (gh * db).astype(np.float32),
    ])
    del gh, mh, db
    assert X_add.shape == (5, fi.size), X_add.shape
    X_all = np.vstack([X_static, X_add, np.asarray(h34, dtype=np.float32), np.asarray(h72, dtype=np.float32)])
    del X_static, X_add
    n_feat = X_all.shape[0]
    print(f"[{time.time() - t0:.1f}s] Assembled {n_feat} strictly catalogue-free columns across {fi.size:,} px", flush=True)

    # Match gems25.holdout.quadrant_ids exactly (footprint median row/col, NOT grid midpoint).
    # The irregular footprint's median row is 936 while grid midpoint is 1865; using grid midpoint
    # would silently build a different spatial split than the pre-registered experiment.
    qmasks = [ctx.holdout.quad == q for q in range(4)]
    near_lab = distance_transform_edt(~lab) <= 1.5
    p_oof = np.zeros(fi.size, dtype=np.float32)

    for q_id, q_grid in enumerate(qmasks):
        q_vec = ctx.vec(foot & q_grid)
        excl_grid = binary_dilation(q_grid, iterations=BUFFER_PX)
        tr_allow = foot & ~excl_grid
        pos_vec = ctx.vec(tr_allow & lab)
        neg_pool = ctx.vec(tr_allow & ~lab & ~near_lab)

        p_q_sum = np.zeros(q_vec.size, dtype=np.float32)
        for m in range(args.draws):
            seed_m = BASE_SEED + 100 * q_id + m
            rng = np.random.default_rng(seed_m)
            neg_vec = rng.choice(neg_pool, size=min(N_NEG, neg_pool.size), replace=False)
            tr_idx = np.sort(np.concatenate([pos_vec, neg_vec]))
            y_tr = np.isin(tr_idx, pos_vec).astype(np.int8)
            X_tr = X_all[:, tr_idx].T.copy()
            model = HistGradientBoostingClassifier(random_state=seed_m, **HGB_PARAMS).fit(X_tr, y_tr)
            del X_tr
            for lo in range(0, q_vec.size, PRED_CHUNK):
                hi = min(lo + PRED_CHUNK, q_vec.size)
                Xq = X_all[:, q_vec[lo:hi]].T
                p_q_sum[lo:hi] += model.predict_proba(Xq)[:, 1].astype(np.float32)
            del model
            print(
                f"[{time.time() - t0:.1f}s] OOF {FOLDS[q_id]} draw {m} (seed={seed_m}): "
                f"train={tr_idx.size:,} ({pos_vec.size:,} pos) -> pred={q_vec.size:,}",
                flush=True,
            )
        p_oof[q_vec] = p_q_sum / float(args.draws)

    scores_path = work / "h72_catfree_full_scores.npy"
    np.save(scores_path, p_oof)
    print(f"[{time.time() - t0:.1f}s] Saved continuous OOF surface -> {scores_path}", flush=True)

    score_grid = np.zeros(foot.shape, dtype=np.float32)
    score_grid.ravel()[fi] = p_oof
    domain = binary_erosion(foot, iterations=DOMAIN_ERODE)
    d_cat = distance_transform_edt(~lab)
    far_b2 = d_cat > COLLAR_B2_PX
    r = ridge_nms(score_grid, domain, 1.0)
    cand_scores = np.where(r & far_b2 & domain, score_grid, np.float32(0.0))
    k_pool = int(round(KFRAC * int(domain.sum())))
    top = select_top_positive(cand_scores, domain, k_pool)
    spaced = score_ordered_dots(score_grid, top, MIN_DIST)

    if int(spaced.sum()) > TARGET_DOTS:
        ys, xs = np.nonzero(spaced)
        vals = score_grid[ys, xs]
        order = np.argsort(-vals, kind="mergesort")[:TARGET_DOTS]
        em = np.zeros_like(spaced)
        em[ys[order], xs[order]] = True
    else:
        em = spaced

    assert not (em & lab).any(), "Emitted pixel collided with known catalogue"
    assert float(d_cat[em].min()) > COLLAR_B2_PX, "B2 2 px collar violated"
    med_d_cat = float(np.median(d_cat[em]))
    share_le_10 = float((d_cat[em] <= 10.0).mean())

    pred = np.where(em & foot, np.float32(1.0), np.float32(0.0))
    tmpl = data_dir() / "sample_submission.tif"
    cid = content_id(pred, foot, lab)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    recs = {}
    for outside, suffix in (("zero", "zeros"), ("nan", "nan")):
        fname = make_filename(SLUG, DATE, cid, suffix)
        tif = write_submission(pred, tmpl, out / fname, outside=outside)
        chk = check_file(tif, tmpl)
        assert chk["ok_to_upload"] and not chk["hard_failures"], chk["hard_failures"]
        recs[suffix] = dict(
            file=tif.name,
            path=f"docs/downloads/{tif.name}",
            bytes=tif.stat().st_size,
            sha256=chk["sha256"],
            content_id=cid,
            positive_pixels=chk["positive_pixels"],
            format_ok=chk["ok_to_upload"],
            hard_failures=chk["hard_failures"],
            checks=chk["checks"],
        )

    zpath = zip_single(out / recs["zeros"]["file"])
    note = f"{args.verdict_note} | id {cid}"
    assert len(note) <= 120, f"Note exceeds 120 chars ({len(note)}): {note}"

    receipt = dict(
        built_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        slug=SLUG,
        hypothesis="H72-CF MBSP-MTG 100% Catalogue-Free 4-Quadrant OOF HGB + B2 collar + 37,654 spaced ridge dots",
        n_features=int(n_feat),
        h34_columns=list(H34_NAMES),
        h72_columns=list(H72_NAMES),
        draws=int(args.draws),
        kfrac=KFRAC,
        min_dist=MIN_DIST,
        collar_b2_px=COLLAR_B2_PX,
        target_dots=TARGET_DOTS,
        positive_pixels=int(em.sum()),
        min_d_cat_px=round(float(d_cat[em].min()), 3),
        median_d_cat_px=round(med_d_cat, 3),
        share_d_cat_le_10px=round(share_le_10, 4),
        content_id=cid,
        note=note,
        scores_npy="${GEMS_WORK_DIR:-data/work}/h72_catfree_full_scores.npy",
        seconds=round(time.time() - t0, 2),
        files=dict(zeros=recs["zeros"], nan=recs["nan"], zip=f"docs/downloads/{zpath.name}"),
    )
    receipt_path = out / f"checks-{Path(recs['zeros']['file']).stem}.json"
    receipt_path.write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps({
        "zeros_file": recs["zeros"]["file"],
        "nan_file": recs["nan"]["file"],
        "zip_file": zpath.name,
        "sha256_zeros": recs["zeros"]["sha256"],
        "content_id": cid,
        "positive_pixels": int(em.sum()),
        "min_d_cat_px": receipt["min_d_cat_px"],
        "median_d_cat_px": receipt["median_d_cat_px"],
        "share_d_cat_le_10px": receipt["share_d_cat_le_10px"],
        "note": note,
        "note_len": len(note),
        "seconds": receipt["seconds"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
