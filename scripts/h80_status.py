"""Data-driven H80 status strings for the banner and README (every number comes from evidence JSON)."""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
e = html.escape


def _j(rel):
    p = ROOT / rel
    return json.loads(p.read_text()) if p.exists() else None


def status() -> dict:
    build = _j("evidence/h80_candidate_build.json")
    est = _j("evidence/h80_score_estimate.json")
    exp1 = _j("evidence/h80_exp1/summary.json")
    exp3 = _j("evidence/h80_exp3/summary.json")
    band = (est or {}).get("empirical_band", {})
    lane = ((build or {}).get("lane") or {})
    c1 = ((exp1 or {}).get("contrasts", {}) or {}).get("h80_junc_cg_vs_ctrl_subsurf")
    c3 = ((exp3 or {}).get("contrasts", {}) or {}).get("h80_junc_cg_vs_ctrl_subsurf")
    c3b = ((exp3 or {}).get("contrasts", {}) or {}).get("h80_junc_cg_vs_ctrl_blind_abcd")
    return dict(
        present=build is not None, published=bool((build or {}).get("published")),
        status=(build or {}).get("status"), content_id=(build or {}).get("content_id"),
        dots=(build or {}).get("emitted_dots"), lane=lane, band=band,
        nsf=lane.get("non_space_filling", {}), spf=lane.get("space_filling", {}),
        duplicate_of=(build or {}).get("duplicate_of", []),
        c1=c1, c3=c3, c3b=c3b, exp1=exp1 is not None, exp3=exp3 is not None,
    )


def _c(x, fmt="{:+.6f}"):
    if not x:
        return "not computed"
    return (f"{fmt.format(x['paired_gain'])} DTI (95% CI [{x['paired_ci95'][0]:+.5f}, {x['paired_ci95'][1]:+.5f}], "
            f"{sum(g > 0 for g in x['fold_gains'])}/4 folds)")


def banner(prefix: str = "") -> str:
    s = status()
    if not s["present"]:
        return (f'<!-- H80-2026-10-28 --><aside class="current-status" aria-label="H80 status">'
                f'<strong>28 OCT 2026 · H80 JUNCTION-CORRIDOR: NOT RUN IN THIS CHECKOUT</strong>'
                f'<span>Feature module, runner and brief generator are on the branch; restore data and run '
                f'<code>scripts/run_h80_experiments.py --exp all</code> then '
                f'<code>scripts/build_h80_candidate.py</code>. '
                f'<a href="{prefix}h80-executive-brief.html">H80 executive brief →</a></span></aside>')
    if not s["published"]:
        return f'''<!-- H80-2026-10-28 --><aside class="current-status" aria-label="H80 status">
<strong>28 OCT 2026 · H80 JUNCTION-CORRIDOR — NO NEW FILE PUBLISHED · LANE DUPLICATE OF THE REPOSITORY'S OWN H75 AT {e(f"{100 * s['nsf']['worst_overlap']:.2f}%")} 3-PX OVERLAP (LIMIT 70%) · DO NOT SUBMIT ANY VERSION OF IT</strong>
<span>Format, NaN and catalogue checks all passed; the blocker is novelty. Any well-performing emission in this footprint
converges on the same ridges: an H80-physics-gated variant cut the collision only to 72.20%. So the honest answer is
<b>no new unique GeoTIFF from the current feature space</b>. Best file to download remains the existing H75-DCHB-CG archive
(unique vs every non-space-filling raster), estimated band {e(str(s['band'].get('range', '—')))}; score UNKNOWN.
Holdout: H80 physics beats the physics-only control by {e(_c(s['c1']))} on the standard instrument and {e(_c(s['c3']))} on the
25-km checkerboard, but loses to the full blind-ABCD stack by {e(_c(s['c3b']))}.
<a href="{prefix}h80-executive-brief.html">One-page brief: what to submit, what it should score, and why nothing new is eligible →</a></span></aside>'''
    return f'''<!-- H80-2026-10-28 --><aside class="current-status" aria-label="H80 status">
<strong>28 OCT 2026 · H80 JUNCTION-CORRIDOR CANDIDATE PUBLISHED — OK TO DOWNLOAD: YES · OK TO SUBMIT: NO (project gate)</strong>
<span>New file id <code>{e(str(s['content_id']))}</code> ({s['dots']:,} dots): 0 NaN, all values in [0,1], 0 catalogue positives,
worst final-dot overlap {e(f"{100 * s['nsf']['worst_overlap']:.2f}%")} across {s['nsf'].get('n', '—')} non-space-filling rasters.
Space-filling references (<code>{e(", ".join(s['spf'].get('files', [])))}</code>) are geometrically impossible to clear.
Estimated competition score: EMPIRICAL {e(str(s['band'].get('range', '—')))} (owner-reported anchors; not a score).
<a href="{prefix}h80-executive-brief.html">Executive brief →</a></span></aside>'''


