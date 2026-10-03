#!/usr/bin/env python3
"""H28 stage 1c — the two-band truth-intensity mixture of pre-registration amendment D3.

The single-parent model of §5b under-predicts the two GEMSDOE10 rasters by 0.037/0.059 DTI: those surfaces sit
on truth the H19-5 band does not contain.  This script tests whether a second band is identified by the same
anchor logic, and — only if the pre-registered adoption rule passes — designs an emission under the mixture.

    .venv/bin/python scripts/run_h28_mixture.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25 import livecal  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import dot_thin  # noqa: E402

EVID = ROOT / "evidence" / "h28_calibration"
PARENT = "h19-5"
CANDIDATES = ["h25-ctx-ridge", "r7-nms3-dem10-scarp", "lidarscarp-top2pct", "pindrop-nodes"]
ANCHORS = ["lattice-s5", "h19-5", "h19-4", "h16-1", "d1-5", "h25-ctx-ridge", "h28-dotted-ridge",
           "r7-nms3-dem10-scarp", "lidarscarp-top2pct"]
LAMBDA_HAT = 1.85
B_GRID = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0]
SINGLE_PARENT_SPREAD_5_ANCHOR = 0.05254206483105798   # §5b, evidence/h28_calibration/anchors.json
DESIGN_SPACINGS = (2.4, 2.8, 3.2)
DESIGN_BUDGETS = (30_000, 44_090, 60_000)


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


n_from_score = livecal.invert_truth_count  # single source of truth for the §5b inversion


def band(mask: np.ndarray, dom: np.ndarray, lam: float) -> tuple[np.ndarray, float]:
    d = distance_transform_edt(~mask)
    g = np.where(dom, np.exp(-np.minimum(d, 80.0) / lam), 0.0).astype(np.float64)
    return g, float(g.sum())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true", help="skip the design stage")
    args = ap.parse_args()
    t_all = time.time()
    d = data_dir()
    tmpl = load(d / "sample_submission.tif")
    foot = np.isfinite(tmpl)
    lab = tmpl == 1
    dom = foot & ~lab

    ledger = json.loads((ROOT / "registry" / "artifact_ledger.json").read_text())
    rows = {r["id"]: r for r in ledger["artifacts"]}
    paths = {k: ROOT / v["file"] for k, v in rows.items() if v.get("file")}
    scores = {k: v.get("score") for k, v in rows.items()}
    missing = [a for a in ANCHORS if a not in paths or scores.get(a) is None]
    if missing:
        raise SystemExit(f"anchors without a hash-verified score: {missing}")

    def emask(aid: str) -> np.ndarray:
        arr = np.nan_to_num(load(paths[aid]), nan=0.0) > 0
        return arr & foot & ~lab

    p1 = emask(PARENT)
    g1, z1 = band(p1, dom, LAMBDA_HAT)
    print(f"parent {PARENT}: {int(p1.sum()):,} px; band mass Z1={z1:,.0f}", flush=True)

    # per-anchor integrals against each candidate band
    per_cand: dict[str, dict] = {}
    for cand in CANDIDATES:
        p2 = emask(cand)
        g2, z2 = band(p2, dom, LAMBDA_HAT)
        rec = {"px": int(p2.sum()), "z2": z2, "overlap_with_parent": int((p1 & p2).sum()), "anchors": {}}
        for aid in ANCHORS:
            t0 = time.time()
            m = emask(aid)
            mm, uu = livecal.emission_fields(m.astype(np.float32))
            rec["anchors"][aid] = {
                "mass": float(m.sum()), "score": scores[aid],
                "TA1": float((g1 * mm).sum()), "UA1": float((g1 * uu).sum()),
                "TA2": float((g2 * mm).sum()), "UA2": float((g2 * uu).sum()),
            }
            print(f"  {cand:<24} anchor {aid:<22} M={rec['anchors'][aid]['mass']:>9.0f} "
                  f"({time.time() - t0:.1f}s)", flush=True)
        scan = []
        for b in B_GRID:
            z = z1 + b * z2
            ns = []
            detail = {}
            for aid, a in rec["anchors"].items():
                t = (a["TA1"] + b * a["TA2"]) / z
                u = (a["UA1"] + b * a["UA2"]) / z
                n = n_from_score(a["score"], a["mass"], t, u)
                ns.append(n)
                detail[aid] = {"T": t, "U": u, "implied_N": n, "mass": a["mass"], "score": a["score"]}
            fin = np.array([x for x in ns if np.isfinite(x)], dtype=float)
            med = float(np.median(fin)) if fin.size else float("nan")
            spread = float(np.max(np.abs(fin - med) / med)) if fin.size else float("nan")
            scan.append({"b": b, "n_finite": int(fin.size), "median_N": med, "max_relative_spread": spread,
                         "mean_abs_dti_residual": None, "detail": detail})
        rec["scan"] = scan
        per_cand[cand] = rec
        ok = [s for s in scan if s["n_finite"] == len(ANCHORS)]
        best = min(ok, key=lambda s: s["max_relative_spread"]) if ok else None
        print(f"  -> {cand}: best b={best['b'] if best else None} spread={best['max_relative_spread']:.4f} "
              f"N={best['median_N']:.0f}" if best else f"  -> {cand}: no b identifies all anchors", flush=True)

    # reference: single parent (b = 0) over the same nine anchors
    single = next(s for s in per_cand[CANDIDATES[0]]["scan"] if s["b"] == 0.0)

    def mean_abs_resid(scan_row: dict, n_hat: float) -> float:
        out = []
        for aid, a in scan_row["detail"].items():
            t, u = a["T"], a["U"]
            fp = max(a["mass"] - n_hat * u, 0.0)
            pred = n_hat * t / (0.2 * (n_hat * t + fp) + 0.8 * n_hat)
            out.append(abs(pred - a["score"]))
        return float(np.mean(out))

    ranked = []
    for cand, rec in per_cand.items():
        for s in rec["scan"]:
            if s["n_finite"] == len(ANCHORS) and s["b"] > 0:
                s["mean_abs_dti_residual"] = mean_abs_resid(s, s["median_N"])
                ranked.append((cand, s))
    single["mean_abs_dti_residual"] = mean_abs_resid(single, single["median_N"])
    if not ranked:
        raise SystemExit("no mixture identifies all nine anchors; the single-parent model stands")
    cand_hat, s_hat = min(ranked, key=lambda cs: cs[1]["max_relative_spread"])
    n_hat = s_hat["median_N"]
    adopted = (s_hat["max_relative_spread"] <= SINGLE_PARENT_SPREAD_5_ANCHOR
               and s_hat["mean_abs_dti_residual"] <= 0.75 * single["mean_abs_dti_residual"])
    rule = {
        "criterion_i": {"quantity": "max relative spread of implied N over the nine anchors",
                        "mixture": s_hat["max_relative_spread"],
                        "single_parent_same_nine_anchors": single["max_relative_spread"],
                        "single_parent_five_anchors_reference": SINGLE_PARENT_SPREAD_5_ANCHOR,
                        "threshold": SINGLE_PARENT_SPREAD_5_ANCHOR,
                        "met": bool(s_hat["max_relative_spread"] <= SINGLE_PARENT_SPREAD_5_ANCHOR)},
        "criterion_ii": {"quantity": "mean absolute DTI residual over the nine anchors at the fitted N",
                         "mixture": s_hat["mean_abs_dti_residual"],
                         "single_parent": single["mean_abs_dti_residual"],
                         "required_improvement": 0.25,
                         "met": bool(s_hat["mean_abs_dti_residual"] <= 0.75 * single["mean_abs_dti_residual"])},
        "adopted": bool(adopted),
        "selected": {"second_parent": cand_hat, "b": s_hat["b"], "n_hat": n_hat, "lambda_hat": LAMBDA_HAT},
    }
    print(f"\nadoption: {json.dumps(rule, indent=1, default=str)}", flush=True)

    out = {
        "generated_utc": utc(), "script": "scripts/run_h28_mixture.py",
        "preregistration": "knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md (D3)",
        "score_provenance": ("user/owner-reported public-leaderboard values matched to file bytes by SHA-256; "
                             "NOT DrivenData receipts"),
        "anchors": ANCHORS, "candidates": CANDIDATES, "b_grid": B_GRID, "lambda_hat": LAMBDA_HAT,
        "single_parent_nine_anchor": {k: v for k, v in single.items() if k != "detail"},
        "single_parent_detail": single["detail"],
        "per_candidate": {c: {"px": r["px"], "overlap_with_parent": r["overlap_with_parent"],
                              "scan": [{k: v for k, v in s.items() if k != "detail"} for s in r["scan"]]}
                          for c, r in per_cand.items()},
        "adoption_rule": rule,
        "elapsed_s": round(time.time() - t_all, 1),
    }

    # ---- design stage (only if adopted) -------------------------------------------------------------
    if adopted and not args.quick:
        p2 = emask(cand_hat)
        g2, z2 = band(p2, dom, LAMBDA_HAT)
        w_mix = g1 + s_hat["b"] * g2
        pi_mix = w_mix / float(w_mix.sum())
        nu = (n_hat * livecal.disc_mass(pi_mix)).astype(np.float32)

        def exact(mask_or_float: np.ndarray) -> dict:
            pf = np.clip(np.asarray(mask_or_float, dtype=np.float32), 0, 1) * np.float32(dom)
            mm, uu = livecal.emission_fields(pf)
            t = float((pi_mix * mm).sum())
            u = float((pi_mix * uu).sum())
            mass = float(pf.sum())
            sel = pf > 0
            fp = float((pf[sel] * livecal.psi(nu[sel])).sum())
            tp = n_hat * t
            return {"dti": float(tp / (0.2 * (tp + fp) + 0.8 * n_hat)), "t": t, "u": u, "mass": mass,
                    "redundancy": u - t, "fp_per_px": float(fp / mass) if mass else 0.0,
                    "credit_per_px": float(tp / mass) if mass else 0.0}

        designs = []
        union = p1 | p2
        for dd in (1.5, 2.0, 2.4, 2.8, 3.2):
            for nm, msk in (("dot_thin(P1)", dot_thin(p1, dd)), ("dot_thin(P1|P2)", dot_thin(union, dd))):
                rec = {"rule": nm, "min_dist": dd}
                rec.update(exact(msk))
                designs.append(rec)
                print(f"  {nm:<18} d={dd:>4.2f} M={rec['mass']:>8.0f} DTI={rec['dti']:.5f} "
                      f"R={rec['redundancy']:.4f}", flush=True)
        u_field = livecal.value_field(pi_mix)
        jit = (1.0 + 1e-3 * (np.random.default_rng(20261002).random(int(dom.size)).reshape(dom.shape) - 0.5)
               * 2.0).astype(np.float32)
        for md in DESIGN_SPACINGS:
            t0 = time.time()
            mask, _ = livecal.greedy_disjoint(u_field * jit, dom, min_dist=md, max_keep=max(DESIGN_BUDGETS))
            ko = np.flatnonzero(mask.ravel())
            ko = ko[np.argsort(-(u_field * jit).ravel()[ko], kind="stable")]
            print(f"  greedy pool at {md} px: {ko.size:,} ({time.time() - t0:.1f}s)", flush=True)
            for target in DESIGN_BUDGETS:
                if target > ko.size:
                    continue
                sub = np.zeros(u_field.size, bool)
                sub[ko[:target]] = True
                rec = {"rule": f"greedy_value_{md}", "min_dist": md, "budget": target}
                rec.update(exact(sub.reshape(u_field.shape)))
                designs.append(rec)
                print(f"  greedy_value d={md} M={rec['mass']:>8.0f} DTI={rec['dti']:.5f} "
                      f"c/px={rec['credit_per_px']:.4f}", flush=True)
        refs = {}
        for aid in ("d1-5", "d2-8", "h19-5", "lattice-s5", cand_hat):
            if aid in paths:
                refs[aid] = {"reported": scores.get(aid), **exact(emask(aid))}
                print(f"  ref {aid:<22} M={refs[aid]['mass']:>8.0f} pred={refs[aid]['dti']:.5f} "
                      f"reported={refs[aid]['reported']}", flush=True)
        best = max(designs, key=lambda r: r["dti"])
        d28 = refs.get("d2-8", {}).get("dti")
        out["design"] = {"designs": designs, "references": refs, "best": best,
                         "beats_d2_8": bool(d28 is not None and best["dti"] > d28),
                         "note": ("predictions use the adopted two-band pi at full resolution: TP from the exact "
                                  "kernel-max field, FP from the saturating Poisson term")}
        if best["dti"] > (d28 or 0.0):
            # rebuild the winning mask and store it for packaging
            np.save(work_dir() / "h28_mixture_best.npy",
                    np.array([best["rule"], best.get("min_dist"), best.get("budget", 0)], dtype=object),
                    allow_pickle=True)
    (EVID / "mixture.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(f"\nwrote {EVID / 'mixture.json'} in {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
