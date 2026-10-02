#!/usr/bin/env python3
"""Package the shipped GeoTIFFs and write ``registry/submissions.json`` (the single source for site, README and tests).

* PRIMARY  - dotted H19-5 at wider spacing (pixel-identical to the group's unscored alternate), re-written with
             ``gems25.submission.write_submission`` so its raster profile equals the portal-accepted 0.2477 file.
* FALLBACK - the same values with zeros outside the footprint (earlier files with either convention were scored).
* EXPLORATORY - the trained factorial-evidence surface from ``build_candidate.py`` (if its receipt exists).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, make_note, write_submission  # noqa: E402

OUT = ROOT / "docs" / "downloads"
D28 = "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"


def paired_gate(a: list[float], b: list[float]) -> dict:
    d = np.array(a) - np.array(b)
    return dict(mean_gain=float(d.mean()), folds_positive=int((d > 0).sum()), worst_fold=float(d.min()),
                passed=bool(d.mean() > 0.001 and (d > 0).sum() >= 3 and d.min() >= -0.01), per_fold=[float(x) for x in d])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exploratory-receipt", default=None, help="docs/downloads/checks-<file>.json from build_candidate.py")
    ap.add_argument("--date", default="20261002")
    a = ap.parse_args()
    d = data_dir()
    tmpl = d / "sample_submission.tif"
    with rasterio.open(tmpl) as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(d / "labels.tif") as s:
        lab = s.read(1) == 1
    with rasterio.open(d / "scored" / D28) as s:
        pred = np.nan_to_num(s.read(1), nan=0.0).astype(np.float32)
    cid = content_id(pred, foot, lab)
    assert cid == "e56ea318af89", cid  # reproduces the group's content id for the alternate
    OUT.mkdir(parents=True, exist_ok=True)
    fname = make_filename("dotted-h19-5-d2-8", a.date, cid, "nan")
    tif = write_submission(pred, tmpl, OUT / fname, outside="nan")
    zero = write_submission(pred, tmpl, OUT / fname.replace("-nan.tif", "-zeros.tif"), outside="zero")
    chk, chk0 = check_file(tif, tmpl), check_file(zero, tmpl)
    emu = json.loads((ROOT / "evidence" / "emission_model.json").read_text())
    m = emu["d2_8"]
    hr = json.loads((ROOT / "evidence" / "harness_references.json").read_text())
    k15 = next(k for k in hr if "d1.5" in k)
    k28 = next(k for k in hr if "d2.8" in k)
    gate = paired_gate(hr[k28]["by_fold"], hr[k15]["by_fold"])
    note = make_note("D2.8", "H19-5 Poisson-disk dots, 44,090 px; model 0.255", cid)
    (OUT / f"checks-{tif.stem}.json").write_text(json.dumps(dict(chk, note=note), indent=1) + "\n")
    files = [
        dict(id="primary", role="primary", file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size, sha256=chk["sha256"],
             content_id=cid, positive_pixels=chk["positive_pixels"], format_ok=chk["ok_to_upload"], checks=chk["checks"], receipt=f"checks-{tif.stem}.json",
             outside="nan", status="unscored candidate", title="Recommended next upload: dotted H19-5, wider spacing (D2.8)",
             summary=("The 0.1922 detector (H19-5) thinned by deterministic Poisson-disk dotting to 44,090 pixels — 73 % of the pixels of the 0.2477 file, 36 % of H19-5. "
                      f"Calibrated emission model: {m['model_dti']:.3f} (band {m['model_dti_low']:.3f}–{m['model_dti_high']:.3f}); a model, not a score. "
                      "Honest provenance: byte-identical to the group's unscored GEMSDOE24 alternate, re-hosted here because it is the best evidence-supported next upload — not new detection work."),
             expected_range=f"{m['model_dti_low']:.3f}–{m['model_dti_high']:.3f}", note=note,
             parent="H19-5 (owner-reported 0.1922); byte-identical (same SHA-256) to the group's unscored GEMSDOE24 alternate e56ea318af89, which this repo's writer reproduces exactly",
             transform="dot_thin(H19-5, min_dist 2.4) == dot_thin(H19-5, 2.8) (integer lattice)",
             paired_harness_gate_vs_d1_5=gate,
             gate_summary=("emission model band lies above 0.2477; paired hide-and-recover diagnostic vs the 0.2477 file (leak-inflated, same mask family): "
                           f"{gate['mean_gain']:+.4f} mean, {gate['folds_positive']}/4 folds, worst fold {gate['worst_fold']:+.4f} -> "
                           f"{'passes' if gate['passed'] else 'does not pass'} the frozen gate"),
             do_not_resubmit=False),
        dict(id="primary-zeros", role="fallback", file=zero.name, path=f"docs/downloads/{zero.name}", bytes=zero.stat().st_size, sha256=chk0["sha256"],
             content_id=cid, positive_pixels=chk0["positive_pixels"], format_ok=chk0["ok_to_upload"], checks=chk0["checks"], receipt=f"checks-{tif.stem}.json",
             outside="zero", status="fallback (same predictions)", title="Fallback: same predictions, zeros outside the footprint",
             summary="Identical values inside the footprint; 0.0 instead of NaN outside it. Use only if the NaN-outside file is rejected (earlier files with either convention were scored by the portal).",
             expected_range="same as primary", note=note.replace("D2.8 |", "D2.8 zeros-outside |", 1)[:120], parent="primary", transform="outside=zero",
             do_not_resubmit=False),
    ]
    if a.exploratory_receipt:
        r = json.loads(Path(a.exploratory_receipt).read_text())
        ov = ROOT / "evidence" / "exploratory_overlap.json"
        overlap_text = ""
        if ov.exists():
            o = json.loads(ov.read_text())
            overlap_text = (f" Independence: only {100 * o['primary_D2.8']['share_of_exploratory_within_3px_of_it']:.0f} % of its dots lie within 3 px of the primary's; "
                            f"{100 * o['exploratory']['share_within_3px_of_catalogue']:.1f} % lie within 3 px of known faults (random baseline {100 * o['exploratory']['random_footprint_share_within_3px']:.1f} %, H19 dots {100 * o['exploratory']['primary_share_within_3px_of_catalogue']:.1f} %).")
        files.append(dict(
            id="exploratory", role="alternate", file=r["file"], path=r["path"], bytes=r["bytes"], sha256=r["sha256"], content_id=r["content_id"],
            positive_pixels=r["positive_pixels"], format_ok=r["format_ok"], checks=r["checks"], receipt=Path(a.exploratory_receipt).name,
            outside="nan", status="unscored exploratory candidate", title="Exploratory: new factorial-evidence surface (separate slot, owner decision)",
            summary=(r.get("summary", "") + overlap_text), expected_range="no live calibration", note=r["note"],
            parent=f"trained here: families {r['build']['base']} + {r['build']['extras'] or 'no add-ons'}, {r['build']['draws']} hide-and-recover draws",
            transform=f"ridge NMS -> top {100 * r['build']['kfrac']:.2f} % -> {r['build']['variant']}", gate_summary=r.get("gate_summary", ""), do_not_resubmit=False))
        zf = OUT / r["fallback"]["file"]
        if zf.exists():
            zf.unlink()  # the exploratory candidate ships NaN-outside only
    (ROOT / "registry" / "submissions.json").write_text(json.dumps(dict(schema_version=1, generated_by="scripts/package_submissions.py", files=files), indent=1) + "\n")
    for f in files:
        print(f"{f['role']:9s} {f['file']}  {f['positive_pixels']:,} px  format_ok={f['format_ok']}  sha {f['sha256'][:12]}")


if __name__ == "__main__":
    main()
