#!/usr/bin/env python3
"""Design sweep and maximin choice — guard against the optimizer's curse.

The marginal-gain design built by ``scripts/build_hlc1_candidate.py`` is chosen *against* one fitted
truth model, so its predicted DTI (0.570) is an in-sample optimum of that model, not a prediction:
the model was fitted with a restricted parametric family and a design that maximises it inherits every
fitting error.  This script scores a family of simple, *model-independent* designs - rank by the
out-of-fold detector, exclude a catalogue buffer, Poisson-disc thin at the spacing the successful
family uses - under two calibrated truth models (dead-zone radius 1.2 km and 3.7 km) and picks the
design that maximises the WORST predicted DTI over both.  No design here is optimised against either
model: the only free knobs are the buffer and the budget, and both are swept on a coarse grid.

    python scripts/sweep_hlc1_designs.py     # writes evidence/hlc1_design_sweep_2026-10-31.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25 import livecal, livecal_cells  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402

N_ZB = 200
BUFFERS = (2.0, 4.0, 8.0, 12.0, 20.0, 30.5)
BUDGETS = (20_860, 30_000, 37_654, 44_090)
MIN_DIST = 2.8
CAL = {
    "dz37": ("evidence/livecal_refit3_2026-10-31.json", "step_dead+betapdf+r10000"),
    "dz12": ("evidence/livecal_refit3_2026-10-31.json", "step_dead+betapdf+r10000+dzcap12"),
}


def rows_from_mask(mask, code, foot, lab):
    p = (mask & foot & ~lab).astype(np.float32)
    m, u = livecal.emission_fields(p)
    c = code.ravel()
    ok = c >= 0
    idx = c[ok].astype(np.int64)
    ncell = livecal.N_BINS * N_ZB
    return dict(ta=np.bincount(idx, weights=m.ravel()[ok], minlength=ncell),
                ua=np.bincount(idx, weights=u.ravel()[ok], minlength=ncell),
                ne=np.bincount(idx, weights=p.ravel()[ok], minlength=ncell),
                mass=float(p.sum()), positives=int((p > 0).sum()))


def main() -> int:
    t0 = time.time()
    d, w = data_dir(), work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    z = np.load(w / "refdet_z.npy")
    d_cat = distance_transform_edt(~lab)
    code, reps, q = livecal_cells.cell_code(d_cat, foot, lab, z, N_ZB)
    nb = np.bincount(code[code >= 0].ravel(), minlength=livecal.N_BINS * N_ZB).astype(float)

    models = {}
    for tag, (path, key) in CAL.items():
        cal = json.loads((ROOT / path).read_text())
        r = cal["results"][key]
        models[tag] = dict(theta=np.asarray(r["theta"], float), model=r["model"], link=r["link"],
                           ratio=float(r.get("ratio", np.inf)), n_truth=float(r["n_truth"]),
                           n_shape=livecal.MODEL_PARAMS[r["model"]], loo_rmse=r["loo_rmse"],
                           dead_zone_px=float(r["theta"][2]), key=key)
        print(f"model {tag}: {key}  N={models[tag]['n_truth']:.0f}  dead zone "
              f"{models[tag]['dead_zone_px']:.1f} px  loo={models[tag]['loo_rmse']:.4f}")

    # reference: the owner-reported best file, scored by the same models (in-sample, for scale only)
    import rasterio
    with rasterio.open(d / "owner_mirrors" / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") as s:
        b2 = np.nan_to_num(s.read(1)) > 0
    ref = {}
    for tag, m in models.items():
        _, wts = livecal_cells.cell_weights(m["theta"], m["model"], reps, q, m["link"], m["n_shape"], m["ratio"])
        ref[tag] = float(livecal_cells.predict([rows_from_mask(b2, code, foot, lab)], wts, nb, m["n_truth"])[0])
    print("B2 predicted (in-sample anchor check):", {k: round(v, 4) for k, v in ref.items()},
          " owner-reported 0.2778")

    out = []
    for buf in BUFFERS:
        elig = foot & ~lab & (d_cat > buf)
        mask, vals = livecal.greedy_disjoint(z.astype(np.float64), elig, min_dist=MIN_DIST,
                                            max_keep=max(BUDGETS))
        picks = np.flatnonzero(mask.ravel())
        # greedy_disjoint returns a mask only: order the picks by detector value before truncating,
        # otherwise picks[:K] is the northernmost K dots, not the best K.
        picks = picks[np.argsort(-z.ravel()[picks], kind="stable")]
        print(f"buffer {buf:>5.1f} px: {picks.size:,} dots available", flush=True)
        for K in BUDGETS:
            if K > picks.size:
                continue
            sub = np.zeros(foot.size, bool)
            sub[picks[:K]] = True
            sub = sub.reshape(foot.shape)
            row = rows_from_mask(sub, code, foot, lab)
            preds = {}
            for tag, m in models.items():
                _, wts = livecal_cells.cell_weights(m["theta"], m["model"], reps, q, m["link"],
                                                    m["n_shape"], m["ratio"])
                preds[tag] = float(livecal_cells.predict([row], wts, nb, m["n_truth"])[0])
            out.append(dict(buffer_px=buf, budget=K, dots=int(row["positives"]), **{f"dti_{k}": v for k, v in preds.items()},
                            dti_min=min(preds.values()), dti_mean=float(np.mean(list(preds.values()))),
                            median_d_cat_px=float(np.median(d_cat[sub]))))
            print(f"   K={K:>7,}  dti_dz37={preds['dz37']:.4f}  dti_dz12={preds['dz12']:.4f}  "
                  f"min={min(preds.values()):.4f}  median d_cat={out[-1]['median_d_cat_px']:.1f}", flush=True)

    best = max(out, key=lambda r: (r["dti_min"], r["dti_mean"]))
    rec = dict(generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               script="scripts/sweep_hlc1_designs.py",
               why=("the model-optimal design is an in-sample optimum of one fitted model and is not "
                    "credible; these designs are model-independent (detector rank + buffer + spacing)"),
               models={k: {kk: (vv if not isinstance(vv, np.ndarray) else vv.tolist()) for kk, vv in v.items()}
                       for k, v in models.items()},
               b2_reference_in_sample=ref,
               sweep=out, maximin_choice=best,
               evidence_class="COMPUTED; every DTI here is a MODEL ESTIMATE on OWNER-REPORTED anchors",
               seconds=round(time.time() - t0, 1))
    (ROOT / "evidence" / "hlc1_design_sweep_2026-10-31.json").write_text(json.dumps(rec, indent=1) + "\n")
    print("\nmaximin choice:", best)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
