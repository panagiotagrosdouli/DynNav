import csv,json
from pathlib import Path
import numpy as np
from dynnav.core.types import ScenarioConfig
from dynnav.planning.grid_planners import plan
from dynnav.risk.risk_model import compute_risk_map
from dynnav.uncertainty.uncertainty_model import compute_uncertainty_map
from dynnav.recoverability.recoverability_model import compute_recoverability_map
from dynnav.rerouting.rerouter import should_reroute,RerouteEvent
from dynnav.safety.supervisor import decide

class GridWorld:
    def __init__(self,cfg:ScenarioConfig): self.cfg=cfg; self.grid=np.zeros((cfg.height,cfg.width),int); self.dynamic=[]; self._build_world()
    def _build_world(self):
        g=self.grid; g[0,:]=g[-1,:]=g[:,0]=g[:,-1]=1; g[8:22,12]=1; g[8:22,25]=1; g[14,12:26]=1; g[14,18]=0; g[9:13,25]=0; g[20,12]=0; g[4:7,31:39]=1; g[20:24,5:11]=1; g[2,2]=0; g[27,41]=0; self.dynamic=[(18+i*2,9+i%4) for i in range(self.cfg.dynamic_obstacle_count)]
    def _move_dynamic(self,t): self.dynamic=[(x,9+((t+i)%8)) for i,(x,y) in enumerate(self.dynamic)]
    def _discover(self,known,robot):
        rx,ry=robot; rr=self.cfg.sensor_radius; h,w=known.shape
        for y in range(max(0,ry-rr),min(h,ry+rr+1)):
            for x in range(max(0,rx-rr),min(w,rx+rr+1)):
                if abs(rx-x)+abs(ry-y)<=rr: known[y,x]=True
        return known
    def run(self,output_dir='results'):
        out=Path(output_dir); (out/'metrics').mkdir(parents=True,exist_ok=True); (out/'videos').mkdir(exist_ok=True); (out/'figures').mkdir(exist_ok=True)
        known=np.zeros_like(self.grid,dtype=bool); robot=self.cfg.start; goal=self.cfg.goal; path=[]; trajectory=[robot]; planned=[]; reroutes=[]; safety=[]; dynlog=[]; plan_times=[]; collisions=0; near=0; success=False; cooldown=0
        for t in range(self.cfg.max_steps):
            self._move_dynamic(t); dynlog += [{'t':t,'id':i,'x':x,'y':y} for i,(x,y) in enumerate(self.dynamic)]; known=self._discover(known,robot); unknown=~known
            risk=compute_risk_map(self.grid,self.dynamic,unknown); unc=compute_uncertainty_map(known); rec=compute_recoverability_map(self.grid,self.cfg.start); visible=np.where(known,self.grid,0)
            need,trigger=should_reroute(t,path,visible,self.dynamic,risk,unc,rec,cooldown)
            if need or not path:
                res=plan(self.cfg.planner,visible,robot,goal,risk,unc,rec,self.cfg.weights); plan_times.append(res.planning_time_ms); old=len(path); path=res.path; planned.append({'t':t,'planner':res.planner,'path':path,'planning_time_ms':res.planning_time_ms}); after=float(np.mean([risk[y,x] for x,y in path]) if path else 1.0); reroutes.append(RerouteEvent(t,robot,trigger,old,len(path),float(risk[robot[1],robot[0]]),after,bool(path)).__dict__); cooldown=t+self.cfg.reroute_cooldown
            blocked=len(path)>1 and (path[1] in self.dynamic or self.grid[path[1][1],path[1][0]]==1); dec=decide(float(risk[robot[1],robot[0]]),float(unc[robot[1],robot[0]]),float(rec[robot[1],robot[0]]),blocked); safety.append({'t':t,'x':robot[0],'y':robot[1],'state':dec.state.value,'reason':dec.reason,'risk':float(risk[robot[1],robot[0]]),'uncertainty':float(unc[robot[1],robot[0]]),'recoverability':float(rec[robot[1],robot[0]])})
            if blocked: path=[]; near+=1; continue
            if len(path)>1: robot=path[1]; path=path[1:]
            trajectory.append(robot)
            if robot in self.dynamic: collisions+=1; break
            if robot==goal: success=True; break
        risk=compute_risk_map(self.grid,self.dynamic,~known); unc=compute_uncertainty_map(known); rec=compute_recoverability_map(self.grid,self.cfg.start); np.save(out/'metrics'/'risk_map.npy',risk); np.save(out/'metrics'/'uncertainty_map.npy',unc); np.save(out/'metrics'/'recoverability_map.npy',rec)
        with open(out/'metrics'/'executed_trajectory.csv','w',newline='') as f: wr=csv.DictWriter(f,['t','x','y']); wr.writeheader(); wr.writerows({'t':i,'x':x,'y':y} for i,(x,y) in enumerate(trajectory))
        (out/'metrics'/'planned_paths.json').write_text(json.dumps(planned,indent=2))
        for name,rows,fields in [('reroute_events.csv',reroutes,['timestamp','robot_position','trigger_type','previous_path_length','new_path_length','risk_before','risk_after','success']),('dynamic_obstacles.csv',dynlog,['t','id','x','y']),('safety_events.csv',safety,['t','x','y','state','reason','risk','uncertainty','recoverability'])]:
            with open(out/'metrics'/name,'w',newline='') as f: wr=csv.DictWriter(f,fields); wr.writeheader(); wr.writerows(rows)
        summary={'label':'Synthetic Demo','success':success,'collision_count':collisions,'near_miss_count':near,'reroute_count':len(reroutes),'travel_time_steps':len(trajectory)-1,'trajectory_length':len(trajectory)-1,'average_planning_time_ms':float(np.mean(plan_times) if plan_times else 0),'mission_completion':bool(success)}; (out/'metrics'/'mission_summary.json').write_text(json.dumps(summary,indent=2)); return {'grid':self.grid,'trajectory':trajectory,'risk':risk,'uncertainty':unc,'recoverability':rec,'summary':summary,'safety':safety,'dynamic_obstacles':dynlog,'reroutes':reroutes}

def run_synthetic_demo(output_dir='results'): return GridWorld(ScenarioConfig(output_dir=output_dir)).run(output_dir)
