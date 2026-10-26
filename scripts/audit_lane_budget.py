#!/usr/bin/env python3
"""Compute the exact dot budget implied by the literal 70%-within-3-px lane rule.

Reads only restored, SHA-pinned inputs (template, catalogue, registry rasters).
Writes a machine-readable receipt and a run card; it never writes a submission
TIF, never contacts DrivenData, and never treats the arithmetic bound as proof of
uniqueness.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from gems25.lane_budget import halo_budget, rule_can_pass  # noqa: E402
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import check_file, sha256_file  # noqa: E402
from validate_gem_candidate import load_registry_rasters  # noqa: E402

OUT = ROOT / "evidence" / "lane_budget_2026-10-26"
CANDIDATE_BUDGETS = (38854, 44090, 59472, 70524)


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    template = data_dir() / "sample_submission.tif"
    faults = data_dir() / "existing_faults.tif"
    with rasterio.open(template) as t:
        foot = np.isfinite(t.read(1))
        grid = dict(crs=str(t.crs), shape=list(t.shape), transform=list(t.transform)[:6])
    with rasterio.open(faults) as f:
        visible = np.nan_to_num(f.read(1)) > 0
    if visible.shape != foot.shape:
        raise SystemExit("fault catalogue and template grids differ")
    domain = foot & ~visible

    rows = []
    for reg in load_registry_rasters():
        arr = np.nan_to_num(reg["arr"] if "arr" in reg else _read(reg)).astype(np.float32)
        if arr.shape != foot.shape:
            rows.append(dict(file=reg["file"], skipped="shape differs from template"))
            continue
        b = halo_budget(domain, (arr > 0) & foot)
        b.update(file=reg["file"], sha256=reg["sha256"],
                 budgets={str(k): dict(can_pass=rule_can_pass(k, b["uncovered_pixels"])) for k in CANDIDATE_BUDGETS})
        rows.append(b)
    if not rows or any("skipped" in r for r in rows):
        raise SystemExit("registry incomplete or contains a non-grid raster; refusing to report a budget")

    best = min(rows, key=lambda r: r["max_feasible_unique_dots"])
    summary = dict(
        generated_utc=datetime.now(timezone.utc).isoformat(),
        evidence_class="COMPUTED arithmetic bound on the literal lane rule; not a holdout score",
        grid=grid, template_footprint_pixels=int(foot.sum()), catalogue_pixels=int(visible.sum()),
        eligible_domain_pixels=int(domain.sum()),
        rule=dict(radius_px=3.0, overlap_cap=0.7,
                  statement="duplicate if >70% of unique dots lie within 3 px of a registry raster's dots"),
        registry_rasters=rows,
        binding_raster=dict(file=best["file"], sha256=best["sha256"],
                            uncovered_pixels=best["uncovered_pixels"],
                            coverage_fraction=best["coverage_fraction"],
                            max_feasible_unique_dots=best["max_feasible_unique_dots"]),
        interpretation=("Any candidate with more unique dots than the binding raster's "
                        "max_feasible_unique_dots cannot satisfy the literal rule, whatever its "
                        "geology, spacing or rank correlation. Passing this bound is necessary, "
                        "never sufficient: the rule must still be measured on the final dots, and "
                        "|Spearman| > 0.90 also fails. Moving dots to uncovered pixels to evade the "
                        "check would optimise the registry, not geology."),
    )
    save("budget.json", summary)

    featured = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
    primary = next(f for f in featured if f["role"] == "primary")
    path = ROOT / primary["path"]
    revalidation = dict(role="existing artifact revalidation; NOT a new raster",
                        file=primary["file"], sha256_file=sha256_file(path),
                        matches_registry_entry=sha256_file(path) == primary["sha256"],
                        validator=check_file(path, template),
                        positive_pixels=int((np.nan_to_num(_read(dict(path=path))) > 0).sum()))
    save("featured_revalidation.json", revalidation)

    card = dict(
        hypothesis="Literal parallel-run lane rule implies a maximum feasible dot count",
        mechanism=("With K unique dots and U eligible pixels outside a registry halo, at most U "
                   "dots can be outside, so the rule requires 10*max(0,K-U) <= 7*K; the largest "
                   "K satisfying this is an exact upper bound independent of geology or model."),
        non_fault_mimic="Not applicable: an arithmetic feasibility bound is not a geological feature.",
        evaluator=None, holdout_dti=None, ci95=None, withheld_positives=None,
        correlation_overlap_vs_registry=dict(
            binding_raster=best["file"], uncovered_pixels=best["uncovered_pixels"],
            coverage_fraction=best["coverage_fraction"],
            scope="restored local registry only; not proof every sibling artifact is registered"),
        raster_sha256=None, validator_output=None, submission_name=None,
        note="No new TIF; literal lane budget audit only. DO NOT SUBMIT.",
        verdict="negative", okay_to_submit=False, experiments=0,
        preregistration_commit="d1c2bd7",
        holdout_label=None,
        reason=("No new geological candidate was run: the literal 70% rule cannot be met by "
                f"candidates above {best['max_feasible_unique_dots']:,} unique dots against "
                f"{best['file']}. No TIFF was written and no weekly slot is authorized."),
        elapsed_seconds=round(time.monotonic() - started, 1),
    )
    save("run_card.json", card)
    print(json.dumps(dict(binding=summary["binding_raster"], domain=summary["eligible_domain_pixels"]), indent=1))


def _read(reg):
    with rasterio.open(reg["path"]) as src:
        return src.read(1)


if __name__ == "__main__":
    main()
