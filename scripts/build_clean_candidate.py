#!/usr/bin/env python3
"""Build the protocol-clean candidate (E5 arm C1, knowledge/56 §6) at full-catalogue scale.

Dots = every footprint pixel that is NOT catalogue and NOT inside the r13 3-px halo (6,514 px), plus the
(K - 6,514) non-catalogue r13-halo pixels with the LOWEST count of other registry halos covering them
(ties broken by a seeded key). K = 21,700. Zeros outside the footprint, 1.0 on dots.

Checked before writing: every registry raster's dot share <= 0.70 (cache), then by the full lane checker.
VERDICT: E5 NEGATIVE (holdout far below random). The file is unique and format-valid and is NOT cleared for a slot.

    python scripts/build_clean_candidate.py
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
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import content_id, make_filename, make_note, write_submission, zip_single  # noqa: E402

K = 21_700
R13 = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
DOCS = ROOT / "docs" / "downloads"
EVID = ROOT / "evidence" / "clean_candidate_2026-10-31.json"


def main() -> int:
    tmpl, labp = data_dir() / "sample_submission.tif", data_dir() / "labels.tif"
    with rasterio.open(tmpl) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(labp) as s:
        cat = (s.read(1) == 1) & foot
    cache = np.load(work_dir() / "registry_halos.npz")
    names = [str(x) for x in cache["names"]]
    packed = cache["packed"]
    n = int(foot.sum())
    halos = [np.unpackbits(packed[i])[:n].astype(bool) for i in range(packed.shape[0])]
    r13i = names.index(R13)
    inr13 = halos[r13i]
    kother = np.zeros(n, np.int32)
    for i, h in enumerate(halos):
        if i != r13i:
            kother += h
    catv = cat[foot]
    free = np.flatnonzero(~inr13 & ~catv)
    halo_c = np.flatnonzero(inr13 & ~catv)
    need = K - free.size
    assert 0 < need <= halo_c.size
    rng = np.random.default_rng(20261031)
    key = kother[halo_c].astype(np.float64) + rng.random(halo_c.size) * 0.5
    pick = halo_c[np.argsort(key, kind="stable")[:need]]
    sel = np.concatenate([free, pick])
    assert sel.size == K and np.unique(sel).size == K
    share = {names[i]: float(halos[i][sel].mean()) for i in range(len(names))}
    worst = max(share.items(), key=lambda kv: kv[1])
    assert worst[1] <= 0.70, worst
    emit = np.zeros(n, bool)
    emit[sel] = True
    pred = np.zeros(foot.shape, np.float32)
    pred[foot] = emit.astype(np.float32)
    assert not (pred[cat] > 0).any()

    cid = content_id(pred, foot, cat)
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    fname = make_filename("h-clean1-protocol-clean-k21700-NOSLOT", date, cid, outside="zero")
    out = DOCS / fname
    write_submission(pred, tmpl, out, outside="zero")
    zpath = zip_single(out)
    note = make_note("h-clean1 E5 NEG", "unique, lane-clean, holdout neg: NO SLOT", cid)
    rec = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        script="scripts/build_clean_candidate.py",
        preregistration="knowledge/56_preregistered_bound_fill_and_repulsion_2026-10-31.md §6",
        status="UNIQUE + FORMAT-VALID + PROTOCOL-CLEAN (cache); E5 HOLDOUT NEGATIVE; NOT cleared for a leaderboard slot",
        file=out.name, zip=zpath.name, sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        content_id=cid, dots=K, lane_free_dots=int(free.size), halo_dots=int(need),
        max_registry_dot_share_cache=round(worst[1], 5), worst_registry_raster=worst[0],
        outside="zeros", inside_values=[0.0, 1.0], note=note, note_chars=len(note),
        okay_to_download_and_submit="Download: only as a unique, format-valid file. Submit: NO (not cleared; E5 holdout far below random)",
        estimated_score="NOT ESTIMATED (holdout DTI 0.004 vs random floor 0.033; organizer score unknown)",
    )
    EVID.write_text(json.dumps(rec, indent=1, allow_nan=False) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
