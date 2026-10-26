#!/usr/bin/env python3
"""Build the pre-registered H71-1 HGPC-BLIND full-footprint GeoTIFFs.

Frozen rule (knowledge/27 §4): even if holdout gates fail, emit DIRECT from
``H71_blind_hgpc`` (ridge NMS, B=2 against full labels.tif, sapd 3.0, kfrac 0.035).
Zero HGB. Zero Family E. No pixels copied from any prior submission.

    .venv/bin/python scripts/build_h71_candidate.py --verdict-note \"holdout FAIL vs H35; no slot; unscored; not slot-approved\"
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25.experiment import DOMAIN_ERODE  # noqa: E402
from gems25.h71 import H71_NAMES, load_h71_sidecar  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import (  # noqa: E402
    check_file,
    content_id,
    make_filename,
    make_note,
    write_submission,
    zip_single,
)
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402

KFRAC = 0.035
MIN_DIST = 3.0
COLLAR_B2 = 2.0
SLUG = "h71-hgpc-blind-b2-sapd3-k3p5"
DATE = "20261026"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verdict-note", required=True)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    args = ap.parse_args()
    t0 = time.time()
    work, data = work_dir(), data_dir()
    foot = np.load(work / "bands" / "_footprint.npy")
    lab = np.load(work / "bands" / "_labels.npy")
    fi = np.flatnonzero(foot.ravel())
    h71 = load_h71_sidecar(work, foot, fi, static=np.load(work / "static_ABCD.npy", mmap_mode="r"),
                           static_names=json.loads((work / "static_ABCD.npy.names.json").read_text()))
    grid = np.zeros(foot.shape, dtype=np.float32)
    grid.ravel()[fi] = np.asarray(h71[0], dtype=np.float32)  # H71_blind_hgpc
    domain = binary_erosion(foot, iterations=DOMAIN_ERODE)
    k = int(round(KFRAC * int(domain.sum())))
    r = ridge_nms(grid, domain, 1.0)
    far = distance_transform_edt(~lab) > COLLAR_B2
    sc = np.where(r & far & domain, grid, 0.0)
    top = select_top_positive(sc, domain, k)
    dots = score_ordered_dots(grid, top, MIN_DIST)
    pred = np.where(foot, dots.astype(np.float32), np.float32(0.0))
    n_on_cat = int((dots & lab).sum())
    if n_on_cat:
        raise SystemExit(f"{n_on_cat} emitted pixels sit on catalogue traces")
    cid = content_id(pred, foot, lab)
    tmpl = data / "sample_submission.tif"
    out = Path(args.out)
    zname = make_filename(SLUG, DATE, cid, "zeros")
    nname = make_filename(SLUG, DATE, cid, "nan")
    zpath = out / zname
    npath = out / nname
    write_submission(pred, tmpl, zpath, outside="zero")
    write_submission(pred, tmpl, npath, outside="nan")
    zzip = zip_single(zpath)
    zchk = check_file(zpath, tmpl)
    nchk = check_file(npath, tmpl)
    note = make_note("H71-1 HGPC-B", args.verdict_note, cid, scored="unscored")
    receipt = dict(
        built_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        slug=SLUG,
        hypothesis="H71-1 HGPC-BLIND DIRECT gravity-basement polarity, B=2, sapd3.0",
        columns=H71_NAMES,
        kfrac=KFRAC,
        min_dist=MIN_DIST,
        collar_b2_px=COLLAR_B2,
        domain_erode_px=DOMAIN_ERODE,
        positive_pixels=int(dots.sum()),
        content_id=cid,
        note=note,
        seconds=round(time.time() - t0, 1),
        files=dict(zeros=zchk, nan=nchk, zip=str(zzip)),
    )
    (out / f"checks-{zpath.stem}.json").write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps(dict(zeros=str(zpath), nan=str(npath), zip=str(zzip), content_id=cid,
                          positive_pixels=int(dots.sum()), note=note,
                          zeros_ok=zchk["ok_to_upload"], nan_ok=nchk["ok_to_upload"],
                          seconds=receipt["seconds"]), indent=2))


if __name__ == "__main__":
    main()
