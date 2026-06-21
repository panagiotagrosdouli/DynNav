"""
analysis/plots.py
==================
Phase 8: publication-quality matplotlib figures for every experimental phase.
Saves PNG (300dpi) figures to figures/.
"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
FIG_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11,
    "figure.dpi": 150, "savefig.dpi": 300, "axes.grid": True,
    "grid.alpha": 0.3, "font.family": "serif",
})

PLANNER_ORDER = ["Astar", "Dstar", "DstarLite", "RiskAwarePlanner", "CVaRPlanner", "DynNavCurrent", "TrustAwareCVaR"]
COLORS = plt.cm.tab10(np.linspace(0, 1, 10))


def _bar_with_ci(ax, labels, means, sems, title, ylabel):
    x = np.arange(len(labels))
    ax.bar(x, means, yerr=sems, capsize=4, color=COLORS[: len(labels)])
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_title(title)
    ax.set_ylabel(ylabel)


def plot_baseline_comparison():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase4_baseline_benchmark.csv"))
    metrics = [("success", "Success Rate"), ("collisions", "Collisions / Episode"),
               ("cvar95", "CVaR-95 Risk"), ("avg_replan_latency_ms", "Replan Latency (ms)")]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (metric, label) in zip(axes.flat, metrics):
        g = df.groupby("planner")[metric].agg(["mean", "sem"]).reindex(PLANNER_ORDER)
        _bar_with_ci(ax, PLANNER_ORDER, g["mean"], g["sem"], f"Baseline Comparison: {label}", label)
    fig.suptitle("Phase 4 — Planner Baseline Comparison (50 maps × 12 episodes)", y=1.02, fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "phase4_baseline_comparison.png"), bbox_inches="tight")
    plt.close(fig)


def plot_calibration_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5a_calibration_sweep.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for planner in ["CVaRPlanner", "DynNavCurrent", "TrustAwareCVaR"]:
        sub = df[df.planner == planner].groupby("target_ece")["collisions"].agg(["mean", "sem"])
        axes[0].errorbar(sub.index, sub["mean"], yerr=sub["sem"], marker="o", label=planner, capsize=3)
        sub2 = df[df.planner == planner].groupby("target_ece")["success"].agg(["mean", "sem"])
        axes[1].errorbar(sub2.index, sub2["mean"], yerr=sub2["sem"], marker="o", label=planner, capsize=3)
    axes[0].set_xlabel("Target ECE (uncertainty miscalibration)"); axes[0].set_ylabel("Collisions / Episode")
    axes[0].set_title("(A) Calibration Quality vs. Collision Rate")
    axes[1].set_xlabel("Target ECE"); axes[1].set_ylabel("Success Rate")
    axes[1].set_title("(B) Calibration Quality vs. Success Rate")
    for ax in axes:
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "phase5a_calibration_sweep.png"), bbox_inches="tight")
    plt.close(fig)


def plot_trust_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5b_trust_sweep.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    g1 = df.groupby("trust")["collisions"].agg(["mean", "sem"])
    g2 = df.groupby("trust")["energy"].agg(["mean", "sem"])
    axes[0].errorbar(g1.index, g1["mean"], yerr=g1["sem"], marker="o", color="firebrick", capsize=3)
    axes[0].set_xlabel("Trust Level"); axes[0].set_ylabel("Collisions / Episode")
    axes[0].set_title("(A) Trust Level vs. Collision Rate (TrustAwareCVaR)")
    axes[1].errorbar(g2.index, g2["mean"], yerr=g2["sem"], marker="s", color="navy", capsize=3)
    axes[1].set_xlabel("Trust Level"); axes[1].set_ylabel("Energy Consumption")
    axes[1].set_title("(B) Trust Level vs. Energy Consumption")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "phase5b_trust_sweep.png"), bbox_inches="tight")
    plt.close(fig)


def plot_density_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5c_density_sweep.csv"))
    order = ["low", "medium", "high", "extreme"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for planner in ["CVaRPlanner", "DynNavCurrent", "TrustAwareCVaR"]:
        sub = df[df.planner == planner].groupby("density_override")["collisions"].agg(["mean", "sem"]).reindex(order)
        ax.errorbar(order, sub["mean"], yerr=sub["sem"], marker="o", label=planner, capsize=3)
    ax.set_xlabel("Dynamic Obstacle Density"); ax.set_ylabel("Collisions / Episode")
    ax.set_title("Phase 5C — Collision Rate vs. Dynamic Obstacle Density")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "phase5c_density_sweep.png"), bbox_inches="tight")
    plt.close(fig)


def plot_attack_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5d_attack_sweep.csv"))
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    attacks = sorted(df["attack_type"].unique())
    width = 0.25
    planners = ["CVaRPlanner", "DynNavCurrent", "TrustAwareCVaR"]
    x = np.arange(len(attacks))
    for i, planner in enumerate(planners):
        means = [df[(df.attack_type == a) & (df.planner == planner)]["collisions"].mean() for a in attacks]
        sems = [df[(df.attack_type == a) & (df.planner == planner)]["collisions"].sem() for a in attacks]
        ax.bar(x + i * width, means, width, yerr=sems, capsize=3, label=planner, color=COLORS[i])
    ax.set_xticks(x + width)
    ax.set_xticklabels(attacks)
    ax.set_ylabel("Collisions / Episode")
    ax.set_title("Phase 5D — Robustness to Adversarial Attacks")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "phase5d_attack_sweep.png"), bbox_inches="tight")
    plt.close(fig)


def plot_shield_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5e_shield_sweep.csv"))
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    planners = sorted(df["planner"].unique())
    width = 0.35
    x = np.arange(len(planners))
    means_on = [df[(df.planner == p) & (df.shield_enabled)]["safety_violations"].mean() for p in planners]
    means_off = [df[(df.planner == p) & (~df.shield_enabled)]["safety_violations"].mean() for p in planners]
    sems_on = [df[(df.planner == p) & (df.shield_enabled)]["safety_violations"].sem() for p in planners]
    sems_off = [df[(df.planner == p) & (~df.shield_enabled)]["safety_violations"].sem() for p in planners]
    ax.bar(x - width / 2, means_on, width, yerr=sems_on, capsize=3, label="Shield ON", color="seagreen")
    ax.bar(x + width / 2, means_off, width, yerr=sems_off, capsize=3, label="Shield OFF", color="indianred")
    ax.set_xticks(x); ax.set_xticklabels(planners, rotation=20, ha="right")
    ax.set_ylabel("Safety Violations / Episode")
    ax.set_title("Phase 5E — Effect of Safety Shield")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "phase5e_shield_sweep.png"), bbox_inches="tight")
    plt.close(fig)


def plot_pareto_risk_vs_path():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase4_baseline_benchmark.csv"))
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for i, planner in enumerate(PLANNER_ORDER):
        sub = df[df.planner == planner]
        ax.scatter(sub["cvar95"].mean(), sub["path_length"].mean(), s=120, color=COLORS[i], label=planner)
    ax.set_xlabel("Mean CVaR-95 Risk"); ax.set_ylabel("Mean Path Length")
    ax.set_title("Risk–Efficiency Trade-off Across Planners")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "pareto_risk_vs_pathlength.png"), bbox_inches="tight")
    plt.close(fig)


def generate_all_plots():
    plot_baseline_comparison()
    plot_calibration_sweep()
    plot_trust_sweep()
    plot_density_sweep()
    plot_attack_sweep()
    plot_shield_sweep()
    plot_pareto_risk_vs_path()
    print(f"All figures written to {FIG_DIR}")


if __name__ == "__main__":
    generate_all_plots()
