"""H38 — DTI-exact marginal-credit (greedy submodular) emission + segment matched filter.

Pre-registered in ``knowledge/25`` (committed before any fit). The detector surface is
unchanged (H35 arm B); only the *selection rule* for turning a candidate pool into dots
changes. Under the official metric (``gems25.metric``: triangular kernel ``k(d)``,
R=3 px, credit of a truth pixel = maximum kernel over nearby dots, DTI =
TP/(0.2(TP+FP)+0.8N)), a candidate dot ``x`` is worth adding to a set ``S`` iff
``dTP(x|S) / dFP(x) > alpha*D/(1-alpha*D)`` at the current DTI ``D``
(:func:`gems25.metric.marginal_inclusion_ratio`).

Truth is unknown at emission time, so credit is priced against a plug-in truth
density ``phat`` proportional to the (non-negative) detector score, normalised so
``sum(phat) = Nhat`` over the scored domain (catalogue pixels excluded: staff say
they are masked, so ``phat = 0`` there):

* ``dTP_hat(x|S) = sum_g phat_g * max(0, k(d_xg) - cur_g)`` where ``cur_g`` is the
  current maximum kernel coverage of ``g`` by ``S`` (exact incremental accounting;
  non-increasing in ``S``, i.e. the objective is submodular).
* ``dFP_hat(x) = 1 - E[max_g k(d_xg) * Bern(phat_g)]`` under spatial independence of
  the at most 25 truth pixels inside the kernel support. With neighbours sorted by
  ``k`` descending, ``E[max] = sum_j k_j * p_j * prod_{i<j} (1 - p_i)`` exactly.
  ``dFP_hat`` does not depend on ``S`` (nor does the true per-dot FP).

Selection is lazy greedy on the ratio ``dTP_hat/dFP_hat`` (stale ratios are upper
bounds because ``dTP_hat`` only shrinks), stopping when the best true ratio no
longer exceeds the break-even ``tau(Dhat)`` at the running plug-in DTI. There is no
fixed dot count and no fixed spacing. Deterministic: ties break by raster index.

Named failure mode (knowledge/25): ``phat`` is the detector's own score, so greedy
spending follows the detector's confidence, right or wrong; the independence
approximation understates FP along continuous false lineaments (roads, survey
levelling), where neighbouring truth events are correlated, not independent.
"""

from __future__ import annotations

import heapq

import numpy as np

from .metric import ALPHA, BETA, kernel, marginal_inclusion_ratio

# Kernel offsets sorted by kernel value descending (ties by dy, dx): the order the
# E[max] formula and every neighbourhood gather below assumes.
_OFFS: list[tuple[int, int, float]] = sorted(
    (
        (dy, dx, float(kernel(float(np.hypot(dy, dx)))))
        for dy in range(-3, 4)
        for dx in range(-3, 4)
        if float(kernel(float(np.hypot(dy, dx)))) > 0.0
    ),
    key=lambda t: (-t[2], t[0], t[1]),
)
_KVALS = np.array([k for _, _, k in _OFFS], dtype=np.float64)


def plug_in_density(score: np.ndarray, domain: np.ndarray, known: np.ndarray, n_hat: float) -> np.ndarray:
    """ ``phat`` : score restricted to ``domain & ~known``, scaled to sum to ``n_hat``, clipped to [0, 1]."""
    score = np.asarray(score, dtype=np.float64)
    domain = np.asarray(domain, bool)
    known = np.asarray(known, bool)
    if score.shape != domain.shape or score.shape != known.shape or score.ndim != 2:
        raise ValueError("score/domain/known must be equal-shaped 2-D grids")
    if not np.isfinite(n_hat) or n_hat <= 0:
        raise ValueError("n_hat must be positive and finite")
    w = np.where(domain & ~known, np.clip(np.nan_to_num(score, nan=0.0), 0.0, None), 0.0)
    tot = float(w.sum())
    if tot <= 0:
        raise ValueError("score has no positive mass inside the scored domain")
    return np.clip(w * (float(n_hat) / tot), 0.0, 1.0)


def _neighbour_matrix(field: np.ndarray, cand_flat: np.ndarray, width: int) -> np.ndarray:
    """(n_cand, n_off) values of ``field`` at ``cand + offset`` (0 outside the grid)."""
    H, W = field.shape
    pad = np.zeros((H + 6, W + 6), dtype=np.float64)
    pad[3:-3, 3:-3] = field
    cy, cx = np.divmod(cand_flat, width)
    out = np.empty((cand_flat.size, len(_OFFS)), dtype=np.float64)
    for j, (dy, dx, _) in enumerate(_OFFS):
        out[:, j] = pad[cy + 3 + dy, cx + 3 + dx]
    return out


def expected_fp(phat: np.ndarray, cand_flat: np.ndarray) -> np.ndarray:
    """ ``dFP_hat`` per candidate under the independence approximation (exact neighbour sum)."""
    P = _neighbour_matrix(np.asarray(phat, dtype=np.float64), np.asarray(cand_flat), phat.shape[1])
    # columns are in descending-k order; survivors_j = prod_{i<j} (1 - p_i)
    surv = np.ones_like(P)
    if P.shape[1] > 1:
        surv[:, 1:] = np.cumprod(1.0 - P[:, :-1], axis=1)
    emax = (P * surv * _KVALS[None, :]).sum(axis=1)
    return 1.0 - emax


