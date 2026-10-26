#!/usr/bin/env python3
"""Finalize the APFL session (knowledge/29): run card + registry + score scenarios.

Writes registry/run_card_apfl2_2026-10-26.json (Protocol #5), registers the new
testing TIFs at the top of registry/submissions.json as DO NOT SUBMIT (demoting
the previous primary to alternate, repo convention), and writes
evidence/apfl2_score_scenarios.json (exact DTI break-even algebra; scenarios are
INFERENCE, never scores). Reads only committed evidence + receipts; fits nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CID = "2e9e4189f554"
ZEROS = f"gems25-apfl2-h35plus-apfl-b2-sapd2-4-k3p5-20261026-{CID}-zeros.tif"
NANF = f"gems25-apfl2-h35plus-apfl-b2-sapd2-4-k3p5-20261026-{CID}-nan.tif"
NOTE = "GEMSDOE25 APFL2 H35+APFL B2 sapd2.4 | holdout FAIL; no slot; unscored; not slot-approved | id 2e9e4189f554"
FOCUS_LOCAL = {
    "GEMSDOE24": "g24_d1-5_0.2477.tif", "GEMSDOE25": "g25_d2-8_0.2600.tif",
    "GEMSDOE27": "g27_topo-gap-d1-5_0.2449.tif", "GEMSDOE28": "g28_h36-1-rung30_0.2710.tif",
    "GEMSDOE30": "g30_d28-poisson_0.2600.tif", "GEMSDOE31": "g31_h27-4-solo-d28_0.2708.tif",
    "GEMSDOE32": "g32_h33-2-b2_0.2778.tif", "GEMSDOE33": "g33_h33d_0.2632.tif",
    "GEMSDOE36": "g36_anderson-pinn_0.2750.tif",
}


def J(p: Path):
    return json.loads(Path(p).read_text())


def main() -> None:
    assert len(NOTE) <= 140
    direct = J(ROOT / "evidence/apfl_direct_screen/analysis.json")
    hgb = J(ROOT / "evidence/apfl_hgb_screen/analysis.json")
    checks = J(ROOT / f"docs/downloads/checks-{Path(ZEROS).stem}.json")
    lane = J(ROOT / f"docs/downloads/lane-{Path(ZEROS).stem}.json")
    surf = J(ROOT / "evidence/apfl2_lane_surface.json")
    rows = {r["file"]: r for r in lane["rows"]}
    # Lane checker dedupes registry rasters by SHA-256, so a focus raster restored
    # under two names (data/scored + data/registry_top) appears once, under either
    # name. Key the focus lookup by pinned SHA-256, falling back to filename.
    top_src = {r["local"]: r["sha256"] for r in J(ROOT / "registry/top_scorer_sources.json")["rasters"]}
    by_sha = {r["sha256"]: r for r in lane["rows"]}
    def focus_row(fname: str) -> dict:
        return rows.get(fname) or by_sha[top_src[fname]]
    focus_overlap = {site: dict(dots_within_3px=focus_row(f)["dots_within_3px"], spearman=focus_row(f)["spearman"],
                                byte_identical=focus_row(f)["byte_identical"], lane_file=focus_row(f)["file"])
                     for site, f in FOCUS_LOCAL.items()}
    ext = [r for r in lane["rows"] if not r["file"].startswith("gems25-") and not r.get("non_discriminative_dense")]
    own = [r for r in lane["rows"] if r["file"].startswith("gems25-")]
    worst_ext = max(ext, key=lambda r: r["dots_within_3px"])
    worst_own = max(own, key=lambda r: r["dots_within_3px"])

    # --- exact break-even algebra (S = T/(0.2M + 0.8N) with T+F ~= M for binary dots) ---
    n_truth = 12503.0  # lattice calibration, evidence/why_0_2477.json (owner-anchor dependent)
    M_new, M_b2 = 48658, 37654
    def required(M, D):
        T = D * (0.2 * M + 0.8 * n_truth)
        return dict(tp_required=round(T, 1), credit_per_px_required=round(T / M, 4))
    b2_credit_px = required(M_b2, 0.2778)["credit_per_px_required"]
    scenarios = dict(
        label="INFERENCE scenarios, NOT scores. N_truth=12503 from blind-lattice calibration (owner-anchor dependent).",
        formula="D = T/(0.2*M + 0.8*N); T_required = D*(0.2M+0.8N)",
        new_file_M=M_new,
        to_tie_0_2778=required(M_new, 0.2778), to_reach_0_3195=required(M_new, 0.3195),
        b2_implied_credit_per_px=b2_credit_px,
        if_new_file_earned_b2_credit_per_px=dict(D=round(b2_credit_px * M_new / (0.2 * M_new + 0.8 * n_truth), 4)),
        if_new_file_earned_dotted_h19_5_credit_per_px_0_0903=dict(D=round(0.0903 * M_new / (0.2 * M_new + 0.8 * n_truth), 4)),
        warning="HGB-lineage live anchor in the owner brief is H66 0.0742 (OWNER-REPORTED); catalogue-gap holdout does not predict live DTI (Spearman +0.33, n=24, n.s.). No point estimate is warranted.",
    )
    (ROOT / "evidence/apfl2_score_scenarios.json").write_text(json.dumps(scenarios, indent=1) + "\n")

    def pooled(analysis, arm):
        return analysis["arms"][arm]["pooled"]

    card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-26 APFL completion (arena/8aa4ff79-gemsdoe25)",
        preregistration="knowledge/29_preregistered_apfl_completion_2026-10-26.md (commit e78a10b, before any fit)",
        hypothesis="Blind alluvial-piedmont faults produce coincident LiDAR step + DEM TPI flexure + gravity analytic-signal + basement-depth gradient + conductivity edge (APFL product); tested DIRECT (Exp1) and as HGB columns on H35 (Exp2), B=2 collar emission.",
        mechanism="Catalogue-free 5-term product (src/gems25/apfl.py, reconstruction of the frozen knowledge/27 formula) targeting Qal-piedmont faults missing from QFFDB/INGENIOUS; ridge-NMS + score-ordered Poisson-disk dotting.",
        mimicking_non_fault_process="Unfaulted alluvial-fan onlap wedges, axial drainage incision, aeolian deflation (same TPI/depth gradients without a gravity step).",
        experiments_used="3 of 3 (Exp1 APFL-DIRECT screen draws 60-61 FAIL; Exp2 APFL-HGB screen draws 62-63 FAIL; Exp3 OCEM descriptive B2/offcat2 re-scoring, no fit). No confirmation run.",
        holdout_dti=dict(
            exp1_direct=dict(candidate=pooled(direct, "APFL_DIRECT_B2"), control_h35=pooled(direct, "CTRL_H35_24"),
                             crest_floor=pooled(direct, "CTRL_CREST_B2"), gate=direct["gate"], canary=direct["leakage_canary"]),
            exp2_hgb=dict(candidate=pooled(hgb, "H35_PLUS_APFL"), candidate_b2_descriptive=pooled(hgb, "H35_PLUS_APFL_B2"),
                          control_h35=pooled(hgb, "CTRL_H35_24"), control_b2_descriptive=pooled(hgb, "CTRL_H35_B2"),
                          gate=hgb["gate"], canary=hgb["leakage_canary"]),
            ocem_finding="B2 collar with budget refill is ~neutral on the catalogue-gap proxy (pooled +0.0002..+0.0006); live B2 was deletion without refill, untestable on this proxy. dti_offcat2 == dti in every cell: hidden whole components are >=2px from visible traces by 8-connectivity, so a >=200m off-catalogue restriction is vacuous (needs >=3-5px or distance-stratified truth).",
        ),
        correlation_overlap_vs_registry=dict(
            surface_before_placement=dict(worst_abs_spearman=surf["worst_abs_spearman"], cap=0.90, flagged=surf["flagged"],
                                          receipt="evidence/apfl2_lane_surface.json"),
            final_dots=dict(
                vs_focus_sites=focus_overlap,
                worst_external_scored=dict(file=worst_ext["file"], dots_within_3px=worst_ext["dots_within_3px"], cap=0.70),
                worst_own_lineage=dict(file=worst_own["file"], dots_within_3px=worst_own["dots_within_3px"], cap=0.70),
                vs_shipped_apfl_original=rows["gems25-apfl-piedmont-flexure-s3p0-k3p5-20261026-8aebdab87158-zeros.tif"]["dots_within_3px"],
                lattice_literal=1.0, verdict=lane["verdict"],
                reading="UNIQUE vs all 9 focus sites and all external scored rasters (worst 0.671 < 0.70; 0.316 vs GEMSDOE32 B2). NOT unique vs this repo's own unscored HGB testing lineage (0.75-0.93) — same H35 surface family. Literal lattice flag as in every prior session (IR-25-LANE-DENSITY).",
                receipt=f"docs/downloads/lane-{Path(ZEROS).stem}.json"),
        ),
        raster_sha256=checks["files"]["zeros"]["sha256"],
        validator_output=dict(file=ZEROS, format_ok=checks["files"]["zeros"]["format_ok"],
                              hard_failures=checks["files"]["zeros"]["hard_failures"],
                              positive_pixels=checks["files"]["zeros"]["positive_pixels"],
                              strict_whole_array_0_1=True,
                              detail="single-band float32 EPSG:32611 3730x3292, template transform, 0 NaN in 5,167,373-px footprint, values {0,1}; zeros-outside passes ((a>=0)&(a<=1)).all() (the check behind the owner's portal error); independently re-verified with plain rasterio this session",
                              full_checks=f"docs/downloads/checks-{Path(ZEROS).stem}.json"),
        submission=dict(name=ZEROS, note=NOTE, note_chars=len(NOTE), content_id=CID,
                        ok_to_download=True, ok_to_submit_slot=False),
        score_scenarios="evidence/apfl2_score_scenarios.json (INFERENCE only)",
        focus_audit="evidence/focus_audit_session_2026-10-26.json",
        verdict="negative — both screens failed the frozen gate vs same-run H35; lane-duplicate vs own HGB lineage; DO NOT SUBMIT. Negative result is the deliverable.",
    )
    (ROOT / "registry/run_card_apfl2_2026-10-26.json").write_text(json.dumps(card, indent=1) + "\n")

    # --- register in registry/submissions.json (newest testing file first, DO NOT SUBMIT) ---
    subs_path = ROOT / "registry/submissions.json"
    subs = J(subs_path)
    for f in subs["files"]:
        if f.get("role") in ("primary", "fallback"):
            f["role"] = "alternate"
    e2 = pooled(hgb, "H35_PLUS_APFL_B2")
    base_entry = dict(
        format_ok=True, verdict="negative", slot_approved=False, do_not_resubmit=True,
        ok_to_download=True, ok_to_submit_slot=False,
        expected_range="no live projection warranted — Exp2 screen FAIL vs H35 (see evidence/apfl2_score_scenarios.json for labelled INFERENCE scenarios, not a score)",
        lane_summary=(f"UNIQUE vs 9 focus sites (vs GEMSDOE32 B2 {focus_overlap['GEMSDOE32']['dots_within_3px']:.1%} within 3px) "
                      f"and external scored rasters (worst {worst_ext['dots_within_3px']:.1%}); surface |rho| {surf['worst_abs_spearman']:.3f}. "
                      f"NOT unique vs own HGB lineage (worst {worst_own['dots_within_3px']:.1%}, {worst_own['file']}); literal lattice 100% (IR-25-LANE-DENSITY)."),
        slot_reason=(f"Exp1 APFL-DIRECT HOLDOUT-DTI {pooled(direct,'APFL_DIRECT_B2')['pooled_dti']:.4f} vs H35 {pooled(direct,'CTRL_H35_24')['pooled_dti']:.4f} (0/4 folds); "
                     f"Exp2 H35+APFL {pooled(hgb,'H35_PLUS_APFL')['pooled_dti']:.4f} vs H35 {pooled(hgb,'CTRL_H35_24')['pooled_dti']:.4f} (1/4 folds, gain {hgb['gate']['mean_gain']:+.4f}). Frozen gate failed twice; no confirmation. Not slot-approved."),
        run_card="registry/run_card_apfl2_2026-10-26.json", note=NOTE,
    )
    entries = []
    for suffix, fname, role in (("zeros", ZEROS, "primary"), ("nan", NANF, "fallback")):
        rec = checks["files"][suffix]
        e = dict(id=f"apfl2-h35plus-apfl-b2-{suffix}", role=role, file=fname, path=f"docs/downloads/{fname}",
                 bytes=rec["bytes"], sha256=rec["sha256"], content_id=CID, positive_pixels=rec["positive_pixels"],
                 checks=rec["checks"], receipt=f"checks-{Path(fname).stem}.json",
                 outside="zero" if suffix == "zeros" else "nan",
                 status="UNIQUE vs FOCUS SITES · FORMAT-VALID · HOLDOUT FAIL (Exp1+Exp2) · OWN-LINEAGE LANE OVERLAP · verdict negative · DO NOT SUBMIT",
                 title=f"APFL2 H35+APFL B2 (sapd2.4, {suffix} outside) — TESTING ONLY · DO NOT SUBMIT",
                 summary=(f"New 2026-10-26 GeoTIFF (48,658 dots) from pre-registered APFL completion (knowledge/29): H35 HGB + 7 reconstructed piedmont-flexure columns, B=2 collar, sapd2.4. "
                          f"HOLDOUT-DTI (recipe, draws 62-63) {e2['pooled_dti']:.4f} vs same-run H35 — screen FAIL. Canary max AUC {hgb['leakage_canary']['max_feature_auc']:.3f}. "
                          f"Unique vs all 9 focus sites; strict lane gate fails vs own H35 lineage (not unique). Zeros-outside twin passes the strict [0,1] whole-array check. DO NOT SUBMIT."),
                 **base_entry)
        if suffix == "zeros":
            e["zip"] = Path(ZEROS).with_suffix(".zip").name
        entries.append(e)
    subs["files"] = entries + [f for f in subs["files"] if CID not in str(f.get("content_id"))]
    subs["generated_by"] = "APFL2 session (arena/8aa4ff79): newest testing file featured, DO NOT SUBMIT; H71 demoted to alternate"
    subs_path.write_text(json.dumps(subs, indent=1) + "\n")
    print("run card + registry + scenarios written")
    print(json.dumps(scenarios, indent=1))
    print(json.dumps(focus_overlap, indent=1))


if __name__ == "__main__":
    main()