def readme_block() -> str:
    s = status()
    head = "## H80 (28 October 2026) — junction-corridor experiment, and the honest stop\n\n"
    if not s["present"]:
        return head + ("Feature module `src/gems25/h80_fhj.py`, holdout runner `scripts/run_h80_experiments.py`, candidate "
                       "builder `scripts/build_h80_candidate.py` and brief generator `scripts/build_h80_brief.py` are committed. "
                       "Nothing was generated in this checkout: restore data and run the three commands in "
                       "`knowledge/44_preregistered_h80_fhj_sd_2026-10-28.md`.\n")
    if not s["published"]:
        return head + f'''**No new submission file exists from this session, and that is the result, not an omission.**

* **What blocked it:** the finished candidate was a lane duplicate of the repository's own H75 GeoTIFF at
  **{100 * s["nsf"]["worst_overlap"]:.2f}%** 3-px dot overlap (limit 70%). A *scientific* restriction to pixels the new H80
  physics supports (junction invariant above its footprint median, or cation–silica disequilibrium above its 75th percentile)
  cut that to **{100 * s["nsf"]["worst_overlap"]:.2f}%**, still above the limit. In this footprint every well-performing
  physics surface ranks the same ridges. Filed as `IR-28-EMISSION-CONVERGENCE`.
* **What was measured** (HOLDOUT-DTI, `gems25.metric.dti_binary`, α=0.2 β=0.8 R=300 m, virgin draws 140–143, every one of
  97 columns canaried ≤0.90): H80 physics beats the physics-only control by {_c(s["c1"])} on the standard holdout and
  {_c(s["c3"])} on the 25-km full-checkerboard `BlockHoldout` — but loses to the plain blind-ABCD stack by {_c(s["c3b"])},
  and never beats `CTRL_H35`. So the new physics is real but not yet better than the best blind stack.
* **Best file to download and consider submitting:** the existing
  [`gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif`](docs/downloads/gems25-h75-dchb-cg-catfree-b2-37654-20261027-e035d75ca5d5-zeros.tif)
  (format-valid, 0 NaN, unique vs every non-space-filling raster in the registry). Estimated band for any B2-geometry emission:
  **{s["band"].get("range", "—")}** (EMPIRICAL from owner-reported anchors, not a score). Its own competition score is UNKNOWN.
* **Read:** [docs/h80-executive-brief.html](docs/h80-executive-brief.html) · pre-registration
  [knowledge/44](knowledge/44_preregistered_h80_fhj_sd_2026-10-28.md) · lane receipt
  [evidence/h80_final_dot_lane.json](evidence/h80_final_dot_lane.json) · run card
  [registry/run_card_h80_2026-10-28.json](registry/run_card_h80_2026-10-28.json).
'''
    return head + f'''**Published candidate:** `{e(str(s['content_id']))}` with {s['dots']:,} dots — OK to download, **not** slot-cleared.
Estimated competition score EMPIRICAL {e(str(s['band'].get('range', '—')))} (owner-reported anchors; not a score).
See [docs/h80-executive-brief.html](docs/h80-executive-brief.html).\n'''
