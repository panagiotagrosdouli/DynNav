"""Streamlit deployment shim for the repository's ``src`` layout.

Streamlit Community Cloud executes ``app/dashboard.py`` with the ``app``
directory on ``sys.path``.  In deployments where the repository itself has
not yet been installed as a package, this shim exposes the canonical
``src/dynnav_dashboard`` package without duplicating implementation code.
"""

from __future__ import annotations

from pathlib import Path

_SOURCE_PACKAGE = Path(__file__).resolve().parents[2] / "src" / "dynnav_dashboard"
if not _SOURCE_PACKAGE.is_dir():
    raise ImportError(f"DynNav dashboard source package not found: {_SOURCE_PACKAGE}")

# Make imports such as ``dynnav_dashboard.config`` resolve to the canonical
# implementation under ``src/dynnav_dashboard``.
__path__ = [str(_SOURCE_PACKAGE)]
