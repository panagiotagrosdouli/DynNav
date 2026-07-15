#!/usr/bin/env python3
"""Discover every documentation-like file and generate inventory artifacts."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

from markdown_audit_core import (
    build_inventory,
    write_csv,
    write_documentation_map,
    write_inventory_markdown,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("results/manifests/markdown_inventory.json"))
    args = parser.parse_args()

    root = args.root.resolve()
    records, findings, graph, commands = build_inventory(root)
    write_json(root / args.output, [asdict(record) for record in records])
    write_csv(root / "results/manifests/markdown_inventory.csv", records)
    write_inventory_markdown(root / "docs/MARKDOWN_INVENTORY.md", records, findings)
    write_json(root / "results/manifests/markdown_link_graph.json", graph)
    write_json(root / "results/manifests/documented_commands.json", commands)
    write_documentation_map(root / "docs/DOCUMENTATION_MAP.md", records, graph)

    errors = [item for item in findings if item.severity == "error"]
    print(f"Discovered {len(records)} documentation-like files")
    print(f"Validation errors: {len(errors)}")
    for finding in findings:
        print(f"{finding.severity.upper()} {finding.file}:{finding.line} {finding.kind}: {finding.target} — {finding.message}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
