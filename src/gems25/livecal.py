"""Live-anchored calibration of the hidden truth and DTI-optimal emission design (H28).

Everything here is exact algebra on the published DTI, plus an explicit Poisson model for the hidden
truth.  It is used in two directions:

*forward* — given a truth-intensity model ``pi`` (a probability vector over the footprint) and a
submission ``p``, predict the DTI the organizer would report::

    TP  = sum_g max_x p(x) k(d(x,g))          ->  E[TP] = N * <pi, m_p>,   m_p(x) = max_o p(x+o) k(o)
    FP  = sum_x p(x) (1 - max_g k(d(x,g)))    ->  E[FP] = M - N * <pi, u_p>, u_p(x) = sum_o p(x+o) k(o)
    DTI = TP / (0.2 (TP + FP) + 0.8 N)

``E[TP] = N <pi, m_p>`` is exact for a Poisson/binomial truth with intensity ``N*pi`` (linearity over truth
pixels).  ``E[FP]`` is computed with the exact Poisson saturation of the maximum,

    E[FP_p] = int_0^1 exp(-Lambda_p(t)) dt,   Lambda_p(t) = N * (pi mass within R(1-t) of p),

evaluated under the assumption that ``pi`` is locally constant over one kernel disc, so that
``Lambda_p(t) = nu_b * V(R(1-t)) / V(R)`` with ``nu_b = N pi_b V(R)`` the expected number of truth pixels
within R of a pixel in bin b.  This is exactly the first-order term ``M - N <pi, u_p>`` for small ``nu``
(``int_0^1 V(R(1-t)) dt = sum_o k(o) = KERNEL_VOLUME``) and it saturates at 1 as ``nu`` grows, which the
first-order term does not.  ``scripts/run_h28.py`` checks both against Monte-Carlo runs of the published
metric and reports the residual, so the approximation is measured, not assumed.

*inverse* — fit ``(N, pi)`` to the artefacts' reported DTIs, then design the emission that maximises the
predicted DTI.  With ``p`` binary and kernels pairwise disjoint (emitted pixels >= ``DISJOINT_DIST`` = 6 px
apart, because two kernels overlap iff their centres are closer than 2R) the redundancy ``U - T`` vanishes and

    DTI(P) = N * sum_{p in P} u(p) / (0.2 |P| + 0.8 N)

so the optimal design is "take the pixels with the largest ``u = pi*k`` subject to a 6 px exclusion", and the
marginal pixel is worth emitting while ``u > 0.2 * DTI / N``.  ``design_emission`` implements exactly that and
``predicted_dti`` re-checks the chosen design with the full (non-approximated) TP term.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize

from .metric import ALPHA, BETA, RADIUS_PX, dti_binary, dti_exact, kernel

R_KERNEL = RADIUS_PX


def kernel_offsets(r: float = R_KERNEL) -> tuple[np.ndarray, np.ndarray]:
    """The ``(dy, dx)`` offsets and weights with ``k > 0`` — the same disc ``gems25.metric`` uses."""
    rad = int(np.ceil(r))
    offs: list[tuple[int, int]] = []
    ws: list[float] = []
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            w = float(kernel(np.hypot(dy, dx), r))
            if w > 0.0:
                offs.append((dy, dx))
                ws.append(w)
    return np.asarray(offs, dtype=int), np.asarray(ws, dtype=float)


KERNEL_OFFSETS, KERNEL_WEIGHTS = kernel_offsets()
KERNEL_VOLUME = float(KERNEL_WEIGHTS.sum())
# two emitted pixels share kernel support iff their distance is < 2R, so 2R is the redundancy-free spacing
DISJOINT_DIST = 2.0 * R_KERNEL


def _shift_into(out: np.ndarray, p: np.ndarray, dy: int, dx: int, w: float, mode: str) -> None:
    """``out[x] op= w * p[x + (dy, dx)]`` with zero fill outside the array."""
    ny, nx = p.shape
    y0, y1 = max(0, -dy), min(ny, ny - dy)
    x0, x1 = max(0, -dx), min(nx, nx - dx)
    if y0 >= y1 or x0 >= x1:
        return
    src = p[y0 + dy : y1 + dy, x0 + dx : x1 + dx]
    if mode == "max":
        np.maximum(out[y0:y1, x0:x1], src * np.float32(w), out=out[y0:y1, x0:x1])
    else:
        out[y0:y1, x0:x1] += src * np.float32(w)


def emission_fields(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(m_p, u_p)``: the kernel-max field (TP density) and the kernel-sum field (FP credit)."""
    p = np.ascontiguousarray(p, dtype=np.float32)
    m = np.zeros_like(p)
    u = np.zeros_like(p)
    for (dy, dx), w in zip(KERNEL_OFFSETS, KERNEL_WEIGHTS):
        _shift_into(m, p, dy, dx, w, "max")
        _shift_into(u, p, dy, dx, w, "sum")
    return m, u


