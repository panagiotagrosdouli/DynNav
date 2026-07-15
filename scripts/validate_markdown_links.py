#!/usr/bin/env python3
"""Validate local links and heading anchors in all documentation-like files."""

from pathlib import Path
import argparse
from markdown_audit_core import build_inventory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    _, findings, _, _ = build_inventory(args.root.resolve())
    failures = [f for f in findings if f.kind in {"missing-target", "missing-anchor", "outside-repository"}]
    for item in failures:
        print(f"ERROR {item.file}:{item.line} {item.kind}: {item.target} — {item.message}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
