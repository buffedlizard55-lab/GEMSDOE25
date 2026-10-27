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
    text = ["# GEMSDOE25 — designed-factorial fault discovery for the DOE GEMS Prize\n", readme_status()]
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
