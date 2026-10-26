#!/usr/bin/env python3
"""Build this session's full-footprint candidate TIFs (knowledge/29 §5, knowledge/30).

Production protocol is ``scripts/build_h38_candidate.py``'s verbatim (3 pseudo-new
draws, averaged B35 surface: BDE+7 + directed tip + 3 H34 columns; greedy
marginal-credit emission on the ridge-NMS top-3.5% pool, Nhat = 0.25 x |catalogue|);
the ONLY change is the per-draw training scheme, selected with ``--scheme``:

  BIN   status-quo classifier sample (used when no experiment passed -> DO NOT SUBMIT file)
  IGN3  ring-excluded negatives (gems25.objective; only if Exp-3 gates passed)

The verdict text is passed in explicitly and is written into the filename note and
checks JSON. Writes zeros-outside (primary) and NaN-outside twins + a single-TIF zip,
each re-checked with ``gems25.submission.check_file``.
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
from gems25.greedy import greedy_dots  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.objective import build_objective_samples  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, select_top_positive  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402

KFRAC = 0.035
SLUGS = {"BIN": "obj-bin-greedy-k3p5", "IGN3": "obj-ign3-greedy-k3p5"}


class _FullDraw:
    """Minimal Draw stand-in for full-footprint production (train_region = whole footprint)."""

    def __init__(self, hidden, footprint):
        self.hidden_train = hidden
        self.train_region = footprint


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scheme", choices=("BIN", "IGN3"), required=True)
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
        seed_base = 424_200 if a.scheme == "IGN3" else 724_200  # BIN uses fresh seeds: 424200 would reproduce the existing H38 file
        rng = np.random.default_rng(seed_base + m)
        hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
        hidden = np.isin(H.comp, hid)
        visible = lab & ~hidden
        E = build_catalogue_features(visible, fi)
        tip_vis = build_tip_continuation(visible, foot, fi)
        if a.scheme == "IGN3":
            samples = build_objective_samples(ctx, _FullDraw(hidden, foot), fold=0, draw_seed=seed_base + m)
            idx, y = samples["ign3"]
            print(f"[{time.time() - t0:.0f}s] draw {m}: IGN3 sample {samples['diag']}", flush=True)
        else:
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
    np.save(work / f"objective_{a.scheme.lower()}_full_scores.npy", p)
    grid = np.zeros(foot.shape, np.float32)
    grid.ravel()[fi] = p
    r = ridge_nms(grid, foot, 1.0)
    sc = np.where(r & ~lab, grid, 0.0)
    top = select_top_positive(sc, foot, int(round(KFRAC * int(foot.sum()))))
    n_hat = 0.25 * float(lab.sum())
    t1 = time.time()
    em, diag = greedy_dots(grid, top, foot, lab, n_hat)
    print(f"[{time.time() - t0:.0f}s] greedy emission in {time.time() - t1:.0f}s: {diag}", flush=True)
    assert not (em & lab).any(), "emission on a catalogue pixel"
    pred = np.where(em, 1.0, 0.0).astype(np.float32)
    tmpl = data_dir() / "sample_submission.tif"
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    cid = content_id(pred, foot, lab)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    recs = {}
    for outside, suffix in (("zero", "zeros"), ("nan", "nan")):
        fname = make_filename(SLUGS[a.scheme], date, cid, suffix)
        tif = write_submission(pred, tmpl, out / fname, outside=outside)
        chk = check_file(tif, tmpl)
        recs[suffix] = dict(file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size,
                            sha256=chk["sha256"], content_id=cid, positive_pixels=chk["positive_pixels"],
                            format_ok=chk["ok_to_upload"], hard_failures=chk["hard_failures"], checks=chk["checks"])
        print(json.dumps({kk: recs[suffix][kk] for kk in ("file", "bytes", "sha256", "content_id",
                                                          "positive_pixels", "format_ok")}, indent=1), flush=True)
    zpath = zip_single(out / recs["zeros"]["file"])
    note = f"GEMSDOE25 {a.scheme} greedy k3.5% | {a.verdict_note} | id {cid}"
    assert len(note) <= 140, len(note)
    rec = dict(primary_outside="zeros", note=note, note_chars=len(note), files=recs,
               zip=dict(file=zpath.name, path=f"docs/downloads/{zpath.name}", bytes=zpath.stat().st_size),
               build=dict(scheme=a.scheme, base=BASE, extras=EXTRAS, tip_column="H27_tip", h34_columns=H34_NAMES,
                          kfrac=KFRAC, emission="greedy_marginal_credit (gems25.greedy)", n_hat=n_hat,
                          greedy_diag=diag, draws=a.draws, draw_seeds=[(424_200 if a.scheme == "IGN3" else 724_200) + m for m in range(a.draws)],
                          seconds=round(time.time() - t0), utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                          scores=f"data/work/objective_{a.scheme.lower()}_full_scores.npy (gitignored cache)",
                          preregistration="knowledge/29 + knowledge/30 (build rule knowledge/29 §5)"),
               verdict_note=a.verdict_note,
               label="HOLDOUT-DTI only; not a competition score (see registry/run_card_objective_2026-10-26.json)")
    (out / f"checks-{Path(recs['zeros']['file']).stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print("NOTE:", note)
    print("hard failures zeros/nan:", recs["zeros"]["hard_failures"], recs["nan"]["hard_failures"])


if __name__ == "__main__":
    main()
