#!/usr/bin/env python3
"""Portal-safety sweep (2026-10-28) over every GeoTIFF in docs/downloads/.

For each file: the shared validator (``gems25.submission.check_file``) against the pinned owner-mirror template,
plus whether any cell is NaN/Inf or outside [0, 1]. A file that fails ``portal_all_cells_finite_in_0_1`` is the
convention that produced the owner-reported portal error "Predicted values must be in range [0, 1]".
This is a local format sweep only. It never uploads, never selects a slot and never clears novelty.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import check_file  # noqa: E402

OUT = ROOT / "evidence" / "portal_safety_sweep_2026-10-28.json"


def main() -> int:
    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        print("template missing; run scripts/restore_data.py --group core")
        return 2
    rows = []
    for p in sorted((ROOT / "docs" / "downloads").glob("*.tif")):
        r = check_file(p, tmpl)
        portal_fail = "portal_all_cells_finite_in_0_1" in r["hard_failures"]
        rows.append(dict(
            file=p.name, sha256=r["sha256"], positive_pixels=r["positive_pixels"],
            portal_safe=not portal_fail,
            other_hard_failures=[h for h in r["hard_failures"] if h != "portal_all_cells_finite_in_0_1"],
        ))
    safe = [x for x in rows if x["portal_safe"]]
    unsafe = [x for x in rows if not x["portal_safe"]]
    receipt = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/audit_portal_safety.py",
        evidence_class="COMPUTED local format sweep; no portal, organizer or score claim",
        total=len(rows), portal_safe=len(safe), portal_rejected_convention=len(unsafe),
        portal_safe_files=[x["file"] for x in safe], rows=rows,
    )
    OUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"tif files: {len(rows)} | portal-safe (no NaN/Inf, all cells in [0,1]): {len(safe)} | "
          f"NaN-outside (portal-rejected convention): {len(unsafe)}")
    print("other hard failures:", sorted({h for x in rows for h in x["other_hard_failures"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
