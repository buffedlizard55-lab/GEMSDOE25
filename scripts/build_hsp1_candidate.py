#!/usr/bin/env python3
"""Full-footprint file for pre-registered arm A1 (knowledge/54, H-SP1). INSPECTION ONLY - DO NOT PACKAGE.

WARNING: the output is a literal lane duplicate of r13 (99.87% of dots within 3 px). Running this script writes
a TIF into docs/downloads; do not zip, upload or cite it as a candidate.

Run 2026-10-30: experiment 1 FAILED gate G1 (evidence/soft_catalogue_prior_exp1_2026-10-30.json: random dots A4
beat A1 on dev and confirm draws). Per the pre-registration, no lane check is required for a verdict of
negative, but this file is still written so the verifiers can be exercised on a unique, format-valid TIFF.
It is labelled DO NOT SUBMIT in its filename and note and is never a candidate for a slot.

Construction (same as arm A1, visible = the full catalogue, since all catalogue faults are known in the real file):
  score = A_mag_hg_ridge * exp(-d_cat / 10 px) over footprint & ~catalogue, top 21,000 pixels, value 1.0; zeros elsewhere.

    python scripts/build_hsp1_candidate.py
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
from gems25.submission import content_id, make_filename, make_note, write_submission, zip_single  # noqa: E402

K, LAM = 21_000, 10.0
DOCS = ROOT / "docs" / "downloads"
EVID = ROOT / "evidence" / "hsp1_candidate_2026-10-30.json"


def main() -> int:
    tmpl, labp = data_dir() / "sample_submission.tif", data_dir() / "labels.tif"
    with rasterio.open(tmpl) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(labp) as s:
        cat = (s.read(1) == 1) & foot
    names = json.loads((work_dir() / "static_ABCD.npy.names.json").read_text())
    static = np.load(work_dir() / "static_ABCD.npy", mmap_mode="r")
    ridge = np.full(foot.shape, -np.inf, np.float32)
    ridge[foot] = np.nan_to_num(np.asarray(static[names.index("A_mag_hg_ridge")], np.float32), nan=-np.inf)
    dist = distance_transform_edt(~cat).astype(np.float32)
    score = ridge * np.exp(-dist / LAM).astype(np.float32)
    elig = foot & ~cat & np.isfinite(score)
    s = np.where(elig, score, -np.inf).ravel()
    idx = np.argpartition(-s, K)[:K]
    emit = np.zeros(foot.size, bool)
    emit[idx] = True
    emit = emit.reshape(foot.shape) & elig
    n_dots = int(emit.sum())
    assert n_dots == K and not (emit & cat).any()
    pred = emit.astype(np.float32)  # dots = 1.0, everything else 0.0 (inside footprint)

    cid = content_id(pred, foot, cat)
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    fname = make_filename("NOSUBMIT-hsp1-softprior-a1-k21000", date, cid, outside="zero")
    out = DOCS / fname
    write_submission(pred, tmpl, out, outside="zero")
    zpath = zip_single(out)
    note = make_note("NOSUBMIT h82-A1 failed G1 (random beat it)", "research only, do not submit", cid)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    rec = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/build_hsp1_candidate.py",
        status="INSPECTION ONLY - DO NOT SUBMIT (pre-registered gate G1 failed; see knowledge/54 and evidence/soft_catalogue_prior_exp1_2026-10-30.json)",
        file=out.name, zip=zpath.name, sha256=sha, content_id=cid, dots=n_dots, note=note,
        note_chars=len(note), outside="zeros", inside_values=[0.0, 1.0],
        okay_to_download_and_submit=False, estimated_score="NOT ESTIMATED",
    )
    EVID.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
