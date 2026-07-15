#!/usr/bin/env python3
"""Runtime hardening shared by repository documentation validators."""

from __future__ import annotations

from pathlib import Path

import markdown_audit_core

_SOURCE_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".c", ".cc", ".cpp",
    ".cxx", ".h", ".hh", ".hpp", ".java", ".rs", ".go", ".rb", ".php",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
}
_ORIGINAL_IS_DOCUMENT = markdown_audit_core.is_document


def install_document_discovery_filter() -> None:
    """Prevent source files with Markdown-like strings from becoming documents."""

    def filtered(path: Path) -> bool:
        if path.suffix.lower() in _SOURCE_SUFFIXES:
            return False
        return _ORIGINAL_IS_DOCUMENT(path)

    markdown_audit_core.is_document = filtered
