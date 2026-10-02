#!/usr/bin/env python3
"""Why did the dotted H19-5 (owner-reported 0.2477) score best?  Forensics on the real scored rasters.

Reads the pinned scored rasters (``restore_data.py --group scored``) and the organizers' template/labels, and writes
``evidence/why_0_2477.json``. Nothing here is a leaderboard score except where marked OWNER/LEADERBOARD.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.metric import kernel  # noqa: E402
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import check_file  # noqa: E402
from gems25.thinning import dot_thin, neighbour_profile  # noqa: E402

# Owner-reported (task statement 2026-10-02) public scores; LEADERBOARD = row read on the official page 2026-10-02.
SCORES = {
    "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif": (0.1922, "OWNER; leaderboard row smrtdoog5 0.1922 (#28)"),
    "gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif": (0.1894, "OWNER; leaderboard row SDCF9 0.1894 (#30)"),
    "gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif": (0.1855, "OWNER; leaderboard row extradr19 0.1855 (#33)"),
    "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif": (0.2477, "OWNER; leaderboard row wbg1 0.2477 (#16)"),
    "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif": (None, "unscored"),
    "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif": (0.0904, "OWNER (blind lattice probe)"),
    "8GEMSDOE_Hedge-v2_submission.tif": (0.1563, "OWNER; leaderboard row smashi34 0.1563 (#41)"),
    "gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif": (0.1280, "OWNER"),
    "gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif": (0.1839, "OWNER"),
    "gemsdoe-ens12-adopted-7f00890a.tif": (0.1563, "OWNER"),
    "gemsdoe9-PLACEHOLDER-2314b599.tif": (0.0107, "OWNER"),
}


def load(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def main() -> None:
    d = data_dir()
    tmpl = d / "sample_submission.tif"
    foot = np.isfinite(load(tmpl))
    lab = load(d / "labels.tif") == 1
    dcat = distance_transform_edt(~lab)
    sdir = d / "scored"
    out: dict = {"rasters": {}, "relations": {}}
    masks = {}
    for name, (score, src) in SCORES.items():
        p = sdir / name
        if not p.exists():
            continue
        a = load(p)
        m = np.nan_to_num(a, nan=0.0) > 0
        m &= foot
        masks[name] = m
        chk = check_file(p, tmpl)
        n = int(m.sum())
        off = m & ~lab
        dist_e = distance_transform_edt(~m)
        # nearest-neighbour spacing between emitted pixels (excluding self)
        ys, xs = np.nonzero(m)
        sub = np.random.default_rng(0).choice(ys.size, min(ys.size, 20000), replace=False)
        # distance to nearest other emitted pixel: EDT on mask with the pixel removed is costly; use 2nd order stat
        from scipy.spatial import cKDTree
        tree = cKDTree(np.column_stack([ys, xs]))
        dd, _ = tree.query(np.column_stack([ys[sub], xs[sub]]), k=2)
        nn = dd[:, 1]
        out["rasters"][name] = dict(
            score=score, score_source=src, positive_px=n, share_of_footprint=n / foot.sum(),
            on_catalogue_px=int((m & lab).sum()), frac_off_catalogue_within_3px_of_catalogue=float((dcat[off] <= 3).mean()) if off.any() else None,
            binary=bool(set(np.unique(a[np.isfinite(a)])) <= {0.0, 1.0}), neighbour_profile=neighbour_profile(m),
            nn_spacing_px=dict(p10=float(np.percentile(nn, 10)), median=float(np.median(nn)), p90=float(np.percentile(nn, 90)), mean=float(nn.mean())),
            format_ok=chk["ok_to_upload"], nan_inside_footprint=int(np.isnan(a[foot]).sum()), finite_outside=int(np.isfinite(a[~foot]).sum()), sha256=chk["sha256"],
        )
    h = next(k for k in masks if "h19-5" in k and "dotted" not in k)
    d15 = next(k for k in masks if "d1-5" in k)
    d28 = next(k for k in masks if "d2-8" in k)
    out["relations"]["d1_5_is_subset_of_h19_5"] = bool((masks[d15] & ~masks[h]).sum() == 0)
    out["relations"]["d2_8_is_subset_of_h19_5"] = bool((masks[d28] & ~masks[h]).sum() == 0)
    out["relations"]["d1_5_equals_dot_thin(h19_5, 1.5)"] = bool((dot_thin(masks[h], 1.5) == masks[d15]).all())
    out["relations"]["d2_8_equals_dot_thin(h19_5, 2.4)"] = bool((dot_thin(masks[h], 2.4) == masks[d28]).all())
    out["relations"]["pixel_retention_d1_5"] = float(masks[d15].sum() / masks[h].sum())
    out["relations"]["pixel_retention_d2_8"] = float(masks[d28].sum() / masks[h].sum())
    h4 = next(k for k in masks if "h19-4" in k)
    out["relations"]["jaccard_h19_4_h19_5"] = float((masks[h4] & masks[h]).sum() / (masks[h4] | masks[h]).sum())

    # ---- geometric credit retention under truth placed uniformly in the neighbourhood of H19-5's detections
    dH = distance_transform_edt(~masks[h])
    S = (dH < 3) & foot & ~lab
    kH = kernel(dH[S])
    for key, mk in (("d1_5", masks[d15]), ("d2_8", masks[d28])):
        dD = distance_transform_edt(~mk)
        out["relations"][f"geometric_credit_retention_{key}"] = float(kernel(dD[S]).sum() / kH.sum())

    # ---- density calibration from the blind lattice (owner-reported 0.0904)
    lat = next((k for k in masks if "lattice" in k), None)
    if lat:
        m = masks[lat]
        dL = distance_transform_edt(~m)
        pool = foot & ~lab
        mean_credit = float(kernel(dL[pool]).mean())  # E[credit] for a truth pixel placed uniformly off-catalogue
        a = float((m & ~lab).sum() / foot.sum())  # false-positive mass per footprint cell (truth is sparse)
        S0 = 0.0904
        tau = 0.2 * S0 * a / (mean_credit * (1 - 0.2 * S0) - 0.8 * S0)
        out["lattice_calibration"] = dict(emitted_px=int(m.sum()), mean_credit_per_truth_px=mean_credit, fp_mass_per_cell=a,
                                          score_owner_reported=S0, truth_density_per_cell=float(tau),
                                          truth_px_in_footprint=float(tau * foot.sum()), as_pct_of_catalogue=float(tau * foot.sum() / lab.sum()))
        # pooled-subset reading: tau is the density in the *scored subset*, not necessarily the footprint
    # ---- implied credit / FP mass from the two live scores (owner-reported 0.1922 and 0.2477)
    from scipy.optimize import brentq
    D0, D1 = 0.1922, 0.2477
    n0, n1 = int(masks[h].sum()), int(masks[d15].sum())
    rho = out["relations"]["geometric_credit_retention_d1_5"]
    s = n1 / n0

    def g(f, rho=rho):
        c = D0 * (0.2 * f + 0.8) / (1 - 0.2 * D0)
        return rho * c / (0.2 * rho * c + 0.2 * s * f + 0.8) - D1

    try:
        f = brentq(g, 0.01, 500)
        c = D0 * (0.2 * f + 0.8) / (1 - 0.2 * D0)
        out["implied_by_live_scores"] = dict(retention_used=rho, credit_per_truth=c, fp_mass_per_truth=f,
                                             implied_truth_px_if_92pct_of_h19_5_px_are_fp=n0 * 0.92 / f,
                                             break_even_ratio_at_0_2477=0.2 * D1 / (1 - 0.2 * D1))
    except ValueError:
        out["implied_by_live_scores"] = dict(note="no solution for the geometric retention", retention_used=rho)
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence" / "why_0_2477.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    for k, v in out["relations"].items():
        print(f"{k}: {v}")
    print(json.dumps(out.get("lattice_calibration"), indent=1))
    print(json.dumps(out.get("implied_by_live_scores"), indent=1))
    for n, r in out["rasters"].items():
        print(f"{n[:70]:70s} px={r['positive_px']:>7d} fmt_ok={r['format_ok']} nn_med={r['nn_spacing_px']['median']:.2f} 3+nbr={r['neighbour_profile']['three_plus']:.2f} within3px_of_cat={r['frac_off_catalogue_within_3px_of_catalogue']:.3f}")


if __name__ == "__main__":
    main()
