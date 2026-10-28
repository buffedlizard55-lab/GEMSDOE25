#!/usr/bin/env python3
"""Conditional model estimate of the official DTI for one emission raster.

**This is not a competition score and not a projection of the leaderboard.**  It evaluates the published
DTI formula against a *modelled* hidden truth field ``pi`` that was calibrated in
``knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md`` from owner-reported
scores of the group's own historical rasters (``evidence/h28_calibration/anchors.json``).  Its only
legitimate uses are (a) ranking two emissions produced in the same run and (b) a labelled sanity check
against a raster whose owner-reported score is already known.

Everything is computed here; nothing is copied from a report:

* ``pi(x) ∝ exp(-d_cat(x) / 1.85 px)`` normalised over footprint pixels outside the catalogue;
* ``N̂ = 12,691`` withheld truth pixels (the calibration's model-implied count);
* ``TP = N̂ · Σ pi(x) m(x)`` where ``m`` is the 300 m triangular kernel *maximum* field;
* ``FP = Σ_{p>0} p(x) · Ψ(ν_x)`` with the exact Poisson saturation ``Ψ`` of the kernel maximum;
* ``DTI = TP / (0.2(TP+FP) + 0.8 N̂)``.

    python scripts/estimate_score.py docs/downloads/<file>.tif
    python scripts/estimate_score.py docs/downloads/<file>.tif --json evidence/<name>.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25 import livecal  # noqa: E402
from gems25.paths import data_dir  # noqa: E402

CALIBRATION = ROOT / "evidence" / "h28_calibration" / "design.json"
PI_MODEL = "pure_exp"
PI_A = 0.0
PI_RHO_PX = 1.85


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_calibration() -> dict:
    d = json.loads(CALIBRATION.read_text())
    cal = d["calibrated"]
    return dict(pi=cal["pi"], lambda_hat_px=float(cal["lambda_hat_px"]), n_hat=float(cal["n_hat"]),
                anchor=cal.get("anchor", "owner-reported historical scores"),
                ceiling=float(d["ceiling_best"]["dti"]), ceiling_min_dist=float(d["ceiling_best"]["min_dist"]))


def estimate(raster: Path, template: Path | None = None) -> dict:
    cal = load_calibration()
    tmpl = template or (data_dir() / "sample_submission.tif")
    with rasterio.open(tmpl) as t:
        foot = np.isfinite(t.read(1))
    labels = data_dir() / "labels.tif"
    with rasterio.open(labels) as ls:
        lab = (ls.read(1) == 1) & foot
    with rasterio.open(raster) as s:
        arr = np.nan_to_num(s.read(1), nan=0.0).astype(np.float32)
        crs, transform, shape = s.crs, s.transform, s.shape
    if shape != foot.shape:
        raise ValueError(f"candidate shape {shape} does not match the template footprint {foot.shape}")

    d_cat = distance_transform_edt(~lab)
    pi = livecal.pi_field(np.array([PI_A, cal["lambda_hat_px"]]), d_cat, foot, lab, PI_MODEL)
    n_hat = cal["n_hat"]
    nu_field = (n_hat * livecal.disc_mass(pi)).astype(np.float32)
    pred = livecal_estimate(arr, pi, nu_field, n_hat, foot, lab)
    pred.update(
        raster=raster.name,
        raster_sha256=sha256_file(raster),
        crs_epsg=crs.to_epsg() if crs else None,
        transform=tuple(transform)[:6],
        shape=list(shape),
        positive_pixels=int(((arr > 0) & foot & ~lab).sum()),
        positive_on_catalogue=int(((arr > 0) & lab).sum()),
        calibrated_pi=cal["pi"],
        n_hat=n_hat,
        evidence_class="MODEL ESTIMATE (conditional on owner-reported calibration anchors); NOT a score, "
                        "NOT HOLDOUT-DTI, NOT ORGANIZER-CONFIRMED",
        calibration_file=str(CALIBRATION.relative_to(ROOT)),
        calibration_ceiling_dti=cal["ceiling"],
        calibration_ceiling_min_dist_px=cal["ceiling_min_dist"],
        caveat=("The model was fitted to the H19-5 dotting family. Emission families outside that band are "
                "under-predicted by up to ~0.06 DTI (IR-25-LIVE-MODEL-SCOPE), so treat the value as an "
                "order-of-magnitude comparison, never as a promise."),
    )
    return pred


def livecal_estimate(arr: np.ndarray, pi: np.ndarray, nu_field: np.ndarray, n_truth: float,
                     foot: np.ndarray, lab: np.ndarray) -> dict:
    pf = np.clip(arr, 0.0, 1.0) * np.float32(foot & ~lab)
    m, u = livecal.emission_fields(pf)
    t = float((pi * m).sum())
    uu = float((pi * u).sum())
    mass = float(pf.sum())
    sel = pf > 0
    fp = float((pf[sel] * livecal.psi(nu_field[sel])).sum()) if sel.any() else 0.0
    tp = n_truth * t
    den = 0.2 * (tp + fp) + 0.8 * n_truth
    dti = float(tp / den) if den > 0 else 0.0
    return dict(
        model_estimated_dti=round(dti, 6),
        predicted_tp=round(tp, 3),
        predicted_fp=round(fp, 3),
        emitted_mass=mass,
        coverage_t=round(t, 6),
        redundancy_r_over_u=round(uu - t, 6),
        fp_per_emitted_px=round(float(fp / mass), 6) if mass else 0.0,
        credit_per_emitted_px=round(float(tp / mass), 6) if mass else 0.0,
        nu_mean=round(float(nu_field[sel].mean()), 4) if sel.any() else 0.0,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raster", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    rec = estimate(args.raster)
    text = json.dumps(rec, indent=1, allow_nan=False) + "\n"
    print(text, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
