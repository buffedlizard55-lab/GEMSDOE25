#!/usr/bin/env python3
"""Render README.md: status and result tables come from registry/ + evidence/, the owner brief from knowledge/owner_brief_verbatim.txt."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def J(p):
    return json.loads((ROOT / p).read_text())


def opt(p):
    f = ROOT / p
    return json.loads(f.read_text()) if f.exists() else None


def main() -> None:
    subs = J("registry/submissions.json")["files"]
    primary = next(s for s in subs if s["role"] == "primary")
    others = [s for s in subs if s["role"] != "primary"]
    ls = J("registry/live_scores.json")
    snap = ls["leaderboard_snapshot"]
    fac = J("evidence/factorial/results.json")
    why = J("evidence/why_0_2477.json")
    emu = J("evidence/emission_model.json")
    add = opt("evidence/addons/results.json")
    irr = J("registry/irregularities.json")["issues"]
    best = max(a["score"] for a in ls["artifacts"] if a["score"] is not None)
    brief = (ROOT / "knowledge" / "owner_brief_verbatim.txt").read_text().rstrip()
    L = []
    A = L.append
    A("# GEMSDOE25 — designed-factorial fault discovery for the DOE GEMS Prize\n")
    A("> **Maximize P(Win)** · **Own the Outcome** — the Arena core values are the decision rule for every change in this repository.\n")
    A("**Competition:** [DOE GEMS Prize, DrivenData #306](https://www.drivendata.org/competitions/306/competition-doe-gems/) · "
      "**Live site:** <https://buffedlizard55-lab.github.io/GEMSDOE25/> · **Weekly limit:** 3 submissions · "
      "**Ends:** 3 Dec 2026 (page: 11:59 p.m. UTC; rules: 5:00 p.m. ET — see IR-25-DEADLINE)\n")
    A("## ⬇ Download the submission file\n")
    A(f"**[↓ `{primary['file']}`](docs/downloads/{primary['file']})** — {primary['summary']}\n")
    A(f"* Format: single-band float32 GeoTIFF, EPSG:32611, 3730 × 3292, 100 m, values in [0, 1] at **all 5,167,373 footprint pixels**, NaN outside "
      f"(verified against the organizers' template; independent check receipt: `docs/downloads/{primary['receipt']}`).")
    A(f"* Unique content id `{primary['content_id']}` · SHA-256 `{primary['sha256']}` · {primary['positive_pixels']:,} emitted pixels · status: **{primary['status']}**.")
    A(f"* **Note to paste** in DrivenData's *Note (optional)* field: `{primary['note']}`")
    for o in others:
        A(f"* Also: [`{o['file']}`](docs/downloads/{o['file']}) — {o['title']} ({o['status']}; {o['positive_pixels']:,} px).")
    A("* Step-by-step upload guide: [`docs/executive-summary.html`](https://buffedlizard55-lab.github.io/GEMSDOE25/docs/executive-summary.html).\n")
    A("## Where things stand\n")
    A(f"* Leaderboard snapshot ({snap['read_utc']}, human-read): **#1 {snap['top10'][0]['participant']} {snap['top10'][0]['best_public_dti']:.4f}**; rank #5 {snap['top10'][4]['best_public_dti']:.4f}. "
      f"Group best (owner-reported) **{best:.4f}** = rank #16 (`wbg1`, by equal value). Gap: +{snap['gap_to_rank5']:.3f} to rank #5, +{snap['gap_to_rank1']:.3f} (+{100 * snap['relative_gain_needed_for_rank1']:.0f} %) to #1.")
    A("* **Root cause of the portal error** (`Predicted values must be in range [0, 1]`): the previous GEMSDOE25 file used an invented footprint — "
      "2,344,929 of the 5,167,373 official footprint pixels were NaN (NaN fails every range test) and it emitted 1,249,834 positive pixels. Fixed and tested "
      "(`evidence/old_gems25_tif_forensics.json`, `src/gems25/submission.py`). The cause is inferred from the data; the portal validator is not public.")
    r = why["relations"]
    A(f"* **Why 0.2477:** the file is *exactly* `dot_thin(H19-5, 1.5)` — a pixel-identical deterministic subset ({r['pixel_retention_d1_5'] * 100:.1f} % of H19-5's pixels, none on a catalogue pixel). "
      f"Same detections, half the false-positive mass; geometric credit retention ≈ {r['geometric_credit_retention_d1_5']:.2f}. Two live-score readings agree on |G| ≈ 12.5–12.8 k px.")
    d28 = emu["d2_8"]
    A(f"* **Can we beat 0.2477?** The calibrated emission model gives **{d28['model_dti']:.4f}** (band {d28['model_dti_low']:.4f}–{d28['model_dti_high']:.4f}) for the denser-thinned `dot_thin(H19-5, 2.4)` "
      "(44,090 px) — a model, not a score. Beating **0.3195** needs new information or a much better detector; nothing in this repository demonstrates that.")
    A("")
    A("## Designed factorial experiment (replaces one-factor-at-a-time)\n")
    A(f"2^(5−1), Resolution V, generator E = ABCD → {fac['design']['runs']} runs × {fac['design']['cells_per_run']} spatially blocked hide-and-recover cells; response = exact sparse-regime DTI. "
      f"Lenth ME = {fac['effects_dti']['lenth']['me']:.4f}. Pre-registered before the run (`knowledge/04_preregistered_factorial_2026-10-02.md`).\n")
    A("| Factor | Family | Class | Main effect (DTI) | Folds + |")
    A("|---|---|---|---|---|")
    for k, v in fac["classification"].items():
        A(f"| {k} | {v['label']} | **{v['classification']}** | {v['main_effect']:+.4f} | {v['folds_positive']}/4 |")
    A("")
    A("Top interactions: " + ", ".join(f"`{k}` {v:+.4f}" for k, v in fac["ranked_interactions"][:4]) + ". Full tables: [`evidence/factorial/results.md`](evidence/factorial/results.md).\n")
    if add:
        A("## Add-on hypotheses (pre-registered gate, paired)\n")
        A("| Arm | mean DTI | Δ vs base | folds + | gate |")
        A("|---|---|---|---|---|")
        A(f"| BASE `{add['base']}` | {add['BASE']['mean_dti']:.4f} | — | — | — |")
        for k, v in add["arms"].items():
            g = v["gate_vs_base"]
            A(f"| {k} | {v['mean_dti']:.4f} | {g['mean_gain']:+.4f} | {g['folds_positive']}/4 | {'pass' if g['passed'] else 'fail'} |")
        em = add["EM0_equal_N"]
        A(f"| EM-0 score-ordered dots vs `dot_thin` (equal N≈{em['n_eq_mean']:.0f}) | {em['sapd']:.4f} vs {em['dot_thin']:.4f} | {em['gate_sapd_vs_dot_thin']['mean_gain']:+.4f} | {em['gate_sapd_vs_dot_thin']['folds_positive']}/4 | {'pass' if em['gate_sapd_vs_dot_thin']['passed'] else 'fail'} |")
        A("")
    A("## Flagged for review (full list with evidence: [`registry/irregularities.json`](registry/irregularities.json))\n")
    for i in irr:
        if i["severity"] in ("critical", "high"):
            A(f"* **{i['id']}** ({i['severity']}, {i['status']}) — {i['issue'][:260]}{'…' if len(i['issue']) > 260 else ''}")
    A("")
    A("## Limitations and what is needed\n")
    A("1. **No DrivenData login** → the original competition files, live leaderboard and uploads are out of reach; every competition raster here is an owner mirror (hash-pinned, not authenticated). DrivenData's Terms of Use forbid automatic access, so scores are *typed by the owner* (`scripts/record_live_score.py`).")
    A("2. **Network:** the sandbox reaches github.com and PyPI (plus an HTML page-fetch tool); `sciencebase.gov`, `gdr.openei.org`, `dropbox.com`, `docs.nlr.gov` are unreachable from code, so raw 3DEP tiles, the slip/dilation-tendency shapefile and heat-flow rasters need a networked runner (GitHub Actions).")
    A("3. **Compute:** 2 CPUs / 4 GB RAM, no GPU → boosted trees, not the reference U-Net; no raw 1 m DEM processing.")
    A("4. **The proxy is not the truth:** the hide-and-recover holdout hides catalogue components; proxy-vs-live correlation measured by the group was weak (Spearman +0.33, n = 24, n.s.). Live scores (3 per week) are the only real validation.")
    A("5. **Hidden labels, public/private split and the portal validator are undisclosed.**\n")
    A("## Next work (order matters)\n")
    A(f"1. **Owner:** upload the primary file once; record the score (`python scripts/record_live_score.py --file {primary['content_id']} --score 0.xxxx`); the emission model then has three live anchors and is re-fit.")
    A("2. Run the exploratory surface in a *separate* slot only after step 1; record it.")
    A("3. Add a networked fetch workflow for the USGS slip/dilation-tendency shapefile (H26-4), GDR heat-flow rasters and Qfaults v2; extend the factorial with H26-1/2/3 as *factors* (2^(7−3), Resolution IV) instead of testing them one at a time.")
    A("4. Rebuild the LiDAR descriptors from raw 3DEP tiles on CI and implement scarp cross-profile templates (highest ceiling).")
    A("5. Owner decisions listed in IR-25-SCORE-IDENTITY, IR-25-TOU, IR-25-PUBLIC-DATA, IR-25-DEADLINE.\n")
    A("## Standing session charter\n")
    A("Read this README **and the verbatim brief below** at the start of every session, then `AGENTS.md`. First commands: `git fetch origin`, compare with the session branch, `gh pr list --state open`. Pre-register before running. No weekly slot without passing the gate or an explicit owner exception. Never automate drivendata.org. Review in three passes. Unknown stays unknown.\n")
    A("## Reproduce\n")
    A("```bash\npython -m venv .venv && .venv/bin/pip install -r requirements.txt\n.venv/bin/python scripts/restore_data.py --group all          # SHA-256-pinned inputs from the owner's public repos -> data/ (ignored by Git)\n.venv/bin/python scripts/build_features.py && .venv/bin/python scripts/build_addons.py\n.venv/bin/python scripts/run_factorial.py && .venv/bin/python scripts/analyze_factorial.py\n.venv/bin/python scripts/run_addons.py && .venv/bin/python scripts/analyze_addons.py\n.venv/bin/python scripts/analyze_scored_rasters.py && .venv/bin/python scripts/emission_model.py\n.venv/bin/python scripts/build_candidate.py --help             # train on the full catalogue, emit, verify, package\n.venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py\n.venv/bin/python -m pytest -q\n```\n")
    A("Set `GEMS_DATA_DIR` / `GEMS_WORK_DIR` to keep the 419 MB raster and the ~1.5 GB feature cache outside the checkout.\n")
    A("## Repository map\n")
    A("| Path | Role |\n|---|---|\n| `src/gems25/` | metric (official DTI + brute-force twin), hide-and-recover holdout, thinning/NMS, families & features, factorial engine, experiment cells, strict submission writer/checker |\n| `scripts/` | restore, build, run, analyse, package, site, README, feed, score recorder |\n| `registry/` | sources (with verification status), irregularities, score ledger, data pins, shipped submissions |\n| `evidence/` | machine-readable results and forensics |\n| `knowledge/` | pre-registrations, ranked hypotheses, verified research digest, the brief |\n| `docs/`, `index.html` | GitHub Pages site (root `index.html` is the landing page; Pages builds from `main:/`) |\n| `tests/` | unit, parity, integrity and reproduction tests |\n")
    A("## Owner brief (verbatim) — read every session\n")
    A("<details><summary><strong>Full text of the owner's brief for this session</strong> (copied from the task message of 2026-10-02; link markup and whitespace as pasted)</summary>\n")
    A("```text\n" + brief + "\n```\n")
    A("</details>\n")
    (ROOT / "README.md").write_text("\n".join(L))
    print("README.md written,", len("\n".join(L)), "chars")


if __name__ == "__main__":
    main()
