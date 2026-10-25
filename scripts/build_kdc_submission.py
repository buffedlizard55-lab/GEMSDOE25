#!/usr/bin/env python3
"""Build the G25 KDC unique submission: H33-2-B2 dots (same-team base, disclosed) + kernel-disjoint HGB complement.

Inputs
  * ``--scores``: full-footprint HGB score vector saved by ``scripts/build_candidate.py --keep-scores`` (BDE + 7 add-ons,
    3 pseudo-new draws: the H31-C/H28 comparator model trained on the full catalogue).
  * ``data/registry_top/g32_h33-2-b2_0.2778.tif`` (base) and ``g19_h19-5_0.1922.tif`` (incumbent halo), pinned in
    ``registry/top_scorer_sources.json``.

Complement rule (knowledge/17 §3; ``--flank`` adds knowledge/18's 3 < d(H19-5) <= 8 px band):
  footprint, not catalogue, d(catalogue) > 2 px, d(H19-5) > 3 px, HGB ridge-NMS pixels, score-ordered 2.4 px dots, best M.
  M = 17,720 so the 37,654 base dots are 68.0 % of the file (lane cap 70 %).

Outputs (``--out``): ``<name>-zeros.tif`` (primary: all finite, 0 outside the footprint), ``<name>-nan.tif``, a single-file
ZIP of the primary, and ``checks-<name>.json`` with validator output, lane check and SHA-256 receipts. Nothing is uploaded.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, zip_single, write_submission  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots  # noqa: E402

M_COMPLEMENT = 17_720
CAT_PX, HALO_PX, FLANK_PX, MIN_DIST = 2.0, 3.0, 8.0, 2.4
LANE_CORR_CAP, LANE_OVERLAP_CAP, LANE_RADIUS = 0.90, 0.70, 3.0
DEGENERATE = ("13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",)  # 5-px full-footprint lattice (IR-25-LANE-DENSITY)


def read_pos(p: Path) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(p) as s:
        a = s.read(1).astype(np.float32)
    return np.isfinite(a) & (a > 0), np.where(np.isfinite(a) & (a > -1e30), a, 0.0)


def registry_files() -> list[Path]:
    d = data_dir()
    files = sorted((d / "registry_top").glob("*.tif")) + sorted((d / "scored").glob("*.tif"))
    files += sorted((ROOT / "docs" / "downloads").glob("gems25-*.tif"))
    return files


def lane_check(final: np.ndarray, surface: np.ndarray | None, foot: np.ndarray, exclude: set[str]) -> dict:
    fi = np.flatnonzero(foot.ravel())
    sub = np.random.default_rng(7).choice(fi, size=min(1_500_000, fi.size), replace=False)
    fv = final.ravel()[sub].astype(np.float32)
    sv = None if surface is None else surface.ravel()[sub]
    rows = []
    for p in registry_files():
        if p.name in exclude:
            continue
        pos, val = read_pos(p)
        if pos.shape != final.shape or not pos.any():
            continue
        rv = val.ravel()[sub]
        rho_final = float(spearmanr(fv, rv).statistic)
        rho_surface = float(spearmanr(sv, rv).statistic) if sv is not None else None
        near = distance_transform_edt(~pos)[final] <= LANE_RADIUS
        overlap = float(near.mean())
        degenerate = p.name in DEGENERATE
        dup = (not degenerate) and (abs(rho_final) > LANE_CORR_CAP or overlap > LANE_OVERLAP_CAP
                                    or (rho_surface is not None and abs(rho_surface) > LANE_CORR_CAP))
        rows.append(dict(file=p.name, spearman_final=round(rho_final, 4),
                         spearman_surface_preplacement=None if rho_surface is None else round(rho_surface, 4),
                         overlap_within_3px=round(overlap, 4), degenerate_lattice=degenerate, duplicate=bool(dup)))
    subst = [r for r in rows if not r["degenerate_lattice"]]
    return dict(caps=dict(spearman=LANE_CORR_CAP, overlap=LANE_OVERLAP_CAP, radius_px=LANE_RADIUS),
                spearman_sample_pixels=int(sub.size), n_registry=len(rows),
                worst_abs_spearman_final=max(abs(r["spearman_final"]) for r in subst),
                worst_abs_spearman_surface=max(abs(r["spearman_surface_preplacement"] or 0) for r in subst),
                worst_overlap=max(r["overlap_within_3px"] for r in subst),
                worst_overlap_file=max(subst, key=lambda r: r["overlap_within_3px"])["file"],
                lane_clean=not any(r["duplicate"] for r in rows), rows=rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--flank", action="store_true")
    ap.add_argument("--exclude-registry", action="store_true",
                    help="also keep complement dots > 3 px from every other-site registry raster's dots (lane compliance)")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--note", required=True, help="DrivenData note (<= 140 chars); '{cid}' is replaced")
    ap.add_argument("--verdict", required=True, choices=["promote", "negative"])
    ap.add_argument("--evidence", required=True, help="path of the holdout analysis JSON this verdict rests on")
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    a = ap.parse_args()
    foot = np.load(work_dir() / "bands" / "_footprint.npy")
    lab = np.load(work_dir() / "bands" / "_labels.npy")
    p = np.load(a.scores)
    grid = np.zeros(foot.shape, np.float32)
    grid.ravel()[np.flatnonzero(foot.ravel())] = p
    base, _ = read_pos(data_dir() / "registry_top" / "g32_h33-2-b2_0.2778.tif")
    h19, _ = read_pos(data_dir() / "registry_top" / "g19_h19-5_0.1922.tif")
    assert int(base.sum()) == 37_654 and not (base & lab).any() and not (base & ~foot).any()
    d_cat = distance_transform_edt(~lab)
    d_h19 = distance_transform_edt(~h19)
    eligible = foot & ~lab & (d_cat > CAT_PX) & (d_h19 > HALO_PX)
    if a.flank:
        eligible &= d_h19 <= FLANK_PX
    excluded_rasters = []
    if a.exclude_registry:
        union = np.zeros(foot.shape, bool)
        for rp in registry_files():
            if rp.name in DEGENERATE or rp.name.startswith("gems25-"):
                continue
            rpos, _ = read_pos(rp)
            if rpos.shape == foot.shape:
                union |= rpos
                excluded_rasters.append(rp.name)
        eligible &= distance_transform_edt(~union) > HALO_PX
    ridge = ridge_nms(grid, foot, 1.0)
    comp = score_ordered_dots(grid, ridge & eligible & (grid > 0), MIN_DIST, max_keep=M_COMPLEMENT)
    n_comp = int(comp.sum())
    if n_comp != M_COMPLEMENT:
        raise SystemExit(f"only {n_comp} complement dots available (< {M_COMPLEMENT}); lane share would not hold")
    final = base | comp
    assert not (final & lab).any() and not (final & ~foot).any()
    d_base = distance_transform_edt(~base)
    pred = np.where(final, 1.0, 0.0).astype(np.float32)
    cid = content_id(pred, foot, lab)
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"gems25-{a.slug}-{date}-{cid}"
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tmpl = data_dir() / "sample_submission.tif"
    zeros = write_submission(pred, tmpl, out / f"{stem}-zeros.tif", outside="zero")
    nan = write_submission(pred, tmpl, out / f"{stem}-nan.tif", outside="nan")
    zp = zip_single(zeros)
    chk0, chkn = check_file(zeros, tmpl), check_file(nan, tmpl)
    # independent re-read of the written primary file
    with rasterio.open(zeros) as s:
        arr = s.read(1)
        reread = dict(crs=str(s.crs), shape=list(s.shape), transform=list(s.transform)[:6], count=s.count, dtype=s.dtypes[0],
                      nan_anywhere=int(np.isnan(arr).sum()), min=float(arr.min()), max=float(arr.max()),
                      positives=int((arr > 0).sum()), positives_on_catalogue=int(((arr > 0) & lab).sum()),
                      in_footprint_finite=int(np.isfinite(arr[foot]).sum()), footprint_px=int(foot.sum()))
    lane = lane_check(final, grid, foot, exclude={zeros.name, nan.name})
    note = a.note.replace("{cid}", cid)
    if len(note) > 140:
        raise SystemExit(f"note is {len(note)} chars (> 140)")
    rec = dict(
        file=zeros.name, role="primary (zeros outside footprint; no NaN anywhere)", sha256=chk0["sha256"], bytes=zeros.stat().st_size,
        zip=dict(file=zp.name, bytes=zp.stat().st_size), nan_twin=dict(file=nan.name, sha256=chkn["sha256"], ok=chkn["ok_to_upload"]),
        content_id=cid, note=note, note_chars=len(note), verdict=a.verdict, evidence=a.evidence,
        composition=dict(total_dots=int(final.sum()), base_h33_2_b2_dots=int(base.sum()), complement_dots=n_comp,
                         base_share=round(int(base.sum()) / int(final.sum()), 4), flank_band=a.flank,
                         exclude_registry=a.exclude_registry, excluded_registry_rasters=excluded_rasters,
                         complement_min_dist_to_base_px=float(d_base[comp].min()),
                         complement_min_dist_to_h19_5_px=float(d_h19[comp].min()),
                         complement_min_dist_to_catalogue_px=float(d_cat[comp].min()),
                         complement_score_min=float(grid[comp].min()), complement_score_median=float(np.median(grid[comp]))),
        validator=dict(primary=chk0, nan_twin=chkn, independent_reread=reread),
        lane=lane, built_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        scores_vector=dict(path=a.scores, n=int(p.size)),
    )
    (out / f"checks-{stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("file", "sha256", "content_id", "note", "verdict", "composition")}, indent=1))
    print("validator ok:", chk0["ok_to_upload"], chk0["hard_failures"], "| lane clean:", lane["lane_clean"],
          "worst overlap", lane["worst_overlap"], lane["worst_overlap_file"], "worst rho", lane["worst_abs_spearman_final"],
          "surface rho", lane["worst_abs_spearman_surface"])


if __name__ == "__main__":
    main()
