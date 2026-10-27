"""H78 is a local-format-valid historical artifact, not an eligible submission."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

from scripts.build_h78_submission import main as retired_h78_main

ROOT = Path(__file__).resolve().parents[1]
TIF_NAME = "gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif"
ZIP_NAME = "gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.zip"


def test_h78_files_exist_as_archives():
    assert (ROOT / "docs/downloads" / TIF_NAME).exists()
    assert (ROOT / "docs/downloads" / ZIP_NAME).exists()
    assert (ROOT / "registry/run_card_h78_2026-10-27.json").exists()


def test_h78_format_validation_does_not_imply_approval():
    with rasterio.open(ROOT / "docs/downloads" / TIF_NAME) as ds:
        assert ds.count == 1 and ds.dtypes[0] == "float32"
        assert ds.crs.to_epsg() == 32611 and ds.shape == (3730, 3292)
        arr = ds.read(1)
        assert np.isfinite(arr).all()
        assert ((arr >= 0.0) & (arr <= 1.0)).all()
        assert (arr > 0).sum() == 43550
    card = json.loads((ROOT / "registry/run_card_h78_2026-10-27.json").read_text())
    assert card["validator_output"]["format_only"] is True
    assert card["submission"]["ok_to_submit"] is False


def test_h78_run_card_retracts_unsupported_scores_and_records_literal_failure():
    card = json.loads((ROOT / "registry/run_card_h78_2026-10-27.json").read_text())
    lane = json.loads((ROOT / "evidence/h78_literal_lane_reaudit_2026-10-27.json").read_text())
    assert card["estimated_competition_score"] is None
    assert card["holdout_dti"]["pooled_dti"] is None and card["holdout_dti"]["ci95"] is None
    assert card["submission"]["ok_to_submit"] is False
    assert len(card["submission"]["note"]) <= 140
    assert lane["lane_clear"] is False and lane["rows"][0]["dots_within_3px"] == 1.0
    assert lane["rank_footprint_pixels"] == 5_167_373
    assert card["correlation_overlap_vs_registry"]["spearman_full_footprint_vs_lattice"] == lane["rows"][0]["spearman"]


def test_h78_publisher_cannot_recreate_or_promote_a_failed_candidate(capsys):
    assert retired_h78_main() == 2
    assert "DO NOT SUBMIT" in capsys.readouterr().err
