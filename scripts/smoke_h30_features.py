#!/usr/bin/env python3
"""Run the registered H30 feature-construction smoke test; never fits a model or evaluates DTI."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems25.experiment import Cell, load_context  # noqa: E402
from gems25.holdout import FOLD_NAMES  # noqa: E402
from gems25.paths import work_dir  # noqa: E402
from run_h30_relay_factorial import verified_cache_hashes  # noqa: E402


FEATURE_COLUMNS = ("H27_tip", "H30_pair_bridge", "H30_scarp_persistence")
SOURCE_IDS = ("training_features", "labels", "ext_lidar_scarp_features_u8")


def main() -> None:
    work = work_dir()
    cache_hashes = verified_cache_hashes(work)
    ctx = load_context(work)
    if ctx.addon is None or ctx.addon.shape != (5, ctx.fi.size):
        raise SystemExit("H26 add-on cache is absent or malformed; run scripts/build_addons.py first")

    fold, draw = 0, 6
    cell = Cell(ctx, fold, draw, extras=True, h27=True, h30=True)
    if cell.Xtr.shape[1] != cell.Xq.shape[1]:
        raise SystemExit("training and test feature widths do not match")
    columns = {}
    for name in FEATURE_COLUMNS:
        col = ctx.col[name]
        train = cell.Xtr[:, col]
        test = cell.Xq[:, col]
        if not np.isfinite(train).all() or not np.isfinite(test).all():
            raise SystemExit(f"nonfinite feature values found in {name}")
        columns[name] = {
            "column": int(col),
            "train_nonzero": int(np.count_nonzero(train)),
            "test_nonzero": int(np.count_nonzero(test)),
            "all_train_values_finite": True,
            "all_test_values_finite": True,
        }

    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    input_hashes = {
        row["id"]: row["sha256"] for row in manifest["files"] if row["id"] in SOURCE_IDS
    }
    evidence = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": "real-data H30 feature-construction smoke test",
        "model_fit_executed": False,
        "dti_evaluated": False,
        "preregistration": "knowledge/11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md",
        "cell": {
            "fold": fold,
            "fold_name": FOLD_NAMES[fold],
            "draw": draw,
            "features_enabled": ["extras", "H27", "H30"],
            "prep_seconds": round(float(cell.prep_seconds), 2),
            "Xtr_shape": list(cell.Xtr.shape),
            "Xq_shape": list(cell.Xq.shape),
        },
        "input_sha256_from_registry_data_manifest": input_hashes,
        "derived_cache_sha256_verified": cache_hashes,
        "input_provenance_caveat": (
            "Training and label rasters are hash-pinned owner mirrors, not organizer-authenticated. "
            "The LiDAR scarp feature raster is owner-derived from 3DEP tiles and is not a raw USGS rebuild."
        ),
        "terrain_scales_from_context": {
            name: list(ctx.scale[name]) for name in ("L_step_max", "L_cross_max", "L_coh100")
        },
        "h30_scarp_feature_diagnostics": {
            **ctx.h30_scarp_diag,
            "range": [float(ctx.h30_scarp.min(initial=0.0)), float(ctx.h30_scarp.max(initial=0.0))],
        },
        "h30_pair_bridge_diagnostics": cell.bridge_diag,
        "feature_column_checks": columns,
        "interpretation": (
            "One fold/draw confirmed aligned train/test feature matrices, finite H30 columns, and nonempty feature fields. "
            "This is an engineering smoke test only: no model was fitted, no holdout DTI was computed, and it does not "
            "validate scientific or competition performance."
        ),
    }
    out = ROOT / "evidence" / "h30_feature_smoke.json"
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"H30 feature smoke saved: {out.relative_to(ROOT)}; Xtr={cell.Xtr.shape}, Xq={cell.Xq.shape}; no fit/DTI")


if __name__ == "__main__":
    main()
