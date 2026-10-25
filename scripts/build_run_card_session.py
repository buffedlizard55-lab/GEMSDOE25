#!/usr/bin/env python3
"""Assemble the session RUN CARD (protocol item 5) from the tracked evidence JSONs.

Reads the two screening analyses, the B2-chain re-verification, the build receipt, both lane
receipts and the independent audits; writes registry/run_card_session_2026-10-25_gmce_mscr.json.
Refuses to run if any input is missing, so the card cannot silently lose a number.

    .venv/bin/python scripts/build_run_card_session.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(p: str) -> dict:
    path = ROOT / p
    assert path.exists(), f"missing run-card input: {p}"
    return json.loads(path.read_text())


def holdout(exp: str, ana: dict) -> dict:
    cand = next(a for a in ana["arms"] if a != "BEST")
    return dict(
        experiment=exp,
        label="HOLDOUT-DTI",
        evaluator=ana["evaluator"],
        draws=ana["draws"],
        candidate_arm=cand,
        candidate_pooled_dti=ana["arms"][cand]["pooled_dti"],
        candidate_pooled_ci95=ana["arms"][cand]["pooled_ci95"],
        control_arm="BEST (H35-B config recomputed in the same run)",
        control_pooled_dti=ana["arms"]["BEST"]["pooled_dti"],
        control_pooled_ci95=ana["arms"]["BEST"]["pooled_ci95"],
        paired_gain_mean=ana[[k for k in ana if k.startswith("paired_")][0]]["mean"],
        paired_gain_ci95=ana[[k for k in ana if k.startswith("paired_")][0]]["ci95"],
        folds_positive=ana[[k for k in ana if k.startswith("paired_")][0]]["folds_positive"],
        worst_fold=ana[[k for k in ana if k.startswith("paired_")][0]]["worst_fold"],
        withheld_positives=ana["withheld_positives"],
        leakage_canary=ana["leakage_canary"],
        gate=ana["gate"], verdict=ana["verdict"], formatted=ana["formatted"])


def main() -> None:
    gmce = J("evidence/gmce_screen/analysis.json")
    mscr = J("evidence/mscr_screen/analysis.json")
    b2 = J("evidence/gmce_session_b2_chain_verification.json")
    checks_files = sorted((ROOT / "docs/downloads").glob("checks-gems25-mscr-*.json"))
    assert checks_files, "MSCR build receipt missing"
    build = json.loads(checks_files[-1].read_text())
    lane_strict = J(f"docs/downloads/lane-{build['files']['zeros']['file'].replace('.tif', '.json')}")
    lane_ext = J("evidence/mscr_lane_extended.json")
    aud_z = J("evidence/mscr_independent_audit_zeros.json")
    aud_n = J("evidence/mscr_independent_audit_nan.json")
    focus_rows = [r for r in lane_ext["rows"] if r["group"] == "registry_top" and "cand_dots_within_3px" in r]
    z = build["files"]["zeros"]
    card = dict(
        schema="run_card/v1 (PARALLEL-RUN PROTOCOL item 5)",
        session="2026-10-25 GMCE-1 + MSCR-1 (arena/58bd9d81-gemsdoe25)",
        experiments_used="2 of 3 budget (GMCE screen; MSCR screen). No confirmation: frozen gates failed at screen stage.",
        question=dict(
            why_0_2778=dict(
                summary=("Emission economics on one strong surface: h19-5 (121,131 px, OWNER 0.1922) -> dot_thin 1.5 "
                         "(60,069 px, OWNER 0.2477) -> re-thin 2.4/2.8 (44,090 px, OWNER 0.2600) -> delete d<=1px "
                         "(40,199 px, OWNER 0.2708) -> delete d<=2px = B2 (37,654 px, OWNER 0.2778). Deleted collar dots "
                         "carried ~0.001-0.005 implied credit/dot vs break-even tau ~0.055-0.059."),
                evidence="evidence/gmce_session_b2_chain_verification.json (recomputed this session; all identities true)",
                identities=b2["identities"], thinning_note=b2["thinning_note"],
                inversion=b2["inversion"], targets=b2["targets"],
                caveats=("Scores are OWNER-reported, not organizer receipts; inversion assumes N_hidden=12,691 px and "
                         "TP_w+FP_w ~= emitted mass; B2's blanket 200 m deletion conflicts with the READ staff wording on "
                         "corrections within 300 m; brief leader claims 0.3195 vs 0.4413 conflict (IR-25-LEADERBOARD-CONFLICT).")),
            can_we_beat_it=("Not demonstrated. Two new detector blocks (GMCE-1, MSCR-1) added nothing over the same-run "
                            "holdout best on fresh draws (paired -0.0012 / -0.0004). No live score above 0.2778 is claimed; "
                            "any such number would be a projection.")),
        experiment_1=dict(
            hypothesis=("GMCE-1: a basement-offsetting fault steps both potential fields across one line, so gravity and "
                        "RTP gradient vectors are (anti)parallel on a co-located edge even under cover."),
            mechanism=("3 columns from iso_grav_anom + rtp: min(pct log grad mags)*|cos dtheta|, signed twin, ridge of the "
                       "first; added to the frozen H35-B HGB detector, emission unchanged."),
            mimicking_non_fault_process=("Lithologic contacts (intrusion margins, stratigraphic pinch-outs) with joint "
                                         "density+magnetization contrast; shared survey-levelling lineaments."),
            preregistration="knowledge/21_preregistered_gmce_2026-10-25.md (commit 8198a31)",
            holdout_dti=holdout("GMCE screen", gmce)),
        experiment_2=dict(
            hypothesis=("MSCR-1: fault-controlled range fronts/graben margins are topographic lines at 400 m wavelength "
                        "and persist from 100 m to 400 m scales, unlike single-scale drainage noise."),
            mechanism=("3 columns from det_elev: ridge(z,4.0), sqrt(pct(ridge(z,1))*pct(ridge(z,4))), ridge(-z,4.0); "
                       "added to the same frozen detector/emission."),
            mimicking_non_fault_process="Lithologic strike ridges/valleys (hogbacks, soft-unit strike valleys); fluvial terrace edges.",
            preregistration="knowledge/22_preregistered_mscr_exp2_2026-10-25.md (commit b9c5a5e)",
            holdout_dti=holdout("MSCR screen", mscr)),
        tif=dict(
            primary_file=z["file"], sha256=z["sha256"], content_id=z["content_id"],
            positive_pixels=z["positive_pixels"], bytes=z["bytes"], outside="zeros (no NaN anywhere)",
            nan_twin=build["files"]["nan"], zip=build["zip"], note=build["note"], note_chars=build["note_chars"],
            build=build["build"],
            validator_independent_zeros=aud_z, validator_independent_nan=aud_n,
            writer_checks_hard_failures=build["files"]["zeros"]["hard_failures"]),
        lane=dict(
            thresholds=dict(abs_spearman_max=0.90, dots_within_3px_max=0.70),
            strict_receipt=dict(file=f"docs/downloads/lane-{z['file'].replace('.tif', '.json')}",
                                verdict=lane_strict["verdict"], flagged=lane_strict["flagged"],
                                registry_checked=lane_strict["registry_checked"],
                                sha_in_artifact_ledger=lane_strict["sha_in_artifact_ledger"]),
            extended=dict(
                focus_site_winners_registry_top=dict(
                    n=len(focus_rows),
                    worst_cand_dots_within_3px=max(r["cand_dots_within_3px"] for r in focus_rows),
                    worst_abs_spearman_surface=max(abs(r["spearman_surface"]) for r in focus_rows),
                    b2_overlap=next(r["cand_dots_within_3px"] for r in focus_rows if r["file"].startswith("g32_"))),
                external_sparse=lane_ext["external_sparse"], lattice=lane_ext["lattice"],
                own_lineage=lane_ext["own_lineage"],
                reading=("Surface (pre-placement) and final-dot Spearman <= 0.90 vs every compared raster. Dot overlap "
                         "<= 0.70 vs all sparse focus-site winners (worst 0.38) but > 0.70 vs dense rasters (r13 lattice "
                         "1.00, pindrop/h23/r7 103k-336k dots, reverse overlap 0.19-0.44, surface rho <= 0.18) and vs this "
                         "repo's own H31/H35 HGB lineage (0.76-0.92). Under the repo's merged literal strict lane rule "
                         "(no density exception) this is a DUPLICATE LANE / STOP."))),
        verdict="negative",
        ok_to_download_testing=True,
        ok_to_submit_slot=False,
        slot_statement="DO NOT SUBMIT: both pre-registered holdout gates FAILED and the literal strict lane gate stops the file.",
        next_steps=[
            "Do not spend a weekly slot on GMCE-1/MSCR-1 transforms; the incumbent band stack appears saturated for incremental static columns on this proxy (two fresh-draw negatives).",
            "Blocked-data route (rank 5, knowledge/21): GDR 1391 paleo-geothermal zip + USGS heat-flow DOI 10.5066/P9BZPVUC need a networked runner; verify bytes/coverage/licence before proposing.",
            "Junction field (H30-2) remains registered-only; its proxy/live sign conflict must be resolved by design (e.g. hug-gated, catalogue-distance-stratified scoring) before fitting.",
            "Owner decisions still open: lattice-density lane policy (IR-25-LANE-DENSITY), leaderboard conflict 0.3195 vs 0.4413, deadline convention, GeoDAWN licence line."],
        limitations=[
            "No DrivenData access (AGENTS rule 3): template/labels/scores are hash-pinned owner mirrors, not organizer-authenticated.",
            "Holdout is a catalogue-gap proxy (proxy-live Spearman +0.33 n.s. n=24, GEMSDOE24); HOLDOUT-DTI is not a competition score.",
            "Sandbox egress is github/pypi/npm only: ScienceBase/GDR/3DEP raw downloads are impossible here.",
            "No GPU use was needed; HGB CPU fits only. data/work caches rebuilt this session are bit-identical to evidence/work_cache_hashes.json pins."],
    )
    assert len(card["tif"]["note"]) <= 140
    out = ROOT / "registry/run_card_session_2026-10-25_gmce_mscr.json"
    out.write_text(json.dumps(card, indent=1) + "\n")
    print(f"wrote {out.relative_to(ROOT)}; verdict {card['verdict']}; note {len(card['tif']['note'])} chars")


if __name__ == "__main__":
    main()
