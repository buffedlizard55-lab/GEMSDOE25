#!/usr/bin/env python3
"""Network-free re-audit of the 9 focus sites from the pinned local mirrors (2026-10-26 session).

Reads ``data/registry_top`` (restored + SHA-256-checked by ``scripts/fetch_top_scorers.py``)
and the cached footprint/labels; recomputes dot counts, catalogue-distance shells, the exact
H19-5 -> D1.5 -> D2.8 -> R1 -> B2 -> G36 pixel identities, and pairwise 3-px dot overlaps among
the nine focus-site exemplars. Scores copied from ``registry/top_scorer_sources.json`` remain
OWNER-REPORTED claims; this script verifies geometry only, never a competition score.

    .venv/bin/python scripts/audit_focus_local.py
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
from gems25.paths import data_dir, work_dir  # noqa: E402

FOCUS = {  # site -> (local file in data/registry_top, owner-reported score from registry/top_scorer_sources.json)
    "GEMSDOE24": ("g24_d1-5_0.2477.tif", 0.2477),
    "GEMSDOE25": ("g25_d2-8_0.2600.tif", 0.2600),
    "GEMSDOE27": ("g27_topo-gap-d1-5_0.2449.tif", 0.2449),
    "GEMSDOE28": ("g28_h36-1-rung30_0.2710.tif", 0.2710),
    "GEMSDOE30": ("g30_d28-poisson_0.2600.tif", 0.2600),
    "GEMSDOE31": ("g31_h27-4-solo-d28_0.2708.tif", 0.2708),
    "GEMSDOE32": ("g32_h33-2-b2_0.2778.tif", 0.2778),
    "GEMSDOE33": ("g33_h33d_0.2632.tif", 0.2632),
    "GEMSDOE36": ("g36_anderson-pinn_0.2750.tif", 0.2750),
}
PARENT = ("g19_h19-5_0.1922.tif", 0.1922)
EXTRA28 = {
    "GEMSDOE28_r1_h27-4": ("g28_h27-4-r1-solo_0.2708.tif", 0.2708),
    "GEMSDOE28_prethin_h32-1": ("g28_h32-1-prethin_0.2649.tif", 0.2649),
    "GEMSDOE28_hfeuler_h38-1": ("g28_h38-1-hf-euler_0.2707.tif", 0.2707),
}


def load_mask(p: Path, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(p) as s:
        arr = s.read(1)
        profile = dict(crs=str(s.crs), shape=(s.height, s.width), transform=tuple(s.transform))
    return (np.isfinite(arr) & (arr > 0) & foot), profile


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    w = work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy") & foot
    dist_cat = distance_transform_edt(~lab)
    top = data_dir() / "registry_top"
    src = {r["local"]: r for r in json.loads((ROOT / "registry" / "top_scorer_sources.json").read_text())["rasters"]}

    masks, rows = {}, {}
    for site, (fname, score) in {**{"19GEMSDOE_parent": PARENT}, **FOCUS, **EXTRA28}.items():
        p = top / fname
        if not p.exists():
            raise SystemExit(f"missing {p}; run scripts/fetch_top_scorers.py")
        got = sha256(p)
        pin = src[fname]["sha256"]
        if got != pin:
            raise SystemExit(f"HASH MISMATCH {fname}: {got} != {pin}")
        m, profile = load_mask(p, foot)
        masks[site] = m
        dc = dist_cat[m]
        rows[site] = dict(
            file=fname, sha256=got, owner_reported_score=score, dots=int(m.sum()),
            on_catalogue=int((m & lab).sum()),
            shells=dict(
                d_le_1px=int((m & (dist_cat <= 1.0) & (dist_cat > 0)).sum()),
                d_1_2px=int((m & (dist_cat > 1.0) & (dist_cat <= 2.0)).sum()),
                d_2_3px=int((m & (dist_cat > 2.0) & (dist_cat <= 3.0)).sum()),
                d_gt_3px=int((m & (dist_cat > 3.0)).sum()),
            ),
            median_dist_cat_px=float(np.median(dc)) if dc.size else None, profile=profile,
            submission_name_in_brief=src[fname]["submission_name_in_brief"],
        )

    d28, b2, g36 = masks["GEMSDOE25"], masks["GEMSDOE32"], masks["GEMSDOE36"]
    r1_a, r1_b = masks["GEMSDOE28_r1_h27-4"], masks["GEMSDOE31"]
    identities = dict(
        g25_d28_mask_equals_g30=bool(np.array_equal(d28, masks["GEMSDOE30"])),
        g28_r1_mask_equals_g31=bool(np.array_equal(r1_a, r1_b)),
        r1_equals_d28_and_distcat_gt_1=bool(np.array_equal(d28 & (dist_cat > 1.0), r1_a)),
        b2_equals_d28_and_distcat_gt_2=bool(np.array_equal(d28 & (dist_cat > 2.0), b2)),
        b2_subset_of_g36=bool(not (b2 & ~g36).any()),
        g36_extra_over_b2=int((g36 & ~b2).sum()),
        d28_subset_of_h19_5=bool(not (d28 & ~masks["19GEMSDOE_parent"]).any()),
        d15_subset_of_h19_5=bool(not (masks["GEMSDOE24"] & ~masks["19GEMSDOE_parent"]).any()),
        g27_minus_d15=int((masks["GEMSDOE27"] & ~masks["GEMSDOE24"]).sum()),
        d15_minus_g27=int((masks["GEMSDOE24"] & ~masks["GEMSDOE27"]).sum()),
        g28_rung30_minus_r1=int((masks["GEMSDOE28"] & ~r1_a).sum()),
        r1_minus_g28_rung30=int((r1_a & ~masks["GEMSDOE28"]).sum()),
        g33_minus_b2=int((masks["GEMSDOE33"] & ~b2).sum()),
        b2_minus_g33=int((b2 & ~masks["GEMSDOE33"]).sum()),
        deleted_d28_to_r1=int((d28 & ~r1_a).sum()),
        deleted_r1_to_b2=int((r1_a & ~b2).sum()),
    )

    # pairwise 3-px overlaps among the 9 focus exemplars (forward share of row dots)
    dil = {}
    for site in FOCUS:
        d = distance_transform_edt(~masks[site])
        dil[site] = d <= 3.0
    overlaps = {}
    for a in FOCUS:
        overlaps[a] = {b: (float((masks[a] & dil[b]).sum() / max(masks[a].sum(), 1)) if a != b else 1.0)
                       for b in FOCUS}

    out = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        generated_by="scripts/audit_focus_local.py (local pinned mirrors only; no network; no DrivenData contact)",
        evidence_class={"geometry": "COMPUTED from SHA-256-verified local bytes",
                        "scores": "OWNER-REPORTED (registry/top_scorer_sources.json); not organizer-confirmed"},
        sites=rows, identities=identities, pairwise_3px_forward_overlap=overlaps,
        ranking_by_owner_reported_score=sorted(FOCUS, key=lambda s: -FOCUS[s][1]),
    )
    dest = ROOT / "evidence" / "focus_audit_local_2026-10-26.json"
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(identities, indent=1))
    for s in out["ranking_by_owner_reported_score"]:
        r = rows[s]
        print(f"{s:12s} score={r['owner_reported_score']:.4f} (OWNER) dots={r['dots']:6d} "
              f"on_cat={r['on_catalogue']} shells={r['shells']}")
    print(f"wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
