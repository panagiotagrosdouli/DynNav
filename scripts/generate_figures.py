import sys,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt
import numpy as np

def generate(results_dir='results'):
    d=Path(results_dir); (d/'figures').mkdir(parents=True,exist_ok=True); Path('assets/figures').mkdir(parents=True,exist_ok=True); risk=np.load(d/'metrics'/'risk_map.npy'); unc=np.load(d/'metrics'/'uncertainty_map.npy'); rec=np.load(d/'metrics'/'recoverability_map.npy'); traj=[(int(r['x']),int(r['y'])) for r in csv.DictReader(open(d/'metrics'/'executed_trajectory.csv'))]
    for name,arr,title in [('risk_heatmap.png',risk,'Synthetic Demo risk map'),('uncertainty_heatmap.png',unc,'Synthetic Demo uncertainty map'),('recoverability_heatmap.png',rec,'Synthetic Demo recoverability map')]:
        plt.figure(figsize=(7,4)); plt.imshow(arr,origin='lower'); plt.colorbar(); plt.title(title); plt.tight_layout(); plt.savefig(d/'figures'/name,dpi=160); plt.savefig(Path('assets/figures')/name,dpi=160); plt.close()
    xs=[p[0] for p in traj]; ys=[p[1] for p in traj]; plt.figure(figsize=(7,4)); plt.imshow(risk,origin='lower',alpha=.45); plt.plot(xs,ys,label='executed trajectory'); plt.scatter([xs[0]],[ys[0]],label='start'); plt.scatter([xs[-1]],[ys[-1]],marker='*',label='final'); plt.legend(); plt.title('Synthetic Demo trajectory'); plt.tight_layout(); plt.savefig(d/'figures'/'trajectory.png',dpi=160); plt.savefig('assets/figures/trajectory.png',dpi=160); plt.close()
if __name__=='__main__': generate('results')
