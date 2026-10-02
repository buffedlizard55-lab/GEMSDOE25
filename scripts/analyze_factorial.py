#!/usr/bin/env python3
"""Analyse ``evidence/factorial/cells.jsonl`` exactly as pre-registered (knowledge/04_preregistered_factorial_*)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25 import factorial as fx  # noqa: E402
from gems25.families import FAMILIES  # noqa: E402

FOLDS = ["NW", "NE", "SW", "SE"]


def main() -> None:
    ev = ROOT / "evidence" / "factorial"
    rows = [json.loads(line) for line in (ev / "cells.jsonl").read_text().splitlines()]
    des = json.loads((ev / "design.json").read_text())
    X = np.array(des["X"])
    names = des["names"]
    by = defaultdict(dict)
    for r in rows:
        by[r["row"]][(r["fold"], r["draw"])] = r
    draws = sorted({r["draw"] for r in rows})
    n_runs = X.shape[0]
    complete = all(len(by[i]) == 4 * len(draws) for i in range(n_runs))
    if not complete:
        raise SystemExit("incomplete design: " + str({i: len(by[i]) for i in range(n_runs)}))

    def metric(key: str):
        M = np.zeros((n_runs, 4))  # run x fold (mean over draws)
        for i in range(n_runs):
            for f in range(4):
                M[i, f] = np.mean([by[i][(f, d)][key] for d in draws])
        return M

    out: dict = {"design": {"names": names, "resolution": des["alias"]["resolution"],
                            "defining_relation": des["alias"]["defining_relation"], "runs": n_runs,
                            "cells_per_run": 4 * len(draws)}}
    runs = []
    for i in range(n_runs):
        letters = "".join(n for n, v in zip(names, X[i]) if v > 0)
        cells = [by[i][(f, d)] for f in range(4) for d in draws]
        runs.append(dict(row=i, levels=dict(zip(names, X[i].tolist())), families=letters,
                         dti_mean=float(np.mean([c["dti"] for c in cells])),
                         dti_sd_cells=float(np.std([c["dti"] for c in cells], ddof=1)),
                         dti_by_fold=[float(np.mean([by[i][(f, d)]["dti"] for d in draws])) for f in range(4)],
                         auc_mean=float(np.mean([c["auc"] for c in cells])),
                         coverage_mean=float(np.mean([c["coverage"] for c in cells])),
                         hug_mean=float(np.mean([c["hug"] for c in cells])),
                         emitted_mean=float(np.mean([c["emitted"] for c in cells])),
                         dti_undotted_mean=float(np.mean([c["dti_undotted"] for c in cells]))))
    out["runs"] = runs
    refs = {}
    for ref in ("REF_topo", "REF_geo", "REF_null"):
        if ref in by:
            cs = [by[ref][(f, d)] for f in range(4) for d in draws if (f, d) in by[ref]]
            refs[ref] = dict(dti_mean=float(np.mean([c["dti"] for c in cs])), auc_mean=float(np.mean([c["auc"] for c in cs])),
                             hug_mean=float(np.mean([c["hug"] for c in cs])), emitted_mean=float(np.mean([c["emitted"] for c in cs])),
                             by_fold=[float(np.mean([by[ref][(f, d)]["dti"] for d in draws])) for f in range(4)])
    out["references_same_harness"] = refs

    for key, label in (("dti", "dti"), ("auc", "auc"), ("hug", "hug")):
        M = metric(key)
        y = M.mean(1)
        eff = fx.estimate_effects(X, y, names)
        L = fx.lenth(eff)
        fe = fx.fold_effects(X, M, names)
        out[f"effects_{label}"] = dict(effects=eff, lenth=L, folds=fe)

    eff, L, fe = out["effects_dti"]["effects"], out["effects_dti"]["lenth"], out["effects_dti"]["folds"]
    me = L["me"]
    y_all = next(r["dti_mean"] for r in runs if r["families"] == "ABCDE")
    cls = {}
    for f in names:
        main_ok = eff[f] > me and fe[f]["blocks_positive"] >= 3
        combos = [k for k in eff if len(k) == 2 and f in k and eff[k] > me and fe[k]["blocks_positive"] >= 3]
        if eff[f] < -me:
            c = "harmful"
        elif main_ok:
            c = "matters alone"
        elif combos:
            c = "matters in combination"
        else:
            c = "inert"
        cls[f] = dict(family=FAMILIES[f]["name"], label=FAMILIES[f]["label"], classification=c,
                      main_effect=eff[f], main_effect_pct_of_all_families=100 * eff[f] / y_all,
                      main_effect_se_folds=fe[f]["se"], folds_positive=fe[f]["blocks_positive"],
                      lenth_ME=me, significant_interactions=combos)
    out["classification"] = cls
    out["ranked_main_effects"] = sorted(((f, eff[f]) for f in names), key=lambda t: -abs(t[1]))
    out["ranked_interactions"] = sorted(((k, v) for k, v in eff.items() if len(k) == 2), key=lambda t: -abs(t[1]))
    best = max(runs, key=lambda r: (r["dti_mean"], -len(r["families"])))
    out["best_design_row"] = best
    out["all_families_row"] = next(r for r in runs if r["families"] == "ABCDE")
    # additive + 2fi model prediction for every one of the 32 corners (for the confirmation stage)
    full = fx.design(5)
    pred = []
    cmap = fx.contrasts(full["X"], names, 2)
    mean_y = float(np.mean([r["dti_mean"] for r in runs]))
    for i in range(full["X"].shape[0]):
        yhat = mean_y + sum(0.5 * eff[k] * cmap[k][i] for k in eff)
        pred.append(dict(levels=dict(zip(names, full["X"][i].tolist())), predicted_dti=float(yhat),
                         families="".join(n for n, v in zip(names, full["X"][i]) if v > 0), in_design=None))
    in_design = {tuple(r["levels"][n] for n in names) for r in runs}
    for p in pred:
        p["in_design"] = tuple(p["levels"][n] for n in names) in in_design
    out["model_predictions_all_32_corners"] = sorted(pred, key=lambda p: -p["predicted_dti"])
    out["deviations"] = []
    (ev / "results.json").write_text(json.dumps(out, indent=1, default=float) + "\n")

    # human-readable summary
    lines = ["# Factorial results (auto-generated by scripts/analyze_factorial.py)\n",
             f"Design 2^(5-1) Resolution {out['design']['resolution']}, {n_runs} runs x {out['design']['cells_per_run']} cells. Primary response: mean sparse DTI.\n",
             "## Runs\n", "| row | families | mean DTI | by fold (NW NE SW SE) | AUC | hug | emitted |", "|---|---|---|---|---|---|---|"]
    for r in sorted(runs, key=lambda r: -r["dti_mean"]):
        lines.append(f"| {r['row']} | {r['families']} | {r['dti_mean']:.4f} | {' '.join(f'{v:.3f}' for v in r['dti_by_fold'])} | {r['auc_mean']:.3f} | {r['hug_mean']:.2f} | {r['emitted_mean']:.0f} |")
    lines += ["", "## Same-harness references", "| reference | mean DTI | AUC | hug |", "|---|---|---|---|"]
    for k, v in refs.items():
        lines.append(f"| {k} | {v['dti_mean']:.4f} | {v['auc_mean']:.3f} | {v['hug_mean']:.2f} |")
    lines += ["", f"## Effects on DTI (Lenth PSE={L['pse']:.4f}, ME={L['me']:.4f}, SME={L['sme']:.4f})", "| effect | value | SE (folds) | folds + | |effect|>ME |", "|---|---|---|---|---|"]
    for k, v in sorted(eff.items(), key=lambda t: -abs(t[1])):
        lines.append(f"| {k} | {v:+.4f} | {fe[k]['se']:.4f} | {fe[k]['blocks_positive']}/4 | {'yes' if abs(v) > me else ''} |")
    lines += ["", "## Classification (pre-registered rule)", "| factor | family | class | main effect | % of all-families run |", "|---|---|---|---|---|"]
    for f, c in cls.items():
        lines.append(f"| {f} | {c['label']} | **{c['classification']}** | {c['main_effect']:+.4f} | {c['main_effect_pct_of_all_families']:+.0f}% |")
    (ev / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
