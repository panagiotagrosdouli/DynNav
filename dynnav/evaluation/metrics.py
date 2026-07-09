import csv,json
from pathlib import Path
import numpy as np

def evaluate(results_dir='results'):
    d=Path(results_dir)/'metrics'; traj=list(csv.DictReader(open(d/'executed_trajectory.csv'))); saf=list(csv.DictReader(open(d/'safety_events.csv'))); summary=json.loads((d/'mission_summary.json').read_text())
    summary.update({'path_length':max(0,len(traj)-1),'safety_intervention_count':sum(1 for r in saf if r['state']!='NORMAL'),'risk_exposure':float(np.mean([float(r['risk']) for r in saf]) if saf else 0),'uncertainty_exposure':float(np.mean([float(r['uncertainty']) for r in saf]) if saf else 0),'recoverability_exposure':float(np.mean([float(r['recoverability']) for r in saf]) if saf else 0)})
    (d/'summary.json').write_text(json.dumps(summary,indent=2))
    with open(d/'metrics.csv','w',newline='') as f: wr=csv.DictWriter(f,summary.keys()); wr.writeheader(); wr.writerow(summary)
    return summary