# ---------------------------------------------------------------------------------------------
# distance-to-catalogue bins: the covariate basis the truth intensity is modelled in
# ---------------------------------------------------------------------------------------------

def distance_bins(d_cat: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Integer bin code per pixel plus the representative distance of each bin.

    Bin 0 is the catalogue itself (excluded from the truth support: known pixels are masked when scoring).
    Bins 1..20 are 1 px wide, then 21-30, 31-50, 51+.  Pixels outside the footprint get code -1.
    """
    edges = np.array([20.5, 30.5, 50.5])
    code = np.full(d_cat.shape, -1, dtype=np.int32)
    inside = footprint & (d_cat > 0)
    dd = np.where(inside, d_cat, 0.0)
    coarse = np.searchsorted(edges, dd, side="left")  # 0 -> <=20, 1 -> <=30, 2 -> <=50, 3 -> beyond
    fine = np.clip(np.rint(dd).astype(np.int32), 1, 20)
    code[inside] = np.where(coarse[inside] == 0, fine[inside], 20 + coarse[inside])
    code[footprint & ~inside] = 0  # catalogue pixels
    nbin = 24
    reps = np.zeros(nbin, dtype=float)
    reps[0] = 0.0
    reps[1:21] = np.arange(1, 21)
    reps[21], reps[22], reps[23] = 25.5, 40.5, 70.0
    return code, reps[:nbin]


N_BINS = 24
CATALOGUE_BIN = 0


@dataclass
class ArtefactStats:
    """Everything the calibration needs about one submission raster, precomputed once."""

    id: str
    score: float | None
    mass: float
    ta: np.ndarray  # per-bin sum of the kernel-max field  -> <pi, m_p> * Z
    ua: np.ndarray  # per-bin sum of the kernel-sum field  -> <pi, u_p> * Z
    nb_emit: np.ndarray = field(default_factory=lambda: np.zeros(1))  # per-bin emitted mass
    on_catalogue: float = 0.0
    extra: dict = field(default_factory=dict)


def artefact_stats(
    ident: str,
    arr: np.ndarray,
    *,
    labels: np.ndarray,
    footprint: np.ndarray,
    code: np.ndarray,
    score: float | None,
) -> ArtefactStats:
    """Bin-summarise one raster.  Predictions on known pixels are dropped first, exactly as the metric does."""
    p = np.nan_to_num(np.asarray(arr, dtype=np.float32), nan=0.0)
    p = np.clip(p, 0.0, 1.0)
    on_cat = float(p[labels].sum())
    p = p * np.float32(~labels)
    p = p * np.float32(footprint)
    m, u = emission_fields(p)
    idx = np.where(code >= 0, code, 0).ravel()
    w = (code >= 0).ravel()
    ta = np.bincount(idx[w], weights=m.ravel()[w], minlength=N_BINS).astype(float)
    ua = np.bincount(idx[w], weights=u.ravel()[w], minlength=N_BINS).astype(float)
    nb_emit = np.bincount(idx[w], weights=p.ravel()[w], minlength=N_BINS).astype(float)
    return ArtefactStats(id=ident, score=score, mass=float(p.sum()), ta=ta, ua=ua, on_catalogue=on_cat,
                         nb_emit=nb_emit)


def bin_counts(code: np.ndarray) -> np.ndarray:
    idx = np.where(code >= 0, code, 0).ravel()
    w = (code >= 0).ravel()
    return np.bincount(idx[w], minlength=N_BINS).astype(float)


# ---------------------------------------------------------------------------------------------
# the truth-intensity model
# ---------------------------------------------------------------------------------------------

def pi_weights(params: np.ndarray, reps: np.ndarray, model: str) -> np.ndarray:
    """Unnormalised truth intensity per distance bin.  Bin 0 (known pixels) always gets zero mass."""
    w = np.zeros_like(reps)
    d = reps[1:]
    if model == "uniform":
        w[1:] = 1.0
    elif model == "exp_halo":  # background + exponential enrichment towards known traces
        a, rho = params
        w[1:] = 1.0 + max(a, 0.0) * np.exp(-d / max(rho, 1e-3))
    elif model == "step_halo":  # background + flat enrichment inside a radius
        a, r = params
        w[1:] = 1.0 + max(a, 0.0) * (d <= max(r, 0.0))
    elif model == "pure_exp":  # no uniform background at all
        a, rho = params
        w[1:] = np.exp(-d / max(rho, 1e-3)) * (1.0 + max(a, 0.0))
    elif model == "two_scale":  # background + near halo + broad halo
        a1, r1, a2, r2 = params
        w[1:] = 1.0 + max(a1, 0.0) * np.exp(-d / max(r1, 1e-3)) + max(a2, 0.0) * np.exp(-d / max(r2, 1e-3))
    else:  # pragma: no cover - guarded by callers
        raise ValueError(model)
    w[CATALOGUE_BIN] = 0.0
    return w


MODEL_PARAMS = {"uniform": 0, "exp_halo": 2, "step_halo": 2, "pure_exp": 2, "two_scale": 4}


DISC_COUNT_R = None  # set below, after disc_count() is defined


def disc_count(r: float) -> int:
    """Number of pixel offsets within Euclidean distance ``r`` (inclusive)."""
    rad = int(np.ceil(r))
    n = 0
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            if np.hypot(dy, dx) <= r + 1e-9:
                n += 1
    return n


def saturation_steps() -> tuple[np.ndarray, np.ndarray]:
    """Exact step structure of ``V(R(1-t))``: ``(t-interval lengths, disc counts)``.

    ``r = R(1-t)`` decreases from R to 0, and ``V(r)`` jumps only when ``r`` crosses one of the finitely many
    offset distances, so the integral over t is a finite sum and no quadrature error is introduced.
    """
    ds = sorted({float(np.hypot(dy, dx)) for dy, dx in KERNEL_OFFSETS})  # 0, 1, sqrt2, 2, sqrt5, 2sqrt2
    ds = ds + [R_KERNEL]
    v_r = float(disc_count(R_KERNEL))
    lengths, counts = [], []
    for lo, hi in zip(ds[:-1], ds[1:]):
        lengths.append((hi - lo) / R_KERNEL)
        counts.append(disc_count(lo) / v_r)
    return np.asarray(lengths, dtype=float), np.asarray(counts, dtype=float)


PSI_T_LEN, PSI_COUNT = saturation_steps()


def _psi_table(nu_max: float = 200.0) -> tuple[np.ndarray, np.ndarray]:
    """``Psi(nu) = int_0^1 exp(-nu V(R(1-t))/V(R)) dt`` on a grid, for interpolation.

    The grid is dense near zero because ``Psi`` is interpolated linearly and is convex: with a coarse grid the
    first-order term (which the whole low-density regime rests on) would be biased by ~0.3 %.
    """
    nu = np.concatenate([np.linspace(0.0, 2.0, 20001), np.linspace(2.0, nu_max, 19801)[1:]])
    psi = np.exp(-np.outer(nu, PSI_COUNT)) @ PSI_T_LEN
    return nu, psi


DISC_COUNT_R = disc_count(R_KERNEL)
_PSI_NU, _PSI_VAL = _psi_table()


def psi(nu: np.ndarray | float) -> np.ndarray:
    """Expected false-positive mass of one emitted pixel whose kernel disc holds ``nu`` truth pixels."""
    return np.interp(np.asarray(nu, dtype=float), _PSI_NU, _PSI_VAL)


def predicted_dti(stats: ArtefactStats, n_truth: float, w: np.ndarray, nb: np.ndarray) -> dict:
    """Analytic DTI prediction for one artefact under ``(n_truth, pi ∝ w)``."""
    z = float(w @ nb)
    t = float(w @ stats.ta) / z
    u = float(w @ stats.ua) / z
    tp = n_truth * t
    nu = n_truth * w * float(DISC_COUNT_R) / z  # expected truth px within R of a pixel in each bin
    nb_emit = stats.nb_emit if stats.nb_emit.size == N_BINS else np.zeros(N_BINS)
    fp = float((nb_emit * psi(nu)).sum())
    fp_first_order_raw = stats.mass - n_truth * u
    fp_first_order = max(fp_first_order_raw, 0.0)
    den = ALPHA * (tp + fp) + BETA * n_truth
    dti = tp / den if den > 0 else 0.0
    return {
        "dti": dti,
        "tp_frac": t,
        "u_frac": u,
        "redundancy": u - t,
        "fp": fp,
        "fp_first_order": fp_first_order,
        "fp_first_order_raw": fp_first_order_raw,
        "fp_per_px": fp / stats.mass if stats.mass else 0.0,
        "nu_mean": float((nb_emit * nu).sum() / stats.mass) if stats.mass else 0.0,
    }


def invert_truth_count(score: float, mass: float, t: float, u: float) -> float:
    """Closed-form inversion of the DTI for the hidden truth count ``N`` (pre-registration §5b).

    ``score = N t / (0.2 (N t + mass - N u) + 0.8 N)`` rearranges to a linear equation in ``N``.  A
    non-positive denominator means **no** ``N`` can produce that score under this ``(t, u)`` — the truth model is
    falsified rather than fitted, which is the strongest statement the ledger can make.
    """
    num = 0.2 * score * mass
    den = t * (1.0 - 0.2 * score) - 0.8 * score + 0.2 * score * u
    return float(num / den) if den > 1e-12 else float("nan")


def _loss(theta: np.ndarray, rows: list[ArtefactStats], nb: np.ndarray, reps: np.ndarray, model: str,
          lo: np.ndarray, hi: np.ndarray) -> float:
    n_truth = float(np.clip(theta[0], lo[0], hi[0]))
    w = pi_weights(theta[1:], reps, model)
    if not np.isfinite(w).any() or w.sum() <= 0:
        return 1e6
    out = 0.0
    for r in rows:
        if r.score is None:
            continue
        out += (predicted_dti(r, n_truth, w, nb)["dti"] - r.score) ** 2
    return out / max(1, sum(1 for r in rows if r.score is not None))


def fit(rows: list[ArtefactStats], nb: np.ndarray, reps: np.ndarray, model: str,
        starts: list[np.ndarray] | None = None,
        bounds: tuple[np.ndarray, np.ndarray] = (
            np.array([2_000.0, 0.0, 0.05, 0.0, 0.05, 0.0]),
            np.array([120_000.0, 400.0, 60.0, 400.0, 60.0, 400.0]),
        )) -> dict:
    """Least-squares fit of ``(N, pi)`` to the reported DTIs.  Returns the best start's optimum."""
    k = MODEL_PARAMS[model]
    lo, hi = bounds[0][: 1 + k], bounds[1][: 1 + k]
    if starts is None:
        starts = []
        for n0 in (8_000.0, 12_500.0, 20_000.0, 40_000.0):
            if k == 0:
                starts.append(np.array([n0]))
            elif k == 2:
                for a0 in (0.5, 3.0, 20.0):
                    for r0 in (1.0, 3.0, 10.0):
                        starts.append(np.array([n0, a0, r0]))
            else:
                for a1, r1, a2, r2 in ((3.0, 1.5, 1.0, 10.0), (20.0, 1.0, 2.0, 15.0), (1.0, 2.0, 0.5, 30.0)):
                    starts.append(np.array([n0, a1, r1, a2, r2]))
    best = None
    for s in starts:
        s = np.clip(s, lo, hi)
        res = minimize(_loss, s, args=(rows, nb, reps, model, lo, hi), method="Nelder-Mead",
                       options={"maxiter": 6000, "xatol": 1e-6, "fatol": 1e-12})
        if best is None or res.fun < best.fun:
            best = res
    theta = np.clip(best.x, lo, hi)
    n_truth = float(theta[0])
    w = pi_weights(theta[1:], reps, model)
    scored = [r for r in rows if r.score is not None]
    resid = {r.id: predicted_dti(r, n_truth, w, nb)["dti"] - r.score for r in scored}
    return {
        "model": model,
        "theta": theta.tolist(),
        "n_truth": n_truth,
        "pi_params": theta[1:].tolist(),
        "weights": (w / (w @ nb)).tolist(),
        "mse": float(best.fun),
        "rmse": float(np.sqrt(best.fun)),
        "max_abs_resid": float(max(abs(v) for v in resid.values())) if resid else 0.0,
        "residuals": resid,
        "n_artifacts": len(scored),
        "loss_message": str(best.message),
    }


def loo_rmse(rows: list[ArtefactStats], nb: np.ndarray, reps: np.ndarray, model: str, **kw) -> dict:
    """Leave-one-artefact-out prediction error: the honest test of whether the pi model transfers."""
    scored = [r for r in rows if r.score is not None]
    errs = {}
    for held in scored:
        rest = [r for r in scored if r.id != held.id]
        f = fit(rest, nb, reps, model, **kw)
        w = np.asarray(f["weights"], dtype=float)
        errs[held.id] = predicted_dti(held, f["n_truth"], w, nb)["dti"] - held.score
    v = np.asarray(list(errs.values()), dtype=float)
    return {"model": model, "loo_rmse": float(np.sqrt(np.mean(v**2))), "loo_max_abs": float(np.max(np.abs(v))),
            "loo_errors": errs, "n": int(v.size)}


# ---------------------------------------------------------------------------------------------
# Monte-Carlo check of the analytic expectation (uses the exact metric, no approximation)
# ---------------------------------------------------------------------------------------------

def sample_truth(n_truth: float, w: np.ndarray, code: np.ndarray, nb: np.ndarray, seed: int) -> np.ndarray:
    """Draw ``round(n_truth)`` truth pixels from the binned intensity (without replacement)."""
    n = int(round(n_truth))
    p = (w * nb)
    p = p / p.sum()
    rng = np.random.default_rng(seed)
    take = rng.multinomial(n, p)
    flat = code.ravel()
    chosen = []
    for b, k in enumerate(take):
        if k <= 0:
            continue
        idx = np.flatnonzero(flat == b)
        if idx.size == 0:
            continue
        chosen.append(rng.choice(idx, size=min(int(k), idx.size), replace=False))
    if not chosen:
        return np.zeros(code.shape, dtype=bool)
    out = np.zeros(code.size, dtype=bool)
    out[np.concatenate(chosen)] = True
    return out.reshape(code.shape)


def sample_truth_field(pi: np.ndarray, n_truth: float, seed: int, footprint: np.ndarray | None = None,
                       labels: np.ndarray | None = None) -> np.ndarray:
    """Draw ``round(n_truth)`` distinct truth pixels with probability proportional to a full-resolution ``pi``.

    Uses the Efraimidis-Spirakis weighted-reservoir keys ``U^(1/pi)`` (exact sampling without replacement,
    O(grid) with no Python loop).  Pixels with ``pi = 0`` can never be drawn.
    """
    w = np.asarray(pi, dtype=np.float64).ravel().copy()
    if footprint is not None:
        w &= np.asarray(footprint, bool).ravel()
    if labels is not None:
        w &= ~np.asarray(labels, bool).ravel()
    if w.sum() <= 0:
        return np.zeros(pi.shape, bool)
    w = w / w.sum()
    rng = np.random.default_rng(seed)
    # Efraimidis-Spirakis keys in log space: argmax u^(1/w) == argmax log(u)/w.  The power form underflows to 0
    # for every pixel when w ~ 1e-6 (as it is here), which silently degrades the draw to a near-uniform sample.
    with np.errstate(divide="ignore"):
        keys = np.where(w > 0, np.log(np.maximum(rng.random(w.size), 1e-300)) / np.maximum(w, 1e-300), -np.inf)
    k = int(min(round(n_truth), w.size))
    idx = np.argpartition(-keys, k - 1)[:k]
    out = np.zeros(w.size, bool)
    out[idx] = True
    return out.reshape(pi.shape)


def mc_dti(arr: np.ndarray, labels: np.ndarray, footprint: np.ndarray, n_truth: float, w: np.ndarray,
           code: np.ndarray, nb: np.ndarray, draws: int = 6, seed: int = 0) -> dict:
    """Exact DTI (``metric.dti_binary``/``dti_exact``) averaged over truth draws from ``(n_truth, w)``."""
    a = np.asarray(arr)
    binary = np.nanmin(a) >= 0 and np.all((np.nan_to_num(a, nan=0.0) == 0) | (np.nan_to_num(a, nan=0.0) == 1))
    vals = []
    for i in range(draws):
        g = sample_truth(n_truth, w, code, nb, seed + i)
        if binary:
            r = dti_binary(a > 0, g, valid=footprint, known=labels)
        else:
            r = dti_exact(np.nan_to_num(a, nan=0.0), g, valid=footprint, known=labels)
        vals.append(float(r["dti"]))
    v = np.asarray(vals)
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)) if v.size > 1 else 0.0,
            "values": [round(x, 6) for x in v], "draws": int(v.size)}


