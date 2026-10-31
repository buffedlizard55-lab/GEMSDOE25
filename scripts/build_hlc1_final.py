#!/usr/bin/env python3
"""Build the H-LC1 submission candidate files (detector-led, model-checked).

Recipe (model-independent - chosen BEFORE any estimate was computed):
    score  = out-of-fold GBM detector on the 69-feature stack (OOF AUC 0.6702 on visible labels)
    buffer = exclude every pixel within 2 px (200 m) of the published USGS/INGENIOUS catalogue
    thin   = Poisson-disc at 2.8 px (280 m) so no dot wastes credit already banked by a neighbour
    budget = 37,654 dots - exactly the budget of the owner-reported best file (0.2778)

The buffer/thin/budget triple is the operating point that is already attached to a live score in the
owner-reported record; only the detector is new, which is what makes the file unique without making
it an unanchored extrapolation.  The truth model (evidence/livecal_refit3_2026-10-31.json) then
estimates its score.  The model's own optimum (buffer 12 px, 44,090 dots) is written as a second,
research-only file because its estimate (0.50-0.53) sits far outside the support of the 17 live
anchors and is an in-sample optimum of the fitted model.

    python scripts/build_hlc1_final.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25 import livecal, livecal_cells, submission  # noqa: E402
from gems25.paths import work_dir  # noqa: E402

N_ZB = 200


def rows_from_mask(mask, code, foot, lab):
    """One artefact row: truth-weighted / kernel-max / kernel-mean emissions binned by cell."""
    p = (mask & foot & ~lab).astype(np.float32)
    m, u = livecal.emission_fields(p)
    c = code.ravel()
    ok = c >= 0
    idx = c[ok].astype(np.int64)
    return dict(ta=np.bincount(idx, weights=m.ravel()[ok], minlength=livecal.N_BINS * N_ZB),
                ua=np.bincount(idx, weights=u.ravel()[ok], minlength=livecal.N_BINS * N_ZB),
                ne=np.bincount(idx, weights=p.ravel()[ok], minlength=livecal.N_BINS * N_ZB),
                mass=float(p.sum()), positives=int((p > 0).sum()))

DATE = "20261031"
OUT_DIR = ROOT / "docs" / "downloads"
ALPHA, BETA = 0.2, 0.8

DESIGNS = [
    dict(slug="hlc1-detector-led-b2-k37654", buffer=2.0, budget=37_654, min_dist=2.8,
         primary=True,
         rationale=("identical buffer/thinning/budget to the owner-reported best file (0.2778); "
                    "only the detector is new (out-of-fold GBM vs the H19-5 multi-line detector)")),
    dict(slug="hlc1-maximin-b12-k44090", buffer=12.0, budget=44_090, min_dist=2.8,
         primary=False,
         rationale=("maximin over the two calibrated truth models; higher model estimate but no "
                    "live anchor at this buffer or budget - research only")),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    t0 = time.time()
    w = work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    z = np.load(w / "refdet_z.npy").astype(np.float64)
    d_cat = distance_transform_edt(~lab)
    code, reps, q = livecal_cells.cell_code(d_cat, foot, lab, z, N_ZB)
    nb = np.bincount(code[code >= 0].ravel(), minlength=livecal.N_BINS * N_ZB).astype(float)

    cal = json.loads((ROOT / "evidence" / "livecal_refit3_2026-10-31.json").read_text())
    models = {}
    for key in ("step_dead+betapdf+r10000", "step_dead+betapdf+r10000+dzcap12"):
        r = cal["results"][key]
        theta = np.asarray(r["theta"], float)
        _, wts = livecal_cells.cell_weights(theta, r["model"], reps, q, r["link"],
                                            livecal.MODEL_PARAMS[r["model"]], float(r.get("ratio", np.inf)))
        models[key] = dict(theta=theta.tolist(), n_truth=float(r["n_truth"]), weights=wts,
                           loo_rmse=r["loo_rmse"], dead_zone_px=float(theta[2]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    made = []
    for d in DESIGNS:
        elig = foot & ~lab & (d_cat > d["buffer"])
        mask, _ = livecal.greedy_disjoint(z, elig, min_dist=d["min_dist"], max_keep=d["budget"])
        arr = np.where(foot, mask.astype("float32"), np.float32("nan"))
        pos = int((arr[foot] > 0).sum())
        row = rows_from_mask(arr > 0, code, foot, lab)
        est = {k: float(livecal_cells.predict([row], m["weights"], nb, m["n_truth"])[0])
               for k, m in models.items()}

        cid = submission.content_id(arr, foot, lab)
        name = submission.make_filename(d["slug"], f"{DATE}T{time.strftime('%H%M%SZ', time.gmtime())}", cid, "zeros")
        tif = OUT_DIR / name
        submission.write_submission(arr, ROOT / "data" / "sample_submission.tif", tif, outside="zero")
        zip_path = tif.with_suffix(".zip")
        subprocess.run(["zip", "-q", "-j", "-9", str(zip_path), str(tif)], check=True, cwd=OUT_DIR)
        note = submission.make_note(
            "H-LC1",
            f"out-of-fold GBM detector, {d['buffer']:g}px catalogue buffer, "
            f"{d['min_dist']}px spacing, {pos:,} dots", cid)
        rec = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   script="scripts/build_hlc1_final.py", slug=d["slug"], primary=bool(d["primary"]),
                   recipe=dict(detector="out-of-fold GBM on the 69-feature cached stack (refdet_z.npy)",
                               buffer_px=d["buffer"], min_dist_px=d["min_dist"], budget=d["budget"],
                               rationale=d["rationale"]),
                   dots=pos, median_d_cat_px=float(np.median(d_cat[arr > 0])),
                   model_estimate=est,
                   loo_rmse={k: m["loo_rmse"] for k, m in models.items()},
                   file=dict(name=name, sha256=sha256_file(tif), bytes=tif.stat().st_size,
                             zip=zip_path.name, zip_bytes=zip_path.stat().st_size),
                   note=note,
                   evidence_class=("COMPUTED; the model estimate is a MODEL ESTIMATE, not a score and "
                                   "not ORGANIZER-CONFIRMED"))
        (ROOT / "evidence" / f"hlc1_{'primary' if d['primary'] else 'maximin'}_{DATE}.json").write_text(
            json.dumps(rec, indent=1) + "\n")
        made.append(rec)
        print(f"\n{'PRIMARY' if d['primary'] else 'RESEARCH'} {name}\n  {pos:,} dots  "
              f"median d_cat {rec['median_d_cat_px']:.1f} px  sha {rec['file']['sha256'][:16]}\n"
              f"  model estimate: " + "  ".join(f"{k.split('+')[-1]} {v:.4f}" for k, v in est.items()) +
              f"\n  note: {note}")

    all_rec = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), designs=made,
                   seconds=round(time.time() - t0, 1))
    print(json.dumps(all_rec, indent=1))
    print("\nnext: audit_lane_duplicates.py then verify_candidate_independent.py on the primary TIF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
