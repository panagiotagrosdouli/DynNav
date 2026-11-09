"""Interactive C11 validation of semantic navigation goals."""

from __future__ import annotations

import json

import plotly.graph_objects as go
import streamlit as st

from dynnav.researcher.vlm_goal_validator import ValidationConfig, validate_vlm_goal
from ._common import apply_theme, explanation_block, section_header


def render(st_ctx=st) -> None:
    explanation_block(
        "C11 — VLM goal validation",
        "A vision-language model proposes a semantic destination. DynNav checks its confidence, region label, "
        "image coordinates, and metric distance before allowing the proposal to reach navigation. This panel "
        "runs the repository's goal validator; it does not call or simulate a VLM.",
    )

    section_header("Candidate semantic goal")
    left, right = st_ctx.columns(2)
    with left:
        description = st_ctx.text_input("Goal description", "go forward through the corridor")
        region = st_ctx.selectbox(
            "Proposed region",
            ["corridor", "doorway", "open_space", "room", "exit", "hallway", "frontier", "restricted_room"],
        )
        confidence = st_ctx.slider("VLM confidence", 0.0, 1.0, 0.86, 0.01)
    with right:
        pixel_u = st_ctx.number_input("Image u (pixels)", 0, 1280, 320)
        pixel_v = st_ctx.number_input("Image v (pixels)", 0, 960, 240)
        waypoint_x = st_ctx.number_input("Waypoint x (metres)", -20.0, 20.0, 3.0, 0.1)
        waypoint_y = st_ctx.number_input("Waypoint y (metres)", -20.0, 20.0, 0.2, 0.1)

    maximum_distance = st_ctx.slider("Maximum waypoint distance (m)", 1.0, 15.0, 8.0, 0.5)
    cfg = ValidationConfig(max_waypoint_distance_m=maximum_distance)
    report = validate_vlm_goal(
        description=description,
        region_label=region,
        confidence=confidence,
        pixel_hint=(int(pixel_u), int(pixel_v)),
        image_shape=(480, 640),
        metric_waypoint=(float(waypoint_x), float(waypoint_y)),
        cfg=cfg,
    )

    section_header("Validation decision")
    color = {"ACCEPT": "#15803d", "ASK_HUMAN": "#b45309", "REJECT": "#b91c1c"}[report.decision.value]
    st_ctx.markdown(
        f'<div style="border-left:5px solid {color};padding:1rem;border-radius:.5rem;'
        f'background:rgba(148,163,184,.10)"><strong style="font-size:1.25rem;color:{color}">'
        f'{report.decision.value}</strong><br>{report.reason}</div>',
        unsafe_allow_html=True,
    )

    checks = {
        "Confidence": report.valid_confidence,
        "Allowed region and text": report.valid_region,
        "Pixel inside 640×480 image": report.valid_pixel,
        "Waypoint within configured range": report.valid_waypoint,
    }
    check_column, output_column = st_ctx.columns([1, 1])
    with check_column:
        st_ctx.dataframe(
            [{"Check": name, "Result": "PASS" if passed else "FAIL"} for name, passed in checks.items()],
            hide_index=True,
            use_container_width=True,
        )
    with output_column:
        st_ctx.code(json.dumps(report.to_dict(), indent=2), language="json")

    fig = go.Figure(
        go.Bar(
            x=["confidence", "region", "pixel", "waypoint"],
            y=[float(report.valid_confidence), float(report.valid_region), float(report.valid_pixel), float(report.valid_waypoint)],
            marker_color=["#16a34a" if value else "#dc2626" for value in checks.values()],
        )
    )
    fig.update_yaxes(range=[0, 1.15], tickvals=[0, 1], ticktext=["Fail", "Pass"])
    fig.update_layout(showlegend=False, title="Validator checks", margin={"t": 50, "b": 10})
    st_ctx.plotly_chart(apply_theme(fig, height=280), use_container_width=True)
