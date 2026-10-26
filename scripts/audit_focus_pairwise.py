#!/usr/bin/env python3
"""Reproducibly compare the nine focus-site winners and the current H71 research raster.

The focus-site source bytes are fetched only from pinned public GitHub commits recorded in
``evidence/focus_audit_2026-10-26.json`` and verified against their SHA-256 pins. DrivenData
is never contacted. This computes exact mask identity and the protocol's directed 3-pixel
neighbor overlap; it does not verify any competition score.

    python scripts/audit_focus_pairwise.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

FOCUS_AUDIT = ROOT / "evidence" / "focus_audit_2026-10-26.json"
FOCUS_FORENSICS = ROOT / "evidence" / "focus_sites_forensics.json"
SUBMISSIONS = ROOT / "registry" / "submissions.json"
H71_CARD = ROOT / "registry" / "run_card_h71_2026-10-26.json"
OUT = ROOT / "evidence" / "focus_pairwise_overlap_2026-10-26.json"
DOT_RADIUS_PX = 3.0
OVERLAP_CAP = 0.70


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_blob(repo: str, revision: str, path: str) -> bytes:
    """Read one immutable public GitHub blob through git, without a GitHub API/DrivenData call."""
    cache = data_dir() / "raw" / "focus_pairwise_git" / repo.replace("/", "__")
    cache.mkdir(parents=True, exist_ok=True)
    if not (cache / "HEAD").exists():
        subprocess.run(["git", "init", "--bare", "-q"], cwd=cache, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", f"https://github.com/{repo}.git"],
            cwd=cache,
            check=True,
        )
    fetch = subprocess.run(
        ["git", "fetch", "-q", "--depth=1", "--filter=blob:none", "origin", revision],
        cwd=cache,
        capture_output=True,
        text=True,
    )
    if fetch.returncode:
        raise RuntimeError(f"could not fetch pinned GitHub revision {repo}@{revision}: {fetch.stderr.strip()}")
    show = subprocess.run(
        ["git", "show", f"FETCH_HEAD:{path}"],
        cwd=cache,
        capture_output=True,
    )
    if show.returncode:
        raise RuntimeError(f"could not read pinned GitHub file {repo}@{revision}:{path}: {show.stderr.decode(errors='replace')}")
    return show.stdout


def _focus_blob(artifact: dict, revision: str) -> bytes:
    if artifact["repo"] == "local":
        return (ROOT / artifact["path"]).read_bytes()
    return _git_blob(artifact["repo"], revision, artifact["path"])


def _read_mask(path: Path, footprint: np.ndarray, expected_grid: dict) -> np.ndarray:
    with rasterio.open(path) as src:
        if src.count != 1:
            raise ValueError(f"{path.name}: expected one band, found {src.count}")
        if src.shape != footprint.shape:
            raise ValueError(f"{path.name}: shape {src.shape} != footprint {footprint.shape}")
        if src.crs != expected_grid["crs"] or src.transform != expected_grid["transform"]:
            raise ValueError(f"{path.name}: CRS or geotransform differs from the pinned template")
        values = src.read(1)
    return (values > 0) & np.isfinite(values) & footprint


def main() -> None:
    audit = json.loads(FOCUS_AUDIT.read_text())
    forensics = json.loads(FOCUS_FORENSICS.read_text())
    registry = json.loads(SUBMISSIONS.read_text())["files"]
    h71_card = json.loads(H71_CARD.read_text())
    artifact_by_label = {item["label"]: item for item in forensics["focus_artifacts"]}
    data = data_dir()

    template_path = data / "sample_submission.tif"
    if not template_path.exists():
        raise SystemExit("Missing pinned sample_submission.tif; run bash scripts/download_competition_data.sh first")
    with rasterio.open(template_path) as template:
        footprint = np.isfinite(template.read(1))
        grid = {"crs": template.crs, "transform": template.transform}
        grid_json = {
            "crs": str(template.crs),
            "shape": list(template.shape),
            "transform": list(template.transform)[:6],
            "pixel_size_m": [abs(template.transform.a), abs(template.transform.e)],
        }

    scratch = data / "focus_pairwise"
    scratch.mkdir(parents=True, exist_ok=True)
    rasters: list[dict] = []
    for row in audit["sites"]:
        artifact = artifact_by_label.get(row["submission"])
        if artifact is None:
            raise ValueError(f"No pinned source path for {row['site']} {row['submission']}")
        revision = row.get("source_head")
        if not revision:
            raise ValueError(f"Missing pinned source revision for {row['site']}")
        blob = _focus_blob(artifact, revision)
        got = sha256_bytes(blob)
        if got != row["sha256"] or got != artifact["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {row['site']} {row['submission']}: {got}")
        local = scratch / f"{row['site']}.tif"
        local.write_bytes(blob)
        mask = _read_mask(local, footprint, grid)
        rasters.append(
            {
                "site": row["site"],
                "submission": row["submission"],
                "file": Path(artifact["path"]).name,
                "source_repo": "buffedlizard55-lab/GEMSDOE25" if artifact["repo"] == "local" else artifact["repo"],
                "source_revision": revision,
                "source_path": artifact["path"],
                "site_url": row["site_url"],
                "owner_reported_dti": row["owner_reported_score"],
                "score_evidence": "OWNER-REPORTED; no organizer receipt in this repository",
                "sha256": got,
                "emitted_pixels": int(mask.sum()),
                "mask": mask,
            }
        )

    primary = next(item for item in registry if item["role"] == "primary")
    if primary["id"] != "h71-hgpc-blind":
        raise ValueError("The registered primary changed; review the current selector before comparing H71")
    h71_path = ROOT / primary["path"]
    h71_sha = sha256_file(h71_path)
    if h71_sha != primary["sha256"] or h71_sha != h71_card["tif"]["sha256"]:
        raise ValueError(f"H71 primary SHA-256 mismatch: {h71_sha}")
    h71_mask = _read_mask(h71_path, footprint, grid)
    rasters.append(
        {
            "site": "GEMSDOE25 (H71 research candidate)",
            "submission": primary["file"],
            "file": primary["file"],
            "source_repo": "buffedlizard55-lab/GEMSDOE25",
            "source_revision": "local tracked artifact; SHA-256 pinned in registry/submissions.json",
            "source_path": primary["path"],
            "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE25/",
            "owner_reported_dti": None,
            "score_evidence": "No organizer-confirmed score; no defensible live-score projection",
            "sha256": h71_sha,
            "emitted_pixels": int(h71_mask.sum()),
            "mask": h71_mask,
        }
    )

    # Keep only one distance grid in memory at a time. Distances are converted to float32
    # after computation; the <= 3 px predicate is unchanged at this threshold.
    distances: dict[str, np.ndarray] = {}
    for row in rasters:
        distances[row["site"]] = distance_transform_edt(~row["mask"]).astype(np.float32)

    pair_rows = []
    per_site = {}
    for left in rasters:
        similarities = []
        for right in rasters:
            if left is right:
                continue
            left_count, right_count = left["emitted_pixels"], right["emitted_pixels"]
            left_near_right = (
                float(np.mean(distances[right["site"]][left["mask"]] <= DOT_RADIUS_PX)) if left_count else 0.0
            )
            right_near_left = (
                float(np.mean(distances[left["site"]][right["mask"]] <= DOT_RADIUS_PX)) if right_count else 0.0
            )
            exact = bool(np.array_equal(left["mask"], right["mask"]))
            pair_rows.append(
                {
                    "candidate_site": left["site"],
                    "registry_site": right["site"],
                    "candidate_sha256": left["sha256"],
                    "registry_sha256": right["sha256"],
                    "candidate_dot_count": left_count,
                    "registry_dot_count": right_count,
                    "candidate_dots_within_3px_of_registry_dots": left_near_right,
                    "registry_dots_within_3px_of_candidate_dots": right_near_left,
                    "exact_prediction_mask_match": exact,
                    "duplicate_lane_by_protocol": bool(exact or left_near_right > OVERLAP_CAP),
                }
            )
            if right["owner_reported_dti"] is not None:
                similarities.append(
                    {
                        "other_site": right["site"],
                        "other_owner_reported_dti": right["owner_reported_dti"],
                        "candidate_dots_within_3px": left_near_right,
                        "exact_prediction_mask_match": exact,
                    }
                )
        if left["owner_reported_dti"] is not None:
            max_overlap = max(similarities, key=lambda item: item["candidate_dots_within_3px"])
            exact_peers = [item["other_site"] for item in similarities if item["exact_prediction_mask_match"]]
            per_site[left["site"]] = {
                "submission": left["submission"],
                "file": left["file"],
                "owner_reported_dti": left["owner_reported_dti"],
                "sha256": left["sha256"],
                "emitted_pixels": left["emitted_pixels"],
                "max_cross_site_candidate_dot_share_within_3px": max_overlap["candidate_dots_within_3px"],
                "most_similar_focus_site": max_overlap["other_site"],
                "most_similar_site_owner_reported_dti": max_overlap["other_owner_reported_dti"],
                "exact_mask_match_sites": exact_peers,
                "strict_lane_unique_vs_all_other_focus_winners": bool(max_overlap["candidate_dots_within_3px"] <= OVERLAP_CAP and not exact_peers),
                "protocol_interpretation": (
                    "historical file; not eligible as a new submission; fails the >70% 3-px uniqueness gate"
                    if max_overlap["candidate_dots_within_3px"] > OVERLAP_CAP or exact_peers
                    else "historical file; not eligible as a new submission"
                ),
            }

    h71_site = "GEMSDOE25 (H71 research candidate)"
    h71_vs_focus = [row for row in pair_rows if row["candidate_site"] == h71_site and row["registry_site"] in per_site]
    h71_max = max(h71_vs_focus, key=lambda item: item["candidate_dots_within_3px_of_registry_dots"])
    h71_surface = json.loads((ROOT / "evidence" / "h71_lane_surface.json").read_text())
    h71_extended = json.loads((ROOT / "evidence" / "h71_lane_extended.json").read_text())

    out = {
        "schema": "focus_pairwise_overlap/v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "scripts/audit_focus_pairwise.py",
        "inputs": {
            "focus_site_audit": "evidence/focus_audit_2026-10-26.json",
            "focus_artifact_forensics": "evidence/focus_sites_forensics.json",
            "template": "data/sample_submission.tif (owner-mirror; SHA-256 pinned in registry/data_manifest.json)",
            "prediction_mask_rule": "finite positive prediction pixels intersected with the template footprint",
            "distance_rule": "Euclidean pixel distance <= 3.0 pixels (300 m on the 100 m grid); directed share = candidate positive pixels in the 3-px halo of another raster",
            "exact_rule": "np.array_equal of the footprint-masked boolean prediction arrays",
        },
        "thresholds": {"maximum_candidate_dots_within_3px": OVERLAP_CAP, "rank_correlation_absolute_maximum": 0.90},
        "grid": grid_json,
        "score_caveat": "All focus-site DTI figures are OWNER-REPORTED and unverified by organizer receipts; this geometry audit calculates no DTI.",
        "focus_winners": per_site,
        "exact_prediction_mask_duplicate_pairs": [
            {"site_a": row["candidate_site"], "site_b": row["registry_site"], "sha256_a": row["candidate_sha256"]}
            for row in pair_rows
            if row["candidate_site"] in per_site
            and row["registry_site"] in per_site
            and row["candidate_site"] < row["registry_site"]
            and row["exact_prediction_mask_match"]
        ],
        "pairwise_directed_rows": pair_rows,
        "h71_candidate": {
            "file": primary["file"],
            "sha256": h71_sha,
            "emitted_pixels": int(h71_mask.sum()),
            "max_focus_site_dot_share_within_3px": h71_max["candidate_dots_within_3px_of_registry_dots"],
            "most_similar_focus_site": h71_max["registry_site"],
            "unique_vs_all_nine_focus_winners_under_70pct_rule": bool(
                h71_max["candidate_dots_within_3px_of_registry_dots"] <= OVERLAP_CAP
            ),
            "surface_max_abs_spearman_vs_available_registry": h71_surface["worst_abs_spearman"],
            "final_max_abs_spearman_vs_available_registry": h71_extended["external_sparse"]["worst_abs_spearman_final"],
            "final_max_external_dots_within_3px": h71_extended["external_sparse"]["worst_cand_dots_within_3px"],
            "strict_global_registry_lane_clear": False,
            "strict_global_registry_lane_stop": {
                "file": h71_extended["lattice"][0]["file"],
                "candidate_dots_within_3px_of_registry_dots": h71_extended["lattice"][0]["cand_dots_within_3px"],
                "duplicate_lane_by_protocol": True,
                "reason": "literal overlap rule applies to every registry raster; no density-aware exception is authorized",
            },
            "holdout_dti": h71_card["holdout_dti"],
            "verdict": "negative; H71 screens failed vs same-run H35 and the literal dense-lattice lane check fails; DO NOT SUBMIT",
        },
        "limitations": [
            "The artifacts are owner-mirrored and hash-pinned, not authenticated by the competition organizer.",
            "The 3-px audit is a geometric novelty screen; it does not establish scientific validity or leaderboard performance.",
            "The candidate-versus-registry rank-correlation figures are carried from the pinned H71 surface/final-lane receipts; the other historical pair rows report dot overlap and exact mask identity only.",
        ],
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}; {len(per_site)} site winners; {len(pair_rows)} directed comparisons")
    for site, row in per_site.items():
        print(
            f"{site}: max 3-px share {row['max_cross_site_candidate_dot_share_within_3px']:.4f} "
            f"vs {row['most_similar_focus_site']}; exact peers={row['exact_mask_match_sites']}"
        )
    h = out["h71_candidate"]
    print(
        f"H71 vs focus winners: max {h['max_focus_site_dot_share_within_3px']:.4f} "
        f"vs {h['most_similar_focus_site']}; strict global lane clear={h['strict_global_registry_lane_clear']}"
    )


if __name__ == "__main__":
    main()
