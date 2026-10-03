# 12 · H30-1 paired relay × terrain — registered screen and confirmation outcomes

**Status:** completed proxy experiment; the primary H30-1 candidate failed fresh-draw confirmation. Stop this candidate. No full-data TIFF, submission, or weekly slot was created or approved.

This is the outcome record for the design frozen in [`11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md`](11_preregistered_h30_pairwise_relay_factorial_2026-10-03.md). Machine-readable rows, designs, gates, and hashes are in [`evidence/h30_relay_screen/`](../evidence/h30_relay_screen/) and [`evidence/h30_relay_confirm/`](../evidence/h30_relay_confirm/). The test is a spatially blocked catalogue-gap proxy, not hidden competition truth or a competition score.

## Registered results

The preregistered P+S arm (`T_PLUS_P_S`) is the only primary candidate. Its paired reference is chosen independently in each fold as the better same-run DTI of `BASE_NO_TIP` and `T_BASE`; the reference DTI and hug share use that same control arm. Means below average the two draws within each of four spatial blocks.

| Stage | P+S mean DTI | Best-control mean DTI | Mean paired gain | Positive folds | Worst-fold gain | Mean hug-share change | Registered result |
|---|---:|---:|---:|---:|---:|---:|---|
| Screen, draws 6–7 | 0.151567 | 0.147489 | +0.004078 | 4/4 | +0.000893 | −0.000379 | **PASS; confirmation permitted** |
| Confirmation, draws 8–9 | 0.148330 | 0.149605 | −0.001275 | 1/4 | −0.003842 | +0.007223 | **FAIL; stop** |

The frozen gate requires mean gain **greater than +0.001 DTI**, at least 3/4 positive folds, no fold below −0.010 DTI, and mean hug-share increase no greater than +0.10. The screen passed all conditions. The fresh confirmation failed the mean-gain and positive-fold conditions; its DTI/hug result is not rescued by the screen result. It is not eligible for a candidate file or slot.

## Arm means and factorial contrasts

| Stage | BASE_NO_TIP | T_BASE | T+P | T+S | T+P+S |
|---|---:|---:|---:|---:|---:|
| Screen (draws 6–7) | 0.144949 | 0.146848 | 0.150500 | 0.147097 | 0.151567 |
| Confirmation (draws 8–9) | 0.144521 | 0.146370 | 0.148347 | 0.146417 | 0.148330 |

The registered 2² effects are calculated only over `T_BASE`, `T+P`, `T+S`, and `T+P+S`. The four blocks—not the eight fold×draw cells—are the units summarized below; t intervals are descriptive with only four spatial blocks.

| Stage | P effect | S effect | P×S coded effect | P×S difference-in-differences |
|---|---:|---:|---:|---:|
| Screen | +0.004061 (95% t interval +0.000394 to +0.007728) | +0.000658 (−0.000535 to +0.001850) | +0.000409 (−0.003140 to +0.003958) | +0.000818 (−0.006279 to +0.007916) |
| Confirmation | +0.001945 (−0.001238 to +0.005128) | +0.000015 (−0.001972 to +0.002001) | −0.000032 (−0.002279 to +0.002216) | −0.000064 (−0.004559 to +0.004431) |

The screen's P+S advantage did not replicate on fresh draws. S and the P×S interaction were near zero in confirmation, with intervals spanning both signs. Four spatial blocks are too few for strong population-level significance claims. T+P is a registered diagnostic arm only; the preregistration forbids promoting it post hoc because P+S failed confirmation.

## Analysis correction and provenance

The screen runner completed the registered 40 cells and wrote `design.json` plus `cells.jsonl`. The first analyzer attempt stopped because its validator incorrectly required the distance-weighted `TP_w` and `FP_w` credit sums to be integers. The repository's implementation of the published metric in `src/gems25/metric.py` returns fractional weighted credits; only `emitted` and `n_truth` are integer counts. The validator was corrected to accept finite, bounded fractional credits and check coverage consistency. The analyzer was then rerun on the **unchanged raw screen files**; no feature, model, draw, DTI, gate, or fit was changed or rerun. The correction and regression test are recorded in `registry/review_passes.json`.

- Screen model code revision: `ba859e4ab05582067b428f1279ce557af37a51b3`.
- Confirmation model code revision: `71801985182ba7fc75ef3790671e91340c869a0a`.
- Screen design SHA-256: `73ac63613312eac8f2bfa069b3c514ebe03089ff26ec92d797dcd426d0258ca7`.
- Screen raw-cell SHA-256: `d23a63005a66aa7603038828ec1e45718717324b5c4356315ad2b8abb5931eed`.
- Confirmation design/cell hashes are recorded in `evidence/h30_relay_confirm/results.json`.

## Decision and limits

- **H30-1:** failed its preregistered fresh-draw confirmation; stop. Do not create a submission TIFF from this run, do not use a weekly slot, and do not post-hoc promote either diagnostic single-factor arm.
- **H30-2/H30-3:** remain registered hypotheses only; they were not fitted or tested by H30-1.
- **Competition claims:** these DTI values are computed on owner-mirror catalogue-gap holdout data only. They do not verify the owner-reported 0.2477 or 0.3195 scores and do not predict a leaderboard result.
- **Submission state:** the existing D2.8 GeoTIFF remains format-validated, unscored, and not slot-approved. No DrivenData page, leaderboard, forum, data endpoint, or submission endpoint was accessed.

Any future geological hypothesis requires a genuinely new preregistration. The A–E five-family factorial and prior H26/H27/H28/H29 work remain separate; the H30-1 screen/confirmation do not replace or rewrite those records.
