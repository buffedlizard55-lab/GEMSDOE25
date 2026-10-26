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


def test_final_lane_reads_file_backed_registry(tmp_path):
    import rasterio
    from affine import Affine

    ctx = _ctx((40, 40))
    dots = np.zeros(ctx.foot.shape, np.float32)
    dots[::4, ::4] = 1
    path = tmp_path / 'reference.tif'
    with rasterio.open(path, 'w', driver='GTiff', height=40, width=40,
                       count=1, dtype='float32', crs='EPSG:32611',
                       transform=Affine(100, 0, 0, 0, -100, 4000)) as dst:
        dst.write(dots, 1)
    rows = validator.lane_check(ctx, dots, dots, [{'file': path.name, 'path': path}])
    assert rows[0]['overlap_within_3px'] == 1
    assert rows[0]['duplicate'] is True
    assert not validator.lane_is_clear(rows)


def test_final_lane_empty_candidate_cannot_pass():
    import warnings
    from scipy.stats import ConstantInputWarning

    ctx = _ctx((40, 40))
    zero = np.zeros(ctx.foot.shape)
    ref = np.zeros(ctx.foot.shape)
    ref[::4, ::4] = 1
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConstantInputWarning)
        rows = validator.lane_check(ctx, zero, zero, [{'file': 'reference', 'arr': ref}])
    assert not validator.lane_is_clear(rows)


def test_registry_loader_resolves_gems_data_dir_scored_when_default(tmp_path, monkeypatch):
    import rasterio
    from affine import Affine

    data_root = tmp_path / "ext_data"
    repo_root = tmp_path / "repo"
    scored_dir = data_root / "scored"
    research_dir = data_root / "research"
    scored_dir.mkdir(parents=True)
    research_dir.mkdir(parents=True)
    (repo_root / "docs" / "downloads").mkdir(parents=True)
    profile = {
        "driver": "GTiff",
        "height": 8,
        "width": 9,
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:32611",
        "transform": Affine(100, 0, 0, 0, -100, 800),
    }
    for idx, p in enumerate((scored_dir / "s.tif", research_dir / "r.tif"), start=1):
        arr = np.full((8, 9), float(idx), dtype=np.float32)
        with rasterio.open(p, "w", **profile) as dst:
            dst.write(arr, 1)

    monkeypatch.setattr(validator, "ROOT", repo_root)
    monkeypatch.setattr(validator, "REGISTRY_DIR", validator._DEFAULT_REGISTRY_DIR)
    monkeypatch.setattr(validator, "data_dir", lambda: data_root)

    registry = validator.load_registry_rasters()
    assert [row["file"] for row in registry] == ["s.tif", "r.tif"]