def _dtp_one(phat_pad: np.ndarray, cur_pad: np.ndarray, y: int, x: int) -> float:
    tot = 0.0
    for dy, dx, k in _OFFS:
        p = phat_pad[y + 3 + dy, x + 3 + dx]
        if p > 0.0:
            gain = k - cur_pad[y + 3 + dy, x + 3 + dx]
            if gain > 0.0:
                tot += p * gain
    return float(tot)


def greedy_dots(
    score: np.ndarray,
    candidates: np.ndarray,
    domain: np.ndarray,
    known: np.ndarray,
    n_hat: float,
    *,
    max_dots: int | None = None,
) -> tuple[np.ndarray, dict]:
    """Lazy-greedy marginal-credit selection from ``candidates`` (knowledge/25, arm A1).

    Returns ``(selected_mask, diagnostics)``. ``candidates`` on catalogue (``known``)
    pixels or outside ``domain`` are never selected.
    """
    score = np.asarray(score, dtype=np.float64)
    candidates = np.asarray(candidates, bool)
    domain = np.asarray(domain, bool)
    known = np.asarray(known, bool)
    if not (score.shape == candidates.shape == domain.shape == known.shape):
        raise ValueError("score/candidates/domain/known must be equal-shaped grids")
    phat = plug_in_density(score, domain, known, n_hat)
    cand = np.flatnonzero((candidates & domain & ~known).ravel())
    out = np.zeros(candidates.shape, bool)
    diag0 = dict(
        n_candidates=int(cand.size), n_selected=0, plugin_tp=0.0, plugin_fp=0.0,
        plugin_dti=0.0, n_hat=float(n_hat), last_accepted_ratio=None, first_rejected_ratio=None,
        stop_reason="empty_candidate_pool",
    )
    if cand.size == 0:
        return out, diag0
    H, W = score.shape
    dfp = expected_fp(phat, cand)
    phat_pad = np.zeros((H + 6, W + 6), dtype=np.float64)
    phat_pad[3:-3, 3:-3] = phat
    cur_pad = np.zeros_like(phat_pad)
    # initial (exact, cur=0) dTP for every candidate, vectorised
    P = _neighbour_matrix(phat, cand, W)
    dtp0 = (P * _KVALS[None, :]).sum(axis=1)
    del P
    eps = 1e-12
    heap: list[tuple[float, int, int]] = []  # (-stale_ratio, flat_idx, cand_position)
    for pos in range(cand.size):
        heap.append((-(dtp0[pos] / max(dfp[pos], eps)), int(cand[pos]), pos))
    heapq.heapify(heap)
    tp_hat = fp_hat = 0.0
    n_sel = 0
    cap = int(cand.size if max_dots is None else min(max_dots, cand.size))
    last_ratio = None
    stop_reason = "pool_exhausted"
    first_rejected = None
    while heap and n_sel < cap:
        neg_ratio, flat, pos = heapq.heappop(heap)
        y, x = divmod(int(flat), W)
        dtp = _dtp_one(phat_pad, cur_pad, int(y), int(x))
        ratio = dtp / max(float(dfp[pos]), eps)
        # lazy check: is this the true argmax? (next stale ratio is an upper bound)
        if heap and ratio < -heap[0][0] - 1e-15:
            heapq.heappush(heap, (-ratio, int(flat), pos))
            continue
        dhat = tp_hat / (ALPHA * (tp_hat + fp_hat) + BETA * float(n_hat)) if (tp_hat + fp_hat) > 0 else 0.0
        tau = marginal_inclusion_ratio(float(dhat), ALPHA)
        if dtp <= 0.0 or ratio <= tau:
            first_rejected = float(ratio)
            stop_reason = "break_even"
            break
        # accept: update coverage field and running plug-in sums
        for dy, dx, k in _OFFS:
            yy, xx = int(y) + 3 + dy, int(x) + 3 + dx
            if k > cur_pad[yy, xx]:
                cur_pad[yy, xx] = k
        tp_hat += dtp
        fp_hat += float(dfp[pos])
        out.ravel()[flat] = True
        n_sel += 1
        last_ratio = float(ratio)
    else:
        if n_sel >= cap and cap < cand.size:
            stop_reason = "max_dots_cap"
    dhat_final = tp_hat / (ALPHA * (tp_hat + fp_hat) + BETA * float(n_hat)) if tp_hat > 0 else 0.0
    diag = dict(
        n_candidates=int(cand.size), n_selected=int(n_sel),
        plugin_tp=float(tp_hat), plugin_fp=float(fp_hat), plugin_dti=float(dhat_final),
        n_hat=float(n_hat), last_accepted_ratio=last_ratio,
        first_rejected_ratio=first_rejected, stop_reason=stop_reason,
    )
    return out, diag


