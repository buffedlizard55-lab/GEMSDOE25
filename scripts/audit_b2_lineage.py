#!/usr/bin/env python3
"""Byte-level lineage audit of the GEMSDOE32 B2 (owner-reported 0.2778) raster.

Tests two claims on the actual files, not on notes:
  * B2 is a strict subset of each parent (GEMSDOE25 / GEMSDOE32 D2.8 zeros, 44,090 dots;
    GEMSDOE28 h27-4 r1-solo, 40,199 dots);
  * every dot removed from a parent lies within 200 m (2 px at 100 m) of a labelled catalogue pixel,
    and B2 has no dot within 200 m of the catalogue.

Inputs (restore first, all gitignored under data/):
  data/labels.tif                         (scripts/restore_data.py --group core)
  data/mirror/gemsdoe32_b2_0.2778_zeros.tif        GitHub blob 17a76895f68174cc93f3cb1597d25686f6d6bc67 (buffedlizard55-lab/GEMSDOE32)
  data/mirror/gemsdoe32_d2-8_zeros.tif             GitHub blob bfb7e86d046dd178c3d6ab60522861b5464dd420 (buffedlizard55-lab/GEMSDOE32)
  data/mirror/gemsdoe28_h27-4_r1-solo_nan.tif      GitHub blob 12b0a4ddf1cf76f2552621b8a8b1a1b88d783786 (buffedlizard55-lab/GEMSDOE28)
Fetch: gh api repos/<repo>/git/blobs/<sha> --jq .content | base64 -d > <file>
The B2 and h27-4 SHA-256 values are checked against evidence/nine_site_top_files_2026-10-28.json.

Writes evidence/b2_lineage_2026-10-29.json. Evidence class: COMPUTED on owner-mirror bytes;
the 0.2778 score is OWNER-REPORTED and is not verified here.
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

BUF_PX = 2  # 200 m at 100 m cells, the CAT_BUF_BLIND value in scripts/run_h74_experiments.py
MIRROR = data_dir() / "mirror"
FILES = {
    "b2": MIRROR / "gemsdoe32_b2_0.2778_zeros.tif",
    "d28": MIRROR / "gemsdoe32_d2-8_zeros.tif",
    "h27": MIRROR / "gemsdoe28_h27-4_r1-solo_nan.tif",
}
EXPECTED_SHA = {  # from evidence/nine_site_top_files_2026-10-28.json (owner-mirror pins)
    "b2": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "h27": "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dots(p: Path) -> np.ndarray:
    a = rasterio.open(p).read(1)
    return np.nan_to_num(a, nan=0.0) == 1.0


def main() -> int:
    labels = rasterio.open(data_dir() / "labels.tif").read(1) == 1
    dist = distance_transform_edt(~labels)  # pixels to nearest catalogue pixel
    near = dist <= BUF_PX
    d = {k: dots(p) for k, p in FILES.items()}
    out = dict(
        evidence_class="COMPUTED on owner-mirror bytes; 0.2778 is OWNER-REPORTED, not organizer-confirmed",
        script="scripts/audit_b2_lineage.py",
        catalogue_pixels=int(labels.sum()),
        buffer_px=BUF_PX,
        sha256={k: sha256(p) for k, p in FILES.items()},
        sha256_matches_pins={k: sha256(FILES[k]) == v for k, v in EXPECTED_SHA.items()},
        dots={k: int(v.sum()) for k, v in d.items()},
        b2_subset_of={
            "d28_d2-8": bool(not (d["b2"] & ~d["d28"]).any()),
            "h27_4": bool(not (d["b2"] & ~d["h27"]).any()),
        },
        removed={
            "from_d2-8": int((d["d28"] & ~d["b2"]).sum()),
            "from_h27_4": int((d["h27"] & ~d["b2"]).sum()),
        },
        removed_within_200m={
            "from_d2-8": int(((d["d28"] & ~d["b2"]) & near).sum()),
            "from_h27_4": int(((d["h27"] & ~d["b2"]) & near).sum()),
        },
        b2_dots_within_200m=int((d["b2"] & near).sum()),
        b2_dots_on_catalogue=int((d["b2"] & labels).sum()),
        dots_within_200m_of_catalogue={k: int((v & near).sum()) for k, v in d.items()},
    )
    out["consistent_with_pruning_rule"] = bool(
        out["b2_subset_of"]["d28_d2-8"] and out["b2_subset_of"]["h27_4"]
        and out["removed_within_200m"]["from_d2-8"] == out["removed"]["from_d2-8"]
        and out["removed_within_200m"]["from_h27_4"] == out["removed"]["from_h27_4"]
        and out["b2_dots_within_200m"] == 0
    )
    dest = ROOT / "evidence" / "b2_lineage_2026-10-29.json"
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0 if out["consistent_with_pruning_rule"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
