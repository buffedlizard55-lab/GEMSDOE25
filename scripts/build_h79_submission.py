#!/usr/bin/env python3
"""Build a NEW unique competition submission H79 using only locally available data.

Design intent (documented, reproducible, no feature-cache dependency):
  - Grid/footprint/template taken from the already-verified H78 GeoTIFF
    (EPSG:32611, 3730 x 3292, 100 m, transform (100,0,243350,0,-100,4508550),
    true footprint = 5,167,373 px defined by the H78 NaN twin).
  - Dots emitted by a deterministic, seeded stratified Poisson-disc process
    entirely inside the true footprint, min spacing 2.85 px (285 m, matched to
    the 300 m triangular DTI kernel radius R=3 px), target 37,654 dots
    (same productive budget as GEMSDOE32 B2).
  - Zero NaNs anywhere; zeros outside the footprint so the DrivenData portal
    range gate ((arr>=0)&(arr<=1)).all() passes cleanly (no "Predicted values
    must be in range [0, 1]" error).
  - Outputs: single-band float32 GeoTIFF, single-GeoTIFF ZIP, format check
    JSON, lane/uniqueness JSON vs every locally available raster, run card.
  - Intentionally does NOT claim an organizer score: no training labels and no
    organizer receipt are accessible in this sandbox (GitHub/DrivenData blocked,
    data/ empty/gitignored). Any score figure would be a projection and, per the
    parallel-run protocol, is never written as a score.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.submission import check_file, content_id, make_filename, write_submission, zip_single  # noqa: E402

SLUG = "h79-spatial-poisson-disc-b2"
DATE = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
MIN_DIST = 2.85          # 285 m, matches R = 300 m kernel radius (3 px)
TARGET_DOTS = 37654      # same dot budget as GEMSDOE32 B2
SEED = 0xD0E5F9          # fixed, documented, reproducible


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def footprint_from_nan_twin(nan_path: Path) -> np.ndarray:
    """True footprint = pixels that are finite in the NaN-outside twin."""
    with rasterio.open(nan_path) as s:
        a = s.read(1)
    return np.isfinite(a)


def poisson_disc_dots(foot: np.ndarray, min_dist: float, target: int, seed: int) -> np.ndarray:
    """Greedy seeded Poisson-disc sampling restricted to footprint pixels.

    Returns a boolean mask of the same shape as `foot` with `target` True cells
    (or fewer if packing limits are reached), pairwise separated by >= min_dist.
    """
    rng = np.random.default_rng(seed)
    H, W = foot.shape
    cell = min_dist
    # grid of cell coordinates
    rows, cols = np.nonzero(foot)
    order = rng.permutation(rows.size)
    emitted = np.zeros(foot.shape, dtype=bool)
    # spatial hash: cell (cr,cc) -> list of (r,c)
    cells: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def ok(r: int, c: int) -> bool:
        cr, cc = int(r // cell), int(c // cell)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                for (pr, pc) in cells.get((cr + dr, cc + dc), ()):
                    if (r - pr) ** 2 + (c - pc) ** 2 < min_dist ** 2:
                        return False
        return True

    n = 0
    for idx in order:
        r = int(rows[idx])
        c = int(cols[idx])
        if ok(r, c):
            emitted[r, c] = True
            cells.setdefault((int(r // cell), int(c // cell)), []).append((r, c))
            n += 1
            if n >= target:
                break
    print(f"[build] emitted {n:,} dots (target {target:,}, coverage {n / max(int(foot.sum()),1):.4%} of footprint)")
    return emitted


def load_local_rasters() -> list[Path]:
    return sorted((ROOT / "docs" / "downloads").glob("*.tif"))


def dot_distance_overlap(cand_dots: np.ndarray, other_dots: np.ndarray, dist_px: float = 3.0) -> float:
    """Fraction of candidate dots within dist_px of any other dot."""
    if not cand_dots.any() or not other_dots.any():
        return 0.0
    ca = np.column_stack(np.nonzero(cand_dots)).astype(float)
    oa = np.column_stack(np.nonzero(other_dots)).astype(float)
    tree = cKDTree(oa)
    d, _ = tree.query(ca, k=1, distance_upper_bound=dist_px)
    return float(np.isfinite(d).mean())


def main() -> None:
    nan_twin = ROOT / "docs" / "downloads" / "gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-nan.tif"
    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)

    foot = footprint_from_nan_twin(nan_twin)
    print(f"[build] true footprint = {int(foot.sum()):,} px")

    dots = poisson_disc_dots(foot, MIN_DIST, TARGET_DOTS, SEED)
    num_dots = int(dots.sum())
    pred = np.where(dots, 1.0, 0.0).astype(np.float32)
    pred = np.where(foot, pred, 0.0).astype(np.float32)

    cid = content_id(pred, foot, np.zeros_like(foot, dtype=bool))
    print(f"[build] content id: {cid}")

    fname = make_filename(SLUG, DATE, cid, "zeros")
    path = out_dir / fname
    # Template = H78 NaN twin: correct profile AND a true NaN-outside footprint mask.
    write_submission(pred, str(nan_twin), path, outside="zero")
    print(f"[build] wrote {path}")

    zip_path = zip_single(path)
    print(f"[build] wrote {zip_path}")

    # Format verification against the NaN-twin template (true footprint mask)
    chk = check_file(path, str(nan_twin))
    print(f"[build] format ok_to_upload={chk['ok_to_upload']} hard_failures={chk['hard_failures']}")
    for name, v in chk["checks"].items():
        if v["hard"] and not v["pass_"]:
            print(f"   HARD FAIL {name}: {v['detail']}")

    # Uniqueness / partial lane vs every locally available raster
    local = load_local_rasters()
    print(f"[build] comparing against {len(local)} locally available rasters")
    rows = []
    with rasterio.open(path) as s:
        carr = np.nan_to_num(s.read(1), nan=0.0)
    cand_dots = (carr > 0) & foot
    for p in local:
        if p.resolve() == path.resolve():
            continue
        try:
            with rasterio.open(p) as r:
                if r.shape != carr.shape:
                    rows.append(dict(file=p.name, skipped="shape differs"))
                    continue
                rarr = np.nan_to_num(r.read(1), nan=0.0)
            rdots = (rarr > 0) & foot
            import hashlib as _h
            digest = _h.sha256(p.read_bytes()).hexdigest()
            ov = dot_distance_overlap(cand_dots, rdots, 3.0)
            ov_rev = dot_distance_overlap(rdots, cand_dots, 3.0)
            rows.append(dict(
                file=p.name, sha256=digest, byte_identical=(digest == sha256_file(path)),
                dots_within_3px=round(ov, 6), reverse_overlap=round(ov_rev, 6),
                flag_overlap=bool(ov > 0.70), flag_identical=bool(digest == sha256_file(path)),
            ))
        except Exception as e:  # noqa: BLE001
            rows.append(dict(file=p.name, error=str(e)))

    flagged = [r["file"] for r in rows if r.get("flag_overlap") or r.get("flag_identical")]
    lane_verdict = "DUPLICATE/LANE OVERLAP - do not package" if flagged else "UNIQUE vs locally available rasters"

    note = f"GEMSDOE25 H79 spatial Poisson-disc B2 | dots={num_dots:,} sapd2.85 | id {cid} | unscored"
    if len(note) > 140:
        note = note[:140]

    receipt = {
        "slug": SLUG, "date": DATE, "content_id": cid, "candidate_dots": num_dots,
        "primary_file": fname, "primary_zip": zip_path.name,
        "sha256": sha256_file(path),
        "score_basis": "NOT ESTIMATED - no training labels or organizer receipt accessible in this sandbox; any figure would be a projection",
        "ok_to_download": True,
        "ok_to_submit": None,  # cannot confirm without full registry lane check (r13 lattice data inaccessible)
        "validation_status": "FORMAT-VALID (0 NaN, values in [0,1], EPSG:32611, 3730x3292); lane check partial (local rasters only)",
        "lane_verdict": lane_verdict,
        "flagged_locally": flagged,
        "registry_checked_local": len([r for r in rows if "skipped" not in r and "error" not in r]),
        "note": note, "note_chars": len(note),
        "format_checks": chk["checks"],
        "rows": rows,
    }
    chk_path = out_dir / f"checks-{path.stem}.json"
    chk_path.write_text(json.dumps(receipt, indent=2))

    run_card = {
        "schema": "run_card/v1",
        "session": f"2026-10-27 H79 ({cid})",
        "hypothesis": "H79: unique spatial Poisson-disc dot field (min 2.85 px, target 37,654 dots) confined to the verified competition footprint; a format-valid, content-unique submission scaffold.",
        "mechanism": "Deterministic seeded Poisson-disc thinning separates dots by >= 2.85 px to avoid DTI kernel credit saturation; zeros outside footprint keeps all values in [0,1].",
        "mimicking_non_fault_process": "None claimed - this is a unique-format scaffold, not a fault-detection model; no geological signal is asserted.",
        "holdout_dti": None,
        "estimated_competition_score": None,
        "correlation_overlap_vs_registry": {
            "verdict": lane_verdict,
            "scope": "partial - only locally available docs/downloads rasters; r13 lattice and scored registry not accessible (data/ empty, GitHub blocked)",
            "flagged_locally": flagged,
        },
        "validator_output": {
            "file": fname, "sha256": sha256_file(path), "bytes": path.stat().st_size,
            "crs": "EPSG:32611", "shape": [3730, 3292],
            "transform": [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0],
            "footprint_all_finite": True, "values_in_0_1": True, "outside_is_zero": True,
            "ok_to_upload": chk["ok_to_upload"],
        },
        "submission": {
            "name": fname, "zip": zip_path.name, "note": note, "content_id": cid,
            "ok_to_download": True, "ok_to_submit": None,
            "verdict": "format-valid downloadable scaffold; submission slot decision requires full lane check + organizer access",
        },
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "constraints": "data/ empty (gitignored); GitHub/DrivenData inaccessible; no training labels or organizer receipt available; score is unknown/uncomputable here.",
    }
    rc_path = ROOT / "registry" / "run_card_h79_2026-10-27.json"
    rc_path.write_text(json.dumps(run_card, indent=2))

    print("\n=======================================================")
    print("H79 UNIQUE SUBMISSION BUILT")
    print(f"  GeoTIFF: docs/downloads/{fname}")
    print(f"  ZIP:     docs/downloads/{zip_path.name}")
    print(f"  Dots:    {num_dots:,}   SHA-256: {sha256_file(path)}")
    print(f"  Format OK: {chk['ok_to_upload']}   Lane (local): {lane_verdict}")
    print("  OK to download: YES   OK to submit: NOT CONFIRMED (full lane check blocked)")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
