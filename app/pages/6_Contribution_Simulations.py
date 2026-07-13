"""
DynNav Dashboard — Contribution Simulations Page
================================================

Interactive mini-simulations for each of the 26 DynNav research
contributions. Pick a contribution from the dropdown; the page renders its
explanation, controls, plots, metrics and an interpretation block.

All simulations are synthetic and deterministic given a seed. They use only
``streamlit``, ``numpy``, ``pandas``, ``plotly`` and ``networkx``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st  # noqa: E402

from dynnav_dashboard.config import (  # noqa: E402
    APP_ICON, APP_TITLE, COLORS, RESEARCH_MODULES,
)
from dynnav_dashboard.contributions import RENDERERS  # noqa: E402


st.set_page_config(
    page_title=f"{APP_TITLE} — Contribution Simulations",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Build code → metadata index from config.RESEARCH_MODULES
# ---------------------------------------------------------------------------

def _code_label(m) -> str:
    return f"C{m.code} — {m.title}"


CODE_INDEX: dict[str, object] = {f"C{m.code}": m for m in RESEARCH_MODULES}
ORDERED_CODES: list[str] = list(CODE_INDEX.keys())


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div style='margin-bottom:1.2rem;'>
        <div style='font-size:0.78rem;letter-spacing:0.14em;color:{COLORS["text_muted"]};
                    text-transform:uppercase;font-weight:600;'>
            DynNav Research Dashboard
        </div>
        <h1 style='font-size:2.0rem;font-weight:700;color:{COLORS["text"]};
                    margin:0.25rem 0 0.4rem 0;'>
            Contribution Simulations
        </h1>
        <p style='font-size:1.0rem;color:{COLORS["text"]};opacity:0.85;
                   max-width:55rem;line-height:1.55;'>
            Each of the 26 DynNav contributions ships with its own interactive
            mini-simulation. Select a contribution below to see a short
            research explanation, adjustable controls, a simulation output,
            a metrics panel and an interpretation of the result. All data is
            synthetic and deterministic given a seed — no ROS, no GPU and
            no external services are involved.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        f"<div style='font-size:0.78rem;letter-spacing:0.14em;"
        f"color:{COLORS['text_muted']};text-transform:uppercase;font-weight:600;'>"
        f"About this page</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Each simulation is a self-contained module under "
        "`src/dynnav_dashboard/contributions/`. They share theming and "
        "small grid / A* helpers but are otherwise independent — you can "
        "lift any one into your own dashboard."
    )
    st.divider()
    st.markdown(
        f"<div style='font-size:0.78rem;letter-spacing:0.14em;"
        f"color:{COLORS['text_muted']};text-transform:uppercase;font-weight:600;'>"
        f"Category coverage</div>",
        unsafe_allow_html=True,
    )
    cats: dict[str, int] = {}
    for m in RESEARCH_MODULES:
        cats[m.category] = cats.get(m.category, 0) + 1
    cat_rows = "".join(
        f"<div style='display:flex;justify-content:space-between;"
        f"font-size:0.85rem;padding:2px 0;'>"
        f"<span style='color:{COLORS['text']};opacity:0.9'>{c}</span>"
        f"<span style='color:{COLORS['text_muted']}'>{n}</span></div>"
        for c, n in sorted(cats.items(), key=lambda kv: -kv[1])
    )
    st.markdown(cat_rows, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Selector
# ---------------------------------------------------------------------------

col_sel, col_meta = st.columns([1.0, 2.0], gap="large")

with col_sel:
    selected_code = st.selectbox(
        "Select a contribution",
        ORDERED_CODES,
        index=0,
        format_func=lambda code: _code_label(CODE_INDEX[code]),
        key="contrib_select",
    )

selected = CODE_INDEX[selected_code]

with col_meta:
    st.markdown(
        f"""
        <div style='background:{COLORS["surface"]};border:1px solid rgba(255,255,255,0.06);
                    border-radius:10px;padding:0.85rem 1.1rem;'>
            <div style='display:flex;gap:0.75rem;align-items:center;
                        margin-bottom:0.35rem;'>
                <span style='background:{COLORS["primary"]};color:white;
                              font-size:0.72rem;letter-spacing:0.08em;
                              padding:2px 8px;border-radius:4px;
                              text-transform:uppercase;font-weight:700;'>
                    {selected_code}
                </span>
                <span style='color:{COLORS["text_muted"]};font-size:0.78rem;
                              letter-spacing:0.12em;text-transform:uppercase;'>
                    {selected.category}
                </span>
            </div>
            <div style='font-size:1.05rem;font-weight:600;color:{COLORS["text"]};
                        margin-bottom:0.2rem;'>{selected.title}</div>
            <div style='font-size:0.9rem;color:{COLORS["text"]};opacity:0.85;'>
                {selected.one_liner}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")


# ---------------------------------------------------------------------------
# Dispatch to the selected contribution's renderer
# ---------------------------------------------------------------------------

renderer = RENDERERS.get(selected_code)
if renderer is None:
    st.error(
        f"No simulation registered for {selected_code}. "
        "This should not happen — please report it via the repository issues."
    )
else:
    try:
        renderer(st)
    except Exception as exc:  # pragma: no cover - defensive UI guard
        st.error(
            "An unexpected error occurred while rendering this simulation. "
            "Try a different seed or reload the page."
        )
        with st.expander("Technical details"):
            st.exception(exc)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.write("")
st.markdown(
    f"<div style='color:{COLORS['text_muted']};font-size:0.8rem;text-align:center;"
    f"padding-top:0.6rem;border-top:1px solid rgba(255,255,255,0.06);'>"
    f"All simulations use synthetic data only. Deterministic given each "
    f"contribution's seed slider.</div>",
    unsafe_allow_html=True,
)
