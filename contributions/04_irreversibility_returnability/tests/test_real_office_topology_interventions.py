"""C04 regression tests for action-like synthetic topology changes on maps."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/"code"))
import returnability_map as rm

pytest.importorskip("networkx")
pytest.importorskip("scipy")
file=HERE/"experiments"/"eval_real_office_topology_interventions.py"
spec=importlib.util.spec_from_file_location("c04_topology_interventions",file)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_disconnection_after_actual_graph_articulation_injected():
    free=np.zeros((7,7),dtype=bool)
    free[3,:]=True
    graph=m.largest_connected_graph(free)
    pivot,base,robot,_,_=m.choose_fragile_states(graph,1)[0]
    before=rm.compute_return_cost_grid(free,np.zeros_like(free,dtype=float),
                                      (base[1],base[0]))
    changed=free.copy()
    changed[pivot[1],pivot[0]]=False
    after=rm.compute_return_cost_grid(changed,np.zeros_like(changed,dtype=float),
                                     (base[1],base[0]))
    assert before[robot[1],robot[0]]<1e8
    assert after[robot[1],robot[0]]>=1e8

def test_invalid_base_and_mismatch_fail_closed():
    grid=np.ones((5,5),dtype=bool)
    I=np.zeros((5,5))
    with pytest.raises(ValueError,match="outside"):
        rm.compute_return_cost_grid(grid,I,(-1,1))
    with pytest.raises(ValueError,match="identical"):
        rm.compute_return_cost_grid(grid,np.zeros((4,5)),(1,1))
    with pytest.raises(ValueError,match="configuration"):
        rm.compute_return_cost_grid(grid,I,(1,1),rm.ReturnabilityConfig(step_cost=-1))

def test_high_irreversibility_cell_cuts_return_path():
    free=np.zeros((5,5),dtype=bool)
    free[2,1:4]=True
    I=np.zeros((5,5),dtype=float)
    before=rm.compute_return_cost_grid(free,I,(2,1))
    assert before[2,3]==pytest.approx(2)
    I[2,2]=1.0
    after=rm.compute_return_cost_grid(free,I,(2,1),rm.ReturnabilityConfig(tau=.85))
    assert after[2,3]>=1e8
