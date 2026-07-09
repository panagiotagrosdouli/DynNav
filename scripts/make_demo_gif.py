import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import imageio.v2 as imageio, matplotlib.pyplot as plt
from dynnav.simulation.grid_world import run_synthetic_demo

def make_demo(results_dir='results'):
    data=run_synthetic_demo(results_dir); d=Path(results_dir); Path('assets/gifs').mkdir(parents=True,exist_ok=True); Path('assets/videos').mkdir(parents=True,exist_ok=True); (d/'videos').mkdir(exist_ok=True); frames=d/'videos'/'frames'; frames.mkdir(parents=True,exist_ok=True); grid=data['grid']; risk=data['risk']; traj=data['trajectory']; safety=data['safety']; paths=[]; step=max(1,len(traj)//20)
    for i,p in list(enumerate(traj))[::step]:
        plt.figure(figsize=(4.8,3.2)); plt.imshow(grid,origin='lower',cmap='gray_r',alpha=.75); plt.imshow(risk,origin='lower',alpha=.25); plt.plot([q[0] for q in traj[:i+1]],[q[1] for q in traj[:i+1]],label='executed'); plt.scatter([traj[0][0]],[traj[0][1]],label='start'); plt.scatter([41],[27],marker='*',label='goal'); plt.scatter([p[0]],[p[1]],label='robot'); st=safety[min(i,len(safety)-1)]; plt.title(f'DynNav Dynamic Navigation Rerouting — Synthetic Demo\nstep={i} risk={float(st["risk"]):.2f} uncertainty={float(st["uncertainty"]):.2f} safety={st["state"]}'); plt.legend(fontsize=7); plt.tight_layout(); fp=frames/f'frame_{i:04d}.png'; plt.savefig(fp,dpi=70); plt.close(); paths.append(fp)
    imgs=[imageio.imread(p) for p in paths]; imageio.mimsave('assets/gifs/demo.gif',imgs,duration=0.12); imageio.mimsave(d/'videos'/'dynnav_demo.gif',imgs,duration=0.12); imageio.mimsave('assets/videos/demo.mp4',imgs,fps=6,macro_block_size=1); imageio.mimsave(d/'videos'/'dynnav_demo.mp4',imgs,fps=6,macro_block_size=1)
if __name__=='__main__': make_demo('results')
