"""
Contribution 16: Federated Navigation Learning
===============================================
Federated multi-robot learning: clients train a local navigation model and
share parameters with a server. Optional server-side Gaussian noise is a
client-level central-DP mechanism under the assumptions documented below; it
does not hide updates from the aggregation server.

Implements FedAvg (McMahan et al. 2017), with optional clipped client updates
and server-side Gaussian noise. In DP mode the server uses uniform weights,
fixed participation, replace-one client adjacency and basic composition across
rounds. This is a research simulation, not a production privacy guarantee.

Research Question (RQ-Fed): Does federated learning of navigation heuristics
across a heterogeneous robot fleet improve generalisation to unseen environments
without sharing private map data?

References:
    McMahan et al. (2017) "Communication-Efficient Learning of Deep Networks
    from Decentralized Data" (FedAvg)
    Dwork & Roth (2014) "The Algorithmic Foundations of Differential Privacy"
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class FedNavConfig:
    n_robots: int = 6
    local_epochs: int = 5
    global_rounds: int = 20
    lr: float = 0.01
    dp_epsilon: Optional[float] = None    # None = no DP noise
    dp_delta: float = 1e-5
    dp_clip_norm: float = 1.0
    aggregation: str = "weighted"         # "uniform" | "weighted"
    input_dim: int = 16                   # feature vector size
    output_dim: int = 2                   # (vx, vy) action

    def __post_init__(self) -> None:
        if self.n_robots < 1 or self.local_epochs < 1 or self.global_rounds < 1:
            raise ValueError("robot count, epochs, and rounds must be positive")
        if self.lr <= 0 or not np.isfinite(self.lr):
            raise ValueError("lr must be finite and positive")
        if self.aggregation not in {"uniform", "weighted"}:
            raise ValueError("aggregation must be 'uniform' or 'weighted'")
        if self.input_dim < 1 or self.output_dim < 1:
            raise ValueError("model dimensions must be positive")
        if self.dp_epsilon is not None:
            if not np.isfinite(self.dp_epsilon) or self.dp_epsilon <= 0:
                raise ValueError("dp_epsilon must be finite and positive")
            if not 0 < self.dp_delta < 1 or not np.isfinite(self.dp_delta):
                raise ValueError("dp_delta must be finite and in (0, 1)")
            if not np.isfinite(self.dp_clip_norm) or self.dp_clip_norm <= 0:
                raise ValueError("dp_clip_norm must be finite and positive")
            if self.aggregation != "uniform":
                raise ValueError("DP mode requires uniform aggregation")
            if self.dp_epsilon / self.global_rounds > 1:
                raise ValueError("basic composition requires epsilon/rounds <= 1")


# ---------------------------------------------------------------------------
# Minimal linear navigation model (replace with MLP / CNN in prod)
# ---------------------------------------------------------------------------

@dataclass
class NavModel:
    """Simple linear policy: action = W @ features + b"""
    W: np.ndarray
    b: np.ndarray

    @classmethod
    def random_init(cls, in_d: int, out_d: int, seed: int = 0) -> "NavModel":
        rng = np.random.default_rng(seed)
        return cls(
            W=rng.standard_normal((out_d, in_d)) * 0.01,
            b=np.zeros(out_d),
        )

    def predict(self, features: np.ndarray) -> np.ndarray:
        return np.tanh(self.W @ features + self.b)

    def get_params(self) -> dict[str, np.ndarray]:
        return {"W": self.W.copy(), "b": self.b.copy()}

    def set_params(self, params: dict[str, np.ndarray]) -> None:
        self.W = params["W"].copy()
        self.b = params["b"].copy()

    def clone(self) -> "NavModel":
        return NavModel(self.W.copy(), self.b.copy())


# ---------------------------------------------------------------------------
# Robot (local client)
# ---------------------------------------------------------------------------

class FederatedRobotClient:
    """
    Represents one robot that trains locally on its own experience buffer
    and returns model updates to the server.
    """

    def __init__(self, robot_id: int, model: NavModel, cfg: FedNavConfig):
        self.robot_id = robot_id
        self.model = model.clone()
        self.cfg = cfg
        self._experience: list[tuple[np.ndarray, np.ndarray]] = []
        self._rng = np.random.default_rng(robot_id)

    def collect_experience(self, n_steps: int = 50) -> None:
        """Simulate local data collection (stub: random features & targets)."""
        features = self._rng.standard_normal((n_steps, self.cfg.input_dim))
        # Simulated expert actions (e.g. from a local planner)
        targets = np.tanh(self._rng.standard_normal((n_steps, self.cfg.output_dim)))
        self._experience = list(zip(features, targets))
        logger.debug("[Robot %d] Collected %d samples", self.robot_id, n_steps)

    def local_train(self) -> dict[str, np.ndarray]:
        """Run SGD for local_epochs; return updated parameters."""
        if not self._experience:
            raise RuntimeError(f"Robot {self.robot_id}: no experience collected")

        for _ in range(self.cfg.local_epochs):
            for feat, tgt in self._experience:
                pred = self.model.predict(feat)
                err = pred - tgt  # MSE gradient
                d_tanh = (1 - pred ** 2)                          # (out_d,)
                grad_W = np.outer(d_tanh * err, feat)             # (out_d, in_d)
                grad_b = d_tanh * err                             # (out_d,)
                self.model.W -= self.cfg.lr * grad_W
                self.model.b -= self.cfg.lr * grad_b

        # The server applies clipping/noise to client deltas. Clipping absolute
        # model parameters would not bound sensitivity of a client's update.
        return self.model.get_params()

    @property
    def n_samples(self) -> int:
        return len(self._experience)


# ---------------------------------------------------------------------------
# Federated Server
# ---------------------------------------------------------------------------

class FederatedServer:
    """
    Aggregates model updates from robot clients using FedAvg (weighted or
    uniform) and broadcasts the new global model.
    """

    def __init__(self, global_model: NavModel, cfg: FedNavConfig):
        self.global_model = global_model
        self.cfg = cfg
        self.round_history: list[dict] = []

    def aggregate(self, client_updates: list[tuple[dict[str, np.ndarray], int]]
                  ) -> dict[str, np.ndarray]:
        """
        FedAvg aggregation.
        Parameters
        ----------
        client_updates : list of (params_dict, n_samples)
        """
        if not client_updates:
            raise ValueError("No client updates to aggregate")

        reference = self.global_model.get_params()
        expected_keys = set(reference)
        for params, n_samples in client_updates:
            if n_samples <= 0:
                raise ValueError("client sample counts must be positive")
            if set(params) != expected_keys:
                raise ValueError("client parameter keys do not match global model")
            for key, value in params.items():
                if value.shape != reference[key].shape or not np.all(np.isfinite(value)):
                    raise ValueError(f"invalid client parameter array: {key}")

        if self.cfg.dp_epsilon is not None and len(client_updates) != self.cfg.n_robots:
            raise ValueError("DP mode requires the configured fixed client cohort")

        if self.cfg.dp_epsilon is not None:
            return self._aggregate_dp(client_updates, reference)

        total_n = sum(n for _, n in client_updates)
        weights = (
            [n / total_n for _, n in client_updates]
            if self.cfg.aggregation == "weighted"
            else [1.0 / len(client_updates)] * len(client_updates)
        )

        agg: dict[str, np.ndarray] = {}
        for (params, _), w in zip(client_updates, weights):
            for k, v in params.items():
                agg[k] = agg.get(k, np.zeros_like(v)) + w * v

        return agg

    def _aggregate_dp(
        self,
        client_updates: list[tuple[dict[str, np.ndarray], int]],
        reference: dict[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        """Aggregate clipped client deltas with a basic-composition Gaussian mechanism.

        This gives a central client-level mechanism for the released aggregate,
        assuming a fixed cohort and replace-one adjacency. The server still sees
        each unnoised client update; this is not local differential privacy.
        """
        count = len(client_updates)
        clipped_deltas: list[dict[str, np.ndarray]] = []
        for params, _ in client_updates:
            delta = {key: params[key] - reference[key] for key in reference}
            norm = float(np.sqrt(sum(np.sum(value ** 2) for value in delta.values())))
            scale = min(1.0, self.cfg.dp_clip_norm / max(norm, 1e-12))
            clipped_deltas.append({key: value * scale for key, value in delta.items()})

        mean_delta = {
            key: sum(update[key] for update in clipped_deltas) / count
            for key in reference
        }
        eps_round = self.cfg.dp_epsilon / self.cfg.global_rounds
        delta_round = self.cfg.dp_delta / self.cfg.global_rounds
        # Classic Gaussian calibration for eps <= 1. Replace-one sensitivity
        # of the mean is 2*C/count for fixed-size client adjacency.
        sigma = (2 * self.cfg.dp_clip_norm / count
                 * np.sqrt(2 * np.log(1.25 / delta_round)) / eps_round)
        rng = np.random.default_rng()
        return {
            key: reference[key] + value + rng.normal(0.0, sigma, value.shape)
            for key, value in mean_delta.items()
        }

    def run_round(self, clients: list[FederatedRobotClient]) -> dict:
        """Execute one federated round: collect → train → aggregate → broadcast."""
        updates = []
        if self.cfg.dp_epsilon is not None and len(clients) != self.cfg.n_robots:
            raise ValueError("DP mode requires the configured fixed client cohort")
        for client in clients:
            client.model.set_params(self.global_model.get_params())
            client.collect_experience()
            params = client.local_train()
            updates.append((params, client.n_samples))

        new_params = self.aggregate(updates)
        self.global_model.set_params(new_params)

        # Evaluate on a held-out synthetic validation set
        rng = np.random.default_rng(999)
        val_X = rng.standard_normal((100, self.cfg.input_dim))
        val_Y = np.tanh(rng.standard_normal((100, self.cfg.output_dim)))
        preds = np.stack([self.global_model.predict(x) for x in val_X])
        val_loss = float(np.mean((preds - val_Y) ** 2))

        record = {
            "round": len(self.round_history) + 1,
            "val_mse": round(val_loss, 6),
            "n_clients": len(clients),
            "total_samples": sum(n for _, n in updates),
        }
        self.round_history.append(record)
        logger.info("Fed round %d | val_MSE=%.4f", record["round"], val_loss)
        return record

    def run_training(self, clients: list[FederatedRobotClient]
                     ) -> list[dict]:
        """Run all global rounds."""
        for _ in range(self.cfg.global_rounds):
            self.run_round(clients)
        return self.round_history
