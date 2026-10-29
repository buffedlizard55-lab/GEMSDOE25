#!/usr/bin/env python3
"""Share of the GEMSDOE32 B2 dots within 3 px of registry raster r13 (literal parallel-run lane rule, 70% cap).

Inputs: data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif (scripts/restore_data.py --group scored)
        data/mirror/gemsdoe32_b2_0.2778_zeros.tif (see scripts/audit_b2_lineage.py for the blob ID)
Writes evidence/b2_lane_vs_r13_2026-10-29.json. COMPUTED on owner-mirror bytes; not a score.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

R13 = data_dir() / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
B2 = data_dir() / "mirror" / "gemsdoe32_b2_0.2778_zeros.tif"
CAP = 0.70


def main() -> int:
    r13 = np.nan_to_num(rasterio.open(R13).read(1), nan=0) == 1
    b2 = np.nan_to_num(rasterio.open(B2).read(1), nan=0) == 1
    dist = distance_transform_edt(~r13)  # px to nearest r13 dot
    within = int((b2 & (dist <= 3)).sum())
    share = within / int(b2.sum())
    rec = dict(
        evidence_class="COMPUTED on owner-mirror bytes; not a score",
        script="scripts/audit_b2_lane_vs_r13.py",
        r13_sha256=hashlib.sha256(R13.read_bytes()).hexdigest(),
        r13_dots=int(r13.sum()),
        b2_dots=int(b2.sum()),
        b2_within_3px_of_r13=within,
        share=round(share, 5),
        literal_lane_cap=CAP,
        passes_literal_cap=bool(share <= CAP),
    )
    (ROOT / "evidence" / "b2_lane_vs_r13_2026-10-29.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    return 0 if rec["passes_literal_cap"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
