#!/usr/bin/env python3
"""Experiment E3: Build and auto-validate the full-footprint 4-fold spatially-blocked OOF H36 GeoTIFF.

Implements `knowledge/21_preregistered_h36_spigm_submodular_2026-10-25.md` §3.3:
  1. 4-fold spatially-blocked out-of-fold (`NW, NE, SW, SE` with 15-px collar) HGB training
     across 3 pseudo-hidden draws (`300, 301, 302`) for both `Head S` (zero-topography crustal)
     and `Head M` (integrated multi-physics).
  2. Pre-placement continuous surface Spearman check across all 47 registry rasters
     (`data/scored`, `data/registry_top`, `docs/downloads`).
  3. Exact Minoux (1978) 300 m tent submodular allocation (`37,654` binary off-catalogue dots)
     with tip-preserved `B=2.0 px` visible-flank shielding, checked against all 47 registry rasters.
  4. Applies the frozen `knowledge/21` §3.3 non-lattice lane rule (`H36_PoE_submod` primary;
     falls back to `H36_S_submod` if `H36_PoE_submod` exceeds 0.70 3-px dot overlap on any
     substantive non-lattice raster).
  5. Writes content-addressed `-zeros.tif` (all-finite `[0, 1]` portal-safe primary) and
     `-nan.tif` (official NaN-outside twin) via `gems25.submission.write_submission` and runs
     automated zero-human-intervention dual validation (`check_file` + strict whole-array `[0, 1]` check).
"""

from __future__ import annotations

import datetime as dt
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h36_spigm import (  # noqa: E402
    H36_NAMES,
    TARGET_FULL_DOTS,
    compute_alpha_sub,
    load_h36_sidecar,
    poe_blend,
    submod300_emit,
)
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission  # noqa: E402
from run_h28_holdout import EXTRAS  # noqa: E402

LATTICE_FILES = {"13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"}
DENSE_MULTILINE_THRESHOLD = 100_000
SAMPLE_RHO = 400_000
RHO_MAX = 0.90
OVERLAP_MAX = 0.70
OOF_SEEDS = (300, 301, 302)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _collect_registry_tifs(ddir: Path, exclude_substr: str | None = None) -> list[tuple[str, Path]]:
    seen_sha: set[str] = set()
    entries: list[tuple[str, Path]] = []
    # Check every file across data/scored, data/registry_top, and docs/downloads
    folders = [
        ("scored", ddir / "scored"),
        ("registry_top", ddir / "registry_top"),
        ("downloads", ROOT / "docs" / "downloads"),
    ]
    for group, folder in folders:
        if not folder.exists():
            continue
        for p in sorted(folder.glob("*.tif")):
            if exclude_substr and exclude_substr in p.name:
                continue
            entries.append((group, p))
            _ = seen_sha
    return entries


def _surface_lane_audit(
    scores_vec: np.ndarray,
    foot: np.ndarray,
    fi: np.ndarray,
    reg_entries: list[tuple[str, Path]],
) -> dict:
    rng = np.random.default_rng(0)
    samp_vec = np.sort(rng.choice(fi.size, min(SAMPLE_RHO, fi.size), replace=False))
    samp_flat = fi[samp_vec]
    svals = np.asarray(scores_vec, dtype=np.float64)[samp_vec]
    rows = []
    for group, p in reg_entries:
        with rasterio.open(p) as ds:
            if ds.shape != foot.shape:
                continue
            rv = np.nan_to_num(ds.read(1), nan=0.0).ravel()[samp_flat]
        rho = float(spearmanr(svals, rv).statistic) if np.unique(rv).size > 1 else 0.0
        rows.append(
            dict(
                group=group,
                file=p.name,
                spearman_surface=round(rho, 6),
                abs_spearman=round(abs(rho), 6),
                flag_rank=bool(abs(rho) > RHO_MAX),
            )
        )
    worst = max((r["abs_spearman"] for r in rows), default=0.0)
    flagged = [r["file"] for r in rows if r["flag_rank"]]
    return dict(
        sample_pixels=int(samp_vec.size),
        rho_max=RHO_MAX,
        registry_checked=len(rows),
        worst_abs_spearman=round(worst, 6),
        flagged=flagged,
        all_clear=len(flagged) == 0,
        rows=rows,
    )


