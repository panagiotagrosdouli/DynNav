#!/usr/bin/env python3
"""Hash every tracked file and record explicitly bounded format-level checks.

Parsing is not semantic review, scientific validation, or execution evidence.
Unsupported formats remain marked unvalidated rather than silently passing.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

import tomllib
import yaml
from PIL import Image


def inspect_file(root: Path, name: str) -> dict:
    path = root / name
    row = {"path": name, "checks": [], "semantic_review": "NOT PERFORMED"}
    if path.is_symlink():
        row.update(status="UNVALIDATED", symlink_target=str(path.readlink()))
        return row
    try:
        data = path.read_bytes()
        row.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        row["checks"].append("read_and_sha256")
        suffix = path.suffix.lower()
        check = None
        if suffix == ".py":
            check = "python_ast_parse"
            ast.parse(data, filename=name)
        elif suffix == ".json":
            check = "json_parse"
            json.loads(data)
        elif suffix in {".yaml", ".yml"}:
            check = "yaml_safe_parse"
            list(yaml.safe_load_all(data))
        elif suffix == ".toml":
            check = "toml_parse"
            tomllib.loads(data.decode("utf-8"))
        elif suffix in {".xml", ".sdf", ".urdf", ".xacro", ".svg"}:
            check = "xml_parse"
            ET.fromstring(data)
        elif suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".pgm"}:
            check = "pillow_verify"
            with Image.open(path) as img:
                img.verify()
        elif suffix == ".zip":
            check = "zip_crc"
            with zipfile.ZipFile(path) as archive:
                bad = archive.testzip()
                if bad:
                    raise ValueError(f"CRC failure: {bad}")
        elif suffix == ".sh":
            check = "bash_syntax"
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            if result.returncode:
                raise ValueError(result.stderr.strip())
        if check:
            row["checks"].append(check)
            row["status"] = "STATIC FORMAT CHECK PASSED"
        else:
            row["status"] = "UNVALIDATED"
    except Exception as exc:
        row.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    rows = [inspect_file(root, name) for name in sorted(filter(None, names))]
    report = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
        "scope": "Working-tree bytes of tracked files; format checks only; no provenance or semantic certification",
        "limitations": [
            "YAML parsing does not validate workflow semantics; PyYAML uses YAML 1.1 scalar rules.",
            "C/C++, TypeScript, JavaScript, SQL, Dockerfiles, PDFs and LaTeX require separate toolchains.",
            "Image/archive integrity does not verify origin, license or scientific authenticity.",
            "No runtime dependency, checkpoint, dataset or bibliography verification is implied.",
        ],
        "counts": dict(Counter(row["status"] for row in rows)),
        "files": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["counts"], sort_keys=True))
    return int(any(row["status"] == "FAILED" for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
