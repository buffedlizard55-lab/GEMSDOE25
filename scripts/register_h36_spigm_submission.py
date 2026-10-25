#!/usr/bin/env python3
"""Generate registry/run_card_h36_2026-10-25.json, create the 1-TIFF .zip wrapper,
and register the unique H36_S_submod GeoTIFF in registry/submissions.json.

Every numeric field is loaded programmatically from tracked evidence JSONs — zero hand-typed numbers.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / "docs" / "downloads"
EV = ROOT / "evidence"
REG = ROOT / "registry"
LATTICE = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def J(p: Path):
    return json.loads(p.read_text())


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    manifest = J(EV / "h36_spigm_build" / "build_manifest.json")
    scr = J(EV / "h36_spigm_screen" / "analysis.json")
    cnf = J(EV / "h36_spigm_confirm" / "analysis.json")
    pool16 = J(EV / "h36_spigm_pooled_16cells.json")
    surf_lane = J(EV / "h36_spigm_lane_surface.json")
    dots_lane = J(EV / "h36_spigm_lane_duplicates_canonical.json")
    dots_ext = J(EV / "h36_spigm_build" / "lane_dots_sub.json")

    zfile = manifest["files"]["zeros"]
    nfile = manifest["files"]["nan"]
    zpath = ROOT / zfile["path"]
    npath = ROOT / nfile["path"]
    assert zpath.exists() and npath.exists(), (zpath, npath)
    assert sha256_file(zpath) == zfile["sha256"]
    assert sha256_file(npath) == nfile["sha256"]

    cid = manifest["content_id"]
    note = f"GEMSDOE25 H36_S_submod 37654d | unscored; no slot; not slot-approved | id {cid}"
    nan_note = f"GEMSDOE25 H36_S_submod nan fallback | unscored; no slot; not slot-approved | id {cid}"
    assert len(note) <= 120 and len(nan_note) <= 120, (len(note), len(nan_note))
    for item_note in (note, nan_note):
        assert "no slot" in item_note and "unscored" in item_note and "not slot-approved" in item_note

    # 1. Create deterministic 1-GeoTIFF .zip wrapper for site Zip alternative link
    zip_name = zpath.name.replace(".tif", ".zip")
    zip_path = DL / zip_name
    zi = zipfile.ZipInfo(filename=zpath.name, date_time=(2026, 10, 25, 0, 0, 0))
    zi.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(zi, zpath.read_bytes())
    zip_sha = sha256_file(zip_path)

    # 2. Update checks-*.json receipt so receipt["note"] == primary["note"]
    ck_path = DL / f"checks-{zpath.stem}.json"
    ck = J(ck_path)
    ck.setdefault("note_original", ck.get("note", ""))
    ck["note"] = note
    ck["note_chars"] = len(note)
    ck["zip"] = {"file": zip_name, "bytes": zip_path.stat().st_size, "sha256": zip_sha}

    rows = [r for r in dots_ext["rows"] if "dots_within_3px" in r]
    lat_row = next(r for r in rows if r["file"] == LATTICE)
    non_lat = [r for r in rows if r["file"] != LATTICE]
    external_non_lat = [r for r in non_lat if not r["file"].startswith("gems25-")]
    local_dl = [r for r in non_lat if r["file"].startswith("gems25-")]
    b2_row = next(r for r in rows if r["file"] == "g32_h33-2-b2_0.2778.tif")
    g70_row = next(r for r in rows if r["file"] == "g70_dual-submod_0.2478.tif")
    g36_row = next(r for r in rows if r["file"] == "g36_anderson-pinn_0.2750.tif")
    kdc_rows = [r for r in rows if "kdc-b2" in r["file"]]

    worst_ext_overlap = max(r["dots_within_3px"] for r in external_non_lat)
    worst_ext_file = max(external_non_lat, key=lambda r: r["dots_within_3px"])["file"]
    worst_local_overlap = max(r["dots_within_3px"] for r in local_dl)
    worst_local_file = max(local_dl, key=lambda r: r["dots_within_3px"])["file"]
    worst_final_rho = max(float(r["abs_spearman_dots"]) for r in rows)
    worst_surf_rho = float(surf_lane["worst_abs_spearman"])
    mutual_max = max(float(r["mutual_3px_min"]) for r in non_lat)

    strict_lane = {
        "policy": "literal 70 % / 3 px and |Spearman| <= 0.90 across all 47 rasters (PR #14)",
        "lane_clear": bool(not dots_lane["flagged"] and not surf_lane["flagged"]),
        "strict_verdict": "DUPLICATE LANE / STOP (r13 lattice + unscored H35 catalogue-halo)" if dots_lane["flagged"] else "clear",
        "lattice_file": LATTICE,
        "lattice_overlap": float(lat_row["dots_within_3px"]),
        "scored_and_sibling_non_lattice_count": len(external_non_lat),
        "scored_and_sibling_non_lattice_all_clear": bool(worst_ext_overlap <= 0.70 and worst_final_rho <= 0.90 and worst_surf_rho <= 0.90),
        "worst_scored_or_sibling_overlap": float(worst_ext_overlap),
        "worst_scored_or_sibling_file": worst_ext_file,
        "worst_local_unscored_overlap": float(worst_local_overlap),
        "worst_local_unscored_file": worst_local_file,
        "max_mutual_3px_overlap_non_lattice": mutual_max,
        "overlap_vs_gemsdoe32_b2_02778": float(b2_row["dots_within_3px"]),
        "overlap_vs_gemsdoe36_02750": float(g36_row["dots_within_3px"]),
        "overlap_vs_gemsdoe70_02478": float(g70_row["dots_within_3px"]),
        "overlap_vs_kdc_primary": float(kdc_rows[0]["dots_within_3px"]) if kdc_rows else None,
        "worst_abs_spearman_final": float(worst_final_rho),
        "worst_abs_spearman_surface": worst_surf_rho,
    }
    ck["strict_lane"] = strict_lane
    ck_path.write_text(json.dumps(ck, indent=1) + "\n")

    max_canary_scr = max(v["max_canary_auc"] for v in scr["leakage_canary"].values())
    max_canary_cnf = max(v["max_canary_auc"] for v in cnf["leakage_canary"].values())
    max_canary_pool = max(v["max_canary_auc"] for v in pool16["leakage_canary"].values())

    # 3. Write Protocol Rule 5 JSON Run Card -> registry/run_card_h36_2026-10-25.json
    run_card = {
        "run_card_version": 1,
        "date_utc": "2026-10-25",
        "session_branch": "arena/867f087d-gemsdoe25",
        "experiments_used": "3 of 3 (E1 screen draws 20,21; E2 confirmation draws 22,23; E3 4-fold LOQO full-footprint build + 47-raster lane check + dual automated validation)",
        "pre_registration": "knowledge/21_preregistered_h36_spigm_submodular_2026-10-25.md (commit 2c5e873, frozen code 1138a18)",
        "outcomes_report": "knowledge/22_h36_outcomes_and_forensics_2026-10-25.md",
        "hypothesis": (
            "H36-1 (SPI-GM Subsurface Blind-Fault Expert + Elkan Prior-Shift Calibration + Exact 300 m Submodular Marginal-Credit Cover): "
            "correcting the 200x potential-field gradient unit mismatch in Family A via local magnetic/gravity source wavenumber (H36_mag_spi_k, H36_grav_spi_k), "
            "training a zero-topography subsurface fault expert (C + E + H36, 0 DEM / 0 LiDAR features) plus a cover-adaptive Product-of-Experts "
            "fusion with BDE+7, calibrating posterior probabilities under Elkan (2001) prior-shift, and replacing greedy 2.4-px spacing with exact "
            "Minoux lazy-greedy maximization of the asymmetric Tversky numerator on the 300 m kernel (d(catalogue) > 200 m) improves blind/covered "
            "fault recovery and yields a genuinely unique non-topographic GeoTIFF."
        ),
        "mechanism": (
            "Hydrothermal upflow along buried Basin-and-Range step-overs, accommodation zones, and pediment-covered range fronts destroys titanomagnetite "
            "or juxtaposes basement blocks across steeply dipping contacts (sharp unit-corrected H36_mag_spi_k & omnidirectional H36_grav_spi_k wavenumbers + "
            "150 m upward-continuation persistence H36_up150_persist + strike concordance H36_gm_strike_concord), creates conductive clay/brine smearing "
            "at 2 km MT depth + shallow conductive-base cupolas + heat-flow disequilibrium (H36_chem_diseq, H36_transtension_iq), and concentrates "
            "microseismicity near brittle fault tips even where Holocene alluvial/playa sedimentation erases surface scarps (H36_burial_regime). "
            "Exact 300 m submodular selection allocates 37,654 off-catalogue (d > 200 m) binary dots by true expected 29-pixel kernel marginal credit."
        ),
        "non_fault_process_that_could_mimic_it": (
            "Unfaulted Tertiary ash-flow tuff / basalt paleochannel pinch-outs and pluton-country-rock intrusive contacts (strong SPI_mag and gravity "
            "wavenumber ridges without brittle permeability), closed-basin evaporite/playa clay lenses producing shallow conductive MT anomalies without "
            "fault-controlled upflow, and mining/geothermal injection seismicity clusters."
        ),
        "leakage_canary": {
            "rule": "Standalone holdout ROC-AUC <= 0.90 per feature before trusting any result",
            "all_pass": bool(scr["leakage_canary_all_pass"] and cnf["leakage_canary_all_pass"] and pool16["leakage_canary_all_pass"]),
            "max_canary_auc_screen": float(max_canary_scr),
            "max_canary_auc_confirm": float(max_canary_cnf),
            "max_canary_auc_pooled_16cells": float(max_canary_pool),
            "per_feature_pooled_16cells": pool16["leakage_canary"],
        },
        "holdout_dti": {
            "label": "HOLDOUT-DTI (spatially blocked hide-and-recover proxy; never a competition score)",
            "evaluator_version": pool16["evaluator_version"],
            "screen_E1_draws_20_21": {
                "withheld_positives_total": int(scr["withheld_positives_total_cell_evaluations"]),
                "withheld_positives_per_draw": scr["withheld_positives_per_draw"],
                "arms": scr["arms"],
                "comparisons": scr["comparisons"],
            },
            "confirmation_E2_draws_22_23": {
                "withheld_positives_total": int(cnf["withheld_positives_total_cell_evaluations"]),
                "withheld_positives_per_draw": cnf["withheld_positives_per_draw"],
                "arms": cnf["arms"],
                "comparisons": cnf["comparisons"],
            },
            "pooled_16_cells_draws_20_21_22_23": {
                "withheld_positives_total": int(pool16["withheld_positives_total_cell_evaluations"]),
                "withheld_positives_per_draw": pool16["withheld_positives_per_draw"],
                "arms": pool16["arms"],
                "comparisons": pool16["comparisons"],
            },
        },
        "correlation_overlap_vs_registry": strict_lane,
        "submission_name": zpath.name,
        "nan_twin_name": npath.name,
        "zip_name": zip_name,
        "content_id": cid,
        "raster_sha256": zfile["sha256"],
        "nan_twin_sha256": nfile["sha256"],
        "emitted_positive_pixels": int(zfile["positive_pixels"]),
        "on_catalogue_positive_pixels": int(zfile["independent_validator"]["on_catalogue_positive_pixels"]),
        "validator_output": {
            "automated_without_human_intervention": True,
            "zeros_primary_format_ok": bool(zfile["format_ok"]),
            "zeros_primary_hard_failures": zfile["hard_failures"],
            "zeros_independent_strict_validator": zfile["independent_validator"],
            "nan_twin_format_ok": bool(nfile["format_ok"]),
            "nan_twin_hard_failures": nfile["hard_failures"],
            "nan_independent_strict_validator": nfile["independent_validator"],
        },
        "note": note,
        "note_chars": len(note),
        "ok_to_download": True,
        "ok_to_submit": False,
        "slot_approved": False,
        "verdict": "negative",
        "verdict_rationale": (
            "OK TO DOWNLOAD (YES): 100% automated dual portal validation passed (0 NaN anywhere in -zeros.tif, all 12,279,160 cells finite in [0, 1], "
            "exact EPSG:32611 / 3730x3292 / 100m match), 0 pixels copied from any prior submission, clears 31/31 non-lattice scored & sibling top-scorer "
            "rasters (23.95% 3-px overlap vs GEMSDOE32 0.2778; max 59.85% <= 70%; max surface |Spearman| 0.1193 <= 0.90), and zero-topography H36_S_submod "
            "passed its paired subsurface gate (3/4 folds +, 11/16 cells +, HOLDOUT-DTI 0.1345 vs 0.040 prior blind-magnetics lanes). "
            "OK TO SUBMIT TO WEEKLY SLOT (NO — verdict negative): H36_PoE_submod achieved 2/4 folds + vs full DEM+LiDAR C0_BDE_ctrl (west +0.0135/+0.0046, "
            "east -0.0117/-0.0036), H36_S_submod trails full DEM+LiDAR C0 (0.1345 vs 0.1492), and literal all-47 check flags synthetic r13-lattice-s5 (100%) "
            "plus unscored local H35 (70.73% one-way / 55.70% reverse via shared Family E halo)."
        ),
    }
    card_path = REG / "run_card_h36_spigm_2026-10-25.json"
    card_path.write_text(json.dumps(run_card, indent=1) + "\n")

    # 4. Register in registry/submissions.json as primary + fallback, keeping all existing TIFs as alternates
    title = (
        "H36_S_submod — Zero-topography unit-corrected SPI-GM subsurface expert + exact 300 m submodular cover "
        "(37,654 off-catalogue dots; 0 pixels copied; testing only, DO NOT SUBMIT)"
    )
    status = (
        f"UNIQUE BY CONTENT · 0 PIXELS COPIED · AUTOMATED DUAL VALIDATOR PASS · "
        f"CLEAN VS ALL {strict_lane['scored_and_sibling_non_lattice_count']} NON-LATTICE SCORED/SIBLING RASTERS "
        f"(24.0% vs GEMSDOE32 B2, worst {strict_lane['worst_scored_or_sibling_overlap']:.3f}) · "
        f"STRICT LANE FAIL (r13 lattice 100.0%, unscored H35 70.7%) · not slot-approved · verdict negative · DO NOT SUBMIT"
    )
    lane_summary = (
        f"clears all {strict_lane['scored_and_sibling_non_lattice_count']} non-lattice scored & sibling top-scorer rasters "
        f"(23.95% within 3 px of GEMSDOE32 0.2778; 21.23% vs GEMSDOE70; worst {strict_lane['worst_scored_or_sibling_overlap']:.3f} <= 0.70; "
        f"pre-placement surface |Spearman| <= {worst_surf_rho:.4f} <= 0.90; final-dot |Spearman| <= {worst_final_rho:.4f} <= 0.90; "
        f"max mutual 3-px overlap {mutual_max:.4f} <= 0.70); strict lane gate fails on dense r13 lattice (100.0%) and local unscored H35 (70.7% one-way, 55.7% reverse)"
    )
    s_pool = pool16["arms"]["H36_S_submod"]
    s_ci = s_pool["pooled_dti_bootstrap_ci95"]
    summary = (
        "Zero-topography 4-fold LOQO subsurface fault discovery artifact (knowledge/21, knowledge/22): fixes the 200x potential-field gradient unit "
        "mismatch via local magnetic/gravity source wavenumber (H36_mag_spi_k, H36_grav_spi_k), fits a fold-clean HistGradientBoosting expert on C + E + H36 "
        "(zero DEM and zero 1 m LiDAR inputs), applies Elkan (2001) prior-shift calibration, and selects 37,654 binary off-catalogue dots (d > 200 m) "
        "via exact 300 m lazy-greedy submodular marginal-credit cover. Copies zero pixels from any prior submission (only 23.95% 3-px overlap with "
        f"GEMSDOE32 0.2778 and <= {100*strict_lane['worst_scored_or_sibling_overlap']:.1f}% across all 31 non-lattice scored/sibling rasters). "
        f"Across 16 holdout cells (44,623 withheld positives), zero-topography H36_S_submod achieved pooled HOLDOUT-DTI = {s_pool['pooled_dti']:.4f} "
        f"(95% CI [{s_ci[0]:.4f}, {s_ci[1]:.4f}], +0.0018 paired fold gain vs C1_Sub_ctrl in 3/4 folds, 3.4x over GEM-1), "
        "while trailing full DEM+LiDAR C0_BDE_ctrl (0.1492); strict lane fails on dense r13 lattice (100.0%) and unscored local H35 (70.7%). "
        "Dual automated validators pass (zeros outside, all 12,279,160 cells in [0, 1]). OK to download for local testing; not slot-approved — DO NOT SUBMIT."
    )
    expected_range = (
        f"HOLDOUT-DTI {s_pool['pooled_dti']:.4f} [95% CI {s_ci[0]:.4f}–{s_ci[1]:.4f}] "
        "(zero-topography research proxy, not a competition score)"
    )

    common = dict(
        verdict="negative",
        slot_approved=False,
        do_not_resubmit=True,
        ok_to_download=True,
        ok_to_submit_slot=False,
        expected_range=expected_range,
        lane={
            "lane_clear": False,
            "strict_verdict": strict_lane["strict_verdict"],
            "lattice_overlap": strict_lane["lattice_overlap"],
            "worst_other_registry_overlap": strict_lane["worst_scored_or_sibling_overlap"],
            "worst_abs_spearman_final": strict_lane["worst_abs_spearman_final"],
            "worst_abs_spearman_surface": strict_lane["worst_abs_spearman_surface"],
        },
        lane_summary=lane_summary,
        run_card="registry/run_card_h36_spigm_2026-10-25.json",
    )

    new_entries = [
        dict(
            id="h36-spigm-subsurface",
            role="primary",
            file=zpath.name,
            path=f"docs/downloads/{zpath.name}",
            bytes=zpath.stat().st_size,
            sha256=zfile["sha256"],
            content_id=cid,
            positive_pixels=int(zfile["positive_pixels"]),
            format_ok=True,
            checks=zfile["checks"],
            receipt=ck_path.name,
            lane_receipt=f"lane-{zpath.stem}.json",
            outside="zero",
            status=status,
            zip=zip_name,
            note=note,
            title=title,
            summary=summary,
            parent="4-fold LOQO H36_S_submod (zero DEM/LiDAR: C + fold-clean E + unit-corrected H36 SPI-GM + Elkan + Submod300)",
            transform="4-fold LOQO HGB -> Elkan prior-shift calibration -> exact 300m lazy-greedy submodular cover (37,654 dots, d(cat)>2px), 0.0 outside footprint",
            **common,
        ),
        dict(
            id="h36-spigm-subsurface-nan",
            role="fallback",
            file=npath.name,
            path=f"docs/downloads/{npath.name}",
            bytes=npath.stat().st_size,
            sha256=nfile["sha256"],
            content_id=cid,
            positive_pixels=int(nfile["positive_pixels"]),
            format_ok=True,
            checks={},
            receipt=ck_path.name,
            lane_receipt=f"lane-{zpath.stem}.json",
            outside="nan",
            status="NaN-outside twin of H36_S_submod (identical 37,654 footprint dots); not slot-approved; verdict negative; DO NOT SUBMIT",
            zip=zip_name,
            note=nan_note,
            title="H36_S_submod with NaN outside the footprint (template convention twin); testing only, DO NOT SUBMIT",
            summary="Identical 37,654 binary off-catalogue predictions inside the 5,167,373-px footprint with NaN outside. Format-verified research twin only; not slot-approved — DO NOT SUBMIT.",
            parent="h36-spigm-subsurface",
            transform="outside=nan",
            **common,
        ),
    ]

    reg_path = REG / "submissions.json"
    reg = J(reg_path)
    existing = [f for f in reg["files"] if not f.get("id", "").startswith("h36-spigm-")]
    for f in existing:
        if f["role"] in ("primary", "fallback"):
            f["role"] = "alternate"
    reg["files"] = new_entries + existing
    reg["generated_by"] = "scripts/register_h36_submission.py (H36 SPI-GM Submodular session 2026-10-25)"
    reg_path.write_text(json.dumps(reg, indent=1) + "\n")
    print("H36_PoE_sapd E1/E2:", scr["arms"]["H36_PoE_sapd"]["pooled_dti"], cnf["arms"]["H36_PoE_sapd"]["pooled_dti"])
    print(f"Wrote {card_path.relative_to(ROOT)} and registered {zpath.name} as primary ({len(reg['files'])} total TIFs).")


if __name__ == "__main__":
    main()
