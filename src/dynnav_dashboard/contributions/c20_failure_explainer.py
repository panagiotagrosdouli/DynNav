"""C20 — Failure Explainer: episode metrics translated into explanations."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from ..config import COLORS
from ._common import (
    apply_theme,
    explanation_block,
    interpretation_block,
    metrics_row,
    section_header,
)


# Each "rule" maps a condition over episode metrics into an explanation phrase
# and a contribution score. The score is used to rank phrases.
def _explain(metrics: dict) -> tuple[list[tuple[str, float]], str]:
    """Return a ranked list of (phrase, score) and a one-line summary."""
    reasons: list[tuple[str, float]] = []
    m = metrics

    if m["min_clearance"] < 0.4:
        s = (0.4 - m["min_clearance"]) / 0.4
        reasons.append(("repeated low-clearance interactions with obstacles", 1.0 * s))
    if m["max_risk"] > 0.7:
        s = (m["max_risk"] - 0.7) / 0.3
        reasons.append(("perceived risk peaks above the safety threshold", 1.0 * s))
    if m["mode_transitions"] > 8:
        s = min(1.0, (m["mode_transitions"] - 8) / 12)
        reasons.append(("excessive safe-mode chattering near boundaries", 0.7 * s))
    if m["replan_count"] > 6:
        s = min(1.0, (m["replan_count"] - 6) / 10)
        reasons.append(("frequent replanning suggesting unstable estimator", 0.8 * s))
    if m["battery_remaining"] < 0.15:
        s = (0.15 - m["battery_remaining"]) / 0.15
        reasons.append(("near-depletion battery state at incident time", 1.0 * s))
    if m["mean_speed"] > 0.85:
        s = (m["mean_speed"] - 0.85) / 0.15
        reasons.append(("high commanded speed reducing reaction margin", 0.85 * s))
    if m["estimator_rmse"] > 0.3:
        s = min(1.0, (m["estimator_rmse"] - 0.3) / 0.5)
        reasons.append(("localisation error exceeding planner tolerance", 0.9 * s))
    if m["humans_proximity_violations"] > 0:
        s = min(1.0, m["humans_proximity_violations"] / 5.0)
        reasons.append(("multiple violations of human proxemic zones", 0.6 * s))

    reasons.sort(key=lambda r: r[1], reverse=True)

    if not reasons:
        return [], "Episode completed within nominal envelopes."
    top = reasons[0][0]
    summary = f"Primary cause: {top}."
    return reasons, summary


def render(st_ctx=st) -> None:
    explanation_block(
        "C20 — Failure Explainer: From Metrics to Human-Readable Causes",
        "Post-incident analysis is only useful when the engineer on call "
        "can understand it. DynNav records dozens of episode metrics "
        "(clearance, risk, replan rate, estimator RMSE, etc.) and runs "
        "them through a small rule-based explainer that produces a ranked "
        "list of human-readable causes plus a one-line summary. The "
        "ranking score reflects each condition's distance from its safe "
        "envelope.",
    )

    section_header("Interactive controls — synthetic episode metrics")
    c1, c2, c3 = st.columns(3)
    min_clearance = c1.slider("Min clearance (m)", 0.05, 1.50, 0.25, 0.05,
                                key="c20_clear")
    max_risk = c1.slider("Max risk", 0.0, 1.0, 0.82, 0.02, key="c20_risk")
    mode_tx = c1.slider("Safe-mode transitions", 0, 30, 12, key="c20_tx")
    replans = c2.slider("Replan count", 0, 20, 8, key="c20_rep")
    batt = c2.slider("Battery remaining", 0.0, 1.0, 0.10, 0.02, key="c20_bat")
    mspeed = c2.slider("Mean commanded speed (norm.)", 0.1, 1.0, 0.92, 0.02,
                         key="c20_sp")
    est_rmse = c3.slider("Estimator RMSE (m)", 0.0, 1.0, 0.42, 0.02,
                          key="c20_est")
    prox_viol = c3.slider("Human proximity violations", 0, 8, 2, key="c20_prox")
    success = c3.toggle("Mission outcome: success", value=False, key="c20_succ")

    metrics = {
        "min_clearance": float(min_clearance),
        "max_risk": float(max_risk),
        "mode_transitions": int(mode_tx),
        "replan_count": int(replans),
        "battery_remaining": float(batt),
        "mean_speed": float(mspeed),
        "estimator_rmse": float(est_rmse),
        "humans_proximity_violations": int(prox_viol),
    }
    reasons, summary = _explain(metrics)

    section_header("Ranked causes")
    if reasons:
        labels = [r[0] for r in reasons]
        scores = [r[1] for r in reasons]
        fig = go.Figure(go.Bar(
            x=scores, y=labels, orientation="h",
            marker_color=[
                COLORS["danger"] if s > 0.7 else
                COLORS["highlight"] if s > 0.4 else
                COLORS["primary"]
                for s in scores
            ],
            text=[f"{s:.2f}" for s in scores], textposition="auto",
        ))
        fig.update_xaxes(title="Cause severity score", range=[0, 1.05])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(apply_theme(fig, height=340), use_container_width=True)
    else:
        st.success("No abnormal causes detected.")

    section_header("Generated explanation")
    border = COLORS["success"] if success and not reasons else COLORS["danger"]
    body_lines = [f"<b>{summary}</b>"]
    if reasons:
        body_lines.append("<ul style='margin-top:0.4rem;padding-left:1.2rem'>")
        for phrase, score in reasons[:4]:
            body_lines.append(
                f"<li style='margin-bottom:0.25rem;color:{COLORS['text']}'>"
                f"<span style='opacity:0.85'>{phrase}</span> "
                f"<span style='color:{COLORS['text_muted']};font-size:0.8rem'>"
                f"(score {score:.2f})</span></li>"
            )
        body_lines.append("</ul>")
    st.markdown(
        f"<div style='background:{COLORS['surface']};border-left:4px solid {border};"
        f"border-radius:8px;padding:1rem 1.2rem;font-size:0.95rem;"
        f"color:{COLORS['text']};'>{''.join(body_lines)}</div>",
        unsafe_allow_html=True,
    )

    metrics_row([
        ("Mission outcome",
         "SUCCESS" if success else "FAILURE",
         COLORS["success"] if success else COLORS["danger"]),
        ("Causes flagged", f"{len(reasons)}",
         COLORS["highlight"] if reasons else COLORS["success"]),
        ("Top cause score",
         f"{reasons[0][1]:.2f}" if reasons else "0.00",
         COLORS["danger"] if reasons else COLORS["success"]),
    ])

    interpretation_block(
        "The explainer behaves like a rule-mined triage tool. Adjust the "
        "metrics to model different incidents and observe the ranking "
        "shift — for example, low clearance combined with high speed makes "
        "<i>reduced reaction margin</i> the dominant cause, while the "
        "same low clearance with low speed shifts the blame onto "
        "<i>localisation error</i>. In production this layer can also be "
        "trained from labelled incident reports for better coverage."
    )
