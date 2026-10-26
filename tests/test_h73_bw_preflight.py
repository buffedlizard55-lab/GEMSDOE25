import hashlib
import json
from pathlib import Path

from scripts.preflight_h73_bw import H34_NAMES, REQUIRED, inspect_cache


def _write(path: Path, value: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
    return hashlib.sha256(value).hexdigest()


def test_h73_bw_cache_preflight_accepts_pinned_shared_inputs_and_unpinned_h34(tmp_path):
    work = tmp_path / "work"
    manifest = tmp_path / "work_cache_hashes.json"
    entries = {}
    for relative in REQUIRED:
        path = work / relative
        if relative.endswith("h34_columns.npy.names.json"):
            content = json.dumps(H34_NAMES).encode()
        else:
            content = ("cached:" + relative).encode()
        digest = _write(path, content)
        if relative not in {"h34_columns.npy", "h34_columns.npy.names.json"}:
            entries[relative] = {"sha256": digest, "bytes": len(content)}
    manifest.write_text(json.dumps(entries))

    result = inspect_cache(work, manifest)
    assert result["status"] == "ready_for_selector"
    assert result["errors"] == []
    assert result["auto_restore_performed"] is False
    assert result["feature_build_performed"] is False
    assert result["h34_loader_called"] is False
    assert result["model_fit_performed"] is False
    assert result["environment"]["python"]
    assert len(result["evaluator_source_hashes"]["src/gems25/holdout.py"]) == 64
    assert result["warnings"] == ["unpinned:h34_columns.npy", "unpinned:h34_columns.npy.names.json"]
    h34 = {row["path"]: row for row in result["required_artifacts"] if "h34_columns" in row["path"]}
    assert all(row["exists"] and row["matches_pin"] is None for row in h34.values())


def test_h73_bw_cache_preflight_blocks_missing_h34_without_building_it(tmp_path):
    work = tmp_path / "work"
    manifest = tmp_path / "work_cache_hashes.json"
    entries = {}
    for relative in REQUIRED:
        if relative.startswith("h34_columns"):
            continue
        content = relative.encode()
        digest = _write(work / relative, content)
        entries[relative] = {"sha256": digest, "bytes": len(content)}
    manifest.write_text(json.dumps(entries))

    result = inspect_cache(work, manifest)
    assert result["status"] == "blocked_before_fit"
    assert result["errors"] == ["missing:h34_columns.npy", "missing:h34_columns.npy.names.json"]
    assert not (work / "h34_columns.npy").exists()
    assert result["h34_loader_called"] is False and result["model_fit_performed"] is False


def test_h73_bw_cache_preflight_blocks_pinned_hash_mismatch(tmp_path):
    work = tmp_path / "work"
    manifest = tmp_path / "work_cache_hashes.json"
    entries = {}
    for relative in REQUIRED:
        if relative.startswith("h34_columns"):
            content = json.dumps(H34_NAMES).encode() if relative.endswith("names.json") else b"unpinned-sidecar"
            _write(work / relative, content)
            continue
        content = ("actual:" + relative).encode()
        _write(work / relative, content)
        entries[relative] = {"sha256": hashlib.sha256(b"different").hexdigest(), "bytes": len(content)}
    manifest.write_text(json.dumps(entries))

    result = inspect_cache(work, manifest)
    assert result["status"] == "blocked_before_fit"
    assert sum(error.startswith("pin_mismatch:") for error in result["errors"]) == 6
    assert result["h34_loader_called"] is False and result["model_fit_performed"] is False


def test_h73_bw_cache_preflight_blocks_h34_sidecar_name_mismatch(tmp_path):
    work = tmp_path / "work"
    manifest = tmp_path / "work_cache_hashes.json"
    entries = {}
    for relative in REQUIRED:
        content = b"cached" if not relative.endswith("names.json") else json.dumps(["wrong"]).encode()
        digest = _write(work / relative, content)
        if not relative.startswith("h34_columns"):
            entries[relative] = {"sha256": digest, "bytes": len(content)}
    manifest.write_text(json.dumps(entries))

    result = inspect_cache(work, manifest)
    assert result["status"] == "blocked_before_fit"
    assert "h34_names_mismatch" in result["errors"]


def test_h73_bw_cache_preflight_fails_closed_without_manifest_pins(tmp_path):
    work = tmp_path / "work"
    missing_manifest = tmp_path / "missing_manifest.json"
    for relative in REQUIRED:
        content = json.dumps(H34_NAMES).encode() if relative.endswith("h34_columns.npy.names.json") else relative.encode()
        _write(work / relative, content)

    result = inspect_cache(work, missing_manifest)
    assert result["status"] == "blocked_before_fit"
    assert "cache_manifest_missing" in result["errors"]
    assert sum(error.startswith("missing_pin:") for error in result["errors"]) == 6
    assert result["h34_loader_called"] is False and result["model_fit_performed"] is False
