"""
Contribution 26: Swarm Consensus Navigation
============================================
 A centralized coordinator selects a representative navigation proposal from
 a batch using a median/MAD outlier heuristic. This is not a distributed
 agreement protocol and provides no Byzantine fault-tolerance guarantee.

Robots submit local proposals to one coordinator. The coordinator applies a
robust-statistics heuristic to their reported costs and selects a submitted
path. The demonstration does not model message exchange or agreement rounds.

Extensions:
    - Raft-based leader election for coordinator
    - Gossip protocol for scalable plan propagation
    - Disagreement detection (builds on Contribution 09 multi-robot)

Research Question (RQ-Swarm): How does centralized median/MAD proposal
selection behave under synthetic corrupted, silent, and packet-loss cases?

References:
    Lamport et al. (1982) "Byzantine Generals Problem"
    Olfati-Saber (2006) "Flocking for Multi-Agent Dynamic Systems"
    Vieira et al. (2009) "Swarm consensus for multi-robot navigation"
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NavProposal:
    robot_id: int
    path: list[tuple[int, int]]      # sequence of (row, col) waypoints
    cost: float                      # risk-weighted cost estimate
    confidence: float                # robot's self-reported confidence
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None  # simple hash for integrity


@dataclass
class ConsensusResult:
    agreed_path: list[tuple[int, int]]
    agreed_cost: float
    n_participants: int
    n_byzantine_detected: int
    rounds: int
    method: str


# ---------------------------------------------------------------------------
# Robot agent
# ---------------------------------------------------------------------------

class SwarmRobot:
    """
    One robot in the swarm. Computes a local plan and participates in consensus.
    """

    def __init__(self, robot_id: int,
                 faulty: bool = False,
                 fault_type: str = "random"):
        self.robot_id = robot_id
        self.faulty = faulty          # simulates Byzantine / compromised robot
        self.fault_type = fault_type  # "random" | "constant_bad" | "silent"
        self._rng = np.random.default_rng(robot_id)

    def compute_proposal(self, grid: np.ndarray,
                         start: tuple[int, int],
                         goal: tuple[int, int]) -> NavProposal:
        """
        Compute a local navigation plan (A* stub with random perturbation).
        Byzantine robots return corrupted proposals.
        """
        path, cost = self._local_astar(grid, start, goal)
        confidence = 1.0

        if self.faulty:
            if self.fault_type == "random":
                # Randomly corrupt path
                path = [(self._rng.integers(0, grid.shape[0]),
                         self._rng.integers(0, grid.shape[1]))
                        for _ in range(len(path))]
                cost = self._rng.uniform(100, 1000)
                confidence = self._rng.uniform(0.1, 0.5)
            elif self.fault_type == "constant_bad":
                cost = 9999.0
                confidence = 0.99   # lies about confidence
            elif self.fault_type == "silent":
                return None   # type: ignore

        sig = f"robot_{self.robot_id}_{hash(str(path)) % 10000:04d}"
        return NavProposal(self.robot_id, path, cost, confidence,
                           signature=sig)

    def _local_astar(self, grid: np.ndarray,
                     start: tuple[int, int],
                     goal: tuple[int, int]) -> tuple[list, float]:
        """Simplified A* on the occupancy grid (BFS stub)."""
        import heapq
        H, W = grid.shape
        dist = {start: 0.0}
        prev = {start: None}
        heap = [(0.0, start)]

        while heap:
            d, u = heapq.heappop(heap)
            if u == goal:
                break
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                v = (u[0]+dr, u[1]+dc)
                if not (0 <= v[0] < H and 0 <= v[1] < W):
                    continue
                if grid[v[0], v[1]] > 0.5:
                    continue   # occupied
                nd = d + 1.0 + 2.0 * grid[v[0], v[1]]
                if nd < dist.get(v, np.inf):
                    dist[v] = nd
                    prev[v] = u
                    h = abs(v[0]-goal[0]) + abs(v[1]-goal[1])
                    heapq.heappush(heap, (nd + h, v))

        if goal not in prev:
            return [start], np.inf

        path, cur = [], goal
        while cur is not None:
            path.append(cur); cur = prev[cur]
        path.reverse()
        # Add small perturbation to cost for realism
        cost = dist.get(goal, np.inf) + self._rng.uniform(-0.5, 0.5)
        return path, max(0, cost)


# ---------------------------------------------------------------------------
# Consensus protocol
# ---------------------------------------------------------------------------

class BFTConsensus:
    """
    Backwards-compatible name for a centralized robust proposal selector.

    Algorithm:
        1. Receive proposals at one coordinator.
        2. Flag reported costs beyond median ± k*MAD as outliers.
        3. Select a submitted path nearest the median cost.

    Outlier flags do not identify malicious robots. There is no BFT guarantee.
    """

    def __init__(self, n_robots: int,
                 byzantine_threshold: float = 3.0,   # k*MAD for outlier detection
                 min_participants: float = 0.67):     # min fraction needed
        if n_robots < 1:
            raise ValueError("n_robots must be positive")
        if not np.isfinite(byzantine_threshold) or byzantine_threshold < 0:
            raise ValueError("byzantine_threshold must be finite and nonnegative")
        if not np.isfinite(min_participants) or not 0 < min_participants <= 1:
            raise ValueError("min_participants must be in (0, 1]")
        self.n_robots = n_robots
        self.byz_thresh = byzantine_threshold
        self.min_part = min_participants

    def reach_consensus(self,
                        proposals: list[NavProposal]) -> ConsensusResult:
        """
        Select one proposal from a list using centralized robust statistics.
        Returns the selected plan; this does not establish distributed agreement.
        """
        valid = [p for p in proposals if p is not None]
        ids = [p.robot_id for p in valid]
        if len(set(ids)) != len(ids):
            raise ValueError("proposal robot_id values must be unique")
        for proposal in valid:
            if (not np.isfinite(proposal.cost) or proposal.cost < 0
                    or not np.isfinite(proposal.confidence)
                    or not 0 <= proposal.confidence <= 1
                    or not proposal.path):
                raise ValueError("proposal contains invalid cost, confidence, or path")
        logger.info("Consensus: %d/%d robots responded", len(valid), self.n_robots)

        if len(valid) < int(np.ceil(self.n_robots * self.min_part)):
            logger.error("Not enough participants for robust selection")
            return ConsensusResult(
                agreed_path=[],
                agreed_cost=np.inf,
                n_participants=len(valid),
                n_byzantine_detected=0,
                rounds=1,
                method="abstain_insufficient_participants",
            )

        # Step 1: Flag cost outliers via scaled MAD (not attacker detection).
        costs = np.array([p.cost for p in valid])
        median_cost = float(np.median(costs))
        mad = float(np.median(np.abs(costs - median_cost)))
        # When MAD is zero, only proposals numerically equal to the median
        # remain. This handles a majority of identical reports without an
        # arbitrary epsilon turning every outlier into an inlier.
        tolerance = max(1e-12, self.byz_thresh * 1.4826 * mad)
        outlier_mask = np.abs(costs - median_cost) > tolerance

        honest = [p for p, out in zip(valid, outlier_mask) if not out]
        n_byz = int(outlier_mask.sum())
        logger.info("Cost outliers flagged: %d (threshold=%.1f scaled MAD)",
                    n_byz, self.byz_thresh)

        if not honest:
            honest = valid   # all suspected — use all
            n_byz = 0

        # A self-reported confidence can be adversarially inflated, so do not
        # let it affect the robust center or proposal tie-breaking.
        h_costs = np.array([p.cost for p in honest])
        agreed_cost = float(np.median(h_costs))

        # Step 3: Select path from robot closest to agreed cost, highest conf
        honest.sort(key=lambda p: (abs(p.cost - agreed_cost), p.robot_id))
        best = honest[0]

        logger.info(
            "Consensus reached: cost=%.3f path_len=%d by robot %d",
            agreed_cost, len(best.path), best.robot_id
        )
        return ConsensusResult(
            agreed_path=best.path,
            # Keep the returned path and cost from the same robot proposal;
            # the robust center is only used to rank submitted proposals.
            agreed_cost=float(best.cost),
            n_participants=len(valid),
            n_byzantine_detected=n_byz,
            rounds=1,
            method="centralized_mad_median",
        )

# ---------------------------------------------------------------------------
# Swarm coordinator
# ---------------------------------------------------------------------------

class SwarmCoordinator:
    """
    Orchestrates the full swarm: creates robots, collects proposals,
    runs centralized proposal selection, and logs results.
    """

    def __init__(self, n_robots: int = 6, n_byzantine: int = 1):
        self.robots = [
            SwarmRobot(i, faulty=(i < n_byzantine),
                       fault_type="random" if i % 2 == 0 else "constant_bad")
            for i in range(n_robots)
        ]
        self.consensus = BFTConsensus(n_robots)
        self.history: list[dict] = []

    def plan(self, grid: np.ndarray,
             start: tuple[int, int],
             goal: tuple[int, int]) -> ConsensusResult:
        """Full swarm planning round."""
        proposals = [r.compute_proposal(grid, start, goal)
                     for r in self.robots]
        result = self.consensus.reach_consensus(
            [p for p in proposals if p is not None]
        )
        self.history.append({
            "path_len": len(result.agreed_path),
            "cost": round(result.agreed_cost, 3),
            "byz_detected": result.n_byzantine_detected,
            "participants": result.n_participants,
        })
        return result

    def summary(self) -> dict:
        if not self.history:
            return {}
        return {
            "total_rounds": len(self.history),
            "mean_byz_detected": round(
                float(np.mean([h["byz_detected"] for h in self.history])), 2),
            "mean_cost": round(
                float(np.mean([h["cost"] for h in self.history])), 3),
            "n_robots": len(self.robots),
            "n_faulty": sum(1 for r in self.robots if r.faulty),
        }
