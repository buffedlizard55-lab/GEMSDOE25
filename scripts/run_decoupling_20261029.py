#!/usr/bin/env python3
"""Frozen Experiment 1: magnetic/RTP edge in radiometrically quiet cover.

Never uploads. Fails closed on incomplete registry, leakage or lane duplicates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_gradient_magnitude
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.features import nearest_fill  # noqa: E402
from gems25.holdout import Holdout  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission, sha256_file  # noqa: E402
from scripts.check_lane_surface import audit_surface  # noqa: E402
from scripts.check_lane_duplicates import audit, declared_hashes, registry_rasters, registry_inventory  # noqa: E402
from scripts.holdout_eval import eval_array  # noqa: E402

OUT = ROOT / "evidence" / "decoupling_2026-10-29.json"
TEMPLATE = data_dir() / "sample_submission.tif"
CONTROL = ROOT / "docs/downloads/gems25-h35-resmag-tip-sapd2-4-k3p5-20261025-d5d4cde1e719-zeros.tif"


def main() -> None:
    with rasterio.open(TEMPLATE) as src:
        foot = np.isfinite(src.read(1))
        profile = (src.shape, src.crs, src.transform)
    labels = rasterio.open(data_dir() / "labels.tif").read(1)
    references = registry_rasters()
    expected = declared_hashes()
    inventory = registry_inventory(references, expected)
    if not inventory["complete"]:
        raise RuntimeError("declared registry incomplete; stop before placement")
    rtp = nearest_fill(np.load(work_dir() / "bands/02_rtp.npy", mmap_mode="r"))
    tc = nearest_fill(np.load(work_dir() / "bands/06_tc.npy", mmap_mode="r"))
    mag = gaussian_gradient_magnitude(rtp, 3.0)
    rad = gaussian_gradient_magnitude(tc, 3.0)
    del rtp, tc
    mag = np.clip(mag / max(float(np.percentile(mag[foot], 99)), 1e-9), 0, 3)
    rad = np.clip(rad / max(float(np.percentile(rad[foot], 99)), 1e-9), 0, 3)
    surface = (mag / (1.0 + rad)).astype(np.float32)
    if not np.isfinite(surface[foot]).all():
        raise RuntimeError("nonfinite surface")
    ho = Holdout(foot, labels, hide_frac=.2)
    canaries = {}
    for name, layer in (("rtp_gradient", mag), ("total_count_gradient", rad)):
        aucs = []
        for seed in (140, 141):
            for fold in range(4):
                d = ho.draw(fold, seed)
                valid = d.quadrant & ~d.visible
                y = d.hidden_test[valid].astype(np.uint8)
                if y.min() == y.max():
                    raise RuntimeError("canary has only one class")
                aucs.append(float(roc_auc_score(y, layer[valid])))
        canaries[name] = dict(auc_by_draw=aucs, max_auc=max(aucs), mean_auc=float(np.mean(aucs)))
        if max(aucs) > .90:
            OUT.write_text(json.dumps(dict(verdict="LEAKAGE CANARY - stop", canaries=canaries), indent=2))
            return
    # Full-footprint surface audit before any dot placement.
    surf_audit = audit_surface(surface[foot], foot, profile, references, expected)
    report = dict(preregistration="knowledge/48_preregistered_magnetic_radiometric_decoupling_2026-10-29.md",
                  preregistration_commit="22f8451", evaluator="gems25.metric.dti_binary(alpha=.2,beta=.8,R=3px)",
                  canaries=canaries, surface_audit=surf_audit)
    if not surf_audit["surface_clear"]:
        report["verdict"] = "SURFACE DUPLICATE / REGISTRY INCOMPLETE - stop before placement"
        OUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        return
    def locate(name):
        matches = [p for p in references if name in p.name]
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one {name}: {len(matches)}")
        return rasterio.open(matches[0]).read(1) > 0
    r13 = locate("13gems_20261001_r13-lattice-s5_v2_nan-outside")
    pin = locate("pindrop-v4-nodes-f347b70daa")
    lattice = locate("gems25-unique-latticegap-geothermal-20261028")
    r13hole = foot & (distance_transform_edt(~r13) > 3)
    phalo = distance_transform_edt(~pin) <= 3
    lhalo = distance_transform_edt(~lattice) <= 3
    clear = distance_transform_edt(~((labels > 0) & foot)) > 3
    R2 = r13hole & ~phalo & lhalo & clear
    R5 = foot & ~r13hole & ~phalo & ~lhalo & clear
    def select(region, n):
        indices = np.flatnonzero(region.ravel())
        if len(indices) < n:
            raise RuntimeError(f"only {len(indices)} eligible cells for {n} dots; stop")
        # Stable deterministic tie ordering by pixel index, then decreasing score.
        return indices[np.lexsort((indices, -surface.ravel()[indices]))[:n]]
    pred = np.zeros(foot.shape, np.float32)
    pred.ravel()[select(R2, 2537)] = 1
    pred.ravel()[select(R5, 5600)] = 1
    cid = content_id(pred, foot, labels > 0)
    filename = make_filename("mag-rad-decoupling", "20261029", cid, outside="zero")
    dest = ROOT / "docs/downloads" / filename
    write_submission(pred, TEMPLATE, dest, outside="zero")
    final_audit = audit(dest, TEMPLATE, registry_rasters(), expected)
    fmt = check_file(dest, TEMPLATE)
    report.update(file=str(dest.relative_to(ROOT)), sha256=sha256_file(dest),
                  positive_pixels=int(pred.sum()), final_audit=final_audit, validator=fmt,
                  note=f"GEMSDOE25 mag/rad decoupling | {cid} | research only; DO NOT SUBMIT")
    # Evaluate regardless of a final-dot duplicate: negative evidence is useful, but never promote.
    with rasterio.open(CONTROL) as src:
        ctrl = src.read(1)
    cand = eval_array(ho, pred, "DECPL")
    base = eval_array(ho, ctrl, "CTRL_H35 archive raster")
    from scripts.holdout_eval import pooled
    rng = np.random.default_rng(7)
    diffs = [pooled([cand["draws"][j] for j in idx]) - pooled([base["draws"][j] for j in idx])
             for idx in rng.integers(0, 8, (10000, 8))]
    delta_ci = np.percentile(diffs, [2.5, 97.5]).tolist()
    report["holdout_dti"] = dict(evidence_class="HOLDOUT-DTI", candidate=cand, control=base,
                                paired_gain=cand["pooled_dti"]-base["pooled_dti"],
                                paired_gain_ci95=delta_ci, withheld_positive_occurrences=cand["n_truth_total"])
    report["verdict"] = ("SELECTOR-ELIGIBLE, not submitted" if final_audit["lane_clear"]
                         and fmt["format_valid"] and delta_ci[0] > 0 else "NEGATIVE - DO NOT SUBMIT")
    OUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(verdict=report["verdict"], file=report["file"],
                          candidate_dti=cand["pooled_dti"], control_dti=base["pooled_dti"],
                          gain_ci95=delta_ci, final_lane=final_audit["lane_clear"]), indent=2))


if __name__ == "__main__":
    main()
