"""C15 identical-cadence controls and honest evidence-label tests."""
import importlib.util
import sys
from pathlib import Path
import pytest

SCRIPT=Path(__file__).resolve().parents[1]/"experiments"/"eval_time_aligned_latency.py"
spec=importlib.util.spec_from_file_location("c15_equal_clock",SCRIPT)
m=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=m
spec.loader.exec_module(m)

def test_two_methods_see_identical_input_cadence():
    pairs=m.paired_scenario(speed=6,dt_us=10000,n_frames=8)
    assert len(pairs)==2
    assert pairs[0]["frame_period_us"]==pairs[1]["frame_period_us"]
    assert pairs[0]["n_frames"]==pairs[1]["n_frames"]
    assert all(not row["physical_camera"] and not row["physical_robot"] for row in pairs)

def test_first_frame_bright_obstacle_is_visible_to_frame_baseline():
    rows=m.paired_scenario(speed=6,dt_us=33333,n_frames=8)
    assert rows[0]["detected"] is True
    assert rows[0]["first_detection_time_us"]==0

def test_invalid_time_grid_fails_closed():
    with pytest.raises(ValueError):
        m.paired_scenario(speed=5,dt_us=0,n_frames=8)
    with pytest.raises(ValueError):
        m.paired_scenario(speed=0,dt_us=10000,n_frames=8)

def test_reproducible_honest_summary(tmp_path):
    report=m.run(tmp_path,intervals=(10000,),speeds=(3,),n_frames=8)
    assert report["n_paired_scenarios"]==1
    assert report["actual_event_camera"] is False
    assert report["real_robot_trials"]==0
    assert (tmp_path/"paired_trials.csv").exists()

def test_actual_on_off_events_are_generated_after_first_reference_frame():
    import numpy as np
    sys.path.insert(0,str(SCRIPT.parents[1]))
    from neuromorphic_sensing import DVSSimulator,DVSSimulatorConfig
    sim=DVSSimulator(DVSSimulatorConfig(height=4,width=4,noise_rate=0.0,
                                        threshold_pos=.12,threshold_neg=.12))
    start=np.full((4,4),0.1)
    bright=start.copy(); bright[1,2]=0.9
    first=sim.process_frame(start,dt_us=10000)
    on=sim.process_frame(bright,dt_us=10000)
    off=sim.process_frame(start,dt_us=10000)
    assert not first
    assert any((e.x,e.y,e.polarity)==(2,1,1) for e in on)
    assert any((e.x,e.y,e.polarity)==(2,1,-1) for e in off)

def test_simulated_motion_produces_genuine_signal_driven_events():
    from neuromorphic_benchmark import moving_obstacle_frames
    from neuromorphic_sensing import DVSSimulator,DVSSimulatorConfig
    frames=moving_obstacle_frames(n_frames=4,height=32,width=32,obstacle_size=5,
                                  speed_px_per_frame=4)
    sim=DVSSimulator(DVSSimulatorConfig(height=32,width=32,noise_rate=0.0))
    counts=[len(sim.process_frame(frame)) for frame in frames]
    assert counts[0]==0
    assert sum(counts[1:])>0,counts