def _dot_lane_audit(
    emitted_2d: np.ndarray,
    foot: np.ndarray,
    fi: np.ndarray,
    reg_entries: list[tuple[str, Path]],
) -> dict:
    cand_dots = np.asarray(emitted_2d, dtype=bool) & foot
    n_cand = int(cand_dots.sum())
    dist_to_cand = distance_transform_edt(~cand_dots)
    rng = np.random.default_rng(0)
    samp_flat = fi[np.sort(rng.choice(fi.size, min(SAMPLE_RHO, fi.size), replace=False))]
    c_samp = cand_dots.ravel()[samp_flat].astype(np.float64)

    rows = []
    for group, p in reg_entries:
        with rasterio.open(p) as ds:
            if ds.shape != foot.shape:
                continue
            arr = np.nan_to_num(ds.read(1), nan=0.0)
        rdots = (arr >= 0.5) & foot
        n_reg = int(rdots.sum())
        if n_reg > 0 and n_cand > 0:
            dist_to_reg = distance_transform_edt(~rdots)
            ov_cand = float((dist_to_reg[cand_dots] <= 3.0).mean())
            ov_reg = float((dist_to_cand[rdots] <= 3.0).mean())
        else:
            ov_cand, ov_reg = 0.0, 0.0
        r_samp = arr.ravel()[samp_flat].astype(np.float64)
        rho = float(spearmanr(c_samp, r_samp).statistic) if np.unique(r_samp).size > 1 else 0.0
        is_lattice = p.name in LATTICE_FILES
        is_dense = n_reg >= DENSE_MULTILINE_THRESHOLD
        rows.append(
            dict(
                group=group,
                file=p.name,
                sha256=_sha256(p),
                registry_dots=n_reg,
                is_synthetic_lattice=is_lattice,
                is_dense_multiline=is_dense,
                spearman_dots=round(rho, 6),
                abs_spearman_dots=round(abs(rho), 6),
                dots_within_3px=round(ov_cand, 6),
                registry_dots_within_3px_of_candidate=round(ov_reg, 6),
                mutual_3px_min=round(min(ov_cand, ov_reg), 6),
                flag_rank=bool(abs(rho) > RHO_MAX),
                flag_overlap=bool(ov_cand > OVERLAP_MAX),
            )
        )

    non_lattice_rows = [r for r in rows if not r["is_synthetic_lattice"]]
    comparable_dotted_rows = [r for r in non_lattice_rows if not r["is_dense_multiline"]]
    flagged_all = [r["file"] for r in rows if r["flag_rank"] or r["flag_overlap"]]
    flagged_non_lattice = [r["file"] for r in non_lattice_rows if r["flag_rank"] or r["flag_overlap"]]
    flagged_comparable = [r["file"] for r in comparable_dotted_rows if r["flag_rank"] or r["flag_overlap"]]

    worst_non_lattice_ov = max((r["dots_within_3px"] for r in non_lattice_rows), default=0.0)
    worst_non_lattice_file = (
        max(non_lattice_rows, key=lambda r: r["dots_within_3px"])["file"] if non_lattice_rows else None
    )
    worst_comparable_ov = max((r["dots_within_3px"] for r in comparable_dotted_rows), default=0.0)
    worst_comparable_file = (
        max(comparable_dotted_rows, key=lambda r: r["dots_within_3px"])["file"] if comparable_dotted_rows else None
    )
    worst_abs_rho = max((r["abs_spearman_dots"] for r in rows), default=0.0)

    return dict(
        candidate_dots=n_cand,
        thresholds=dict(spearman_max=RHO_MAX, dots_within_3px_max=OVERLAP_MAX, dist_px=3.0),
        registry_checked=len(rows),
        literal_strict_all_clear=len(flagged_all) == 0,
        substantive_non_lattice_clear=len(flagged_non_lattice) == 0,
        comparable_dotted_clear=len(flagged_comparable) == 0,
        worst_abs_spearman_dots=round(worst_abs_rho, 6),
        worst_non_lattice_overlap_3px=round(worst_non_lattice_ov, 6),
        worst_non_lattice_file=worst_non_lattice_file,
        worst_comparable_dotted_overlap_3px=round(worst_comparable_ov, 6),
        worst_comparable_dotted_file=worst_comparable_file,
        flagged_literal_all=flagged_all,
        flagged_non_lattice=flagged_non_lattice,
        flagged_comparable_dotted=flagged_comparable,
        rows=rows,
    )


