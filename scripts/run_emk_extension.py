#!/usr/bin/env python3
"""Post-hoc K-grid extension (knowledge/05 Addendum A): where does the dotted-emission optimum lie beyond 2.45 %?"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import dot_thin, score_ordered_dots  # noqa: E402

KS = (0.0245, 0.035, 0.05, 0.075)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--extras", nargs="*", default=[])
    ap.add_argument("--out", default=str(ROOT / "evidence" / "addons" / "emk_extension.json"))
    a = ap.parse_args()
    ctx = load_context(work_dir())
    cols = ctx.columns(a.base) + ctx.named(a.extras)
    rows = []
    for fold in range(4):
        for draw in (0, 1):
            cell = Cell(ctx, fold, draw, extras=bool(a.extras))
            p, _ = cell.fit_predict(cols, seed=draw)
            for kf in KS:
                s, top = cell.candidates(p, int(round(kf * cell.dom_c.sum())))
                for var, e in (("dot1.5", dot_thin(top, 1.5)), ("sapd1.5", score_ordered_dots(s, top, 1.5)), ("sapd2.4", score_ordered_dots(s, top, 2.4))):
                    rows.append(dict(fold=fold, draw=draw, kfrac=kf, variant=var, **cell.evaluate(e)))
            print(f"fold {fold} draw {draw} done", flush=True)
            del cell
    agg = defaultdict(list)
    for r in rows:
        agg[(r["variant"], r["kfrac"])].append(r)
    out = dict(base=a.base, extras=a.extras, note="post hoc, exploratory; frozen grid ended at 2.45 %",
               table=[dict(variant=v, kfrac=k, dti=float(np.mean([r["dti"] for r in x])), emitted=float(np.mean([r["emitted"] for r in x])),
                           coverage=float(np.mean([r["coverage"] for r in x])),
                           by_fold=[float(np.mean([r["dti"] for r in x if r["fold"] == f])) for f in range(4)])
                      for (v, k), x in sorted(agg.items())])
    out["best"] = max(out["table"], key=lambda r: r["dti"])
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    for r in out["table"]:
        print(f"{r['variant']:8s} K={100 * r['kfrac']:.2f}% DTI={r['dti']:.4f} px={r['emitted']:.0f}")
    print("best:", out["best"])


if __name__ == "__main__":
    main()
