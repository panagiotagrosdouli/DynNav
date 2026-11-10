"""C17 actual semantic graph regression tests, including cross-process grounding."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from topo_semantic_map import TopologicalSemanticMap
from topo_semantic_evaluator import build_demo_semantic_map, evaluate_grounding

def test_embeddings_stable_between_python_hash_seeds():
    source=("import sys,json;sys.path.insert(0,sys.argv[1]);"
            "from topo_semantic_map import TopologicalSemanticMap;"
            "print(json.dumps(TopologicalSemanticMap().embed_label_stub('robotics_lab')[:15].tolist()))")
    outputs=[]
    for seed in ("11","999"):
        env=dict(os.environ,PYTHONHASHSEED=seed)
        p=subprocess.run([sys.executable,"-c",source,str(ROOT)],capture_output=True,text=True,env=env,check=True)
        outputs.append(json.loads(p.stdout))
    assert outputs[0]==outputs[1]

def test_serialized_graph_preserves_embedding_and_blocked_edges():
    original=build_demo_semantic_map()
    query="robotics_lab"
    emb=original.embed_label_stub(query)
    first=original.ground_query(emb,top_k=1)
    corridor=next(nid for nid,node in original.nodes.items() if node.label=="corridor")
    lab=next(nid for nid,node in original.nodes.items() if node.label=="robotics_lab")
    original.invalidate_edge(corridor,lab)
    restored=TopologicalSemanticMap.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored.ground_query(emb,top_k=1)[0][1]=="robotics_lab"
    assert restored.ground_query(emb,top_k=1)[0][2]==pytest.approx(first[0][2])
    assert len(restored.edges)==len(original.edges)
    assert any(not e.passable for e in restored.edges)
    assert restored._next_id==len(original.nodes)

def test_non_contiguous_node_identifiers_persist():
    graph=TopologicalSemanticMap.from_dict({"nodes":[
        {"id":3,"label":"a","centroid":[0,0],"embedding":None},
        {"id":8,"label":"b","centroid":[1,0],"embedding":None}],
        "edges":[{"src":3,"dst":8,"weight":2,"passable":True,"type":"door"}]})
    assert graph.plan(3,8)==([3,8],2.0)
    assert graph.add_node("new",(4,4))==9

def test_invalid_edges_and_negative_weights_fail_closed():
    g=TopologicalSemanticMap()
    n=g.add_node("base",(0,0))
    with pytest.raises(ValueError):g.add_edge(n,99)
    with pytest.raises(ValueError):g.add_edge(n,n,weight=-1)
    with pytest.raises(ValueError):g.add_edge(n,n,weight=float("nan"))
    with pytest.raises(ValueError):TopologicalSemanticMap.from_dict({"nodes":[{"id":0,"label":"x","centroid":[0,0]}],
            "edges":[{"src":0,"dst":2,"weight":1,"passable":True,"type":"open"}]})

def test_nonfinite_embeddings_rejected_not_grounded():
    m=TopologicalSemanticMap()
    m.add_node("lab",(0,0),embedding=np.array([1.,2.]))
    with pytest.raises(ValueError):
        m.ground_query(np.array([1.,float("nan")]))
    with pytest.raises(ValueError):
        m.ground_query(np.array([1.,2.,3.]))
