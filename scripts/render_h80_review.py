"""Evidence-led H80 negative diagnostic, shared by all executive entry points."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render_h80(root_page=False):
    prefix = '' if root_page else '../'
    card = json.loads((ROOT/'registry/run_card_h80_2026-10-28.json').read_text())
    hold = card['holdout_dti']
    summary = json.loads((ROOT/'evidence/h80_exp1/summary.json').read_text())['F1_G1']
    rows = []
    for arm, r in summary['arms'].items():
        rows.append(f'<tr><td>{html.escape(arm)}</td><td>{r["pooled_dti"]:.5f}</td>'
                    f'<td>[{r["ci95"][0]:.5f}, {r["ci95"][1]:.5f}]</td><td>NO — research readout only</td></tr>')
    return f'''<section id="h80-review" class="review-decision">
<h1>H80 tested — negative. No competition-ready TIFF.</h1>
<p><b>OK TO SUBMIT: NO — DO NOT SUBMIT.</b> Estimated competition score: <b>UNKNOWN / NOT ESTIMATED</b>.
One blocked factorial screen was completed; confirmation experiments were withdrawn. No new TIFF, weekly slot or upload.</p>
<p><b>HOLDOUT-DTI {hold['dti']:.5f}</b>, 95% CI [{hold['ci95'][0]:.5f}, {hold['ci95'][1]:.5f}],
{hold['withheld_positive_occurrences']:,} withheld-positive occurrences; same-run H35 {hold['comparator_dti']:.5f}.
Paired difference {hold['paired_gain']:+.5f} (95% CI [{hold['paired_ci95'][0]:+.5f}, {hold['paired_ci95'][1]:+.5f}]).
These are local catalogue-gap proxy measurements, NOT leaderboard scores.</p>
<div class="table-scroll"><table><thead><tr><th>Research arm</th><th>HOLDOUT-DTI</th><th>95% CI</th><th>Submit?</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p>Evaluator: <code>gems25.metric.dti_binary</code>, alpha 0.2, beta 0.8, triangular 300 m;
shared buffered whole-component <code>draw_block25km</code>, four quadrant clusters, draws 140–141.
All 792 feature/regime canaries passed (maximum AUC {card['leakage_canary']['maximum_auc']:.5f}).
Only four spatial clusters: uncertainty does not resolve catalogue-to-hidden-fault domain shift.</p>
<p><b>Scientific interpretation warning:</b> mirrored <code>tc</code> is described as a magnetic derivative, not heatflow;
<code>deq_n100a15</code> as earthquake distance, not event rate. uint8 K/Th/U ratios are code-space proxies, not physical concentrations.
No newly verified geothermal vent or causal discovery is claimed.</p>
<p><b>Strict novelty remains blocked:</b> at 37,654 dots, the r13 lower bound is 82.70% overlap (cap 70%).
All 117 declared hashes were restored, but one reference has a mismatched transform. This is not full-registry clearance.
No dense-reference exemption, lattice-gap evasion or alternate packaging was used.</p>
<p><a href="{prefix}knowledge/45_h80_outcome_2026-10-28.md">Full outcome, ranked hypotheses, limitations &amp; next steps</a> ·
<a href="{prefix}registry/run_card_h80_2026-10-28.json" download>Download JSON run card</a> ·
<a href="{prefix}evidence/h80_focus_winners_reaudit_2026-10-28.json">Fresh nine-site pixel audit</a> ·
<a href="{prefix}evidence/h80_exp1/design.json">Evaluator/code/cache pins</a> ·
<a href="{prefix}evidence/h80_exp1/canaries.jsonl">All canaries</a></p>
<p>Data placement is complete in this sandbox via pinned owner mirrors; it is no longer the sole blocker.
Only GEMSDOE25 is changed. The nine historical download rows below are learning references, never new submissions.</p>
</section>'''
