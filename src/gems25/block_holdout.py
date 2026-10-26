"""Checkerboard block-withheld extension of the shared hide-and-recover evaluator.

This module keeps the historical ``gems25.holdout`` evaluator byte-identical for reproducibility while
providing the 25-km diagnostic split described in the H73-BW pre-registration.
"""

from __future__ import annotations

import numpy as np

from .holdout import COLLAR_PX, Draw, Holdout


class BlockHoldout(Holdout):
    """Checkerboard spatial holdout with every component touching a held-out block hidden.

    ``block_size_px=250`` is a 25 km square at the competition's 100 m grid spacing. Blocks are
    anchored to pixel (0, 0) and assigned to four checkerboard folds by the parity of their row/column
    block indices. The inherited 1.5 km collar removes nearby components from training. Unlike
    :class:`gems25.holdout.Holdout`, all catalogue components intersecting a test fold are hidden; the
    20% hide fraction applies only to pseudo-new training components outside the collar.
    """

    FOLD_NAMES = ("block_parity_00", "block_parity_01", "block_parity_10", "block_parity_11")

    def __init__(
        self,
        footprint: np.ndarray,
        labels: np.ndarray,
        hide_frac: float = 0.20,
        block_size_px: int = 250,
    ):
        if isinstance(block_size_px, bool) or int(block_size_px) != block_size_px or block_size_px <= 2 * COLLAR_PX:
            raise ValueError(f"block_size_px must be an integer greater than {2 * COLLAR_PX}")
        super().__init__(footprint, labels, hide_frac)
        self.block_size_px = int(block_size_px)
        height, width = self.footprint.shape
        row_parity = (np.arange(height, dtype=np.int32) // self.block_size_px % 2).astype(np.int8)
        col_parity = (np.arange(width, dtype=np.int32) // self.block_size_px % 2).astype(np.int8)
        self.quad = (2 * row_parity[:, None] + col_parity[None, :]).astype(np.int8, copy=False)
        self.quad[~self.footprint] = -1
        self.block_grid_shape = (
            (height + self.block_size_px - 1) // self.block_size_px,
            (width + self.block_size_px - 1) // self.block_size_px,
        )
        self._collar = {}
        if any(not np.any(self.quad == fold) for fold in range(4)):
            raise ValueError("footprint must intersect blocks from all four checkerboard folds")

    def _pick(self, rng, ids: np.ndarray, target_px: float) -> np.ndarray:
        """Use the shared component sampler, including its required zero-target edge case."""
        if target_px < 0:
            raise ValueError("target_px must be non-negative")
        if ids.size == 0 or target_px == 0:
            return np.empty(0, dtype=ids.dtype)
        return super()._pick(rng, ids, target_px)

    def draw(self, fold: int, seed: int) -> Draw:
        """Hide all test-fold components; sample pseudo-new training components as in ``Holdout``."""
        if fold not in range(4):
            raise ValueError("fold must be one of 0, 1, 2, 3")
        rng = np.random.default_rng(10_000 * (seed + 1) + fold)
        q = self.quad == fold
        collar = self.collar(fold)
        ids = np.arange(1, self.n_comp + 1)
        touch_collar = np.isin(ids, np.unique(self.comp[collar & self.labels]))
        in_test = np.isin(ids, np.unique(self.comp[q & self.labels]))
        test_ids = ids[in_test]
        train_ids = ids[~touch_collar]

        # Hide every component intersecting held-out geography everywhere, including portions that
        # cross block edges. This prevents the adjacent-fragment shortcut in the selector.
        hidden_test = np.isin(self.comp, test_ids) & self.labels
        selected_train = self._pick(
            rng,
            train_ids,
            self.hide_frac * float(self.comp_size[train_ids].sum()),
        )
        hidden_train = np.isin(self.comp, selected_train)
        visible = self.labels & ~hidden_test & ~hidden_train
        rows = np.flatnonzero(q.any(axis=1))
        cols = np.flatnonzero(q.any(axis=0))
        bbox = (slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1))
        return Draw(
            fold=fold,
            seed=seed,
            quadrant=q,
            collar=collar,
            hidden_test=hidden_test & q,
            hidden_train=hidden_train & ~collar,
            visible=visible,
            train_region=self.footprint & ~collar,
            bbox=bbox,
        )
