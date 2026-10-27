#!/usr/bin/env python3
"""Build & validate the 4-Quadrant LOQO OOF H79_POE_SGMC research GeoTIFF.

Pre-registered in ``knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md`` (commit ``b59b129``):
  - Selected by frozen Exp 3 rule: ``H79_POE_SGMC`` achieved higher pooled 25-km block HOLDOUT-DTI
    (0.085235 vs 0.072458 for H79_POE and 0.060855 for H79_SINGLE_HGB; +0.012777 over H79_POE,
    4/4 folds, 95% CI [+0.001717, +0.024844]).
  - Two-expert domain-decoupled Leave-One-Quadrant-Out (LOQO) OOF surface (seeds 20261027, 20261028):
      M_crustal (56 static cols: ACD + [X1_K, X1_ThK, X1_UK, X3_gm] + H34 + H74_RMPS + H79_CTHM + H79_SGMC)
      M_morpho  (26 static cols: Family B + [S_dem_c2, S_dem_s2])
    Fused per quadrant via ``fuse_poe_scores(p_crustal, p_morpho)``.
  - Emitted on d_cat > 2.0 px (B2 collar hygiene) via shared ``gems25.greedy.greedy_dots``
    (kfrac = 0.035, max_dots = 37,654).
  - Enforces two-stage lane check BEFORE publishing to docs/downloads/:
      Stage 1: continuous OOF surface |Spearman| <= 0.90 across all registry rasters;
      Stage 2: density-aware final-dot check ``flagged_lane == []``, ``external_sparse.lane_pass == True``,
               ``own_lineage.lane_pass == True`` across all 103+ registry rasters.
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
from scipy.ndimage import binary_dilation, binary_erosion, distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from build_h74_candidate import independent_rasterio_audit  # noqa: E402
from gems25.experiment import DOMAIN_ERODE, HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import ADDON_NAMES  # noqa: E402
from gems25.greedy import greedy_dots  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h74_rmps import H74_RMPS_NAMES, load_h74_rmps_sidecar  # noqa: E402
from gems25.h79_cthm import (  # noqa: E402
    H79_ALL_NAMES,
    POE_FLOOR_CRUSTAL,
    POE_FLOOR_MORPHO,
    POE_GAMMA_CRUSTAL,
    build_h79_sidecar,
    fuse_poe_scores,
)
from gems25.holdout import COLLAR_PX, FOLD_NAMES, quadrant_ids  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, select_top_positive  # noqa: E402

DATE_TAG = "20261027"
MAX_DOTS = 37_654
KFRAC = 0.035
CAT_BUF_PX = 2.0
LOQO_SEEDS = (20261027, 20261028)
SUBSURF_EXTRAS = ("X1_K", "X1_ThK", "X1_UK", "X3_gm")
NOTE_POE = "H79 CTHM-PoE+SGMC LOQO B2 37654d [DO NOT SUBMIT: BW25km 0.0852<0.1237; research]"
NOTE_SUBSURF = "H79 CTHM subsurf blind LOQO B2 37654d [DO NOT SUBMIT: BW25km 0.0563<0.1285; research]"
NOTE_CRUSTAL56 = "GEMSDOE25 H79-CTHM | no slot, not slot-approved; DO NOT SUBMIT | id e7ad8a4bf3ed | unscored"
assert len(NOTE_POE) <= 120 and len(NOTE_SUBSURF) <= 120 and len(NOTE_CRUSTAL56) <= 120


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=("poe_sgmc", "subsurf", "crustal_sgmc"), default="crustal_sgmc")
    ap.add_argument("--rebuild-surface", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    work = work_dir()
    data = data_dir()
    tmpl = data / "sample_submission.tif"
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("addons.npy missing")

    h34_mm = load_h34_sidecar(work, ctx.fi)
    h74_mm = load_h74_rmps_sidecar(work, ctx.fi)
    h79_mm, h79_names = build_h79_sidecar(work, data / "external")
    assert h79_names == H79_ALL_NAMES

    base78_names = list(ctx.static_names) + list(ctx.e_names) + list(ctx.extra_names)
    assert len(base78_names) == 78
    bcol = {n: i for i, n in enumerate(base78_names)}

    acd_sub_names = [ctx.all_names[i] for i in ctx.columns("ACD")] + list(SUBSURF_EXTRAS)
    assert len(acd_sub_names) == 44
    acd_sub_idxs = [bcol[n] for n in acd_sub_names]

    b_only_names = [ctx.all_names[i] for i in ctx.columns("B")]
    assert len(b_only_names) == 24
    b_only_idxs = [bcol[n] for n in b_only_names]

    s_dem_names = list(ADDON_NAMES[3:5])
    subsurf55_names = acd_sub_names + list(H34_NAMES) + list(H74_RMPS_NAMES) + list(H79_ALL_NAMES[:4])
    crustal_names = acd_sub_names + list(H34_NAMES) + list(H74_RMPS_NAMES) + list(H79_ALL_NAMES)
    morpho_names = b_only_names + s_dem_names
    assert len(subsurf55_names) == 55
    assert len(crustal_names) == 56
    assert len(morpho_names) == 26
    assert not any(n.startswith(("B_", "L_", "E_")) for n in crustal_names)
    assert not any(n.startswith("E_") for n in morpho_names)

    e_zero = np.zeros((len(ctx.e_names), ctx.fi.size), dtype=np.float32)

    def gather_experts(idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        X78 = np.empty((idx.size, 78), dtype=np.float32)
        gather_columns(ctx, e_zero, idx, True, out=X78)

        Xc = np.empty((idx.size, 56), dtype=np.float32)
        Xc[:, :44] = X78[:, acd_sub_idxs]
        Xc[:, 44:47] = np.asarray(h34_mm[:, idx], dtype=np.float32).T
        Xc[:, 47:51] = np.asarray(h74_mm[:, idx], dtype=np.float32).T
        Xc[:, 51:56] = np.asarray(h79_mm[:, idx], dtype=np.float32).T

        Xm = np.empty((idx.size, 26), dtype=np.float32)
        Xm[:, :24] = X78[:, b_only_idxs]
        Xm[:, 24:26] = np.asarray(ctx.addon[3:5, idx], dtype=np.float32).T
        del X78
        return Xc, Xm

    arm_tag = args.arm
    note_str = {"poe_sgmc": NOTE_POE, "subsurf": NOTE_SUBSURF, "crustal_sgmc": NOTE_CRUSTAL56}[args.arm]
    scores_path = work / f"h79_{arm_tag}_oof_scores.npy"
    quad_meta_path = work / f"h79_{arm_tag}_quad_meta.json"
    if scores_path.exists() and not args.rebuild_surface:
        oof_scores = np.load(scores_path)
        quad_meta = json.loads(quad_meta_path.read_text()) if quad_meta_path.exists() else []
        print(f"Loaded cached H79 ({arm_tag}) LOQO OOF surface {scores_path} (n={oof_scores.size:,})", flush=True)
    else:
        qid = quadrant_ids(ctx.foot)
        near_cat = distance_transform_edt(~ctx.labels) <= 1.5
        oof_scores = np.zeros(ctx.fi.size, dtype=np.float32)
        quad_meta = []

        for q_i, q_name in enumerate(FOLD_NAMES):
            tq = time.time()
            q_foot = qid == q_i
            collar = binary_dilation(q_foot, iterations=COLLAR_PX)
            tr_foot = ctx.foot & ~collar

            pos_tr = ctx.vec(tr_foot & ctx.labels)
            cand_neg = ctx.vec(tr_foot & ~ctx.labels & ~near_cat)
            q_idx = ctx.vec(q_foot)
            Xc_q, Xm_q = gather_experts(q_idx)

            pc_acc = np.zeros(q_idx.size, dtype=np.float64)
            pm_acc = np.zeros(q_idx.size, dtype=np.float64)
            iters_c, iters_m = [], []
            for s_i, seed in enumerate(LOQO_SEEDS):
                rng = np.random.default_rng(seed + 101 * q_i + s_i)
                neg_tr = rng.choice(cand_neg, size=min(N_NEG, cand_neg.size), replace=False)
                tr_idx = np.sort(np.concatenate([pos_tr, neg_tr]))
                y_tr = np.isin(tr_idx, pos_tr).astype(np.int8)
                Xc_tr, Xm_tr = gather_experts(tr_idx)

                c_cols = 56 if args.arm in ("poe_sgmc", "crustal_sgmc") else 55
                clf_c = HistGradientBoostingClassifier(random_state=seed + q_i, **HGB_PARAMS)
                clf_c.fit(Xc_tr[:, :c_cols], y_tr)
                pc_acc += clf_c.predict_proba(Xc_q[:, :c_cols])[:, 1]
                iters_c.append(int(clf_c.n_iter_))
                del Xc_tr, clf_c
                gc.collect()

                if args.arm == "poe_sgmc":
                    clf_m = HistGradientBoostingClassifier(random_state=seed + 1000 + q_i, **HGB_PARAMS)
                    clf_m.fit(Xm_tr, y_tr)
                    pm_acc += clf_m.predict_proba(Xm_q)[:, 1]
                    iters_m.append(int(clf_m.n_iter_))
                    del clf_m
                del Xm_tr
                gc.collect()

            p_c = (pc_acc / len(LOQO_SEEDS)).astype(np.float32)
            if args.arm == "poe_sgmc":
                p_m = (pm_acc / len(LOQO_SEEDS)).astype(np.float32)
                oof_scores[q_idx] = fuse_poe_scores(p_c, p_m)
                del p_m
            else:
                oof_scores[q_idx] = p_c
            quad_meta.append(
                dict(
                    quadrant=q_name,
                    n_train_pos=int(pos_tr.size),
                    n_pred_px=int(q_idx.size),
                    n_iter_crustal=iters_c,
                    n_iter_morpho=iters_m,
                    mean_score=round(float(oof_scores[q_idx].mean()), 6),
                    p99_score=round(float(np.quantile(oof_scores[q_idx], 0.99)), 6),
                    elapsed_s=round(time.time() - tq, 2),
                )
            )
            print(
                f"LOQO {q_name} ({arm_tag}): pos={pos_tr.size:,} pred={q_idx.size:,} "
                f"iters_c={iters_c} iters_m={iters_m} ({time.time()-tq:.1f}s)",
                flush=True,
            )
            del Xc_q, Xm_q, pc_acc, pm_acc, p_c
            gc.collect()

        np.save(scores_path, oof_scores)
        quad_meta_path.write_text(json.dumps(quad_meta, indent=1) + "\n")

    surface_sha256 = hashlib.sha256(oof_scores.tobytes()).hexdigest()

    # Stage 1: pre-placement continuous surface check BEFORE dot placement
    surf_out = ROOT / "evidence" / f"h79_{arm_tag}_surface_lane.json"
    res_surf = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_lane_surface.py"),
            str(scores_path),
            "--out",
            str(surf_out),
        ],
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
    emitted, gdiag = greedy_dots(
        p_grid,
        top,
        dom,
        excl,
        n_hat_full,
        max_dots=MAX_DOTS,
    )
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
    slug = {"poe_sgmc": "poe-sgmc", "subsurf": "subsurf-blind", "crustal_sgmc": "crustal-sgmc"}[args.arm]
    stem = f"gems25-h79-cthm-{slug}-b2-{n_dots}-{DATE_TAG}-{payload_sha12}"

    # Write to STAGING first to verify density-aware lane check before publishing to docs/downloads/
    stage_dir = work / f"staging_h79_{arm_tag}"
    stage_dir.mkdir(parents=True, exist_ok=True)
    stage_zeros = stage_dir / f"{stem}-zeros.tif"
    write_submission(pred, tmpl, stage_zeros, outside="zero")

    stage_lit_out = work / f"staging_h79_{arm_tag}_lane_lit.json"
    stage_ext_out = work / f"staging_h79_{arm_tag}_lane_ext.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_lane_duplicates.py"),
            str(stage_zeros),
            "--out",
            str(stage_lit_out),
        ],
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
        {k: lit_rec[k] for k in ("verdict", "verdict_density_aware", "flagged_literal", "flagged_lane")},
        flush=True,
    )
    print(
        "Staging extended check:",
        {k: ext_rec[k] for k in ("external_sparse", "own_lineage")},
        flush=True,
    )

    if (
        lit_rec["flagged_lane"]
        or not ext_rec["external_sparse"]["lane_pass"]
        or not ext_rec["own_lineage"]["lane_pass"]
    ):
        (ROOT / "evidence" / f"h79_{arm_tag}_stopped_lane.json").write_text(json.dumps(lit_rec, indent=1) + "\n")
        (ROOT / "evidence" / f"h79_{arm_tag}_stopped_extended.json").write_text(json.dumps(ext_rec, indent=1) + "\n")
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
    checks_path = dl_dir / f"checks-{stem}-zeros.json"
    lane_dl_path = dl_dir / f"lane-{stem}-zeros.json"

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
    pub_lit_out = ROOT / "evidence" / f"h79_{arm_tag}_lane_literal.json"
    pub_ext_out = ROOT / "evidence" / f"h79_{arm_tag}_lane_extended.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_lane_duplicates.py"),
            str(zeros_path),
            "--out",
            str(pub_lit_out),
        ],
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
    checks_path.write_text(json.dumps(val_zeros, indent=1) + "\n")
    lane_dl_path.write_text(pub_lit_out.read_text())

    em_dcat = d_cat[emitted]
    used_c_names = crustal_names if args.arm in ("poe_sgmc", "crustal_sgmc") else subsurf55_names
    build_meta = dict(
        arm=args.arm,
        stem=stem,
        note=note_str,
        note_len=len(note_str),
        crustal_feature_count=len(used_c_names),
        crustal_feature_names=used_c_names,
        morpho_feature_count=len(morpho_names) if args.arm == "poe_sgmc" else 0,
        morpho_feature_names=morpho_names if args.arm == "poe_sgmc" else [],
        poe_params=(
            dict(
                gamma_crustal=POE_GAMMA_CRUSTAL,
                floor_crustal=POE_FLOOR_CRUSTAL,
                floor_morpho=POE_FLOOR_MORPHO,
            )
            if args.arm == "poe_sgmc"
            else None
        ),
        loqo_seeds=list(LOQO_SEEDS),
        quadrants=quad_meta,
        oof_surface_sha256=surface_sha256,
        emitted_dots=n_dots,
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
    (ROOT / "evidence" / f"h79_{arm_tag}_candidate_build.json").write_text(json.dumps(build_meta, indent=1) + "\n")
    print(f"Published & verified {stem} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
