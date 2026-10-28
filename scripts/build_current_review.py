#!/usr/bin/env python3
"""Render the current, evidence-led decision without upgrading archives into submissions."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
e = html.escape


def read_json(path: str):
    return json.loads((ROOT / path).read_text())


def current_banner(prefix: str) -> str:
    try:
        from h81_status import banner as _h81_banner
        h81 = _h81_banner(prefix)
    except Exception:  # pragma: no cover - banner must never break the build
        h81 = ''
    return h81 + f'''<!-- CURRENT-REVIEW-2026-10-28 --><aside class="current-status" aria-label="Current decision">
<strong>28 OCT 2026 · COMPETITION-READY TIF: NO · OK TO SUBMIT: NO — DO NOT SUBMIT</strong>
<span>Independent hash-pinned geometry audit rerun: at 37,654 dots, at least 82.70% must overlap the registered
r13 halo, exceeding the strict 70% cap. No assigned single-method lane was supplied; no new fitting experiment,
TIFF or weekly slot was used. Historical downloads below are for research only. Competition score estimate: UNKNOWN.</span>
<a href="{prefix}current-review.html#review-2026-10-28">Current audit and next steps →</a>
<a href="{prefix}../knowledge/43_session_962e5a5b_review.md">Latest repair audit: executive warnings restored; stricter readiness receipts →</a></aside>'''


def render_body(root_page: bool = False) -> str:
    card = read_json("registry/run_card_2026-10-27.json")
    focus = read_json("evidence/focus_winners_reaudit_2026-10-27.json")
    geometry = read_json("evidence/lane_preflight_2026-10-27.json")
    h78 = read_json("registry/run_card_h78_2026-10-27.json")
    h79 = read_json("registry/run_card_h79_2026-10-27.json")
    h74 = read_json("registry/run_card_h74_2026-10-26.json")
    h75 = read_json("registry/run_card_h75_2026-10-27.json")
    h75_cg = read_json("registry/run_card_h75_dchb_cg_2026-10-27.json")
    h79_cthm = read_json("registry/run_card_h79_cthm_2026-10-27.json")
    sib_cg = read_json("evidence/focus_sites_h75_dchb_cg_latest_2026-10-27.json")
    h71 = read_json("registry/run_card_h71_2026-10-26.json")["holdout_dti"]
    subs = read_json("registry/submissions.json")["files"]
    archive = {s["content_id"]: s for s in subs if s["file"].endswith("-zeros.tif")}
    download = "docs/downloads/" if root_page else "downloads/"
    repo = "" if root_page else "../"
    h78_name = h78["submission"]["name"]
    descriptions = {
        "GEMSDOE24": "Different positive mask in this nine-file comparison; H19-5 D1.5 lineage.",
        "GEMSDOE25": "Exact-mask duplicate of GEMSDOE30 (D2.8).",
        "GEMSDOE27": "Different mask; D1.5 topographic gap-closure lineage.",
        "GEMSDOE28": "Rung30 winner differs from GEMSDOE31; GEMSDOE28's lower-scoring R1 is an Exact-mask duplicate of GEMSDOE31 (R1).",
        "GEMSDOE30": "Exact-mask duplicate of GEMSDOE25 (D2.8).",
        "GEMSDOE31": "R1 equals GEMSDOE28's lower-scoring R1, not its Rung30 winner.",
        "GEMSDOE32": "B2 is D2.8 after removing pixels within 200 m of the mirrored catalogue; historical, not new.",
        "GEMSDOE33": "Different mask in this nine-file comparison; not cleared against the full registry.",
        "GEMSDOE36": "Contains the B2 mask plus 1,200 additional positive pixels.",
    }
    winner_rows = []
    for row in sorted(focus["sites"], key=lambda r: -r["owner_reported_score"]):
        winner_rows.append(
            f'<tr><th><a href="{e(row["site_url"])}">{e(row["site"])}</a></th>'
            f'<td><a download href="{e(row["download_url"])}"><code>{e(row["file"])}</code></a>'
            f'<small>{row["footprint_positive_pixels"]:,} positive pixels; pinned public mirror</small></td>'
            f'<td>UNKNOWN — no calibrated estimate</td><td>{row["owner_reported_score"]:.4f}<small>OWNER-REPORTED · no organizer receipt</small></td>'
            f'<td>{e(descriptions[row["site"]])}</td><td><b>NO — historical file</b></td></tr>'
        )
    archive_rows = []
    for cid, explanation in (
        ("e7ad8a4bf3ed", "H79-CTHM-CRUSTAL-SGMC: PoE (+0.0116 vs single-HGB) & SGMC (+0.0128, 4/4 folds) pass blind gates; clears ALL 106 sparse rasters including H75-DCHB-CG (44.20%) & H75-EU3D-POE65 (44.17%); literal r13 lattice fail & below CTRL_H35."),
        ("e035d75ca5d5", "H75-DCHB-CG: Exp 3 25-km Checkerboard Gate G2 PASS (+0.02031 vs SUBSURF, +0.00384 vs ABCD; L_gap beats H35); cleared 108 pre-merge sparse rasters, literal r13 & 72.34% post-merge EU3D-POE65 convergence fail."),
        ("0a97fd71c3f3", "H75-POE65: H75_APRON 4/4 screen pass (+0.00176); CatFree POE65 literal r13 fail & below H35."),
        ("3751606e1ce5", "H74: strict lane failed; H35 holdout gate failed."),
        ("88bbebfe79b4", "H72-3: H35 FAIL · STRICT LANE FAIL."),
        ("1d7c1e9ea55f", "H72-CF: holdout and literal lane failed."),
        ("3646faf70507", "Objective diagnostic: no slot approval."),
        ("1b7533ebb62b", "H73-PM: strict lane and H35 holdout failed."),
    ):
        item = archive[cid]
        archive_rows.append(
            f'<tr><td><a download href="{download}{e(item["file"])}"><code>{e(item["file"])}</code></a>'
            f'<small>Research identifier: {e(item["note"])}</small></td>'
            f'<td>NOT ESTIMATED</td><td>{e(explanation)}</td><td><b>NO — DO NOT SUBMIT</b></td></tr>'
        )
    cg_x1 = h75_cg["holdout_dti"]["experiment_1_standard_holdout"]
    cg_x2 = h75_cg["holdout_dti"]["experiment_2_block25km_holdout"]
    cg_x3 = h75_cg["holdout_dti"]["experiment_3_checkerboard25km_full_block_holdout"]
    cg_ln = h75_cg["correlation_overlap_vs_registry"]
    cg_ci3 = cg_x3["contrasts"]["h75_cg_vs_ctrl_subsurf"]["arms"]["H75_CG_BLIND"]["ci95"]
    sib_rows = "".join(
        f'<tr><td><b>{e(r["site"])}</b></td><td><code>{e(r["file"])}</code></td>'
        f'<td>{e(r["status"])}</td><td>{e(r["uniqueness"])}</td><td><b>{e(r["ok_to_submit"])}</b></td></tr>'
        for r in sib_cg["extended_sibling_sites"]
    )
    x1_75 = h75["holdout_dti"]["experiment_1_block25km_checkerboard"]
    x2_75 = h75["holdout_dti"]["experiment_2_standard_holdout"]
    ln75 = h75["correlation_overlap_vs_registry"]
    ct_x1 = h79_cthm["holdout_dti"]["experiment_1_standard_holdout"]
    ct_x2 = h79_cthm["holdout_dti"]["experiment_2_block25km_holdout"]
    ct_x3 = h79_cthm["holdout_dti"]["experiment_3_confirm_block25km"]
    ct_c56 = h79_cthm["holdout_dti"]["shipped_crustal_sgmc_56col_readout"]
    ct_ln = h79_cthm["correlation_overlap_vs_registry"]
    ct_pm = ct_ln["post_merge_109_audit"]
    bounds = "".join(f"<tr><td>{x['dots']:,}</td><td>{x['minimum_overlap']:.2%}</td><td>Impossible</td></tr>"
                     for x in geometry["cases"])
    body = f'''<section id="review-2026-10-28" class="review-decision"><h2>28 October: independent preflight, not a new submission</h2>
<p><b>No eligible download exists. Do not spend a slot.</b> The rerun found only 6,514 eligible pixels outside the r13 three-pixel halo.
At most 21,713 distinct dots are not ruled out by this one-reference bound; fewer dots are not automatically unique or high-scoring.
Historical H73-BW: BLOCKED BEFORE FIT. This is computed geometry, not HOLDOUT-DTI. No holdout result or organizer-confirmed score was produced this session.</p>
<p><a href="{repo}evidence/lane_feasibility_2026-10-28.json">Pinned audit and source links</a> ·
<a href="{repo}knowledge/41_session_plan_2026-10-28.md">Four planning-only geological hypotheses</a> ·
<a href="{repo}knowledge/42_review_outcome_2026-10-28.md">Limitations, readiness gate and next steps</a>.</p>
<p>The new receipt-consistency gate requires exact-file identity, format, complete surface/final-dot registry checks,
feature-alone canaries and a positive paired holdout confidence interval. It permits selector review only, never an upload.
Only this repository is changed; the eight sibling sites remain untouched. Tables below use historical pinned snapshots, not a current feed.</p></section><section class="hero"><p class="eyebrow">RESEARCH DECISION BRIEF / 27 OCTOBER 2026</p>
<h1>Know when to stop.</h1><p class="lead">The requested unique competition-ready TIFF remains unfulfilled. At 37,654 dots, literal overlap with the registered r13 lattice is at least 82.70%, and no catalogue-free candidate has yet beaten CTRL_H35 for weekly-slot approval. All downloads below are research/inspection archives only (<b>DO NOT SUBMIT</b>).</p>
<div class="stats"><div class="stat"><b>Research-archive download: YES</b><span>Inspection/testing only.</span></div>
<div class="stat"><b>Competition-ready TIF: NO</b><span>OK TO SUBMIT: NO — DO NOT SUBMIT.</span></div>
<div class="stat"><b>Estimated competition score: UNKNOWN</b><span>No defensible leaderboard estimate is available.</span></div></div></section>
<section class="review-decision" id="h79-cthm-poe"><span class="badge b-bad">RESEARCH ARCHIVE ONLY · CLEARS ALL 106 SPARSE RASTERS (&le;58.02%) · LITERAL R13 LANE FAIL · DO NOT SUBMIT</span>
<h2>Latest H79-CTHM+SGMC Crustal-Thermomechanical LOQO B2 GeoTIFF &amp; Domain-Decoupled PoE Suite (draws 114–117)</h2>
<p><a download href="{download}{e(h79_cthm['submission_name'])}"><code>{e(h79_cthm['submission_name'])}</code></a> · <a download href="{download}{e(h79_cthm['nan_twin_name'])}">NaN-outside twin</a> · <a download href="{download}{e(h79_cthm['zip_name'])}">matching ZIP</a> · <a download href="{repo}registry/run_card_h79_cthm_2026-10-27.json">H79-CTHM JSON Run Card</a> · <a href="{repo}knowledge/40_h79_cthm_poe_outcome_2026-10-27.md">Full H79-CTHM report, 9-site live audit &amp; 0.2778 PhD proof</a> · <a href="{repo}registry/review_passes_h79_2026-10-27.json">3 review passes</a> · <b>OK TO DOWNLOAD: YES (inspection/testing only) · OK TO SUBMIT: NO — DO NOT SUBMIT</b> (OK to spend a weekly slot: NO).</p>
<p>Content id <code>{e(h79_cthm['content_id'])}</code> · <code>{h79_cthm['positive_pixels']:,}</code> binary dots · SHA-256 <code>{e(h79_cthm['raster_sha256'])}</code> · EPSG:32611 · <code>3730&times;3292</code> · 0 NaN/Inf across all 12,279,160 cells in <code>[0, 1]</code> (prevents portal error <code>"Predicted values must be in range [0, 1]"</code>) · research identifier: <code>{e(h79_cthm['note'])}</code>. Pre-registered at <a href="{repo}knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md"><code>b59b129</code></a> before code or fitting: four zero-topography crustal/hydrothermal operators (<code>H79_aniso_conduit_plume</code>, <code>H79_demag_argillic_crest</code>, <code>H79_euler_contact_index</code>, <code>H79_grav_mt_gouge_juxtapose</code>) plus strike-aligned USGS SGMC Coulomb reactivation (<code>H79_sgmc_coulomb_react</code>) and two-expert floor-protected Product-of-Experts <code>S_PoE</code>.</p>
<p><b>Holdout outcomes (HOLDOUT-DTI, virgin draws 114–117, all 2,232 standalone feature canaries &le; 0.8656 &le; 0.90):</b> (1) <b>Exp 1 (Standard Holdout, draws [114, 115], {ct_x1['withheld_positive_occurrences']:,} withheld +):</b> <code>H79_POE</code> <code>{ct_x1['h79_poe_pooled']:.5f}</code> (<code>+{ct_x1['poe_vs_ctrl_subsurf']['paired_gain']:.5f}</code> vs <code>CTRL_SUBSURF</code> across 4/4 folds; <code>CTRL_H35</code> <code>{ct_x1['ctrl_h35_pooled']:.5f}</code>). (2) <b>Exp 2 (25-km Block Holdout, draws [114, 115], {ct_x2['withheld_positive_occurrences']:,} withheld +, median d_vis {ct_x2['median_truth_d_vis_px']:.1f} px):</b> <code>H79_POE</code> <code>{ct_x2['h79_poe_pooled']:.5f}</code> (<code>+{ct_x2['poe_vs_ctrl_subsurf']['paired_gain']:.5f}</code> vs <code>CTRL_SUBSURF</code> across 4/4 folds; <code>H79_SUBSURF</code> <code>+{ct_x2['subsurf_vs_ctrl_subsurf']['paired_gain']:.5f}</code>). (3) <b>Exp 3 (25-km Block Confirmation + SGMC, virgin draws [116, 117], {ct_x3['withheld_positive_occurrences']:,} withheld +): BOTH Blind Gates PASS — <code>H79_POE</code> (<code>{ct_x3['h79_poe_pooled']:.5f}</code>) beat single concatenated HGB on identical 81 features by <code>+{ct_x3['poe_vs_single_hgb']['paired_gain']:.5f}</code> (95% CI <code>[{ct_x3['poe_vs_single_hgb']['paired_ci95'][0]:+.4f}, {ct_x3['poe_vs_single_hgb']['paired_ci95'][1]:+.4f}]</code>), and adding <code>H79_sgmc_coulomb_react</code> raised <code>H79_POE_SGMC</code> to <code>{ct_x3['h79_poe_sgmc_pooled']:.5f}</code> (<code>+{ct_x3['poe_sgmc_vs_poe']['paired_gain']:.5f}</code>, 4/4 folds; very-far &gt;20 px DTI <code>0.10059</code>)</b>; shipped 56-col zero-topography <code>H79_CRUSTAL_SGMC</code> scored <code>{ct_c56['pooled_dti']:.5f}</code> (95% CI <code>[{ct_c56['ci95'][0]:.4f}, {ct_c56['ci95'][1]:.4f}]</code>, +36.2% above <code>H74_SUBSURF</code>), below <code>CTRL_H35</code> (<code>{ct_x3['ctrl_h35_pooled']:.5f}</code>). <b>Uniqueness across all {ct_pm['total_unique_sha_aligned_rasters_checked']} aligned rasters: clears ALL {ct_pm['sparse_halo_lt_0p70_count']} sparse rasters (&le;58.02% max vs <code>h19-c.tif</code>; 23.54% vs B2; 49.69% vs H74-SUBSURF; 44.20% vs H75-DCHB-CG; 44.17% vs H75-EU3D-POE65; 29.14% vs H78; 20.61% vs H79-scaffold)</b>, while literal 70% flags the 3 &gt;70%-halo rasters (r13 lattice 100.00%, 82.70% min; pindrop 75.5–75.7%) — <b>DO NOT SUBMIT.</b></p></section>
<section class="review-decision" id="h75-dchb-cg"><span class="badge b-bad">RESEARCH ARCHIVE ONLY · EXP 3 CHECKERBOARD G2 PASS · LITERAL R13 &amp; CONCURRENT POE FAIL · DO NOT SUBMIT</span>
<h2>Latest H75-DCHB-CG Corridor-Gated Dual-Regime LOQO B2 GeoTIFF &amp; 25-km Full Checkerboard BlockHoldout (draws 120–123)</h2>
<p><a download href="{download}{e(h75_cg['submission_name'])}"><code>{e(h75_cg['submission_name'])}</code></a> · <a download href="{download}{e(h75_cg['nan_twin_name'])}">NaN-outside twin</a> · <a download href="{download}{e(h75_cg['zip_name'])}">matching ZIP</a> · <a download href="{repo}registry/run_card_h75_dchb_cg_2026-10-27.json">H75-DCHB-CG JSON Run Card</a> · <a href="{repo}knowledge/40_h75_dchb_cg_outcomes_and_executive_summary_2026-10-27.md">Full H75-DCHB-CG report, 27-repo table &amp; 0.2778 PhD proof</a> · <a href="{repo}registry/review_passes_h75_dchb_cg_2026-10-27.json">3 review passes</a> · <b>OK TO DOWNLOAD: YES (inspection/testing only) · OK TO SUBMIT: NO — DO NOT SUBMIT</b> (OK to spend a weekly slot: NO).</p>
<p>Content id <code>{e(h75_cg['content_id'])}</code> · <code>{h75_cg['positive_pixels']:,}</code> binary dots · SHA-256 <code>{e(h75_cg['raster_sha256'])}</code> · EPSG:32611 · <code>3730&times;3292</code> · 0 NaN/Inf across all 5,167,373 footprint pixels in <code>[0, 1]</code> · research identifier: <code>{e(h75_cg['note'])}</code>. Pre-registered at <a href="{repo}knowledge/38_preregistered_h75_dchb_cg_2026-10-27.md"><code>12931bb</code></a> before code or fitting: five strictly catalogue-free hydrogeologic/radiometric/Riedel/destriped-Blakely operators (<code>H75_darcy_seepage_barrier</code>, <code>H75_uth_sinter_emergence</code>, <code>H75_oblique_piedmont_inflection</code>, <code>H75_riedel_obliquity_shear</code>, <code>H75_destriped_blakely_contact</code>) coupled across 3 LOQO experts via <code>P_cor^0.60 * P_trace^0.40</code> on <code>L_valid=1</code> and quantile-calibrated <code>0.95 * P_cor^0.60 * P_gap^0.40</code> across the 24.66% <code>L_valid=0</code> 3DEP gap.</p>
<p><b>Holdout outcomes (HOLDOUT-DTI, virgin draws 120–123, all 2,184 standalone feature canaries &le; 0.8179 &le; 0.90):</b> (1) <b>Exp 1 (Standard Holdout, draws [120, 121], {cg_x1['withheld_positive_occurrences']:,} withheld +):</b> <code>H75_CG_BLIND</code> <code>{cg_x1['per_arm']['H75_CG_BLIND']['pooled_dti']:.5f}</code> (<code>+{cg_x1['contrasts']['h75_cg_vs_ctrl_subsurf']['paired_gain']:.5f}</code> vs <code>CTRL_SUBSURF</code> in 4/4 folds; <code>{cg_x1['contrasts']['h75_cg_vs_ctrl_blind_abcd']['paired_gain']:+.5f}</code> vs <code>CTRL_BLIND_ABCD</code>; <code>CTRL_H35</code> <code>{cg_x1['per_arm']['CTRL_H35']['pooled_dti']:.5f}</code>). (2) <b>Exp 2 (25-km Tile-Sampled H75-BW, draws [120, 121], {cg_x2['withheld_positive_occurrences']:,} withheld +):</b> <code>H75_CG_BLIND</code> <code>{cg_x2['per_arm']['H75_CG_BLIND']['pooled_dti']:.5f}</code> (<code>L_valid=0</code> gap DTI <code>{cg_x2['per_arm']['H75_CG_BLIND']['lidar_gap_dti']:.5f}</code>, +18.8% above <code>CTRL_BLIND_ABCD</code> <code>{cg_x2['per_arm']['CTRL_BLIND_ABCD']['lidar_gap_dti']:.5f}</code>). (3) <b>Exp 3 (25-km Full Checkerboard BlockHoldout hiding 100% of test-block components, virgin draws [122, 123], {cg_x3['withheld_positive_occurrences']:,} withheld +): Gate G2 PASS — <code>H75_CG_BLIND</code> <code>{cg_x3['per_arm']['H75_CG_BLIND']['pooled_dti']:.5f}</code> (95% CI <code>[{cg_ci3[0]:.4f}, {cg_ci3[1]:.4f}]</code>) beat BOTH <code>CTRL_SUBSURF</code> (<code>+{cg_x3['contrasts']['h75_cg_vs_ctrl_subsurf']['paired_gain']:.5f}</code>, 4/4 folds) and <code>CTRL_BLIND_ABCD</code> (<code>+{cg_x3['contrasts']['h75_cg_vs_ctrl_blind_abcd']['paired_gain']:.5f}</code>, 3/4 folds), beat <code>CTRL_H35</code> in 2/4 folds and on <code>L_valid=0</code> gap (<code>{cg_x3['per_arm']['H75_CG_BLIND']['lidar_gap_dti']:.5f}</code> vs <code>{cg_x3['per_arm']['CTRL_H35']['lidar_gap_dti']:.5f}</code>)</b>, while pooled Slot Gate G1 vs <code>CTRL_H35</code> (<code>{cg_x3['contrasts']['h75_cg_vs_ctrl_h35']['paired_gain']:+.5f}</code>) stayed negative. Cleared all {cg_ln['registry_checked']} pre-merge sparse rasters (<code>68.58% &le; 70%</code> vs <code>h23-a-6pct.tif</code>, <code>34.83%</code> vs B2, <code>27.22%</code> vs H78, <code>20.44%</code> vs H79); post-merge full-footprint 116-raster audit flags literal r13 lattice (100.00%; 82.70% min) and 72.34% 3-px dot convergence vs concurrent <code>h75-eu3d-poe65</code> (surface Spearman 0.1106) — <b>DO NOT SUBMIT.</b></p>
<details><summary><b>4 Ranked Untried H75-DCHB-CG Hypotheses &amp; Extended Sibling Site Audit (GEMSDOE48..92, KANLER, WBG, EUG, GINNY)</b></summary>
<div class="table-scroll"><table><thead><tr><th>Rank &amp; ID</th><th>Layers &amp; Physical Transform</th><th>Named Non-Fault Mimic</th><th>Planning Bracket &amp; Status</th></tr></thead><tbody>
<tr><td><b>#1 H75-1 (DCHB-CG)</b></td><td><code>dem.tif</code>, <code>magnetotelluric.tif</code>, <code>gravity.tif</code>, <code>geodawn_rad_u8.tif</code>, GDR 1391 quartz enthalpy (no <code>dist_known_fault_px</code>), <code>lidar_scarp_features_u8.tif</code>, <code>magnetic.tif</code>: Darcy piezometric barrier + U/Th sinter + cross-contour shoreline deconfounder + &plusmn;17&deg; Riedel shear + destriped Blakely contact in 3-expert Corridor-Gated Dual-Regime LOQO.</td><td>Tertiary volcanic pinch-outs, perched cold-spring caliche aprons, oblique gravel spits, dipping pluton margins</td><td><code>+0.002..+0.008</code> BlockHoldout planning bracket (not a score) · <b>IMPLEMENTED &amp; VALIDATED (Exp 3 Gate G2 PASS)</b></td></tr>
<tr><td><b>#2 H75-2 (PBVD)</b></td><td><code>gravity.tif</code> (<code>isostatic_grav</code>, <code>depth_to_base_surf</code>), <code>dem.tif</code>: Asymmetric Playfair-basin volume deficit &amp; hanging-wall depocenter tilt.</td><td>Differential compaction over buried paleovalleys or caldera fill</td><td><code>+0.001..+0.004</code> planning bracket · Deferred</td></tr>
<tr><td><b>#3 H75-3 (VVAC)</b></td><td>GDR 1391 <code>gdr_volcanic_vents_in_footprint.csv</code> + <code>magnetic.tif</code> + <code>magnetotelluric.tif</code>: Anisotropic dyke-vent chain alignment with Analytic Signal &amp; mid-crustal MT phase tensor.</td><td>Topographically channeled basaltic lava-flow lobes</td><td><code>+0.0005..+0.003</code> planning bracket · Deferred</td></tr>
<tr><td><b>#4 H75-4 (KTHP)</b></td><td><code>geodawn_rad_u8.tif</code> (<code>K, eTh, eU</code>) + <code>dem.tif</code>: Cross-divide K/eTh provenance discontinuity across D8 watershed ridges.</td><td>Stratigraphic tuff-on-carbonate unconformities &amp; aeolian loess mantles</td><td><code>+0.0005..+0.0025</code> planning bracket · Deferred</td></tr>
</tbody></table></div>
<div class="table-scroll"><table><thead><tr><th>Sibling Group</th><th>Top Verified Artifact / State</th><th>Score / Evidence Class</th><th>Uniqueness &amp; Audit Status</th><th>OK to submit?</th></tr></thead><tbody>{sib_rows}</tbody></table></div>
</details></section>
<section class="review-decision" id="h75-session"><span class="badge b-bad">RESEARCH ARCHIVE ONLY · LITERAL R13 LANE FAIL · DO NOT SUBMIT</span>
<h2>Latest H75-EU3D-POE65 research GeoTIFF &amp; 25-km Checkerboard BlockHoldout execution (draws 130–133)</h2>
<p><a download href="{download}{e(h75['submission_name'])}"><code>{e(h75['submission_name'])}</code></a> · <a download href="{download}{e(h75['nan_twin_name'])}">NaN-outside twin</a> · <a download href="{download}{e(h75['zip_name'])}">matching ZIP</a> · <a download href="{repo}registry/run_card_h75_2026-10-27.json">H75 JSON Run Card</a> · <a href="{repo}knowledge/39_h75_outcomes_and_executive_summary_2026-10-27.md">Full H75 report, 9-site table &amp; 0.2778 PhD proof</a> · <b>OK TO DOWNLOAD: YES (inspection/testing only) · OK TO SUBMIT: NO — DO NOT SUBMIT</b> (OK to spend a weekly slot: NO).</p>
<p>Content id <code>{e(h75['content_id'])}</code> · <code>{h75['positive_pixels']:,}</code> binary dots · SHA-256 <code>{e(h75['raster_sha256'])}</code> · EPSG:32611 · <code>3730&times;3292</code> · 0 NaN/Inf across all 12,279,160 cells in <code>[0, 1]</code> · research identifier: <code>{e(h75['note'])}</code>. Pre-registered at <a href="{repo}knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md"><code>3053f69</code></a> before code or fitting: two-stage <code>P_scarp^0.35 * P_root^0.65</code> coupling 28 Family-B/RBDT scarp columns with 55 static <code>ACD + H34 + H74_RMPS + H75_EU3D</code> (7&times;7 3-D Euler homogeneity <i>N</i>=0.5 contact vs <i>N</i>=2.0/2.5 plug + Morris WNW–ESE slip/dilation + basin-normalized MT-thermal) columns.</p>
<p><b>Holdout outcomes (HOLDOUT-DTI, virgin draws 130–133, all 1,520 standalone feature canaries &le; 0.8038 &le; 0.90):</b> (1) <b>Exp 1 (25-km Checkerboard BlockHoldout, draws [130, 131], {x1_75['withheld_positive_occurrences']:,} withheld +):</b> <code>PM_DEAPRON</code> (<code>{x1_75['pm_deapron_pooled']:.5f}</code>) beat <code>CTRL_H35</code> (<code>{x1_75['ctrl_h35_pooled']:.5f}</code>) by <b><code>+{x1_75['h73_bw_selector_gate']['overall_paired_gain_vs_h35']:.5f}</code></b> (3/4 folds; far &gt;9 px <code>+{x1_75['h73_bw_selector_gate']['far_gt9_paired_gain_vs_h35']:.5f}</code>, reversing <code>-0.02515</code> component-split penalty by <code>+0.02708</code>); <code>H75_POE65</code> scored <code>{x1_75['h75_poe65_pooled']:.5f}</code> (+123.9% over <code>ROOT_H75</code> in 4/4 folds). (2) <b>Exp 2 (Standard Holdout, draws [132, 133], {x2_75['withheld_positive_occurrences']:,} withheld +):</b> <b><code>H75_APRON</code> (<code>{x2_75['h75_apron_pooled']:.5f}</code>) beat <code>CTRL_H35</code> (<code>{x2_75['ctrl_h35_pooled']:.5f}</code>) by <code>+{x2_75['h75_apron_screen_gate']['paired_gain_vs_ctrl_h35']:.5f}</code> (95% CI <code>[{x2_75['h75_apron_screen_gate']['paired_ci95_vs_ctrl_h35'][0]:+.5f}, {x2_75['h75_apron_screen_gate']['paired_ci95_vs_ctrl_h35'][1]:+.5f}]</code>, 4/4 folds PASS!)</b>; shipped CatFree <code>H75_POE65</code> scored <code>{x2_75['h75_poe65_pooled']:.5f}</code> (95% CI <code>[{x2_75['h75_poe65_ci95'][0]:.5f}, {x2_75['h75_poe65_ci95'][1]:.5f}]</code>, +40.7% over <code>ROOT_H75</code> in 4/4 folds, below <code>CTRL_H35</code>). Diagnostic sparse overlap cleared all {ln75['registry_checked']} rasters (35.77% vs B2, 69.84% &le; 70% vs <code>h23-a-6pct.tif</code>, 63.78% max own-lineage), but <b>literal 70% fails vs r13 lattice (100.00%) and pindrop (76.54%) — DO NOT SUBMIT.</b></p></section>
<section class="review-decision"><span class="badge b-bad">STRICT LANE DUPLICATE · LITERAL LANE FAIL · NOT SUBMISSION-ELIGIBLE</span>
<h2>Existing H78 TIFF: format pass, not unique under the lane rule</h2>
<p><a download href="{download}{e(h78_name)}"><code>{e(h78_name)}</code></a> · <a download href="{download}{e(h78['submission']['zip'])}">matching ZIP</a> · <b>research inspection only; OK TO SUBMIT: NO — DO NOT SUBMIT</b>.</p>
<p>Local exact-file audit: one float32 band, EPSG:32611, 3730 × 3292, expected 100 m transform; all pixels finite in [0,1], zero outside, 43,550 positive pixels and zero positives on the mirrored catalogue. ZIP content matches. SHA-256 <code>{e(h78['validator_output']['sha256'])}</code>.</p>
<p><b>100% within 3 px of the registered r13 lattice; threshold 70%.</b> Full-footprint Spearman against that reference is {h78['correlation_overlap_vs_registry']['spearman_full_footprint_vs_lattice']:.6f}; the registry-wide audit is incomplete. No density waiver applies. The previous H78 holdout, forecast and submit-ready statements were hard-coded and is withdrawn / retracted.</p>
<p>The earlier portal error “Predicted values must be in range [0, 1]” is consistent with NaNs inside an earlier owner-mirrored footprint. Zero padding also passes a stricter local whole-array range check, but the official format specifies null/NaN outside the bounds; organizer acceptance of zero padding is unknown. Format does not prove novelty, performance, or approval.</p>
<p>The <a href="{repo}scripts/verify_candidate_independent.py">automated independent validator</a> checks the pinned template, labels, exact raster and ZIP without human inspection; a failed check exits nonzero. This does not replace the separate lane and scientific checks.</p>
<p><a href="{repo}evidence/h78_independent_reaudit_2026-10-27.json">Format/ZIP audit</a> · <a href="{repo}evidence/h78_literal_lane_reaudit_2026-10-27.json">Literal lane audit</a> · <a href="{repo}knowledge/38_h78_mhscf_and_phd_focus_sites_analysis_2026-10-27.md">Correction and explanation</a> · <a href="{repo}registry/run_card_2026-10-27.json">Current JSON run card</a></p></section>
<section class="review-decision"><span class="badge b-bad">CATALOGUE MASK + LITERAL LANE FAIL · DO NOT SUBMIT</span>
<h2>Concurrent H79 random-dot scaffold: not a submission</h2>
<p>A separate parallel PR added <a download href="{download}{e(h79['submission']['name'])}"><code>{e(h79['submission']['name'])}</code></a> and its <a download href="{download}{e(h79['submission']['zip'])}">ZIP</a>. This is an existing research archive, not an output of the stopped continuation and not a geological model.</p>
<p><b>99.8699% of 37,654 dots lie within 3 px of r13</b> (maximum 70%), and <b>416 positives lie on mirrored catalogue pixels</b>. Local grid/range and exact ZIP pass; the catalogue-mask gate fails. Its prior local-only novelty check did not include r13. No blocked holdout or organizer score exists; <b>DO NOT SUBMIT</b>.</p>
<p><a href="{repo}evidence/h79_independent_reaudit_2026-10-27.json">Independent mask/format audit</a> · <a href="{repo}evidence/h79_literal_lane_reaudit_2026-10-27.json">Literal lane audit</a> · <a href="{repo}registry/run_card_h79_2026-10-27.json">Corrected H79 card</a>.</p></section>
<section id="lane-feasibility"><h2>Why the frozen continuation stopped</h2>
<p>The mirrored template, labels and r13 grid were hash-checked. Only <b>6,514</b> eligible pixels are outside the lattice's 3-pixel halo. At fixed budget K, at least max(0, K − 6,514) dots overlap. For 37,654 dots the minimum is <b>82.70%</b> — a strict failure, before placement or fitting.</p>
<div class="table-scroll"><table><thead><tr><th>Fixed dot budget K</th><th>Minimum overlap</th><th>70% gate</th></tr></thead><tbody>{bounds}</tbody></table></div>
<p>At most 21,713 dots are not ruled out by this <em>one necessary bound</em>; smaller budgets are not automatically feasible or competitive. Historical H73-BW: BLOCKED BEFORE FIT. This is computed geometry, not HOLDOUT-DTI. No density exception or movement into uncovered slivers was used. <a href="{repo}evidence/lane_preflight_2026-10-27.json">Fresh preflight receipt</a>.</p></section>
<section><h2>Nine historical winners: files, claims, and uniqueness</h2>
<p>Highest <em>supplied</em> result for each requested site, not an exhaustive live leaderboard. Values are OWNER-REPORTED, not ORGANIZER-CONFIRMED; none is eligible as a new submission. New-file estimated competition score: <b>Not estimated</b>.</p>
<div class="table-scroll"><table><thead><tr><th>Site</th><th>Historical file for learning only</th><th>Estimated new-submission score</th><th>Historical score</th><th>Positive-mask uniqueness / lineage</th><th>OK to submit?</th></tr></thead><tbody>{''.join(winner_rows)}</tbody></table></div>
<p>The pinned downloads were verified against public GitHub blob IDs. <a href="{repo}evidence/focus_winners_reaudit_2026-10-27.json">Pixel audit</a> · <a href="{repo}evidence/focus_source_links_2026-10-27.json">Source verification</a> · <a href="{repo}registry/review_passes_2026-10-27.json">Three review passes</a>. Conflicting overall-leader claims 0.3195 and 0.4413 remain unverified.</p></section>
<section><h2>Why GEMSDOE32 B2 may have done well</h2>
<p>Its 0.2778 is the strongest supplied OWNER-REPORTED result. B2 equals D2.8 with 6,436 dots within 200 m of known faults removed. Sparse dots reduce redundant mass; selective pruning might remove more false-positive mass than nearby triangular-kernel credit. This is a plausible consequence of the local scoring formula, not proof of hidden-label causation or an organizer-confirmed score. A unique method might beat it, but there is no evidence or valid forecast that this continuation does.</p></section>
<section><h2>Four ranked geological hypotheses — not newly tested</h2>
<div class="table-scroll"><table><thead><tr><th>Rank and layers</th><th>Physical signature and missing-fault rationale</th><th>Named non-fault mimic</th><th>Novelty, expected benefit and cost</th></tr></thead><tbody>
<tr><td>1. Root × scarp: magnetic/gravity gradients and H74 subsurface features × LiDAR/DEM</td><td>Separately fitted subsurface edge and scarp experts corroborate a buried fault root and subtle surface trace.</td><td>Alluvial fan margin crossing a lithologic contact; lake shoreline</td><td>Separate experts and blocked testing extend H74; related H36 PoE already exists. Benefit unknown; medium-high cost.</td></tr>
<tr><td>2. Signed paired edges: GeoDAWN magnetics and gravity</td><td>Paired edge polarity and migration at two continuation scales could mark a covered fault-bounded block.</td><td>Intrusive sheets, volcanic contacts, survey seams</td><td>Tests edge pairing, not isolated edge magnitude. Benefit unknown; high cost.</td></tr>
<tr><td>3. Drainage/provenance boundary: DEM, GeoDAWN K/Th/U</td><td>Repeated compositional transitions across adjacent divides may reveal a buried structural barrier.</td><td>Fan avulsion, source-rock contacts, drainage capture</td><td>Catchment recurrence differs from local ROD translation. Benefit unknown; high cost; drainage graph not built.</td></tr>
<tr><td>4. Temperature residuals: well/spring observations, elevation and gravity</td><td>Elevation-conditioned temperature residuals aligned with basement edges might flag a concealed fault conduit.</td><td>Meteoric groundwater circulation, sampling bias</td><td>Residual modeling differs from raw proximity; benefit unknown; medium-high cost and sparse-data risk.</td></tr></tbody></table></div>
<p>Ranking is qualitative, not a score forecast. The unspecified “single method paragraph” was not identifiable; rank 1 follows the previous H74 handoff provisionally, not an owner-confirmed lane. No blocked hide-and-recover experiment or per-feature canary was run because the preregistered stop occurred first. <a href="{repo}knowledge/39_lane_hypotheses_and_preflight_2026-10-27.md">Frozen hypotheses, implementation and sources</a>.</p></section>
<section id="h73-status"><h2>Prior research archives, not submission candidates</h2>
<p><b>OK TO DOWNLOAD: YES</b> for inspection-only research archives; <b>OK TO SUBMIT: NO — DO NOT SUBMIT.</b> OK to spend a weekly slot: NO. A different filename or outside-footprint variant is not a new prediction. The density-aware statistic is diagnostic only.</p>
<div class="table-scroll"><table><thead><tr><th>Archived file</th><th>Estimated competition score</th><th>Unique under literal lane rule?</th><th>Decision</th></tr></thead><tbody>{''.join(archive_rows)}</tbody></table></div>
<p>Archived H72-3 research artifact only: prior H71 HOLDOUT-DTI {h71['pooled_dti']:.6f}, evaluator <code>{e(h71['evaluator_version'])}</code>, {h71['withheld_positives']:,} withheld positives, 95% CI [{h71['ci_95'][0]:.6f}, {h71['ci_95'][1]:.6f}]; not an organizer score. Its lane result was 100% within 3 px of the registered r13 lattice; threshold 70%.</p>
<p><b>H73-BW BLOCKED BEFORE FIT</b>: H73-BW diagnostic candidate: <b>no file produced</b>. The earlier preflight recorded eight missing cache artifacts; after the restored/rebuilt stack, the H34 sidecar and names are still missing. No H73-BW fit or HOLDOUT-DTI exists. <a href="{repo}evidence/h73_bw_cache_rebuild_2026-10-27.json">Current cache receipt</a> · <a href="{repo}registry/run_card_h73_bw_2026-10-26.json">Historical run card</a> · <a href="{repo}knowledge/30_executive_summary_and_apfl_outcomes_2026-10-26.md">APFL piedmont-flexure completion (prior negative)</a>.</p></section>
<section id="how-to-submit"><h2>Submission checklist — only after a separate selector approves</h2>
<ol><li>Preregister a feasible lane; compare the full surface before placement and final dots to the complete declared registry. Stop for |Spearman| &gt; 0.90 or &gt;70% overlap within 3 px of any one reference.</li>
<li>Test each feature alone for leakage, hide whole buffered fault segments, derive catalogue features only from visible faults, mask visible pixels exactly, and report pooled HOLDOUT-DTI with evaluator, withheld positives and 95% CI against the same-run control. Confirm on fresh draws.</li>
<li>Independently validate the exact file's finite footprint, [0,1] values, single-band grid/CRS/transform and ZIP; decide the outside-footprint convention with organizer guidance. A separate selector must respect the weekly cap. No selector approval exists now.</li>
<li>Only if all gates and selector pass, use the official competition interface and a note of at most 140 characters. Current research note: <code>{e(card['submission_note'])}</code> (not a submission instruction).</li></ol>
<details><summary>Historical file for learning only — never submit as a new file</summary>
<p>Archived H66 &amp; H74 research files for local inspection only (<code>{e(h74['submission_name'])}</code>, id <code>{e(h74['content_id'])}</code>, note <code>{e(h74['note'])}</code> — DO NOT SUBMIT): <a download href="{download}gems25-h66-mgd-flank-sapd3-0-k3p5-20261025-da617550a0e9-zeros.tif">Download historical H66 TIF — DO NOT SUBMIT</a>.</p>
</details>
<p><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Official reference code</a> · <a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN</a> · <a href="https://www.usgs.gov/3d-elevation-program/about-3dep-products-services">USGS 3DEP</a> · <a href="https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and">USGS-hosted Great Basin play-fairway report</a>. Source availability and public mirror hashes do not prove provenance or performance.</p></section>'''
    return body


def readme_status() -> str:
    h75 = read_json("registry/run_card_h75_2026-10-27.json")
    h75_cg = read_json("registry/run_card_h75_dchb_cg_2026-10-27.json")
    h79_cthm = read_json("registry/run_card_h79_cthm_2026-10-27.json")
    ct_x3 = h79_cthm["holdout_dti"]["experiment_3_confirm_block25km"]
    ct_c56 = h79_cthm["holdout_dti"]["shipped_crustal_sgmc_56col_readout"]
    cg_x3 = h75_cg["holdout_dti"]["experiment_3_checkerboard25km_full_block_holdout"]
    cg_ci3 = cg_x3["contrasts"]["h75_cg_vs_ctrl_subsurf"]["arms"]["H75_CG_BLIND"]["ci95"]
    x1_75 = h75["holdout_dti"]["experiment_1_block25km_checkerboard"]
    x2_75 = h75["holdout_dti"]["experiment_2_standard_holdout"]
    ln75 = h75["correlation_overlap_vs_registry"]
    try:
        from h81_status import readme_block as _h81_readme
        h81_head = _h81_readme() + "\n"
    except Exception:  # pragma: no cover
        h81_head = ""
    return h81_head + f'''<!-- CURRENT-REVIEW-2026-10-27 -->
## Current decision — 2026-10-27

**Research-archive download: YES (inspection/testing only) · Competition-ready TIF: NO · OK TO SUBMIT: NO · weekly slot: NO — DO NOT SUBMIT.**

Latest verified **H79-CTHM+SGMC Crustal-Thermomechanical LOQO B2 research GeoTIFF** ([`{h79_cthm['submission_name']}`](docs/downloads/{h79_cthm['submission_name']}), content id `{h79_cthm['content_id']}`, `{h79_cthm['positive_pixels']:,}` dots, `0` NaNs across all `12,279,160` cells in `[0, 1]`; [NaN twin](docs/downloads/{h79_cthm['nan_twin_name']}); [ZIP](docs/downloads/{h79_cthm['zip_name']}); note `{h79_cthm['note']}`) is for inspection/testing only (**DO NOT SUBMIT**). Pre-registered at [`b59b129`](knowledge/39_preregistered_h79_cthm_poe_2026-10-27.md), all 2,232 standalone feature canaries passed (`<= 0.8656 <= 0.90`): on virgin 25-km block draws `116–117`, **`H79_POE` (`{ct_x3['h79_poe_pooled']:.5f}`) beat single concatenated HGB on identical 81 features by `+{ct_x3['poe_vs_single_hgb']['paired_gain']:.5f}` (95% CI `[{ct_x3['poe_vs_single_hgb']['paired_ci95'][0]:+.4f}, {ct_x3['poe_vs_single_hgb']['paired_ci95'][1]:+.4f}]`)**, and strike-aligned SGMC reactivation raised **`H79_POE_SGMC` to `{ct_x3['h79_poe_sgmc_pooled']:.5f}` (`+{ct_x3['poe_sgmc_vs_poe']['paired_gain']:.5f}`, `4/4` folds; `0.10059` on very-far `>20 px` faults)**; shipped 56-col zero-topography `H79_CRUSTAL_SGMC` scored `HOLDOUT-DTI = {ct_c56['pooled_dti']:.5f}` (`+36.2%` vs `H74_SUBSURF`), below `CTRL_H35 = {ct_x3['ctrl_h35_pooled']:.5f}`. **Clears ALL 106 sparse rasters across the 109-raster post-merge portfolio** (`<= 58.02%` max vs `h19-c.tif`, `23.54%` vs `GEMSDOE32 B2`, `44.20%` vs `H75-DCHB-CG`, `44.17%` vs `H75-EU3D-POE65`, `29.14%` vs `H78`, `20.61%` vs `H79-scaffold`), while literal `70%` flags `r13` (**82.70%** geometric minimum at 37,654 dots; 100.00% actual) and `pindrop`. [Full H79-CTHM report, 9-site table & 0.2778 PhD proof](knowledge/40_h79_cthm_poe_outcome_2026-10-27.md) · [H79-CTHM run card](registry/run_card_h79_cthm_2026-10-27.json) · [3 review passes](registry/review_passes_h79_2026-10-27.json).

Latest verified **H75-DCHB-CG Corridor-Gated Dual-Regime LOQO B2 research GeoTIFF** ([`{h75_cg['submission_name']}`](docs/downloads/{h75_cg['submission_name']}), content id `{h75_cg['content_id']}`, `{h75_cg['positive_pixels']:,}` dots; [NaN twin](docs/downloads/{h75_cg['nan_twin_name']}); [ZIP](docs/downloads/{h75_cg['zip_name']}); note `{h75_cg['note']}`) is for inspection/testing only (**DO NOT SUBMIT**). Pre-registered at [`12931bb`](knowledge/38_preregistered_h75_dchb_cg_2026-10-27.md), all 2,184 standalone feature canaries passed (`<= 0.8179 <= 0.90`): on **Exp 3 25-km Full Checkerboard `BlockHoldout`** (virgin draws `122–123`, `{cg_x3['withheld_positive_occurrences']:,}` withheld `+`), **Gate G2 PASSED** — **`H75_CG_BLIND` (`{cg_x3['per_arm']['H75_CG_BLIND']['pooled_dti']:.5f}`, 95% CI `[{cg_ci3[0]:.4f}, {cg_ci3[1]:.4f}]`) beat `CTRL_SUBSURF` (`+{cg_x3['contrasts']['h75_cg_vs_ctrl_subsurf']['paired_gain']:.5f}`, `4/4` folds) AND `CTRL_BLIND_ABCD` (`+{cg_x3['contrasts']['h75_cg_vs_ctrl_blind_abcd']['paired_gain']:.5f}`, `3/4` folds)** and beat `CTRL_H35` on `L_valid=0` gap (`{cg_x3['per_arm']['H75_CG_BLIND']['lidar_gap_dti']:.5f}` vs `{cg_x3['per_arm']['CTRL_H35']['lidar_gap_dti']:.5f}`), while pooled Slot Gate G1 vs `CTRL_H35` (`{cg_x3['contrasts']['h75_cg_vs_ctrl_h35']['paired_gain']:+.5f}`) remained negative. Cleared all `108` pre-merge sparse rasters (`68.58% <= 70%` vs `h23-a-6pct.tif`, `34.83%` vs B2), while post-merge full-footprint 116-raster audit flags literal `r13` (**82.70%** geometric minimum at 37,654 dots; 100.00% actual) and `72.34%` 3-px dot convergence vs concurrent `h75-eu3d-poe65` (surface Spearman `0.1106`). [Full H75-DCHB-CG report & 27-repo table](knowledge/40_h75_dchb_cg_outcomes_and_executive_summary_2026-10-27.md) · [H75-DCHB-CG run card](registry/run_card_h75_dchb_cg_2026-10-27.json) · [3 review passes](registry/review_passes_h75_dchb_cg_2026-10-27.json).

Concurrent verified **H75-EU3D-POE65 research GeoTIFF** ([`{h75['submission_name']}`](docs/downloads/{h75['submission_name']}), content id `{h75['content_id']}`, `{h75['positive_pixels']:,}` dots; [NaN twin](docs/downloads/{h75['nan_twin_name']}); [ZIP](docs/downloads/{h75['zip_name']}); note `{h75['note']}`) is for inspection/testing only (**DO NOT SUBMIT**). Pre-registered at [`3053f69`](knowledge/38_preregistered_h75_eu3d_poe_block25km_2026-10-27.md), all 1,520 standalone feature canaries passed (`<= 0.8038 <= 0.90`): **`H75_APRON` (`{x2_75['h75_apron_pooled']:.5f}`) beat `CTRL_H35` (`{x2_75['ctrl_h35_pooled']:.5f}`) by `+{x2_75['h75_apron_screen_gate']['paired_gain_vs_ctrl_h35']:.5f}` (`4/4` folds PASS, 95% CI `[{x2_75['h75_apron_screen_gate']['paired_ci95_vs_ctrl_h35'][0]:+.5f}, {x2_75['h75_apron_screen_gate']['paired_ci95_vs_ctrl_h35'][1]:+.5f}]`)** on standard `Holdout`, and **`PM_DEAPRON` (`{x1_75['pm_deapron_pooled']:.5f}`) beat `CTRL_H35` (`{x1_75['ctrl_h35_pooled']:.5f}`) by `+{x1_75['h73_bw_selector_gate']['overall_paired_gain_vs_h35']:.5f}`** on 25-km Checkerboard `BlockHoldout`, while shipped CatFree `H75_POE65` (`{x2_75['h75_poe65_pooled']:.5f}` std / `{x1_75['h75_poe65_pooled']:.5f}` BlockHoldout) cleared all `{ln75['registry_checked']}` rasters diagnostically (`35.77%` vs B2, `69.84% <= 70%` max sparse) but failed literal `r13` overlap (**82.70%** geometric minimum at 37,654 dots; 100.00% actual) and `CTRL_H35`. [Full H75 outcomes, 9-site table & 0.2778 PhD proof](knowledge/39_h75_outcomes_and_executive_summary_2026-10-27.md) · [H75 run card](registry/run_card_h75_2026-10-27.json) · [Preflight](evidence/lane_preflight_2026-10-27.json) · [lane hypotheses](knowledge/39_lane_hypotheses_and_preflight_2026-10-27.md) · [continuation run card](registry/run_card_2026-10-27.json).

The existing [H78 zero-outside TIFF](docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif) passes a local format audit only, but **100% of its 43,550 dots overlap the r13 halo; DO NOT SUBMIT**. Prior H78 holdout, hard-coded score estimate and submit-ready claims are retracted as unsupported. [Correction](knowledge/38_h78_mhscf_and_phd_focus_sites_analysis_2026-10-27.md) · [format audit](evidence/h78_independent_reaudit_2026-10-27.json) · [literal lane re-audit](evidence/h78_literal_lane_reaudit_2026-10-27.json). The reported portal error “Predicted values must be in range [0, 1]” is consistent with earlier NaNs inside the mirrored footprint; the exact organizer validation behavior and acceptance of zero outside are unverified.

The [H79 random-dot scaffold](docs/downloads/gems25-h79-spatial-poisson-disc-b2-20261027-66772eeec27a-zeros.tif), added independently by a parallel PR, is also **DO NOT SUBMIT**: **99.8699% overlap r13** and **416 positives are on catalogue pixels**. No geological predictor or blocked holdout was used. [Mask audit](evidence/h79_independent_reaudit_2026-10-27.json) · [lane audit](evidence/h79_literal_lane_reaudit_2026-10-27.json) · [corrected card](registry/run_card_h79_2026-10-27.json).

GEMSDOE32's **0.2778 is OWNER-REPORTED**, not organizer-confirmed. B2 is exactly D2.8 pruned of 6,436 pixels within 200 m of the catalogue; sparsity and selective pruning could explain improved local credit/false-positive balance, but hidden-label causation and future scores are unknown. A fresh nine-site audit also finds GEMSDOE28's 0.2710 Rung30 winner differs from GEMSDOE31; only its lower-scoring R1 is identical to GEMSDOE31. [Executive summary & downloads](docs/executive-summary.html) · [pixel and source audit](evidence/focus_winners_reaudit_2026-10-27.json).

Prior archives, including [H74](docs/downloads/gems25-h74-rmps-subsurf-catfree-b2-37654-20261026-3751606e1ce5-zeros.tif) and [H72-3](docs/downloads/gems25-h72-3-subsurf-pttg-mths-sapd3-0-k3p0-20261026-88bbebfe79b4-zeros.tif), remain inspection-only and are not lane-cleared; [H74 prior analysis](knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md) · [H74 run card](registry/run_card_h74_2026-10-26.json). Read the standing owner brief below every session; Maximize P(Win) and Own the Outcome do not justify submitting a failed candidate.

'''


def main() -> None:
    # Reuse the single generator so all public entry points stay in sync.
    try:
        from build_site import main as build
    except ImportError:
        from scripts.build_site import main as build
    build()


if __name__ == "__main__":
    main()
