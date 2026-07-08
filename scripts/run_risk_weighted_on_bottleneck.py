# run_risk_weighted_on_bottleneck.py
import numpy as np

from irreversibility_map import (
    IrreversibilityConfig,
    build_irreversibility_map,
    load_grid_from_cell_table_csv,
)
from risk_weighted_planner import astar_risk_weighted
from run_irreversibility_bottleneck_sweep import (
    add_bottleneck_wall,
    pick_start_left_goal_right,
)


def main():
    path_csv = "coverage_grid_with_uncertainty.csv"

    unc_grid = load_grid_from_cell_table_csv(
        path_csv,
        value_col="uncertainty",
        row_col=("row", "col"),
        fill_nan_with="max",
    )
    free_mask = np.isfinite(unc_grid)

    # proxy feature density
    unc01 = (unc_grid - unc_grid.min()) / (unc_grid.max() - unc_grid.min() + 1e-9)
    feat_density = 1.0 - unc01

    cfg = IrreversibilityConfig(
        w_uncert=0.60,
        w_sparsity=0.25,
        w_deadend=0.15,
        deadend_radius=2,
    )
    i_grid = build_irreversibility_map(
        uncertainty_grid=unc_grid,
        feature_density_grid=feat_density,
        free_mask=free_mask,
        cfg=cfg,
    )

    # same bottleneck settings you used
    wall_i = 0.95
    door_i = 0.60
    thickness = 2
    i_bottle, wall_cols, door_rows = add_bottleneck_wall(
        i_grid,
        wall_I=wall_i,
        door_I=door_i,
        thickness=thickness,
    )

    start, goal = pick_start_left_goal_right(
        free_mask,
        i_bottle,
        wall_cols=wall_cols,
        I_max=0.50,
    )
    print(
        f"Start={start}, Goal={goal}, "
        f"I_start={i_bottle[start]:.3f}, I_goal={i_bottle[goal]:.3f}"
    )
    print(
        f"Door rows={door_rows}, wall cols={wall_cols}, "
        f"door_I={door_i}, wall_I={wall_i}"
    )

    # Try a few lambda values
    for lam in [0.0, 0.5, 1.0, 2.0, 5.0]:
        res = astar_risk_weighted(
            free_mask=free_mask,
            I_grid=i_bottle,
            start=start,
            goal=goal,
            lam=lam,
            step_cost=1.0,
            risk_agg="sum",
        )

        if res.success:
            path_i = [i_bottle[y, x] for (y, x) in res.path]
            mean_i = float(np.mean(path_i))
            print(
                f"\n[lam={lam:.2f}] success "
                f"cost={res.cost:.2f} expansions={res.expansions}"
            )
            print(
                f"  path_len={len(res.path)}  "
                f"maxI={max(path_i):.3f}  meanI={mean_i:.3f}"
            )
        else:
            print(
                f"\n[lam={lam:.2f}] FAIL reason={res.reason} "
                f"expansions={res.expansions}"
            )


if __name__ == "__main__":
    main()
