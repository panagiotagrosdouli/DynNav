#!/usr/bin/env python3
"""Generate deterministic contribution inventory, dependency, and maturity artifacts.

The canonical source is ``configs/contributions/registry.yaml``. Generated files are
intentionally plain Markdown/JSON/CSV so they remain reviewable without the dashboard.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "configs/contributions/registry.yaml"


def load_registry(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    contributions = data.get("contributions", [])
    if not isinstance(contributions, list) or not contributions:
        raise ValueError("registry must contain a non-empty contributions list")
    return data


def enriched_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in data["contributions"]:
        directory = ROOT / item["directory"]
        renderer = ROOT / "src/dynnav_dashboard/contributions" / f"{item['id'].lower()}_{item['slug']}.py"
        readme = directory / "README.md"
        readme_gr = directory / "README_GR.md"
        rows.append(
            {
                **item,
                "readme": str(readme.relative_to(ROOT)) if readme.exists() else None,
                "readme_gr": str(readme_gr.relative_to(ROOT)) if readme_gr.exists() else None,
                "renderer": str(renderer.relative_to(ROOT)) if renderer.exists() else None,
                "directory_exists": directory.is_dir(),
                "blockers": [],
                "validation_status": "registry_validated" if directory.is_dir() else "missing_directory",
            }
        )
    return rows


def write_inventory(rows: list[dict[str, Any]]) -> None:
    out = ROOT / "results/manifests"
    out.mkdir(parents=True, exist_ok=True)
    (out / "contribution_inventory.json").write_text(
        json.dumps({"schema_version": 1, "contributions": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    fields = [
        "id", "slug", "title", "category", "status", "directory", "readme",
        "readme_gr", "renderer", "directory_exists", "validation_status",
    ]
    with (out / "contribution_inventory.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def write_dependency_graph(rows: list[dict[str, Any]]) -> None:
    edges = [
        {"source": row["id"], "target": target}
        for row in rows
        for target in row.get("integrates_with", [])
    ]
    manifest = ROOT / "results/manifests/contribution_dependency_graph.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps({"schema_version": 1, "nodes": [r["id"] for r in rows], "edges": edges}, indent=2) + "\n",
        encoding="utf-8",
    )

    by_id = {row["id"]: row for row in rows}
    lines = [
        "# DynNav Contribution Dependency Graph",
        "",
        "> Generated from `configs/contributions/registry.yaml`. Relationships indicate intended integration, not experimental validation.",
        "",
        "```mermaid",
        "graph LR",
    ]
    for row in rows:
        safe_title = row["title"].replace('"', "'")
        lines.append(f'  {row["id"]}["{row["id"]} — {safe_title}"]')
    for edge in edges:
        lines.append(f"  {edge['source']} --> {edge['target']}")
    lines += ["```", "", "## Adjacency list", ""]
    for row in rows:
        targets = row.get("integrates_with", [])
        rendered = ", ".join(f"[{target}](../{by_id[target]['directory']}/README.md)" for target in targets) or "None declared"
        lines.append(f"- **{row['id']} — {row['title']}:** {rendered}")
    (ROOT / "docs/CONTRIBUTION_DEPENDENCY_GRAPH.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_index_and_maturity(rows: list[dict[str, Any]]) -> None:
    index = [
        "# DynNav Contribution Index",
        "",
        "> Generated from the canonical registry. Maturity describes currently claimed evidence, not future ambition.",
        "",
        "| ID | Contribution | Category | Maturity | README | Greek | Renderer |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        readme = f"[English](../{row['readme']})" if row["readme"] else "Missing"
        greek = f"[Greek](../{row['readme_gr']})" if row["readme_gr"] else "—"
        renderer = f"[`{Path(row['renderer']).name}`](../{row['renderer']})" if row["renderer"] else "Not discovered"
        index.append(f"| {row['id']} | {row['title']} | `{row['category']}` | {row['status']} | {readme} | {greek} | {renderer} |")
    (ROOT / "docs/CONTRIBUTION_INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")

    counts = Counter(row["status"] for row in rows)
    maturity = [
        "# DynNav Contribution Maturity Matrix",
        "",
        "> Generated from `configs/contributions/registry.yaml`. A passing registry check does not elevate scientific maturity.",
        "",
        "## Distribution",
        "",
        "| Maturity | Count |",
        "|---|---:|",
    ]
    maturity.extend(f"| {status} | {count} |" for status, count in sorted(counts.items()))
    maturity += ["", "## Contribution-level matrix", "", "| ID | Title | Maturity | Evidence boundary |", "|---|---|---|---|"]
    for row in rows:
        boundary = "Synthetic/controlled evidence only" if row["status"] != "Documentation Concept" else "Conceptual documentation; no validated implementation claim"
        maturity.append(f"| {row['id']} | {row['title']} | {row['status']} | {boundary} |")
    (ROOT / "docs/CONTRIBUTION_MATURITY_MATRIX.md").write_text("\n".join(maturity) + "\n", encoding="utf-8")


def write_validation(rows: list[dict[str, Any]]) -> None:
    missing = [row["id"] for row in rows if not row["directory_exists"]]
    payload = {
        "schema_version": 1,
        "status": "passed" if not missing and len(rows) == 26 else "failed",
        "registered_count": len(rows),
        "expected_ids": [f"C{i:02d}" for i in range(1, 27)],
        "missing_directories": missing,
        "claim_boundary": "Registry and path validation only; no dataset, ROS 2, hardware, formal, or trained-neural claim.",
    }
    path = ROOT / "results/manifests/contribution_validation.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args()
    data = load_registry(args.registry)
    rows = enriched_rows(data)
    write_inventory(rows)
    write_dependency_graph(rows)
    write_index_and_maturity(rows)
    write_validation(rows)
    print(f"Generated programme artifacts for {len(rows)} contributions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
