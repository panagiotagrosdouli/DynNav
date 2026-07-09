from dataclasses import dataclass
from dynnav.planning.grid_planners import path_blocked

@dataclass
class RerouteEvent:
    timestamp:int; robot_position:tuple[int,int]; trigger_type:str; previous_path_length:int; new_path_length:int; risk_before:float; risk_after:float; success:bool

def should_reroute(t,path,grid,dynamic,risk,uncertainty,recoverability,cooldown_until=0):
    if t<cooldown_until: return False,'cooldown'
    if not path: return True,'no_path'
    if path_blocked(path,grid,set(dynamic)): return True,'path_blocked'
    x,y=path[min(1,len(path)-1)]
    if risk[y,x]>0.60: return True,'risk_threshold'
    if uncertainty[y,x]>0.75: return True,'uncertainty_threshold'
    if recoverability[y,x]<0.18: return True,'recoverability_threshold'
    return False,'none'
