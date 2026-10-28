#!/usr/bin/env python3
"""Nine-focus-site top-file audit (2026-10-28): format, dot identity and the B2 lineage claim.

Reads only local, SHA-256-pinned owner-mirror rasters (``data/owner_mirrors`` and ``data/scored``).
Nothing is fetched by this script and nothing is uploaded. Scores are OWNER-REPORTED claims from the
user brief; this script never converts them into organizer scores or calibrated estimates.

Outputs ``evidence/nine_site_top_files_2026-10-28.json``:
  * per-file SHA-256 check against ``registry/top_scorer_sources.json`` (or the local data manifest),
  * format check against the pinned sample-submission grid (``gems25.submission.check_file``),
  * dot statistics (positives inside the footprint, on-catalogue positives, value set),
  * exact dot-set equality across the nine top files,
  * subset test: is the 0.2778 B2 dot set contained in each sibling's dot set?

    python scripts/audit_nine_site_top_files.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import check_file, sha256_file  # noqa: E402

OWNER = data_dir() / "owner_mirrors"
SCORED = data_dir() / "scored"
TEMPLATE = data_dir() / "sample_submission.tif"
LABELS = data_dir() / "labels.tif"
OUT = ROOT / "evidence" / "nine_site_top_files_2026-10-28.json"

# site -> (owner-reported score, local path, pinned sha256). Scores: OWNER-REPORTED (user brief).
TOP = {
    "GEMSDOE24": ("gems24-h25-1-dotted-h19-5-d1-5", 0.2477, SCORED / "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
                  "68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310"),
    "GEMSDOE25": ("dotted-h19-5-d2-8", 0.2600, SCORED / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
                  "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"),
    "GEMSDOE27": ("topo-gap-closure-t-v2-on-d1-5", 0.2449, OWNER / "GEMSDOE27__gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
                  "33003374335d84bf885f2d8f5e9dd4c57044c8ec58fa6a0d7fa581e8bc41c11d"),
    "GEMSDOE28": ("h36-1-rung30-blind-r1", 0.2710, OWNER / "GEMSDOE28__gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
                  "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641"),
    "GEMSDOE30": ("d28-poisson300m-offcat-44090", 0.2600, OWNER / "GEMSDOE30__gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif",
                  "5f963b8bca5ec226ddc7caaadec239c6be6d28aa567f890033be04d04bfd5e32"),
    "GEMSDOE31": ("h27-4-solo-d28", 0.2708, OWNER / "GEMSDOE31__gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
                  "07b6db440535404bb41ec8ddc797713e200d308e3da35937393efde5eb84bc40"),
    "GEMSDOE32": ("h33-2-b2", 0.2778, OWNER / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
                  "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "GEMSDOE33": ("h33d-analog-tip-stepover-r30", 0.2632, OWNER / "GEMSDOE33__GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif",
                  "bc3af2a5fcb4b49bc5845a2d7dc3da23daf41ce75e4c64da3337c0c8c93cc12c"),
    "GEMSDOE36": ("anderson-geothermal-pinn-38854", 0.2750, OWNER / "GEMSDOE36__gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
                  "e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a"),
}
# Sibling that owner forensics says is a pruned/identical twin of B2 (h27-4 family), kept for the lineage test.
SIBLINGS = {
    "GEMSDOE28-h27-4-r1-solo": ("h27-4-r1-solo", 0.2708, OWNER / "GEMSDOE28__gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
                                "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"),
}


def dots_of(path: Path, footprint: np.ndarray, catalogue: np.ndarray) -> dict:
    with rasterio.open(path) as s:
        a = s.read(1)
    inside = a[footprint]
    finite = np.isfinite(inside)
    pos_mask = np.zeros(footprint.shape, bool)
    pos_mask[footprint] = finite & (inside > 0)
    idx = np.flatnonzero(pos_mask.ravel())
    vals = np.unique(inside[finite]) if finite.any() else np.array([])
    return dict(
        positives=int(pos_mask.sum()),
        index=idx,
        on_catalogue=int((pos_mask & catalogue).sum()),
        nan_inside=int((~finite).sum()),
        value_set=[float(v) for v in vals[:5]],
        nan_outside=int(np.isnan(a[~footprint]).sum()),
        nonzero_outside=int((np.nan_to_num(a[~footprint]) != 0).sum()),
    )


def main() -> None:
    template_sha = sha256_file(TEMPLATE)
    man = json.loads((ROOT / "registry" / "data_manifest.json").read_text())["files"]
    tpl = [e for e in man if e["id"] == "sample_submission"][0]
    if template_sha != tpl["sha256"]:
        raise SystemExit("template SHA-256 mismatch; refusing to audit")
    with rasterio.open(TEMPLATE) as t:
        footprint = np.isfinite(t.read(1))
    with rasterio.open(LABELS) as lab:
        catalogue = lab.read(1) == 1
    rows, dot_sets = [], {}
    entries = dict(TOP)
    for name, entry in SIBLINGS.items():
        entries[name] = entry
    for site, (slug, score, path, pin) in entries.items():
        sha = sha256_file(path)
        fmt = check_file(path, TEMPLATE)
        d = dots_of(path, footprint, catalogue)
        key = hashlib.sha256(np.sort(d.pop("index")).astype("<i8").tobytes()).hexdigest()[:16]
        dot_sets[site] = key
        rows.append(dict(
            site=site, file=path.name, slug=slug, owner_reported_score=score,
            sha256=sha, sha256_matches_pin=(sha == pin), format_valid=fmt["format_valid"],
            strict_whole_array_valid=fmt["strict_whole_array_valid"], hard_failures=fmt["hard_failures"],
            outside_convention=("zeros" if d["nan_outside"] == 0 else "nan") if d["nonzero_outside"] == 0 else "nonzero",
            dot_set_sha256_16=key, **d,
        ))
    # exact dot-set duplicates among the nine focus sites, plus the Jaccard matrix of their dot sets
    focus = list(TOP)
    dups = []
    idx_of = {}
    for name, (_, _, path, _) in entries.items():
        with rasterio.open(path) as s:
            a = np.nan_to_num(s.read(1)) > 0
        idx_of[name] = set(np.flatnonzero((a & footprint).ravel()).tolist())
    jac = {}
    for i, a in enumerate(focus):
        for b in focus[i + 1:]:
            if dot_sets[a] == dot_sets[b]:
                dups.append([a, b])
            jac[f"{a}|{b}"] = round(len(idx_of[a] & idx_of[b]) / len(idx_of[a] | idx_of[b]), 6)
    max_jac = {a: max((jac.get(f"{min(a, b)}|{max(a, b)}", 0.0) for b in focus if b != a)) for a in focus}
    # B2 lineage: is the 0.2778 dot set a subset of each sibling's dot set?
    b2 = dots_of(TOP["GEMSDOE32"][2], footprint, catalogue)  # noqa: F841 (summary stats only)
    b2_idx = set(np.flatnonzero(((np.nan_to_num(rasterio.open(TOP["GEMSDOE32"][2]).read(1)) > 0)).ravel()).tolist())
    sib_idx = set(np.flatnonzero(((np.nan_to_num(rasterio.open(SIBLINGS["GEMSDOE28-h27-4-r1-solo"][2]).read(1)) > 0)).ravel()).tolist())
    lineage = dict(
        b2_dots=len(b2_idx), h27_4_dots=len(sib_idx),
        b2_subset_of_h27_4=b2_idx <= sib_idx,
        dots_in_h27_4_not_in_b2=len(sib_idx - b2_idx),
        jaccard=round(len(b2_idx & sib_idx) / len(b2_idx | sib_idx), 6),
    )
    # Nested lineage: deletion steps and catalogue proximity of the deleted dots (verified 2026-10-28).
    from scipy.ndimage import distance_transform_edt
    d28_path = data_dir() / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
    with rasterio.open(d28_path) as s_:
        d28 = (np.nan_to_num(s_.read(1)) > 0) & footprint
    d28_set = set(np.flatnonzero(d28.ravel()).tolist())
    h27_set = idx_of["GEMSDOE28-h27-4-r1-solo"]
    cat_dist = distance_transform_edt(~catalogue)
    flat_dist = cat_dist.ravel()
    removed_step1 = d28_set - h27_set
    removed_step2 = h27_set - b2_idx
    lineage_steps = dict(
        d2_8_dots=len(d28_set), h27_4_dots=len(h27_set), b2_dots=len(b2_idx),
        d2_8_subset_chain_ok=bool((h27_set <= d28_set) and (b2_idx <= h27_set)),
        d2_8_to_h27_4_removed=len(removed_step1), h27_4_to_b2_removed=len(removed_step2),
        removed_step1_max_catalogue_distance_px=float(flat_dist[list(removed_step1)].max()) if removed_step1 else None,
        removed_step2_max_catalogue_distance_px=float(flat_dist[list(removed_step2)].max()) if removed_step2 else None,
        d2_8_dots_within_2px_catalogue=int(sum(1 for i in d28_set if flat_dist[i] <= 2.0)),
        b2_dots_within_2px_catalogue=int(sum(1 for i in b2_idx if flat_dist[i] <= 2.0)),
    )
    receipt = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/audit_nine_site_top_files.py",
        evidence_class="COMPUTED on owner-mirror bytes; scores are OWNER-REPORTED claims, not organizer receipts",
        template_sha256=template_sha, footprint_pixels=int(footprint.sum()),
        rows=rows, exact_dot_set_duplicates_among_nine_sites=dups, max_jaccard_vs_other_focus_top=max_jac,
        lineage_steps=lineage_steps,
        jaccard_pairs_focus_top=jac, b2_lineage=lineage,
        estimated_competition_score="UNKNOWN / NOT ESTIMATED (no calibrated projection)",
    )
    OUT.write_text(json.dumps(receipt, indent=2) + "\n")
    for r in rows:
        print(f"{r['site']:<22} {r['owner_reported_score']:.4f} pos={r['positives']:>6} "
              f"sha_ok={r['sha256_matches_pin']} fmt={r['format_valid']} outside={r['outside_convention']} "
              f"on_cat={r['on_catalogue']} set={r['dot_set_sha256_16']}")
    print("exact dot-set duplicates:", dups)
    print("max Jaccard vs other focus tops:", {k: round(v, 4) for k, v in max_jac.items()})
    print("B2 lineage:", lineage)
    print("lineage steps:", lineage_steps)


if __name__ == "__main__":
    main()
