#!/usr/bin/env python3
"""Session-7 (H37) B2-chain recheck — preserved under this name after the 2026-10-25 parallel-session merge (scripts/verify_b2_chain.py is the GMCE/MSCR session version; both compute the same identities with different fetch assumptions).

Re-verify the H19-5 -> D2.8 -> B1 -> B2 (0.2778) pixel chain from restored bytes.

Session-7 line-by-line check of the explanation recorded in
``evidence/focus_sites_forensics.json`` / knowledge/17:

* fetch the GEMSDOE28 B1, GEMSDOE32 B2 and GEMSDOE36 rasters from the owner's
  public GitHub repos and require SHA-256 == the pins in the focus forensics
  (mismatch aborts; nothing is asserted from unpinned bytes);
* verify B1 == D2.8 & (d(catalogue) > 1 px) and B2 == D2.8 & (d > 2 px)
  pixel-exactly, and the GEMSDOE36 = B2 + extra relation;
* report distance shells and the DTI break-even ratios at the OWNER-reported
  scores (scores stay OWNER claims; the algebra is `gems25.metric`).

Output: ``evidence/h37_b2_recheck.json`` (COMPUTED; scores OWNER).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.metric import marginal_inclusion_ratio  # noqa: E402
from gems25.paths import data_dir  # noqa: E402

WANTED = {"gems28-h27-4-r1-solo": "B1_r1", "gems32-h33-2-b2-zeros": "B2", "gems36-anderson-pinn": "anderson36"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(repo: str, path: str, dest: Path, pin: str) -> None:
    if dest.exists() and sha256(dest) == pin:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".partial")
    with tmp.open("wb") as out:
        r = subprocess.run(["gh", "api", f"repos/{repo}/contents/{path}",
                            "-H", "Accept: application/vnd.github.raw"],
                           stdout=out, stderr=subprocess.PIPE)
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"gh fetch failed for {repo}/{path}: {r.stderr.decode()[:300]}")
    got = sha256(tmp)
    if got != pin:
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"SHA-256 mismatch for {repo}/{path}: got {got}, pin {pin}")
    tmp.replace(dest)


def dots(path: Path, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as s:
        return (np.nan_to_num(s.read(1), nan=0.0) > 0) & foot


def main() -> None:
    data = data_dir()
    focus = json.loads((ROOT / "evidence" / "focus_sites_forensics.json").read_text())
    by_id = {a["id"]: a for a in focus["focus_artifacts"]}
    art_dir = data / "artifacts_h37"
    fetched = {}
    for fid, key in WANTED.items():
        a = by_id[fid]
        dest = art_dir / f"{fid}.tif"
        fetch(a["repo"], a["path"], dest, a["sha256"])
        fetched[key] = dict(path=str(dest), sha256=a["sha256"],
                            owner_reported_score=a["owner_reported_score"], repo=a["repo"],
                            source_path=a["path"])

    with rasterio.open(data / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(data / "labels.tif") as s:
        lab = s.read(1) == 1
    d28 = dots(data / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", foot)
    h195 = dots(data / "scored" / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", foot)
    dist = distance_transform_edt(~lab)

    def shells(d: np.ndarray, dd: np.ndarray) -> dict:
        x = dd[d]
        return dict(d_eq_0=int((x == 0).sum()), d_in_0_1=int(((x > 0) & (x <= 1)).sum()),
                    d_in_1_2=int(((x > 1) & (x <= 2)).sum()), d_in_2_3=int(((x > 2) & (x <= 3)).sum()),
                    d_gt_3=int((x > 3).sum()))

    b1 = dots(Path(fetched["B1_r1"]["path"]), foot)
    b2 = dots(Path(fetched["B2"]["path"]), foot)
    a36 = dots(Path(fetched["anderson36"]["path"]), foot)
    exp_b1 = d28 & (dist > 1.0)
    exp_b2 = d28 & (dist > 2.0)
    out = dict(
        evidence_class="COMPUTED from hash-pinned owner-mirror rasters; scores are OWNER-reported claims",
        generated_by="scripts/verify_b2_chain_h37.py",
        footprint_pixels=int(foot.sum()), catalogue_pixels=int(lab.sum()),
        fetched=fetched,
        counts=dict(h19_5=int(h195.sum()), d28=int(d28.sum()), B1=int(b1.sum()), B2=int(b2.sum()),
                    anderson36=int(a36.sum())),
        identities=dict(
            d28_subset_of_h19_5_xor=int((d28 & ~h195).sum()),
            B1_eq_d28_and_dist_gt_1_xor=int((b1 ^ exp_b1).sum()),
            B2_eq_d28_and_dist_gt_2_xor=int((b2 ^ exp_b2).sum()),
            B2_eq_B1_and_dist_gt_2_xor=int((b2 ^ (b1 & (dist > 2.0))).sum()),
            anderson36_minus_B2=int((a36 & ~b2).sum()),
            B2_minus_anderson36=int((b2 & ~a36).sum()),
        ),
        shells=dict(d28=shells(d28, dist), B1=shells(b1, dist), B2=shells(b2, dist),
                    anderson36=shells(a36, dist)),
        breakeven_at_owner_scores={
            k: marginal_inclusion_ratio(v)
            for k, v in (("d28_0.2600", 0.2600), ("B1_0.2708", 0.2708), ("B2_0.2778", 0.2778))
        },
        owner_chain=["h19-5 solid 0.1922 OWNER", "dot d1.5 0.2477 OWNER", "d2.8 0.2600 OWNER",
                     "B1 (d>1px) 0.2708 OWNER", "B2 (d>2px) 0.2778 OWNER"],
    )
    out_path = ROOT / "evidence" / "h37_b2_recheck.json"
    out_path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("counts", "identities", "breakeven_at_owner_scores")}, indent=1))


if __name__ == "__main__":
    main()
