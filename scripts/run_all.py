from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from dynnav.research_pipeline import load_config, run_pipeline


@dataclass(frozen=True)
class StageResult:
    name: str
    status: str
    detail: str


REQUIRED_IMPORTS = (
    "dynnav",
    "dynnav.mapping",
    "dynnav.benchmarks",
    "dynnav.lab_grade",
    "dynnav.planning",
    "dynnav.research_modules",
    "dynnav.research_pipeline",
)

REQUIRED_REPOSITORY_PATHS = (
    "README.md",
    "pyproject.toml",
    "configs/default.yaml",
    "docs/REPRODUCIBILITY.md",
    "assets/readme/dynnav_living_map.svg",
    "website/package.json",
)

REQUIRED_PIPELINE_ARTIFACTS = (
    "metrics/metrics.csv",
    "metrics/summary.json",
    "executed_trajectory.csv",
    "reroute_events.csv",
    "safety_events.csv",
    "figures/trajectory.png",
    "videos/dynnav_demo.gif",
    "reports/evaluation_report.md",
    "reports/reproducibility_report.md",
)


def _run_stage(name: str, action: Callable[[], str]) -> StageResult:
    try:
        return StageResult(name, "passed", action())
    except Exception as exc:  # noqa: BLE001 - top-level validator must report every stage
        return StageResult(name, "failed", f"{type(exc).__name__}: {exc}")


def _check_imports() -> str:
    for module_name in REQUIRED_IMPORTS:
        importlib.import_module(module_name)
    return f"imported {len(REQUIRED_IMPORTS)} required modules"


def _check_repository_paths() -> str:
    missing = [path for path in REQUIRED_REPOSITORY_PATHS if not Path(path).exists()]
    if missing:
        raise FileNotFoundError("missing required repository paths: " + ", ".join(missing))
    return f"found {len(REQUIRED_REPOSITORY_PATHS)} required repository paths"


def _check_config(config_path: str) -> str:
    cfg = load_config(config_path)
    height, width = cfg["map_size"]
    if height < 8 or width < 8:
        raise ValueError("map_size dimensions must both be at least 8")
    if not 0 <= float(cfg["obstacle_density"]) < 1:
        raise ValueError("obstacle_density must be in [0, 1)")
    if int(cfg["dynamic_obstacle_count"]) < 0:
        raise ValueError("dynamic_obstacle_count must be non-negative")
    if int(cfg["max_steps"]) <= 0:
        raise ValueError("max_steps must be positive")
    for key in ("start", "goal"):
        x, y = cfg[key]
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"{key}={cfg[key]} lies outside map_size={cfg['map_size']}")
    return f"validated configuration {config_path}"


def _check_document_references() -> str:
    readme = Path("README.md").read_text(encoding="utf-8")
    required_refs = (
        "assets/readme/dynnav_living_map.svg",
        "docs/MATHEMATICAL_FORMULATION.md",
        "docs/EVALUATION_PROTOCOL.md",
        "docs/REPRODUCIBILITY.md",
        "docs/ROS2_NAV2_INTEGRATION.md",
    )
    missing_text = [ref for ref in required_refs if ref not in readme]
    missing_files = [ref for ref in required_refs if not Path(ref).exists()]
    if missing_text or missing_files:
        raise ValueError(
            "README reference audit failed; "
            f"missing references={missing_text}, missing files={missing_files}"
        )
    return f"validated {len(required_refs)} README references"


def _check_artifacts(root: Path) -> str:
    missing = [str(root / rel) for rel in REQUIRED_PIPELINE_ARTIFACTS if not (root / rel).is_file()]
    if missing:
        raise FileNotFoundError("missing generated artifacts: " + ", ".join(missing))
    empty = [str(root / rel) for rel in REQUIRED_PIPELINE_ARTIFACTS if (root / rel).stat().st_size == 0]
    if empty:
        raise ValueError("empty generated artifacts: " + ", ".join(empty))
    return f"validated {len(REQUIRED_PIPELINE_ARTIFACTS)} generated artifacts"


def _run_pipeline(config_path: str, out_dir: Path, smoke: bool) -> str:
    cfg = load_config(config_path)
    cfg["output_dir"] = str(out_dir)
    metrics = run_pipeline(cfg, smoke=smoke)
    (out_dir / "manifests").mkdir(parents=True, exist_ok=True)
    (out_dir / "manifests" / "run_summary.json").write_text(
        json.dumps({"mode": "smoke" if smoke else "research", "metrics": metrics}, indent=2),
        encoding="utf-8",
    )
    _check_artifacts(out_dir)
    return f"generated deterministic outputs in {out_dir}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and validate the DynNav research platform")
    parser.add_argument("--mode", choices=("smoke", "demo", "research", "validate"), default=None)
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--out-dir", default="results/run_all")
    parser.add_argument("--smoke", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    if args.mode is None:
        args.mode = "smoke" if args.smoke else "validate"
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out_dir)
    stages = [
        _run_stage("imports", _check_imports),
        _run_stage("configuration", lambda: _check_config(args.config)),
        _run_stage("repository paths", _check_repository_paths),
        _run_stage("documentation references", _check_document_references),
    ]

    if args.mode in {"smoke", "demo", "research"}:
        smoke = args.mode == "smoke"
        stages.append(
            _run_stage(
                f"{args.mode} pipeline",
                lambda: _run_pipeline(args.config, out_dir, smoke=smoke),
            )
        )
    elif args.mode == "validate" and out_dir.exists():
        stages.append(_run_stage("existing artifacts", lambda: _check_artifacts(out_dir)))
    else:
        stages.append(StageResult("existing artifacts", "skipped", f"{out_dir} does not exist"))

    print("DynNav validation summary")
    for stage in stages:
        print(f"- {stage.status.upper():7} {stage.name}: {stage.detail}")

    failed = [stage for stage in stages if stage.status == "failed"]
    skipped = [stage for stage in stages if stage.status == "skipped"]
    print(f"Passed stages: {sum(stage.status == 'passed' for stage in stages)}")
    print(f"Failed stages: {len(failed)}")
    print(f"Skipped optional stages: {len(skipped)}")
    print(f"Output path: {out_dir}")
    if failed and args.verbose:
        print("Environmental or validation blockers:")
        for stage in failed:
            print(f"  - {stage.name}: {stage.detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
