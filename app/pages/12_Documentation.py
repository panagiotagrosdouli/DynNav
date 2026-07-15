from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="DynNav Documentation", page_icon="📚", layout="wide")

ROOT = Path(__file__).resolve().parents[2]

DOCUMENTS = {
    "Getting started": ["README.md", "app/README.md"],
    "Architecture": ["docs/ARCHITECTURE.md", "docs/STREAMLIT_APP_AUDIT.md"],
    "Planning": ["docs/PLANNING.md", "docs/algorithms.md"],
    "Risk and safety": ["docs/RISK_AWARE_PLANNING.md", "docs/SAFETY.md"],
    "Experiments": ["docs/EXPERIMENTS.md", "docs/REPRODUCIBILITY.md"],
    "ROS2 and Nav2": ["docs/ROS2_NAV2.md", "docs/ROS2_INTEGRATION.md"],
    "Limitations": ["docs/LIMITATIONS.md", "README.md"],
}


def safe_document(path_text: str) -> tuple[Path | None, str | None]:
    candidate = (ROOT / path_text).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None, "Document path escapes the repository root."
    if candidate.suffix.lower() != ".md":
        return None, "Only canonical Markdown files are supported."
    if not candidate.is_file():
        return None, "Document is not currently available in this checkout."
    return candidate, None


st.title("Documentation")
st.caption("Read curated repository documentation without rendering arbitrary uploaded HTML.")
st.info(
    "Synthetic interactive research environment. Documentation does not establish physical-robot safety, "
    "ROS2 validation, deployment readiness, or formal guarantees."
)

category = st.selectbox("Category", list(DOCUMENTS), key="docs_category")
available = []
missing = []
for relative_path in DOCUMENTS[category]:
    path, error = safe_document(relative_path)
    if path is not None:
        available.append(relative_path)
    else:
        missing.append((relative_path, error))

if not available:
    st.warning("No canonical document is currently available for this category.")
else:
    selected = st.selectbox("Document", available, key="docs_document")
    path, error = safe_document(selected)
    if error or path is None:
        st.error(error or "Unable to open the document.")
    else:
        text = path.read_text(encoding="utf-8", errors="replace")
        st.caption(f"Source: `{selected}` · {len(text.splitlines())} lines")
        st.markdown(text, unsafe_allow_html=False)
        st.download_button(
            "Download Markdown",
            data=text,
            file_name=path.name,
            mime="text/markdown",
            key="docs_download",
        )

if missing:
    with st.expander("Unavailable canonical documents"):
        for relative_path, reason in missing:
            st.write(f"`{relative_path}` — {reason}")

st.subheader("Application page map")
st.dataframe(
    [
        {"Page": "Robot Lab", "Purpose": "Closed-loop playback, events, and run export"},
        {"Page": "Scenario Builder", "Purpose": "Configure deterministic synthetic environments"},
        {"Page": "Planner Arena", "Purpose": "Compare available planners on the same world"},
        {"Page": "Belief & Mapping Lab", "Purpose": "Inspect occupancy belief and uncertainty"},
        {"Page": "Risk & Safety Lab", "Purpose": "Compose risk layers and supervisor thresholds"},
        {"Page": "Dynamic Obstacles", "Purpose": "Inspect predictions and route conflicts"},
        {"Page": "Multi-Robot Lab", "Purpose": "Explore synthetic fleet communication and conflicts"},
        {"Page": "Contribution Explorer", "Purpose": "Run C01–C26 interactive renderers"},
        {"Page": "Experiment Studio", "Purpose": "Run deterministic comparisons and sweeps"},
        {"Page": "Results & Reports", "Purpose": "Replay and export reproducible evidence"},
        {"Page": "System Status", "Purpose": "Inspect runtime and optional capabilities"},
    ],
    hide_index=True,
    use_container_width=True,
)
