import heapq, math, time
from dataclasses import dataclass
import numpy as np
from dynnav.core.types import GridPoint, Path, PlannerWeights

@dataclass
class PlanResult:
    path: Path; cost: float; planning_time_ms: float; expanded: int; planner: str

def neighbors(p, shape):
    h,w=shape; x,y=p
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx,ny=x+dx,y+dy
        if 0<=nx<w and 0<=ny<h: yield (nx,ny)

def heuristic(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])

def cell_cost(p,risk,unc,rec,w):
    x,y=p; return 1.0+w.lambda_risk*float(risk[y,x])+w.lambda_uncertainty*float(unc[y,x])-w.lambda_recoverability*float(rec[y,x])

def _search(grid,start,goal,risk=None,uncertainty=None,recoverability=None,weights=None,use_h=True,name='astar'):
    t0=time.perf_counter(); h,w=grid.shape
    risk=np.zeros_like(grid,float) if risk is None else risk; uncertainty=np.zeros_like(grid,float) if uncertainty is None else uncertainty; recoverability=np.zeros_like(grid,float) if recoverability is None else recoverability; weights=weights or PlannerWeights(0,0,0)
    pq=[(0,start)]; came={start:None}; g={start:0.0}; expanded=0
    while pq:
        _,cur=heapq.heappop(pq); expanded+=1
        if cur==goal: break
        for nb in neighbors(cur,(h,w)):
            x,y=nb
            if grid[y,x]==1: continue
            ng=g[cur]+max(0.05,cell_cost(nb,risk,uncertainty,recoverability,weights))
            if nb not in g or ng<g[nb]:
                g[nb]=ng; came[nb]=cur; heapq.heappush(pq,(ng+(heuristic(nb,goal) if use_h else 0),nb))
    dt=(time.perf_counter()-t0)*1000
    if goal not in came: return PlanResult([],math.inf,dt,expanded,name)
    path=[]; cur=goal
    while cur is not None: path.append(cur); cur=came[cur]
    return PlanResult(path[::-1],g[goal],dt,expanded,name)

def astar(grid,start,goal,**kw): return _search(grid,start,goal,use_h=True,name='astar',weights=PlannerWeights(0,0,0),**kw)
def dijkstra(grid,start,goal,**kw): return _search(grid,start,goal,use_h=False,name='dijkstra',weights=PlannerWeights(0,0,0),**kw)
def weighted_astar(grid,start,goal,risk,uncertainty,recoverability,weights,name='risk_aware_astar'): return _search(grid,start,goal,risk,uncertainty,recoverability,weights,True,name)
def plan(planner,grid,start,goal,risk,uncertainty,recoverability,weights):
    if planner=='dijkstra': return dijkstra(grid,start,goal)
    if planner=='astar': return astar(grid,start,goal)
    if planner=='uncertainty_aware_astar': return weighted_astar(grid,start,goal,risk,uncertainty,recoverability,PlannerWeights(0,weights.lambda_uncertainty,0),planner)
    if planner=='recoverability_aware_astar': return weighted_astar(grid,start,goal,risk,uncertainty,recoverability,PlannerWeights(0,0,weights.lambda_recoverability),planner)
    return weighted_astar(grid,start,goal,risk,uncertainty,recoverability,weights,planner)

def path_blocked(path,grid,dynamic): return any(grid[y,x]==1 or (x,y) in dynamic for x,y in path[:8])
