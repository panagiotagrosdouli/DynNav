"""Swarm consensus evaluation utilities for Contribution 26.

The base module implements BFT weighted-median consensus. This evaluator turns
that mechanism into measurable multi-robot outcomes:

- consensus accuracy against an honest reference path cost,
- mission success rate,
- Byzantine detection recall proxy,
- communication overhead,
- scalability score,
- trust-weighted agreement quality,
- packet-loss / silent-robot robustness.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from swarm_consensus import SwarmCoordinator, SwarmRobot


@dataclass(frozen=True)
class SwarmConsensusEvalResult:
    scenario: str
    n_robots: int
    n_byzantine: int
    fault_type: str
    packet_loss_rate: float
    participants: int
    consensus_method: str
    consensus_rounds: int
    consensus_accuracy: float
    mission_success: bool
    byzantine_detection_recall: float
    communication_messages: int
    communication_scaling: float
    trust_weighted_agreement: float
    scalability_score: float
    agreed_cost: float
    reference_cost: float

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return asdict(self)


def make_grid(size: int = 24, obstacle_density: float = 0.08, seed: int = 26) -> np.ndarray:
    rng = np.random.default_rng(seed)
    grid = (rng.random((size, size)) < obstacle_density).astype(float)
    grid[0, 0] = 0.0
    grid[size - 2, size - 2] = 0.0
    # Add a central obstacle block but keep corridors around it.
    c = size // 2
    grid[c - 2:c + 2, c - 2:c + 2] = 1.0
    grid[c, :] = np.minimum(grid[c, :], 0.0)
    grid[:, c] = np.minimum(grid[:, c], 0.0)
    return grid


def honest_reference_cost(grid: np.ndarray, start: tuple[int, int], goal: tuple[int, int]) -> float:
    robot = SwarmRobot(999, faulty=False)
    _, cost = robot._local_astar(grid, start, goal)
    return float(cost)


def configure_faults(coord: SwarmCoordinator, n_byzantine: int, fault_type: str) -> None:
    for i, robot in enumerate(coord.robots):
        robot.faulty = i < n_byzantine
        robot.fault_type = fault_type if robot.faulty else "honest"


def apply_packet_loss(coord: SwarmCoordinator, packet_loss_rate: float, seed: int = 1234) -> None:
    rng = np.random.default_rng(seed)
    for robot in coord.robots:
        if not robot.faulty and rng.random() < packet_loss_rate:
            robot.faulty = True
            robot.fault_type = "silent"


def consensus_accuracy(agreed_cost: float, reference_cost: float) -> float:
    if not np.isfinite(agreed_cost) or not np.isfinite(reference_cost):
        return 0.0
    rel_error = abs(agreed_cost - reference_cost) / max(1.0, abs(reference_cost))
    return float(max(0.0, 1.0 - rel_error))


def trust_weighted_agreement(result_cost: float, reference_cost: float, participants: int, n_robots: int) -> float:
    acc = consensus_accuracy(result_cost, reference_cost)
    participation = participants / max(1, n_robots)
    return float(0.7 * acc + 0.3 * participation)


def evaluate_swarm_consensus_case(
    scenario: str,
    n_robots: int,
    n_byzantine: int,
    fault_type: str = "random",
    packet_loss_rate: float = 0.0,
    grid_seed: int = 26,
) -> SwarmConsensusEvalResult:
    grid = make_grid(size=24, obstacle_density=0.06, seed=grid_seed)
    start = (0, 0)
    goal = (22, 22)
    ref_cost = honest_reference_cost(grid, start, goal)

    coord = SwarmCoordinator(n_robots=n_robots, n_byzantine=0)
    configure_faults(coord, n_byzantine=n_byzantine, fault_type=fault_type)
    apply_packet_loss(coord, packet_loss_rate=packet_loss_rate, seed=grid_seed + n_robots)
    actual_faulty = sum(1 for r in coord.robots if r.faulty)

    result = coord.plan(grid, start, goal)
    acc = consensus_accuracy(result.agreed_cost, ref_cost)
    mission_success = bool(result.agreed_path and np.isfinite(result.agreed_cost) and acc >= 0.75)
    detection_recall = result.n_byzantine_detected / max(1, actual_faulty)
    messages = int(result.n_participants * max(1, result.rounds))
    comm_scaling = float(messages / max(1, n_robots))
    twa = trust_weighted_agreement(result.agreed_cost, ref_cost, result.n_participants, n_robots)
    scalability = float(twa / (1.0 + 0.02 * messages))

    return SwarmConsensusEvalResult(
        scenario=scenario,
        n_robots=n_robots,
        n_byzantine=actual_faulty,
        fault_type=fault_type,
        packet_loss_rate=float(packet_loss_rate),
        participants=result.n_participants,
        consensus_method=result.method,
        consensus_rounds=result.rounds,
        consensus_accuracy=acc,
        mission_success=mission_success,
        byzantine_detection_recall=float(min(1.0, detection_recall)),
        communication_messages=messages,
        communication_scaling=comm_scaling,
        trust_weighted_agreement=twa,
        scalability_score=scalability,
        agreed_cost=float(result.agreed_cost),
        reference_cost=float(ref_cost),
    )


def benchmark_cases() -> list[dict[str, float | int | str]]:
    cases: list[dict[str, float | int | str]] = []
    for n in [5, 10, 20, 50]:
        cases.append({"scenario": f"scale_{n}_honest", "n_robots": n, "n_byzantine": 0, "fault_type": "random", "packet_loss_rate": 0.0})
        cases.append({"scenario": f"scale_{n}_bft_bound", "n_robots": n, "n_byzantine": max(1, (n - 1) // 3), "fault_type": "constant_bad", "packet_loss_rate": 0.0})
    cases.extend([
        {"scenario": "random_byzantine", "n_robots": 12, "n_byzantine": 3, "fault_type": "random", "packet_loss_rate": 0.0},
        {"scenario": "silent_faults", "n_robots": 12, "n_byzantine": 2, "fault_type": "silent", "packet_loss_rate": 0.0},
        {"scenario": "packet_loss_20pct", "n_robots": 12, "n_byzantine": 1, "fault_type": "random", "packet_loss_rate": 0.20},
        {"scenario": "packet_loss_35pct", "n_robots": 12, "n_byzantine": 1, "fault_type": "random", "packet_loss_rate": 0.35},
    ])
    return cases


def summarize_swarm_results(results: list[SwarmConsensusEvalResult]) -> dict[str, float | int]:
    if not results:
        raise ValueError("results must not be empty")
    return {
        "n_cases": len(results),
        "mission_success_rate": sum(r.mission_success for r in results) / len(results),
        "mean_consensus_accuracy": float(np.mean([r.consensus_accuracy for r in results])),
        "mean_detection_recall": float(np.mean([r.byzantine_detection_recall for r in results])),
        "mean_scalability_score": float(np.mean([r.scalability_score for r in results])),
        "mean_messages": float(np.mean([r.communication_messages for r in results])),
    }
