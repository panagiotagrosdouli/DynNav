#!/usr/bin/env python3
"""Runtime hardening shared by repository documentation validators."""

from __future__ import annotations

import re
import shlex
from pathlib import Path

import markdown_audit_core

_SOURCE_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".c", ".cc", ".cpp",
    ".cxx", ".h", ".hh", ".hpp", ".java", ".rs", ".go", ".rb", ".php",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
}
_SHELL_LANGUAGES = {"bash", "sh", "shell", "console", "zsh"}
_EXECUTABLE_PREFIXES = {
    "python", "python3", "pytest", "pip", "pip3", "npm", "npx", "docker",
    "ros2", "colcon", "bash", "sh", "make", "cmake", "git", "find",
    "streamlit", "dynnav-benchmark", "sudo", "source", "export", "mkdir",
}
_FENCE_OPEN = re.compile(r"^\s*```\s*([^\s`]*)\s*$")
_ORIGINAL_IS_DOCUMENT = markdown_audit_core.is_document
_ORIGINAL_SHLEX_SPLIT = shlex.split


def _safe_shlex_split(command: str, comments: bool = False, posix: bool = True) -> list[str]:
    """Classify malformed documented shell lines without crashing inventory work."""

    try:
        return _ORIGINAL_SHLEX_SPLIT(command, comments=comments, posix=posix)
    except ValueError:
        stripped = command.strip()
        return [stripped] if stripped else []


def _documented_commands(text: str) -> list[str]:
    """Extract executable shell commands and join backslash continuations."""

    commands: list[str] = []
    in_fence = False
    language = ""
    buffer = ""
    for raw_line in text.splitlines():
        match = _FENCE_OPEN.match(raw_line)
        if match:
            if not in_fence:
                in_fence = True
                language = match.group(1).lower()
                buffer = ""
            else:
                if buffer:
                    commands.append(buffer.strip())
                in_fence = False
                language = ""
                buffer = ""
            continue
        if not in_fence or (language and language not in _SHELL_LANGUAGES):
            continue
        line = raw_line.strip().lstrip("$> ")
        if not line or line.startswith("#"):
            continue
        if buffer:
            line = f"{buffer} {line}"
            buffer = ""
        if line.endswith("\\"):
            buffer = line[:-1].rstrip()
            continue
        try:
            first = _ORIGINAL_SHLEX_SPLIT(line, comments=True)[0]
        except (ValueError, IndexError):
            first = ""
        if first in _EXECUTABLE_PREFIXES:
            commands.append(line)
    if buffer:
        commands.append(buffer.strip())
    return commands


def install_document_discovery_filter() -> None:
    """Install source exclusion and resilient documentation command parsing."""

    def filtered(path: Path) -> bool:
        if path.suffix.lower() in _SOURCE_SUFFIXES:
            return False
        return _ORIGINAL_IS_DOCUMENT(path)

    markdown_audit_core.is_document = filtered
    markdown_audit_core.shlex.split = _safe_shlex_split
    markdown_audit_core.commands = _documented_commands
