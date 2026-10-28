"""Locks the 2026-10-28 H81 session: run card <-> evidence <-> registry <-> brief must stay honest.

The session's outcome is NEGATIVE (lane duplicate), so these tests assert that the repository keeps saying so:
no file is registered, no download is offered for the withheld candidate, and every published number is
recomputable from the evidence JSON.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def J(rel):
    return json.loads((ROOT / rel).read_text())


def test_run_card_matches_evidence_and_never_authorizes_a_slot():
    card = J("registry/run_card_h81_2026-10-28.json")
    assert card == J("docs/data/run_card_h81_2026-10-28.json")
    build = J("evidence/h81_candidate_build.json")
    gates = J("evidence/h81_gates.json")
    assert card["schema"].startswith("run_card/v1")
    assert card["content_id"] == build["content_id"]
    assert card["estimated_competition_score"] is None
    assert card["submission"]["slot_approved"] is False
    assert card["submission"]["ok_to_submit_slot"] is False
    assert card["submission"]["verdict"] == "negative"
    assert len(card["submission"]["note"]) <= 120
    assert "not slot-approved" in card["submission"]["note"]
    assert gates["G3_packaging_gate"]["passed"] is False
    assert gates["G3_packaging_gate"]["published"] is False
    if not build.get("published"):
        assert card["submission"]["ok_to_download"] is False
        assert card["submission"]["name"] is None
        assert "NOTHING WAS PUBLISHED" in card["submission"]["status"]
        assert build["lane"]["non_space_filling"]["pass_"] is False
        assert build["duplicate_of"]
        assert "Nothing published" in build["note"] or "No submission file was published" in build["note"]


def test_holdout_numbers_are_recomputed_from_the_summaries():
    card = J("registry/run_card_h81_2026-10-28.json")
    for key, rel in (("experiment_1_standard_holdout", "evidence/h81_exp1/summary.json"),
                     ("experiment_3_checkerboard25km_block_holdout", "evidence/h81_exp3/summary.json")):
        if not (ROOT / rel).exists():
            continue
        s = J(rel)
        block = card["holdout_dti"][key]
        assert block["draws"] == s["draws"]
        assert block["cells_per_arm"] == s["n_cells_per_arm"]
        for arm, st in s["per_arm"].items():
            assert block["per_arm"][arm]["pooled_dti"] == round(st["pooled_dti"], 6)
        for name, c in s["contrasts"].items():
            assert block["contrasts"][name]["paired_gain"] == round(c["paired_gain"], 6)
            assert block["contrasts"][name]["folds_positive"] == sum(g > 0 for g in c["fold_gains"])


def test_no_unpublished_candidate_is_registered_or_shipped():
    subs = J("registry/submissions.json")["files"]
    assert not any(f.get("id", "").startswith("h81") for f in subs), "an unpublished candidate must not be registered"
    assert not list((ROOT / "docs" / "downloads").glob("*h81*")), "no H81 bytes may appear in docs/downloads"


def test_brief_retracts_unsupported_score_bands_and_does_not_promote_a_download():
    page = (ROOT / "docs" / "h81-executive-brief.html").read_text()
    assert "H81 NEGATIVE" in page
    assert "NEW-SUBMISSION SCORE: NOT ESTIMATED" in page
    assert "0.2250–0.2250" not in page
    assert "0.2708–0.2778" not in page
    assert "There is no approved TIFF to download" in page
    assert "OK TO SUBMIT: YES" not in page
    assert "OWNER-REPORTED" in page
    assert "h81_exp3/summary.json" in page
    for href in re.findall(r'(?:href|src)="([^"#?]+)"', page):
        parts = urlsplit(href)
        if parts.scheme or parts.netloc:
            continue
        assert (ROOT / "docs" / parts.path).resolve().exists(), href


def test_score_estimate_labels_the_model_failure_it_found():
    est = J("evidence/h81_score_estimate.json")
    band = est["empirical_band"]
    assert band["evidence_class"].startswith("EMPIRICAL ESTIMATE")
    assert band["n_matched"] >= 1
    assert band["min"] <= band["point_estimate"] <= band["max"]
    assert "NOT a score" in band["evidence_class"]
    warn = est["model_estimate_scope_warning"]
    assert "0.2778" in warn and "0.03" in warn
    assert est["model_estimate"]["model_estimated_dti"] < band["min"]
    opt = J("evidence/h81_score_estimate_optimum_geometry.json")
    assert opt["empirical_band"]["n_matched"] >= 3
    assert opt["empirical_band"]["min"] >= 0.26
    gated = J("evidence/h81_score_estimate_gated.json")
    assert gated["empirical_band"]["n_matched"] == 0


def test_lane_audit_reports_both_classes_without_waiving_the_literal_rule():
    lane = J("evidence/h81_final_dot_lane.json")
    assert lane["non_space_filling"]["pass_"] is False
    assert lane["non_space_filling"]["worst_overlap"] > 0.70
    assert lane["space_filling"]["n"] >= 1
    assert "cannot be avoided by any dense emission" in lane["space_filling"]["pigeonhole_note"]
    surface = J("evidence/h81_surface_lane.json")
    assert surface["comparable"]["pass_"] is True
    assert surface["comparable"]["max_abs_spearman"] <= 0.90
    assert surface["incomparable"], "the off-grid reference must be named, not dropped"
    assert surface["incomparable"][0]["sha256"]
