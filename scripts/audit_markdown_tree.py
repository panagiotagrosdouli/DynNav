#!/usr/bin/env python3
"""Discover every documentation-like file and generate inventory artifacts."""

from __future__ import annotations

import argparse
import shlex
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

import markdown_audit_core
from markdown_audit_runtime import install_document_discovery_filter

_ORIGINAL_SHLEX_SPLIT = shlex.split


def _safe_shlex_split(command: str, comments: bool = False, posix: bool = True) -> list[str]:
    """Return a conservative token when a documented command is malformed.

    Inventory generation must complete so it can emit its structured findings and
    artifacts. Command syntax remains a required check in
    ``validate_documented_commands.py``; this fallback does not mark malformed
    commands as valid.
    """

    try:
        return _ORIGINAL_SHLEX_SPLIT(command, comments=comments, posix=posix)
    except ValueError:
        stripped = command.strip()
        return [stripped] if stripped else []


def _write_encoded_documentation_map(
    path: Path,
    records: list[markdown_audit_core.DocumentRecord],
    graph: dict[str, object],
) -> None:
    """Write deterministic repository links safe for spaces and punctuation."""

    path.parent.mkdir(parents=True, exist_ok=True)
    canonical = [
        record
        for record in records
        if record.filename.lower().startswith("readme")
        or record.path.startswith("docs/")
    ]
    lines = [
        "# Documentation Map",
        "",
        "> Generated from the repository-wide documentation inventory.",
        "",
        "## Canonical and index documents",
        "",
    ]
    for record in canonical:
        target = "../" + quote(record.path, safe="/#:.?=&%_-")
        lines.append(
            f"- [`{record.path}`]({target}) — {record.current_purpose}; "
            f"maturity: **{record.apparent_maturity}**"
        )
    lines.extend(["", "## Orphan documents", ""])
    orphans = graph.get("orphans", [])
    if isinstance(orphans, list):
        lines.extend(f"- `{orphan}`" for orphan in orphans)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/manifests/markdown_inventory.json"),
    )
    args = parser.parse_args()

    install_document_discovery_filter()
    markdown_audit_core.shlex.split = _safe_shlex_split

    root = args.root.resolve()
    records, findings, graph, commands = markdown_audit_core.build_inventory(root)
    markdown_audit_core.write_json(
        root / args.output,
        [asdict(record) for record in records],
    )
    markdown_audit_core.write_csv(
        root / "results/manifests/markdown_inventory.csv",
        records,
    )
    markdown_audit_core.write_inventory_markdown(
        root / "docs/MARKDOWN_INVENTORY.md",
        records,
        findings,
    )
    markdown_audit_core.write_json(
        root / "results/manifests/markdown_link_graph.json",
        graph,
    )
    markdown_audit_core.write_json(
        root / "results/manifests/documented_commands.json",
        commands,
    )
    _write_encoded_documentation_map(
        root / "docs/DOCUMENTATION_MAP.md",
        records,
        graph,
    )

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
