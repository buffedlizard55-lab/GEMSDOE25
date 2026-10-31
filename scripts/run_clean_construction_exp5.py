#!/usr/bin/env python3
"""E5 of knowledge/56 (H-CLEAN1): protocol-clean halo fill (ascending registry coverage) vs random. HOLDOUT-DTI only.

Pre-registered after E3/E4 (disclosed in knowledge/56 §6). Writes evidence/clean_construction_exp5_2026-10-31.json.

    python scripts/run_clean_construction_exp5.py
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
from run_soft_catalogue_prior import pooled, boot, auc_or_none, sha  # noqa: E402

K = 21_700
DEV = [(f, s) for s in (140, 141) for f in range(4)]
CONF = [(f, s) for s in (160, 161, 162, 163) for f in range(4)]   # virgin: unused before this file
OUT = ROOT / "evidence" / "clean_construction_exp5_2026-10-31.json"
R13 = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def main() -> int:
    t0 = datetime.now(timezone.utc)
    tmpl, labp = data_dir() / "sample_submission.tif", data_dir() / "labels.tif"
    with rasterio.open(tmpl) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(labp) as s:
        labels = (s.read(1) == 1) & foot
    cache = np.load(work_dir() / "registry_halos.npz")   # built by scripts/build_registry_halo_cache.py
    names = [str(x) for x in cache["names"]]
    packed = cache["packed"]
    halos_full = [np.unpackbits(packed[i])[: foot.sum()].astype(bool) for i in range(packed.shape[0])]
    r13i = [i for i, n in enumerate(names) if n == R13][0]
    halo_r13 = np.zeros(foot.shape, bool)
    halo_r13[foot] = halos_full[r13i]
    kother = np.zeros(foot.shape, np.int32)
    for i, h in enumerate(halos_full):
        if i != r13i:
            kother[foot] += h
    names_ridge = json.loads((work_dir() / "static_ABCD.npy.names.json").read_text())
    static = np.load(work_dir() / "static_ABCD.npy", mmap_mode="r")
    ho = Holdout(foot, labels)
    ridge = np.full(foot.shape, -np.inf, np.float32)
    ridge[foot] = np.nan_to_num(np.asarray(static[names_ridge.index("A_mag_hg_ridge")], np.float32), nan=-np.inf)

    arms = ("C1", "C2", "C3")
    rows = {a: {"dev": [], "conf": []} for a in arms}
    canary = {"dev": [], "conf": []}
    for split, draws in (("dev", DEV), ("conf", CONF)):
        for fold, seed in draws:
            d = ho.draw(fold, seed)
            vis = d.visible
            E = foot & ~vis
            Eh = E & ~halo_r13
            Hh = E & halo_r13
            need = K - int(Eh.sum())
            assert 0 < need <= int(Hh.sum())
            m = d.quadrant & E
            y = d.hidden_test[m].astype(np.uint8)
            dist = distance_transform_edt(~vis).astype(np.float32)
            canary[split].append(dict(fold=fold, seed=seed, n_pos=int(y.sum()), auc_ridge=auc_or_none(y, ridge[m]),
                                      auc_neg_dist_vis=auc_or_none(y, -dist[m])))
            # C1: ascending registry coverage, ties by seeded random key
            rng1 = np.random.default_rng(5000 + 10 * seed + fold)
            hidx = np.flatnonzero(Hh.ravel())
            key = kother.ravel()[hidx].astype(np.float64) + rng1.random(hidx.size) * 0.5
            pick1 = hidx[np.argsort(key, kind="stable")[:need]]
            c1v = Eh.ravel().copy()
            c1v[pick1] = True
            c1 = c1v.reshape(foot.shape)
            # C2: random halo fill
            rng2 = np.random.default_rng(6000 + 10 * seed + fold)
            pick2 = rng2.choice(hidx, need, replace=False)
            c2v = Eh.ravel().copy()
            c2v[pick2] = True
            c2 = c2v.reshape(foot.shape)
            # C3: random floor over E
            rng3 = np.random.default_rng(7000 + 10 * seed + fold)
            c3v = np.zeros(foot.size, bool)
            c3v[rng3.choice(np.flatnonzero(E.ravel()), K, replace=False)] = True
            c3 = c3v.reshape(foot.shape)
            for a, e in dict(C1=c1, C2=c2, C3=c3).items():
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
    diffs = {s: {"C1-C2": paired("C1", "C2", s), "C1-C3": paired("C1", "C3", s)} for s in ("dev", "conf")}
    canary_summary = {}
    for s in ("dev", "conf"):
        for key in ("auc_ridge", "auc_neg_dist_vis"):
            vals = [c[key] for c in canary[s] if c[key] is not None]
            canary_summary[f"{s}.{key}"] = dict(min=min(vals), max=max(vals), n=len(vals))
    g0 = all(v["max"] <= 0.90 for v in canary_summary.values())

    def gate(s):
        return dict(C1_beats_C2=diffs[s]["C1-C2"]["diff"] > 0 and diffs[s]["C1-C2"]["ci95"][0] > 0,
                    C1_beats_C3=diffs[s]["C1-C3"]["diff"] > 0 and diffs[s]["C1-C3"]["ci95"][0] > 0)

    gd, gc = gate("dev"), gate("conf")
    passed = g0 and all(gd.values()) and all(gc.values())
    rec = dict(
        generated_utc=t0.isoformat(timespec="seconds"),
        script="scripts/run_clean_construction_exp5.py",
        preregistration="knowledge/56_preregistered_bound_fill_and_repulsion_2026-10-31.md §6 (added after E3/E4; disclosed)",
        evidence_class="HOLDOUT-DTI (catalogue-gap proxy; not organizer-confirmed)",
        parameters=dict(K=K, dev_draws=DEV, confirm_draws=CONF, score_layer="A_mag_hg_ridge (canary only)",
                        halo_rank="ascending count of the other registry halos"),
        inputs=dict(template_sha256=sha(tmpl), labels_sha256=sha(labp)),
        arms=res, paired_differences=diffs,
        leakage_canary=dict(summary=canary_summary, per_draw=canary),
        gates=dict(G0_canary=g0, G1_dev=gd, G2_virgin_confirm=gc),
        verdict="clean-construction-holdout-signal" if passed else "negative",
        note="Holdout proxy only. Clears no file and approves no slot.",
    )
    OUT.write_text(json.dumps(rec, indent=1, allow_nan=False, default=float) + "\n")
    print(json.dumps({"verdict": rec["verdict"], "gates": rec["gates"]}, indent=1))
    for a in arms:
        print(a, {s: (round(res[a][s]["pooled_dti"], 5), [round(x, 5) for x in res[a][s]["ci95"]]) for s in ("dev", "conf")})
    for s in ("dev", "conf"):
        for k, v in diffs[s].items():
            print(s, k, round(v["diff"], 5), [round(x, 5) for x in v["ci95"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
