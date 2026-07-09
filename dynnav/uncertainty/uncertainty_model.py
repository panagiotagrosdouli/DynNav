import numpy as np

def compute_uncertainty_map(known_mask, frontier_weight=0.4):
    unknown=(~known_mask).astype(float); h,w=known_mask.shape; frontier=np.zeros((h,w),float)
    for y in range(1,h-1):
        for x in range(1,w-1):
            if known_mask[y,x] and not known_mask[y-1:y+2,x-1:x+2].all(): frontier[y,x]=1.0
    return np.clip(unknown+frontier_weight*frontier,0,1)
