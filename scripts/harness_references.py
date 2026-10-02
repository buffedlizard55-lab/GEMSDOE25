#!/usr/bin/env python3
"""Score the group's scored rasters (as emitted) inside the same hide-and-recover cells -> evidence/harness_references.json.

CAUTION (IR-25-PROXY-LIMITS): these rasters are not out-of-fold (they were built with the whole catalogue and mask every
catalogue pixel, including the ones this harness hides). They are diagnostics only, never 'baselines to beat'.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402

REFS = {
    "H19-5 (0.1922)": "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "H19-4 (0.1894)": "gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
    "H16-1 (0.1855)": "gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif",
    "dotted H19-5 d1.5 (0.2477)": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
    "dotted H19-5 d2.8 (unscored)": "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "blind lattice s5 (0.0904)": "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
}


def main() -> None:
    ctx = load_context(work_dir())
    masks = {}
    for k, f in REFS.items():
        with rasterio.open(data_dir() / "scored" / f) as s:
            masks[k] = np.nan_to_num(s.read(1), nan=0.0) > 0
    rows = []
    for fold in range(4):
        for draw in (0, 1):
            cell = Cell(ctx, fold, draw)
            for k, m in masks.items():
                r = cell.evaluate(m[cell.sl] & cell.dom_c)
                rows.append(dict(ref=k, fold=fold, draw=draw, **r))
            del cell
    out = {}
    for k in REFS:
        rs = [r for r in rows if r["ref"] == k]
        out[k] = dict(mean_dti=float(np.mean([r["dti"] for r in rs])),
                      by_fold=[float(np.mean([r["dti"] for r in rs if r["fold"] == f])) for f in range(4)],
                      hug=float(np.mean([r["hug"] for r in rs])), emitted=float(np.mean([r["emitted"] for r in rs])))
    (ROOT / "evidence" / "harness_references.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in out.items():
        print(f"{k:32s} DTI={v['mean_dti']:.4f} folds={[round(x,3) for x in v['by_fold']]} hug={v['hug']:.2f} px={v['emitted']:.0f}")


if __name__ == "__main__":
    main()
