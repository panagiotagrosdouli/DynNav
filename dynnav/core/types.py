from dataclasses import dataclass
from enum import Enum

GridPoint = tuple[int, int]
Path = list[GridPoint]

class SafetyState(str, Enum):
    NORMAL='NORMAL'; CAUTION='CAUTION'; REROUTE='REROUTE'; SLOW_DOWN='SLOW_DOWN'; STOP='STOP'; MISSION_ABORT='MISSION_ABORT'

@dataclass(frozen=True)
class PlannerWeights:
    lambda_risk: float = 1.5
    lambda_uncertainty: float = 0.8
    lambda_recoverability: float = 0.7

@dataclass
class ScenarioConfig:
    seed: int = 7
    width: int = 44
    height: int = 30
    start: GridPoint = (2, 2)
    goal: GridPoint = (41, 27)
    planner: str = 'risk_aware_astar'
    max_steps: int = 260
    sensor_radius: int = 5
    dynamic_obstacle_count: int = 5
    reroute_cooldown: int = 3
    weights: PlannerWeights = PlannerWeights()
    output_dir: str = 'results'
