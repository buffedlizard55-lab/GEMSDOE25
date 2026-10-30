#!/usr/bin/env python3
"""Experiment 1 of pre-registration knowledge/54 (H-SP1): soft visible-catalogue prior, fixed dot budget.

Arms (same draws, same evaluator, same run):
  A0 top-K ridge (A_mag_hg_ridge) | A1 ridge * exp(-d/lam) (candidate) | A2 ridge, d>2px only |
  A3 ridge * exp(+d/lam) (sign control) | A4 K random eligible pixels (floor).
Eligible pixels: footprint and not VISIBLE catalogue (per draw). Hidden catalogue is never excluded.
Outputs HOLDOUT-DTI only (catalogue-gap proxy). Writes evidence/soft_catalogue_prior_exp1_2026-10-30.json.

    python scripts/run_soft_catalogue_prior.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.holdout import Holdout  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402

K = 21_000          # pre-registered dot budget (below lane cap 21,713)
LAM = 10.0          # pre-registered decay length, px (1 km)
BUF = 2.0           # pre-registered hard buffer, px (200 m)
DEV = [(f, s) for s in (140, 141) for f in range(4)]
CONF = [(f, s) for s in (144, 145, 146, 147) for f in range(4)]
ALPHA, BETA, EPS = 0.2, 0.8, 1e-7
OUT = ROOT / "evidence" / "soft_catalogue_prior_exp1_2026-10-30.json"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pooled(rows: list[dict]) -> float:
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    return tp / (tp + ALPHA * fp + BETA * fn + EPS)


def boot(rows_a, rows_b=None, nrep=10_000, seed=7):
    rng = np.random.default_rng(seed)
    m = len(rows_a)
    vals = []
    for _ in range(nrep):
        idx = rng.integers(0, m, m)
        a = pooled([rows_a[i] for i in idx])
        vals.append(a if rows_b is None else a - pooled([rows_b[i] for i in idx]))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def top_k(score: np.ndarray, eligible: np.ndarray, k: int) -> np.ndarray:
    """Boolean emission of the k highest finite-score eligible pixels (deterministic tie-break by index)."""
    s = np.where(eligible & np.isfinite(score), score, -np.inf).ravel()
    idx = np.argpartition(-s, k)[:k]
    idx = idx[np.isfinite(s[idx])]
    out = np.zeros(s.shape, bool)
    out[idx] = True
    return out.reshape(score.shape)


def auc_or_none(y: np.ndarray, x: np.ndarray):
    if y.min() == y.max():
        return None
    return float(roc_auc_score(y, x))


def main() -> int:
    t0 = datetime.now(timezone.utc)
    tmpl, labp = data_dir() / "sample_submission.tif", data_dir() / "labels.tif"
    with rasterio.open(tmpl) as t:
        foot = np.isfinite(t.read(1))
    with rasterio.open(labp) as s:
        labels = (s.read(1) == 1) & foot
    names = json.loads((work_dir() / "static_ABCD.npy.names.json").read_text())
    static = np.load(work_dir() / "static_ABCD.npy", mmap_mode="r")
    ridge_vec = np.asarray(static[names.index("A_mag_hg_ridge")], dtype=np.float32)
    ridge = np.zeros(foot.shape, np.float32)
    ridge[foot] = np.nan_to_num(ridge_vec, nan=-np.inf)
    ridge[~foot] = -np.inf
    ho = Holdout(foot, labels)

    rows = {a: {"dev": [], "conf": []} for a in ("A0", "A1", "A2", "A3", "A4")}
    canary = {"dev": [], "conf": []}
    ndraw = {"dev": 0, "conf": 0}
    for split, draws in (("dev", DEV), ("conf", CONF)):
        for fold, seed in draws:
            d = ho.draw(fold, seed)
            vis = d.visible
            elig = foot & ~vis
            dist = distance_transform_edt(~vis).astype(np.float32)  # px to visible catalogue
            # leakage canary: each feature alone, test quadrant, non-visible pixels, hidden_test = positives
            m = d.quadrant & ~vis
            y = d.hidden_test[m].astype(np.uint8)
            canary[split].append({
                "fold": fold, "seed": seed, "n_pos": int(y.sum()), "n_px": int(m.sum()),
                "auc_ridge": auc_or_none(y, ridge[m]),
                "auc_neg_dist_vis": auc_or_none(y, -dist[m]),
            })
            # exponent clipped at 60 so exp(+d/lam) cannot overflow float32 (would silently drop far pixels)
            prior = np.exp(-dist / LAM).astype(np.float32)
            anti = np.exp(np.minimum(dist / LAM, 60.0)).astype(np.float32)
            emis = {
                "A0": top_k(ridge, elig, K),
                "A1": top_k(ridge * prior, elig, K),
                "A2": top_k(ridge, elig & (dist > BUF), K),
                "A3": top_k(ridge * anti, elig, K),
            }
            rng = np.random.default_rng(1000 + 10 * seed + fold)
            pool = np.flatnonzero(elig.ravel())
            rnd = np.zeros(foot.size, bool)
            rnd[rng.choice(pool, K, replace=False)] = True
            emis["A4"] = rnd.reshape(foot.shape)
            for a, e in emis.items():
                assert int(e.sum()) == K, (a, int(e.sum()))
                assert not (e & vis).any(), f"{a} emitted on visible catalogue"
                sc = ho.score(d, e)
                rows[a][split].append(dict(fold=fold, seed=seed, tp=float(sc["tp"]), fp=float(sc["fp"]),
                                           fn=float(sc["fn"]), n_truth=int(sc["n_truth"]), dti=float(sc["dti"])))
            ndraw[split] += 1

    res = {}
    for a in rows:
        res[a] = {}
        for split in ("dev", "conf"):
            r = rows[a][split]
            res[a][split] = dict(pooled_dti=pooled(r), ci95=boot(r), n_truth_total=sum(x["n_truth"] for x in r),
                                 per_draw_dti=[round(x["dti"], 6) for x in r])

    def paired(a, b, split):
        return dict(diff=pooled(rows[a][split]) - pooled(rows[b][split]),
                    ci95=boot(rows[a][split], rows[b][split]))

    diffs = {}
    for split in ("dev", "conf"):
        diffs[split] = {f"A1-{b}": paired("A1", b, split) for b in ("A0", "A2", "A3", "A4")}

    canary_summary = {}
    for split in ("dev", "conf"):
        for key in ("auc_ridge", "auc_neg_dist_vis"):
            vals = [c[key] for c in canary[split] if c[key] is not None]
            canary_summary[f"{split}.{key}"] = dict(min=min(vals), max=max(vals), n=len(vals))
    g0 = all(v["max"] <= 0.90 for v in canary_summary.values())

    def gate(split):
        dd = diffs[split]
        return dict(
            A1_beats_A0=dd["A1-A0"]["diff"] > 0 and dd["A1-A0"]["ci95"][0] > 0,
            A1_beats_A2=dd["A1-A2"]["diff"] > 0 and dd["A1-A2"]["ci95"][0] > 0,
            A1_beats_A4=dd["A1-A4"]["diff"] > 0 and dd["A1-A4"]["ci95"][0] > 0,
            A3_below_A1=dd["A1-A3"]["diff"] > 0,
        )

    g_dev, g_conf = gate("dev"), gate("conf")
    promote = g0 and all(g_dev.values()) and all(g_conf.values())
    rec = dict(
        generated_utc=t0.isoformat(timespec="seconds"),
        script="scripts/run_soft_catalogue_prior.py",
        preregistration="knowledge/54_preregistered_soft_catalogue_prior_2026-10-30.md (commit 5b5c31b)",
        evidence_class="HOLDOUT-DTI (catalogue-gap proxy; evaluator gems25.holdout + gems25.metric; not organizer-confirmed)",
        parameters=dict(K=K, lam_px=LAM, buffer_px=BUF, hide_frac=0.20, dev_draws=DEV, confirm_draws=CONF),
        inputs=dict(template_sha256=sha(tmpl), labels_sha256=sha(labp),
                    static_feature="A_mag_hg_ridge", static_npy_sha256=sha(work_dir() / "static_ABCD.npy")),
        draws_run=ndraw,
        arms=res, paired_differences=diffs,
        leakage_canary=dict(summary=canary_summary, per_draw=canary),
        gates=dict(G0_canary_max_auc_le_0_90=g0, G1_dev=g_dev, G2_confirm=g_conf,
                   G3_sign_control_in_pre_registered_direction=bool(g_dev["A3_below_A1"] and g_conf["A3_below_A1"])),
        verdict="promote-to-lane-check" if promote else "negative",
        note="Passing G0-G3 only permits the G4 lane and verifier checks. It does not clear any file or approve a slot.",
    )
    OUT.write_text(json.dumps(rec, indent=1, allow_nan=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("verdict", "gates")}, indent=1))
    for a in res:
        print(a, {s: round(res[a][s]["pooled_dti"], 5) for s in ("dev", "conf")})
    for s in ("dev", "conf"):
        for k, v in diffs[s].items():
            print(s, k, round(v["diff"], 5), [round(x, 5) for x in v["ci95"]])
    print("canary", canary_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
