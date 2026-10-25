#!/usr/bin/env python3
"""Build GEM-FUSE1: GEM-1 blind magnetics surface + B=2 catalogue pruning (H33-2 on new detector).
Writes both -nan and -zeros variants, checks lane vs registry, runs quick holdout screen.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, time
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr
import rasterio

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"scripts"))
from gems25.paths import data_dir, work_dir
from gems25.submission import check_file, write_submission, content_id, make_filename, make_note
from gems25.experiment import load_context
from gems25.thinning import ridge_nms, select_top_positive, score_ordered_dots
import validate_gem_candidate as vgc

KFRAC=0.0245
MIN_DIST=1.5
PRUNE_PX=2.0

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1<<20),b""): h.update(c)
    return h.hexdigest()

t0=time.time()
ctx=load_context(work_dir())
foot, lab = ctx.foot, ctx.labels
bands=work_dir()/ "bands"
surf=vgc.surface_gem1(foot, bands)
print(f"surface built: {np.nanmin(surf[foot]):.4f}..{np.nanmax(surf[foot]):.4f}")

# emission full footprint: same as GEM-1 builder but with 2.4? Use validated 1.5 + prune2
H,W=foot.shape
k=int(round(KFRAC*int(foot.sum())))
print(f"budget k={k} ({KFRAC*100:.2f}% of footprint)")
g=np.where(foot & np.isfinite(surf), surf, 0.0).astype(np.float32)
r=ridge_nms(g, foot, 1.0)
sc=np.where(r & ~lab, g, 0.0)
top=select_top_positive(sc, foot, k)
dots=score_ordered_dots(g, top, MIN_DIST)
print(f"dots before prune {dots.sum()}")

# prune within PRUNE_PX of catalogue (full footprint visible = lab)
dist = distance_transform_edt(~lab)
prune_mask = (dist <= PRUNE_PX) & foot
dots_pruned = dots & ~prune_mask
print(f"prune ≤{PRUNE_PX}px removes {(dots & prune_mask).sum()} dots -> {dots_pruned.sum()} remain")

assert not (dots_pruned & lab).any()
pred=np.where(dots_pruned,1.0,0.0).astype(np.float32)
tmpl=data_dir()/ "sample_submission.tif"
date=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
cid=content_id(pred, foot, lab)
out=Path(ROOT/"docs/downloads")
out.mkdir(parents=True, exist_ok=True)
slug="gem-fuse1-blind-magnetics-prune2"
fname=make_filename(slug, date, cid, "nan")
tif=write_submission(pred, tmpl, out/fname, outside="nan")
zero=write_submission(pred, tmpl, out/fname.replace("-nan.tif","-zeros.tif"), outside="zero")
chk=check_file(tif, tmpl)
chk0=check_file(zero, tmpl)
print(json.dumps(dict(file=chk["file"], bytes=chk["bytes"], sha256=chk["sha256"], content_id=cid, positive_pixels=chk["positive_pixels"], format_ok=chk["ok_to_upload"]), indent=1))
print("hard failures", chk["hard_failures"], "fallback ok", chk0["ok_to_upload"])

# lane check vs registry
REGDIR=ROOT/"data/scored"
lane_rows=[]
with rasterio.open(tmpl) as t:
    foot_tmpl=np.isfinite(t.read(1))
with rasterio.open(tif) as s:
    cand_arr=s.read(1)
cand_dots=(cand_arr>0)&foot_tmpl
sample_rng=np.random.default_rng(0)
fidx=np.flatnonzero(foot_tmpl.ravel())
samp=np.sort(sample_rng.choice(fidx, min(400000, fidx.size), replace=False))
cvals=cand_arr.ravel()[samp]
for p in sorted(REGDIR.glob("*.tif")):
    with rasterio.open(p) as r:
        if r.shape!=cand_arr.shape: continue
        rv=r.read(1)
    rho=float(spearmanr(cvals, rv.ravel()[samp]).correlation)
    rdots=(rv>0)&foot_tmpl
    d2r=distance_transform_edt(~rdots) if rdots.any() else np.full(cand_arr.shape,np.inf)
    ov=float((d2r[cand_dots]<=3).mean()) if cand_dots.any() else 0.0
    d2c=distance_transform_edt(~cand_dots) if cand_dots.any() else np.full(cand_arr.shape,np.inf)
    ov_rev=float((d2c[rdots]<=3).mean()) if rdots.any() else 0.0
    flag=rho>0.90 or ov>0.70
    lane_rows.append(dict(file=p.name, spearman=round(rho,6), dots_within_3px=round(ov,6), registry_dots_within_3px_of_candidate=round(ov_rev,6), registry_dots=int(rdots.sum()), flag=flag))
    print(f"  {p.name[:60]:60s} rho={rho:+.3f} ov={ov:.3f} rev={ov_rev:.3f} {'DUP' if flag else 'ok'}")

flagged=[r for r in lane_rows if r["flag"]]
print(f"flagged {len(flagged)} / {len(lane_rows)}")
# detect lattice artefact
for r in lane_rows:
    if "lattice" in r["file"]:
        print(f"lattice {r['file']} overlap {r['dots_within_3px']} is density artefact if >0.7 (dense grid 206k dots)")

# save receipts
note=make_note("GEM-FUSE1", "blind magnetics + B2 prune 2px 2.45pct", cid, limit=120)
rec=dict(file=tif.name, path=f"docs/downloads/{tif.name}", bytes=tif.stat().st_size, sha256=chk["sha256"], content_id=cid, positive_pixels=int(dots_pruned.sum()), dots_before_prune=int(dots.sum()), pruned=int((dots&prune_mask).sum()), format_ok=chk["ok_to_upload"], checks=chk["checks"], note=note, build=dict(surface="GEM-1 norm|grad RTP|x(1-norm relief)", kfrac=KFRAC, min_dist=MIN_DIST, prune_px=PRUNE_PX, seconds=round(time.time()-t0), utc=dt.datetime.now(dt.timezone.utc).isoformat()), lane_rows=lane_rows, flagged=[r["file"] for r in flagged], fallback=dict(file=zero.name, sha256=chk0["sha256"], bytes=zero.stat().st_size, format_ok=chk0["ok_to_upload"]))
(out/f"checks-{tif.stem}.json").write_text(json.dumps(rec,indent=1)+"\n")
(out/f"lane-{tif.stem}.json").write_text(json.dumps(dict(candidate=tif.name, sha256=chk["sha256"], candidate_dots=int(dots_pruned.sum()), thresholds=dict(spearman_max=0.90, dots_within_3px_max=0.70, dist_px=3.0), flagged=[r["file"] for r in flagged], rows=lane_rows), indent=1)+"\n")
print("note:", note, len(note))
print(f"done in {time.time()-t0:.0f}s")

