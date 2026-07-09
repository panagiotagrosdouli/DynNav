from __future__ import annotations

from pathlib import Path

from dynnav.research_pipeline import load_config, make_grid, plan, run_pipeline, fields


def test_grid_world_generation_default_config() -> None:
    cfg = load_config("configs/default.yaml")
    grid = make_grid(cfg)
    assert grid.shape == tuple(cfg["map_size"])
    assert grid[cfg["start"][1], cfg["start"][0]] == 0
    assert grid[cfg["goal"][1], cfg["goal"][0]] == 0


def test_planner_returns_valid_path() -> None:
    cfg = load_config("configs/default.yaml")
    grid = make_grid(cfg)
    known = grid == 0
    risk, uncertainty, recoverability = fields(grid, known, [])
    path, info = plan(grid, tuple(cfg["start"]), tuple(cfg["goal"]), risk, uncertainty, recoverability, "astar")
    assert info["success"]
    assert path[0] == tuple(cfg["start"])
    assert path[-1] == tuple(cfg["goal"])


def test_run_all_smoke_outputs(tmp_path: Path) -> None:
    cfg = load_config("configs/default.yaml")
    cfg["output_dir"] = str(tmp_path)
    metrics = run_pipeline(cfg, smoke=True)
    assert "replanning_count" in metrics
    assert (tmp_path / "metrics/metrics.csv").exists()
    assert (tmp_path / "figures/trajectory.png").exists()
    assert (tmp_path / "videos/dynnav_demo.gif").exists()
    assert (tmp_path / "reports/evaluation_report.md").exists()
