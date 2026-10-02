#!/usr/bin/env python3
"""Analyze the frozen H27-1 2² screen/confirmation and apply its absolute-plus-paired gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.design import H27_ARMS, H27_HISTORICAL_HOLDOUT_BEST, factorial_2x2_effects, h27_promotion_gate  # noqa: E402

EXPECTED_DRAWS = {"screen": {4, 5}, "confirm": {6, 7}}
DIAGNOSTICS = ("dti", "coverage", "emitted", "hug", "auc")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=None, help="run directory; defaults to evidence/h27_<stage>")
    args = ap.parse_args()
    run_dir = Path(args.dir) if args.dir else None
    if run_dir is None:
        candidates = [ROOT / "evidence" / f"h27_{stage}" for stage in EXPECTED_DRAWS]
        run_dir = next((p for p in candidates if (p / "cells.jsonl").exists()), candidates[0])

    design = json.loads((run_dir / "design.json").read_text())
    stage = design["stage"]
    if stage not in EXPECTED_DRAWS:
        raise SystemExit(f"unknown H27 stage {stage!r}")
    if stage == "confirm":
        screen_path = ROOT / "evidence" / "h27_screen" / "results.json"
        if not screen_path.exists() or not json.loads(screen_path.read_text()).get("slot_eligible", False):
            raise SystemExit("confirmation results are not valid unless the frozen draws 4,5 screen passed both gates")
    expected_draws = EXPECTED_DRAWS[stage]
    rows = [json.loads(line) for line in (run_dir / "cells.jsonl").read_text().splitlines() if line.strip()]
    expected_keys = {(fold, draw, arm) for fold in range(4) for draw in expected_draws for arm in H27_ARMS}
    actual_keys = [(r["fold"], r["draw"], r["arm"]) for r in rows]
    if len(actual_keys) != len(set(actual_keys)):
        raise SystemExit("duplicate fold/draw/arm rows in cells.jsonl")
    if set(actual_keys) != expected_keys:
        missing = sorted(expected_keys - set(actual_keys))
        extra = sorted(set(actual_keys) - expected_keys)
        raise SystemExit(f"incomplete/unregistered design rows; missing={missing}; extra={extra}")
    if set(design["draws"]) != expected_draws:
        raise SystemExit(f"design draw set differs from frozen {stage} draws {sorted(expected_draws)}")
    row_order = design.get("row_order_zero_based", [])
    canonical = design.get("canonical_matrix", [])
    if sorted(row_order) != list(range(4)) or len(canonical) != 4:
        raise SystemExit("saved design order/matrix is malformed")
    expected_matrix = [canonical[i] for i in row_order]
    if expected_matrix != design.get("randomized_matrix"):
        raise SystemExit("saved randomized matrix does not match the frozen row order")
    cfg_by_arm = {cfg["arm"]: cfg for cfg in expected_matrix}
    order_by_arm = {cfg["arm"]: i + 1 for i, cfg in enumerate(expected_matrix)}
    for row in rows:
        cfg = cfg_by_arm.get(row["arm"])
        if (row.get("stage") != stage or row.get("design_seed") != design["design_seed"] or cfg is None
                or row.get("run_order") != order_by_arm[row["arm"]]
                or row.get("T") != cfg["T"] or row.get("S") != cfg["S"]
                or row.get("kfrac") != design["emission"]["kfrac"]
                or row.get("min_dist_px") != design["emission"]["min_dist_px"]):
            raise SystemExit(f"cell metadata disagrees with the frozen design: {row}")

    lookup = {(r["fold"], r["draw"], r["arm"]): r for r in rows}
    fold_arm: dict[int, dict[str, dict[str, float]]] = {}
    for fold in range(4):
        fold_arm[fold] = {}
        for arm in H27_ARMS:
            fold_arm[fold][arm] = {
                metric: float(np.mean([lookup[(fold, draw, arm)][metric] for draw in sorted(expected_draws)]))
                for metric in DIAGNOSTICS
            }

    arms = {}
    for arm in H27_ARMS:
        arms[arm] = {
            f"mean_{metric}": float(np.mean([fold_arm[f][arm][metric] for f in range(4)]))
            for metric in DIAGNOSTICS
        }
        arms[arm]["by_fold_dti"] = [fold_arm[f][arm]["dti"] for f in range(4)]
        arms[arm]["by_fold_hug"] = [fold_arm[f][arm]["hug"] for f in range(4)]

    fold_effects = [factorial_2x2_effects({arm: fold_arm[f][arm]["dti"] for arm in H27_ARMS}) for f in range(4)]
    overall_responses = {arm: arms[arm]["mean_dti"] for arm in H27_ARMS}
    effects = factorial_2x2_effects(overall_responses)
    effect_summary = {
        name: {"mean": value, "by_fold": [fe[name] for fe in fold_effects]}
        for name, value in effects.items()
    }
    hug_delta = float(np.mean([
        fold_arm[f]["TS"]["hug"] - fold_arm[f]["BASE"]["hug"] for f in range(4)
    ]))
    gate = h27_promotion_gate(
        arms["TS"]["by_fold_dti"], arms["BASE"]["by_fold_dti"], hug_delta,
        historical_best=H27_HISTORICAL_HOLDOUT_BEST,
    )
    result = {
        "hypothesis": "H27-1",
        "stage": stage,
        "draws": sorted(expected_draws),
        "design": design,
        "n_cells": len(rows),
        "historical_holdout_best": H27_HISTORICAL_HOLDOUT_BEST,
        "arms": arms,
        "factorial_effects_dti": effect_summary,
        "promotion_gate": gate,
        "slot_eligible": gate["passed"],
        "proxy_warning": "Hide-and-recover catalogue-gap evidence only; a pass is necessary, not sufficient, and is not a competition score.",
    }
    (run_dir / "results.json").write_text(json.dumps(result, indent=1) + "\n")

    lines = [
        f"# H27-1 {stage} results",
        "",
        f"Draws: {', '.join(map(str, sorted(expected_draws)))} · 4 spatial folds · {len(rows)} complete cells.",
        f"Historical comparator: **{H27_HISTORICAL_HOLDOUT_BEST:.9f}** (repository proxy, draws 0–1; not a competition score).",
        "",
        "## Paired arm means",
        "",
        "| Arm | Mean DTI | NW | NE | SW | SE | Emitted px | Coverage | Hug share | AUC |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in H27_ARMS:
        a = arms[arm]
        f = a["by_fold_dti"]
        lines.append(
            f"| {arm} | {a['mean_dti']:.6f} | {f[0]:.6f} | {f[1]:.6f} | {f[2]:.6f} | {f[3]:.6f} | "
            f"{a['mean_emitted']:.1f} | {a['mean_coverage']:.4f} | {a['mean_hug']:.4f} | {a['mean_auc']:.4f} |"
        )
    lines += ["", "## Estimated 2² effects on DTI", "", "| Effect | Mean contrast | NW | NE | SW | SE |", "|---|---:|---:|---:|---:|---:|"]
    for name, values in effect_summary.items():
        by = values["by_fold"]
        lines.append(f"| {name} | {values['mean']:+.6f} | {by[0]:+.6f} | {by[1]:+.6f} | {by[2]:+.6f} | {by[3]:+.6f} |")
    lines += [
        "",
        "## Frozen promotion gate",
        "",
        f"- Historical absolute comparator: TS {gate['candidate_mean_dti']:.6f} {'>' if gate['historical_comparator_passed'] else '≤'} {gate['historical_best']:.6f}: **{'pass' if gate['historical_comparator_passed'] else 'fail'}**.",
        f"- Paired TS−BASE gain: {gate['mean_gain_vs_paired_base']:+.6f}; {gate['folds_positive']}/4 folds positive; worst fold {gate['worst_fold_gain']:+.6f}; hug-share change {gate['hug_share_delta']:+.4f}: **{'pass' if gate['paired_gate_passed'] else 'fail'}**.",
        f"- Overall decision: **{'PASS — confirmation required before slot eligibility' if gate['passed'] and stage == 'screen' else 'PASS — holdout gate met; no upload is automatic' if gate['passed'] else 'FAIL — stop; no candidate/slot promotion'}**.",
        "- This is a spatially blocked catalogue-gap proxy, not new-fault ground truth or a live score.",
        "",
        "Exact raw rows, randomized design order, model timing, and all diagnostics are in `design.json` and `cells.jsonl`.",
    ]
    (run_dir / "results.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"stage": stage, "effects": effect_summary, "promotion_gate": gate, "slot_eligible": gate["passed"]}, indent=1))


if __name__ == "__main__":
    main()
