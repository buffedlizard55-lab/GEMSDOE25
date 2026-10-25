#!/usr/bin/env python3
"""Build the H35 arm-B (R+T) full-footprint candidate TIFs (knowledge/19).

Only to be run if B passed the frozen screen + confirmation gates. Production protocol is
``scripts/build_candidate.py``'s (3 pseudo-new draws, averaged; sapd2.4 / kfrac 0.035),
with each draw's features = BDE+7 + directed tip (from that draw's *visible* catalogue)
+ 3 H34 columns, in the holdout runner's column order. Prediction uses the full
catalogue's tip field. Writes zeros-outside (primary, strict-validator-proof) and
NaN-outside twins, both re-checked with ``gems25.submission.check_file``.
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
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402

KFRAC, MIN_DIST, SLUG = 0.035, 2.4, "h35-resmag-tip-sapd2-4-k3p5"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--verdict-note", required=True)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    a = ap.parse_args()
    t0 = time.time()
    work = work_dir()
    ctx = load_context(work)
    sidecar = load_h34_sidecar(work, ctx.fi)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    H = ctx.holdout
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    E_full = build_catalogue_features(lab, fi)
    tip_full = build_tip_continuation(lab, foot, fi)
    print(f"[{time.time() - t0:.0f}s] BDE+7 + tip + {H34_NAMES}", flush=True)
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
        X = np.hstack([gather_columns(ctx, E, idx, True)[:, cols],
                       tip_vis[idx].astype(np.float32)[:, None], np.asarray(sidecar[:, idx]).T])
        model = HistGradientBoostingClassifier(random_state=m, **HGB_PARAMS).fit(X, y)
        print(f"[{time.time() - t0:.0f}s] draw {m}: fit on {idx.size:,} rows ({int(y.sum()):,} positives)", flush=True)
        del X, E, tip_vis
        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo + 500_000, fi.size))
            Xp = np.hstack([gather_columns(ctx, E_full, sl, True)[:, cols],
                            tip_full[sl].astype(np.float32)[:, None], np.asarray(sidecar[:, sl]).T])
            p_sum[sl] += model.predict_proba(Xp)[:, 1].astype(np.float32)
            del Xp
        del model
    p = p_sum / a.draws
    np.save(work / "h35_full_scores.npy", p)
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
        fname = make_filename(SLUG, date, cid, suffix)
        tif = write_submission(pred, tmpl, out / fname, outside=outside)
        chk = check_file(tif, tmpl)
        recs[suffix] = dict(file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size,
                            sha256=chk["sha256"], content_id=cid, positive_pixels=chk["positive_pixels"],
                            format_ok=chk["ok_to_upload"], hard_failures=chk["hard_failures"], checks=chk["checks"])
        print(json.dumps({kk: recs[suffix][kk] for kk in ("file", "bytes", "sha256", "content_id",
                                                          "positive_pixels", "format_ok")}, indent=1), flush=True)
    note = f"GEMSDOE25 H35 R+T sapd2.4 k3.5% | {a.verdict_note} | id {cid}"
    assert len(note) <= 140, len(note)
    rec = dict(primary_outside="zeros", note=note, note_chars=len(note), files=recs,
               build=dict(base=BASE, extras=EXTRAS, tip_column="H27_tip", h34_columns=H34_NAMES,
                          kfrac=KFRAC, min_dist=MIN_DIST, draws=a.draws, seconds=round(time.time() - t0),
                          utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                          scores="data/work/h35_full_scores.npy (gitignored cache)"),
               verdict_note=a.verdict_note,
               label="HOLDOUT-DTI only; not a competition score (see registry/run_card_h34_2026-10-25.json)")
    (out / f"checks-{Path(recs['zeros']['file']).stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print("NOTE:", note)
    print("hard failures zeros/nan:", recs["zeros"]["hard_failures"], recs["nan"]["hard_failures"])


if __name__ == "__main__":
    main()
