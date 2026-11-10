"""C09 multi-agent discrete-safety and explicit liveness-limit regressions.

All robots are simulated agents, NOT ROS2 hardware vehicles or
network-connected robots.
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import numpy as np
import pytest

SRC=Path(__file__).resolve().parents[1]/"code"/"decentralized_nav.py"
spec=importlib.util.spec_from_file_location("c09_decentralized_nav_safe",SRC)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)

def test_headon_adjacent_swap_is_refused_in_narrow_corridor():
    world=np.zeros((1,2),dtype=np.uint8)
    robots=[module.RobotAgent(robot_id=0,pos=(0,0),goal=(1,0)),
            module.RobotAgent(robot_id=1,pos=(1,0),goal=(0,0))]
    result=module.run_decentralized(world,robots,max_steps=5,share_risk=False)
    assert result.all_reached is False
    assert [r.pos for r in robots]==[(0,0),(1,0)]
    assert result.collision_events>0  # blocked movement requests, not crashes

def test_noncolliding_agents_reach_separate_goals():
    world=np.zeros((5,9),dtype=np.uint8)
    robots=[module.RobotAgent(robot_id=0,pos=(0,0),goal=(0,3)),
            module.RobotAgent(robot_id=1,pos=(8,0),goal=(8,3))]
    result=module.run_decentralized(world,robots,max_steps=15,share_risk=False)
    assert result.all_reached is True
    assert len({r.pos for r in robots})==2
    assert result.collision_events==0

def test_duplicate_initial_position_rejected():
    world=np.zeros((4,4),dtype=np.uint8)
    robots=[module.RobotAgent(robot_id=0,pos=(0,0),goal=(1,1)),
            module.RobotAgent(robot_id=1,pos=(0,0),goal=(2,2))]
    with pytest.raises(ValueError,match="one initial grid cell"):
        module.run_decentralized(world,robots)

def test_duplicate_robot_identifier_and_blocked_goal_rejected():
    world=np.zeros((4,4),dtype=np.uint8)
    robots=[module.RobotAgent(robot_id=0,pos=(0,0),goal=(2,0)),
            module.RobotAgent(robot_id=0,pos=(3,3),goal=(2,2))]
    with pytest.raises(ValueError,match="Duplicate robot_id"):
        module.run_decentralized(world,robots)
    world[2,2]=1
    robots[1].robot_id=1
    with pytest.raises(ValueError,match="blocked/outside"):
        module.run_decentralized(world,robots)

def test_robot_initially_at_goal_does_not_move():
    grid=np.zeros((5,5),dtype=np.uint8)
    robots=[module.RobotAgent(robot_id=1,pos=(0,0),goal=(0,0)),
            module.RobotAgent(robot_id=2,pos=(4,4),goal=(3,4))]
    result=module.run_decentralized(grid,robots,max_steps=6,share_risk=False)
    assert result.all_reached
    assert robots[0].pos==(0,0)
    assert robots[0].steps==0

def test_sequential_centralized_baseline_refuses_headon_swap():
    grid=np.zeros((1,2),dtype=np.uint8)
    agents=[module.RobotAgent(0,(0,0),(1,0)),
            module.RobotAgent(1,(1,0),(0,0))]
    result=module.run_centralized(grid,agents,max_steps=10)
    assert not result.all_reached
    assert [a.pos for a in agents]==[(0,0),(1,0)]
    assert result.collision_events==2
    assert result.strategy == "centralized"  # legacy public label; implementation is sequential

def test_sequential_centralized_baseline_reaches_separate_goals():
    grid=np.zeros((5,9),dtype=np.uint8)
    agents=[module.RobotAgent(0,(0,0),(0,3)),
            module.RobotAgent(1,(8,0),(8,3))]
    result=module.run_centralized(grid,agents,max_steps=10)
    assert result.all_reached
    assert len(set(a.pos for a in agents))==2

def test_shared_target_prioritizes_lower_id_without_overlap():
    grid=np.zeros((12,12),dtype=np.uint8)
    agents=[module.RobotAgent(0,(0,0),(5,5)),
            module.RobotAgent(1,(1,0),(5,5))]
    outcome=module.run_decentralized(grid,agents,max_steps=200,share_risk=False)
    assert agents[0].reached_goal
    assert agents[0].pos==(5,5)
    assert not agents[1].reached_goal
    assert len({r.pos for r in agents})==2
    assert not outcome.all_reached
