#!/usr/bin/env python3
"""Read-only cache gate for the pre-registered H73-BW block selector.

This deliberately does not restore inputs, build features, or call load_h34_sidecar (which builds a
missing sidecar). It exits 2 unless every required cache exists and all previously pinned artifacts
match evidence/work_cache_hashes.json.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import work_dir  # noqa: E402

PREREGISTRATION = "knowledge/34_h73_bw_block_selector_2026-10-26.md"
CACHE_MANIFEST = ROOT / "evidence/work_cache_hashes.json"
REQUIRED = (
    "bands/_footprint.npy",
    "bands/_labels.npy",
    "static_ABCD.npy",
    "static_ABCD.npy.names.json",
    "addons.npy",
    "addons.npy.names.json",
    "h34_columns.npy",
    "h34_columns.npy.names.json",
)
PIN_REQUIRED = REQUIRED[:6]
H34_NAMES = ["H34_resmag_shallow_ridge", "H34_resmag_mid_ridge", "H34_baseflex_ridge"]
EVALUATOR_SOURCES = (
    "src/gems25/block_holdout.py",
    "src/gems25/holdout.py",
    "src/gems25/experiment.py",
    "src/gems25/features.py",
    "src/gems25/h73_pm.py",
    "src/gems25/metric.py",
    "src/gems25/validation.py",
)
DISTRIBUTIONS = ("numpy", "scipy", "scikit-learn", "rasterio", "pandas")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _environment_versions() -> dict:
    versions = {"python": sys.version.split()[0]}
    for package in DISTRIBUTIONS:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _source_hashes() -> dict:
    result = {}
    for relative in EVALUATOR_SOURCES:
        path = ROOT / relative
        result[relative] = sha256_file(path) if path.is_file() else None
    return result


def inspect_cache(work: Path, manifest_path: Path = CACHE_MANIFEST) -> dict:
    """Return a non-mutating presence/hash receipt; no cache directories or files are created."""
    work, manifest_path = Path(work), Path(manifest_path)
    errors: list[str] = []
    warnings: list[str] = []
    records: list[dict] = []
    source_hashes = _source_hashes()
    errors.extend(f"missing_source:{path}" for path, digest in source_hashes.items() if digest is None)
    try:
        manifest = json.loads(manifest_path.read_text())
        if not isinstance(manifest, dict):
            raise ValueError("manifest root must be an object")
    except FileNotFoundError:
        manifest = {}
        errors.append("cache_manifest_missing")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        manifest = {}
        errors.append(f"cache_manifest_invalid:{type(exc).__name__}")

    for relative in REQUIRED:
        path = work / relative
        expected = manifest.get(relative)
        pin_valid = isinstance(expected, dict) and bool(expected.get("sha256"))
        if relative in PIN_REQUIRED and not pin_valid:
            errors.append(f"missing_pin:{relative}")
        if not path.is_file():
            records.append({
                "path": relative,
                "exists": False,
                "expected_sha256": expected.get("sha256") if isinstance(expected, dict) else None,
            })
            errors.append(f"missing:{relative}")
            continue

        actual_size = path.stat().st_size
        actual_sha = sha256_file(path)
        record = {
            "path": relative,
            "exists": True,
            "bytes": actual_size,
            "sha256": actual_sha,
            "expected_sha256": expected.get("sha256") if isinstance(expected, dict) else None,
        }
        if pin_valid:
            size_ok = expected.get("bytes") is None or actual_size == expected["bytes"]
            sha_ok = actual_sha == expected["sha256"]
            record["matches_pin"] = bool(size_ok and sha_ok)
            if not record["matches_pin"]:
                errors.append(f"pin_mismatch:{relative}")
        else:
            record["matches_pin"] = None
            record["pin_status"] = "no expected hash recorded"
            if relative not in PIN_REQUIRED:
                warnings.append(f"unpinned:{relative}")
        records.append(record)

        if relative == "h34_columns.npy.names.json":
            try:
                names = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid_h34_names:{type(exc).__name__}")
            else:
                record["names"] = names
                if names != H34_NAMES:
                    errors.append("h34_names_mismatch")

    status = "ready_for_selector" if not errors else "blocked_before_fit"
    return {
        "schema": "h73_bw_cache_preflight/v1",
        "status": status,
        "preregistration": PREREGISTRATION,
        "work_dir": str(work),
        "cache_manifest": str(manifest_path),
        "cache_manifest_sha256": sha256_file(manifest_path) if manifest_path.is_file() else None,
        "environment": _environment_versions(),
        "evaluator_source_hashes": source_hashes,
        "required_artifacts": records,
        "errors": errors,
        "warnings": warnings,
        "auto_restore_performed": False,
        "feature_build_performed": False,
        "h34_loader_called": False,
        "model_fit_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=work_dir())
    parser.add_argument("--manifest", type=Path, default=CACHE_MANIFEST)
    parser.add_argument("--json-out", type=Path, help="Optional path for this cache-only receipt")
    args = parser.parse_args()
    result = inspect_cache(args.work_dir, args.manifest)
    text = json.dumps(result, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    print(text, end="")
    return 0 if result["status"] == "ready_for_selector" else 2


if __name__ == "__main__":
    raise SystemExit(main())
