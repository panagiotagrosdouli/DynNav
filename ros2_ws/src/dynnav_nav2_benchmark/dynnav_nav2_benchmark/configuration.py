"""ROS-independent planner configuration for the Nav2 benchmarks."""

from __future__ import annotations

import copy
from typing import Any

PLANNER_IDS = (
    "NavFn",
    "Smac2D",
    "DynNavShortest",
    "DynNavRisk",
    "DynNavRecoverability",
    "DynNavJoint",
)

HISTORY_PLANNER_IDS = (
    "NavFn",
    "DynNavShortest",
    "DynNavHistory",
)

CORRELATED_HISTORY_PLANNER_IDS = (
    "DynNavShortest",
    "DynNavHistory",
    "DynNavRobustHistory",
)


def planner_parameter_overrides() -> dict[str, dict[str, Any]]:
    """Return the complete six-planner configuration used in every static trial."""

    return {
        "NavFn": {
            "plugin": "nav2_navfn_planner::NavfnPlanner",
            "tolerance": 0.5,
            "use_astar": False,
            "allow_unknown": True,
        },
        "Smac2D": {
            "plugin": "nav2_smac_planner::SmacPlanner2D",
            "tolerance": 0.125,
            "downsample_costmap": False,
            "downsampling_factor": 1,
            "allow_unknown": True,
            "max_iterations": 1_000_000,
            "max_on_approach_iterations": 1_000,
            "terminal_checking_interval": 5_000,
            "max_planning_time": 2.0,
            "cost_travel_multiplier": 2.0,
        },
        "DynNavShortest": {
            "plugin": "dynnav_nav2_cpp::DynNavGlobalPlanner",
            "allow_unknown": True,
            "lethal_cost_threshold": 253,
            "neutral_cost": 1.0,
            "risk_weight": 0.0,
            "irreversibility_weight": 0.0,
            "unknown_risk": 0.5,
            "max_iterations": 0,
        },
        "DynNavRisk": {
            "plugin": "dynnav_nav2_cpp::DynNavGlobalPlanner",
            "allow_unknown": True,
            "lethal_cost_threshold": 253,
            "neutral_cost": 1.0,
            "risk_weight": 4.0,
            "irreversibility_weight": 0.0,
            "unknown_risk": 0.5,
            "max_iterations": 0,
        },
        "DynNavRecoverability": {
            "plugin": "dynnav_nav2_cpp::DynNavGlobalPlanner",
            "allow_unknown": True,
            "lethal_cost_threshold": 253,
            "neutral_cost": 1.0,
            "risk_weight": 0.0,
            "irreversibility_weight": 4.0,
            "unknown_risk": 0.5,
            "max_iterations": 0,
        },
        "DynNavJoint": {
            "plugin": "dynnav_nav2_cpp::DynNavGlobalPlanner",
            "allow_unknown": True,
            "lethal_cost_threshold": 253,
            "neutral_cost": 1.0,
            "risk_weight": 4.0,
            "irreversibility_weight": 4.0,
            "unknown_risk": 0.5,
            "max_iterations": 0,
        },
    }


