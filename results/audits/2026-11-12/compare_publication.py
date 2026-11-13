import json, math
from pathlib import Path
root=Path('work/audit/reproduced'); m=json.loads(Path('paper/dynnav_r/evidence_manifest.json').read_text()); checks=[]
def check(name,a,b):
 ok=math.isclose(a,b,rel_tol=1e-12,abs_tol=0) if isinstance(a,(int,float)) else a==b
 checks.append(dict(claim=name,generated=a,manifest=b,passed=ok))
def read(name):return json.loads((root/name/'summary.json').read_text())
d=read('history_information_gap_benchmark'); old=m['counterfactual_information_gap']
for key,mkey in [('mean_history_separation','mean_history_separation'),('max_history_separation','maximum_history_separation'),('max_absolute_risky_history_state_only_error','risky_history_invariant_max_abs_error')]:check('gap.'+key,d[key],old[mkey])
d=read('commitment_phase_benchmark')['history_aware'];check('phase.match_rate',d['analytic_boundary_match_rate'],m['analytic_phase_boundary']['match_rate']);check('phase.trials',d['trials'],m['analytic_phase_boundary']['trials'])
d=read('commitment_execution_benchmark');old=m['homogeneous_stochastic_execution']
for planner,rates in old['irreversible_failure_rate'].items():
 for prob,rate in zip(old['closure_probabilities'],rates):check('homogeneous.'+planner+'.'+str(prob),d[f'{planner}:p={prob}']['irreversible_failure_rate'],rate)
d=read('heldout_history_generalization')
for scenario,v in m['frozen_heterogeneous_evaluation']['scenarios'].items():
 for planner,rate in v['failure_rate'].items():check('heldout.'+scenario+'.'+planner,d[scenario][planner]['irreversible_failure_rate'],rate)
 e=d[scenario]['paired_binary_effects_vs_shortest']['history_exact'];check('heldout.'+scenario+'.risk_difference',e['risk_difference'],v['history_exact_vs_shortest_risk_difference'])
 for index,side in enumerate(['lower','upper']):check('heldout.'+scenario+'.CI.'+side,e['interval'][side],v['history_exact_vs_shortest_bootstrap_95'][index])
d=read('geometric_heldout')
for scenario,v in m['frozen_geometric_heldout']['scenarios'].items():
 for planner,prefix in [('shortest','shortest'),('state_only_single','state_only'),('state_only_exact','state_only_exact'),('history_exact','history_exact')]:
  check('geometric.'+scenario+'.'+planner,d[scenario][planner]['irreversible_failure_rate'],v[prefix+'_failure_rate'])
 e=d[scenario]['paired_binary_effects_vs_shortest']['history_exact']
 check('geometric.'+scenario+'.mcnemar',e['mcnemar_exact_pvalue'],v['history_exact_vs_shortest_mcnemar_exact_pvalue'])
 for index,side in enumerate(['lower','upper']):check('geometric.'+scenario+'.CI.'+side,e['interval'][side],v['history_exact_vs_shortest_bootstrap_95'][index])
d=read('cut_scaling_benchmark');check('series.max_cut_error',d['max_cut_absolute_error'],m['series_cut_scaling']['max_cut_absolute_error'])
d=read('joint_cut_counterexample');old=m['joint_cut_counterexample'];check('joint.optimistic_cases',d['cut_optimism_cases'],old['cut_optimism_cases'])
for row in d['pairs']:check('joint.exact_return.'+str(row['closure_probability']),row['cut_exact_return_probability'],old['cut_route_exact_return_probability_by_p'][str(row['closure_probability'])])
d=read('geometric_pareto')
for scenario,rows in d.items():
 hard=[r for r in rows if r['family']=='hard_return'];check('pareto.'+scenario+'.hard_zero_failure',all(r['planner_success'] and r['irreversible_failure_rate']==0 for r in hard),m['geometric_soft_vs_hard_pareto']['scenario_summary'][scenario]['hard_zero_failure_all_thresholds'])
report={'scope':'Selected manifest non-timing claims compared with fresh raw-generated summaries; not all manuscript claims or bibliography','checks':checks,'all_passed':all(x['passed'] for x in checks),'source_code_revision':'94990150a83825bfc2be470c9511687b04153536'}
Path('work/audit/expanded-publication-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(len(checks),'checks',report['all_passed'])
for c in checks:
 if not c['passed']:print(c)
assert report['all_passed']
