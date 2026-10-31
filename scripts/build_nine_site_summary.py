#!/usr/bin/env python3
"""Nine-site executive table (COMPUTED from restored rasters + OWNER-REPORTED scores from the brief).

For each focus site's top file: dots, outside-footprint convention, portal-format hypothesis, catalogue proximity,
max 3-px overlap with any OTHER nine-site top file, and the status verdict. Scores are copied from the brief and
labelled OWNER-REPORTED. Estimated organizer score is NOT ESTIMATED for every file.

    python scripts/build_nine_site_summary.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.paths import data_dir  # noqa: E402
from inventory_submissions import load_dots  # noqa: E402

# site -> (file name stem inside data/, owner-reported score, previously submitted per owner brief)
TOP = {
    "GEMSDOE24": ("gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477, True),
    "GEMSDOE25": ("gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600, True),
    "GEMSDOE27": ("GEMSDOE27__gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449, True),
    "GEMSDOE28": ("GEMSDOE28__gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710, True),
    "GEMSDOE30": ("GEMSDOE30__gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif", 0.2600, True),
    "GEMSDOE31": ("GEMSDOE31__gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif", 0.2708, True),
    "GEMSDOE32": ("GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778, True),
    "GEMSDOE33": ("GEMSDOE33__GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif", 0.2632, True),
    "GEMSDOE36": ("GEMSDOE36__gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", 0.2750, True),
}
OUT = ROOT / "evidence" / "nine_site_summary_2026-10-31.json"


def main() -> int:
    with rasterio.open(data_dir() / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(data_dir() / "labels.tif") as t:
        cat = (t.read(1) == 1) & foot
    dtc = distance_transform_edt(~cat)
    dots, meta = {}, {}
    for site, (name, score, prev) in TOP.items():
        p = data_dir() / "owner_mirrors" / name
        if not p.exists():
            p = data_dir() / "scored" / name
        d, fmt = load_dots(p, foot)
        dots[site] = d
        meta[site] = dict(file=name, owner_score=score, previously_submitted_per_brief=prev, dots=int(d.sum()),
                          outside=fmt["outside"], portal_format_pass_hypothesis=fmt["portal_pass_hypothesis"],
                          within_200m_of_catalogue_pct=round(100 * float((dtc[d] <= 2.0).mean()), 2))
    edt = {s: distance_transform_edt(~d) for s, d in dots.items()}
    for s in TOP:
        others = {o: round(100 * float((edt[o][dots[s]] <= 3.0).mean()), 2) for o in TOP if o != s}
        jac = {o: round(float((dots[s] & dots[o]).sum() / (dots[s] | dots[o]).sum()), 4) for o in TOP if o != s}
        worst = max(others, key=others.get)
        meta[s]["max_within3px_share_of_its_dots_to_another_top_file_pct"] = others[worst]
        meta[s]["nearest_other_site"] = worst
        meta[s]["max_jaccard_to_another_top_file"] = max(jac.values())
        meta[s]["unique_among_nine"] = bool(others[worst] <= 70.0)
        meta[s]["estimated_organizer_score"] = "NOT ESTIMATED"
        blocked = []
        if meta[s]["outside"] != "zero":
            blocked.append("NaN outside footprint (portal rejected NaN per user report)")
        if prev := meta[s]["previously_submitted_per_brief"]:
            blocked.append("already submitted (copying a previous submission is not allowed)")
        if not meta[s]["unique_among_nine"]:
            blocked.append(f"overlaps {worst} ({others[worst]}% of dots within 3 px)")
        meta[s]["ok_to_download_and_submit"] = "NO" if blocked else "YES (gates only; not a score estimate)"
        meta[s]["blocking_reasons"] = blocked
    out = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/build_nine_site_summary.py",
        evidence_class="COMPUTED dots/format/overlap; OWNER-REPORTED scores (brief); organizer receipts: none",
        sites=meta,
    )
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    for s, m in meta.items():
        print(s, m["dots"], m["outside"], m["within_200m_of_catalogue_pct"], m["max_within3px_share_of_its_dots_to_another_top_file_pct"],
              m["nearest_other_site"], m["ok_to_download_and_submit"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
