import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dynnav.simulation.grid_world import run_synthetic_demo
if __name__=='__main__': run_synthetic_demo('results')
