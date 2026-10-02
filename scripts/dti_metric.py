"""
Distance-weighted Tversky Index (DTI) for the GEMS Prize Challenge.

Official metric definition:
    DTI(α=0.2, β=0.8) = TP_w / (TP_w + α·FP_w + β·FN_w)

where TP_w, FP_w, FN_w are distance-weighted using a triangular kernel
k(d) = max(1 - d/R, 0) with R = 300m (3 pixels at 100m resolution).

Reference: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric
"""

import numpy as np
from scipy import ndimage


def compute_dti(
    prediction: np.ndarray,
    truth: np.ndarray,
    alpha: float = 0.2,
    beta: float = 0.8,
    radius_px: int = 3,
    epsilon: float = 1e-10,
) -> dict:
    """
    Compute the distance-weighted Tversky Index.

    Parameters
    ----------
    prediction : np.ndarray
        2D array of predicted probabilities in [0, 1].
    truth : np.ndarray
        2D binary array (0/1) of ground truth fault locations.
    alpha : float
        False positive penalty weight (default 0.2 per competition).
    beta : float
        False negative penalty weight (default 0.8 per competition).
    radius_px : int
        Kernel support radius in pixels (default 3 = 300m at 100m/px).
    epsilon : float
        Smoothing term to avoid division by zero.

    Returns
    -------
    dict with keys: dti, tp_w, fp_w, fn_w
    """
    assert prediction.shape == truth.shape, "Shape mismatch"
    assert prediction.ndim == 2, "Must be 2D"

    # Build the triangular kernel
    kernel_size = 2 * radius_px + 1
    y_grid, x_grid = np.mgrid[-radius_px:radius_px + 1, -radius_px:radius_px + 1]
    distances = np.sqrt(y_grid**2 + x_grid**2)
    kernel = np.maximum(1.0 - distances / (radius_px + 0.5), 0.0)

    # Get coordinates of true positives
    truth_coords = np.argwhere(truth > 0)  # (N_truth, 2)
    pred_mask = prediction > 0

    # --- TP_w ---
    # For each truth pixel g, sum p(x) * k(d(x,g)) over x within R
    tp_w = 0.0
    if len(truth_coords) > 0:
        for gy, gx in truth_coords:
            # Extract local window around this truth pixel
            y_lo = max(0, gy - radius_px)
            y_hi = min(prediction.shape[0], gy + radius_px + 1)
            x_lo = max(0, gx - radius_px)
            x_hi = min(prediction.shape[1], gx + radius_px + 1)

            # Corresponding kernel slice
            ky_lo = y_lo - (gy - radius_px)
            ky_hi = kernel_size - ((gy + radius_px + 1) - y_hi)
            kx_lo = x_lo - (gx - radius_px)
            kx_hi = kernel_size - ((gx + radius_px + 1) - x_hi)

            local_pred = prediction[y_lo:y_hi, x_lo:x_hi]
            local_kernel = kernel[ky_lo:ky_hi, kx_lo:kx_hi]
            tp_w += np.sum(local_pred * local_kernel)

    # --- FP_w ---
    # For each predicted pixel x where p(x) > 0:
    # FP contribution = p(x) * [1 - max_{g in G} k(d(x,g))]
    fp_w = 0.0
    if len(truth_coords) > 0:
        # Build distance transform from truth: for each pixel, distance to nearest truth
        truth_binary = (truth > 0).astype(np.float32)
        dist_to_truth = ndimage.distance_transform_edt(1 - truth_binary)

        # For pixels within radius, compute kernel credit
        # max kernel credit = max over truth pixels of k(d(x,g))
        # = k(dist_to_truth(x)) when dist <= radius
        max_kernel_credit = np.zeros_like(prediction)
        within_radius = dist_to_truth <= radius_px + 0.5
        max_kernel_credit[within_radius] = np.maximum(
            1.0 - dist_to_truth[within_radius] / (radius_px + 0.5), 0.0
        )

        pred_pixels = pred_mask.astype(np.float32)
        fp_w = np.sum(prediction * pred_pixels * (1.0 - max_kernel_credit))
    else:
        fp_w = np.sum(prediction)

    # --- FN_w ---
    # For each truth pixel g:
    # FN contribution = 1 - max_{x: d(x,g)<=R} p(x) * k(d(x,g))
    fn_w = 0.0
    if len(truth_coords) > 0:
        # For each truth pixel, find max weighted prediction within radius
        for gy, gx in truth_coords:
            y_lo = max(0, gy - radius_px)
            y_hi = min(prediction.shape[0], gy + radius_px + 1)
            x_lo = max(0, gx - radius_px)
            x_hi = min(prediction.shape[1], gx + radius_px + 1)

            ky_lo = y_lo - (gy - radius_px)
            ky_hi = kernel_size - ((gy + radius_px + 1) - y_hi)
            kx_lo = x_lo - (gx - radius_px)
            kx_hi = kernel_size - ((gx + radius_px + 1) - x_hi)

            local_pred = prediction[y_lo:y_hi, x_lo:x_hi]
            local_kernel = kernel[ky_lo:ky_hi, kx_lo:kx_hi]
            max_weighted = np.max(local_pred * local_kernel)
            fn_w += (1.0 - max_weighted)
    else:
        fn_w = float(np.sum(truth > 0))

    # --- DTI ---
    dti = tp_w / (tp_w + alpha * fp_w + beta * fn_w + epsilon)

    return {
        "dti": float(dti),
        "tp_w": float(tp_w),
        "fp_w": float(fp_w),
        "fn_w": float(fn_w),
    }


