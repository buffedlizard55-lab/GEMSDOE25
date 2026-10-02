#!/usr/bin/env python3
"""Out-of-sample check of the dotting model on the pair NOT used for calibration: solid H25 (0.1280) -> dotted H28 (0.1839).

Calibration used only H19-5 -> dotted H19-5 (0.1922 -> 0.2477) and the lattice density. For H25 we assume the
same false-positive mass per emitted pixel (0.90) and solve the credit from its own score, then predict H28.
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


def mask(p):
    with rasterio.open(p) as s:
        return np.nan_to_num(s.read(1), nan=0.0) > 0


def main() -> None:
    d = data_dir()
    with rasterio.open(d / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(d / "labels.tif") as s:
        lab = s.read(1) == 1
    m25 = mask(next((d / "scored").glob("gems10-h25-ctx-ridge-*.tif")))
    m28 = mask(next((d / "scored").glob("gems10-h28-dotted-ridge-*.tif")))
    emu = json.loads((ROOT / "evidence" / "emission_model.json").read_text())
    N = emu["requirements"]["truth_px_used"]
    fpp = emu["requirements"]["fp_mass_per_emitted_px"]
    n25, n28 = int(m25.sum()), int(m28.sum())
    d25, d28 = distance_transform_edt(~m25), distance_transform_edt(~m28)
    S = (d25 < 3) & foot & ~lab
    rho = float(kernel(d28[S]).sum() / kernel(d25[S]).sum())
    D25, D28_actual = 0.1280, 0.1839
    f25 = fpp * n25 / N
    c25 = D25 * (0.2 * f25 + 0.8) / (1 - 0.2 * D25)
    pred = rho * c25 / (0.2 * rho * c25 + 0.2 * (n28 / n25) * f25 + 0.8)
    out = dict(pair="H25 solid (owner 0.1280) -> H28 dotted (owner 0.1839)", n_solid=n25, n_dotted=n28, geometric_retention=rho,
               assumed_fp_mass_per_px=fpp, truth_px_used=N, credit_per_truth_solid=c25, predicted_dotted_dti=float(pred), owner_reported_dotted_dti=D28_actual,
               error=float(pred - D28_actual),
               sensitivity={f"fp_per_px_x{k}": float(rho * (D25 * (0.2 * (fpp * k) * n25 / N + 0.8) / (1 - 0.2 * D25)) /
                                                    (0.2 * rho * (D25 * (0.2 * (fpp * k) * n25 / N + 0.8) / (1 - 0.2 * D25)) + 0.2 * (n28 / n25) * (fpp * k) * n25 / N + 0.8))
                            for k in (0.8, 0.9, 1.0, 1.1)},
               reading="Out-of-sample: only the dotting mechanism (credit retention, false-positive mass proportional to pixels) is tested; the FP mass per pixel is carried over from H19-5.")
    (ROOT / "evidence" / "emission_model_oos_check.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items() if k != "sensitivity" and k != "reading"}, indent=1))
    print({k: round(v, 4) for k, v in out["sensitivity"].items()})


if __name__ == "__main__":
    main()