def _planner_server(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        planner_parameters = payload["planner_server"]["ros__parameters"]
    except (KeyError, TypeError) as exc:
        raise ValueError("base Nav2 parameters do not define planner_server") from exc
    if not isinstance(planner_parameters, dict):
        raise ValueError("planner_server.ros__parameters must be a mapping")
    return planner_parameters


def freeze_global_costmap_for_planner_comparison(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Return Nav2 parameters with a static-map-only global planning costmap.

    The local costmap is intentionally untouched so physical Gazebo blockers
    remain visible to the controller/collision stack.  This helper exists to
    make paired global-plan comparisons use the same map-derived cost surface
    in every trial rather than a scan-history-dependent obstacle layer.
    """

    merged = copy.deepcopy(payload)
    try:
        global_costmap = merged["global_costmap"]["global_costmap"][
            "ros__parameters"
        ]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "base Nav2 parameters do not define global_costmap.global_costmap"
        ) from exc
    if not isinstance(global_costmap, dict):
        raise ValueError("global costmap ros__parameters must be a mapping")

    global_costmap["plugins"] = ["static_layer", "inflation_layer"]
    global_costmap.pop("obstacle_layer", None)
    global_costmap.pop("voxel_layer", None)

    static_layer = global_costmap.setdefault("static_layer", {})
    if not isinstance(static_layer, dict):
        raise ValueError("global static_layer parameters must be a mapping")
    static_layer.setdefault("plugin", "nav2_costmap_2d::StaticLayer")
    static_layer["map_subscribe_transient_local"] = True

    inflation_layer = global_costmap.setdefault("inflation_layer", {})
    if not isinstance(inflation_layer, dict):
        raise ValueError("global inflation_layer parameters must be a mapping")
    inflation_layer.setdefault("plugin", "nav2_costmap_2d::InflationLayer")
    return merged


def inject_planner_parameters(payload: dict[str, Any]) -> dict[str, Any]:
    """Copy base Nav2 parameters and replace only planner-server plugins."""

    merged = copy.deepcopy(payload)
    planner_parameters = _planner_server(merged)
    planner_parameters["planner_plugins"] = list(PLANNER_IDS)
    planner_parameters.pop("GridBased", None)
    planner_parameters.update(planner_parameter_overrides())
    return merged


def inject_history_planner_parameters(
    payload: dict[str, Any],
    *,
    safe_cell: tuple[int, int],
    trigger: tuple[tuple[int, int], tuple[int, int]],
    closure_cell: tuple[int, int],
    closure_probability: float,
    recoverability_weight: float,
) -> dict[str, Any]:
    """Inject the frozen three-planner action-history comparison.

    `DynNavShortest` and `DynNavHistory` use the same C++ plugin and base
    costmap semantics. The latter differs only by the opt-in augmented history
    state and its recoverability term, isolating the representation under test.
    """

    if not 0.0 <= closure_probability <= 1.0:
        raise ValueError("closure_probability must be in [0, 1]")
    if recoverability_weight < 0.0:
        raise ValueError("recoverability_weight must be non-negative")

    merged = copy.deepcopy(payload)
    planner_parameters = _planner_server(merged)
    planner_parameters["planner_plugins"] = list(HISTORY_PLANNER_IDS)
    planner_parameters.pop("GridBased", None)

    base = planner_parameter_overrides()
    planner_parameters["NavFn"] = base["NavFn"]
    planner_parameters["DynNavShortest"] = base["DynNavShortest"]

    (sx, sy), (tx, ty) = trigger
    cx, cy = closure_cell
    safe_x, safe_y = safe_cell
    history = dict(base["DynNavShortest"])
    history.update(
        {
            "history_aware": True,
            "history_safe_cells": f"{safe_x}:{safe_y}",
            "history_hazards": f"{sx}:{sy}>{tx}:{ty}@{cx}:{cy}@{closure_probability:.17g}",
            "history_recoverability_weight": float(recoverability_weight),
            "history_max_hazard_cells": 16,
        }
    )
    planner_parameters["DynNavHistory"] = history
    return merged


def inject_correlated_history_planner_parameters(
    payload: dict[str, Any],
    *,
    safe_cell: tuple[int, int],
    hazards: tuple[
        tuple[
            tuple[tuple[int, int], tuple[int, int]]
            | tuple[tuple[tuple[int, int], tuple[int, int]], ...],
            tuple[int, int] | tuple[tuple[int, int], ...],
            float,
        ],
        ...,
    ],
    recoverability_weight: float,
    pairwise_joint_lower: float = 0.0,
    pairwise_joint_upper: float = 1.0,
) -> dict[str, Any]:
    """Inject the bounded two-hazard dependence comparison.

    The independence and robust planners share exactly the same trigger,
    closure and marginal-probability model. The robust condition differs only
    by allowing the joint closure probability to vary inside the configured
    interval. The current C++ robust oracle intentionally supports at most two
    hazards.
    """

    if len(hazards) != 2:
        raise ValueError("correlated history benchmark requires exactly two hazards")
    if recoverability_weight < 0.0:
        raise ValueError("recoverability_weight must be non-negative")
    if not 0.0 <= pairwise_joint_lower <= pairwise_joint_upper <= 1.0:
        raise ValueError("pairwise joint bounds must satisfy 0 <= lower <= upper <= 1")

    encoded: list[str] = []
    for trigger_spec, closure_spec, probability in hazards:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("closure probability must be in [0, 1]")

        if (
            len(trigger_spec) == 2
            and all(
                isinstance(cell, tuple)
                and len(cell) == 2
                and all(isinstance(value, int) for value in cell)
                for cell in trigger_spec
            )
        ):
            trigger_edges = (trigger_spec,)
        else:
            trigger_edges = tuple(trigger_spec)
        if not trigger_edges:
            raise ValueError("trigger gate cannot be empty")
        trigger_text = "+".join(
            f"{int(sx)}:{int(sy)}>{int(tx)}:{int(ty)}"
            for (sx, sy), (tx, ty) in trigger_edges
        )

        if (
            len(closure_spec) == 2
            and all(isinstance(value, int) for value in closure_spec)
        ):
            closure_cells = (closure_spec,)
        else:
            closure_cells = tuple(closure_spec)
        if not closure_cells:
            raise ValueError("closure footprint cannot be empty")
        closure_text = "+".join(
            f"{int(cx)}:{int(cy)}" for cx, cy in closure_cells
        )
        encoded.append(
            f"{trigger_text}@{closure_text}@{probability:.17g}"
        )

    merged = copy.deepcopy(payload)
    planner_parameters = _planner_server(merged)
    planner_parameters["planner_plugins"] = list(CORRELATED_HISTORY_PLANNER_IDS)
    planner_parameters.pop("GridBased", None)

    base = planner_parameter_overrides()
    planner_parameters["DynNavShortest"] = base["DynNavShortest"]

    safe_x, safe_y = safe_cell
    common = dict(base["DynNavShortest"])
    common.update(
        {
            "history_aware": True,
            "history_safe_cells": f"{safe_x}:{safe_y}",
            "history_hazards": ";".join(encoded),
            "history_recoverability_weight": float(recoverability_weight),
            "history_max_hazard_cells": 2,
        }
    )
    planner_parameters["DynNavHistory"] = dict(common)

    robust = dict(common)
    robust.update(
        {
            "history_robust_pairwise_dependence": True,
            "history_pairwise_joint_lower": float(pairwise_joint_lower),
            "history_pairwise_joint_upper": float(pairwise_joint_upper),
        }
    )
    planner_parameters["DynNavRobustHistory"] = robust
    return merged
