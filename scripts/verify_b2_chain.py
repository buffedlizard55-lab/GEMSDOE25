#!/usr/bin/env python3
"""Re-verify the H19-5 -> D1.5 -> D2.8 -> R1 -> B2 -> G36 pixel chain from hash-pinned mirrors.

Inputs are the SHA-256-pinned files restored by ``scripts/fetch_top_scorers.py`` into
``data/registry_top`` plus the pinned ``labels.tif`` / ``sample_submission.tif``. Nothing is
fetched. Every competition score used in the arithmetic inversion is an OWNER-reported claim
(registry/top_scorer_sources.json), and the inversion additionally assumes the H28-calibrated
hidden-truth size N=12,691 px and the approximation TP_w + FP_w ~= emitted mass M (exact only
if the kernel-hit mass of the prediction equals the truth-side credit mass). Those assumptions
are recorded in the output; the pixel identities themselves are exact.

    .venv/bin/python scripts/verify_b2_chain.py
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
from gems25.metric import marginal_inclusion_ratio  # noqa: E402
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import sha256_file  # noqa: E402
from gems25.thinning import dot_thin  # noqa: E402

TOP = data_dir() / "registry_top"
FILES = {  # key -> (file, OWNER-reported score)
    "h19_5": ("g19_h19-5_0.1922.tif", 0.1922),
    "d1_5": ("g24_d1-5_0.2477.tif", 0.2477),
    "d2_8": ("g25_d2-8_0.2600.tif", 0.2600),
    "g30": ("g30_d28-poisson_0.2600.tif", 0.2600),
    "r1_g28": ("g28_h27-4-r1-solo_0.2708.tif", 0.2708),
    "r1_g31": ("g31_h27-4-solo-d28_0.2708.tif", 0.2708),
    "b2_g32": ("g32_h33-2-b2_0.2778.tif", 0.2778),
    "g36": ("g36_anderson-pinn_0.2750.tif", 0.2750),
}
N_G = 12691.0


def read_mask(name: str, foot: np.ndarray) -> np.ndarray:
    p = TOP / FILES[name][0]
    with rasterio.open(p) as s:
        a = s.read(1)
    return (np.nan_to_num(a, nan=0.0) > 0) & foot


def implied_tp(score: float, mass: float, n_g: float = N_G) -> float:
    """Invert DTI ~= TP / (0.2*M + 0.8*N) approximately... (exact algebra, approx. model).

    With FN = N - TP and the approximation TP + FP ~= M (emitted binary mass):
    DTI = TP / (TP + 0.2*FP + 0.8*FN) = TP / (0.2*TP + 0.2*FP + 0.8*N) [since alpha = 1-beta]
        ~= TP / (0.2*M + 0.8*N), hence TP ~= DTI * (0.2*M + 0.8*N) / (1 - 0.04*DTI) only if
    the 0.2*TP term is instead kept explicit; we use this repo's earlier convention
    (scripts/analyze_focus_sites.py) so the numbers are comparable cell-for-cell.
    """
    return score * (0.2 * mass + 0.8 * n_g) / (1.0 - 0.04 * score)


def main() -> None:
    reg = {r["local"]: r["sha256"] for r in json.loads((ROOT / "registry/top_scorer_sources.json").read_text())["rasters"]}
    hashes = {}
    for k, (fname, _s) in FILES.items():
        h = sha256_file(TOP / fname)
        assert h == reg[fname], f"hash mismatch for {fname}"
        hashes[k] = h
    with rasterio.open(data_dir() / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(data_dir() / "labels.tif") as s:
        lab = s.read(1) == 1
    dist = distance_transform_edt(~(lab & foot))
    m = {k: read_mask(k, foot) for k in FILES}
    counts = {k: int(v.sum()) for k, v in m.items()}
    shells = {}
    d = dist[m["d2_8"]]
    for name, lo, hi in [("d_eq_0", -1, 0), ("0_lt_d_le_1", 0, 1.0), ("1_lt_d_le_2", 1.0, 2.0),
                         ("2_lt_d_le_3", 2.0, 3.0), ("d_gt_3", 3.0, np.inf)]:
        shells[name] = int(((d > lo) & (d <= hi)).sum())
    thin24 = dot_thin(m["h19_5"], 2.4)
    identities = {
        "d1_5_equals_dot_thin_h19_5_1.5": bool(np.array_equal(dot_thin(m["h19_5"], 1.5), m["d1_5"])),
        "d2_8_equals_dot_thin_h19_5_2.4": bool(np.array_equal(thin24, m["d2_8"])),
        "d2_8_equals_dot_thin_h19_5_2.8": bool(np.array_equal(dot_thin(m["h19_5"], 2.8), m["d2_8"])),
        "d2_8_subset_of_h19_5": bool(not (m["d2_8"] & ~m["h19_5"]).any()),
        "d1_5_subset_of_h19_5": bool(not (m["d1_5"] & ~m["h19_5"]).any()),
        "g30_equals_d2_8_on_footprint": bool(np.array_equal(m["g30"], m["d2_8"])),
        "r1_g28_equals_r1_g31": bool(np.array_equal(m["r1_g28"], m["r1_g31"])),
        "r1_equals_d2_8_and_dist_gt_1": bool(np.array_equal(m["d2_8"] & (dist > 1.0), m["r1_g28"])),
        "b2_equals_d2_8_and_dist_gt_2": bool(np.array_equal(m["d2_8"] & (dist > 2.0), m["b2_g32"])),
        "b2_equals_r1_and_dist_gt_2": bool(np.array_equal(m["r1_g28"] & (dist > 2.0), m["b2_g32"])),
        "b2_subset_of_g36": bool(not (m["b2_g32"] & ~m["g36"]).any()),
        "no_chain_file_emits_on_catalogue": bool(all(not (v & lab).any() for v in m.values())),
    }
    steps = []
    chain = [("d2_8", "r1_g28"), ("r1_g28", "b2_g32"), ("b2_g32", "g36")]
    for a, b in chain:
        sa, sb = FILES[a][1], FILES[b][1]
        ma, mb = float(counts[a]), float(counts[b])
        tpa, tpb = implied_tp(sa, ma), implied_tp(sb, mb)
        dm = mb - ma
        steps.append(dict(from_=a, to=b, mass_from=ma, mass_to=mb, delta_mass=dm,
                          owner_dti_from=sa, owner_dti_to=sb,
                          implied_delta_tp=float(tpb - tpa),
                          implied_credit_per_delta_px=float((tpb - tpa) / dm) if dm else None,
                          break_even_tau_at_from=float(marginal_inclusion_ratio(sa))))
    out = dict(
        evidence_class="COMPUTED pixel identities on hash-pinned mirrors; scores OWNER-reported; inversion conditional",
        hashes=hashes, counts=counts, d2_8_distance_shells=shells, identities=identities,
        thinning_note=(
            "dot_thin is NOT nested across spacings on this parent: only "
            f"{int((m['d2_8'] & m['d1_5']).sum())} of D2.8's {counts['d2_8']} dots are in D1.5 "
            f"({int((m['d2_8'] & ~m['d1_5']).sum())} are h19-5 pixels that D1.5 blocked). D1.5->D2.8 is a "
            "re-thinning of the same parent surface, not a subset deletion; only R1 and B2 are exact deletions."
        ),
        inversion=dict(assumed_N_hidden_px=N_G,
                       approximation="TP_w + FP_w ~= emitted binary mass M; DTI = TP/(TP+0.2FP+0.8FN), FN=N-TP",
                       convention="matches scripts/analyze_focus_sites.py cell-for-cell",
                       steps=steps),
        targets=dict(
            credit_per_dot_at_b2=float(implied_tp(0.2778, counts["b2_g32"]) / counts["b2_g32"]),
            note="OWNER targets 0.3195 and 0.4413 conflict in the brief (IR-25-LEADERBOARD-CONFLICT); both unconverted.",
            implied_credit_per_dot_needed={
                s: float(implied_tp(s, counts["b2_g32"]) / counts["b2_g32"])
                for s in (0.2878, 0.3195, 0.4413)
            },
        ),
    )
    print(json.dumps(out, indent=1))
    if not all(identities.values()):
        raise SystemExit(f"IDENTITY FAILURE: {identities}")
    out_path = ROOT / "evidence" / "gmce_session_b2_chain_verification.json"
    out_path.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
