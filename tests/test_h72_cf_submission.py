"""H72 result / artifact / publication consistency: a content-new file must stay DO NOT SUBMIT."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
FILE = "gems25-h72-mbsp-mtg-catfree-b2-37654-20261026-1d7c1e9ea55f-zeros.tif"


def J(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def test_h72_primary_bytes_format_and_registry_status():
    card = J("registry/run_card_h72_cf_2026-10-26.json")
    subs = J("registry/submissions.json")["files"]
    primary = next(x for x in subs if x["role"] == "primary")
    p = ROOT / "docs" / "downloads" / FILE

    assert primary["file"] == FILE
    assert primary["content_id"] == card["raster"]["content_id"] == "1d7c1e9ea55f"
    assert primary["sha256"] == card["raster"]["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert primary["verdict"] == card["verdict"] == "negative"
    assert primary["slot_approved"] is False and primary["ok_to_submit_slot"] is False
    assert primary["ok_to_download"] is True
    assert "DO NOT SUBMIT" in primary["status"]
    assert card["leaderboard_score_estimate"]["value"] is None
    assert "NO DEFENSIBLE" in card["leaderboard_score_estimate"]["status"]
    assert len(primary["note"]) <= 140 and "no slot" in primary["note"]

    with rasterio.open(p) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes == ("float32",)
        assert src.crs.to_epsg() == 32611 and src.shape == (3730, 3292)
        assert tuple(src.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(arr).all()
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    assert int((arr > 0).sum()) == 37_654


def test_h72_holdout_labels_counts_and_negative_artifact_gate():
    card = J("registry/run_card_h72_cf_2026-10-26.json")
    hold = card["holdout_dti"]
    main = hold["screen_and_confirm_H72_with_H35"]
    cf = hold["shipped_catfree_detector_family"]

    assert main["withheld_positive_occurrences"] == 45_277
    assert main["candidate_pooled"] > main["same_run_h35_pooled"]
    assert main["paired_gain_ci95"][0] > 0
    assert main["screen_gate_passed"] and main["confirmation_gate_passed"]

    assert cf["withheld_positive_occurrences"] == 22_334
    assert cf["candidate_pooled"] < cf["same_run_h35_pooled"]
    assert cf["paired_gain_vs_H35_ci95"][1] < 0
    assert cf["artifact_performance_gate_passed_vs_best_control"] is False
    assert cf["exact_artifact_emission_evaluated"] is False
    assert hold["leakage_canary"]["max_auc_across_all_three_experiments"] <= 0.90


def test_h72_content_unique_but_strict_lane_negative():
    card = J("registry/run_card_h72_cf_2026-10-26.json")
    uniq = J("evidence/h72_cf_content_uniqueness.json")
    lane = card["correlation_overlap_vs_registry"]

    assert uniq["unique_by_scored_content_vs_prior_registry"] is True
    assert uniq["same_content_prior_registry_matches"] == []
    assert len(uniq["same_content_encoding_twins"]) == 1
    assert card["raster"]["unique_by_content"] is True

    assert lane["surface_pre_placement"]["pass"] is True
    final = lane["final_dots"]
    assert final["focus_and_top_scorers_27"]["lane_pass"] is True
    assert final["own_lineage"]["lane_pass"] is True
    assert final["calibration_artifacts"]["lane_pass"] is False
    assert final["dense_lattice_overlap"] == 1.0
    assert final["strict_lane_pass"] is False
    assert card["ok_to_spend_weekly_slot"] is False


def test_hallucinated_live_score_rows_are_absent_and_authentic_replacements_present():
    rows = J("registry/live_scores.json")["artifacts"]
    labels = {x["label"]: x["score"] for x in rows}
    assert "h50-b2-d28-37654-20261005T195308Z-c55bafc4-zeros" not in labels
    assert "h81-1-b2-strict-relay-54-37708-20261020T060000Z-851c36de-zeros" not in labels
    assert labels["h59-sharpened-scarp-scatter-90k-20261007T171954Z-allfinite"] == 0.0764
    assert labels["gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros"] == 0.1564
    assert labels["gems81-cont-poisson44090-buf2-20261021T233115Z-42223e10-zeros"] == 0.0041
    assert labels["gemsdoe92-listricdip-updip50-37654-20261025T190000Z-zeros"] == 0.0255


def test_owner_prompt_score_list_is_complete_in_registry():
    import re

    brief = (ROOT / "knowledge" / "owner_brief_2026-10-26_verbatim.txt").read_text().splitlines()
    claimed = {
        m.group(1).strip()
        for line in brief
        if (m := re.match(r"^\s*([^:\n]+):\s*0\.\d{4}\s*$", line))
    }
    registered = {x["label"] for x in J("registry/live_scores.json")["artifacts"]}
    assert claimed <= registered
    assert len(claimed) >= 110  # guards against an accidentally truncated prompt archive


def test_h72_current_pages_are_unmistakable_after_site_build():
    for page in ("index.html", "docs/index.html", "docs/current-review.html", "docs/executive-summary.html"):
        text = (ROOT / page).read_text()
        assert FILE in text, page
        assert "OK TO DOWNLOAD: YES" in text.upper(), page
        assert "OK TO SUBMIT: NO" in text.upper(), page
        assert "DO NOT SUBMIT" in text, page
        assert "NO DEFENSIBLE" in text.upper() or "defensible leaderboard estimate is" in text.lower(), page
