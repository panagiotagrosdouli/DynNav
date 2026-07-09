import numpy as np
from collections import deque

def compute_recoverability_map(grid,start):
    h,w=grid.shape; dist=np.full((h,w),np.inf); q=deque([start]); dist[start[1],start[0]]=0
    while q:
        x,y=q.popleft()
        for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0<=nx<w and 0<=ny<h and grid[ny,nx]==0 and not np.isfinite(dist[ny,nx]): dist[ny,nx]=dist[y,x]+1; q.append((nx,ny))
    finite=dist[np.isfinite(dist)]; maxd=float(finite.max()) if finite.size else 1.0
    base=np.where(np.isfinite(dist),1.0-dist/maxd,0.0); esc=np.zeros_like(base)
    for y in range(1,h-1):
        for x in range(1,w-1):
            if grid[y,x]==0: esc[y,x]=sum(grid[ny,nx]==0 for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)))/4
    return np.clip(0.65*base+0.35*esc,0,1)
