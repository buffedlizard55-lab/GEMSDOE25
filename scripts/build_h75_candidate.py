#!/usr/bin/env python3
"""Build the full-footprint 4-quadrant LOQO H75-EU3D-POE unique GeoTIFF candidate.

Pre-registered in ``knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md`` (commit ``3053f69``):
  - Fits two independent 4-quadrant Leave-One-Quadrant-Out (LOQO, 1.5-km collar, seeds 20261201, 20261202)
    out-of-fold HGB experts on full INGENIOUS catalogue in the 3 non-target quadrants:
      * ``P_scarp`` (28 static Family B + S_dem + RBDT columns; zero A/C/D/E)
      * ``P_root``  (55 static ACD + SUBSURF_EXTRAS + H34 + H74_RMPS + H75_EU3D columns; zero B/E)
  - Evaluates the frozen candidate cascade ``H75_POE50 -> H75_POE65 -> ROOT_H75`` in staging:
      1) Pre-placement continuous surface check via ``scripts/check_lane_surface.py`` (|Spearman| <= 0.90)
      2) B2 hygiene (``d_cat > 2.0 px``) + shared ``greedy_dots(kfrac=0.035, max_dots=37,654)``
      3) Staging final-dot duplicate audit via ``scripts/check_lane_duplicates.py`` &
         ``scripts/lane_check_extended.py`` BEFORE writing to ``docs/downloads/``.
      4) Selects the FIRST cascade arm clearing ``flagged_lane == []``, ``external_sparse.lane_pass == True``,
         and ``own_lineage.lane_pass == True``. Any halted arm is logged in ``evidence/`` and never published.
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
from gems25.h72_pttg import H72_VCCD_NAMES, load_h72_vccd_sidecar  # noqa: E402
from gems25.h74_rmps import H74_RMPS_NAMES, load_h74_rmps_sidecar  # noqa: E402
from gems25.h75_eu3d import H75_EU3D_NAMES, load_h75_eu3d_sidecar, poe_combine  # noqa: E402
from gems25.holdout import COLLAR_PX, FOLD_NAMES, quadrant_ids  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, select_top_positive  # noqa: E402

DATE_TAG = "20261027"
MAX_DOTS = 37_654
KFRAC = 0.035
CAT_BUF_PX = 2.0
LOQO_SEEDS = (20261201, 20261202)
SUBSURF_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm")
SCARP_VCCD_COLS = ("RBDT_throw_dipole", "RBDT_non_shoreline_scarp")


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
    ap.add_argument("--rebuild-surfaces", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    work = work_dir()
    data = data_dir()
    tmpl = data / "sample_submission.tif"
    ctx = load_context(work)
    h34_mm = load_h34_sidecar(work, ctx.fi)
    vccd_mm = load_h72_vccd_sidecar(work, data / "external", ctx.fi)
    h74_mm = load_h74_rmps_sidecar(work, ctx.fi)
    h75_mm = load_h75_eu3d_sidecar(work, ctx.fi)

    base78_names = list(ctx.static_names) + list(ctx.e_names) + list(ctx.extra_names)
    assert len(base78_names) == 78
    bcol = {n: i for i, n in enumerate(base78_names)}

    b_only_names = [ctx.all_names[i] for i in ctx.columns("B")]
    b_only_idxs = [bcol[n] for n in b_only_names]
    rbdt_vccd_idxs = [H72_VCCD_NAMES.index(n) for n in SCARP_VCCD_COLS]
    scarp_feat_names = b_only_names + ["S_dem_c2", "S_dem_s2"] + list(SCARP_VCCD_COLS)
    assert len(scarp_feat_names) == 28
    assert not any(n.startswith(("A_", "C_", "D_", "E_")) for n in scarp_feat_names)

    acd_sub_names = [ctx.all_names[i] for i in ctx.columns("ACD")] + list(SUBSURF_EXTRAS)
    acd_sub_idxs = [bcol[n] for n in acd_sub_names]
    root_feat_names = acd_sub_names + list(H34_NAMES) + list(H74_RMPS_NAMES) + list(H75_EU3D_NAMES)
    assert len(root_feat_names) == 55
    assert not any(n.startswith(("B_", "L_", "E_")) for n in root_feat_names)

    e_zero = np.zeros((len(ctx.e_names), ctx.fi.size), dtype=np.float32)

    def gather_scarp(idx: np.ndarray) -> np.ndarray:
        X78 = np.empty((idx.size, 78), dtype=np.float32)
        gather_columns(ctx, e_zero, idx, True, out=X78)
        X = np.empty((idx.size, 28), dtype=np.float32)
        X[:, :24] = X78[:, b_only_idxs]
        del X78
        X[:, 24:26] = np.asarray(ctx.addon[3:5, idx], dtype=np.float32).T
        X[:, 26:28] = np.asarray(vccd_mm[rbdt_vccd_idxs][:, idx], dtype=np.float32).T
        return X

    def gather_root(idx: np.ndarray) -> np.ndarray:
        X78 = np.empty((idx.size, 78), dtype=np.float32)
        gather_columns(ctx, e_zero, idx, True, out=X78)
        X = np.empty((idx.size, 55), dtype=np.float32)
        X[:, :44] = X78[:, acd_sub_idxs]
        del X78
        X[:, 44:47] = np.asarray(h34_mm[:, idx], dtype=np.float32).T
        X[:, 47:51] = np.asarray(h74_mm[:, idx], dtype=np.float32).T
        X[:, 51:55] = np.asarray(h75_mm[:, idx], dtype=np.float32).T
        return X

    scarp_path = work / "h75_loqo_scarp_scores.npy"
    root_path = work / "h75_loqo_root_scores.npy"
    quad_meta_path = work / "h75_loqo_quad_meta.json"

    if scarp_path.exists() and root_path.exists() and not args.rebuild_surfaces:
        oof_scarp = np.load(scarp_path)
        oof_root = np.load(root_path)
        quad_meta = json.loads(quad_meta_path.read_text()) if quad_meta_path.exists() else []
        print(f"Loaded cached LOQO surfaces ({oof_scarp.size:,} px)", flush=True)
    else:
        qid = quadrant_ids(ctx.foot)
        near_cat = distance_transform_edt(~ctx.labels) <= 1.5
        oof_scarp = np.zeros(ctx.fi.size, dtype=np.float32)
        oof_root = np.zeros(ctx.fi.size, dtype=np.float32)
        quad_meta = []

        for q_i, q_name in enumerate(FOLD_NAMES):
            tq = time.time()
            q_foot = qid == q_i
            collar = binary_dilation(q_foot, iterations=COLLAR_PX)
            tr_foot = ctx.foot & ~collar

            pos_tr = ctx.vec(tr_foot & ctx.labels)
            cand_neg = ctx.vec(tr_foot & ~ctx.labels & ~near_cat)
            q_idx = ctx.vec(q_foot)

            Xq_s = gather_scarp(q_idx)
            Xq_r = gather_root(q_idx)
            acc_s = np.zeros(q_idx.size, dtype=np.float64)
            acc_r = np.zeros(q_idx.size, dtype=np.float64)
            iters_s, iters_r = [], []

            for s_i, seed in enumerate(LOQO_SEEDS):
                rng = np.random.default_rng(seed + 101 * q_i + s_i)
                neg_tr = rng.choice(cand_neg, size=min(N_NEG, cand_neg.size), replace=False)
                tr_idx = np.sort(np.concatenate([pos_tr, neg_tr]))
                y_tr = np.isin(tr_idx, pos_tr).astype(np.int8)

                Xtr_s = gather_scarp(tr_idx)
                clf_s = HistGradientBoostingClassifier(random_state=seed + q_i, **HGB_PARAMS).fit(Xtr_s, y_tr)
                acc_s += clf_s.predict_proba(Xq_s)[:, 1]
                iters_s.append(int(clf_s.n_iter_))
                del Xtr_s, clf_s

                Xtr_r = gather_root(tr_idx)
                clf_r = HistGradientBoostingClassifier(random_state=seed + q_i + 50, **HGB_PARAMS).fit(Xtr_r, y_tr)
                acc_r += clf_r.predict_proba(Xq_r)[:, 1]
                iters_r.append(int(clf_r.n_iter_))
                del Xtr_r, clf_r
                gc.collect()

            oof_scarp[q_idx] = (acc_s / len(LOQO_SEEDS)).astype(np.float32)
            oof_root[q_idx] = (acc_r / len(LOQO_SEEDS)).astype(np.float32)
            quad_meta.append(
                dict(
                    quadrant=q_name,
                    n_train_pos=int(pos_tr.size),
                    n_pred_px=int(q_idx.size),
                    scarp_iters=iters_s,
                    root_iters=iters_r,
                    scarp_mean_prob=round(float(oof_scarp[q_idx].mean()), 6),
                    root_mean_prob=round(float(oof_root[q_idx].mean()), 6),
                    elapsed_s=round(time.time() - tq, 2),
                )
            )
            print(f"LOQO {q_name}: pos={pos_tr.size:,} pred={q_idx.size:,} ({time.time() - tq:.1f}s)", flush=True)
            del Xq_s, Xq_r, acc_s, acc_r
            gc.collect()

        np.save(scarp_path, oof_scarp)
        np.save(root_path, oof_root)
        quad_meta_path.write_text(json.dumps(quad_meta, indent=1) + "\n")

    dom = binary_erosion(ctx.foot, iterations=DOMAIN_ERODE)
    d_cat = distance_transform_edt(~ctx.labels).astype(np.float32)
    excl = ctx.labels | (d_cat <= CAT_BUF_PX)
    pool_k = int(round(KFRAC * float(dom.sum())))
    n_hat_full = max(0.25 * float((ctx.labels & dom).sum()), 100.0)

    # Pre-registered candidate cascade: H75_POE50 -> H75_POE65 -> ROOT_H75
    cascade = [
        ("poe50", "gems25-h75-eu3d-poe50-catfree-b2", poe_combine(oof_scarp, oof_root, gamma=0.50), 0.50),
        ("poe65", "gems25-h75-eu3d-poe65-catfree-b2", poe_combine(oof_scarp, oof_root, gamma=0.65), 0.65),
        ("root", "gems25-h75-eu3d-root-catfree-b2", oof_root.copy(), 1.00),
    ]

    halted_cascade = []
    selected = None

    for arm_tag, slug_prefix, oof_scores, gamma_val in cascade:
        scores_file = work / f"h75_{arm_tag}_oof_scores.npy"
        np.save(scores_file, oof_scores)
        surf_sha = hashlib.sha256(oof_scores.tobytes()).hexdigest()

        # Stage 1: pre-placement continuous surface check BEFORE dot placement
        surf_json = ROOT / "evidence" / f"h75_{arm_tag}_surface_lane.json"
        res_surf = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_lane_surface.py"), str(scores_file), "--out", str(surf_json)],
            capture_output=True,
            text=True,
        )
        surf_rec = json.loads(surf_json.read_text())
        print(f"[{arm_tag}] Surface lane: worst_abs_spearman={surf_rec['worst_abs_spearman']:.5f}, flagged={surf_rec['flagged']}", flush=True)
        if res_surf.returncode != 0 or surf_rec["flagged"]:
            halted_cascade.append(dict(arm=arm_tag, stage="surface", flagged=surf_rec["flagged"], receipt=str(surf_json.relative_to(ROOT))))
            continue

        # Stage 2: B2-hygiene greedy_dots in STAGING directory
        t_em = time.time()
        p_grid = np.zeros(ctx.foot.shape, dtype=np.float32)
        p_grid.ravel()[ctx.fi] = np.nan_to_num(oof_scores, nan=0.0).astype(np.float32)
        ridge = ridge_nms(p_grid, dom, 1.0)
        s_clean = np.where(ridge & ~excl, p_grid, 0.0)
        top = select_top_positive(s_clean, dom, pool_k)
        emitted, gdiag = greedy_dots(p_grid, top, dom, excl, n_hat_full, max_dots=MAX_DOTS)
        emitted &= dom & ~excl
        n_dots = int(emitted.sum())
        assert 0 < n_dots <= MAX_DOTS
        payload_sha12 = hashlib.sha256(np.packbits(emitted.ravel()).tobytes()).hexdigest()[:12]
        stem = f"{slug_prefix}-{n_dots}-{DATE_TAG}-{payload_sha12}"
        print(f"[{arm_tag}] Staging {n_dots:,} dots (stop={gdiag['stop_reason']}, {time.time()-t_em:.1f}s) -> {stem}", flush=True)

        stage_dir = work / f"staging_h75_{arm_tag}"
        stage_dir.mkdir(parents=True, exist_ok=True)
        stage_zeros = stage_dir / f"{stem}-zeros.tif"
        write_submission(emitted.astype(np.float32), tmpl, stage_zeros, outside="zero")

        stage_lit = work / f"staging_h75_{arm_tag}_lane_lit.json"
        stage_ext = work / f"staging_h75_{arm_tag}_lane_ext.json"
        stage_sha = hashlib.sha256(stage_zeros.read_bytes()).hexdigest()
        if not (
            stage_lit.exists()
            and stage_ext.exists()
            and json.loads(stage_lit.read_text()).get("sha256") == stage_sha
        ):
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "check_lane_duplicates.py"), str(stage_zeros), "--out", str(stage_lit)],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "lane_check_extended.py"),
                    str(stage_zeros),
                    "--scores",
                    str(scores_file),
                    "--out",
                    str(stage_ext),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        lit_rec = json.loads(stage_lit.read_text())
        ext_rec = json.loads(stage_ext.read_text())
        print(
            f"[{arm_tag}] Staging final-dot audit: flagged_lane={lit_rec['flagged_lane']} "
            f"ext_sparse={ext_rec['external_sparse']['worst_cand_dots_within_3px']:.4f}({ext_rec['external_sparse']['worst_overlap_file']}) "
            f"own={ext_rec['own_lineage']['worst_cand_dots_within_3px']:.4f}({ext_rec['own_lineage']['worst_overlap_file']})",
            flush=True,
        )

        if (
            lit_rec["flagged_lane"]
            or not ext_rec["external_sparse"]["lane_pass"]
            or not ext_rec["own_lineage"]["lane_pass"]
        ):
            stop_lit_p = ROOT / "evidence" / f"h75_{arm_tag}_stopped_lane.json"
            stop_ext_p = ROOT / "evidence" / f"h75_{arm_tag}_stopped_extended.json"
            stop_lit_p.write_text(json.dumps(lit_rec, indent=1) + "\n")
            stop_ext_p.write_text(json.dumps(ext_rec, indent=1) + "\n")
            halted_cascade.append(
                dict(
                    arm=arm_tag,
                    stage="final_dots",
                    gamma=gamma_val,
                    flagged_lane=lit_rec["flagged_lane"],
                    worst_external_sparse=ext_rec["external_sparse"],
                    worst_own_lineage=ext_rec["own_lineage"],
                    stopped_before_publish=True,
                    receipt=str(stop_lit_p.relative_to(ROOT)),
                    extended_receipt=str(stop_ext_p.relative_to(ROOT)),
                )
            )
            continue

        selected = (arm_tag, gamma_val, stem, payload_sha12, scores_file, surf_sha, surf_json, emitted, gdiag)
        break

    if selected is None:
        raise RuntimeError(f"All pre-registered H75 cascade arms halted in staging: {halted_cascade}")

    arm_tag, gamma_val, stem, payload_sha12, scores_file, surf_sha, surf_json, emitted, gdiag = selected
    n_dots = int(emitted.sum())
    pred = emitted.astype(np.float32)
    note = f"GEMSDOE25 H75-{arm_tag.upper()} | no slot, not slot-approved; DO NOT SUBMIT | id {payload_sha12} | unscored"
    assert len(note) <= 120

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

    pub_lit_out = ROOT / "evidence" / "h75_published_lane_literal.json"
    pub_ext_out = ROOT / "evidence" / "h75_published_lane_extended.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_lane_duplicates.py"), str(zeros_path), "--out", str(pub_lit_out)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "lane_check_extended.py"),
            str(zeros_path),
            "--scores",
            str(scores_file),
            "--out",
            str(pub_ext_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    em_dcat = d_cat[emitted]
    build_meta = dict(
        selected_arm=arm_tag,
        gamma=gamma_val,
        stem=stem,
        content_id=payload_sha12,
        note=note,
        note_len=len(note),
        scarp_feature_count=len(scarp_feat_names),
        scarp_feature_names=scarp_feat_names,
        root_feature_count=len(root_feat_names),
        root_feature_names=root_feat_names,
        loqo_seeds=list(LOQO_SEEDS),
        quadrants=quad_meta,
        oof_surface_sha256=surf_sha,
        surface_lane_receipt=str(surf_json.relative_to(ROOT)),
        halted_cascade=halted_cascade,
        emitted_dots=n_dots,
        greedy_diag={k: (round(float(v), 6) if isinstance(v, float) else v) for k, v in gdiag.items()},
        emitted_d_cat_min=round(float(em_dcat.min()), 4),
        emitted_d_cat_median=round(float(np.median(em_dcat)), 4),
        emitted_frac_2_9=round(float(((em_dcat > 2.0) & (em_dcat <= 9.0)).mean()), 5),
        emitted_frac_gt9=round(float((em_dcat > 9.0).mean()), 5),
        emitted_frac_gt20=round(float((em_dcat > 20.0).mean()), 5),
        zeros=dict(validator=val_zeros, independent=ind_zeros),
        nan=dict(validator=val_nan, independent=ind_nan),
        zip=dict(
            path=str(zip_path.relative_to(ROOT)),
            size_bytes=zip_path.stat().st_size,
            sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        ),
        elapsed_s=round(time.time() - t0, 2),
    )
    (ROOT / "evidence" / "h75_candidate_build.json").write_text(json.dumps(build_meta, indent=1) + "\n")
    print(f"Published & verified {stem} (selected={arm_tag}, gamma={gamma_val}) in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
