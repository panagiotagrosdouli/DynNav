"""Geometric C17 topology does not invent traversability through tile walls."""
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest
pytest.importorskip("scipy")
path=Path(__file__).resolve().parents[1]/"experiments"/"eval_real_office_geometric_topology.py"
spec=importlib.util.spec_from_file_location("c17_real_geometric_topology",path)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)

def test_wall_between_tiles_prevents_false_edges():
    grid=np.zeros((12,12),dtype=np.uint8)
    grid[:,6]=1
    graph,region=module.extract_topology(grid,tile=3)
    start=int(region[1,1]); goal=int(region[9,10])
    path,_=graph.plan(start,goal)
    assert not path
    assert region[1,6]==-1

def test_free_passage_and_json_restore_retains_connectivity():
    grid=np.zeros((12,12),dtype=np.uint8)
    grid[:,6]=1
    grid[5,6]=0
    graph,region=module.extract_topology(grid,tile=3)
    start=int(region[1,1]); goal=int(region[9,10])
    path,_=graph.plan(start,goal)
    assert path
    restored=module.TopologicalSemanticMap.from_dict(graph.to_dict())
    assert restored.plan(start,goal)[0]==path
    assert all(edge.weight>=0 for edge in graph.edges)

def test_map_fully_blocked_has_no_nodes():
    graph,region=module.extract_topology(np.ones((9,9),dtype=np.uint8),tile=3)
    assert not graph.nodes
    assert np.all(region==-1)