# ---------------------------------------------------------------------------------------------
# inverse design
# ---------------------------------------------------------------------------------------------

def pi_field(params: np.ndarray, d_cat: np.ndarray, footprint: np.ndarray, labels: np.ndarray,
             model: str) -> np.ndarray:
    """Full-resolution truth intensity (normalised to sum 1) from the fitted shape parameters."""
    d = np.where(footprint & ~labels, d_cat, np.inf)
    if model == "uniform":
        w = np.ones_like(d)
    elif model == "exp_halo":
        a, rho = params
        w = 1.0 + max(a, 0.0) * np.exp(-np.minimum(d, 200.0) / max(rho, 1e-3))
    elif model == "step_halo":
        a, r = params
        w = 1.0 + max(a, 0.0) * (d <= max(r, 0.0))
    elif model == "pure_exp":
        a, rho = params
        w = (1.0 + max(a, 0.0)) * np.exp(-np.minimum(d, 200.0) / max(rho, 1e-3))
    elif model == "two_scale":
        a1, r1, a2, r2 = params
        dd = np.minimum(d, 200.0)
        w = 1.0 + max(a1, 0.0) * np.exp(-dd / max(r1, 1e-3)) + max(a2, 0.0) * np.exp(-dd / max(r2, 1e-3))
    else:  # pragma: no cover
        raise ValueError(model)
    w = np.where(np.isfinite(d), w, 0.0).astype(np.float64)
    s = w.sum()
    return w / s if s > 0 else w


