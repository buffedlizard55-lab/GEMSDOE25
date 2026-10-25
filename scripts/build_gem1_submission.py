#!/usr/bin/env python3
"""Build the GEM-1 unique submission GeoTIFF (blind-magnetics surface).

Pipeline (fully determined, no random training):
  1. Surface GEM-1 = pct_norm(|grad RTP|) x (1 - pct_norm(relief)) over the full footprint.
     Rationale (knowledge/15): concealed faults juxtapose magnetically different blocks
     without breaking the surface -> strong RTP edge where relief is low. Targets faults
     missing from the USGS/INGENIOUS catalogue because they lack a Quaternary scarp.
  2. Emission: Hessian ridge NMS -> drop catalogue pixels -> score-ordered Poisson-disk
     dots (H26-0, holdout-validated +0.0037 vs score-blind dotting at equal N) keeping the
     highest-scoring pixel of each neighbourhood, budget kfrac = 0.0245 (same as the
     validated holdout cell).
  3. Write single-band float32 GeoTIFF with the pinned template's CRS/EPSG:32611,
     shape (3730, 3292), 100 m geotransform; NaN outside the footprint; values in [0,1]
     inside; 0 NaN inside the footprint. Verified with src/gems25/submission.py::check_file.
  4. Unique content-addressed filename + SHA-256 receipt + short DrivenData note.

This is a HOLDOUT-DTI number (proxy), not a competition score:
  screen (draws 0,1) +0.0180 DTI vs same-run control, 4/4 folds, worst +0.0107, AUC 0.526;
  confirmation (draws 2,3) +0.0216, 4/4 folds, worst +0.0102, AUC 0.561 (evidence/gem_validation/).
  It does NOT beat the frozen 0.152003389 comparator (which itself does not reproduce here,
  IR-25-COMPARATOR-DRIFT), so it is NOT slot-approved. OK to download for format/reproducibility
  testing; NOT authorized for a weekly scoring slot on current evidence.

Run: .venv/bin/python scripts/build_gem1_submission.py [--kfrac 0.0245] [--slug gem1-blind-magnetics]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25.experiment import load_context  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import (check_file, content_id, make_filename, make_note,  # noqa: E402
                               write_submission)
from validate_gem_candidate import surface_gem1  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kfrac", type=float, default=0.0245)
    ap.add_argument("--slug", default="gem1-blind-magnetics")
    ap.add_argument("--tag", default="GEM-1")
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    a = ap.parse_args()
    t0 = time.time()

    work = work_dir()
    ctx = load_context(work)
    foot = ctx.foot
    lab = ctx.labels

    surface = surface_gem1(foot, work / "bands")
    H, W = foot.shape
    k = int(round(a.kfrac * int(foot.sum())))

    # score-ordered Poisson-disk dots (H26-0), catalogue pixels excluded
    from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive

    g = np.where(foot & np.isfinite(surface), surface, 0.0).astype(np.float32)
    r = ridge_nms(g, foot, 1.0)
    sc = np.where(r & ~lab, g, 0.0)
    top = select_top_positive(sc, foot, k)
    dots = score_ordered_dots(g, top, 1.5)
    assert not (dots & lab).any(), "emission on a catalogue pixel"
    pred = np.where(dots, 1.0, 0.0).astype(np.float32)

    tmpl = data_dir() / "sample_submission.tif"
    date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    cid = content_id(pred, foot, lab)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fname = make_filename(a.slug, date, cid, "nan")
    tif = write_submission(pred, tmpl, out / fname, outside="nan")
    chk = check_file(tif, tmpl)

    summary = "holdout-validated, unscored, no slot"
    note = make_note(a.tag, summary, cid, limit=120)
    rec = dict(file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size,
               sha256=chk["sha256"], content_id=cid, positive_pixels=int(dots.sum()),
               format_ok=chk["ok_to_upload"], checks=chk["checks"], note=note,
               build=dict(base="GEM-1 unsupervised surface", kfrac=a.kfrac, variant="score_ordered_dots",
                          seconds=round(time.time() - t0), utc=dt.datetime.now(dt.timezone.utc).isoformat()),
               status="format-validated; holdout-validated vs same-run control; NOT slot-approved; NOT a competition score",
               holdout_dti={"screen_draws_0_1": 0.036657, "screen_gain_vs_control": 0.018021,
                            "confirmation_draws_2_3": 0.042195, "confirmation_gain_vs_control": 0.021601,
                            "auc": 0.561},
               lane={"worst_registry_spearman_abs": 0.0717, "max_dot_overlap_substantive_raster": 0.4816,
                     "lattice_raster_overlap_100pct": "degenerate full-footprint lattice, flagged as irregularity"},
               limitation="holdout is a catalogue-gap proxy, not new-fault truth or a live score; "
                          "does not beat the frozen 0.152003389 comparator; no DrivenData access was used")
    (out / f"checks-{tif.stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("file", "bytes", "sha256", "content_id", "positive_pixels",
                                          "format_ok", "note")}, indent=1))
    print("hard failures:", chk["hard_failures"])


if __name__ == "__main__":
    main()
