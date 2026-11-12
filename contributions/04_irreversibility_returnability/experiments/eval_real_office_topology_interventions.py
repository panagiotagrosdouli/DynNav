"""C04 returnability under artificially blocked passages on genuine office map.

Real source: LILocBench ROS occupancy grid mapped by an actual robot.
Intervention: synthetic removal of an actual map free-space articulation cell.
This is offline graph-topology stress testing, NOT proof a robot action caused
the blockage or that a Dingo experienced the resulting retreat failure.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.ndimage import label
import yaml

from dynnav.mapping.ros_map import load_ros_map

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"code"))
from returnability_map import ReturnabilityConfig, compute_return_cost_grid

FOUR=np.array([[0,1,0],[1,1,1],[0,1,0]],dtype=np.uint8)

def map_grid(ros_map):
    free=np.ones((ros_map.grid.height,ros_map.grid.width),dtype=bool)
    for x,y in ros_map.grid.obstacles:
        free[y,x]=False
    return free

def largest_connected_graph(free):
    labels,n=label(free,structure=FOUR)
    if n<1:
        raise ValueError("No free map component")
    sizes=np.bincount(labels.reshape(-1))
    sizes[0]=0
    dominant=int(np.argmax(sizes))
    ys,xs=np.nonzero(labels==dominant)
    graph=nx.Graph()
    for y,x in zip(ys.tolist(),xs.tolist()):
        graph.add_node((x,y))
        if x>0 and labels[y,x-1]==dominant:
            graph.add_edge((x,y),(x-1,y))
        if y>0 and labels[y-1,x]==dominant:
            graph.add_edge((x,y),(x,y-1))
    return graph

def choose_fragile_states(graph,n_cases):
    if n_cases<1:
        raise ValueError("n_cases must be >=1")
    cases=[]
    considered=0
    # Each candidate must genuinely disconnect a previously connected
    # component when the simulated passage is removed.
    for pivot in list(nx.articulation_points(graph)):
        neighbours=list(graph.neighbors(pivot))
        graph.remove_node(pivot)
        components=sorted(nx.connected_components(graph),key=len,reverse=True)
        graph.add_node(pivot)
        graph.add_edges_from((pivot,n) for n in neighbours)
        considered+=1
        if len(components)<2:
            raise AssertionError("Articulation decomposition inconsistent")
        # Select a meaningful robot-side subgroup where possible.
        if len(components[1])<2:
            if considered<100:
                continue
            # One-cell dead-end is also an exact topology failure, but less
            # informative than a multi-cell separated region.
        base=min(components[0])
        robot=min(components[1])
        if nx.has_path(graph,base,robot) is False:
            raise AssertionError("Pre-intervention base and robot not connected")
        cases.append((pivot,base,robot,len(components[0]),len(components[1])))
        if len(cases)>=n_cases:
            break
    if len(cases)!=n_cases:
        raise RuntimeError(f"Insufficient real mapped articulation cells: {len(cases)}/{n_cases}")
    return cases

def evaluate(map_yaml,output_dir,n_cases):
    map_yaml=map_yaml.resolve()
    metadata=yaml.safe_load(map_yaml.read_text(encoding="utf-8"))
    image=(map_yaml.parent/metadata["image"]).resolve()
    ros_map=load_ros_map(map_yaml,unknown_as_obstacle=True)
    free=map_grid(ros_map)
    graph=largest_connected_graph(free)
    cases=choose_fragile_states(graph,n_cases)
    irreversibility=np.zeros_like(free,dtype=float)
    cfg=ReturnabilityConfig(tau=.85,use_8conn=False)
    rows=[]
    for idx,(pivot,base,robot,main_size,isolated_size) in enumerate(cases):
        initial=compute_return_cost_grid(free,irreversibility,(base[1],base[0]),cfg)
        before=float(initial[robot[1],robot[0]])
        changed=free.copy()
        changed[pivot[1],pivot[0]]=False
        after_grid=compute_return_cost_grid(changed,irreversibility,(base[1],base[0]),cfg)
        after=float(after_grid[robot[1],robot[0]])
        if not (before<cfg.unreachable_cost*.5 and after>=cfg.unreachable_cost*.5):
            raise AssertionError("Injected real-map topology change did not break returnability")
        rows.append(dict(case=idx,pivot_x=pivot[0],pivot_y=pivot[1],
                         base_x=base[0],base_y=base[1],
                         simulated_robot_x=robot[0],simulated_robot_y=robot[1],
                         originally_connected_free_component_nodes=graph.number_of_nodes(),
                         post_cut_large_component_nodes=main_size,
                         post_cut_robot_component_nodes=isolated_size,
                         original_return_distance_cells=before,
                         after_injection_returnable=False,
                         original_returnable=True,
                         synthetic_intervention="single_mapped_passage_blocked"))
    output_dir.mkdir(parents=True,exist_ok=True)
    with (output_dir/"trials.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report=dict(evidence="real_occupancy_map_OFFLINE_with_artificial_topology_obstruction",
                source_map_yaml_sha256=hashlib.sha256(map_yaml.read_bytes()).hexdigest(),
                source_map_image_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                cases=len(rows),
                map_dimensions=[ros_map.grid.width,ros_map.grid.height],
                metric="real map graph reachability to virtual base before/after an artificially blocked free-space articulation cell",
                robot_action_caused_obstruction=False,
                physical_robot_trials=0,
                real_robot_recovery_success_rate_unavailable=True,
                scientific_limit="Artificial topological intervention on authentic recorded map, NOT causal real robot manipulation or safe-return robot motion")
    (output_dir/"summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2,sort_keys=True))
    print("C04 observed synthetic topology failures:",len(rows))
    return rows,report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("map_yaml",type=Path)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--n-cases",type=int,default=3)
    a=p.parse_args()
    evaluate(a.map_yaml,a.output_dir,a.n_cases)
if __name__=="__main__":
    main()
