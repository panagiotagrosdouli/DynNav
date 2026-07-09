import numpy as np
from dynnav.core.types import ScenarioConfig
from dynnav.simulation.grid_world import GridWorld
from dynnav.planning.grid_planners import astar,dijkstra
from dynnav.risk.risk_model import compute_risk_map
from dynnav.uncertainty.uncertainty_model import compute_uncertainty_map
from dynnav.recoverability.recoverability_model import compute_recoverability_map
from dynnav.safety.supervisor import decide
from dynnav.evaluation.metrics import evaluate

def test_planners_find_paths():
    g=GridWorld(ScenarioConfig()).grid; assert astar(g,(2,2),(41,27)).path; assert dijkstra(g,(2,2),(41,27)).path

def test_fields_are_normalized():
    g=GridWorld(ScenarioConfig()).grid; known=np.ones_like(g,dtype=bool)
    for a in (compute_risk_map(g,[(10,10)],~known), compute_uncertainty_map(known), compute_recoverability_map(g,(2,2))): assert a.min()>=0 and a.max()<=1

def test_safety_transition(): assert decide(.1,.1,.8,True).state.value=='REROUTE'

def test_end_to_end(tmp_path):
    out=tmp_path/'results'; GridWorld(ScenarioConfig(max_steps=90)).run(out); m=evaluate(out); assert m['label']=='Synthetic Demo'; assert (out/'metrics'/'summary.json').exists()
