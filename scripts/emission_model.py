#!/usr/bin/env python3
"""First-order live-score model for score-blind dotting of H19-5 -> ``evidence/emission_model.json``.

Model (assumptions stated, not measured): truth |G| pixels; H19-5 earns credit c|G| with false-positive mass f|G|.
Thinning to n pixels keeps a fraction rho(d) of the credit (geometric: truth uniform in the neighbourhood of H19-5's
detections, kernel credit to the nearest kept pixel) and the false-positive mass scales with the pixel count.
(c, f) are solved from the two owner-reported scores (0.1922 and 0.2477) given rho(1.5); DTI(d) follows from
DTI = rho c / (0.2 rho c + 0.2 (n/n0) f + 0.8).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.metric import kernel  # noqa: E402
from gems25.paths import data_dir  # noqa: E402
from gems25.thinning import dot_thin  # noqa: E402

D0, D1 = 0.1922, 0.2477


def main() -> None:
    d = data_dir()
    with rasterio.open(d / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(d / "labels.tif") as s:
        lab = s.read(1) == 1
    with rasterio.open(next((d / "scored").glob("gems19-h19-5-*-nan.tif"))) as s:
        h = np.nan_to_num(s.read(1), nan=0.0) > 0
    n0 = int(h.sum())
    dH = distance_transform_edt(~h)
    S = (dH < 3) & foot & ~lab
    kH = kernel(dH[S]).sum()
    curve = []
    for md in (1.0, 1.5, 2.0, 2.4, 3.0, 3.5, 4.0, 5.0):
        m = dot_thin(h, md)
        rho = float(kernel(distance_transform_edt(~m)[S]).sum() / kH)
        curve.append(dict(min_dist=md, px=int(m.sum()), retention=rho))
    rho15 = next(r["retention"] for r in curve if r["min_dist"] == 1.5)
    n15 = next(r["px"] for r in curve if r["min_dist"] == 1.5)

    def solve(scale: float):
        rho_ = rho15 * scale
        s = n15 / n0

        def g(f):
            c = D0 * (0.2 * f + 0.8) / (1 - 0.2 * D0)
            return rho_ * c / (0.2 * rho_ * c + 0.2 * s * f + 0.8) - D1

        f = brentq(g, 0.01, 500)
        return D0 * (0.2 * f + 0.8) / (1 - 0.2 * D0), f

    def dti(r, c, f, n):
        return r * c / (0.2 * r * c + 0.2 * (n / n0) * f + 0.8)

    bands = {}
    for scale in (0.95, 1.0, 1.05):
        c, f = solve(scale)
        bands[scale] = [dti(min(1.0, row["retention"] * scale), c, f, row["px"]) for row in curve]
    c, f = solve(1.0)
    for i, row in enumerate(curve):
        row["model_dti"] = bands[1.0][i]
        row["model_dti_low"] = min(b[i] for b in bands.values())
        row["model_dti_high"] = max(b[i] for b in bands.values())
    best = max(curve, key=lambda r: r["model_dti"])
    out = dict(
        inputs=dict(score_h19_5_owner_reported=D0, score_d1_5_owner_reported=D1, n_h19_5=n0, n_d1_5=n15, retention_d1_5=rho15),
        solved=dict(credit_per_truth=c, fp_mass_per_truth=f),
        curve=curve,
        best_by_model=best,
        d2_8=next(r for r in curve if r["min_dist"] == 2.4),
        caveat=("First-order model with two fitted parameters and the two live scores as its only anchors; the shape of the curve in d is an "
                "extrapolation. The retention is geometric (truth assumed uniform near H19-5's detections). The band varies retention by +/-5 %. "
                "Not a leaderboard result."),
    )
    (ROOT / "evidence" / "emission_model.json").write_text(json.dumps(out, indent=1) + "\n")
    for r in curve:
        print(f"d={r['min_dist']:.1f} px={r['px']:>7,} rho={r['retention']:.3f} model DTI={r['model_dti']:.4f} [{r['model_dti_low']:.4f}, {r['model_dti_high']:.4f}]")
    print("best by model:", best["min_dist"], round(best["model_dti"], 4))


if __name__ == "__main__":
    main()
