#!/usr/bin/env python3
"""Exact lower bound on 3-px overlap with the registered r13 lattice (2026-10-28).

For a catalogue-free candidate with N dots placed only on footprint pixels that are not catalogue pixels
(labels == 1), the candidate can place at most ``eligible`` dots outside the r13 3-px halo, where ``eligible``
= footprint & ~catalogue & ~halo(r13). Therefore at least N - eligible dots lie within 3 px of r13, so
overlap >= 1 - eligible/N for any placement. This is arithmetic on the restored, SHA-256-pinned rasters;
it does not depend on any candidate. It is a bound, not a claim about any file.

    python scripts/audit_r13_lane_bound.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

R13 = data_dir() / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
R13_PIN = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
OUT = ROOT / "evidence" / "lane_bound_r13_2026-10-28.json"


def main() -> None:
    sha = hashlib.sha256(R13.read_bytes()).hexdigest()
    if sha != R13_PIN:
        raise SystemExit(f"r13 SHA-256 mismatch: {sha}")
    with rasterio.open(data_dir() / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(data_dir() / "labels.tif") as lab:
        cat = lab.read(1) == 1
    with rasterio.open(R13) as s:
        r = np.nan_to_num(s.read(1)) > 0
    rdots = r & foot
    halo = (distance_transform_edt(~rdots) <= 3.0) & foot
    eligible = int((foot & ~cat & ~halo).sum())
    n_dots = 37654
    receipt = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/audit_r13_lane_bound.py",
        evidence_class="COMPUTED arithmetic bound on pinned rasters (not a candidate, not a score)",
        r13_sha256=sha, r13_dots_in_footprint=int(rdots.sum()), footprint_pixels=int(foot.sum()),
        catalogue_pixels_in_footprint=int((foot & cat).sum()), halo_pixels=int(halo.sum()),
        eligible_pixels_outside_halo_and_catalogue=eligible,
        min_overlap_at_37654_dots=round(max(0.0, 1 - eligible / n_dots), 6),
        max_dots_with_min_overlap_at_most_0_70=int(eligible / 0.30),
        note="Any catalogue-free candidate above this dot count has at least 70% of its dots within 3 px of r13 "
             "(the literal lane rule). The cap is a fact about the registry, not an owner-approved policy.",
    )
    OUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("eligible_pixels_outside_halo_and_catalogue",
                                             "min_overlap_at_37654_dots", "max_dots_with_min_overlap_at_most_0_70")}, indent=2))


if __name__ == "__main__":
    main()
