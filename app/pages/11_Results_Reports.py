from __future__ import annotations

import io
import json
import zipfile
from dataclasses import replace

import pandas as pd
import streamlit as st

from dynnav_dashboard.config import DEFAULT_SCENARIO
from dynnav_dashboard.simulation import build_environment, plan_astar, plan_risk_aware

st.set_page_config(page_title="DynNav Results & Reports", page_icon="📊", layout="wide")
st.title("Results & Reports")
st.caption("Inspect, filter, export, and replay deterministic DynNav experiment manifests.")
st.info("Synthetic software evidence only. Replayed results are not ROS2, Gazebo, hardware, or certified-safety validation.")

source = st.radio("Result source", ["Current session", "Upload manifest"], horizontal=True)
payload = st.session_state.get("dynnav_experiment") if source == "Current session" else None

if source == "Upload manifest":
    uploaded = st.file_uploader("Upload experiment manifest", type=["json"])
    if uploaded:
        try:
            payload = json.load(uploaded)
            if not isinstance(payload, dict) or not isinstance(payload.get("runs"), list):
                raise ValueError("manifest must contain a runs array")
            st.success("Manifest structure validated.")
        except (ValueError, json.JSONDecodeError) as exc:
            st.error(f"Invalid manifest: {exc}")
            payload = None

if not payload:
    st.warning("No experiment is available. Run Experiment Studio or upload a manifest.")
    st.stop()

runs = pd.DataFrame(payload["runs"])
required = {"planner", "seed", "risk_weight", "success", "cost", "runtime_ms", "avg_risk", "max_risk"}
missing = sorted(required - set(runs.columns))
if missing:
    st.error(f"Manifest is missing required fields: {', '.join(missing)}")
    st.stop()

planner_options = sorted(runs["planner"].astype(str).unique())
selected_planners = st.multiselect("Planner filter", planner_options, default=planner_options)
success_filter = st.selectbox("Mission result", ["All", "Success", "Failure"])
filtered = runs[runs["planner"].isin(selected_planners)]
if success_filter == "Success":
    filtered = filtered[filtered["success"]]
elif success_filter == "Failure":
    filtered = filtered[~filtered["success"]]

st.subheader("Run summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Visible runs", len(filtered))
c2.metric("Success rate", f"{100.0 * filtered['success'].mean():.1f}%" if len(filtered) else "—")
c3.metric("Mean risk", f"{filtered['avg_risk'].mean():.3f}" if len(filtered) else "—")
c4.metric("Mean runtime", f"{filtered['runtime_ms'].mean():.3f} ms" if len(filtered) else "—")
st.dataframe(filtered, use_container_width=True, hide_index=True)
if len(filtered):
    st.bar_chart(filtered.groupby("planner")[["cost", "avg_risk", "runtime_ms"]].mean())

st.subheader("Manifest")
st.json({key: value for key, value in payload.items() if key != "runs"})

st.subheader("Replay one recorded run")
replay_index = st.selectbox(
    "Recorded run",
    list(range(len(runs))),
    format_func=lambda index: f"#{index + 1} · {runs.iloc[index]['planner']} · seed {int(runs.iloc[index]['seed'])} · weight {float(runs.iloc[index]['risk_weight']):.2f}",
)
recorded = runs.iloc[int(replay_index)].to_dict()
if st.button("Replay and compare", type="primary"):
    seed = int(recorded["seed"])
    weight = float(recorded["risk_weight"])
    cfg = replace(DEFAULT_SCENARIO, random_seed=seed, risk_weight=weight)
    env = build_environment(cfg, seed=seed)
    if recorded["planner"] == "Classical A*":
        replay = plan_astar(env, cfg.start, cfg.goal)
    elif recorded["planner"] == "Risk-aware A*":
        replay = plan_risk_aware(env, cfg.start, cfg.goal, weight)
    else:
        st.error(f"Replay is unavailable for planner {recorded['planner']!r}; no silent substitution was performed.")
        st.stop()

    compared = pd.DataFrame(
        [
            {"metric": "success", "recorded": bool(recorded["success"]), "replayed": bool(replay.success)},
            {"metric": "cost", "recorded": float(recorded["cost"]), "replayed": float(replay.cost)},
            {"metric": "runtime_ms", "recorded": float(recorded["runtime_ms"]), "replayed": float(replay.runtime_ms)},
            {"metric": "avg_risk", "recorded": float(recorded["avg_risk"]), "replayed": float(replay.avg_risk)},
            {"metric": "max_risk", "recorded": float(recorded["max_risk"]), "replayed": float(replay.max_risk)},
        ]
    )
    st.dataframe(compared, use_container_width=True, hide_index=True)
    deterministic_metrics = ["success", "cost", "avg_risk", "max_risk"]
    differences = []
    for metric in deterministic_metrics:
        a = recorded[metric]
        b = getattr(replay, metric)
        if isinstance(a, bool):
            equal = bool(a) == bool(b)
        else:
            equal = abs(float(a) - float(b)) <= 1e-9
        if not equal:
            differences.append(metric)
    if differences:
        st.warning("Replay differs for deterministic metrics: " + ", ".join(differences))
    else:
        st.success("Deterministic planner outputs reproduced. Runtime may vary by machine and process load.")

csv_data = filtered.to_csv(index=False)
json_data = json.dumps(payload, indent=2)
report = "# DynNav Experiment Report\n\n" + f"Run ID: `{payload.get('run_id', 'unknown')}`\n\n" + filtered.describe(include="all").to_markdown() + "\n"

bundle = io.BytesIO()
with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
    archive.writestr("manifest.json", json_data)
    archive.writestr("metrics.csv", csv_data)
    archive.writestr("report.md", report)

st.subheader("Downloads")
d1, d2, d3, d4 = st.columns(4)
d1.download_button("CSV", csv_data, "dynnav_results.csv", "text/csv")
d2.download_button("JSON", json_data, "dynnav_manifest.json", "application/json")
d3.download_button("Markdown report", report, "dynnav_report.md", "text/markdown")
d4.download_button("Run bundle", bundle.getvalue(), "dynnav_run_bundle.zip", "application/zip")
