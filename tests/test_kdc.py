"""Automated gates for the 2026-10-25 KDC deliverable: the site's "OK to download / OK to spend a slot" labels must follow from
evidence files, not from hand-written text."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SUBS = json.loads((ROOT / "registry" / "submissions.json").read_text())["files"]
# The KDC file was the featured primary in session 6; session 7 features XG1 (also negative).
# These tests are KDC-specific, so select the KDC registry entry by id, not by featured role.
PRIMARY = next(s for s in SUBS if s["id"] == "kdc-b2-complement")
CARD = json.loads((ROOT / "registry" / "run_card_kdc_2026-10-25.json").read_text())
RECEIPT = json.loads((ROOT / "docs" / "downloads" / PRIMARY["receipt"]).read_text())
GATE_MIN_GAIN, GATE_MIN_POS, GATE_WORST, R_MIN = 0.001, 3, -0.01, 0.50  # knowledge/17 §2 (frozen)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_primary_files_exist_and_hashes_match_registry():
    for s in SUBS:
        if s["role"] in ("primary", "fallback"):
            p = ROOT / s["path"]
            assert p.exists(), p
            assert sha256(p) == s["sha256"]
            assert p.stat().st_size == s["bytes"]
    assert (ROOT / "docs" / "downloads" / PRIMARY["zip"]).exists()


def test_note_short_and_names_the_file():
    assert len(PRIMARY["note"]) <= 120
    assert all(t in PRIMARY["note"] for t in ("no slot", "unscored", "not slot-approved"))
    assert PRIMARY["content_id"] in PRIMARY["note"]
    assert CARD["note"] == PRIMARY["note"] and CARD["note_chars"] == len(PRIMARY["note"])


def recompute_gate(g: dict) -> bool:
    gain = np.array(g["per_fold_gain"])
    g1 = gain.mean() > GATE_MIN_GAIN and (gain > 0).sum() >= GATE_MIN_POS and gain.min() >= GATE_WORST
    g2 = g["efficiency_R_pooled"] >= R_MIN and sum(r >= R_MIN for r in g["efficiency_R_by_fold"]) >= 3
    return bool(g1 and g2 and g["G3_ok"] and g["G4_canary"])


@pytest.mark.parametrize("path,arm", [("evidence/kdc_screen/analysis.json", "K_self"), ("evidence/kdc5_screen/analysis.json", "K_flank")])
def test_frozen_gate_recomputes_and_fails(path, arm):
    g = json.loads((ROOT / path).read_text())["gate"][arm]
    assert recompute_gate(g) == g["passed"] is False


def test_slot_label_follows_gate_evidence():
    gates_passed = [e["gate"]["passed"] for e in CARD["experiments"]]
    slot_ok = any(gates_passed)
    assert PRIMARY["ok_to_submit_slot"] is slot_ok is False
    assert PRIMARY["slot_approved"] is False
    assert PRIMARY["verdict"] == CARD["verdict"] == "negative"
    assert "DO NOT SUBMIT" in PRIMARY["status"]


def test_download_label_follows_validator_and_strict_lane():
    v = RECEIPT["validator"]["primary"]
    assert v["ok_to_upload"] and not v["hard_failures"]
    assert all(c["pass_"] for c in v["checks"].values() if c["hard"])
    lane = RECEIPT["lane"]
    # substantive registry rasters: clean (lattice excluded only in this sub-check)
    assert lane["worst_overlap"] <= lane["caps"]["overlap"]
    assert lane["worst_abs_spearman_final"] <= lane["caps"]["spearman"] and lane["worst_abs_spearman_surface"] <= lane["caps"]["spearman"]
    # strict literal policy (PR #14): the dense r13 lattice counts, so the lane fails and the file must say DO NOT SUBMIT
    strict = RECEIPT["strict_lane"]
    assert strict["lattice_overlap"] > 0.70 and strict["lane_clear"] is False
    assert PRIMARY["lane"]["lane_clear"] is False
    assert "do not submit" in PRIMARY["status"].lower() and "strict lane" in PRIMARY["summary"].lower()
    assert PRIMARY["ok_to_download"] is True and PRIMARY["ok_to_submit_slot"] is False


def test_run_card_has_protocol_fields():
    for k in ("hypothesis", "mechanism", "non_fault_process_that_could_mimic_it", "holdout_dti", "correlation_overlap_vs_registry",
              "validator_output", "submission_name", "note", "verdict", "deviation_from_preregistration"):
        assert k in CARD, k
    assert CARD["live_build"]["sha256"] == PRIMARY["sha256"]
    assert CARD["holdout_dti"]["label"] == "HOLDOUT-DTI"


def test_composition_is_base_plus_complement():
    c = RECEIPT["composition"]
    assert c["total_dots"] == c["base_h33_2_b2_dots"] + c["complement_dots"] == PRIMARY["positive_pixels"]
    assert c["base_share"] <= 0.70  # >= 30 % of dots differ from the incumbent (lane rule)
    assert c["complement_min_dist_to_base_px"] > 3 and c["complement_min_dist_to_catalogue_px"] > 2


def test_primary_revalidates_independently():
    tmpl = ROOT / "data" / "sample_submission.tif"
    if not tmpl.exists():
        pytest.skip("competition template not restored (run scripts/restore_data.py)")
    from gems25.submission import check_file

    r = check_file(ROOT / PRIMARY["path"], tmpl)
    assert r["ok_to_upload"], r["hard_failures"]
    assert r["positive_pixels"] == PRIMARY["positive_pixels"]
