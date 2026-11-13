"""Evidence browser: explicitly read-only and sourced from pinned research artifacts."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from dynnav_dashboard.audit_view import render_audit_evidence

from dynnav_dashboard.publication_evidence import (
    CLAIMS, MANIFEST, gazebo_probe_summary, load_claim_rows, load_manifest,
    publication_summary,
)

st.set_page_config(page_title="DynNav Publication Evidence", page_icon="📑", layout="wide")
st.title("Publication Evidence & Claim Boundaries")
st.caption("Pinned publication measurements, explicit limitations, and traceable sources.")
st.warning(
    "Read-only historical research evidence, not a new experiment. "
    "Synthetic model results do not prove deployment safety or physical-robot efficacy. "
    "Gazebo probes validate integration, NOT a stable comparative navigation advantage."
)

try:
    manifest = load_manifest()
    claim_rows = load_claim_rows()
    result = publication_summary(manifest)
    gazebo = gazebo_probe_summary(manifest)
except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
    st.error(f"Evidence files could not be validated: {exc}")
    st.stop()

st.markdown(f"**Manuscript:** {manifest['paper_title']}")
st.caption(f"Evidence source: `{MANIFEST.relative_to(MANIFEST.parents[2])}` · "
           f"Claim status source: `{CLAIMS.relative_to(CLAIMS.parents[0])}`")

tab_study, tab_audit, tab_claims, tab_gazebo, tab_provenance = st.tabs([
    "Retained Study", "Verified Audit Reproduction", "Claim–Evidence Matrix", "Gazebo Integration", "Provenance & Downloads",
])

with tab_audit:
    render_audit_evidence()

with tab_study:
    st.subheader("Unavoidable-hazard evaluation — retained publication artifact")
    c1, c2, c3 = st.columns(3)
    c1.metric("Generated scenarios", result["scenario_count"])
    c2.metric("Paired seeds per scenario", result["paired_seeds_per_scenario"])
    c3.metric("Improved scenarios", f'{result["improved_scenarios"]}/{result["scenario_count"]}')
    chart_data = pd.DataFrame([
        {"Planner": "State-only exact", "Return infeasibility (%)": 100 * result["baseline_return_infeasible_rate"]},
        {"Planner": "History-conditioned exact", "Return infeasibility (%)": 100 * result["history_return_infeasible_rate"]},
    ]).set_index("Planner")
    st.bar_chart(chart_data, y="Return infeasibility (%)")
    delta = result["scenario_mean_difference"] * 100
    lower, upper = (value * 100 for value in result["scenario_bootstrap_95"])
    st.write(
        f"Scenario-level mean difference (history − state-only): **{delta:.2f} percentage points**. "
        f"95% paired bootstrap interval: **[{lower:.2f}, {upper:.2f}] percentage points**."
    )
    st.info(
        f'{result["nonworse_scenarios"]}/{result["scenario_count"]} scenarios were non-worse '
        "within this synthetic scenario generator. This is NOT universal planner superiority "
        "or a real-world robot reliability estimate."
    )
    st.caption(f'Original retained workflow: https://github.com/panagiotagrosdouli/DynNav/actions/runs/{result["source_workflow_run_id"]}')

with tab_claims:
    st.subheader("Statements supported and unsupported by the repository")
    choice = st.selectbox("Claim status", ["All", "SUPPORTED", "UNSUPPORTED"])
    shown = claim_rows if choice == "All" else [row for row in claim_rows if row["Status"] == choice]
    st.metric("Visible claims", len(shown))
    st.dataframe(pd.DataFrame(shown), hide_index=True, use_container_width=True)
    st.caption("SUPPORTED means only the narrow wording in the matrix is supported.")

with tab_gazebo:
    st.subheader("Action-triggered Gazebo integration probe")
    st.metric("Protocol-valid trials", gazebo["valid_trials"])
    st.dataframe(pd.DataFrame([
        {"Planner": name,
         "Successful navigation actions": count,
         "Observed operational irreversible failures": gazebo["operational_irreversible_failures"].get(name)}
        for name, count in gazebo["navigation_success"].items()
    ]), hide_index=True, use_container_width=True)
    st.warning(gazebo["interpretation"])
    st.caption(f'Original retained workflow: https://github.com/panagiotagrosdouli/DynNav/actions/runs/{gazebo["workflow_run_id"]}')

with tab_provenance:
    st.subheader("Provenance")
    st.write("All values on this page are loaded from checked-in repository files; no trials are run by this page.")
    st.json({
        "manifest": str(MANIFEST.relative_to(MANIFEST.parents[2])),
        "claims": str(CLAIMS.relative_to(CLAIMS.parents[0])),
        "reviewer_measurement_workflow": result["source_workflow_run_id"],
        "gazebo_probe_workflow": gazebo["workflow_run_id"],
        "claim_scope": manifest["claim_scope"],
    })
    st.download_button(
        "Download pinned evidence JSON",
        json.dumps(manifest, indent=2),
        file_name="dynnav_publication_evidence_manifest.json",
        mime="application/json",
    )
    st.download_button(
        "Download claim–evidence CSV",
        pd.DataFrame(claim_rows).to_csv(index=False),
        file_name="dynnav_claim_evidence_matrix.csv",
        mime="text/csv",
    )
