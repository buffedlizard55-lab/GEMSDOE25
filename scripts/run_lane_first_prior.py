#!/usr/bin/env python3
"""Experiment 2 (pre-registration knowledge/55, H-LF1): lane-first construction on the holdout.

Emission is restricted to E = footprint & ~visible & ~r13_halo(3 px). Arms L0-L4 as in knowledge/55 §3.
Writes evidence/lane_first_exp2_2026-10-30.json. HOLDOUT-DTI only.

    python scripts/run_lane_first_prior.py
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
from run_soft_catalogue_prior import DEV, CONF, LAM, boot, pooled, sha, top_k, auc_or_none  # noqa: E402

K = 6_000
R13 = data_dir() / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
R13_PIN = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
OUT = ROOT / "evidence" / "lane_first_exp2_2026-10-30.json"


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
        r13 = s.read(1)
    r13_dots = (r13 > 0) & foot
    halo = distance_transform_edt(~r13_dots) <= 3.0
    names = json.loads((work_dir() / "static_ABCD.npy.names.json").read_text())
    static = np.load(work_dir() / "static_ABCD.npy", mmap_mode="r")
    ridge = np.full(foot.shape, -np.inf, np.float32)
    ridge[foot] = np.nan_to_num(np.asarray(static[names.index("A_mag_hg_ridge")], np.float32), nan=-np.inf)
    ho = Holdout(foot, labels)

    arms = ("L0", "L1", "L2", "L3", "L4")
    rows = {a: {"dev": [], "conf": []} for a in arms}
    canary = {"dev": [], "conf": []}
    min_elig = {"dev": None, "conf": None}
    for split, draws in (("dev", DEV), ("conf", CONF)):
        for fold, seed in draws:
            d = ho.draw(fold, seed)
            vis = d.visible
            E = foot & ~vis & ~halo
            dist = distance_transform_edt(~vis).astype(np.float32)
            n_e = int(E.sum())
            min_elig[split] = n_e if min_elig[split] is None else min(min_elig[split], n_e)
            assert n_e >= K, n_e
            m = d.quadrant & E
            y = d.hidden_test[m].astype(np.uint8)
            canary[split].append({"fold": fold, "seed": seed, "n_pos": int(y.sum()), "n_px": int(m.sum()),
                                  "auc_ridge": auc_or_none(y, ridge[m]),
                                  "auc_neg_dist_vis": auc_or_none(y, -dist[m])})
            prior = np.exp(-dist / LAM).astype(np.float32)
            anti = np.exp(np.minimum(dist / LAM, 60.0)).astype(np.float32)
            emis = {
                "L0": top_k(ridge, E, K),
                "L1": top_k(ridge * prior, E, K),
                "L2": top_k(ridge, E & (dist > 2.0), K),
                "L3": top_k(ridge * anti, E, K),
            }
            rng = np.random.default_rng(1000 + 10 * seed + fold)
            pool = np.flatnonzero(E.ravel())
            rnd = np.zeros(foot.size, bool)
            rnd[rng.choice(pool, K, replace=False)] = True
            emis["L4"] = rnd.reshape(foot.shape)
            for a, e in emis.items():
                assert int(e.sum()) == K, (a, int(e.sum()))
                assert not (e & vis).any() and not (e & halo).any(), f"{a} violates lane/catalogue mask"
                sc = ho.score(d, e)
                rows[a][split].append(dict(fold=fold, seed=seed, tp=float(sc["tp"]), fp=float(sc["fp"]),
                                           fn=float(sc["fn"]), n_truth=int(sc["n_truth"]), dti=float(sc["dti"])))

    res = {a: {s: dict(pooled_dti=pooled(rows[a][s]), ci95=boot(rows[a][s]),
                       n_truth_total=sum(x["n_truth"] for x in rows[a][s]),
                       per_draw_dti=[round(x["dti"], 6) for x in rows[a][s]]) for s in ("dev", "conf")} for a in arms}

    def paired(a, b, s):
        return dict(diff=pooled(rows[a][s]) - pooled(rows[b][s]), ci95=boot(rows[a][s], rows[b][s]))

    diffs = {s: {f"L1-{b}": paired("L1", b, s) for b in ("L0", "L2", "L4", "L3")} for s in ("dev", "conf")}
    canary_summary = {}
    for s in ("dev", "conf"):
        for key in ("auc_ridge", "auc_neg_dist_vis"):
            vals = [c[key] for c in canary[s] if c[key] is not None]
            canary_summary[f"{s}.{key}"] = dict(min=min(vals), max=max(vals), n=len(vals))
    g0 = all(v["max"] <= 0.90 for v in canary_summary.values())

    def gate(s):
        dd = diffs[s]
        return dict(L1_beats_L0=dd["L1-L0"]["diff"] > 0 and dd["L1-L0"]["ci95"][0] > 0,
                    L1_beats_L2=dd["L1-L2"]["diff"] > 0 and dd["L1-L2"]["ci95"][0] > 0,
                    L1_beats_L4=dd["L1-L4"]["diff"] > 0 and dd["L1-L4"]["ci95"][0] > 0,
                    L1_above_L3=dd["L1-L3"]["diff"] > 0)

    gd, gc = gate("dev"), gate("conf")
    passed = g0 and all(gd.values()) and all(gc.values())
    rec = dict(
        generated_utc=t0.isoformat(timespec="seconds"),
        script="scripts/run_lane_first_prior.py",
        preregistration="knowledge/55_preregistered_lane_first_2026-10-30.md",
        evidence_class="HOLDOUT-DTI (catalogue-gap proxy; not organizer-confirmed)",
        parameters=dict(K=K, lam_px=LAM, dev_draws=DEV, confirm_draws=CONF, lane_halo_px=3.0),
        inputs=dict(template_sha256=sha(tmpl), labels_sha256=sha(labp), r13_sha256=R13_PIN),
        min_eligible_pixels=min_elig,
        arms=res, paired_differences=diffs,
        leakage_canary=dict(summary=canary_summary, per_draw=canary),
        gates=dict(G0_canary=g0, G1_dev=gd, G2_confirm=gc),
        verdict="promote-to-file-build" if passed else "negative",
        note="A pass permits building a file for the full lane and verifier loop only. It clears nothing and approves no slot.",
    )
    OUT.write_text(json.dumps(rec, indent=1, allow_nan=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("verdict", "gates", "min_eligible_pixels")}, indent=1))
    for a in arms:
        print(a, {s: round(res[a][s]["pooled_dti"], 5) for s in ("dev", "conf")})
    for s in ("dev", "conf"):
        for k, v in diffs[s].items():
            print(s, k, round(v["diff"], 5), [round(x, 5) for x in v["ci95"]])
    print("canary", canary_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
