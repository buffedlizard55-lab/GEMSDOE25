#!/usr/bin/env python3
"""Frozen CF-1 screen: paired visible-only hide-and-recover, seed 21, four folds."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import t
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from gems25.crossfield import crossfield  # noqa: E402
from gems25.experiment import Cell, HGB_PARAMS, load_context  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402

OUT = ROOT / "evidence" / "crossfield_2026-10-25"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    w = work_dir()
    ctx = load_context(w)
    f = w / "crossfield.npy"
    if f.exists():
        cf = np.load(f, mmap_mode="r")
    else:
        field = crossfield(np.load(w / "bands/02_rtp.npy"),
                           np.load(w / "bands/13_iso_grav_anom.npy"), ctx.foot)
        np.save(f, field.ravel()[ctx.fi])
        cf = np.load(f, mmap_mode="r")
    assert cf.size == ctx.fi.size
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    rows = []
    for fold in range(4):
        cell = Cell(ctx, fold, 21, extras=True)
        canary_raw = cell.auc(np.asarray(cf[cell.q]))
        canary = max(canary_raw, 1 - canary_raw)
        if not np.isfinite(canary) or canary > .90:
            raise RuntimeError(f"leakage canary failed on fold {fold}: {canary}")
        pc, _ = cell.fit_predict(cols, seed=21)
        Xtr = np.column_stack((cell.Xtr[:, cols], cf[cell.train_idx]))
        Xq = np.column_stack((cell.Xq[:, cols], cf[cell.q]))
        model = HistGradientBoostingClassifier(random_state=21, **HGB_PARAMS).fit(Xtr, cell.y)
        pa = model.predict_proba(np.ascontiguousarray(Xq))[:, 1].astype(np.float32)
        for arm, p in (("C", pc), ("A", pa)):
            sc, top = cell.candidates(p, int(round(.035 * cell.dom_c.sum())))
            ev = cell.evaluate(score_ordered_dots(sc, top, 2.4))
            rows.append(dict(fold=fold, draw=21, arm=arm, canary_raw_auc=canary_raw,
                             canary_abs_auc=canary, **ev))
            print(f"fold={fold} arm={arm} DTI={ev['dti']:.6f} positives={ev['n_truth']}", flush=True)
        del cell, Xtr, Xq, model
    diffs = np.array([next(r['dti'] for r in rows if r['fold']==i and r['arm']=='A') -
                      next(r['dti'] for r in rows if r['fold']==i and r['arm']=='C') for i in range(4)])
    mean = float(diffs.mean())
    half = float(t.ppf(.975, 3) * diffs.std(ddof=1) / 2)
    card = dict(evaluator="gems25.metric.dti_binary via Cell.evaluate, alpha=.2 beta=.8 R=3px",
                draw=21, rows=rows, paired_differences=diffs.tolist(), gain=mean,
                gain_ci95=[mean-half, mean+half], positive_folds=int((diffs>0).sum()),
                withheld_positives=sum(r['n_truth'] for r in rows if r['arm']=='A'),
                canary_max=max(r['canary_abs_auc'] for r in rows),
                pass_screen=bool(mean>.001 and (diffs>0).sum()>=3 and diffs.min()>=-.01))
    (OUT / "screen.json").write_text(json.dumps(card, indent=2)+"\n")
    print(json.dumps({k:card[k] for k in ('gain','gain_ci95','positive_folds','pass_screen')},indent=2))


if __name__ == '__main__':
    main()
