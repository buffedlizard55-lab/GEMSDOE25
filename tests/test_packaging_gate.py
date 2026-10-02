from scripts.package_submissions import CURRENT_HOLDOUT_BEST, promotion_receipt_valid


def receipt(**gate_overrides):
    gate = {
        "stage": "confirmation",
        "passed": True,
        "paired_gate_passed": True,
        "historical_best": CURRENT_HOLDOUT_BEST,
        "candidate_mean_dti": CURRENT_HOLDOUT_BEST + 0.001,
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


def test_exploratory_packaging_requires_confirmed_holdout_win_for_exact_file():
    assert promotion_receipt_valid(receipt())
    assert not promotion_receipt_valid({"format_ok": True, "slot_eligible": True})
    assert not promotion_receipt_valid(receipt(stage="screen"))
    assert not promotion_receipt_valid(receipt(passed=False))
    assert not promotion_receipt_valid(receipt(paired_gate_passed=False))
    assert not promotion_receipt_valid(receipt(candidate_mean_dti=CURRENT_HOLDOUT_BEST))
    assert not promotion_receipt_valid(receipt(historical_best=CURRENT_HOLDOUT_BEST + 0.01))
    assert not promotion_receipt_valid(receipt(candidate_sha256="another-file"))


def test_exploratory_packaging_fails_closed_on_incomplete_or_invalid_receipts():
    assert not promotion_receipt_valid(receipt(historical_best=CURRENT_HOLDOUT_BEST - 0.01))
    assert not promotion_receipt_valid(receipt(candidate_mean_dti="not-a-number"))
    assert not promotion_receipt_valid(receipt(candidate_mean_dti=float("inf")))
    assert not promotion_receipt_valid(receipt(candidate_mean_dti=True))
    assert not promotion_receipt_valid({**receipt(), "format_ok": False})