def disc_mass(pi: np.ndarray, r: float = R_KERNEL) -> np.ndarray:
    """``pi * 1[d <= r]``: the truth mass inside the kernel disc of each pixel (drives the FP saturation)."""
    rad = int(np.ceil(r))
    pi32 = np.ascontiguousarray(pi, dtype=np.float32)
    out = np.zeros_like(pi32)
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            if np.hypot(dy, dx) <= r + 1e-9:
                _shift_into(out, pi32, dy, dx, 1.0, "sum")
    return out.astype(np.float64)


def value_field(pi: np.ndarray) -> np.ndarray:
    """``u = pi * k``: the expected kernel mass a single emitted pixel collects (the marginal value)."""
    pi32 = np.ascontiguousarray(pi, dtype=np.float32)
    u = np.zeros_like(pi32)
    for (dy, dx), w in zip(KERNEL_OFFSETS, KERNEL_WEIGHTS):
        _shift_into(u, pi32, dy, dx, w, "sum")
    return u.astype(np.float64)


def greedy_disjoint(value: np.ndarray, eligible: np.ndarray, min_dist: float = DISJOINT_DIST,
                    max_keep: int = 200_000, block: np.ndarray | None = None,
                    stop_value: float = -np.inf) -> tuple[np.ndarray, np.ndarray]:
    """Highest-value pixels subject to a ``min_dist`` exclusion.  Returns ``(mask, values_in_pick_order)``.

    Deterministic: ties are broken by flat index.  Blocking uses the exact offset disc, so the result is a
    maximal packing of the eligible set at ``min_dist`` and (for ``min_dist >= 2R``) redundancy-free.
    """
    rad = int(np.ceil(min_dist))
    if block is None:
        offs = [(dy, dx) for dy in range(-rad, rad + 1) for dx in range(-rad, rad + 1)
                if float(np.hypot(dy, dx)) < min_dist]
        block = np.asarray(offs, dtype=int)
    ny, nx = value.shape
    flat_v = np.asarray(value, dtype=np.float64).ravel()
    cand = np.flatnonzero(np.asarray(eligible, bool).ravel())
    if cand.size == 0:
        return np.zeros(value.shape, bool), np.zeros(0)
    cand = cand[np.argsort(-flat_v[cand], kind="stable")]
    order = cand
    kept = np.zeros(value.size, dtype=bool)
    blocked = np.zeros(value.size, dtype=bool)
    picked: list[int] = []
    vals: list[float] = []
    for f in order:
        if len(picked) >= max_keep:
            break
        vf = flat_v[f]
        if not np.isfinite(vf) or vf < stop_value:
            break  # descending order: nothing below can qualify either
        if blocked[f]:
            continue
        picked.append(int(f))
        vals.append(float(vf))
        kept[f] = True
        y, x = divmod(int(f), nx)
        ys = np.clip(y + block[:, 0], 0, ny - 1)
        xs = np.clip(x + block[:, 1], 0, nx - 1)
        valid = ((y + block[:, 0] >= 0) & (y + block[:, 0] < ny) &
                 (x + block[:, 1] >= 0) & (x + block[:, 1] < nx))
        blocked[ys[valid] * nx + xs[valid]] = True
    mask = kept.reshape(value.shape)
    return mask, np.asarray(vals, dtype=float)


