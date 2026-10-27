#!/usr/bin/env python3
"""Re-audit the highest supplied, SHA-pinned raster from each of nine sites.

This is a local mirror/pixel audit, not a live leaderboard query or an organizer
receipt. Run scripts/fetch_top_scorers.py and restore the core inputs first.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import sha256_file  # noqa: E402

SITES = (24, 25, 27, 28, 30, 31, 32, 33, 36)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/focus_winners_reaudit_2026-10-27.json")
    args = ap.parse_args()
    manifest = json.loads((ROOT / "registry/top_scorer_sources.json").read_text())["rasters"]
    pins = json.loads((ROOT / "registry/data_manifest.json").read_text())["files"]
    previous = {r["site"]: r for r in json.loads((ROOT / "evidence/focus_audit_2026-10-26.json").read_text())["sites"]}
    with rasterio.open(data_dir() / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
        grid = (ds.shape, ds.crs, ds.transform)
        if ds.count != 1 or ds.crs is None:
            raise ValueError("invalid template")
    with rasterio.open(data_dir() / "labels.tif") as ds:
        if (ds.shape, ds.crs, ds.transform) != grid:
            raise ValueError("labels grid mismatch")
        labels = ds.read(1) == 1
    masks, rows = {}, []
    for number in SITES:
        name = f"GEMSDOE{number}"
        choices = [x for x in manifest if re.search(rf"/{name}(?:/|$)", x["site"], re.I)]
        if not choices:
            raise ValueError(f"missing {name}")
        entry = max(choices, key=lambda x: x["owner_reported_score"])
        path = data_dir() / "registry_top" / entry["local"]
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"hash mismatch: {path}")
        with rasterio.open(path) as ds:
            if ds.count != 1 or (ds.shape, ds.crs, ds.transform) != grid:
                raise ValueError(f"grid mismatch: {path}")
            values = ds.read(1)
        v = values[footprint]
        if not np.isfinite(v).all() or (v < 0).any() or (v > 1).any():
            raise ValueError(f"invalid footprint values: {path}")
        mask = footprint & (values > 0)
        masks[name] = mask
        if entry["repo"].startswith("local-restore"):
            source = next(x for x in pins if x.get("sha256") == entry["sha256"] and x.get("path"))
            repo, ref, source_path = source["repo"], source["ref"], source["path"]
        else:
            repo, ref, source_path = entry["repo"], previous[name]["source_head"], entry["path"]
        url = f"https://github.com/{repo}/raw/{ref}/{source_path}"
        rows.append(dict(site=name, site_url=entry["site"], file=Path(source_path).name,
                         download_url=url, source_revision=ref, sha256=entry["sha256"],
                         owner_reported_score=entry["owner_reported_score"], score_class="OWNER-REPORTED; unconfirmed",
                         footprint_positive_pixels=int(mask.sum()), footprint_range=[float(v.min()), float(v.max())],
                         shape=list(grid[0]), crs=str(grid[1]), transform=list(grid[2])[:6],
                         historical_file=True, slot_approved=False))
    comparisons = []
    for i, left in enumerate(SITES):
        a = masks[f"GEMSDOE{left}"]
        for right in SITES[i + 1:]:
            b = masks[f"GEMSDOE{right}"]
            both = int((a & b).sum())
            comparisons.append(dict(left=f"GEMSDOE{left}", right=f"GEMSDOE{right}",
                                    intersection=both, left_only=int(a.sum())-both,
                                    right_only=int(b.sum())-both, masks_equal=bool(np.array_equal(a, b))))
    distance = distance_transform_edt(~labels)
    d28, b2, r1, g36 = (masks[x] for x in ("GEMSDOE25", "GEMSDOE32", "GEMSDOE31", "GEMSDOE36"))
    # GEMSDOE28's lower-scoring R1 is a separate comparison, not its best Rung30 file.
    r1_28 = next(x for x in manifest if x["local"] == "g28_h27-4-r1-solo_0.2708.tif")
    r1_path = data_dir() / "registry_top" / r1_28["local"]
    if sha256_file(r1_path) != r1_28["sha256"]:
        raise ValueError("GEMSDOE28 R1 comparison hash mismatch")
    with rasterio.open(r1_path) as ds:
        if ds.count != 1 or (ds.shape, ds.crs, ds.transform) != grid:
            raise ValueError("GEMSDOE28 R1 comparison grid mismatch")
        r1_28_mask = footprint & (ds.read(1) > 0)
    identities = dict(b2_equals_d28_pruned_distance_le_2=bool(np.array_equal(b2, d28 & (distance > 2))),
                      r1_equals_d28_pruned_distance_le_1=bool(np.array_equal(r1, d28 & (distance > 1))),
                      gems28_lower_scoring_r1_equals_gems31=bool(np.array_equal(r1_28_mask, r1)),
                      gems28_winner_equals_gems31=bool(np.array_equal(masks["GEMSDOE28"], r1)),
                      d28_pixels_removed_b2=int((d28 & (distance <= 2)).sum()),
                      g36_contains_b2=bool(np.all(~b2 | g36)), g36_extra_over_b2=int((g36 & ~b2).sum()))
    result = dict(evidence_class="COMPUTED mask geometry and OWNER-REPORTED scores; not organizer receipts",
                  highest_scope="Highest supplied pinned score per requested site, not an exhaustive leaderboard search",
                  sites=rows, identities=identities, pairwise=comparisons,
                  limitations=["Hashes prove mirror consistency, not organizer provenance.",
                               "Positive-mask equality alone does not prove equal continuous prediction values.",
                               "Historical results are not eligible as new submissions."])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(f"wrote {args.out}; {len(rows)} sites, {len(comparisons)} mask comparisons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
