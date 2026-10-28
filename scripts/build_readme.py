#!/usr/bin/env python3
"""Generate README status and preserve each available owner-brief archive verbatim."""
from __future__ import annotations

import json
from pathlib import Path

try:
    from build_current_review import readme_status
except ImportError:
    from scripts.build_current_review import readme_status

ROOT = Path(__file__).resolve().parents[1]
BRIEFS = (
    ("Current owner brief 2026-10-28 — normalized, not verbatim", "current_project_brief_2026-10-28.md"),
    ("Owner brief 2026-10-27 (H75-DCHB-CG session) — saved as verbatim", "owner_brief_2026-10-27_verbatim.txt"),
    ("Current 2026-10-27 session scope — condensed, not verbatim", "owner_prompt_2026-10-27.txt"),
    ("Current standing protocol — normalized, not verbatim", "current_project_brief_2026-10-26.md"),
    ("Owner brief 2026-10-26 — saved as verbatim", "owner_brief_2026-10-26_verbatim.txt"),
    ("Owner brief 2026-10-25 — saved as verbatim", "owner_brief_2026-10-25_verbatim.txt"),
    ("Owner brief 2026-10-25 session 6 — reconstructed, not verbatim", "owner_brief_2026-10-25_s6_RECONSTRUCTED.txt"),
    ("Owner brief 2026-10-25 — consolidated, not verbatim", "owner_brief_2026-10-25_consolidated.md"),
    ("Session 8 scope — consolidated, not verbatim", "current_project_brief_2026-10-25_session8.md"),
    ("Continuation scope — consolidated, not verbatim", "current_project_brief_2026-10-03.md"),
    ("Session handoff — condensed, not verbatim", "current_session_brief_2026-10-25_66ca_CONDENSED.md"),
    ("Original owner brief (2026-10-02) — verbatim archive", "owner_brief_verbatim.txt"),
)


