#!/usr/bin/env python3
"""Run the frozen H31-1 tip-preserved flank-shielding × multi-physics sub-scarp 2² screen or confirmation.

Preregistration: ``knowledge/14_preregistered_h31_flank_shielded_subscarp_factorial_2026-10-25.md``.
Includes the mandatory Protocol Rule 4 Leakage Canary (every standalone feature ROC-AUC <= 0.90)
and requires a clean committed worktree before fitting.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from gems25.experiment import Cell, HGB_PARAMS, N_NEG, load_context  # noqa: E402
from gems25.h31 import (  # noqa: E402
    EVALUATOR_VERSION,
    H31_BASE_EXTRAS,
    H31_FEATURE_NAMES,
    H31_SUB_INPUTS,
    H31_SURF_INPUTS,
)
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402

DRAWS = {"screen": [10, 11], "confirm": [12, 13]}
FOLDS = ["NW", "NE", "SW", "SE"]
DESIGN_SEED = 20261025
KFRAC = 0.035
MIN_DIST_PX = 2.4
FLANK_RADIUS_PX = 2.5
TIP_PRESERVE_THRESHOLD = 0.05
BASE_FAMILIES = "BDE"
CANARY_MAX_AUC = 0.90


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verified_cache_hashes(work: Path) -> dict[str, dict[str, int | str]]:
    """Refuse H31 fitting unless all derived caches match the pinned provenance record."""
    record_path = ROOT / "evidence" / "work_cache_hashes.json"
    if not record_path.exists():
        raise SystemExit(f"missing derived-cache provenance record: {record_path}")
    record = json.loads(record_path.read_text())
    required = (
        "static_ABCD.npy",
        "static_ABCD.npy.names.json",
        "addons.npy",
        "addons.npy.names.json",
        "bands/_footprint.npy",
        "bands/_labels.npy",
    )
    actual: dict[str, dict[str, int | str]] = {}
    for name in required:
        expected = record.get(name)
        path = work / name
        if not isinstance(expected, dict) or not path.is_file():
            raise SystemExit(f"missing pinned cache or cache hash: {name}")
        entry = {"sha256": file_sha256(path), "bytes": path.stat().st_size}
        if entry != {"sha256": expected.get("sha256"), "bytes": expected.get("bytes")}:
            raise SystemExit(f"derived cache differs from evidence/work_cache_hashes.json: {name}")
        actual[name] = entry
    return actual


def frozen_git_revision() -> str:
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"cannot record repository revision: {exc}") from exc
    if status.strip():
        raise SystemExit("refusing to fit with a dirty worktree; commit/freeze the design, code, and evidence first")
    return revision


def canonical_rows() -> list[dict]:
    return [
        {"arm": "CTRL_NO_TIP", "M": -1, "C": -1, "include_tip": False, "factorial_arm": False},
        {"arm": "M0_C0", "M": -1, "C": -1, "include_tip": True, "factorial_arm": True},
        {"arm": "M1_C0", "M": 1, "C": -1, "include_tip": True, "factorial_arm": True},
        {"arm": "M0_C1", "M": -1, "C": 1, "include_tip": True, "factorial_arm": True},
        {"arm": "M1_C1", "M": 1, "C": 1, "include_tip": True, "factorial_arm": True},
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=tuple(DRAWS), default="screen")
    ap.add_argument("--out", default=None, help="run directory; refuses to overwrite any existing run unless --resume")
    ap.add_argument("--resume", action="store_true", help="resume an interrupted run from complete 5-arm cells")
    args = ap.parse_args()
    revision = frozen_git_revision()
    draws = DRAWS[args.stage]
    if args.stage == "confirm":
        from scripts.analyze_h31_factorial import verify_passing_screen

        verify_passing_screen(ROOT / "evidence" / "h31_screen")

    out = Path(args.out) if args.out else ROOT / "evidence" / f"h31_{args.stage}"
    if out.exists() and (not out.is_dir() or any(out.iterdir())) and not args.resume:
        raise SystemExit(f"refusing to overwrite a nonempty H31 run directory: {out}; choose a fresh directory or --resume")
    out.mkdir(parents=True, exist_ok=True)
    design_path, cells_path, canary_path = out / "design.json", out / "cells.jsonl", out / "canary.json"
    existing_by_cell: dict[tuple[int, int], list[dict]] = {}
    resume_src = cells_path if cells_path.exists() else (work_dir() / f"_h31_{args.stage}_resume.jsonl")
    if args.resume and resume_src.exists():
        for line in resume_src.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                existing_by_cell.setdefault((int(r["fold"]), int(r["draw"])), []).append(r)
        existing_by_cell = {k: v for k, v in existing_by_cell.items() if len(v) == 5}

    work = work_dir()
    cache_hashes = verified_cache_hashes(work)
    ctx = load_context(work)
    ctx.ensure_h31_subscarp()
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("H26 add-on cache is absent or malformed; run scripts/build_addons.py first")
    if not np.isfinite(ctx.h31_subscarp).all() or not np.any(ctx.h31_subscarp > 0):
        raise SystemExit("H31 subscarp concordance feature is empty or nonfinite")

    canonical = canonical_rows()
    order = np.random.default_rng(DESIGN_SEED).permutation(len(canonical)).tolist()
    randomized = [canonical[i] for i in order]
    base_cols = ctx.columns(BASE_FAMILIES) + ctx.named(H31_BASE_EXTRAS)
    tip_col = ctx.named(["H27_tip"])
    m_cols = ctx.named(H31_FEATURE_NAMES)
    fit_cols = {
        "CTRL_NO_TIP": base_cols,
        "M0": base_cols + tip_col,
        "M1": base_cols + tip_col + m_cols,
    }
    canary_feature_names = [*H31_FEATURE_NAMES, "H27_tip", *H31_SURF_INPUTS, *H31_SUB_INPUTS]

    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    input_hashes = {
        row["id"]: {"sha256": row["sha256"], "bytes": row["bytes"]}
        for row in manifest["files"]
    }
    prereg_rel = "knowledge/14_preregistered_h31_flank_shielded_subscarp_factorial_2026-10-25.md"
    design = {
        "code_revision": revision,
        "clean_worktree_before_fit": True,
        "evaluator_version": EVALUATOR_VERSION,
        "derived_cache_sha256_verified": cache_hashes,
        "hypothesis": "H31-1 tip-preserved lateral-flank shielding × multi-physics subdued-scarp concordance",
        "stage": args.stage,
        "preregistration": prereg_rel,
        "preregistration_sha256": file_sha256(ROOT / prereg_rel),
        "draws": draws,
        "spatial_folds": FOLDS,
        "design_seed": DESIGN_SEED,
        "canonical_matrix": canonical,
        "row_order_zero_based": order,
        "randomized_matrix": randomized,
        "factorial_rows": ["M0_C0", "M1_C0", "M0_C1", "M1_C1"],
        "control_row": "CTRL_NO_TIP",
        "fixed_model_families": BASE_FAMILIES,
        "fixed_addons": H31_BASE_EXTRAS,
        "fixed_tip_control": "H27_tip",
        "h31_features": H31_FEATURE_NAMES,
        "canary_max_auc_threshold": CANARY_MAX_AUC,
        "hgb_parameters": {
            "max_iter": HGB_PARAMS["max_iter"],
            "learning_rate": HGB_PARAMS["learning_rate"],
            "max_leaf_nodes": HGB_PARAMS["max_leaf_nodes"],
            "min_samples_leaf": HGB_PARAMS["min_samples_leaf"],
            "l2_regularization": HGB_PARAMS["l2_regularization"],
            "class_weight": {str(key): value for key, value in HGB_PARAMS["class_weight"].items()},
            "early_stopping": HGB_PARAMS["early_stopping"],
            "fit_seed": "draw",
            "negative_sample_count_max": N_NEG,
        },
        "emission": {
            "method": "Hessian ridge NMS → (optional tip-preserved flank shield) → top-K → score-ordered Poisson-disk",
            "nms_sigma_px": 1.0,
            "k_fraction": KFRAC,
            "min_distance_px": MIN_DIST_PX,
            "flank_radius_px": FLANK_RADIUS_PX,
            "tip_preserve_threshold": TIP_PRESERVE_THRESHOLD,
            "drop_visible_catalogue": True,
        },
        "subscarp_feature_diagnostics": ctx.h31_subscarp_diag,
        "data_manifest_sha256_and_bytes": input_hashes,
        "environment": {
            "python": sys.version.split()[0],
            "numpy": package_version("numpy"),
            "scipy": package_version("scipy"),
            "scikit-learn": package_version("scikit-learn"),
            "rasterio": package_version("rasterio"),
        },
    }
    design_path.write_text(json.dumps(design, indent=1) + "\n")

    t_all = time.time()
    canary_by_cell: list[dict] = []
    with cells_path.open("w") as sink:
        for fold in range(4):
            for draw_seed in draws:
                cell = Cell(ctx, fold, draw_seed, extras=True, h27=True, h30=False, h31=True)
                # 1. Protocol Rule 4: Leakage Canary on each feature alone BEFORE model fitting
                cell_canary = {}
                for fname in canary_feature_names:
                    c_res = cell.feature_canary_auc(ctx.col[fname])
                    cell_canary[fname] = c_res
                    if c_res["canary_auc"] > CANARY_MAX_AUC:
                        raise SystemExit(
                            f"LEAKAGE CANARY VIOLATION: feature {fname} has holdout AUC "
                            f"{c_res['canary_auc']:.4f} > {CANARY_MAX_AUC} in fold {fold} draw {draw_seed}"
                        )
                canary_by_cell.append({"fold": fold, "fold_name": FOLDS[fold], "draw": draw_seed, "features": cell_canary})

                if (fold, draw_seed) in existing_by_cell:
                    for row in existing_by_cell[(fold, draw_seed)]:
                        sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(
                        f"[{args.stage} fold {fold} draw {draw_seed} RESUMED 5/5 rows] "
                        f"elapsed={time.time() - t_all:.0f}s",
                        flush=True,
                    )
                    del cell
                    continue

                # 2. Fit the 3 unique HGB models for this cell
                preds: dict[str, tuple[np.ndarray, dict]] = {}
                for m_key, cols in fit_cols.items():
                    preds[m_key] = cell.fit_predict(cols, seed=draw_seed)

                k = int(round(KFRAC * cell.dom_c.sum()))
                for run_order, cfg in enumerate(randomized, start=1):
                    arm = cfg["arm"]
                    if arm == "CTRL_NO_TIP":
                        p, timing = preds["CTRL_NO_TIP"]
                    elif cfg["M"] == -1:
                        p, timing = preds["M0"]
                    else:
                        p, timing = preds["M1"]

                    if cfg["C"] == -1:
                        score_crop, candidates = cell.candidates(p, k)
                        shield_diag = None
                    else:
                        score_crop, candidates, shield_diag = cell.candidates_flank_shielded(
                            p, k, flank_radius_px=FLANK_RADIUS_PX, tip_preserve_threshold=TIP_PRESERVE_THRESHOLD
                        )
                    emitted = score_ordered_dots(score_crop, candidates, MIN_DIST_PX)
                    row = {
                        "stage": args.stage,
                        "fold": fold,
                        "fold_name": FOLDS[fold],
                        "draw": draw_seed,
                        "run_order": run_order,
                        "arm": arm,
                        "M": cfg["M"],
                        "C": cfg["C"],
                        "include_tip": cfg["include_tip"],
                        "factorial_arm": cfg["factorial_arm"],
                        "design_seed": DESIGN_SEED,
                        "k_fraction": KFRAC,
                        "min_distance_px": MIN_DIST_PX,
                        "flank_radius_px": FLANK_RADIUS_PX if cfg["C"] == 1 else 0.0,
                        "auc": cell.auc(p),
                        **cell.evaluate(emitted),
                        "offflank_diagnostics": cell.offflank_diag,
                        "shield_diagnostics": shield_diag,
                        **timing,
                    }
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(
                        f"[{args.stage} fold {fold} draw {draw_seed} row {run_order}/5 {arm}] "
                        f"DTI={row['dti']:.6f} emitted={row['emitted']} hug={row['hug']:.3f} "
                        f"elapsed={time.time() - t_all:.0f}s",
                        flush=True,
                    )
                del cell

    # Summarize leakage canary across all 8 cells
    canary_summary = {}
    for fname in canary_feature_names:
        vals = [c["features"][fname]["canary_auc"] for c in canary_by_cell]
        raws = [c["features"][fname]["raw_auc"] for c in canary_by_cell]
        canary_summary[fname] = {
            "mean_canary_auc": float(np.mean(vals)),
            "max_canary_auc": float(np.max(vals)),
            "mean_raw_auc": float(np.mean(raws)),
            "passed_threshold_0_90": bool(np.max(vals) <= CANARY_MAX_AUC),
        }
    canary_doc = {
        "stage": args.stage,
        "threshold_max_auc": CANARY_MAX_AUC,
        "all_passed": all(v["passed_threshold_0_90"] for v in canary_summary.values()),
        "summary_by_feature": canary_summary,
        "by_cell": canary_by_cell,
    }
    canary_path.write_text(json.dumps(canary_doc, indent=1) + "\n")
    print(f"DONE: raw cells in {cells_path}, canary in {canary_path}", flush=True)


if __name__ == "__main__":
    main()
