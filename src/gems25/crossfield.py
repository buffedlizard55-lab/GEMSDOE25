"""Catalogue-free transverse RTP / isostatic-gravity gradient signature (CF-1)."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

from .features import nearest_fill


def crossfield(rtp: np.ndarray, gravity: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """min of per-field 90th-percentile-normalized magnitudes times |sin(angle)|.

    A transverse pair is not itself proof of a fault: crossing lithologic contacts can mimic it.
    Only footprint values influence scale; interpolation of missing raw pixels is local.
    """
    if rtp.shape != gravity.shape or rtp.shape != footprint.shape or rtp.ndim != 2:
        raise ValueError("RTP, gravity and footprint must share a 2-D shape")
    if not np.any(footprint):
        raise ValueError("empty footprint")
    vectors = []
    mags = []
    for field in (rtp, gravity):
        filled = nearest_fill(np.asarray(field, np.float32))
        y = gaussian_filter(filled, 2.0, order=(1, 0)).astype(np.float32)
        x = gaussian_filter(filled, 2.0, order=(0, 1)).astype(np.float32)
        mag = np.hypot(y, x)
        scale = float(np.percentile(mag[footprint & np.isfinite(mag)], 90))
        if scale <= 0 or not np.isfinite(scale):
            raise ValueError("degenerate field")
        vectors.append((y / np.maximum(mag, 1e-12), x / np.maximum(mag, 1e-12)))
        mags.append(np.clip(mag / scale, 0.0, 3.0))
    sine = np.abs(vectors[0][0] * vectors[1][1] - vectors[0][1] * vectors[1][0])
    out = np.minimum(mags[0], mags[1]) * sine
    return np.where(footprint, np.nan_to_num(out, nan=0.0, posinf=0.0), 0).astype(np.float32)
