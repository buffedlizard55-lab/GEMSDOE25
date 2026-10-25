#!/usr/bin/env python3
"""Registry-only arithmetic: are post-B2 micro-variants ever above B2 (OWNER scores)?

Reads ``registry/live_scores.json`` (owner-reported claims, not organizer receipts) and
extracts every scored artefact dated >= 2026-10-05 whose label carries a B2-family
emission token (``-b2``, ``-b25``, ``-c25``, ``b224``), excluding the GEMSDOE32 original.
No raster is read and no model is fitted. Writes ``evidence/b2_microvariants.json``.

    .venv/bin/python scripts/analyze_b2_microvariants.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
B2_LABEL = "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros"
B2_DOTS = 37654
TOKENS = ("-b2", "-b25", "-c25", "b224")


def datestr(label: str) -> str:
    m = re.search(r"(20\d{6})", label)
    return m.group(1) if m else ""


def dot_count(label: str) -> int | None:
    m = re.search(r"-(\d{5})-", label + "-")
    return int(m.group(1)) if m else None


def main() -> None:
    ledger = json.loads((ROOT / "registry" / "live_scores.json").read_text())
    arts = ledger["artifacts"]
    anchor = [a for a in arts if a["label"] == B2_LABEL]
    if len(anchor) != 1 or anchor[0].get("score") is None:
        raise SystemExit(f"B2 anchor not uniquely scored in registry: {anchor}")
    b2_score = float(anchor[0]["score"])

    rows = []
    for a in arts:
        label, score = a["label"], a.get("score")
        if score is None or label == B2_LABEL:
            continue
        if not any(t in label for t in TOKENS) or datestr(label) < "20261005":
            continue
        cnt = dot_count(label)
        rows.append(
            dict(
                project=a["project"],
                label=label,
                owner_reported_score=float(score),
                delta_vs_b2=round(float(score) - b2_score, 4),
                dots_from_label=cnt,
                delta_dots_vs_b2=None if cnt is None else cnt - B2_DOTS,
                note=a.get("note", ""),
                status=a.get("status", ""),
                is_b2_rehost=bool(cnt == B2_DOTS and float(score) == b2_score),
                independent_detector=bool("independent" in a.get("note", "")),
            )
        )
    rows.sort(key=lambda r: -r["owner_reported_score"])
    rehosts = [r for r in rows if r["is_b2_rehost"]]
    micro = [r for r in rows if not r["is_b2_rehost"] and not r["independent_detector"]]
    indep = [r for r in rows if r["independent_detector"]]

    def rng(rs):
        if not rs:
            return None
        ds = [r["delta_vs_b2"] for r in rs]
        return dict(n=len(rs), delta_min=min(ds), delta_max=max(ds), all_below_b2=all(d < 0 for d in ds))

    out = dict(
        generated_by="scripts/analyze_b2_microvariants.py",
        evidence_class="OWNER (scores are owner-reported claims in registry/live_scores.json; not organizer receipts)",
        anchor=dict(label=B2_LABEL, owner_reported_score=b2_score, dots=B2_DOTS),
        selection="label contains -b2/-b25/-c25/b224, first 20YYMMDD date in label >= 20261005, scored, not the anchor",
        rehosts=rehosts,
        micro_variants=micro,
        independent_detectors=indep,
        summary=dict(micro_variants=rng(micro), independent_detectors=rng(indep), rehosts_at_anchor_score=len(rehosts)),
        focus_sites_highest={
            site: (
                lambda best: dict(owner_reported_score=float(best["score"]), label=best["label"])
            )(max((a for a in arts if a["project"] == site and a.get("score") is not None), key=lambda a: a["score"]))
            for site in (
                "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
            )
        },
        marginal_note=(
            "For a pure addition to / deletion from B2, the sign of the score change alone decides whether the "
            "changed set was below/above the break-even ratio tau = alpha*DTI/(1-alpha*DTI) "
            "(gems25.metric.marginal_inclusion_ratio); no truth-size assumption is needed for that sign claim."
        ),
    )
    path = ROOT / "evidence" / "b2_microvariants.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["summary"], indent=1))
    for r in rows:
        print(f"{r['owner_reported_score']:.4f} {r['delta_vs_b2']:+.4f} dots={r['dots_from_label']} {r['project']} {r['label'][:80]}")
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
