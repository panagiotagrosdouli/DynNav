from __future__ import annotations

import ast
from pathlib import Path

import pytest

# The core CI intentionally installs only ``.[dev]``. Keep this dashboard-only
# smoke module collectable there, while executing it fully in the dedicated
# Streamlit workflow and in local ``.[dashboard,dev]`` environments.
pytest.importorskip("streamlit", reason="dashboard optional dependencies are not installed")
pytest.importorskip("plotly", reason="dashboard optional dependencies are not installed")
pytest.importorskip("networkx", reason="dashboard optional dependencies are not installed")

from dynnav_dashboard.contributions import RENDERERS
from dynnav_dashboard.registry import load_contribution_registry


ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    ROOT / "app/dashboard.py",
    *sorted((ROOT / "app/pages").glob("*.py")),
]


def test_all_streamlit_pages_parse() -> None:
    assert len(PAGES) >= 13
    for page in PAGES:
        ast.parse(page.read_text(encoding="utf-8"), filename=str(page))


def test_contribution_registry_matches_renderers() -> None:
    expected = [f"C{i:02d}" for i in range(1, 27)]
    registry = load_contribution_registry()
    assert [item.id for item in registry] == expected
    assert sorted(RENDERERS) == expected
    assert all(callable(RENDERERS[item_id]) for item_id in expected)


def test_dashboard_docker_entrypoint() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert '"streamlit", "run", "app/dashboard.py"' in dockerfile
    assert '"--server.address", "0.0.0.0"' in dockerfile
    assert "EXPOSE 8501" in dockerfile
    assert "_stcore/health" in dockerfile


def test_responsible_claim_notice_is_present() -> None:
    notice_terms = ("Synthetic", "ROS2", "Gazebo", "formal")
    sources = "\n".join(page.read_text(encoding="utf-8") for page in PAGES)
    for term in notice_terms:
        assert term in sources
