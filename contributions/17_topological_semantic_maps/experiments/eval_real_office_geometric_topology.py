"""C17 extracted *geometric* zone topology on authentic LILocBench occupancy map.

Node labels are deterministic tile-component identifiers, NOT inferred room
semantics; no camera, CLIP, real place recognition or robot movement.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy.ndimage import label as cc_label
from dynnav.mapping.ros_map import load_ros_map

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
C03=HERE.parents[1]/"03_belief_risk_planning"/"experiments"
sys.path.insert(0,str(C03))
from topo_semantic_map import TopologicalSemanticMap
from eval_real_map_proximity_risk import occupancy,sample_connected_pairs

STRUCT=np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=np.uint8)

def extract_topology(grid,tile=50):
    if grid.ndim!=2 or tile<3:
        raise ValueError("Invalid occupancy geometry or tile size")
    h,w=grid.shape
    graph=TopologicalSemanticMap()
    region_ids=np.full((h,w),-1,dtype=np.int32)
    for y0 in range(0,h,tile):
        for x0 in range(0,w,tile):
            sub=(grid[y0:y0+tile,x0:x0+tile]==0)
            labels,count=cc_label(sub,structure=STRUCT)
            for local in range(1,count+1):
                ys,xs=np.nonzero(labels==local)
                if len(xs)==0:continue
                # Representative observed free cell, not unknown semantic centroid.
                x,y=int(xs[0]+x0),int(ys[0]+y0)
                name=f"tile_y{y0//tile}_x{x0//tile}_component{local}"
                nid=graph.add_node(name,(float(x),float(y)),source="geometric_tile_component")
                region_ids[y0+ys,x0+xs]=nid
    # A graph transition is inserted ONLY for actual adjacent free grid cells,
    # never for mere Euclidean distance of two region centroids.
    pairs=set()
    for a,b in ((region_ids[:,:-1],region_ids[:,1:]),(region_ids[:-1,:],region_ids[1:,:])):
        mask=(a>=0)&(b>=0)&(a!=b)
        for u,v in zip(a[mask],b[mask]):
            pairs.add(tuple(sorted((int(u),int(v)))))
    for u,v in sorted(pairs):
        graph.add_edge(u,v,weight=1.0,bidirectional=True,transition_type="observed_free_grid_adjacency")
    return graph,region_ids

def evaluate(map_yaml,output,n_tasks=6,seed=17,tile=50):
    import yaml
    map_yaml=map_yaml.resolve()
    meta=yaml.safe_load(map_yaml.read_text())
    original_image=(map_yaml.parent/meta["image"]).resolve()
    ros_map=load_ros_map(map_yaml,unknown_as_obstacle=True)
    grid=occupancy(ros_map)
    graph,region=extract_topology(grid,tile)
    tasks=sample_connected_pairs(grid,n_tasks,seed,min_distance=8)
    rows=[]
    for i,(start,goal) in enumerate(tasks):
        start_node=int(region[start[1],start[0]])
        goal_node=int(region[goal[1],goal[0]])
        path,cost=graph.plan(start_node,goal_node)
        if not path or path[0]!=start_node or path[-1]!=goal_node:
            raise AssertionError("Graph disconnected across originally connected free map")
        for a,b in zip(path,path[1:]):
            if not any(e.src==a and e.dst==b and e.passable for e in graph.edges):
                raise AssertionError("C17 reported a nonexistent graph transition")
        rows.append(dict(query=i,start_x=start[0],start_y=start[1],
                         goal_x=goal[0],goal_y=goal[1],graph_path_nodes=len(path),
                         graph_transition_count=len(path)-1,abstract_edge_cost=cost,
                         graph_connected=True))
    # Safe graph persistence must retain actual graph connectivity and all its node IDs.
    restored=TopologicalSemanticMap.from_dict(json.loads(json.dumps(graph.to_dict())))
    for r in rows:
        u=int(region[r["start_y"],r["start_x"]])
        v=int(region[r["goal_y"],r["goal_x"]])
        path,_=restored.plan(u,v)
        if not path:raise AssertionError("C17 real-map graph lost its connectivity after JSON roundtrip")
    output.mkdir(parents=True,exist_ok=True)
    with (output/"paired_topology_queries.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    summary=dict(evidence="REAL_OFFICE_MAP_GEOMETRY_ONLY_SYNTHETIC_TOPOLOGICAL_ZONE_LABELS",
                 official_yaml_sha256=hashlib.sha256(map_yaml.read_bytes()).hexdigest(),
                 official_image_sha256=hashlib.sha256(original_image.read_bytes()).hexdigest(),
                 map_dimensions=[int(grid.shape[1]),int(grid.shape[0])],
                 tile_cells=tile,graph_nodes=len(graph.nodes),directed_edges=len(graph.edges),
                 paired_queries=len(rows),valid_route_count=sum(x["graph_connected"] for x in rows),
                 semantics_from_real_sensor_annotations=False,
                 real_robot_navigation_trials=0,
                 claims_limit="Only static real occupancy geometry; graph labels are synthetic connected-component IDs. Not real language recognition or closed-loop physical navigation.")
    (output/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,indent=2))
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("map_yaml",type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--queries",type=int,default=6)
    p.add_argument("--tile",type=int,default=50)
    a=p.parse_args()
    evaluate(a.map_yaml,a.output_dir,n_tasks=a.queries,tile=a.tile)
if __name__=="__main__":
    main()
