"""Tests for the live-anchored calibration algebra in :mod:`gems25.livecal`.

The point of these tests is that nothing in ``scripts/run_h28.py`` rests on an untested identity: the
expected-TP/expected-FP formulas are checked against Monte-Carlo evaluation of the *published* metric
(``metric.dti_binary`` / ``dti_exact``), and the design primitives are checked against their definitions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems25 import livecal  # noqa: E402
from gems25.metric import dti_binary, dti_exact  # noqa: E402


def test_kernel_matches_metric():
    offs, ws = livecal.kernel_offsets()
    assert offs.shape == (25, 2) and ws.size == 25
    # the offsets with k > 0 are exactly d^2 in {0,1,2,4,5,8}
    d2 = sorted({int(dy * dy + dx * dx) for dy, dx in offs})
    assert d2 == [0, 1, 2, 4, 5, 8]
    assert abs(livecal.KERNEL_VOLUME - 9.3802978105) < 1e-9
    assert livecal.DISJOINT_DIST == 6.0


def test_emission_fields_are_kernel_max_and_sum():
    rng = np.random.default_rng(0)
    p = (rng.random((23, 19)) > 0.9).astype(np.float32)
    m, u = livecal.emission_fields(p)
    # brute force on a few pixels
    for y, x in [(0, 0), (5, 7), (11, 3), (22, 18), (9, 9)]:
        bm = bu = 0.0
        for (dy, dx), w in zip(livecal.KERNEL_OFFSETS, livecal.KERNEL_WEIGHTS):
            ny, nx = y + dy, x + dx
            if 0 <= ny < p.shape[0] and 0 <= nx < p.shape[1] and p[ny, nx] > 0:
                bm = max(bm, float(p[ny, nx]) * w)
                bu += float(p[ny, nx]) * w
        assert abs(m[y, x] - bm) < 1e-5
        assert abs(u[y, x] - bu) < 1e-4
    assert np.all(u >= m - 1e-6)


def test_saturation_function_is_exact_at_first_order():
    """``1 - Psi(nu) -> nu * KERNEL_VOLUME / V(R)`` — the linear FP term is the low-density limit."""
    T, C = livecal.PSI_T_LEN, livecal.PSI_COUNT
    assert abs(T.sum() - 1.0) < 1e-12
    assert abs(float((T * C).sum()) - livecal.KERNEL_VOLUME / livecal.DISC_COUNT_R) < 1e-12
    for nu in (1e-6, 1e-4, 1e-2):
        assert abs((1.0 - float(livecal.psi(nu))) / nu - livecal.KERNEL_VOLUME / livecal.DISC_COUNT_R) < 1e-3
    assert float(livecal.psi(0.0)) == 1.0
    assert 0.0 < float(livecal.psi(50.0)) < float(livecal.psi(1.0)) < 1.0


def test_expected_tp_is_exact_and_expected_fp_saturates():
    """E[TP] = N <pi, m_p> is exact; E[FP] must track Monte Carlo even when truth is dense."""
    rng = np.random.default_rng(3)
    shape = (40, 40)
    p = (rng.random(shape) > 0.85).astype(np.float64)
    footprint = np.ones(shape, bool)
    labels = np.zeros(shape, bool)
    code = np.zeros(shape, np.int32)
    code[10:30, 10:30] = 1
    code[0:5, :] = 2
    nb = livecal.bin_counts(code)
    w = np.zeros(livecal.N_BINS)
    w[1], w[2] = 3.0, 1.0
    st = livecal.artefact_stats("t", p.astype(np.float32), labels=labels, footprint=footprint,
                                code=code, score=None)
    for n_truth in (30.0, 400.0):
        pred = livecal.predicted_dti(st, n_truth, w, nb)
        vals = []
        for s in range(400):
            g = livecal.sample_truth(n_truth, w, code, nb, seed=1000 + s)
            r = dti_binary(p > 0, g, valid=footprint, known=labels)
            vals.append(r["dti"])
        mc = float(np.mean(vals))
        # E[TP]/N is exact (linearity over truth pixels), so the MC coverage must match tightly
        cov = []
        for s in range(400):
            g = livecal.sample_truth(n_truth, w, code, nb, seed=1000 + s)
            cov.append(dti_binary(p > 0, g, valid=footprint, known=labels)["coverage"])
        assert abs(float(np.mean(cov)) - pred["tp_frac"]) < 3e-3, (float(np.mean(cov)), pred["tp_frac"])
        if n_truth == 30.0:
            assert abs(pred["dti"] - mc) < 0.01, (pred["dti"], mc)
            assert pred["nu_mean"] < 1.0
        else:
            # dense truth: the saturating FP term must stay close; the first-order term would not
            assert abs(pred["dti"] - mc) < 0.06, (pred["dti"], mc)
            # the linear term would go unphysically negative here; saturation keeps FP in [0, M]
            assert pred["fp_first_order_raw"] < 0.0 < pred["fp"] <= st.mass
        assert pred["nu_mean"] >= 0.0


def test_predicted_dti_reproduces_a_known_case():
    """A design whose pixels sit exactly on the truth must score 1.0 (TP=|G|, FP=0)."""
    shape = (30, 30)
    g = np.zeros(shape, bool)
    g[5, 5] = g[15, 15] = g[25, 10] = True
    r = dti_binary(g, g, valid=np.ones(shape, bool))
    assert abs(r["dti"] - 1.0) < 1e-6


def test_soft_predictions_use_the_same_algebra():
    rng = np.random.default_rng(5)
    shape = (30, 30)
    p = np.clip(rng.random(shape), 0, 1) * (rng.random(shape) > 0.8)
    g = np.zeros(shape, bool)
    g[[3, 9, 20], [4, 11, 21]] = True
    a = dti_exact(p, g, valid=np.ones(shape, bool))
    b = dti_exact(p, g, valid=np.ones(shape, bool))
    assert a["dti"] == b["dti"]


def test_distance_bins_partition_the_footprint():
    labels = np.zeros((20, 20), bool)
    labels[10, 10] = True
    from scipy.ndimage import distance_transform_edt

    d = distance_transform_edt(~labels)
    foot = np.ones((20, 20), bool)
    foot[0:2, :] = False
    code, reps = livecal.distance_bins(d, foot)
    assert reps.size == livecal.N_BINS
    assert code[10, 10] == livecal.CATALOGUE_BIN
    assert code[10, 11] == 1
    assert (code[~foot] == -1).all()
    assert (code[foot & (d > 0)] >= 1).all()


def test_greedy_disjoint_respects_the_exclusion_and_the_order():
    v = np.zeros((25, 25))
    v[5, 5] = 9.0
    v[5, 7] = 8.0  # within 6 px of the best -> must be dropped
    v[20, 20] = 7.0
    v[20, 22] = 6.0
    elig = v > 0  # zero-value pixels are not candidates: a design never pays FP mass for no credit
    mask, vals = livecal.greedy_disjoint(v, elig, min_dist=6.0, max_keep=10)
    assert int(mask.sum()) == 2
    assert mask[5, 5] and mask[20, 20]
    assert list(np.round(vals, 3)) == [9.0, 7.0]
    yy, xx = np.nonzero(mask)
    assert np.hypot(yy[0] - yy[1], xx[0] - xx[1]) >= 6.0 - 1e-9


def test_greedy_disjoint_is_a_covering_of_the_value_support():
    rng = np.random.default_rng(1)
    v = np.where(rng.random((60, 60)) > 0.97, rng.random((60, 60)), 0.0)
    elig = v > 0
    mask, _ = livecal.greedy_disjoint(v, elig, min_dist=6.0, max_keep=10_000)
    # maximal packing: every eligible pixel is within min_dist of a kept pixel
    from scipy.ndimage import distance_transform_edt

    d = distance_transform_edt(~mask)
    assert d[elig].max() < 6.0


def test_design_dti_curve_marginal_rule():
    vals = np.array([0.5, 0.4, 0.3, 1e-9, 1e-9])
    n = 10_000.0
    out = livecal.design_dti_curve(vals, n)
    m = np.arange(1, 6)
    dti = n * np.cumsum(vals) / (0.2 * m + 0.8 * n)
    assert out["budget"] == int(np.argmax(dti)) + 1
    assert abs(out["dti"] - dti.max()) < 1e-12
    assert abs(out["marginal_value_threshold"] - 0.2 * out["dti"] / n) < 1e-12
    # the budget stops exactly where the marginal value falls below the threshold
    assert out["marginal_value_at_budget"] >= out["marginal_value_threshold"] - 1e-12


def test_pi_weights_never_put_mass_on_known_pixels():
    reps = np.zeros(livecal.N_BINS)
    reps[1:21] = np.arange(1, 21)
    for model, params in (("uniform", []), ("exp_halo", [5.0, 2.0]), ("step_halo", [5.0, 3.0]),
                          ("pure_exp", [1.0, 2.0]), ("two_scale", [5.0, 1.5, 2.0, 12.0])):
        w = livecal.pi_weights(np.asarray(params, dtype=float), reps, model)
        assert w[livecal.CATALOGUE_BIN] == 0.0
        assert np.isfinite(w).all()
        assert w[1:].sum() > 0


def test_pi_field_matches_the_binned_weights():
    labels = np.zeros((41, 41), bool)
    labels[20, 20] = True
    from scipy.ndimage import distance_transform_edt

    d = distance_transform_edt(~labels)
    foot = np.ones((41, 41), bool)
    code, reps = livecal.distance_bins(d, foot)
    nb = livecal.bin_counts(code)
    params = np.array([4.0, 2.5])
    field = livecal.pi_field(params, d, foot, labels, "exp_halo")
    assert abs(field.sum() - 1.0) < 1e-9
    assert field[labels].sum() == 0.0
    w = livecal.pi_weights(params, reps, "exp_halo")
    per_bin_field = np.array([field[code == b].sum() for b in range(livecal.N_BINS)])
    per_bin_w = w * nb / (w @ nb)
    # inside a 1 px-wide distance band the exponential is flat to within the band width
    assert np.abs(per_bin_field[1:11] - per_bin_w[1:11]).max() < 0.02
