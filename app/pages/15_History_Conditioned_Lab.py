"""Interactive history-conditioned safe-return research demonstration."""
from __future__ import annotations

from dataclasses import asdict
import json

import matplotlib.pyplot as plt
import streamlit as st

from dynnav_dashboard.history_lab import (
    CLOSURE, ENDPOINT, FREE, RISKY_HISTORY, SAFE, SAFE_HISTORY, TRIGGER,
    compare_histories,
)

st.set_page_config(page_title="DynNav History-Aware Planning", page_icon="🧩", layout="wide")
st.title("History-Conditioned Safe Return")
st.caption("A genuine exact-oracle calculation of two traversal histories ending at the same coordinate.")
st.info(
    "Synthetic graph mechanism example only. This does not execute Nav2/Gazebo or "
    "demonstrate physical safety. The state-augmentation principle is standard Markovization."
)

with st.sidebar:
    p = st.slider("Conditional closure probability", min_value=0.0,
                  max_value=1.0, value=0.8, step=0.05)
    show_paths = st.checkbox("Display both executed histories", value=True)

try:
    comparison = compare_histories(float(p))
except ValueError as exc:
    st.error(f"Invalid scenario: {exc}")
    st.stop()

m1, m2, m3 = st.columns(3)
m1.metric("No-trigger history · return chance", f"{comparison.safe_return_probability:.1%}")
m2.metric("Triggered history · return chance", f"{comparison.risky_return_probability:.1%}")
m3.metric("Same-endpoint separation", f"{comparison.separation:.1%}")

st.markdown(
    "Both paths terminate at **(4, 2)**. Traversing the marked directed edge activates "
    "a Bernoulli future closure at the corridor bottleneck **(2, 2)**. "
    "This closure is not assumed to occur immediately when activated."
)

left, right = st.columns([2, 1])
with left:
    fig, ax = plt.subplots(figsize=(9, 6))
    for x in range(5):
        for y in range(5):
            color = "#f1f5f9" if (x, y) in FREE else "#334155"
            ax.add_patch(plt.Rectangle((x-0.5, y-0.5), 1, 1,
                                       facecolor=color, edgecolor="#94a3b8", linewidth=0.8))
    if show_paths:
        for path, color, label in [
            (SAFE_HISTORY, "#0e7490", "No trigger"),
            (RISKY_HISTORY, "#d97706", "Activated hazard"),
        ]:
            ax.plot([c[0] for c in path], [c[1] for c in path],
                    marker="o", linewidth=2, alpha=0.84, color=color, label=label)
    ax.scatter([SAFE[0]], [SAFE[1]], s=150, marker="s", color="#16a34a", zorder=6, label="Safe set")
    ax.scatter([ENDPOINT[0]], [ENDPOINT[1]], s=190, marker="*", color="#7c3aed", zorder=7, label="Shared endpoint")
    ax.scatter([CLOSURE[0]], [CLOSURE[1]], s=180, marker="X", color="#dc2626", zorder=7, label="Future closure")
    (sx, sy), (tx, ty) = TRIGGER
    ax.annotate("", xy=(tx, ty+0.12), xytext=(sx, sy+0.12),
                arrowprops=dict(arrowstyle="-|>", color="#b45309", lw=3))
    ax.set(xlim=(-0.7, 4.7), ylim=(-0.7, 4.7), xlabel="grid x", ylabel="grid y",
           title="Controlled 5×5 topology and activation edge")
    ax.set_aspect("equal")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1))
    st.pyplot(fig)
    plt.close(fig)
with right:
    st.subheader("Why endpoint-only estimation fails")
    st.write(
        "A deterministic estimator that sees only the shared endpoint must output "
        "the same value for both histories. Its worst-history absolute error is at least "
        "half their return-probability separation."
    )
    st.metric("Endpoint-only minimax error lower bound",
              f"{comparison.endpoint_only_minimax_error_bound:.1%}")
    st.latex(r"\min_{\hat R(x)}\max_{h\in\{h_1,h_2\}}"
             r"\left|\hat R(x)-R(x,h)\right|\geq "
             r"\frac{|R_1-R_2|}{2}")
    st.caption(
        "This is a representation result under the declared finite independent-hazard "
        "model, not evidence that all state-only methods fail. A sufficiently augmented "
        "MDP/POMDP can distinguish histories."
    )

st.subheader("Reproducibility")
st.write("Changing the slider recomputes the exact combinatorial return oracle; it does not load precomputed values.")
output = {
    "evidence_type": "synthetic_exact_oracle_live_calculation",
    "algorithm": "dynnav.commitment_hazard.exact_history_conditioned_return_probability",
    "safe_cell": SAFE,
    "shared_endpoint": ENDPOINT,
    "trigger": TRIGGER,
    "future_closure_cell": CLOSURE,
    "safe_history": SAFE_HISTORY,
    "risky_history": RISKY_HISTORY,
    "result": asdict(comparison),
}
st.json(output)
st.download_button(
    "Download exact-oracle scenario JSON", json.dumps(output, indent=2),
    file_name="dynnav_history_aliasing_demo.json", mime="application/json",
)
st.caption(
    "For retained publication measurements, see the separate Publication Evidence page. "
    "This interactive example does not modify the pinned manuscript evidence."
)
