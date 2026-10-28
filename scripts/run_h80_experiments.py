#!/usr/bin/env python3
"""H80 preregistered diagnostic only; shared splits, canaries, emission and metric.

No full-footprint placement or TIFF writer is invoked: the literal r13 gate
already rules out the frozen budget. Seeds/arms cannot be overridden.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from gems25.experiment import DOMAIN_ERODE, N_NEG, gather_columns, load_context  # noqa: E402
from gems25.features import build_catalogue_features, build_tip_continuation  # noqa: E402
from gems25.h34 import H34_NAMES, load_h34_sidecar  # noqa: E402
from gems25.h74_rmps import H74_RMPS_NAMES, draw_block25km, load_h74_rmps_sidecar  # noqa: E402
from gems25.h79_cthm import H79_ALL_NAMES, build_h79_sidecar, fuse_poe_scores  # noqa: E402
from gems25.h80_scra import H80_NAMES, SCRA_DEEP_PARAMS, build_h80_sidecar, fuse_scra_poe_scores  # noqa: E402
from gems25.paths import data_dir, work_dir  # noqa: E402
from gems25.validation import feature_canary, pooled_summary  # noqa: E402
from run_h28_holdout import EXTRAS  # noqa: E402
from run_h74_experiments import emit_blind_submod, emit_sapd, fit_predict  # noqa: E402
from gems25.metric import dti_binary  # noqa: E402

SPECS = {
    'exp1': ('block25km', (140, 141), ('CTRL_H35', 'CTRL_CRUSTAL56', 'F0_G0', 'F1_G0', 'F0_G1', 'F1_G1', 'H80_CRUSTAL60')),
    'exp2': ('standard', (140, 141), ('CTRL_H35', 'CTRL_CRUSTAL56', 'F1_G1', 'H80_PLUS_H35', 'H80_CRUSTAL60')),
    'exp3': ('block25km', (142, 143), ('CTRL_H35', 'CTRL_CRUSTAL56', 'F0_G0', 'F1_G1', 'H80_SCRA_DEEP', 'H80_PLUS_H35', 'H80_CRUSTAL60')),
}


def dump(obj, path):
    Path(path).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def run(exp):
    start = time.monotonic()
    mode, draws, arms = SPECS[exp]
    out = ROOT / 'evidence' / f'h80_{exp}'
    out.mkdir(exist_ok=False)
    w = work_dir()
    ctx = load_context(w)
    h34 = load_h34_sidecar(w, ctx.fi)
    h74 = load_h74_rmps_sidecar(w, ctx.fi)
    h79, _ = build_h79_sidecar(w, data_dir() / 'external')
    h80, regime, _ = build_h80_sidecar(w, data_dir() / 'external')
    names = (list(ctx.static_names) + list(ctx.e_names) + list(ctx.extra_names)
             + ['H27_tip'] + H34_NAMES + H74_RMPS_NAMES + ['S_dem_c2', 'S_dem_s2'] + H79_ALL_NAMES + H80_NAMES)
    assert len(names) == 97 and len(set(names)) == 97
    col = {n: i for i, n in enumerate(names)}
    h35_names = [ctx.all_names[i] for i in ctx.columns('BDE')] + EXTRAS + ['H27_tip'] + H34_NAMES
    crust_names = ([ctx.all_names[i] for i in ctx.columns('ACD')] + ['X1_K', 'X1_ThK', 'X1_UK', 'X3_gm']
                   + H34_NAMES + H74_RMPS_NAMES + H79_ALL_NAMES)
    morph_names = [ctx.all_names[i] for i in ctx.columns('B')] + ['S_dem_c2', 'S_dem_s2']
    columns = {'h35': [col[n] for n in h35_names], 'c56': [col[n] for n in crust_names],
               'c60': [col[n] for n in crust_names + H80_NAMES], 'm26': [col[n] for n in morph_names],
               'plus': [col[n] for n in h35_names + H80_NAMES]}
    assert [len(columns[k]) for k in ('h35', 'c56', 'c60', 'm26', 'plus')] == [59, 56, 60, 26, 63]
    paths = ['src/gems25/metric.py', 'src/gems25/holdout.py', 'src/gems25/validation.py',
             'src/gems25/h74_rmps.py', 'src/gems25/h80_scra.py', 'scripts/run_h74_experiments.py',
             'scripts/run_h80_experiments.py']
    dump(dict(label='HOLDOUT-DTI', exp=exp, mode=mode, draws=draws, arms=arms,
              preregistration_commit='69e6176376c8ec08577e691afa8c60ed3a400989',
              correction_commit='59eec13', full_footprint_placement=False,
              hashes={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
              cache_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                            list(w.glob('*.npy'))},
              evaluator='gems25.metric.dti_binary; buffered whole-component 4-quadrant; alpha=.2 beta=.8 R=300m triangular',
              feature_names=names, caveats=['four spatial clusters only', 'catalogue-gap proxy, not hidden labels',
                                           'K/Th/U uint8 ratios are code-space proxies', 'no weekly slot or TIFF']), out / 'design.json')
    dom_full_px = float(binary_erosion(ctx.foot, iterations=DOMAIN_ERODE).sum())
    grid = np.zeros(ctx.foot.shape, np.float32)

    def matrix(idx, E, tip):
        x = np.empty((len(idx), len(names)), np.float32)
        gather_columns(ctx, E, idx, True, out=x[:, :78])
        x[:, 78] = tip[idx]
        x[:, 79:82] = h34[:, idx].T
        x[:, 82:86] = h74[:, idx].T
        x[:, 86:88] = ctx.addon[3:5, idx].T
        x[:, 88:93] = h79[:, idx].T
        x[:, 93:97] = h80[:, idx].T
        return x

    all_rows = []
    with (out / 'cells.jsonl').open('w') as sink, (out / 'canaries.jsonl').open('w') as csink:
        for fold in range(4):
            for seed in draws:
                tcell = time.monotonic()
                if tcell - start > 5400:
                    raise RuntimeError('90-minute diagnostic time guard; stop without promotion')
                d = ctx.holdout.draw(fold, seed) if mode == 'standard' else draw_block25km(ctx.holdout, fold, seed, block_px=250)
                assert not (d.visible & d.hidden_test).any() and not (d.train_region & d.quadrant).any()
                E = build_catalogue_features(d.visible, ctx.fi)
                tip = build_tip_continuation(d.visible, ctx.foot, ctx.fi)
                pos = ctx.vec(d.hidden_train)
                near = distance_transform_edt(~d.hidden_train) <= 1.5
                pool = ctx.vec(d.train_region & ~ctx.labels & ~near)
                neg = np.random.default_rng(777 + 31 * fold + seed).choice(pool, min(N_NEG, len(pool)), replace=False)
                tr_idx = np.sort(np.concatenate([pos, neg]))
                y = np.isin(tr_idx, pos).astype(np.int8)
                q_idx = ctx.vec(d.quadrant)
                fi_q, sl = ctx.fi[q_idx], d.bbox
                dom = binary_erosion(d.quadrant, iterations=DOMAIN_ERODE)
                truth, domain, known = (d.hidden_test & dom)[sl], dom[sl], d.visible[sl]
                dv = distance_transform_edt(~known).astype(np.float32)
                Xtr, Xq = matrix(tr_idx, E, tip), matrix(q_idx, E, tip)
                del E, tip, near, pool
                dq = dom.ravel()[fi_q]
                hq = (d.hidden_test & dom).ravel()[fi_q]
                cq = ctx.labels.ravel()[fi_q]
                ap = np.flatnonzero(hq)
                an_pool = np.flatnonzero(dq & ~cq)
                an = np.random.default_rng(5).choice(an_pool, min(150000, len(an_pool)), replace=False)
                ai = np.concatenate([ap, an])
                ay = np.concatenate([np.ones(len(ap)), np.zeros(len(an))])
                canaries = {n: feature_canary(Xq[ai, j], ay) for j, n in enumerate(names)}
                canaries.update({n: feature_canary(regime[j, q_idx[ai]], ay)
                                 for j, n in enumerate(('c_cover', 'w_regime'))})
                cr = dict(fold=fold, draw=seed, features=canaries,
                          all_passed=all(c['passed'] for c in canaries.values()))
                csink.write(json.dumps(cr, allow_nan=False) + '\n')
                csink.flush()
                if not cr['all_passed']:
                    raise RuntimeError('feature-alone canary fired; stop before fitting')
                preds = {}
                for key in ('h35', 'c56', 'c60', 'm26') + (('plus',) if 'H80_PLUS_H35' in arms else ()):
                    ids = columns[key]
                    preds[key], _ = fit_predict(Xtr[:, ids], y, Xq[:, ids], seed=seed + (1000 if key == 'm26' else 0))
                cc, wr = regime[:, q_idx]
                for arm in arms:
                    if arm == 'CTRL_H35':
                        score = preds['h35']
                    elif arm == 'CTRL_CRUSTAL56':
                        score = preds['c56']
                    elif arm == 'H80_CRUSTAL60':
                        score = preds['c60']
                    elif arm == 'H80_PLUS_H35':
                        score = preds['plus']
                    elif arm in ('F0_G0', 'F1_G0'):
                        score = fuse_poe_scores(preds['c56' if arm == 'F0_G0' else 'c60'], preds['m26'])
                    else:
                        score = fuse_scra_poe_scores(preds['c56' if arm == 'F0_G1' else 'c60'], preds['m26'], cc, wr,
                                                    **(SCRA_DEEP_PARAMS if arm == 'H80_SCRA_DEEP' else {}))
                    if arm in ('CTRL_H35', 'H80_PLUS_H35'):
                        em, _ = emit_sapd(grid, fi_q, sl, domain, known, score)
                    else:
                        em, _ = emit_blind_submod(grid, fi_q, sl, domain, known, dv, score, dom_full_px)
                    ev = dti_binary(em, truth, valid=domain, known=known)
                    row = dict(arm=arm, fold=fold, draw=seed, **ev, emitted=int(em.sum()))
                    all_rows.append(row)
                    sink.write(json.dumps(row, allow_nan=False) + '\n')
                    sink.flush()
                print(f'{exp} fold={fold} draw={seed} truth={int(truth.sum())} canary_max={max(c["canary_auc"] for c in canaries.values()):.4f} '
                      f'elapsed={time.monotonic()-start:.1f}s cell={time.monotonic()-tcell:.1f}s', flush=True)
                del Xtr, Xq, preds, score, em, d, dv
                gc.collect()
    results = {arm: pooled_summary(all_rows, candidate=arm, control='CTRL_H35') for arm in arms if arm != 'CTRL_H35'}
    results['vs_crustal56'] = pooled_summary(all_rows, candidate='F1_G1', control='CTRL_CRUSTAL56')
    if exp == 'exp1':
        # Paired factorial main effects: averaging four DTI cells, descriptive only.
        from gems25.validation import pooled_dti
        scores = {a: pooled_dti([r for r in all_rows if r['arm'] == a]) for a in arms}
        results['factorial'] = dict(feature_main_effect=((scores['F1_G0']-scores['F0_G0'])+(scores['F1_G1']-scores['F0_G1']))/2,
                                   regime_main_effect=((scores['F0_G1']-scores['F0_G0'])+(scores['F1_G1']-scores['F1_G0']))/2,
                                   interaction=scores['F1_G1']-scores['F1_G0']-scores['F0_G1']+scores['F0_G0'])
    dump(results, out / 'summary.json')
    print(f'{exp} complete in {time.monotonic()-start:.1f}s', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exp', choices=SPECS, required=True)
    parser.add_argument('--replay-negative-screen', action='store_true',
                        help='Explicitly reproduce failed exp1 only; never promote')
    args = parser.parse_args()
    if args.exp != 'exp1' or not args.replay_negative_screen:
        parser.error('H80 screen negative and geological interpretation unresolved. exp2/exp3 withdrawn; '
                     'only --exp exp1 --replay-negative-screen is permitted in a clean evidence directory.')
    with threadpool_limits(limits=2):
        run(args.exp)
