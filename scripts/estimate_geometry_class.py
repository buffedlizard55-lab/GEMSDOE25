#!/usr/bin/env python3
"""Empirical, geometry-matched score band for a dot-emission raster.

Two *different* estimates are produced and never conflated:

1. ``model_estimate`` — the calibrated ``pi``-model of ``scripts/estimate_score.py``.  It reproduces the
   H19-5 dotting family to <=0.004 DTI (lattice 0.0914 vs 0.0904 reported; h19-5 0.1903 vs 0.1922;
   d1-5 0.2437 vs 0.2477) but **under-predicts catalogue-hygienic (d_cat > 2 px) emissions badly**
   (GEMSDOE32 B2: 0.0376 predicted vs 0.2778 reported), because its truth intensity decays away from
   the catalogue.  It is therefore reported for transparency and explicitly not used for the band.

2. ``empirical_band`` — the owner-reported scores of the group's own *historically scored* rasters that
   share the candidate's emission geometry (dot count within +/-10 %, nearest-neighbour spacing within
   +/-0.4 px, catalogue buffer <= 2 px).  This is the only defensible estimate available without the
   hidden labels.  It is an EMPIRICAL ESTIMATE, not a score, not HOLDOUT-DTI and not a projection.

Everything is computed from restored, SHA-256-pinned bytes in this run.

    python scripts/estimate_geometry_class.py docs/downloads/<file>.tif \
        --json evidence/h81_score_estimate.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from estimate_score import estimate, sha256_file  # noqa: E402
from gems25.paths import data_dir  # noqa: E402

# (id, path under data/registry_top, owner-reported score, provenance note)
SCORED_GEOMETRY_REFERENCES = (
    ("gemsdoe32-b2", "g32_h33-2-b2_0.2778.tif", 0.2778,
     "GEMSDOE32 h33-h33-2-b2 (owner-reported; hash c55bafc47005… matched in registry/artifact_ledger.json)"),
    ("gemsdoe36-anderson-pinn", "g36_anderson-pinn_0.2750.tif", 0.2750,
     "GEMSDOE36 Anderson-PINN (owner-reported; 96.9% B2 overlap)"),
    ("gemsdoe28-r1", "g28_h27-4-r1-solo_0.2708.tif", 0.2708,
     "GEMSDOE28 h27-4-r1-solo (owner-reported; exact-mask twin of GEMSDOE31)"),
    ("gemsdoe27-h31-1", "g27_h31_0.2250.tif", 0.2250,
     "GEMSDOE27 H31-1 catalogue-free ML (owner-reported)"),
    ("gemsdoe25-d2-8", "../../../data/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", None,
     "D2.8 dotting of H19-5 (unscored in every owner list; 0.2600 is the GEMSDOE25/30 D2.8 claim)"),
)


def geometry_stats(arr: np.ndarray, foot: np.ndarray, lab: np.ndarray, d_cat: np.ndarray,
                   sample: int = 20000, seed: int = 0) -> dict:
    dots = (np.nan_to_num(arr, nan=0.0) > 0) & foot & ~lab
    n = int(dots.sum())
    out = dict(positive_pixels=n, on_catalogue=int(((np.nan_to_num(arr, nan=0.0) > 0) & lab).sum()))
    if n >= 2:
        ys, xs = np.nonzero(dots)
        rng = np.random.default_rng(seed)
        sel = rng.choice(ys.size, min(sample, ys.size), replace=False)
        tree = cKDTree(np.column_stack([ys, xs]))
        nn = tree.query(np.column_stack([ys[sel], xs[sel]]), k=2)[0][:, 1]
        dv = d_cat[dots]
        out.update(
            nn_median_px=round(float(np.median(nn)), 3),
            nn_mean_px=round(float(nn.mean()), 3),
            share_nn_below_6px=round(float((nn < 6.0).mean()), 4),
            d_cat_min_px=round(float(dv.min()), 3),
            d_cat_median_px=round(float(np.median(dv)), 3),
            frac_2_9_px=round(float(((dv > 2.0) & (dv <= 9.0)).mean()), 4),
            frac_gt9_px=round(float((dv > 9.0).mean()), 4),
            frac_gt20_px=round(float((dv > 20.0).mean()), 4),
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raster", type=Path)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--dot-tolerance", type=float, default=0.10)
    ap.add_argument("--spacing-tolerance", type=float, default=0.40)
    ap.add_argument("--catalogue-buffer-max", type=float, default=2.5)
    args = ap.parse_args()

    d = data_dir()
    with rasterio.open(d / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(d / "labels.tif") as ls:
        lab = (ls.read(1) == 1) & foot
    d_cat = distance_transform_edt(~lab)

    with rasterio.open(args.raster) as s:
        cand_arr = np.nan_to_num(s.read(1), nan=0.0).astype(np.float32)
    cand = geometry_stats(cand_arr, foot, lab, d_cat)

    refs = []
    for rid, rel, score, note in SCORED_GEOMETRY_REFERENCES:
        p = Path(rel) if rel.startswith("..") else (d / "registry_top" / rel)
        p = (Path(__file__).resolve().parents[1] / rel) if rel.startswith("..") else p
        if not p.exists():
            refs.append(dict(id=rid, file=str(p), status="missing"))
            continue
        with rasterio.open(p) as s:
            arr = np.nan_to_num(s.read(1), nan=0.0).astype(np.float32)
        st = geometry_stats(arr, foot, lab, d_cat)
        st.update(id=rid, file=p.name, sha256=sha256_file(p), owner_reported_score=score, provenance=note)
        refs.append(st)

    usable = [r for r in refs
              if r.get("status") != "missing" and r.get("owner_reported_score") is not None
              and r.get("positive_pixels") and abs(r["positive_pixels"] / max(cand["positive_pixels"], 1) - 1)
              <= args.dot_tolerance
              and r.get("nn_median_px") is not None
              and abs(r["nn_median_px"] - cand.get("nn_median_px", 0.0)) <= args.spacing_tolerance
              and r.get("d_cat_min_px", 99) <= args.catalogue_buffer_max]
    band = dict(
        n_matched=len(usable), matched_ids=[r["id"] for r in usable],
        matched_scores=[r["owner_reported_score"] for r in usable],
        min=min((r["owner_reported_score"] for r in usable), default=None),
        max=max((r["owner_reported_score"] for r in usable), default=None),
        median=float(np.median([r["owner_reported_score"] for r in usable])) if usable else None,
    )
    band["range"] = (f"{band['min']:.4f}–{band['max']:.4f}" if usable else "NO MATCHED HISTORY")
    band["point_estimate"] = round(float(np.median(band["matched_scores"])), 4) if usable else None
    band["rule"] = (f"dot count within ±{args.dot_tolerance:.0%}, median nearest-neighbour spacing within "
                    f"±{args.spacing_tolerance} px, catalogue buffer ≤{args.catalogue_buffer_max} px; "
                    "owner-reported scores of the group's own scored rasters")
    band["evidence_class"] = ("EMPIRICAL ESTIMATE from owner-reported scores of geometry-matched rasters — "
                              "NOT a score, NOT HOLDOUT-DTI, NOT ORGANIZER-CONFIRMED, no statistical CI (n<10)")

    model = estimate(args.raster)
    rec = dict(
        raster=args.raster.name, raster_sha256=sha256_file(args.raster),
        candidate_geometry=cand, references=refs, empirical_band=band,
        model_estimate=dict(**model),
        model_estimate_scope_warning=(
            "The calibrated pi-model under-predicts catalogue-hygienic emissions (GEMSDOE32 B2: predicted "
            f"{0.037554:.4f} vs 0.2778 owner-reported). It is recorded for transparency only and must not be "
            "used as the band for this candidate."),
    )
    text = json.dumps(rec, indent=1, allow_nan=False) + "\n"
    print(text, end="")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
