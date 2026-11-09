#!/usr/bin/env python3
"""Read-only tracked-path and static Python-import inventory for DynNav.

The report is a structural audit, not proof that an import executes successfully.
Git-ignored files, dynamic imports and non-Python dependencies are outside scope.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

SOURCE_SUFFIXES = {".py", ".c", ".cpp", ".h", ".hpp", ".js", ".jsx", ".ts", ".tsx"}
GENERATED_PREFIXES = ("results/", "logs_", "assets/", "pdfs/")


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return sorted(part.decode("utf-8") for part in result.stdout.split(b"\0") if part)


def directory_paths(paths: list[str]) -> list[str]:
    directories: set[str] = set()
    for name in paths:
        parts = Path(name).parts
        directories.update("/".join(parts[:length]) for length in range(1, len(parts)))
    return sorted(directories)


def local_module(name: str, source_paths: set[str]) -> str | None:
    relative = name.replace(".", "/")
    for candidate in (
        f"{relative}.py",
        f"{relative}/__init__.py",
        f"src/{relative}.py",
        f"src/{relative}/__init__.py",
    ):
        if candidate in source_paths:
            return candidate
    return None


def imports_in_file(path: str, content: str, source_paths: set[str]) -> tuple[list[dict[str, str]], str | None]:
    """Return resolvable static imports, with syntax errors reported separately."""
    try:
        tree = ast.parse(content, filename=path)
    except SyntaxError as exc:
        return [], f"{exc.msg} at line {exc.lineno}"

    dependencies: set[tuple[str, str]] = set()
    parent = list(Path(path).parent.parts)
    if parent and parent[0] == "src":
        parent.pop(0)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [(alias.name, "import") for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                keep = max(0, len(parent) - (node.level - 1))
                prefix = parent[:keep]
                base = ".".join([*prefix, *(node.module.split(".") if node.module else [])])
            else:
                base = node.module or ""
            names = [(base, "from")] if base else []
            names.extend((f"{base}.{alias.name}".strip("."), "from-member") for alias in node.names if alias.name != "*")
        else:
            continue

        for name, kind in names:
            target = local_module(name, source_paths)
            if target and target != path:
                dependencies.add((target, kind))

    return [
        {"target": target, "kind": kind}
        for target, kind in sorted(dependencies)
    ], None


def build_report(root: Path, files: list[str]) -> dict:
    directories = directory_paths(files)
    source_paths = {p for p in files if p.endswith(".py")}
    links: list[dict] = []
    parse_errors: list[dict] = []
    digest_groups: dict[str, list[str]] = defaultdict(list)
    root_counts = Counter(directory.split("/")[0] for directory in directories if "/" not in directory)

    for name in files:
        path = root / name
        if not path.is_file():
            continue
        if path.suffix in SOURCE_SUFFIXES and not name.startswith(GENERATED_PREFIXES):
            digest_groups[hashlib.sha256(path.read_bytes()).hexdigest()].append(name)
        if name not in source_paths:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            parse_errors.append({"file": name, "error": "cannot decode as UTF-8"})
            continue
        dependencies, error = imports_in_file(name, content, source_paths)
        if error:
            parse_errors.append({"file": name, "error": error})
        for dep in dependencies:
            links.append({"source": name, **dep})

    for folder in directories:
        if "/" in folder:
            root_counts[folder.split("/")[0]] += 1

    return {
        "schema_version": 1,
        "scope": "tracked files and static resolvable Python imports only",
        "root_directories": sorted({path.split("/")[0] for path in directories}),
        "directory_count": len(directories),
        "tracked_file_count": len(files),
        "python_file_count": len(source_paths),
        "directory_paths": directories,
        "folder_counts_by_root": dict(sorted(root_counts.items())),
        "static_local_python_import_edges": sorted(links, key=lambda edge: (edge["source"], edge["target"], edge["kind"])),
        "duplicate_source_content_candidates": [
            {"sha256": digest, "paths": sorted(paths)}
            for digest, paths in sorted(digest_groups.items())
            if len(paths) > 1
        ],
        "python_parse_errors": parse_errors,
        "limitations": [
            "Import resolution is approximate and static; wildcard and dynamic imports are not resolved.",
            "An import edge does not prove that the import is executed in a test or production.",
            "An identical source digest does not prove that either file is safely removable.",
            "ROS XML/CMake, web API calls, JavaScript imports and runtime dependencies need separate audits.",
            "Git does not record empty directories or untracked local files.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, default=Path("results/repository_dependency_audit.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    report = build_report(root, tracked_files(root))
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"Tracked files: {report['tracked_file_count']}; folders: {report['directory_count']}; "
        f"Python imports: {len(report['static_local_python_import_edges'])}; "
        f"parse issues: {len(report['python_parse_errors'])}; report: {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
