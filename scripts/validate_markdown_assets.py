#!/usr/bin/env python3
"""Validate local image and media references in documentation-like files."""

from pathlib import Path
import argparse
from markdown_audit_core import build_inventory, IMAGE_SUFFIXES


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    records, findings, _, _ = build_inventory(args.root.resolve())
    asset_targets = {asset for record in records for asset in record.images_referenced}
    failures = [f for f in findings if f.kind == "missing-target" and Path(f.target.partition("#")[0]).suffix.lower() in IMAGE_SUFFIXES]
    print(f"Referenced assets: {len(asset_targets)}")
    for item in failures:
        print(f"ERROR {item.file}:{item.line} missing asset: {item.target}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
