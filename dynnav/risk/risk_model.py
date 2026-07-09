import numpy as np

def normalize(a):
    a=a.astype(float); m=float(a.max()); return a/m if m>0 else a

def _dist(shape, pts):
    h,w=shape; yy,xx=np.indices((h,w)); d=np.full((h,w),h+w,float)
    for x,y in pts: d=np.minimum(d,np.abs(xx-x)+np.abs(yy-y))
    return d

def obstacle_proximity_risk(grid,radius=5):
    pts=[(int(x),int(y)) for y,x in np.argwhere(grid==1)]; d=_dist(grid.shape,pts) if pts else np.zeros_like(grid,float)
    return normalize(np.where(grid==1,1,np.maximum(0,(radius-d)/radius)))

def dynamic_obstacle_risk(shape,dynamic,radius=6):
    if not dynamic: return np.zeros(shape,float)
    return normalize(np.maximum(0,(radius-_dist(shape,dynamic))/radius))

def narrow_passage_risk(grid):
    p=np.pad(grid,1,constant_values=1); b=p[1:-1,2:]+p[1:-1,:-2]+p[2:,1:-1]+p[:-2,1:-1]
    return np.where(grid==0,b/4,1)

def compute_risk_map(grid,dynamic,unknown):
    return normalize(0.55*obstacle_proximity_risk(grid)+0.3*dynamic_obstacle_risk(grid.shape,dynamic)+0.15*unknown.astype(float)+0.2*narrow_passage_risk(grid))
