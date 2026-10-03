#!/usr/bin/env python3
"""Fetch every competition raster used by the live-anchored calibration, hash it, and tie it to a reported score.

Nothing is asserted that is not computed here:

* locations come from ``registry/artifact_mirrors.json`` (paths copied from GitHub tree listings);
* bytes come from the owner's *public* GitHub mirrors through ``gh api`` (``raw.githubusercontent.com`` is not
  reachable from this sandbox); DrivenData is never contacted;
* the SHA-256 of each fetched file is computed locally and matched against
  ``evidence/provenance/gemsdoe27_live_scores_snapshot.json`` (a snapshot of the owner's own hash<->score ledger).
  A file whose hash matches no ledger row is recorded with ``score=None`` and ``fit=False``;
* the result is written to ``registry/artifact_ledger.json``.

    python scripts/restore_artifacts.py            # fetch, verify, write the ledger
    python scripts/restore_artifacts.py --check     # verify only what is already on disk
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems25.paths import data_dir  # noqa: E402

MIRRORS = ROOT / "registry" / "artifact_mirrors.json"
SNAPSHOT = ROOT / "evidence" / "provenance" / "gemsdoe27_live_scores_snapshot.json"
LEDGER_OUT = ROOT / "registry" / "artifact_ledger.json"

# ids that registry/data_manifest.json already pins inside data/scored (no second download, no second hash source)
LOCAL_PINNED = {
    "h19-5": "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
    "h19-4": "gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif",
    "h16-1": "gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif",
    "d1-5": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
    "d2-8": "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "lattice-s5": "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
    "hedge-v2": "8GEMSDOE_Hedge-v2_submission.tif",
    "h25-ctx-ridge": "gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif",
    "h28-dotted-ridge": "gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif",
    "ens12": "gemsdoe-ens12-adopted-7f00890a.tif",
    "placeholder": "gemsdoe9-PLACEHOLDER-2314b599.tif",
}
# rows the owner's brief lists but the sibling hash ledger does not carry: the file->score link is unverified
BRIEF_ONLY_SCORE = {
    "h18-4-geologic-map-faults-gap": 0.0360,
    "h20-1": 0.1890,
    "h23-a-6pct": 0.1002,
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(repo: str, ref: str, path: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        if shutil.which("gh"):
            with tmp.open("wb") as out:
                r = subprocess.run(
                    ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}",
                     "-H", "Accept: application/vnd.github.raw"],
                    stdout=out, stderr=subprocess.PIPE,
                )
            if r.returncode != 0:
                sys.stderr.write(f"  gh api failed for {repo}/{path}: {r.stderr.decode()[:200]}\n")
                return False
        else:  # pragma: no cover - the sandbox always has gh
            import requests

            url = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
            with requests.get(url, stream=True, timeout=180) as resp:
                resp.raise_for_status()
                with tmp.open("wb") as out:
                    for chunk in resp.iter_content(1 << 20):
                        out.write(chunk)
        if tmp.stat().st_size == 0:
            return False
        tmp.replace(dest)
        return True
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="do not download; verify only what is on disk")
    args = ap.parse_args()

    mirrors = json.loads(MIRRORS.read_text())
    snap = json.loads(SNAPSHOT.read_text())
    by_hash = {a["sha256"]: a for a in snap["artifacts"] if a.get("sha256")}
    d = data_dir()
    out_rows = []

    # 1. the rows already pinned by registry/data_manifest.json (restored into data/scored)
    manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    pin_by_dest = {e["dest"]: e for e in manifest["files"]}
    for aid, fname in LOCAL_PINNED.items():
        p = d / "scored" / fname
        row = {"id": aid, "file": f"data/scored/{fname}" if p.exists() else None,
               "source": "registry/data_manifest.json pin (owner mirror)", "sha256": None, "bytes": None,
               "score": None, "score_source": None, "fit": False, "status": "missing"}
        if p.exists():
            got = sha256_file(p)
            pin = pin_by_dest.get(f"scored/{fname}")
            row.update(sha256=got, bytes=p.stat().st_size, status="present")
            if pin and pin["sha256"] != got:
                row["status"] = f"PIN MISMATCH (expected {pin['sha256'][:12]})"
            hit = by_hash.get(got)
            if hit and hit.get("owner_reported_public_score") is not None:
                row["score"] = hit["owner_reported_public_score"]
                row["score_source"] = f"sibling ledger row matched by full SHA-256: {hit['label']}"
                row["fit"] = True
            elif got.startswith("91eae1ca42ec"):
                row["score_source"] = "unscored in every owner list (the D2.8 alternate)"
            else:
                row["score_source"] = "no sibling ledger row has this SHA-256"
                if aid == "hedge-v2":
                    row["score"] = 0.1563
                    row["score_source"] = "owner brief list (8GEMSDOE Hedge-v2_submission 0.1563); not in the sibling hash ledger"
                    row["fit"] = False
        out_rows.append(row)

    # 2. the mirrors listed in registry/artifact_mirrors.json
    for m in mirrors["mirrors"]:
        dest = d / "artifacts" / f"{m['id']}.tif"
        got = None
        if dest.exists():
            got = sha256_file(dest)
        elif not args.check:
            # An ambiguous mirror (several candidate paths) is accepted only on a byte-exact ledger match.
            ambiguous = bool(m.get("alternates"))
            for cand in [m["path"], *m.get("alternates", [])]:
                print(f"fetch {m['repo']}/{cand}", flush=True)
                if not fetch(m["repo"], m["ref"], cand, dest):
                    continue
                h = sha256_file(dest)
                if not ambiguous or h in by_hash:
                    got = h
                    break
                dest.unlink(missing_ok=True)
            if ambiguous and got is None:
                print(f"  ambiguous mirror for {m['id']}: no candidate matched the sibling ledger; excluded", flush=True)
        row = {"id": m["id"], "owner_label": m["owner_label"], "repo": m["repo"], "ref": m["ref"],
               "path": m["path"], "file": f"data/artifacts/{m['id']}.tif" if got else None, "sha256": got,
               "bytes": dest.stat().st_size if got else None, "score": None, "score_source": None,
               "fit": False, "status": "present" if got else "not fetched"}
        if got:
            hit = by_hash.get(got)
            if hit:
                row["score"] = hit.get("owner_reported_public_score")
                row["score_source"] = f"sibling ledger row matched by full SHA-256: {hit['label']}"
                row["fit"] = row["score"] is not None
                row["sibling_repo"] = hit.get("repo")
            else:
                row["score_source"] = "no sibling ledger row has this SHA-256"
                if m["id"] in BRIEF_ONLY_SCORE:
                    row["score"] = BRIEF_ONLY_SCORE[m["id"]]
                    row["score_source"] = ("owner brief list only; the sibling hash ledger has no row for these bytes, "
                                           "so the file-to-score link is unverified")
            cid = m.get("content_id")
            if cid:
                row["content_id"] = cid
                row["content_id_matches_sha_prefix"] = bool(got.startswith(cid[:12])) or bool(cid in got[:12])
        if m.get("note"):
            row["note"] = m["note"]
        out_rows.append(row)

    fit = [r for r in out_rows if r["fit"]]
    ledger = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "scripts/restore_artifacts.py",
        "warning": ("Every SHA-256 below was computed from fetched bytes in this run; every score was matched to those bytes "
                    "through the owner's own hash<->score ledger snapshot or is explicitly marked as brief-only. Scores are "
                    "user/owner-reported public-leaderboard values, NOT DrivenData receipts, and a hash match proves mirror "
                    "consistency, not that the organizer scored these bytes. drivendata.org was never contacted."),
        "score_snapshot": mirrors["score_snapshot"],
        "n_rows": len(out_rows),
        "n_used_in_fit": len(fit),
        "artifacts": out_rows,
    }
    LEDGER_OUT.write_text(json.dumps(ledger, indent=1) + "\n")
    print(f"\n{len(out_rows)} rows -> {LEDGER_OUT.relative_to(ROOT)}; {len(fit)} usable for the fit")
    for r in out_rows:
        print(f"  {r['id']:<28} {str(r['score']):>7} sha={str(r['sha256'])[:12]} fit={r['fit']} {r['status']}")


if __name__ == "__main__":
    main()
