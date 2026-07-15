#!/usr/bin/env python3
"""Discover every documentation-like file and generate inventory artifacts."""

from __future__ import annotations

import argparse
import re
import shlex
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

import markdown_audit_core
from markdown_audit_runtime import install_document_discovery_filter

_ORIGINAL_SHLEX_SPLIT = shlex.split
_LINK_DESTINATION = re.compile(r"(\]\()([^\n)]+)(\))")


def _safe_shlex_split(command: str, comments: bool = False, posix: bool = True) -> list[str]:
    """Return a conservative token when a documented command is malformed."""

    try:
        return _ORIGINAL_SHLEX_SPLIT(command, comments=comments, posix=posix)
    except ValueError:
        stripped = command.strip()
        return [stripped] if stripped else []


def _encode_generated_local_links(path: Path) -> None:
    """Encode spaces, parentheses, and Unicode in generated local destinations."""

    text = path.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        target = match.group(2)
        if "://" in target or target.startswith(("mailto:", "tel:", "data:")):
            return match.group(0)
        encoded = quote(target, safe="/#:.?=&%_-")
        return f"{match.group(1)}{encoded}{match.group(3)}"

    path.write_text(_LINK_DESTINATION.sub(replace, text), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("results/manifests/markdown_inventory.json"))
    args = parser.parse_args()

    install_document_discovery_filter()
    markdown_audit_core.shlex.split = _safe_shlex_split

    root = args.root.resolve()
    records, findings, graph, commands = markdown_audit_core.build_inventory(root)
    markdown_audit_core.write_json(root / args.output, [asdict(record) for record in records])
    markdown_audit_core.write_csv(root / "results/manifests/markdown_inventory.csv", records)
    markdown_audit_core.write_inventory_markdown(root / "docs/MARKDOWN_INVENTORY.md", records, findings)
    markdown_audit_core.write_json(root / "results/manifests/markdown_link_graph.json", graph)
    markdown_audit_core.write_json(root / "results/manifests/documented_commands.json", commands)
    documentation_map = root / "docs/DOCUMENTATION_MAP.md"
    markdown_audit_core.write_documentation_map(documentation_map, records, graph)
    _encode_generated_local_links(documentation_map)

    errors = [item for item in findings if item.severity == "error"]
    print(f"Discovered {len(records)} documentation-like files")
    print(f"Validation errors: {len(errors)}")
    for finding in findings:
        print(
            f"{finding.severity.upper()} {finding.file}:{finding.line} "
            f"{finding.kind}: {finding.target} — {finding.message}"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
