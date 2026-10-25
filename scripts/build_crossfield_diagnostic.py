#!/usr/bin/env python3
"""Build a CF-1 diagnostic only after its negative holdout screen. Never slot-promote."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, write_submission  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402


def main():
    w = work_dir()
    ctx = load_context(w)
    f = np.load(w / "crossfield.npy", mmap_mode="r")
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    full_e = build_catalogue_features(lab, fi)
    p_sum = np.zeros(fi.size, np.float32)
    h = ctx.holdout
    for m in range(3):
        rng = np.random.default_rng(424200 + m)
        ids = np.arange(1, h.n_comp + 1)
        hid = h._pick(rng, ids, .2 * lab.sum())
        hidden = np.isin(h.comp, hid)
        visible = lab & ~hidden
        e = build_catalogue_features(visible, fi)
        pos = ctx.vec(hidden)
        near = distance_transform_edt(~hidden) <= 1.5
        cand = ctx.vec(foot & ~lab & ~near)
        neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
        idx = np.sort(np.concatenate((pos, neg)))
        y = np.isin(idx, pos).astype(np.int8)
        X = np.column_stack((gather_columns(ctx, e, idx, True)[:, cols], f[idx]))
        model = HistGradientBoostingClassifier(random_state=m, **HGB_PARAMS).fit(X, y)
        del X, e
        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo+500_000, fi.size))
            Xp = np.column_stack((gather_columns(ctx, full_e, sl, True)[:, cols], f[sl]))
            p_sum[sl] += model.predict_proba(np.ascontiguousarray(Xp))[:, 1].astype(np.float32)
        print('trained diagnostic draw', m, flush=True)
    scores = p_sum / 3
    np.save(w / "crossfield_full_scores.npy", scores)
    grid = np.zeros(foot.shape, np.float32)
    grid.ravel()[fi] = scores
    ridges = ridge_nms(grid, foot, 1.0)
    top = select_top_positive(np.where(ridges & ~lab, grid, 0), foot,
                              int(round(.035 * int(foot.sum()))))
    dots = score_ordered_dots(grid, top, 2.4)
    assert not (dots & lab).any()
    pred = dots.astype(np.float32)
    cid = content_id(pred, foot, lab)
    dst = ROOT / 'docs/downloads' / f'gems25-cf1-transverse-negative-20261025-{cid}-zeros.tif'
    if dst.exists():
        raise SystemExit('refusing to overwrite diagnostic')
    write_submission(pred, data_dir() / 'sample_submission.tif', dst, outside='zero')
    receipt = check_file(dst, data_dir() / 'sample_submission.tif')
    (ROOT / 'evidence/crossfield_2026-10-25/validator.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({k: receipt[k] for k in ('file','sha256','positive_pixels','ok_to_upload','hard_failures')},indent=2))


if __name__ == '__main__':
    main()
