"""The structural eligibility gate rejects missing scientific and novelty evidence."""
from copy import deepcopy

from scripts.build_gem_fuse1 import main as retired_fuse1_builder_main
from scripts.package_submissions import main as retired_packager_main, promotion_receipt_valid
from scripts.register_h31_submission import main as retired_h31_registry_writer_main


def receipt(**gate_overrides):
    checks = {name: {"pass_": True, "hard": True} for name in (
        "template_matches_expected_grid_and_footprint", "single_band", "dtype_float32", "crs_epsg_32611",
        "shape_matches_template", "geotransform_matches_template", "footprint_all_finite",
        "footprint_values_in_0_1", "variant_strict_whole_array_no_nan")}
    features = ["gravity", "scarp"]
    cells = [{"fold": f, "draw": d, "features": {name: {"passed": True, "canary_auc": 0.7}
                                                  for name in features}}
             for f in range(4) for d in (2, 3)]
    gate = {"stage": "confirmation", "passed": True, "paired_gate_passed": True,
            "run_id": "paired-confirmation-2026-10-25-test", "same_run_best_control_id": "control-C",
            "same_run_best_dti": 0.15, "candidate_mean_dti": 0.152, "paired_mean_gain": 0.002,
            "folds_positive": 4, "worst_fold_gain": 0.001, "candidate_sha256": "a" * 64,
            "metric_label": "HOLDOUT-DTI", "evaluator": "gems25.holdout.v1.2",
            "evaluator_sha256": "d" * 64, "withheld_positives": 123,
            "paired_ci95": [0.001, 0.003], "cells": [[f, d] for f in range(4) for d in (2, 3)]}
    gate.update(gate_overrides)
    sha, template, labels, surface_sha, manifest = ('a' * 64, 'f' * 64, 'e' * 64, 'c' * 64, 'b' * 64)
    common = dict(raster_sha256=sha, registry_complete=True, max_abs_rank_correlation=.1,
                  registry_manifest_sha256=manifest, template_sha256=template,
                  rank_footprint_pixels=5_167_373, registry_checked=117)
    ready = dict(raster_sha256=sha, lane='assigned-test-lane',
                 format=dict(raster_sha256=sha, template_sha256=template, labels_sha256=labels,
                             **dict.fromkeys(('no_nan_inside', 'values_in_range', 'whole_array_finite_in_range',
                                              'crs_match', 'shape_match', 'transform_match', 'single_band',
                                              'dtype_float32', 'catalogue_mask_exact'), True)),
                 surface=dict(**common, scores_sha256=surface_sha),
                 dots=dict(**common, surface_sha256=surface_sha, max_overlap_3px=.1, exact_duplicate=False),
                 canary=dict(raster_sha256=sha, run_id=gate['run_id'], all_features_tested=True,
                             feature_names=features, cells=cells, max_auc=.7),
                 holdout=dict(raster_sha256=sha, labels_sha256=labels, run_id=gate['run_id'], stage=gate['stage'],
                              evidence_class=gate['metric_label'], evaluator_version=gate['evaluator'],
                              evaluator_sha256=gate['evaluator_sha256'], withheld_positives=gate['withheld_positives'],
                              dti=gate['candidate_mean_dti'], dti_ci95=[.14, .17],
                              comparator_dti=gate['same_run_best_dti'], paired_delta_ci95=gate['paired_ci95'],
                              cells=[dict(fold=f, draw=d) for f in range(4) for d in (2, 3)],
                              same_run_comparator=True, whole_segment_buffered=True, visible_only_features=True,
                              visible_mask_exact=True, pooled=True, alpha=.2, beta=.8, kernel_m=300, kernel='triangular'))
    return {"format_ok": True, "slot_eligible": True, "sha256": sha, "checks": checks, "readiness": ready,
            "promotion_gate": gate,
            "feature_canaries": {"run_id": gate["run_id"], "features": features, "cells": cells},
            "lane_check": {
                "surface": {"surface_clear": True, "registry_complete": True, "flagged": [],
                            "registry_manifest_sha256": "b" * 64, "scores_sha256": "c" * 64,
                            "template_sha256": "f" * 64, "rank_footprint_pixels": 5_167_373},
                "final": {"lane_clear": True, "registry_complete": True, "flagged_literal": [],
                          "registry_manifest_sha256": "b" * 64, "surface_sha256": "c" * 64,
                          "template_sha256": "f" * 64, "rank_footprint_pixels": 5_167_373, "sha256": "a" * 64}}}


def test_legacy_duplicate_packager_fails_closed():
    import pytest
    with pytest.raises(SystemExit, match="known duplicate D2.8 artifact"):
        retired_packager_main()


