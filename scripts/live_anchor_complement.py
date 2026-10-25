#!/usr/bin/env python3
"""INFERENCE: what owner-reported scores of the sibling "swap" files imply about off-H19-5 dot value.

For every registry file with no dot within 2 px of the catalogue, split its dots into near-incumbent (<= 3 px of H19-5)
and off-incumbent. Assume the near-incumbent dots carry H33-2-B2's average per-dot credit c_in and solve the DTI identity
DTI = TP / (0.2 (TP + FP) + 0.8 N),  FP = n - TP / r
for the file's TP, then for the off-incumbent per-dot credit c_out, over the grid N in {10000, 12691, 16000}, r in {1.0, 2.0}.
Efficiency e = c_out / c_in is compared with the live break-even R* (knowledge/17). Scores are OWNER-REPORTED claims and the
model is an approximation; the output is INFERENCE, not a measurement.  Output: evidence/live_anchor_complement.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir, work_dir  # noqa: E402

GRID = [(N, r) for N in (10_000, 12_691, 16_000) for r in (1.0, 2.0)]


def solve_tp(s: float, n: int, N: int, r: float) -> float:
    return s * (0.2 * n + 0.8 * N) / (1 - 0.2 * s * (1 - 1 / r))


def pos(p: Path) -> np.ndarray:
    with rasterio.open(p) as f:
        a = f.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> None:
    lab = np.load(work_dir() / "bands" / "_labels.npy")
    top = data_dir() / "registry_top"
    h19 = pos(top / "g19_h19-5_0.1922.tif")
    d_h19 = distance_transform_edt(~h19)
    d_cat = distance_transform_edt(~lab)
    s_b2, n_b2 = 0.2778, 37_654
    rows = []
    for p in sorted(top.glob("*.tif")):
        P = pos(p)
        n = int(P.sum())
        if (d_cat[P] <= 2).any() or p.name.startswith(("g19", "g32")):
            continue
        s = float(p.stem.rsplit("_", 1)[1])
        f = float((d_h19[P] <= 3).mean())
        est = []
        for N, r in GRID:
            c_in = solve_tp(s_b2, n_b2, N, r) / n_b2
            tp = solve_tp(s, n, N, r)
            c_out = (tp - f * n * c_in) / ((1 - f) * n) if f < 1 else float("nan")
            tp_b2 = solve_tp(s_b2, n_b2, N, r)
            fp_b2 = n_b2 - tp_b2 / r
            be = 0.2 * s_b2 / (1 - 0.2 * s_b2)
            est.append(dict(N=N, r=r, efficiency_e=round(c_out / c_in, 3), live_break_even_R=round(be / (tp_b2 / fp_b2), 3)))
        e = [x["efficiency_e"] for x in est]
        identifiable = f <= 0.95  # with < 5 % off-incumbent dots the split is dominated by near-dot heterogeneity
        rows.append(dict(file=p.name, owner_reported_score=s, dots=n, frac_within_3px_h19_5=round(f, 3), identifiable=identifiable,
                         efficiency_range=[min(e), max(e)] if identifiable else None, grid=est))
    out = dict(generated_by="scripts/live_anchor_complement.py", evidence_class="INFERENCE from OWNER-REPORTED scores",
               assumptions=["near-incumbent dots carry B2's average per-dot credit", "FP = n - TP/r",
                            "N (hidden truth px) and r on the stated grid"], rows=rows)
    path = ROOT / "evidence" / "live_anchor_complement.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    for r_ in sorted(rows, key=lambda x: -x["owner_reported_score"]):
        if not r_["identifiable"]:
            print(f"{r_['file'][:30]:30s} not identifiable (near-H19-5 {r_['frac_within_3px_h19_5']:.3f})")
            continue
        print(f"{r_['file'][:30]:30s} score {r_['owner_reported_score']:.4f} dots {r_['dots']:6d} near-H19-5 {r_['frac_within_3px_h19_5']:.3f} "
              f"off-incumbent efficiency e in [{r_['efficiency_range'][0]:.2f}, {r_['efficiency_range'][1]:.2f}]")


if __name__ == "__main__":
    main()
