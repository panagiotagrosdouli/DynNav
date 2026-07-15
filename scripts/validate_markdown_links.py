#!/usr/bin/env python3
"""Validate local links and heading anchors in all documentation-like files."""

from __future__ import annotations

import argparse
from pathlib import Path

import markdown_audit_core
from markdown_audit_runtime import install_document_discovery_filter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    install_document_discovery_filter()
    _, findings, _, _ = markdown_audit_core.build_inventory(args.root.resolve())
    failures = [f for f in findings if f.kind in {"missing-target", "missing-anchor", "outside-repository"}]
    for item in failures:
        print(f"ERROR {item.file}:{item.line} {item.kind}: {item.target} — {item.message}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