def test_known_gem_fuse1_lane_duplicate_builder_is_retired(capsys):
    assert retired_fuse1_builder_main() == 2
    assert "strict lane duplicate" in capsys.readouterr().err


def test_h31_registry_writer_cannot_restore_lane_duplicate(capsys):
    assert retired_h31_registry_writer_main() == 2
    assert "strict lane rule" in capsys.readouterr().err


def test_requires_confirmed_same_run_holdout_win_and_ci_for_exact_file():
    assert promotion_receipt_valid(receipt())
    assert not promotion_receipt_valid({"format_ok": True, "slot_eligible": True})
    for overrides in (dict(stage="screen"), dict(passed=False), dict(paired_gate_passed=False),
                      dict(candidate_mean_dti=0.15, paired_mean_gain=0.0), dict(same_run_best_dti=0.151),
                      dict(same_run_best_control_id=""), dict(run_id=""), dict(candidate_sha256="another-file"),
                      dict(same_run_best_dti="not-a-number"), dict(candidate_mean_dti=float("inf")),
                      dict(candidate_mean_dti=True), dict(paired_mean_gain=0.5), dict(folds_positive=2),
                      dict(worst_fold_gain=-0.02), dict(paired_ci95=[-0.001, 0.003]),
                      dict(paired_ci95=[0.001, float("nan")]), dict(withheld_positives=0),
                      dict(metric_label="leaderboard"), dict(evaluator_sha256="not-a-hash")):
        assert not promotion_receipt_valid(receipt(**overrides)), overrides
    bad = receipt()
    bad["promotion_gate"].pop("paired_ci95")
    assert not promotion_receipt_valid(bad)
    assert not promotion_receipt_valid({**receipt(), "format_ok": False})


def test_literal_surface_and_final_gates_are_both_required():
    for section, field, value in (
        ("surface", "surface_clear", False), ("surface", "registry_complete", False),
        ("surface", "flagged", ["dense-lattice"]), ("final", "lane_clear", False),
        ("final", "registry_complete", False), ("final", "flagged_literal", ["dense-lattice"]),
        ("final", "sha256", "e" * 64), ("final", "registry_manifest_sha256", "e" * 64),
        ("final", "surface_sha256", "e" * 64), ("final", "template_sha256", "e" * 64),
        ("surface", "rank_footprint_pixels", 400_000),
    ):
        bad = receipt()
        bad["lane_check"][section][field] = value
        assert not promotion_receipt_valid(bad), (section, field)
    bad = receipt()
    bad["lane_check"]["final"]["flagged_lane"] = []  # an old density waiver cannot help
    bad["lane_check"]["final"]["flagged_literal"] = ["dense-lattice"]
    assert not promotion_receipt_valid(bad)
    bad = receipt()
    bad["checks"]["variant_strict_whole_array_no_nan"]["pass_"] = False
    assert not promotion_receipt_valid(bad)


def test_every_feature_canary_covers_every_evaluated_fold_and_draw():
    bad = receipt()
    bad["feature_canaries"]["cells"][0]["features"]["gravity"]["canary_auc"] = 0.901
    assert not promotion_receipt_valid(bad)
    bad = receipt()
    del bad["feature_canaries"]["cells"][0]["features"]["scarp"]
    assert not promotion_receipt_valid(bad)
    bad = receipt()
    bad["feature_canaries"]["cells"].pop()
    assert not promotion_receipt_valid(bad)
    bad = receipt()
    bad["feature_canaries"]["cells"][0]["features"]["gravity"]["passed"] = False
    assert not promotion_receipt_valid(bad)
    bad = receipt()
    bad["feature_canaries"]["features"].append(["malformed"])
    assert not promotion_receipt_valid(bad)
    bad = deepcopy(receipt())
    bad["feature_canaries"]["run_id"] = "another-run"
    assert not promotion_receipt_valid(bad)


def test_legacy_gate_cannot_bypass_or_disagree_with_shared_readiness():
    bad = receipt()
    del bad['readiness']
    assert not promotion_receipt_valid(bad)
    bad = receipt()
    bad['readiness']['holdout']['dti_ci95'] = None
    assert not promotion_receipt_valid(bad)
    bad = receipt()
    bad['readiness']['surface']['registry_manifest_sha256'] = 'a' * 64
    assert not promotion_receipt_valid(bad)
    bad = receipt()
    bad['readiness']['holdout']['run_id'] = bad['readiness']['canary']['run_id'] = 'different-run'
    assert not promotion_receipt_valid(bad)
