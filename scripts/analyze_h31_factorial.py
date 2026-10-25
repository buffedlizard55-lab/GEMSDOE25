#!/usr/bin/env python3
"""Validate and analyze the frozen H31-1 2² flank-shielded × sub-scarp holdout run."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import t

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.h31 import (  # noqa: E402
    EVALUATOR_VERSION,
    H31_ARMS,
    H31_CONTROL,
    factorial_2x2_effects,
    h31_promotion_gate,
    pooled_dti_summary,
)

EXPECTED_DRAWS = {"screen": [10, 11], "confirm": [12, 13]}
EXPECTED_ARMS = {H31_CONTROL, *H31_ARMS}
EXPECTED_FOLDS = ["NW", "NE", "SW", "SE"]
METRICS = ("dti", "coverage", "emitted", "hug", "auc")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def summarize_effect(values: np.ndarray) -> dict:
    arr = np.asarray(values, dtype=float)
    mean = float(arr.mean())
    se = float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else 0.0
    critical = float(t.ppf(0.975, arr.size - 1)) if arr.size > 1 else 0.0
    return {
        "mean": mean,
        "se_across_four_spatial_folds": se,
        "t_95_ci": [mean - critical * se, mean + critical * se],
        "folds_positive": int(np.count_nonzero(arr > 0.0)),
        "by_fold": [float(x) for x in arr],
    }


def verify_passing_screen(run: Path) -> dict:
    """Recompute the saved H31 screen gate from hash-bound raw cells before permitting confirmation."""
    run = Path(run)
    design_path, cells_path, results_path, canary_path = (
        run / "design.json",
        run / "cells.jsonl",
        run / "results.json",
        run / "canary.json",
    )
    if not all(p.is_file() for p in (design_path, cells_path, results_path, canary_path)):
        raise SystemExit(f"confirmation requires complete screen design/cells/canary/results in {run}")
    results = json.loads(results_path.read_text())
    canary = json.loads(canary_path.read_text())
    if not canary.get("all_passed"):
        raise SystemExit("H31 screen leakage canary did not pass")
    expected_hashes = {
        "design.json": sha256_file(design_path),
        "cells.jsonl": sha256_file(cells_path),
        "canary.json": sha256_file(canary_path),
    }
    if results.get("evidence_sha256") != expected_hashes:
        raise SystemExit("saved H31 screen summary does not bind the exact design, canary, and raw-cell files")
    if results.get("screen_gate_passed") is not True:
        raise SystemExit("H31 screen gate failed; confirmation is prohibited")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", default=None, help="run directory; defaults to evidence/h31_<stage>")
    args = ap.parse_args()
    run = Path(args.dir) if args.dir else ROOT / "evidence" / "h31_screen"
    design_path, cells_path, canary_path = run / "design.json", run / "cells.jsonl", run / "canary.json"
    if not all(p.exists() for p in (design_path, cells_path, canary_path)):
        raise SystemExit(f"missing H31 design, canary, or raw cell file in {run}")

    design = json.loads(design_path.read_text())
    canary = json.loads(canary_path.read_text())
    stage = design.get("stage")
    if stage not in EXPECTED_DRAWS:
        raise SystemExit(f"unknown H31 stage {stage!r}")
    if not canary.get("all_passed"):
        raise SystemExit("H31 leakage canary failed (AUC > 0.90)")

    screen = None
    if stage == "confirm":
        screen = verify_passing_screen(ROOT / "evidence" / "h31_screen")

    rows = [json.loads(line) for line in cells_path.read_text().splitlines() if line.strip()]
    expected_keys = {(fold, draw, arm) for fold in range(4) for draw in EXPECTED_DRAWS[stage] for arm in EXPECTED_ARMS}
    actual_keys = [(row.get("fold"), row.get("draw"), row.get("arm")) for row in rows]
    if len(rows) != 40 or set(actual_keys) != expected_keys:
        raise SystemExit(f"incomplete/duplicate H31 cells in {cells_path}: got {len(rows)} rows")

    lookup = {(r["fold"], r["draw"], r["arm"]): r for r in rows}
    by_arm: dict[str, dict] = {}
    fold_arm: dict[int, dict[str, dict[str, float]]] = {f: {} for f in range(4)}

    for arm in sorted(EXPECTED_ARMS):
        arm_rows = [r for r in rows if r["arm"] == arm]
        pooled = pooled_dti_summary(arm_rows, evaluator_version=EVALUATOR_VERSION)
        fold_dti = [
            float(np.mean([lookup[(fold, draw, arm)]["dti"] for draw in sorted(EXPECTED_DRAWS[stage])]))
            for fold in range(4)
        ]
        fold_arr = np.asarray(fold_dti, dtype=float)
        se_f = float(fold_arr.std(ddof=1) / np.sqrt(4))
        crit = float(t.ppf(0.975, 3))
        mean_dti = float(fold_arr.mean())
        by_arm[arm] = {
            "n_cells": len(arm_rows),
            "mean_dti": mean_dti,
            "mean_dti_95_ci": [mean_dti - crit * se_f, mean_dti + crit * se_f],
            "pooled": pooled,
            "sd_dti_cells": float(np.std([r["dti"] for r in arm_rows], ddof=1)),
            "mean_coverage": float(np.mean([r["coverage"] for r in arm_rows])),
            "mean_emitted": float(np.mean([r["emitted"] for r in arm_rows])),
            "mean_hug": float(np.mean([r["hug"] for r in arm_rows])),
            "mean_auc": float(np.mean([r["auc"] for r in arm_rows])),
            "by_fold_dti": fold_dti,
            "by_fold_hug": [
                float(np.mean([lookup[(fold, draw, arm)]["hug"] for draw in sorted(EXPECTED_DRAWS[stage])]))
                for fold in range(4)
            ],
        }
        for fold in range(4):
            fold_arm[fold][arm] = {
                m: float(np.mean([lookup[(fold, draw, arm)][m] for draw in sorted(EXPECTED_DRAWS[stage])]))
                for m in METRICS
            }

    factorial_fold_effects = [
        factorial_2x2_effects({arm: fold_arm[fold][arm]["dti"] for arm in H31_ARMS})
        for fold in range(4)
    ]
    effect_names = tuple(factorial_fold_effects[0])
    effects = {
        name: summarize_effect(np.array([entry[name] for entry in factorial_fold_effects], dtype=float))
        for name in effect_names
    }

    gate = h31_promotion_gate(
        by_arm["M1_C1"]["by_fold_dti"],
        {
            H31_CONTROL: by_arm[H31_CONTROL]["by_fold_dti"],
            "M0_C0": by_arm["M0_C0"]["by_fold_dti"],
        },
        by_arm["M1_C1"]["by_fold_hug"],
        {
            H31_CONTROL: by_arm[H31_CONTROL]["by_fold_hug"],
            "M0_C0": by_arm["M0_C0"]["by_fold_hug"],
        },
    )
    # Also compute pooled DTI gain of M1_C1 vs best same-run control
    pooled_cand = by_arm["M1_C1"]["pooled"]
    pooled_ctrl_no_tip = by_arm[H31_CONTROL]["pooled"]
    pooled_m0_c0 = by_arm["M0_C0"]["pooled"]
    best_pooled_ctrl = max(pooled_ctrl_no_tip["pooled_dti"], pooled_m0_c0["pooled_dti"])
    pooled_gain = float(pooled_cand["pooled_dti"] - best_pooled_ctrl)

    prior_screen_passed = bool(screen["screen_gate_passed"]) if screen is not None else True
    screen_gate_passed = bool(gate["paired_gate_passed"])
    confirmation_gate_passed = bool(gate["paired_gate_passed"] and prior_screen_passed) if stage == "confirm" else None

    evidence_hashes = {
        "design.json": sha256_file(design_path),
        "cells.jsonl": sha256_file(cells_path),
        "canary.json": sha256_file(canary_path),
    }
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evaluator_version": EVALUATOR_VERSION,
        "run_directory": str(run),
        "n_rows": len(rows),
        "stage": stage,
        "evidence_sha256": evidence_hashes,
        "leakage_canary": {
            "all_passed": canary["all_passed"],
            "threshold_max_auc": canary["threshold_max_auc"],
            "summary_by_feature": canary["summary_by_feature"],
        },
        "design": design,
        "arms": by_arm,
        "factorial_effects_by_fold": factorial_fold_effects,
        "factorial_effects": effects,
        "paired_promotion_gate": gate,
        "pooled_comparison": {
            "M1_C1_pooled_dti": pooled_cand["pooled_dti"],
            "M1_C1_formatted": pooled_cand["formatted_label"],
            "CTRL_NO_TIP_pooled_dti": pooled_ctrl_no_tip["pooled_dti"],
            "M0_C0_pooled_dti": pooled_m0_c0["pooled_dti"],
            "pooled_gain_vs_best_control": pooled_gain,
        },
        "screen_gate_passed": screen_gate_passed if stage == "screen" else prior_screen_passed,
        "confirmation_gate_passed": confirmation_gate_passed,
        "proxy_holdout_passed": confirmation_gate_passed if stage == "confirm" else False,
        "slot_eligible": False,
        "slot_decision": (
            "not eligible: screen only; fresh confirmation on draws 12,13 required"
            if stage == "screen" and screen_gate_passed
            else "screen gate failed; stop"
            if stage == "screen"
            else "screen + confirmation holdout gates passed; candidate GeoTIFF build and duplicate-lane audit permitted; weekly slot selection remains a separate human selector step"
            if confirmation_gate_passed
            else "confirmation gate failed; stop"
        ),
    }
    (run / "results.json").write_text(json.dumps(out, indent=1) + "\n")

    lines = [
        f"# H31-1 tip-preserved flank shielding × sub-scarp concordance — {stage} results",
        "",
        f"- **Evaluator:** `{EVALUATOR_VERSION}`",
        f"- **Draws:** `{sorted(EXPECTED_DRAWS[stage])}` across 4 spatial folds (`NW`, `NE`, `SW`, `SE`; {len(rows)} model cells)",
        f"- **Leakage canary (all standalone features AUC <= 0.90):** `{'PASS' if canary['all_passed'] else 'FAIL'}` "
        f"(max standalone AUC = {max(v['max_canary_auc'] for v in canary['summary_by_feature'].values()):.4f})",
        "",
        "| Arm | Pooled HOLDOUT-DTI (95% CI) | Withheld Positives | 4-Fold Mean DTI | NW | NE | SW | SE | Mean Hug | Coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ("CTRL_NO_TIP", "M0_C0", "M1_C0", "M0_C1", "M1_C1"):
        item = by_arm[arm]
        p = item["pooled"]
        folds = " | ".join(f"{v:.6f}" for v in item["by_fold_dti"])
        lines.append(
            f"| `{arm}` | **{p['pooled_dti']:.6f}** [{p['ci_95'][0]:.6f}, {p['ci_95'][1]:.6f}] | "
            f"{p['withheld_positives']:,} | {item['mean_dti']:.6f} | {folds} | "
            f"{item['mean_hug']:.4f} | {item['mean_coverage']:.4f} |"
        )
    lines += ["", "## Coded 2² Factorial Effects (4 spatial-fold blocks)", ""]
    for name, item in effects.items():
        lines.append(
            f"- **`{name}`**: `{item['mean']:+.6f}` HOLDOUT-DTI "
            f"(SE `{item['se_across_four_spatial_folds']:.6f}`, 95% CI `[{item['t_95_ci'][0]:+.6f}, {item['t_95_ci'][1]:+.6f}]`, "
            f"`{item['folds_positive']}/4` folds positive)"
        )
    lines += [
        "",
        "## Paired Promotion Gate (`M1_C1` vs per-fold best same-run control)",
        "",
        f"- **4-fold mean paired gain:** `{gate['mean_gain_vs_best_paired_control']:+.6f}` HOLDOUT-DTI",
        f"- **Pooled HOLDOUT-DTI gain:** `{pooled_gain:+.6f}` (`{pooled_cand['formatted_label']}`)",
        f"- **Positive folds:** `{gate['folds_positive']}/4`; **worst fold:** `{gate['worst_fold_gain']:+.6f}`",
        f"- **Catalogue-hugging (`hug`) change:** `{gate['mean_hug_share_delta']:+.4f}`",
        f"- **Stage gate verdict:** **`{'PASS' if gate['paired_gate_passed'] else 'FAIL'}`**",
        f"- **Slot status:** `{out['slot_decision']}`",
        "",
    ]
    (run / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
