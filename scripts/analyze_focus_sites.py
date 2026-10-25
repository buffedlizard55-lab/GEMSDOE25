#!/usr/bin/env python3
"""Forensic pixel-by-pixel audit of the 9 focus sites (GEMSDOE24..36) and why GEMSDOE32 H33-2-B2 scored 0.2778.

Fetches the published candidate GeoTIFFs from the owner's public GitHub repositories via bare git blob
retrieval (no DrivenData contact) and computes:
1. SHA-256, positive pixel count, value range, and distance-to-catalogue distribution;
2. exact pixel-subset / superset identities across H19-5 -> D1.5 -> D2.8 -> R1 -> B2 -> G36;
3. exact DTI denominator/numerator inversion on the nested chain under the official metric
   DTI = TP_w / (0.2*(TP_w + FP_w) + 0.8*|G|).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.metric import marginal_inclusion_ratio  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402

FOCUS_TARGETS = [
    {
        "site": "19GEMSDOE",
        "id": "h19-5-parent",
        "label": "h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "inputs/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
        "reported_score": 0.1922,
        "site_url": "https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html",
    },
    {
        "site": "GEMSDOE24",
        "id": "gems24-d1-5",
        "label": "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan",
        "repo": "buffedlizard55-lab/GEMSDOE24",
        "ref": "07345ea0604953d7efb858d9cfbc21e20c7aca0b",
        "path": "docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        "reported_score": 0.2477,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE24/",
    },
    {
        "site": "GEMSDOE25",
        "id": "gems25-d2-8",
        "label": "dotted-h19-5-d2-8-20261002-e56ea318af89-nan",
        "repo": "local",
        "ref": "HEAD",
        "path": "docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
        "reported_score": 0.2600,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE25/",
    },
    {
        "site": "GEMSDOE27",
        "id": "gems27-topo-gap-t-v2",
        "label": "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan",
        "repo": "buffedlizard55-lab/GEMSDOE27",
        "ref": "HEAD",
        "path": "docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
        "reported_score": 0.2449,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE27/",
    },
    {
        "site": "GEMSDOE28",
        "id": "gems28-h27-4-r1-solo",
        "label": "h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan",
        "repo": "buffedlizard55-lab/GEMSDOE28",
        "ref": "HEAD",
        "path": "docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
        "reported_score": 0.2708,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
    },
    {
        "site": "GEMSDOE28",
        "id": "gems28-h32-1-prethin",
        "label": "h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan",
        "repo": "buffedlizard55-lab/GEMSDOE28",
        "ref": "HEAD",
        "path": "docs/downloads/gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif",
        "reported_score": 0.2649,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
    },
    {
        "site": "GEMSDOE28",
        "id": "gems28-h36-1-rung30",
        "label": "h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan",
        "repo": "buffedlizard55-lab/GEMSDOE28",
        "ref": "HEAD",
        "path": "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        "reported_score": 0.2710,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
    },
    {
        "site": "GEMSDOE28",
        "id": "gems28-h38-1-hf-euler",
        "label": "h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan",
        "repo": "buffedlizard55-lab/GEMSDOE28",
        "ref": "HEAD",
        "path": "docs/downloads/gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif",
        "reported_score": 0.2707,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE28/",
    },
    {
        "site": "GEMSDOE30",
        "id": "gems30-d28-poisson300m",
        "label": "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca",
        "repo": "buffedlizard55-lab/GEMSDOE30",
        "ref": "HEAD",
        "path": "docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca-nanoutside.tif",
        "reported_score": 0.2600,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE30/",
    },
    {
        "site": "GEMSDOE31",
        "id": "gems31-h27-4-solo-d28",
        "label": "h27-4-solo-d28-20261004-8acb75e1-nan",
        "repo": "buffedlizard55-lab/GEMSDOE31",
        "ref": "HEAD",
        "path": "docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
        "reported_score": 0.2708,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE31/docs/",
    },
    {
        "site": "GEMSDOE32",
        "id": "gems32-h33-2-b2-zeros",
        "label": "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros",
        "repo": "buffedlizard55-lab/GEMSDOE32",
        "ref": "HEAD",
        "path": "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "reported_score": 0.2778,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html",
    },
    {
        "site": "GEMSDOE33",
        "id": "gems33-h33d-analog-tip",
        "label": "h33d-analog-tip-stepover-r30-20261004-cb490425926e",
        "repo": "buffedlizard55-lab/GEMSDOE33",
        "ref": "HEAD",
        "path": "docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e-nanoutside.tif",
        "reported_score": 0.2632,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE33/",
    },
    {
        "site": "GEMSDOE36",
        "id": "gems36-anderson-pinn",
        "label": "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros",
        "repo": "buffedlizard55-lab/GEMSDOE36",
        "ref": "HEAD",
        "path": "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "reported_score": 0.2750,
        "site_url": "https://buffedlizard55-lab.github.io/GEMSDOE36/docs/",
    },
]


def fetch_focus_tif(entry: dict, dest_dir: Path) -> Path:
    dest = dest_dir / f"{entry['id']}.tif"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    if entry["repo"] == "local":
        dest.write_bytes((ROOT / entry["path"]).read_bytes())
        return dest
    short_repo = entry["repo"].split("/")[-1]
    git_dir = data_dir() / "raw" / "_sibling_git" / short_repo
    if not (git_dir / "HEAD").exists():
        git_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "--bare", "-q"], cwd=git_dir, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", f"https://github.com/{entry['repo']}.git"],
            cwd=git_dir,
            check=True,
        )
    subprocess.run(
        ["git", "fetch", "-q", "--depth=1", "--filter=blob:none", "origin", entry["ref"]],
        cwd=git_dir,
        check=True,
    )
    with dest.open("wb") as out:
        subprocess.run(["git", "show", f"FETCH_HEAD:{entry['path']}"], cwd=git_dir, stdout=out, check=True)
    return dest


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    w = work_dir()
    foot = np.load(w / "bands" / "_footprint.npy")
    lab = np.load(w / "bands" / "_labels.npy")
    dist_cat = distance_transform_edt(~(lab & foot))

    dest_dir = data_dir() / "sibling_focus"
    dest_dir.mkdir(parents=True, exist_ok=True)

    masks: dict[str, np.ndarray] = {}
    rows: list[dict] = []

    for entry in FOCUS_TARGETS:
        p = fetch_focus_tif(entry, dest_dir)
        sha = sha256_file(p)
        with rasterio.open(p) as s:
            arr = s.read(1)
        pos = (arr > 0) & np.isfinite(arr) & foot
        masks[entry["id"]] = pos
        dc = dist_cat[pos]
        shells = {
            "d_eq_0_on_catalogue": int((pos & lab).sum()),
            "d_in_0_1px": int((pos & (dist_cat > 0.0) & (dist_cat <= 1.0)).sum()),
            "d_in_1_2px": int((pos & (dist_cat > 1.0) & (dist_cat <= 2.0)).sum()),
            "d_in_2_3px": int((pos & (dist_cat > 2.0) & (dist_cat <= 3.0)).sum()),
            "d_gt_3px": int((pos & (dist_cat > 3.0)).sum()),
        }
        rows.append(
            {
                "site": entry["site"],
                "id": entry["id"],
                "label": entry["label"],
                "site_url": entry["site_url"],
                "repo": entry["repo"],
                "path": entry["path"],
                "sha256": sha,
                "bytes": p.stat().st_size,
                "owner_reported_score": entry["reported_score"],
                "evidence_class": "owner/user-reported claim (bytes hash-verified locally; score not organizer-confirmed)",
                "emitted_pixels": int(pos.sum()),
                "min_dist_to_catalogue_px": float(dc.min()) if dc.size else None,
                "p5_dist_to_catalogue_px": float(np.percentile(dc, 5)) if dc.size else None,
                "median_dist_to_catalogue_px": float(np.median(dc)) if dc.size else None,
                "distance_shells_px": shells,
                "break_even_marginal_ratio_tau": float(marginal_inclusion_ratio(entry["reported_score"])),
            }
        )

    d28 = masks["gems25-d2-8"]
    r1 = masks["gems28-h27-4-r1-solo"]
    b2 = masks["gems32-h33-2-b2-zeros"]
    g36 = masks["gems36-anderson-pinn"]
    g30 = masks["gems30-d28-poisson300m"]
    g31 = masks["gems31-h27-4-solo-d28"]
    h36 = masks["gems28-h36-1-rung30"]
    h38 = masks["gems28-h38-1-hf-euler"]

    identities = {
        "gems25_d28_equals_gems30_d28_on_footprint": bool(np.array_equal(d28, g30)),
        "gems28_r1_equals_gems31_r1_on_footprint": bool(np.array_equal(r1, g31)),
        "gems28_r1_is_exact_d28_with_dist_cat_gt_1px": bool(np.array_equal(d28 & (dist_cat > 1.0), r1)),
        "gems32_b2_is_exact_d28_with_dist_cat_gt_2px": bool(np.array_equal(d28 & (dist_cat > 2.0), b2)),
        "gems32_b2_is_strict_subset_of_gems36_anderson_pinn": bool(int((b2 & ~g36).sum()) == 0),
        "gems36_extra_pixels_over_gems32_b2": int((g36 & ~b2).sum()),
        "gems28_h38_is_strict_superset_of_gems28_h36": bool(int((h36 & ~h38).sum()) == 0),
        "gems28_h38_extra_pixels_over_gems28_h36": int((h38 & ~h36).sum()),
    }
    assert all(
        identities[k]
        for k in (
            "gems25_d28_equals_gems30_d28_on_footprint",
            "gems28_r1_equals_gems31_r1_on_footprint",
            "gems28_r1_is_exact_d28_with_dist_cat_gt_1px",
            "gems32_b2_is_exact_d28_with_dist_cat_gt_2px",
            "gems32_b2_is_strict_subset_of_gems36_anderson_pinn",
        )
    ), f"unexpected pixel identity failure: {identities}"

    # Zero-credit deletion/addition check under N_G = 12,691 (H28 calibrated truth count)
    n_g = 12691.0
    m_d28, s_d28 = 44090.0, 0.2600
    m_r1, s_r1 = 40199.0, 0.2708
    m_b2, s_b2 = 37654.0, 0.2778
    m_g36, s_g36 = 38854.0, 0.2750

    tp_d28 = s_d28 * (0.2 * m_d28 + 0.8 * n_g) / (1.0 - 0.04 * s_d28)
    denom_d28 = tp_d28 / s_d28
    pred_r1_zero_loss = tp_d28 / (denom_d28 - 0.2 * (m_d28 - m_r1))
    pred_b2_zero_loss = tp_d28 / (denom_d28 - 0.2 * (m_d28 - m_b2))

    tp_r1 = s_r1 * (0.2 * m_r1 + 0.8 * n_g) / (1.0 - 0.04 * s_r1)
    tp_b2 = s_b2 * (0.2 * m_b2 + 0.8 * n_g) / (1.0 - 0.04 * s_b2)
    tp_g36 = s_g36 * (0.2 * m_g36 + 0.8 * n_g) / (1.0 - 0.04 * s_g36)

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "scripts/analyze_focus_sites.py",
        "evidence_boundary": (
            "All GeoTIFF bytes and SHA-256 digests were verified locally from the owner's public GitHub repositories. "
            "All competition DTI values (0.1922, 0.2477, 0.2600, 0.2708, 0.2778, 0.2750, 0.3195, 0.4413) are "
            "user/owner-reported claims, not organizer-confirmed receipts."
        ),
        "focus_artifacts": rows,
        "pixel_identities_verified": identities,
        "nested_chain_inversion_conditional_on_reported_scores": {
            "assumed_hidden_truth_px_n_g": n_g,
            "d28_to_r1_delete_0_1px_collar": {
                "deleted_pixels": int(m_d28 - m_r1),
                "reported_dti_before": s_d28,
                "reported_dti_after": s_r1,
                "predicted_dti_if_zero_credit_lost": float(pred_r1_zero_loss),
                "implied_credit_lost_tp_units": float(tp_d28 - tp_r1),
                "implied_credit_per_deleted_px": float((tp_d28 - tp_r1) / (m_d28 - m_r1)),
                "break_even_tau_at_0_2600": float(marginal_inclusion_ratio(s_d28)),
            },
            "r1_to_b2_delete_1_2px_collar": {
                "deleted_pixels": int(m_r1 - m_b2),
                "reported_dti_before": s_r1,
                "reported_dti_after": s_b2,
                "predicted_dti_if_zero_credit_lost_from_d28": float(pred_b2_zero_loss),
                "implied_credit_lost_tp_units": float(tp_r1 - tp_b2),
                "implied_credit_per_deleted_px": float((tp_r1 - tp_b2) / (m_r1 - m_b2)),
                "break_even_tau_at_0_2708": float(marginal_inclusion_ratio(s_r1)),
            },
            "b2_to_g36_add_1200_anderson_pinn_dots": {
                "added_pixels": int(m_g36 - m_b2),
                "reported_dti_before": s_b2,
                "reported_dti_after": s_g36,
                "implied_credit_gained_tp_units": float(tp_g36 - tp_b2),
                "implied_credit_per_added_px": float((tp_g36 - tp_b2) / (m_g36 - m_b2)),
                "break_even_tau_at_0_2778": float(marginal_inclusion_ratio(s_b2)),
            },
        },
    }
    out_path = ROOT / "evidence" / "focus_sites_forensics.json"
    out_path.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {out_path.relative_to(ROOT)} ({len(rows)} focus artifacts verified)")
    print(json.dumps(identities, indent=1))
    print(json.dumps(out["nested_chain_inversion_conditional_on_reported_scores"], indent=1))


if __name__ == "__main__":
    main()
