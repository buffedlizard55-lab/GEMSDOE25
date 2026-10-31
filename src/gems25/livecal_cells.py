"""Truth intensity on a two-covariate cell grid (distance-to-catalogue x reference-detector quantile).

``src/gems25/livecal.py`` models the hidden-truth intensity as a function of distance to the catalogue
alone.  ``knowledge/56`` and ``knowledge/57`` show that this cannot reproduce the owner-reported scores:
a detector factor is required (leave-one-out RMSE halves when it is added).  This module holds the
two-covariate machinery shared by the calibration script and the candidate builder, so the fitted model
and the design that uses it cannot drift apart.

Everything here is algebra on the published DTI plus an explicit cell-wise truth model.  It produces
**model estimates**, never scores.
"""
from __future__ import annotations

import numpy as np

from .livecal import DISJOINT_DIST, N_BINS, distance_bins, disc_count, psi
from .metric import ALPHA, BETA

__all__ = [
    "cell_code", "detector_gain", "cell_weights", "predict", "N_BINS", "DISC_COUNT_R",
]

DISC_COUNT_R = disc_count(3.0)


def cell_code(d_cat: np.ndarray, foot: np.ndarray, lab: np.ndarray, z: np.ndarray, n_zb: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(code, reps, q)``: the per-pixel cell id, the distance-bin representatives and the
    detector-quantile bin centres.  ``code`` is -1 outside the eligible support (the truth support is
    footprint pixels that are not catalogue pixels)."""
    dcode, reps = distance_bins(d_cat, foot)
    elig = foot & ~lab
    edges = np.quantile(z[elig], np.linspace(0, 1, n_zb + 1)[1:-1])
    zb = np.full(foot.shape, -1, np.int32)
    zb[elig] = np.searchsorted(edges, z[elig], side="right").astype(np.int32)
    code = np.full(foot.shape, -1, np.int32)
    ok = (dcode >= 0) & (zb >= 0)
    code[ok] = dcode[ok].astype(np.int32) * n_zb + zb[ok].astype(np.int32)
    q = (np.arange(n_zb, dtype=float) + 0.5) / n_zb
    return code, reps, q


def detector_gain(params: np.ndarray, q: np.ndarray, link: str, ratio: float = np.inf) -> np.ndarray:
    """Per-detector-bin truth multiplier.

    none    : flat (the detector carries no information)
    exp     : exp(gamma * q)                                monotone increasing in the detector score
    power   : q ** gamma                                    monotone increasing
    betapdf : (q + e)^(a-1) (1 - q + e)^(b-1), normalised    can peak strictly inside (0, 1)

``ratio`` caps the dynamic range ``max(g)/min(g)``; ``np.inf`` leaves it free.  A free fit can reach a
range of 1e10, which is not defensible from a dozen anchors and produces a design that puts every dot
in a handful of pixels, so the capped fits are the ones used for design.
    """
    if link == "none":
        return np.ones_like(q)
    if link == "exp":
        g = np.exp(np.clip(float(params[0]), 0.0, 60.0) * q)
    elif link == "power":
        g = np.power(np.clip(q, 1e-6, 1.0), np.clip(float(params[0]), 0.0, 60.0))
    elif link == "betapdf":
        a, b = float(params[0]), float(params[1])
        e = 1e-3
        g = np.power(np.clip(q, 0.0, 1.0) + e, a - 1.0) * np.power(1.0 - np.clip(q, 0.0, 1.0) + e, b - 1.0)
        g = np.nan_to_num(g, nan=0.0, posinf=0.0, neginf=0.0)
    else:
        raise ValueError(link)
    if np.isfinite(ratio) and ratio > 1.0:
        g = np.maximum(g, np.nanmax(g) / ratio)
    s = g.sum()
    return g / s if s > 0 else g


def cell_weights(theta: np.ndarray, model: str, reps: np.ndarray, q: np.ndarray, link: str,
                 n_shape: int, ratio: float = np.inf) -> tuple[float, np.ndarray]:
    """``(n_truth, w)`` with ``w`` the unnormalised per-cell truth density, flat over the cells."""
    from .livecal import pi_weights

    n = float(np.clip(theta[0], 1.0, 1e7))
    shape = np.asarray(theta[1:1 + n_shape], dtype=float)
    gpar = np.asarray(theta[1 + n_shape:], dtype=float)
    f = pi_weights(shape, reps, model)          # (N_BINS,); bin 0 = catalogue -> zero truth
    g = detector_gain(gpar, q, link, ratio)     # (n_zb,)
    return n, (f[:, None] * g[None, :]).ravel()


def predict(rows: list[dict], w: np.ndarray, nb: np.ndarray, n_truth: float,
            alpha: float = ALPHA, beta: float = BETA) -> np.ndarray:
    """Analytic model DTI for one row per artefact; each row holds per-cell ``ta``, ``ua``, ``ne``."""
    z = float(w @ nb)
    out = np.empty(len(rows))
    nu = n_truth * w * float(DISC_COUNT_R) / z
    psi_nu = psi(nu)
    for i, r in enumerate(rows):
        t = float(w @ r["ta"]) / z
        tp = n_truth * t
        fp = float(r["ne"] @ psi_nu)
        den = alpha * (tp + fp) + beta * n_truth
        out[i] = tp / den if den > 0 else 0.0
    return out


def pi_grid(theta: np.ndarray, model: str, reps: np.ndarray, q: np.ndarray, link: str, n_shape: int,
            code: np.ndarray, ratio: float = np.inf) -> np.ndarray:
    """Full-resolution truth intensity (sums to 1 over the eligible support) for a fitted ``theta``."""
    _, w = cell_weights(theta, model, reps, q, link, n_shape, ratio)
    pi = np.zeros(code.shape, dtype=np.float64)
    ok = code >= 0
    pi[ok] = w[code[ok]]
    s = pi.sum()
    return pi / s if s > 0 else pi


DISJOINT_DIST_ALIAS = DISJOINT_DIST  # re-exported so callers need only this module
