"""Integrity tests for the H28 live-anchored calibration: ledger, evidence, gates, and the inversion algebra.

These tests exist so that a future session cannot silently (a) fit an artefact whose score is not hash-linked,
(b) promote a candidate on a failed gate, or (c) quote a calibrated number that the evidence files do not contain.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25 import livecal  # noqa: E402


def J(p: str):
    f = ROOT / p
    return json.loads(f.read_text()) if f.exists() else None


LEDGER = J("registry/artifact_ledger.json")
ANCHORS = J("evidence/h28_calibration/anchors.json")
DESIGN = J("evidence/h28_calibration/design.json")
MIXTURE = J("evidence/h28_calibration/mixture.json")
HABITAT = J("evidence/h28_calibration/habitat_fit.json")
HOLDOUT = J("evidence/h28_holdout/results.json")


@pytest.mark.skipif(LEDGER is None, reason="artefact ledger not restored")
def test_ledger_only_fits_hash_linked_scores():
    assert LEDGER["n_rows"] == len(LEDGER["artifacts"])
    fitted = [a for a in LEDGER["artifacts"] if a.get("fit")]
    assert LEDGER["n_used_in_fit"] == len(fitted)
    for a in fitted:
        assert re.fullmatch(r"[0-9a-f]{64}", a["sha256"] or ""), a["id"]
        assert "matched by full SHA-256" in a["score_source"], a["id"]
        assert isinstance(a["score"], float) and 0.0 < a["score"] < 1.0
    # every excluded row must say why
    for a in LEDGER["artifacts"]:
        if not a.get("fit"):
            assert a["score_source"], a["id"]
            assert a["score"] is None or "unverified" in a["score_source"] or "brief" in a["score_source"]


@pytest.mark.skipif(LEDGER is None, reason="artefact ledger not restored")
def test_mirror_registry_never_points_at_drivendata():
    """No fetch location may be a DrivenData host (AGENTS.md rule 3); prose about the policy is fine."""
    mirrors = J("registry/artifact_mirrors.json")
    for m in mirrors["mirrors"]:
        assert m["repo"].startswith("buffedlizard55-lab/"), m
        assert m["path"].endswith(".tif")
        assert "drivendata" not in (m["repo"] + m["path"]).lower()
    assert "drivendata" not in mirrors["score_snapshot"]["source_url"].lower()
    for a in LEDGER["artifacts"]:
        assert "drivendata" not in (a.get("repo") or "").lower()


@pytest.mark.skipif(ANCHORS is None or DESIGN is None, reason="H28 calibration not run")
def test_anchor_checks_all_pass_and_are_consistent():
    for k in ("A1", "A2", "A3", "A4"):
        assert ANCHORS["checks"][k]["verdict"] == "PASS", k
    assert DESIGN["checks"]["C3_masking"]["verdict"] == "PASS"
    assert DESIGN["checks"]["C5_monte_carlo"]["verdict"] == "PASS"
    sel = ANCHORS["selected"]
    assert sel["lambda_hat_px"] == 1.85
    assert 8_000 < sel["n_hat"] < 20_000
    # the selected shape must be the one with the smallest spread among the identified shapes
    identified = {k: v for k, v in ANCHORS["scan"].items() if v["n_finite"] == 5}
    best = min(identified, key=lambda k: identified[k]["max_relative_spread"])
    assert best == sel["pi"]
    # uniform truth must be falsified for the group's surfaces (the headline claim)
    assert ANCHORS["scan"]["uniform"]["n_finite"] < 5


@pytest.mark.skipif(DESIGN is None, reason="H28 calibration not run")
def test_the_shipped_file_is_the_ceiling_of_its_family():
    ceil = DESIGN["ceiling_best"]
    subs = J("registry/submissions.json")["files"]
    primary = next(s for s in subs if s["role"] == "primary")
    assert abs(ceil["min_dist"] - 2.4) < 1e-9
    assert int(ceil["mass"]) == primary["positive_pixels"]
    ref = DESIGN["reference_rows_under_calibrated_pi"]["d2-8"]
    assert abs(ref["dti"] - ceil["dti"]) < 1e-9
    # the summary the download page shows must quote the same number
    assert f"{ref['dti']:.4f}" in primary["summary"]
    # and the 6 px kernel-disjoint design must not be presented as a win anywhere
    assert DESIGN["decision"]["sensitivity_cells_beating_d1_5"] == "0/9"
    assert DESIGN["decision"]["sensitivity_cells_beating_d2_8"] == "0/9"
    assert DESIGN["decision"]["d2_8_dominates_d1_5_in_every_cell"] is True


@pytest.mark.skipif(DESIGN is None, reason="H28 calibration not run")
def test_the_model_reproduces_the_anchors_it_was_fitted_to():
    refs = DESIGN["reference_rows_under_calibrated_pi"]
    for aid in ("lattice-s5", "h19-5", "d1-5"):
        assert abs(refs[aid]["dti"] - refs[aid]["reported"]) <= 0.005, aid
    mc = DESIGN["checks"]["C5_monte_carlo"]["per_artefact"]
    assert max(v["abs_err"] for v in mc.values()) <= 0.01


@pytest.mark.skipif(MIXTURE is None, reason="H28 mixture not run")
def test_mixture_was_not_adopted_and_nothing_was_designed_from_it():
    rule = MIXTURE["adoption_rule"]
    assert rule["adopted"] is False
    assert rule["criterion_i"]["met"] is False or rule["criterion_ii"]["met"] is False
    assert "design" not in MIXTURE, "a design was built from a model that failed its adoption rule"


@pytest.mark.skipif(HABITAT is None, reason="H28 habitat diagnostic not run")
def test_habitat_model_is_recorded_as_a_failure():
    for k in ("C1", "C2", "C4"):
        assert HABITAT["checks"][k]["verdict"] == "FAIL", k
    assert min(v["loo_rmse"] for v in HABITAT["loo"].values()) > 0.020


@pytest.mark.skipif(HOLDOUT is None, reason="H28 holdout not run")
def test_holdout_gate_failed_and_nothing_is_slot_approved():
    assert HOLDOUT["verdict"]["gate_passed"] is False
    assert HOLDOUT["gate"]["passed"] is False
    assert not any(s.get("slot_approved") for s in J("registry/submissions.json")["files"])
    # the comparator reproduction result must be recorded whichever way it fell
    assert HOLDOUT["reproduction_check"]["verdict"] in ("PASS", "FAIL")
    if HOLDOUT["reproduction_check"]["verdict"] == "FAIL":
        ids = [i["id"] for i in J("registry/irregularities.json")["issues"]]
        assert "IR-25-COMPARATOR-DRIFT" in ids
    # spacing far above the kernel diameter must be worse than the status quo (the redundancy theorem's limit)
    by = {(r["value"], r["min_dist"], r["kfrac"]): r["dti_mean"] for r in HOLDOUT["table"]}
    assert by[("score", 6.0, 0.035)] < by[("score", 2.4, 0.035)] - 0.02
    assert by[("score", 3.0, 0.035)] > by[("score", 1.5, 0.035)]


def test_truth_count_inversion_round_trips():
    """`invert_truth_count` must undo the linear-FP form of the DTI exactly (that is what §5b inverts)."""
    rng = np.random.default_rng(0)
    for _ in range(200):
        mass = float(rng.uniform(2e4, 5e5))
        t_frac = float(rng.uniform(0.05, 0.6))
        u_frac = t_frac * float(rng.uniform(1.0, 3.0))
        score = float(rng.uniform(0.005, 0.35))
        n = livecal.invert_truth_count(score, mass, t_frac, u_frac)
        if not np.isfinite(n) or n <= 0:
            continue
        back = n * t_frac / (0.2 * (n * t_frac + max(mass - n * u_frac, 0.0)) + 0.8 * n)
        if mass - n * u_frac > 0:  # the clamp is what makes the two differ; only test the unclamped branch
            assert abs(back - score) < 1e-9 * max(1.0, score), (score, back)


def test_inversion_is_monotone_in_the_credit_and_rejects_impossible_scores():
    # more credit per pixel -> a smaller truth count is needed to explain the same score
    n_hi = livecal.invert_truth_count(0.1922, 121_131.0, 0.50, 0.55)
    n_lo = livecal.invert_truth_count(0.1922, 121_131.0, 0.20, 0.22)
    assert np.isfinite(n_hi) and np.isfinite(n_lo) and n_hi < n_lo


def test_falsified_pi_returns_nan():
    """A reported score too high for the geometry has no solution in N: the denominator is non-positive."""
    assert np.isnan(livecal.invert_truth_count(0.9, 100_000.0, 0.05, 0.05))
    assert np.isfinite(livecal.invert_truth_count(0.0904, 204_504.0, 0.3718, 0.3718))
    if ANCHORS:
        # the real falsification: under uniform truth the group's own surfaces have no finite solution
        uni = ANCHORS["scan"]["uniform"]["per_anchor"]
        assert np.isnan(uni["h19-5"]["implied_N"])
        assert np.isfinite(uni["lattice-s5"]["implied_N"])


def test_disjoint_spacing_constant_is_twice_the_kernel_radius():
    assert livecal.DISJOINT_DIST == 2 * livecal.R_KERNEL == 6.0
    assert livecal.DISC_COUNT_R == 29
    assert abs(livecal.KERNEL_VOLUME - 9.3802978105) < 1e-9


def test_knowledge_index_and_readme_point_at_the_h28_preregistration():
    idx = (ROOT / "knowledge" / "00_INDEX.md").read_text()
    readme = (ROOT / "README.md").read_text()
    name = "10_preregistered_h28_live_anchored_emission_design_2026-10-02.md"
    assert name in idx and name in readme
    doc = (ROOT / "knowledge" / name).read_text()
    for marker in ("## 11. Deviations log", "### D1", "### D2", "### D3", "## 12. Findings", "## 13. Ranked next"):
        assert marker in doc, marker
    # findings must quote the calibrated numbers the evidence files contain
    if ANCHORS:
        assert f"{ANCHORS['selected']['n_hat']:,.0f}".replace(",", " ") in doc or "12 691" in doc
