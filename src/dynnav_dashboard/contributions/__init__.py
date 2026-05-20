"""
DynNav Dashboard — Per-Contribution Interactive Simulations.

Each module in this package implements a single contribution demo. Every
module exposes a top-level :func:`render` function that takes a Streamlit
container (or module) and renders that contribution's:

  1. short research explanation
  2. interactive controls
  3. simulation output plot(s)
  4. metrics
  5. interpretation of results

All simulations are synthetic, deterministic given a seed, and depend only on
``streamlit``, ``numpy``, ``pandas``, ``plotly``, and ``networkx``.
"""

from __future__ import annotations

from typing import Callable, Dict

from . import (
    c01_learned_astar,
    c02_ekf_ukf,
    c03_cvar_astar,
    c04_returnability,
    c05_safe_mode_fsm,
    c06_energy_connectivity,
    c07_next_best_view,
    c08_security_ids,
    c09_multi_robot,
    c10_human_aware,
    c11_twin_critic_rl,
    c12_diffusion_occupancy,
    c13_world_model,
    c14_causal_scm,
    c15_neuromorphic,
    c16_federated_learning,
    c17_topological_maps,
    c18_cbf_stl_shields,
    c19_llm_planner,
    c20_failure_explainer,
    c21_ppo,
    c22_curriculum_rl,
    c23_gaussian_splatting,
    c24_nerf_uncertainty,
    c25_adversarial,
    c26_bft_swarm,
)

RENDERERS: Dict[str, Callable] = {
    "C01": c01_learned_astar.render,
    "C02": c02_ekf_ukf.render,
    "C03": c03_cvar_astar.render,
    "C04": c04_returnability.render,
    "C05": c05_safe_mode_fsm.render,
    "C06": c06_energy_connectivity.render,
    "C07": c07_next_best_view.render,
    "C08": c08_security_ids.render,
    "C09": c09_multi_robot.render,
    "C10": c10_human_aware.render,
    "C11": c11_twin_critic_rl.render,
    "C12": c12_diffusion_occupancy.render,
    "C13": c13_world_model.render,
    "C14": c14_causal_scm.render,
    "C15": c15_neuromorphic.render,
    "C16": c16_federated_learning.render,
    "C17": c17_topological_maps.render,
    "C18": c18_cbf_stl_shields.render,
    "C19": c19_llm_planner.render,
    "C20": c20_failure_explainer.render,
    "C21": c21_ppo.render,
    "C22": c22_curriculum_rl.render,
    "C23": c23_gaussian_splatting.render,
    "C24": c24_nerf_uncertainty.render,
    "C25": c25_adversarial.render,
    "C26": c26_bft_swarm.render,
}

__all__ = ["RENDERERS"]
