#!/usr/bin/env python3
"""Runtime hardening shared by repository documentation validators."""

from __future__ import annotations

import shlex
from pathlib import Path

import markdown_audit_core

_SOURCE_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".c", ".cc", ".cpp",
    ".cxx", ".h", ".hh", ".hpp", ".java", ".rs", ".go", ".rb", ".php",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
}
_ORIGINAL_IS_DOCUMENT = markdown_audit_core.is_document
_ORIGINAL_SHLEX_SPLIT = shlex.split


def _safe_shlex_split(command: str, comments: bool = False, posix: bool = True) -> list[str]:
    """Classify malformed documented shell lines without crashing inventory work."""

    try:
        return _ORIGINAL_SHLEX_SPLIT(command, comments=comments, posix=posix)
    except ValueError:
        stripped = command.strip()
        return [stripped] if stripped else []


def install_document_discovery_filter() -> None:
    """Install source exclusion and resilient inventory-only command parsing."""

    def filtered(path: Path) -> bool:
        if path.suffix.lower() in _SOURCE_SUFFIXES:
            return False
        return _ORIGINAL_IS_DOCUMENT(path)

    markdown_audit_core.is_document = filtered
    markdown_audit_core.shlex.split = _safe_shlex_split
