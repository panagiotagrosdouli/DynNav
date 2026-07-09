import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dynnav.simulation.grid_world import run_synthetic_demo
from dynnav.evaluation.metrics import evaluate
from scripts.generate_figures import generate
from scripts.make_demo_gif import make_demo
from scripts.run_benchmarks import main as bench
if __name__=='__main__': run_synthetic_demo('results'); evaluate('results'); generate('results'); make_demo('results'); bench(); print('Synthetic Demo complete: metrics, figures, demo.gif and demo.mp4 generated.')
