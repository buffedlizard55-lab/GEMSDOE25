#!/usr/bin/env python3
"""Fail-closed final-dot lane audit against the restored, declared registry.

A duplicate is any reference with |Spearman| > .90 or >70% of candidate
positive pixels within 3 pixels. Missing pins, wrong grids, invalid data and
undefined correlations are not evidence of uniqueness. The process exits
nonzero on a duplicate OR an incomplete audit; a separate surface-stage audit is
also required. --reference is for diagnosing a known pair, never clearance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import EXPECTED  # noqa: E402

RHO_MAX, OVERLAP_MAX, OVERLAP_DIST = 0.90, 0.70, 3.0


def sha256(p: Path) -> str:
    digest = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def registry_rasters() -> list[Path]:
    """List locally available registry files, including byte-identical paths.

    Keeping both paths matters when the candidate itself is in the registry:
    dropping duplicates first can hide an earlier byte-identical reference.
    """
    paths = []
    for sub in ("scored", "calibration", "research", "artifacts", "registry_top"):
        paths.extend(sorted((data_dir() / sub).glob("*.tif")))
    paths.extend(sorted((ROOT / "docs" / "downloads").glob("*.tif")))
    return paths


def declared_hashes() -> set[str]:
    """Inventory hash-pinned historical references; no claim about unlisted sites."""
    ledger = json.loads((ROOT / "registry/artifact_ledger.json").read_text())
    top = json.loads((ROOT / "registry/top_scorer_sources.json").read_text())
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())
    submissions = json.loads((ROOT / "registry/submissions.json").read_text())
    extra = json.loads((ROOT / "registry/lane_reference_pins.json").read_text())
    mirrors = json.loads((ROOT / "registry/artifact_mirrors.json").read_text())
    required_ids = {row.get("id") for row in mirrors["mirrors"]} | set(mirrors["already_pinned_locally"]["ids"])
    ledger_ids = {row.get("id") for row in ledger["artifacts"]}
    if None in required_ids or not required_ids.issubset(ledger_ids):
        raise ValueError("declared artifact mirror is missing from the hash-pinned ledger")
    values = [row.get("sha256") for row in ledger["artifacts"]]
    values += [row.get("sha256") for row in top["rasters"]]
    values += [row.get("sha256") for row in manifest["files"] if row.get("group") == "scored"]
    values += [row.get("sha256") for row in submissions["files"]]
    values += [row.get("sha256") for row in extra["rasters"]]
    if any(not isinstance(s, str) or len(s) != 64 or any(c not in "0123456789abcdef" for c in s) for s in values):
        raise ValueError("a declared reference is missing a valid SHA-256 pin")
    return set(values)


def validate_template(path: Path) -> str:
    """Require the pinned owner-mirror grid; matching a bad template is not clearance."""
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())["files"]
    entries = [x for x in manifest if x.get("id") == "sample_submission"]
    if len(entries) != 1 or not isinstance(entries[0].get("sha256"), str):
        raise ValueError("missing or ambiguous template SHA-256 pin")
    entry = entries[0]
    digest = sha256(path)
    if digest != entry["sha256"]:
        raise ValueError("template SHA-256 does not match the declared owner-mirror pin")
    with rasterio.open(path) as src:
        if (src.count != 1 or src.crs is None or src.crs.to_epsg() != EXPECTED["epsg"]
                or src.shape != EXPECTED["shape"] or tuple(src.transform)[:6] != EXPECTED["transform"]
                or int(np.isfinite(src.read(1)).sum()) != EXPECTED["footprint_pixels"]):
            raise ValueError("template CRS, shape, transform or footprint does not match expected grid")
    return digest


def registry_inventory(paths: list[Path], expected: set[str]) -> dict:
    present = {sha256(p) for p in paths}
    missing = sorted(expected - present)
    manifest_sha = hashlib.sha256("\n".join(sorted(expected)).encode("ascii")).hexdigest() if expected else None
    return dict(declared_hashes=len(expected), available_files=len(paths), registry_manifest_sha256=manifest_sha,
                missing_sha256=missing, complete=bool(expected) and not missing,
                scope="declared pinned registry only; not every submission on every site")


def compare_arrays(candidate: np.ndarray, reference: np.ndarray, footprint: np.ndarray) -> dict:
    """Literal comparison. Undefined rank or nonfinite footprint values fail closed."""
    cv, rv, foot = np.asarray(candidate), np.asarray(reference), np.asarray(footprint, dtype=bool)
    if foot.ndim != 2 or cv.shape != foot.shape or rv.shape != foot.shape:
        raise ValueError("candidate/reference/footprint must have matching 2-D shapes")
    if not foot.any() or not np.isfinite(cv[foot]).all() or not np.isfinite(rv[foot]).all():
        raise ValueError("empty footprint or nonfinite candidate/reference within footprint")
    if (cv[foot] < 0).any() or (cv[foot] > 1).any():
        raise ValueError("candidate values inside footprint must be within [0,1]")
    if (cv[~foot] > 0).any():
        raise ValueError("candidate has positive values outside the footprint")
    cand_dots = (cv > 0) & foot
    if not cand_dots.any():
        raise ValueError("empty candidate cannot pass a lane audit")
    rdots = (rv > 0) & foot
    # The mandate is a threshold over the entire footprint, not a sample that
    # could miss a correlation just above the limit.
    cvals, rvals = cv[foot], rv[foot]
    if not len(cvals) or np.ptp(cvals) == 0 or np.ptp(rvals) == 0:
        rho = None
    else:
        value = float(spearmanr(cvals, rvals).statistic)
        rho = value if np.isfinite(value) else None
    # A reference with no positive pixels has no halo; rank still has to be defined.
    dist = distance_transform_edt(~rdots) if rdots.any() else np.full(foot.shape, np.inf)
    overlap = float((dist[cand_dots] <= OVERLAP_DIST).mean())
    coverage = float((dist[foot] <= OVERLAP_DIST).mean())
    reverse_dist = distance_transform_edt(~cand_dots)
    reverse = float((reverse_dist[rdots] <= OVERLAP_DIST).mean()) if rdots.any() else 0.0
    flag_rank = rho is None or abs(rho) > RHO_MAX
    flag_overlap = overlap > OVERLAP_MAX
    return dict(spearman=rho, dots_within_3px=overlap,
                registry_dots_within_3px_of_candidate=reverse,
                registry_dots=int(rdots.sum()), halo_coverage_3px=coverage,
                flag_rank=flag_rank, rank_undefined=rho is None, flag_overlap=flag_overlap,
                duplicate=bool((rho is not None and abs(rho) > RHO_MAX) or flag_overlap),
                # This number is diagnostic and never changes the literal decision.
                symmetric_min_overlap_3px=min(overlap, reverse))


def _read_aligned(path: Path, template_profile: tuple, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        if src.count != 1 or (src.shape, src.crs, src.transform) != template_profile:
            raise ValueError(f"single-band grid/CRS/transform mismatch: {path}")
        arr = src.read(1)
    if not np.isfinite(arr[footprint]).all():
        raise ValueError(f"nonfinite reference values within footprint: {path}")
    return arr


def audit(candidate: Path, template: Path, references: list[Path], expected: set[str],
          *, selected_only: bool = False) -> dict:
    candidate, template = Path(candidate), Path(template)
    template_sha = validate_template(template)
    with rasterio.open(template) as src:
        if src.count != 1 or src.crs is None:
            raise ValueError("template must have a CRS and exactly one band")
        foot = np.isfinite(src.read(1))
        profile = (src.shape, src.crs, src.transform)
    cv = _read_aligned(candidate, profile, foot)
    cand_sha = sha256(candidate)
    inventory = registry_inventory(references, expected)
    refs = [p for p in references if p.resolve() != candidate.resolve()]
    # Do not omit same-stem twins: filenames do not prove prediction identity.
    rows, errors = [], []
    for p in refs:
        try:
            rv = _read_aligned(p, profile, foot)
            row = compare_arrays(cv, rv, foot)
            row.update(file=p.name, sha256=sha256(p), byte_identical=sha256(p) == cand_sha)
            row["duplicate"] = bool(row["duplicate"] or row["byte_identical"])
            rows.append(row)
        except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
            errors.append(dict(file=p.name, error=str(exc)))
            break
        if row["duplicate"] or row["rank_undefined"]:
            break
    flags = [r["file"] for r in rows if r["duplicate"]]
    exact_in_ledger = cand_sha in expected
    evaluated_all = bool(refs) and len(rows) == len(refs) and not errors
    complete = bool(not selected_only and inventory["complete"] and evaluated_all
                    and all(not r["rank_undefined"] for r in rows))
    if flags or exact_in_ledger:
        verdict = "DUPLICATE/LANE OVERLAP - stop; do not package"
    elif not complete:
        verdict = "UNVERIFIED - incomplete or invalid registry; stop"
    else:
        verdict = "FINAL-DOT CHECK CLEAR vs declared registry only; surface and other gates still required"
    return dict(candidate=candidate.name, sha256=cand_sha, template_sha256=template_sha,
                candidate_dots=int(((cv > 0) & foot).sum()),
                thresholds=dict(spearman_max=RHO_MAX, dots_within_3px_max=OVERLAP_MAX, dist_px=OVERLAP_DIST),
                registry_inventory=inventory, registry_manifest_sha256=inventory["registry_manifest_sha256"],
                registry_checked=len(rows), registry_complete=complete,
                selected_references_only=selected_only, errors=errors,
                sha_in_artifact_ledger=exact_in_ledger, sha_is_registered_reference=exact_in_ledger,
                flagged=flags, flagged_literal=flags, rows=rows, verdict=verdict,
                lane_clear=complete and not flags and not exact_in_ledger,
                rank_footprint_pixels=int(foot.sum()),
                note="A symmetric overlap is diagnostic only; no density exception is authorized. "
                     "Spearman covers the full footprint and can have heavy ties. Surface audit is separate. "
                     "The legacy sha_in_artifact_ledger field includes all declared reference pins.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--template", type=Path, default=data_dir() / "sample_submission.tif")
    ap.add_argument("--reference", type=Path, action="append", help="diagnose selected reference(s), never a full clearance")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try:
        refs = args.reference if args.reference is not None else registry_rasters()
        result = audit(args.candidate, args.template, refs, declared_hashes(), selected_only=args.reference is not None)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, rasterio.errors.RasterioError) as exc:
        result = dict(candidate=str(args.candidate), verdict="UNVERIFIED - audit error; stop", lane_clear=False, error=str(exc))
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["lane_clear"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
