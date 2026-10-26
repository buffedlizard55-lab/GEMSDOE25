"""Necessary (not sufficient) literal-overlap gate, independent of any model."""
from fractions import Fraction
from numbers import Integral

import numpy as np
from scipy.ndimage import distance_transform_edt


def capacity_bound(eligible_pixels: int, uncovered_pixels: int, dots: int,
                   overlap_cap: str = '0.70') -> dict:
    """Pigeonhole bound for distinct pixels; use rational strict comparisons."""
    for value in (eligible_pixels, uncovered_pixels, dots):
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise ValueError('counts must be integers')
    n, u, k = int(eligible_pixels), int(uncovered_pixels), int(dots)
    cap = Fraction(overlap_cap)
    if not 0 <= u <= n or not 0 < k <= n or not 0 <= cap < 1:
        raise ValueError('invalid domain, dot count or overlap cap')
    forced = max(0, k-u)
    minimum = Fraction(forced, k)
    maximum = min(n, (u * cap.denominator) // (cap.denominator-cap.numerator))
    return dict(dots=k, forced_overlapping_pixels=forced, minimum_overlap=float(minimum),
                overlap_cap=float(cap), impossible=minimum > cap,
                max_dots_not_ruled_out=maximum,
                status='IMPOSSIBLE' if minimum > cap else 'NOT_RULED_OUT_NOT_APPROVED')


def halo_capacity(footprint: np.ndarray, known: np.ndarray, reference: np.ndarray,
                  radius_px: float = 3.0) -> dict:
    """Exact Euclidean halo using all finite positive reference dots in footprint."""
    foot = np.asarray(footprint, dtype=bool)
    known = np.asarray(known, dtype=bool)
    ref = np.asarray(reference)
    if foot.ndim != 2 or known.shape != foot.shape or ref.shape != foot.shape:
        raise ValueError('matching two-dimensional grids required')
    if not np.isfinite(radius_px) or radius_px < 0:
        raise ValueError('finite nonnegative radius required')
    eligible = foot & ~known
    dots = np.isfinite(ref) & (ref > 0) & foot
    # scipy's EDT on an all-True input does not mean distance to an empty set.
    covered = distance_transform_edt(~dots) <= radius_px if dots.any() else np.zeros(foot.shape, bool)
    n = int(eligible.sum())
    c = int((eligible & covered).sum())
    return dict(eligible_pixels=n, covered_pixels=c, uncovered_pixels=n-c,
                reference_dots=int(dots.sum()), radius_px=float(radius_px))