def greedy_dots_bruteforce(
    score: np.ndarray,
    candidates: np.ndarray,
    domain: np.ndarray,
    known: np.ndarray,
    n_hat: float,
    *,
    max_dots: int | None = None,
) -> tuple[np.ndarray, dict]:
    """Reference implementation: recompute every candidate's ratio at every step (tests only)."""
    score = np.asarray(score, dtype=np.float64)
    candidates = np.asarray(candidates, bool)
    domain = np.asarray(domain, bool)
    known = np.asarray(known, bool)
    phat = plug_in_density(score, domain, known, n_hat)
    cand = np.flatnonzero((candidates & domain & ~known).ravel())
    out = np.zeros(candidates.shape, bool)
    if cand.size == 0:
        return out, dict(n_candidates=0, n_selected=0, plugin_tp=0.0, plugin_fp=0.0, plugin_dti=0.0)
    H, W = score.shape
    dfp = expected_fp(phat, cand)
    phat_pad = np.zeros((H + 6, W + 6), dtype=np.float64)
    phat_pad[3:-3, 3:-3] = phat
    cur_pad = np.zeros_like(phat_pad)
    alive = np.ones(cand.size, bool)
    tp_hat = fp_hat = 0.0
    n_sel = 0
    cap = int(cand.size if max_dots is None else min(max_dots, cand.size))
    eps = 1e-12
    while n_sel < cap and alive.any():
        best_pos, best_ratio, best_dtp = -1, -np.inf, 0.0
        for pos in np.flatnonzero(alive):
            y, x = divmod(int(cand[pos]), W)
            dtp = _dtp_one(phat_pad, cur_pad, int(y), int(x))
            ratio = dtp / max(float(dfp[pos]), eps)
            if ratio > best_ratio + 1e-15:  # ties: lowest raster index wins (cand is sorted)
                best_pos, best_ratio, best_dtp = int(pos), float(ratio), dtp
        dhat = tp_hat / (ALPHA * (tp_hat + fp_hat) + BETA * float(n_hat)) if (tp_hat + fp_hat) > 0 else 0.0
        if best_dtp <= 0.0 or best_ratio <= marginal_inclusion_ratio(float(dhat), ALPHA):
            break
        y, x = divmod(int(cand[best_pos]), W)
        for dy, dx, k in _OFFS:
            yy, xx = int(y) + 3 + dy, int(x) + 3 + dx
            if k > cur_pad[yy, xx]:
                cur_pad[yy, xx] = k
        tp_hat += best_dtp
        fp_hat += float(dfp[best_pos])
        out.ravel()[cand[best_pos]] = True
        alive[best_pos] = False
        n_sel += 1
    dhat_final = tp_hat / (ALPHA * (tp_hat + fp_hat) + BETA * float(n_hat)) if tp_hat > 0 else 0.0
    return out, dict(
        n_candidates=int(cand.size), n_selected=int(n_sel),
        plugin_tp=float(tp_hat), plugin_fp=float(fp_hat), plugin_dti=float(dhat_final),
    )


def line_max_mean(score: np.ndarray, valid: np.ndarray, length: int = 15, n_orient: int = 8) -> np.ndarray:
    """Segment matched filter (knowledge/25, arm A3): per pixel, the maximum over
    ``n_orient`` orientations of the mean score along a centred ``length``-px segment.

    Means divide by the number of *valid* samples on the segment; pixels whose every
    segment has no valid sample get 0. Deterministic; offsets are nearest-pixel samples
    along each orientation's unit vector with consecutive duplicates removed.
    """
    score = np.asarray(score, dtype=np.float64)
    valid = np.asarray(valid, bool)
    if score.shape != valid.shape or score.ndim != 2:
        raise ValueError("score/valid must be equal-shaped 2-D grids")
    if length < 1 or length % 2 == 0 or n_orient < 1:
        raise ValueError("length must be a positive odd number and n_orient >= 1")
    half = length // 2
    s = np.where(valid, np.nan_to_num(score, nan=0.0), 0.0)
    H, W = s.shape
    pad_s = np.zeros((H + 2 * half, W + 2 * half), dtype=np.float64)
    pad_v = np.zeros_like(pad_s)
    pad_s[half:-half, half:-half] = s
    pad_v[half:-half, half:-half] = valid.astype(np.float64)
    best = np.zeros((H, W), dtype=np.float64)
    for oi in range(n_orient):
        ang = np.pi * oi / n_orient
        uy, ux = np.sin(ang), np.cos(ang)
        offs: list[tuple[int, int]] = []
        for t in range(-half, half + 1):
            o = (int(round(t * uy)), int(round(t * ux)))
            if not offs or offs[-1] != o:
                offs.append(o)
        acc = np.zeros((H, W), dtype=np.float64)
        cnt = np.zeros((H, W), dtype=np.float64)
        for dy, dx in offs:
            acc += pad_s[half + dy: half + dy + H, half + dx: half + dx + W]
            cnt += pad_v[half + dy: half + dy + H, half + dx: half + dx + W]
        mean = np.where(cnt > 0, acc / np.maximum(cnt, 1.0), 0.0)
        best = np.maximum(best, mean)
    return best.astype(np.float32)
