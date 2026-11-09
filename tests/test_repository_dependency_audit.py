"""Focused tests for the read-only repository dependency inventory."""

import runpy
from pathlib import Path

AUDIT = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts" / "audit_repository_dependencies.py"))
directory_paths = AUDIT["directory_paths"]
imports_in_file = AUDIT["imports_in_file"]
build_report = AUDIT["build_report"]


def test_directory_paths_include_nested_folders_and_exclude_files():
    paths = ["dynnav/__init__.py", "dynnav/planners/astar.py", "README.md", ".github/workflows/ci.yml"]
    assert directory_paths(paths) == [".github", ".github/workflows", "dynnav", "dynnav/planners"]


def test_static_import_resolution_and_relative_imports():
    paths = {"dynnav/core/__init__.py", "dynnav/core/grid.py", "dynnav/planners/a.py"}
    code = "import dynnav.core.grid\nfrom ..core import grid\nimport external_library\n"
    edges, error = imports_in_file("dynnav/planners/a.py", code, paths)
    assert error is None
    assert {edge["target"] for edge in edges} == {"dynnav/core/grid.py", "dynnav/core/__init__.py"}


def test_syntax_errors_are_reported():
    edges, error = imports_in_file("pkg/bad.py", "if (:\n", {"pkg/bad.py"})
    assert edges == []
    assert "line 1" in error


def test_identical_sources_are_only_candidates(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    for name in ("a/x.py", "b/x.py"):
        (tmp_path / name).write_text("VALUE = 1\n", encoding="utf-8")
    report = build_report(tmp_path, ["a/x.py", "b/x.py"])
    assert report["directory_count"] == 2
    assert report["tracked_file_count"] == 2
    assert report["duplicate_source_content_candidates"][0]["paths"] == ["a/x.py", "b/x.py"]
