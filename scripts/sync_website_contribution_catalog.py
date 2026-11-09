"""Generate the website contribution catalog from DynNav's canonical registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "configs/contributions/registry.yaml"
EXPERIMENTS_PATH = ROOT / "configs/contributions/experiments.yaml"
DASHBOARD_REGISTRY_PATH = ROOT / "src/dynnav_dashboard/contribution_registry.yaml"
OUTPUT_PATH = ROOT / "website/data/contributions.json"


def _tracked_directory(relative_path: str) -> str | None:
    if not relative_path:
        return None
    directory = ROOT / relative_path
    if directory.is_dir() and any(item.is_file() for item in directory.rglob("*")):
        return relative_path
    return None


def build_catalog() -> list[dict[str, object]]:
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    experiment_data = yaml.safe_load(EXPERIMENTS_PATH.read_text(encoding="utf-8"))
    dashboard_registry = yaml.safe_load(DASHBOARD_REGISTRY_PATH.read_text(encoding="utf-8"))
    experiments = {item["contribution_id"]: item for item in experiment_data["experiments"]}
    renderers = {item["id"]: item["renderer"] for item in dashboard_registry["contributions"]}
    catalog: list[dict[str, object]] = []

    for item in registry["contributions"]:
        contribution_id = item["id"]
        contribution_dir = item["directory"]
        readme = f"{contribution_dir}/README.md"
        if not readme or not (ROOT / readme).is_file():
            raise ValueError(f"{contribution_id} has no existing English README: {readme}")

        renderer_name = renderers.get(contribution_id)
        renderer_file = ROOT / "src/dynnav_dashboard/contributions" / f"{renderer_name}.py" if renderer_name else None
        if renderer_file is None or not renderer_file.is_file():
            raise ValueError(f"{contribution_id} dashboard renderer is missing: {renderer_name}")
        renderer = str(renderer_file.relative_to(ROOT))
        if contribution_id not in experiments:
            raise ValueError(f"{contribution_id} has no registered experiment contract")

        code_dir = _tracked_directory(f"{contribution_dir}/code")
        experiment_runner = experiments[contribution_id]["runner"]
        if not (ROOT / experiment_runner).is_file():
            raise ValueError(f"{contribution_id} experiment runner is missing: {experiment_runner}")
        result_dir = _tracked_directory(f"{contribution_dir}/results")
        tests_dir = _tracked_directory(f"{contribution_dir}/tests")
        test_path = tests_dir or "tests/test_contribution_experiment_suite.py"

        catalog.append(
            {
                "id": contribution_id,
                "title": item["title"],
                "category": item["category"],
                "maturity": item["status"],
                "directory": contribution_dir,
                "readme": readme,
                "source": code_dir,
                "renderer": renderer,
                "tests": test_path,
                "experiment": experiments[contribution_id],
                "existing_results": result_dir,
            }
        )

    expected_ids = [f"C{i:02d}" for i in range(1, 27)]
    actual_ids = [item["id"] for item in catalog]
    if actual_ids != expected_ids:
        raise ValueError(f"Registry must contain C01–C26 in order; found {actual_ids}")
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the committed catalog is stale")
    args = parser.parse_args()
    rendered = json.dumps(build_catalog(), ensure_ascii=False, indent=2) + "\n"

    if args.check:
        if not OUTPUT_PATH.is_file() or OUTPUT_PATH.read_text(encoding="utf-8") != rendered:
            print(f"{OUTPUT_PATH.relative_to(ROOT)} is out of date; run {Path(__file__).relative_to(ROOT)}")
            return 1
        print(f"Verified {len(json.loads(rendered))} registry entries, experiment contracts, and linked repository paths.")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)} with {len(json.loads(rendered))} entries.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, ValueError, yaml.YAMLError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
