"""Exact feasibility bound for the literal parallel-run dot-overlap rule.

The rule: a candidate is a duplicate-lane if more than 70% of its unique dots lie
within 3 px of a registry raster's dots. For a fixed candidate count K and U
eligible pixels outside the halo, *any* dot set can put at most U dots outside.
Hence the smallest possible in-halo count is max(0, K-U), and the rule can be
met only when ``10*max(0, K-U) <= 7*K``.

This is a **necessary** bound: it ignores spacing, geology and rank correlation,
so passing the arithmetic does not make a candidate unique or good. It is used
only to stop expensive work when no dot set of that size could pass.

Coordinates are raster pixels, matching ``validate_gem_candidate.lane_check``
(100 m pixels, 3 px = 300 m).
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

OVERLAP_CAP = 0.7
RADIUS_PX = 3.0


def _mask(name: str, value) -> np.ndarray:
    arr = np.asarray(value)
    if arr.ndim != 2:
        raise ValueError(f"{name} must be a 2-D raster mask")
    if arr.dtype != bool:
        raise ValueError(f"{name} must be a boolean mask; convert explicitly")
    return arr


def halo_budget(domain, reference, radius_px: float = RADIUS_PX, cap: float = OVERLAP_CAP) -> dict:
    """Count pixels a candidate can place outside a reference raster's halo.

    ``domain`` is the eligible candidate footprint (already excluding visible
    faults); ``reference`` is the registry raster's positive mask. Pixels outside
    ``domain`` cannot host candidate dots and are never counted as uncovered.
    """
    domain = _mask("domain", domain)
    reference = _mask("reference", reference)
    if domain.shape != reference.shape:
        raise ValueError(f"domain {domain.shape} and reference {reference.shape} differ")
    if not np.isfinite(radius_px) or radius_px < 0:
        raise ValueError("radius_px must be finite and non-negative")
    if not 0 <= cap < 1:
        raise ValueError("cap must lie in [0, 1)")
    n_domain = int(domain.sum())
    if n_domain == 0:
        raise ValueError("empty domain: no candidate pixels are eligible")
    # An empty reference has no halo; EDT of an all-True mask would otherwise
    # fall back to a virtual background and invent coverage.
    dist = (distance_transform_edt(~reference) if reference.any()
            else np.full(reference.shape, np.inf))
    in_halo = domain & (dist <= radius_px)
    uncovered = n_domain - int(in_halo.sum())
    # Pass needs in-halo/K <= cap. With cap = num/den exactly, that is
    # den*max(0, K-U) <= num*K. For U < cap*domain the binding case is K > U,
    # giving (den-num)*K <= den*U; otherwise a K <= domain always passes.
    from fractions import Fraction

    frac = Fraction(str(cap)).limit_denominator(1000)
    den, num = frac.denominator, frac.numerator
    max_k = n_domain if den * uncovered >= num * n_domain else (den * uncovered) // (den - num)
    return dict(
        domain_pixels=n_domain,
        reference_pixels=int(reference.sum()),
        covered_domain_pixels=int(in_halo.sum()),
        uncovered_pixels=uncovered,
        coverage_fraction=1.0 - uncovered / n_domain,
        radius_px=float(radius_px),
        overlap_cap=float(cap),
        max_feasible_unique_dots=int(min(n_domain, max_k)),
    )


def rule_can_pass(k: int, uncovered: int, cap: float = OVERLAP_CAP) -> bool:
    """True iff a K-dot candidate is *arithmetically able* to meet the cap."""
    if not isinstance(k, (int, np.integer)) or not isinstance(uncovered, (int, np.integer)):
        raise TypeError("k and uncovered must be integers")
    if k < 0 or uncovered < 0:
        raise ValueError("k and uncovered must be non-negative")
    from fractions import Fraction

    frac = Fraction(str(cap)).limit_denominator(1000)
    outside = max(0, int(k) - int(uncovered))
    return frac.denominator * outside <= frac.numerator * int(k)
