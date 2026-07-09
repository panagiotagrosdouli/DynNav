import sys,csv,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dynnav.core.types import ScenarioConfig
from dynnav.simulation.grid_world import GridWorld
from dynnav.evaluation.metrics import evaluate

def main():
    planners=['dijkstra','astar','risk_aware_astar','uncertainty_aware_astar','recoverability_aware_astar']; rows=[]; Path('results/metrics').mkdir(parents=True,exist_ok=True); Path('results/reports').mkdir(parents=True,exist_ok=True)
    for p in planners:
        out=f'results/benchmarks/{p}'; GridWorld(ScenarioConfig(planner=p,output_dir=out)).run(out); m=evaluate(out); m['planner']=p; rows.append(m)
    keys=sorted(set().union(*[r.keys() for r in rows]));
    with open('results/metrics/benchmark_summary.csv','w',newline='') as f: wr=csv.DictWriter(f,keys); wr.writeheader(); wr.writerows(rows)
    Path('results/reports/benchmark_report.md').write_text('# Synthetic Demo benchmark report\n\nGenerated from deterministic grid-world code. Results are synthetic, not real-robot claims.\n\n'+json.dumps(rows,indent=2))
if __name__=='__main__': main()
