#!/usr/bin/env python3
"""G25-K1 Kernel-Disjoint Complement (KDC) — hide-and-recover screen / confirmation.

Pre-registered in ``knowledge/17_preregistered_kdc_kernel_disjoint_complement_2026-10-25.md`` (committed before any fit).
One HGB fit per (fold, draw) cell (BDE + 7 add-ons, seed = draw), exactly the H28/H31 comparator model. Arms:

* C       comparator: top-K ridge candidates (kfrac 0.035), score-ordered dots 2.4 px (must reproduce H28 cells).
* CB      C minus dots <= 2 px from the visible catalogue.
* K_self  CB + M HGB ridge dots outside X (primary);  M = round(0.4706 * |CB|).
* K_gem1  CB + M GEM-1 (|grad RTP| x low relief) ridge dots outside X (secondary).
* K_rand  CB + M dots on a seeded random score outside X (negative control).
X = within 3 px of C's raw top-K candidates  U  within 2 px of the visible catalogue  U  outside the eroded domain.

    python scripts/run_kdc_holdout.py --draws 0 1 --out evidence/kdc_screen
    python scripts/run_kdc_holdout.py --draws 2 3 --out evidence/kdc_confirm      # only after a screen pass
    python scripts/analyze_kdc_holdout.py evidence/kdc_screen
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS, FOLDS  # noqa: E402
from validate_gem_candidate import surface_gem1  # noqa: E402

KFRAC = 0.035
MIN_DIST = 2.4
CAT_PRUNE_PX = 2.0
HALO_PX = 3.0
BASE_SHARE = 0.68
M_FACTOR = round((1 - BASE_SHARE) / BASE_SHARE, 4)  # 0.4706
H28_CELLS = ROOT / "evidence" / "h28_holdout" / "cells.jsonl"


def h28_reference() -> dict:
    ref = {}
    for line in H28_CELLS.read_text().splitlines():
        row = json.loads(line)
        if row["value"] == "score" and row["min_dist"] == MIN_DIST and row["kfrac"] == KFRAC:
            ref[(row["fold"], row["draw"])] = row["dti"]
    return ref


def complement(score_c: np.ndarray, eligible: np.ndarray, dom_c: np.ndarray, m: int, ridge: bool = True) -> np.ndarray:
    """Score-ordered 2.4 px dots among (ridge-NMS) pixels of ``score_c`` inside ``eligible``; best ``m`` kept."""
    s = np.where(dom_c, np.nan_to_num(score_c, nan=0.0), 0.0).astype(np.float32)
    cand = (ridge_nms(s, dom_c, 1.0) if ridge else dom_c) & eligible & (s > 0)
    return score_ordered_dots(s, cand, MIN_DIST, max_keep=m)


def single_feature_auc(cell: Cell, cols: list[int], names: list[str]) -> dict:
    from sklearn.metrics import roc_auc_score
    if cell.auc_pos.size == 0:
        return {}
    idx = np.concatenate([cell.auc_pos, cell.auc_neg])
    y = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
    out = {}
    for c, n in zip(cols, names):
        v = np.nan_to_num(cell.Xq[idx, c], nan=np.nanmedian(cell.Xq[idx, c]))
        a = float(roc_auc_score(y, v)) if np.ptp(v) > 0 else 0.5
        out[n] = round(max(a, 1 - a), 4)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cells_path, design_path = out / "cells.jsonl", out / "design.json"
    if cells_path.exists() or design_path.exists():
        raise SystemExit(f"refusing to overwrite {out}; choose a fresh --out")
    design = dict(
        hypothesis="G25-K1 kernel-disjoint complement (KDC)",
        preregistration="knowledge/17_preregistered_kdc_kernel_disjoint_complement_2026-10-25.md",
        draws=a.draws, folds=[0, 1, 2, 3], kfrac=KFRAC, min_dist=MIN_DIST, cat_prune_px=CAT_PRUNE_PX, halo_px=HALO_PX,
        base_share=BASE_SHARE, m_factor=M_FACTOR, model={"base": BASE, "extras": EXTRAS, "fit_seed": "draw"},
        evaluator="gems25.metric.dti_binary (alpha 0.2, beta 0.8, R = 3 px)",
    )
    design_path.write_text(json.dumps(design, indent=1) + "\n")  # frozen before any fit

    ref = h28_reference()
    ctx = load_context(work_dir())
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("add-on cache missing; run scripts/build_addons.py first")
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    col_names = [ctx.all_names[c] for c in cols]
    gem1_full = surface_gem1(ctx.foot, work_dir() / "bands")
    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in (0, 1, 2, 3):
            for draw in a.draws:
                cell = Cell(ctx, fold, draw, extras=True)
                p, timing = cell.fit_predict(cols, seed=draw)
                k = int(round(KFRAC * cell.dom_c.sum()))
                s_crop, top = cell.candidates(p, k)
                em_c = score_ordered_dots(s_crop, top, MIN_DIST)
                d_vis = distance_transform_edt(~cell.known_c)
                em_cb = em_c & (d_vis > CAT_PRUNE_PX)
                x_zone = (distance_transform_edt(~top) <= HALO_PX) | (d_vis <= CAT_PRUNE_PX) | ~cell.dom_c
                eligible = ~x_zone
                m = int(round(M_FACTOR * em_cb.sum()))
                rng = np.random.default_rng(90_000 + 100 * fold + draw)
                comps = {
                    "K_self": complement(s_crop, eligible, cell.dom_c, m),
                    "K_gem1": complement(gem1_full[cell.sl], eligible, cell.dom_c, m),
                    "K_rand": complement(rng.random(s_crop.shape).astype(np.float32), eligible, cell.dom_c, m, ridge=False),
                }
                arms = {"C": em_c, "CB": em_cb}
                for name, kmask in comps.items():
                    assert not (kmask & x_zone).any()
                    arms[name] = em_cb | kmask
                auc_feat = single_feature_auc(cell, cols, col_names)
                gem_q = gem1_full.ravel()[ctx.fi[cell.q]]
                for name, em in arms.items():
                    ev = cell.evaluate(em)
                    row = dict(fold=fold, fold_name=FOLDS[fold], draw=draw, arm=name, m_target=m,
                               complement_emitted=int((em & ~em_cb).sum()) if name.startswith("K_") else 0,
                               auc_model=cell.auc(p), auc_gem1=cell.auc(gem_q), **ev, **timing)
                    if name == "C":
                        row["h28_reference_dti"] = ref.get((fold, draw))
                        row["reproduces_h28"] = ref.get((fold, draw)) is not None and abs(ev["dti"] - ref[(fold, draw)]) <= 1e-6
                        row["auc_single_feature"] = auc_feat
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"[{time.time() - t_all:.0f}s] fold {fold} draw {draw} {name:6s}: DTI={ev['dti']:.6f} "
                          f"tp={ev['tp']:.1f} fp={ev['fp']:.1f} emitted={ev['emitted']}", flush=True)
                del cell
    print(f"DONE {cells_path} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
