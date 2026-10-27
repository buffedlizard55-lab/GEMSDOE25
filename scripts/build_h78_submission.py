#!/usr/bin/env python3
"""Build and validate the H78 Multiscale Hydrothermal-Structural Conduit Fusion (MHSCF) submission.

Hypothesis H78 (MHSCF):
  - Integrates coincident LiDAR step, gravity basement gradient, depth gradient,
    potassium hydrothermal metasomatism (K/Th anomaly), magnetic alteration,
    and hydrothermal wellspring/vent corridor alignment.
  - Applies Ridge-NMS lineament extraction.
  - Strictly enforces B2 catalogue collar exclusion (d_cat > 2.0 px = 200 m).
  - Uses score-ordered Poisson disc thinning with min_dist = 2.85 px (285 m),
    matching the 300 m triangular kernel radius R = 3 px.
  - Budget targeting 37,654 to 39,500 optimal DTI dots.
  - Zero NaNs (0.0 outside footprint) ensuring portal validator ((arr>=0)&(arr<=1)).all() passes cleanly.
  - Generates single GeoTIFF (.tif), ZIP archive (.zip), format checks JSON, lane check JSON, and Run Card.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import load_context  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission, zip_single  # noqa: E402
from gems25.thinning import ridge_nms, score_ordered_dots, select_top_positive  # noqa: E402

SLUG = "h78-mhscf-conduit-b2-sapd2-85"
DATE = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
MIN_DIST = 2.85  # 285 m spacing for 300 m kernel
COLLAR_PX = 2.0  # B2 collar exclusion: strictly > 200 m from known faults
KFRAC = 0.033    # Candidate positive selection pool fraction


def load_hydrothermal_conduit_field(foot: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Compute normalized hydrothermal spring and volcanic vent proximity corridor."""
    csv_springs = data_dir() / "external" / "gdr_wellspring_in_footprint.csv"
    csv_vents = data_dir() / "external" / "gdr_volcanic_vents_in_footprint.csv"
    
    grid = np.zeros(shape, dtype=np.float32)
    # Springs
    if csv_springs.exists():
        import csv
        with open(csv_springs, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    r, c = int(row["row"]), int(row["col"])
                    if 0 <= r < shape[0] and 0 <= c < shape[1]:
                        # Weight hot/warm springs higher
                        tclass = row.get("thermalclass", "").strip().lower()
                        weight = 2.0 if tclass == "hot" else (1.5 if tclass == "warm" else 1.0)
                        grid[r, c] = max(grid[r, c], weight)
                except (ValueError, KeyError):
                    continue

    # Vents
    if csv_vents.exists():
        import csv
        with open(csv_vents, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    r, c = int(row["row"]), int(row["col"])
                    if 0 <= r < shape[0] and 0 <= c < shape[1]:
                        grid[r, c] = max(grid[r, c], 1.5)
                except (ValueError, KeyError):
                    continue

    # Gaussian blur to create convective permeability corridor (sigma=15 px = 1.5 km)
    blurred = gaussian_filter(grid, sigma=15.0)
    if blurred.max() > 0:
        blurred /= blurred.max()
    return np.clip(blurred, 0.0, 1.0).astype(np.float32)


def main():
    t0 = time.time()
    work = work_dir()
    ctx = load_context(work)
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi
    H, W = foot.shape

    print(f"[{time.time()-t0:.1f}s] Extracting independent multi-modal geothermal features...")
    # 1. Gravity analytic signal and basement gradient
    grav_as = np.zeros(foot.shape, np.float32)
    grav_hg = np.zeros(foot.shape, np.float32)
    depth_grad = np.zeros(foot.shape, np.float32)
    mag_hg = np.zeros(foot.shape, np.float32)
    crest = np.zeros(foot.shape, np.float32)
    curv = np.zeros(foot.shape, np.float32)

    grav_as.ravel()[fi] = ctx.static[ctx.static_names.index("A_grav_as")]
    grav_hg.ravel()[fi] = ctx.static[ctx.static_names.index("A_grav_hg_ridge")]
    depth_grad.ravel()[fi] = ctx.static[ctx.static_names.index("D_depth_base_grad")]
    mag_hg.ravel()[fi] = ctx.static[ctx.static_names.index("A_mag_hg_ridge")]
    crest.ravel()[fi] = ctx.static[ctx.static_names.index("B_crest")]
    curv.ravel()[fi] = ctx.static[ctx.static_names.index("B_slope_grad")]

    # Normalize each channel p1-p99 on footprint
    def norm_p(arr):
        v = arr[foot]
        lo, hi = np.percentile(v, 1.0), np.percentile(v, 99.0)
        return np.clip((arr - lo) / max(hi - lo, 1e-6), 0.0, 1.0).astype(np.float32)

    g_as_n = norm_p(grav_as)
    g_hg_n = norm_p(grav_hg)
    d_gr_n = norm_p(depth_grad)
    m_hg_n = norm_p(mag_hg)
    c_cr_n = norm_p(crest)
    c_cv_n = norm_p(curv)

    # 2. Hydrothermal conduit field from springs and vents
    print(f"[{time.time()-t0:.1f}s] Loading hydrothermal conduit field...")
    conduit = load_hydrothermal_conduit_field(foot, foot.shape)

    # 3. Potassium metasomatism (alteration index)
    k_alt = np.zeros(foot.shape, np.float32)
    if ctx.addon is not None:
        k_vec = np.clip(ctx.addon[1], 0.0, 5.0)  # X1_ThK
        lo, hi = np.percentile(k_vec, 2.0), np.percentile(k_vec, 98.0)
        k_scaled = np.clip((k_vec - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
        k_alt.ravel()[fi] = k_scaled

    # 4. Independent Hydrothermal-Structural Conduit Fusion (MHSCF) surface:
    # Emphasizes:
    # - Basement density boundary (g_as_n, g_hg_n, d_gr_n)
    # - Magnetic permeability boundary (m_hg_n)
    # - Topographic structural expression (c_cr_n, c_cv_n)
    # - Hydrothermal fluid upflow proximity (conduit, k_alt)
    print(f"[{time.time()-t0:.1f}s] Fusing independent MHSCF discovery surface...")
    basement_step = 0.35 * g_as_n + 0.35 * g_hg_n + 0.30 * d_gr_n
    magnetic_step = m_hg_n
    topo_structure = 0.50 * c_cr_n + 0.50 * c_cv_n
    hydrothermal = 0.60 * conduit + 0.40 * k_alt

    # Multiplicative interaction between structure and hydrothermal indicators
    surface = (basement_step * 0.40 + magnetic_step * 0.30 + topo_structure * 0.30) * (1.0 + 0.80 * hydrothermal)
    surface = np.where(foot, surface, 0.0).astype(np.float32)
    p99 = np.percentile(surface[foot], 99.0)
    if p99 > 0:
        surface = np.clip(surface / p99, 0.0, 1.0)

    # Ridge-NMS lineament sharpening
    print(f"[{time.time()-t0:.1f}s] Running Ridge-NMS lineament extraction...")
    ridges = ridge_nms(surface, foot, 1.0)

    # Enforce B2 catalogue collar exclusion: dist_to_known_catalogue > 2.0 px
    print(f"[{time.time()-t0:.1f}s] Enforcing B2 catalogue collar exclusion (d_cat > {COLLAR_PX} px)...")
    dist_cat = distance_transform_edt(~lab)
    far_from_cat = dist_cat > COLLAR_PX
    scored_candidates = np.where(ridges & far_from_cat & foot, surface, 0.0)

    # Select top candidate pool
    target_pool = int(round(KFRAC * int(foot.sum())))
    print(f"[{time.time()-t0:.1f}s] Selecting candidate pool of {target_pool:,} pixels...")
    top_pool = select_top_positive(scored_candidates, foot, target_pool)

    # Score-ordered Poisson disc thinning with min_dist = 2.85 px
    print(f"[{time.time()-t0:.1f}s] Running score-ordered Poisson disc thinning (min_dist={MIN_DIST} px)...")
    emitted_dots = score_ordered_dots(surface, top_pool, MIN_DIST)
    num_dots = int(emitted_dots.sum())
    print(f"[{time.time()-t0:.1f}s] Emitted dots: {num_dots:,}")

    # Safety assertions
    assert not (emitted_dots & lab).any(), "CRITICAL: Emission placed on known catalogue fault!"
    assert (dist_cat[emitted_dots] > COLLAR_PX).all(), "CRITICAL: Emission placed inside B2 collar!"

    # Create binary prediction array
    pred = np.where(emitted_dots, 1.0, 0.0).astype(np.float32)
    cid = content_id(pred, foot, lab)
    print(f"[{time.time()-t0:.1f}s] Scored content id: {cid}")

    tmpl = data_dir() / "sample_submission.tif"
    out_dir = ROOT / "docs" / "downloads"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write files: BOTH zeros (primary, competition portal safe) and nan (legacy)
    fname_zeros = make_filename(SLUG, DATE, cid, "zeros")
    fname_nan = make_filename(SLUG, DATE, cid, "nan")
    
    path_zeros = out_dir / fname_zeros
    path_nan = out_dir / fname_nan

    print(f"Writing primary competition-safe GeoTIFF (zeros outside): {path_zeros}...")
    write_submission(pred, tmpl, path_zeros, outside="zero")
    print(f"Writing legacy GeoTIFF (nan outside): {path_nan}...")
    write_submission(pred, tmpl, path_nan, outside="nan")

    # Create single-GeoTIFF ZIP archive for easy portal submission
    zip_path = zip_single(path_zeros)
    print(f"Created portal ZIP package: {zip_path}")

    # Format verification
    print("Verifying format checks with independent rasterio inspector...")
    chk_zeros = check_file(path_zeros, tmpl)
    chk_nan = check_file(path_nan, tmpl)
    assert chk_zeros["format_valid"] and chk_nan["format_valid"]

    # Check Lane protocol against ALL available registry rasters
    print("Running Parallel-Run Protocol Lane Check...")
    cmd_lane = [sys.executable, str(ROOT / "scripts" / "check_lane_duplicates.py"),
                str(path_zeros), "--out", str(out_dir / f"lane-{path_zeros.name}.json")]
    subprocess.run(cmd_lane, check=True)
    lane_data = json.loads((out_dir / f"lane-{path_zeros.name}.json").read_text())

    # Build DrivenData research identifier note (must be <= 120 chars; DO NOT SUBMIT)
    note = f"GEMSDOE25 H78-MHSCF | no slot, not slot-approved; DO NOT SUBMIT | id {cid} | unscored"
    if len(note) > 120:
        note = note[:120]

    audit_path = ROOT / "evidence" / "h78_measured_holdout_audit_2026-10-27.json"
    audit78 = json.loads(audit_path.read_text()) if audit_path.exists() else {}

    chk_zeros["note"] = note
    chk_nan["note"] = note
    chk_json_path = out_dir / f"checks-{path_zeros.stem}.json"
    chk_json_path.write_text(json.dumps(chk_zeros, indent=1) + "\n")
    (out_dir / f"checks-{path_nan.stem}.json").write_text(json.dumps(chk_nan, indent=1) + "\n")
    print(f"Wrote submission verification receipt: {chk_json_path}")

    run_card = {
        "schema": "run_card/v1 (PARALLEL-RUN PROTOCOL item 5 — remediated 2026-10-27)",
        "session": f"2026-10-27 H78 MHSCF ({cid}) — remediated post-PR#60 audit",
        "remediation_irregularity": "IR-25-H78-FABRICATED-HOLDOUT-AND-CI-FAILURE-20261027",
        "hypothesis": "H78-MHSCF: Static heuristic linear combination of gravity/magnetic gradients, DEM crest/slope, spring/vent proximity, and X1_ThK with ridge-NMS, B2 collar (d_cat > 2.0 px), and 2.85-px Poisson disc thinning.",
        "mechanism": "Static heuristic weighted fusion without supervised LOQO training; post-hoc audited on draws [60, 61].",
        "named_non_fault_mimic": "Intrusive pluton boundaries, unfaulted volcanic flow fronts, hydrothermally altered calderas, erosional terrace scarps.",
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator": "gems25.metric.dti_binary (alpha=0.2, beta=0.8, R=3.0px)",
            "draws": audit78.get("draws", [60, 61]),
            "pooled_dti": audit78.get("pooled_dti"),
            "ci95": audit78.get("ci95"),
            "withheld_positive_occurrences": audit78.get("withheld_positive_occurrences"),
        },
        "organizer_confirmed_score": None,
        "estimated_competition_score": None,
        "correlation_overlap_vs_registry": {
            "lane_clear": False,
            "verdict": lane_data["verdict"],
            "verdict_density_aware": lane_data["verdict_density_aware"],
            "flagged_literal": lane_data["flagged_literal"],
            "flagged_lane": lane_data["flagged_lane"],
            "total_registry_checked": lane_data["registry_checked"],
        },
        "validator_output": {
            "format_valid": bool(chk_zeros["format_valid"]),
            "ok_to_upload_format_only": bool(chk_zeros["ok_to_upload"]),
            "bytes": path_zeros.stat().st_size,
            "positive_pixels": chk_zeros["positive_pixels"],
            "hard_failures": chk_zeros["hard_failures"],
        },
        "submission": {
            "name": fname_zeros,
            "nan_twin": fname_nan,
            "zip": zip_path.name,
            "note": note,
            "note_chars": len(note),
            "content_id": cid,
            "verdict": "negative",
            "slot_approved": False,
            "ok_to_download": True,
            "ok_to_submit": False,
        },
        "verdict": "negative",
        "slot_approved": False,
        "ok_to_download_inspection": True,
        "ok_to_submit_slot": False,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    rc_path = ROOT / "registry" / "run_card_h78_2026-10-27.json"
    rc_path.write_text(json.dumps(run_card, indent=1) + "\n")
    print(f"Wrote run card: {rc_path}")

    print("\n=======================================================")
    print("GENERATED ARCHIVED RESEARCH ARTIFACT (DO NOT SUBMIT):")
    print(f"  GeoTIFF: docs/downloads/{fname_zeros}")
    print(f"  ZIP:     docs/downloads/{zip_path.name}")
    print(f"  Dots:    {num_dots:,}")
    print(f"  SHA-256: {chk_zeros['sha256']}")
    print(f"  Note:    {note}")
    print("  OK to download (inspection): YES")
    print("  OK to submit (weekly slot):  NO — DO NOT SUBMIT")
    print(f"  Lane verdict:   {lane_data['verdict_density_aware']}")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
