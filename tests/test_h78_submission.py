"""Verify format validity, 0-NaN safety, and post-PR#60 remediation of the archived H78 artifact."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

ROOT = Path(__file__).resolve().parents[1]
TIF_NAME = "gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif"
ZIP_NAME = "gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.zip"


def test_h78_files_exist() -> None:
    assert (ROOT / "docs" / "downloads" / TIF_NAME).exists()
    assert (ROOT / "docs" / "downloads" / ZIP_NAME).exists()
    assert (ROOT / "registry" / "run_card_h78_2026-10-27.json").exists()
    assert (ROOT / "evidence" / "h78_measured_holdout_audit_2026-10-27.json").exists()


def test_h78_format_validation() -> None:
    p = ROOT / "docs" / "downloads" / TIF_NAME
    with rasterio.open(p) as ds:
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert ds.crs.to_epsg() == 32611
        assert ds.shape == (3730, 3292)
        arr = ds.read(1)
        assert np.all(np.isfinite(arr)), "Raster must have 0 NaNs or Infs everywhere"
        assert ((arr >= 0.0) & (arr <= 1.0)).all(), "All values must strictly lie in [0, 1]"
        assert np.sum(arr > 0) == 43550, "Expected exactly 43,550 emitted dots"


def test_h78_remediated_run_card_is_honest() -> None:
    card = json.loads((ROOT / "registry" / "run_card_h78_2026-10-27.json").read_text())
    audit = json.loads((ROOT / "evidence" / "h78_measured_holdout_audit_2026-10-27.json").read_text())
    assert card["estimated_competition_score"] is None
    assert card["organizer_confirmed_score"] is None
    assert card["verdict"] == "negative"
    assert card["slot_approved"] is False
    assert card["submission"]["ok_to_download"] is True
    assert card["submission"]["ok_to_submit"] is False
    assert len(card["submission"]["note"]) <= 120
    assert "DO NOT SUBMIT" in card["submission"]["note"]
    assert card["holdout_dti"]["pooled_dti"] == pytest.approx(audit["pooled_dti"])
    assert card["correlation_overlap_vs_registry"]["total_registry_checked"] >= 100
    assert card["correlation_overlap_vs_registry"]["lane_clear"] is False