def design_dti_curve(vals: np.ndarray, n_truth: float) -> dict:
    """Predicted DTI versus budget for a redundancy-free design, from the picked values in order.

    ``DTI(M) = N * sum_{i<M} u_i / (0.2 M + 0.8 N)`` and the marginal pixel is worth taking while
    ``u_(M) > 0.2 * DTI / N``.
    """
    cum = np.cumsum(vals)
    m = np.arange(1, vals.size + 1, dtype=float)
    dti = n_truth * cum / (ALPHA * m + BETA * n_truth)
    best = int(np.argmax(dti))
    thresh = ALPHA * dti[best] / n_truth
    return {"budget": best + 1, "dti": float(dti[best]), "marginal_value_threshold": float(thresh),
            "marginal_value_at_budget": float(vals[best]),
            "curve_m": [int(x) for x in m[:: max(1, m.size // 60)]],
            "curve_dti": [float(x) for x in dti[:: max(1, m.size // 60)]]}


# ---------------------------------------------------------------------------------------------
# vectorised calibration set (the loss is evaluated tens of thousands of times while fitting)
# ---------------------------------------------------------------------------------------------

@dataclass
class CalibrationSet:
    """All fitted artefacts stacked into matrices so one loss evaluation is a handful of dot products."""

    ids: list[str]
    scores: np.ndarray
    ta: np.ndarray      # (n, N_BINS) kernel-max field sums
    ua: np.ndarray      # (n, N_BINS) kernel-sum field sums
    ne: np.ndarray      # (n, N_BINS) emitted mass per bin
    mass: np.ndarray    # (n,) total emitted mass after masking known pixels
    nb: np.ndarray      # (N_BINS,) scored-domain pixel count per bin
    reps: np.ndarray    # (N_BINS,) representative distance per bin

    @classmethod
    def from_stats(cls, rows: list[ArtefactStats], nb: np.ndarray, reps: np.ndarray) -> "CalibrationSet":
        used = [r for r in rows if r.score is not None and r.nb_emit.size == N_BINS]
        return cls(ids=[r.id for r in used],
                   scores=np.array([float(r.score) for r in used]),
                   ta=np.vstack([r.ta for r in used]),
                   ua=np.vstack([r.ua for r in used]),
                   ne=np.vstack([r.nb_emit for r in used]),
                   mass=np.array([r.mass for r in used]),
                   nb=np.asarray(nb, dtype=float), reps=np.asarray(reps, dtype=float))

    def subset(self, keep: np.ndarray) -> "CalibrationSet":
        return self.take(np.flatnonzero(np.asarray(keep, bool)))

    def take(self, idx: np.ndarray) -> "CalibrationSet":
        """Row selection *with* repetition (used by the bootstrap)."""
        idx = np.asarray(idx, dtype=int)
        return CalibrationSet(ids=[self.ids[i] for i in idx], scores=self.scores[idx], ta=self.ta[idx],
                              ua=self.ua[idx], ne=self.ne[idx], mass=self.mass[idx],
                              nb=self.nb, reps=self.reps)

    def predict_all(self, n_truth: float, w: np.ndarray) -> dict:
        z = float(w @ self.nb)
        t = (self.ta @ w) / z
        u = (self.ua @ w) / z
        nu = n_truth * w * float(DISC_COUNT_R) / z
        fp = self.ne @ psi(nu)
        tp = n_truth * t
        den = ALPHA * (tp + fp) + BETA * n_truth
        dti = np.where(den > 0, tp / np.maximum(den, 1e-30), 0.0)
        return {"dti": dti, "tp_frac": t, "u_frac": u, "redundancy": u - t, "fp": fp,
                "nu_mean": (self.ne @ nu) / np.maximum(self.mass, 1e-9)}

    def loss(self, theta: np.ndarray, model: str, lo: np.ndarray, hi: np.ndarray) -> float:
        n_truth = float(np.clip(theta[0], lo[0], hi[0]))
        w = pi_weights(theta[1:], self.reps, model)
        if not np.isfinite(w).all() or (w * self.nb).sum() <= 0:
            return 1e6
        d = self.predict_all(n_truth, w)["dti"] - self.scores
        return float(np.mean(d ** 2))

    def fit(self, model: str, starts: list[np.ndarray] | None = None,
            bounds: tuple[np.ndarray, np.ndarray] = (
                np.array([2_000.0, 0.0, 0.05, 0.0, 0.05, 0.0]),
                np.array([120_000.0, 400.0, 60.0, 400.0, 60.0, 400.0])),
            maxiter: int = 1500) -> dict:
        k = MODEL_PARAMS[model]
        lo, hi = bounds[0][: 1 + k], bounds[1][: 1 + k]
        if starts is None:
            starts = default_starts(k)
        best, best_fun = None, np.inf
        for s in starts:
            s = np.clip(np.asarray(s, dtype=float), lo, hi)
            res = minimize(self.loss, s, args=(model, lo, hi), method="Nelder-Mead",
                           options={"maxiter": maxiter, "maxfev": maxiter * 2, "xatol": 1e-7, "fatol": 1e-14})
            if res.fun < best_fun:
                best, best_fun = res, float(res.fun)
        theta = np.clip(best.x, lo, hi)
        w = pi_weights(theta[1:], self.reps, model)
        pred = self.predict_all(float(theta[0]), w)
        resid = pred["dti"] - self.scores
        return {"model": model, "theta": theta.tolist(), "n_truth": float(theta[0]),
                "pi_params": theta[1:].tolist(), "weights": w.tolist(),
                "z": float(w @ self.nb), "mse": best_fun, "rmse": float(np.sqrt(best_fun)),
                "max_abs_resid": float(np.max(np.abs(resid))),
                "residuals": {i: float(r) for i, r in zip(self.ids, resid)},
                "predicted": {i: float(v) for i, v in zip(self.ids, pred["dti"])},
                "n_artifacts": int(self.scores.size), "converged": bool(best.success),
                "message": str(best.message)}


def default_starts(k: int) -> list[np.ndarray]:
    if k == 0:
        return [np.array([n]) for n in (6_000.0, 9_000.0, 12_500.0, 20_000.0, 35_000.0, 60_000.0)]
    if k == 2:
        return [np.array([n, a, r]) for n in (8_000.0, 12_500.0, 20_000.0, 40_000.0)
                for a in (0.3, 1.0, 4.0, 15.0, 60.0) for r in (0.5, 1.5, 4.0, 12.0)]
    return [np.array([n, a1, r1, a2, r2]) for n in (8_000.0, 12_500.0, 25_000.0)
            for a1, r1 in ((4.0, 1.0), (20.0, 1.0), (2.0, 3.0))
            for a2, r2 in ((1.0, 10.0), (3.0, 25.0), (0.3, 5.0))]


def loo(cal: CalibrationSet, model: str, **kw) -> dict:
    """Leave-one-artefact-out prediction error — the honest test of whether the model transfers."""
    errs = {}
    for i in range(cal.scores.size):
        keep = np.ones(cal.scores.size, bool)
        keep[i] = False
        f = cal.subset(keep).fit(model, **kw)
        w = np.asarray(f["weights"], dtype=float)
        errs[cal.ids[i]] = float(cal.predict_all(f["n_truth"], w)["dti"][i] - cal.scores[i])
    v = np.asarray(list(errs.values()), dtype=float)
    return {"model": model, "loo_rmse": float(np.sqrt(np.mean(v ** 2))),
            "loo_max_abs": float(np.max(np.abs(v))), "loo_errors": errs, "n": int(v.size)}


def bootstrap(cal: CalibrationSet, model: str, draws: int = 200, seed: int = 20261002, **kw) -> dict:
    """Artefact-level bootstrap: how much of the fitted truth model is carried by a few rows."""
    rng = np.random.default_rng(seed)
    starts = default_starts(MODEL_PARAMS[model])[:6]
    rows = []
    n = cal.scores.size
    for _ in range(draws):
        idx = rng.integers(0, n, n)
        if np.unique(idx).size < max(4, n // 2):
            continue
        f = cal.take(idx).fit(model, starts=[starts[0], starts[-1]], **kw)
        rows.append(f["theta"])
    th = np.asarray(rows, dtype=float)
    if th.size == 0:
        return {"model": model, "draws": 0}
    q = np.percentile(th, [2.5, 50.0, 97.5], axis=0)
    return {"model": model, "draws": int(th.shape[0]),
            "ci_low": q[0].tolist(), "ci_median": q[1].tolist(), "ci_high": q[2].tolist()}
