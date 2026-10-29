"""Regression: a research download must never be advertised as submit-ready."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_negative_card_and_exact_artifact():
    c = json.loads((ROOT / "registry/run_card_decoupling_2026-10-29.json").read_text())
    tif = ROOT / c["file"]
    assert tif.exists()
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == c["sha256"]
    assert c["holdout_dti"]["valid_for_selection"] is False
    assert c["registry"]["global_registry_clear"] is False
    assert c["validator"]["portal_all_cells_finite_in_0_1"] is True
    assert c["validator"]["crs_shape_transform_match"] is True
    assert c["holdout_dti"]["withheld_positive_occurrences"] == 23923
    assert c["registry"]["max_dot_overlap_3px"] <= 0.70
    assert c["registry"]["surface_max_abs_rho"] <= 0.90
    assert len(c["note"]) <= 140 and "DO NOT SUBMIT" in c["note"]


def test_every_entry_page_is_unambiguously_research_only():
    name = "gems25-mag-rad-decoupling-20261029-8e2e136eddc8-zero.tif"
    for rel in ("index.html", "docs/index.html", "docs/executive-summary.html",
                "docs/nine-site-brief.html", "docs/submission-guide.html"):
        html = (ROOT / rel).read_text()
        assert html.count('<!-- DECPL-STATUS-START -->') == 1
        assert name in html and 'SUBMIT: NO — DO NOT SUBMIT' in html
        assert 'Estimated organizer score: UNKNOWN' in html
