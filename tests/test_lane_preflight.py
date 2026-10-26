from types import SimpleNamespace

import numpy as np
import pytest

from scripts import validate_gem_candidate as validator


def _ctx(shape):
    foot = np.ones(shape, dtype=bool)
    return SimpleNamespace(foot=foot, fi=np.flatnonzero(foot))


def test_surface_lane_preflight_uses_absolute_spearman_and_fails_closed():
    shape = (40, 40)
    ctx = _ctx(shape)
    surface = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
    inverse = -surface

    rows = validator.surface_lane_check(
        ctx, surface, [{"file": "inverse.tif", "arr": inverse}]
    )

    assert rows[0]["spearman"] == pytest.approx(-1.0)
    assert rows[0]["duplicate"] is True
    assert validator.surface_lane_is_clear(rows) is False
    assert validator.surface_lane_is_clear([]) is False


def test_surface_lane_preflight_does_not_clear_undefined_correlation():
    shape = (40, 40)
    ctx = _ctx(shape)
    surface = np.zeros(shape, dtype=np.float32)
    reference = np.ones(shape, dtype=np.float32)

    rows = validator.surface_lane_check(
        ctx, surface, [{"file": "constant.tif", "arr": reference}]
    )

    assert rows[0]["spearman"] != rows[0]["spearman"]  # NaN means undefined.
    assert rows[0]["duplicate"] is True
    assert validator.surface_lane_is_clear(rows) is False


def test_registry_loader_includes_top_scorers_and_keeps_arrays_out_of_ram(tmp_path, monkeypatch):
    import rasterio
    from affine import Affine

    data_root = tmp_path / "data"
    repo_root = tmp_path / "repo"
    top_dir = data_root / "registry_top"
    top_dir.mkdir(parents=True)
    (data_root / "scored").mkdir()
    (data_root / "calibration").mkdir()
    (repo_root / "docs" / "downloads").mkdir(parents=True)
    path = top_dir / "top.tif"
    profile = {
        "driver": "GTiff",
        "height": 8,
        "width": 9,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": Affine(100, 0, 0, 0, -100, 800),
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.zeros((8, 9), np.float32), 1)

    monkeypatch.setattr(validator, "ROOT", repo_root)
    monkeypatch.setattr(validator, "REGISTRY_DIR", data_root / "scored")
    monkeypatch.setattr(validator, "data_dir", lambda: data_root)

    registry = validator.load_registry_rasters()

    assert [row["file"] for row in registry] == ["top.tif"]
    assert "arr" not in registry[0]
    assert validator._registry_array(registry[0]).shape == (8, 9)
