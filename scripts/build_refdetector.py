#!/usr/bin/env python3
"""Out-of-fold reference detector score ``z`` (pre-registration ``knowledge/56`` §2).

Trains a quadrant-blocked model on visible-catalogue pixels versus a uniform background sample and
writes a full-grid float32 score plus fixed 6-level quantile bins computed on the eligible
(off-catalogue) footprint.  Every pixel's score is out-of-sample: the model that scores quadrant k
never saw quadrant k nor a 15 px collar around it, and no catalogue component touching another
quadrant's training region was used.

The machine has ~3 GB of RAM and the standardised stack is ~1.4 GB, so the stack is streamed to a
float32 memmap on disk and never materialised twice.

    python scripts/build_refdetector.py

Writes ``data/work/std_stack.npy``, ``data/work/refdet_z.npy``, ``data/work/refdet_z_bins.npy`` and the
receipt ``evidence/refdetector_build_2026-10-31.json``.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation, label
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.holdout import quadrant_ids  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402

COLLAR_PX = 15
SEED = 20261031
NEG_PER_POS = 4
CHUNK = 200_000


def standardise(work: Path) -> tuple[np.memmap, list[str]]:
    """Stream the 64 static + 5 add-on columns into one z-scored float32 memmap."""
    out_path = work / "std_stack.npy"
    static = np.load(work / "static_ABCD.npy", mmap_mode="r")
    add = np.load(work / "addons.npy", mmap_mode="r")
    names = json.loads((work / "static_ABCD.npy.names.json").read_text())
    names = list(names) + list(json.loads((work / "addons.npy.names.json").read_text()))
    n, m = static.shape[0] + add.shape[0], static.shape[1]
    if out_path.exists() and np.load(out_path, mmap_mode="r").shape == (n, m):
        return np.load(out_path, mmap_mode="r"), names
    mm = np.lib.format.open_memmap(out_path, mode="w+", dtype=np.float32, shape=(n, m))
    for r in range(n):
        src = static if r < static.shape[0] else add
        row = np.asarray(src[r if r < static.shape[0] else r - static.shape[0]], dtype=np.float32)
        good = np.isfinite(row)
        mu = float(row[good].mean()) if good.any() else 0.0
        sd = float(row[good].std()) if good.any() else 1.0
        if not np.isfinite(sd) or sd < 1e-9:
            sd = 1.0
        mm[r] = np.where(good, (row - mu) / sd, 0.0).astype(np.float32)
    mm.flush()
    return np.load(out_path, mmap_mode="r"), names


def predict_chunked(clf, X: np.memmap, cols: np.ndarray) -> np.ndarray:
    out = np.empty(cols.size, dtype=np.float32)
    for i in range(0, cols.size, CHUNK):
        out[i:i + CHUNK] = clf.predict_proba(X[:, cols[i:i + CHUNK]].T)[:, 1]
    return out


def main() -> int:
    t0 = time.time()
    w = work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    X, names = standardise(w)
    H, W = foot.shape
    fidx = np.flatnonzero(foot.ravel())                       # flat index -> column
    flat2col = np.full(H * W, -1, dtype=np.int64)
    flat2col[fidx] = np.arange(fidx.size, dtype=np.int64)

    def cols(mask2d: np.ndarray) -> np.ndarray:
        sel = np.asarray(mask2d, bool).ravel()
        return flat2col[sel]

    quad = quadrant_ids(foot)
    comp, ncomp = label(lab, structure=np.ones((3, 3), int))
    cat_dil1 = binary_dilation(lab, structure=np.ones((3, 3), bool), iterations=1)
    z = np.zeros((H, W), dtype=np.float32)
    diag = []
    for fold in range(4):
        q = quad == fold
        collar = binary_dilation(q, structure=np.ones((3, 3), bool), iterations=COLLAR_PX) & foot
        train_region = foot & ~collar
        keep = np.zeros(ncomp + 1, bool)
        keep[np.unique(comp[train_region & lab])] = True      # components wholly inside the training region
        pos = train_region & lab & keep[comp]
        rng = np.random.default_rng(SEED + fold)
        bg = train_region & ~cat_dil1
        bg_cols = cols(bg)
        n_neg = min(NEG_PER_POS * int(pos.sum()), bg_cols.size)
        neg_cols = rng.choice(bg_cols, size=n_neg, replace=False)
        pos_cols = cols(pos)
        y = np.concatenate([np.ones(pos_cols.size), np.zeros(neg_cols.size)])
        Xi = np.concatenate([X[:, pos_cols].T, X[:, neg_cols].T], axis=0).astype(np.float32)
        clf = HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.1, max_leaf_nodes=31, min_samples_leaf=200,
            l2_regularization=1.0, random_state=7,
        )
        clf.fit(Xi, y)
        zc = cols(q)
        z.ravel()[np.flatnonzero(q.ravel())] = predict_chunked(clf, X, zc)
        diag.append(dict(fold=fold, n_pos_train=int(pos_cols.size), n_neg_train=int(neg_cols.size),
                         train_auc=float(roc_auc_score(y, clf.predict_proba(Xi)[:, 1]))))
        del Xi, clf

    elig = foot & ~lab
    zv = z[elig]
    qs = np.quantile(zv, np.linspace(0, 1, 7)[1:-1])
    bins = np.full((H, W), -1, np.int8)
    bins[elig] = np.searchsorted(qs, zv, side="right").astype(np.int8)
    np.save(w / "refdet_z.npy", z)
    np.save(w / "refdet_z_bins.npy", bins)

    y_true = np.concatenate([np.ones(int(lab.sum())), np.zeros(int((elig).sum()))])
    y_score = np.concatenate([z[lab], z[elig]])
    auc_oof = float(roc_auc_score(y_true, y_score))
    rec = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        script="scripts/build_refdetector.py",
        preregistration="knowledge/56_preregistered_live_anchored_truth_refit_2026-10-31.md",
        n_features=X.shape[0], feature_names=names,
        collar_px=COLLAR_PX, seed=SEED, neg_per_pos=NEG_PER_POS,
        folds=diag,
        oof_auc_visible_catalogue=auc_oof,
        bin_edges=[float(v) for v in qs],
        bin_counts=[int((bins == b).sum()) for b in range(6)],
        z_stats=dict(min=float(zv.min()), p50=float(np.median(zv)), max=float(zv.max())),
        evidence_class="COMPUTED",
        note=("Out-of-fold by quadrant with a 15 px collar; each quadrant is scored by a model trained on the "
              "other three. The AUC against visible catalogue pixels is a diagnostic only and says nothing "
              "about recovery of faults absent from the catalogue."),
        seconds=round(time.time() - t0, 1),
    )
    (ROOT / "evidence" / "refdetector_build_2026-10-31.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if k != "feature_names"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
