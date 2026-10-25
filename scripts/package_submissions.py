#!/usr/bin/env python3
"""Retired legacy packager for the D2.8 H19-5 research artifact.

The old implementation could recreate and register a TIFF already identified as
byte-identical to a sibling submission. It is intentionally disabled. It must
not be used to package a competition candidate. Future packaging must consume a
new, exact-file receipt whose candidate beats a comparable same-run control,
passes feature-leakage and strict lane gates, and passes the template validator.
"""

from __future__ import annotations

import math


def promotion_receipt_valid(receipt: dict) -> bool:
    """Validate the essential promotion fields for one exact file.

    This validator is retained for unit tests and future packaging code. The
    retired D2.8 CLI does not call it or create artifacts.
    """
    if not isinstance(receipt, dict) or receipt.get("format_ok") is not True or receipt.get("slot_eligible") is not True:
        return False
    gate = receipt.get("promotion_gate")
    checks = receipt.get("checks")
    if not isinstance(gate, dict) or not isinstance(checks, dict):
        return False
    hard_checks = [item for item in checks.values() if isinstance(item, dict) and item.get("hard") is True]
    if not hard_checks or any(item.get("pass_") is not True for item in hard_checks):
        return False
    try:
        control_raw = gate["same_run_best_dti"]
        candidate_raw = gate["candidate_mean_dti"]
        gain_raw = gate["paired_mean_gain"]
        folds_positive = gate["folds_positive"]
        worst_fold_raw = gate["worst_fold_gain"]
        if any(isinstance(value, bool) for value in (control_raw, candidate_raw, gain_raw, folds_positive, worst_fold_raw)):
            return False
        if not isinstance(folds_positive, int):
            return False
        control = float(control_raw)
        candidate = float(candidate_raw)
        gain = float(gain_raw)
        worst_fold = float(worst_fold_raw)
        run_id = gate.get("run_id")
        control_id = gate.get("same_run_best_control_id")
        candidate_sha = gate.get("candidate_sha256")
        file_sha = receipt.get("sha256")
        valid_sha = isinstance(candidate_sha, str) and len(candidate_sha) == 64 and all(c in "0123456789abcdef" for c in candidate_sha)
        numeric = (control, candidate, gain, worst_fold)
        return bool(
            gate.get("stage") == "confirmation"
            and gate.get("passed") is True
            and gate.get("paired_gate_passed") is True
            and isinstance(run_id, str) and bool(run_id.strip())
            and isinstance(control_id, str) and bool(control_id.strip())
            and all(math.isfinite(value) for value in numeric)
            and 0.0 <= control <= 1.0 and 0.0 <= candidate <= 1.0
            and candidate > control
            and math.isclose(gain, candidate - control, rel_tol=0.0, abs_tol=1e-6)
            and gain > 0.001
            and folds_positive >= 3
            and worst_fold >= -0.010
            and valid_sha
            and candidate_sha == file_sha
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def main() -> None:
    raise SystemExit(
        "disabled: this legacy script rebuilds the known duplicate D2.8 artifact "
        "(content id e56ea318af89; SHA-256 91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8). "
        "It cannot package a unique candidate. Do not use it for a submission."
    )


if __name__ == "__main__":
    main()
