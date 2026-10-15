"""C01-ERGO exploratory optimal A* with bounded neural tie-breaking.

Neural estimates NEVER change the primary f=g+Manhattan ordering. Cache keys
include the full map digest and goal: no stale neural values after map changes.
This is a research prototype, not an implementation of LPA* or Rational Lazy A*.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import heapq
import math
import time
from typing import Callable
import numpy as np

Node = tuple[int, int]
Prediction = Callable[[Node, Node, np.ndarray], float]
NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))

def manhattan(n: Node, goal: Node) -> int:
    return abs(n[0] - goal[0]) + abs(n[1] - goal[1])

def fingerprint(grid: np.ndarray) -> str:
    arr = np.ascontiguousarray(grid)
    h = hashlib.sha256()
    h.update(str((arr.shape, arr.dtype.str)).encode())
    h.update(arr.tobytes())
    return h.hexdigest()

def valid(grid: np.ndarray, n: Node) -> bool:
    x,y=n
    return 0 <= y < grid.shape[0] and 0 <= x < grid.shape[1] and grid[y,x] == 0

@dataclass
class SearchResult:
    path: list[Node] | None
    expansions: int
    neural_calls: int
    cache_hits: int
    neural_seconds: float
    total_seconds: float

class ExactMapCache:
    """Conservative map-specific cache. Reuse across identical maps and goals only."""
    def __init__(self) -> None:
        self.values: dict[tuple[str, Node, Node], float] = {}
    def get(self, digest: str, node: Node, goal: Node) -> float | None:
        return self.values.get((digest,node,goal))
    def put(self, digest: str, node: Node, goal: Node, value: float) -> None:
        self.values[(digest,node,goal)] = value

def search(grid: np.ndarray, start: Node, goal: Node, predict: Prediction | None = None,
           *, budget: int = 0, cache: ExactMapCache | None = None,
           gating: Callable[[Node, Node, np.ndarray], bool] | None = None) -> SearchResult:
    """Optimal under 4-connected, non-negative unit edges, even with arbitrary predictions.

    Neural values are only tie-breakers among equal primary f. Closed nodes need
    no reopening because the primary Manhattan heuristic is consistent.
    """
    t0 = time.perf_counter()
    if budget < 0:
        raise ValueError("budget must be non-negative")
    if not valid(grid,start) or not valid(grid,goal):
        raise ValueError("start and goal must be free in-bounds cells")
    digest = fingerprint(grid) if cache is not None else ""
    calls = hits = expansions = 0
    neural_time = 0.0
    def tie(n: Node) -> float:
        nonlocal calls,hits,neural_time
        if predict is None or (gating is not None and not gating(n,goal,grid)):
            return 0.0
        if cache is not None:
            v = cache.get(digest,n,goal)
            if v is not None:
                hits += 1
                return -v
        if calls >= budget:
            return 0.0
        ts=time.perf_counter()
        v=float(predict(n,goal,grid))
        neural_time += time.perf_counter()-ts
        calls += 1
        if not math.isfinite(v):
            return 0.0
        if cache is not None:
            cache.put(digest,n,goal,v)
        return -v
    serial=0
    # (primary f, secondary neural priority, smaller -g, serial, node, g snapshot)
    openq=[(float(manhattan(start,goal)),tie(start),0,serial,start,0)]
    best:dict[Node,int]={start:0}
    parent:dict[Node,Node|None]={start:None}
    closed:set[Node]=set()
    while openq:
        _,_,_,_,cur,g=heapq.heappop(openq)
        if cur in closed or g != best[cur]:
            continue
        closed.add(cur)
        expansions+=1
        if cur==goal:
            path=[cur]
            while parent[cur] is not None:
                cur=parent[cur]
                path.append(cur)
            path.reverse()
            return SearchResult(path,expansions,calls,hits,neural_time,time.perf_counter()-t0)
        for dx,dy in NEIGHBORS:
            nxt=(cur[0]+dx,cur[1]+dy)
            if not valid(grid,nxt):
                continue
            ng=g+1
            if ng < best.get(nxt,math.inf):
                best[nxt]=ng
                parent[nxt]=cur
                serial+=1
                heapq.heappush(openq,(ng+manhattan(nxt,goal),tie(nxt),-ng,serial,nxt,ng))
    return SearchResult(None,expansions,calls,hits,neural_time,time.perf_counter()-t0)
