"""Federated navigation learning evaluation utilities for Contribution 16.

The base module implements FedAvg. This evaluator adds audit metrics that matter
for robot fleets:

- mean validation error,
- per-client generalization error,
- fairness gap between best and worst client,
- communication cost,
- privacy/noise setting metadata.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from federated_nav import FedNavConfig, FederatedRobotClient, FederatedServer, NavModel


@dataclass(frozen=True)
class FederatedEvalResult:
    scenario: str
    aggregation: str
    dp_enabled: bool
    dp_epsilon: float
    n_clients: int
    rounds: int
    mean_client_mse: float
    worst_client_mse: float
    best_client_mse: float
    fairness_gap: float
    communication_floats: int
    final_server_val_mse: float

    def to_dict(self) -> dict[str, float | int | bool | str]:
        return asdict(self)


def make_client_validation_sets(cfg: FedNavConfig, n_eval: int = 64) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create heterogeneous local validation sets for each robot."""
    sets = []
    for robot_id in range(cfg.n_robots):
        rng = np.random.default_rng(10_000 + robot_id)
        shift = (robot_id - cfg.n_robots / 2) / max(1, cfg.n_robots)
        x = rng.standard_normal((n_eval, cfg.input_dim)) + shift
        # Heterogeneous expert style per robot.
        w = rng.standard_normal((cfg.output_dim, cfg.input_dim)) * (0.15 + 0.03 * robot_id)
        y = np.tanh(x @ w.T)
        sets.append((x, y))
    return sets


def evaluate_model_on_clients(model: NavModel, validation_sets: list[tuple[np.ndarray, np.ndarray]]) -> list[float]:
    losses = []
    for x, y in validation_sets:
        preds = np.stack([model.predict(row) for row in x])
        losses.append(float(np.mean((preds - y) ** 2)))
    return losses


def estimate_communication_floats(model: NavModel, n_clients: int, rounds: int) -> int:
    params = model.get_params()
    n_params = sum(int(v.size) for v in params.values())
    # Each round: server broadcasts global params and each client returns params.
    return int(rounds * n_params * (n_clients + n_clients))


def run_federated_eval(
    scenario: str,
    aggregation: str,
    dp_epsilon: float | None,
    n_clients: int = 6,
    rounds: int = 8,
) -> FederatedEvalResult:
    cfg = FedNavConfig(
        n_robots=n_clients,
        global_rounds=rounds,
        local_epochs=3,
        lr=0.02,
        aggregation=aggregation,
        dp_epsilon=dp_epsilon,
    )
    global_model = NavModel.random_init(cfg.input_dim, cfg.output_dim, seed=42)
    clients = [FederatedRobotClient(i, global_model, cfg) for i in range(cfg.n_robots)]
    server = FederatedServer(global_model, cfg)
    history = server.run_training(clients)
    validation_sets = make_client_validation_sets(cfg)
    client_losses = evaluate_model_on_clients(server.global_model, validation_sets)

    return FederatedEvalResult(
        scenario=scenario,
        aggregation=aggregation,
        dp_enabled=dp_epsilon is not None,
        dp_epsilon=float(dp_epsilon if dp_epsilon is not None else -1.0),
        n_clients=n_clients,
        rounds=rounds,
        mean_client_mse=float(np.mean(client_losses)),
        worst_client_mse=float(np.max(client_losses)),
        best_client_mse=float(np.min(client_losses)),
        fairness_gap=float(np.max(client_losses) - np.min(client_losses)),
        communication_floats=estimate_communication_floats(server.global_model, n_clients, rounds),
        final_server_val_mse=float(history[-1]["val_mse"]),
    )
