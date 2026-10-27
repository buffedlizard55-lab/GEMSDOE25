"""A concurrent random scaffold fails the same literal lane and catalogue gates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "gems25-h79-spatial-poisson-disc-b2-20261027-66772eeec27a-zeros.tif"
SHA = "e98b9a35609db124f5838cff415a1b0bdf462d65a746161c0bee706add3983d8"


def load(path):
    return json.loads((ROOT / path).read_text())


def test_exact_file_and_negative_automated_receipts():
    assert hashlib.sha256((ROOT / "docs/downloads" / NAME).read_bytes()).hexdigest() == SHA
    mask = load("evidence/h79_independent_reaudit_2026-10-27.json")
    lane = load("evidence/h79_literal_lane_reaudit_2026-10-27.json")
    assert mask["sha256"] == lane["sha256"] == SHA
    assert mask["catalogue_positive_pixels"] == 416
    assert not mask["checks"]["no_emission_on_catalogue"] and not mask["all_hard_checks_pass"]
    assert mask["checks"]["footprint_all_finite"] and mask["checks"]["footprint_values_in_0_1"]
    assert mask["zip"]["contains_exactly_candidate_bytes"]
    inventory = load("docs/data/download_audit.json")
    row = next(row for row in inventory["files"] if row["file"] == NAME)
    assert row["recorded_catalogue_positive_pixels"] == 416 and "DUPLICATE" in row["novelty"]
    assert lane["rows"][0]["dots_within_3px"] > .99
    assert "DUPLICATE" in lane["verdict"] and not lane["registry_complete"]
    assert lane["rank_footprint_pixels"] == 5_167_373


def test_h79_cannot_be_promoted_or_rebuilt(capsys):
    from scripts import build_h79_submission

    card = load("registry/run_card_h79_2026-10-27.json")
    assert card["holdout_dti"] is None and card["estimated_competition_score"] is None
    assert card["submission"]["ok_to_submit"] is False
    assert "DO NOT SUBMIT" in card["submission"]["note"] and len(card["submission"]["note"]) <= 140
    assert card["validator_output"]["catalogue_positive_pixels"] == 416
    assert build_h79_submission.main() == 2
    assert "retired" in capsys.readouterr().err
    pins = load("registry/lane_reference_pins.json")["rasters"]
    assert any(row["sha256"] == SHA and row["path"].endswith(NAME) for row in pins)
