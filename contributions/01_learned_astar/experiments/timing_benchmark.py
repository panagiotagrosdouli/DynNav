"""HISTORICAL cross-contribution C07/multi-objective timing, not C01 A* timing.

Retained in its original C01 path for provenance; CLI resolves actual source
dependencies and requires explicit coverage/centroid data inputs.
"""
import argparse
import sys
import time
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
for _folder in (REPO / "contributions" / "07_nbv_exploration" / "code", REPO / "core"):
    if str(_folder) not in sys.path:
        sys.path.insert(0, str(_folder))

from info_gain_planner import (
    load_coverage_grid,
    load_uncertainty_grid,
    compute_entropy_map,
    load_cluster_centroids,
)
from multiobj_planner import (
    compute_multiobjective_scores,
    approximate_pareto_front,
)

N_RUNS = 50  # πόσες φορές θα τρέξει κάθε μέθοδος για μέσο χρόνο


def benchmark_multiobj(H_map, U_map, centroids_df, robot_row=0, robot_col=0):
    """
    Μετράει χρόνο εκτέλεσης του multi-objective planner.
    """
    start = time.perf_counter()
    df_scores = None
    for _ in range(N_RUNS):
        df_scores = compute_multiobjective_scores(
            H_map,
            U_map,
            centroids_df,
            robot_row=robot_row,
            robot_col=robot_col,
            window_radius=4,
            w_ent=0.5,
            w_unc=0.3,
            w_cost=0.2,
        )
    end = time.perf_counter()
    avg_time = (end - start) / N_RUNS
    return avg_time, df_scores


def benchmark_pareto(df_scores):
    """
    Μετράει χρόνο υπολογισμού του Pareto front.
    """
    start = time.perf_counter()
    for _ in range(N_RUNS):
        _ = approximate_pareto_front(df_scores)
    end = time.perf_counter()
    avg_time = (end - start) / N_RUNS
    return avg_time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--centroids", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be positive")
    N_RUNS = args.runs
    probability = load_coverage_grid(str(args.coverage))
    entropy = compute_entropy_map(probability)
    uncertainty = load_uncertainty_grid(str(args.coverage))
    centroids = load_cluster_centroids(str(args.centroids))
    multiobj_sec, scores = benchmark_multiobj(entropy, uncertainty, centroids)
    pareto_sec = benchmark_pareto(scores)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame([
        {"component":"historical_C07_multiobjective", "avg_time_ms":multiobj_sec*1000},
        {"component":"historical_C07_pareto_front", "avg_time_ms":pareto_sec*1000},
    ])
    result.to_csv(args.out, index=False)
    print("HISTORICAL NON-C01-ASTAR TIMING (not evidence of learned-A* speed):")
    print(result.to_string(index=False))
