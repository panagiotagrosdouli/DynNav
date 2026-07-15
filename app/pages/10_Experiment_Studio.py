from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from dynnav_dashboard.config import DEFAULT_SCENARIO
from dynnav_dashboard.simulation import build_environment, plan_astar, plan_risk_aware

st.set_page_config(page_title="DynNav Experiment Studio", page_icon="🧪", layout="wide")
st.title("Experiment Studio")
st.caption("Run deterministic single-seed, multi-seed, baseline-comparison, ablation, and sensitivity experiments.")
st.info("Synthetic interactive research environment. Results do not establish physical-robot safety, ROS2 validation, deployment readiness, or formal guarantees.")

experiment_type = st.selectbox(
    "Experiment type",
    ["Single run", "Multi-seed", "Baseline comparison", "Risk-weight sweep"],
)
planner = st.selectbox("Planner", ["Classical A*", "Risk-aware A*"])
seed_start = st.number_input("First seed", 0, 100000, 7, 1)
episodes = st.slider("Episodes", 1, 25, 5)
risk_weight = st.slider("Risk weight", 0.0, 8.0, 2.5, 0.1)

if experiment_type == "Single run":
    seeds = [int(seed_start)]
elif experiment_type == "Baseline comparison":
    seeds = list(range(int(seed_start), int(seed_start) + int(episodes)))
elif experiment_type == "Multi-seed":
    seeds = list(range(int(seed_start), int(seed_start) + int(episodes)))
else:
    seeds = list(range(int(seed_start), int(seed_start) + min(int(episodes), 10)))

estimated_runs = len(seeds) * (2 if experiment_type == "Baseline comparison" else 1)
if experiment_type == "Risk-weight sweep":
    estimated_runs *= 5
st.metric("Estimated planner runs", estimated_runs)


def execute(planner_name: str, seed: int, weight: float) -> dict:
    cfg = replace(DEFAULT_SCENARIO, random_seed=seed, risk_weight=weight)
    env = build_environment(cfg, seed=seed)
    result = plan_astar(env, cfg.start, cfg.goal) if planner_name == "Classical A*" else plan_risk_aware(env, cfg.start, cfg.goal, weight)
    return {
        "planner": planner_name,
        "seed": seed,
        "risk_weight": weight,
        "success": bool(result.success),
        "path_cells": len(result.path),
        "cost": float(result.cost),
        "expansions": int(result.expansions),
        "runtime_ms": float(result.runtime_ms),
        "avg_risk": float(result.avg_risk),
        "max_risk": float(result.max_risk),
    }

if st.button("Run experiment", type="primary", use_container_width=True):
    rows: list[dict] = []
    progress = st.progress(0.0, text="Preparing experiment")
    run_specs: list[tuple[str, int, float]] = []
    if experiment_type == "Baseline comparison":
        for seed in seeds:
            run_specs.extend([("Classical A*", seed, risk_weight), ("Risk-aware A*", seed, risk_weight)])
    elif experiment_type == "Risk-weight sweep":
        weights = [0.0, risk_weight * 0.5, risk_weight, risk_weight * 1.5, risk_weight * 2.0]
        for seed in seeds:
            run_specs.extend([("Risk-aware A*", seed, float(weight)) for weight in weights])
    else:
        run_specs = [(planner, seed, risk_weight) for seed in seeds]

    for index, spec in enumerate(run_specs, start=1):
        rows.append(execute(*spec))
        progress.progress(index / len(run_specs), text=f"Completed {index}/{len(run_specs)}")

    payload = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment_type": experiment_type,
        "scenario": asdict(DEFAULT_SCENARIO),
        "runs": rows,
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload["run_id"] = hashlib.sha256(payload_bytes).hexdigest()[:16]
    st.session_state["dynnav_experiment"] = payload
    st.success(f"Experiment {payload['run_id']} completed with {len(rows)} planner runs.")

payload = st.session_state.get("dynnav_experiment")
if payload:
    frame = pd.DataFrame(payload["runs"])
    st.subheader("Experiment results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Runs", len(frame))
    c2.metric("Success rate", f"{100.0 * frame['success'].mean():.1f}%")
    c3.metric("Mean cost", f"{frame['cost'].mean():.2f}")
    c4.metric("Mean runtime", f"{frame['runtime_ms'].mean():.3f} ms")
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.line_chart(frame, x="risk_weight", y=["cost", "avg_risk", "max_risk"])
    st.download_button("Download metrics CSV", frame.to_csv(index=False), f"dynnav_{payload['run_id']}_metrics.csv", "text/csv")
    st.download_button("Download experiment manifest", json.dumps(payload, indent=2), f"dynnav_{payload['run_id']}_manifest.json", "application/json")
