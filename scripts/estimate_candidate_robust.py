#!/usr/bin/env python3
"""Estimate the H-LC1 candidates under every calibrated truth model, including the ones that FAILED.

The headline estimate comes from the best model (``step_dead+betapdf+r10000``, LOO RMSE 0.0168).  That
model reaches its fit by concentrating truth density at the very top of the detector ranking, which is
exactly the region the candidate is built from - so the estimate is an extrapolation of the most
extrapolative parameter in the model.  This script re-estimates the same candidates under the smooth
links (``exp``, ``power``) that fit the anchors 2.5-2.9x worse, to bracket how much of the headline
number is the betapdf tail rather than the design.

    python scripts/estimate_candidate_robust.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25 import livecal, livecal_cells  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from build_hlc1_final import rows_from_mask  # noqa: E402

N_ZB = 200
NCELL = livecal.N_BINS * N_ZB
ALPHA, BETA = 0.2, 0.8

SPECS = [
    ("evidence/livecal_refit3_2026-10-31.json", "step_dead+betapdf+r10000", "betapdf tail, best fit"),
    ("evidence/livecal_refit3_2026-10-31.json", "step_dead+betapdf+r10000+dzcap12", "betapdf, 1.2 km dead zone"),
    ("evidence/livecal_refit3_linkexp_2026-10-31.json", "step_dead+exp+r1", "smooth exp link (fails G1)"),
    ("evidence/livecal_refit3_linkexp_2026-10-31.json", "step_dead+power+r1", "smooth power link (fails G1)"),
]
ARTEFACTS = [
    ("GEMSDOE32-B2 (owner-reported 0.2778)",
     "data/owner_mirrors/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
    ("GEMSDOE28-h27-4 (0.2708)", None),
]
for f in ("evidence/hlc1_primary_20261031.json", "evidence/hlc1_maximin_20261031.json"):
    r = json.loads((ROOT / f).read_text())
    ARTEFACTS.append((f"{r['slug']} ({r['dots']:,} dots)", f"docs/downloads/{r['file']['name']}"))


def main() -> int:
    t0 = time.time()
    d, w = data_dir(), work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    z = np.load(w / "refdet_z.npy")
    d_cat = distance_transform_edt(~lab)
    code, reps, q = livecal_cells.cell_code(d_cat, foot, lab, z, N_ZB)
    nb = np.bincount(code[code >= 0].ravel(), minlength=NCELL).astype(float)

    models = []
    for path, key, note in SPECS:
        r = json.loads((ROOT / path).read_text())["results"][key]
        theta = np.asarray(r["theta"], float)
        _, wts = livecal_cells.cell_weights(theta, r["model"], reps, q, r["link"],
                                            livecal.MODEL_PARAMS[r["model"]], float(r.get("ratio", np.inf)))
        models.append(dict(key=key, note=note, weights=wts, n_truth=float(r["n_truth"]),
                           loo=float(r["loo_rmse"]),
                           b2_loo=float(r["loo_pred"][10]), lat_loo=float(r["loo_pred"][-1]),
                           g1=bool(abs(r["loo_pred"][10] - 0.2778) <= 0.040)))

    print(f"{'artefact':46s}" + "".join(f"{m['key'].split('+')[1]:>9s}" for m in models) + "   g-shape spread")
    table = {}
    for name, path in ARTEFACTS:
        if path is None:
            continue
        with rasterio.open(ROOT / path) as s:
            arr = np.nan_to_num(s.read(1)) > 0
        row = rows_from_mask(arr, code, foot, lab)
        est = {m["key"]: float(livecal_cells.predict([row], m["weights"], nb, m["n_truth"])[0])
               for m in models}
        table[name] = est
        spread = max(est.values()) - min(est.values())
        print(f"{name:46s}" + "".join(f"{est[m['key']]:9.4f}" for m in models) + f"   {spread:.4f}")

    print("\nmodel            LOO     G1    B2(loo)  lattice(loo, true 0.0904)")
    for m in models:
        print(f"{m['key']:38s} {m['loo']:.4f}  {str(m['g1']):5s}  {m['b2_loo']:.4f}   {m['lat_loo']:.4f}")

    # out-of-family deflation measured on the one unlike anchor (lattice-s5)
    for m in models:
        m["oof_factor"] = 0.0904 / m["lat_loo"]
    prim = [k for k in table if "detector-led" in k][0]
    print("\nOut-of-family deflation (lattice actual/predicted) applied to the primary candidate:")
    for m in models:
        print(f"  {m['key']:38s} raw {table[prim][m['key']]:.4f} x {m['oof_factor']:.3f} = "
              f"{table[prim][m['key']] * m['oof_factor']:.4f}")

    rec = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               script="scripts/estimate_candidate_robust.py",
               models=[{k: v for k, v in m.items() if k != "weights"} for m in models],
               estimates=table, seconds=round(time.time() - t0, 1))
    (ROOT / "evidence" / "hlc1_estimate_robust_2026-10-31.json").write_text(json.dumps(rec, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
