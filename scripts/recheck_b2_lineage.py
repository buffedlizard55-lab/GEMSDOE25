#!/usr/bin/env python3
"""Recompute the GEMSDOE32 B2 (0.2778, OWNER-REPORTED) lineage from restored bytes.

Inputs (restore first):
    python scripts/restore_data.py --group core
    python scripts/restore_data.py --group owner_mirror

Checks, all COMPUTED from the files on disk (no score is produced here):
  * B2 dot count, parent (GEMSDOE28 h27-4 NaN-outside) dot count, subset relation, Jaccard;
  * distance of every parent dot that B2 removed to the labelled catalogue (existing_faults.tif);
  * B2 dots within 2 px (200 m at 100 m pixels) of the catalogue.
Writes evidence/b2_lineage_recheck_2026-10-29.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

OUT = ROOT / "evidence" / "b2_lineage_recheck_2026-10-29.json"
B2 = data_dir() / "owner_mirrors" / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
PARENT = data_dir() / "owner_mirrors" / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
CATALOGUE = data_dir() / "existing_faults.tif"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_mask(p: Path) -> np.ndarray:
    import rasterio

    with rasterio.open(p) as s:
        arr = s.read(1)
    return np.nan_to_num(arr) > 0


def main() -> int:
    from scipy.ndimage import distance_transform_edt

    for p in (B2, PARENT, CATALOGUE):
        if not p.exists():
            print(f"missing {p}; run restore_data.py --group core and --group owner_mirror")
            return 2
    import rasterio

    with rasterio.open(CATALOGUE) as s:
        cat = np.nan_to_num(s.read(1)) > 0
    b2 = load_mask(B2)
    parent = load_mask(PARENT)
    removed = parent & ~b2
    added = b2 & ~parent
    dist_px = distance_transform_edt(~cat)  # px to nearest catalogue pixel (catalogue pixels = 0)
    removed_d = dist_px[removed]
    b2_d = dist_px[b2]
    inter = int((b2 & parent).sum())
    union = int((b2 | parent).sum())
    receipt = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/recheck_b2_lineage.py",
        evidence_class="COMPUTED lineage arithmetic on owner mirrors (no score, no holdout, no organizer receipt)",
        sha256=dict(b2=sha256(B2), parent=sha256(PARENT), catalogue=sha256(CATALOGUE)),
        b2_dots=int(b2.sum()),
        parent_dots=int(parent.sum()),
        b2_subset_of_parent=bool(not added.any()),
        dots_added_by_b2=int(added.sum()),
        dots_removed_from_parent=int(removed.sum()),
        jaccard=round(inter / union, 5),
        catalogue_pixels=int(cat.sum()),
        removed_dots_max_catalogue_distance_px=float(removed_d.max()) if removed_d.size else None,
        removed_dots_within_2px_catalogue=int((removed_d <= 2).sum()) if removed_d.size else 0,
        b2_dots_within_2px_catalogue=int((b2_d <= 2).sum()),
        b2_dots_on_catalogue_pixels=int((b2 & cat).sum()),
    )
    OUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