def compute_dti_fast(
    prediction: np.ndarray,
    truth: np.ndarray,
    alpha: float = 0.2,
    beta: float = 0.8,
    radius_px: int = 3,
    epsilon: float = 1e-10,
) -> dict:
    """
    Fast approximate DTI using distance transforms (vectorized).
    Slightly different from exact computation for large radii but
    much faster for full-image scoring.
    """
    truth_binary = (truth > 0).astype(np.float32)
    pred_binary = (prediction > 0).astype(np.float32)

    # Distance to nearest truth pixel
    dist_to_truth = ndimage.distance_transform_edt(1 - truth_binary)

    # Kernel credit for each pixel
    max_kernel = np.zeros_like(prediction)
    within = dist_to_truth <= radius_px + 0.5
    max_kernel[within] = np.maximum(1.0 - dist_to_truth[within] / (radius_px + 0.5), 0.0)

    # TP_w: for each truth pixel, the weighted prediction within radius
    # Approximation: sum over truth pixels of their local max weighted prediction
    # Use dilation to find max prediction within kernel radius for each truth pixel
    from scipy.ndimage import maximum_filter
    weighted_pred = prediction * max_kernel
    max_within_radius = maximum_filter(weighted_pred, size=2 * radius_px + 1)
    tp_w = np.sum(max_within_radius * truth_binary)

    # FP_w: sum of p(x) * (1 - max_kernel(x)) for predicted pixels
    fp_w = np.sum(prediction * pred_binary * (1.0 - max_kernel))

    # FN_w: for each truth pixel, 1 - max weighted prediction
    fn_w = np.sum(truth_binary * (1.0 - max_within_radius))

    dti = tp_w / (tp_w + alpha * fp_w + beta * fn_w + epsilon)

    return {
        "dti": float(dti),
        "tp_w": float(tp_w),
        "fp_w": float(fp_w),
        "fn_w": float(fn_w),
    }


if __name__ == "__main__":
    # Quick sanity check matching the competition's scoring example
    # Vertical line of truth, specific prediction pattern
    truth = np.zeros((10, 10))
    truth[2:8, 5] = 1  # vertical line

    pred = np.zeros((10, 10))
    pred[3:7, 5] = 1.0  # correct predictions
    pred[4, 7] = 0.8    # false positive at distance 2

    result = compute_dti(pred, truth)
    print(f"DTI = {result['dti']:.4f}")
    print(f"TP_w = {result['tp_w']:.4f}, FP_w = {result['fp_w']:.4f}, FN_w = {result['fn_w']:.4f}")
