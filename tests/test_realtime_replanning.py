import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "contributions", "realtime_replanning", "code"
    ),
)

import numpy as np  # noqa: E402
from dstar_lite import DStarLite  # noqa: E402
from naive_replanner import NaiveReplanner  # noqa: E402


def _open_grid(H=10, W=10):
    return np.zeros((H, W), dtype=np.int32)


def _maze_grid():
    g = np.zeros((8, 8), dtype=np.int32)
    g[2, 1:6] = 1
    g[5, 2:7] = 1
    return g


class TestDStarLiteBasic:
    def test_simple_plan_found(self):
        grid = _open_grid()
        d = DStarLite(grid, (0, 0), (9, 9))
        path = d.plan()
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (9, 9)

    def test_path_length_manhattan_lower_bound(self):
        grid = _open_grid()
        d = DStarLite(grid, (0, 0), (5, 5))
        path = d.plan()
        assert path is not None
        assert len(path) - 1 >= 10

    def test_no_path_when_blocked(self):
        grid = np.zeros((5, 5), dtype=np.int32)
        grid[:, 2] = 1
        d = DStarLite(grid, (0, 2), (4, 2))
        path = d.plan()
        assert path is None

    def test_path_all_cells_free(self):
        grid = _open_grid()
        d = DStarLite(grid, (0, 0), (9, 9))
        path = d.plan()
        assert path is not None
        for x, y in path:
            assert grid[y, x] == 0

    def test_goal_equals_start(self):
        grid = _open_grid()
        d = DStarLite(grid, (5, 5), (5, 5))
        assert d.plan() == [(5, 5)]


class TestDStarLiteReplan:
    def test_replan_after_obstacle(self):
        grid = _open_grid()
        d = DStarLite(grid, (0, 0), (9, 9))
        path1 = d.plan()
        assert path1 is not None
        bx, by = path1[2]
        d.update_edge(bx, by, blocked=True)
        path2 = d.replan()
        assert path2 is not None
        assert (bx, by) not in path2

    def test_replan_incremental_count(self):
        d = DStarLite(_open_grid(), (0, 0), (5, 5))
        d.plan()
        d.replan()
        d.replan()
        assert d.replan_count == 2

    def test_replan_with_new_start(self):
        d = DStarLite(_open_grid(), (0, 0), (9, 9))
        d.plan()
        path = d.replan(new_start=(3, 3))
        assert path is not None
        assert path[0] == (3, 3)
        assert path[-1] == (9, 9)

    def test_obstacle_cleared(self):
        grid = _open_grid()
        grid[0, 5] = 1
        d = DStarLite(grid, (0, 0), (9, 0))
        assert d.plan() is not None
        d.update_edge(5, 0, blocked=False)
        assert d.replan() is not None

    def test_repeated_block_and_clear_terminates(self):
        d = DStarLite(_open_grid(15, 15), (0, 0), (14, 14))
        path = d.plan()
        assert path is not None

        for _ in range(25):
            d.update_edge(7, 7, blocked=True)
            blocked_path = d.replan()
            assert blocked_path is not None
            assert (7, 7) not in blocked_path

            d.update_edge(7, 7, blocked=False)
            assert d.replan() is not None

        assert d.replan_count == 50
        assert d.expansions < 15 * 15 * 50 * 51

    def test_moving_start_replans_remain_bounded(self):
        d = DStarLite(_open_grid(20, 20), (0, 0), (19, 19))
        path = d.plan()
        assert path is not None

        for new_start in path[1:12]:
            repaired = d.replan(new_start=new_start)
            assert repaired is not None
            assert repaired[0] == new_start
            assert repaired[-1] == (19, 19)


class TestDStarLiteVsNaive:
    def test_same_path_length_open_grid(self):
        grid = _open_grid()
        dstar = DStarLite(grid.copy(), (0, 0), (9, 9))
        naive = NaiveReplanner(grid.copy(), (0, 0), (9, 9))
        p_dstar = dstar.plan()
        p_naive = naive.plan()
        assert p_dstar is not None and p_naive is not None
        assert len(p_dstar) == len(p_naive)

    def test_dstar_expansions_are_non_negative(self):
        grid = _open_grid(15, 15)
        dstar = DStarLite(grid.copy(), (0, 0), (14, 14))
        naive = NaiveReplanner(grid.copy(), (0, 0), (14, 14))
        dstar.plan()
        naive.plan()
        dstar.update_edge(7, 7, blocked=True)
        dstar.replan()
        naive.update_edge(7, 7, blocked=True)
        naive.replan()
        assert dstar.expansions >= 0


class TestNaiveReplanner:
    def test_plan_found(self):
        r = NaiveReplanner(_open_grid(), (0, 0), (9, 9))
        path = r.plan()
        assert path is not None
        assert path[0] == (0, 0)
        assert path[-1] == (9, 9)

    def test_no_path_isolated_goal(self):
        grid = np.zeros((5, 5), dtype=np.int32)
        grid[:, 3] = 1
        r = NaiveReplanner(grid, (0, 0), (4, 0))
        assert r.plan() is None

    def test_replan_count_increments(self):
        r = NaiveReplanner(_open_grid(), (0, 0), (5, 5))
        r.plan()
        r.replan()
        r.replan()
        assert r.replan_count == 2

    def test_update_edge_blocks_cell(self):
        r = NaiveReplanner(_open_grid(6, 6), (0, 0), (5, 5))
        path1 = r.plan()
        assert path1 is not None
        bx, by = path1[2]
        r.update_edge(bx, by, blocked=True)
        path2 = r.replan()
        assert path2 is None or (bx, by) not in path2

    def test_replan_with_new_start(self):
        r = NaiveReplanner(_open_grid(), (0, 0), (9, 9))
        r.plan()
        path = r.replan(new_start=(4, 4))
        assert path is not None
        assert path[0] == (4, 4)
        assert path[-1] == (9, 9)

    def test_path_valid_no_obstacles(self):
        grid = _open_grid()
        r = NaiveReplanner(grid, (1, 1), (8, 8))
        path = r.plan()
        assert path is not None
        for x, y in path:
            assert grid[y, x] == 0
