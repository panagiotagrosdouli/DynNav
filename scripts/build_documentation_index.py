#!/usr/bin/env python3
"""Build the generated documentation map from a Markdown inventory JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from markdown_audit_core import DocumentRecord, write_documentation_map


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    root = args.root.resolve()
    raw = json.loads((root / args.inventory).read_text(encoding="utf-8"))
    records = [DocumentRecord(**item) for item in raw]
    graph_path = root / "results/manifests/markdown_link_graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8")) if graph_path.exists() else {"orphans": []}
    write_documentation_map(root / "docs/DOCUMENTATION_MAP.md", records, graph)
    print(f"Documentation map generated from {len(records)} inventory records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
