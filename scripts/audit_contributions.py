#!/usr/bin/env python3
"""Recursively inventory and validate every DynNav contribution module."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

MATURITY = (
    "Implemented",
    "Research Prototype",
    "Experimental",
    "Synthetic Validation",
    "Simulation Validation",
    "Pending ROS2 Validation",
    "Pending Hardware Validation",
    "Planned",
    "Deprecated",
)
REQUIRED_HEADINGS = (
    "One-sentence contribution",
    "Research motivation",
    "Research question",
    "Scientific hypothesis",
    "Current maturity",
    "Architecture",
    "Mathematical formulation",
    "Repository structure",
    "Implementation",
    "Algorithms",
    "Visual explanation",
    "Experiments",
    "Baselines",
    "Ablations",
    "Generated outputs",
    "Reproduction",
    "Tests",
    "Limitations",
    "Future work",
    "Related DynNav modules",
)
MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".mp4", ".webp"}
SOURCE_SUFFIXES = {".py", ".sh", ".bash", ".yaml", ".yml", ".json", ".toml", ".xml"}
NUMBERED = re.compile(r"^(\d{2})[_-].+")


@dataclass
class Contribution:
    path: str
    number: str | None
    name: str
    readme: str | None
    maturity: str
    implementation_paths: list[str]
    scripts: list[str]
    tests: list[str]
    configurations: list[str]
    generated_artifacts: list[str]
    figures: list[str]
    gifs: list[str]
    videos: list[str]
    experiment_outputs: list[str]
    ci_references: list[str]
    readme_references: list[str]
    missing_sections: list[str]
    validation_errors: list[str]


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def maturity_for(readme_text: str, files: list[Path]) -> str:
    lower = readme_text.lower()
    for label in MATURITY:
        if label.lower() in lower:
            return label
    has_code = any(path.suffix.lower() == ".py" for path in files)
    has_tests = any("test" in path.name.lower() for path in files)
    has_results = any("result" in part.lower() for path in files for part in path.parts)
    if has_code and has_tests and has_results:
        return "Synthetic Validation"
    if has_code and has_tests:
        return "Research Prototype"
    if has_code:
        return "Experimental"
    return "Planned"


def references_to(root: Path, needle: str) -> tuple[list[str], list[str]]:
    ci: list[str] = []
    docs: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".yml", ".yaml", ".py", ".toml"}:
            continue
        content = text(path)
        if needle not in content:
            continue
        target = rel(root, path)
        if ".github/workflows" in target:
            ci.append(target)
        if path.suffix.lower() == ".md":
            docs.append(target)
    return sorted(set(ci)), sorted(set(docs))


def audit(root: Path) -> list[Contribution]:
    contributions_root = root / "contributions"
    if not contributions_root.is_dir():
        raise FileNotFoundError("contributions/ does not exist")

    records: list[Contribution] = []
    for directory in sorted((p for p in contributions_root.iterdir() if p.is_dir()), key=lambda p: p.name.casefold()):
        files = sorted(p for p in directory.rglob("*") if p.is_file())
        match = NUMBERED.match(directory.name)
        readme_path = next((p for p in files if p.name.lower() == "readme.md" and p.parent == directory), None)
        readme_text = text(readme_path) if readme_path else ""
        missing = [heading for heading in REQUIRED_HEADINGS if heading.lower() not in readme_text.lower()]
        errors: list[str] = []
        if match and readme_path is None:
            errors.append("missing canonical README.md")
        if readme_path and not readme_text.lstrip().startswith("# "):
            errors.append("README lacks a level-one title")

        implementation = [rel(root, p) for p in files if p.suffix.lower() in SOURCE_SUFFIXES and "test" not in p.name.lower()]
        scripts = [p for p in implementation if "/experiments/" in f"/{p}" or "/scripts/" in f"/{p}"]
        tests = [rel(root, p) for p in files if "test" in p.name.lower() and p.suffix.lower() == ".py"]
        repo_tests = [p for p in (root / "tests").glob("test_*.py") if directory.name in text(p)] if (root / "tests").is_dir() else []
        tests.extend(rel(root, p) for p in repo_tests)
        configs = [rel(root, p) for p in files if p.suffix.lower() in {".yaml", ".yml", ".json", ".toml"}]
        media = [rel(root, p) for p in files if p.suffix.lower() in MEDIA_SUFFIXES]
        artifacts = [rel(root, p) for p in files if any(token in part.lower() for part in p.parts for token in ("result", "output", "artifact", "report", "metric"))]
        ci_refs, doc_refs = references_to(root, directory.name)

        records.append(
            Contribution(
                path=rel(root, directory),
                number=match.group(1) if match else None,
                name=directory.name,
                readme=rel(root, readme_path) if readme_path else None,
                maturity=maturity_for(readme_text, files),
                implementation_paths=sorted(set(implementation)),
                scripts=sorted(set(scripts)),
                tests=sorted(set(tests)),
                configurations=sorted(set(configs)),
                generated_artifacts=sorted(set(artifacts)),
                figures=sorted(p for p in media if Path(p).suffix.lower() not in {".gif", ".mp4"}),
                gifs=sorted(p for p in media if Path(p).suffix.lower() == ".gif"),
                videos=sorted(p for p in media if Path(p).suffix.lower() == ".mp4"),
                experiment_outputs=sorted(set(artifacts)),
                ci_references=ci_refs,
                readme_references=doc_refs,
                missing_sections=missing,
                validation_errors=errors,
            )
        )
    return records


def write_index(path: Path, records: list[Contribution]) -> None:
    lines = ["# DynNav Contribution Index", "", "Generated from the complete checked-out `contributions/` tree.", "", "| Contribution | Maturity | Code | Tests | Media | README |", "|---|---|---:|---:|---:|---|"]
    for record in records:
        readme = f"[{record.readme}](../{record.readme})" if record.readme else "Missing"
        lines.append(f"| `{record.name}` | {record.maturity} | {len(record.implementation_paths)} | {len(record.tests)} | {len(record.figures) + len(record.gifs) + len(record.videos)} | {readme} |")
    lines.extend(["", "## Validation boundary", "", "Statuses are inferred conservatively from repository evidence. Synthetic tests or committed figures do not establish ROS2, Gazebo, or hardware validation."])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--inventory", type=Path, default=Path("results/manifests/contribution_inventory.json"))
    parser.add_argument("--validation", type=Path, default=Path("results/manifests/contribution_validation.json"))
    parser.add_argument("--index", type=Path, default=Path("docs/CONTRIBUTION_INDEX.md"))
    args = parser.parse_args()
    root = args.root.resolve()
    records = audit(root)
    numbered = [r for r in records if r.number]
    errors = [
        {"contribution": r.name, "errors": r.validation_errors, "missing_sections": r.missing_sections}
        for r in records if r.validation_errors or (r.number and r.missing_sections)
    ]
    for target, payload in (
        (root / args.inventory, {"total_directories": len(records), "numbered_contributions": len(numbered), "contributions": [asdict(r) for r in records]}),
        (root / args.validation, {"valid": not errors, "errors": errors}),
    ):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_index(root / args.index, records)
    print(f"Contribution directories: {len(records)}; numbered: {len(numbered)}; validation groups: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
