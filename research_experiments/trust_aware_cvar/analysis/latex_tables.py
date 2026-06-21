"""
analysis/latex_tables.py
==========================
Phase 8: generates publication-ready LaTeX tables from the result CSVs.
Writes .tex files to results/tables/.
"""
from __future__ import annotations
import os
import pandas as pd

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
TABLE_DIR = os.path.join(RESULTS_DIR, "tables")
os.makedirs(TABLE_DIR, exist_ok=True)

PLANNER_ORDER = ["Astar", "Dstar", "DstarLite", "RiskAwarePlanner", "CVaRPlanner", "DynNavCurrent", "TrustAwareCVaR"]


def df_to_latex(df, caption, label, float_fmt="%.3f"):
    return df.to_latex(caption=caption, label=label, float_format=float_fmt, escape=True)


def table_baseline_benchmark():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase4_baseline_benchmark.csv"))
    agg = df.groupby("planner").agg(
        SuccessRate=("success", "mean"), CollisionsEp=("collisions", "mean"),
        NearMissEp=("near_misses", "mean"), CVaR95=("cvar95", "mean"),
        PathLength=("path_length", "mean"), Energy=("energy", "mean"),
        ReplanLatencyMs=("avg_replan_latency_ms", "mean"),
    ).reindex(PLANNER_ORDER)
    tex = df_to_latex(agg, "Baseline planner comparison across the full 50-map / 12-episode benchmark suite.",
                       "tab:baseline")
    with open(os.path.join(TABLE_DIR, "table1_baseline.tex"), "w") as f:
        f.write(tex)
    return agg


def table_calibration_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5a_calibration_sweep.csv"))
    agg = df.groupby(["planner", "target_ece"]).agg(
        CollisionsEp=("collisions", "mean"), SuccessRate=("success", "mean"),
        CVaR95=("cvar95", "mean"),
    ).reset_index()
    tex = df_to_latex(agg, "Effect of uncertainty-calibration quality (target ECE) on navigation safety.",
                       "tab:calibration")
    with open(os.path.join(TABLE_DIR, "table2_calibration.tex"), "w") as f:
        f.write(tex)
    return agg


def table_trust_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5b_trust_sweep.csv"))
    agg = df.groupby("trust").agg(
        CollisionsEp=("collisions", "mean"), SuccessRate=("success", "mean"),
        CVaR95=("cvar95", "mean"), Energy=("energy", "mean"), PathLength=("path_length", "mean"),
    ).reset_index()
    tex = df_to_latex(agg, "Effect of trust level on the Trust-Aware CVaR planner.", "tab:trust")
    with open(os.path.join(TABLE_DIR, "table3_trust.tex"), "w") as f:
        f.write(tex)
    return agg


def table_density_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5c_density_sweep.csv"))
    order = ["low", "medium", "high", "extreme"]
    agg = df.groupby(["planner", "density_override"]).agg(
        CollisionsEp=("collisions", "mean"), SuccessRate=("success", "mean"),
    ).reset_index()
    agg["density_override"] = pd.Categorical(agg["density_override"], categories=order, ordered=True)
    agg = agg.sort_values(["planner", "density_override"])
    tex = df_to_latex(agg, "Effect of dynamic obstacle density on collision and success rate.", "tab:density")
    with open(os.path.join(TABLE_DIR, "table4_density.tex"), "w") as f:
        f.write(tex)
    return agg


def table_attack_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5d_attack_sweep.csv"))
    agg = df.groupby(["planner", "attack_type"]).agg(
        CollisionsEp=("collisions", "mean"), SuccessRate=("success", "mean"),
    ).reset_index()
    tex = df_to_latex(agg, "Robustness of risk-aware planners under FGSM, PGD, and sensor-spoofing attacks.",
                       "tab:attack")
    with open(os.path.join(TABLE_DIR, "table5_attack.tex"), "w") as f:
        f.write(tex)
    return agg


def table_shield_sweep():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5e_shield_sweep.csv"))
    agg = df.groupby(["planner", "shield_enabled"]).agg(
        SafetyViolationsEp=("safety_violations", "mean"), PathLength=("path_length", "mean"),
        SuccessRate=("success", "mean"),
    ).reset_index()
    tex = df_to_latex(agg, "Effect of the formal safety shield (Contribution 18 reproduction) on residual safety violations.",
                       "tab:shield")
    with open(os.path.join(TABLE_DIR, "table6_shield.tex"), "w") as f:
        f.write(tex)
    return agg


def table_statistical_significance():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "statistical_summary.csv"))
    keep_cols = [c for c in ["comparison", "metric", "mean_a", "mean_b", "t_p", "mwu_p", "cohens_d", "significant_p05"] if c in df.columns]
    sub = df[df["comparison"].notna()][keep_cols].head(30) if "comparison" in df.columns else df.head(30)
    tex = df_to_latex(sub, "Statistical significance summary (Welch t-test, Mann-Whitney U, Cohen's d) "
                            "for the Trust-Aware CVaR Planner vs. baselines (first 30 comparisons).",
                       "tab:stats")
    with open(os.path.join(TABLE_DIR, "table7_statistics.tex"), "w") as f:
        f.write(tex)
    return sub


def table_ablation_trust_components():
    """
    Ablation: ECE=0.30 (poor calibration) vs ECE=0.01 (good) for TrustAwareCVaR,
    isolating the marginal effect of the trust-from-calibration channel alone
    holding map/episode seeds fixed -- a minimal but real ablation given the
    available factors.
    """
    df = pd.read_csv(os.path.join(RESULTS_DIR, "phase5a_calibration_sweep.csv"))
    sub = df[df.planner == "TrustAwareCVaR"]
    agg = sub.groupby("target_ece").agg(
        CollisionsEp=("collisions", "mean"), SuccessRate=("success", "mean"), CVaR95=("cvar95", "mean"),
    ).reset_index()
    tex = df_to_latex(agg, "Ablation: sensitivity of the Trust-Aware CVaR planner to the calibration-quality "
                            "input channel of the trust score, all other trust sub-components held fixed.",
                       "tab:ablation_calibration")
    with open(os.path.join(TABLE_DIR, "table8_ablation_calibration.tex"), "w") as f:
        f.write(tex)
    return agg


def generate_all_tables():
    table_baseline_benchmark()
    table_calibration_sweep()
    table_trust_sweep()
    table_density_sweep()
    table_attack_sweep()
    table_shield_sweep()
    table_statistical_significance()
    table_ablation_trust_components()
    print(f"All LaTeX tables written to {TABLE_DIR}")


if __name__ == "__main__":
    generate_all_tables()
