#!/usr/bin/env python3
"""Independent verification of the H38 candidate files (plain rasterio/numpy).

Deliberately does NOT use ``gems25.submission`` for the file checks (a second,
unshared implementation of every hard check). Also re-derives the greedy emission
from the saved full-build surface (``data/work/h38_full_scores.npy``) and requires
pixel-equality with the shipped dots. Writes ``evidence/h38_verify_independent.json``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.greedy import greedy_dots  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.thinning import ridge_nms, select_top_positive  # noqa: E402

DL = ROOT / "docs" / "downloads"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    zeros = sorted(DL.glob("gems25-h38-greedy-credit-*-zeros.tif"))
    assert len(zeros) == 1, zeros
    zp = zeros[0]
    np_path = Path(str(zp).replace("-zeros.tif", "-nan.tif"))
    zip_path = zp.with_suffix(".zip")
    tmpl_path = data_dir() / "sample_submission.tif"
    labels_path = data_dir() / "labels.tif"
    checks: dict[str, object] = {}

    with rasterio.open(tmpl_path) as t:
        t_arr, t_crs, t_tr, t_shape = t.read(1), t.crs, t.transform, t.shape
    foot = np.isfinite(t_arr)
    with rasterio.open(labels_path) as s:
        lab = s.read(1) > 0
    assert lab.shape == t_shape

    def audit(path: Path, label: str) -> np.ndarray:
        with rasterio.open(path) as s:
            arr = s.read(1)
            checks[f"{label}.single_band_float32"] = bool(s.count == 1 and s.dtypes == ("float32",))
            checks[f"{label}.crs_epsg32611_matches_template"] = bool(s.crs is not None and s.crs.to_epsg() == 32611 and s.crs == t_crs)
            checks[f"{label}.shape_transform_match"] = bool(s.shape == t_shape == (3730, 3292) and s.transform == t_tr)
            checks[f"{label}.transform_tuple"] = [float(v) for v in tuple(s.transform)[:6]]
        inside = arr[foot]
        checks[f"{label}.footprint_px"] = int(foot.sum())
        checks[f"{label}.footprint_all_finite"] = bool(np.isfinite(inside).all())
        checks[f"{label}.footprint_min_max"] = [float(np.min(inside)), float(np.max(inside))]
        checks[f"{label}.footprint_values_subset_0_1"] = sorted(set(np.unique(inside).tolist()))
        checks[f"{label}.positive_px"] = int((inside > 0).sum())
        checks[f"{label}.positives_on_catalogue"] = int(((arr > 0) & lab).sum())
        checks[f"{label}.positives_outside_footprint"] = int(((np.nan_to_num(arr, nan=0.0) > 0) & ~foot).sum())
        return arr

    z = audit(zp, "zeros")
    checks["zeros.strict_whole_array_in_0_1_no_nan"] = bool(((z >= 0) & (z <= 1)).all())
    checks["zeros.nan_anywhere"] = int(np.isnan(z).sum())
    checks["zeros.outside_all_zero"] = bool((z[~foot] == 0).all())
    n = audit(np_path, "nan")
    checks["nan.outside_all_nan"] = bool(np.isnan(n[~foot]).all())
    checks["twins.footprint_values_identical"] = bool((z[foot] == n[foot]).all())

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        checks["zip.single_member_named_like_tif"] = bool(names == [zp.name])
        checks["zip.member_bytes_equal_tif"] = bool(len(names) == 1 and zf.read(names[0]) == zp.read_bytes())

    # content id, re-implemented here (sha256 of <f4 values on footprint minus catalogue)
    v = np.asarray(z[foot & ~lab], dtype="<f4").copy()
    v[v == 0] = 0
    cid = hashlib.sha256(v.tobytes()).hexdigest()[:12]
    checks["content_id_recomputed"] = cid
    checks["content_id_in_filename"] = bool(cid in zp.name)

    reg = json.loads((ROOT / "registry" / "submissions.json").read_text())
    prim = next(f for f in reg["files"] if f["id"] == "h38-greedy-credit")
    checks["sha256_file"] = sha256(zp)
    checks["sha256_matches_registry"] = bool(sha256(zp) == prim["sha256"])
    checks["note_chars"] = len(prim["note"])
    checks["note_le_140"] = bool(len(prim["note"]) <= 140)

    # greedy re-derivation from the saved surface must reproduce the shipped dots exactly
    work = work_dir()
    p = np.load(work / "h38_full_scores.npy")
    fi = np.flatnonzero(foot.ravel())
    grid = np.zeros(foot.shape, np.float32)
    grid.ravel()[fi] = p
    r = ridge_nms(grid, foot, 1.0)
    top = select_top_positive(np.where(r & ~lab, grid, 0.0), foot, int(round(0.035 * int(foot.sum()))))
    em, diag = greedy_dots(grid, top, foot, lab, 0.25 * float(lab.sum()))
    checks["greedy_rederived_dots_equal_shipped"] = bool((em == (z > 0)).all())
    checks["greedy_rederived_diag"] = diag

    hard = [
        checks["zeros.single_band_float32"], checks["zeros.crs_epsg32611_matches_template"],
        checks["zeros.shape_transform_match"], checks["zeros.footprint_all_finite"],
        checks["zeros.strict_whole_array_in_0_1_no_nan"], checks["zeros.outside_all_zero"],
        checks["nan.outside_all_nan"], checks["twins.footprint_values_identical"],
        checks["zip.single_member_named_like_tif"], checks["zip.member_bytes_equal_tif"],
        checks["content_id_in_filename"], checks["sha256_matches_registry"], checks["note_le_140"],
        checks["greedy_rederived_dots_equal_shipped"],
        checks["zeros.positives_on_catalogue"] == 0, checks["zeros.positives_outside_footprint"] == 0,
        checks["zeros.footprint_min_max"] == [0.0, 1.0], checks["zeros.nan_anywhere"] == 0,
    ]
    out = dict(candidate=zp.name, all_hard_checks_pass=bool(all(hard)), checks=checks)
    (ROOT / "evidence" / "h38_verify_independent.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out, indent=1, default=float))
    if not out["all_hard_checks_pass"]:
        raise SystemExit("INDEPENDENT VERIFICATION FAILED")


if __name__ == "__main__":
    main()
