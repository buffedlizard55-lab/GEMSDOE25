"""Shared fail-closed feature canaries and pooled, spatial-cluster uncertainty.

These are validation helpers, not a fork of the holdout or submission writer.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score


def feature_canary(values, target, cap=0.90):
    """Audit signed/inverted finite-value AUC AND missingness; no NaN-to-zero bias.

    Constant observed features are uninformative (AUC .5), not automatically
    leaking. Missing classes or wholly missing data cannot pass validation.
    """
    v, y = np.asarray(values, float), np.asarray(target)
    if v.ndim != 1 or y.shape != v.shape or not np.isin(y, [0, 1]).all():
        raise ValueError("aligned one-dimensional values and binary labels required")
    finite = np.isfinite(v)
    counts = {"positives": int((y == 1).sum()), "negatives": int((y == 0).sum()),
              "finite_positives": int(((y == 1) & finite).sum()), "finite_negatives": int(((y == 0) & finite).sum())}
    if not counts["finite_positives"] or not counts["finite_negatives"]:
        return dict(**counts, auc=None, canary_auc=None, missingness_auc=None, passed=False, reason="missing finite class")
    auc = float(roc_auc_score(y[finite], v[finite]))
    missing_auc = float(roc_auc_score(y, ~finite))
    maximum = max(auc, 1-auc, missing_auc, 1-missing_auc)
    return dict(**counts, auc=auc, canary_auc=maximum, missingness_auc=missing_auc,
                passed=bool(maximum <= cap), reason="pass" if maximum <= cap else "presumptive leakage")


def pooled_dti(rows):
    if not rows:
        raise ValueError("no metric rows")
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    n = sum(r["n_truth"] for r in rows)
    if not n:
        raise ValueError("no withheld positives")
    return float(tp / (0.2*(tp+fp) + 0.8*n + 1e-7))


def pooled_summary(rows, candidate="ROD", control="H35", seed=26026, draws=10000):
    """Resample entire quadrants, keeping repeated draws and paired arms together.

    The interval is a percentile cluster-bootstrap, not independent-pixel error.
    Four spatial clusters give low resolution and do not resolve proxy bias.
    """
    arms = sorted({r["arm"] for r in rows})
    folds = sorted({r["fold"] for r in rows})
    if len(folds) < 2 or candidate not in arms or control not in arms:
        raise ValueError("need paired candidate/control and >=2 spatial folds")
    keys = {a: {(r["fold"], r["draw"]) for r in rows if r["arm"] == a} for a in arms}
    if any(len([r for r in rows if r["arm"] == a]) != len(keys[a]) or keys[a] != keys[control] for a in arms):
        raise ValueError("duplicate or unpaired fold/draw rows")
    for key in keys[control]:
        if len({r["n_truth"] for r in rows if (r["fold"], r["draw"]) == key}) != 1:
            raise ValueError("arms have different withheld positives")
    totals = {}
    for a in arms:
        totals[a] = np.array([[sum(r[k] for r in rows if r["arm"] == a and r["fold"] == f)
                               for k in ("tp", "fp", "n_truth")] for f in folds])
    sample = np.random.default_rng(seed).integers(0, len(folds), size=(draws, len(folds)))
    boots, result = {}, {}
    for a in arms:
        t = totals[a][sample].sum(axis=1)
        boots[a] = t[:, 0]/(0.2*(t[:, 0]+t[:, 1])+0.8*t[:, 2]+1e-7)
        result[a] = dict(pooled_dti=pooled_dti([r for r in rows if r["arm"] == a]),
                         ci95=np.quantile(boots[a], [0.025, 0.975]).tolist(),
                         withheld_positive_occurrences=int(totals[a][:, 2].sum()))
    gains = [pooled_dti([r for r in rows if r["arm"] == candidate and r["fold"] == f]) -
             pooled_dti([r for r in rows if r["arm"] == control and r["fold"] == f]) for f in folds]
    delta = result[candidate]["pooled_dti"]-result[control]["pooled_dti"]
    ci = np.quantile(boots[candidate]-boots[control], [0.025, 0.975]).tolist()
    return dict(label="HOLDOUT-DTI", arms=result, paired_gain=delta, paired_ci95=ci, fold_gains=gains,
                screen_passed=bool(delta > .001 and ci[0] > 0 and sum(g > 0 for g in gains) >= 3 and min(gains) >= -.01),
                ci_method=f"quadrant cluster percentile bootstrap; {draws} draws; seed {seed}; {len(folds)} clusters")
