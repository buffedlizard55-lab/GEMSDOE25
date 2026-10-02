"""Two-level fractional factorial designs (Box, Hunter & Hunter, *Statistics for Experimenters*).

* ``design(k, generators)``  - 2^(k-p) design from generators such as ``{"E": "ABCD"}``.
* ``alias_structure``        - defining-contrast subgroup, resolution, aliases of every main effect / 2fi.
* ``estimate_effects``       - all main effects and two-factor interactions by contrasts.
* ``lenth``                  - Lenth (1989) pseudo standard error, margin of error (ME) and simultaneous
                               margin of error (SME) for unreplicated designs.
* ``fold_effects``           - effects per block/fold, giving an empirical standard error.

Sparsity of effects: only a few main effects and low-order interactions are expected to be active, so a
Resolution V half fraction (16 runs for 5 factors) estimates all 5 main effects and all 10 two-factor
interactions clear of one another (each two-factor interaction is aliased only with a three-factor one).
"""

from __future__ import annotations

from itertools import combinations
from string import ascii_uppercase

import numpy as np
from scipy import stats


def design(k: int, generators: dict[str, str] | None = None) -> dict:
    """Return the +/-1 design matrix and metadata for a 2^(k-p) design.

    Factors are named A, B, C ... The first ``k - p`` letters not listed in ``generators`` form a full
    factorial in standard (Yates) order with A varying fastest... reversed to the conventional layout where
    the last base factor varies fastest, matching the textbook tables.
    """
    generators = generators or {}
    names = list(ascii_uppercase[:k])
    base = [n for n in names if n not in generators]
    nb = len(base)
    n = 2**nb
    cols: dict[str, np.ndarray] = {}
    for j, b in enumerate(base):
        cols[b] = np.where((np.arange(n) >> (nb - 1 - j)) & 1, 1, -1).astype(int)
    for g, word in generators.items():
        c = np.ones(n, int)
        for ch in word:
            c = c * cols[ch]
        cols[g] = c
    X = np.column_stack([cols[nm] for nm in names])
    return dict(names=names, X=X, runs=n, generators=dict(generators), base=base)


def _word_mult(a: str, b: str) -> str:
    return "".join(sorted(set(a) ^ set(b)))


def alias_structure(k: int, generators: dict[str, str]) -> dict:
    """Defining contrast subgroup, resolution and aliases of every main effect and 2fi (up to 3fi)."""
    words = [g + w for g, w in generators.items()]  # e.g. 'E' + 'ABCD' -> 'EABCD'
    words = ["".join(sorted(w)) for w in words]
    group = set(words)
    changed = True
    while changed:  # close under multiplication (symmetric difference of letters)
        changed = False
        for a, b in list(combinations(sorted(group), 2)):
            w = _word_mult(a, b)
            if w and w not in group:
                group.add(w)
                changed = True
    group = sorted(group, key=lambda w: (len(w), w))
    resolution = min(len(w) for w in group) if group else None
    names = list(ascii_uppercase[:k])
    effects = ["".join(c) for r in (1, 2) for c in combinations(names, r)]
    aliases = {}
    for e in effects:
        al = sorted({_word_mult(e, w) for w in group if _word_mult(e, w)} - {e}, key=lambda x: (len(x), x))
        aliases[e] = [a for a in al if len(a) <= 4]
    return dict(defining_relation=["I=" + w for w in group], resolution=resolution, aliases=aliases)


def contrasts(X: np.ndarray, names: list[str], order: int = 2) -> dict[str, np.ndarray]:
    out = {}
    for r in range(1, order + 1):
        for comb in combinations(range(len(names)), r):
            out["".join(names[i] for i in comb)] = np.prod(X[:, list(comb)], axis=1)
    return out


def estimate_effects(X: np.ndarray, y: np.ndarray, names: list[str], order: int = 2) -> dict[str, float]:
    """Effect = mean(y | contrast = +1) - mean(y | contrast = -1)."""
    y = np.asarray(y, float)
    out = {}
    for lab, c in contrasts(X, names, order).items():
        out[lab] = float(y[c > 0].mean() - y[c < 0].mean())
    return out


def lenth(effects: dict[str, float], alpha: float = 0.05) -> dict:
    """Lenth's PSE, ME and SME (unreplicated two-level designs)."""
    labs = list(effects)
    c = np.array([effects[k] for k in labs], float)
    m = c.size
    s0 = 1.5 * np.median(np.abs(c))
    keep = np.abs(c) < 2.5 * s0
    pse = 1.5 * np.median(np.abs(c[keep])) if keep.any() else s0
    d = m / 3.0
    me = float(stats.t.ppf(1 - alpha / 2, d) * pse)
    gamma = (1 + (1 - alpha) ** (1.0 / m)) / 2
    sme = float(stats.t.ppf(gamma, d) * pse)
    return dict(pse=float(pse), me=me, sme=sme, d=d, m=m, s0=float(s0))


def fold_effects(X: np.ndarray, Y: np.ndarray, names: list[str], order: int = 2) -> dict:
    """``Y`` has shape (runs, n_blocks). Effects per block + mean, SE and t over blocks."""
    per = [estimate_effects(X, Y[:, j], names, order) for j in range(Y.shape[1])]
    labs = list(per[0])
    arr = np.array([[p[k] for k in labs] for p in per])  # (blocks, effects)
    nb = arr.shape[0]
    mean = arr.mean(0)
    se = arr.std(0, ddof=1) / np.sqrt(nb) if nb > 1 else np.full_like(mean, np.nan)
    t = np.divide(mean, se, out=np.full_like(mean, np.nan), where=se > 0)
    pos = (arr > 0).sum(0)
    return {
        k: dict(mean=float(mean[i]), se=float(se[i]), t=float(t[i]), blocks_positive=int(pos[i]), n_blocks=nb,
                per_block=[float(v) for v in arr[:, i]])
        for i, k in enumerate(labs)
    }
