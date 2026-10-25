#!/usr/bin/env python3
"""Build the session-7 unique full-footprint candidate TIFs (knowledge/22 section 5).

Frozen selection rule (knowledge/23): the session file is the SPR arm (A37S) only
if it passed screen+confirmation gates; otherwise the DOC arm (A37) labelled
negative. The caller passes ``--arm`` accordingly; this script does not decide.

Production protocol is `scripts/build_h35_candidate.py`'s (3 pseudo-new draws,
averaged; sapd2.4 / kfrac 0.035), with each draw's features = BDE+7 + directed
tip (from that draw's visible catalogue) + 3 H34 columns + the arm's extra
columns, in the holdout runners' column order. Prediction uses the full
catalogue's tip field. Before placement, the continuous surface is Spearman
screened against every restored scored raster and every downloads TIF
(400k footprint sample, seed 0 -- PARALLEL-RUN PROTOCOL item 1). Writes
zeros-outside (primary) and NaN-outside twins, both re-checked with
`gems25.submission.check_file`, plus a single-GeoTIFF zip of the primary.
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
from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h37_doc_spr import H37_NAMES, SPR_NAMES, load_h37_sidecar, load_spr_sidecar  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402

KFRAC, MIN_DIST = 0.035, 2.4
ARMS = {
    "doc": dict(slug="h37-doc-dipoffset-sapd2-4-k3p5", names=H37_NAMES, loader=load_h37_sidecar),
    "spr": dict(slug="h37-spr-springline-sapd2-4-k3p5", names=SPR_NAMES, loader=load_spr_sidecar),
}


def surface_lane(p: np.ndarray, fi: np.ndarray, registry_paths: list[Path], shape) -> dict:
    """Spearman of the candidate surface vs each registry raster (seed-0 400k sample)."""
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
        rows.append(dict(file=path.name, surface_spearman=round(rho, 6),
                         flag_rank=bool(abs(rho) > 0.90)))
    scored = [r for r in rows if "surface_spearman" in r]
    worst = max((abs(r["surface_spearman"]) for r in scored), default=None)
    return dict(sample_pixels=int(samp.size), worst_abs_spearman=worst,
                flagged=[r["file"] for r in scored if r["flag_rank"]], rows=rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=list(ARMS), required=True)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--verdict-note", required=True)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    a = ap.parse_args()
    spec = ARMS[a.arm]
    t0 = time.time()
    work = work_dir()
    ctx = load_context(work)
    r_sidecar = load_h34_sidecar(work, ctx.fi)
    extra = spec["loader"](work, ctx.fi)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    H = ctx.holdout
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    E_full = build_catalogue_features(lab, fi)
    tip_full = build_tip_continuation(lab, foot, fi)
    print(f"[{time.time() - t0:.0f}s] BDE+7 + tip + {H34_NAMES} + {spec['names']}", flush=True)
    p_sum = np.zeros(fi.size, np.float32)
    ids = np.arange(1, H.n_comp + 1)
    for m in range(a.draws):
        rng = np.random.default_rng(424_200 + m)
        hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
        hidden = np.isin(H.comp, hid)
        visible = lab & ~hidden
        E = build_catalogue_features(visible, fi)
        tip_vis = build_tip_continuation(visible, foot, fi)
        pos = ctx.vec(hidden)
        near = distance_transform_edt(~hidden) <= 1.5
        cand = ctx.vec(foot & ~lab & ~near)
        neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
        idx = np.sort(np.concatenate([pos, neg]))
        y = np.isin(idx, pos).astype(np.int8)
        # column order matches the holdout runners / build_h35: [BDE+7, tip, H34(3), extras]
        X = np.hstack([gather_columns(ctx, E, idx, True)[:, cols],
                       tip_vis[idx].astype(np.float32)[:, None],
                       np.asarray(r_sidecar[:, idx]).T, np.asarray(extra[:, idx]).T])
        model = HistGradientBoostingClassifier(random_state=m, **HGB_PARAMS).fit(X, y)
        print(f"[{time.time() - t0:.0f}s] draw {m}: fit on {idx.size:,} rows ({int(y.sum()):,} pos) X={X.shape}", flush=True)
        del X, E, tip_vis
        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo + 500_000, fi.size))
            Xp = np.hstack([gather_columns(ctx, E_full, sl, True)[:, cols],
                            tip_full[sl].astype(np.float32)[:, None],
                            np.asarray(r_sidecar[:, sl]).T, np.asarray(extra[:, sl]).T])
            p_sum[sl] += model.predict_proba(Xp)[:, 1].astype(np.float32)
            del Xp
        del model
    p = p_sum / a.draws
    np.save(work / f"h37_{a.arm}_full_scores.npy", p)

    registry = sorted((data_dir() / "scored").glob("*.tif")) + sorted((ROOT / "docs" / "downloads").glob("*.tif"))
    surf = surface_lane(p, fi, registry, foot.shape)
    build_dir = ROOT / "evidence" / "h37_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / f"surface_lane_{a.arm}.json").write_text(json.dumps(
        dict(arm=a.arm, checked_before_placement=True, threshold=0.90, **surf), indent=1) + "\n")
    print(f"surface lane: worst |rho|={surf['worst_abs_spearman']:.4f} flagged={surf['flagged']}", flush=True)

    grid = np.zeros(foot.shape, np.float32)
    grid.ravel()[fi] = p
    r = ridge_nms(grid, foot, 1.0)
    sc = np.where(r & ~lab, grid, 0.0)
    top = select_top_positive(sc, foot, int(round(KFRAC * int(foot.sum()))))
    em = score_ordered_dots(grid, top, MIN_DIST)
    assert not (em & lab).any(), "emission on a catalogue pixel"
    pred = np.where(em, 1.0, 0.0).astype(np.float32)
    tmpl = data_dir() / "sample_submission.tif"
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    cid = content_id(pred, foot, lab)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    recs = {}
    for outside, suffix in (("zero", "zeros"), ("nan", "nan")):
        fname = make_filename(spec["slug"], date, cid, suffix)
        tif = write_submission(pred, tmpl, out / fname, outside=outside)
        chk = check_file(tif, tmpl)
        recs[suffix] = dict(file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size,
                            sha256=chk["sha256"], content_id=cid, positive_pixels=chk["positive_pixels"],
                            format_ok=chk["ok_to_upload"], hard_failures=chk["hard_failures"], checks=chk["checks"])
        print(json.dumps({kk: recs[suffix][kk] for kk in ("file", "bytes", "sha256", "content_id",
                                                          "positive_pixels", "format_ok")}, indent=1), flush=True)
    zpath = zip_single(out / recs["zeros"]["file"])
    note = f"GEMSDOE25 H37 {a.arm.upper()} sapd2.4 k3.5% | {a.verdict_note} | id {cid}"
    assert len(note) <= 140, len(note)
    rec = dict(primary_outside="zeros", note=note, note_chars=len(note), files=recs,
               zip=dict(file=zpath.name, bytes=zpath.stat().st_size),
               surface_lane=dict(worst_abs_spearman=surf["worst_abs_spearman"], flagged=surf["flagged"],
                                 path=f"evidence/h37_build/surface_lane_{a.arm}.json"),
               build=dict(arm=a.arm, base=BASE, extras=EXTRAS, tip_column="H27_tip",
                          h34_columns=H34_NAMES, extra_columns=spec["names"],
                          kfrac=KFRAC, min_dist=MIN_DIST, draws=a.draws,
                          seconds=round(time.time() - t0),
                          utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                          scores=f"data/work/h37_{a.arm}_full_scores.npy (gitignored cache)"),
               verdict_note=a.verdict_note,
               label="HOLDOUT-DTI only; not a competition score (see registry/run_card_h37_2026-10-25.json)")
    (out / f"checks-{Path(recs['zeros']['file']).stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print("NOTE:", note)
    print("hard failures zeros/nan:", recs["zeros"]["hard_failures"], recs["nan"]["hard_failures"])


if __name__ == "__main__":
    main()
