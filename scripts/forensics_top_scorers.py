#!/usr/bin/env python3
"""Forensics of the highest owner-reported GEMSDOE submissions (2026-10-25 session).

Inputs: rasters fetched by SHA-256 from the owner's public GitHub repositories into
``data/registry_top/`` (see ``registry/top_scorer_sources.json``). Scores are OWNER-REPORTED claims
copied from the user brief, never organizer receipts.

For every raster we compute (COMPUTED evidence class):
  * number of positive pixels, distinct positive values, on-catalogue positives;
  * histogram of distance (px) from each emitted pixel to the nearest catalogue pixel;
  * set relations with the lineage (subset of d2-8? of h27-4? Jaccard / shared pixels);
  * nearest-neighbour spacing between emitted pixels.
Output: evidence/top_scorer_forensics.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

TOP = data_dir() / "registry_top"
OUT = ROOT / "evidence" / "top_scorer_forensics.json"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_pos(p: Path) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(p) as s:
        a = s.read(1).astype(np.float64)
    pos = np.isfinite(a) & (a > 0)
    return pos, a


def main() -> None:
    with rasterio.open(data_dir() / "labels.tif") as s:
        lab = s.read(1) > 0
    with rasterio.open(data_dir() / "sample_submission.tif") as s:
        tmpl = s.read(1)
        foot = np.isfinite(tmpl) & (tmpl > -1e30)
    dcat = distance_transform_edt(~lab)
    files = sorted(TOP.glob("*.tif"))
    rasters = {}
    for p in files:
        pos, a = load_pos(p)
        key = p.stem
        vals = np.unique(a[pos])
        d = dcat[pos]
        yy, xx = np.nonzero(pos)
        nn = cKDTree(np.c_[yy, xx]).query(np.c_[yy, xx], k=2)[0][:, 1] if yy.size > 1 else np.array([])
        rasters[key] = pos
        rec = dict(
            file=p.name, sha256=sha(p), reported_score_owner_claim=float(key.rsplit("_", 1)[1]),
            positive_pixels=int(pos.sum()), positives_outside_footprint=int((pos & ~foot).sum()),
            on_catalogue_positives=int((pos & lab).sum()),
            distinct_positive_values=int(vals.size), value_min=float(vals.min()), value_max=float(vals.max()),
            frac_within_1px_catalogue=float((d <= 1.0).mean()), frac_within_2px=float((d <= 2.0).mean()),
            frac_within_3px=float((d <= 3.0).mean()), frac_beyond_10px=float((d > 10).mean()),
            median_dist_catalogue_px=float(np.median(d)),
            nn_spacing_median_px=float(np.median(nn)) if nn.size else None,
            nn_spacing_min_px=float(nn.min()) if nn.size else None,
        )
        print(json.dumps(rec))
        OUT.parent.mkdir(parents=True, exist_ok=True)
        rasters[key + "__rec"] = rec
    keys = [k for k in rasters if not k.endswith("__rec")]
    rel = {}
    for a in keys:
        for b in keys:
            if a >= b:
                continue
            A, B = rasters[a], rasters[b]
            inter = int((A & B).sum())
            rel[f"{a}|{b}"] = dict(shared=inter, a_in_b=inter / max(int(A.sum()), 1),
                                   b_in_a=inter / max(int(B.sum()), 1),
                                   jaccard=inter / max(int((A | B).sum()), 1))
    # H33-2-B2 reconstruction test: is it exactly {h27-4 dots with d(catalogue) > 2}?
    recon = {}
    b2 = next((k for k in keys if k.startswith("g32_h33-2-b2")), None)
    for base in [k for k in keys if "h27-4" in k]:
        pruned = rasters[base] & (dcat > 2.0)
        if b2:
            recon[base] = dict(pruned_pixels=int(pruned.sum()),
                               identical_to_h33_2_b2=bool((pruned == rasters[b2]).all()),
                               xor_pixels=int((pruned ^ rasters[b2]).sum()))
    out = dict(
        generated_by="scripts/forensics_top_scorers.py", evidence_class="COMPUTED (scores are OWNER-REPORTED claims)",
        catalogue_pixels=int(lab.sum()), footprint_pixels=int(foot.sum()),
        rasters=[rasters[k + "__rec"] for k in keys], pairwise=rel, h33_2_b2_reconstruction=recon,
    )
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)
    print(json.dumps(recon, indent=1))


if __name__ == "__main__":
    main()
