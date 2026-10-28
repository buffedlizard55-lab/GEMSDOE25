"""H80 numerical/label-isolation tests; these do not establish performance."""
import csv
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine

from gems25.h80_scra import (
    H80_NAMES, _load_disequilibrium_impulses, compute_cover_regime_grids,
    compute_h80_grids, fuse_scra_poe_scores,
)


def write_u8(path, arrays):
    with rasterio.open(path, 'w', driver='GTiff', height=arrays.shape[1], width=arrays.shape[2],
                       count=len(arrays), dtype='uint8', crs='EPSG:32611', transform=Affine(100, 0, 0, 0, -100, 10000)) as s:
        s.write(arrays)


@pytest.fixture
def inputs(tmp_path):
    size = 64
    yy, xx = np.mgrid[:size, :size].astype(np.float32)
    foot = np.ones((size, size), bool)
    foot[:3] = False
    base = {n: (np.sin(xx/7) + np.cos(yy/9) + 3).astype(np.float32) for n in
            ('tmi', 'tmi_hg', 'iso_grav_anom', 'depth_to_base_surf', 'det_elev_slope',
             'deq_n100a15', 'ieq_n100a15', 'cond_surf', 'tc', 'geod_dilaterate', 'iso_grav_anom_hg')}
    base['depth_to_base_surf'] *= 200
    rng = np.random.default_rng(80)
    write_u8(tmp_path/'geodawn_rad_u8.tif', rng.integers(1, 255, (4, size, size), dtype=np.uint8))
    write_u8(tmp_path/'geodawn_extensions_u8.tif', rng.integers(1, 255, (4, size, size), dtype=np.uint8))
    write_u8(tmp_path/'lidar_scarp_features_u8.tif', np.full((12, size, size), 255, np.uint8))
    return base, foot, tmp_path


def test_four_operators_are_finite_range_and_masked(inputs):
    base, foot, ext = inputs
    grids, cover, weight = compute_h80_grids(base, foot, ext)
    assert list(grids) == H80_NAMES
    for arr in [*grids.values(), cover, weight]:
        assert arr.dtype == np.float32 and arr.shape == foot.shape
        assert np.isfinite(arr).all() and arr.min() >= 0 and arr.max() <= 1
    for arr in grids.values():
        assert not arr[~foot].any()
    assert np.all(weight >= .65)


def test_cover_regime_responds_to_depth_not_labels(inputs):
    base, foot, ext = inputs
    base['det_elev_slope'][:] = 25
    base['depth_to_base_surf'][:] = 0
    c_shallow, w_shallow = compute_cover_regime_grids(base, foot, ext)
    base['depth_to_base_surf'][:] = 1500
    c_deep, w_deep = compute_cover_regime_grids(base, foot, ext)
    assert np.all(c_deep[foot] > c_shallow[foot])
    assert np.all(w_deep[foot] > w_shallow[foot])


def test_chemistry_loader_ignores_catalogue_distance_and_handles_missing(tmp_path):
    path = tmp_path/'gdr_wellspring_in_footprint.csv'
    row = dict(row='20', col='30', temp_c='40', geothermquartz_c='160',
               geothermchalc_c='100', geothermcat_c='180', dist_known_fault_px='0')
    def write(record):
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=record)
            writer.writeheader()
            writer.writerow(record)
    write(row)
    a = _load_disequilibrium_impulses(tmp_path, (64, 64))
    row['dist_known_fault_px'] = '999999'
    write(row)
    b = _load_disequilibrium_impulses(tmp_path, (64, 64))
    assert np.array_equal(a, b) and a[20, 30] > 0
    row['row'] = 'nan'
    write(row)
    assert not _load_disequilibrium_impulses(tmp_path, (64, 64)).any()


def test_fusion_shape_range_and_cover_adaptation():
    crust = np.array([.9, .1, .8, .2])
    morph = 1-crust
    cover = np.array([0, 1, 0, 1])
    result = fuse_scra_poe_scores(crust, morph, cover, np.ones(4))
    assert np.isfinite(result).all() and result.min() > 0 and result.max() <= 1
    assert not np.array_equal(result, fuse_scra_poe_scores(crust, morph, 1-cover, np.ones(4)))
    with pytest.raises(ValueError, match='shapes'):
        fuse_scra_poe_scores(crust, morph, np.ones(3), np.ones(4))


def test_preregistration_explicitly_withdraws_packaging_and_sparse_waiver():
    root = Path(__file__).resolve().parents[1]
    text = (root/'knowledge/44_preregistered_h80_scra_poe_2026-10-28.md').read_text()
    assert 'withdrawn before fitting' in text and 'no new competition TIFF' in text
    runner = (root/'scripts/run_h80_experiments.py').read_text()
    assert 'write_submission(' not in runner


@pytest.mark.parametrize('bad', [float('nan'), float('inf')])
def test_fusion_nonfinite_inputs_never_silently_repair(bad):
    with pytest.raises(ValueError, match='finite'):
        fuse_scra_poe_scores(np.array([bad, .2]), np.ones(2), np.ones(2), np.ones(2))


@pytest.mark.parametrize('bad', [-.1, 1.1, float('nan'), True])
def test_fusion_rejects_invalid_parameters(bad):
    with pytest.raises(ValueError, match='parameters'):
        fuse_scra_poe_scores(np.ones(2), np.ones(2), np.ones(2), np.ones(2), gamma_range=bad)


def test_h80_replay_requires_all_inputs_instead_of_silent_fallback(tmp_path):
    from gems25.h80_scra import build_h80_sidecar
    with pytest.raises(ValueError, match='every frozen input'):
        build_h80_sidecar(tmp_path, tmp_path/'external')


def test_h80_cache_invalidates_on_changed_input_bytes(tmp_path, monkeypatch):
    import gems25.h80_scra as module
    bands = tmp_path/'bands'
    bands.mkdir()
    np.save(bands/'_footprint.npy', np.ones((8, 8), bool))
    ext = tmp_path/'external'
    ext.mkdir()
    for name in ('geodawn_extensions_u8.tif', 'geodawn_rad_u8.tif', 'lidar_scarp_features_u8.tif',
                 'gdr_wellspring_in_footprint.csv'):
        (ext/name).write_bytes(b'fake bytes for fingerprint test only')
    calls = []
    monkeypatch.setattr(module, 'load_base', lambda path: {})
    def compute(base, footprint, external):
        calls.append(True)
        grids = {name: np.full(footprint.shape, .2, np.float32) for name in H80_NAMES}
        return grids, np.ones(footprint.shape, np.float32), np.ones(footprint.shape, np.float32)
    monkeypatch.setattr(module, 'compute_h80_grids', compute)
    module.build_h80_sidecar(tmp_path, ext)
    module.build_h80_sidecar(tmp_path, ext)
    assert len(calls) == 1
    (ext/'geodawn_rad_u8.tif').write_bytes(b'changed input bytes')
    module.build_h80_sidecar(tmp_path, ext)
    assert len(calls) == 2
