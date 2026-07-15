from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"


def _load_script(name: str):
    path = SCRIPTS_ROOT / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    added_scripts_path = str(SCRIPTS_ROOT) not in sys.path
    if added_scripts_path:
        sys.path.insert(0, str(SCRIPTS_ROOT))
    try:
        spec.loader.exec_module(module)
    finally:
        if added_scripts_path:
            sys.path.remove(str(SCRIPTS_ROOT))
    return module


def test_inventory_split_survives_trailing_escape() -> None:
    module = _load_script("audit_markdown_tree.py")
    assert module._safe_shlex_split("python script.py \\") == ["python script.py \\"]


def test_inventory_split_still_parses_valid_commands_after_patch() -> None:
    module = _load_script("audit_markdown_tree.py")
    original = module.markdown_audit_core.shlex.split
    try:
        module.markdown_audit_core.shlex.split = module._safe_shlex_split
        assert module._safe_shlex_split("python script.py --flag value") == [
            "python",
            "script.py",
            "--flag",
            "value",
        ]
    finally:
        module.markdown_audit_core.shlex.split = original


def test_command_validator_keeps_strict_parser() -> None:
    module = _load_script("validate_documented_commands.py")
    assert module._safe_inventory_split("python script.py \\") == ["python script.py \\"]
    try:
        module._ORIGINAL_SHLEX_SPLIT("python script.py \\", comments=True)
    except ValueError as exc:
        assert "escaped character" in str(exc)
    else:
        raise AssertionError("strict parser must reject a trailing escape")
