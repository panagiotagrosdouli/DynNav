"""Shared retained-evidence presentation used by Results and Publication pages."""

from __future__ import annotations

import json

import streamlit as st

from dynnav_dashboard.audit_evidence import load_audit


def render_audit_evidence() -> None:
    st.subheader("Verified research-audit reproduction")
    try:
        packet = load_audit()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"Retained audit could not be verified: {exc}")
        return
    st.success("Checksums and complete paired raw-trial denominators verified.")
    st.caption("Integrity is relative to the committed index; it is not independent dataset authentication.")
    st.write(packet["scope"])
    st.json({
        "audit_code_checkpoint": packet["code_revision"],
        "index_sha256": packet["index_sha256"],
        "raw_trial_rows": packet["trial_rows"],
        "protocol": packet["protocol"],
        "provenance_boundary": packet["provenance_boundary"],
    })
    aggregate = packet["summary"]["aggregate"]
    left, right = st.columns(2)
    left.metric("State-only exact return infeasibility",
                f"{aggregate['state_only_exact']['mean_return_infeasible_rate']:.5f}")
    right.metric("History exact return infeasibility",
                 f"{aggregate['history_exact']['mean_return_infeasible_rate']:.5f}")
    effect = packet["effect"]
    st.write(
        f"History minus state-only: {effect['estimate']:.5f}; "
        f"95% scenario bootstrap interval [{effect['lower']:.5f}, {effect['upper']:.5f}] "
        f"over {effect['sample_size']} paired scenarios."
    )
    st.warning(
        "Controlled synthetic generator with independent closure events. No arbitrary-map generalization, "
        "physical-robot benefit, certified safety, or universal advantage over hard-return constraints is established. "
        "Historical publication timings are separate runner-specific artifacts."
    )
    for name, data in packet["verified_files"].items():
        st.download_button(f"Download verified {name}", data, file_name=name.replace("/", "_"))
    st.download_button("Download audit uncertainty JSON", json.dumps(effect, indent=2), "audit_uncertainty.json")
