from __future__ import annotations

import csv
import io
import json
import time
from dataclasses import asdict, replace
from hashlib import sha256

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from dynnav_dashboard.config import DEFAULT_SCENARIO
from dynnav_dashboard.simulation import build_environment, simulate_rollout

st.set_page_config(page_title="DynNav Robot Lab", page_icon="🤖", layout="wide")

NOTICE = (
    "Synthetic interactive research environment. Results shown here do not establish physical-robot safety, "
    "ROS2 validation, deployment readiness, or formal guarantees."
)


def _scenario_signature(values: dict[str, object]) -> str:
    payload = json.dumps(values, sort_keys=True, default=str).encode("utf-8")
    return sha256(payload).hexdigest()[:16]


def _initial_state() -> None:
    defaults = {
        "robot_lab_frame": 0,
        "robot_lab_playing": False,
        "robot_lab_signature": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _supervisor_state(frame, rollout, local_risk: float, local_uncertainty: float, caution: float) -> str:
    if rollout.reached_goal and frame.step == rollout.frames[-1].step:
        return "GOAL REACHED"
    if not frame.path_remaining:
        return "SAFE STOP"
    if frame.replanned:
        return "REPLAN"
    if local_risk >= caution or local_uncertainty >= caution:
        return "CAUTION"
    return "NORMAL"


def _event_rows(rollout, env, caution: float) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    previous_state = None
    for index, frame in enumerate(rollout.frames):
        x, y = frame.robot
        risk = float(frame.risk_snapshot[y, x])
        uncertainty = float(env.uncertainty[y, x])
        state = _supervisor_state(frame, rollout, risk, uncertainty, caution)
        event = "navigation-step"
        severity = "info"
        if frame.replanned:
            event, severity = "route-replanned", "warning"
        if state == "CAUTION":
            event, severity = "caution-threshold", "warning"
        if state == "SAFE STOP":
            event, severity = "safe-stop", "error"
        if state == "GOAL REACHED":
            event, severity = "goal-reached", "success"
        if state != previous_state or frame.replanned or index in {0, len(rollout.frames) - 1}:
            rows.append(
                {
                    "frame": index,
                    "step": frame.step,
                    "event": event,
                    "robot_pose": str(frame.robot),
                    "safety_state": state,
                    "risk": round(risk, 6),
                    "uncertainty": round(uncertainty, 6),
                    "replans": frame.replan_count,
                    "planning_ms": round(frame.runtime_ms, 6),
                    "severity": severity,
                }
            )
        previous_state = state
    return rows


def _csv_bytes(rows: list[dict[str, object]]) -> bytes:
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return output.getvalue().encode("utf-8")


_initial_state()
st.title("Robot Lab")
st.caption("Run, inspect, replay, and export a deterministic closed-loop DynNav navigation episode.")
st.info(NOTICE)

with st.sidebar:
    st.header("Experiment controls")
    seed = st.number_input("Map seed", min_value=0, max_value=100_000, value=7, step=1)
    risk_weight = st.slider("Risk weight", 0.0, 6.0, 2.5, 0.1)
    planner_name = st.radio("Planner", ["Risk-aware A*", "Classical A*"], index=0)
    dynamic_step_every = st.slider("Move obstacles every N steps", 1, 6, 2)
    caution_threshold = st.slider("Caution threshold", 0.10, 0.95, 0.70, 0.05)
    playback_speed = st.slider("Playback speed (frames/s)", 1, 8, 3)
    show_uncertainty = st.checkbox("Show uncertainty", value=True)
    show_risk = st.checkbox("Show risk", value=True)
    st.caption("Changing experiment controls creates a new deterministic run and resets playback.")

cfg = replace(DEFAULT_SCENARIO, random_seed=int(seed), risk_weight=float(risk_weight))
run_inputs = {
    "seed": int(seed),
    "risk_weight": float(risk_weight),
    "planner": planner_name,
    "dynamic_step_every": int(dynamic_step_every),
    "caution_threshold": float(caution_threshold),
    "config": asdict(cfg),
}
signature = _scenario_signature(run_inputs)
if signature != st.session_state.robot_lab_signature:
    st.session_state.robot_lab_signature = signature
    st.session_state.robot_lab_frame = 0
    st.session_state.robot_lab_playing = False

env = build_environment(cfg, seed=int(seed))
rollout = simulate_rollout(
    env,
    cfg,
    use_risk_aware=planner_name == "Risk-aware A*",
    dynamic_step_every=int(dynamic_step_every),
)
if not rollout.frames:
    st.error("The selected configuration produced no simulation frames.")
    st.stop()

last_frame = len(rollout.frames) - 1
st.session_state.robot_lab_frame = min(st.session_state.robot_lab_frame, last_frame)

controls = st.columns([1, 1, 1, 1, 1, 3])
if controls[0].button("⏮ Restart", use_container_width=True):
    st.session_state.robot_lab_frame = 0
    st.session_state.robot_lab_playing = False
    st.rerun()
if controls[1].button("◀ Previous", use_container_width=True):
    st.session_state.robot_lab_frame = max(0, st.session_state.robot_lab_frame - 1)
    st.session_state.robot_lab_playing = False
    st.rerun()
if controls[2].button("▶ Play" if not st.session_state.robot_lab_playing else "⏸ Pause", use_container_width=True):
    st.session_state.robot_lab_playing = not st.session_state.robot_lab_playing
    st.rerun()
if controls[3].button("Next ▶", use_container_width=True):
    st.session_state.robot_lab_frame = min(last_frame, st.session_state.robot_lab_frame + 1)
    st.session_state.robot_lab_playing = False
    st.rerun()
if controls[4].button("⏭ End", use_container_width=True):
    st.session_state.robot_lab_frame = last_frame
    st.session_state.robot_lab_playing = False
    st.rerun()

selected_frame = controls[5].slider(
    "Timeline",
    0,
    last_frame,
    st.session_state.robot_lab_frame,
    key="robot_lab_timeline",
)
if selected_frame != st.session_state.robot_lab_frame:
    st.session_state.robot_lab_frame = selected_frame
    st.session_state.robot_lab_playing = False

frame = rollout.frames[st.session_state.robot_lab_frame]
robot_x, robot_y = frame.robot
local_risk = float(frame.risk_snapshot[robot_y, robot_x])
local_uncertainty = float(env.uncertainty[robot_y, robot_x])
supervisor = _supervisor_state(frame, rollout, local_risk, local_uncertainty, float(caution_threshold))

metrics = st.columns(7)
metrics[0].metric("Frame", f"{st.session_state.robot_lab_frame}/{last_frame}")
metrics[1].metric("Step", frame.step)
metrics[2].metric("Supervisor", supervisor)
metrics[3].metric("Replans", frame.replan_count)
metrics[4].metric("Route risk", f"{local_risk:.3f}")
metrics[5].metric("Uncertainty", f"{local_uncertainty:.3f}")
metrics[6].metric("Remaining", len(frame.path_remaining))

world_tab, diagnostics_tab, events_tab, export_tab = st.tabs(
    ["World view", "Diagnostics", "Event log", "Export & replay"]
)

with world_tab:
    plot_col, explanation_col = st.columns([2.3, 1])
    with plot_col:
        fig, ax = plt.subplots(figsize=(10, 7.5))
        occupancy = np.clip(env.static + frame.dynamic_snapshot, 0, 1)
        ax.imshow(occupancy, origin="lower", cmap="Greys", alpha=0.92)
        if show_uncertainty:
            ax.imshow(env.uncertainty, origin="lower", cmap="Purples", alpha=0.24)
        if show_risk:
            ax.imshow(frame.risk_snapshot, origin="lower", cmap="Oranges", alpha=0.27)
        if frame.path_remaining:
            px, py = zip(*frame.path_remaining)
            ax.plot(px, py, linewidth=2.8, label="Active route")
        dyn_y, dyn_x = np.where(frame.dynamic_snapshot > 0.5)
        if len(dyn_x):
            ax.scatter(dyn_x, dyn_y, marker="s", s=36, label="Dynamic obstacle")
        ax.scatter(robot_x, robot_y, marker=(3, 0, 0), s=210, label="Robot")
        ax.scatter(*cfg.start, marker="o", s=70, facecolors="none", label="Start")
        ax.scatter(*cfg.goal, marker="*", s=190, label="Goal")
        ax.set_title(f"Closed-loop navigation — {planner_name} — step {frame.step}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_aspect("equal")
        ax.legend(loc="upper left", fontsize=8)
        st.pyplot(fig, clear_figure=True)
    with explanation_col:
        st.subheader("Decision explanation")
        explanations = {
            "NORMAL": "The active route remains traversable and the local risk and uncertainty signals remain below the configured caution threshold.",
            "CAUTION": "The robot remains able to move, but at least one local signal crossed the caution threshold. The route is monitored more conservatively.",
            "REPLAN": "The route monitor invalidated or compromised the forward route, so the planner generated a replacement from the current robot cell.",
            "SAFE STOP": "No usable route is available in this frame. The explanatory supervisor stops rather than selecting an occupied route.",
            "GOAL REACHED": "The robot reached the configured goal and the episode terminated successfully.",
        }
        st.success(explanations[supervisor]) if supervisor == "GOAL REACHED" else st.write(explanations[supervisor])
        st.progress(local_risk, text=f"Local risk {local_risk:.3f}")
        st.progress(local_uncertainty, text=f"Local uncertainty {local_uncertainty:.3f}")
        st.write(f"Robot cell: `{frame.robot}`")
        st.write(f"Replanned now: `{'yes' if frame.replanned else 'no'}`")
        st.write(f"Planning time: `{frame.runtime_ms:.3f} ms`")

with diagnostics_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Episode metrics")
        st.json(
            {
                "run_id": signature,
                "planner": planner_name,
                "reached_goal": rollout.reached_goal,
                "final_robot": rollout.final_robot,
                "distance": round(rollout.total_distance, 4),
                "replans": rollout.total_replans,
                "average_risk": round(rollout.avg_risk, 6),
                "maximum_risk": round(rollout.max_risk, 6),
                "average_compute_ms": round(rollout.avg_compute_ms, 6),
                "blocked_dynamic_steps": rollout.collisions,
            }
        )
    with right:
        st.subheader("Internal loop")
        st.code(
            "observe → update occupancy → estimate uncertainty/risk → plan → monitor → "
            "continue/caution/replan/stop → record evidence",
            language="text",
        )
        st.write("Every displayed metric is derived from the current deterministic rollout, not from a hardcoded benchmark table.")

event_rows = _event_rows(rollout, env, float(caution_threshold))
with events_tab:
    st.dataframe(event_rows, hide_index=True, use_container_width=True)
    jump_options = {f"frame {row['frame']} — {row['event']}": int(row["frame"]) for row in event_rows}
    selected_event = st.selectbox("Jump to event", list(jump_options), key="robot_lab_event_jump")
    if st.button("Jump", key="robot_lab_jump_button"):
        st.session_state.robot_lab_frame = jump_options[selected_event]
        st.session_state.robot_lab_playing = False
        st.rerun()

with export_tab:
    manifest = {
        "schema_version": 1,
        "run_id": signature,
        "application": "DynNav Robot Lab",
        "inputs": run_inputs,
        "result": {
            "reached_goal": rollout.reached_goal,
            "final_robot": rollout.final_robot,
            "total_distance": rollout.total_distance,
            "total_replans": rollout.total_replans,
            "average_risk": rollout.avg_risk,
            "maximum_risk": rollout.max_risk,
            "average_compute_ms": rollout.avg_compute_ms,
            "blocked_dynamic_steps": rollout.collisions,
        },
        "events": event_rows,
        "evidence_boundary": NOTICE,
    }
    st.download_button(
        "Download run manifest (JSON)",
        json.dumps(manifest, indent=2, default=str),
        file_name=f"dynnav_robot_lab_{signature}.json",
        mime="application/json",
    )
    st.download_button(
        "Download event log (CSV)",
        _csv_bytes(event_rows),
        file_name=f"dynnav_robot_lab_events_{signature}.csv",
        mime="text/csv",
    )
    uploaded = st.file_uploader("Inspect a saved Robot Lab manifest", type=["json"])
    if uploaded is not None:
        try:
            replay_manifest = json.load(uploaded)
            if replay_manifest.get("schema_version") != 1 or "inputs" not in replay_manifest:
                st.error("Unsupported or incomplete manifest.")
            else:
                st.success("Manifest structure is valid. Match its input controls to reproduce the run.")
                st.json(replay_manifest["inputs"])
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            st.error(f"Invalid JSON manifest: {exc}")

if st.session_state.robot_lab_playing:
    if st.session_state.robot_lab_frame >= last_frame:
        st.session_state.robot_lab_playing = False
    else:
        time.sleep(1.0 / float(playback_speed))
        st.session_state.robot_lab_frame += 1
        st.rerun()
