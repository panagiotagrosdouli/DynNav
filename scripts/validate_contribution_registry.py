#!/usr/bin/env python3
"""Validate the canonical DynNav contribution registry without importing Streamlit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

ALLOWED_STATUS = {
    "Implemented", "Research Prototype", "Experimental", "Synthetic Validation",
    "Dataset Validation", "Simulation Validation", "Documentation Concept", "Planned",
    "Missing Implementation", "Deprecated", "Duplicate", "ROS 2 Validation Pending",
    "Hardware Validation Required",
}


def load_registry(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("contributions"), list):
        raise ValueError("registry must contain a contributions list")
    return data


def validate(root: Path, registry_path: Path) -> dict[str, Any]:
    entries = load_registry(registry_path)["contributions"]
    errors: list[str] = []
    warnings: list[str] = []
    ids: set[str] = set()
    slugs: set[str] = set()

    for entry in entries:
        cid = str(entry.get("id", ""))
        slug = str(entry.get("slug", ""))
        if cid in ids:
            errors.append(f"duplicate id: {cid}")
        if slug in slugs:
            errors.append(f"duplicate slug: {slug}")
        ids.add(cid)
        slugs.add(slug)
        if entry.get("status") not in ALLOWED_STATUS:
            errors.append(f"{cid}: invalid status {entry.get('status')!r}")
        directory = root / str(entry.get("directory", ""))
        if not directory.is_dir():
            errors.append(f"{cid}: missing directory {directory.relative_to(root)}")
        for target in entry.get("integrates_with", []):
            if target == cid:
                errors.append(f"{cid}: self dependency")

    expected = {f"C{i:02d}" for i in range(1, 27)}
    if ids != expected:
        errors.append(f"registry IDs differ from C01-C26: missing={sorted(expected-ids)}, extra={sorted(ids-expected)}")
    for entry in entries:
        for target in entry.get("integrates_with", []):
            if target not in ids:
                errors.append(f"{entry['id']}: unknown dependency {target}")

    return {
        "schema_version": 1,
        "registry": str(registry_path.relative_to(root)),
        "contribution_count": len(entries),
        "ids": sorted(ids),
        "errors": errors,
        "warnings": warnings,
        "status": "passed" if not errors else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--registry", type=Path, default=Path("configs/contributions/registry.yaml"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    report = validate(root, root / args.registry)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        destination = root / args.output
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
