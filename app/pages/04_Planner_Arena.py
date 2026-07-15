from __future__ import annotations

from dataclasses import asdict, replace
import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from dynnav_dashboard.config import DEFAULT_SCENARIO, ScenarioConfig
from dynnav_dashboard.simulation import build_environment, plan_astar, plan_risk_aware

st.set_page_config(page_title="DynNav Planner Arena", page_icon="🏁", layout="wide")
st.title("Planner Arena")
st.caption("Run available planners on exactly the same map, seed, risk field, start, and goal.")
st.info(
    "Only planners implemented in the current dashboard engine are shown. Results are synthetic and are not physical-robot or ROS2 validation."
)

active = st.session_state.get("active_scenario", asdict(DEFAULT_SCENARIO))
base = {**asdict(DEFAULT_SCENARIO), **active}
base["start"] = tuple(base.get("start", DEFAULT_SCENARIO.start))
base["goal"] = tuple(base.get("goal", DEFAULT_SCENARIO.goal))

with st.sidebar:
    st.header("Arena controls")
    seed = st.number_input("Scenario seed", 0, 100_000, int(base["random_seed"]), key="arena_seed")
    risk_weight = st.slider("Risk-aware weight", 0.0, 8.0, float(base["risk_weight"]), 0.1, key="arena_risk")
    show_risk = st.checkbox("Show risk field", True, key="arena_show_risk")
    show_uncertainty = st.checkbox("Show uncertainty", False, key="arena_show_uncertainty")
    selected = st.multiselect(
        "Planners",
        ["Classical A*", "Risk-aware A*"],
        default=["Classical A*", "Risk-aware A*"],
        key="arena_planners",
    )

if not selected:
    st.warning("Select at least one available planner.")
    st.stop()

cfg = ScenarioConfig(**base)
cfg = replace(cfg, random_seed=int(seed), risk_weight=float(risk_weight))
env = build_environment(cfg, seed=cfg.random_seed)

results = {}
if "Classical A*" in selected:
    results["Classical A*"] = plan_astar(env, cfg.start, cfg.goal)
if "Risk-aware A*" in selected:
    results["Risk-aware A*"] = plan_risk_aware(env, cfg.start, cfg.goal, cfg.risk_weight)

rows = []
for name, result in results.items():
    rows.append(
        {
            "Planner": name,
            "Success": bool(result.success),
            "Path cells": len(result.path),
            "Cost": float(result.cost),
            "Expanded nodes": int(result.expansions),
            "Runtime ms": float(result.runtime_ms),
            "Average risk": float(result.avg_risk),
            "Maximum risk": float(result.max_risk),
        }
    )
metrics = pd.DataFrame(rows)

plot_col, insight_col = st.columns([1.7, 1])
with plot_col:
    st.subheader("Shared-world path comparison")
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.imshow(env.static + env.dynamic, origin="lower", cmap="Greys", alpha=0.92)
    if show_uncertainty:
        ax.imshow(env.uncertainty, origin="lower", cmap="Purples", alpha=0.25)
    if show_risk:
        ax.imshow(env.risk, origin="lower", cmap="Oranges", alpha=0.28)
    line_styles = {"Classical A*": "--", "Risk-aware A*": "-"}
    for name, result in results.items():
        if result.success and result.path:
            xs, ys = zip(*result.path)
            ax.plot(xs, ys, line_styles[name], linewidth=2.8, label=name)
    ax.scatter(*cfg.start, s=90, marker="o", label="Start")
    ax.scatter(*cfg.goal, s=180, marker="*", label="Goal")
    ax.set_title(f"Seed {cfg.random_seed} · risk weight {cfg.risk_weight:.1f}")
    ax.set_aspect("equal")
    ax.legend(loc="upper left")
    st.pyplot(fig, clear_figure=True)

with insight_col:
    st.subheader("Decision summary")
    successful = metrics[metrics["Success"]]
    if successful.empty:
        st.error("No selected planner found a route on this scenario.")
    else:
        shortest = successful.loc[successful["Cost"].idxmin()]
        safest = successful.loc[successful["Average risk"].idxmin()]
        fastest = successful.loc[successful["Runtime ms"].idxmin()]
        st.metric("Lowest path cost", shortest["Planner"], f"{shortest['Cost']:.2f}")
        st.metric("Lowest average risk", safest["Planner"], f"{safest['Average risk']:.3f}")
        st.metric("Lowest planning time", fastest["Planner"], f"{fastest['Runtime ms']:.3f} ms")

        if len(successful) > 1:
            classical = successful[successful["Planner"] == "Classical A*"]
            risk = successful[successful["Planner"] == "Risk-aware A*"]
            if not classical.empty and not risk.empty:
                c = classical.iloc[0]
                r = risk.iloc[0]
                risk_delta = r["Average risk"] - c["Average risk"]
                cost_delta = r["Cost"] - c["Cost"]
                st.markdown(
                    f"Risk-aware A* changed average route risk by **{risk_delta:+.3f}** and path cost by **{cost_delta:+.2f}**. "
                    "These values come directly from the shared synthetic planning run."
                )

st.subheader("Planner metrics")
st.dataframe(metrics.round(4), hide_index=True, use_container_width=True)

chart_left, chart_right = st.columns(2)
with chart_left:
    st.subheader("Cost versus risk")
    st.scatter_chart(metrics.set_index("Planner")[["Cost", "Average risk"]], use_container_width=True)
with chart_right:
    st.subheader("Search effort")
    st.bar_chart(metrics.set_index("Planner")[["Expanded nodes", "Runtime ms"]], use_container_width=True)

csv_buffer = io.StringIO()
metrics.to_csv(csv_buffer, index=False)
st.download_button(
    "Download planner comparison CSV",
    data=csv_buffer.getvalue(),
    file_name=f"dynnav_planner_arena_seed_{cfg.random_seed}.csv",
    mime="text/csv",
)

st.subheader("Reproducibility record")
st.json(
    {
        "scenario": asdict(cfg),
        "selected_planners": selected,
        "map_seed": cfg.random_seed,
        "shared_environment": True,
        "available_planners": ["Classical A*", "Risk-aware A*"],
    }
)
