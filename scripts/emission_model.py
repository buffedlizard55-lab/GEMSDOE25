#!/usr/bin/env python3
"""Conditional score-claim model for score-blind dotting of H19-5 -> ``evidence/emission_model.json``.

Model (assumptions stated, not measured): truth |G| pixels; H19-5 earns credit c|G| with false-positive mass f|G|.
Thinning to n pixels keeps a fraction rho(d) of the credit (geometric: truth uniform in the neighbourhood of H19-5's
detections, kernel credit to the nearest kept pixel) and the false-positive mass scales with the pixel count.
(c, f) are solved from two user/owner-reported, unverified DTI claims (0.1922 and 0.2477) given rho(1.5).
Outputs are conditional extrapolations, not verified competition scores or evidence that a file won.
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
    # ---- what would a target score require?  (truth size |G| from the blind lattice, owner-reported 0.0904)
    lat_N = 12503.0  # evidence/why_0_2477.json lattice_calibration.truth_px_in_footprint (rounded); live-pair reading gives 12,769
    lw = json.loads((ROOT / "evidence" / "why_0_2477.json").read_text())
    lat_N = float(lw["lattice_calibration"]["truth_px_in_footprint"])
    fp_per_px = f * lat_N / n0  # false-positive mass per emitted pixel of H19-5 (kept constant under thinning)
    req = []
    for tgt, label in (
        (D1, "reported 0.2477 claim (unverified)"),
        (0.2941, "reported rank-#5 claim 0.2941 (unverified)"),
        (0.3195, "reported rank-#1 claim 0.3195 (unverified)"),
    ):
        for n in (30_000, 40_000, 60_000):
            c_req = tgt * (0.2 * fp_per_px * n / lat_N + 0.8) / (1 - 0.2 * tgt)
            req.append(dict(target=tgt, label=label, emitted_px=n, credit_fraction_required=c_req, credit_per_emitted_px=c_req * lat_N / n))
    c15 = c * rho15
    # ---- consensus pruning break-even: dropping a fraction q of the dotted H19-5's pixels (chosen by a second detector).
    # DTI(q, s) = c15 (1 - s) / (0.2 (c15 (1 - s) + F (1 - q)) + 0.8), F = fp_per_px * n15 / |G|; s = share of the credit carried by the dropped pixels.
    F15 = fp_per_px * n15 / lat_N
    base_dti = c15 / (0.2 * (c15 + F15) + 0.8)
    prune = []
    for q in (0.1, 0.2, 0.3, 0.5):
        g_ = lambda sh: c15 * (1 - sh) / (0.2 * (c15 * (1 - sh) + F15 * (1 - q)) + 0.8) - base_dti  # noqa: E731
        s_star = brentq(g_, 0.0, 0.999)
        prune.append(dict(dropped_fraction_of_pixels=q, max_credit_share_of_dropped=s_star, per_pixel_credit_of_dropped_vs_average_max=s_star / q))
    have = dict(emitted_px=n15, credit_fraction=c15, credit_per_emitted_px=c15 * lat_N / n15)
    out = dict(
        input_status="The DTI anchors are user/owner-reported claims, not independently verified; no organizer receipt/page was accessed.",
        inputs=dict(score_h19_5_owner_reported=D0, score_d1_5_owner_reported=D1, n_h19_5=n0, n_d1_5=n15, retention_d1_5=rho15),
        solved=dict(credit_per_truth=c, fp_mass_per_truth=f),
        curve=curve,
        best_by_model=best,
        consensus_pruning_break_even=dict(baseline_model_dti=base_dti, rows=prune,
            reading="Dropping q of the pixels raises DTI only if the dropped pixels carry less than s* of the credit, i.e. their credit per pixel is below (s*/q) of the average."),
        requirements=dict(truth_px_used=lat_N, fp_mass_per_emitted_px=fp_per_px, dotted_h19_5_d1_5_has=have, table=req,
                          reading="credit_per_emitted_px = (credit fraction of |G|) * |G| / emitted pixels; compare with the dotted H19-5 row above"),
        d2_8=next(r for r in curve if r["min_dist"] == 2.4),
        caveat=("First-order model with two fitted parameters and two user/owner-reported, unverified DTI claims as its only score anchors; all outputs are conditional, "
                "and the shape of the curve in d is an extrapolation. Retention is geometric (truth assumed uniform near H19-5's detections); the band varies retention by +/-5 %. "
                "No organizer receipt/page was accessed; this is not a verified leaderboard result."),
    )
    (ROOT / "evidence" / "emission_model.json").write_text(json.dumps(out, indent=1) + "\n")
    for r in curve:
        print(f"d={r['min_dist']:.1f} px={r['px']:>7,} rho={r['retention']:.3f} model DTI={r['model_dti']:.4f} [{r['model_dti_low']:.4f}, {r['model_dti_high']:.4f}]")
    print("best by model:", best["min_dist"], round(best["model_dti"], 4))


if __name__ == "__main__":
    main()
