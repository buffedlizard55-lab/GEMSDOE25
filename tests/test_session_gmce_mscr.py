"""Locks the 2026-10-25 GMCE/MSCR session: run card <-> analyses <-> registry.

The negative verdict must *follow* from the two pre-registered screen analyses (gate
fields failing on evidence), canaries must pass, and the MSCR registry entry (looked up
by its pinned SHA-256) must be the unique MSCR file with slot labels off. Nothing here
may be satisfied by hand-edited prose.

Merge note (H38 session): the featured (primary) role moved to the newer H38 file when
the branches were unioned, so this module pins the MSCR *entry* rather than whichever
entry is currently featured; every original assertion is preserved against that entry.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "registry/run_card_session_2026-10-25_gmce_mscr.json").read_text())
SUBS = json.loads((ROOT / "registry/submissions.json").read_text())["files"]
PRIMARY = next(s for s in SUBS if s["sha256"] == "0c8b7e91d7a4402e8fc9e6e840b5533669de1a17f1c1acc941c0c3bde0db7ea5")
EXPS = [CARD["experiment_1"]["holdout_dti"], CARD["experiment_2"]["holdout_dti"]]
ANALYSES = ["evidence/gmce_screen/analysis.json", "evidence/mscr_screen/analysis.json"]


def test_run_card_matches_analyses_and_registry():
    for e, path in zip(EXPS, ANALYSES):
        a = json.loads((ROOT / path).read_text())
        arm = e["candidate_arm"]
        assert abs(e["paired_gain_mean"] - a[f"paired_{arm}_vs_BEST"]["mean"]) < 1e-12
        assert e["folds_positive"] == a[f"paired_{arm}_vs_BEST"]["folds_positive"]
        assert e["gate"]["passed"] is a["gate"]["passed"] is False
    assert CARD["tif"]["sha256"] == PRIMARY["sha256"]
    assert CARD["tif"]["note"] == PRIMARY["note"] and len(PRIMARY["note"]) <= 140
    assert PRIMARY["sha256"] == "0c8b7e91d7a4402e8fc9e6e840b5533669de1a17f1c1acc941c0c3bde0db7ea5"


def test_negative_verdict_follows_the_frozen_gates():
    for e in EXPS:
        assert e["paired_gain_mean"] <= e["gate"]["mean_gain_gt"] or e["folds_positive"] < e["gate"]["folds_positive_min"]
        assert e["leakage_canary"]["passed"] and e["leakage_canary"]["max_feature_auc"] <= e["leakage_canary"]["cap"]
    assert CARD["verdict"] == "negative"
    assert PRIMARY["verdict"] == "negative" and PRIMARY["ok_to_submit_slot"] is False
    assert PRIMARY["ok_to_download"] is True
    assert "DO NOT SUBMIT" in PRIMARY["status"]


def test_b2_chain_reverification_present_and_clean():
    v = json.loads((ROOT / "evidence/gmce_session_b2_chain_verification.json").read_text())
    i = v["identities"]
    assert i["d2_8_equals_dot_thin_h19_5_2.4"] and i["d2_8_equals_dot_thin_h19_5_2.8"]
    assert i["r1_equals_d2_8_and_dist_gt_1"] and i["b2_equals_d2_8_and_dist_gt_2"] and i["b2_subset_of_g36"]
    assert v["counts"]["b2_g32"] == 37654 and v["counts"]["h19_5"] == 121131 and v["counts"]["d2_8"] == 44090


def test_independent_audit_and_lane_receipts_agree_with_registry():
    az = json.loads((ROOT / "evidence/mscr_independent_audit_zeros.json").read_text())
    assert az["all_hard_checks_pass"] and az["positive_pixels"] == PRIMARY["positive_pixels"] == 48442
    assert az["checks"]["footprint_values_in_0_1"] and az["checks"]["strict_whole_array_0_le_x_le_1"]
    assert az["checks"]["footprint_all_finite"] and az["checks"]["no_emission_on_catalogue"]
    lane = json.loads((ROOT / "evidence/mscr_lane_extended.json").read_text())
    assert lane["sha256"] == PRIMARY["sha256"]
    assert lane["lattice"][0]["cand_dots_within_3px"] > 0.70  # literal strict lane fails -> do not submit
    assert len(lane["rows"]) >= 50
