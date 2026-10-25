#!/usr/bin/env python3
"""Build the unique Session-8 H38 (OSPC + 300 m submodular multi-scale skeleton) GeoTIFFs.

Follows knowledge/25 §4.5 and the shared build_h35_candidate / build_h37_candidate 3-draw
production protocol:
  1. Fit 3 pseudo-hide draws (seeds 424_200..424_202) on [BDE+7, H27_tip, H34(3), H38_OSPC(4)]
     and average full-footprint predicted probabilities.
  2. Screen the continuous pre-placement surface (400k footprint sample, seed 0) via Spearman
     against every unique registry raster in scored/, calibration/, registry_top/, and docs/downloads/.
  3. Match the full-grid dot budget M exactly to S0 (sapd2.4 / kfrac 0.035) on the same surface,
     then allocate M binary off-catalogue dots via exact lazy-greedy 300 m submodular coverage
     `gems25.h38.submodular_skeleton_dots`.
  4. Write zeros-outside (primary) and NaN-outside (template twin) GeoTIFFs, run automated
     16-check format validation (`gems25.submission.check_file`), create the single-GeoTIFF zip,
     and write `docs/downloads/checks-<stem>.json`.
"""

from __future__ import annotations

import argparse
import datetime as dt
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
from check_lane_duplicates import registry_rasters  # noqa: E402
from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h38 import (  # noqa: E402
    DEFAULT_MIN_DIST_FLOOR_PX,
    DEFAULT_POOL_KFRAC,
    H38_NAMES,
    build_h38_ospc_columns,
    submodular_skeleton_dots,
)
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402

KFRAC, MIN_DIST = 0.035, 2.4
SLUG = "h38-ospc-submod"


