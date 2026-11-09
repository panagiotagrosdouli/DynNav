"""
Contribution 12: Diffusion Occupancy Maps
==========================================
Untrained NumPy diffusion-shaped occupancy prototype for probabilistic
occupancy prediction. Its score network has no training routine or checkpoint;
it is not an evaluated learned diffusion model.
Instead of a single deterministic occupancy grid, the model produces a
*distribution* over future occupancy maps by running reverse diffusion
from Gaussian noise conditioned on the current sensor history.

Research Question (RQ-Diff): Does a diffusion-based occupancy model
reduce collision rate and improve risk estimation compared to deterministic
or Kalman-filter-based predictions?

References:
    Song et al. (2020) "Score-Based Generative Modeling through SDEs"
    Luo & Hu (2021) "Diffusion Probabilistic Models for 3D Point Cloud Generation"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class DiffusionOccupancyConfig:
    grid_h: int = 64
    grid_w: int = 64
    T: int = 50                    # diffusion steps
    beta_start: float = 1e-4
    beta_end: float = 0.02
    n_samples: int = 10            # particles for Monte-Carlo risk
    history_len: int = 5           # frames of occupancy history as conditioning
    device: str = "cpu"            # "cuda" if available
    seed: int = 42

    def __post_init__(self) -> None:
        if min(self.grid_h, self.grid_w, self.T, self.n_samples, self.history_len) < 1:
            raise ValueError("grid dimensions, diffusion steps, samples, and history must be positive")
        if not 0 < self.beta_start < 1 or not 0 < self.beta_end < 1:
            raise ValueError("beta schedule parameters must be in (0, 1)")


# ---------------------------------------------------------------------------
# Noise schedule helpers
# ---------------------------------------------------------------------------

def cosine_beta_schedule(T: int,
                          s: float = 0.008) -> tuple[np.ndarray, np.ndarray]:
    """Cosine beta schedule (Nichol & Dhariwal 2021)."""
    if T < 1 or not np.isfinite(s) or s < 0:
        raise ValueError("T must be positive and s must be finite and nonnegative")
    steps = np.arange(T + 1) / T
    alpha_bar = np.cos((steps + s) / (1 + s) * np.pi / 2) ** 2
    alpha_bar = alpha_bar / alpha_bar[0]
    betas = 1 - alpha_bar[1:] / alpha_bar[:-1]
    betas = np.clip(betas, 0, 0.999)
    alphas = 1.0 - betas
    alphas_cumprod = np.cumprod(alphas)
    return betas, alphas_cumprod


# ---------------------------------------------------------------------------
# Lightweight U-Net score network (numpy-only, replace with PyTorch in prod)
# ---------------------------------------------------------------------------

class ScoreNetwork:
    """
    Minimal score-estimator s_θ(x_t, t, cond).
    Production: replace with a proper U-Net (e.g. diffusers UNet2DModel).
    Here we use a single-layer MLP stub for correctness testing.
    """

    def __init__(self, grid_h: int, grid_w: int, seed: int = 0):
        self.h = grid_h
        self.w = grid_w
        d = grid_h * grid_w
        rng = np.random.default_rng(seed)
        self.W1 = rng.standard_normal((2 * d + 1, 128)) * 0.01  # x, condition, timestep
        self.W2 = rng.standard_normal((128, d)) * 0.01

    def forward(self, x: np.ndarray, t: int,
                cond: np.ndarray) -> np.ndarray:
        """
        x    : (H, W) noisy occupancy
        t    : diffusion timestep
        cond : (H, W) conditioning (last observed occupancy)
        Returns score estimate (H, W).
        """
        flat = x.flatten()
        cond_flat = np.asarray(cond, dtype=float).reshape(-1)
        if flat.size != self.h * self.w or cond_flat.size != self.h * self.w:
            raise ValueError("x and cond must match the configured grid shape")
        if not np.all(np.isfinite(flat)) or not np.all(np.isfinite(cond_flat)):
            raise ValueError("x and cond must contain finite values")
        if not np.isfinite(t):
            raise ValueError("t must be finite")
        inp = np.concatenate([flat, cond_flat, [t / 1000.0]])
        h = np.tanh(inp @ self.W1)
        score = (h @ self.W2).reshape(self.h, self.w)
        return score


# ---------------------------------------------------------------------------
# Diffusion Occupancy Predictor
# ---------------------------------------------------------------------------

class DiffusionOccupancyPredictor:
    """
    Generates N future occupancy map samples via DDPM reverse diffusion,
    then derives risk metrics from the ensemble.
    """

    def __init__(self, config: DiffusionOccupancyConfig | None = None):
        self.cfg = config or DiffusionOccupancyConfig()
        self.betas, self.alphas_bar = cosine_beta_schedule(self.cfg.T)
        self.alphas = 1.0 - self.betas
        self.score_net = ScoreNetwork(self.cfg.grid_h, self.cfg.grid_w, seed=self.cfg.seed)
        self._rng = np.random.default_rng(self.cfg.seed)

    # ------------------------------------------------------------------
    # Forward (training) pass  — adds noise
    # ------------------------------------------------------------------

    def q_sample(self, x0: np.ndarray, t: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Diffuse x0 to timestep t.
        Returns (x_t, noise).
        """
        x0 = np.asarray(x0, dtype=float)
        if x0.shape != (self.cfg.grid_h, self.cfg.grid_w) or not np.all(np.isfinite(x0)):
            raise ValueError("x0 must be a finite map matching the configured grid")
        if not 0 <= t < self.cfg.T:
            raise ValueError("t must be in [0, T)")
        noise = self._rng.standard_normal(x0.shape)
        alpha_bar_t = self.alphas_bar[t]
        x_t = np.sqrt(alpha_bar_t) * x0 + np.sqrt(1 - alpha_bar_t) * noise
        return x_t, noise

    # ------------------------------------------------------------------
    # Reverse (inference) pass  — denoises
    # ------------------------------------------------------------------

    def p_sample_step(self, x_t: np.ndarray, t: int,
                      cond: np.ndarray) -> np.ndarray:
        """One reverse step: x_t → x_{t-1}."""
        beta_t = self.betas[t]
        alpha_t = self.alphas[t]
        alpha_bar_t = self.alphas_bar[t]

        score = self.score_net.forward(x_t, t, cond)
        # DDPM mean (simplified)
        mean = (1 / np.sqrt(alpha_t)) * (
            x_t - (beta_t / np.sqrt(1 - alpha_bar_t)) * score
        )
        if t > 0:
            noise = self._rng.standard_normal(x_t.shape)
            x_prev = mean + np.sqrt(beta_t) * noise
        else:
            x_prev = mean
        return x_prev

    def sample(self, cond: np.ndarray) -> np.ndarray:
        """Full reverse chain: noise → predicted occupancy map."""
        x = self._rng.standard_normal((self.cfg.grid_h, self.cfg.grid_w))
        for t in reversed(range(self.cfg.T)):
            x = self.p_sample_step(x, t, cond)
        return np.clip(x, 0.0, 1.0)

    # ------------------------------------------------------------------
    # Risk metrics from ensemble
    # ------------------------------------------------------------------

    def predict_risk(self, history: list[np.ndarray]
                     ) -> dict[str, np.ndarray]:
        """
        Run N reverse diffusions conditioned on the last observed occupancy.
        Returns per-cell occupancy mean, std, and CVaR risk map.

        Parameters
        ----------
        history : list of (H, W) binary occupancy grids, newest last
        """
        if not history:
            raise ValueError("Need at least one occupancy frame in history")
        if len(history) > self.cfg.history_len:
            raise ValueError("history exceeds configured history_len")
        frames = [np.asarray(frame, dtype=float) for frame in history]
        expected_shape = (self.cfg.grid_h, self.cfg.grid_w)
        if any(frame.shape != expected_shape or not np.all(np.isfinite(frame))
               or np.any((frame < 0) | (frame > 1)) for frame in frames):
            raise ValueError("history frames must be finite occupancy maps in [0, 1] with configured shape")
        cond = frames[-1]
        samples = np.stack(
            [self.sample(cond) for _ in range(self.cfg.n_samples)], axis=0
        )  # (N, H, W)

        mean_map = samples.mean(axis=0)
        std_map = samples.std(axis=0)

        # CVaR at α=0.95: expected occupancy in worst 5% of samples
        alpha = 0.95
        k = max(1, int((1 - alpha) * self.cfg.n_samples))
        sorted_s = np.sort(samples, axis=0)   # ascending along sample axis
        cvar_map = sorted_s[-k:].mean(axis=0)

        logger.debug(
            "Diffusion risk map | mean=%.3f std=%.3f cvar=%.3f",
            mean_map.mean(), std_map.mean(), cvar_map.mean()
        )
        return {
            "mean": mean_map,
            "std": std_map,
            "cvar_95": cvar_map,
            "samples": samples,
        }

    def risk_weighted_cost(self, path: list[tuple[int, int]],
                           risk_maps: dict[str, np.ndarray],
                           lambda_risk: float = 2.0) -> float:
        """
        Compute the risk-augmented path cost.
        cost = path_length + lambda_risk * sum(cvar along path cells)
        """
        cvar = risk_maps["cvar_95"]
        cvar = np.asarray(cvar, dtype=float)
        if cvar.ndim != 2 or not np.all(np.isfinite(cvar)) or np.any((cvar < 0) | (cvar > 1)):
            raise ValueError("cvar_95 must be a finite 2D map in [0, 1]")
        if not np.isfinite(lambda_risk) or lambda_risk < 0:
            raise ValueError("lambda_risk must be finite and nonnegative")
        if not path:
            raise ValueError("path must contain at least one grid cell")
        if any(not (0 <= r < cvar.shape[0] and 0 <= c < cvar.shape[1]) for r, c in path):
            raise ValueError("path contains a cell outside the risk map")
        risk_sum = sum(cvar[r, c] for r, c in path)
        return float(len(path)) + lambda_risk * risk_sum
