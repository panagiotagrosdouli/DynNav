#!/usr/bin/env python3
"""Repository-wide discovery and validation for Markdown and documentation-like files."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shlex
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse

IGNORED_DIRS = {".git", ".next", "node_modules", ".venv", "venv", "__pycache__"}
DOC_NAMES = re.compile(
    r"^(readme(?:[._ -].*)?|contributing(?:\..*)?|changelog(?:\..*)?|roadmap(?:\..*)?|"
    r"audit(?:\..*)?|work[_ -]?log(?:\..*)?|status(?:\..*)?|reproducibility(?:[_ -]?report)?(?:\..*)?|"
    r"design(?:[_ -]?notes?)?(?:\..*)?|support(?:\..*)?|security(?:\..*)?|code[_ -]?of[_ -]?conduct(?:\..*)?)$",
    re.IGNORECASE,
)
MARKDOWN_SUFFIXES = {".md", ".markdown"}
MARKDOWN_SIGNALS = (
    re.compile(r"^#{1,6}\s+\S", re.MULTILINE),
    re.compile(r"```(?:bash|sh|shell|python|yaml|json|dockerfile|text)?\s*$", re.MULTILINE),
    re.compile(r"!?\[[^\]]+\]\([^)]+\)"),
)
LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")
HTML_REF_RE = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
COMMAND_FENCE_RE = re.compile(r"```(?:bash|sh|shell|console|zsh|python|dockerfile)?\n(.*?)```", re.DOTALL | re.IGNORECASE)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".mp4"}


@dataclass
class DocumentRecord:
    path: str
    filename: str
    extension: str
    directory_depth: int
    file_size: int
    line_count: int
    git_tracking_status: str
    last_modification_commit: str
    current_purpose: str
    target_audience: str
    linked_from_another_document: bool
    inbound_links: list[str]
    outbound_links: list[str]
    images_referenced: list[str]
    code_paths_referenced: list[str]
    commands_referenced: list[str]
    duplication_group: str
    apparent_maturity: str
    accuracy_status: str
    action_required: str
    final_action_taken: str
    sha256: str


@dataclass
class Finding:
    severity: str
    file: str
    line: int
    kind: str
    target: str
    message: str


def is_probably_text(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:8192]
    except OSError:
        return False
    return b"\x00" not in chunk


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def is_document(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in MARKDOWN_SUFFIXES or DOC_NAMES.match(path.name):
        return True
    if not is_probably_text(path) or path.stat().st_size > 2_000_000:
        return False
    text = read_text(path)
    return sum(bool(pattern.search(text)) for pattern in MARKDOWN_SIGNALS) >= 2


def discover_documents(root: Path) -> list[Path]:
    return sorted((p for p in iter_files(root) if is_document(p)), key=lambda p: str(p.relative_to(root)).casefold())


def run_git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def git_status(root: Path, path: Path) -> str:
    result = run_git(root, "status", "--porcelain", "--", str(path.relative_to(root)))
    if result == "unknown":
        return "unknown"
    return "tracked-clean" if not result else result[:2].strip() or "modified"


def last_commit(root: Path, path: Path) -> str:
    return run_git(root, "log", "-1", "--format=%H", "--", str(path.relative_to(root)))


def normalize_target(raw: str) -> str:
    return raw.strip().strip("<>").split(maxsplit=1)[0]


def external(target: str) -> bool:
    parsed = urlparse(target)
    return parsed.scheme in {"http", "https", "mailto", "tel", "data"} or target.startswith("//")


def references(text: str) -> list[str]:
    refs = [normalize_target(match.group(2)) for match in LINK_RE.finditer(text)]
    refs.extend(normalize_target(match.group(1)) for match in HTML_REF_RE.finditer(text))
    return [ref for ref in refs if ref]


def commands(text: str) -> list[str]:
    found: list[str] = []
    for block in COMMAND_FENCE_RE.findall(text):
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "$", ">")):
                stripped = stripped.lstrip("$> ")
            if stripped and not stripped.startswith("#"):
                found.append(stripped)
    return found


def classify_purpose(path: Path, text: str) -> str:
    lower = f"{path.name} {text[:1000]}".lower()
    for token, purpose in (
        ("contribut", "Contribution guidance"),
        ("reproduc", "Reproducibility report"),
        ("audit", "Audit report"),
        ("work log", "Work log"),
        ("roadmap", "Roadmap"),
        ("experiment", "Experiment documentation"),
        ("ros2", "ROS2 integration documentation"),
        ("lidar", "LiDAR integration documentation"),
        ("readme", "Directory or subsystem overview"),
    ):
        if token in lower:
            return purpose
    return "Technical documentation"


def classify_audience(path: Path, text: str) -> str:
    lower = f"{path} {text[:1500]}".lower()
    if ".github" in lower or "pull request" in lower or "issue template" in lower:
        return "Contributors and maintainers"
    if any(token in lower for token in ("ros2", "nav2", "lidar", "turtlebot")):
        return "Robotics developers and researchers"
    if any(token in lower for token in ("experiment", "evaluation", "benchmark", "reproduc")):
        return "Researchers and reviewers"
    return "Users, contributors, and researchers"


def maturity(text: str) -> str:
    lower = text.lower()
    for label in ("deprecated", "missing implementation", "planned", "documentation concept", "experimental", "research prototype", "implemented"):
        if label in lower:
            return label.title()
    return "Unclassified"


def slug(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text).strip().lower()
    clean = re.sub(r"[`*_~]", "", clean)
    clean = re.sub(r"[^\w\- ]", "", clean)
    return re.sub(r"[\s-]+", "-", clean).strip("-")


def heading_anchors(text: str) -> set[str]:
    result: set[str] = set()
    counts: dict[str, int] = defaultdict(int)
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = slug(match.group(2))
        if not base:
            continue
        index = counts[base]
        counts[base] += 1
        result.add(base if index == 0 else f"{base}-{index}")
    return result


def fence_closed(text: str) -> bool:
    open_marker: str | None = None
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if not match:
            continue
        marker = match.group(1)[0]
        if open_marker is None:
            open_marker = marker
        elif open_marker == marker:
            open_marker = None
    return open_marker is None


def resolve_local(source: Path, target: str, root: Path) -> tuple[Path | None, str]:
    clean, _, fragment = target.partition("#")
    clean = unquote(clean.split("?", 1)[0])
    destination = source if not clean else (source.parent / clean).resolve()
    try:
        destination.relative_to(root.resolve())
    except ValueError:
        return None, fragment
    return destination, fragment


def build_inventory(root: Path) -> tuple[list[DocumentRecord], list[Finding], dict[str, object], list[dict[str, object]]]:
    docs = discover_documents(root)
    doc_set = {p.resolve() for p in docs}
    texts = {p: read_text(p) for p in docs}
    inbound: dict[Path, list[str]] = defaultdict(list)
    outbound: dict[Path, list[str]] = defaultdict(list)
    findings: list[Finding] = []
    command_rows: list[dict[str, object]] = []
    anchor_cache = {p.resolve(): heading_anchors(texts[p]) for p in docs}

    for path in docs:
        rel = str(path.relative_to(root))
        text = texts[path]
        if not fence_closed(text):
            findings.append(Finding("error", rel, 0, "unclosed-code-fence", "", "document contains an unclosed fenced block"))
        for line_no, line in enumerate(text.splitlines(), 1):
            for raw in references(line):
                outbound[path].append(raw)
                if external(raw):
                    continue
                destination, fragment = resolve_local(path, raw, root)
                if destination is None:
                    findings.append(Finding("error", rel, line_no, "outside-repository", raw, "reference escapes repository root"))
                    continue
                if not destination.exists():
                    findings.append(Finding("error", rel, line_no, "missing-target", raw, "referenced path does not exist"))
                    continue
                if destination.resolve() in doc_set:
                    inbound[destination.resolve()].append(rel)
                if fragment and destination.is_file() and destination.resolve() in anchor_cache:
                    if slug(fragment) not in anchor_cache[destination.resolve()]:
                        findings.append(Finding("error", rel, line_no, "missing-anchor", raw, "target heading anchor does not exist"))
        for command in commands(text):
            first = shlex.split(command, comments=True)[0] if command.strip() else ""
            classification = "illustrative"
            if first in {"python", "python3", "pytest", "npm", "docker", "ros2", "colcon", "bash", "sh"}:
                classification = "required and executable"
            if first in {"ros2", "colcon"}:
                classification = "ROS2-only"
            if any(token in command.lower() for token in ("turtlebot", "/dev/", "lidar", "serial")):
                classification = "hardware-only"
            command_rows.append({"document": rel, "command": command, "classification": classification, "verified": False})

    hashes: dict[str, list[Path]] = defaultdict(list)
    for path, text in texts.items():
        normalized = re.sub(r"\s+", " ", text).strip().lower()
        hashes[hashlib.sha256(normalized.encode()).hexdigest()].append(path)

    records: list[DocumentRecord] = []
    for path in docs:
        rel = str(path.relative_to(root))
        text = texts[path]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        normalized_digest = hashlib.sha256(re.sub(r"\s+", " ", text).strip().lower().encode()).hexdigest()
        group = ""
        if len(hashes[normalized_digest]) > 1:
            group = "exact-normalized:" + normalized_digest[:12]
        refs = outbound[path]
        images = sorted({r for r in refs if Path(r.partition("#")[0]).suffix.lower() in IMAGE_SUFFIXES})
        code_paths = sorted({r for r in refs if not external(r) and Path(r.partition("#")[0]).suffix.lower() in {".py", ".yaml", ".yml", ".json", ".xml", ".launch.py", ".sh"}})
        action = "Keep with minor update"
        if group:
            action = "Investigate manually"
        if path.suffix.lower() not in MARKDOWN_SUFFIXES:
            action = "Convert to canonical README" if path.name.lower().startswith("readme") else "Investigate manually"
        records.append(DocumentRecord(
            path=rel,
            filename=path.name,
            extension=path.suffix,
            directory_depth=len(path.relative_to(root).parts) - 1,
            file_size=path.stat().st_size,
            line_count=len(text.splitlines()),
            git_tracking_status=git_status(root, path),
            last_modification_commit=last_commit(root, path),
            current_purpose=classify_purpose(path, text),
            target_audience=classify_audience(path, text),
            linked_from_another_document=bool(inbound[path.resolve()]),
            inbound_links=sorted(set(inbound[path.resolve()])),
            outbound_links=sorted(set(refs)),
            images_referenced=images,
            code_paths_referenced=code_paths,
            commands_referenced=commands(text),
            duplication_group=group,
            apparent_maturity=maturity(text),
            accuracy_status="Needs implementation review",
            action_required=action,
            final_action_taken="Pending review",
            sha256=digest,
        ))

    graph = {
        "nodes": [record.path for record in records],
        "edges": [
            {"source": str(path.relative_to(root)), "target": ref}
            for path, refs in outbound.items()
            for ref in sorted(set(refs))
        ],
        "orphans": sorted(record.path for record in records if not record.linked_from_another_document and record.path != "README.md"),
        "findings": [asdict(item) for item in findings],
    }
    return records, findings, graph, command_rows


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, records: list[DocumentRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(record) for record in records]
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value for key, value in row.items()})


def write_inventory_markdown(path: Path, records: list[DocumentRecord], findings: list[Finding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Markdown Inventory",
        "",
        "> Generated by `scripts/audit_markdown_tree.py`. Do not edit generated tables manually.",
        "",
        f"- Documentation-like files discovered: **{len(records)}**",
        f"- Validation errors: **{sum(item.severity == 'error' for item in findings)}**",
        "",
        "| Path | Purpose | Maturity | Inbound | Action | Final disposition |",
        "|---|---|---|---:|---|---|",
    ]
    for record in records:
        lines.append(f"| `{record.path}` | {record.current_purpose} | {record.apparent_maturity} | {len(record.inbound_links)} | {record.action_required} | {record.final_action_taken} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_documentation_map(path: Path, records: list[DocumentRecord], graph: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    canonical = [r for r in records if r.filename.lower().startswith("readme") or r.path.startswith("docs/")]
    lines = [
        "# Documentation Map",
        "",
        "> Generated from the repository-wide documentation inventory.",
        "",
        "## Canonical and index documents",
        "",
    ]
    for record in canonical:
        lines.append(f"- [`{record.path}`](../{record.path}) — {record.current_purpose}; maturity: **{record.apparent_maturity}**")
    lines.extend(["", "## Orphan documents", ""])
    for orphan in graph.get("orphans", []):
        lines.append(f"- `{orphan}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
