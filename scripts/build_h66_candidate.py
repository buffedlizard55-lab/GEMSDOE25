#!/usr/bin/env python3
"""Build the pre-registered H66-1 (`G1_C1`: MGD-F + tip-preserved flank shield + sapd3.0) full-footprint GeoTIFFs.

Follows `knowledge/25_preregistered_h66_mgd_and_sgmc_react_2026-10-25.md` section 4.1 verbatim:
  * Columns (86 total, identical order to `run_h66_1` arm `G1_C1`):
      BDE+7 (78) + H27_tip (1) + H34 RESMAG-FLEX (3) + H66 MGD-F (4)
  * Trained on 3 deterministic pseudo-new visible/hidden splits (`seed = 20261025 + m`) so
    dynamic `E` and `H27_tip` are learned on off-visible hidden components, then predicted on
    full `labels.tif` (`E_full`, `tip_full`).
  * Emission (`Factor C = +1`, `min_dist = 3.0 px`, `kfrac = 0.035`):
      `candidates_flank_shielded(..., flank_radius_px=2.5, tip_preserve_threshold=0.05)`
      followed by `score_ordered_dots(..., min_dist=3.0)`.
  * Writes `-zeros.tif` (primary, strict whole-array `0 <= x <= 1`), `-nan.tif` (template-twin),
    and `.zip`, validated automatically via `gems25.submission.check_file`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems25.experiment import HGB_PARAMS, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h31 import candidates_flank_shielded  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h66_mgd_sgmc import H66_MGD_NAMES, load_h66_mgd_sidecar  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.submission import check_file, content_id, make_filename, write_submission, zip_single  # noqa: E402
from gems25.thinning import score_ordered_dots  # noqa: E402
from run_h28_holdout import BASE, EXTRAS  # noqa: E402

KFRAC = 0.035
MIN_DIST = 3.0
FLANK_RADIUS_PX = 2.5
TIP_PRESERVE_THR = 0.05
BASE_SEED = 20261025
SLUG = "h66-mgd-flank-sapd3-0-k3p5"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draws", type=int, default=3)
    ap.add_argument("--verdict-note", required=True)
    ap.add_argument("--out", default=str(ROOT / "docs" / "downloads"))
    args = ap.parse_args()

    t0 = time.time()
    work, ext_dir = work_dir(), data_dir() / "external"
    ctx = load_context(work)
    h34 = load_h34_sidecar(work, ctx.fi)
    mgd = load_h66_mgd_sidecar(work, ext_dir, ctx.foot, ctx.fi)
    cols = ctx.columns(BASE) + ctx.named(EXTRAS)
    H = ctx.holdout
    foot, lab, fi = ctx.foot, ctx.labels, ctx.fi

    E_full = build_catalogue_features(lab, fi)
    tip_full = build_tip_continuation(lab, foot, fi)
    print(f"[{time.time() - t0:.0f}s] H66-1 G1_C1 full build: BDE+7 + H27_tip + {H34_NAMES} + {H66_MGD_NAMES}", flush=True)

    p_sum = np.zeros(fi.size, dtype=np.float32)
    ids = np.arange(1, H.n_comp + 1)
    for m in range(args.draws):
        seed_m = BASE_SEED + m
        rng = np.random.default_rng(seed_m)
        hid = H._pick(rng, ids, 0.20 * float(lab.sum()))
        hidden = np.isin(H.comp, hid)
        visible = lab & ~hidden
        E = build_catalogue_features(visible, fi)
        tip_vis = build_tip_continuation(visible, foot, fi)
        pos = ctx.vec(hidden)
        near = distance_transform_edt(~hidden) <= 1.5
        cand = ctx.vec(foot & ~lab & ~near)
        neg = rng.choice(cand, size=min(N_NEG, cand.size), replace=False)
        idx = np.sort(np.concatenate([pos, neg]))
        y = np.isin(idx, pos).astype(np.int8)
        X = np.hstack([
            gather_columns(ctx, E, idx, True)[:, cols],
            tip_vis[idx].astype(np.float32)[:, None],
            np.asarray(h34[:, idx], dtype=np.float32).T,
            np.asarray(mgd[:, idx], dtype=np.float32).T,
        ])
        model = HistGradientBoostingClassifier(random_state=seed_m, **HGB_PARAMS).fit(X, y)
        print(f"[{time.time() - t0:.0f}s] draw {m} (seed={seed_m}): fit on {idx.size:,} rows ({int(y.sum()):,} pos)", flush=True)
        del X, E, tip_vis
        for lo in range(0, fi.size, 500_000):
            sl = np.arange(lo, min(lo + 500_000, fi.size))
            Xp = np.hstack([
                gather_columns(ctx, E_full, sl, True)[:, cols],
                tip_full[sl].astype(np.float32)[:, None],
                np.asarray(h34[:, sl], dtype=np.float32).T,
                np.asarray(mgd[:, sl], dtype=np.float32).T,
            ])
            p_sum[sl] += model.predict_proba(Xp)[:, 1].astype(np.float32)
            del Xp
        del model

    p = (p_sum / float(args.draws)).astype(np.float32)
    np.save(work / "h66_full_scores.npy", p)

    score_grid = np.zeros(foot.shape, dtype=np.float32)
    score_grid.ravel()[fi] = p
    tip_grid = np.zeros(foot.shape, dtype=np.float32)
    tip_grid.ravel()[fi] = tip_full

    k_budget = int(round(KFRAC * int(foot.sum())))
    s_clean, top, shield_diag = candidates_flank_shielded(
        score_grid,
        foot,
        lab,
        tip_grid,
        k_budget,
        flank_radius_px=FLANK_RADIUS_PX,
        tip_preserve_threshold=TIP_PRESERVE_THR,
    )
    em = score_ordered_dots(s_clean, top, MIN_DIST)
    assert not (em & lab).any(), "emission landed on a known catalogue pixel"

    pred = np.where(em, 1.0, 0.0).astype(np.float32)
    tmpl = data_dir() / "sample_submission.tif"
    date = "20261025"
    cid = content_id(pred, foot, lab)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    recs = {}
    for outside, suffix in (("zero", "zeros"), ("nan", "nan")):
        fname = make_filename(SLUG, date, cid, suffix)
        tif = write_submission(pred, tmpl, out / fname, outside=outside)
        chk = check_file(tif, tmpl)
        assert chk["ok_to_upload"] and not chk["hard_failures"], chk["hard_failures"]
        recs[suffix] = dict(
            file=tif.name,
            path=f"docs/downloads/{tif.name}",
            bytes=tif.stat().st_size,
            sha256=chk["sha256"],
            content_id=cid,
            positive_pixels=chk["positive_pixels"],
            format_ok=chk["ok_to_upload"],
            hard_failures=chk["hard_failures"],
            checks=chk["checks"],
        )
        print(json.dumps({kk: recs[suffix][kk] for kk in ("file", "bytes", "sha256", "content_id",
                                                          "positive_pixels", "format_ok")}, indent=1), flush=True)

    zpath = zip_single(out / recs["zeros"]["file"])
    note = f"GEMSDOE25 H66-1 MGD-C sapd3.0 | {args.verdict_note} | id {cid}"
    assert len(note) <= 120, f"Note exceeds 120 chars ({len(note)}): {note}"

    receipt = dict(
        primary_outside="zeros",
        note=note,
        note_chars=len(note),
        files=recs,
        zip=dict(file=zpath.name, path=f"docs/downloads/{zpath.name}", bytes=zpath.stat().st_size),
        shield_diagnostics=shield_diag,
        build=dict(
            base=BASE,
            extras=EXTRAS,
            tip_column="H27_tip",
            h34_columns=H34_NAMES,
            h66_mgd_columns=H66_MGD_NAMES,
            flank_radius_px=FLANK_RADIUS_PX,
            tip_preserve_threshold=TIP_PRESERVE_THR,
            kfrac=KFRAC,
            min_dist=MIN_DIST,
            draws=args.draws,
            base_seed=BASE_SEED,
            seconds=round(time.time() - t0, 1),
            utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            scores="work_dir()/h66_full_scores.npy (gitignored cache)",
        ),
        verdict_note=args.verdict_note,
        label="HOLDOUT-DTI only; not an organizer-confirmed competition score (see registry/run_card_h66_2026-10-25.json)",
    )
    receipt_path = out / f"checks-{Path(recs['zeros']['file']).stem}.json"
    receipt_path.write_text(json.dumps(receipt, indent=1) + "\n")
    print("NOTE:", note, f"({len(note)} chars)")
    print("RECEIPT:", receipt_path.name)


if __name__ == "__main__":
    main()