def _strict_whole_array_validator(tif_path: Path, foot: np.ndarray, lab: np.ndarray, expect_all_finite: bool) -> dict:
    """Independent second validator verifying portal [0, 1] range & zero catalogue overlap."""
    with rasterio.open(tif_path) as ds:
        arr = ds.read(1)
        crs_str = str(ds.crs)
        transform_tuple = tuple(ds.transform)[:6]
        dtype_str = str(ds.dtypes[0])
        nodata_val = ds.nodata
        count = ds.count
        shape = ds.shape

    in_f = arr[foot]
    out_f = arr[~foot]
    foot_finite = bool(np.isfinite(in_f).all())
    foot_in_01 = bool(foot_finite and float(in_f.min()) >= 0.0 and float(in_f.max()) <= 1.0)
    whole_finite = bool(np.isfinite(arr).all())
    whole_in_01 = bool(whole_finite and float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0)
    on_cat_pos = int((np.nan_to_num(arr, nan=0.0)[lab] > 0.0).sum())
    outside_ok = whole_in_01 if expect_all_finite else bool(np.isnan(out_f).all())

    passed = bool(
        count == 1
        and dtype_str == "float32"
        and crs_str == "EPSG:32611"
        and shape == (3730, 3292)
        and transform_tuple == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        and foot_in_01
        and on_cat_pos == 0
        and outside_ok
        and (nodata_val is None if expect_all_finite else True)
    )
    return dict(
        independent_validator_pass=passed,
        count=count,
        dtype=dtype_str,
        crs=crs_str,
        shape=list(shape),
        transform=list(transform_tuple),
        nodata=nodata_val,
        footprint_all_finite=foot_finite,
        footprint_in_0_1=foot_in_01,
        whole_array_all_finite=whole_finite,
        whole_array_in_0_1=whole_in_01,
        cannot_trigger_range_0_1_portal_error=whole_in_01,
        on_catalogue_positive_pixels=on_cat_pos,
        footprint_min=float(np.nanmin(in_f)),
        footprint_max=float(np.nanmax(in_f)),
        positive_pixels=int((np.nan_to_num(arr, nan=0.0) >= 0.5).sum()),
    )


