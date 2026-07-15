#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
from pathlib import Path

from dynnav_dashboard.contributions import RENDERERS
from dynnav_dashboard.registry import load_contribution_registry


REQUIRED_PAGES = {
    "app/dashboard.py",
    "app/pages/01_Home.py",
    "app/pages/02_Robot_Lab.py",
    "app/pages/03_Scenario_Builder.py",
    "app/pages/04_Planner_Arena.py",
    "app/pages/05_Belief_Mapping_Lab.py",
    "app/pages/06_Risk_Safety_Lab.py",
    "app/pages/07_Dynamic_Obstacles.py",
    "app/pages/08_Multi_Robot_Lab.py",
    "app/pages/09_Contribution_Explorer.py",
    "app/pages/13_System_Status.py",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[str] = []

    for path in sorted(REQUIRED_PAGES):
        if not (root / path).is_file():
            failures.append(f"missing page: {path}")

    registry = load_contribution_registry()
    expected_ids = [f"C{i:02d}" for i in range(1, 27)]
    if [item.id for item in registry] != expected_ids:
        failures.append("contribution registry is incomplete or out of order")
    if sorted(RENDERERS) != expected_ids:
        failures.append("renderer registry does not contain exactly C01-C26")

    for item in registry:
        try:
            importlib.import_module(f"dynnav_dashboard.contributions.{item.renderer}")
        except Exception as exc:
            failures.append(f"{item.id} renderer import failed: {exc}")

    report = {
        "pages_checked": len(REQUIRED_PAGES),
        "contributions_checked": len(registry),
        "renderers_registered": len(RENDERERS),
        "failures": failures,
    }
    report_path = root / "results/manifests/streamlit_validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for failure in failures:
        print(f"ERROR {failure}")
    print(json.dumps(report, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
