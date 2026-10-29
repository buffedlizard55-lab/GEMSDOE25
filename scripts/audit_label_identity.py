#!/usr/bin/env python3
"""Label-identity audit (2026-10-29): are the restored label, catalogue and sample-submission rasters distinct?

Reads the restored competition-input mirrors in ``data/`` and writes
``evidence/label_identity_audit_2026-10-29.json``. Computed from bytes only; nothing is fetched and no
organizer page is contacted.

Why this matters: ``labels.tif`` and ``existing_faults.tif`` are documented as byte-identical
(knowledge/08), and ``sample_submission.tif`` is documented as having its 60,988 ones on the labelled
faults. If the organizer's inputs really were identical, the known catalogue and the hidden target would
coincide and every hide-and-recover holdout built on them would be suspect. If they are a mirror copy
error, the holdout is fine. This script records the facts; it cannot decide between the two.
The organizer page is login-walled, so a human must check it (IR-29-LABELS-EQUALS-CATALOGUE).

    python scripts/audit_label_identity.py
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

OUT = ROOT / "evidence" / "label_identity_audit_2026-10-29.json"
FILES = {
    "labels": data_dir() / "labels.tif",
    "existing_faults": data_dir() / "existing_faults.tif",
    "sample_submission": data_dir() / "sample_submission.tif",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    missing = [k for k, p in FILES.items() if not p.exists()]
    if missing:
        print(f"not restored: {missing}; run scripts/restore_data.py --group core", file=sys.stderr)
        return 2
    arrays, meta = {}, {}
    for k, p in FILES.items():
        with rasterio.open(p) as ds:
            a = ds.read(1)
            meta[k] = {
                "file": p.name,
                "sha256": sha256(p),
                "dtype": ds.dtypes[0],
                "shape": list(a.shape),
                "crs": str(ds.crs),
                "nodata": ds.nodata,
                "transform": list(ds.transform)[:6],
            }
        arrays[k] = a
    lab, cat, sub = arrays["labels"], arrays["existing_faults"], arrays["sample_submission"]
    finite_sub = np.isfinite(sub)
    checks = {
        "labels_bytes_identical_to_existing_faults": meta["labels"]["sha256"] == meta["existing_faults"]["sha256"],
        "labels_array_equal_existing_faults": bool(np.array_equal(lab, cat)),
        "sample_ones_equal_labels_ones": bool(np.array_equal((sub == 1) & finite_sub, lab == 1)),
        "labels_positive_count": int((lab == 1).sum()),
        "existing_faults_positive_count": int((cat == 1).sum()),
        "sample_ones_count": int(((sub == 1) & finite_sub).sum()),
        "sample_nonfinite_count": int((~finite_sub).sum()),
        "sample_finite_values": sorted(float(v) for v in np.unique(sub[finite_sub])),
        "labels_value_counts": {str(int(v)): int(c) for v, c in zip(*np.unique(lab, return_counts=True))},
    }
    receipt = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "scripts/audit_label_identity.py",
        "evidence_class": "COMPUTED on restored owner-mirror bytes; organizer identity NOT verified",
        "issue": "IR-29-LABELS-EQUALS-CATALOGUE",
        "inputs": meta,
        "checks": checks,
        "interpretation": (
            "Three inputs that a competition would normally keep distinct (catalogue, target labels, "
            "sample submission) coincide. Either the owner mirror copied one file over others, or the "
            "organizer inputs really coincide. A human must read the organizer data page to decide. "
            "Until then, no holdout or score built on these inputs is treated as certified."
        ),
    }
    OUT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(checks, indent=2))
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
