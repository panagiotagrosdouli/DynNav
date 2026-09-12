from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_markdown import audit, markdown_files  # noqa: E402


def test_generated_indexes_are_not_direct_audit_inputs(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (docs / "DOCUMENTATION_MAP.md").write_text(
        "# Generated map\n\n[stale](../removed.md)\n",
        encoding="utf-8",
    )
    (docs / "MARKDOWN_INVENTORY.md").write_text(
        "# Generated inventory\n\n[stale](../also-removed.md)\n",
        encoding="utf-8",
    )

    discovered = {path.relative_to(tmp_path).as_posix() for path in markdown_files(tmp_path)}
    assert discovered == {"README.md"}

    files, errors, _warnings = audit(tmp_path)
    assert {path.relative_to(tmp_path).as_posix() for path in files} == {"README.md"}
    assert errors == []


def test_source_markdown_missing_target_still_fails(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Project\n\n[missing](missing.md)\n",
        encoding="utf-8",
    )

    _files, errors, _warnings = audit(tmp_path)
    assert len(errors) == 1
    assert errors[0].kind == "missing-target"
