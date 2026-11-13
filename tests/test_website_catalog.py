"""The public catalog must follow the tracked contribution tree."""

import json

from scripts import sync_website_contribution_catalog as catalog


def test_committed_catalog_matches_canonical_inputs():
    rendered = json.dumps(catalog.build_catalog(), ensure_ascii=False, indent=2) + "\n"
    assert catalog.OUTPUT_PATH.read_text(encoding="utf-8") == rendered


def test_untracked_files_do_not_create_catalog_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(catalog, "ROOT", tmp_path)
    folder = tmp_path / "contributions/example/tests"
    folder.mkdir(parents=True)
    (folder / "ignored.pyc").write_bytes(b"ignored")
    assert catalog._tracked_directory("contributions/example/tests", set()) is None
    (folder / "test_example.py").write_text("pass\n")
    assert catalog._tracked_directory(
        "contributions/example/tests", {"contributions/example/tests/test_example.py"}
    ) == "contributions/example/tests"
