#!/usr/bin/env python3
"""Classify documented commands and fail on invalid executable input paths."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

import markdown_audit_core
from markdown_audit_runtime import install_document_discovery_filter

INPUT_PATH_FLAGS = {"--file", "--config", "--root", "--inventory", "--input"}
_ORIGINAL_SHLEX_SPLIT = shlex.split


def _safe_inventory_split(command: str, comments: bool = False, posix: bool = True) -> list[str]:
    try:
        return _ORIGINAL_SHLEX_SPLIT(command, comments=comments, posix=posix)
    except ValueError:
        stripped = command.strip()
        return [stripped] if stripped else []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()

    install_document_discovery_filter()
    markdown_audit_core.shlex.split = _safe_inventory_split
    _, _, _, commands = markdown_audit_core.build_inventory(root)

    failures: list[str] = []
    for row in commands:
        command = str(row["command"])
        try:
            parts = _ORIGINAL_SHLEX_SPLIT(command, comments=True)
        except ValueError as exc:
            failures.append(f"{row['document']}: malformed command: {exc}: {command}")
            continue
        for index, token in enumerate(parts[:-1]):
            if token not in INPUT_PATH_FLAGS:
                continue
            candidate = parts[index + 1]
            if (
                any(char in candidate for char in "$*{}<>")
                or candidate.startswith("~")
                or candidate.startswith("results/")
                or Path(candidate).is_absolute()
            ):
                continue
            path = (root / candidate).resolve()
            if not path.exists():
                failures.append(f"{row['document']}: missing command input {candidate}: {command}")
    for failure in failures:
        print(f"ERROR {failure}")
    print(f"Documented commands classified: {len(commands)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
