"""Locks the 2026-10-26 training-objective session: run card <-> evidence <-> registry <-> GeoTIFFs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "registry" / "run_card_objective_2026-10-26.json").read_text())
SUBS = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
# Merge note: featured rotated to h72-3-subsurf; obj-bin-greedy remains locked as alternate.
PRIMARY = next(s for s in SUBS if s["id"] == "obj-bin-greedy")
NAN_TWIN = next(s for s in SUBS if s["id"] == "obj-bin-greedy-nan")
EXPS = (
    ("experiment_1_tent", "tent_screen_2026-10-26", "TENT-greedy_vs_BIN-greedy"),
    ("experiment_2_hardneg", "hardneg_screen_2026-10-26", "HNEG-greedy_vs_BIN-greedy"),
    ("experiment_3_ign3", "ign3_screen_2026-10-26", "IGN3-greedy_vs_BIN-greedy"),
)


def test_objective_primary_matches_run_card() -> None:
    assert PRIMARY["id"] == "obj-bin-greedy"
    assert PRIMARY["sha256"] == CARD["tif"]["sha256"] == "160dbdc0c2abc25bd40a3f38a36c2a69f8a02503337dea7ab706f6d77a08934d"
    assert NAN_TWIN["sha256"] == CARD["tif"]["nan_twin_sha256"]
    assert PRIMARY["content_id"] == NAN_TWIN["content_id"] == CARD["tif"]["content_id"] == "3646faf70507"
    assert PRIMARY["positive_pixels"] == NAN_TWIN["positive_pixels"] == 53522
    assert PRIMARY["note"] == CARD["tif"]["note"]
    assert len(PRIMARY["note"]) <= 140 and "DO NOT SUBMIT" in PRIMARY["note"]
    assert CARD["verdict"] == PRIMARY["verdict"] == "negative"
    assert PRIMARY["ok_to_download"] is True
    assert PRIMARY["ok_to_submit_slot"] is False and PRIMARY["slot_approved"] is False
    assert "DO NOT SUBMIT" in PRIMARY["status"]


def test_all_three_experiments_failed_and_card_matches_analyzers() -> None:
    for card_key, ev_dir, contrast in EXPS:
        res = json.loads((ROOT / "evidence" / ev_dir / "results.json").read_text())
        exp = CARD["experiments"][card_key]
        assert res["gate"]["passed"] is False and exp["gate"]["passed"] is False
        assert exp["draws"] == res["draws"] and exp["withheld_positives_total"] == res["withheld_positives_total"]
        assert abs(exp["paired"]["mean_gain"] - res["contrasts"][contrast]["standard"]["mean"]) < 1e-12
        assert abs(exp["bin_greedy"]["pooled_dti"] - res["arms"]["BIN-greedy"]["pooled_dti"]) < 1e-12
        assert res["leakage_canary"]["max_effective_auc"] <= 0.90
        cells = [json.loads(line) for line in (ROOT / "evidence" / ev_dir / "cells.jsonl").read_text().splitlines()]
        assert exp["withheld_positives_total"] == sum(
            c["n_truth"] for c in cells if c["arm"] == "BIN" and c["emission"] == "greedy"
        )
        assert exp["evaluator"].startswith("gems25.metric.dti_binary")


def test_lane_unique_vs_scored_but_fails_own_lineage() -> None:
    lane = json.loads((ROOT / "evidence" / "objective_lane_extended.json").read_text())
    ext, own = lane["external_sparse"], lane["own_lineage"]
    assert ext["lane_pass"] is True and ext["worst_cand_dots_within_3px"] <= 0.70
    assert ext["worst_abs_spearman_surface"] <= 0.90 and ext["worst_abs_spearman_final"] <= 0.90
    b2 = next(r for r in lane["rows"] if r["file"] == "g32_h33-2-b2_0.2778.tif")
    assert b2["cand_dots_within_3px"] < 0.40
    # The strict lane must stay failed: same-lineage reuse is exactly why this is not promotable.
    assert own["lane_pass"] is False and own["worst_cand_dots_within_3px"] > 0.70
    assert lane["lattice"][0]["cand_dots_within_3px"] > 0.70


def test_candidate_revalidates_strict_range() -> None:
    import pytest

    from gems25.paths import data_dir
    from gems25.submission import check_file

    tmpl = data_dir() / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("competition template not restored")
    res = check_file(ROOT / PRIMARY["path"], tmpl)
    assert res["ok_to_upload"] is True, res["hard_failures"]
    assert res["positive_pixels"] == 53522 and res["sha256"] == PRIMARY["sha256"]
    audit = json.loads((ROOT / "evidence" / "objective_independent_audit_zeros.json").read_text())
    assert audit["all_hard_checks_pass"] is True
    assert audit["checks"]["strict_whole_array_0_le_x_le_1"] is True
    assert audit["checks"]["no_emission_on_catalogue"] is True


def test_site_and_readme_make_submit_status_obvious() -> None:
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html", "docs/current-review.html"):
        html = (ROOT / rel).read_text()
        assert PRIMARY["file"] in html and "3646faf70507" in html
        assert "OK to download: YES" in html or "OK TO DOWNLOAD: YES" in html
        assert "DO NOT SUBMIT" in html
    readme = (ROOT / "README.md").read_text()
    assert PRIMARY["file"] in readme
    assert "OK to download (local testing): YES · OK to spend a weekly slot: NO — DO NOT SUBMIT" in readme
    assert "knowledge/31_objective_outcomes_and_executive_summary_2026-10-26.md" in readme
    assert (ROOT / "docs" / "downloads" / PRIMARY["zip"]).exists()
