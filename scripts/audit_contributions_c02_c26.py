#!/usr/bin/env python3
"""Audit every C02-C26 tracked file, preserving precise claim boundaries.

Both C07 historic folders count toward one registered contribution.
"""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def inventory(root):
    dirs = sorted(p for p in (root / "contributions").iterdir() if p.is_dir())
    result = {}
    for n in range(2,27):
        matches = [p for p in dirs if p.name.startswith(f"{n:02d}_")]
        if not matches:
            raise FileNotFoundError(f"Missing C{n:02d} directory")
        result[f"C{n:02d}"] = matches
    return result

def inspect_checkpoint_payload(value, torch, name="root"):
    """Validate nested torch checkpoint tensors plus restricted metadata safely."""
    if isinstance(value, torch.Tensor):
        if not torch.isfinite(value).all().item():
            raise ValueError(f"Nonfinite saved tensor: {name}")
        return {"kind":"tensor", "shape":list(value.shape)}
    if isinstance(value, dict):
        if not value:
            raise ValueError(f"Empty checkpoint dictionary: {name}")
        if not all(isinstance(k,str) for k in value):
            raise ValueError(f"Non-string checkpoint metadata keys: {name}")
        return {k:inspect_checkpoint_payload(v,torch,name+"."+k) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [inspect_checkpoint_payload(v,torch,name) for v in value]
    if isinstance(value,(str,int,float,bool)) or value is None:
        import math
        if isinstance(value,float) and not math.isfinite(value):
            raise ValueError(f"Nonfinite checkpoint metadata: {name}")
        return value
    raise ValueError(f"Unsupported checkpoint metadata type: {name}: {type(value).__name__}")

def inspect_file(path, root, torch=None):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    suffix = path.suffix.lower()
    result = dict(file=path.relative_to(root).as_posix(), size=path.stat().st_size,
                  sha256=h.hexdigest(), type=suffix, status="UNCLASSIFIED_REVIEW_REQUIRED")
    try:
        if suffix == ".py":
            tree = ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
            compile(tree,str(path),"exec")
            result["status"] = "SOURCE_COMPILES_RUNTIME_UNVERIFIED"
        elif suffix == ".csv":
            with path.open(encoding="utf-8-sig",newline="") as f:
                reader=csv.reader(f)
                header=next(reader,None)
                if not header or not any(h.strip() for h in header):
                    raise ValueError("CSV header is missing")
                count=sum(1 for _ in reader)
            result.update(status="CSV_STRUCTURALLY_VALID",rows=count,columns=header)
        elif suffix == ".npz":
            import numpy as np
            with np.load(path,allow_pickle=False) as data:
                arrays={}
                for key in data.files:
                    value=data[key]
                    arrays[key]=list(value.shape)
                    if value.dtype.kind in ("f","i","u") and not np.isfinite(value).all():
                        raise ValueError(f"Nonfinite array: {key}")
            if not arrays:
                raise ValueError("Empty NPZ")
            result.update(status="NPZ_STRUCTURALLY_VALID",arrays=arrays)
        elif suffix == ".pt":
            if torch is None:
                result["status"]="BLOCKED_TORCH_MISSING"
            else:
                state=torch.load(path,map_location="cpu",weights_only=True)
                if not isinstance(state,dict) or not state:
                    raise ValueError("Not a populated state_dict")
                schema=inspect_checkpoint_payload(state,torch)
                result.update(status="PT_TENSORS_AND_METADATA_VALID",checkpoint_schema=schema)
        elif suffix == ".png":
            from PIL import Image
            with Image.open(path) as image:
                image.verify()
            result["status"]="PNG_DECODABLE"
        elif suffix == ".svg":
            tree=ET.parse(path)
            if not tree.getroot().tag.endswith("svg"):
                raise ValueError("Invalid SVG")
            result["status"]="SVG_XML_VALID"
        elif suffix in (".md",".txt"):
            path.read_text(encoding="utf-8")
            result["status"]="TEXT_READABLE"
    except Exception as e:
        result.update(status="FAILED",error=f"{type(e).__name__}: {e}")
    return result

def generate(root,out,selected=None):
    try:
        import torch
    except ImportError:
        torch=None
    directories=inventory(root)
    if selected is not None:
        unknown=selected-set(directories)
        if unknown:
            raise ValueError(f"Invalid IDs: {sorted(unknown)}")
        directories={key:value for key,value in directories.items() if key in selected}
    modules=[]
    for cid,paths in directories.items():
        files=[inspect_file(p,root,torch) for folder in paths for p in sorted(folder.rglob("*"))
               if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts]
        counts=dict(sorted(Counter(v["status"] for v in files).items()))
        modules.append(dict(id=cid,directories=[p.relative_to(root).as_posix() for p in paths],
                            file_count=len(files),status_counts=counts,
                            physical_robot_control_verified=False,
                            structural_checks_do_not_prove_efficacy=True,files=files))
    report=dict(schema_version=1,scope="C02-C26 file-level integrity only",
                n_contributions=len(modules),n_files=sum(v["file_count"] for v in modules),
                contributions=modules,
                limitation="Source compilation and artifact validity are not experiment execution, statistical verification or real robot evidence")
    out.mkdir(parents=True,exist_ok=True)
    (out/"file_manifest.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# C02-C26 exhaustive file integrity",
           "","These are structural checks, not independent scientific validation or physical-robot results.",
           "","| ID | Directories | Files | Python sources compiled | File errors |",
           "|---|---:|---:|---:|---:|"]
    for item in modules:
        lines.append(f'| {item["id"]} | {len(item["directories"])} | {item["file_count"]} | {item["status_counts"].get("SOURCE_COMPILES_RUNTIME_UNVERIFIED",0)} | {item["status_counts"].get("FAILED",0)} |')
    lines += ["",f'Total files inspected: {report["n_files"]}.',"",
              "See file_manifest.json for the SHA-256 and status of each individual file.",
              "C07 consists of two historical directories and is counted once.",
              "ROS 2, trained neural systems, formal proof and physical robot evidence need separate tests.",""]
    (out/"summary.md").write_text("\n".join(lines),encoding="utf-8")
    print("\n".join(lines))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--only",default="")
    args=p.parse_args()
    ids={v.strip().upper() for v in args.only.split(",") if v.strip()} if args.only else None
    report=generate(ROOT,args.output_dir.resolve(),ids)
    problems=[(mod["id"],f["file"],f.get("error")) for mod in report["contributions"]
              for f in mod["files"] if f["status"]=="FAILED"]
    for cid,path,reason in problems:
        print("FAILED",cid,path,reason,file=sys.stderr)
    return int(bool(problems))

if __name__=="__main__":
    raise SystemExit(main())
