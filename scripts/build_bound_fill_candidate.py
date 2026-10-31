#!/usr/bin/env python3
"""Build the single pre-registered candidate of knowledge/56 (arm F1, H-BF1) at full-catalogue scale.

F1 = every footprint pixel that is NOT catalogue and NOT inside the r13 3-px halo (lane-free: 6,514 px), plus the
top-ridge (A_mag_hg_ridge) non-catalogue halo pixels up to K = 21,700 total dots (below the 21,713 lane bound).
Output: zeros outside the footprint, 1.0 on dots, 0.0 elsewhere inside (portal-safe form; NaN outside is rejected).

VERDICT CARRIED IN THE FILE NAME AND NOTE: experiment E3 (evidence/bound_fill_exp3_2026-10-31.json) is NEGATIVE.
This file is unique and format-valid, but it is NOT cleared for a leaderboard slot.

    python scripts/build_bound_fill_candidate.py
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

K = 21_700
DOCS = ROOT / "docs" / "downloads"
EVID = ROOT / "evidence" / "bound_fill_candidate_2026-10-31.json"
R13 = data_dir() / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def main() -> int:
    tmpl, labp = data_dir() / "sample_submission.tif", data_dir() / "labels.tif"
    with rasterio.open(tmpl) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(labp) as s:
        cat = (s.read(1) == 1) & foot
    with rasterio.open(R13) as s:
        r13 = (s.read(1) > 0) & foot
    halo = distance_transform_edt(~r13) <= 3.0
    names = json.loads((work_dir() / "static_ABCD.npy.names.json").read_text())
    static = np.load(work_dir() / "static_ABCD.npy", mmap_mode="r")
    ridge = np.full(foot.shape, -np.inf, np.float32)
    ridge[foot] = np.nan_to_num(np.asarray(static[names.index("A_mag_hg_ridge")], np.float32), nan=-np.inf)

    free = foot & ~cat & ~halo
    halo_el = foot & ~cat & halo
    n_free = int(free.sum())
    need = K - n_free
    assert need > 0 and need <= int(halo_el.sum())
    s = np.where(halo_el & np.isfinite(ridge), ridge, -np.inf).ravel()
    idx = np.argpartition(-s, need)[:need]
    assert np.isfinite(s[idx]).all()
    emit = free.ravel().copy()
    emit[idx] = True
    emit = emit.reshape(foot.shape)
    assert int(emit.sum()) == K and not (emit & cat).any() and not (emit & ~foot).any()
    share_in_halo = float((emit & halo).sum() / K)
    assert share_in_halo <= 0.70, share_in_halo
    pred = emit.astype(np.float32)

    cid = content_id(pred, foot, cat)
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    fname = make_filename("h-bf1-lane-bound-fill-k21700-NOSLOT", date, cid, outside="zero")
    out = DOCS / fname
    write_submission(pred, tmpl, out, outside="zero")
    zpath = zip_single(out)
    note = make_note("h-bf1 E3 NEG", "unique, lane-ok, holdout neg: NO SLOT", cid)
    rec = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/build_bound_fill_candidate.py",
        preregistration="knowledge/56_preregistered_bound_fill_and_repulsion_2026-10-31.md",
        status="UNIQUE + FORMAT-VALID; holdout experiment E3 NEGATIVE; NOT cleared for a leaderboard slot",
        file=out.name, zip=zpath.name, sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        content_id=cid, dots=K, lane_free_dots=n_free, halo_dots=need, halo_share=round(share_in_halo, 5),
        outside="zeros", inside_values=[0.0, 1.0], note=note, note_chars=len(note),
        okay_to_download_and_submit="NO - not cleared (see knowledge/56 and the executive summary)",
        estimated_score="NOT ESTIMATED (holdout DTI at random floor or below; not organizer-confirmed)",
    )
    EVID.write_text(json.dumps(rec, indent=1, allow_nan=False) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
