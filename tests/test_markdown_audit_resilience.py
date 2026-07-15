from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inventory_split_survives_trailing_escape() -> None:
    module = _load_script("audit_markdown_tree.py")
    assert module._safe_shlex_split("python script.py \\") == ["python script.py \\"]


def test_command_validator_keeps_strict_parser() -> None:
    module = _load_script("validate_documented_commands.py")
    assert module._safe_inventory_split("python script.py \\") == ["python script.py \\"]
    try:
        module._ORIGINAL_SHLEX_SPLIT("python script.py \\", comments=True)
    except ValueError as exc:
        assert "escaped character" in str(exc)
    else:
        raise AssertionError("strict parser must reject a trailing escape")
