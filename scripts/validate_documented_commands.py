#!/usr/bin/env python3
"""Classify documented commands and fail on obviously invalid executable paths."""

from pathlib import Path
import argparse
import shlex
from markdown_audit_core import build_inventory

PATH_FLAGS = {"-f", "--file", "--config", "--root", "--output", "--inventory", "--out-dir"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    _, _, _, commands = build_inventory(root)
    failures: list[str] = []
    for row in commands:
        command = str(row["command"])
        try:
            parts = shlex.split(command, comments=True)
        except ValueError as exc:
            failures.append(f"{row['document']}: malformed command: {exc}: {command}")
            continue
        for index, token in enumerate(parts[:-1]):
            if token not in PATH_FLAGS:
                continue
            candidate = parts[index + 1]
            if any(char in candidate for char in "$*{}<>"):
                continue
            path = (root / candidate).resolve()
            if not path.exists():
                failures.append(f"{row['document']}: missing command path {candidate}: {command}")
    for failure in failures:
        print(f"ERROR {failure}")
    print(f"Documented commands classified: {len(commands)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
