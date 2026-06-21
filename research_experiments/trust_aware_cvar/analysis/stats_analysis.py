"""
analysis/stats_analysis.py
============================
Phase 7: statistical analysis of all experimental results.
Produces a single CSV (results/statistical_summary.csv) with, for every
relevant comparison:
  - t-test (Welch) p-value
  - Mann-Whitney U p-value
  - Cohen's d effect size
  - 95% confidence interval (bootstrap) on the mean difference
Also runs one-way ANOVA across calibration levels and density levels.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from scipy import stats

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def cohens_d(a, b):
    na, nb = len(a), len(b)
    pooled_std = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1)) / (na + nb - 2))
    if pooled_std == 0:
        return 0.0
    return (np.mean(a) - np.mean(b)) / pooled_std


def bootstrap_ci_diff(a, b, n_boot=2000, alpha=0.05, seed=0):
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        sa = rng.choice(a, size=len(a), replace=True)
        sb = rng.choice(b, size=len(b), replace=True)
        diffs[i] = sa.mean() - sb.mean()
    lo, hi = np.percentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def compare_two_groups(a: np.ndarray, b: np.ndarray, label_a, label_b, metric):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    t_stat, t_p = stats.ttest_ind(a, b, equal_var=False)
    try:
        u_stat, u_p = stats.mannwhitneyu(a, b, alternative="two-sided")
    except ValueError:
        u_stat, u_p = np.nan, np.nan
    d = cohens_d(a, b)
    ci_lo, ci_hi = bootstrap_ci_diff(a, b)
    return dict(comparison=f"{label_a}_vs_{label_b}", metric=metric,
                mean_a=float(a.mean()), mean_b=float(b.mean()),
                n_a=len(a), n_b=len(b),
                t_stat=float(t_stat), t_p=float(t_p),
                mwu_stat=float(u_stat), mwu_p=float(u_p),
                cohens_d=float(d), ci95_diff_lo=ci_lo, ci95_diff_hi=ci_hi,
                significant_p05=bool(t_p < 0.05))


def anova_across_levels(df: pd.DataFrame, group_col: str, metric: str):
    groups = [g[metric].values.astype(float) for _, g in df.groupby(group_col)]
    groups = [g for g in groups if len(g) > 1]
    if len(groups) < 2:
        return dict(group_col=group_col, metric=metric, f_stat=np.nan, p_value=np.nan)
    f_stat, p_value = stats.f_oneway(*groups)
    return dict(group_col=group_col, metric=metric, f_stat=float(f_stat), p_value=float(p_value))


def run_full_analysis():
    rows = []

    # --- Phase 4: TrustAwareCVaR vs every baseline, on collisions / success / cvar95 / energy ---
    df4 = pd.read_csv(os.path.join(RESULTS_DIR, "phase4_baseline_benchmark.csv"))
    target = "TrustAwareCVaR"
    for planner in df4["planner"].unique():
        if planner == target:
            continue
        for metric in ["collisions", "success", "cvar95", "energy", "path_length", "avg_replan_latency_ms"]:
            a = df4[df4.planner == target][metric].values
            b = df4[df4.planner == planner][metric].values
            rows.append(compare_two_groups(a, b, target, planner, metric))

    # --- Phase 5A: calibration sweep ANOVA + pairwise extremes (ECE 0.01 vs 0.30) ---
    df5a = pd.read_csv(os.path.join(RESULTS_DIR, "phase5a_calibration_sweep.csv"))
    for planner in df5a["planner"].unique():
        sub = df5a[df5a.planner == planner]
        for metric in ["collisions", "success", "cvar95"]:
            anova_res = anova_across_levels(sub, "target_ece", metric)
            anova_res["planner"] = planner
            anova_res["test_type"] = "ANOVA_calibration_levels"
            rows.append(anova_res)
        a = sub[sub.target_ece == 0.01]["collisions"].values
        b = sub[sub.target_ece == 0.30]["collisions"].values
        cmp = compare_two_groups(a, b, f"{planner}_ECE0.01", f"{planner}_ECE0.30", "collisions")
        rows.append(cmp)

    # --- Phase 5B: trust-level sweep ANOVA (TrustAwareCVaR only) ---
    df5b = pd.read_csv(os.path.join(RESULTS_DIR, "phase5b_trust_sweep.csv"))
    for metric in ["collisions", "success", "cvar95", "energy"]:
        anova_res = anova_across_levels(df5b, "trust", metric)
        anova_res["planner"] = "TrustAwareCVaR"
        anova_res["test_type"] = "ANOVA_trust_levels"
        rows.append(anova_res)
    a = df5b[df5b.trust == 0.2]["collisions"].values
    b = df5b[df5b.trust == 1.0]["collisions"].values
    rows.append(compare_two_groups(a, b, "Trust0.2", "Trust1.0", "collisions"))

    # --- Phase 5C: density sweep ANOVA per planner ---
    df5c = pd.read_csv(os.path.join(RESULTS_DIR, "phase5c_density_sweep.csv"))
    for planner in df5c["planner"].unique():
        sub = df5c[df5c.planner == planner]
        for metric in ["collisions", "success"]:
            anova_res = anova_across_levels(sub, "density_override", metric)
            anova_res["planner"] = planner
            anova_res["test_type"] = "ANOVA_density_levels"
            rows.append(anova_res)

    # --- Phase 5D: adversarial attack sweep -- TrustAwareCVaR vs DynNavCurrent under each attack ---
    df5d = pd.read_csv(os.path.join(RESULTS_DIR, "phase5d_attack_sweep.csv"))
    for atk in df5d["attack_type"].unique():
        sub = df5d[df5d.attack_type == atk]
        a = sub[sub.planner == "TrustAwareCVaR"]["collisions"].values
        b = sub[sub.planner == "DynNavCurrent"]["collisions"].values
        rows.append(compare_two_groups(a, b, f"TrustAwareCVaR_{atk}", f"DynNavCurrent_{atk}", "collisions"))

    # --- Phase 5E: shield on vs off, per planner ---
    df5e = pd.read_csv(os.path.join(RESULTS_DIR, "phase5e_shield_sweep.csv"))
    for planner in df5e["planner"].unique():
        sub = df5e[df5e.planner == planner]
        a = sub[sub.shield_enabled]["safety_violations"].values
        b = sub[~sub.shield_enabled]["safety_violations"].values
        rows.append(compare_two_groups(a, b, f"{planner}_ShieldON", f"{planner}_ShieldOFF", "safety_violations"))

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(RESULTS_DIR, "statistical_summary.csv"), index=False)
    print(f"Wrote {len(out)} statistical comparisons to statistical_summary.csv")
    return out


if __name__ == "__main__":
    run_full_analysis()
