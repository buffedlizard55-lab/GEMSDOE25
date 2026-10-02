#!/usr/bin/env python3
"""Train on the full catalogue (hide-and-recover pseudo-new positives), predict the whole footprint, emit, verify, package.

    python scripts/build_candidate.py --base BE --kfrac 0.0245 --variant dot1.5 --slug factorial-be-dot1-5 --role primary

The model, features and emission are exactly those validated in the hide-and-recover cells (same code path:
``gems25.experiment``). Known catalogue pixels are never emitted (staff: masked, pixel-exact).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features  # noqa: E402
from gems25.families import family_columns  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, make_note, sha256_file, write_submission, zip_single  # noqa: E402
from gems25.thinning import dot_thin, ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="family letters, e.g. BE")
    ap.add_argument("--extras", nargs="*", default=[], help="add-on column names (X1_K ...)")
    ap.add_argument("--kfrac", type=float, default=0.0245)
    ap.add_argument("--variant", default="dot1.5", choices=["solid", "dot1.5", "sapd1.5", "sapd2.4"])
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--tag", required=True, help="short id in the note, e.g. F-BE")
    ap.add_argument("--summary", required=True)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    ap.add_argument("--keep-scores", default=None, help="save the final float score vector (.npy) here")
    a = ap.parse_args()
    t0 = time.time()
    ctx = load_context(work_dir())
    use_extras = bool(a.extras)
    cols = ctx.columns(a.base) + ctx.named(a.extras)
    H = ctx.holdout
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    print(f"[{time.time() - t0:.0f}s] families {a.base} + {a.extras}: {len(cols)} columns", flush=True)
    E_full = build_catalogue_features(lab, fi)
    p_sum = np.zeros(fi.size, np.float32)
    ids = np.arange(1, H.n_comp + 1)
    for m in range(a.draws):
        rng = np.random.default_rng(424_200 + m)
        hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
        hidden = np.isin(H.comp, hid)
        visible = lab & ~hidden
        E = build_catalogue_features(visible, fi)
        pos = ctx.vec(hidden)
        near = distance_transform_edt(~hidden) <= 1.5
        cand = ctx.vec(foot & ~lab & ~near)
        neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
        idx = np.sort(np.concatenate([pos, neg]))
        y = np.isin(idx, pos).astype(np.int8)
        X = gather_columns(ctx, E, idx, use_extras)[:, cols]
        model = HistGradientBoostingClassifier(random_state=m, **HGB_PARAMS).fit(X, y)
        print(f"[{time.time() - t0:.0f}s] draw {m}: fit on {idx.size:,} rows ({int(y.sum()):,} positives)", flush=True)
        del X, E
        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo + 500_000, fi.size))
            p_sum[sl] += model.predict_proba(gather_columns(ctx, E_full, sl, use_extras)[:, cols])[:, 1].astype(np.float32)
    p = p_sum / a.draws
    if a.keep_scores:
        np.save(a.keep_scores, p)
    grid = np.zeros(foot.shape, np.float32)
    grid.ravel()[fi] = p
    print(f"[{time.time() - t0:.0f}s] predicted; NMS + emission ({a.variant}, K={a.kfrac:.4f})", flush=True)
    r = ridge_nms(grid, foot, 1.0)
    sc = np.where(r & ~lab, grid, 0.0)
    k = int(round(a.kfrac * foot.sum()))
    top = select_top_positive(sc, foot, k)
    if a.variant == "solid":
        em = top
    elif a.variant == "dot1.5":
        em = dot_thin(top, 1.5)
    else:
        em = score_ordered_dots(grid, top, 1.5 if a.variant == "sapd1.5" else 2.4)
    assert not (em & lab).any(), "emission on a catalogue pixel"
    pred = np.where(em, 1.0, 0.0).astype(np.float32)
    tmpl = data_dir() / "sample_submission.tif"
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    cid = content_id(pred, foot, lab)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fname = make_filename(a.slug, date, cid, "nan")
    tif = write_submission(pred, tmpl, out / fname, outside="nan")
    zero = write_submission(pred, tmpl, out / fname.replace("-nan.tif", "-zeros.tif"), outside="zero")
    chk = check_file(tif, tmpl)
    chk0 = check_file(zero, tmpl)
    note = make_note(a.tag, a.summary, cid)
    rec = dict(file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size, sha256=chk["sha256"], content_id=cid,
               positive_pixels=int(em.sum()), format_ok=chk["ok_to_upload"], checks=chk["checks"], note=note,
               fallback=dict(file=zero.name, sha256=chk0["sha256"], bytes=zero.stat().st_size, format_ok=chk0["ok_to_upload"], positive_pixels=chk0["positive_pixels"]),
               build=dict(base=a.base, extras=a.extras, kfrac=a.kfrac, variant=a.variant, draws=a.draws, seconds=round(time.time() - t0), utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    (out / f"checks-{tif.stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k_: rec[k_] for k_ in ("file", "bytes", "sha256", "content_id", "positive_pixels", "format_ok", "note")}, indent=1))
    print("hard failures:", chk["hard_failures"], "| fallback ok:", chk0["ok_to_upload"])


if __name__ == "__main__":
    main()