def main() -> None:
    t0 = time.time()
    work, ddir = work_dir(), data_dir()
    ev_dir = ROOT / "evidence" / "h36_spigm_build"
    ev_dir.mkdir(parents=True, exist_ok=True)

    ctx = load_context(work)
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    sidecar = load_h36_sidecar(work, ddir / "external", foot)

    alpha_sub_full = compute_alpha_sub(
        np.asarray(ctx.static[ctx.col["det_elev_slope"]], dtype=np.float32),
        np.asarray(ctx.static[ctx.col["L_valid"]], dtype=np.float32),
    )

    # Full visible catalogue features for inference (in live inference, all labels.tif traces are visible)
    E_full = build_catalogue_features(lab, fi)
    tip_full = build_tip_continuation(lab, foot, fi)

    # Column index subsets inside gather_columns(ctx, E, idx, extras=True)
    # Note: gather_columns has 64 static + 7 E + 5 addon = 76 cols; tip + sidecar are appended explicitly
    acde_cols = ctx.columns("ACDE")
    abcde_extra_cols = ctx.columns("ABCDE") + [ctx.col[n] for n in EXTRAS if n in ctx.extra_names]

    p_s_oof = np.zeros(fi.size, dtype=np.float32)
    p_m_oof = np.zeros(fi.size, dtype=np.float32)
    pi_trains: list[float] = []

    H = ctx.holdout
    for fold in (0, 1, 2, 3):
        q_mask = H.quad == fold
        q_idx = ctx.vec(q_mask)
        ps_fold = np.zeros(q_idx.size, dtype=np.float32)
        pm_fold = np.zeros(q_idx.size, dtype=np.float32)

        for seed in OOF_SEEDS:
            d = H.draw(fold, seed)
            E_vis = build_catalogue_features(d.visible, fi)
            tip_vis = build_tip_continuation(d.visible, foot, fi)

            rng = np.random.default_rng(777 + 31 * fold + seed)
            pos = ctx.vec(d.hidden_train)
            near = distance_transform_edt(~d.hidden_train) <= 1.5
            cand = ctx.vec(d.train_region & ~lab & ~near)
            neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
            tr_idx = np.sort(np.concatenate([pos, neg]))
            y_tr = np.isin(tr_idx, pos).astype(np.int8)
            pi_trains.append(float(y_tr.mean()))

            X_base_tr = gather_columns(ctx, E_vis, tr_idx, extras=True)
            tip_tr = tip_vis[tr_idx].astype(np.float32)[:, None]
            h36_tr = np.asarray(sidecar[:, tr_idx], dtype=np.float32).T
            del E_vis, tip_vis

            X_s_tr = np.hstack([X_base_tr[:, acde_cols], tip_tr, h36_tr])
            mod_s = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(X_s_tr, y_tr)
            del X_s_tr

            X_m_tr = np.hstack([X_base_tr[:, abcde_extra_cols], tip_tr, h36_tr])
            del X_base_tr, tip_tr, h36_tr
            mod_m = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS).fit(X_m_tr, y_tr)
            del X_m_tr

            # Predict in chunks on target quadrant q_idx using full-catalogue inference features
            for lo in range(0, q_idx.size, 450_000):
                sl_local = slice(lo, min(lo + 450_000, q_idx.size))
                sub_idx = q_idx[sl_local]
                Xb_q = gather_columns(ctx, E_full, sub_idx, extras=True)
                tq = tip_full[sub_idx].astype(np.float32)[:, None]
                hq = np.asarray(sidecar[:, sub_idx], dtype=np.float32).T

                Xs_q = np.hstack([Xb_q[:, acde_cols], tq, hq])
                ps_fold[sl_local] += mod_s.predict_proba(Xs_q)[:, 1].astype(np.float32)
                del Xs_q

                Xm_q = np.hstack([Xb_q[:, abcde_extra_cols], tq, hq])
                pm_fold[sl_local] += mod_m.predict_proba(Xm_q)[:, 1].astype(np.float32)
                del Xm_q, Xb_q, tq, hq

            del mod_s, mod_m
            gc.collect()
            print(f"[{time.time() - t0:5.0f}s] LOQO fold={fold} seed={seed} done ({tr_idx.size:,} tr rows)", flush=True)

        p_s_oof[q_idx] = ps_fold / len(OOF_SEEDS)
        p_m_oof[q_idx] = pm_fold / len(OOF_SEEDS)

    del E_full
    gc.collect()

    s_poe_oof = poe_blend(p_m_oof, p_s_oof, alpha_sub_full)
    pi_train_mean = float(np.mean(pi_trains))

    np.save(work / "h36_oof_poe_scores.npy", s_poe_oof)
    np.save(work / "h36_oof_sub_scores.npy", p_s_oof)

    reg_entries = _collect_registry_tifs(ddir, exclude_substr="h36-spigm")
    print(f"[{time.time() - t0:5.0f}s] Registry rasters collected: {len(reg_entries)}", flush=True)

    # Pre-placement continuous surface lane audit on s_poe_oof and p_s_oof
    surf_poe = _surface_lane_audit(s_poe_oof, foot, fi, reg_entries)
    surf_sub = _surface_lane_audit(p_s_oof, foot, fi, reg_entries)
    (ev_dir / "lane_surface_poe.json").write_text(json.dumps(surf_poe, indent=1) + "\n")
    (ev_dir / "lane_surface_sub.json").write_text(json.dumps(surf_sub, indent=1) + "\n")
    print(
        f"[{time.time() - t0:5.0f}s] Surface Spearman: PoE worst |rho|={surf_poe['worst_abs_spearman']:.4f} "
        f"| Sub worst |rho|={surf_sub['worst_abs_spearman']:.4f}",
        flush=True,
    )

    # Build 2-D grids for exact 300 m tent submodular allocation
    tip_2d = np.zeros(foot.shape, dtype=np.float32)
    tip_2d.ravel()[fi] = tip_full
    sub_2d = np.zeros(foot.shape, dtype=np.float32)
    sub_2d.ravel()[fi] = p_s_oof
    poe_2d = np.zeros(foot.shape, dtype=np.float32)
    poe_2d.ravel()[fi] = s_poe_oof

    em_poe = submod300_emit(poe_2d, sub_2d, foot, lab, tip_2d, pi_train=pi_train_mean, max_dots=TARGET_FULL_DOTS)
    dot_poe = _dot_lane_audit(em_poe, foot, fi, reg_entries)
    (ev_dir / "lane_dots_poe.json").write_text(json.dumps(dot_poe, indent=1) + "\n")
    print(
        f"[{time.time() - t0:5.0f}s] PoE dots={dot_poe['candidate_dots']} "
        f"worst_non_lattice_3px={dot_poe['worst_non_lattice_overlap_3px']:.4f} ({dot_poe['worst_non_lattice_file']}) "
        f"non_lattice_clear={dot_poe['substantive_non_lattice_clear']}",
        flush=True,
    )

    # Apply frozen knowledge/21 §3.3 non-lattice lane rule
    if surf_poe["all_clear"] and dot_poe["substantive_non_lattice_clear"]:
        chosen_arm = "H36_PoE_submod"
        slug = "h36-spigm-poe-submod300"
        chosen_em = em_poe
        chosen_surf = surf_poe
        chosen_dot = dot_poe
        fallback_reason = None
    else:
        print(
            f"[{time.time() - t0:5.0f}s] PoE flagged on non-lattice registry {dot_poe['flagged_non_lattice']}; "
            f"applying frozen knowledge/21 §3.3 rule -> pure zero-topography crustal Head S (`H36_S_submod`)",
            flush=True,
        )
        em_sub = submod300_emit(sub_2d, None, foot, lab, tip_2d, pi_train=pi_train_mean, max_dots=TARGET_FULL_DOTS)
        dot_sub = _dot_lane_audit(em_sub, foot, fi, reg_entries)
        (ev_dir / "lane_dots_sub.json").write_text(json.dumps(dot_sub, indent=1) + "\n")
        print(
            f"[{time.time() - t0:5.0f}s] Sub dots={dot_sub['candidate_dots']} "
            f"worst_non_lattice_3px={dot_sub['worst_non_lattice_overlap_3px']:.4f} ({dot_sub['worst_non_lattice_file']}) "
            f"non_lattice_clear={dot_sub['substantive_non_lattice_clear']}",
            flush=True,
        )
        chosen_arm = "H36_S_submod"
        slug = "h36-spigm-subsurface-submod300"
        chosen_em = em_sub
        chosen_surf = surf_sub
        chosen_dot = dot_sub
        fallback_reason = (
            f"H36_PoE_submod exceeded 0.70 3-px dot overlap on internal DEM-lineage rasters "
            f"{dot_poe['flagged_non_lattice']} (worst {dot_poe['worst_non_lattice_overlap_3px']:.4f}); "
            f"per frozen knowledge/21 §3.3 rule, emitted pure zero-topography crustal Head S (`H36_S_submod`)."
        )

    assert not (chosen_em & lab).any(), "Emitted pixel landed on a known catalogue pixel!"
    pred = np.where(chosen_em, 1.0, 0.0).astype(np.float32)
    tmpl = ddir / "sample_submission.tif"
    date_str = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    cid = content_id(pred, foot, lab)
    dl_dir = ROOT / "docs" / "downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)

    files_out = {}
    for outside, suffix, expect_fin in (("zero", "zeros", True), ("nan", "nan", False)):
        fname = make_filename(slug, date_str, cid, suffix)
        tif_path = write_submission(pred, tmpl, dl_dir / fname, outside=outside)
        chk1 = check_file(tif_path, tmpl)
        chk2 = _strict_whole_array_validator(tif_path, foot, lab, expect_all_finite=expect_fin)
        assert len(chk1["hard_failures"]) == 0, f"check_file hard failures: {chk1['hard_failures']}"
        assert chk2["independent_validator_pass"], f"independent validator failed: {chk2}"
        files_out[suffix] = dict(
            file=tif_path.name,
            path=f"docs/downloads/{tif_path.name}",
            bytes=tif_path.stat().st_size,
            sha256=chk1["sha256"],
            content_id=cid,
            positive_pixels=chk1["positive_pixels"],
            format_ok=chk1["ok_to_upload"],
            hard_failures=chk1["hard_failures"],
            checks=chk1["checks"],
            independent_validator=chk2,
        )

    # Note <= 120 chars with explicit "no slot" and "unscored" per tests/test_repo_integrity.py
    note = f"GEMSDOE25 {chosen_arm} 37654d | unscored, no slot (holdout/lattice gate) | id {cid}"
    assert len(note) <= 120, f"Note too long ({len(note)} > 120): {note}"

    manifest = dict(
        generated_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        chosen_arm=chosen_arm,
        slug=slug,
        fallback_reason=fallback_reason,
        content_id=cid,
        submission_name=Path(files_out["zeros"]["file"]).stem,
        note=note,
        note_chars=len(note),
        primary_outside="zeros",
        ok_to_download=True,
        ok_to_submit_weekly_slot=False,
        verdict="negative",
        oof_seeds=list(OOF_SEEDS),
        pi_train_mean=round(pi_train_mean, 6),
        h36_columns=list(H36_NAMES),
        files=files_out,
        lane_surface=chosen_surf,
        lane_dots=chosen_dot,
        wall_seconds=round(time.time() - t0, 1),
    )
    (ev_dir / "build_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    (dl_dir / f"checks-{Path(files_out['zeros']['file']).stem}.json").write_text(
        json.dumps(manifest, indent=1) + "\n"
    )
    (dl_dir / f"lane-{Path(files_out['zeros']['file']).stem}.json").write_text(
        json.dumps(chosen_dot, indent=1) + "\n"
    )
    print(json.dumps({
        "chosen_arm": chosen_arm,
        "primary_file": files_out["zeros"]["file"],
        "sha256": files_out["zeros"]["sha256"],
        "content_id": cid,
        "positive_pixels": files_out["zeros"]["positive_pixels"],
        "note": note,
        "note_chars": len(note),
        "substantive_non_lattice_clear": chosen_dot["substantive_non_lattice_clear"],
        "comparable_dotted_clear": chosen_dot["comparable_dotted_clear"],
        "worst_non_lattice_overlap_3px": chosen_dot["worst_non_lattice_overlap_3px"],
        "worst_comparable_dotted_overlap_3px": chosen_dot["worst_comparable_dotted_overlap_3px"],
        "worst_abs_spearman_surface": chosen_surf["worst_abs_spearman"],
    }, indent=1))


if __name__ == "__main__":
    main()
