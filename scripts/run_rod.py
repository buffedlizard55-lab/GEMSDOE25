#!/usr/bin/env python3
"""Run the single preregistered ROD-1 screen. No competition access or upload.

All model-independent inputs come from the shared feature cache. Refuses to
replace evidence. A lane stop means no writer call and no new hypothesis.
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from gems25.experiment import Cell, HGB_PARAMS, load_context  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.rod import build_rod  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, sha256_file, write_submission  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402
from gems25.validation import feature_canary, pooled_summary  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402
from validate_gem_candidate import (  # noqa: E402
    lane_check, lane_is_clear, load_registry_rasters, surface_lane_check, surface_lane_is_clear,
)

OUT = ROOT / "evidence" / "rod_2026-10-26"
DRAWS = (60, 61)


def save(name, value):
    # Every non-finite diagnostic is unavailable, never invalid JSON NaN.
    def clean(v):
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        if isinstance(v, list):
            return [clean(x) for x in v]
        if isinstance(v, float) and not np.isfinite(v):
            return None
        return v
    (OUT / name).write_text(json.dumps(clean(value), indent=2, allow_nan=False) + "\n")


def emit_grid(score, domain, visible):
    ridge = ridge_nms(score, domain, 1.0)
    top = select_top_positive(np.where(ridge & ~visible, score, 0), domain, int(round(.035*domain.sum())))
    return score_ordered_dots(score, top, 2.4)


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    ctx = load_context(work_dir())
    inputs = build_rod(ctx.static, ctx.static_names, ctx.foot)
    np.save(work_dir() / "rod_primary.npy", inputs["ROD_primary"])
    surface = np.zeros(ctx.foot.shape, np.float32)
    surface.ravel()[ctx.fi] = inputs["ROD_primary"]
    registry = load_registry_rasters()
    save("registry_inventory.json", [dict(file=r["file"], sha256=r["sha256"], path=str(r["path"].relative_to(ROOT))) for r in registry])
    evaluator = {p: sha256_file(ROOT / p) for p in (
        "src/gems25/metric.py", "src/gems25/holdout.py", "src/gems25/experiment.py", "src/gems25/validation.py",
        "src/gems25/rod.py", "scripts/run_rod.py")}
    card = dict(hypothesis="ROD-1 radiometric offset discontinuity", mechanism="Tangential registration improvement across a scarp",
                non_fault_mimic="Volcanic flow lobes, alluvial fan sorting, airborne mosaic seams",
                evaluator=evaluator, holdout_dti=None, ci95=None, withheld_positives=None,
                correlation_overlap_vs_registry=None, raster_sha256=None, validator_output=None,
                submission_name=None, note="ROD-1; automatic gates; no slot authorized.", verdict="negative",
                okay_to_submit=False, experiments=1, preregistration_commit="f32cf6d")

    def finish(reason):
        card["reason"] = reason
        card["elapsed_seconds"] = round(time.monotonic()-started, 1)
        save("run_card.json", card)
        print(reason, flush=True)

    print("Checking full surface against registry before placement", flush=True)
    surface_rows = surface_lane_check(ctx, surface, registry)
    save("surface_lane.json", surface_rows)
    card["correlation_overlap_vs_registry"] = dict(
        surface_max_abs_rho=max((r.get("abs_spearman") or 0 for r in surface_rows), default=None),
        surface_registry_count=len(surface_rows), final_dots=None,
        scope="available local registry; not proof that every sibling artifact is registered")
    if not surface_lane_is_clear(surface_rows):
        finish("DUPLICATE / UNVERIFIED surface; stopped before placement")
        return

    h34 = load_h34_sidecar(work_dir(), ctx.fi)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS) + [ctx.col["H27_tip"]]
    col_names = {v: k for k, v in ctx.col.items()}
    all_rows, canaries = [], []
    unique_truth = np.zeros(ctx.foot.shape, bool)
    with (OUT / "cells.jsonl").open("w") as sink:
        for fold in range(4):
            for draw in DRAWS:
                if time.monotonic()-started > 6000:
                    finish("Time guard: incomplete screen; no candidate authorized")
                    return
                cell = Cell(ctx, fold, draw, extras=True, h27=True)
                idx = np.concatenate([cell.auc_pos, cell.auc_neg])
                target = np.concatenate([np.ones(cell.auc_pos.size), np.zeros(cell.auc_neg.size)])
                checks = {}
                for name, values in inputs.items():
                    checks[name] = feature_canary(values[cell.q[idx]], target)
                for j in cols:
                    checks["incumbent:" + col_names[j]] = feature_canary(cell.Xq[idx, j], target)
                for j, name in enumerate(H34_NAMES):
                    checks["incumbent:" + name] = feature_canary(h34[j, cell.q[idx]], target)
                canaries.append(dict(fold=fold, draw=draw, features=checks))
                save("feature_canaries.json", canaries)
                if not all(r["passed"] for r in checks.values()):
                    finish("Feature-alone leakage canary failed; stop before trusting performance")
                    return
                unique_truth[cell.sl] |= cell.truth_c
                Xtr = np.hstack([cell.Xtr[:, cols], np.asarray(h34[:, cell.train_idx]).T])
                model = HistGradientBoostingClassifier(random_state=draw, **HGB_PARAMS).fit(Xtr, cell.y)
                del Xtr
                Xq = np.hstack([cell.Xq[:, cols], np.asarray(h34[:, cell.q]).T])
                pred = model.predict_proba(Xq)[:, 1].astype(np.float32)
                del Xq, model
                scores = {"H35": pred, "ROD": inputs["ROD_primary"][cell.q],
                          "OFFSET": inputs["ROD_offset"][cell.q], "SCARP": inputs["ROD_scarp"][cell.q],
                          "UNIFORM": np.full(cell.q.size, .5, np.float32)}
                for arm, values in scores.items():
                    s, top = cell.candidates(values, int(round(.035*cell.dom_c.sum())))
                    dots = score_ordered_dots(s, top, 2.4)
                    row = dict(fold=fold, draw=draw, arm=arm, **cell.evaluate(dots))
                    all_rows.append(row)
                    sink.write(json.dumps(row) + "\n")
                    sink.flush()
                    print(f"fold={fold} draw={draw} {arm} HOLDOUT-DTI={row['dti']:.6f}", flush=True)
                del cell, pred, scores, s, top, dots
                gc.collect()
    analysis = pooled_summary(all_rows)
    analysis["distinct_withheld_pixels"] = int(unique_truth.sum())
    analysis["evaluator"] = evaluator
    analysis["confirmation"] = "not run; screen alone is not promotion"
    save("analysis.json", analysis)
    result = analysis["arms"]["ROD"]
    card.update(holdout_dti=result["pooled_dti"], ci95=result["ci95"], withheld_positives=dict(
        occurrences=result["withheld_positive_occurrences"], distinct=int(unique_truth.sum())),
        holdout_label="HOLDOUT-DTI", performance_gate=analysis["screen_passed"])

    final = emit_grid(surface, ctx.foot, ctx.labels)
    # The exact emitted mask is hashed before any serialization. A hash is not a lane pass.
    card["candidate_mask_sha256"] = hashlib.sha256(np.packbits(final.ravel()).tobytes()).hexdigest()
    card["candidate_dots"] = int(final.sum())
    print("Checking final dots; strict rule, no density waiver", flush=True)
    lane = lane_check(ctx, final, final.astype(np.float32), registry)
    save("final_lane.json", lane)
    card["correlation_overlap_vs_registry"]["final_dots"] = dict(
        max_overlap=max(r.get("overlap_within_3px", 0) for r in lane),
        max_abs_rho=max(r.get("abs_spearman") or 0 for r in lane),
        flagged=[r["file"] for r in lane if r.get("duplicate", True)], count=len(lane))
    if not lane_is_clear(lane):
        finish("DUPLICATE-LANE: final dots fail literal overlap/rank gate; stopped, no TIFF written")
        return
    cid = content_id(final, ctx.foot, ctx.labels)
    name = make_filename("rod1-negative", "20261026", cid, "zeros")
    path = ROOT / "docs" / "downloads" / name
    write_submission(final, data_dir()/"sample_submission.tif", path, outside="zero")
    validation = check_file(path, data_dir()/"sample_submission.tif")
    save("validator.json", validation)
    card.update(submission_name=name, raster_sha256=validation["sha256"], validator_output=validation)
    finish("Lane-clean diagnostic only; no fresh confirmation or selector authorization; DO NOT SUBMIT")


if __name__ == "__main__":
    main()
