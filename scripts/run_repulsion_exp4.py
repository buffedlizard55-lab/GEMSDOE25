#!/usr/bin/env python3
"""E4 of knowledge/56 (H-REP1): is the B2 effect catalogue repulsion or plain thinning? HOLDOUT-DTI only.

Arms: P0 base top-37,654 of the ridge over eligible pixels; P1 base minus dots within 2 px of the VISIBLE catalogue
(B2-style, count drops); P2 density-matched uniform random thinning of the base; P3 repulsion with count refill.
Writes evidence/repulsion_exp4_2026-10-31.json.

    python scripts/run_repulsion_exp4.py
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

KB = 37_654
BUF_PX = 2.0
DEV = [(f, s) for s in (140, 141) for f in range(4)]
CONF = [(f, s) for s in (150, 151, 152, 153) for f in range(4)]
OUT = ROOT / "evidence" / "repulsion_exp4_2026-10-31.json"


def main() -> int:
    t0 = datetime.now(timezone.utc)
    tmpl, labp = data_dir() / "sample_submission.tif", data_dir() / "labels.tif"
    with rasterio.open(tmpl) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(labp) as s:
        labels = (s.read(1) == 1) & foot
    names = json.loads((work_dir() / "static_ABCD.npy.names.json").read_text())
    static = np.load(work_dir() / "static_ABCD.npy", mmap_mode="r")
    ridge = np.full(foot.shape, -np.inf, np.float32)
    ridge[foot] = np.nan_to_num(np.asarray(static[names.index("A_mag_hg_ridge")], np.float32), nan=-np.inf)
    ho = Holdout(foot, labels)

    arms = ("P0", "P1", "P2", "P3")
    rows = {a: {"dev": [], "conf": []} for a in arms}
    canary = {"dev": [], "conf": []}
    removed = {"dev": [], "conf": []}
    for split, draws in (("dev", DEV), ("conf", CONF)):
        for fold, seed in draws:
            d = ho.draw(fold, seed)
            vis = d.visible
            E = foot & ~vis
            N2 = distance_transform_edt(~vis) <= BUF_PX
            B = top_k(ridge, E, KB)
            P1 = B & ~N2
            nrem = int((B & N2).sum())
            removed[split].append(nrem)
            rng = np.random.default_rng(4000 + 10 * seed + fold)
            bidx = np.flatnonzero(B.ravel())
            P2v = B.ravel().copy()
            P2v[rng.choice(bidx, nrem, replace=False)] = False
            P2 = P2v.reshape(foot.shape)
            P3 = P1 | top_k(ridge, E & ~N2 & ~P1, nrem)
            m = d.quadrant & E
            y = d.hidden_test[m].astype(np.uint8)
            dist = distance_transform_edt(~vis).astype(np.float32)
            canary[split].append(dict(fold=fold, seed=seed, n_pos=int(y.sum()), auc_ridge=auc_or_none(y, ridge[m]),
                                      auc_neg_dist_vis=auc_or_none(y, -dist[m])))
            for a, e in dict(P0=B, P1=P1, P2=P2, P3=P3).items():
                assert not (e & vis).any(), f"{a} emits on visible catalogue"
                if a == "P0" or a == "P3":
                    assert int(e.sum()) == KB, (a, int(e.sum()))
                if a == "P2":  # thinning removes exactly as many dots as P1 (pre-registered)
                    assert int(e.sum()) == int(P1.sum()), (a, int(e.sum()), int(P1.sum()))
                sc = ho.score(d, e)
                rows[a][split].append(dict(fold=fold, seed=seed, tp=float(sc["tp"]), fp=float(sc["fp"]),
                                           fn=float(sc["fn"]), n_truth=int(sc["n_truth"]), dti=float(sc["dti"])))
            print(split, fold, seed, {a: round(rows[a][split][-1]["dti"], 5) for a in arms}, "removed", nrem, flush=True)

    def paired(a, b, s):
        return dict(diff=pooled(rows[a][s]) - pooled(rows[b][s]), ci95=boot(rows[a][s], rows[b][s]))

    res = {a: {s: dict(pooled_dti=pooled(rows[a][s]), ci95=boot(rows[a][s]),
                       n_truth_total=sum(x["n_truth"] for x in rows[a][s])) for s in ("dev", "conf")} for a in arms}
    diffs = {s: {"P1-P2": paired("P1", "P2", s), "P1-P0": paired("P1", "P0", s), "P3-P0": paired("P3", "P0", s)}
             for s in ("dev", "conf")}
    canary_summary = {}
    for s in ("dev", "conf"):
        for key in ("auc_ridge", "auc_neg_dist_vis"):
            vals = [c[key] for c in canary[s] if c[key] is not None]
            canary_summary[f"{s}.{key}"] = dict(min=min(vals), max=max(vals), n=len(vals))
    g0 = all(v["max"] <= 0.90 for v in canary_summary.values())
    mech = {s: diffs[s]["P1-P2"]["diff"] > 0 and diffs[s]["P1-P2"]["ci95"][0] > 0 for s in ("dev", "conf")}
    verdict = ("mechanism-supported (repulsion beyond thinning)" if (g0 and all(mech.values()))
               else "thinning-explains-B2 (no repulsion beyond density)")
    rec = dict(
        generated_utc=t0.isoformat(timespec="seconds"),
        script="scripts/run_repulsion_exp4.py",
        preregistration="knowledge/56_preregistered_bound_fill_and_repulsion_2026-10-31.md",
        evidence_class="HOLDOUT-DTI (catalogue-gap proxy; not organizer-confirmed)",
        parameters=dict(K_base=KB, buffer_px=BUF_PX, dev_draws=DEV, confirm_draws=CONF, score_layer="A_mag_hg_ridge"),
        inputs=dict(template_sha256=sha(tmpl), labels_sha256=sha(labp)),
        removed_dots_by_draw=removed,
        arms=res, paired_differences=diffs,
        leakage_canary=dict(summary=canary_summary, per_draw=canary),
        gates=dict(G0_canary=g0, P1_beats_P2_dev=mech["dev"], P1_beats_P2_confirm=mech["conf"]),
        verdict=verdict,
        note="Holdout proxy only. Not an organizer score. The 0.2778 value is an owner-reported number and is not mixed with these.",
    )
    OUT.write_text(json.dumps(rec, indent=1, allow_nan=False, default=float) + "\n")
    print(json.dumps({"verdict": verdict, "gates": rec["gates"]}, indent=1))
    for a in arms:
        print(a, {s: (round(res[a][s]["pooled_dti"], 5), [round(x, 5) for x in res[a][s]["ci95"]]) for s in ("dev", "conf")})
    for s in ("dev", "conf"):
        for k, v in diffs[s].items():
            print(s, k, round(v["diff"], 5), [round(x, 5) for x in v["ci95"]])
    print("canary", canary_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
