#!/usr/bin/env python3
"""Fresh pixel-exact audit of the nine focus-site winners (this session).

Reads only pinned mirrors in data/registry_top + data/scored + labels/template.
Scores attached are OWNER-REPORTED claims from registry/top_scorer_sources.json;
every geometric statement is COMPUTED here. Output: evidence/focus_audit_session_2026-10-26.json
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
from gems25.submission import check_file  # noqa: E402

FOCUS = {
    "GEMSDOE24": "g24_d1-5_0.2477.tif",
    "GEMSDOE25": "g25_d2-8_0.2600.tif",
    "GEMSDOE27": "g27_topo-gap-d1-5_0.2449.tif",
    "GEMSDOE28": "g28_h36-1-rung30_0.2710.tif",
    "GEMSDOE30": "g30_d28-poisson_0.2600.tif",
    "GEMSDOE31": "g31_h27-4-solo-d28_0.2708.tif",
    "GEMSDOE32": "g32_h33-2-b2_0.2778.tif",
    "GEMSDOE33": "g33_h33d_0.2632.tif",
    "GEMSDOE36": "g36_anderson-pinn_0.2750.tif",
}
R1_FILE = "g28_h27-4-r1-solo_0.2708.tif"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def mask(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> None:
    d = data_dir()
    top = d / "registry_top"
    src = json.loads((ROOT / "registry/top_scorer_sources.json").read_text())
    by_local = {r["local"]: r for r in src["rasters"]}
    with rasterio.open(d / "labels.tif") as s:
        labels = s.read(1) > 0
    with rasterio.open(d / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    dist_cat = distance_transform_edt(~labels)

    masks, rows = {}, {}
    for site, fname in FOCUS.items():
        p = top / fname
        m = mask(p)
        masks[site] = m
        chk = check_file(p, d / "sample_submission.tif")
        rows[site] = dict(
            file=fname, sha256=sha256(p), pinned_sha256=by_local.get(fname, {}).get("sha256"),
            sha256_matches_pin=bool(sha256(p) == by_local.get(fname, {}).get("sha256")),
            owner_reported_score=by_local.get(fname, {}).get("owner_reported_score"),
            submission_name=by_local.get(fname, {}).get("submission_name_in_brief"),
            dots=int(m.sum()), dots_on_catalogue=int((m & labels).sum()),
            dots_outside_footprint=int((m & ~foot).sum()),
            format_ok=bool(chk["ok_to_upload"]), hard_failures=chk["hard_failures"],
            strict_whole_array_0_1=bool(chk["checks"]["variant_strict_whole_array_no_nan"]["pass_"]),
        )
    r1 = mask(top / R1_FILE)
    d28, b2 = masks["GEMSDOE25"], masks["GEMSDOE32"]
    dist_b2 = distance_transform_edt(~b2)
    identities = dict(
        g25_d28_equals_g30_mask=bool(np.array_equal(d28, masks["GEMSDOE30"])),
        r1_equals_d28_and_edt_gt1=bool(np.array_equal(r1, d28 & (dist_cat > 1))),
        g31_equals_r1_mask=bool(np.array_equal(masks["GEMSDOE31"], r1)),
        b2_equals_d28_and_edt_gt2=bool(np.array_equal(b2, d28 & (dist_cat > 2))),
        g36_superset_b2=bool(not (b2 & ~masks["GEMSDOE36"]).any()),
        g36_extra_dots_vs_b2=int((masks["GEMSDOE36"] & ~b2).sum()),
        d28_to_b2_removed=int((d28 & ~b2).sum()),
        shell_d_le1_removed=int((d28 & (dist_cat <= 1)).sum()),
        shell_1lt_d_le2_removed=int((d28 & (dist_cat > 1) & (dist_cat <= 2)).sum()),
        g27_superset_d15=bool(not (masks["GEMSDOE24"] & ~masks["GEMSDOE27"]).any()),
        g27_extra_vs_d15=int((masks["GEMSDOE27"] & ~masks["GEMSDOE24"]).sum()),
        lattice_note="halo computed with Euclidean EDT<=3, not the Chebyshev dilation above",
    )
    for site in FOCUS:
        m = masks[site]
        rows[site]["share_dots_within_3px_of_b2"] = float((dist_b2[m] <= 3.0).mean()) if m.any() else 0.0
        rows[site]["exact_pixel_overlap_with_b2"] = int((m & b2).sum())

    # Break-even arithmetic (exact DTI algebra, alpha=0.2): tau(D)=0.2D/(1-0.2D) is the
    # credit/FP ratio a marginal pixel must exceed; 0.2*D is the per-pixel credit bar
    # used in knowledge/27. Report both, labelled.
    def tau(dv: float) -> float:
        return 0.2 * dv / (1.0 - 0.2 * dv)

    breakeven = {f"D={dv}": dict(tau_credit_over_fp=tau(dv), per_pixel_credit_bar=0.2 * dv)
                 for dv in (0.2600, 0.2708, 0.2778, 0.3195, 0.4413)}
    out = dict(
        generated_by="scripts/audit_focus_sites_session.py",
        evidence_class="COMPUTED from pinned mirrors; scores OWNER-REPORTED (registry/top_scorer_sources.json); no organizer receipt",
        footprint_px=int(foot.sum()), catalogue_px=int(labels.sum()),
        focus=rows, identities=identities, breakeven=breakeven,
    )
    dest = ROOT / "evidence/focus_audit_session_2026-10-26.json"
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in identities.items()}, indent=1))
    for s, r in rows.items():
        print(s, r["owner_reported_score"], r["dots"], "pin_ok=", r["sha256_matches_pin"], "fmt_ok=", r["format_ok"])
    print("wrote", dest)


if __name__ == "__main__":
    main()
