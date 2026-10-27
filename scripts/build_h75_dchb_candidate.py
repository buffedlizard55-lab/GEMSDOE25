#!/usr/bin/env python3
"""Build the full-footprint 4-quadrant LOQO OOF H75_CG_BLIND Corridor-Gated Dual-Regime GeoTIFF.

Pre-registered in ``knowledge/38_preregistered_h75_dchb_cg_2026-10-27.md`` (committed at ``12931bb``):
  - Zero Family E (catalogue distance/density/tip), zero labels/SGMC in feature builders.
  - Three LOQO expert ensembles per quadrant (2 seeds: 20261201, 20261202 -> 24 HGB models total):
      * M_corridor (54 topography-free subsurface + Darcy/UTh/Blakely corridor cols)
      * M_trace    (83 full static ABCD + EXTRAS + H34 + H74_RMPS + H75_DCHB cols)
      * M_gap      (70 LiDAR-free cols for the 24.66% L_valid == 0 3DEP gap)
  - Coupled via frozen ``combine_corridor_gated_scores(..., gamma=0.60, gap_scale=0.95)``.
  - Pre-publish staging duplicate guard: verifies continuous surface ``|Spearman| <= 0.90`` AND
    density-aware final-dot uniqueness (``flagged_lane == []``, ``external_sparse.lane_pass == True``,
    ``own_lineage.lane_pass == True``) across all 106+ registry rasters BEFORE writing to ``docs/downloads/``.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, binary_erosion, distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.greedy import greedy_dots  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h74_rmps import H74_RMPS_NAMES, load_h74_rmps_sidecar  # noqa: E402
from gems25.h75_dchb import (  # noqa: E402
    CORRIDOR_GAMMA_DEFAULT,
    H75_CORRIDOR_SUBSET,
    H75_DCHB_NAMES,
    LIDAR_GAP_SCALE_DEFAULT,
    combine_corridor_gated_scores,
    load_h75_dchb_sidecar,
)
from gems25.holdout import COLLAR_PX, FOLD_NAMES, quadrant_ids  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, select_top_positive  # noqa: E402
from run_h28_holdout import EXTRAS  # noqa: E402

DATE_TAG = "20261027"
MAX_DOTS = 37_654
KFRAC = 0.035
CAT_BUF_PX = 2.0
LOQO_SEEDS = (20261201, 20261202)
SUBSURF_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm")
NOTE = "H75-DCHB-CG blind LOQO B2 37654d [DO NOT SUBMIT: G2 checkerboard PASS, G1<H35; research]"
assert len(NOTE) <= 120


def independent_rasterio_audit(path: Path, tmpl_path: Path, kind: str) -> dict:
    with rasterio.open(tmpl_path) as t, rasterio.open(path) as s:
        tb = t.read(1)
        sb = s.read(1)
        foot = np.isfinite(tb)
        inside = sb[foot]
        outside = sb[~foot]
        info = dict(
            path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            size_bytes=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            crs=str(s.crs),
            shape=list(s.shape),
            count=s.count,
            dtype=str(s.dtypes[0]),
            transform=[round(float(x), 6) for x in s.transform[:6]],
            crs_matches=(s.crs == t.crs),
            shape_matches=(s.shape == t.shape),
            transform_matches=(s.transform == t.transform),
            inside_nan_count=int(np.isnan(inside).sum()),
            inside_inf_count=int(np.isinf(inside).sum()),
            inside_min=float(np.nanmin(inside)),
            inside_max=float(np.nanmax(inside)),
            inside_in_0_1=bool(
                np.isfinite(inside).all() and inside.min() >= 0.0 and inside.max() <= 1.0
            ),
            inside_positive_dots=int((inside > 0.0).sum()),
            inside_unique_values=[float(v) for v in np.unique(inside)[:10]],
        )
        if kind == "zeros":
            info["outside_all_zero"] = bool(np.all(outside == 0.0))
        else:
            info["outside_all_nan"] = bool(np.isnan(outside).all())
        return info


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rebuild-surface", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    work = work_dir()
    data = data_dir()
    tmpl = data / "sample_submission.tif"
    ctx = load_context(work)
    h34_mm = load_h34_sidecar(work, ctx.fi)
    h74_mm = load_h74_rmps_sidecar(work, ctx.fi)
    h75_mm = load_h75_dchb_sidecar(work, ctx.fi)

    l_valid_fi = np.asarray(ctx.static[ctx.static_names.index("L_valid")], dtype=np.float32) > 0.5
    l_valid_grid = np.zeros(ctx.foot.shape, dtype=bool)
    l_valid_grid.ravel()[ctx.fi] = l_valid_fi

    union_names = (
        list(ctx.static_names)
        + list(ctx.e_names)
        + list(ctx.extra_names)
        + list(H34_NAMES)
        + list(H74_RMPS_NAMES)
        + list(H75_DCHB_NAMES)
    )
    assert len(union_names) == 90
    ucol = {n: i for i, n in enumerate(union_names)}

    acd_sub_names = [ctx.all_names[i] for i in ctx.columns("ACD")] + list(SUBSURF_EXTRAS)
    abcd_ext_names = [ctx.all_names[i] for i in ctx.columns("ABCD")] + list(EXTRAS)
    m_corridor_names = acd_sub_names + list(H34_NAMES) + list(H74_RMPS_NAMES) + list(H75_CORRIDOR_SUBSET)
    m_trace_names = abcd_ext_names + list(H34_NAMES) + list(H74_RMPS_NAMES) + list(H75_DCHB_NAMES)
    m_gap_names = [n for n in m_trace_names if not n.startswith("L_")]

    assert (len(m_corridor_names), len(m_trace_names), len(m_gap_names)) == (54, 83, 70)
    assert not any(n.startswith(("B_", "L_", "E_")) for n in m_corridor_names)
    assert not any(n.startswith("E_") for n in m_trace_names)
    assert not any(n.startswith(("L_", "E_")) for n in m_gap_names)

    cols_cor = [ucol[n] for n in m_corridor_names]
    cols_tr = [ucol[n] for n in m_trace_names]
    cols_gp = [ucol[n] for n in m_gap_names]

    e_zero = np.zeros((len(ctx.e_names), ctx.fi.size), dtype=np.float32)

    def gather_union90(idx: np.ndarray) -> np.ndarray:
        X = np.empty((idx.size, 90), dtype=np.float32)
        gather_columns(ctx, e_zero, idx, True, out=X[:, :78])
        X[:, 78:81] = np.asarray(h34_mm[:, idx], dtype=np.float32).T
        X[:, 81:85] = np.asarray(h74_mm[:, idx], dtype=np.float32).T
        X[:, 85:90] = np.asarray(h75_mm[:, idx], dtype=np.float32).T
        return X

    scores_path = work / "h75_cg_blind_oof_scores.npy"
    cor_scores_path = work / "h75_corridor_oof_scores.npy"
    quad_meta_path = work / "h75_cg_blind_quad_meta.json"

    if scores_path.exists() and not args.rebuild_surface:
        oof_scores = np.load(scores_path)
        quad_meta = json.loads(quad_meta_path.read_text()) if quad_meta_path.exists() else []
        print(f"Loaded cached LOQO OOF surface {scores_path} (n={oof_scores.size:,})", flush=True)
    else:
        qid = quadrant_ids(ctx.foot)
        near_cat = distance_transform_edt(~ctx.labels) <= 1.5
        oof_scores = np.zeros(ctx.fi.size, dtype=np.float32)
        oof_cor = np.zeros(ctx.fi.size, dtype=np.float32)
        quad_meta = []

        for q_i, q_name in enumerate(FOLD_NAMES):
            tq = time.time()
            q_foot = qid == q_i
            collar = binary_dilation(q_foot, iterations=COLLAR_PX)
            tr_foot = ctx.foot & ~collar

            pos_tr = ctx.vec(tr_foot & ctx.labels)
            cand_neg = ctx.vec(tr_foot & ~ctx.labels & ~near_cat)
            q_idx = ctx.vec(q_foot)
            lv_q = l_valid_fi[q_idx]
            Xq = gather_union90(q_idx)

            p_cor_acc = np.zeros(q_idx.size, dtype=np.float64)
            p_tr_acc = np.zeros(q_idx.size, dtype=np.float64)
            p_gp_acc = np.zeros(q_idx.size, dtype=np.float64)
            iters = []

            for s_i, seed in enumerate(LOQO_SEEDS):
                rng = np.random.default_rng(seed + 101 * q_i + s_i)
                neg_tr = rng.choice(cand_neg, size=min(N_NEG, cand_neg.size), replace=False)
                tr_idx = np.sort(np.concatenate([pos_tr, neg_tr]))
                y_tr = np.isin(tr_idx, pos_tr).astype(np.int8)
                Xtr = gather_union90(tr_idx)

                clf_cor = HistGradientBoostingClassifier(random_state=seed + q_i, **HGB_PARAMS).fit(Xtr[:, cols_cor], y_tr)
                p_cor_acc += clf_cor.predict_proba(np.ascontiguousarray(Xq[:, cols_cor]))[:, 1]
                n_it_cor = int(clf_cor.n_iter_)
                del clf_cor

                clf_tr = HistGradientBoostingClassifier(random_state=seed + 10 + q_i, **HGB_PARAMS).fit(Xtr[:, cols_tr], y_tr)
                p_tr_acc += clf_tr.predict_proba(np.ascontiguousarray(Xq[:, cols_tr]))[:, 1]
                n_it_tr = int(clf_tr.n_iter_)
                del clf_tr

                clf_gp = HistGradientBoostingClassifier(random_state=seed + 20 + q_i, **HGB_PARAMS).fit(Xtr[:, cols_gp], y_tr)
                p_gp_acc += clf_gp.predict_proba(np.ascontiguousarray(Xq[:, cols_gp]))[:, 1]
                n_it_gp = int(clf_gp.n_iter_)
                del clf_gp, Xtr
                gc.collect()
                iters.append(dict(seed=seed, cor=n_it_cor, trace=n_it_tr, gap=n_it_gp))

            p_cor_q = (p_cor_acc / len(LOQO_SEEDS)).astype(np.float32)
            p_tr_q = (p_tr_acc / len(LOQO_SEEDS)).astype(np.float32)
            p_gp_q = (p_gp_acc / len(LOQO_SEEDS)).astype(np.float32)
            p_cg_q = combine_corridor_gated_scores(
                p_cor_q,
                p_tr_q,
                p_gp_q,
                lv_q,
                gamma=CORRIDOR_GAMMA_DEFAULT,
                gap_scale=LIDAR_GAP_SCALE_DEFAULT,
            )
            oof_scores[q_idx] = p_cg_q
            oof_cor[q_idx] = p_cor_q
            quad_meta.append(
                dict(
                    quadrant=q_name,
                    n_train_pos=int(pos_tr.size),
                    n_pred_px=int(q_idx.size),
                    lidar_gap_share=round(float((~lv_q).mean()), 5),
                    n_iter=iters,
                    mean_prob=round(float(p_cg_q.mean()), 6),
                    p99_prob=round(float(np.quantile(p_cg_q, 0.99)), 6),
                    elapsed_s=round(time.time() - tq, 2),
                )
            )
            print(
                f"LOQO {q_name}: pos={pos_tr.size:,} pred={q_idx.size:,} "
                f"p99={quad_meta[-1]['p99_prob']:.4f} ({time.time() - tq:.1f}s)",
                flush=True,
            )
            del Xq, p_cor_acc, p_tr_acc, p_gp_acc
            gc.collect()

        np.save(scores_path, oof_scores)
        np.save(cor_scores_path, oof_cor)
        quad_meta_path.write_text(json.dumps(quad_meta, indent=1) + "\n")

    surface_sha256 = hashlib.sha256(oof_scores.tobytes()).hexdigest()

    # Stage 1: pre-placement continuous surface check BEFORE dot placement
    surf_out = ROOT / "evidence" / "h75_cg_surface_lane.json"
    res_surf = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_lane_surface.py"), str(scores_path), "--out", str(surf_out)],
        capture_output=True,
        text=True,
    )
    print("Surface lane check stdout:", res_surf.stdout.strip(), flush=True)
    if res_surf.returncode != 0:
        raise RuntimeError(f"PRE-PLACEMENT SURFACE DUPLICATE STOP:\n{res_surf.stdout}\n{res_surf.stderr}")
    surf_rec = json.loads(surf_out.read_text())
    assert surf_rec["flagged"] == [], f"Surface flagged: {surf_rec['flagged']}"

    # Stage 2: B2-hygiene submodular greedy dot placement on full footprint
    t_em = time.time()
    p_grid = np.zeros(ctx.foot.shape, dtype=np.float32)
    p_grid.ravel()[ctx.fi] = np.nan_to_num(oof_scores, nan=0.0).astype(np.float32)
    dom = binary_erosion(ctx.foot, iterations=DOMAIN_ERODE)
    d_cat = distance_transform_edt(~ctx.labels).astype(np.float32)
    excl = ctx.labels | (d_cat <= CAT_BUF_PX)
    ridge = ridge_nms(p_grid, dom, 1.0)
    s_clean = np.where(ridge & ~excl, p_grid, 0.0)
    pool_k = int(round(KFRAC * float(dom.sum())))
    top = select_top_positive(s_clean, dom, pool_k)
    n_hat_full = max(0.25 * float((ctx.labels & dom).sum()), 100.0)
    emitted, gdiag = greedy_dots(p_grid, top, dom, excl, n_hat_full, max_dots=MAX_DOTS)
    emitted &= dom & ~excl
    n_dots = int(emitted.sum())
    print(
        f"Emitted {n_dots:,} dots (stop={gdiag['stop_reason']}, plugin_dti={gdiag['plugin_dti']:.5f}) "
        f"in {time.time() - t_em:.1f}s",
        flush=True,
    )
    assert 0 < n_dots <= MAX_DOTS, f"Unexpected dot count: {n_dots}"

    pred = emitted.astype(np.float32)
    payload_sha12 = hashlib.sha256(np.packbits(emitted.ravel()).tobytes()).hexdigest()[:12]
    stem = f"gems25-h75-dchb-cg-catfree-b2-{n_dots}-{DATE_TAG}-{payload_sha12}"

    # Stage 3: Staging density-aware uniqueness check BEFORE publishing to docs/downloads/
    stage_dir = work / "staging_h75_cg"
    stage_dir.mkdir(parents=True, exist_ok=True)
    stage_zeros = stage_dir / f"{stem}-zeros.tif"
    write_submission(pred, tmpl, stage_zeros, outside="zero")

    stage_lit_out = work / "staging_h75_cg_lane_lit.json"
    stage_ext_out = work / "staging_h75_cg_lane_ext.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_lane_duplicates.py"), str(stage_zeros), "--out", str(stage_lit_out)],
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "lane_check_extended.py"),
            str(stage_zeros),
            "--scores",
            str(scores_path),
            "--out",
            str(stage_ext_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    lit_rec = json.loads(stage_lit_out.read_text())
    ext_rec = json.loads(stage_ext_out.read_text())
    print(
        "Staging literal/density check:",
        {k: lit_rec[k] for k in ("verdict", "verdict_density_aware", "flagged_literal", "flagged_lane", "registry_checked")},
        flush=True,
    )
    print("Staging extended check:", {k: ext_rec[k] for k in ("external_sparse", "own_lineage")}, flush=True)

    if (
        lit_rec["flagged_lane"]
        or not ext_rec["external_sparse"]["lane_pass"]
        or not ext_rec["own_lineage"]["lane_pass"]
    ):
        (ROOT / "evidence" / "h75_cg_stopped_lane.json").write_text(json.dumps(lit_rec, indent=1) + "\n")
        (ROOT / "evidence" / "h75_cg_stopped_extended.json").write_text(json.dumps(ext_rec, indent=1) + "\n")
        raise RuntimeError(
            f"FINAL-DOT DENSITY-AWARE DUPLICATE STOP: refusing to write to docs/downloads/: "
            f"flagged_lane={lit_rec['flagged_lane']} ext={ext_rec['external_sparse']['lane_pass']} "
            f"own={ext_rec['own_lineage']['lane_pass']}"
        )

    # Passed both pre-placement surface AND density-aware final-dot uniqueness -> publish!
    dl_dir = ROOT / "docs" / "downloads"
    zeros_path = dl_dir / f"{stem}-zeros.tif"
    nan_path = dl_dir / f"{stem}-nan.tif"
    zip_path = dl_dir / f"{stem}.zip"
    write_submission(pred, tmpl, zeros_path, outside="zero")
    write_submission(pred, tmpl, nan_path, outside="nan")
    zip_single(zeros_path, zip_path)

    val_zeros = check_file(zeros_path, tmpl)
    val_nan = check_file(nan_path, tmpl)
    assert val_zeros["ok_to_upload"] and val_nan["ok_to_upload"]
    ind_zeros = independent_rasterio_audit(zeros_path, tmpl, "zeros")
    ind_nan = independent_rasterio_audit(nan_path, tmpl, "nan")
    assert ind_zeros["crs_matches"] and ind_zeros["shape_matches"] and ind_zeros["transform_matches"]
    assert ind_zeros["inside_in_0_1"] and ind_zeros["outside_all_zero"]
    assert ind_nan["inside_in_0_1"] and ind_nan["outside_all_nan"]

    # Re-run official lane scripts against final published file so own_downloads excludes itself cleanly
    pub_lit_out = ROOT / "evidence" / "h75_cg_lane_literal.json"
    pub_ext_out = ROOT / "evidence" / "h75_cg_lane_extended.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_lane_duplicates.py"), str(zeros_path), "--out", str(pub_lit_out)],
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "lane_check_extended.py"),
            str(zeros_path),
            "--scores",
            str(scores_path),
            "--out",
            str(pub_ext_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    em_dcat = d_cat[emitted]
    lgap_emit_share = round(float((~l_valid_grid[emitted]).mean()), 5)
    build_meta = dict(
        stem=stem,
        note=NOTE,
        note_len=len(NOTE),
        corridor_gamma=CORRIDOR_GAMMA_DEFAULT,
        lidar_gap_scale=LIDAR_GAP_SCALE_DEFAULT,
        feature_counts=dict(
            m_corridor=len(m_corridor_names),
            m_trace=len(m_trace_names),
            m_gap=len(m_gap_names),
        ),
        m_corridor_names=m_corridor_names,
        m_trace_names=m_trace_names,
        m_gap_names=m_gap_names,
        loqo_seeds=list(LOQO_SEEDS),
        quadrants=quad_meta,
        oof_surface_sha256=surface_sha256,
        emitted_dots=n_dots,
        emitted_d_cat_min=round(float(em_dcat.min()), 4),
        emitted_d_cat_median=round(float(np.median(em_dcat)), 4),
        emitted_frac_2_9=round(float(((em_dcat > 2.0) & (em_dcat <= 9.0)).mean()), 5),
        emitted_frac_gt9=round(float((em_dcat > 9.0).mean()), 5),
        emitted_frac_gt20=round(float((em_dcat > 20.0).mean()), 5),
        emitted_lidar_gap_share=lgap_emit_share,
        zeros=dict(validator=val_zeros, independent=ind_zeros),
        nan=dict(validator=val_nan, independent=ind_nan),
        zip=dict(
            path=str(zip_path.relative_to(ROOT)),
            size_bytes=zip_path.stat().st_size,
            sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        ),
        elapsed_s=round(time.time() - t0, 2),
    )
    (ROOT / "evidence" / "h75_cg_candidate_build.json").write_text(json.dumps(build_meta, indent=1) + "\n")
    print(f"Published & verified {stem} in {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
