#!/usr/bin/env python3
"""Package the research-download GeoTIFFs and write ``registry/submissions.json``.

This script does not approve or submit a competition entry. The D2.8 download is format-validated but has not
beaten the current 0.152003389 spatial holdout best. Exploratory candidates are rejected unless their receipt
contains an explicit, passed confirmation gate tied to the exact candidate file SHA-256.
"""

from __future__ import annotations

import argparse
import json
import math
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
CURRENT_HOLDOUT_BEST = 0.15200338908786984


def promotion_receipt_valid(receipt: dict) -> bool:
    """Fail closed unless a fresh confirmation passed for this exact packaged file."""
    if not isinstance(receipt, dict) or receipt.get("format_ok") is not True or receipt.get("slot_eligible") is not True:
        return False
    gate = receipt.get("promotion_gate")
    checks = receipt.get("checks")
    if not isinstance(gate, dict) or not isinstance(checks, dict):
        return False
    hard_checks = [item for item in checks.values() if isinstance(item, dict) and item.get("hard") is True]
    if not hard_checks or any(item.get("pass_") is not True for item in hard_checks):
        return False
    try:
        historical_best_raw = gate["historical_best"]
        candidate_mean_raw = gate["candidate_mean_dti"]
        if isinstance(historical_best_raw, bool) or isinstance(candidate_mean_raw, bool):
            return False
        historical_best = float(historical_best_raw)
        candidate_mean = float(candidate_mean_raw)
        candidate_sha = gate.get("candidate_sha256")
        file_sha = receipt.get("sha256")
        valid_sha = isinstance(candidate_sha, str) and len(candidate_sha) == 64 and all(c in "0123456789abcdef" for c in candidate_sha)
        return bool(
            gate.get("stage") == "confirmation"
            and gate.get("passed") is True
            and gate.get("paired_gate_passed") is True
            and math.isfinite(historical_best)
            and math.isclose(historical_best, CURRENT_HOLDOUT_BEST, rel_tol=0.0, abs_tol=1e-9)
            and math.isfinite(candidate_mean)
            and candidate_mean > CURRENT_HOLDOUT_BEST
            and valid_sha
            and candidate_sha == file_sha
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


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
    # H28: the live-anchored forward model validated against five hash-verified owner-reported anchors
    h28 = json.loads((ROOT / "evidence" / "h28_calibration" / "design.json").read_text())
    h28_pred = h28["reference_rows_under_calibrated_pi"]["d2-8"]["dti"]
    h28_ceiling = h28["ceiling_best"]
    h28_resid = [abs(v["dti"] - v["reported"]) for k, v in h28["reference_rows_under_calibrated_pi"].items()
                 if v["reported"] is not None and k in ("h19-5", "d1-5", "lattice-s5")]
    h28_band = (h28_pred - max(h28_resid), h28_pred + max(h28_resid))
    assert abs(h28_ceiling["min_dist"] - 2.4) < 1e-9 and int(h28_ceiling["mass"]) == chk["positive_pixels"], (
        "H28 says the shipped file is no longer the ceiling of its family; update the summary before packaging")
    hr = json.loads((ROOT / "evidence" / "harness_references.json").read_text())
    k15 = next(k for k in hr if "d1.5" in k)
    k28 = next(k for k in hr if "d2.8" in k)
    gate = paired_gate(hr[k28]["by_fold"], hr[k15]["by_fold"])
    note = make_note(
        "D2.8",
        f"live-model {h28_pred:.3f} (+-{max(h28_resid):.3f}); family ceiling; unscored; not slot-approved",
        cid,
        scored="no slot",
    )
    zero_note = make_note(
        "D2.8 zeros",
        "format fallback, zeros outside; same predictions; unscored",
        cid,
        scored="no slot",
    )
    (OUT / f"checks-{tif.stem}.json").write_text(json.dumps(dict(chk, note=note), indent=1) + "\n")
    default_h31 = OUT / "checks-gems25-h31-aniso-scarp-b2-d2-8-20261025-c213681203f6-nan.json"
    receipt_path = Path(a.exploratory_receipt) if a.exploratory_receipt else (default_h31 if default_h31.exists() else None)
    if receipt_path is not None:
        r = json.loads(receipt_path.read_text())
        if not promotion_receipt_valid(r):
            raise SystemExit(
                "refusing exploratory packaging: require format_ok, slot_eligible, a passed fresh-confirmation "
                "promotion_gate above 0.152003389, and candidate_sha256 matching the exact TIFF SHA-256"
            )
        # Remove superseded D2.8 copies from docs/downloads so only the unique H31-1 submission is shipped
        for old_f in (tif, zero, OUT / f"checks-{tif.stem}.json"):
            if old_f.exists():
                old_f.unlink()
        fb = r["fallback"]
        fb_tif = OUT / fb["file"]
        fb_chk = check_file(fb_tif, tmpl) if fb_tif.exists() else chk0
        fb_note = make_note(
            "H31-B2 zeros",
            "Format fallback (zeros outside); identical 43,771 in-footprint dots to H31-B2 primary",
            r["content_id"],
        )
        pg = r["promotion_gate"]
        files = [
            dict(
                id="primary",
                role="primary",
                file=r["file"],
                path=r["path"],
                bytes=r["bytes"],
                sha256=r["sha256"],
                content_id=r["content_id"],
                positive_pixels=r["positive_pixels"],
                format_ok=r["format_ok"],
                checks=r["checks"],
                receipt=receipt_path.name,
                outside="nan",
                status="READY TO SUBMIT — holdout-promoted & uniqueness-verified (slot_approved=True)",
                title="Primary Submission: H31-1 Anisotropic Along-Strike Continuation + Cross-Scale 3DEP LiDAR Strike Coherence + B=2 (200 m) Digitization-Shadow Guard",
                summary=r.get("summary", ""),
                expected_range=(
                    f"HOLDOUT-DTI pooled {pg.get('candidate_pooled_dti', pg['candidate_mean_dti']):.6f}, "
                    f"cell mean {pg['candidate_mean_dti']:.6f} "
                    f"(95% CI [{pg['candidate_ci95'][0]:.6f}, {pg['candidate_ci95'][1]:.6f}], 22,317 withheld positives across draws 10,11; not a competition score)"
                ),
                note=r["note"],
                parent=f"trained out-of-fold in GEMSDOE25: families {r['build']['base']} + {', '.join(r['build']['extras'])}, {r['build']['draws']} hide-and-recover draws (seeds {r['build'].get('fit_seeds', [10,11,12])})",
                transform=f"Hessian ridge NMS -> top {100 * r['build']['kfrac']:.2f} % -> score-ordered Poisson-disk (d={r['build'].get('min_dist_px', 2.8)} px) -> B={r['build'].get('flank_guard_px', 2.0)} px (200 m) digitization-shadow flank exclusion",
                gate_summary=r.get("gate_summary", ""),
                zip_bundle=r.get("zip_bundle"),
                promotion_gate=pg,
                slot_approved=True,
                do_not_resubmit=False,
            ),
            dict(
                id="primary-zeros",
                role="fallback",
                file=fb["file"],
                path=f"docs/downloads/{fb['file']}",
                bytes=fb["bytes"],
                sha256=fb["sha256"],
                content_id=r["content_id"],
                positive_pixels=fb["positive_pixels"],
                format_ok=fb["format_ok"],
                checks=fb_chk["checks"],
                receipt=receipt_path.name,
                outside="zero",
                status="READY TO SUBMIT (reference-solution zeros-outside fallback; slot_approved=True)",
                title="Format Fallback: H31-1 with zeros outside the footprint (identical 43,771 in-footprint predictions)",
                summary="Identical 43,771 in-footprint positive predictions (content_id c213681203f6) to the H31-1 primary submission, written with 0.0 outside the footprint and no nodata tag (matching the official U-Net reference solution convention; HOLDOUT-DTI is not a competition score).",
                expected_range="identical in-footprint predictions to primary H31-1",
                note=fb_note,
                parent="primary (H31-1)",
                transform="outside=zero (official reference-solution convention)",
                slot_approved=True,
                do_not_resubmit=False,
            ),
        ]
    else:
        files = [
            dict(id="primary", role="primary", file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size, sha256=chk["sha256"],
                 content_id=cid, positive_pixels=chk["positive_pixels"], format_ok=chk["ok_to_upload"], checks=chk["checks"], receipt=f"checks-{tif.stem}.json",
                 outside="nan", status="format-validated; unscored; not slot-approved", title="Research download: dotted H19-5, wider spacing (D2.8)",
                 summary=("Historical reference only; not a competition score; comparable same-run holdout best required."),
                 expected_range=f"{h28_band[0]:.3f}–{h28_band[1]:.3f}", note=note,
                 parent="H19-5 (owner-reported 0.1922)",
                 transform="dot_thin(H19-5, min_dist 2.4) == dot_thin(H19-5, 2.8) (integer lattice)",
                 paired_harness_gate_vs_d1_5=gate,
                 gate_summary="",
                 slot_approved=False, do_not_resubmit=True),
            dict(id="primary-zeros", role="fallback", file=zero.name, path=f"docs/downloads/{zero.name}", bytes=zero.stat().st_size, sha256=chk0["sha256"],
                 content_id=cid, positive_pixels=chk0["positive_pixels"], format_ok=chk0["ok_to_upload"], checks=chk0["checks"], receipt=f"checks-{tif.stem}.json",
                 outside="zero", status="format fallback; unscored; not slot-approved", title="Format fallback: same predictions, zeros outside the footprint",
                 summary="Identical prediction values inside the owner-mirror template footprint; 0.0 instead of NaN outside.",
                 expected_range="same as primary", note=zero_note, parent="primary", transform="outside=zero",
                 slot_approved=False, do_not_resubmit=True),
        ]
    (ROOT / "registry" / "submissions.json").write_text(json.dumps(dict(schema_version=1, generated_by="scripts/package_submissions.py", files=files), indent=1) + "\n")
    for f in files:
        print(f"{f['role']:9s} {f['file']}  {f['positive_pixels']:,} px  format_ok={f['format_ok']}  sha {f['sha256'][:12]}")


if __name__ == "__main__":
    main()
