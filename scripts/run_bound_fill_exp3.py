#!/usr/bin/env python3
"""E3 of knowledge/56 (H-BF1): lane bound-fill construction on the holdout. HOLDOUT-DTI only.

Arms F1 (candidate, lane-compliant by construction), F2 (random halo control), F3 (unconstrained reference,
not lane-compliant), F4 (random floor). Gates G0-G3 as pre-registered. Writes evidence/bound_fill_exp3_2026-10-31.json.

    python scripts/run_bound_fill_exp3.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.holdout import Holdout  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from run_soft_catalogue_prior import pooled, boot, top_k, auc_or_none, sha  # noqa: E402

K = 21_713                                   # lane bound (knowledge/56 §1)
LANE_MAX_SHARE = 0.70
DEV = [(f, s) for s in (140, 141) for f in range(4)]
CONF = [(f, s) for s in (150, 151, 152, 153) for f in range(4)]   # virgin: never used before knowledge/56
R13 = data_dir() / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
R13_PIN = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
OUT = ROOT / "evidence" / "bound_fill_exp3_2026-10-31.json"


def main() -> int:
    t0 = datetime.now(timezone.utc)
    tmpl, labp = data_dir() / "sample_submission.tif", data_dir() / "labels.tif"
    if sha(R13) != R13_PIN:
        raise SystemExit("r13 pin mismatch")
    with rasterio.open(tmpl) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(labp) as s:
        labels = (s.read(1) == 1) & foot
    with rasterio.open(R13) as s:
        r13 = (s.read(1) > 0) & foot
    halo = distance_transform_edt(~r13) <= 3.0
    names = json.loads((work_dir() / "static_ABCD.npy.names.json").read_text())
    static = np.load(work_dir() / "static_ABCD.npy", mmap_mode="r")
    ridge = np.full(foot.shape, -np.inf, np.float32)
    ridge[foot] = np.nan_to_num(np.asarray(static[names.index("A_mag_hg_ridge")], np.float32), nan=-np.inf)
    ho = Holdout(foot, labels)

    arms = ("F1", "F2", "F3", "F4")
    rows = {a: {"dev": [], "conf": []} for a in arms}
    canary = {"dev": [], "conf": []}
    lane_share = {"dev": [], "conf": []}
    for split, draws in (("dev", DEV), ("conf", CONF)):
        for fold, seed in draws:
            d = ho.draw(fold, seed)
            vis = d.visible
            E = foot & ~vis
            Eh = E & ~halo                       # lane-free, not visible: always included
            Hh = E & halo                        # halo, not visible: competes for the remaining budget
            n_eh = int(Eh.sum())
            need = K - n_eh
            assert 0 < need <= int(Hh.sum()), (n_eh, need, int(Hh.sum()))
            share = need / K
            assert share <= LANE_MAX_SHARE, share
            lane_share[split].append(share)
            m = d.quadrant & E
            y = d.hidden_test[m].astype(np.uint8)
            dist = distance_transform_edt(~vis).astype(np.float32)
            canary[split].append(dict(fold=fold, seed=seed, n_pos=int(y.sum()), n_px=int(m.sum()),
                                      auc_ridge=auc_or_none(y, ridge[m]), auc_neg_dist_vis=auc_or_none(y, -dist[m])))
            f1 = Eh | top_k(ridge, Hh, need)
            rng = np.random.default_rng(2000 + 10 * seed + fold)
            pick = rng.choice(np.flatnonzero(Hh.ravel()), need, replace=False)
            f2v = Eh.ravel().copy()
            f2v[pick] = True
            f2 = f2v.reshape(foot.shape)
            f3 = top_k(ridge, E, K)
            rng4 = np.random.default_rng(3000 + 10 * seed + fold)
            f4v = np.zeros(foot.size, bool)
            f4v[rng4.choice(np.flatnonzero(E.ravel()), K, replace=False)] = True
            f4 = f4v.reshape(foot.shape)
            emis = dict(F1=f1, F2=f2, F3=f3, F4=f4)
            for a, e in emis.items():
                assert int(e.sum()) == K, (a, int(e.sum()))
                assert not (e & vis).any(), f"{a} emits on visible catalogue"
                sc = ho.score(d, e)
                rows[a][split].append(dict(fold=fold, seed=seed, tp=float(sc["tp"]), fp=float(sc["fp"]),
                                           fn=float(sc["fn"]), n_truth=int(sc["n_truth"]), dti=float(sc["dti"])))
            print(split, fold, seed, {a: round(rows[a][split][-1]["dti"], 5) for a in arms}, flush=True)

    def paired(a, b, s):
        return dict(diff=pooled(rows[a][s]) - pooled(rows[b][s]), ci95=boot(rows[a][s], rows[b][s]))

    res = {a: {s: dict(pooled_dti=pooled(rows[a][s]), ci95=boot(rows[a][s]),
                       n_truth_total=sum(x["n_truth"] for x in rows[a][s])) for s in ("dev", "conf")} for a in arms}
    diffs = {s: {"F1-F2": paired("F1", "F2", s), "F1-F4": paired("F1", "F4", s), "F1-F3": paired("F1", "F3", s)}
             for s in ("dev", "conf")}
    canary_summary = {}
    for s in ("dev", "conf"):
        for key in ("auc_ridge", "auc_neg_dist_vis"):
            vals = [c[key] for c in canary[s] if c[key] is not None]
            canary_summary[f"{s}.{key}"] = dict(min=min(vals), max=max(vals), n=len(vals))
    g0 = all(v["max"] <= 0.90 for v in canary_summary.values())
    g3 = all(max(lane_share[s]) <= LANE_MAX_SHARE for s in lane_share)

    def gate(s):
        return dict(F1_beats_F2=diffs[s]["F1-F2"]["diff"] > 0 and diffs[s]["F1-F2"]["ci95"][0] > 0,
                    F1_beats_F4=diffs[s]["F1-F4"]["diff"] > 0 and diffs[s]["F1-F4"]["ci95"][0] > 0)

    gd, gc = gate("dev"), gate("conf")
    passed = g0 and g3 and all(gd.values()) and all(gc.values())
    rec = dict(
        generated_utc=t0.isoformat(timespec="seconds"),
        script="scripts/run_bound_fill_exp3.py",
        preregistration="knowledge/56_preregistered_bound_fill_and_repulsion_2026-10-31.md",
        evidence_class="HOLDOUT-DTI (catalogue-gap proxy; not organizer-confirmed)",
        parameters=dict(K=K, lane_max_share=LANE_MAX_SHARE, dev_draws=DEV, confirm_draws=CONF,
                        confirm_seeds=[150, 151, 152, 153], lane_halo_px=3.0, score_layer="A_mag_hg_ridge"),
        inputs=dict(template_sha256=sha(tmpl), labels_sha256=sha(labp), r13_sha256=R13_PIN),
        arms=res, paired_differences=diffs, halo_share_by_split={s: [round(x, 4) for x in lane_share[s][:4]] + ["..."] for s in lane_share},
        leakage_canary=dict(summary=canary_summary, per_draw=canary),
        gates=dict(G0_canary=g0, G3_lane_share_le_70pct=g3, G1_dev=gd, G2_confirm=gc),
        verdict="compliant-file-holdout-signal" if passed else "negative",
        note="A pass allows a file build and the full duplicate/format audit. It clears no file and approves no slot.",
    )
    OUT.write_text(json.dumps(rec, indent=1, allow_nan=False, default=float) + "\n")
    print(json.dumps({k: rec[k] for k in ("verdict", "gates")}, indent=1))
    for a in arms:
        print(a, {s: (round(res[a][s]["pooled_dti"], 5), [round(x, 5) for x in res[a][s]["ci95"]]) for s in ("dev", "conf")})
    for s in ("dev", "conf"):
        for k, v in diffs[s].items():
            print(s, k, round(v["diff"], 5), [round(x, 5) for x in v["ci95"]])
    print("canary", canary_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
