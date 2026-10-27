"""Audit the preserved H78 raster as format-valid research data, not an eligible submission."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
TIF_NAME = "gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif"
ZIP_NAME = "gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.zip"


def test_h78_files_exist():
    assert (ROOT / "docs" / "downloads" / TIF_NAME).exists()
    assert (ROOT / "docs" / "downloads" / ZIP_NAME).exists()
    assert (ROOT / "registry" / "run_card_h78_2026-10-27.json").exists()


def test_h78_format_validation():
    p = ROOT / "docs" / "downloads" / TIF_NAME
    with rasterio.open(p) as ds:
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert ds.crs.to_epsg() == 32611
        assert ds.shape == (3730, 3292)
        arr = ds.read(1)
        # CRITICAL check for DrivenData portal error "Predicted values must be in range [0, 1]"
        assert np.all(np.isfinite(arr)), "Raster must have 0 NaNs or Infs everywhere"
        assert ((arr >= 0.0) & (arr <= 1.0)).all(), "All values must strictly lie in [0, 1]"
        assert np.sum(arr > 0) == 43550, "Expected exactly 43,550 emitted dots"


def test_h78_run_card_fails_closed_on_lane_and_score_evidence():
    card = json.loads((ROOT / "registry" / "run_card_h78_2026-10-27.json").read_text())
    assert card["estimated_competition_score"] is None
    assert card["holdout_dti"] is None
    assert card["submission"]["ok_to_submit"] is False
    assert card["submission"]["ok_to_download"] is True
    assert "DO NOT SUBMIT" in card["submission"]["note"]
    assert len(card["submission"]["note"]) <= 140
    lane = card["correlation_overlap_vs_registry"]
    assert lane["r13_dots_within_3px"] == 1.0
    assert lane["strict_literal_flags"]


def test_h78_builder_is_retired_before_data_loading():
    import pytest

    from scripts.build_h78_submission import main

    with pytest.raises(SystemExit, match="strict lane duplicate"):
        main()


def test_h78_site_and_readme_make_no_submit_status_obvious():
    for page in (ROOT / "index.html", ROOT / "docs" / "index.html", ROOT / "docs" / "executive-summary.html"):
        text = page.read_text()
        above_fold = text[:16000]
        assert "STRICT LANE DUPLICATE" in above_fold
        assert "OK TO SUBMIT: NO" in above_fold
        assert "Estimated Score: <b>0.2785" not in above_fold
        assert "OK TO SUBMIT: YES" not in above_fold
        assert "VALIDATED COMPETITION READY" not in above_fold
    readme = (ROOT / "README.md").read_text()
    assert "OK TO SUBMIT: NO" in readme[:4000]
    assert "Calibrated Competition DTI Estimate: **0.2785**" not in readme[:4000]
    assert "hard-coded" in readme[:4000]


def test_h78_receipts_separate_format_validity_from_submission_eligibility():
    receipt = json.loads(
        (ROOT / "docs" / "downloads" / f"checks-{TIF_NAME[:-4]}.json").read_text()
    )
    lane = json.loads(
        (ROOT / "docs" / "downloads" / f"lane-{TIF_NAME[:-4]}.json").read_text()
    )
    assert receipt["ok_to_download"] is True
    assert receipt["ok_to_submit"] is False
    assert receipt["estimated_competition_score"] is None
    assert "FORMAT VALIDATED ONLY" in receipt["validation_status"]
    assert lane["strict_literal_verdict"] == "DUPLICATE / STOP / DO NOT SUBMIT"
    assert lane["strict_literal_flags"] == ["13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"]
