import inspect
import time

import numpy as np
import pandas as pd

import risk_weighted_planner as rwp
from ids_cost_shaping import shape_lambda, synthetic_anomaly_stream

OUT_CSV = "ids_cost_shaping_results_real.csv"


def _call_with_signature(func, kwargs):
    sig = inspect.signature(func)
    filt = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return func(**filt)


def make_world(n=60, obstacle_p=0.12, seed=0):
    rng = np.random.default_rng(seed)
    occ = (rng.random((n, n)) < obstacle_p).astype(np.uint8)
    # free borders
    occ[0, :] = 0
    occ[:, 0] = 0
    occ[n - 1, :] = 0
    occ[:, n - 1] = 0

    risk = (0.2 + 0.8 * rng.random((n, n))).astype(np.float32)

    start = (1, 1)
    goal = (n - 2, n - 2)
    occ[start] = 0
    occ[goal] = 0
    return occ, risk, start, goal


def normalize_path(path):
    if path is None:
        return None
    if isinstance(path, np.ndarray):
        path = path.tolist()
    out = []
    for p in path:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            out.append((int(p[0]), int(p[1])))
    return out if len(out) >= 2 else None


def extract_path(result):
    if result is None:
        return None
    if isinstance(result, dict):
        for k in ["path", "waypoints"]:
            if k in result:
                return normalize_path(result[k])
        return None
    if isinstance(result, (list, np.ndarray)):
        return normalize_path(result)
    if isinstance(result, tuple):
        for item in result:
            if isinstance(item, (list, np.ndarray)):
                p = normalize_path(item)
                if p is not None:
                    return p
        return None
    return None


def plan_real(occ, risk, start, goal, lam, risk_budget=None):
    meta = {}
    common = {
        "occ_grid": occ,
        "occupancy": occ,
        "grid": occ,
        "occupancy_grid": occ,
        "risk_grid": risk,
        "risk": risk,
        "start": start,
        "goal": goal,
        "start_rc": start,
        "goal_rc": goal,
        "lambda_risk": lam,
        "lam": lam,
        "risk_lambda": lam,
        "risk_budget": risk_budget,
        "budget": risk_budget,
    }

    # Prefer adapter
    if hasattr(rwp, "_adapter_plan_with_lambda"):
        try:
            res = _call_with_signature(rwp._adapter_plan_with_lambda, common)
            path = extract_path(res)
            if path is not None:
                meta["api_used"] = "_adapter_plan_with_lambda"
                return path, meta
        except Exception as e:
            meta["last_err"] = f"adapter: {repr(e)}"

    if hasattr(rwp, "astar_risk_weighted"):
        try:
            res = _call_with_signature(rwp.astar_risk_weighted, common)
            path = extract_path(res)
            if path is not None:
                meta["api_used"] = "astar_risk_weighted"
                return path, meta
        except Exception as e:
            meta["last_err"] = f"astar: {repr(e)}"

    if hasattr(rwp, "plan_under_risk_budget"):
        try:
            if risk_budget is None:
                risk_budget = float(np.percentile(risk, 90)) * 200.0
                common["risk_budget"] = risk_budget
                common["budget"] = risk_budget
            res = _call_with_signature(rwp.plan_under_risk_budget, common)
            path = extract_path(res)
            if path is not None:
                meta["api_used"] = "plan_under_risk_budget"
                return path, meta
        except Exception as e:
            meta["last_err"] = f"budget: {repr(e)}"

    meta.setdefault("api_used", "none")
    meta.setdefault("last_err", "")
    return None, meta


def path_metrics(path, risk):
    if path is None or len(path) < 2:
        return None
    try:
        path_length = float(rwp.path_length_l2(path))
    except Exception:
        path_length = float(
            sum(
                abs(path[i + 1][0] - path[i][0])
                + abs(path[i + 1][1] - path[i][1])
                for i in range(len(path) - 1)
            )
        )
    try:
        path_risk = float(rwp.path_risk_sum(path, risk))
    except Exception:
        path_risk = float(sum(float(risk[r, c]) for (r, c) in path))
    max_r = float(max(float(risk[r, c]) for (r, c) in path))
    return {
        "path_length": path_length,
        "path_risk_sum": path_risk,
        "path_max_risk_cell": max_r,
    }


def main():
    print("[DEBUG] real runner starting…")
    t0 = time.time()

    seeds = list(range(6))
    attack_levels = [0.0, 0.7]
    modes = ["baseline", "lambda_shaping"]

    horizon = 12
    attack_start, attack_end = 4, 10
    lambda0 = 1.0

    rows = []

    for seed in seeds:
        occ, risk, start, goal = make_world(seed=seed)
        for attack_level in attack_levels:
            scores = synthetic_anomaly_stream(
                T=horizon,
                attack_start=attack_start,
                attack_end=attack_end,
                base=0.05,
                attack_level=attack_level,
                noise=0.03,
                seed=seed,
            )
            for mode in modes:
                ok_plans = 0
                total_cost = 0.0
                total_risk = 0.0
                max_risk_cell = 0.0
                api_used_any = None
                last_err_any = ""

                for t in range(horizon):
                    score = float(scores[t])
                    if mode == "baseline":
                        lam = lambda0
                    else:
                        lam = shape_lambda(lambda0, score, beta=2.5)

                    path, meta = plan_real(occ, risk, start, goal, lam)
                    api_used_any = api_used_any or meta.get("api_used", None)
                    last_err_any = meta.get("last_err", "") or last_err_any

                    metrics = path_metrics(path, risk) if path is not None else None
                    if metrics is None:
                        continue

                    ok_plans += 1
                    total_cost += metrics["path_length"]
                    total_risk += metrics["path_risk_sum"]
                    max_risk_cell = max(
                        max_risk_cell,
                        metrics["path_max_risk_cell"],
                    )

                episode_success = 1 if ok_plans >= int(0.7 * horizon) else 0
                rows.append(
                    {
                        "seed": seed,
                        "attack_level": attack_level,
                        "mode": mode,
                        "lambda0": lambda0,
                        "T": horizon,
                        "attack_start": attack_start,
                        "attack_end": attack_end,
                        "mean_score": float(np.mean(scores)),
                        "max_score": float(np.max(scores)),
                        "ok_plans": int(ok_plans),
                        "episode_success": int(episode_success),
                        "total_cost": float(total_cost),
                        "total_risk": float(total_risk),
                        "max_risk_cell": float(max_risk_cell),
                        "api_used": api_used_any or "none",
                        "last_err": last_err_any,
                        "used_toy_fallback": 0,
                    }
                )

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"[OK] wrote {OUT_CSV} rows={len(df)}")
    print("[INFO] api_used counts:", df["api_used"].value_counts().to_dict())
    print(f"[TIME] {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()
