from scripts.package_submissions import main as retired_packager_main, promotion_receipt_valid
from scripts.build_gem_fuse1 import main as retired_fuse1_builder_main
from scripts.register_h31_submission import main as retired_h31_registry_writer_main


def receipt(**gate_overrides):
    gate = {
        "stage": "confirmation",
        "passed": True,
        "paired_gate_passed": True,
        "run_id": "paired-confirmation-2026-10-25-test",
        "same_run_best_control_id": "control-C",
        "same_run_best_dti": 0.15,
        "candidate_mean_dti": 0.152,
        "paired_mean_gain": 0.002,
        "folds_positive": 4,
        "worst_fold_gain": 0.001,
        "candidate_sha256": "a" * 64,
    }
    gate.update(gate_overrides)
    return {
        "format_ok": True,
        "slot_eligible": True,
        "sha256": "a" * 64,
        "checks": {"finite_range": {"pass_": True, "hard": True}},
        "promotion_gate": gate,
    }


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


def test_exploratory_packaging_requires_confirmed_holdout_win_for_exact_file():
    assert promotion_receipt_valid(receipt())
    assert not promotion_receipt_valid({"format_ok": True, "slot_eligible": True})
    assert not promotion_receipt_valid(receipt(stage="screen"))
    assert not promotion_receipt_valid(receipt(passed=False))
    assert not promotion_receipt_valid(receipt(paired_gate_passed=False))
    assert not promotion_receipt_valid(receipt(candidate_mean_dti=0.15, paired_mean_gain=0.0))
    assert not promotion_receipt_valid(receipt(same_run_best_dti=0.151))
    assert not promotion_receipt_valid(receipt(same_run_best_control_id=""))
    assert not promotion_receipt_valid(receipt(run_id=""))
    assert not promotion_receipt_valid(receipt(candidate_sha256="another-file"))


def test_exploratory_packaging_fails_closed_on_incomplete_or_invalid_receipts():
    assert not promotion_receipt_valid(receipt(same_run_best_dti="not-a-number"))
    assert not promotion_receipt_valid(receipt(candidate_mean_dti=float("inf")))
    assert not promotion_receipt_valid(receipt(candidate_mean_dti=True))
    assert not promotion_receipt_valid(receipt(paired_mean_gain=0.5))
    assert not promotion_receipt_valid(receipt(folds_positive=2))
    assert not promotion_receipt_valid(receipt(worst_fold_gain=-0.02))
    assert not promotion_receipt_valid({**receipt(), "format_ok": False})