def main() -> None:
    subs = json.loads((ROOT / "registry/submissions.json").read_text())["files"]
    items = []
    seen = set()
    for entry in subs:
        cid = entry["content_id"]
        if cid in seen or not entry["file"].endswith("-zeros.tif"):
            continue
        seen.add(cid)
        items.append(f"| [{entry['file']}](docs/downloads/{entry['file']}) | `{cid}` | Inspection only; no slot approval |")
    h80 = json.loads((ROOT / "registry/run_card_h80_2026-10-28.json").read_text())
    h = h80["holdout_dti"]
    latest = f'''## Latest result — H80 blocked factorial screen, 28 October 2026

**OK TO SUBMIT: NO — DO NOT SUBMIT.** No new TIFF, calibrated competition estimate or weekly slot.
HOLDOUT-DTI **{h['dti']:.5f}**, 95% CI [{h['ci95'][0]:.5f}, {h['ci95'][1]:.5f}],
{h['withheld_positive_occurrences']:,} withheld-positive occurrences vs same-run H35 {h['comparator_dti']:.5f};
paired gain {h['paired_gain']:+.5f} (95% CI [{h['paired_ci95'][0]:+.5f}, {h['paired_ci95'][1]:+.5f}]).
Shared buffered 25-km tile-sampled component holdout, four quadrant clusters, draws 140–141;
alpha .2, beta .8, 300 m triangular kernel. All 792 feature/regime canaries pass.
This is a local catalogue-gap proxy, not an organizer score. One screen completed; experiments 2–3 withdrawn.

Data placement and the shared cache were restored successfully here; GPU training is not required for this diagnostic.
Scientific interpretation warning: mirrored `tc` is a magnetic derivative, not heatflow; `deq_n100a15` is a distance channel,
not event rate; quantized K/Th/U code-space ratios are not physical concentrations. No causal geothermal claim is validated.
At the frozen 37,654-dot budget, r13 forces at least **82.70%** overlap, so no packaging is allowed.
All 117 declared hashes are available but one registry transform is wrong; integrity is not full lane clearance.

[Executive summary and nine-site historical download table](docs/executive-summary.html) ·
[Full result, ranked hypotheses, sources and next steps](knowledge/45_h80_outcome_2026-10-28.md) ·
[JSON run card](registry/run_card_h80_2026-10-28.json) ·
[Three-pass review](registry/review_passes_h80_2026-10-28.json).
Only GEMSDOE25 is updated. Estimated competition score: **UNKNOWN / NOT ESTIMATED**.
Earlier dated decisions below are historical, not claims that this session ran no experiment.

'''
    from nine_site_status import readme_block as _nine_readme
    text = ["# GEMSDOE25 — designed-factorial fault discovery for the DOE GEMS Prize\n", _nine_readme(), latest, readme_status()]
    text.append("## Current review and reproducibility\n")
    text.append("[Executive summary and nine-site downloads](docs/executive-summary.html) · "
                "[current review](docs/current-review.html) · [historical archive](docs/history.html) · "
                "[three review passes](registry/review_passes_2026-10-27.json) · "
                "[irregularities](registry/irregularities.json) · [sources](registry/sources.json). "
                "Scores without organizer receipts are owner-reported, not verified.\n")
    text.append("To reproduce the audits without accessing the competition website:\n\n"
                "```sh\npython scripts/restore_data.py --group core\n"
                "python scripts/restore_data.py --group scored\n"
                "python scripts/fetch_top_scorers.py\n"
                "python scripts/audit_lane_feasibility.py --preregistration-commit 95149bc7373fc939313c1bb09cbc8940ed3fad78 --output evidence/lane_preflight_2026-10-27.json\n"
                "python scripts/audit_focus_winners.py\n"
                "python scripts/verify_candidate_independent.py docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif --require-zip\n"
                "python scripts/check_lane_duplicates.py docs/downloads/gems25-h78-mhscf-conduit-b2-sapd2-85-20261027-b2488f5d216c-zeros.tif --reference data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif  # exits 2: literal failure\n"
                "python scripts/verify_candidate_independent.py docs/downloads/gems25-h79-spatial-poisson-disc-b2-20261027-66772eeec27a-zeros.tif --require-zip  # exits 2: catalogue mask\n"
                "python scripts/check_lane_duplicates.py docs/downloads/gems25-h79-spatial-poisson-disc-b2-20261027-66772eeec27a-zeros.tif --reference data/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif  # exits 2: literal failure\n"
                "python scripts/build_readme.py && python scripts/build_site.py\n```\n\n"
                "The restored inputs are public owner mirrors. Their pinned hashes establish integrity, not organizer authenticity. "
                "No automatic organizer interaction or upload is authorized.\n")
    text.append("## Archived research files\n\nThese existing files may be downloaded for learning only. "
                "No file in this table is approved for a weekly slot; a format pass or content difference is not lane clearance.\n\n"
                "| File | Content ID | Status |\n|---|---|---|\n" + "\n".join(items) + "\n")
    text.append("Historical records: [H28 preregistration](knowledge/10_preregistered_h28_live_anchored_emission_design_2026-10-02.md) · "
                "[objective outcomes](knowledge/31_objective_outcomes_and_executive_summary_2026-10-26.md) · "
                "[H74 outcomes](knowledge/37_h74_outcomes_and_executive_summary_2026-10-26.md). "
                "Old records are preserved as historical evidence and may be superseded by the current lane and correction receipts.\n")
    text.append("## Owner prompts and standing briefs — read each session\n\n"
                "The original brief is preserved below exactly as saved. The latest session handoff was condensed; "
                "we do not claim the condensed text is a verbatim transcript.\n")
    for label, name in BRIEFS:
        content = (ROOT / "knowledge" / name).read_text().rstrip()
        text.append(f"<details><summary>{label}</summary>\n\n````text\n{content}\n````\n\n</details>\n")
    (ROOT / "README.md").write_text("\n".join(text))
    print("README.md rebuilt with current decision and preserved prompt archives")


if __name__ == "__main__":
    main()
