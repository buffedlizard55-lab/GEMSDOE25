import numpy as np
import pytest

from gems25.factorial import alias_structure, contrasts, design, estimate_effects, fold_effects, lenth

GEN = {"E": "ABCD"}


def test_design_2_5_1_is_balanced_orthogonal_resolution_V():
    d = design(5, GEN)
    X = d["X"]
    assert X.shape == (16, 5)
    assert (X.sum(0) == 0).all()  # balanced
    # all 15 main-effect and 2fi contrast columns are mutually orthogonal
    C = np.column_stack(list(contrasts(X, d["names"], 2).values()))
    G = C.T @ C
    assert np.allclose(G, 16 * np.eye(15))
    a = alias_structure(5, GEN)
    assert a["resolution"] == 5 and a["defining_relation"] == ["I=ABCDE"]
    # each 2fi is aliased with exactly one 3fi, each main effect with one 4fi
    assert a["aliases"]["AB"] == ["CDE"] and a["aliases"]["A"] == ["BCDE"]
    assert a["aliases"]["DE"] == ["ABC"]


def test_no_run_has_zero_active_families_and_all_five_run_exists():
    X = design(5, GEN)["X"]
    n_active = (X == 1).sum(1)
    assert set(n_active) <= {1, 3, 5} and n_active.min() >= 1 and (n_active == 5).sum() == 1


def test_effects_recover_known_model_exactly():
    d = design(5, GEN)
    X = d["X"]
    # y = 10 + 3*A/2 ... effect(A)=3, effect(B)=-2, effect(A:C)=4  (effect = 2*coefficient)
    y = 10 + 1.5 * X[:, 0] - 1.0 * X[:, 1] + 2.0 * X[:, 0] * X[:, 2]
    e = estimate_effects(X, y, d["names"])
    assert e["A"] == pytest.approx(3.0) and e["B"] == pytest.approx(-2.0) and e["AC"] == pytest.approx(4.0)
    for k, v in e.items():
        if k not in ("A", "B", "AC"):
            assert v == pytest.approx(0.0, abs=1e-12)


def test_lenth_flags_only_the_active_effects():
    rng = np.random.default_rng(3)
    d = design(5, GEN)
    X = d["X"]
    y = 5 + 3.0 * X[:, 1] + 2.4 * X[:, 0] * X[:, 3] + rng.normal(0, 0.15, 16)
    e = estimate_effects(X, y, d["names"])
    L = lenth(e)
    active = [k for k, v in e.items() if abs(v) > L["me"]]
    assert set(active) == {"B", "AD"}


def test_fold_effects_has_se_and_sign_counts():
    d = design(5, GEN)
    X = d["X"]
    rng = np.random.default_rng(4)
    Y = np.column_stack([3 * X[:, 2] + rng.normal(0, 0.2, 16) for _ in range(4)])
    fe = fold_effects(X, Y, d["names"])
    assert fe["C"]["blocks_positive"] == 4 and fe["C"]["t"] > 10
    assert abs(fe["A"]["mean"]) < 0.5


def test_other_design_2_7_3_resolution_IV():
    gens = {"E": "ABC", "F": "BCD", "G": "ACD"}
    d = design(7, gens)
    assert d["X"].shape == (16, 7)
    assert alias_structure(7, gens)["resolution"] == 4
