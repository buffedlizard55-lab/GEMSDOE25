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
    conf = opt("evidence/addons_confirm/results.json")
    h27_screen = opt("evidence/h27_screen/results.json")
    h27_confirm = opt("evidence/h27_confirm/results.json")
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
    A("## ⬇ Download the format-validated GeoTIFF (not slot-approved)\n")
    A(f"**[↓ `{primary['file']}`](docs/downloads/{primary['file']})** — {primary['summary']}\n")
    A(f"* Format: single-band float32 GeoTIFF, EPSG:32611, 3730 × 3292, 100 m, values in [0, 1] at **all 5,167,373 footprint pixels**, NaN outside "
      f"(verified against the pinned owner-mirror template, not organizer-authenticated; independent check receipt: `docs/downloads/{primary['receipt']}`).")
    A(f"* Unique content id `{primary['content_id']}` · SHA-256 `{primary['sha256']}` · {primary['positive_pixels']:,} emitted pixels · status: **{primary['status']}**.")
    A(f"* **Note to paste** in DrivenData's *Note (optional)* field: `{primary['note']}`")
    for o in others:
        if o["role"] == "fallback":
            A(f"* Format fallback (format troubleshooting only; not slot-approved): [`{o['file']}`](docs/downloads/{o['file']}) — {o['title']} ({o['status']}; {o['positive_pixels']:,} px).")
    A("* Step-by-step upload guide: [`docs/executive-summary.html`](https://buffedlizard55-lab.github.io/GEMSDOE25/docs/executive-summary.html).\n")
    A("## Where things stand\n")
    A(f"* **Unverified leaderboard claims** (reported {snap['reported_utc']}; no organizer page or receipt was accessed): #1 {snap['top10'][0]['participant']} {snap['top10'][0]['best_public_dti']:.4f}; reported rank #5 {snap['top10'][4]['best_public_dti']:.4f}. "
      f"The group-best claim is **{best:.4f}**; the previously reported rank #16/account association is not authenticated. These are not independently verified scores; apparent gaps to ranks #5/#1 are arithmetic on supplied claims only.")
    A("* **Root cause of the reported portal error** (`Predicted values must be in range [0, 1]`): the previous GEMSDOE25 file used an invented footprint — "
      "2,344,929 of the 5,167,373 owner-mirror template-footprint pixels were NaN (NaN fails every range test) and it emitted 1,249,834 positive pixels. Fixed and tested "
      "(`evidence/old_gems25_tif_forensics.json`, `src/gems25/submission.py`). The cause is inferred from the data; the portal validator is not public.")
    r = why["relations"]
    A(f"* **Local audit of the reported 0.2477 raster (score unverified):** it is *exactly* `dot_thin(H19-5, 1.5)` — a pixel-identical deterministic subset ({r['pixel_retention_d1_5'] * 100:.1f} % of H19-5's pixels, none on a catalogue pixel). "
      f"This verifies the raster transformation, not the claimed competition DTI. No organizer receipt/page was accessed; the claimed 0.2477 and 0.3195 remain unverified.")
    d28 = emu["d2_8"]
    A(f"* **Model-only calibration:** if the supplied 0.2477 score claim is correct, the emission model predicts **{d28['model_dti']:.4f}** (band {d28['model_dti_low']:.4f}–{d28['model_dti_high']:.4f}) for `dot_thin(H19-5, 2.4)` "
      "(44,090 px). This is an extrapolation on owner/user-provided score anchors, not independent evidence or a score; no comparison to the unverified 0.3195 claim is established.")
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
    if conf:
        A("## Confirmation replicate (fresh draws 2,3; pre-registered)\n")
        A("| Arm | mean DTI | Δ vs BDE | folds + | gate |")
        A("|---|---|---|---|---|")
        A(f"| BASE `{conf['base']}` | {conf['BASE']['mean_dti']:.4f} | — | — | — |")
        for k, v in conf["arms"].items():
            g = v["gate_vs_base"]
            A(f"| {k} | {v['mean_dti']:.4f} | {g['mean_gain']:+.4f} | {g['folds_positive']}/4 | {'pass' if g['passed'] else 'fail'} |")
        em = conf["EM0_equal_N"]
        A(f"| EM-0 score-ordered dots vs `dot_thin` | {em['sapd']:.4f} vs {em['dot_thin']:.4f} | {em['gate_sapd_vs_dot_thin']['mean_gain']:+.4f} | {em['gate_sapd_vs_dot_thin']['folds_positive']}/4 | {'pass' if em['gate_sapd_vs_dot_thin']['passed'] else 'fail'} |")
        A("\n`CFG_*` rows are whole family sets (e.g. `CFG_BE` = the factorial's predicted-best corner, which did not replicate its predicted 0.145).\n")
    A("## Score ledger — user/owner-reported claims (not organizer-verified; full ledger in `registry/live_scores.json`)\n")
    A("| Project | Submission | Score | Note |")
    A("|---|---|---|---|")
    for a_ in sorted((x for x in ls["artifacts"] if x["score"] is not None), key=lambda x: -x["score"])[:10]:
        A(f"| {a_['project']} | `{a_['label']}` | {a_['score']:.4f} | {a_['note']} |")
    A("")
    A("## Prior H26 register — outcomes (ranked before its runs; not a list of untried work)\n")
    A("| Rank | ID | Idea | Recorded outcome |")
    A("|---|---|---|---|")
    A("| 1 | H26-0 | score-aware Poisson-disk dotting + marginal-ratio budget | **passes** (+0.0037 vs score-blind dotting at equal N, 4/4 folds, replicated +0.0034) |")
    A("| 2 | H26-2 | strike-compatibility prior (DEM line orientation × visible-catalogue strike) | alone: fail on draws 0,1 (+0.0015, 2/4), small pass on fresh draws 2,3 (+0.0033, 3/4); jointly passes both |")
    A("| 3 | H26-1 | oriented cross-scarp radiometric contrast (K, Th/K, U/K × DEM normal) | alone: fail on draws 0,1 (+0.0006, 2/4), small pass on draws 2,3 (+0.0026, 4/4); jointly passes both |")
    A("| 4 | H26-3 | concealed joint step (gravity ∧ magnetic ridge, basement-depth step) | alone: fail on draws 0,1 (+0.0003, 2/4), small pass on draws 2,3 (+0.0032, 4/4); jointly passes both |")
    A("| 5 | H26-4 | dilation-tendency-weighted orientation prior (USGS 10.5066/P9YL58W6) | page-listed shapefile; direct access failed, bytes/licence not verified |")
    A("")
    if h27_confirm:
        h27_status = "confirmation passed" if h27_confirm["slot_eligible"] else "confirmation failed; do not promote"
        h27_metrics = h27_confirm["arms"]["TS"]["mean_dti"]
    elif h27_screen:
        h27_status = "screen passed; confirmation draws 6,7 required" if h27_screen["slot_eligible"] else "screen failed; stop, no slot"
        h27_metrics = h27_screen["arms"]["TS"]["mean_dti"]
    else:
        h27_status, h27_metrics = "pre-registered for draws 4,5; not yet scored", None
    A("## Current ranked geological candidates (H27; full layers, signatures, costs and preregistration in `knowledge/09_preregistered_hypotheses_2026-10-02.md`)\n")
    A("| Rank | ID | Idea | Expected proxy ΔDTI (planning bracket) | Status |")
    A("|---|---|---|---|---|")
    h27_result = f"TS DTI {h27_metrics:.6f}; {h27_status}" if h27_metrics is not None else h27_status
    A(f"| 1 | H27-1 | directed visible-fault-tip continuation × multi-scale DEM/LiDAR scarp | +0.001 to +0.010 | {h27_result} |")
    A("| 2 | H27-2 | residualized GDR 2 m temperature probes | 0 to +0.010 | blocked: binary/schema/coverage not fetched |")
    A("| 3 | H27-3 | paleo-geothermal deposits away from visible traces | 0 to +0.005 | blocked: binary/schema/coverage not fetched |")
    A("| 4 | H27-4 | USGS heat-flow residual × structural/scarp support | 0 to +0.005 | blocked: binary, residual definition and licence not verified |")
    A("\nThese ΔDTI ranges are planning judgments, not estimates. No weekly slot is eligible unless the tested candidate beats the 0.152003389 holdout comparator and also passes paired confirmation; the site never uploads automatically.\n")
    A("## Flagged for review (full list with evidence: [`registry/irregularities.json`](registry/irregularities.json))\n")
    for i in irr:
        if i["severity"] in ("critical", "high"):
            A(f"* **{i['id']}** ({i['severity']}, {i['status']}) — {i['issue'][:260]}{'…' if len(i['issue']) > 260 else ''}")
    A("")
    A("## Limitations and what is needed\n")
    A("1. **No competition credentials or organizer receipts.** Every competition raster is an owner mirror (hash-pinned, not organizer-authenticated). The 0.2477 result and 0.3195 leader are user-provided, unverified claims; no competition/leaderboard page was accessed. Do not automate or monitor DrivenData.")
    A("2. **External binaries are blocked here:** GDR 1391 lists the 2 m probe and paleo-geothermal files under CC BY 4.0, but direct downloads failed; the USGS heat-flow ZIP is page-listed, but its bytes and licence were not verified. H27-2/3/4 require a networked runner and source/coverage checks before use.")
    A("3. **Compute:** 2 CPUs / 4 GB RAM, no GPU → boosted trees, not the reference U-Net; no raw 1 m DEM processing. The H27 screen ran in about 14 minutes after the feature cache was built.")
    A("4. **The proxy is not the truth:** the hide-and-recover holdout hides catalogue components; proxy-vs-live correlation in the group's prior record was weak (Spearman +0.33, n = 24, n.s.). Holdout wins are necessary, not sufficient.")
    A("5. **Hidden labels, public/private split, source authenticity, score claims and the portal validator remain undisclosed/unverified.**\n")
    A("## Next work (order matters)\n")
    if h27_confirm:
        if h27_confirm["slot_eligible"]:
            A("1. H27-1 passed the preregistered confirmation proxy gates. Package a full-data candidate from the confirmed model, validate its exact GeoTIFF and hash, and review it before any manual slot use. The existing D2.8 download is not that candidate.")
        else:
            A("1. H27-1 failed fresh-draw confirmation. Stop; do not use a weekly slot. Any new idea requires a new preregistration.")
    elif h27_screen:
        if h27_screen["slot_eligible"]:
            A("1. H27-1 screen passed; run the frozen confirmation on draws 6,7 before packaging. No weekly slot is eligible until that fresh-draw confirmation passes.")
        else:
            A("1. H27-1 failed the absolute holdout-comparator gate on draws 4,5. Stop per preregistration; do not run confirmation or spend a slot. A T-only follow-up is unconfirmed and would need its own preregistration and fresh holdout validation.")
    else:
        A("1. Run the frozen H27-1 screen on draws 4,5 (`python scripts/run_h27.py --stage screen && python scripts/analyze_h27.py --dir evidence/h27_screen`); do not skip or alter the absolute comparator gate.")
    A("2. On a networked runner, retrieve the official GDR probe/paleo files and USGS heat-flow ZIP; verify checksums, schema, coverage, residual definitions and licence before preregistering any new test.")
    A("3. Keep the D2.8 file format-validated but unscored/not slot-approved. Only package and consider a specific candidate after it beats the 0.152003389 spatial holdout best under a prespecified paired test and (when specified) fresh-draw confirmation.")
    A("4. If organizer verification of 0.2477/0.3195 is needed, use an independently supplied non-sensitive receipt; this repository will not fetch or monitor DrivenData.")
    A("5. Owner decisions remain in IR-25-SCORE-IDENTITY, IR-25-TOU, IR-25-PUBLIC-DATA, IR-25-DEADLINE, and IR-27-EXTERNAL-DATA-ACCESS.\n")
    A("## Standing session charter\n")
    A("Read this README **and the verbatim brief below** at the start of every session, then `AGENTS.md`. First commands: `git fetch origin`, compare with the session branch, `gh pr list --state open`. Pre-register before running. No weekly slot unless that specific candidate beats the current holdout best and passes the exact-file audit; no exception is authorized here. Never automate drivendata.org. Review in three passes. Unknown stays unknown.\n")
    A("## Reproduce\n")
    A("```bash\npython -m venv .venv && .venv/bin/pip install -r requirements.txt\n"
      ".venv/bin/python scripts/restore_data.py --group all          # SHA-256-pinned inputs from the owner's public repos -> data/ (ignored by Git); same as: bash scripts/download_competition_data.sh\n"
      ".venv/bin/python scripts/build_features.py && .venv/bin/python scripts/build_addons.py\n"
      "# pre-registered experiments (knowledge/04, 05)\n"
      ".venv/bin/python scripts/run_factorial.py && .venv/bin/python scripts/analyze_factorial.py            # ~30 min on 2 CPUs\n"
      ".venv/bin/python scripts/run_addons.py && .venv/bin/python scripts/analyze_addons.py                  # draws 0,1\n"
      ".venv/bin/python scripts/run_addons.py --out evidence/addons_confirm --draws 2 3 --extra-configs ABCDE BE E && .venv/bin/python scripts/analyze_addons.py --dir evidence/addons_confirm\n"
      ".venv/bin/python scripts/run_emk_extension.py --base BDE --extras X1_K X1_ThK X1_UK X2_compat X2_compat_coh X3_gm X3_gd   # post hoc (Addendum A)\n"
      "# H27-1 frozen 2x2 screen (knowledge/09); confirmation is permitted only if screen gate passes\n"
      ".venv/bin/python scripts/run_h27.py --stage screen && .venv/bin/python scripts/analyze_h27.py --dir evidence/h27_screen\n"
      "# if and only if the screen's absolute + paired gates pass:\n"
      ".venv/bin/python scripts/run_h27.py --stage confirm && .venv/bin/python scripts/analyze_h27.py --dir evidence/h27_confirm\n"
      "# forensics and emission model\n"
      ".venv/bin/python scripts/analyze_scored_rasters.py && .venv/bin/python scripts/emission_model.py && .venv/bin/python scripts/validate_emission_model.py && .venv/bin/python scripts/harness_references.py\n"
      "# files, site, README\n"
      ".venv/bin/python scripts/build_candidate.py --help            # train on the full catalogue, emit, verify (exploratory surface)\n"
      ".venv/bin/python scripts/package_submissions.py --exploratory-receipt docs/downloads/checks-<file>.json\n"
      ".venv/bin/python scripts/build_data_dictionary.py && .venv/bin/python scripts/build_site.py && .venv/bin/python scripts/build_readme.py\n"
      ".venv/bin/python -m pytest -q && .venv/bin/python -m ruff check src scripts tests\n```\n")
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