def surface_lane(p: np.ndarray, fi: np.ndarray, registry_paths: list[Path], shape: tuple[int, int]) -> dict:
    """Spearman rank-correlation of the continuous pre-placement surface vs every registry raster."""
    rng = np.random.default_rng(0)
    samp = np.sort(rng.choice(fi.size, min(400_000, fi.size), replace=False))
    cvals = p[samp]
    samp_flat = fi[samp]
    rows = []
    for path in registry_paths:
        with rasterio.open(path) as r:
            if r.shape != shape:
                rows.append(dict(file=path.name, skipped="shape differs"))
                continue
            rv = np.nan_to_num(r.read(1), nan=0.0).ravel()[samp_flat]
        rho = float(spearmanr(cvals, rv).correlation)
        if not np.isfinite(rho):
            rho = 0.0
        rows.append(
            dict(
                file=path.name,
                surface_spearman=round(rho, 6),
                flag_rank=bool(abs(rho) > 0.90),
            )
        )
    scored = [r for r in rows if "surface_spearman" in r]
    worst = max((abs(r["surface_spearman"]) for r in scored), default=0.0)
    worst_file = max(scored, key=lambda r: abs(r["surface_spearman"]))["file"] if scored else None
    return dict(
        sample_pixels=int(samp.size),
        registry_checked=len(scored),
        worst_abs_spearman=round(float(worst), 6),
        worst_abs_spearman_file=worst_file,
        flagged=[r["file"] for r in scored if r["flag_rank"]],
        rows=rows,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--verdict-note", default="unscored; not slot-approved; no slot")
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    args = ap.parse_args()

    t0 = time.time()
    work = work_dir()
    ctx = load_context(work)
    r_sidecar = load_h34_sidecar(work, ctx.fi)
    h38_sidecar, _ = build_h38_ospc_columns(work, data_dir() / "external")
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    H = ctx.holdout
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi

    E_full = build_catalogue_features(lab, fi)
    tip_full = build_tip_continuation(lab, foot, fi)
    print(f"[{time.time() - t0:.0f}s] fitting {args.draws}-draw H38 OSPC full-footprint ensemble...", flush=True)

    p_sum = np.zeros(fi.size, np.float32)
    pi_true_list: list[float] = []
    r_train_list: list[float] = []
    ids = np.arange(1, H.n_comp + 1)
    n_foot = float(foot.sum())

    for m in range(args.draws):
        rng = np.random.default_rng(424_200 + m)
        hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
        hidden = np.isin(H.comp, hid)
        visible = lab & ~hidden
        pi_true_list.append(float(visible.sum()) / n_foot)

        E = build_catalogue_features(visible, fi)
        tip_vis = build_tip_continuation(visible, foot, fi)
        pos = ctx.vec(hidden)
        near = distance_transform_edt(~hidden) <= 1.5
        cand = ctx.vec(foot & ~lab & ~near)
        neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
        idx = np.sort(np.concatenate([pos, neg]))
        y = np.isin(idx, pos).astype(np.int8)
        r_train_list.append(float(y.mean()))

        X = np.hstack(
            [
                gather_columns(ctx, E, idx, True)[:, cols],
                tip_vis[idx].astype(np.float32)[:, None],
                np.asarray(r_sidecar[:, idx]).T,
                np.asarray(h38_sidecar[:, idx]).T,
            ]
        )
        model = HistGradientBoostingClassifier(random_state=m, **HGB_PARAMS).fit(X, y)
        print(
            f"[{time.time() - t0:.0f}s] draw {m}: fit on {idx.size:,} rows ({int(y.sum()):,} pos), X={X.shape}",
            flush=True,
        )
        del X, E, tip_vis

        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo + 500_000, fi.size))
            Xp = np.hstack(
                [
                    gather_columns(ctx, E_full, sl, True)[:, cols],
                    tip_full[sl].astype(np.float32)[:, None],
                    np.asarray(r_sidecar[:, sl]).T,
                    np.asarray(h38_sidecar[:, sl]).T,
                ]
            )
            p_sum[sl] += model.predict_proba(Xp)[:, 1].astype(np.float32)
            del Xp
        del model

    p = (p_sum / float(args.draws)).astype(np.float32)
    np.save(work / "h38_ospc_full_scores.npy", p)

    # Pre-placement continuous surface lane check across all registry directories
    reg_paths = [rp for rp in registry_rasters() if not rp.name.startswith(f"gems25-{SLUG}-")]
    surf = surface_lane(p, fi, reg_paths, foot.shape)
    build_dir = ROOT / "evidence" / "h38_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    surf_path = build_dir / "surface_lane_h38.json"
    surf_path.write_text(
        json.dumps(dict(arm="G1_S1", checked_before_placement=True, threshold=0.90, **surf), indent=2) + "\n"
    )
    print(
        f"[{time.time() - t0:.0f}s] pre-placement surface lane ({surf['registry_checked']} rasters): "
        f"worst |rho|={surf['worst_abs_spearman']:.4f} ({surf['worst_abs_spearman_file']}) flagged={surf['flagged']}",
        flush=True,
    )

    # Full-grid S0 reference count M_target, then exact S1 submodular multi-scale skeleton emission
    grid = np.zeros(foot.shape, np.float32)
    grid.ravel()[fi] = p
    r_s0 = ridge_nms(grid, foot, 1.0)
    sc_s0 = np.where(r_s0 & ~lab, grid, 0.0)
    top_s0 = select_top_positive(sc_s0, foot, int(round(KFRAC * int(foot.sum()))))
    em_s0 = score_ordered_dots(grid, top_s0, MIN_DIST)
    m_target = int(em_s0.sum())

    pi_true_mean = float(np.mean(pi_true_list))
    r_train_mean = float(np.mean(r_train_list))
    t_sub = time.time()
    em = submodular_skeleton_dots(
        grid,
        foot,
        lab,
        n_dots=m_target,
        pi_true=pi_true_mean,
        r_train=r_train_mean,
        pool_kfrac=DEFAULT_POOL_KFRAC,
        min_dist_floor=DEFAULT_MIN_DIST_FLOOR_PX,
    )
    sub_s = round(time.time() - t_sub, 3)
    assert int(em.sum()) == m_target, (int(em.sum()), m_target)
    assert not (em & lab).any(), "emission placed dot on known catalogue pixel"
    assert not (em & ~foot).any(), "emission placed dot outside footprint"

    # Measure direct overlap between S1 (submodular) and S0 (sapd2.4) on the exact same H38 surface
    dist_to_s0 = distance_transform_edt(~em_s0)
    ov_vs_own_s0 = float((dist_to_s0[em] <= 3.0).mean())
    exact_vs_own_s0 = float((em & em_s0).sum() / max(m_target, 1))
    print(
        f"[{time.time() - t0:.0f}s] S1 submodular emitted {int(em.sum()):,} dots in {sub_s:.2f}s "
        f"(exact pixel overlap vs S0={exact_vs_own_s0:.3f}, 3-px overlap vs S0={ov_vs_own_s0:.3f})",
        flush=True,
    )

    pred = np.where(em, 1.0, 0.0).astype(np.float32)
    tmpl = data_dir() / "sample_submission.tif"
    date = "20261025"
    cid = content_id(pred, foot, lab)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # Remove any prior H38 draft files if re-run idempotently
    for old in out.glob(f"*{SLUG}*"):
        old.unlink()

    recs = {}
    for outside, suffix in (("zero", "zeros"), ("nan", "nan")):
        fname = make_filename(SLUG, date, cid, suffix)
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
        print(
            json.dumps(
                {kk: recs[suffix][kk] for kk in ("file", "bytes", "sha256", "content_id", "positive_pixels", "format_ok")},
                indent=2,
            ),
            flush=True,
        )

    zpath = zip_single(out / recs["zeros"]["file"])
    note = f"GEMSDOE25 H38 ospc-submod | {args.verdict_note} | id {cid}"
    assert len(note) <= 120, len(note)

    rec = dict(
        primary_outside="zeros",
        note=note,
        note_chars=len(note),
        files=recs,
        zip=dict(file=zpath.name, bytes=zpath.stat().st_size),
        surface_lane=dict(
            worst_abs_spearman=surf["worst_abs_spearman"],
            worst_abs_spearman_file=surf["worst_abs_spearman_file"],
            flagged=surf["flagged"],
            path="evidence/h38_build/surface_lane_h38.json",
        ),
        build=dict(
            arm="G1_S1",
            base=BASE,
            extras=EXTRAS,
            tip_column="H27_tip",
            h34_columns=list(H34_NAMES),
            h38_columns=list(H38_NAMES),
            s0_kfrac=KFRAC,
            s0_min_dist=MIN_DIST,
            s1_pool_kfrac=DEFAULT_POOL_KFRAC,
            s1_min_dist_floor=DEFAULT_MIN_DIST_FLOOR_PX,
            pi_true_mean=round(pi_true_mean, 6),
            r_train_mean=round(r_train_mean, 6),
            exact_overlap_vs_s0_on_same_surface=round(exact_vs_own_s0, 6),
            within_3px_overlap_vs_s0_on_same_surface=round(ov_vs_own_s0, 6),
            draws=args.draws,
            submodular_emit_seconds=sub_s,
            seconds=round(time.time() - t0, 1),
            utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            scores="data/work/h38_ospc_full_scores.npy (gitignored cache)",
        ),
        verdict_note=args.verdict_note,
        label="HOLDOUT-DTI only; not a competition score (see registry/run_card_h38_2026-10-25.json)",
    )
    checks_path = out / f"checks-{Path(recs['zeros']['file']).stem}.json"
    checks_path.write_text(json.dumps(rec, indent=2) + "\n")
    print("NOTE:", note, f"({len(note)} chars)")
    print("WROTE:", checks_path)


if __name__ == "__main__":
    main()
