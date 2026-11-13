"""Audit the complete C01 tracked file inventory, without hiding failures.

Audits every tracked C01 file (not only a hand-picked executable subset):
- source compile and import availability; native ROS modules may require Jazzy;
- neural checkpoint serialization, layer dimensions and finite parameters;
- existing CSV, NPZ and PNG artifact structure and metadata;
- docs and SVG basic validity;
- tests are executed separately by CI.

This is an integrity/smoke matrix, not full training reproduction, safety
certification, Gazebo or physical robot validation.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def inventory(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and not p.name.startswith(".") and "__pycache__" not in p.parts)


def inspect_one(path: Path, root: Path, *, torch_available: bool) -> dict:
    import numpy as np
    relative = path.relative_to(root).as_posix()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    result = {"file": relative, "bytes": path.stat().st_size, "sha256": digest, "status": "UNCHECKED", "checks": []}
    suffix = path.suffix.lower()
    try:
        if suffix == ".py":
            contents = path.read_text(encoding="utf-8")
            tree = ast.parse(contents, filename=str(path))
            compile(tree, str(path), "exec")
            result["checks"].append("python_ast_compile")
            imports = sorted({alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names} |
                             {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module})
            result["imports"] = imports
            result["status"] = "SOURCE_COMPILES_RUNTIME_NOT_FULLY_EXECUTED"
        elif suffix == ".pt":
            if not torch_available:
                result["status"] = "BLOCKED_TORCH_UNAVAILABLE"
            else:
                import torch
                try:
                    state = torch.load(path, map_location="cpu", weights_only=True)
                except TypeError:
                    state = torch.load(path, map_location="cpu")
                if not isinstance(state, dict) or not state:
                    raise ValueError("checkpoint is not a populated state dict")
                layers = {}
                for key, value in state.items():
                    if not hasattr(value, "shape") or not torch.isfinite(value).all().item():
                        raise ValueError(f"invalid or nonfinite tensor: {key}")
                    layers[key] = list(value.shape)
                result["layers"] = layers
                result["checks"].append("torch_checkpoint_loaded_finite")
                result["status"] = "CHECKPOINT_STRUCTURALLY_VERIFIED_NOT_EFFICACY_VALIDATED"
        elif suffix == ".npz":
            with np.load(path, allow_pickle=False) as data:
                shapes = {}
                for key in data.files:
                    value = data[key]
                    shapes[key] = list(value.shape)
                    if value.dtype.kind in {"f", "i", "u"} and not bool(np.isfinite(value).all()):
                        raise ValueError(f"nonfinite values in {key}")
                if not shapes:
                    raise ValueError("empty NPZ archive")
                result["arrays"] = shapes
                result["checks"].append("npz_loaded_and_finite")
                result["status"] = "NPZ_STRUCTURALLY_VERIFIED"
        elif suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                headers = next(reader, None)
                if not headers or not any(h.strip() for h in headers):
                    raise ValueError("CSV missing header")
                count = sum(1 for _ in reader)
            result["columns"] = headers
            result["rows"] = count
            result["status"] = "CSV_STRUCTURALLY_VERIFIED" if count else "CSV_HEADER_ONLY"
        elif suffix == ".png":
            from PIL import Image
            with Image.open(path) as im:
                im.verify()
            result["checks"].append("png_decodable")
            result["status"] = "IMAGE_STRUCTURALLY_VERIFIED"
        elif suffix == ".svg":
            tree = ET.parse(path)
            if not tree.getroot().tag.endswith("svg"):
                raise ValueError("not an SVG root")
            result["status"] = "SVG_STRUCTURALLY_VERIFIED"
        elif suffix == ".md":
            if path.stat().st_size == 0:
                raise ValueError("empty document")
            path.read_text(encoding="utf-8")
            result["status"] = "DOCUMENT_READABLE_NOT_FACT_INDEPENDENTLY_VERIFIED"
        else:
            result["status"] = "UNCLASSIFIED_FILE_REVIEW_REQUIRED"
    except Exception as exc:
        result["status"] = "FAILED"
        result["error"] = type(exc).__name__ + ": " + str(exc)
    return result


def audit(root: Path, output: Path) -> dict:
    try:
        import torch
        torch_available = True
    except ImportError:
        torch_available = False
    records = [inspect_one(path, root, torch_available=torch_available) for path in inventory(root)]
    counts = {}
    for record in records:
        counts[record["status"]] = counts.get(record["status"], 0) + 1
    report = {
        "evidence_classification": "tracked_files_integrity_and_static_source_audit_only",
        "torch_available": torch_available,
        "total_files": len(records),
        "status_counts": counts,
        "not_proven": [
            "that every historical script completes a valid end-to-end run",
            "that every saved model was trained on held-out real-world data",
            "that all C01 artifacts were independently reproduced",
            "that a physical robot was driven by C01",
        ],
        "files": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"total_files":len(records),"status_counts":counts,"output":str(output)}, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = audit(args.root.resolve(), args.output)
    return 1 if result["status_counts"].get("FAILED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
