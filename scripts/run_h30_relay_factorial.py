#!/usr/bin/env python3
"""Run the frozen H30-1 paired-relay × terrain 2² screen or confirmation.

Preregistration: ``knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md``.
The primary candidate is T+P+S. A confirmation on fresh draws is permitted only after the screen gate passes.
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
sys.path.insert(0, str(ROOT / "src"))
from gems25.experiment import Cell, HGB_PARAMS, N_NEG, load_context  # noqa: E402
from gems25.h30 import H30_BASE_EXTRAS  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402

DRAWS = {"screen": [6, 7], "confirm": [8, 9]}
FOLDS = ["NW", "NE", "SW", "SE"]
DESIGN_SEED = 20261004
KFRAC = 0.035
MIN_DIST_PX = 2.4
BASE_FAMILIES = "BDE"


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
    """Refuse H30 fitting unless all derived caches match the pinned, previously audited build."""
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
        {"arm": "BASE_NO_TIP", "P": -1, "S": -1, "include_tip": False, "factorial_arm": False},
        {"arm": "T_BASE", "P": -1, "S": -1, "include_tip": True, "factorial_arm": True},
        {"arm": "T_PLUS_P", "P": 1, "S": -1, "include_tip": True, "factorial_arm": True},
        {"arm": "T_PLUS_S", "P": -1, "S": 1, "include_tip": True, "factorial_arm": True},
        {"arm": "T_PLUS_P_S", "P": 1, "S": 1, "include_tip": True, "factorial_arm": True},
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", choices=tuple(DRAWS), default="screen")
    ap.add_argument("--out", default=None, help="run directory; refuses to overwrite any existing run")
    args = ap.parse_args()
    revision = frozen_git_revision()
    draws = DRAWS[args.stage]
    if args.stage == "confirm":
        screen = ROOT / "evidence" / "h30_relay_screen" / "results.json"
        if not screen.exists():
            raise SystemExit("confirmation requires an analyzed, passing H30 screen on draws 6,7")
        prior = json.loads(screen.read_text())
        prior_design = prior.get("design", {})
        prior_gate = prior.get("paired_promotion_gate", {})
        if not (
            prior.get("stage") == "screen"
            and prior_design.get("stage") == "screen"
            and prior_design.get("draws") == DRAWS["screen"]
            and prior.get("n_rows") == 40
            and prior.get("screen_gate_passed") is True
            and prior_gate.get("paired_gate_passed") is True
        ):
            raise SystemExit("confirmation requires a complete passing H30 screen on the frozen draws 6,7")

    out = Path(args.out) if args.out else ROOT / "evidence" / f"h30_relay_{args.stage}"
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise SystemExit(f"refusing to overwrite a nonempty H30 run directory: {out}; choose a fresh directory")
    out.mkdir(parents=True, exist_ok=True)
    design_path, cells_path = out / "design.json", out / "cells.jsonl"

    work = work_dir()
    cache_hashes = verified_cache_hashes(work)
    ctx = load_context(work)
    ctx.ensure_h30_scarp()
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("H26 add-on cache is absent or malformed; run scripts/build_addons.py first")
    required = {"L_step_max", "L_cross_max", "L_coh100"}
    if not required.issubset(ctx.static_names):
        raise SystemExit(f"static cache lacks H30 terrain inputs: {sorted(required - set(ctx.static_names))}")
    if not np.isfinite(ctx.h30_scarp).all() or not np.any(ctx.h30_scarp > 0):
        raise SystemExit("H30 scarp-persistence feature is empty or nonfinite")
    if ctx.h30_scarp_diag.get("missing_inputs"):
        raise SystemExit(f"H30 scarp inputs missing: {ctx.h30_scarp_diag['missing_inputs']}")

    canonical = canonical_rows()
    order = np.random.default_rng(DESIGN_SEED).permutation(len(canonical)).tolist()
    randomized = [canonical[i] for i in order]
    base_cols = ctx.columns(BASE_FAMILIES) + ctx.named(H30_BASE_EXTRAS)
    h27_tip_col = ctx.named(["H27_tip"])
    p_col = ctx.named(["H30_pair_bridge"])
    s_col = ctx.named(["H30_scarp_persistence"])
    arm_cols = {
        "BASE_NO_TIP": base_cols,
        "T_BASE": base_cols + h27_tip_col,
        "T_PLUS_P": base_cols + h27_tip_col + p_col,
        "T_PLUS_S": base_cols + h27_tip_col + s_col,
        "T_PLUS_P_S": base_cols + h27_tip_col + p_col + s_col,
    }
    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    input_hashes = {
        row["id"]: {"sha256": row["sha256"], "bytes": row["bytes"]}
        for row in manifest["files"]
    }
    design = {
        "code_revision": revision,
        "clean_worktree_before_fit": True,
        "derived_cache_sha256_verified": cache_hashes,
        "hypothesis": "H30-1 paired visible-fault relay bridge × LiDAR scarp persistence",
        "stage": args.stage,
        "preregistration": "knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md",
        "preregistration_sha256": file_sha256(ROOT / "knowledge" / "11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md"),
        "draws": draws,
        "spatial_folds": FOLDS,
        "design_seed": DESIGN_SEED,
        "canonical_matrix": canonical,
        "row_order_zero_based": order,
        "randomized_matrix": randomized,
        "factorial_rows": ["T_BASE", "T_PLUS_P", "T_PLUS_S", "T_PLUS_P_S"],
        "control_row": "BASE_NO_TIP",
        "fixed_model_families": BASE_FAMILIES,
        "fixed_addons": H30_BASE_EXTRAS,
        "fixed_tip_control": "H27_tip",
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
            "method": "Hessian ridge NMS → top-K → score-ordered Poisson-disk",
            "nms_sigma_px": 1.0,
            "k_fraction": KFRAC,
            "min_distance_px": MIN_DIST_PX,
            "drop_visible_catalogue": True,
        },
        "paired_bridge_definition": {
            "endpoint_source": "draw.visible only",
            "connectivity": 8,
            "distinct_visible_components": True,
            "distance_px": [2.0, 15.0],
            "minimum_tip_coherence": 0.25,
            "minimum_cos2_strike_compatibility": 0.5,
            "minimum_cross_strike_fraction": 0.35,
            "pair_weight": "exp(-distance/8) × clip((cos2-0.5)/0.5,0,1) × sqrt(coherence_1*coherence_2) × cross_strike_fraction",
            "segment_sampling_max_step_px": 0.5,
            "buffer_disk_radius_px": 2,
        },
        "terrain_feature": "clip(scale(L_step_max) * scale(L_cross_max) * scale(L_coh100), 0, 1); Context.scale 1st/99th percentiles from default_rng(1) sample of 200000 footprint pixels",
        "terrain_scaling_parameters_1st_99th_percentile": {
            name: list(ctx.scale[name]) for name in ("L_step_max", "L_cross_max", "L_coh100")
        },
        "terrain_feature_diagnostics": ctx.h30_scarp_diag,
        "data_manifest_sha256_and_bytes": input_hashes,
        "environment": {
            "python": sys.version.split()[0],
            "numpy": package_version("numpy"),
            "scipy": package_version("scipy"),
            "scikit-learn": package_version("scikit-learn"),
            "rasterio": package_version("rasterio"),
        },
        "notes": (
            "All five arms in each fold/draw share one Cell, one visible catalogue, and one seeded training sample. "
            "The P/S contrasts are analyzed only on the four T_BASE factorial rows; BASE_NO_TIP is a second same-run control. "
            "Historical H27/H28 values are contextual, not cross-draw promotion baselines."
        ),
    }
    design_path.write_text(json.dumps(design, indent=1) + "\n")  # Freeze exact matrix before any model fit.

    t_all = time.time()
    with cells_path.open("w") as sink:
        for fold in range(4):
            for draw_seed in draws:
                cell = Cell(ctx, fold, draw_seed, extras=True, h27=True, h30=True)
                k = int(round(KFRAC * cell.dom_c.sum()))
                for run_order, cfg in enumerate(randomized, start=1):
                    arm = cfg["arm"]
                    p, timing = cell.fit_predict(arm_cols[arm], seed=draw_seed)
                    score_crop, candidates = cell.candidates(p, k)
                    emitted = score_ordered_dots(score_crop, candidates, MIN_DIST_PX)
                    row = {
                        "stage": args.stage,
                        "fold": fold,
                        "fold_name": FOLDS[fold],
                        "draw": draw_seed,
                        "run_order": run_order,
                        "arm": arm,
                        "P": cfg["P"],
                        "S": cfg["S"],
                        "include_tip": cfg["include_tip"],
                        "factorial_arm": cfg["factorial_arm"],
                        "design_seed": DESIGN_SEED,
                        "k_fraction": KFRAC,
                        "min_distance_px": MIN_DIST_PX,
                        "auc": cell.auc(p),
                        **cell.evaluate(emitted),
                        "pair_diagnostics": cell.bridge_diag,
                        **timing,
                    }
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(
                        f"[{args.stage} fold {fold} draw {draw_seed} row {run_order}/5 {arm}] "
                        f"DTI={row['dti']:.6f} emitted={row['emitted']} "
                        f"fit={row['fit_s']:.1f}s elapsed={time.time() - t_all:.0f}s",
                        flush=True,
                    )
                del cell
    print(f"DONE: raw cells in {cells_path}", flush=True)


if __name__ == "__main__":
    main()
