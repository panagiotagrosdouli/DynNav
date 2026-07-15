#!/usr/bin/env python3
"""Recursively audit repository Markdown files and local references."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

IGNORED_PARTS = {".git", ".next", "node_modules", ".venv", "venv", "__pycache__"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_REFERENCE = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
HTML_TAG = re.compile(r"<[^>]+>")
UNSUPPORTED_CLAIMS = {
    "formally verified": "requires a formal proof or verification artifact",
    "formal safety guarantee": "requires a formal proof or safety certificate",
    "validated on turtlebot": "requires traceable robot logs and configuration",
    "real robot validation": "requires traceable hardware evidence",
    "state-of-the-art": "requires a fair benchmark and cited comparison",
}


@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    kind: str
    target: str
    message: str


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.parts)
    )


def github_slug(text: str) -> str:
    text = html.unescape(HTML_TAG.sub("", text)).strip().lower()
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING.match(line)
        if not match:
            continue
        base = github_slug(match.group(2))
        if not base:
            continue
        index = counts.get(base, 0)
        counts[base] = index + 1
        found.add(base if index == 0 else f"{base}-{index}")
    return found


def references(line: str) -> list[str]:
    refs = [match.group(1).strip() for match in MARKDOWN_LINK.finditer(line)]
    refs.extend(match.group(1).strip() for match in HTML_REFERENCE.finditer(line))
    return refs


def is_external(target: str) -> bool:
    parsed = urlparse(target)
    return parsed.scheme in {"http", "https", "mailto", "tel", "data"} or target.startswith("//")


def audit(root: Path) -> tuple[list[Path], list[Finding], list[Finding]]:
    files = markdown_files(root)
    errors: list[Finding] = []
    warnings: list[Finding] = []
    anchor_cache: dict[Path, set[str]] = {}

    for path in files:
        relative = path.relative_to(root)
        lines = path.read_text(encoding="utf-8").splitlines()
        in_fence = False
        for number, line in enumerate(lines, start=1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            lower = line.lower()
            for phrase, reason in UNSUPPORTED_CLAIMS.items():
                if phrase in lower:
                    warnings.append(Finding(str(relative), number, "claim-review", phrase, reason))

            for raw_target in references(line):
                target = raw_target.strip("<>")
                if not target or is_external(target):
                    continue
                if target.startswith("#"):
                    destination = path
                    fragment = unquote(target[1:])
                else:
                    clean, separator, fragment = target.partition("#")
                    clean = unquote(clean.split("?", 1)[0])
                    destination = (path.parent / clean).resolve() if clean else path
                    try:
                        destination.relative_to(root.resolve())
                    except ValueError:
                        errors.append(Finding(str(relative), number, "outside-repository", target, "reference escapes repository root"))
                        continue
                    if clean and not destination.exists():
                        errors.append(Finding(str(relative), number, "missing-target", target, "local path does not exist"))
                        continue

                if fragment and destination.is_file() and destination.suffix.lower() == ".md":
                    anchor_set = anchor_cache.setdefault(destination, anchors(destination))
                    normalized = github_slug(unquote(fragment))
                    if normalized not in anchor_set:
                        errors.append(Finding(str(relative), number, "missing-anchor", target, f"anchor '{normalized}' does not exist"))

    return files, errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    files, errors, warnings = audit(root)
    print(f"Markdown files: {len(files)}")
    for path in files:
        print(path.relative_to(root))

    for finding in warnings:
        print(f"WARNING {finding.file}:{finding.line}: {finding.kind}: {finding.target} ({finding.message})")
    for finding in errors:
        print(f"ERROR {finding.file}:{finding.line}: {finding.kind}: {finding.target} ({finding.message})")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(
                {
                    "markdown_files": [str(path.relative_to(root)) for path in files],
                    "errors": [asdict(item) for item in errors],
                    "warnings": [asdict(item) for item in warnings],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    print(f"Errors: {len(errors)}; warnings: {len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
